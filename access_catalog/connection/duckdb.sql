drop schema if exists %(schema)s cascade;
create schema %(schema)s;
use %(schema)s;


drop table if exists services;
create table services (
	__start			timestamp 				default (now()),
	__final			timestamp,
	uuid			uuid					default (uuid()),
	name			varchar(200),
	"desc"			varchar(200),
	icon			varchar(200)			default ('https://emojicdn.elk.sh/⚙️'),
	tags			varchar[],		
	properties		struct(__link varchar)
);
insert into services(name, "desc", icon, tags, properties) 
values (
    'Loginom', 
	'Аналитическая low-code платформа, позволяющая проводить анализ данных без программирования.', 
	'{static}/service_loginom.png', 
	['Аналитика'], 
	{'__link': 'https://loginom.ru'}
) , (
    'Proceset', 'Аналитическая система для сбора и загрузки данных, проведения исследований.', 
	'{static}/service_proceset.png', 
	['Аналитика'],
	{'__link': 'https://infomaximum.ru/product'}
) , (
    'OpenMetadata', 
	'Универсальная открытая платформа для управления метаданными.', 
	'{static}/service_openmetadata.png', 
	['Метаданные', 'OMD'],
	{'__link': 'https://open-metadata.org'}
) , (
    'Visiology', 
	'Cистема бизнес-аналитики для создания визуальных представлений больших массивов данных в интуитивно понятном виде.', 
	'{static}/service_visiology.png', 
	['Аналитика'], 
	{'__link': 'https://ru.visiology.su'}
) , (
    'Каталог сервисных доступов', 
	'Цифровой каталог для управления доступами к внутренним сервисам платформы.', 
	'{static}/service_access_catalog.png', 
	['Аналитика'], 
	{'__link': null}
) , (
    'Clickhouse', 
	'Cтолбцовая система управления базами данных для онлайн-обработки аналитических запросов.', 
	'{static}/service_clickhouse.png', 
	[], 
	{'__link': null}
) , (
    'Сервер', 
	null, 
	'{static}/service_ubuntu.png', 
	[], 
	{'__link': null}
) , (
    'Gitlab', 
	'Система управления репозиториями Git с собственной вики, системой отслеживания ошибок, CI/CD пайплайном и другими функциями.', 
	'{static}/service_gitlab.png', 
	[], 
	{'__link': 'https://about.gitlab.com'}
);


drop table if exists projects;  
create table projects (
	__start			timestamp		default (now()),
	__final			timestamp		default (null),
	uuid			uuid			default (uuid()),
	name			varchar(200),
	"desc"			varchar(200),
	icon			varchar(200)	default ('https://emojicdn.elk.sh/📁'),
	tags			varchar[],
	properties		struct(__link varchar)
);
insert into projects(name, icon, "desc") 
values (
    'Матпотоки', 'https://emojicdn.elk.sh/💸', 'Проект направлен на ...'
) , (
    'Лояльность', 'https://emojicdn.elk.sh/🛢️', 'Проект направлен на ...'
) , (
    'Чат-бот', 'https://emojicdn.elk.sh/🤖', 'Проект направлен на ...'
) , (
    'Витрины', 'https://emojicdn.elk.sh/🚀', 'Проект направлен на ...'
);


drop table if exists roles;  
create table roles (
	__start			datetime		default (now()),
	__final			datetime		default (null),
	uuid			uuid			default (uuid()),
	name			varchar(200),
	"desc"			varchar(200),
	icon			varchar(200)	default ('https://emojicdn.elk.sh/☑️'),
	tags			varchar[],
	properties		struct(Привелегии varchar)
);
insert into roles (name, "desc", icon, properties) 
values (
	'Автор', 'Право администрирования платформой.', 'https://emojicdn.elk.sh/🗝️', '{"Привелегии": "Все привелегии"}'
) , (
	'Разработчик', 'Право редактирования содержимого платформы.', 'https://emojicdn.elk.sh/🛠️', '{"Привелегии": "Редактор + удаление процессов"}'
) , (
	'Редактор', 'Право редактирования содержимого платформы.', 'https://emojicdn.elk.sh/🖋️', '{"Привелегии": "Читатель + изменение процессов"}'
) , (
	'Читатель', 'Право ознакомления с платформой.', 'https://emojicdn.elk.sh/🔎', '{"Привелегии": "мониторинг состояния процессов"}'
);


drop table if exists users;  
create table users (
	__start			datetime		default (now()),
	__final			datetime		default (null),
	uuid			uuid			default (uuid()),
	name			varchar(200),
	"desc"			varchar(200),
	icon			varchar(200)	default ('https://emojicdn.elk.sh/👽'),
	tags			varchar[],
	properties		struct(__login varchar, __password_hash varchar, должность varchar, организация varchar, почта varchar, телефон varchar)
);
insert into users (name, icon, properties, tags)
values (
	'Иванов Иван Иванович', 
	'https://emojicdn.elk.sh/🏋️‍♂️️', 
	{'__login': 'ivanovii', '__password_hash': 'b59c67bf196a4758191e42f76670ceba', 'должность': 'эксперт', 'организация': 'ООО', 'почта': 'IvanovII@ooo.ru', 'телефон': '999-999-99-96'},
	['DE']
), (
	'Ольгина Ольга Олеговна', 
	'https://emojicdn.elk.sh/🚴‍♂️️', 
	{'__login': 'olginaoo', '__password_hash': 'b59c67bf196a4758191e42f76670ceba', 'должность': 'эксперт', 'организация': 'ООО', 'почта': 'OlginaOO@ooo.ru', 'телефон': '999-999-99-97'},
	['DE']
), (
	'Петров Петр Петрович', 
	'https://emojicdn.elk.sh/⛷️️', 
	{'__login': 'petrovpp', '__password_hash': 'b59c67bf196a4758191e42f76670ceba', 'должность': 'эксперт', 'организация': 'ООО', 'почта': 'PertovPP@ooo.ru', 'телефон': '999-999-99-98'},
	['Аналитика']
), (
	'Сергеев Сергей Сергеевич',
	'https://emojicdn.elk.sh/🧘🏻️️',
	{'__login': 'sergeevss', '__password_hash': 'b59c67bf196a4758191e42f76670ceba', 'должность': 'эксперт', 'организация': 'ООО', 'почта': 'SergeevSS@ooo.ru', 'телефон': '999-999-99-99'},
	['Кадры']
);


drop table if exists %(schema)s.accesses;
create table %(schema)s.accesses (
	__start			datetime		default (now()),
	__final			datetime		default (null),
	service_uuid 	uuid,
	project_uuid 	uuid,
	role_uuid 		uuid,
	user_uuid 		uuid,
	status			varchar(36),
	creator			varchar(36),
	comment			varchar(200)
);
insert into %(schema)s.accesses by name
select now() as __start
	 , null as __final
	 , s.uuid as service_uuid
	 , p.uuid as project_uuid
	 , r.uuid as role_uuid
	 , u.uuid as user_uuid
	 , 'Готово' as status
	 , lag(n.name) over (partition by s.uuid order by random()) as creator
	 , null as comment
from %(schema)s.users n
full join %(schema)s.services s on true
full join %(schema)s.projects p on true
full join %(schema)s.roles r on true
full join %(schema)s.users u on true
order by random()
limit 5;
insert into %(schema)s.accesses by name
select now() as __start
	 , null as __final
	 , s.uuid as service_uuid
	 , p.uuid as project_uuid
	 , r.uuid as role_uuid
	 , u.uuid as user_uuid
	 , 'Готово' as status
	 , lag(n.name) over (partition by s.uuid order by random()) as creator
	 , null as comment
from %(schema)s.users n
full join %(schema)s.services s on true
full join %(schema)s.projects p on true
full join %(schema)s.roles r on true
full join %(schema)s.users u on true
order by random()
limit 5;
