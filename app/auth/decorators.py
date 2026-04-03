from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def role_required(*roles):
    """Restrict access to users with specific roles. Logs and returns 403 on violation."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                current_app.logger.warning(
                    "403 Forbidden: user=%s attempted access to %s (required roles: %s)",
                    getattr(current_user, "username", "anonymous"),
                    f.__name__,
                    ", ".join(roles),
                )
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
