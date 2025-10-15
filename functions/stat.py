from datetime import datetime, date
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from utils.typing_task import keep_typing
from table.get_data import get_worksheet, get_sheet_start_date, get_rows_between, group_platforms, count_posts_between, last_non_ad_date_bulk

def _parse_input_date(s: str) -> date:
    return datetime.strptime(s.strip(), '%d.%m.%Y').date()

def _ru_days(n: int) -> str:
    n10 = n % 10
    n100 = n % 100
    if n10 == 1 and n100 != 11:
        return 'день'
    if n10 in (2, 3, 4) and n100 not in (12, 13, 14):
        return 'дня'
    return 'дней'

def _fmt_ddmmyyyy(d: date | None) -> str:
    return d.strftime('%d.%m.%Y') if d else '—'

def _ru_date_text(d: date) -> str:
    months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
    return f'{d.day} {months[d.month - 1]} {d.year} года'

def _build_report(sheet, d_from: date, d_to: date) -> str:
    rows = get_rows_between(sheet, d_from, d_to)
    groups = group_platforms()
    counts = count_posts_between(sheet, rows, groups)
    names = list(groups.keys())
    non_zero = [(n, counts.get(n, 0)) for n in names if counts.get(n, 0) > 0]
    zero = [n for n in names if counts.get(n, 0) == 0]
    span = (d_to - d_from).days + 1
    header = f'📝 *ОТЧЕТ ЗА {_fmt_ddmmyyyy(d_from)} – {_fmt_ddmmyyyy(d_to)}*\n\n✅ *Вот, сколько всего мы опубликовали за эти {span} { _ru_days(span)}*'
    lines = [header, '']

    vk, insta, yt, tiktok, dzen, boosty = False, False, False, False, False, False
    for i, (name, cnt) in enumerate(non_zero, start = 1):
        if 'ВКонтакте' in name and not vk: 
            lines.append(f'')
            vk = True 
        if 'Instagram' in name and not insta:  
            lines.append(f'')
            insta = True 
        if 'YouTube' in name and not yt:  
            lines.append(f'')
            yt = True 
        if 'TikTok' in name and not tiktok:  
            lines.append(f'')
            tiktok = True 
        # if 'Дзен' in name and not dzen:  
        #     lines.append(f'')
        #     dzen = True 
        if 'Boosty' in name and not boosty:  
            lines.append(f'')
            boosty = True 
        lines.append(f'{i}. {name} — {cnt}')

    if zero:
        last_map = last_non_ad_date_bulk(sheet, groups, zero)
        lines.append('')
        lines.append('❌ *Но есть площадки, в которых мы ничего не опубликовали*')
        lines.append('')
        for i, name in enumerate(zero, start = 1):
            last = last_map.get(name)
            if last and last > date.today():
                lines.append(f'{i}. {name}: последний контент был до появления Влада (8 октября 2025)')
            else:
                lines.append(f'{i}. {name}: последний контент был { _fmt_ddmmyyyy(last) }')
    else:
        lines.append('')
        lines.append('_TL;DR: Контент выходил на всех наших площадках_')
    return '\n'.join(lines)

@keep_typing
async def cmd_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text('⚠️ Ошибка: Надо вызывать команду в формате «/stat DD.MM.YYYY DD.MM.YYYY»', parse_mode = None)
        return
    try:
        d_from = _parse_input_date(context.args[0])
        d_to = _parse_input_date(context.args[1])
    except Exception:
        await update.message.reply_text('⚠️ Ошибка: Надо вызывать команду в формате «/stat DD.MM.YYYY DD.MM.YYYY»', parse_mode = None)
        return
    if d_from > d_to:
        d_from, d_to = d_to, d_from
    def _work() -> str:
        sheet = get_worksheet()
        start = get_sheet_start_date(sheet)
        if start and d_from < start:
            return f'⚠️ Ошибка: Мы начали вести таблицу с { _ru_date_text(start) }'
        return _build_report(sheet, d_from, d_to)
    text = await asyncio.to_thread(_work)
    await update.message.reply_text(text, disable_web_page_preview = True, parse_mode = 'Markdown')
