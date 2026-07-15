"""Real-flock tests for the per-project advisory lease (issue #1139, defect D16).

Per Constitution Principle III these use REAL ``fcntl.flock`` on REAL files
under pytest ``tmp_path`` — no mocks. They assert the three properties the
scheduler will rely on:

* acquiring the same project lease twice in one process fails the second
  (non-blocking) acquire (yields ``False``) — the in-host mutual-exclusion;
* releasing the lease (leaving the with-block) frees it for the next acquire;
* different project ids are independent (two projects lease concurrently).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from llmxive.pipeline.project_lease import project_lease

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("fcntl") is None,
    reason="fcntl unavailable (non-POSIX)",
)


def test_yields_true_when_uncontended(tmp_path: Path) -> None:
    """A fresh project acquires cleanly and yields True."""
    with project_lease("PROJ-001-alpha", repo_root=tmp_path) as acquired:
        assert acquired is True


def test_lease_file_created_under_state_leases(tmp_path: Path) -> None:
    """The lock file lands in state/leases/<project_id>.lock."""
    with project_lease("PROJ-001-alpha", repo_root=tmp_path) as acquired:
        assert acquired is True
        assert (tmp_path / "state" / "leases" / "PROJ-001-alpha.lock").is_file()


def test_same_project_twice_second_is_false(tmp_path: Path) -> None:
    """THE core property: while one block holds the lease, a second
    non-blocking acquire of the SAME project id yields False (not held).

    fcntl.flock is tied to the open file description, so two independent
    os.open calls of the same lock file conflict even within one process."""
    with project_lease("PROJ-042-beta", repo_root=tmp_path) as first:
        assert first is True
        with project_lease("PROJ-042-beta", repo_root=tmp_path) as second:
            assert second is False


def test_releasing_frees_the_lease(tmp_path: Path) -> None:
    """After the holding with-block exits, the project can be re-leased."""
    with project_lease("PROJ-007-gamma", repo_root=tmp_path) as first:
        assert first is True
    # Outer block released — a fresh non-blocking acquire must now succeed.
    with project_lease("PROJ-007-gamma", repo_root=tmp_path) as again:
        assert again is True


def test_different_projects_are_independent(tmp_path: Path) -> None:
    """Two DIFFERENT project ids lease concurrently — no cross-project block."""
    with project_lease("PROJ-100-x", repo_root=tmp_path) as a:
        assert a is True
        with project_lease("PROJ-200-y", repo_root=tmp_path) as b:
            assert b is True


def test_lease_released_on_exception(tmp_path: Path) -> None:
    """If the with-block raises, the lease is released (no deadlock on retry)."""
    with pytest.raises(RuntimeError, match="boom"):
        with project_lease("PROJ-303-delta", repo_root=tmp_path) as acquired:
            assert acquired is True
            raise RuntimeError("boom")
    # Must re-acquire immediately — the lease was freed despite the exception.
    with project_lease("PROJ-303-delta", repo_root=tmp_path) as again:
        assert again is True


def test_blocking_acquire_succeeds_when_free(tmp_path: Path) -> None:
    """blocking=True yields True immediately when uncontended."""
    with project_lease("PROJ-404-eps", repo_root=tmp_path, blocking=True) as acquired:
        assert acquired is True


def test_cross_process_mutual_exclusion(tmp_path: Path) -> None:
    """REAL cross-process guarantee: a forked child cannot acquire a project
    the parent holds, and CAN acquire a different one. This is the scenario
    the scheduler relies on (two in-host ticks racing for one project)."""
    if not hasattr(os, "fork"):
        pytest.skip("os.fork not available (non-POSIX)")

    # Parent takes and HOLDS the lease on PROJ-500 for the child's lifetime.
    with project_lease("PROJ-500-held", repo_root=tmp_path) as held:
        assert held is True

        r_same, w_same = os.pipe()
        r_other, w_other = os.pipe()
        pid = os.fork()
        if pid == 0:  # child
            os.close(r_same)
            os.close(r_other)
            try:
                with project_lease("PROJ-500-held", repo_root=tmp_path) as c_same:
                    os.write(w_same, b"1" if c_same else b"0")
                with project_lease("PROJ-501-free", repo_root=tmp_path) as c_other:
                    os.write(w_other, b"1" if c_other else b"0")
            finally:
                os._exit(0)

        os.close(w_same)
        os.close(w_other)
        same = os.read(r_same, 1)
        other = os.read(r_other, 1)
        os.close(r_same)
        os.close(r_other)
        os.waitpid(pid, 0)

    assert same == b"0", "child must NOT acquire a project the parent holds"
    assert other == b"1", "child MUST acquire a different, free project"
