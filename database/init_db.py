import sqlite3
import os

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db(db_path):
    with get_db(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE,
                email       TEXT UNIQUE,
                password    TEXT,
                line_id     TEXT UNIQUE,
                display_name TEXT,
                avatar_url  TEXT,
                role        TEXT DEFAULT 'user',
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS cases (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                location    TEXT,
                lat         REAL,
                lng         REAL,
                animal_type TEXT DEFAULT '不明',
                status      TEXT DEFAULT 'open',
                source      TEXT DEFAULT 'user',
                source_url  TEXT,
                image_url   TEXT,
                reporter_id INTEGER,
                handler_id  INTEGER,
                handled_at  TEXT,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                updated_at  TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (reporter_id) REFERENCES users(id),
                FOREIGN KEY (handler_id)  REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS case_notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id    INTEGER NOT NULL,
                user_id    INTEGER NOT NULL,
                note       TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (case_id) REFERENCES cases(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
    print(f"[DB] 初始化完成：{db_path}")
