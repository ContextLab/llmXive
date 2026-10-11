"""A model outage pauses the acceptance run; it does not end it.

Canary 11 (2026-10-11) died at step 7, and canary 6 at step 45, with
``BackendUnavailable``: one model's circuit was open, its peer hung, and the
exception left ``run`` as a failed acceptance. Scheduled production runs meet
the same outage by trying the project again on the next tick. The runner now
does the same inside its wall-clock budget, without spending one of its steps.
"""
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.backends.base import BackendUnavailable
from llmxive.pipeline import acceptance, graph
from llmxive.state import project as store
from llmxive.types import Project, Stage

PID = "PROJ-911-outage"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    now = datetime.now(UTC)
    (tmp_path / "projects" / PID).mkdir(parents=True)
    store.save(Project(id=PID, title="Outage", field="mathematics",
                       current_stage=Stage.FLESH_OUT_COMPLETE, points_research={}, points_paper={},
                       created_at=now, updated_at=now, artifact_hashes={}), repo_root=tmp_path)
    return tmp_path


def _steps(monkeypatch, repo: Path, script: list):
    """Make each pipeline step do the next thing in ``script``: raise it, or move to it."""
    calls: list[str] = []

    def step(project, *, repo_root):
        action = script.pop(0)
        calls.append(project.current_stage.value)
        if isinstance(action, Exception):
            raise action
        project.current_stage = action
        store.save(project, repo_root=repo_root)
        return project

    monkeypatch.setattr(graph, "run_one_step", step)
    return calls


def test_an_outage_is_waited_out_and_the_step_is_run_again(repo: Path, monkeypatch, capsys) -> None:
    waits: list[float] = []
    monkeypatch.setattr(acceptance.time, "sleep", waits.append)
    calls = _steps(monkeypatch, repo, [
        BackendUnavailable("every model in chain failed"),
        BackendUnavailable("circuit open"),
        Stage.VALIDATED,
        Stage.BLOCKED,
    ])
    with pytest.raises(RuntimeError, match="step limit exhausted"):
        acceptance.run(PID, repo, max_steps=2, outage_wait_s=45)
    # The first step ran three times and counted once: the limit of two was
    # reached by two completed steps, not by the two outages.
    assert calls == ["flesh_out_complete", "flesh_out_complete", "flesh_out_complete", "validated"]
    assert waits == [45, 45]
    result = acceptance.json.loads((repo / "state/acceptance" / f"{PID}.json").read_text())
    assert [(s["before"], s["after"]) for s in result["steps"]] == [
        ("flesh_out_complete", "validated"), ("validated", "blocked")]
    assert [o["stage"] for o in result["outages"]] == ["flesh_out_complete", "flesh_out_complete"]
    assert "every model in chain failed" in result["outages"][0]["reason"]
    out = capsys.readouterr().out
    assert out.count("[acceptance] 1: flesh_out_complete") == 1
    assert out.count("[acceptance] outage at flesh_out_complete") == 2


def test_an_outage_that_outlasts_the_budget_fails_the_run(repo: Path, monkeypatch) -> None:
    clock = {"now": 0.0}
    monkeypatch.setattr(acceptance.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(acceptance.time, "sleep", lambda s: clock.__setitem__("now", clock["now"] + s))
    calls = _steps(monkeypatch, repo, [BackendUnavailable("down")] * 10)
    with pytest.raises(RuntimeError, match="budget exhausted"):
        acceptance.run(PID, repo, budget_s=100, outage_wait_s=40)
    # Tried at 0 s, 40 s, 80 s and, after a wait cut to the 20 s that remained, at 100 s.
    assert len(calls) == 4
    result = acceptance.json.loads((repo / "state/acceptance" / f"{PID}.json").read_text())
    assert result["status"] == "failed" and len(result["outages"]) == 4


def test_any_other_error_still_ends_the_run_at_once(repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(acceptance.time, "sleep", lambda _s: pytest.fail("must not wait"))
    calls = _steps(monkeypatch, repo, [ValueError("a real defect"), Stage.VALIDATED])
    with pytest.raises(ValueError, match="a real defect"):
        acceptance.run(PID, repo)
    assert calls == ["flesh_out_complete"]
