from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
import hashlib
import html
import json
import mimetypes
import secrets
import smtplib
import sqlite3
import sys
from datetime import datetime
from email.mime.text import MIMEText


APP_DIR   = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
DB_PATH   = APP_DIR / "ecosort.db"
HOST      = "127.0.0.1"
PORT      = 8890
PAGE_SIZE = 10

SMTP_HOST = ""
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASS = ""

QUIZ_QUESTIONS = [
    {"id":"q1","text_kz":"Пластик бөтелке қанша жыл ыдырайды?","text_ru":"Сколько лет разлагается пластиковая бутылка?",
     "options_kz":["10–20 жыл","50–100 жыл","450 жылға дейін","Ешқашан"],"options_ru":["10–20 лет","50–100 лет","До 450 лет","Никогда"],"correct":2},
    {"id":"q2","text_kz":"Пайдаланылған батарейкаларды қайда тапсыру керек?","text_ru":"Куда нужно сдавать использованные батарейки?",
     "options_kz":["Қарапайым қоқысқа","Арнайы жәшіктерге","Компостқа","Жерге көму"],"options_ru":["В обычный мусор","В специальные боксы","В компост","Закопать в землю"],"correct":1},
    {"id":"q3","text_kz":"Қандай қалдықты компосттауға болады?","text_ru":"Какой вид отходов можно компостировать?",
     "options_kz":["Пластик пакеттер","Шыны бөтелкелер","Көкөніс қабығы","Металл банкалар"],"options_ru":["Пластиковые пакеты","Стеклянные бутылки","Овощные очистки","Металлические банки"],"correct":2},
    {"id":"q4","text_kz":"Бөтелкені тапсыру алдында не істеу керек?","text_ru":"Что нужно сделать с бутылкой перед сдачей?",
     "options_kz":["Бөлшектеу","Жуып, сығу","Өртеу","Ештеңе"],"options_ru":["Разбить","Промыть и сжать","Сжечь","Ничего"],"correct":1},
    {"id":"q5","text_kz":"Органикалық қалдықтар полигонда қандай газ бөледі?","text_ru":"Какой газ выделяют органические отходы на полигонах?",
     "options_kz":["Оттегі","Азот","Метан","Сутегі"],"options_ru":["Кислород","Азот","Метан","Водород"],"correct":2},
]

# ─── Переводы ────────────────────────────────────────────────────────────────
T = {
    'kz': {
        'nav_home':'Басты бет','nav_map':'Карта','nav_events':'Акциялар',
        'nav_cards':'Карталар','nav_encyclopedia':'Энциклопедия',
        'nav_quiz':'Тест','nav_support':'Сұраулар',
        'register':'Тіркелу','login':'Кіру','logout':'Шығу',
        'cabinet':'Кабинет','admin_label':'Әкімші',
        'visitor':'Қонақ','user_prefix':'Пайдаланушы: ',
        'lang_switch':'Русский',
        # Герой
        'hero_eyebrow':'Жаңа деңгейдегі экологиялық платформа',
        'hero_slogan':'«Таза табиғат - болашаққа аманат»',
        'hero_text':'Қалдықтарды қабылдау нүктелерін табуға, акцияларға қатысуға және экологиялық сауаттылықты арттыруға арналған платформа.',
        'hero_btn1':'Тіркелу','hero_btn2':'Қатысу',
        'live_counter_label':'Базада қазір','live_counter_small':'шараларға қатысу өтінімдері',
        # Статистика
        'stat_users':'пайдаланушы','stat_events':'акция',
        'stat_joins':'қатысу','stat_requests':'сұрау',
        # Разделы
        'site_sections_eyebrow':'Сайт құрылымы',
        'site_sections_title':'Экологиялық өмір салтына арналған барлық құралдар бір жерде',
        'how_eyebrow':'Қалай жұмыс істейді','how_title':'Тіркелуден бастап қатысуға дейінгі жол',
        'step1_title':'Тіркелу','step1_text':'Қатысушы аккаунт жасайды және жеке кабинет алады.',
        'step2_title':'Акцияны таңдау','step2_text':'Шаралар бетін ашып, қолайлы іс-шараны таңдайды.',
        'step3_title':'Өтінім','step3_text':'«Қатысу» батырмасын басады — өтінім тарихында пайда болады.',
        'step4_title':'Команда жауабы','step4_text':'EcoSort командасы өтінімдерді қарап, пайдаланушыларға көмектеседі.',
        'quicklinks_eyebrow':'Жылдам бөлімдер','quicklinks_title':'EcoSort негізгі мүмкіндіктері',
        'feature1_title':'Жұмыс картасы','feature1_sub':'OpenStreetMap-тегі қабылдау нүктелері',
        'feature2_title':'Акциялар','feature2_sub':'Шаралар және пайдаланушыларды жазу',
        'feature3_title':'Карталар','feature3_sub':'Пайдалы экологиялық материалдар',
        'feature4_title':'Сұраулар','feature4_sub':'Өтініштер және қолдау жауаптары',
        'upcoming_eyebrow':'Жақындағы шаралар','upcoming_title':'Жақындағы экологиялық шаралар',
        'cards_eyebrow':'Пайдалы карталар','cards_title':'Пайдалы экологиялық материалдар',
        'impact_eyebrow':'Нәтижелер мен серіктестік','impact_title':'EcoSort — қоғамдық экологиялық платформа',
        'impact1':'қалдық қайта өңдеуге жіберілді','impact2':'серіктес нүктелер мен ұйымдар',
        'impact3':'экологиялық энциклопедия санаттары','impact4':'өтініш нысаны мен кері байланыс',
        'photo_eyebrow':'Фотогалерея','photo_title':'Бірге тазалық сақтаймыз',
        'photo1_title':'Таза жағалау',
        'photo1_text':'Волонтерлар жыл сайын мыңдаған килограмм қоқысты жинайды. EcoSort субботниктері арқылы жағалаулар, саябақтар және тұрғын аудандар тазарады. Әр қатысушы табиғатты қорғауға нақты үлес қосады.',
        'photo2_title':'Ағаш отырғызу',
        'photo2_text':'Жасыл қалалар болашақ ұрпаққа берілетін мұра. EcoSort акциялары аясында мектептер мен тұрғын үйлер маңына жүздеген саженец отырғызылады. Бір ағаш — бір жылда 22 кг СО₂ сіңіреді.',
        'photo3_title':'Қайта өңдеу',
        'photo3_text':'Дұрыс сортталған қалдық ресурсқа айналады. Пластик, қағаз, шыны және металл — бөлек жиналса, 70%-ға дейін қайта пайдалануға жіберіледі. EcoSort картасы арқылы жақын қабылдау нүктесін табыңыз.',
        'photo4_title':'Экологиялық білім',
        'photo4_text':'Мектептер мен отбасылар бірге сауатты болады. EcoSort тесттері мен энциклопедиясы арқылы балалар мен ересектер қалдықтарды дұрыс сортталуды үйренеді. Білім — экологиялық өзгерістің негізі.',
        # Акции
        'events_eyebrow':'Акциялар мен шаралар','events_title':'Жақындағы экологиялық шаралар',
        'events_subtitle':'Қызықты акцияны таңдап, қатысуға өтінім жіберіңіз.',
        'events_search':'Акциялар бойынша іздеу...','events_empty':'Акциялар табылмады.',
        'btn_join':'Қатысу','btn_login_join':'Кіру','btn_find':'Табу','btn_reset':'Тазалау',
        'btn_delete':'Жою','btn_accept':'Қабылдау','btn_reject':'Бас тарту',
        'btn_reply':'Жауап беру','btn_send':'Жіберу','btn_complete':'Аяқтау','btn_activate':'Белсендіру',
        'already_joined':'Қатысасыз','event_done':'Акция аяқталды','users_only':'Тек пайдаланушыларға',
        'pending':'Қаралуда ⏳','accepted':'Қабылданды ✓','rejected':'Қабылданбады ✗',
        # Карточки
        'cards_page_eyebrow':'Ақпараттық карталар','cards_page_title':'Пайдалы экологиялық материалдар',
        'cards_search':'Карталар бойынша іздеу...','cards_empty':'Карталар табылмады.',
        # Профиль
        'profile_eyebrow':'Пайдаланушының жеке кабинеті',
        'profile_title':'Профиль, қатысу тарихы және жетістіктер',
        'profile_history':'Қатысу тарихы','profile_badges':'Жетістіктер',
        'profile_no_joins':'Қатысулар жоқ. Акция таңдап «Қатысу» батырмасын басыңыз.',
        'profile_test_title':'Экологиялық сауаттылық тесті',
        'profile_test_desc':'сұраққа жауап беріп, нәтижені жеке кабинетте сақтаңыз.',
        'profile_test_btn':'Тест тапсыру','profile_results':'Тест нәтижелері',
        'profile_no_tests':'Тест нәтижелері жоқ.',
        'profile_support_title':'Менің сұраулар','profile_support_empty':'Сұрау жоқ.',
        'badge_new':'Эко-жаңадан','badge_joined':'Акция қатысушысы',
        'badge_3plus':'Табиғат қорғаушы','badge_test':'Эко-сауаттылық',
        'profile_need_login_title':'Алдымен кіріңіз немесе тіркеліңіз',
        'profile_need_login_text':'Кіргеннен кейін профиль, қатысу тарихы және тест нәтижелері пайда болады.',
        # Поддержка
        'support_eyebrow':'Сұраулар мен қолдау','support_title':'Пайдаланушының өтініш нысаны',
        'support_subtitle':'Әр сұрау support_requests кестесіне сақталады және әкімшіге көрінеді.',
        'support_form_title':'Сұрау жіберу','support_name':'Ат','support_email':'Email',
        'support_message':'Хабарлама','support_send':'Сұрау жіберу',
        'support_how_title':'Сұраулар қалай өңделеді',
        'support_how1':'1. Пайдаланушы өтінім жібереді.',
        'support_how2':'2. Сұрау әкімші панелінде пайда болады.',
        'support_how3':'3. Әкімші жауап береді.',
        'thread_title':'Хат алмасу','thread_send':'Хабарлама жіберу',
        'thread_admin':'Әкімші','thread_you':'Сіз',
        'admin_reply':'Жауап:','view_thread':'Жауапты көру',
        # Карта
        'map_eyebrow':'Қабылдау нүктелерінің картасы',
        'map_title':'Қалдықтарды қабылдау нүктелері',
        'map_subtitle':'Картада қалдықтарды қабылдау нүктелері белгіленген. Қалаңызды және қалдық түрін таңдаңыз.',
        'map_city':'Қала','map_all_cities':'Барлық қалалар',
        # Энциклопедия
        'encyclopedia_eyebrow':'Энциклопедия','encyclopedia_title':'Қалдықтар туралы білім базасы',
        'influence':'Әсері:','recycling':'Өңдеу:',
        # Квиз
        'quiz_eyebrow':'Экологиялық сауаттылық тесті',
        'quiz_title':'Білімдеріңізді тексеріңіз',
        'quiz_subtitle':'сұраққа жауап беріп, нәтижеңізді біліңіз.',
        'quiz_submit':'Нәтижені алу',
        'quiz_need_login':'Тест тапсыру үшін кіріңіз',
        # Админ
        'admin_eyebrow':'Әкімші кабинеті','admin_title':'Сайт пен деректер базасын басқару',
        'admin_add_event':'Акция қосу','admin_add_card':'Карта қосу',
        'admin_field_title':'Атауы','admin_field_type':'Түрі','admin_field_date':'Күні',
        'admin_field_city':'Қала','admin_field_desc':'Сипаттама',
        'admin_field_cat':'Санат','admin_field_text':'Мәтін',
        'admin_joins':'Қатысу өтінімдері','admin_pending':'Күтудегі өтінімдер',
        'admin_events':'Ағымдағы акциялар','admin_cards':'Ақпараттық карталар',
        'admin_requests':'Пайдаланушы сұраулары',
        'col_name':'Ат','col_email':'Email','col_event':'Акция',
        'col_date':'Күні','col_action':'Әрекет','col_status':'Мәртебе',
        'col_type':'Түрі','col_category':'Санат','col_title':'Атауы',
        'col_message':'Хабарлама','search_events':'Акциялар бойынша іздеу...',
        'search_cards':'Карталар бойынша іздеу...','search_requests':'Сұраулар бойынша іздеу...',
        'no_joins':'Өтінімдер жоқ.','no_events':'Акциялар жоқ.',
        'no_cards':'Карталар жоқ.','no_requests':'Сұраулар жоқ.',
        'added_event':'Акция деректер базасына қосылды.','added_card':'Карта қосылды.',
        'deleted_event':'Акция жойылды.','deleted_card':'Карта жойылды.',
        'fill_all':'Барлық өрістерді толтырыңыз.',
        'admin_only_title':'Тек әкімшіге қол жетімді',
        'admin_only_text':'admin@ecosort.kz / admin123 ретінде кіріңіз.',
        'admin_users':'Пайдаланушылар','col_reg_date':'Тіркелу күні',
        'col_joins':'Қатысу','col_status_user':'Мәртебе',
        'user_active':'Белсенді','user_banned':'Бұғатталған',
        'btn_ban':'Бұғаттау','btn_unban':'Бұғатты алу','btn_reset_acc':'Тарихты тазалау',
        'banned_notice':'Аккаунтыңыз бұғатталған. Подробнее: hello@ecosort.kz',
        'no_users':'Пайдаланушылар жоқ.',
        'search_users':'Пайдаланушылар бойынша іздеу...',
        # Сброс пароля
        'forgot_eyebrow':'Кіруді қалпына келтіру','forgot_title':'Құпия сөзді сыфырлау',
        'forgot_text':'Аккаунтыңыздың email-ін енгізіңіз. Сыфырлау сілтемесін жіберейік.',
        'forgot_send':'Сілтеме жіберу',
        'reset_eyebrow':'Жаңа құпия сөз','reset_title':'Жаңа құпия сөз ойлап табыңыз',
        'reset_new':'Жаңа құпия сөз','reset_confirm':'Қайталаңыз','reset_save':'Сақтау',
        'footer_about':'EcoSort — қалдықтарды қабылдау нүктелерін табуға, акцияларға қатысуға және экологиялық мәдениетті дамытуға арналған платформа.',
        'footer_write':'Бізге жазыңыз','footer_address':'Мекенжайымыз','footer_hours':'Жұмыс уақыты',
        'search':'Іздеу','page_of':'бет',
    },
    'ru': {
        'nav_home':'Главная','nav_map':'Карта','nav_events':'Акции',
        'nav_cards':'Карточки','nav_encyclopedia':'Энциклопедия',
        'nav_quiz':'Тест','nav_support':'Запросы',
        'register':'Регистрация','login':'Вход','logout':'Выйти',
        'cabinet':'Кабинет','admin_label':'Админ',
        'visitor':'Посетитель','user_prefix':'Пользователь: ',
        'lang_switch':'Қазақша',
        'hero_eyebrow':'Экологическая платформа нового уровня',
        'hero_slogan':'«Чистая природа — наказ будущим поколениям»',
        'hero_text':'Экологическая платформа для поиска пунктов приёма отходов, участия в акциях и повышения экологической грамотности.',
        'hero_btn1':'Зарегистрироваться','hero_btn2':'Принять участие',
        'live_counter_label':'В базе сейчас','live_counter_small':'заявок на участие в мероприятиях',
        'stat_users':'пользователей','stat_events':'акций','stat_joins':'участий','stat_requests':'запросов',
        'site_sections_eyebrow':'Структура сайта',
        'site_sections_title':'Все инструменты для экологичного образа жизни в одном месте',
        'how_eyebrow':'Как это работает','how_title':'Путь пользователя от регистрации до участия',
        'step1_title':'Регистрация','step1_text':'Участник создает аккаунт и получает личный кабинет.',
        'step2_title':'Выбор акции','step2_text':'Открывает страницу мероприятий и выбирает событие.',
        'step3_title':'Заявка','step3_text':'Нажимает «Принять участие», заявка появляется в истории.',
        'step4_title':'Ответ команды','step4_text':'Команда EcoSort видит заявки и помогает пользователям.',
        'quicklinks_eyebrow':'Быстрые разделы','quicklinks_title':'Основные возможности EcoSort',
        'feature1_title':'Рабочая карта','feature1_sub':'Пункты приема на OpenStreetMap',
        'feature2_title':'Акции','feature2_sub':'Мероприятия и запись пользователей',
        'feature3_title':'Карточки','feature3_sub':'Полезные экологические материалы',
        'feature4_title':'Запросы','feature4_sub':'Обращения и ответы поддержки',
        'upcoming_eyebrow':'Ближайшие мероприятия','upcoming_title':'Ближайшие экологические мероприятия',
        'cards_eyebrow':'Полезные карточки','cards_title':'Полезные экологические материалы',
        'impact_eyebrow':'Результаты и партнёрство','impact_title':'EcoSort — общественная экологическая платформа',
        'impact1':'отходов отправлено на переработку','impact2':'партнёрских пункта и организации',
        'impact3':'категорий экологической энциклопедии','impact4':'форма запросов и обратной связи',
        'photo_eyebrow':'Фотогалерея','photo_title':'Вместе сохраняем чистоту',
        'photo1_title':'Чистый берег',
        'photo1_text':'Волонтёры EcoSort ежегодно собирают тысячи килограммов мусора на берегах и в парках. Каждый субботник — это реальный вклад в чистоту природы. Присоединяйтесь к ближайшей акции и сделайте мир чище.',
        'photo2_title':'Посадка деревьев',
        'photo2_text':'Зелёные города — наследие для будущих поколений. В рамках акций EcoSort высаживаются сотни саженцев у школ и жилых домов. Одно дерево поглощает до 22 кг СО₂ в год и служит десятилетиями.',
        'photo3_title':'Переработка',
        'photo3_text':'Правильно отсортированный мусор становится ресурсом, а не загрязнением. Пластик, бумага, стекло и металл при раздельном сборе перерабатываются на 70%. Найдите ближайший пункт приёма на карте EcoSort.',
        'photo4_title':'Экологическое образование',
        'photo4_text':'Школы и семьи вместе учатся быть экологически ответственными. Тесты и энциклопедия EcoSort помогают детям и взрослым понять, как сортировать отходы и беречь природу. Знания — основа реальных изменений.',
        'events_eyebrow':'Акции и мероприятия','events_title':'Ближайшие экологические мероприятия',
        'events_subtitle':'Выберите интересную акцию и отправьте заявку на участие.',
        'events_search':'Поиск по акциям...','events_empty':'Акции не найдены.',
        'btn_join':'Принять участие','btn_login_join':'Войти для участия','btn_find':'Найти','btn_reset':'Сбросить',
        'btn_delete':'Удалить','btn_accept':'Принять','btn_reject':'Отклонить',
        'btn_reply':'Ответить','btn_send':'Отправить','btn_complete':'Завершить','btn_activate':'Активировать',
        'already_joined':'Вы участвуете','event_done':'Акция завершена','users_only':'Только для пользователей',
        'pending':'На рассмотрении ⏳','accepted':'Принято ✓','rejected':'Отклонено ✗',
        'cards_page_eyebrow':'Информационные карточки','cards_page_title':'Полезные экологические материалы',
        'cards_search':'Поиск по карточкам...','cards_empty':'Карточки не найдены.',
        'profile_eyebrow':'Личный кабинет пользователя',
        'profile_title':'Профиль, история участия и достижения',
        'profile_history':'История участия','profile_badges':'Достижения',
        'profile_no_joins':'Пока нет участий. Выберите акцию и нажмите «Принять участие».',
        'profile_test_title':'Тест на экологическую грамотность',
        'profile_test_desc':'вопросов и сохраните результат в личном кабинете.',
        'profile_test_btn':'Пройти тест','profile_results':'Результаты тестов',
        'profile_no_tests':'Результатов теста пока нет.',
        'profile_support_title':'Мои обращения','profile_support_empty':'Обращений нет.',
        'badge_new':'Эко-новичок','badge_joined':'Участник акции',
        'badge_3plus':'Защитник природы','badge_test':'Эко-грамотность',
        'profile_need_login_title':'Сначала войдите или зарегистрируйтесь',
        'profile_need_login_text':'После входа здесь появятся профиль, история участия и результаты тестов.',
        'support_eyebrow':'Запросы и поддержка','support_title':'Форма обращения пользователя',
        'support_subtitle':'Каждый запрос сохраняется и виден администратору.',
        'support_form_title':'Отправить запрос','support_name':'Имя','support_email':'Email',
        'support_message':'Сообщение','support_send':'Отправить запрос',
        'support_how_title':'Как обрабатываются запросы',
        'support_how1':'1. Пользователь отправляет обращение.',
        'support_how2':'2. Запрос появляется в админ-панели.',
        'support_how3':'3. Администратор отвечает.',
        'thread_title':'Переписка','thread_send':'Отправить сообщение',
        'thread_admin':'Администратор','thread_you':'Вы',
        'admin_reply':'Ответ:','view_thread':'Открыть чат',
        'map_eyebrow':'Карта пунктов приема','map_title':'Пункты приема отходов',
        'map_subtitle':'На карте отмечены пункты приёма. Выберите город и тип отходов.',
        'map_city':'Город','map_all_cities':'Все города',
        'encyclopedia_eyebrow':'Энциклопедия','encyclopedia_title':'База знаний по отходам',
        'influence':'Влияние:','recycling':'Переработка:',
        'quiz_eyebrow':'Тест на экологическую грамотность',
        'quiz_title':'Проверьте свои знания',
        'quiz_subtitle':'вопросов и узнайте свой результат.',
        'quiz_submit':'Получить результат',
        'quiz_need_login':'Войдите, чтобы пройти тест',
        'admin_eyebrow':'Кабинет администратора','admin_title':'Управление сайтом и базой данных',
        'admin_add_event':'Добавить акцию','admin_add_card':'Добавить карточку',
        'admin_field_title':'Название','admin_field_type':'Тип','admin_field_date':'Дата',
        'admin_field_city':'Город','admin_field_desc':'Описание',
        'admin_field_cat':'Категория','admin_field_text':'Текст',
        'admin_joins':'Заявки на участие','admin_pending':'Ожидают решения',
        'admin_events':'Текущие акции','admin_cards':'Информационные карточки',
        'admin_requests':'Запросы пользователей',
        'col_name':'Имя','col_email':'Email','col_event':'Акция',
        'col_date':'Дата','col_action':'Действие','col_status':'Статус',
        'col_type':'Тип','col_category':'Категория','col_title':'Название',
        'col_message':'Сообщение','search_events':'Поиск по акциям...',
        'search_cards':'Поиск по карточкам...','search_requests':'Поиск по запросам...',
        'no_joins':'Заявок пока нет.','no_events':'Акций пока нет.',
        'no_cards':'Карточек пока нет.','no_requests':'Запросов пока нет.',
        'added_event':'Акция добавлена в базу данных.','added_card':'Карточка добавлена.',
        'deleted_event':'Акция удалена.','deleted_card':'Карточка удалена.',
        'fill_all':'Заполните все поля.',
        'admin_users':'Пользователи','col_reg_date':'Дата регистрации',
        'col_joins':'Участий','col_status_user':'Статус',
        'user_active':'Активен','user_banned':'Заблокирован',
        'btn_ban':'Заблокировать','btn_unban':'Разблокировать','btn_reset_acc':'Сбросить историю',
        'banned_notice':'Ваш аккаунт заблокирован. Подробнее: hello@ecosort.kz',
        'no_users':'Пользователей нет.',
        'search_users':'Поиск по пользователям...',
        'admin_only_title':'Доступ только для администратора',
        'admin_only_text':'Войдите как admin@ecosort.kz / admin123.',
        'forgot_eyebrow':'Восстановление доступа','forgot_title':'Сброс пароля',
        'forgot_text':'Введите email вашего аккаунта. Мы отправим ссылку для сброса пароля.',
        'forgot_send':'Отправить ссылку',
        'reset_eyebrow':'Новый пароль','reset_title':'Придумайте новый пароль',
        'reset_new':'Новый пароль','reset_confirm':'Повторите пароль','reset_save':'Сохранить',
        'footer_about':'EcoSort — платформа для поиска пунктов приёма отходов, участия в акциях и развития экологической культуры.',
        'footer_write':'Написать нам','footer_address':'Наш адрес','footer_hours':'Время работы',
        'search':'Поиск','page_of':'из',
    }
}

def t(key, lang='kz'):
    return T.get(lang, T['ru']).get(key, T['ru'].get(key, key))


# ─── База данных ──────────────────────────────────────────────────────────────

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def now():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return f"{salt}${digest.hex()}"

def check_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return password_hash(password, salt).split("$", 1)[1] == digest

def esc(value):
    return html.escape(str(value), quote=True)

def _try_alter(conn, sql):
    try:
        conn.execute(sql)
    except sqlite3.OperationalError:
        pass

def init_db():
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
              city TEXT NOT NULL, password_hash TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'user', created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
              sid TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
              token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL, event_type TEXT NOT NULL, event_date TEXT NOT NULL,
              city TEXT NOT NULL, description TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'upcoming', created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              category TEXT NOT NULL, title TEXT NOT NULL,
              body TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participants (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL, event_id INTEGER NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL,
              UNIQUE(user_id, event_id),
              FOREIGN KEY(user_id) REFERENCES users(id),
              FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS support_requests (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL, email TEXT NOT NULL,
              message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
              user_id INTEGER, created_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS support_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id INTEGER NOT NULL,
              sender TEXT NOT NULL DEFAULT 'user',
              message TEXT NOT NULL, created_at TEXT NOT NULL,
              FOREIGN KEY(request_id) REFERENCES support_requests(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS test_results (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL, score INTEGER NOT NULL, created_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        # Добавляем колонки к старым таблицам (если БД уже существует)
        _try_alter(conn, "ALTER TABLE participants ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
        _try_alter(conn, "ALTER TABLE support_requests ADD COLUMN user_id INTEGER")
        _try_alter(conn, "ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")

        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO users (name,email,city,password_hash,role,created_at) VALUES(?,?,?,?,?,?)",
                ("Администратор EcoSort","admin@ecosort.kz","Кызылорда",password_hash("admin123"),"admin",now()),
            )
        if conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
            seeds = [
                ("Чистый берег","Субботник","12 июня, 10:00","Кызылорда","Сбор пластика и стекла у береговой линии.","upcoming"),
                ("Зеленый двор","Посадка деревьев","18 июня, 09:30","Алматы","Командная посадка саженцев возле школ.","upcoming"),
                ("Неделя батареек","Сбор отходов","24 июня","Астана","Прием батареек и мелкой электроники.","upcoming"),
                ("Сбор макулатуры","Отчет","Март","Алматы","Собрано 2,8 тонны бумаги, сохранено ~47 деревьев.","past"),
            ]
            conn.executemany(
                "INSERT INTO events(title,event_type,event_date,city,description,status,created_at) VALUES(?,?,?,?,?,?,?)",
                [(*s, now()) for s in seeds],
            )
        if conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0] == 0:
            seeds = [
                ("Пластик","Как подготовить пластик к сдаче","Промойте упаковку, сожмите бутылку и проверьте маркировку."),
                ("Батарейки","Почему батарейки нельзя выбрасывать","Батарейки содержат вещества, загрязняющие почву и воду."),
                ("Бумага","Что относится к макулатуре","Газеты, офисная бумага и картон подходят для переработки."),
                ("Стекло","Как сдавать стеклянные бутылки","Снимите крышки, ополосните бутылки и сдавайте отдельно."),
                ("Металл","Что принимают как металл","Алюминиевые банки и жестяные упаковки после очистки."),
                ("Электроника","Куда девать старую технику","Мелкую электронику передают в специальные пункты."),
                ("Органика","Компостирование дома","Овощные очистки и кофейную гущу можно превращать в компост."),
                ("Одежда","Повторное использование вещей","Хорошую одежду лучше отдавать на благотворительность."),
                ("Опасные отходы","Лампы и градусники","Ртутные лампы нельзя выбрасывать в обычный мусор."),
                ("Экопривычки","Как начать сортировать за неделю","Поставьте дома две коробки: для бумаги и пластика."),
            ]
            conn.executemany("INSERT INTO cards(category,title,body,created_at) VALUES(?,?,?,?)",
                             [(*s, now()) for s in seeds])

def row_count(table, where="1=1"):
    with db() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]

def query_all(sql, params=()):
    with db() as conn:
        return conn.execute(sql, params).fetchall()

def query_one(sql, params=()):
    with db() as conn:
        return conn.execute(sql, params).fetchone()


# ─── Сессии ───────────────────────────────────────────────────────────────────

def session_create(user_id):
    sid = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute("INSERT INTO sessions(sid,user_id,created_at) VALUES(?,?,?)", (sid, user_id, now()))
    return sid

def session_get_user(sid):
    if not sid: return None
    return query_one("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.sid=?", (sid,))

def session_delete(sid):
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE sid=?", (sid,))


# ─── Сброс пароля ─────────────────────────────────────────────────────────────

def reset_token_create(user_id):
    token = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute("DELETE FROM password_reset_tokens WHERE user_id=?", (user_id,))
        conn.execute("INSERT INTO password_reset_tokens(token,user_id,created_at) VALUES(?,?,?)", (token,user_id,now()))
    return token

def reset_token_get_user(token):
    return query_one("SELECT u.* FROM password_reset_tokens t JOIN users u ON u.id=t.user_id WHERE t.token=?", (token,))

def reset_token_delete(token):
    with db() as conn:
        conn.execute("DELETE FROM password_reset_tokens WHERE token=?", (token,))

def send_reset_email(email, reset_url):
    if not SMTP_HOST or not SMTP_USER: return False
    msg = MIMEText(f"Сілтеме / Ссылка:\n\n{reset_url}", "plain", "utf-8")
    msg["Subject"] = "EcoSort — сброс пароля"
    msg["From"] = SMTP_USER
    msg["To"] = email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(msg)
        return True
    except Exception:
        return False


# ─── HTML-помощники ───────────────────────────────────────────────────────────

def nav_link(path, label, active):
    cls = "is-active" if active == path else ""
    return f'<a class="{cls}" href="{path}">{label}</a>'

def paginator(total, page, base_path, extra_params=None, page_param="page", lang='kz'):
    total_pages = max(1, -(-total // PAGE_SIZE))
    if total_pages <= 1: return ""
    params = dict(extra_params or {})
    def url(p):
        params[page_param] = p
        return f"{base_path}?{urlencode(params)}"
    prev = f'<a class="pager-btn" href="{url(page-1)}">← {t("nav_home",lang)[0]}</a>' if page>1 else '<span class="pager-btn pager-disabled">←</span>'
    nxt  = f'<a class="pager-btn" href="{url(page+1)}">→</a>' if page<total_pages else '<span class="pager-btn pager-disabled">→</span>'
    return f'<div class="pager">{prev}<span>{page} {t("page_of",lang)} {total_pages}</span>{nxt}</div>'

def search_form(action, q, placeholder, lang='kz'):
    reset = f"<a class='button button-light' href='{esc(action)}'>{t('btn_reset',lang)}</a>" if q else ""
    return f"""<form class="search-form" method="get" action="{esc(action)}">
      <input type="text" name="q" value="{esc(q)}" placeholder="{esc(placeholder)}">
      <button class="button button-primary" type="submit">{t('btn_find',lang)}</button>
      {reset}</form>"""

def layout(title, active, content, user=None, notice="", lang='kz'):
    user_label = t('visitor', lang)
    other_lang = 'ru' if lang == 'kz' else 'kz'
    lang_label = t('lang_switch', lang)
    auth_actions = f"""
      <a class="button button-light" href="/register">{t('register',lang)}</a>
      <a class="button button-dark"  href="/login">{t('login',lang)}</a>
    """
    if user:
        if user["role"] == "admin":
            user_label = t('admin_label', lang)
            auth_actions = f"""
              <a class="button button-light" href="/profile">{t('cabinet',lang)}</a>
              <a class="button button-light" href="/admin">{t('admin_label',lang)}</a>
              <a class="button button-dark"  href="/logout">{t('logout',lang)}</a>
            """
        else:
            user_label = t('user_prefix', lang) + user['name']
            auth_actions = f"""
              <a class="button button-light" href="/profile">{t('cabinet',lang)}</a>
              <a class="button button-dark"  href="/logout">{t('logout',lang)}</a>
            """
    notice_html = f'<div class="toast">{esc(notice)}</div>' if notice else ""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{esc(title)} — EcoSort</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <link rel="stylesheet" href="/static/app.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="/"><span class="brand-mark">E</span><span>EcoSort</span></a>
    <nav class="main-nav" id="mainNav">
      {nav_link("/", t('nav_home',lang), active)}
      {nav_link("/map", t('nav_map',lang), active)}
      {nav_link("/events", t('nav_events',lang), active)}
      {nav_link("/cards", t('nav_cards',lang), active)}
      {nav_link("/encyclopedia", t('nav_encyclopedia',lang), active)}
      {nav_link("/quiz", t('nav_quiz',lang), active)}
      {nav_link("/support", t('nav_support',lang), active)}
    </nav>
    <div class="session">
      <span>{esc(user_label)}</span>
      {auth_actions}
      <a class="lang-btn" href="/set-lang/{other_lang}">{lang_label}</a>
      <button class="nav-toggle" type="button" data-menu-button aria-label="Menu">☰</button>
    </div>
  </header>
  {notice_html}
  <main>{content}</main>
  <footer class="site-footer">
    <div>
      <strong>EcoSort</strong>
      <p>{t('footer_about',lang)}</p>
    </div>
    <div>
      <strong>{t('footer_write',lang)}</strong>
      <p>Email: hello@ecosort.kz</p>
      <p>+7 700 123 45 67</p>
    </div>
    <div>
      <strong>{t('footer_address',lang)}</strong>
      <p>Қызылорда, Қорқыт Ата, 12</p>
      <p>Instagram: @ecosort.kz</p>
    </div>
    <div>
      <strong>{t('footer_hours',lang)}</strong>
      <p>Дс-Жм / Пн-Пт: 09:00-18:00</p>
      <p>24/7</p>
    </div>
  </footer>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="/static/app.js"></script>
</body>
</html>"""


# ─── Страницы ─────────────────────────────────────────────────────────────────

def home_page(user=None, notice="", params=None, lang='kz'):
    stats = {
        "users":    row_count("users","role='user'"),
        "events":   row_count("events"),
        "joins":    row_count("participants"),
        "requests": row_count("support_requests"),
    }
    featured_events = query_all("SELECT * FROM events WHERE status='upcoming' ORDER BY id DESC LIMIT 3")
    featured_cards  = query_all("SELECT * FROM cards ORDER BY id DESC LIMIT 4")

    ev_html = "".join(f"""
        <article class="compact-card reveal">
          <span>{esc(r['event_date'])}</span>
          <h3>{esc(r['title'])}</h3>
          <p>{esc(r['city'])} — {esc(r['event_type'])}</p>
          <a class="text-link" href="/events">→</a>
        </article>""" for r in featured_events)

    card_html = "".join(f"""
        <article class="compact-card reveal">
          <span>{esc(r['category'])}</span>
          <h3>{esc(r['title'])}</h3>
          <p>{esc(r['body'][:110])}...</p>
        </article>""" for r in featured_cards)

    # Надёжные бесплатные фото с Unsplash (экология/природа)
    photos = [
        ("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80",
         t('photo1_title',lang), t('photo1_text',lang)),
        ("https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800&q=80",
         t('photo2_title',lang), t('photo2_text',lang)),
        ("https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=800&q=80",
         t('photo3_title',lang), t('photo3_text',lang)),
        ("https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80",
         t('photo4_title',lang), t('photo4_text',lang)),
    ]
    photo_html = "".join(f"""
        <div class="photo-card reveal" style="background-image:url('{url}')">
          <div class="photo-overlay">
            <h3>{esc(title)}</h3>
            <p>{esc(text)}</p>
          </div>
        </div>""" for url, title, text in photos)

    content = f"""
    <section class="hero">
      <div class="hero-content reveal">
        <p class="eyebrow">{t('hero_eyebrow',lang)}</p>
        <h1>EcoSort</h1>
        <p class="hero-slogan">{t('hero_slogan',lang)}</p>
        <p class="hero-text">{t('hero_text',lang)}</p>
        <div class="hero-actions">
          <a class="button button-primary" href="/register">{t('hero_btn1',lang)}</a>
          <a class="button button-glass"   href="/events">{t('hero_btn2',lang)}</a>
        </div>
      </div>
      <div class="hero-widget reveal">
        <span>{t('live_counter_label',lang)}</span>
        <strong data-counter="{stats['joins']}">{stats['joins']}</strong>
        <small>{t('live_counter_small',lang)}</small>
      </div>
    </section>

    <section class="stats-band">
      <article><strong data-counter="{stats['users']}">{stats['users']}</strong><span>{t('stat_users',lang)}</span></article>
      <article><strong data-counter="{stats['events']}">{stats['events']}</strong><span>{t('stat_events',lang)}</span></article>
      <article><strong data-counter="{stats['joins']}">{stats['joins']}</strong><span>{t('stat_joins',lang)}</span></article>
      <article><strong data-counter="{stats['requests']}">{stats['requests']}</strong><span>{t('stat_requests',lang)}</span></article>
    </section>

    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('site_sections_eyebrow',lang)}</p>
        <h2>{t('site_sections_title',lang)}</h2>
      </div>
      <div class="role-grid">
        <article class="role-card reveal"><span>01</span><h3>{t('feature1_title',lang)}</h3><p>{t('feature1_sub',lang)}</p></article>
        <article class="role-card reveal"><span>02</span><h3>{t('feature2_title',lang)}</h3><p>{t('feature2_sub',lang)}</p></article>
        <article class="role-card role-card-dark reveal"><span>03</span><h3>{t('admin_label',lang)}</h3><p>{t('admin_title',lang)}</p></article>
      </div>
    </section>

    <section class="section section-soft home-section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('photo_eyebrow',lang)}</p>
        <h2>{t('photo_title',lang)}</h2>
      </div>
      <div class="photo-grid">{photo_html}</div>
    </section>

    <section class="section home-section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('how_eyebrow',lang)}</p>
        <h2>{t('how_title',lang)}</h2>
      </div>
      <div class="process-grid">
        <article class="process-card reveal">
          <span class="step-num">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
            </svg>
          </span>
          <h3>{t('step1_title',lang)}</h3><p>{t('step1_text',lang)}</p>
        </article>
        <article class="process-card reveal">
          <span class="step-num">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>
              <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>
            </svg>
          </span>
          <h3>{t('step2_title',lang)}</h3><p>{t('step2_text',lang)}</p>
        </article>
        <article class="process-card reveal">
          <span class="step-num">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
            </svg>
          </span>
          <h3>{t('step3_title',lang)}</h3><p>{t('step3_text',lang)}</p>
        </article>
        <article class="process-card reveal">
          <span class="step-num">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </span>
          <h3>{t('step4_title',lang)}</h3><p>{t('step4_text',lang)}</p>
        </article>
      </div>
    </section>

    <section class="section section-soft home-section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('quicklinks_eyebrow',lang)}</p>
        <h2>{t('quicklinks_title',lang)}</h2>
      </div>
      <div class="feature-grid">
        <a class="feature-card reveal" href="/map"><strong>{t('feature1_title',lang)}</strong><span>{t('feature1_sub',lang)}</span></a>
        <a class="feature-card reveal" href="/events"><strong>{t('feature2_title',lang)}</strong><span>{t('feature2_sub',lang)}</span></a>
        <a class="feature-card reveal" href="/cards"><strong>{t('feature3_title',lang)}</strong><span>{t('feature3_sub',lang)}</span></a>
        <a class="feature-card reveal" href="/support"><strong>{t('feature4_title',lang)}</strong><span>{t('feature4_sub',lang)}</span></a>
      </div>
    </section>

    <section class="section home-section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('upcoming_eyebrow',lang)}</p>
        <h2>{t('upcoming_title',lang)}</h2>
      </div>
      <div class="compact-grid">{ev_html}</div>
    </section>

    <section class="section section-soft home-section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('cards_eyebrow',lang)}</p>
        <h2>{t('cards_title',lang)}</h2>
      </div>
      <div class="compact-grid">{card_html}</div>
    </section>

    <section class="section home-section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('impact_eyebrow',lang)}</p>
        <h2>{t('impact_title',lang)}</h2>
      </div>
      <div class="impact-grid">
        <article class="impact-card reveal"><strong>524 т</strong><span>{t('impact1',lang)}</span></article>
        <article class="impact-card reveal"><strong>42</strong><span>{t('impact2',lang)}</span></article>
        <article class="impact-card reveal"><strong>7</strong><span>{t('impact3',lang)}</span></article>
        <article class="impact-card reveal"><strong>24/7</strong><span>{t('impact4',lang)}</span></article>
      </div>
    </section>"""
    return layout("EcoSort", "/", content, user, notice, lang)


def auth_page(kind, user=None, notice="", params=None, lang='kz'):
    is_reg = kind == "register"
    title  = t('register' if is_reg else 'login', lang)
    action = "/register" if is_reg else "/login"
    extra  = f"""
      <label>{t('col_name',lang)}<input type="text" name="name" required></label>
      <label>{t('admin_field_city',lang)}<input type="text" name="city" required></label>
    """ if is_reg else ""
    switch = f'<a href="/login">{t("login",lang)}</a>' if is_reg else f'<a href="/register">{t("register",lang)}</a>'
    forgot = '' if is_reg else f'<a href="/forgot-password">{t("forgot_title",lang)}?</a>'
    content = f"""
    <section class="section auth-section">
      <div class="auth-card reveal">
        <p class="eyebrow">{title}</p>
        <h1>{title} — EcoSort</h1>
        <form class="app-form" method="post" action="{action}">
          {extra}
          <label>Email<input type="email" name="email" required></label>
          <label>{t('reset_new',lang) if is_reg else t('login',lang)}<input type="password" name="password" required minlength="4"></label>
          <button class="button button-primary" type="submit">{title}</button>
        </form>
        <div class="auth-links">{switch}{forgot}<span>Demo: admin@ecosort.kz / admin123</span></div>
      </div>
    </section>"""
    return layout(title, f"/{kind}", content, user, notice, lang)


def profile_page(user=None, notice="", params=None, lang='kz'):
    if not user:
        content = f"""
        <section class="section auth-section">
          <div class="empty-state reveal">
            <p class="eyebrow">{t('cabinet',lang)}</p>
            <h1>{t('profile_need_login_title',lang)}</h1>
            <p>{t('profile_need_login_text',lang)}</p>
            <div class="hero-actions">
              <a class="button button-primary" href="/register">{t('register',lang)}</a>
              <a class="button button-light" href="/login">{t('login',lang)}</a>
            </div>
          </div>
        </section>"""
        return layout(t('cabinet',lang), "/profile", content, user, notice, lang)

    joins = query_all("""
        SELECT e.title, e.event_date, e.city, p.created_at, p.id as part_id, p.status
        FROM participants p JOIN events e ON e.id=p.event_id
        WHERE p.user_id=? ORDER BY p.id DESC""", (user["id"],))

    tests = query_all("SELECT score,created_at FROM test_results WHERE user_id=? ORDER BY id DESC", (user["id"],))

    # Привязываем старые запросы по email (у них user_id=NULL)
    with db() as conn:
        conn.execute("UPDATE support_requests SET user_id=? WHERE email=? AND user_id IS NULL",
                     (user["id"], user["email"]))

    # Ищем по user_id ИЛИ по email (на случай если что-то ещё не привязано)
    my_reqs = query_all("""
        SELECT sr.id, sr.message, sr.created_at, sr.status,
               COUNT(sm.id) as msg_count,
               SUM(CASE WHEN sm.sender='admin' THEN 1 ELSE 0 END) as admin_replies
        FROM support_requests sr
        LEFT JOIN support_messages sm ON sm.request_id=sr.id
        WHERE sr.user_id=? OR sr.email=?
        GROUP BY sr.id ORDER BY sr.id DESC LIMIT 20""", (user["id"], user["email"]))

    badges = [t('badge_new', lang)]
    if joins: badges.append(t('badge_joined', lang))
    if len(joins) >= 3: badges.append(t('badge_3plus', lang))
    if tests: badges.append(t('badge_test', lang))

    status_cls = {'pending':'status-pending','accepted':'status-accepted','rejected':'status-rejected'}
    join_items = "".join(
        f"""<li><span></span>
          <div>
            <div>«{esc(r['title'])}» — {esc(r['event_date'])}, {esc(r['city'])}</div>
            <span class="status {status_cls.get(r['status'],'status-pending')}">{t(r['status'],lang)}</span>
          </div>
        </li>""" for r in joins
    ) or f"<li><span></span>{t('profile_no_joins',lang)}</li>"

    test_items = "".join(
        f"<li><span></span>Тест — {r['score']}% ({esc(r['created_at'])})</li>"
        for r in tests
    ) or f"<li><span></span>{t('profile_no_tests',lang)}</li>"

    badge_html = "".join(f"<span>{esc(b)}</span>" for b in badges)

    # Строим карточки запросов — с ответом выделяем ярко
    req_cards = ""
    has_new_reply = False
    for r in my_reqs:
        has_reply = r['admin_replies'] and r['admin_replies'] > 0
        if has_reply:
            has_new_reply = True
        req_cards += f"""
        <article class="support-req-card {'support-req-replied' if has_reply else ''}">
          <div class="support-req-msg">{esc(r['message'][:120])}{"..." if len(r['message'])>120 else ""}</div>
          <div class="support-req-footer">
            <span class="status {'status-accepted' if has_reply else 'status-pending'}">
              {'💬 ' + t('view_thread',lang).replace('→','') if has_reply else '⏳ ' + t('pending',lang)}
            </span>
            <a class="button button-light" style="min-height:32px;padding:4px 14px;font-size:13px"
               href="/support/thread/{r['id']}">{t('view_thread',lang)}</a>
          </div>
        </article>"""

    if not req_cards:
        req_cards = f'<p class="muted-text" style="padding:12px 0">{t("profile_support_empty",lang)}</p>'

    # Уведомление о новом ответе
    reply_notice = ""
    if has_new_reply:
        lbl = "Adminнің жауабы бар! / Есть ответ от администратора!" if lang == 'kz' else "Есть ответ от администратора!"
        reply_notice = f'<div class="reply-alert">💬 {lbl}</div>'

    content = f"""
    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('profile_eyebrow',lang)}</p>
        <h1>{t('profile_title',lang)}</h1>
      </div>
      {reply_notice}
      <div class="cabinet-grid">
        <article class="profile-panel reveal">
          <div class="avatar">{esc(user['name'][:2]).upper()}</div>
          <div>
            <h3>{esc(user['name'])}</h3>
            <p>{esc(user['email'])}</p>
            <p>{esc(user['city'])}</p>
          </div>
        </article>
        <article class="panel reveal">
          <h3>{t('profile_history',lang)}</h3>
          <ul class="timeline">{join_items}</ul>
        </article>
        <article class="panel reveal">
          <h3>{t('profile_badges',lang)}</h3>
          <div class="badges">{badge_html}</div>
        </article>
      </div>
      <div class="two-col">
        <article class="panel reveal">
          <h3>{t('profile_test_title',lang)}</h3>
          <p>{len(QUIZ_QUESTIONS)} {t('profile_test_desc',lang)}</p>
          <a class="button button-primary" href="/quiz">{t('profile_test_btn',lang)}</a>
        </article>
        <article class="panel reveal">
          <h3>{t('profile_results',lang)}</h3>
          <ul class="timeline">{test_items}</ul>
        </article>
      </div>
      <div class="panel reveal" style="margin-top:16px">
        <h3>{t('profile_support_title',lang)}</h3>
        <div class="support-req-list">{req_cards}</div>
      </div>
    </section>"""
    return layout(t('cabinet',lang), "/profile", content, user, notice, lang)


# Фото для карточек акций по типу мероприятия
EVENT_PHOTOS = {
    "субботник":        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=70",
    "посадка деревьев": "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800&q=70",
    "сбор отходов":     "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=800&q=70",
    "отчет":            "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=70",
    "экология":         "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800&q=70",
    "default":          "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=70",
}

def get_event_photo(event_type: str) -> str:
    key = event_type.lower().strip()
    for k, url in EVENT_PHOTOS.items():
        if k in key or key in k:
            return url
    return EVENT_PHOTOS["default"]


def events_page(user=None, notice="", params=None, lang='kz'):
    params   = params or {}
    q        = params.get("q",[""])[0].strip()
    page_num = max(1, int(params.get("page",["1"])[0]) if params.get("page",["1"])[0].isdigit() else 1)

    sc, sp = "", ()
    if q:
        sc = "AND (title LIKE ? OR city LIKE ? OR event_type LIKE ? OR description LIKE ?)"
        sp = (f"%{q}%",)*4

    total  = query_one(f"SELECT COUNT(*) FROM events WHERE 1=1 {sc}", sp)[0]
    events = query_all(
        f"""SELECT * FROM events WHERE 1=1 {sc}
            ORDER BY CASE status WHEN 'upcoming' THEN 0 ELSE 1 END, id DESC
            LIMIT ? OFFSET ?""", sp+(PAGE_SIZE,(page_num-1)*PAGE_SIZE))

    cards = []
    for ev in events:
        part = None
        if user:
            part = query_one("SELECT id,status FROM participants WHERE user_id=? AND event_id=?", (user["id"],ev["id"]))
        can_join = user and user["role"]=="user" and ev["status"]=="upcoming" and not part
        if ev["status"]=="past":
            btn = f'<span class="status status-done">{t("event_done",lang)}</span>'
        elif part:
            sc2 = {'pending':'status-pending','accepted':'status-accepted','rejected':'status-rejected'}.get(part['status'],'status-pending')
            btn = f'<span class="status {sc2}">{t(part["status"],lang)}</span>'
        elif can_join:
            btn = f'<form method="post" action="/events/{ev["id"]}/join"><button class="button button-light" type="submit">{t("btn_join",lang)}</button></form>'
        elif not user:
            btn = f'<a class="button button-light" href="/login">{t("btn_login_join",lang)}</a>'
        else:
            btn = f'<span class="status status-done">{t("users_only",lang)}</span>'

        photo = get_event_photo(ev["event_type"])
        cards.append(f"""
            <article class="event-card reveal" style="background-image:url('{photo}')">
              <div class="meta">
                <span>{esc(ev['event_date'])}</span>
                <span>{esc(ev['city'])}</span>
                <span>{esc(ev['event_type'])}</span>
              </div>
              <h3>{esc(ev['title'])}</h3>
              <p>{esc(ev['description'])}</p>
              {btn}
            </article>""")

    content = f"""
    <section class="section section-soft">
      <div class="section-head reveal">
        <p class="eyebrow">{t('events_eyebrow',lang)}</p>
        <h1>{t('events_title',lang)}</h1>
        <p>{t('events_subtitle',lang)}</p>
      </div>
      {search_form("/events", q, t('events_search',lang), lang)}
      <div class="event-grid">{''.join(cards) or f'<p class="muted-text">{t("events_empty",lang)}</p>'}</div>
      {paginator(total, page_num, "/events", {"q":q} if q else {}, lang=lang)}
    </section>"""
    return layout(t('nav_events',lang), "/events", content, user, notice, lang)


def cards_page(user=None, notice="", params=None, lang='kz'):
    params   = params or {}
    q        = params.get("q",[""])[0].strip()
    page_num = max(1, int(params.get("page",["1"])[0]) if params.get("page",["1"])[0].isdigit() else 1)

    sc, sp = "", ()
    if q:
        sc = "WHERE (title LIKE ? OR category LIKE ? OR body LIKE ?)"
        sp = (f"%{q}%",)*3

    total = query_one(f"SELECT COUNT(*) FROM cards {sc}", sp)[0]
    cards = query_all(f"SELECT * FROM cards {sc} ORDER BY id DESC LIMIT ? OFFSET ?",
                      sp+(PAGE_SIZE,(page_num-1)*PAGE_SIZE))

    card_html = "".join(f"""
        <article class="info-card reveal">
          <span>{esc(c['category'])}</span>
          <h3>{esc(c['title'])}</h3>
          <p>{esc(c['body'])}</p>
        </article>""" for c in cards)

    content = f"""
    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('cards_page_eyebrow',lang)}</p>
        <h1>{t('cards_page_title',lang)}</h1>
      </div>
      {search_form("/cards", q, t('cards_search',lang), lang)}
      <div class="info-grid">{card_html or f'<p class="muted-text">{t("cards_empty",lang)}</p>'}</div>
      {paginator(total, page_num, "/cards", {"q":q} if q else {}, lang=lang)}
    </section>"""
    return layout(t('nav_cards',lang), "/cards", content, user, notice, lang)


def map_page(user=None, notice="", params=None, lang='kz'):
    content = f"""
    <section class="section section-soft">
      <div class="section-head reveal">
        <p class="eyebrow">{t('map_eyebrow',lang)}</p>
        <h1>{t('map_title',lang)}</h1>
        <p>{t('map_subtitle',lang)}</p>
      </div>
      <div class="map-layout">
        <aside class="filter-panel reveal">
          <label>{t('map_city',lang)}
            <select data-city-filter>
              <option value="all">{t('map_all_cities',lang)}</option>
              <option>Алматы</option><option>Астана</option><option>Кызылорда</option>
            </select>
          </label>
          <label><input type="checkbox" value="Пластик" checked data-type-filter> Пластик</label>
          <label><input type="checkbox" value="Бумага"  checked data-type-filter> Бумага</label>
          <label><input type="checkbox" value="Стекло"  checked data-type-filter> Стекло</label>
          <label><input type="checkbox" value="Металл"  checked data-type-filter> Металл</label>
          <label><input type="checkbox" value="Батарейки" checked data-type-filter> Батарейки</label>
        </aside>
        <div class="real-map reveal" id="realMap" data-map-board></div>
        <div class="station-list reveal" data-station-list></div>
      </div>
    </section>"""
    return layout(t('nav_map',lang), "/map", content, user, notice, lang)


def encyclopedia_page(user=None, notice="", params=None, lang='kz'):
    items = [
        ("Пластик / Пластик","До 450 лет / 450 жылға дейін","Микропластик загрязняет воду.","Дробление, промывка, грануляция."),
        ("Бумага / Қағаз","2–6 месяцев / 2–6 ай","Производство требует древесины.","Измельчение и переработка."),
        ("Стекло / Шыны","Более 1000 лет / 1000 жылдан астам","Осколки опасны.","Сортировка и переплавка."),
        ("Металл / Металл","50–500 лет / 50–500 жыл","Окисляется в почве.","Прессование и переплавка."),
        ("Органика / Органика","Недели–год / Апталар–жыл","На полигонах выделяет метан.","Компостирование."),
        ("Батарейки / Батарейки","До 100 лет / 100 жылға дейін","Тяжёлые металлы вредят почве.","Безопасная утилизация."),
        ("Электроника / Электроника","Десятки лет / Ондаған жыл","Содержит опасные элементы.","Разборка и переработка."),
        ("Текстиль / Тоқыма","До 200 лет / 200 жылға дейін","Синтетика даёт микроволокна.","Повторное использование."),
    ]
    html_items = "".join(f"""
        <article class="info-card reveal">
          <span>{esc(name)}</span>
          <h3>{esc(time)}</h3>
          <p><strong>{t('influence',lang)}</strong> {esc(inf)}</p>
          <p><strong>{t('recycling',lang)}</strong> {esc(rec)}</p>
        </article>""" for name,time,inf,rec in items)

    content = f"""
    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('encyclopedia_eyebrow',lang)}</p>
        <h1>{t('encyclopedia_title',lang)}</h1>
      </div>
      <div class="info-grid">{html_items}</div>
    </section>"""
    return layout(t('nav_encyclopedia',lang), "/encyclopedia", content, user, notice, lang)


def support_page(user=None, notice="", params=None, lang='kz'):
    pre_name  = esc(user['name'])  if user else ""
    pre_email = esc(user['email']) if user else ""
    name_ro   = 'readonly style="opacity:0.7"' if user else ""
    email_ro  = 'readonly style="opacity:0.7"' if user else ""

    # ── Строим панель чатов ──────────────────────────────────────
    is_admin = user and user["role"] == "admin"

    if is_admin:
        # Для администратора — все запросы
        reqs = query_all("""
            SELECT sr.id, sr.name, sr.email, sr.message, sr.created_at,
                   COUNT(sm.id) as msg_count,
                   SUM(CASE WHEN sm.sender='admin' THEN 1 ELSE 0 END) as admin_replies
            FROM support_requests sr
            LEFT JOIN support_messages sm ON sm.request_id=sr.id
            GROUP BY sr.id ORDER BY sr.id DESC LIMIT 30
        """)
        chat_title = "Барлық хат алмасулар" if lang == 'kz' else "Все переписки"
    elif user:
        # Привязываем старые запросы по email
        with db() as conn:
            conn.execute("UPDATE support_requests SET user_id=? WHERE email=? AND user_id IS NULL",
                         (user["id"], user["email"]))
        reqs = query_all("""
            SELECT sr.id, sr.name, sr.email, sr.message, sr.created_at,
                   COUNT(sm.id) as msg_count,
                   SUM(CASE WHEN sm.sender='admin' THEN 1 ELSE 0 END) as admin_replies
            FROM support_requests sr
            LEFT JOIN support_messages sm ON sm.request_id=sr.id
            WHERE sr.user_id=? OR sr.email=?
            GROUP BY sr.id ORDER BY sr.id DESC LIMIT 20
        """, (user["id"], user["email"]))
        chat_title = "Менің хат алмасуларым" if lang == 'kz' else "Мои переписки"
    else:
        reqs = []
        chat_title = ""

    # Строим строки тредов
    if reqs:
        thread_rows = "".join(f"""
        <a class="thread-item {'thread-item-replied' if r['admin_replies'] else ''}"
           href="/support/thread/{r['id']}">
          <div class="thread-item-left">
            <div class="thread-item-who">{esc(r['name'])} <span>·</span> {esc(r['email'])}</div>
            <div class="thread-item-msg">{esc(r['message'][:90])}{"..." if len(r['message'])>90 else ""}</div>
            <div class="thread-item-date">{esc(r['created_at'])}</div>
          </div>
          <div class="thread-item-right">
            {"<span class='thread-new-badge'>💬 Новый ответ</span>" if r['admin_replies'] and r['msg_count'] > 1 else ""}
            {"<span class='thread-badge'>💬 " + str(r['msg_count']) + "</span>" if r['msg_count'] else "<span class='thread-badge thread-badge-wait'>⏳</span>"}
          </div>
        </a>""" for r in reqs)
    else:
        empty_msg = "Сұраулар жоқ" if lang == 'kz' else "Обращений пока нет"
        thread_rows = f'<p class="muted-text" style="padding:16px 0;text-align:center">{empty_msg}</p>'

    # Панель чатов — всегда видима для вошедших
    chat_panel = ""
    if user:
        chat_panel = f"""
      <section class="support-chat-section reveal">
        <div class="support-chat-header">
          <h2>💬 {chat_title}</h2>
          {"<a class='button button-light' style='font-size:13px' href='/admin'>Открыть админ-панель</a>" if is_admin else ""}
        </div>
        <div class="thread-list-full">{thread_rows}</div>
      </section>"""

    content = f"""
    <section class="section section-soft">
      <div class="section-head reveal">
        <p class="eyebrow">{t('support_eyebrow',lang)}</p>
        <h1>{t('support_title',lang)}</h1>
        <p>{t('support_subtitle',lang)}</p>
      </div>
      <div class="support-layout">
        <form class="app-form reveal" method="post" action="/support">
          <h3>{t('support_form_title',lang)}</h3>
          <label>{t('support_name',lang)}
            <input type="text" name="name" value="{pre_name}" required {name_ro}>
          </label>
          <label>{t('support_email',lang)}
            <input type="email" name="email" value="{pre_email}" required {email_ro}>
          </label>
          <label>{t('support_message',lang)}
            <textarea name="message" rows="5" required placeholder="..."></textarea>
          </label>
          <button class="button button-primary" type="submit">{t('support_send',lang)}</button>
        </form>
        <article class="panel reveal">
          <h3>{t('support_how_title',lang)}</h3>
          <p>{t('support_how1',lang)}</p>
          <p>{t('support_how2',lang)}</p>
          <p>{t('support_how3',lang)}</p>
        </article>
      </div>
      {chat_panel}
    </section>"""
    return layout(t('nav_support',lang), "/support", content, user, notice, lang)


def support_thread_page(request_id, user=None, notice="", params=None, lang='kz'):
    req = query_one("SELECT * FROM support_requests WHERE id=?", (request_id,))
    if not req:
        return layout(t('nav_support',lang), "/support", "<section class='section auth-section'><div class='empty-state'><h1>404</h1></div></section>", user, notice, lang)

    is_admin = user and user["role"] == "admin"
    is_owner = req["user_id"] and user and user["id"] == req["user_id"]
    if not is_admin and not is_owner:
        return layout(t('nav_support',lang), "/support",
            f"<section class='section auth-section'><div class='empty-state reveal'><h1>{t('admin_only_title',lang)}</h1><a class='button button-primary' href='/login'>{t('login',lang)}</a></div></section>",
            user, notice, lang)

    messages = query_all("SELECT * FROM support_messages WHERE request_id=? ORDER BY id ASC", (request_id,))
    msg_html = "".join(f"""
        <div class="chat-msg {'chat-admin' if m['sender']=='admin' else 'chat-user'}">
          <div class="chat-who">{t('thread_admin',lang) if m['sender']=='admin' else t('thread_you',lang)}</div>
          <div class="chat-bubble">{esc(m['message'])}</div>
          <div class="chat-time">{esc(m['created_at'])}</div>
        </div>""" for m in messages)

    reply_form = f"""
      <form class="app-form" method="post" action="/support/thread/{request_id}/message">
        <label>{t('thread_send',lang)}
          <textarea name="message" rows="4" required placeholder="..."></textarea>
        </label>
        <button class="button button-primary" type="submit">{t('btn_send',lang)}</button>
      </form>"""

    if is_admin:
        reply_form = f"""
      <form class="app-form" method="post" action="/admin/support/{request_id}/reply">
        <label>{t('admin_reply',lang)}
          <textarea name="reply" rows="4" required placeholder="..."></textarea>
        </label>
        <button class="button button-primary" type="submit">{t('btn_reply',lang)}</button>
      </form>"""

    content = f"""
    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('thread_title',lang)} #{request_id}</p>
        <h1>{esc(req['message'][:60])}{"..." if len(req['message'])>60 else ""}</h1>
        <p>📧 {esc(req['email'])} — {esc(req['created_at'])}</p>
      </div>
      <div class="chat-thread reveal">{msg_html or '<p class="muted-text">...</p>'}</div>
      <div class="panel reveal" style="margin-top:16px">{reply_form}</div>
    </section>"""
    return layout(t('thread_title',lang), "/support", content, user, notice, lang)


def quiz_page(user=None, notice="", params=None, lang='kz'):
    if not user or user["role"] != "user":
        content = f"""
        <section class="section auth-section">
          <div class="empty-state reveal">
            <p class="eyebrow">{t('nav_quiz',lang)}</p>
            <h1>{t('quiz_need_login',lang)}</h1>
            <a class="button button-primary" href="/login">{t('login',lang)}</a>
          </div>
        </section>"""
        return layout(t('nav_quiz',lang), "/quiz", content, user, notice, lang)

    questions_html = ""
    for i, q in enumerate(QUIZ_QUESTIONS):
        opts = q[f'options_{lang}']
        questions_html += f"""
        <article class="panel reveal quiz-question">
          <p class="eyebrow">{i+1} / {len(QUIZ_QUESTIONS)}</p>
          <h3>{q[f'text_{lang}']}</h3>
          <div class="quiz-options">{''.join(
              f'<label class="quiz-option"><input type="radio" name="{esc(q["id"])}" value="{j}" required>{esc(opt)}</label>'
              for j,opt in enumerate(opts)
          )}</div>
        </article>"""

    content = f"""
    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('quiz_eyebrow',lang)}</p>
        <h1>{t('quiz_title',lang)}</h1>
        <p>{len(QUIZ_QUESTIONS)} {t('quiz_subtitle',lang)}</p>
      </div>
      <form method="post" action="/quiz">
        <div class="quiz-grid">{questions_html}</div>
        <div style="margin-top:24px">
          <button class="button button-primary" type="submit">{t('quiz_submit',lang)}</button>
        </div>
      </form>
    </section>"""
    return layout(t('nav_quiz',lang), "/quiz", content, user, notice, lang)


def forgot_password_page(user=None, notice="", params=None, lang='kz'):
    content = f"""
    <section class="section auth-section">
      <div class="auth-card reveal">
        <p class="eyebrow">{t('forgot_eyebrow',lang)}</p>
        <h1>{t('forgot_title',lang)}</h1>
        <p>{t('forgot_text',lang)}</p>
        <form class="app-form" method="post" action="/forgot-password">
          <label>Email<input type="email" name="email" required></label>
          <button class="button button-primary" type="submit">{t('forgot_send',lang)}</button>
        </form>
        <div class="auth-links"><a href="/login">{t('login',lang)}</a></div>
      </div>
    </section>"""
    return layout(t('forgot_title',lang), "/forgot-password", content, user, notice, lang)


def reset_password_page(token, user=None, notice="", params=None, lang='kz'):
    if not reset_token_get_user(token):
        content = f"""
        <section class="section auth-section">
          <div class="empty-state reveal">
            <h1>Ссылка недействительна / Сілтеме жарамсыз</h1>
            <a class="button button-primary" href="/forgot-password">{t('forgot_title',lang)}</a>
          </div>
        </section>"""
        return layout(t('reset_title',lang), "/reset-password", content, user, notice, lang)

    content = f"""
    <section class="section auth-section">
      <div class="auth-card reveal">
        <p class="eyebrow">{t('reset_eyebrow',lang)}</p>
        <h1>{t('reset_title',lang)}</h1>
        <form class="app-form" method="post" action="/reset-password">
          <input type="hidden" name="token" value="{esc(token)}">
          <label>{t('reset_new',lang)}<input type="password" name="password" required minlength="4"></label>
          <label>{t('reset_confirm',lang)}<input type="password" name="password2" required minlength="4"></label>
          <button class="button button-primary" type="submit">{t('reset_save',lang)}</button>
        </form>
      </div>
    </section>"""
    return layout(t('reset_title',lang), "/reset-password", content, user, notice, lang)


def admin_page(user=None, notice="", params=None, lang='kz'):
    if not user or user["role"] != "admin":
        content = f"""
        <section class="section auth-section">
          <div class="empty-state reveal">
            <p class="eyebrow">{t('admin_eyebrow',lang)}</p>
            <h1>{t('admin_only_title',lang)}</h1>
            <p>{t('admin_only_text',lang)}</p>
            <a class="button button-primary" href="/login">{t('login',lang)}</a>
          </div>
        </section>"""
        return layout(t('admin_label',lang), "/admin", content, user, notice, lang)

    params = params or {}
    qe  = params.get("qe",[""])[0].strip()
    qc  = params.get("qc",[""])[0].strip()
    qr  = params.get("qr",[""])[0].strip()
    qu  = params.get("qu",[""])[0].strip()
    pe  = max(1,int(params.get("pe",["1"])[0]) if params.get("pe",["1"])[0].isdigit() else 1)
    pc  = max(1,int(params.get("pc",["1"])[0]) if params.get("pc",["1"])[0].isdigit() else 1)
    pr  = max(1,int(params.get("pr",["1"])[0]) if params.get("pr",["1"])[0].isdigit() else 1)
    pp  = max(1,int(params.get("pp",["1"])[0]) if params.get("pp",["1"])[0].isdigit() else 1)
    pu  = max(1,int(params.get("pu",["1"])[0]) if params.get("pu",["1"])[0].isdigit() else 1)

    stats = {k: row_count(*v) for k,v in {
        "users":("users","role='user'"),"events":("events",),"cards":("cards",),
        "joins":("participants",),"requests":("support_requests",),
    }.items()}

    # ── Пользователи ──────────────────────────────────────────────
    u_cl = "AND (name LIKE ? OR email LIKE ? OR city LIKE ?)" if qu else ""
    u_sp = (f"%{qu}%",)*3 if qu else ()
    total_users = query_one(f"SELECT COUNT(*) FROM users WHERE role='user' {u_cl}", u_sp)[0]
    users_list  = query_all(f"""
        SELECT u.id, u.name, u.email, u.city, u.created_at,
               COALESCE(u.status,'active') as status,
               COUNT(DISTINCT p.id) as joins_count
        FROM users u
        LEFT JOIN participants p ON p.user_id=u.id
        WHERE u.role='user' {u_cl}
        GROUP BY u.id ORDER BY u.id DESC
        LIMIT ? OFFSET ?""", u_sp+(PAGE_SIZE,(pu-1)*PAGE_SIZE))

    user_rows = "".join(f"""<tr>
        <td>
          <div style="font-weight:800;color:#fff">{esc(r['name'])}</div>
          <div style="font-size:12px;color:var(--muted)">{esc(r['city'])}</div>
        </td>
        <td style="font-size:13px">{esc(r['email'])}</td>
        <td style="font-size:12px;color:var(--muted)">{esc(r['created_at'])}</td>
        <td><strong style="color:var(--accent)">{r['joins_count']}</strong></td>
        <td>
          <span class="status {'status-accepted' if r['status']=='active' else 'status-rejected'}">
            {'🟢 ' + t('user_active',lang) if r['status']=='active' else '🔴 ' + t('user_banned',lang)}
          </span>
        </td>
        <td>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <form method="post" action="/admin/users/{r['id']}/ban" style="display:inline">
              <button class="button {'button-danger' if r['status']=='active' else 'button-primary'}"
                      style="min-height:28px;padding:3px 10px;font-size:12px" type="submit">
                {t('btn_ban',lang) if r['status']=='active' else t('btn_unban',lang)}
              </button>
            </form>
            <form method="post" action="/admin/users/{r['id']}/reset" style="display:inline"
                  onsubmit="return confirm('Сбросить историю участий и тесты?')">
              <button class="button button-light" style="min-height:28px;padding:3px 10px;font-size:12px" type="submit">
                🔄 {t('btn_reset_acc',lang)}
              </button>
            </form>
            <form method="post" action="/admin/users/{r['id']}/delete" style="display:inline"
                  onsubmit="return confirm('Удалить аккаунт полностью?')">
              <button class="button button-danger" style="min-height:28px;padding:3px 10px;font-size:12px" type="submit">
                🗑 {t('btn_delete',lang)}
              </button>
            </form>
          </div>
        </td>
      </tr>""" for r in users_list
    ) or f"<tr><td colspan='6'>{t('no_users',lang)}</td></tr>"

    # ── Ожидающие заявки
    pending_parts = query_all("""
        SELECT p.id, u.name, u.email, e.title, p.created_at
        FROM participants p JOIN users u ON u.id=p.user_id JOIN events e ON e.id=p.event_id
        WHERE p.status='pending' ORDER BY p.id DESC""")
    pending_rows = "".join(f"""<tr>
        <td>{esc(r['name'])}</td><td>{esc(r['email'])}</td><td>{esc(r['title'])}</td><td>{esc(r['created_at'])}</td>
        <td>
          <form method="post" action="/admin/participants/{r['id']}/accept" style="display:inline">
            <button class="button button-primary" style="min-height:30px;padding:4px 12px;font-size:13px">{t('btn_accept',lang)}</button>
          </form>
          <form method="post" action="/admin/participants/{r['id']}/reject" style="display:inline" onsubmit="return confirm('Отклонить?')">
            <button class="button button-danger" style="min-height:30px;padding:4px 12px;font-size:13px">{t('btn_reject',lang)}</button>
          </form>
        </td></tr>""" for r in pending_parts
    ) or f"<tr><td colspan='5'>{t('no_joins',lang)}</td></tr>"

    # ── Все заявки
    total_parts = query_one("SELECT COUNT(*) FROM participants")[0]
    all_parts = query_all("""
        SELECT p.id, u.name, u.email, e.title, p.status, p.created_at
        FROM participants p JOIN users u ON u.id=p.user_id JOIN events e ON e.id=p.event_id
        ORDER BY p.id DESC LIMIT ? OFFSET ?""", (PAGE_SIZE,(pp-1)*PAGE_SIZE))
    all_part_rows = "".join(f"""<tr>
        <td>{esc(r['name'])}</td><td>{esc(r['email'])}</td><td>{esc(r['title'])}</td>
        <td><span class="status {'status-accepted' if r['status']=='accepted' else 'status-rejected' if r['status']=='rejected' else 'status-pending'}">{t(r['status'],lang)}</span></td>
        <td>{esc(r['created_at'])}</td></tr>""" for r in all_parts
    ) or f"<tr><td colspan='5'>{t('no_joins',lang)}</td></tr>"

    # ── Акции
    ev_cl = "WHERE (title LIKE ? OR city LIKE ? OR event_type LIKE ?)" if qe else ""
    ev_sp = (f"%{qe}%",)*3 if qe else ()
    total_ev = query_one(f"SELECT COUNT(*) FROM events {ev_cl}", ev_sp)[0]
    events = query_all(f"SELECT * FROM events {ev_cl} ORDER BY id DESC LIMIT ? OFFSET ?", ev_sp+(PAGE_SIZE,(pe-1)*PAGE_SIZE))
    ev_rows = "".join(f"""<tr>
        <td>{esc(r['title'])}</td><td>{esc(r['event_type'])}</td>
        <td>{esc(r['event_date'])}</td><td>{esc(r['city'])}</td>
        <td><span class="status {'status-accepted' if r['status']=='upcoming' else 'status-done'}">{t('status_active' if r['status']=='upcoming' else 'status_done',lang)}</span></td>
        <td>
          <form method="post" action="/admin/events/{r['id']}/toggle" style="display:inline">
            <button class="button button-light" style="min-height:28px;padding:3px 10px;font-size:12px" type="submit">
              {'→ '+t('btn_complete',lang) if r['status']=='upcoming' else '→ '+t('btn_activate',lang)}
            </button>
          </form>
          <form method="post" action="/admin/events/{r['id']}/delete" style="display:inline" onsubmit="return confirm('Удалить?')">
            <button class="button button-danger" style="min-height:28px;padding:3px 10px;font-size:12px" type="submit">{t('btn_delete',lang)}</button>
          </form>
        </td></tr>""" for r in events
    ) or f"<tr><td colspan='6'>{t('no_events',lang)}</td></tr>"

    # ── Карточки
    card_cl = "WHERE (title LIKE ? OR category LIKE ? OR body LIKE ?)" if qc else ""
    card_sp = (f"%{qc}%",)*3 if qc else ()
    total_cards = query_one(f"SELECT COUNT(*) FROM cards {card_cl}", card_sp)[0]
    cards = query_all(f"SELECT * FROM cards {card_cl} ORDER BY id DESC LIMIT ? OFFSET ?", card_sp+(PAGE_SIZE,(pc-1)*PAGE_SIZE))
    card_rows = "".join(f"""<tr>
        <td>{esc(r['category'])}</td><td>{esc(r['title'])}</td><td>{esc(r['created_at'])}</td>
        <td><form method="post" action="/admin/cards/{r['id']}/delete" style="display:inline" onsubmit="return confirm('Удалить?')">
          <button class="button button-danger" style="min-height:28px;padding:3px 10px;font-size:12px">{t('btn_delete',lang)}</button>
        </form></td></tr>""" for r in cards
    ) or f"<tr><td colspan='4'>{t('no_cards',lang)}</td></tr>"

    # ── Запросы поддержки
    req_cl = "WHERE (sr.name LIKE ? OR sr.email LIKE ? OR sr.message LIKE ?)" if qr else ""
    req_sp = (f"%{qr}%",)*3 if qr else ()
    total_req = query_one(f"SELECT COUNT(*) FROM support_requests sr {req_cl}", req_sp)[0]
    requests = query_all(
        f"""SELECT sr.*, COUNT(sm.id) as msg_count
            FROM support_requests sr LEFT JOIN support_messages sm ON sm.request_id=sr.id
            {req_cl} GROUP BY sr.id ORDER BY sr.id DESC LIMIT ? OFFSET ?""",
        req_sp+(PAGE_SIZE,(pr-1)*PAGE_SIZE))
    req_rows = "".join(f"""<tr>
        <td>{esc(r['name'])}</td><td>{esc(r['email'])}</td>
        <td>{esc(r['message'][:80])}</td>
        <td>{r['msg_count'] or 0}</td>
        <td>{esc(r['created_at'])}</td>
        <td><a class="button button-light" style="min-height:28px;padding:3px 10px;font-size:12px" href="/support/thread/{r['id']}">{t('btn_reply',lang)}</a></td>
        </tr>""" for r in requests
    ) or f"<tr><td colspan='6'>{t('no_requests',lang)}</td></tr>"

    content = f"""
    <section class="section">
      <div class="section-head reveal">
        <p class="eyebrow">{t('admin_eyebrow',lang)}</p>
        <h1>{t('admin_title',lang)}</h1>
      </div>
      <div class="admin-stats">
        <article><strong>{stats['users']}</strong><span>{t('stat_users',lang)}</span></article>
        <article><strong>{stats['events']}</strong><span>{t('stat_events',lang)}</span></article>
        <article><strong>{stats['cards']}</strong><span>{t('nav_cards',lang)}</span></article>
        <article><strong>{stats['joins']}</strong><span>{t('stat_joins',lang)}</span></article>
        <article><strong>{stats['requests']}</strong><span>{t('stat_requests',lang)}</span></article>
      </div>

      <div class="table-wrap reveal">
        <h3>👥 {t('admin_users',lang)} ({total_users})</h3>
        {search_form("/admin",qu,t('search_users',lang),lang)}
        <table>
          <thead><tr>
            <th>{t('col_name',lang)}</th>
            <th>Email</th>
            <th>{t('col_reg_date',lang)}</th>
            <th>{t('col_joins',lang)}</th>
            <th>{t('col_status_user',lang)}</th>
            <th>{t('col_action',lang)}</th>
          </tr></thead>
          <tbody>{user_rows}</tbody>
        </table>
        {paginator(total_users, pu, "/admin", {"qu":qu} if qu else {}, page_param="pu", lang=lang)}
      </div>
      <div class="two-col">
        <form class="app-form reveal" method="post" action="/admin/events/create">
          <h3>{t('admin_add_event',lang)}</h3>
          <label>{t('admin_field_title',lang)}<input name="title" required></label>
          <label>{t('admin_field_type',lang)}<input name="event_type" required></label>
          <label>{t('admin_field_date',lang)}<input name="event_date" required></label>
          <label>{t('admin_field_city',lang)}<input name="city" required></label>
          <label>{t('admin_field_desc',lang)}<textarea name="description" rows="4" required></textarea></label>
          <button class="button button-primary" type="submit">{t('admin_add_event',lang)}</button>
        </form>
        <form class="app-form reveal" method="post" action="/admin/cards/create">
          <h3>{t('admin_add_card',lang)}</h3>
          <label>{t('admin_field_cat',lang)}<input name="category" required></label>
          <label>{t('admin_field_title',lang)}<input name="title" required></label>
          <label>{t('admin_field_text',lang)}<textarea name="body" rows="4" required></textarea></label>
          <button class="button button-primary" type="submit">{t('admin_add_card',lang)}</button>
        </form>
      </div>

      <div class="table-wrap reveal">
        <h3>⏳ {t('admin_pending',lang)} ({len(pending_parts)})</h3>
        <table><thead><tr>
          <th>{t('col_name',lang)}</th><th>Email</th><th>{t('col_event',lang)}</th>
          <th>{t('col_date',lang)}</th><th>{t('col_action',lang)}</th>
        </tr></thead><tbody>{pending_rows}</tbody></table>
      </div>

      <div class="table-wrap reveal">
        <h3>{t('admin_joins',lang)}</h3>
        <table><thead><tr>
          <th>{t('col_name',lang)}</th><th>Email</th><th>{t('col_event',lang)}</th>
          <th>{t('col_status',lang)}</th><th>{t('col_date',lang)}</th>
        </tr></thead><tbody>{all_part_rows}</tbody></table>
        {paginator(total_parts, pp, "/admin", {}, page_param="pp", lang=lang)}
      </div>

      <div class="table-wrap reveal">
        <h3>{t('admin_events',lang)}</h3>
        {search_form("/admin",qe,t('search_events',lang),lang)}
        <table><thead><tr>
          <th>{t('col_title',lang)}</th><th>{t('col_type',lang)}</th>
          <th>{t('col_date',lang)}</th><th>{t('admin_field_city',lang)}</th>
          <th>{t('col_status',lang)}</th><th>{t('col_action',lang)}</th>
        </tr></thead><tbody>{ev_rows}</tbody></table>
        {paginator(total_ev, pe, "/admin", {"qe":qe} if qe else {}, page_param="pe", lang=lang)}
      </div>

      <div class="table-wrap reveal">
        <h3>{t('admin_cards',lang)}</h3>
        {search_form("/admin",qc,t('search_cards',lang),lang)}
        <table><thead><tr>
          <th>{t('col_category',lang)}</th><th>{t('col_title',lang)}</th>
          <th>{t('col_date',lang)}</th><th>{t('col_action',lang)}</th>
        </tr></thead><tbody>{card_rows}</tbody></table>
        {paginator(total_cards, pc, "/admin", {"qc":qc} if qc else {}, page_param="pc", lang=lang)}
      </div>

      <div class="table-wrap reveal">
        <h3>{t('admin_requests',lang)}</h3>
        {search_form("/admin",qr,t('search_requests',lang),lang)}
        <table><thead><tr>
          <th>{t('col_name',lang)}</th><th>Email</th><th>{t('col_message',lang)}</th>
          <th>💬</th><th>{t('col_date',lang)}</th><th>{t('col_action',lang)}</th>
        </tr></thead><tbody>{req_rows}</tbody></table>
        {paginator(total_req, pr, "/admin", {"qr":qr} if qr else {}, page_param="pr", lang=lang)}
      </div>
    </section>"""
    return layout(t('admin_label',lang), "/admin", content, user, notice, lang)


# ─── HTTP Handler ─────────────────────────────────────────────────────────────

class EcoSortHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): return

    def get_cookie(self, name):
        jar = cookies.SimpleCookie(self.headers.get("Cookie",""))
        m = jar.get(name)
        return m.value if m else None

    def get_cookie_user(self):
        return session_get_user(self.get_cookie("ecosort_session"))

    def get_lang(self):
        v = self.get_cookie("ecosort_lang")
        return v if v in ('kz','ru') else 'kz'

    def send_html(self, body, status=200, headers=None):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(data)

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def redirect(self, path, notice=""):
        if notice:
            sep = "&" if "?" in path else "?"
            path = f"{path}{sep}notice={quote(notice)}"
        self.send_response(303)
        self.send_header("Location", path)
        self.send_header("Content-Length","0")
        self.send_header("Connection","close")
        self.end_headers()

    def parse_form(self):
        length = int(self.headers.get("Content-Length","0"))
        body = self.rfile.read(length).decode("utf-8")
        return {k: v[0] for k,v in parse_qs(body).items()}

    def serve_static(self, path):
        filename  = unquote(path.removeprefix("/static/"))
        file_path = (STATIC_DIR / filename).resolve()
        if not str(file_path).startswith(str(STATIC_DIR.resolve())) or not file_path.is_file():
            self.send_error(404); return
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"
        notice = parse_qs(parsed.query).get("notice",[""])[0]
        params = parse_qs(parsed.query)
        user   = self.get_cookie_user()
        lang   = self.get_lang()

        if path.startswith("/static/"): self.serve_static(path); return

        # Переключение языка
        if path in ("/set-lang/kz", "/set-lang/ru"):
            new_lang = path.split("/")[-1]
            referer  = self.headers.get("Referer", "/")
            self.send_response(303)
            self.send_header("Location", referer)
            self.send_header("Set-Cookie", f"ecosort_lang={new_lang}; Path=/; SameSite=Lax")
            self.send_header("Content-Length","0")
            self.send_header("Connection","close")
            self.end_headers()
            return

        # API
        if path == "/api/stats":
            self.send_json({"users":row_count("users","role='user'"),"events":row_count("events"),
                            "cards":row_count("cards"),"participants":row_count("participants"),
                            "requests":row_count("support_requests")}); return
        if path == "/api/events":
            self.send_json([dict(r) for r in query_all("SELECT * FROM events ORDER BY id DESC")]); return
        if path == "/api/cards":
            self.send_json([dict(r) for r in query_all("SELECT * FROM cards ORDER BY id DESC")]); return
        if path == "/api/me":
            self.send_json(dict(user) if user else {"user":None}); return

        if path == "/logout":
            sid = self.get_cookie("ecosort_session")
            if sid: session_delete(sid)
            self.send_response(303)
            self.send_header("Location", f"/?notice={quote('Шықтыңыз / Вы вышли')}")
            self.send_header("Set-Cookie","ecosort_session=; Path=/; Max-Age=0; SameSite=Lax; HttpOnly")
            self.send_header("Content-Length","0"); self.send_header("Connection","close"); self.end_headers(); return

        if path == "/reset-password":
            token = params.get("token",[""])[0]
            self.send_html(reset_password_page(token, user, notice, params, lang)); return

        # Страница переписки поддержки
        if path.startswith("/support/thread/"):
            parts = path.split("/")
            if len(parts) >= 4 and parts[3].isdigit():
                self.send_html(support_thread_page(int(parts[3]), user, notice, params, lang)); return
            self.send_error(404); return

        pages = {
            "/": home_page,
            "/login":    lambda u,n,p,l: auth_page("login",    u,n,p,l),
            "/register": lambda u,n,p,l: auth_page("register", u,n,p,l),
            "/profile":  profile_page,
            "/events":   events_page,
            "/cards":    cards_page,
            "/map":      map_page,
            "/encyclopedia": encyclopedia_page,
            "/quiz":     quiz_page,
            "/support":  support_page,
            "/admin":    admin_page,
            "/forgot-password": forgot_password_page,
        }
        page = pages.get(path)
        if not page: self.send_error(404); return
        self.send_html(page(user, notice, params, lang))

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"
        form   = self.parse_form()
        user   = self.get_cookie_user()
        lang   = self.get_lang()

        # Регистрация
        if path == "/register":
            name = form.get("name","").strip()
            email = form.get("email","").strip().lower()
            city  = form.get("city","").strip()
            pw    = form.get("password","")
            if not name or not email or not city or len(pw)<4:
                self.redirect("/register", t('fill_all',lang)); return
            try:
                with db() as conn:
                    cur = conn.execute("INSERT INTO users(name,email,city,password_hash,role,created_at) VALUES(?,?,?,?,'user',?)",
                                       (name,email,city,password_hash(pw),now()))
                    uid = cur.lastrowid
            except sqlite3.IntegrityError:
                self.redirect("/register","Email уже занят / Email бар."); return
            sid = session_create(uid)
            self.send_response(303)
            self.send_header("Location",f"/profile?notice={quote('Тіркелді / Регистрация выполнена')}")
            self.send_header("Set-Cookie",f"ecosort_session={sid}; Path=/; SameSite=Lax; HttpOnly")
            self.send_header("Content-Length","0"); self.send_header("Connection","close"); self.end_headers(); return

        # Вход
        if path == "/login":
            email = form.get("email","").strip().lower()
            pw    = form.get("password","")
            found = query_one("SELECT * FROM users WHERE email=?", (email,))
            if not found or not check_password(pw, found["password_hash"]):
                self.redirect("/login","Қате email немесе құпия сөз / Неверный email или пароль."); return
            if dict(found).get("status","active") == "banned":
                self.redirect("/login", t('banned_notice', lang)); return
            sid = session_create(found["id"])
            target = "/admin" if found["role"]=="admin" else "/profile"
            self.send_response(303)
            self.send_header("Location",f"{target}?notice={quote('Кірдіңіз / Вход выполнен')}")
            self.send_header("Set-Cookie",f"ecosort_session={sid}; Path=/; SameSite=Lax; HttpOnly")
            self.send_header("Content-Length","0"); self.send_header("Connection","close"); self.end_headers(); return

        # Участие в акции
        if path.startswith("/events/") and path.endswith("/join"):
            if not user or user["role"]!="user":
                self.redirect("/login","Алдымен кіріңіз / Сначала войдите."); return
            parts = path.split("/")
            if len(parts)<3 or not parts[2].isdigit(): self.send_error(404); return
            event_id = int(parts[2])
            ev = query_one("SELECT id FROM events WHERE id=? AND status='upcoming'", (event_id,))
            if not ev: self.redirect("/events","Акция жоқ / Акция не найдена."); return
            try:
                with db() as conn:
                    conn.execute("INSERT INTO participants(user_id,event_id,status,created_at) VALUES(?,?,'pending',?)",
                                 (user["id"],event_id,now()))
            except sqlite3.IntegrityError:
                self.redirect("/events","Өтінім бар / Уже участвуете."); return
            self.redirect("/profile","Өтінім жіберілді, әкімші қарайды / Заявка отправлена — ожидайте решения."); return

        # Квиз
        if path == "/quiz":
            if not user or user["role"]!="user":
                self.redirect("/login","Кіріңіз."); return
            correct = sum(1 for q in QUIZ_QUESTIONS
                          if form.get(q["id"],"").isdigit() and int(form[q["id"]])==q["correct"])
            score = round(correct/len(QUIZ_QUESTIONS)*100)
            with db() as conn:
                conn.execute("INSERT INTO test_results(user_id,score,created_at) VALUES(?,?,?)", (user["id"],score,now()))
            self.redirect("/profile",f"Тест: {correct}/{len(QUIZ_QUESTIONS)} ({score}%)"); return

        # Сброс пароля: запрос
        if path == "/forgot-password":
            email = form.get("email","").strip().lower()
            if not email or "@" not in email: self.redirect("/forgot-password",t('fill_all',lang)); return
            found = query_one("SELECT * FROM users WHERE email=?", (email,))
            if found:
                token = reset_token_create(found["id"])
                url   = f"http://{HOST}:{PORT}/reset-password?token={token}"
                if not send_reset_email(email, url):
                    self.redirect("/forgot-password",f"ДЕМО: {url}"); return
            self.redirect("/forgot-password","Хат жіберілді / Письмо отправлено."); return

        # Сброс пароля: сохранение
        if path == "/reset-password":
            token = form.get("token","").strip()
            pw    = form.get("password","")
            pw2   = form.get("password2","")
            if len(pw)<4: self.redirect(f"/reset-password?token={quote(token)}","Мин. 4 символ."); return
            if pw!=pw2:   self.redirect(f"/reset-password?token={quote(token)}","Сәйкес келмейді."); return
            found = reset_token_get_user(token)
            if not found: self.redirect("/forgot-password","Сілтеме ескірді."); return
            with db() as conn:
                conn.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash(pw),found["id"]))
            reset_token_delete(token)
            self.redirect("/login","Құпия сөз өзгертілді / Пароль изменён."); return

        # Поддержка: новый запрос
        if path == "/support":
            name    = form.get("name","").strip()
            email   = form.get("email","").strip()
            message = form.get("message","").strip()
            if not all([name,email,message]) or "@" not in email:
                self.redirect("/support",t('fill_all',lang)); return
            with db() as conn:
                uid = user["id"] if user else None
                cur = conn.execute("INSERT INTO support_requests(name,email,message,user_id,created_at) VALUES(?,?,?,?,?)",
                                   (name,email,message,uid,now()))
                req_id = cur.lastrowid
                conn.execute("INSERT INTO support_messages(request_id,sender,message,created_at) VALUES(?,?,?,?)",
                             (req_id,'user',message,now()))
            self.redirect("/support","Сұрау жіберілді / Запрос отправлен."); return

        # Переписка: пользователь отправляет follow-up
        if path.startswith("/support/thread/") and path.endswith("/message"):
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            req_id = int(parts[3])
            req = query_one("SELECT * FROM support_requests WHERE id=?", (req_id,))
            if not req or (req["user_id"] and (not user or user["id"]!=req["user_id"])):
                self.redirect("/support","Қол жетімді емес / Нет доступа."); return
            msg = form.get("message","").strip()
            if not msg: self.redirect(f"/support/thread/{req_id}","Хабарлама бос."); return
            with db() as conn:
                conn.execute("INSERT INTO support_messages(request_id,sender,message,created_at) VALUES(?,?,?,?)",
                             (req_id,'user',msg,now()))
            self.redirect(f"/support/thread/{req_id}","Жіберілді / Отправлено."); return

        # Переписка: Admin отвечает
        if path.startswith("/admin/support/") and path.endswith("/reply"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым салынған."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            req_id = int(parts[3])
            reply  = form.get("reply","").strip()
            if not reply: self.redirect(f"/support/thread/{req_id}","Бос."); return
            with db() as conn:
                conn.execute("INSERT INTO support_messages(request_id,sender,message,created_at) VALUES(?,?,?,?)",
                             (req_id,'admin',reply,now()))
                conn.execute("UPDATE support_requests SET status='answered' WHERE id=?", (req_id,))
            self.redirect(f"/support/thread/{req_id}","Жауап жіберілді / Ответ отправлен."); return

        # Admin: заблокировать / разблокировать пользователя
        if path.startswith("/admin/users/") and path.endswith("/ban"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            uid = int(parts[3])
            target_user = query_one("SELECT status FROM users WHERE id=? AND role='user'", (uid,))
            if not target_user: self.redirect("/admin","Пайдаланушы табылмады."); return
            new_status = "banned" if target_user.get("status","active")=="active" else "active"
            with db() as conn:
                conn.execute("UPDATE users SET status=? WHERE id=?", (new_status, uid))
                # При бане — удаляем все активные сессии
                if new_status == "banned":
                    conn.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
            msg = t('user_banned',lang) if new_status=="banned" else t('user_active',lang)
            self.redirect("/admin", f"{msg}"); return

        # Admin: сбросить историю пользователя
        if path.startswith("/admin/users/") and path.endswith("/reset"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            uid = int(parts[3])
            with db() as conn:
                conn.execute("DELETE FROM participants WHERE user_id=?", (uid,))
                conn.execute("DELETE FROM test_results WHERE user_id=?", (uid,))
            self.redirect("/admin", t('btn_reset_acc',lang)); return

        # Admin: удалить пользователя
        if path.startswith("/admin/users/") and path.endswith("/delete"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            uid = int(parts[3])
            with db() as conn:
                conn.execute("DELETE FROM users WHERE id=? AND role='user'", (uid,))
            self.redirect("/admin", t('btn_delete',lang)); return

        # Admin: принять заявку
        if path.startswith("/admin/participants/") and path.endswith("/accept"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            pid = int(parts[3])
            with db() as conn:
                conn.execute("UPDATE participants SET status='accepted' WHERE id=?", (pid,))
            self.redirect("/admin",t('accepted',lang)); return

        # Admin: отклонить заявку
        if path.startswith("/admin/participants/") and path.endswith("/reject"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            pid = int(parts[3])
            with db() as conn:
                conn.execute("UPDATE participants SET status='rejected' WHERE id=?", (pid,))
            self.redirect("/admin",t('rejected',lang)); return

        # Admin: toggle event status
        if path.startswith("/admin/events/") and path.endswith("/toggle"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            ev_id = int(parts[3])
            ev = query_one("SELECT status FROM events WHERE id=?", (ev_id,))
            if not ev: self.redirect("/admin","Табылмады."); return
            new_st = "past" if ev["status"]=="upcoming" else "upcoming"
            with db() as conn:
                conn.execute("UPDATE events SET status=? WHERE id=?", (new_st,ev_id))
            self.redirect("/admin",t('btn_complete' if new_st=='past' else 'btn_activate',lang)); return

        # Admin: delete event
        if path.startswith("/admin/events/") and path.endswith("/delete"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            with db() as conn:
                conn.execute("DELETE FROM events WHERE id=?", (int(parts[3]),))
            self.redirect("/admin",t('deleted_event',lang)); return

        # Admin: add event
        if path == "/admin/events/create":
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            fields = {k: form.get(k,"").strip() for k in ["title","event_type","event_date","city","description"]}
            if not all(fields.values()): self.redirect("/admin",t('fill_all',lang)); return
            with db() as conn:
                conn.execute("INSERT INTO events(title,event_type,event_date,city,description,status,created_at) VALUES(?,?,?,?,?,'upcoming',?)",
                             (*fields.values(),now()))
            self.redirect("/admin",t('added_event',lang)); return

        # Admin: delete card
        if path.startswith("/admin/cards/") and path.endswith("/delete"):
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            parts = path.split("/")
            if len(parts)<4 or not parts[3].isdigit(): self.send_error(404); return
            with db() as conn:
                conn.execute("DELETE FROM cards WHERE id=?", (int(parts[3]),))
            self.redirect("/admin",t('deleted_card',lang)); return

        # Admin: add card
        if path == "/admin/cards/create":
            if not user or user["role"]!="admin": self.redirect("/admin","Тыйым."); return
            category = form.get("category","").strip()
            title    = form.get("title","").strip()
            body     = form.get("body","").strip()
            if not all([category,title,body]): self.redirect("/admin",t('fill_all',lang)); return
            with db() as conn:
                conn.execute("INSERT INTO cards(category,title,body,created_at) VALUES(?,?,?,?)", (category,title,body,now()))
            self.redirect("/admin",t('added_card',lang)); return

        self.send_error(404)


def main():
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), EcoSortHandler)
    print(f"EcoSort → http://{HOST}:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    main()
