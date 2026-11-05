"""SQLite: материалы дайджеста и ваши ошибки для воскресного разбора."""
import sqlite3
from contextlib import closing

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    category    TEXT,
    kind        TEXT NOT NULL DEFAULT 'article',   -- article | podcast
    audio_url   TEXT,
    description TEXT,
    blurb       TEXT,       -- одна строка для дайджеста
    text        TEXT,       -- текст статьи или расшифровка подкаста
    summary     TEXT,       -- краткое содержание для обсуждения
    simple      TEXT,       -- пересказ на уровне B1
    sent_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS errors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER,
    original    TEXT NOT NULL,
    corrected   TEXT NOT NULL,
    explanation TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

ITEM_FIELDS = {"url", "title", "category", "kind", "audio_url", "description",
               "blurb", "text", "summary", "simple"}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _write(sql: str, params=()) -> int:
    with closing(_connect()) as conn, conn:
        return conn.execute(sql, params).lastrowid


def _read(sql: str, params=()) -> list[dict]:
    with closing(_connect()) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def init() -> None:
    with closing(_connect()) as conn:
        conn.executescript(SCHEMA)


def seen_urls() -> set[str]:
    return {row["url"] for row in _read("SELECT url FROM items")}


def add_item(**fields) -> int:
    fields = {k: v for k, v in fields.items() if k in ITEM_FIELDS}
    cols = ", ".join(fields)
    marks = ", ".join("?" for _ in fields)
    return _write(f"INSERT INTO items ({cols}) VALUES ({marks})", tuple(fields.values()))


def get_item(item_id: int) -> dict | None:
    rows = _read("SELECT * FROM items WHERE id = ?", (item_id,))
    return rows[0] if rows else None


def update_item(item_id: int, **fields) -> None:
    fields = {k: v for k, v in fields.items() if k in ITEM_FIELDS}
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    _write(f"UPDATE items SET {sets} WHERE id = ?", (*fields.values(), item_id))


def add_errors(item_id: int, corrections: list[dict]) -> None:
    for c in corrections:
        _write(
            "INSERT INTO errors (item_id, original, corrected, explanation) VALUES (?, ?, ?, ?)",
            (item_id, c["original"], c["corrected"], c.get("explanation", "")),
        )


def errors_since(days: int) -> list[dict]:
    return _read(
        "SELECT original, corrected, explanation FROM errors "
        "WHERE created_at >= datetime('now', ?) ORDER BY id",
        (f"-{days} days",),
    )
