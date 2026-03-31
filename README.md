# Task Manager

A simple task manager (add / mark complete / delete) built with Python Flask and SQLite, hardened against common web attacks.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Security layers

| Layer | What it does |
|-------|-------------|
| Input validation | Strips null bytes, normalizes Unicode (NFKC), rejects empty/oversized/control-char input |
| Storage sanitization | `bleach` strips all HTML tags before writing to DB |
| Parameterized SQL | Every query uses `?` placeholders — no string interpolation anywhere |
| CSRF protection | `X-CSRFToken` header required on all mutating requests |
| HTTP security headers | Strict CSP (no inline scripts), `X-Frame-Options: DENY`, `nosniff` |
| Rate limiting | 30 POST/DELETE per minute; 413 on request bodies over 16 KB |
| DB constraints | `CHECK` constraints enforce length and type at the database level |

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks` | List all tasks |
| POST | `/tasks` | Add task — body: `{"title": "..."}` |
| PATCH | `/tasks/<id>/done` | Mark complete |
| DELETE | `/tasks/<id>` | Delete |

All mutating requests require a `X-CSRFToken` header and session cookie (obtained from the page load at `/`).

## Attack behavior

| Input | Response |
|-------|----------|
| Empty or whitespace-only title | 400 — "Title cannot be empty." |
| Title over 200 characters | 400 — "Title must be 200 characters or fewer." |
| `<script>alert(1)</script>` | Stored as `alert(1)` — tags stripped |
| `'; DROP TABLE tasks; --` | Stored as literal text — DB unaffected |
| Non-integer or negative task ID | 404 |
| Missing/invalid CSRF token | 400 — "CSRF validation failed." |
| Over 30 requests/minute | 429 — frontend disables form with countdown |
