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


def test_data_unavailable_failures_flagged_for_real_source_not_synthetic(tmp_path) -> None:
    """A renamed/unreachable HF dataset (HfUriError on a canonical name like
    openai_humaneval) is NOT a code bug the implementer can patch on the failing
    line — re-downloading never succeeds. It must be flagged to switch to a REAL,
    REACHABLE source (corrected id / mirror / small real sample), and EXPLICITLY
    NOT to substitute synthetic data — substituting synthetic is rejected by the
    fabrication gate, so the old 'replace with a synthetic sample' guidance made the
    fix-loop thrash forever (implementer fabricates -> gate rejects -> repeat)."""
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
    assert "DATA-UNAVAILABLE" in fb and "openai_humaneval" in fb
    # New policy: steer to a REAL source and explicitly forbid synthetic substitution.
    assert "REAL" in fb
    assert "do not substitute synthetic" in fb.lower() or "not substitute synthetic" in fb.lower()


def test_fabrication_feedback_steers_gpu_work_to_kaggle_offload(tmp_path) -> None:
    """When the analysis fabricated because the metric needs a GPU, the fix-loop
    feedback must tell the implementer to KEEP the GPU code (so it offloads to
    Kaggle's free GPU and runs the REAL experiment), NOT to fabricate or add a
    silent CPU fallback. (The Kaggle GPUs exist; force-crippling onto CPU is what
    made every external GPU paper fabricate.)"""
    from types import SimpleNamespace

    from llmxive.execution.stage import _FEEDBACK_FILENAME, _write_execution_feedback

    mem = tmp_path / ".specify" / "memory"
    res = SimpleNamespace(
        reason="fabricated", declared_missing=[], artifacts_produced=[],
        fabrication=["code/run.py: self-declared fabricated metric — 'simulate the speedup'"],
    )
    _write_execution_feedback(mem, res, failures=[])
    fb = (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")
    assert "Kaggle" in fb and 'device="cuda"' in fb
    assert "do NOT add a silent CPU fallback" in fb.lower() or "silent CPU fallback" in fb


def test_needs_verified_source_fires_on_fabrication_hollow_and_data_unavailable() -> None:
    """The verified-real-data-source discovery bridge must trigger on the failure
    modes a project falls into BECAUSE it has no real source — fabricated input
    data, hollow (null/empty) results, or a data-unavailable command failure —
    not only on a MISSING data/ deliverable. A fabricating project's fake files
    EXIST on disk (declared_missing empty, artifacts produced), so the old
    missing-deliverable-only check never fired and the project was told 'don't
    fake it' without ever being handed a real source (it then churned forever)."""
    from types import SimpleNamespace

    from llmxive.execution.stage import _needs_verified_source

    def res(**kw):
        base = dict(reason="x", declared_missing=[], artifacts_produced=["figures/f.png"],
                    fabrication=[], hollow=[])
        base.update(kw)
        return SimpleNamespace(**base)

    # Fabricated INPUT data — the largest data-blocked class.
    assert _needs_verified_source(
        res(fabrication=["code/data/download.py: synthetic/fake INPUT data"]), [])
    # Hollow results (a stand-in / empty dataset was loaded).
    assert _needs_verified_source(
        res(hollow=["data/processed/metrics.json: results file is empty"]), [])
    # Data-unavailable command failure (renamed/gated HF dataset).
    assert _needs_verified_source(res(), [
        "python code/data_loader.py -> rc=1\n  HfUriError: Repository id must be "
        "'namespace/name', got 'openai_humaneval'"])
    # Missing data/ deliverable (the original trigger — still fires).
    assert _needs_verified_source(res(declared_missing=["data/processed/x.csv"]), [])
    # Negative control: an ordinary code bug with real artifacts produced and no
    # fabrication/hollow/data signal must NOT trigger discovery (no over-firing).
    assert not _needs_verified_source(res(), ["python code/plot.py -> rc=1\n  KeyError: 'col'"])


def test_fabrication_triggers_real_data_source_discovery(tmp_path, monkeypatch) -> None:
    """End-to-end: a FABRICATION failure now injects the VERIFIED REAL DATA SOURCE
    block into execution_feedback.md (Fix B). Previously the discovery bridge was
    gated on a missing data/ deliverable, so fabricating projects — whose fake
    data files exist — never received a real source and could only keep
    fabricating. We patch discovery to return a verified record and assert the
    real (unpatched) renderer's block lands in the feedback."""
    from types import SimpleNamespace

    import llmxive.execution.data_source as data_source
    from llmxive.execution.stage import _FEEDBACK_FILENAME, _write_execution_feedback

    monkeypatch.setattr(data_source, "ensure_discovered_source", lambda project_dir: {
        "status": "verified", "kind": "pypi_package", "ref": "ucimlrepo",
        "record_count": 4898, "sample_fields": ["fixed_acidity", "quality"],
        "access_python": "from ucimlrepo import fetch_ucirepo\nd = fetch_ucirepo(id=186)",
    })

    mem = tmp_path / "projects" / "PROJ-999-x" / ".specify" / "memory"
    mem.mkdir(parents=True)
    res = SimpleNamespace(
        reason="fabricated", declared_missing=[], artifacts_produced=["data/fake.csv"],
        fabrication=["code/data/ingestion.py: synthetic/fake INPUT data not measured"],
        hollow=[],
    )
    _write_execution_feedback(mem, res, failures=[])
    fb = (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")
    assert "VERIFIED REAL DATA SOURCE" in fb
    assert "ucimlrepo" in fb and "fetch_ucirepo" in fb


def test_pipeline_workflow_passes_kaggle_secret_to_execution_lane() -> None:
    """The execution gate (which dispatches the GPU offload) runs in the
    llmxive-pipeline.yml `Run pipeline` step. That step MUST pass KAGGLE_API_TOKEN
    or `offload.is_available()` is False and GPU papers fall back to a doomed CPU
    run that fabricates. advance.yml already passes it; the main lane must too."""

    from llmxive.config import repo_root
    wf = (repo_root() / ".github" / "workflows" / "llmxive-pipeline.yml").read_text(encoding="utf-8")
    assert "KAGGLE_API_TOKEN" in wf, "the pipeline lane must pass the Kaggle secret"


def test_reopen_appends_reconciliation_task_for_missing_runbook_script(
    tmp_path: Path,
) -> None:
    """A run-book command that invokes a script NO task created (a plan/impl name
    mismatch) must not silently re-open 0 tasks — the auto-fix loop would never
    engage and the project would stall at in_progress forever. This is the live
    PROJ-552 stall: the quickstart calls ``checksum_generator.py`` but the
    implementer built ``checksums.py``, so re-open matched no task. Assert a
    reconciliation task is appended (so the implementer runs) and that it is
    idempotent (no runaway duplicate appends)."""
    from llmxive.execution.stage import _reopen_failing_tasks

    tasks_md = (
        "# Tasks\n"
        "- [X] T044 [US4] Generate SHA-256 checksums in "
        "`code/reproducibility/checksums.py`.\n"
        "- [X] T045 [US4] Record checksums in `data/checksums.sha256`.\n"
    )
    proj = _bootstrap_project(tmp_path, "PROJ-552-x", tasks_md)
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/reproducibility/checksum_generator.py",
                False, -1, 0.0, False, "FileNotFoundError", script_missing=True,
            ),
        ],
        reason="1 run-book script(s) missing (plan/impl path mismatch)",
    )
    n = _reopen_failing_tasks(proj, res)
    assert n >= 1, "a missing run-book script with no owning task must engage the loop"
    updated = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert "checksum_generator.py" in updated
    assert "- [ ] " in updated and "Reconcile run-book" in updated
    assert "- [X] T044" in updated  # pre-existing real task untouched

    # Idempotent: a second identical failure must NOT double-append — the appended
    # task now OWNS the name, so no runaway growth of tasks.md across fix rounds.
    _reopen_failing_tasks(proj, res)
    after = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert after.count("Reconcile run-book") == 1


def test_reopen_still_reopens_owned_missing_script_normally(tmp_path: Path) -> None:
    """When the missing run-book script IS owned by a checked task, the normal
    re-open path handles it (no reconciliation task needed) — the self-heal must
    not fire spuriously."""
    from llmxive.execution.stage import _reopen_failing_tasks

    tasks_md = (
        "# Tasks\n"
        "- [X] T010 Build `code/reproducibility/checksum_generator.py`.\n"
    )
    proj = _bootstrap_project(tmp_path, "PROJ-777-x", tasks_md)
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/reproducibility/checksum_generator.py",
                False, -1, 0.0, False, "FileNotFoundError", script_missing=True,
            ),
        ],
    )
    n = _reopen_failing_tasks(proj, res)
    updated = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert n == 1
    assert "- [ ] T010" in updated  # the owning task was re-opened
    assert "Reconcile run-book" not in updated  # no spurious self-heal task


def test_reopen_reconciles_same_name_different_directory(tmp_path: Path) -> None:
    """The live PROJ-179 stall. The run-book calls ``code/download.py`` but the task
    built ``data/download.py`` — the SAME basename in a DIFFERENT directory. Judging
    ownership by basename declared the script "owned", so no reconciliation task was
    appended; the loop just re-opened the data/ task, the implementer rebuilt
    data/download.py, the run-book still called code/download.py, and the project
    stalled at in_progress forever. Ownership is the FULL path: re-open the
    same-named task (the likely culprit) AND append the reconciliation task that
    actually names the mismatch."""
    from llmxive.execution.stage import _reopen_failing_tasks

    tasks_md = (
        "# Tasks\n"
        "- [X] T005 Implement `data/download.py` to fetch the behavioral dataset.\n"
    )
    proj = _bootstrap_project(tmp_path, "PROJ-179-x", tasks_md)
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/download.py",
                False, -1, 0.0, False, "FileNotFoundError", script_missing=True,
            ),
        ],
    )
    n = _reopen_failing_tasks(proj, res)
    updated = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert n >= 1
    assert "Reconcile run-book" in updated, "the path mismatch was never surfaced"
    assert "code/download.py" in updated


def test_reopen_does_not_match_a_bare_prose_word(tmp_path: Path) -> None:
    """A missing ``code/analysis.py`` must NOT re-open every task whose prose merely
    contains the word "analysis". The bare STEM was in the re-open targets, so an
    unrelated task (`src/analysis/correlation.py`) was re-opened and redone every
    round — churn that never fixed the actual missing script."""
    from llmxive.execution.stage import _reopen_failing_tasks

    tasks_md = (
        "# Tasks\n"
        "- [X] T014 Implement `src/analysis/correlation.py` for the association.\n"
    )
    proj = _bootstrap_project(tmp_path, "PROJ-179-b", tasks_md)
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/analysis.py",
                False, -1, 0.0, False, "FileNotFoundError", script_missing=True,
            ),
        ],
    )
    _reopen_failing_tasks(proj, res)
    updated = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert "- [X] T014" in updated, "unrelated task re-opened on a bare prose word"
    assert "Reconcile run-book" in updated  # the real mismatch IS surfaced


def test_fabrication_reopens_the_owning_task(tmp_path: Path) -> None:
    """Fabrication (and hollow results) occur when every command EXITS 0 — so the
    re-open loop, which builds its targets from FAILING COMMANDS, reopened nothing,
    the implementer was never dispatched, and the fabrication could never be fixed.
    The project just burned the whole model ladder and re-planned. ~44% of execution
    failures are fabrication, so this was the single biggest sink of worker time."""
    from llmxive.execution.stage import _reopen_failing_tasks

    tasks_md = (
        "# Tasks\n"
        "- [X] T010 Generate the input corpus in `code/data/synthetic.py`.\n"
        "- [X] T011 Write the paper intro.\n"
    )
    proj = _bootstrap_project(tmp_path, "PROJ-586-x", tasks_md)
    res = AnalysisRunResult(
        ok=False,
        commands=[RunCommandResult("python code/run.py", True, 0, 1.0, False, "")],
        fabrication=["code/data/synthetic.py: synthetic/fake INPUT data not authorized"],
        reason="1 fabricated/simulated-result signal(s)",
    )
    n = _reopen_failing_tasks(proj, res)
    updated = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert n >= 1, "fabrication re-opened NO task — the implementer never runs"
    assert "- [ ] T010" in updated, "the task owning the fabricated file was not re-opened"
    assert "- [X] T011" in updated, "an unrelated task was re-opened"


def test_hollow_results_reopen_the_owning_task(tmp_path: Path) -> None:
    """Same shape: the analysis ran clean but computed nothing."""
    from llmxive.execution.stage import _reopen_failing_tasks

    tasks_md = (
        "# Tasks\n"
        "- [X] T020 Compute the correlation into `data/results/primary_analysis.json`.\n"
        "- [X] T021 Write the discussion.\n"
    )
    proj = _bootstrap_project(tmp_path, "PROJ-179-x", tasks_md)
    res = AnalysisRunResult(
        ok=False,
        commands=[RunCommandResult("python code/run.py", True, 0, 1.0, False, "")],
        hollow=["data/results/primary_analysis.json: EVERY metric is null/NaN"],
        reason="1 hollow-result signal(s)",
    )
    n = _reopen_failing_tasks(proj, res)
    updated = (proj / "specs" / "001-x" / "tasks.md").read_text(encoding="utf-8")
    assert n >= 1, "hollow results re-opened NO task — the implementer never runs"
    assert "- [ ] T020" in updated
    assert "- [X] T021" in updated
