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


def mask_fenced_code(text: str) -> str:
    """Hide Markdown code examples while preserving every character offset.

    Task-looking lines in a fenced example are documentation, not executable
    tasks. Refuse an unterminated fence instead of hiding unfinished work.
    """
    fence: tuple[str, int] | None = None
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        body = line.lstrip(" \t").rstrip("\r\n")
        hidden = fence is not None
        if fence is not None:
            char, size = fence
            if re.fullmatch(re.escape(char) + "{" + str(size) + ",}[ \t]*", body):
                fence = None
        else:
            opening = re.match(r"(`{3,}|~{3,})(.*)$", body)
            if opening and not (opening[1][0] == "`" and "`" in opening[2]):
                fence = (opening[1][0], len(opening[1]))
                hidden = True
        out.append("".join(c if c in "\r\n" else " " for c in line) if hidden else line)
    if fence is not None:
        raise TaskFormatError("Unterminated Markdown code fence in tasks.md; repair the task document")
    return "".join(out)


def task_continuation(lines: list[str], index: int) -> str:
    """Indented Markdown paragraphs belong to the preceding task, not a new task."""
    continuation = []
    visible = mask_fenced_code("\n".join(lines)).split("\n")
    for j in range(index + 1, len(lines)):
        line = lines[j]
        if line.strip() and (not line[:1].isspace() or CHECKBOX_RE.fullmatch(visible[j])):
            break
        continuation.append(line)
    body = "\n".join(continuation).rstrip()
    return "\n" + body if body else ""


def validate_open_tasks(text: str) -> None:
    text = mask_fenced_code(text)
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
    marks = CHECKBOX_RE.findall(mask_fenced_code(text))
    return bool(marks) and all(mark in {"X", "x"} for mark in marks)


def mark_task(text: str, task_id: str, status: str, annotation: str = "") -> str:
    """Update exactly one task by its full identity; never match a sibling prefix."""
    matches = [m for m in TASK_LINE_RE.finditer(mask_fenced_code(text)) if m.group("id") == task_id]
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
