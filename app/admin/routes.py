import bcrypt
import bleach
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.admin import bp
from app.admin.forms import (
    AssignProfessorsForm,
    AssignStudentsForm,
    ClassForm,
    ScheduleForm,
    SubjectForm,
    UserForm,
)
from app.audit import log_action
from app.auth.decorators import role_required
from app.db import execute_db, query_db


def _sanitize(value):
    return bleach.clean(value.strip()) if value else value


# ---------- Dashboard ----------

@bp.route("/audit-log")
@login_required
@role_required("admin")
def audit_log():
    logs = query_db(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 100"
    )
    return render_template("admin/audit_log.html", logs=logs)


@bp.route("/")
@login_required
@role_required("admin")
def dashboard():
    stats = {
        "users": query_db("SELECT COUNT(*) AS c FROM users", one=True)["c"],
        "classes": query_db("SELECT COUNT(*) AS c FROM classes", one=True)["c"],
        "students": query_db("SELECT COUNT(*) AS c FROM users WHERE role='student'", one=True)["c"],
        "professors": query_db("SELECT COUNT(*) AS c FROM users WHERE role='professor'", one=True)["c"],
    }
    return render_template("admin/dashboard.html", stats=stats)


# ---------- User Management ----------

@bp.route("/users")
@login_required
@role_required("admin")
def users_list():
    search = request.args.get("q", "").strip()
    if search:
        users = query_db(
            "SELECT id, username, email, role, first_name, last_name FROM users "
            "WHERE username LIKE %s OR email LIKE %s OR first_name LIKE %s OR last_name LIKE %s "
            "ORDER BY role, last_name",
            (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
        )
    else:
        users = query_db("SELECT id, username, email, role, first_name, last_name FROM users ORDER BY role, last_name")
    return render_template("admin/users_list.html", users=users, search=search)


@bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def user_create():
    form = UserForm()
    if form.validate_on_submit():
        if not form.password.data:
            flash("Le mot de passe est obligatoire pour un nouvel utilisateur.", "error")
            return render_template("admin/user_form.html", form=form, title="Créer un utilisateur")

        password_hash = bcrypt.hashpw(
            form.password.data.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        try:
            execute_db(
                "INSERT INTO users (username, email, password_hash, role, first_name, last_name) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    _sanitize(form.username.data),
                    _sanitize(form.email.data),
                    password_hash,
                    form.role.data,
                    _sanitize(form.first_name.data),
                    _sanitize(form.last_name.data),
                ),
            )
            log_action("USER_CREATE", f"Created user {_sanitize(form.username.data)}")
            flash("Utilisateur créé avec succès.", "success")
            return redirect(url_for("admin.users_list"))
        except Exception as e:
            current_app.logger.error("Error creating user: %s", e)
            flash("Erreur lors de la création (nom d'utilisateur ou email déjà pris).", "error")

    return render_template("admin/user_form.html", form=form, title="Créer un utilisateur")


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def user_edit(user_id):
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    if not user:
        flash("Utilisateur introuvable.", "error")
        return redirect(url_for("admin.users_list"))

    form = UserForm(obj=None)
    if request.method == "GET":
        form.username.data = user["username"]
        form.email.data = user["email"]
        form.first_name.data = user["first_name"]
        form.last_name.data = user["last_name"]
        form.role.data = user["role"]

    if form.validate_on_submit():
        try:
            if form.password.data:
                password_hash = bcrypt.hashpw(
                    form.password.data.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                execute_db(
                    "UPDATE users SET username=%s, email=%s, password_hash=%s, role=%s, "
                    "first_name=%s, last_name=%s WHERE id=%s",
                    (
                        _sanitize(form.username.data),
                        _sanitize(form.email.data),
                        password_hash,
                        form.role.data,
                        _sanitize(form.first_name.data),
                        _sanitize(form.last_name.data),
                        user_id,
                    ),
                )
            else:
                execute_db(
                    "UPDATE users SET username=%s, email=%s, role=%s, "
                    "first_name=%s, last_name=%s WHERE id=%s",
                    (
                        _sanitize(form.username.data),
                        _sanitize(form.email.data),
                        form.role.data,
                        _sanitize(form.first_name.data),
                        _sanitize(form.last_name.data),
                        user_id,
                    ),
                )
            log_action("USER_EDIT", f"Edited user {user_id}")
            flash("Utilisateur modifié avec succès.", "success")
            return redirect(url_for("admin.users_list"))
        except Exception as e:
            current_app.logger.error("Error updating user: %s", e)
            flash("Erreur lors de la modification.", "error")

    return render_template("admin/user_form.html", form=form, title="Modifier l'utilisateur", edit=True)


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def user_delete(user_id):
    if user_id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "error")
        return redirect(url_for("admin.users_list"))

    execute_db("DELETE FROM users WHERE id = %s", (user_id,))
    log_action("USER_DELETE", f"Deleted user {user_id}")
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for("admin.users_list"))


# ---------- Class Management ----------

@bp.route("/classes")
@login_required
@role_required("admin")
def classes_list():
    search = request.args.get("q", "").strip()
    if search:
        classes = query_db(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM class_students WHERE class_id = c.id) AS student_count, "
            "(SELECT COUNT(*) FROM class_professors WHERE class_id = c.id) AS professor_count "
            "FROM classes c WHERE c.name LIKE %s OR c.description LIKE %s ORDER BY c.name",
            (f"%{search}%", f"%{search}%"),
        )
    else:
        classes = query_db(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM class_students WHERE class_id = c.id) AS student_count, "
            "(SELECT COUNT(*) FROM class_professors WHERE class_id = c.id) AS professor_count "
            "FROM classes c ORDER BY c.name"
        )
    return render_template("admin/classes_list.html", classes=classes, search=search)


@bp.route("/classes/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def class_create():
    form = ClassForm()
    if form.validate_on_submit():
        execute_db(
            "INSERT INTO classes (name, description) VALUES (%s, %s)",
            (_sanitize(form.name.data), _sanitize(form.description.data)),
        )
        log_action("CLASS_CREATE", f"Created class {_sanitize(form.name.data)}")
        flash("Classe créée avec succès.", "success")
        return redirect(url_for("admin.classes_list"))
    return render_template("admin/class_form.html", form=form, title="Créer une classe")


@bp.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def class_edit(class_id):
    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    if not cls:
        flash("Classe introuvable.", "error")
        return redirect(url_for("admin.classes_list"))

    form = ClassForm()
    if request.method == "GET":
        form.name.data = cls["name"]
        form.description.data = cls["description"]

    if form.validate_on_submit():
        execute_db(
            "UPDATE classes SET name=%s, description=%s WHERE id=%s",
            (_sanitize(form.name.data), _sanitize(form.description.data), class_id),
        )
        flash("Classe modifiée.", "success")
        return redirect(url_for("admin.classes_list"))

    return render_template("admin/class_form.html", form=form, title="Modifier la classe", edit=True)


@bp.route("/classes/<int:class_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def class_delete(class_id):
    execute_db("DELETE FROM classes WHERE id = %s", (class_id,))
    log_action("CLASS_DELETE", f"Deleted class {class_id}")
    flash("Classe supprimée.", "success")
    return redirect(url_for("admin.classes_list"))


@bp.route("/classes/<int:class_id>")
@login_required
@role_required("admin")
def class_detail(class_id):
    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    if not cls:
        flash("Classe introuvable.", "error")
        return redirect(url_for("admin.classes_list"))

    students = query_db(
        "SELECT u.id, u.first_name, u.last_name, u.email "
        "FROM users u JOIN class_students cs ON u.id = cs.student_id "
        "WHERE cs.class_id = %s ORDER BY u.last_name",
        (class_id,),
    )
    professors = query_db(
        "SELECT u.id, u.first_name, u.last_name, u.email "
        "FROM users u JOIN class_professors cp ON u.id = cp.professor_id "
        "WHERE cp.class_id = %s ORDER BY u.last_name",
        (class_id,),
    )
    subjects = query_db(
        "SELECT s.*, u.first_name AS prof_first, u.last_name AS prof_last "
        "FROM subjects s JOIN users u ON s.professor_id = u.id "
        "WHERE s.class_id = %s",
        (class_id,),
    )
    schedules = query_db(
        "SELECT sc.*, sub.name AS subject_name "
        "FROM schedules sc JOIN subjects sub ON sc.subject_id = sub.id "
        "WHERE sc.class_id = %s "
        "ORDER BY FIELD(sc.day_of_week, 'Lundi','Mardi','Mercredi','Jeudi','Vendredi'), sc.start_time",
        (class_id,),
    )

    return render_template(
        "admin/class_detail.html",
        cls=cls, students=students, professors=professors,
        subjects=subjects, schedules=schedules,
    )


# ---------- Assign Students / Professors ----------

@bp.route("/classes/<int:class_id>/assign-students", methods=["GET", "POST"])
@login_required
@role_required("admin")
def assign_students(class_id):
    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    if not cls:
        flash("Classe introuvable.", "error")
        return redirect(url_for("admin.classes_list"))

    all_students = query_db(
        "SELECT id, first_name, last_name FROM users WHERE role='student' ORDER BY last_name"
    )
    current_ids = [
        r["student_id"] for r in query_db(
            "SELECT student_id FROM class_students WHERE class_id = %s", (class_id,)
        )
    ]

    form = AssignStudentsForm()
    form.students.choices = [(s["id"], f"{s['last_name']} {s['first_name']}") for s in all_students]

    if request.method == "GET":
        form.students.data = current_ids

    if form.validate_on_submit():
        valid_student_ids = {s["id"] for s in all_students}
        selected_ids = [sid for sid in form.students.data if sid in valid_student_ids]

        execute_db("DELETE FROM class_students WHERE class_id = %s", (class_id,))
        for sid in selected_ids:
            execute_db(
                "INSERT INTO class_students (class_id, student_id) VALUES (%s, %s)",
                (class_id, sid),
            )
        flash("Étudiants attribués.", "success")
        return redirect(url_for("admin.class_detail", class_id=class_id))

    return render_template("admin/assign_students.html", form=form, cls=cls)


@bp.route("/classes/<int:class_id>/assign-professors", methods=["GET", "POST"])
@login_required
@role_required("admin")
def assign_professors(class_id):
    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    if not cls:
        flash("Classe introuvable.", "error")
        return redirect(url_for("admin.classes_list"))

    all_profs = query_db(
        "SELECT id, first_name, last_name FROM users WHERE role='professor' ORDER BY last_name"
    )
    current_ids = [
        r["professor_id"] for r in query_db(
            "SELECT professor_id FROM class_professors WHERE class_id = %s", (class_id,)
        )
    ]

    form = AssignProfessorsForm()
    form.professors.choices = [(p["id"], f"{p['last_name']} {p['first_name']}") for p in all_profs]

    if request.method == "GET":
        form.professors.data = current_ids

    if form.validate_on_submit():
        valid_prof_ids = {p["id"] for p in all_profs}
        selected_ids = [pid for pid in form.professors.data if pid in valid_prof_ids]

        execute_db("DELETE FROM class_professors WHERE class_id = %s", (class_id,))
        for pid in selected_ids:
            execute_db(
                "INSERT INTO class_professors (class_id, professor_id) VALUES (%s, %s)",
                (class_id, pid),
            )
        flash("Professeurs attribués.", "success")
        return redirect(url_for("admin.class_detail", class_id=class_id))

    return render_template("admin/assign_professors.html", form=form, cls=cls)


# ---------- Subjects ----------

@bp.route("/classes/<int:class_id>/subjects/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def subject_create(class_id):
    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    if not cls:
        flash("Classe introuvable.", "error")
        return redirect(url_for("admin.classes_list"))

    profs = query_db("SELECT id, first_name, last_name FROM users WHERE role='professor' ORDER BY last_name")
    form = SubjectForm()
    form.professor_id.choices = [(p["id"], f"{p['last_name']} {p['first_name']}") for p in profs]

    if form.validate_on_submit():
        execute_db(
            "INSERT INTO subjects (name, class_id, professor_id) VALUES (%s, %s, %s)",
            (_sanitize(form.name.data), class_id, form.professor_id.data),
        )
        flash("Matière créée.", "success")
        return redirect(url_for("admin.class_detail", class_id=class_id))

    return render_template("admin/subject_form.html", form=form, cls=cls)


@bp.route("/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def subject_delete(subject_id):
    subject = query_db("SELECT class_id FROM subjects WHERE id = %s", (subject_id,), one=True)
    if subject:
        execute_db("DELETE FROM subjects WHERE id = %s", (subject_id,))
        flash("Matière supprimée.", "success")
        return redirect(url_for("admin.class_detail", class_id=subject["class_id"]))
    flash("Matière introuvable.", "error")
    return redirect(url_for("admin.classes_list"))


# ---------- Schedules ----------

@bp.route("/classes/<int:class_id>/schedules/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def schedule_create(class_id):
    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    if not cls:
        flash("Classe introuvable.", "error")
        return redirect(url_for("admin.classes_list"))

    subjects = query_db("SELECT id, name FROM subjects WHERE class_id = %s", (class_id,))
    form = ScheduleForm()
    form.subject_id.choices = [(s["id"], s["name"]) for s in subjects]

    if form.validate_on_submit():
        execute_db(
            "INSERT INTO schedules (class_id, subject_id, day_of_week, start_time, end_time, room) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                class_id,
                form.subject_id.data,
                form.day_of_week.data,
                str(form.start_time.data),
                str(form.end_time.data),
                _sanitize(form.room.data),
            ),
        )
        flash("Créneau ajouté.", "success")
        return redirect(url_for("admin.class_detail", class_id=class_id))

    return render_template("admin/schedule_form.html", form=form, cls=cls)


@bp.route("/schedules/<int:schedule_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def schedule_delete(schedule_id):
    schedule = query_db("SELECT class_id FROM schedules WHERE id = %s", (schedule_id,), one=True)
    if schedule:
        execute_db("DELETE FROM schedules WHERE id = %s", (schedule_id,))
        flash("Créneau supprimé.", "success")
        return redirect(url_for("admin.class_detail", class_id=schedule["class_id"]))
    flash("Créneau introuvable.", "error")
    return redirect(url_for("admin.classes_list"))
