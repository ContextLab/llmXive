"""Persisted per-project clarifier attempt counter (spec 015 T032).

Spec 015 / discrepancy #5: the clarifier and paper-clarifier previously hardcoded
``attempts_so_far: 0`` in their mechanical step, so neither the LLM nor the agent
could see the real attempt count — the documented escalation path
(``specified → human_input_needed``) was unreachable. This module persists the
count to disk per-project (one file under each agent's ``.specify/memory``
directory) so callers can read the true count, bump it on each invocation, write
``human_input_needed.yaml`` when the cap is hit, and reset on success.

The same primitive serves the research clarifier (``ctx.project_dir/.specify/memory``)
and the paper clarifier (``ctx.project_dir/paper/.specify/memory``).
"""

from __future__ import annotations

from pathlib import Path

import yaml

_ATTEMPTS_FILENAME = "clarifier_attempts.yaml"
_HUMAN_INPUT_FILENAME = "human_input_needed.yaml"


def _attempts_path(memory_dir: Path) -> Path:
    return memory_dir / _ATTEMPTS_FILENAME


def read_attempts(memory_dir: Path) -> int:
    """Return the persisted attempt count (0 when no record exists)."""
    p = _attempts_path(memory_dir)
    if not p.exists():
        return 0
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return 0
    n = data.get("attempts", 0) if isinstance(data, dict) else 0
    return int(n) if isinstance(n, int) and n >= 0 else 0


def bump_attempts(memory_dir: Path) -> int:
    """Increment and persist; return the new count."""
    memory_dir.mkdir(parents=True, exist_ok=True)
    new_n = read_attempts(memory_dir) + 1
    _attempts_path(memory_dir).write_text(
        yaml.safe_dump({"attempts": new_n}), encoding="utf-8",
    )
    return new_n


def reset_attempts(memory_dir: Path) -> None:
    """Clear the persisted count (call on successful clarify)."""
    p = _attempts_path(memory_dir)
    if p.exists():
        p.unlink()


def write_human_input_needed(memory_dir: Path, reason: str, *, stage: str = "clarify") -> Path:
    """Drop a ``human_input_needed.yaml`` so the graph routes the project to
    ``HUMAN_INPUT_NEEDED`` rather than retrying the clarifier forever."""
    memory_dir.mkdir(parents=True, exist_ok=True)
    p = memory_dir / _HUMAN_INPUT_FILENAME
    p.write_text(yaml.safe_dump({"reason": reason, "stage": stage}), encoding="utf-8")
    return p


__all__ = [
    "bump_attempts",
    "read_attempts",
    "reset_attempts",
    "write_human_input_needed",
]
