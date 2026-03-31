from flask import Request


def apply_security_headers(response):
    """
    Applied via @app.after_request to every response.

    Content-Security-Policy explanation:
      - default-src 'none'  : deny everything by default
      - script-src 'self'   : only our own /static/app.js
      - style-src 'self'    : only our own /static/style.css
      - connect-src 'self'  : fetch() only to same origin
      - form-action 'self'  : no form submissions to external URLs
      - base-uri 'none'     : no <base> tag hijacking
      - frame-ancestors 'none' : cannot be embedded in an iframe
    No 'unsafe-inline' anywhere — even if XSS injects a <script> into the DOM,
    the browser will refuse to execute it.
    """
    csp = (
        "default-src 'none'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'"
    )
    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Prevent API responses from being cached — they contain dynamic user data
    if response.content_type and "application/json" in response.content_type:
        response.headers["Cache-Control"] = "no-store"

    return response
