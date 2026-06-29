import json
import os
from config import HISTORY_FILE, DEFAULT_LANGUAGE

_db = {}


def _load():
    global _db
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            _db = json.load(f)


def _save():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(_db, f, ensure_ascii=False, indent=2)


def get_lang(uid):
    _load()
    return _db.get(str(uid), {}).get("lang", DEFAULT_LANGUAGE)


def set_lang(uid, lang):
    _load()
    k = str(uid)
    if k not in _db:
        _db[k] = {"lang": lang, "records": []}
    else:
        _db[k]["lang"] = lang
    _save()


def save_record(uid, record):
    _load()
    k = str(uid)
    if k not in _db:
        _db[k] = {"lang": DEFAULT_LANGUAGE, "records": []}
    _db[k].setdefault("records", []).append(record)
    _db[k]["records"] = _db[k]["records"][-20:]
    _save()


def get_records(uid):
    _load()
    return _db.get(str(uid), {}).get("records", [])


def get_last(uid):
    r = get_records(uid)
    return r[-1] if r else None
