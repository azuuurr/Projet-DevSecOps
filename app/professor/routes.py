import csv
import io
import re

import bleach
from flask import Response, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.auth.decorators import role_required
from app.db import execute_db, query_db
from app.professor import bp
from app.professor.forms import EvaluationForm, GradeForm


def _sanitize(value):
    return bleach.clean(value.strip()) if value else value


# ---------- Dashboard ----------

@bp.route("/")
@login_required
@role_required("professor")
def dashboard():
    classes = query_db(
        "SELECT c.id, c.name, c.description "
        "FROM classes c JOIN class_professors cp ON c.id = cp.class_id "
        "WHERE cp.professor_id = %s ORDER BY c.name",
        (current_user.id,),
    )
    subjects = query_db(
        "SELECT s.id, s.name, c.name AS class_name "
        "FROM subjects s JOIN classes c ON s.class_id = c.id "
        "WHERE s.professor_id = %s",
        (current_user.id,),
    )
    return render_template("professor/dashboard.html", classes=classes, subjects=subjects)


# ---------- Classes ----------

@bp.route("/classes/<int:class_id>")
@login_required
@role_required("professor")
def class_detail(class_id):
    is_assigned = query_db(
        "SELECT 1 FROM class_professors WHERE class_id = %s AND professor_id = %s",
        (class_id, current_user.id),
        one=True,
    )
    if not is_assigned:
        current_app.logger.warning(
            "403: professor %s tried to access class %s", current_user.username, class_id
        )
        flash("Vous n'avez pas accès à cette classe.", "error")
        return redirect(url_for("professor.dashboard"))

    cls = query_db("SELECT * FROM classes WHERE id = %s", (class_id,), one=True)
    students = query_db(
        "SELECT u.id, u.first_name, u.last_name, u.email "
        "FROM users u JOIN class_students cs ON u.id = cs.student_id "
        "WHERE cs.class_id = %s ORDER BY u.last_name",
        (class_id,),
    )
    subjects = query_db(
        "SELECT * FROM subjects WHERE class_id = %s AND professor_id = %s",
        (class_id, current_user.id),
    )
    schedules = query_db(
        "SELECT sc.*, sub.name AS subject_name "
        "FROM schedules sc JOIN subjects sub ON sc.subject_id = sub.id "
        "WHERE sc.class_id = %s AND sub.professor_id = %s "
        "ORDER BY FIELD(sc.day_of_week, 'Lundi','Mardi','Mercredi','Jeudi','Vendredi'), sc.start_time",
        (class_id, current_user.id),
    )

    return render_template(
        "professor/class_detail.html",
        cls=cls, students=students, subjects=subjects, schedules=schedules,
    )


# ---------- Evaluations ----------

@bp.route("/subjects/<int:subject_id>/evaluations")
@login_required
@role_required("professor")
def evaluations_list(subject_id):
    subject = query_db(
        "SELECT s.*, c.name AS class_name FROM subjects s "
        "JOIN classes c ON s.class_id = c.id "
        "WHERE s.id = %s AND s.professor_id = %s",
        (subject_id, current_user.id),
        one=True,
    )
    if not subject:
        flash("Matière introuvable ou non attribuée.", "error")
        return redirect(url_for("professor.dashboard"))

    evaluations = query_db(
        "SELECT e.*, (SELECT COUNT(*) FROM grades WHERE evaluation_id = e.id) AS grade_count "
        "FROM evaluations e WHERE e.subject_id = %s AND e.professor_id = %s ORDER BY e.date DESC",
        (subject_id, current_user.id),
    )
    return render_template(
        "professor/evaluations_list.html",
        subject=subject, evaluations=evaluations,
    )


@bp.route("/subjects/<int:subject_id>/evaluations/create", methods=["GET", "POST"])
@login_required
@role_required("professor")
def evaluation_create(subject_id):
    subject = query_db(
        "SELECT * FROM subjects WHERE id = %s AND professor_id = %s",
        (subject_id, current_user.id),
        one=True,
    )
    if not subject:
        flash("Matière introuvable ou non attribuée.", "error")
        return redirect(url_for("professor.dashboard"))

    form = EvaluationForm()
    if form.validate_on_submit():
        execute_db(
            "INSERT INTO evaluations (title, subject_id, professor_id, date, coefficient) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                _sanitize(form.title.data),
                subject_id,
                current_user.id,
                form.date.data,
                float(form.coefficient.data),
            ),
        )
        flash("Évaluation créée.", "success")
        return redirect(url_for("professor.evaluations_list", subject_id=subject_id))

    return render_template("professor/evaluation_form.html", form=form, subject=subject)


@bp.route("/evaluations/<int:eval_id>/delete", methods=["POST"])
@login_required
@role_required("professor")
def evaluation_delete(eval_id):
    ev = query_db(
        "SELECT * FROM evaluations WHERE id = %s AND professor_id = %s",
        (eval_id, current_user.id),
        one=True,
    )
    if not ev:
        flash("Évaluation introuvable.", "error")
        return redirect(url_for("professor.dashboard"))

    execute_db("DELETE FROM evaluations WHERE id = %s", (eval_id,))
    flash("Évaluation supprimée.", "success")
    return redirect(url_for("professor.evaluations_list", subject_id=ev["subject_id"]))


# ---------- Grades ----------

@bp.route("/evaluations/<int:eval_id>/grades")
@login_required
@role_required("professor")
def grades_list(eval_id):
    ev = query_db(
        "SELECT e.*, s.name AS subject_name, s.class_id "
        "FROM evaluations e JOIN subjects s ON e.subject_id = s.id "
        "WHERE e.id = %s AND e.professor_id = %s",
        (eval_id, current_user.id),
        one=True,
    )
    if not ev:
        flash("Évaluation introuvable.", "error")
        return redirect(url_for("professor.dashboard"))

    students_with_grades = query_db(
        "SELECT u.id AS student_id, u.first_name, u.last_name, g.score, g.comment, g.id AS grade_id "
        "FROM users u "
        "JOIN class_students cs ON u.id = cs.student_id "
        "LEFT JOIN grades g ON g.student_id = u.id AND g.evaluation_id = %s "
        "WHERE cs.class_id = %s ORDER BY u.last_name",
        (eval_id, ev["class_id"]),
    )

    return render_template(
        "professor/grades_list.html",
        evaluation=ev, students=students_with_grades,
    )


@bp.route("/evaluations/<int:eval_id>/grades/export")
@login_required
@role_required("professor")
def grades_export_csv(eval_id):
    ev = query_db(
        "SELECT e.*, s.name AS subject_name, s.class_id "
        "FROM evaluations e JOIN subjects s ON e.subject_id = s.id "
        "WHERE e.id = %s AND e.professor_id = %s",
        (eval_id, current_user.id),
        one=True,
    )
    if not ev:
        flash("Évaluation introuvable.", "error")
        return redirect(url_for("professor.dashboard"))

    graded = query_db(
        "SELECT u.first_name, u.last_name, g.score, g.comment "
        "FROM grades g "
        "JOIN users u ON u.id = g.student_id "
        "WHERE g.evaluation_id = %s "
        "ORDER BY u.last_name, u.first_name",
        (eval_id,),
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Etudiant", "Note", "Commentaire"])
    for row in graded:
        name = f"{row['first_name']} {row['last_name']}"
        note = f"{row['score']}/20" if row["score"] is not None else ""
        writer.writerow([name, note, row["comment"] or ""])

    safe_title = re.sub(r"[^\w\-]+", "_", ev["title"], flags=re.UNICODE).strip("_") or "evaluation"
    filename = f"notes_{safe_title}.csv"

    output = buf.getvalue()
    response = Response(output, mimetype="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@bp.route("/evaluations/<int:eval_id>/grades/<int:student_id>", methods=["GET", "POST"])
@login_required
@role_required("professor")
def grade_edit(eval_id, student_id):
    ev = query_db(
        "SELECT e.*, s.name AS subject_name, s.class_id "
        "FROM evaluations e JOIN subjects s ON e.subject_id = s.id "
        "WHERE e.id = %s AND e.professor_id = %s",
        (eval_id, current_user.id),
        one=True,
    )
    if not ev:
        flash("Évaluation introuvable.", "error")
        return redirect(url_for("professor.dashboard"))

    student = query_db(
        "SELECT u.id, u.first_name, u.last_name FROM users u "
        "JOIN class_students cs ON u.id = cs.student_id "
        "WHERE u.id = %s AND cs.class_id = %s",
        (student_id, ev["class_id"]),
        one=True,
    )
    if not student:
        flash("Étudiant introuvable dans cette classe.", "error")
        return redirect(url_for("professor.grades_list", eval_id=eval_id))

    existing = query_db(
        "SELECT * FROM grades WHERE evaluation_id = %s AND student_id = %s",
        (eval_id, student_id),
        one=True,
    )

    form = GradeForm()
    if request.method == "GET" and existing:
        form.score.data = existing["score"]
        form.comment.data = existing["comment"]

    if form.validate_on_submit():
        if existing:
            execute_db(
                "UPDATE grades SET score = %s, comment = %s WHERE id = %s",
                (float(form.score.data), _sanitize(form.comment.data), existing["id"]),
            )
        else:
            execute_db(
                "INSERT INTO grades (evaluation_id, student_id, score, comment) VALUES (%s, %s, %s, %s)",
                (eval_id, student_id, float(form.score.data), _sanitize(form.comment.data)),
            )
        flash("Note enregistrée.", "success")
        return redirect(url_for("professor.grades_list", eval_id=eval_id))

    return render_template(
        "professor/grade_form.html",
        form=form, evaluation=ev, student=student, edit=existing is not None,
    )
