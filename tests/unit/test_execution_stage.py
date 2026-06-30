"""Tests for the dedicated execution phase + auto-fix loop (spec 023 #25).

Covers the execution-status store, the gate orchestration (success clears
feedback + records ok; failure writes feedback + re-opens failing tasks +
bumps the bounded fix counter), and the graph gate that holds
research_complete until the analysis actually runs.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.execution import analysis_runner
from llmxive.execution.analysis_runner import AnalysisRunResult, RunCommandResult
from llmxive.execution.stage import execute_and_gate
from llmxive.state import execution_status


def _bootstrap_project(tmp_path: Path, project_id: str, tasks_md: str) -> Path:
    proj = tmp_path / "projects" / project_id
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / ".specify" / "memory").mkdir(parents=True)
    (proj / "specs" / "001-x" / "tasks.md").write_text(tasks_md, encoding="utf-8")
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    return proj


# --- execution_status store -------------------------------------------------


def test_execution_status_record_roundtrip_and_fix_rounds(tmp_path: Path) -> None:
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    pid = "PROJ-001-x"
    # First failure -> fix_rounds 1, not ok.
    execution_status.record(pid, ok=False, reason="boom", artifacts=[],
                            failures=["x"], repo_root=tmp_path)
    assert execution_status.is_ok(pid, repo_root=tmp_path) is False
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    # Second failure -> 2.
    execution_status.record(pid, ok=False, reason="boom2", artifacts=[],
                            failures=["y"], repo_root=tmp_path)
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 2
    # Success -> ok True, counter reset.
    execution_status.record(pid, ok=True, reason="ok", artifacts=["data/x.csv"],
                            failures=[], repo_root=tmp_path)
    assert execution_status.is_ok(pid, repo_root=tmp_path) is True
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 0


# --- execute_and_gate orchestration ----------------------------------------


def test_execute_and_gate_success(tmp_path: Path, monkeypatch) -> None:
    pid = "PROJ-002-ok"
    proj = _bootstrap_project(tmp_path, pid, "- [x] T001 produce data/out.csv\n")
    # Pre-existing stale feedback that a success must clear.
    (proj / ".specify" / "memory" / "execution_feedback.md").write_text("old", encoding="utf-8")

    def _ok_run(project_dir, **kw):
        return AnalysisRunResult(
            ok=True,
            commands=[RunCommandResult("python code/a.py", True, 0, 1.0, False, "")],
            artifacts_produced=["data/out.csv"],
        )
    monkeypatch.setattr(analysis_runner, "run_analysis", _ok_run)
    monkeypatch.setattr("llmxive.execution.stage.run_analysis", _ok_run)

    assert execute_and_gate(proj, repo_root=tmp_path) is True
    assert execution_status.is_ok(pid, repo_root=tmp_path) is True
    assert not (proj / ".specify" / "memory" / "execution_feedback.md").exists()


def test_execute_and_gate_failure_reopens_tasks_and_writes_feedback(
    tmp_path: Path, monkeypatch
) -> None:
    pid = "PROJ-003-fail"
    tasks = (
        "- [x] T010 Implement regression in code/analysis/regression.py\n"
        "- [x] T011 Unrelated docs task in docs/notes.md\n"
    )
    proj = _bootstrap_project(tmp_path, pid, tasks)

    def _fail_run(project_dir, **kw):
        return AnalysisRunResult(
            ok=False,
            commands=[
                RunCommandResult("python code/analysis/regression.py", False, 1,
                                 0.5, False, "NameError: name 'sys' is not defined"),
            ],
            artifacts_produced=[],
            declared_missing=["data/processed/knots_cleaned.csv"],
            reason="1 command failed",
        )
    monkeypatch.setattr("llmxive.execution.stage.run_analysis", _fail_run)

    assert execute_and_gate(proj, repo_root=tmp_path) is False
    # status records the failure + bumps the fix counter
    assert execution_status.is_ok(pid, repo_root=tmp_path) is False
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    # feedback note written with the traceback + the missing deliverable
    fb = (proj / ".specify" / "memory" / "execution_feedback.md").read_text()
    assert "regression.py" in fb and "knots_cleaned.csv" in fb
    # the regression task is RE-OPENED ([x] -> [ ]); the unrelated docs task is not
    new_tasks = (proj / "specs" / "001-x" / "tasks.md").read_text()
    assert "- [ ] T010 Implement regression" in new_tasks
    assert "- [x] T011 Unrelated docs task" in new_tasks


def test_execute_and_gate_no_artifacts_is_failure(tmp_path: Path, monkeypatch) -> None:
    """A run-book that exits cleanly but writes NO real data/figure is still
    a failure — scaffolding that prints but produces nothing must not pass."""
    pid = "PROJ-004-empty"
    proj = _bootstrap_project(tmp_path, pid, "- [x] T001 do thing\n")

    def _empty_run(project_dir, **kw):
        return AnalysisRunResult(
            ok=False,  # run_analysis itself sets ok=False when produced is empty
            commands=[RunCommandResult("python code/a.py", True, 0, 1.0, False, "")],
            artifacts_produced=[],
            reason="run-book completed but produced no data/figure artifacts",
        )
    monkeypatch.setattr("llmxive.execution.stage.run_analysis", _empty_run)
    assert execute_and_gate(proj, repo_root=tmp_path) is False
    assert execution_status.is_ok(pid, repo_root=tmp_path) is False


# --- venv self-heal: declare missing third-party run-book imports -----------


def test_declare_missing_imports_adds_thirdparty_skips_stdlib_and_local(tmp_path: Path) -> None:
    """The execution stage re-declares third-party modules the run-book imports
    but the venv lacks (implementer dropped them from requirements.txt), while
    NOT touching the stdlib or the project's own code/ modules."""
    from llmxive.execution.stage import _declare_missing_imports

    proj = tmp_path / "projects" / "PROJ-Z"
    (proj / "code" / "reproducibility").mkdir(parents=True)
    (proj / "code" / "requirements.txt").write_text("database-knotinfo\n", encoding="utf-8")
    failures = [
        "python code/a.py\nModuleNotFoundError: No module named 'pandas'",
        "python code/b.py\nModuleNotFoundError: No module named 'numpy'",
        "python code/c.py\nModuleNotFoundError: No module named 'json'",            # stdlib → skip
        "python code/d.py\nModuleNotFoundError: No module named 'reproducibility'",  # local → skip
        "python code/e.py\nModuleNotFoundError: No module named 'pandas'",          # dupe
    ]
    added = _declare_missing_imports(proj, failures)
    assert added == ["numpy", "pandas"]
    reqs = (proj / "code" / "requirements.txt").read_text()
    assert "numpy" in reqs and "pandas" in reqs
    assert "json" not in reqs and "reproducibility" not in reqs
    # idempotent: a second pass adds nothing.
    assert _declare_missing_imports(proj, failures) == []


def test_data_artifact_ground_truth_surfaces_real_csv_headers(tmp_path) -> None:
    """The DATA-contract block must surface what the producer actually wrote (real
    CSV header) against what the failing consumer requires, so the auto-fix loop
    can reconcile a consumer's 'missing columns {model, rmse, mae}' against the
    producer's true columns (the PROJ-262 metrics-CSV oscillation: the failure
    shows only the consumer's expectation, never the producer's output)."""
    from llmxive.execution.data_contract import (
        find_data_contract_issues,
        render_data_contract_feedback,
    )

    proj = tmp_path / "PROJ-262-x"
    (proj / "code").mkdir(parents=True)
    (proj / "results").mkdir(parents=True)
    # Producer wrote DIFFERENT column names than a consumer expects.
    (proj / "results" / "metrics.csv").write_text(
        "seed,model_name,val_rmse,val_mae\n0,gnn,0.31,0.22\n", encoding="utf-8"
    )
    (proj / "code" / "make_metrics.py").write_text(
        "import csv\n"
        "with open('results/metrics.csv','w') as f:\n"
        "    w=csv.DictWriter(f,fieldnames=['seed','model_name','val_rmse','val_mae'])\n"
        "    w.writeheader()\n",
        encoding="utf-8",
    )
    (proj / "code" / "use_metrics.py").write_text(
        "import pandas as pd\n"
        "df=pd.read_csv('results/metrics.csv')\n",
        encoding="utf-8",
    )
    failures = [
        'File "/x/code/use_metrics.py", line 9, in load\n'
        "ValueError: Metrics CSV missing columns: {'rmse', 'mae', 'model'}"
    ]
    issues = find_data_contract_issues(proj, failures)
    fb = render_data_contract_feedback(issues)
    # The implementer now SEES the producer's real header to align against.
    assert "model_name" in fb and "val_rmse" in fb
    assert "metrics.csv" in fb
    assert "make_metrics.py" in fb  # the producer to edit
    assert "DATA CONTRACT" in fb
    # Empty failures → no issues, no block (best-effort, never crashes).
    assert render_data_contract_feedback(find_data_contract_issues(proj, [])) == ""


def test_execution_feedback_flags_regressions(tmp_path) -> None:
    """A command failing now that was NOT failing last round = the implementer's
    last fix broke working code (the PROJ-262 train_rf regression). The feedback
    must call it out prominently so the loop reverts the breakage instead of
    oscillating toward the fix-round cap."""
    from types import SimpleNamespace

    from llmxive.execution.stage import _FEEDBACK_FILENAME, _write_execution_feedback

    mem = tmp_path / ".specify" / "memory"
    res = SimpleNamespace(reason="2 command(s) failed", declared_missing=[], artifacts_produced=[])
    _write_execution_feedback(
        mem, res,
        failures=["python code/train_rf.py -> rc=1\n    Traceback ..."],
        contract_issues=None,
        regressions=["python code/train_rf.py"],
    )
    fb = (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")
    assert "REGRESSIONS" in fb
    assert "python code/train_rf.py" in fb
    assert "passed before" in fb
    # No regressions → no regression block.
    _write_execution_feedback(mem, res, failures=["x -> rc=1"], regressions=[])
    assert "REGRESSIONS" not in (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")


def test_compute_infra_failures_flagged_distinctly(tmp_path) -> None:
    """GPU/CUDA/8-bit/OOM failures are NOT implementer-fixable code bugs (the
    free CPU CI lacks the hardware); they must be flagged for a METHOD re-scope,
    not edited in place (PROJ-261 bitsandbytes / PROJ-262 GNN dead-ends)."""
    from types import SimpleNamespace

    from llmxive.execution.stage import (
        _FEEDBACK_FILENAME,
        _compute_infra_failures,
        _write_execution_feedback,
    )

    fails = [
        "python code/model_metrics.py -> rc=1\n  RuntimeError: bitsandbytes load_in_8bit requires CUDA",
        "python code/clean.py -> rc=1\n  ValueError: Metrics CSV missing columns",
    ]
    infra = _compute_infra_failures(fails)
    assert infra == ["python code/model_metrics.py"]  # only the GPU one

    mem = tmp_path / ".specify" / "memory"
    res = SimpleNamespace(reason="x", declared_missing=[], artifacts_produced=[])
    _write_execution_feedback(mem, res, failures=fails)
    fb = (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")
    assert "COMPUTE-ENVIRONMENT" in fb and "RE-SCOPE" in fb
    assert "load_in_8bit" in fb


def test_data_unavailable_failures_flagged_for_synthetic_rescope(tmp_path) -> None:
    """A renamed/unreachable HF dataset (HfUriError on a canonical name like
    openai_humaneval) is NOT a code bug the implementer can patch on the failing
    line — re-downloading never succeeds. It must be flagged to REPLACE the load
    with a synthetic sample (the brainstorm cohort whose generated code loads
    stale HF dataset ids; the PROJ-261 datasets dead-end)."""
    from types import SimpleNamespace

    from llmxive.execution.stage import (
        _FEEDBACK_FILENAME,
        _data_unavailable_failures,
        _write_execution_feedback,
    )

    fails = [
        "python code/data_loader.py -> rc=1\n  HfUriError: Invalid HF URI ... "
        "Repository id must be 'namespace/name', got 'openai_humaneval'",
        "python code/clean.py -> rc=1\n  KeyError: 'col'",  # a normal code bug
    ]
    data = _data_unavailable_failures(fails)
    assert data == ["python code/data_loader.py"]  # only the dataset one

    mem = tmp_path / ".specify" / "memory"
    res = SimpleNamespace(reason="x", declared_missing=[], artifacts_produced=[])
    _write_execution_feedback(mem, res, failures=fails)
    fb = (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")
    assert "DATA-UNAVAILABLE" in fb and "synthetic" in fb.lower()
    assert "openai_humaneval" in fb
