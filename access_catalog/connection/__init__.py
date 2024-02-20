""" Коннекторы 

При необходимости дополняйте модуль собственными коннекторами, например:
    ### from .duckdb import Connection, prepare_database
    from .mysql import Connection, prepare_database

"""
from .duckdb import Connection, prepare_database