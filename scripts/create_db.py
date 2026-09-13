"""One-time setup for the helpdesk database.

Run this once, before starting the server:
    python mcp/seed_db.py

The server itself contains no schema or seeding logic. It only ever
connects to the file this script creates.
"""

import pathlib
import sqlite3

TICKETS = {
    "TCK-1001": {
        "requester": "jsilva",
        "subject": "VPN not connecting",
        "status": "open",
    },
    "TCK-1002": {
        "requester": "amartins",
        "subject": "Account locked after failed logins",
        "status": "in_progress",
    },
}

DB_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "helpdesk.db"

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

print(f"Seeded {DB_PATH}")