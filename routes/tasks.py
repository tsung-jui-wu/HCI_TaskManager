from flask import Blueprint, jsonify, request, current_app
from db import get_db
from db import queries
from security.validation import validate_task_title, validate_task_id, ValidationError
from security.sanitization import sanitize_for_storage

tasks_bp = Blueprint("tasks", __name__)


def _task_row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
    }


def _error(message, status=400):
    return jsonify({"error": message}), status


# ---------------------------------------------------------------------------
# GET /tasks  — list all tasks
# ---------------------------------------------------------------------------
@tasks_bp.route("/tasks", methods=["GET"])
def list_tasks():
    with get_db() as conn:
        rows = conn.execute(queries.LIST_TASKS).fetchall()
    return jsonify({"tasks": [_task_row_to_dict(r) for r in rows]}), 200


# ---------------------------------------------------------------------------
# POST /tasks  — create a task
# ---------------------------------------------------------------------------
@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    if not request.is_json:
        return _error("Content-Type must be application/json.", 415)

    data = request.get_json(silent=True)
    if data is None:
        return _error("Invalid JSON body.", 400)

    raw_title = data.get("title")

    try:
        clean_title = validate_task_title(raw_title)
    except ValidationError as exc:
        return _error(str(exc), 400)

    safe_title = sanitize_for_storage(clean_title)

    with get_db() as conn:
        cursor = conn.execute(queries.CREATE_TASK, (safe_title,))
        new_id = cursor.lastrowid

    return jsonify({"id": new_id}), 201


# ---------------------------------------------------------------------------
# PATCH /tasks/<id>/done  — mark a task complete
# ---------------------------------------------------------------------------
@tasks_bp.route("/tasks/<raw_id>/done", methods=["PATCH"])
def mark_done(raw_id):
    try:
        task_id = validate_task_id(raw_id)
    except ValidationError:
        return _error("Task not found.", 404)

    with get_db() as conn:
        row = conn.execute(queries.GET_BY_ID, (task_id,)).fetchone()
        if row is None:
            return _error("Task not found.", 404)
        conn.execute(queries.MARK_DONE, (task_id,))

    return jsonify({"ok": True}), 200


# ---------------------------------------------------------------------------
# DELETE /tasks/<id>  — delete a task
# ---------------------------------------------------------------------------
@tasks_bp.route("/tasks/<raw_id>", methods=["DELETE"])
def delete_task(raw_id):
    try:
        task_id = validate_task_id(raw_id)
    except ValidationError:
        return _error("Task not found.", 404)

    with get_db() as conn:
        row = conn.execute(queries.GET_BY_ID, (task_id,)).fetchone()
        if row is None:
            return _error("Task not found.", 404)
        conn.execute(queries.DELETE_TASK, (task_id,))

    return jsonify({"ok": True}), 200
