"""Only a fresh judgement of new work is a strike against a task.

Audit of fourteen acceptance runs (2026-10-11): the logs record about 65
"rejected 3x" events, but only 30 runs of three consecutive INCOMPLETE verdicts
from the verifier model. The other strikes were never a judgement at all:

* the platform's own run of the task's script failed, and the annotation it
  left on the task line is rejected without a model call;
* a declared output did not exist yet.

Both counted toward the three that mark a task unverifiable and send the
project back to planning, so a script that needed three debugging rounds was
indistinguishable from work the verifier had judged three times. They now count
toward a separate, larger limit; three judgements still close a task. Every
decision is also written to a ledger, because the audit could not say what the
strikes of a past run had been.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llmxive.agents import task_verifier as tv
from llmxive.state import unverifiable

PID = "PROJ-913-strikes"
TASK = "T004 connect the end-to-end entry point"
FAILED = TASK + " <!-- FAILED-IN-EXECUTION: code/run_analysis.py exit=1 -->"


def _pass(tmp_path: Path, line: str, mark: str = "~") -> dict:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(f"# Tasks\n\n- [{mark}] {line}\n", encoding="utf-8")
    return tv.run_verification_pass(
        tmp_path, tasks, already_verified=set(),
        notes_path=tmp_path / "notes.md", state_path=tmp_path / "state.yaml",
        project_id=PID, repo_root=tmp_path)


def _judge(monkeypatch, complete: bool, calls: list | None = None) -> None:
    def verdict(**kwargs):
        if calls is not None:
            calls.append(kwargs["task_text"])
        return SimpleNamespace(complete=complete, reason="judged", deferred=False)
    monkeypatch.setattr(tv, "verify_task", verdict)


def test_a_failed_run_is_not_one_of_the_three_strikes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tv, "verify_task", lambda **k: pytest.fail("a failed run needs no model call"))
    for _ in range(tv.REJECT_CAP + 1):
        result = _pass(tmp_path, FAILED)
        assert [key for key, _ in result["rejected"]] == ["T004"]
        assert result["unverifiable"] == []
    assert not unverifiable.has_unverifiable(PID, repo_root=tmp_path)
    assert "Requested task execution failed" in (tmp_path / "notes.md").read_text(encoding="utf-8")


def test_failed_runs_are_still_bounded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tv, "verify_task", lambda **k: pytest.fail("no model call"))
    results = [_pass(tmp_path, FAILED) for _ in range(tv.STALL_CAP)]
    assert [r["unverifiable"] for r in results[:-1]] == [[]] * (tv.STALL_CAP - 1)
    assert results[-1]["unverifiable"] == ["T004"]
    assert [t["task_key"] for t in unverifiable.load(PID, repo_root=tmp_path)] == ["T004"]


def _ledger(tmp_path: Path) -> list[tuple[str, str]]:
    path = tmp_path / "state.ledger.jsonl"
    return [(e["task"], e["kind"]) for e in map(json.loads, path.read_text(encoding="utf-8").splitlines())]


def test_a_replayed_verdict_is_recorded_as_one_and_still_counts(tmp_path: Path, monkeypatch) -> None:
    """How often a redo changes nothing was not measurable from past runs.

    The behaviour is left as it was; the ledger now says which strikes were
    replays, so the next audit can decide from counts.
    """
    monkeypatch.setenv("LLMXIVE_RECEIPT_KEY", "k" * 64)
    calls: list = []
    _judge(monkeypatch, False, calls)
    results = [_pass(tmp_path, TASK, mark="X") for _ in range(tv.REJECT_CAP)]
    assert len(calls) == 1, "the same evidence is judged once"
    assert results[-1]["unverifiable"] == ["T004"]
    assert _ledger(tmp_path) == [("T004", "judged"), ("T004", "replayed"), ("T004", "replayed"),
                                 ("T004", "unverifiable")]


def test_the_ledger_names_what_each_decision_was(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tv, "signed_verdict", lambda *a, **k: None)
    _pass(tmp_path, FAILED)
    _pass(tmp_path, "T004 write `data/absent.csv` from the census")
    _judge(monkeypatch, False)
    _pass(tmp_path, TASK, mark="X")
    _judge(monkeypatch, True)
    _pass(tmp_path, TASK, mark="X")
    assert [kind for _, kind in _ledger(tmp_path)] == ["failed_run", "missing_artifact", "judged", "accepted"]


def test_three_fresh_judgements_still_close_the_task(tmp_path: Path, monkeypatch) -> None:
    # No signing key: nothing is cached, so each pass is a new judgement.
    monkeypatch.delenv("LLMXIVE_RECEIPT_KEY", raising=False)
    monkeypatch.setattr(tv, "signed_verdict", lambda *a, **k: None)
    _judge(monkeypatch, False)
    results = [_pass(tmp_path, TASK, mark="X") for _ in range(tv.REJECT_CAP)]
    assert [r["unverifiable"] for r in results] == [[], [], ["T004"]]


def test_failed_runs_do_not_shorten_the_judgement_allowance(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tv, "signed_verdict", lambda *a, **k: None)
    _judge(monkeypatch, False)
    assert _pass(tmp_path, FAILED)["unverifiable"] == []
    assert _pass(tmp_path, FAILED)["unverifiable"] == []
    assert _pass(tmp_path, TASK, mark="X")["unverifiable"] == []
    assert _pass(tmp_path, TASK, mark="X")["unverifiable"] == []
    assert _pass(tmp_path, TASK, mark="X")["unverifiable"] == ["T004"]


def test_acceptance_clears_both_counts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tv, "signed_verdict", lambda *a, **k: None)
    for _ in range(tv.STALL_CAP - 1):
        _pass(tmp_path, FAILED)
    _judge(monkeypatch, True)
    assert _pass(tmp_path, TASK, mark="X")["accepted"] == 1
    # A later regression starts from zero, not one run from the limit.
    assert _pass(tmp_path, FAILED)["unverifiable"] == []
