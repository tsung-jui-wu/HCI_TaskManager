import unicodedata


class ValidationError(ValueError):
    pass


# Unicode control character categories to reject.
# Cc = control, Cs = surrogate, Co = private use, Cn = unassigned.
# We allow standard ASCII whitespace (space, tab, newline) through — those
# are already handled by the strip() step. Everything else in Cc is rejected.
_BLOCKED_CATEGORIES = frozenset({"Cs", "Co", "Cn"})
_BLOCKED_CC_CODEPOINTS = frozenset({
    # Common dangerous control characters (beyond standard whitespace)
    "\x00", "\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07",
    "\x08",         "\x0b", "\x0c",         "\x0e", "\x0f",
    "\x10", "\x11", "\x12", "\x13", "\x14", "\x15", "\x16", "\x17",
    "\x18", "\x19", "\x1a", "\x1b", "\x1c", "\x1d", "\x1e", "\x1f",
    "\x7f",
    # Unicode special
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u202a",  # left-to-right embedding
    "\u202b",  # right-to-left embedding
    "\u202c",  # pop directional formatting
    "\u202d",  # left-to-right override
    "\u202e",  # right-to-left override  ← direction hijack
    "\u2028",  # line separator
    "\u2029",  # paragraph separator
    "\u2066",  # left-to-right isolate
    "\u2067",  # right-to-left isolate
    "\u2068",  # first strong isolate
    "\u2069",  # pop directional isolate
    "\ufeff",  # byte order mark
    "\ufffc",  # object replacement character
    "\ufffd",  # replacement character (indicates bad encoding)
})

MAX_TITLE_LENGTH = 200


def validate_task_title(raw) -> str:
    """
    Validates and normalizes a task title.  Raises ValidationError with a
    safe, non-revealing message on any failure.  Returns the cleaned string.

    Pipeline:
      1. Type check
      2. Null-byte strip
      3. Unicode NFKC normalization (collapses homoglyphs, fullwidth, etc.)
      4. Whitespace strip
      5. Empty check
      6. Length check
      7. Control / dangerous character check
    """
    if not isinstance(raw, str):
        raise ValidationError("Title must be a string.")

    # Step 2: strip null bytes explicitly before normalization
    cleaned = raw.replace("\x00", "")

    # Step 3: NFKC normalization — collapses Unicode lookalikes to canonical form
    # e.g. fullwidth 'ａ' → 'a', Cyrillic 'а' stays 'а' (distinguishable after this)
    cleaned = unicodedata.normalize("NFKC", cleaned)

    # Step 4: strip leading/trailing whitespace
    cleaned = cleaned.strip()

    # Step 5: empty check
    if not cleaned:
        raise ValidationError("Title cannot be empty.")

    # Step 6: length check — same limit as DB CHECK constraint
    if len(cleaned) > MAX_TITLE_LENGTH:
        raise ValidationError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer.")

    # Step 7: reject dangerous codepoints and blocked Unicode categories
    for ch in cleaned:
        if ch in _BLOCKED_CC_CODEPOINTS:
            raise ValidationError("Title contains invalid characters.")
        cat = unicodedata.category(ch)
        if cat in _BLOCKED_CATEGORIES:
            raise ValidationError("Title contains invalid characters.")

    return cleaned


def validate_task_id(raw) -> int:
    """
    Validates a task ID from a URL parameter.  Raises ValidationError if it
    is not a positive integer.
    """
    try:
        task_id = int(raw)
    except (TypeError, ValueError):
        raise ValidationError("Invalid task ID.")
    if task_id <= 0:
        raise ValidationError("Invalid task ID.")
    return task_id
