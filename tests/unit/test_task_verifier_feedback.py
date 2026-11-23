"""Exercise durable correction feedback across real file-backed verifier passes."""
import pytest
import yaml

from llmxive.agents import task_verifier as tv


@pytest.mark.parametrize("deterministic", [False, True])
def test_other_tasks_and_deferred_retry_do_not_erase_feedback(tmp_path, monkeypatch, deterministic):
    tasks = tmp_path / "tasks.md"
    notes = tmp_path / "notes.md"
    state = tmp_path / "verify.yaml"
    first = "T001 Write data/result.csv" if deterministic else "T001 Implement the calculation"
    tasks.write_text(f"- [X] {first}\n- [ ] T002 Document the interface\n")
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(False, "formula is incorrect"))

    def run(**kw):
        return tv.run_verification_pass(tmp_path, tasks, already_verified=set(),
                                        notes_path=notes, state_path=state, **kw)

    rejected = run()["rejected"]
    assert len(rejected) == 1
    reason = rejected[0][1]
    tasks.write_text(tasks.read_text().replace("[ ] T002", "[X] T002"))
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(True, "interface checked"))
    assert run()["accepted"] == 1
    assert reason in notes.read_text()
    assert yaml.safe_load(state.read_text())["T001"] == 1

    # Retry is deferred while an artifact exists but cannot yet be judged.
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data/result.csv").write_text("n,result\n1,1\n")
    tasks.write_text(tasks.read_text().replace("[ ] T001", "[X] T001"))
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(None, "backend unavailable"))
    # Change evidence for the prose-only case to invalidate its previous verdict.
    result = run(spec_context="Requirements reviewed on retry")
    assert "T001" in result["deferred"]
    assert reason in notes.read_text()

    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(True, "calculation checked"))
    run(spec_context="Requirements reviewed on retry")
    assert not notes.exists()
    assert not state.exists()


def test_replanned_id_drops_old_feedback_and_reject_count(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks.md"
    state = tmp_path / "verify.yaml"
    notes = tmp_path / "notes.md"
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(False, "old formula incorrect"))

    def run():
        return tv.run_verification_pass(tmp_path, tasks, already_verified=set(),
                                        notes_path=notes, state_path=state)

    for _ in range(2):
        tasks.write_text("- [X] T001 Calculate the original quantity\n")
        run()
    assert yaml.safe_load(state.read_text())["T001"] == 2
    tasks.write_text("- [ ] T001 Document the revised interface\n")
    run()
    assert not notes.exists()
    assert not state.exists()
    tasks.write_text("- [X] T001 Document the revised interface\n")
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(False, "new documentation missing"))
    result = run()
    assert not result["unverifiable"]
    assert yaml.safe_load(state.read_text())["T001"] == 1
    assert "old formula" not in notes.read_text()


def test_rejection_cap_keeps_diagnosis_for_replanning(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks.md"
    notes = tmp_path / "notes.md"
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(False, "calculation is a stub"))
    for attempt in range(tv.REJECT_CAP):
        tasks.write_text(f"- [X] T001 Calculate the quantity [UNVERIFIED: {attempt}] <!-- retry {attempt} -->\n")
        result = tv.run_verification_pass(tmp_path, tasks, already_verified=set(),
                                          notes_path=notes, state_path=tmp_path / "verify.yaml")
    assert result["unverifiable"] == ["T001"]
    tv.run_verification_pass(tmp_path, tasks, already_verified=set(),
                             notes_path=notes, state_path=tmp_path / "verify.yaml")
    assert "calculation is a stub" in notes.read_text()
    tasks.write_text("# No remaining tasks\n")
    tv.run_verification_pass(tmp_path, tasks, already_verified=set(),
                             notes_path=notes, state_path=tmp_path / "verify.yaml")
    assert not notes.exists()


def test_redefined_accepted_task_is_reviewed_again(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks.md"
    notes = tmp_path / "notes.md"
    state = tmp_path / "verify.yaml"
    tasks.write_text("- [X] T001 Calculate a finite sample\n")
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(True, "sample checked"))
    tv.run_verification_pass(tmp_path, tasks, already_verified=set(), notes_path=notes, state_path=state)
    snapshot = tv.claimed_done_keys(tasks.read_text())
    tasks.write_text("- [X] T001 Prove the result for every positive integer\n")
    monkeypatch.setattr(tv, "verify_task", lambda **_: tv.TaskVerdict(False, "finite sample is not a proof"))
    result = tv.run_verification_pass(tmp_path, tasks, already_verified=snapshot,
                                      notes_path=notes, state_path=state)
    assert result["rejected"] == [("T001", "finite sample is not a proof")]
    assert "[X]" not in tasks.read_text()
