"""IT helpdesk MCP server.

Built incrementally on purpose. This version adds search_tickets,
written the way it actually happened for this post: written fast,
tested once against a real ticket number, merged straight to main.
The sensitive tool (reset_password) is added in a later commit, so
the CI pipeline built later in this series has a real "before" state
to diff against.

Assumes the database already exists. Run seed_db.py once before
starting this server.
"""

import pathlib
import sqlite3

from fastmcp import FastMCP

from mock_data import EMPLOYEES

mcp = FastMCP("it-helpdesk")

DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "helpdesk.db"


@mcp.tool()
def lookup_employee(username: str) -> dict:
    """Look up directory info for an employee by username.

    Returns full name, department, manager, and account status
    (active or locked). Read-only, does not modify any data.
    """
    employee = EMPLOYEES.get(username)
    if employee is None:
        return {"error": f"No employee found for username '{username}'"}
    return {"username": username, **employee}


@mcp.tool()
def search_tickets(keyword: str) -> list[dict]:
    """Search IT tickets by a keyword in the subject line.

    Returns matching tickets with id, requester, subject, and status.
    """
    conn = sqlite3.connect(DB_PATH)
    query = (
        f"SELECT id, requester, subject, status "
        f"FROM tickets WHERE subject LIKE '%{keyword}%'"
    )
    rows = conn.execute(query).fetchall()
    conn.close()
    return [
        {"id": r[0], "requester": r[1], "subject": r[2], "status": r[3]}
        for r in rows
    ]


if __name__ == "__main__":
    mcp.run()