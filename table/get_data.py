from datetime import datetime, date
from typing import Optional, List, Dict, Tuple, Iterable
from google.oauth2.service_account import Credentials
from table.table_config import TZ, PLATFORMS
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import gspread, os 

load_dotenv()
SHEET_KEY = os.getenv('SHEET_KEY')

def today_ru(now: Optional[datetime] = None) -> str:
    months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
    d = now or datetime.now(ZoneInfo(TZ))
    return f'{d.day} {months[d.month - 1]} {d.year}'

def _parse_sheet_date_cell(s: str) -> Optional[date]:
    s = str(s).strip()
    try:
        return datetime.strptime(s, '%d.%m.%Y').date()
    except Exception:
        parts = s.replace('  ', ' ').split()
        months = {'января':1,'февраля':2,'марта':3,'апреля':4,'мая':5,'июня':6,'июля':7,'августа':8,'сентября':9,'октября':10,'ноября':11,'декабря':12}
        if len(parts) >= 3 and parts[1] in months:
            try:
                return date(int(parts[2]), months[parts[1]], int(parts[0]))
            except Exception:
                return None
    return None

def find_today_row(sheet, now: Optional[datetime] = None) -> Optional[int]:
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

def _flatten_col_range(raw: List[List[str]], need_len: int) -> List[str]:
    out = []
    src = raw or []
    for i in range(need_len):
        if i < len(src):
            row = src[i]
            out.append(str(row[0]).strip() if row and len(row) > 0 else '')
        else:
            out.append('')
    return out

def _batch_read_columns(sheet, cols: List[str], r1: int, r2: int) -> Dict[str, List[str]]:
    ranges = [f'{c}{r1}:{c}{r2}' for c in cols]
    packs = sheet.batch_get(ranges)
    need = r2 - r1 + 1
    out: Dict[str, List[str]] = {}
    for c, raw in zip(cols, packs):
        out[c] = _flatten_col_range(raw, need)
    return out

def batch_read_cells(sheet, row: int, platforms) -> List[str]:
    ranges = [f'{col}{row}' for _, col in platforms]
    values = sheet.batch_get(ranges)
    flat = []
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
    row = find_today_row(sheet, now = now)
    if row is None:
        return None
    cell_texts = batch_read_cells(sheet, row, PLATFORMS)
    non_empty = []
    for (place, _), text in zip(PLATFORMS, cell_texts):
        if text:
            non_empty.append((place, text))
    return non_empty

def _col_to_index(col: str) -> int:
    col = col.strip().upper()
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n

def get_sheet_start_date(sheet) -> Optional[date]:
    col_a = sheet.col_values(1)
    for v in col_a:
        d = _parse_sheet_date_cell(v)
        if d:
            return d
    return None

def get_rows_between(sheet, d_from: date, d_to: date) -> List[int]:
    col_a = sheet.col_values(1)
    rows = []
    for i, v in enumerate(col_a, start = 1):
        d = _parse_sheet_date_cell(v)
        if d and d_from <= d <= d_to:
            rows.append(i)
    return rows

def group_platforms() -> Dict[str, List[str]]:
    g: Dict[str, List[str]] = {}
    for name, col in PLATFORMS:
        g.setdefault(name, []).append(col)
    return g

def _is_ad_text(s: str) -> bool:
    return 'реклама' in str(s).strip().lower()

def count_posts_between(sheet, rows: List[int], groups: Dict[str, List[str]]) -> Dict[str, int]:
    if not rows:
        return {k: 0 for k in groups.keys()}
    r1 = min(rows)
    r2 = max(rows)
    use = set(rows)
    all_cols: List[str] = sorted({c for cols in groups.values() for c in cols})
    contents = _batch_read_columns(sheet, all_cols, r1, r2)
    ads = _batch_read_columns(sheet, all_cols, r1 + 2, r2 + 2)
    out: Dict[str, int] = {}
    for name, cols in groups.items():
        cnt = 0
        for c in cols:
            vals = contents[c]
            advs = ads.get(c, [])
            for i in range(r2 - r1 + 1):
                rownum = r1 + i
                if rownum not in use:
                    continue
                val = vals[i] if i < len(vals) else ''
                adv = advs[i] if i < len(advs) else ''
                if str(val).strip() and not _is_ad_text(adv):
                    cnt += 1
        out[name] = cnt
    return out

def _val_at(col_vals: List[str], idx1: int) -> str:
    i = idx1 - 1
    return str(col_vals[i]).strip() if 0 <= i < len(col_vals) else ''

def last_non_ad_date_bulk(sheet, groups: Dict[str, List[str]], names: Iterable[str]) -> Dict[str, Optional[date]]:
    col_a = sheet.col_values(1)
    max_row = len(col_a)
    uniq_cols: List[str] = sorted({c for n in names for c in groups.get(n, [])})
    col_cache: Dict[str, List[str]] = {}
    for c in uniq_cols:
        col_cache[c] = sheet.col_values(_col_to_index(c))
    res: Dict[str, Optional[date]] = {}
    for name in names:
        best_row = 0
        for c in groups.get(name, []):
            col_vals = col_cache[c]
            i = max(len(col_vals), max_row)
            while i >= 1:
                v = _val_at(col_vals, i)
                if v:
                    adv = _val_at(col_vals, i + 2)
                    if not _is_ad_text(adv):
                        best_row = max(best_row, i)
                        break
                i -= 1
        if best_row > 0:
            res[name] = _parse_sheet_date_cell(_val_at(col_a, best_row))
        else:
            res[name] = None
    return res
