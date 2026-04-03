from flask import render_template
from flask_login import current_user, login_required

from app.auth.decorators import role_required
from app.db import query_db
from app.student import bp


@bp.route("/")
@login_required
@role_required("student")
def dashboard():
    classes = query_db(
        "SELECT c.id, c.name, c.description "
        "FROM classes c JOIN class_students cs ON c.id = cs.class_id "
        "WHERE cs.student_id = %s ORDER BY c.name",
        (current_user.id,),
    )

    recent_grades = query_db(
        "SELECT g.score, g.comment, g.created_at, e.title AS eval_title, "
        "e.coefficient, s.name AS subject_name "
        "FROM grades g "
        "JOIN evaluations e ON g.evaluation_id = e.id "
        "JOIN subjects s ON e.subject_id = s.id "
        "WHERE g.student_id = %s "
        "ORDER BY g.created_at DESC LIMIT 10",
        (current_user.id,),
    )

    avg_result = query_db(
        "SELECT ROUND(AVG(g.score), 2) AS avg_score "
        "FROM grades g WHERE g.student_id = %s",
        (current_user.id,),
        one=True,
    )
    average = avg_result["avg_score"] if avg_result else None

    return render_template(
        "student/dashboard.html",
        classes=classes, recent_grades=recent_grades, average=average,
    )


@bp.route("/grades")
@login_required
@role_required("student")
def grades():
    grades_by_subject = query_db(
        "SELECT g.score, g.comment, g.created_at, e.title AS eval_title, "
        "e.coefficient, e.date AS eval_date, s.name AS subject_name, s.id AS subject_id "
        "FROM grades g "
        "JOIN evaluations e ON g.evaluation_id = e.id "
        "JOIN subjects s ON e.subject_id = s.id "
        "WHERE g.student_id = %s "
        "ORDER BY s.name, e.date DESC",
        (current_user.id,),
    )

    subjects = {}
    for g in grades_by_subject:
        sid = g["subject_id"]
        if sid not in subjects:
            subjects[sid] = {"name": g["subject_name"], "grades": [], "total_weighted": 0, "total_coeff": 0}
        subjects[sid]["grades"].append(g)
        subjects[sid]["total_weighted"] += float(g["score"]) * float(g["coefficient"])
        subjects[sid]["total_coeff"] += float(g["coefficient"])

    for s in subjects.values():
        s["average"] = round(s["total_weighted"] / s["total_coeff"], 2) if s["total_coeff"] > 0 else None

    return render_template("student/grades.html", subjects=subjects)


@bp.route("/schedule")
@login_required
@role_required("student")
def schedule():
    schedules = query_db(
        "SELECT sc.day_of_week, sc.start_time, sc.end_time, sc.room, "
        "sub.name AS subject_name, u.first_name AS prof_first, u.last_name AS prof_last "
        "FROM schedules sc "
        "JOIN subjects sub ON sc.subject_id = sub.id "
        "JOIN users u ON sub.professor_id = u.id "
        "JOIN class_students cs ON sc.class_id = cs.class_id "
        "WHERE cs.student_id = %s "
        "ORDER BY FIELD(sc.day_of_week, 'Lundi','Mardi','Mercredi','Jeudi','Vendredi'), sc.start_time",
        (current_user.id,),
    )

    days = {}
    for s in schedules:
        day = s["day_of_week"]
        if day not in days:
            days[day] = []
        days[day].append(s)

    return render_template("student/schedule.html", days=days)
