from flask import request
from flask_login import current_user

from app.db import execute_db


def log_action(action, detail=None):
    """Log an action to the audit trail."""
    user_id = current_user.id if current_user.is_authenticated else None
    username = current_user.username if current_user.is_authenticated else "anonymous"
    ip = request.remote_addr if request else None
    try:
        execute_db(
            "INSERT INTO audit_log (user_id, username, action, detail, ip_address) VALUES (%s, %s, %s, %s, %s)",
            (user_id, username, action, detail, ip),
        )
    except Exception:
        pass  # Don't break the app if audit logging fails
