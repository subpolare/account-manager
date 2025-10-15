import random
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
from google.oauth2.service_account import Credentials

TZ = 'Europe/Moscow'

PLATFORMS = [
    ('Пост в Telegram-канале ТОПЛЕС', 'D'),
    ('Пост в Telegram-канале ТОПЛЕС', 'E'),
    ('Пост в Telegram-канале ТОПЛЕС', 'F'),
    ('Stories в Telegram-канале ТОПЛЕС', 'G'),
    ('Пост в личном телеграм-канале Яна', 'J'),
    ('Пост в ВКонтакте', 'M'),
    ('Stories ВКонтакте', 'L'),
    ('ВК Клипы', 'N'),
    ('Личный ВК Яна', 'P'),
    ('Пост в Instagram', 'T'),
    ('Instagram Reels', 'R'),
    ('Stories в Instagram', 'S'),
    ('Пост в YouTube', 'V'),
    ('Shorts в YouTube', 'W'),
    ('TikTok', 'Y'),
    ('Дзен', 'AA'),
    ('1 уровень Boosty', 'AC'),
    ('2 уровень Boosty', 'AD'),
    ('3 уровень Boosty', 'AE'),
]

GREETINGS = [
    'Пути к счастью нет: счастье — это путь',
    'Главное препятствие на пути понимания дзэн — попытка понять дзэн.',
    'Хочешь понять других — пристальнее смотри в самого себя...',
    'ЪУЪ',
    'Матрица повсюду!',
    'Слава всегда найдёт того, кто идёт по верной дороге.',
    'Следуйте за белым кроликом.',
    'После хорошего обеда можно простить кого угодно.',
    'Пусть это будет маленькая сплетня, которая должна исчезнуть между нами...',
    'Доброе утро, последние герои! Доброе утро вам и таким, как вы.',
    'Астрологи провозгласили неделю зарплаты!',
    'Больше конечностей означает больше обнимашек.',
    'Можно вернуть на место все, что угодно, кроме пыли. Пыль красноречива.',
    'Вы рассуждаете совсем как Спок...',
    'Главное препятствие на пути понимания дзэн — попытка понять дзэн...',
    'O RLY!',
    'Я не умею выражать сильных чувств, хотя могу сильно выражаться.',
    'Солнце светит — хорошо, не светит — тоже хорошо, вы сами себе солнце.',
    'All your base are belong to us.',
    'Что за великолепное утро?',
    'Тот, кто владеет штанами — владеет миром!',
    'Потрогайте траву...',
    'Кого ни встретишь, все спрашивают: не знаком ли я с вами?',
    'Нужно больше золота!',
    'Мы взрослеем и праздников становится все меньше :(',
    'Хорошие друзья, хорошие книги и спящая совесть — вот идеальная жизнь!',
    'Нужно хранить то, что любишь.',
    'Верните мне мой 2007!',
    'Вжух, вас посетил кот-волшебник!',
    'Меня тоже вела дорога приключений!',
    'Человеку иногда надо вкусить немного безумия, чтобы освежить вкус к жизни.',
    'Секрет быть скучным состоит в умении рассказать о себе всё.',
    'Умение слышать помогает не пропустить самое важное...',
    'Проснитесь и пойте!',
]

def today_ru(now = None):
    months = [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]
    d = now or datetime.now(ZoneInfo(TZ))
    return f'{d.day} {months[d.month - 1]} {d.year}'

def find_today_row(sheet, now = None):
    col_a = sheet.col_values(1)
    target = today_ru(now)
    target_dot = (now or datetime.now(ZoneInfo(TZ))).strftime('%d.%m.%Y')
    for i, val in enumerate(col_a, start = 1):
        if not val:
            continue
        s = str(val).strip()
        if target in s or target_dot in s:
            return i
    return None

def batch_read_cells(sheet, row, platforms):
    ranges = [f'{col}{row}' for _, col in platforms]
    values = sheet.batch_get(ranges)
    flat = []
    for v in values:
        if v and v[0]:
            flat.append(str(v[0][0]).strip())
        else:
            flat.append('')
    return flat

def build_digest(items):
    greeting = random.choice(GREETINGS)
    lines = [
        '@subpolare @johnnywhale',
        f'☀️ {greeting}\n\n*Сегодня вам предстоит опубликовать 💎 {len(items)} единиц{"ы" if len(items) <= 4 else ""} контента*',
        ''
    ]
    for i, (place, text) in enumerate(items, start = 1):
        text = text.replace('\n', ' ')
        lines.append(f'{i}. {place}: {text}')
    return '\n'.join(lines)

def generate_digest():
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file('service_account.json', scopes = scopes)
    sheet = gspread.authorize(creds).open_by_key('1Fw-IE94KHnTd7RvcbF6d2lbNUm1JTTFp5eELI5RXbXA').sheet1

    row = find_today_row(sheet)
    if row is None:
        return 'Дата на сегодня в столбце A не найдена.'
    cell_texts = batch_read_cells(sheet, row, PLATFORMS)
    non_empty = []
    for (place, _), text in zip(PLATFORMS, cell_texts):
        if text:
            non_empty.append((place, text))
    return build_digest(non_empty)

if __name__ == '__main__':
    print(generate_digest())
