from contextlib import contextmanager
from datetime import date, datetime
from json import loads
import duckdb
import typing as t


class Connection:
    """ Коннектор к DuckDB хранилищу данных """

    select_schema: str = """
        select count(*)
        from duck.information_schema.schemata 
        where catalog_name||'.'||schema_name = '%(schema)s'
    """
    """ Запрос выборки схемы на предмет готовности хранилища к работе """

    select_user: str = """
        select * 
        from (
            select *
                 , element_at(props__map, '__login')[1] as login
                 , element_at(props__map, 'корп. почта')[1] as corp_mail
            from %(schema)s.users 
            where __final is null
        )
        where login = %(username)s or corp_mail = %(username)s
        limit 1
    """
    """ Запрос выборки пользователя для аутентификации """
    
    revoke_access: str = """
        delete from %(schema)s.accesses where true 
            and service_uuid = '%(service_uuid)s'
            and project_uuid = '%(project_uuid)s'
            and role_uuid = '%(role_uuid)s'
            and user_uuid = '%(user_uuid)s'
    """
    """ Запрос отзыва доступа """

    grant_access: str = """
    """
    """ Запрос предоставления доступа """

    select_access: str = """
        select *, __start as start_date from %(schema)s.accesses where True 
            and service_uuid = '%(service_uuid)s'
            and project_uuid = '%(project_uuid)s'
            and role_uuid = '%(role_uuid)s'
            and user_uuid = '%(user_uuid)s'
        order by __start desc
    """
    """ Запрос выборки доступа """

    filter_access: str = """
        select array_agg(distinct s.name) as services
             , array_agg(distinct p.name) as projects
             , array_agg(distinct r.name) as roles
             , array_agg(distinct u.name) as users
        from %(schema)s.accesses a
        left join %(schema)s.services s on a.service_uuid = s.uuid and s.__final is null 
        left join %(schema)s.projects p on a.project_uuid = p.uuid and p.__final is null
        left join %(schema)s.roles r on a.role_uuid = r.uuid and r.__final is null
        left join %(schema)s.users u on a.user_uuid = u.uuid and u.__final is null
        where a.__final is null and %(where)s;
    """
    """ Запрос фильтрации выборки """
    
    select_entity: str = """
        select * from %(schema)s.%(table)s where __final is null order by name
    """
    """ Запрос выборки сущности """

    def __init__(self, *args, handle: bool = False, **kwargs) -> None:
        self.args: tuple[t.Any] = args
        self.kwargs: dict[str, t.Any] = kwargs

        if handle == True: ### режим обработки исключений
            self.execute = self.__handle(self.execute)
            self.insert = self.__handle(self.insert)

    def __handle(self, f: t.Callable) -> t.Callable:
        """ Обработка исключений
        
        """
        def wrapper(*args, **kwargs) -> list[dict[str, t.Any]]:
            try:
                return f(*args, **kwargs)
            except Exception as e:
                print((e, *args, *kwargs.values(),))
                return [{}]
        return wrapper

    @contextmanager
    def __connect(self) -> t.Generator[duckdb.DuckDBPyConnection, None, None]:
        c: duckdb.DuckDBPyConnection = duckdb.connect(*self.args, **self.kwargs)
        try:
            yield c
        finally:
            c.close()

    def execute(self, query: str, **kwargs) -> list[dict[str, t.Any]]:
        """ Выполнение запроса

        Параметры:
            query (str): текстовый запрос
        
        Возвращает: 
            list[dict[str, t.Any]]
        
        """
        with self.__connect() as c:
            rows: duckdb.DuckDBPyRelation = c.sql(query, **kwargs)
            if not rows or not rows.columns:
                return [{}]
            
            cols: dict = dict(zip(rows.columns, rows.types))
            data: list = [dict(zip(cols.keys(), x)) for x in rows.fetchall()]
    
            return [{
                ### корректировка структур
                k: (
                    (dict(zip(*v.values())) if v else {}) if k.endswith('__map') else v
                ) for k,v in x.items() if not k.startswith('__')
            } for x in data]

    def insert(
        self,
        schema: str,
        table: str,
        data: list[dict[str, t.Any]],
        cols: t.Sequence = []
    ) -> None:
        """ Вставка данных в хранилище 

        Параметры:
            schema (str): целевая схема
            table (str): целевая таблица
            data (list[dict[str, t.Any]]): искомые данные
            cols (t.Sequence): перечень колонок для вставки
        
        """
        serialize: t.Callable = lambda x: {
            int: lambda x: str(x),
            str: lambda x: '\'%s\'' % x,
            bool: lambda x: str(x).lower(),
            date: lambda x: '\'%s\'' % x,
            datetime: lambda x: '\'%s\'' % x,
            list: lambda x: ('%s' % x).replace('None', 'null'),
            dict: lambda x: ('MAP %s' % x).replace('None', 'null'),
            None: lambda x: 'null'
        }.get(type(x) if x != None else None, str)(x)

        query: str = """insert into %(s)s.%(t)s (%(c)s) values %(v)s""" % {
            's': schema,
            't': table,
            'c': ', '.join(data[0] if not cols else cols),
            'v': ', '.join(['(%s)' % ', '.join(map(serialize, r.values())) for r in data])
        }

        try:
            self.execute(query)
        except Exception as e:
            print(query)
            raise e

def prepare_database(
    sql: Connection,
    sample: dict[str, list[dict[str, t.Any]]],
    schema: str
) -> None:
    """ Инициализация презентационной базы данных
    
    Параметры:
        sample (dict[str, list[dict[str, t.Any]]]): словарь вида {
            'сущность': [список записей для вставки]
        }
        schema (str): схема данных
        
    """
    create_metadata: str = """
        drop schema if exists %(schema)s cascade;
        create schema %(schema)s;
    """ % {'schema': schema}

    create_entity: str = """
        drop table if exists %(schema)s.%(table)s;
        create table %(schema)s.%(table)s (
            __start			timestamp 				default (now()),
            __final			timestamp,
            uuid			uuid					default (uuid()),
            name			varchar(200),
            dscr    		varchar(200),
            icon			varchar(200),
            tags__list		varchar[],
            props__map		map(varchar, varchar)
        );
    """

    create_accesses: str = """
        drop table if exists %(schema)s.accesses;
        create table %(schema)s.accesses (
            __start			datetime		default (now()),
            __final			datetime		default (null),
            %(create)s,
            status			varchar(36),
            creator			varchar(36),
            comment			varchar(200)
        );
        insert into %(schema)s.accesses by name
        select now() as __start
             , null as __final
             , %(select)s
             , 'Готово' as status
             , 'Деркач Иван Сергеевич' as creator
             , null as comment
        from (select null) _
        %(fljoin)s
        order by random()
        limit 5;
    """ % {
        'schema': schema,
        'create': ',\n'.join(map(lambda x: '%s_uuid uuid' % x[:-1], sample)),
        'select': '\n,'.join(map(lambda x: '%s.uuid as %s_uuid' % (x, x[:-1]), sample)),
        'fljoin': '\n'.join(map(lambda x: 'full join %s.%s on true' % (schema, x), sample))
    }
    print(create_accesses)

    sql.execute(create_metadata)
    for k, v in sample.items():
        sql.execute(create_entity % {'schema': schema, 'table': k})
        sql.insert(schema, k, v)
    sql.execute(create_accesses)