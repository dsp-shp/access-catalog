from nicegui import app, events, ui
import json
import typing as t
import yaml


__path, = __import__(__name__).__path__
STATIC: str = '%s/static' % __path


### Чтение конфигурационного файла
with open('%s/config.yaml' % __path, 'r') as file:
    __config: dict[str, t.Any] = yaml.safe_load(file)
    
    DIALECT: str = __config['database']['dialect']
    CREDENTIALS: dict[str, t.Any] = __config['database']['credentials']
    SCHEMA: str = __config['database']['schema']
    
    DEFAULT_ENTITIES: list[dict[str, str]] = __config['ui']['entities']
    
    TITLE: str = __config['server']['title']
    HOST: str = __config['server']['host']
    PORT: int = __config['server']['port']
    FAVICON: str = '%s/favicon.ico' % STATIC

### Чтение DDL-скриптов и инициализация базы, если последняя не инициализирована
from .. import connection
from inspect import getmembers

if DIALECT == 'duckdb':
    CREDENTIALS['database'] = '/'.join(['..']*20) + __path + '/' + CREDENTIALS['database']

try:
    Connection: t.Any = dict(getmembers(connection))['%s_Connection' % DIALECT]
    sql = Connection(**CREDENTIALS)
    check, = sql.execute(Connection.select_schema % {'schema': SCHEMA})
    if True: # [*check.values()][0] < 1:
        with open('%s/connection/%s.sql' % (__path, DIALECT), 'r') as file:
            ddl: str = file.read()
        with sql.__connect__() as cnx:
            cnx.executemany(ddl % {'schema': SCHEMA})
except KeyError:
    raise Exception('Необходимый модуль для подключения к "%s" отсутствует' % DIALECT)
except Exception as e:
    raise(e)
finally:
    del getmembers, connection, sql

### Чтение CSS стилей
with open('%s/assets/base.css' % __path, 'r') as file:
    STYLESHEET: str = file.read()

### Чтение JS скриптов
with open('%s/scripts/base.js' % __path, 'r') as file:
    SCRIPTS: str = file.read()


### Дефолтные структуры 
DEFAULT_CARDS: dict[str, dict[str, bool]] = {x['name']: {} for x in DEFAULT_ENTITIES}
DEFAULT_FILTERS: str = json.dumps({x['name']: [] for x in DEFAULT_ENTITIES}, ensure_ascii=False)
DEFAULT_SUGGESTS: str = '%s' % DEFAULT_FILTERS


### Общие функции
def search(event: events.ValueChangeEventArguments, cards: list) -> None:
    """ Search-as-you-type """
    
    for x in cards:
        if event.value.lower() in x.name.lower(): # and e.value != '':
            x.style('display: flex;')
        else:
            x.style('display: none;')

def logout() -> None:
    """ Завершение сессии """
    app.storage.user.update({
        'username': app.storage.user.get('username'),
        'authenticated': False
    })
    ui.open('http://127.0.0.1:%s' % PORT, new_tab=False)

def fix_icon(s: str) -> str:
    """ Корректировка URL-строки для https://emojicdn.com """
    return s if not '/emojicdn.' in s else '/'.join([*(p := s.split('/'))[:-1], p[-1][:1]])

def ensure_struct(s: t.Any) -> t.Any:
    """ Функция конвертации строки в структуру """
    return json.loads(s) if isinstance(s, str) else s