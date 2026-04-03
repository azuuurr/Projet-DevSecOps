import mysql.connector
from flask import current_app, g


def get_db():
    if "db" not in g or not g.db.is_connected():
        g.db = mysql.connector.connect(
            host=current_app.config["DATABASE_HOST"],
            port=current_app.config["DATABASE_PORT"],
            user=current_app.config["DATABASE_USER"],
            password=current_app.config["DATABASE_PASSWORD"],
            database=current_app.config["DATABASE_NAME"],
        )
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def query_db(query, args=(), one=False, commit=False):
    """Execute a parameterized query and return results."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, args)

    if commit:
        db.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    rv = cursor.fetchall()
    cursor.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=(), commit=True):
    """Execute a parameterized write query (INSERT, UPDATE, DELETE)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, args)
    if commit:
        db.commit()
    last_id = cursor.lastrowid
    rows_affected = cursor.rowcount
    cursor.close()
    return last_id, rows_affected


def init_app(app):
    app.teardown_appcontext(close_db)
