"""Canonical task identity and checkbox grammar for both implementation tracks."""

import re

TASK_ID_PATTERN = r"[A-Za-z]{1,4}\d+[A-Za-z0-9]*(?:[._\-\u2010\u2011\u2012\u2013][A-Za-z0-9]+)*"
_METADATA = r"(?:\[[^\]\n]*\][ \t]*)*"
_BOUNDARY = r"(?=\s|\*|:|\[|$)"
TASK_ID_RE = re.compile(r"^" + _METADATA + r"\*{0,2}(" + TASK_ID_PATTERN + r")" + _BOUNDARY)
CHECKBOX_RE = re.compile(r"^[ \t]*-[ \t]*\[([ Xx~])\][ \t]+[^\n]*$", re.MULTILINE)
TASK_LINE_RE = re.compile(
    r"^(?P<prefix>[ \t]*-[ \t]*)\[(?P<status>[ Xx~])\]"
    r"(?P<spacing>[ \t]+)"
    + _METADATA
    + r"(?P<bold>\*{0,2})(?P<id>"
    + TASK_ID_PATTERN
    + r")"
    + _BOUNDARY
    + r"(?P<rest>[^\n]*)$",
    re.MULTILINE,
)


class TaskFormatError(ValueError):
    """An unchecked checkbox cannot be mapped to a unique task identity."""


def validate_open_tasks(text: str) -> None:
    malformed = [
        m.group(0)
        for m in CHECKBOX_RE.finditer(text)
        if m.group(1) == " " and not TASK_LINE_RE.fullmatch(m.group(0))
    ]
    ids = [m.group("id") for m in TASK_LINE_RE.finditer(text)]
    duplicates = sorted({key for key in ids if ids.count(key) > 1})
    if malformed or duplicates:
        raise TaskFormatError(
            "Tasker must repair ambiguous task identities while preserving requirements. "
            + "Malformed: "
            + repr(malformed[:8])
            + "; duplicates: "
            + repr(duplicates[:8])
        )


def all_complete(text: str) -> bool:
    marks = CHECKBOX_RE.findall(text)
    return bool(marks) and all(mark in {"X", "x"} for mark in marks)


def mark_task(text: str, task_id: str, status: str, annotation: str = "") -> str:
    """Update exactly one task by its full identity; never match a sibling prefix."""
    matches = [m for m in TASK_LINE_RE.finditer(text) if m.group("id") == task_id]
    if len(matches) != 1:
        raise ValueError(f"expected one task {task_id!r}, found {len(matches)}")
    match = matches[0]
    # Replace only the checkbox character so tags, indentation and punctuation survive.
    return (
        text[: match.start("status")]
        + status
        + text[match.end("status") : match.end()]
        + annotation
        + text[match.end() :]
    )
