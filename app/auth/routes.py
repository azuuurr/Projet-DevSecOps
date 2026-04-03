import bcrypt
from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import limiter, login_manager
from app.audit import log_action
from app.auth import bp
from app.auth.forms import ChangePasswordForm, LoginForm
from app.db import execute_db, query_db


class User:
    """User model for Flask-Login integration."""

    def __init__(self, user_data):
        self.id = user_data["id"]
        self.username = user_data["username"]
        self.email = user_data["email"]
        self.role = user_data["role"]
        self.first_name = user_data["first_name"]
        self.last_name = user_data["last_name"]
        self.is_active = True
        self.is_authenticated = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@login_manager.user_loader
def load_user(user_id):
    user_data = query_db(
        "SELECT id, username, email, role, first_name, last_name FROM users WHERE id = %s",
        (user_id,),
        one=True,
    )
    if user_data:
        return User(user_data)
    return None


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for(_dashboard_for_role(current_user.role)))

    form = LoginForm()
    if form.validate_on_submit():
        user_data = query_db(
            "SELECT id, username, email, password_hash, role, first_name, last_name "
            "FROM users WHERE username = %s",
            (form.username.data,),
            one=True,
        )

        if user_data and bcrypt.checkpw(
            form.password.data.encode("utf-8"),
            user_data["password_hash"].encode("utf-8"),
        ):
            user = User(user_data)
            session.clear()
            login_user(user)
            session.permanent = True
            session.modified = True
            current_app.logger.info("Login successful: user=%s role=%s", user.username, user.role)
            log_action("LOGIN", "Login successful")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for(_dashboard_for_role(user.role)))

        current_app.logger.warning(
            "Login failed: username=%s ip=%s",
            form.username.data,
            request.remote_addr,
        )
        flash("Nom d'utilisateur ou mot de passe incorrect.", "error")

    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    current_app.logger.info("Logout: user=%s", current_user.username)
    log_action("LOGOUT", "User logged out")
    logout_user()
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user_data = query_db(
            "SELECT password_hash FROM users WHERE id = %s",
            (current_user.id,),
            one=True,
        )
        if not bcrypt.checkpw(
            form.current_password.data.encode("utf-8"),
            user_data["password_hash"].encode("utf-8"),
        ):
            flash("Le mot de passe actuel est incorrect.", "error")
            return render_template("auth/profile.html", form=form)

        if form.new_password.data != form.confirm_password.data:
            flash("Les nouveaux mots de passe ne correspondent pas.", "error")
            return render_template("auth/profile.html", form=form)

        new_hash = bcrypt.hashpw(
            form.new_password.data.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, current_user.id))
        current_app.logger.info("Password changed: user=%s", current_user.username)
        log_action("PASSWORD_CHANGE", "Password changed")
        flash("Mot de passe modifié avec succès.", "success")
        return redirect(url_for("auth.profile"))

    user_info = query_db(
        "SELECT username, email, first_name, last_name, role, created_at FROM users WHERE id = %s",
        (current_user.id,),
        one=True,
    )
    return render_template("auth/profile.html", form=form, user_info=user_info)


def _dashboard_for_role(role):
    routes = {
        "admin": "admin.dashboard",
        "professor": "professor.dashboard",
        "student": "student.dashboard",
    }
    return routes.get(role, "auth.login")
