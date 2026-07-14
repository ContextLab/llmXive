"""The execution fix-loop must TERMINATE — the outer re-plan loop was unbounded.

A project whose analysis cannot run climbed the whole ladder (12 fix rounds x every
model tier), then RE-PLANNED — and `reset_fix_loop` wiped BOTH `fix_rounds` and
`model_tier`, so it started the entire ladder over with no memory that it had ever
been here. PROJ-029 burned 843 implementer calls in ONE day cycling this loop, and
because a re-opened project still looks "nearly done", the shortest-remaining-first
scheduler handed it a worker every tick: 12 churning projects consumed ~4,000 of the
day's 5,111 implementer calls while 400 projects got NONE, and only 2 crossed.

Two monotonic counters fix it: `total_attempts` (never reset — how much compute this
project has burned) and `replan_rounds` (never reset by the re-plan it counts).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.state import execution_status as es


def _fail(pid: str, repo: Path) -> dict:
    return es.record(
        pid, ok=False, reason="boom", artifacts=[], failures=["x"], repo_root=repo
    )


def test_total_attempts_is_monotonic_across_escalation_and_replan(tmp_path: Path) -> None:
    """It must survive BOTH resets — it is the only honest record of burned compute."""
    pid = "PROJ-029-x"
    for _ in range(3):
        _fail(pid, tmp_path)
    assert es.total_attempts(pid, repo_root=tmp_path) == 3

    es.bump_model_tier(pid, repo_root=tmp_path)   # resets fix_rounds
    assert es.fix_rounds(pid, repo_root=tmp_path) == 0
    assert es.total_attempts(pid, repo_root=tmp_path) == 3, "escalation wiped the history"

    _fail(pid, tmp_path)
    es.reset_fix_loop(pid, repo_root=tmp_path)    # the RE-PLAN transition
    assert es.fix_rounds(pid, repo_root=tmp_path) == 0
    assert es.total_attempts(pid, repo_root=tmp_path) == 4, "re-plan wiped the history"


def test_replan_rounds_increments_and_survives(tmp_path: Path) -> None:
    pid = "PROJ-029-y"
    _fail(pid, tmp_path)
    assert es.replan_rounds(pid, repo_root=tmp_path) == 0
    es.reset_fix_loop(pid, repo_root=tmp_path)
    assert es.replan_rounds(pid, repo_root=tmp_path) == 1
    _fail(pid, tmp_path)   # record() must not clobber it
    assert es.replan_rounds(pid, repo_root=tmp_path) == 1
    es.reset_fix_loop(pid, repo_root=tmp_path)
    assert es.replan_rounds(pid, repo_root=tmp_path) == 2


def test_replan_cap_is_reachable(tmp_path: Path) -> None:
    """After MAX_REPLAN_ROUNDS the routing layer must have a signal to stop."""
    pid = "PROJ-029-z"
    _fail(pid, tmp_path)
    for _ in range(es.MAX_REPLAN_ROUNDS):
        es.reset_fix_loop(pid, repo_root=tmp_path)
    assert es.replan_rounds(pid, repo_root=tmp_path) >= es.MAX_REPLAN_ROUNDS


def test_success_clears_the_churn_counters(tmp_path: Path) -> None:
    """A project that finally RUNS is not a churner — it must not stay penalised."""
    pid = "PROJ-029-ok"
    for _ in range(4):
        _fail(pid, tmp_path)
    es.record(pid, ok=True, reason="ran", artifacts=["data/x.csv"], failures=[], repo_root=tmp_path)
    assert es.fix_rounds(pid, repo_root=tmp_path) == 0
    assert es.total_attempts(pid, repo_root=tmp_path) == 0
