# from contextlib import contextmanager
# from json import loads
# from mysql.connector import connect, FieldType, MySQLConnection
# import typing as t


# class Connection:
#     """ Коннектор к MySQL хранилищу данных """

#     select_schema: str = """
#         select count(*)
#         from information_schema.schemata
#         where schema_name = %(schema)s
#     """

#     select_user: str = """
#         select * 
#         from %(schema)s.users 
#         where __final is null 
#             and trim('"' from JSON_EXTRACT(properties, '$.__login')) = %(username)s
#         limit 1
#     """
    
#     revoke_access: str = """
#         delete from %(schema)s.accesses where true 
#             and service_uuid = '%(service_uuid)s'
#             and project_uuid = '%(project_uuid)s'
#             and role_uuid = '%(role_uuid)s'
#             and user_uuid = '%(user_uuid)s'
#     """
    
#     grant_access: str = """"""
    
#     select_access: str = """
#         select *, __start as start_date from %(schema)s.accesses where True 
#             and service_uuid = '%(service_uuid)s'
#             and project_uuid = '%(project_uuid)s'
#             and role_uuid = '%(role_uuid)s'
#             and user_uuid = '%(user_uuid)s'
#         order by __start desc
#     """
    
#     filter_access: str = """
#         select cast(concat('[', coalesce(group_concat(distinct CONCAT('"', s.name, '"')), ''), ']') as json) as services
#             , cast(concat('[', coalesce(group_concat(distinct CONCAT('"', p.name, '"')), ''), ']') as json) as projects
#             , cast(concat('[', coalesce(group_concat(distinct CONCAT('"', r.name, '"')), ''), ']') as json) as roles
#             , cast(concat('[', coalesce(group_concat(distinct CONCAT('"', u.name, '"')), ''), ']') as json) as users
#         from %(schema)s.accesses a
#         left join %(schema)s.services s on a.service_uuid = s.uuid and s.__final is null 
#         left join %(schema)s.projects p on a.project_uuid = p.uuid and p.__final is null
#         left join %(schema)s.roles r on a.role_uuid = r.uuid and r.__final is null
#         left join %(schema)s.users u on a.user_uuid = u.uuid and u.__final is null
#         where a.__final is null and %(where)s;
#     """
    
#     select_entity: str = """
#         select * from %(schema)s.%(table)s where __final is null order by name
#     """

#     def __init__(
#         self, 
#         user: str,
#         password: str,
#         host: str = '127.0.0.1',
#         port: int = 3306,
#         database: str = 'mysql',
#         **kwargs
#     ) -> None:
#         self.user = user
#         self.password = password
#         self.host = host
#         self.port = port
#         self.database = database

#     @contextmanager
#     def __connect__(self) -> t.Generator[MySQLConnection, None, None]:
#         cnx = connect(
#             user=self.user,
#             password=self.password,
#             host=self.host,
#             port=self.port,
#             database=self.database
#         )
#         try:
#             yield cnx # type: ignore
#         finally:
#             cnx.commit()
#             cnx.close()

#     def execute(
#         self, 
#         query: str,
#         params: dict = {},
#         handle: bool = False
#     ) -> list[dict]:
#         """ Выполнение запроса

#         Параметры:
#             query (str): текстовый запрос
#             params (dict): параметры выполнения
        
#         Возвращает: 
#             tuple[t.Sequence, dict]: кортеж из данных в виде коллекции коллекций
#                 и маппинга наименования атрибута на его тип
        
#         """
#         try:
#             with self.__connect__() as cnx:
#                 with cnx.cursor() as cursor:
#                     cursor.execute(query, params)
#                     fetched: list = cursor.fetchall()
#                     desc: list = cursor.description # type: ignore
                    
#                     if not fetched or not desc:
#                         return [{}]
#                     cols: dict = {x[0]: FieldType.get_info(x[1]) for x in desc}
#                     data = fetched
                    
#                     return [{
#                         k: (
#                             loads(v) if cols[k] == 'JSON' else v
#                         ) for k,v in x.items() if not k.startswith('__')
#                     } for x in data]
        
#         except Exception as e:
#             if handle == True:
#                 return [{}]
#             raise(e)

#     def insert(
#         self,
#         data: list[dict[str, t.Any]], 
#         schema: str,
#         table: str
#     ) -> None:
#         """ Вставка данных в хранилище """
#         query = """
#             insert into %(schema)s.%(table)s (%(columns)s)
#             values (%(values)s)
#         """ % {
#             'schema': schema,
#             'table': table,
#             'columns': ', '.join([f'`{x}`' for x in data[0].keys()]),
#             'values': ', '.join(['%s']*len(data[0]))
#         }
        
#         with self.__connect__() as cnx:
#             with cnx.cursor() as cursor:
#                 cursor.executemany(query, [[*x.values()] for x in data])

