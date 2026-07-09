"""
SQLite 记忆系统 — 会话间持久记忆
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


class Memory:
    """持久化对话记忆"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / "projects/cet-ai-tutor/data/memory.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_message(self, role: str, content: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def get_history(self, limit: int = 20) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def save_fact(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO user_facts (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def get_fact(self, key: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT value FROM user_facts WHERE key = ?", (key,)
        ).fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_facts(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT key, value FROM user_facts").fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

    def clear_history(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM conversations")
        conn.commit()
        conn.close()
