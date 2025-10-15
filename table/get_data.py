from __future__ import annotations

import gspread, os 
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from typing import List, Optional, Tuple
from google.oauth2.service_account import Credentials

from table.table_config import TZ, PLATFORMS

load_dotenv()
SHEET_KEY = os.getenv('SHEET_KEY')

def today_ru(now: Optional[datetime] = None) -> str:
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    d = now or datetime.now(ZoneInfo(TZ))
    return f'{d.day} {months[d.month - 1]} {d.year}'


def find_today_row(sheet, now: Optional[datetime] = None) -> Optional[int]:
    col_a = sheet.col_values(1)
    target = today_ru(now)
    target_dot = (now or datetime.now(ZoneInfo(TZ))).strftime('%d.%m.%Y')
    for i, val in enumerate(col_a, start=1):
        if not val:
            continue
        s = str(val).strip()
        if target in s or target_dot in s:
            return i
    return None


def batch_read_cells(sheet, row: int, platforms) -> List[str]:
    ranges = [f'{col}{row}' for _, col in platforms]
    values = sheet.batch_get(ranges)
    flat: List[str] = []
    for v in values:
        if v and v[0]:
            flat.append(str(v[0][0]).strip())
        else:
            flat.append('')
    return flat


def get_worksheet():
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file('service_account.json', scopes = scopes)
    return gspread.authorize(creds).open_by_key(SHEET_KEY).sheet1


def get_today_items(now: Optional[datetime] = None) -> Optional[List[Tuple[str, str]]]:
    sheet = get_worksheet()
    row = find_today_row(sheet, now=now)
    if row is None:
        return None

    cell_texts = batch_read_cells(sheet, row, PLATFORMS)
    non_empty: List[Tuple[str, str]] = []
    for (place, _), text in zip(PLATFORMS, cell_texts):
        if text:
            non_empty.append((place, text))
    return non_empty
