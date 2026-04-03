from flask import Blueprint

bp = Blueprint("student", __name__, template_folder="../templates/student")

from app.student import routes  # noqa: E402, F401
