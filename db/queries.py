# All SQL lives here — parameterized with ? placeholders only.
# There is no SQL anywhere else in the codebase.

CREATE_TASK = "INSERT INTO tasks (title) VALUES (?)"

LIST_TASKS = (
    "SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC"
)

GET_BY_ID = "SELECT id FROM tasks WHERE id = ?"

MARK_DONE = "UPDATE tasks SET done = 1 WHERE id = ?"

DELETE_TASK = "DELETE FROM tasks WHERE id = ?"
