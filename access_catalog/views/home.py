from . import *
from ..connection import Connection
from copy import deepcopy
from functools import reduce
from nicegui import app, context, ui
from nicegui.element import Element
from nicegui.elements.column import Column
import json
import typing as t


MAP_TITLE: dict[str, str] = {x['type']: x['name'] for x in DEFAULT_ENTITIES}
MAP_STATUS: dict[str, str] = {
    'готово': 'done',
    'в работе': 'processing',
    'отклонено': 'rejected', 
    'открыто': 'open',
}

class AccessLogic:
    """ Логика отображения элементов в колонке доступов """
    def __init__(self, *args, **kwargs) -> None:
        self.all_entities: bool = kwargs.pop('all_entities', False)
        self.has_records: bool = kwargs.pop('has_records', False)
    
    @property
    def to_select(self) -> bool: return not self.all_entities

    @property
    def to_create(self) -> bool: return self.all_entities and not self.has_records

    @property
    def to_show(self) -> bool: return self.all_entities and self.has_records

@ui.page('/')
def home() -> None:
    """ Домашняя страница """
    
    def item_drop(event) -> None:
        """ Drag'n'drop реализация """
        context.get_client().elements[event.args['id']].move(target_index=event.args['new_index'])

        app.storage.user.update({
            "%s_entities"  % username: [
                {
                    "type": (type_ := x._props['entity']),
                    "name": [x for x in DEFAULT_ENTITIES if x['type'] == type_][0]['name']
                } for x in columns.slots['default'].children[:-1] ### исключить неактивную колонку с доступами ### type: ignore
            ] 
        })

    def deselect(event = None) -> None:
        """ Отмена выделения для всех или для конкретной сущности """
        if not event:
            for x in [x for x in cards_flatten() if x.selected == True]:
                x.__select__()
            return

        entities = [*event.sender._event_listeners.values()][0].args[0]
        flatten = []
        
        for x in [v for k, v in cards.items() if (k in entities)]:
            flatten += [x for x in x if x.selected == True]

        for x in flatten:
            x.__select__()
        
        ui.update()

    def get_accesses() -> None:
        """ Наполнение колонки доступов """
        for x in sql.execute(Connection.select_access % {
            'schema': SCHEMA,
            'service_uuid': str(cards_selected(cards['services'])[0].uuid),
            'project_uuid': str(cards_selected(cards['projects'])[0].uuid),
            'role_uuid': str(cards_selected(cards['roles'])[0].uuid),
            'user_uuid': str(cards_selected(cards['users'])[0].uuid),
        }):
            with ui.element('div').classes('home-body-row-card').style('gap: 10px; width: 100%; background: transparent; align-self: stretch; display: flex; align-items: flex-start;'):
                with ui.column().style('width: 100%; padding: 5px 0 5px 0; gap: 15px;'): #
                    with ui.element('div').style('width: 100%; display: flex; flex-wrap: wrap; align-self: stretch; align-items: flex-start; justify-content: center;'):
                        ui.label(x['status']).classes('home-body-row-card-tag %s' % MAP_STATUS[x['status'].lower()])
                        ui.label(x['start_date'].strftime('%d.%m.%y в %H:%M')).style('margin-top: 1px; flex: 1; font-size: 13px; font-weight: 600; justify-content: center; text-align: end;')
                    if x['creator']:
                        with ui.row().style('gap: 10px; align-self: stretch; width: 100%; display: flex; align-items: flex-start; align-self: stretch;'):
                            ui.label('Заказчик ').style('font-weight: 600; font-size: 14px; line-height: 16px;')
                            ui.label(x['creator']).style('font-size: 14px; line-height: 16px; flex: 1 0 0;')
                    if x['comment']:
                        with ui.column().style('gap: 5px; position: relative; align-self: stretch; width: 100%; display: flex; align-items: flex-start; align-self: stretch;'):
                            ui.label('Комментарий').style('flex: 1; font-weight: 600; font-size: 14px; align-self: stretch; position: relative;')
                            ui.label(x['comment']).style('font-size: 13px; line-height: 15px;')
        ui.button('Отозвать доступ', on_click = lambda: (lambda *args: None)(
            sql.execute(Connection.revoke_access % {
                'schema': SCHEMA,
                'service_uuid': str(cards_selected(cards['services'])[0].uuid),
                'project_uuid': str(cards_selected(cards['projects'])[0].uuid),
                'role_uuid': str(cards_selected(cards['roles'])[0].uuid),
                'user_uuid': str(cards_selected(cards['users'])[0].uuid),
            }),
            ui.notify('Доступ отозван', color='positive'),
            deselect(),
        )).classes('menu-button text-lg !bg-red-500')
                     
    class Entity(Column):
        """ Выбираемая карточка """
        def __init__(self, *args, **kwargs) -> None:
            if not all([x in kwargs.keys() for x in ['type', 'name']]):
                raise Exception("Пропущены значения необходимых атрибутов карточки")
            
            self.uuid = kwargs.pop('uuid')
            self.type: str = kwargs.pop('type')
            self.name: str = kwargs.pop('name')
            self.icon: str = fix_icon(kwargs.pop('icon'))
            self.desc: str | None = kwargs.pop('desc', None)
            self.properties: dict = kwargs.pop('properties', {})
            self.attr_selected = 'selected'
            self.tags: set = {*kwargs.pop('tags', set())}
            if self.type == 'users' and \
                    app.storage.user.get('username') == self.properties.get('__login'):
                self.tags = {*self.tags, 'Я'}
            selected = kwargs.pop('selected', False)
            suggested = kwargs.pop('suggested', False)

            super().__init__(*args, **kwargs)
            self.props(add='%s=%s' % (self.attr_selected, selected))
            cards[self.type].append(self)

            
            ### Горячие клавиши и события
            self.on('click', self.__select__)
            
            with self.classes('home-body-row-card').style('display: %s;' % ('flex' if selected == True else 'hidden')) as c:
                if any([[y for y in x.values() if y == True] for x in prev_cards.values()]):
                    if self.selected and self.name not in prev_filters.get(self.type, []):
                        c.classes(add='foreign')
                    if suggested == False and selected == False:
                        c.classes(add='semi-transparent')
                with ui.row().classes('home-body-row-card-header'):
                    with ui.element('div').classes("home-body-row-card-header-icon-wrapper"):
                        ui.image(self.icon.format(static=STATIC)).classes('icon')
                    with ui.element('div').classes("home-body-row-card-title-wrapper"):
                        ui.label(self.name).classes('home-body-row-card-title-font')
                if self.desc:
                    with ui.element('div').classes("home-body-row-card-desc-wrap").bind_visibility_from(self, 'selected'):
                        ui.label(self.desc).classes('home-body-row-card-desc-font')
                if self.tags:
                    with ui.row().classes('home-body-row-card-tags-wrap'):
                        for x in self.tags:
                            ui.label(x).classes('home-body-row-card-tag %s' % ('open' if x == 'Я' else ''))
                if self.properties.get('__link'):
                    ui.button('Перейти к инструменту', on_click=lambda: ui.open(self.properties.get('__link', ''), new_tab=True)).style(
                        'width: 100%; background-color: #4d4d4d !important; color: #ffffff !important; font-size: 14px; padding: 1px; font-weight: 700; margin: 5px 0 5px 0; align-self: center; border-radius: 20px;'
                    ).bind_visibility_from(self, 'selected')
            
        @property
        def selected(self) -> bool:
            """ Свойство, обозначающее выбран элемент или нет """
            return json.loads(self._props[self.attr_selected].lower())

        def __select__(self, skip_filter: bool = False) -> None:
            """ Выбор элемента 
            
            Параметры:
                skip_filter (bool): пропуск пересчета данных на стороне базы
                
            """
            selected = not self.selected
            self._props[self.attr_selected] = str(selected)
            prev_cards[self.type][self.name] = selected
            app.storage.user.update({'%s_cards' % username: json.dumps(prev_cards, ensure_ascii=False)})
            self.classes(remove='foreign semi-transparent')

            if not [x for x in cards_flatten() if x.selected == True]:
                for x in cards_flatten():
                    x.classes(remove='foreign semi-transparent')
                    app.storage.user.update({
                        "%s_filters" % username: DEFAULT_FILTERS,
                        "%s_suggests" % username: DEFAULT_SUGGESTS,
                    })
            else:
                prev_filters = json.loads(app.storage.user.get("%s_filters" % username, DEFAULT_FILTERS))
                prev_suggests = json.loads(app.storage.user.get("%s_suggests" % username, DEFAULT_SUGGESTS))
                
                if skip_filter == False: ### если необходимо пропустить пересчет в базе данных
                    cols = [x._props['entity'] for x in columns.default_slot.children][:-1] # type: ignore
                    where = ' and '.join([
                        '%(entity)s in (%(values)s)' % {
                            'entity': x[0] + '.name',
                            'values': ', '.join([f"'{y.name}'" for y in cards_selected(cards[x])])
                        } for x in cols if len(cards_selected(cards[x])) > 0
                    ])
                    filters = {
                        k:v if v else [] for k,v in sql.execute(
                            Connection.filter_access % {"schema": SCHEMA, "where": where}
                        )[0].items()
                    }
                else:
                    filters = deepcopy(prev_filters)

                ### Задание стилей для всех карточек
                for k, v in filters.items():
                    for x in cards[k]:
                        if x.name in v or x.name in prev_filters.get(x.type, []):
                            x.classes(remove='semi-transparent')
                        elif x.selected and prev_filters and x.name not in prev_filters.get(x.type, []):
                            x.classes(add='foreign')
                        else:
                            x.classes(add='semi-transparent')

                ### Дополнение и резервация фильтра и потенциальных карточек
                for k,v in filters.items():
                    if cards_selected(cards[k]):
                        prev_filters[k] += filters[k]# + ([self.name] if self.selected and self.type == k else [])
                        prev_suggests[k] = []
                    else:
                        prev_filters[k] = [*{*prev_filters[k]}.intersection(v)]
                        prev_suggests[k] = [*v]
                    ### Дедубликация списков
                    prev_filters[k] = [*{*prev_filters[k]}]

                ### Очистка фильтра от более неактуальных элементов
                for x in cards_flatten():
                    if x.name in prev_filters[x.type] and not x.selected:
                        prev_filters[x.type].pop(prev_filters[x.type].index(x.name))

                ### Обновление сохраненных фильтра и потенциальных карточек
                app.storage.user.update({
                    '%s_selected' % username: all([x for x in filters.values()]),
                    "%s_filters" % username: json.dumps(prev_filters, ensure_ascii=False),
                    "%s_suggests" % username: json.dumps(prev_suggests, ensure_ascii=False)
                })

                ### Обновление логики доступов и отображение
                access_logic.has_records = all([x for x in filters.values()])
                access_logic.all_entities = len({k for k,v in cards.items() if any([x.selected for x in v])}) == 4
                if access_cards:
                    if access_cards[-1].slots['default'].children and access_logic.to_show != True: 
                        while access_cards[-1].slots['default'].children:
                            access_cards[-1].remove(access_cards[-1].slots['default'].children[0])
                    if not access_cards[-1].slots['default'].children and access_logic.to_show == True:
                        with access_cards[-1]:
                            get_accesses()

            self.update()
    
    sql = Connection(**CREDENTIALS)

    ### Значения берутся из предыдущей сессии
    username = app.storage.user.get('username')
    prev_cards = json.loads(app.storage.user.get('%s_cards' % username, DEFAULT_CARDS))
    prev_filters = json.loads(app.storage.user.get('%s_filters' % username, DEFAULT_FILTERS))
    prev_suggests = json.loads(app.storage.user.get('%s_suggests' % username, DEFAULT_SUGGESTS))
    access_logic = AccessLogic(
        all_entities=len({k for k,v in prev_cards.items() if any([x for x in v.values() if x == True])}) == 4,
        has_records=app.storage.user.get('%s_selected' % username, False) == True
    )

    ### Значения устанавливаются в ходе отрисовки страницы
    cards: dict[str, list[t.Any]] = json.loads(DEFAULT_FILTERS)
    cards_flatten = lambda: reduce(lambda a, b: a + b, [*cards.values()])
    cards_selected: t.Callable[[list], list[t.Any]] = lambda e: [x for x in e if x.selected == True]
    columns = None
    access_cards = []

    ### Горячие клавиши и события
    ui.on('keydown.ctrl.shift.e', deselect)
    ui.on('keydown.ctrl.shift.escape', logout)
    ui.on('item-drop', lambda e: item_drop(e))

    ### Добавление стилей и шрифтов и реализация drag & drop для колонок ###
    ui.add_body_html("""<style>%s</style><script type="module">%s</script>""" % (STYLESHEET, SCRIPTS,))

    with ui.element('div').classes("container"):
        """
            HEADER - HEADER - HEADER - HEADER - HEADER - HEADER - HEADER - HEADER
        """
        with ui.element('div').classes("header-wrap"):
            with ui.element('div').classes("header"):
                with ui.link(target='http://localhost:%s' % PORT):
                    ui.image('%s/logo.png' % STATIC).style('height: 40px; width: 120px;')
                with ui.row().classes('header-nav'):
                    with ui.link(target='http://localhost:%s' % PORT):
                        ui.label('Документация').classes('header-nav-text')
                with ui.element('div').classes("header-search"):
                    search_field = ui.input(
                        placeholder='Поиск сервисов, проектов, ролей и пользователей...',
                        on_change=lambda e: search(e, cards_flatten()[:]),
                        autocomplete=[str(x.name) for x in cards_flatten()],
                        # validation={'Input too long': lambda value: len(value) < 20}
                    ).props('dense borderless').classes('header-search-text').on('click', lambda: [x.style('display: none;') for x in cards_flatten()])
                    ui.image('%s/search.svg' % STATIC).classes('w-5 h-5')
            with ui.row().classes('header-nav'):
                with ui.link(target='http://localhost:%s' % PORT):
                    ui.image('%s/help.svg' % STATIC).classes('w-6 h-6')
                with ui.image(str(app.storage.user.get('%s_icon' % app.storage.user.get('username')))).classes('w-6 h-6'):
                    with ui.menu().classes('menu'):
                        with ui.element('div').classes("menu-header"):
                            ui.label(str(app.storage.user.get('%s_name' % app.storage.user.get('username')))).classes('menu-header-title')
                        ui.button('Настройки').classes('menu-button text-lg !text-neutral-700').style('background: #CFDDFC !important;')
                        ui.separator()
                        ui.button('Выйти').classes('menu-button text-lg !bg-red-500').on('click', logout)

        """
            BODY - BODY - BODY - BODY - BODY - BODY - BODY - BODY - BODY - BODY
        """
        columns = ui.row().classes('home-body sortable')
        with columns:
            entities = app.storage.user.get('%s_entities' % username, [])
            for x in entities:
                with ui.card().classes('home-body-row').props(add='entity="%s"' % x['type']):
                    with ui.element('div').classes("home-body-row-header"):
                        ui.label(str(x['name']).capitalize()).classes('home-body-row-header-text cursor-grab')
                        with ui.element('div').classes("home-body-row-cell-selected-wrap"):
                            with ui.element('div').classes("home-body-row-cell-selected")\
                                    .bind_visibility_from(cards, str(x['type']), lambda e: len(cards_selected(e)) > 0):
                                ui.label().classes('home-body-row-cell-selected-text').bind_text_from(cards, x['type'], lambda e: len(cards_selected(e)))
                            with ui.button().classes("home-body-row-cell-selected reset")\
                                    .on('click', lambda e: deselect(e), args=[str(x['type'])], trailing_events=False)\
                                    .bind_visibility_from(cards, str(x['type']), lambda e: len(cards_selected(e)) > 0):
                                ui.image('%s/cross.svg' % STATIC).classes('home-body-row-cell-selected-icon')

                    with ui.element('div').classes('separator'): ui.separator()
                    with ui.scroll_area().classes('home-body-row-scroll'):
                        with ui.column().classes('home-body-row-col') as col:
                            if x['type'] != 'accesses':
                                _cards = sql.execute(Connection.select_entity % {"schema": SCHEMA, "table": x['type']})
                                for y in _cards:
                                    Entity(
                                        uuid=y['uuid'],
                                        type=x['type'],
                                        name=y['name'],
                                        icon=y['icon'],
                                        desc=y['dscr'],
                                        tags=ensure_struct(y['tags__list'] if y['tags__list'] else []),
                                        properties=ensure_struct(y['props__map'] if y['props__map'] else {}),
                                        selected=prev_cards.get(x['type'], {}).get(y['name'], False),
                                        suggested=y['name'] in prev_suggests.get(x['type'], [])
                                    )
                                with ui.element('div').classes('home-body-row-card new').style('opacity: 100%; border-style: dashed;').props('type=%s add=True' % x['type']):
                                    ui.label('+').classes('home-body-row-card-title-font').style('align-self: center; font-weight: 900; color: #8090b2;')
                    with ui.element('div').classes('separator'): ui.separator()
                        
            """
                ACCESSES - ACCESSES - ACCESSES - ACCESSES - ACCESSES - ACCESSES
            """                        
            with ui.card().classes(add='home-body-row non-draggable').props(add='entity="accesses"'):
                with ui.row().classes("home-body-row-header"):
                    ui.label('Доступ').classes('home-body-row-header-text')
                with ui.element('div').classes('separator').style('margin-top: -1px;'): ui.separator()
                with ui.column()\
                        .style('gap: 10px; padding: 10px;')\
                        .bind_visibility_from(target_object=access_logic, target_name='to_select', backward=lambda _: _):
                    ui.label('Для просмотра состояния доступа необходимо также выбрать:')\
                        .style('color: #000000; font-size: 14px; line-height: 16px;')
                    ui.label()\
                        .style('color: #000000; font-size: 14px; font-weight: 600; line-height: 16px; font-style: italic;')\
                        .bind_text_from({'': cards.items()}, '', backward=lambda items: ', '.join([MAP_TITLE[k].capitalize() for k,v in items if not any([x.selected for x in v])]))\
                
                with ui.column().classes('home-body-row-col')\
                        .bind_visibility_from(target_object=access_logic, target_name='to_create', backward=lambda _: _):
                    creator = ui.input(placeholder='Заказчик').props('dense borderless').classes('login-form').style('font-size: 14px !important;')
                    comment = ui.textarea(placeholder='Комментарий').props('dense borderless').classes('login-form').style('font-size: 14px; min-height: 140px;')
                    ui.button(
                        'Запросить доступ', on_click=lambda: (sql.insert(data=[{
                            'service_uuid': str(cards_selected(cards['services'])[0].uuid),
                            'project_uuid': str(cards_selected(cards['projects'])[0].uuid),
                            'role_uuid': str(cards_selected(cards['roles'])[0].uuid),
                            'user_uuid': str(cards_selected(cards['users'])[0].uuid),
                            'status': 'Открыто',
                            'comment': str(comment.value),
                            'creator': str(creator.value if creator.value else username),
                        }], schema=SCHEMA, table='accesses') or deselect() or ui.notify('Запрос доступа создан', color='positive'))
                    ).style(
                        'width: 100%; background-color: #4d4d4d !important; color: #ffffff !important; padding: 1px; font-weight: 700; align-self: center; border-radius: 20px;'
                    )
                        
                with ui.scroll_area().classes('home-body-row-scroll')\
                        .bind_visibility_from(target_object=access_logic, target_name='to_show', backward=lambda _: _):
                    with ui.column().classes('home-body-row-col') as col:
                        access_cards.append(col)
                        if access_logic.has_records:
                            try:
                                get_accesses()
                            except:
                                pass #

                            
