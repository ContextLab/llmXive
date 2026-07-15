"""Per-project registry of REPEATEDLY-UNVERIFIABLE tasks (issue #1139, defect D6).

The independent task-verifier used to FORCE-ACCEPT a task after ``REJECT_CAP``
consecutive INCOMPLETE verdicts — flipping genuinely-undone work to ``[X]`` so a
project could escape an unbreakable redo loop. That is a fail-open: incomplete
work counted as done. This store replaces that escape hatch. When a task hits
``REJECT_CAP`` consecutive INCOMPLETE verdicts it is REOPENED (``[ ]``, never
``[X]``) and recorded HERE, and the verifier stops re-judging it (which is what
actually breaks the loop — the task is not lied about, it is escalated).

CROSS-CLUSTER CONTRACT (consumed by the pipeline graph / kickback router):
  * File:   ``state/unverifiable_tasks/<project_id>.json``
  * Schema: ``{"project_id": str,
              "tasks": [{"task_key": str, "reject_count": int,
                         "last_reason": str, "first_seen": iso8601,
                         "last_seen": iso8601}],
              "updated_at": iso8601}``
  * The CORE pipeline routes a project to ``research_full_revision`` when
    :func:`has_unverifiable` is true (a task the implementer cannot make pass
    needs a re-plan, not another redo lap), and calls :func:`clear` once the
    project has been kicked back so the next cycle starts clean.

All writes go through :func:`llmxive.state._io.atomic_write_text` (Constitution I:
one shared atomic writer — a crash mid-write never truncates the JSON).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llmxive.config import repo_root as _repo_root
from llmxive.state._io import atomic_write_text


def _dir(repo_root: Path | None) -> Path:
    root = repo_root or _repo_root()
    return root / "state" / "unverifiable_tasks"


def _path(project_id: str, *, repo_root: Path | None = None) -> Path:
    return _dir(repo_root) / f"{project_id}.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def load(project_id: str, *, repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Return the recorded unverifiable-task entries for ``project_id`` (``[]`` if
    none). Each entry is a dict with the contract keys documented above."""
    p = _path(project_id, repo_root=repo_root)
    if not p.is_file():
        return []
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    tasks = rec.get("tasks") if isinstance(rec, dict) else None
    return [t for t in tasks if isinstance(t, dict)] if isinstance(tasks, list) else []


def recorded_keys(project_id: str, *, repo_root: Path | None = None) -> set[str]:
    """The set of ``task_key``s already flagged unverifiable — the verifier skips
    these (they are not re-judged until :func:`clear` is called)."""
    return {
        str(t["task_key"])
        for t in load(project_id, repo_root=repo_root)
        if isinstance(t, dict) and t.get("task_key")
    }


def has_unverifiable(project_id: str, *, repo_root: Path | None = None) -> bool:
    """True iff ``project_id`` has ANY recorded unverifiable task — the signal CORE
    uses to route the project to ``research_full_revision``."""
    return bool(load(project_id, repo_root=repo_root))


def record_unverifiable(
    project_id: str,
    task_key: str,
    reason: str,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Record (or bump) ``task_key`` as repeatedly-unverifiable for ``project_id``.

    A new task_key starts at ``reject_count=1``; a repeat call increments it and
    refreshes ``last_reason`` / ``last_seen`` (``first_seen`` is preserved). In
    normal operation the verifier records each key ONCE (it stops re-judging a
    recorded task), so ``reject_count`` counts the number of times the task has
    re-entered the unverifiable state across kickback cycles. Returns the written
    record."""
    tasks = load(project_id, repo_root=repo_root)
    now = _now()
    by_key = {t.get("task_key"): t for t in tasks}
    entry = by_key.get(task_key)
    if entry is None:
        tasks.append(
            {
                "task_key": task_key,
                "reject_count": 1,
                "last_reason": (reason or "").strip()[:600],
                "first_seen": now,
                "last_seen": now,
            }
        )
    else:
        entry["reject_count"] = int(entry.get("reject_count", 0)) + 1
        entry["last_reason"] = (reason or "").strip()[:600]
        entry["last_seen"] = now
        entry.setdefault("first_seen", now)
    rec = {"project_id": project_id, "tasks": tasks, "updated_at": now}
    atomic_write_text(
        _path(project_id, repo_root=repo_root),
        json.dumps(rec, indent=2, sort_keys=False) + "\n",
    )
    return rec


def clear(project_id: str, *, repo_root: Path | None = None) -> None:
    """Drop ALL unverifiable records for ``project_id`` (the whole file).

    CORE calls this after routing the project to ``research_full_revision`` so the
    re-planned cycle starts with a clean slate."""
    _path(project_id, repo_root=repo_root).unlink(missing_ok=True)


__all__ = [
    "clear",
    "has_unverifiable",
    "load",
    "record_unverifiable",
    "recorded_keys",
]
