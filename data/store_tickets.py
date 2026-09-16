"""SQLite-backed ticket store for the IT helpdesk MCP server.

Named ticket_store, not db: a PyPI package literally called db
exists, and on a machine where it happens to be installed, a
same-named local module can get shadowed by it instead of the file
sitting right next to server.py. Renaming it removes the ambiguity
outright, rather than debugging import order every time this repo
runs on a different machine.

Everything else in this project is a plain in-memory dict. This file
exists specifically to give search_tickets a real database to query,
because the vulnerability in this post's scenario doesn't exist
against a Python dict, it needs an actual SQL statement to inject
into.
"""

import pathlib
import sqlite3

from mock_data import TICKETS

# Resolved from this file's own location, one level up from mcp/,
# so the database lives in its own top-level data/ folder, sibling
# to agent/ and mcp/, instead of inside the server's source tree.
DB_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "helpdesk.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            requester TEXT,
            subject TEXT,
            status TEXT
        )
        """
    )
    for ticket_id, data in TICKETS.items():
        conn.execute(
            "INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?)",
            (ticket_id, data["requester"], data["subject"], data["status"]),
        )
    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)