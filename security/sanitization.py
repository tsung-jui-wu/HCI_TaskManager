import bleach


def sanitize_for_storage(validated_string: str) -> str:
    """
    Strips all HTML tags from a validated string before it is written to the
    database.  Using bleach with tags=[] ensures that even if validation is
    somehow bypassed, no HTML payload survives into storage.

    Example: '<script>alert(1)</script>' → 'alert(1)'

    Storing clean data (rather than only escaping on output) means that any
    future code path reading from the DB will always get plain text, regardless
    of whether that path remembers to escape.
    """
    return bleach.clean(validated_string, tags=[], attributes={}, strip=True)
