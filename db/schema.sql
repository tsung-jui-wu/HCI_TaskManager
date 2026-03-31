CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL CHECK(length(title) >= 1 AND length(title) <= 200),
    done       INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1)),
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
