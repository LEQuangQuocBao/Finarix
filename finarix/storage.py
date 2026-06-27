import json
import os
import sys

_current_key: bytes | None = None


def set_key(key: bytes) -> None:
    global _current_key
    _current_key = key


def get_key() -> bytes | None:
    return _current_key


def data_dir() -> str:
    if hasattr(sys, '_MEIPASS'):
        # Packaged exe: use %APPDATA%\Finarix so data survives reinstalls
        base = os.path.join(
            os.environ.get('APPDATA', os.path.expanduser('~')), 'Finarix')
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.dirname(here)
    d = os.path.join(base, 'data')
    os.makedirs(d, exist_ok=True)
    return d


def month_path(year: int, month: int) -> str:
    return os.path.join(data_dir(), f"{year:04d}-{month:02d}.json")


def load_month_file(year: int, month: int):
    p = month_path(year, month)
    if not os.path.exists(p):
        return None
    with open(p, 'rb') as fh:
        raw = fh.read()
    if _current_key:
        try:
            from cryptography.fernet import Fernet, InvalidToken
            raw = Fernet(_current_key).decrypt(raw)
        except Exception:
            pass  # plaintext fallback for migration
    return json.loads(raw)


def save_month_file(year: int, month: int, payload: dict) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
    if _current_key:
        from cryptography.fernet import Fernet
        data = Fernet(_current_key).encrypt(data)
    with open(month_path(year, month), 'wb') as fh:
        fh.write(data)


def next_ym(y: int, m: int): return (y + 1, 1) if m == 12 else (y, m + 1)
def prev_ym(y: int, m: int): return (y - 1, 12) if m == 1 else (y, m - 1)
