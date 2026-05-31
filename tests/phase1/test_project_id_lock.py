"""Regression tests for the project-ID allocation lock (Q1B fix from spec 004).

These tests verify that concurrent calls to `next_available_proj_num`
under `project_id_lock` cannot produce duplicate PROJ-NNN values
(the bug that produced PROJ-261-evaluating-... + PROJ-261-investigating-...
and PROJ-262-predicting-... + PROJ-262-quantifying-... on `main`).

Per Constitution Principle III: real filesystem (pytest tmp_path) +
real `os.fork`-based concurrency, no mocks.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmxive.state.project_id_lock import (
    next_available_proj_num,
    project_id_lock,
)


def _seed_existing(repo_root: Path, nums: list[int]) -> None:
    """Plant fake existing project state YAMLs so next_available_proj_num
    has a non-trivial 'used' set."""
    state_dir = repo_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    for n in nums:
        (state_dir / f"PROJ-{n:03d}-fake-existing.yaml").write_text(
            "id: dummy\n", encoding="utf-8"
        )


def test_next_available_with_no_existing(tmp_path: Path) -> None:
    """No projects exist → next available is 001."""
    assert next_available_proj_num(repo_root=tmp_path) == 1


def test_next_available_with_gaps(tmp_path: Path) -> None:
    """If 001, 003, 005 exist → next available is 002 (smallest gap)."""
    _seed_existing(tmp_path, [1, 3, 5])
    assert next_available_proj_num(repo_root=tmp_path) == 2


def test_next_available_skips_iter_suffixes(tmp_path: Path) -> None:
    """A historic PROJ-007-foo-iter2 from spec 003 era still occupies
    slot 7 — `next_available_proj_num(starting_num=7)` MUST skip past it."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "PROJ-007-foo-iter2.yaml").write_text("id: dummy\n", encoding="utf-8")
    # When starting from 7, must skip to 8 (since iter2 occupies slot 7).
    assert next_available_proj_num(repo_root=tmp_path, starting_num=7) == 8
    # When starting from 1 (default), 1 is free so we get 1.
    assert next_available_proj_num(repo_root=tmp_path) == 1


def test_next_available_scans_projects_dir_too(tmp_path: Path) -> None:
    """A PROJ-NNN dir without a state YAML still counts as used (defensive)."""
    (tmp_path / "projects" / "PROJ-042-orphan").mkdir(parents=True)
    assert next_available_proj_num(repo_root=tmp_path) != 42
    n = next_available_proj_num(repo_root=tmp_path)
    assert n == 1  # since 042 is the only used number, 1 is still free


def test_starting_num_respected(tmp_path: Path) -> None:
    """If caller asks for >= 100, return 100 even if lower nums are free."""
    assert next_available_proj_num(repo_root=tmp_path, starting_num=100) == 100


def test_lock_serializes_concurrent_allocations(tmp_path: Path) -> None:
    """The CRITICAL regression test: two `os.fork()`-spawned children
    each acquire the lock + compute next_available + write a state YAML +
    release. Result MUST be two DISTINCT project numbers, even though
    they raced.

    Without the lock, both would compute next_num=1 from the same disk
    snapshot and both write PROJ-001-*.yaml.
    """
    if not hasattr(os, "fork"):
        pytest.skip("os.fork not available (non-POSIX)")

    # Seed: no projects yet. Both children should land 001 + 002 (in
    # some order), not collide on 001.
    pipe_r, pipe_w = os.pipe()

    def child_work(slug: str) -> None:
        """In each child, take the lock + claim a PID + write a fake
        state YAML, then write the claimed PID to the pipe."""
        try:
            with project_id_lock(tmp_path):
                n = next_available_proj_num(repo_root=tmp_path)
                pid = f"PROJ-{n:03d}-{slug}"
                state_dir = tmp_path / "state" / "projects"
                state_dir.mkdir(parents=True, exist_ok=True)
                # Simulate a slow LLM-call-then-write... no actually,
                # we want to test the lock is held during the claim,
                # so write IMMEDIATELY (which is what cli.py does post-fix).
                (state_dir / f"{pid}.yaml").write_text(
                    f"id: {pid}\n", encoding="utf-8"
                )
                os.write(pipe_w, f"{pid}\n".encode())
        finally:
            os._exit(0)

    pid_a = os.fork()
    if pid_a == 0:
        os.close(pipe_r)
        child_work("alpha")
    pid_b = os.fork()
    if pid_b == 0:
        os.close(pipe_r)
        child_work("beta")

    os.close(pipe_w)
    os.waitpid(pid_a, 0)
    os.waitpid(pid_b, 0)

    output = b""
    while True:
        chunk = os.read(pipe_r, 4096)
        if not chunk:
            break
        output += chunk
    os.close(pipe_r)

    claimed = sorted(line.strip() for line in output.decode().splitlines() if line.strip())
    assert len(claimed) == 2, f"expected 2 PIDs claimed, got {claimed!r}"

    # The numbers MUST be distinct — that's the whole point.
    nums = {p.split("-")[1] for p in claimed}
    assert len(nums) == 2, (
        f"DUPLICATE PROJECT NUMBERS — lock failed: {claimed!r}"
    )
    # And both must be on disk.
    for pid in claimed:
        assert (tmp_path / "state" / "projects" / f"{pid}.yaml").is_file()


def test_lock_yields_inside_with_block(tmp_path: Path) -> None:
    """Smoke test: project_id_lock as context manager yields control
    to the with-block (we can perform work inside without hangs)."""
    inside = []
    with project_id_lock(tmp_path):
        inside.append("work-done")
    assert inside == ["work-done"]


def test_lock_releases_on_exception(tmp_path: Path) -> None:
    """If the with-block raises, the lock is still released so
    subsequent acquisitions don't deadlock."""
    with pytest.raises(RuntimeError, match="boom"):
        with project_id_lock(tmp_path):
            raise RuntimeError("boom")

    # Should be able to re-acquire immediately.
    with project_id_lock(tmp_path):
        pass  # no hang
