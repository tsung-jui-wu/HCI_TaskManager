import sqlite3
import os
from contextlib import contextmanager
from flask import current_app


def init_db(app):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with app.app_context():
        with _connect(app.config["DATABASE"]) as conn:
            with open(schema_path, "r") as f:
                conn.executescript(f.read())


@contextmanager
def get_db():
    db_path = current_app.config["DATABASE"]
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _connect(db_path):
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    # Enforce integrity constraints strictly
    conn.execute("PRAGMA integrity_check")
    return conn
