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


def test_successful_execution_is_invalidated_by_code_or_output_edits(tmp_path):
    project, _ = _project(tmp_path, "print('actual analysis')\n")
    data = project / "data/result.csv"
    data.parent.mkdir()
    data.write_text("n,square\n3,9\n")
    def record():
        execution_status.record(project.name, ok=True, reason="measured output",
                                artifacts=["data/result.csv"], failures=[], repo_root=tmp_path)
    record()
    assert execution_status.is_ok(project.name, repo_root=tmp_path)
    (project / "code/run.py").write_text("raise RuntimeError('regression')\n")
    assert not execution_status.is_ok(project.name, repo_root=tmp_path)
    record()
    data.write_text("n,square\n3,1234\n")
    assert not execution_status.is_ok(project.name, repo_root=tmp_path)
    record()
    data.unlink()
    assert not execution_status.is_ok(project.name, repo_root=tmp_path)


def test_runbook_pytest_failure_blocks_generated_artifact_acceptance(tmp_path, monkeypatch):
    import sys

    from llmxive import sandbox
    from llmxive.execution.analysis_runner import extract_run_commands, run_analysis

    project, tasks = _project(tmp_path, (
        "from pathlib import Path\nPath('data').mkdir(exist_ok=True)\n"
        "Path('data/counts.csv').write_text('n,count\\n3,9\\n')\n"
    ))
    quickstart = tasks.parent / "quickstart.md"
    quickstart.write_text("```bash\npython code/run.py\npytest test_analysis.py -q\n```\n")
    (project / "code/test_analysis.py").write_text("def test_computation():\n    assert 3 * 3 == 8\n")
    # Use the installed test interpreter; commands and pytest run in real subprocesses.
    monkeypatch.setattr(sandbox, "ensure_venv", lambda project_dir: Path(sys.executable))
    assert extract_run_commands(quickstart.read_text())[-1] == "python -m pytest test_analysis.py -q"
    result = run_analysis(project)
    assert not result.ok
    assert result.artifacts_produced == ["data/counts.csv"]
    assert len(result.commands) == 2 and result.commands[1].returncode == 1
    assert "FAILED" in result.commands[1].tail


def test_multiline_task_deliverables_reach_implementer_and_verifier(tmp_path, monkeypatch):
    from llmxive.speckit.implement_cmd import ImplementerAgent

    project, tasks = _project(tmp_path, "print('code only')\n")
    text = "- [ ] T008 Export the following:\n  `data/counts.csv` with exact counts.\n\n- [ ] T009 Plot data/plot.png\n"
    task_id, description = ImplementerAgent()._next_incomplete(text)
    assert task_id == "T008" and "data/counts.csv" in description
    assert "data/plot.png" not in description
    tasks.write_text(text.replace("[ ] T008", "[X] T008"))
    monkeypatch.setattr(tv, "verify_task", lambda **kw: tv.TaskVerdict(True, "should not be reached"))
    mem = project / ".specify/memory"
    result = tv.run_verification_pass(project, tasks, already_verified=set(),
                                     notes_path=mem / "notes.md", state_path=mem / "task_verify.yaml")
    assert result["rejected"] and "data/counts.csv" in result["rejected"][0][1]
    assert "[ ] T008" in tasks.read_text()


def test_src_package_executes_and_is_in_context_fabrication_and_fingerprint_checks(tmp_path):
    from llmxive.execution.fabrication_guard import find_code_fabrication
    from llmxive.speckit.implement_cmd import _summarize_existing_code

    project, tasks = _project(tmp_path, "")
    (project / "code/run.py").unlink()
    source = project / "src/nested"
    source.mkdir(parents=True)
    library = project / "src/library.py"
    library.write_text("def square(n):\n    return n * n\n")
    (source / "run.py").write_text(
        "from pathlib import Path\nfrom library import square\n"
        "Path('data').mkdir(exist_ok=True)\n"
        "Path('data/counts.csv').write_text(f'n,square\\n3,{square(3)}\\n')\n"
    )
    (tasks.parent / "quickstart.md").write_text("```bash\npython -m src.nested.run\n```\n")
    run_implementation_preview(project)
    assert (project / "data/counts.csv").read_text().endswith("3,9\n")
    assert "from src.library import square" in _summarize_existing_code(project)
    execution_status.record(project.name, ok=True, reason="computed",
                            artifacts=["data/counts.csv"], failures=[], repo_root=tmp_path)
    library.write_text("import random\naccuracy = random.uniform(0.8, 0.99)\n")
    assert find_code_fabrication(project)
    assert not execution_status.is_ok(project.name, repo_root=tmp_path)


def test_output_producer_runs_with_relative_project_path(tmp_path, monkeypatch):
    from llmxive import sandbox

    project, _ = _project(tmp_path, "from pathlib import Path\nPath('result.txt').write_text('computed')\n")
    monkeypatch.chdir(tmp_path)
    result = sandbox.run_python_script(project_dir=project.relative_to(tmp_path), script_relpath="code/run.py")
    assert result.ok, result.stderr
    assert (project / "result.txt").read_text() == "computed"
