"""Concurrency-safe project ID allocation (Q1B fix from spec 004).

Background: prior to this module, `cli._cmd_brainstorm` computed
`next_num` once at the top of the function from an in-memory snapshot
of `state/projects/`, then claimed IDs sequentially. Two concurrent
brainstorm runs (e.g., two cron jobs firing at the same time) would
each compute the same `next_num` from their independent disk snapshots
and both write `PROJ-NNN-<slug-A>.yaml` / `PROJ-NNN-<slug-B>.yaml` —
producing duplicate project numbers with different slugs (verified on
disk: PROJ-261-evaluating-... + PROJ-261-investigating-...; PROJ-262-
predicting-... + PROJ-262-quantifying-...).

This module wraps the read-next-num + write-state-YAML critical
section in an `fcntl.flock`-protected atomic block. The lock is held
only during the disk snapshot + the state-YAML write (microseconds),
not during the LLM call (which is the long-running part).

Lock file: `state/.brainstorm.lock`. Lock is exclusive (LOCK_EX).
On non-POSIX platforms (Windows), `fcntl` is unavailable — the lock
falls back to a no-op + a logged warning. (llmXive is POSIX-only per
the spec; Windows fallback is defense-in-depth.)
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import Iterator
from pathlib import Path


def _lock_path(repo_root: Path) -> Path:
    return repo_root / "state" / ".brainstorm.lock"


@contextlib.contextmanager
def project_id_lock(repo_root: Path) -> Iterator[None]:
    """Hold an exclusive lock on `state/.brainstorm.lock` for the
    duration of the with-block.

    On POSIX, uses `fcntl.flock(LOCK_EX)`. On non-POSIX, no-op (logs a
    warning to stderr).
    """
    lock_file = _lock_path(repo_root)
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        import fcntl  # type: ignore[import-not-found]
    except ImportError:
        print(
            "[project_id_lock] fcntl unavailable (non-POSIX?); "
            "concurrent-safety NOT enforced",
            file=sys.stderr,
        )
        yield
        return

    fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def next_available_proj_num(
    *,
    repo_root: Path,
    starting_num: int = 1,
) -> int:
    """Scan `state/projects/` and `projects/` from disk and return the
    smallest `n` >= starting_num such that no `PROJ-NNN-*` exists.

    MUST be called inside `project_id_lock(repo_root)` to be safe
    against concurrent invocations. (This function does NOT take the
    lock itself — the caller controls the critical-section boundary.)
    """
    state_dir = repo_root / "state" / "projects"
    projects_dir = repo_root / "projects"

    used: set[int] = set()
    if state_dir.is_dir():
        for child in state_dir.iterdir():
            if child.suffix != ".yaml":
                continue
            stem = child.stem  # e.g., "PROJ-261-evaluating-..."
            n = _extract_num(stem)
            if n is not None:
                used.add(n)
    if projects_dir.is_dir():
        for child in projects_dir.iterdir():
            if not child.is_dir():
                continue
            n = _extract_num(child.name)
            if n is not None:
                used.add(n)

    n = max(starting_num, 1)
    while n in used:
        n += 1
    return n


def _extract_num(name: str) -> int | None:
    """Parse 'PROJ-NNN-...' (or 'PROJ-NNN-..-iter2') and return NNN
    as int, or None if not parseable.

    Per the post spec-004 convention, `-iterN` siblings are deprecated
    but historic ones may still appear in `state/projects/` snapshots
    on older branches. We treat them as occupying their canonical
    PROJ-NNN slot too (defensive).
    """
    if not name.startswith("PROJ-"):
        return None
    parts = name.split("-")
    if len(parts) < 2:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None
