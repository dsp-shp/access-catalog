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
if DIALECT == 'duckdb': 
    ### костыль из-за невозможности передать абсолютный путь в duckdb.connect()
    CREDENTIALS['database'] = '/'.join(['..']*20) + __path + '/' + CREDENTIALS['database']

from .. import connection
sql = connection.Connection(**CREDENTIALS)

try:
    check, = sql.execute(connection.Connection.select_schema % {'schema': SCHEMA})
    if [*check.values()][0] < 1:
        with open('%s/sample.json' % __path, 'r') as file:
            connection.prepare_database(sql, json.loads(file.read()), SCHEMA)
except Exception as e:
    raise(e)
finally:
    del connection, sql

### Чтение CSS стилей
with open('%s/assets/base.css' % __path, 'r') as file:
    STYLESHEET: str = file.read()

### Чтение JS скриптов
with open('%s/scripts/base.js' % __path, 'r') as file:
    SCRIPTS: str = file.read()


### Дефолтные структуры 
DEFAULT_CARDS: dict[str, dict[str, bool]] = {x['type']: {} for x in DEFAULT_ENTITIES}
DEFAULT_FILTERS: str = json.dumps({x['type']: [] for x in DEFAULT_ENTITIES}, ensure_ascii=False)
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