from contextlib import contextmanager
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
                 , properties->>'__login' as login
                 , properties->>'корп. почта' as corp_mail
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

    def __init__(self, *args, **kwargs) -> None:
        self.args: tuple[t.Any] = args
        self.kwargs: dict[str, t.Any] = kwargs

    @contextmanager
    def __connect__(self) -> t.Generator[duckdb.DuckDBPyConnection, None, None]:
        cnx: duckdb.DuckDBPyConnection = duckdb.connect(*self.args, **self.kwargs)
        try:
            yield cnx
        finally:
            cnx.close()

    def execute(
        self, 
        query: str, 
        params: dict = {}, 
        handle: bool = False
    ) -> list[dict]:
        """ Выполнение запроса

        Параметры:
            query (str): текстовый запрос
            params (dict): параметры выполнения
        
        Возвращает: 
            tuple[t.Sequence, dict]: кортеж из данных в виде коллекции коллекций
                и маппинга наименования атрибута на его тип
        
        """
        try:
            with self.__connect__() as cnx:
                fetched: duckdb.DuckDBPyRelation = cnx.sql(query, params=params)
        
                if not fetched or not fetched.columns:
                    return [{}]
                cols: dict = dict(zip(fetched.columns, fetched.types))
                data: list = [dict(zip(cols.keys(), x)) for x in fetched.fetchall()]
        
                return [{
                    k: (
                        loads(v) if cols[k] == 'JSON' else v
                    ) for k,v in x.items() if not k.startswith('__')
                } for x in data]
        
        except Exception as e:
            if handle == True:
                return [{}]
            raise Exception('%s\n%s' % (e, query % params,))
    
    def insert(
        self,
        data: list[dict[str, t.Any]], 
        schema: str,
        table: str
    ) -> None:
        """ Вставка данных в хранилище """
        query = """
            insert into %(schema)s.%(table)s (%(columns)s)
            values %(values)s
        """ % {
            'schema': schema,
            'table': table,
            'columns': ', '.join([f'"{x}"' for x in data[0].keys()]),
            'values': ', '.join(['({})'.format(', '.join(['?']*len(data[0])))]*len(data))
        }

        with self.__connect__() as cnx:
            cnx.executemany(query, [[*x.values()] for x in data])
