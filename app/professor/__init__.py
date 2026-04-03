from flask import Blueprint

bp = Blueprint("professor", __name__, template_folder="../templates/professor")

from app.professor import routes  # noqa: E402, F401
