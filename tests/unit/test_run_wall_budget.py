"""Per-run wall-clock budget in the ``run`` command loop.

A multi-gate convergence run on the slow reasoning default (qwen3.5-122b) can
accumulate past the 330-min ``llmxive-pipeline.yml`` job timeout; if the job is
killed mid-step the commit-and-push never runs and the WHOLE run's work is lost
(observed: a single 492 run executing ~4.3h). ``_cmd_run`` now stops STARTING new
steps once the elapsed wall-clock exceeds ``LLMXIVE_RUN_WALL_BUDGET_S`` so the
run returns normally and its progress commits before the CI timeout. A fast run
never reaches the budget (pure safety net). These tests drive the REAL loop;
only the scheduler/graph collaborators are stubbed (internal control flow, not
external resources).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from types import SimpleNamespace

from llmxive.pipeline import graph, scheduler
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _args(max_tasks: int = 5) -> SimpleNamespace:
    return SimpleNamespace(agent=None, stage=None, project=None, max_tasks=max_tasks)


def _proj(stage: Stage) -> Project:
    now = datetime.now(UTC)
    return Project(id="PROJ-903-budget", title="X", field="computer science",
                   current_stage=stage, created_at=now, updated_at=now)


def _wire(monkeypatch, *, step_sleep_s: float, counter: dict) -> None:
    # pick_next always offers a project so the loop WOULD run to max_tasks.
    monkeypatch.setattr(scheduler, "pick_next", lambda stage=None: _proj(Stage.VALIDATED))

    def _step(project, repo_root=None):
        counter["n"] += 1
        if step_sleep_s:
            time.sleep(step_sleep_s)
        # Return an ADVANCED stage so the loop continues (not a cycle-break).
        return _proj(Stage.PROJECT_INITIALIZED)

    monkeypatch.setattr(graph, "run_one_step", _step)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)


def test_wall_budget_stops_the_loop_early(tmp_path, monkeypatch) -> None:
    from llmxive.cli import _cmd_run

    counter = {"n": 0}
    # Budget 0.05s; each step sleeps 0.1s → step 1 runs, step 2's pre-check trips.
    monkeypatch.setenv("LLMXIVE_RUN_WALL_BUDGET_S", "0.05")
    _wire(monkeypatch, step_sleep_s=0.1, counter=counter)

    rc = _cmd_run(_args(max_tasks=5))

    assert rc == 0
    # Budget broke the loop after ONE step despite max_tasks=5 (pre-fix: 5).
    assert counter["n"] == 1


def test_fast_run_never_hits_the_budget(tmp_path, monkeypatch) -> None:
    """Regression: with a generous budget the loop still does all max_tasks
    steps — the safety net must not fire on a normal fast run."""
    from llmxive.cli import _cmd_run

    counter = {"n": 0}
    monkeypatch.setenv("LLMXIVE_RUN_WALL_BUDGET_S", "100000")
    _wire(monkeypatch, step_sleep_s=0.0, counter=counter)

    rc = _cmd_run(_args(max_tasks=5))

    assert rc == 0
    assert counter["n"] == 5  # all steps ran; budget never tripped
