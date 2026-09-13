"""Mock backend data for the IT helpdesk agent demo.

No real directory or ticketing system is involved. Everything lives
in memory so the demo is self-contained and reproducible.
"""

EMPLOYEES = {
    "jsilva": {
        "full_name": "Julia Silva",
        "department": "Finance",
        "manager": "rcosta",
        "account_status": "active",
    },
    "rcosta": {
        "full_name": "Rafael Costa",
        "department": "Finance",
        "manager": "amartins",
        "account_status": "active",
    },
    "amartins": {
        "full_name": "Ana Martins",
        "department": "Engineering",
        "manager": None,
        "account_status": "locked",
    },
}

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

KB_ARTICLES = [
    {
        "title": "How to configure the corporate VPN",
        "body": "Install GlobalProtect, use your network username, and select the SP-EAST gateway.",
    },
    {
        "title": "What to do when your account is locked",
        "body": "Accounts lock after 5 failed login attempts. Wait 15 minutes or contact IT to unlock manually.",
    },
]