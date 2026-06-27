import json
import os
import sys


def data_dir():
    if hasattr(sys, '_MEIPASS'):
        base = os.path.dirname(sys.executable)
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.dirname(here)  # up from finarix/ to project root
    d = os.path.join(base, 'data')
    os.makedirs(d, exist_ok=True)
    return d


def month_path(year, month):
    return os.path.join(data_dir(), f"{year:04d}-{month:02d}.json")


def load_month_file(year, month):
    p = month_path(year, month)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    return None


def save_month_file(year, month, payload):
    with open(month_path(year, month), 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def next_ym(y, m): return (y + 1, 1) if m == 12 else (y, m + 1)
def prev_ym(y, m): return (y - 1, 12) if m == 1 else (y, m - 1)
