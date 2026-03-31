import secrets


class Config:
    SECRET_KEY = secrets.token_hex(32)
    DATABASE = "taskmanager.db"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600          # 1-hour CSRF token expiry
    MAX_CONTENT_LENGTH = 16 * 1024      # 16 KB max request body — 413 before any route runs
    WTF_CSRF_CHECK_DEFAULT = True
