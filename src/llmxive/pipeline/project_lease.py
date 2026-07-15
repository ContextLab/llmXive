"""Per-project advisory lease — the IN-HOST half of the concurrent-persistence
guard (issue #1139, defect D16: "concurrent persistence loses completed work").

Background
----------
The Advance workflow runs a matrix of scheduler ticks that each pick a project,
mutate its canonical state, and push to ``main``. ``scheduler.pick_for_worker``
is deterministic only *at a fixed HEAD*: two ticks that started from DIFFERENT
commits can pick the SAME project and both write its state. The rebase-race in
``scripts/ci/commit-and-push.sh`` then does a per-file, last-writer-wins merge,
so one tick's freshly-computed counters (``fix_rounds`` / ``replan_rounds`` /
convergence rounds) can be silently overwritten by the other — completed work
is lost.

This module provides a kernel-enforced ``fcntl.flock`` lease keyed by project
id, so two ticks that share a filesystem can never co-mutate one project's state
at the same time. It mirrors ``llmxive.state.project_id_lock`` exactly (same
``os.open`` + ``fcntl.flock`` approach, same non-POSIX no-op fallback) rather
than forking a divergent lock implementation (Constitution I). Where
``project_id_lock`` guards a single shared critical section (ID allocation) with
one lock file, this keys the lock file by ``project_id`` so DIFFERENT projects
proceed in parallel while the SAME project serializes.

Scope: in-host only. Cross-RUNNER protection still relies on the CAS push
-----------------------------------------------------------------------
``fcntl.flock`` is only meaningful between processes that share the same
filesystem/host. On GitHub Actions each matrix worker runs on its OWN VM, so
this lease does NOT serialize ticks across separate runners — that half of the
guarantee still relies on the compare-and-swap push in
``scripts/ci/commit-and-push.sh`` (rebase-onto-latest-origin/main, then a
re-fetch verify that HEAD actually landed; a lost race fails loud and the
project stays schedulable). The lease closes the gap that CAS cannot: two ticks
on the SAME host (a local ``python -m llmxive run`` fan-out, a future
single-runner multi-worker deployment, or an overlapping re-drive that escaped
the per-index ``concurrency`` group) mutating one project's on-disk state
concurrently.

Relationship to ``llmxive.pipeline.lock``
-----------------------------------------
``pipeline.lock`` is a TTL YAML-sentinel advisory lock (holder run id + expiry)
that the scheduler consults so it never *picks* an actively-held project. That
lock is a check-then-write on a YAML file — it has a TOCTOU window and gives no
kernel guarantee. This lease is complementary: it is the atomic, kernel-enforced
mutual-exclusion primitive that a ``pipeline.lock`` acquire/mutate cycle can be
wrapped in to close that window on a single host. It intentionally does NOT
duplicate the TTL/holder bookkeeping — flock is released automatically when the
holding process exits, so there is no stale-lock class to reclaim.

How ``scheduler.py`` should adopt it (wiring is owned elsewhere)
---------------------------------------------------------------
This module only provides the primitive; wiring it into the scheduler is done in
a separate change. The intended adoption::

    from llmxive.pipeline.project_lease import project_lease

    with project_lease(project_id, repo_root=repo_root) as acquired:
        if not acquired:
            # Another in-host tick already owns this project this cycle;
            # skip it and let pick_for_worker fall through to the next
            # candidate rather than co-mutating its state.
            continue
        # ... pick -> run_one_step -> persist for `project_id` ...

Use non-blocking acquisition (the default) in the scheduler so a contended
project is skipped, not waited on — waiting would just serialize the whole tick
behind one project. Pass ``blocking=True`` only where you genuinely must run the
critical section (e.g. a single-project CLI command) and can afford to wait.
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import Iterator
from pathlib import Path


def _leases_dir(repo_root: Path) -> Path:
    return repo_root / "state" / "leases"


def _lease_path(repo_root: Path, project_id: str) -> Path:
    if not project_id or "/" in project_id or "\\" in project_id or project_id in (".", ".."):
        # Guard against a project id escaping the leases directory. Real ids are
        # "PROJ-###-slug" and never contain path separators.
        raise ValueError(f"unsafe project_id for lease file: {project_id!r}")
    return _leases_dir(repo_root) / f"{project_id}.lock"


@contextlib.contextmanager
def project_lease(
    project_id: str,
    *,
    repo_root: Path,
    blocking: bool = False,
) -> Iterator[bool]:
    """Hold a per-project advisory lease on ``state/leases/<project_id>.lock``
    for the duration of the with-block.

    Yields ``True`` if the lease was acquired (this block now holds exclusive
    in-host ownership of ``project_id``), or ``False`` if it is already held by
    another open file description (only possible in the default non-blocking
    mode). When ``False`` is yielded no lock is held and the caller MUST NOT
    mutate the project — skip it this cycle.

    Args:
        project_id: canonical project id (``PROJ-###-slug``); keys the lock file.
        repo_root: repository root; the lock lives under ``<repo_root>/state/leases``.
        blocking: if ``True``, block until the lease is acquired (always yields
            ``True``). If ``False`` (default), acquire without waiting and yield
            ``False`` when the project is already leased.

    On POSIX, uses ``fcntl.flock`` (``LOCK_EX`` blocking / ``LOCK_EX | LOCK_NB``
    non-blocking). ``flock`` is tied to the open file description, so two
    independent ``os.open`` calls of the same lock file conflict even within one
    process — which is exactly what lets a re-entrant same-project acquire in the
    same process return ``False``. The lease is released on exit (and, as a
    kernel guarantee, whenever the holding process dies), so there is no stale
    lease to reclaim.

    On non-POSIX platforms (Windows), ``fcntl`` is unavailable; the lease
    degrades to a no-op that yields ``True`` with a stderr warning (llmXive is
    POSIX-only; this is defense-in-depth, matching ``project_id_lock``).
    """
    lease_file = _lease_path(repo_root, project_id)
    lease_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        import fcntl
    except ImportError:
        print(
            "[project_lease] fcntl unavailable (non-POSIX?); "
            "in-host concurrent-safety NOT enforced",
            file=sys.stderr,
        )
        yield True
        return

    fd = os.open(str(lease_file), os.O_CREAT | os.O_RDWR, 0o644)
    acquired = False
    try:
        flags = fcntl.LOCK_EX if blocking else (fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            fcntl.flock(fd, flags)
            acquired = True
        except BlockingIOError:
            # Non-blocking acquire found the project already leased. Yield False
            # WITHOUT holding a lock — the caller must skip this project.
            acquired = False
        yield acquired
    finally:
        if acquired:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        else:
            os.close(fd)
