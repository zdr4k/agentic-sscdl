"""IT helpdesk MCP server.

Built incrementally on purpose: this first version ships only the
read-only lookup tool. The write tools (create_ticket) and the
sensitive tool (reset_password) are added in later commits, so the
CI pipeline built later in this series has a real "before" state to
diff against.
"""

from fastmcp import FastMCP

from mock_data import EMPLOYEES

mcp = FastMCP("it-helpdesk")


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


if __name__ == "__main__":
    mcp.run()