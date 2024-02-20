from . import *
from ..connection import Connection
from fastapi.responses import RedirectResponse
from nicegui import app, ui
import json
import typing as t


def validate_pass(password: str, password_hash: str) -> bool:
    from hashlib import md5
    return md5(password.encode('utf-8')).hexdigest() == password_hash

@ui.page('/login')
def login() -> t.Optional[RedirectResponse]:
    sql = Connection(**CREDENTIALS)

    def try_login() -> None:
        if not username.value or not password.value:
            ui.notify('Некорректные логин или пароль', color='negative')
            return
        user = sql.execute(
            query=Connection.select_user % {'schema': SCHEMA, 'username': '$username'},
            params={'username': username.value}
        )[0]
            
        if validate_pass(password.value, user['props__map'].get('__password_hash', '')):
            to_update = {
                'username': username.value,
                'authenticated': True,
                '%s_icon' % username.value: fix_icon(user['icon']),
                '%s_name' % username.value: user['name'],
            }

            if not (entities := app.storage.user.get(user_entities := '%s_entities' % username.value, None)) or len(entities) < len(DEFAULT_ENTITIES):
                to_update.update({
                    user_entities: DEFAULT_ENTITIES
                })
            if not app.storage.user.get(user_cards := '%s_cards' % username.value, None):
                to_update.update({
                    user_cards: json.dumps(DEFAULT_CARDS, ensure_ascii=False)
                })
            if not app.storage.user.get(user_filters := '%s_filters' % username.value, None):
                to_update.update({
                    user_filters: DEFAULT_FILTERS
                })
            if not app.storage.user.get(user_suggests := '%s_suggests' % username.value, None):
                to_update.update({
                    user_suggests: DEFAULT_SUGGESTS
                })
            app.storage.user.update(to_update)

            ui.open(app.storage.user.get('referrer_path', '/'))
        else:
            ui.notify('Некорректные логин или пароль', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')

    ### Добавление стилей и шрифтов
    ui.add_body_html('<style>%s</style>' % STYLESHEET)    
    
    with ui.element('div').classes('container'):
        with ui.column().classes('absolute-center login-col'):
            ui.image('%s/logo.svg' % STATIC).classes('login-img')
            username = ui.input(placeholder='Логин')\
                .props('dense borderless')\
                .classes('login-form')\
                .on('keydown.enter', try_login)
            password = ui.input(placeholder='Пароль', password=True, password_toggle_button=True)\
                .props('dense borderless')\
                .classes('login-form')\
                .on('keydown.enter', try_login)
            with ui.row().classes('login-buttons'):
                ui.button('Войти').classes('login-button login').on('click', try_login)
                ui.button('Запросить доступ').classes('login-button register')
            ui.element('div').style('height: 130px; width: auto;')
