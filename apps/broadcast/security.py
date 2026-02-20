from __future__ import annotations

import html


def escape_html(value: str | None) -> str:
    return html.escape((value or '').strip())


def safe_int(value, default: int = 0, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed
