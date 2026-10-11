"""Rewrite one repeatedly rejected task instead of re-planning the project.

A task that exhausts its attempts used to send the whole project back to
planning. Batch 1 of the 2026-10-11 reliability runs: 7 such re-plans cost
about 220 minutes, each started while 58-83% of the judged tasks stood
accepted, and the plan was rebuilt for all of them because of one or two.

:func:`revise` asks a model for a replacement of that one task and returns
it only if it has the required shape; :func:`apply` writes it into tasks.md
in place of the old line. What the model may decide is the wording of at
most three tasks. Whether a revision happens, how often, and what happens
when it does not help is decided by the caller.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from llmxive.backends.base import ChatMessage
from llmxive.speckit.task_lines import TASK_LINE_RE, mask_fenced_code, task_continuation

LOGGER = logging.getLogger(__name__)

PROMPT_PATH = "agents/prompts/task_reviser.md"
MAX_TASKS = 3
#: A replacement shorter than this cannot name a file and a check.
_MIN_CHARS = 60
_TASK_RE = re.compile(r"^TASK:[ \t]*(\S.*)$", re.MULTILINE)
_PATH_RE = re.compile(r"`[^`\n]*[/.][^`\n]*`")


def rejection_history(ledger: Path, key: str, *, limit: int = 6) -> list[str]:
    """The distinct reasons ``key`` was rejected, oldest first, most recent ``limit``."""
    reasons: list[str] = []
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        reason = " ".join(str(row.get("reason") or "").split())
        if row.get("task") == key and reason and reason not in reasons:
            reasons.append(reason)
    return reasons[-limit:]


def parse(reply: str) -> list[str] | None:
    """The replacement task texts, or ``None`` when the reply is not usable."""
    tasks = [" ".join(text.split()) for text in _TASK_RE.findall(reply)]
    if not 1 <= len(tasks) <= MAX_TASKS:
        return None
    if any(len(task) < _MIN_CHARS or not _PATH_RE.search(task) for task in tasks):
        return None
    return tasks


def build_messages(repo_root: Path, task_text: str, reasons: list[str], spec: str, files: list[str]) -> list[ChatMessage]:
    system = (repo_root / PROMPT_PATH).read_text(encoding="utf-8")
    user = "\n\n".join([
        "# The task as written\n\n" + task_text.strip(),
        "# Why it was rejected (each line is one rejection)\n\n"
        + ("\n".join(f"- {reason}" for reason in reasons) or "(no reason recorded)"),
        "# Project requirements\n\n" + spec.strip(),
        "# Files that exist now\n\n" + "\n".join(f"- `{rel}`" for rel in files),
        "Write the replacement now.",
    ])
    return [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)]


def revise(
    repo_root: Path, task_text: str, reasons: list[str], spec: str, files: list[str], *,
    model: str, default_backend: str = "dartmouth", fallback_backends: tuple[str, ...] = (),
) -> list[str] | None:
    """Ask for a replacement of one task. ``None`` when none usable came back."""
    from llmxive.backends.router import chat_with_fallback

    reply = chat_with_fallback(
        build_messages(repo_root, task_text, reasons, spec, files),
        default_backend=default_backend, fallback_backends=list(fallback_backends), model=model,
        max_tokens=4096,
    )
    tasks = parse(reply.text)
    if tasks is None:
        LOGGER.warning("[task-revision] unusable reply: %r", reply.text[:300])
    return tasks


def apply(tasks_text: str, task_id: str, replacements: list[str]) -> str:
    """Replace task ``task_id`` (and its continuation lines) with open tasks.

    The first replacement keeps the id; further ones get ``<id>r2``, ``<id>r3``.
    """
    matches = [m for m in TASK_LINE_RE.finditer(mask_fenced_code(tasks_text)) if m.group("id") == task_id]
    if len(matches) != 1:
        raise ValueError(f"expected one task {task_id!r}, found {len(matches)}")
    match = matches[0]
    lines = tasks_text.splitlines()
    index = tasks_text[:match.start()].count("\n")
    extra = task_continuation(lines, index).count("\n")
    used = {m.group("id") for m in TASK_LINE_RE.finditer(mask_fenced_code(tasks_text))}
    new_lines = []
    for n, text in enumerate(replacements, start=1):
        new_id = task_id if n == 1 else f"{task_id}r{n}"
        if n > 1 and new_id in used:
            raise ValueError(f"task id {new_id!r} is already in use")
        new_lines.append(f"{match.group('prefix')}[ ]{match.group('spacing')}{new_id} {text}")
    lines[index:index + 1 + extra] = new_lines
    return "\n".join(lines) + ("\n" if tasks_text.endswith("\n") else "")


__all__ = ["MAX_TASKS", "PROMPT_PATH", "apply", "build_messages", "parse", "rejection_history", "revise"]
