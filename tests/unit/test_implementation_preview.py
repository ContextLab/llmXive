"""Real execution must precede verification of generated-output tasks."""

from pathlib import Path

from llmxive.agents import task_verifier as tv
from llmxive.agents.task_verifier import _declared_paths, gather_evidence
from llmxive.execution.analysis_runner import _snapshot_artifacts, declared_deliverables
from llmxive.execution.fabrication_guard import find_synthetic_data_use
from llmxive.execution.stage import run_implementation_preview
from llmxive.state import execution_status


def test_evidence_paths_preserve_nested_roots_and_multidot_names(tmp_path):
    paths = ["paper/figures/tv_vs_N.png", "contracts/tv-summary.schema.yaml"]
    for path in paths:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("real content")
    task = "Write " + " and ".join(f"`{p}`" for p in paths)
    assert _declared_paths(task) == paths
    assert "MISSING" not in gather_evidence(tmp_path, task)
    assert declared_deliverables(task) == {paths[0]}
    assert paths[0] in _snapshot_artifacts(tmp_path)


def _project(tmp_path: Path, script: str) -> tuple[Path, Path]:
    project = tmp_path / "projects" / "PROJ-999-preview"
    code = project / "code"
    feature = project / "specs" / "001-test"
    code.mkdir(parents=True)
    feature.mkdir(parents=True)
    (code / "run.py").write_text(script)
    (feature / "quickstart.md").write_text("```bash\npython code/run.py\n```\n")
    tasks = feature / "tasks.md"
    tasks.write_text("- [X] T001 Export data/counts.csv\n- [ ] T002 Document results\n")
    return project, tasks


def test_preview_produces_output_with_open_tasks_without_accepting_gate(tmp_path):
    project, tasks = _project(tmp_path, (
        "from pathlib import Path\n"
        "Path('data').mkdir(exist_ok=True)\n"
        "Path('data/counts.csv').write_text('n,square\\n' + "
        "''.join(f'{n},{n*n}\\n' for n in range(1, 11)))\n"
    ))
    before = tasks.read_text()
    run_implementation_preview(project)
    assert (project / "data/counts.csv").read_text().endswith("10,100\n")
    assert tasks.read_text() == before
    assert not execution_status.is_ok(project.name, repo_root=tmp_path)
    assert execution_status.fix_rounds(project.name, repo_root=tmp_path) == 0


def test_preview_failure_supplies_traceback_without_consuming_final_fix_rounds(tmp_path):
    project, tasks = _project(tmp_path, "raise RuntimeError('actual computation failed')\n")
    before = tasks.read_text()
    run_implementation_preview(project)
    feedback = project / ".specify/memory/execution_feedback.md"
    assert "actual computation failed" in feedback.read_text()
    assert tasks.read_text() == before
    assert execution_status.fix_rounds(project.name, repo_root=tmp_path) == 0


def test_verified_receipt_invalidates_when_later_task_changes_code(tmp_path, monkeypatch):
    project, tasks = _project(tmp_path, "print('working code')\n")
    tasks.write_text("- [X] T001 Write code/run.py\n")
    monkeypatch.setattr(tv, "verify_task", lambda **kw: tv.TaskVerdict(True, "code inspected"))
    mem = project / ".specify/memory"
    tv.run_verification_pass(project, tasks, already_verified=set(),
                             notes_path=mem / "notes.md", state_path=mem / "task_verify.yaml")
    assert tv.verified_done_keys(project, tasks) == {"T001"}
    (project / "code/run.py").write_text("print('different code')\n")
    assert tv.verified_done_keys(project, tasks) == set()


def test_interrupted_verification_leaves_pending_not_accepted_checkbox(tmp_path, monkeypatch):
    import pytest

    project, tasks = _project(tmp_path, "print('working code')\n")
    tasks.write_text("- [X] T001 Write code/run.py\n")
    def interrupted(**kw):
        raise KeyboardInterrupt
    monkeypatch.setattr(tv, "verify_task", interrupted)
    mem = project / ".specify/memory"
    with pytest.raises(KeyboardInterrupt):
        tv.run_verification_pass(project, tasks, already_verified=set(),
                                 notes_path=mem / "notes.md", state_path=mem / "task_verify.yaml")
    assert "[~]" in tasks.read_text()
    assert tv.verified_done_keys(project, tasks) == set()


def test_wrapped_refusal_is_not_fabrication_but_unrelated_negation_is(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    script = code / "load.py"
    script.write_text('"""Reads actual observations; never falls back to\n    synthetic data."""\n')
    assert find_synthetic_data_use(tmp_path) == []
    script.write_text('"""Real data was not available.\n    We use synthetic data instead."""\n')
    assert find_synthetic_data_use(tmp_path)
