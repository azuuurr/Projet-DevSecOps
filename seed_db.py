"""Seed the database with schema and test data (proper bcrypt hashes)."""
import bcrypt
import mysql.connector
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.environ.get("DATABASE_HOST", "localhost"),
    "port": int(os.environ.get("DATABASE_PORT", 3306)),
    "user": os.environ.get("DATABASE_USER", "root"),
    "password": os.environ.get("DATABASE_PASSWORD", ""),
}
DB_NAME = os.environ.get("DATABASE_NAME", "academic_db")

DEFAULT_PASSWORD = "password123"


def wait_for_db(max_retries=30):
    for i in range(max_retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            conn.close()
            return True
        except mysql.connector.Error:
            print(f"Waiting for database... ({i + 1}/{max_retries})")
            time.sleep(2)
    return False


def run_sql_file(cursor, filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def seed():
    if not wait_for_db():
        print("ERROR: Could not connect to database.")
        sys.exit(1)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print(f"Creating database {DB_NAME}...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_NAME}")

    print("Running schema.sql...")
    run_sql_file(cursor, "sql/schema.sql")
    conn.commit()

    print("Generating bcrypt hashes...")
    password_hash = bcrypt.hashpw(DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    users = [
        ("admin", "admin@academie.fr", "admin", "Marie", "Dupont"),
        ("prof.martin", "martin@academie.fr", "professor", "Jean", "Martin"),
        ("prof.bernard", "bernard@academie.fr", "professor", "Sophie", "Bernard"),
        ("etudiant.durand", "durand@etu.academie.fr", "student", "Lucas", "Durand"),
        ("etudiant.petit", "petit@etu.academie.fr", "student", "Emma", "Petit"),
        ("etudiant.moreau", "moreau@etu.academie.fr", "student", "Hugo", "Moreau"),
        ("etudiant.leroy", "leroy@etu.academie.fr", "student", "Lea", "Leroy"),
        ("etudiant.roux", "roux@etu.academie.fr", "student", "Nathan", "Roux"),
    ]

    print("Inserting users...")
    for username, email, role, first_name, last_name in users:
        cursor.execute(
            "INSERT IGNORE INTO users (username, email, password_hash, role, first_name, last_name) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (username, email, password_hash, role, first_name, last_name),
        )

    print("Inserting classes...")
    cursor.execute("INSERT IGNORE INTO classes (id, name, description) VALUES (1, 'GCS2-A', 'Guardia Cybersecurity School - 2eme annee - Groupe A')")
    cursor.execute("INSERT IGNORE INTO classes (id, name, description) VALUES (2, 'GCS2-B', 'Guardia Cybersecurity School - 2eme annee - Groupe B')")

    print("Assigning students and professors...")
    assignments = [
        ("class_students", [(1, 4), (1, 5), (1, 6), (2, 7), (2, 8)]),
        ("class_professors", [(1, 2), (1, 3), (2, 2)]),
    ]
    for table, pairs in assignments:
        for class_id, user_id in pairs:
            col = "student_id" if "student" in table else "professor_id"
            cursor.execute(f"INSERT IGNORE INTO {table} (class_id, {col}) VALUES (%s, %s)", (class_id, user_id))

    print("Inserting subjects...")
    cursor.execute("INSERT IGNORE INTO subjects (id, name, class_id, professor_id) VALUES (1, 'DevSecOps', 1, 2)")
    cursor.execute("INSERT IGNORE INTO subjects (id, name, class_id, professor_id) VALUES (2, 'Cryptographie', 1, 3)")
    cursor.execute("INSERT IGNORE INTO subjects (id, name, class_id, professor_id) VALUES (3, 'Securite Reseaux', 2, 2)")

    print("Inserting schedules...")
    schedules = [
        (1, 1, "Lundi", "09:00", "12:00", "Salle 101"),
        (1, 1, "Mercredi", "14:00", "17:00", "Salle 101"),
        (1, 2, "Mardi", "09:00", "12:00", "Salle 203"),
        (1, 2, "Jeudi", "14:00", "16:00", "Salle 203"),
        (2, 3, "Lundi", "14:00", "17:00", "Salle 105"),
        (2, 3, "Vendredi", "09:00", "12:00", "Salle 105"),
    ]
    for class_id, subject_id, day, start, end, room in schedules:
        cursor.execute(
            "INSERT IGNORE INTO schedules (class_id, subject_id, day_of_week, start_time, end_time, room) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (class_id, subject_id, day, start, end, room),
        )

    print("Inserting evaluations...")
    cursor.execute("INSERT IGNORE INTO evaluations (id, title, subject_id, professor_id, date, coefficient) VALUES (1, 'Projet Flask Securise', 1, 2, '2026-04-10', 3.0)")
    cursor.execute("INSERT IGNORE INTO evaluations (id, title, subject_id, professor_id, date, coefficient) VALUES (2, 'QCM DevSecOps', 1, 2, '2026-03-28', 1.0)")
    cursor.execute("INSERT IGNORE INTO evaluations (id, title, subject_id, professor_id, date, coefficient) VALUES (3, 'Examen Cryptographie', 2, 3, '2026-04-05', 2.0)")
    cursor.execute("INSERT IGNORE INTO evaluations (id, title, subject_id, professor_id, date, coefficient) VALUES (4, 'TP Securite Reseaux', 3, 2, '2026-04-08', 2.0)")

    print("Inserting grades...")
    grades = [
        (2, 4, 15.50, "Bon travail"),
        (2, 5, 17.00, "Excellent"),
        (2, 6, 12.00, "Peut mieux faire"),
        (3, 4, 14.00, "Satisfaisant"),
        (3, 5, 18.50, "Tres bien"),
        (3, 6, 11.00, "Insuffisant"),
        (4, 7, 16.00, "Bonne maitrise"),
        (4, 8, 13.50, "Correct"),
    ]
    for eval_id, student_id, score, comment in grades:
        cursor.execute(
            "INSERT IGNORE INTO grades (evaluation_id, student_id, score, comment) VALUES (%s, %s, %s, %s)",
            (eval_id, student_id, score, comment),
        )

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\nDatabase seeded successfully!")
    print(f"Default password for all accounts: {DEFAULT_PASSWORD}")
    print("Accounts: admin, prof.martin, prof.bernard, etudiant.durand, etudiant.petit, etudiant.moreau, etudiant.leroy, etudiant.roux")


if __name__ == "__main__":
    seed()
