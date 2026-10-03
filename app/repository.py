"""Stores tickets in SQLite."""
import sqlite3
import threading
from datetime import datetime

from app.workflow import is_overdue, sla_due

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    priority    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'OPEN',
    created_at  TEXT NOT NULL,
    due_at      TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""


class TicketRepository:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.conn.execute(SCHEMA)
            self.conn.commit()

    @staticmethod
    def _to_dict(row):
        ticket = dict(row)
        for key in ("created_at", "due_at", "updated_at"):
            ticket[key] = datetime.fromisoformat(ticket[key])
        ticket["overdue"] = is_overdue(ticket)
        return ticket

    def create(self, title, description, priority, now=None):
        now = now or datetime.now()
        due = sla_due(priority, now)
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO tickets (title, description, priority, status, created_at, due_at, updated_at)"
                " VALUES (?, ?, ?, 'OPEN', ?, ?, ?)",
                (title, description, priority, now.isoformat(), due.isoformat(), now.isoformat()),
            )
            self.conn.commit()
        return self.get(cur.lastrowid)

    def get(self, ticket_id):
        with self.lock:
            row = self.conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return self._to_dict(row) if row else None

    def list(self, status=None, priority=None):
        sql, params = "SELECT * FROM tickets WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if priority:
            sql += " AND priority = ?"
            params.append(priority)
        sql += " ORDER BY id"
        with self.lock:
            rows = self.conn.execute(sql, params).fetchall()
        return [self._to_dict(r) for r in rows]

    def update_status(self, ticket_id, status):
        with self.lock:
            self.conn.execute(
                "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), ticket_id),
            )
            self.conn.commit()
        return self.get(ticket_id)

    def delete(self, ticket_id):
        with self.lock:
            cur = self.conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            self.conn.commit()
        return cur.rowcount > 0
