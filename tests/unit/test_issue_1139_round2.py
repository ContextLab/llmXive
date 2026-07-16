"""Issue #1139 — round-2 regression tests.

Round 1 (PR #1145) fixed ~20 structural defects but the pipeline still produced
ZERO organic `research_complete` crossings: every organic project stalls at the
`in_progress → research_complete` execution gate. A deep audit (this round) found
the execution gate never passes because the fix-loop cannot converge a small set
of concrete, code-fixable defects. These tests lock the round-2 fixes.

Each test names the defect id from the audit (B1/B2/B3/RC-C/F*) so the issue
comment can point at the exact lock.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.execution.analysis_runner import AnalysisRunResult, RunCommandResult
from llmxive.execution.stage import (
    _FEEDBACK_FILENAME,
    _reopen_failing_tasks,
    _runbook_cli_mismatches,
    _write_execution_feedback,
)


def _mk_project(tmp_path: Path, pid: str, tasks_md: str) -> Path:
    """A project dir with a single first-glob specs dir (no canonical pointer, so
    `_reopen_failing_tasks` falls through to the first-glob tasks.md)."""
    proj = tmp_path / "projects" / pid
    (proj / "specs" / "001-feature").mkdir(parents=True, exist_ok=True)
    (proj / "specs" / "001-feature" / "tasks.md").write_text(tasks_md, encoding="utf-8")
    (tmp_path / "state" / "execution_status").mkdir(parents=True, exist_ok=True)
    return proj


# ---------------------------------------------------------------------------
# B1 — reopen the module named in the traceback TAIL, not just the entrypoint
# ---------------------------------------------------------------------------


def test_b1_reopen_scans_traceback_tail_for_failing_module(tmp_path: Path) -> None:
    """The failing command is only ever the ENTRYPOINT (`python code/main.py`),
    but a transitive-import bug lives in a module named solely in the traceback
    tail (`code/analysis/aggregator.py` → `code/simulation/output_writer.py`).
    Before the fix, only the entrypoint task was reopened, the buggy-module task
    stayed `[X]`, and the implementer oscillated on main.py forever (live PROJ-341).
    The reopen must un-check the buggy-module tasks named in the tail."""
    pid = "PROJ-B1-import-chain"
    tasks_md = (
        "- [X] T001 Create the `code/main.py` entrypoint\n"
        "- [X] T002 Implement `code/analysis/aggregator.py`\n"
        "- [X] T003 Implement `code/simulation/output_writer.py`\n"
        "- [X] T004 Write `code/plots/figures.py` (unrelated, must stay done)\n"
    )
    proj = _mk_project(tmp_path, pid, tasks_md)

    tail = (
        "Traceback (most recent call last):\n"
        f'  File "{proj}/code/main.py", line 24, in <module>\n'
        "    from code.analysis.aggregator import main as aggregator_main\n"
        f'  File "{proj}/code/analysis/aggregator.py", line 13, in <module>\n'
        "    from code.simulation.output_writer import load_p_values_raw\n"
        f'  File "{proj}/code/simulation/output_writer.py", line 40, in <module>\n'
        "    log_operation(logger)('start')\n"
        "TypeError: 'LogEntry' object is not callable\n"
    )
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult("python code/main.py", False, 1, 0.5, False, tail),
        ],
    )

    reopened = _reopen_failing_tasks(proj, res)
    after = (proj / "specs" / "001-feature" / "tasks.md").read_text(encoding="utf-8")

    assert reopened >= 3
    assert "- [ ] T001" in after, "entrypoint task should reopen"
    assert "- [ ] T002" in after, "aggregator (named in tail) must reopen"
    assert "- [ ] T003" in after, "output_writer (the real bug, tail-only) must reopen"
    assert "- [X] T004" in after, "unrelated task must stay done"


def test_b1_tail_scan_ignores_venv_library_frames(tmp_path: Path) -> None:
    """A traceback that passes THROUGH an installed dependency under the per-project
    venv (`code/.venv/.../site-packages/pandas/...`) must NOT reopen anything for the
    library frame — only the project's own `code/` modules."""
    pid = "PROJ-B1-venv"
    tasks_md = (
        "- [X] T001 Create `code/main.py`\n"
        "- [X] T002 Implement `code/loaders/ingest.py`\n"
    )
    proj = _mk_project(tmp_path, pid, tasks_md)
    tail = (
        "Traceback (most recent call last):\n"
        f'  File "{proj}/code/main.py", line 3, in <module>\n'
        "    from code.loaders.ingest import load\n"
        f'  File "{proj}/code/loaders/ingest.py", line 2, in <module>\n'
        "    import pandas as pd\n"
        f'  File "{proj}/code/.venv/lib/python3.11/site-packages/pandas/compat/__init__.py", line 27\n'
        "    from pandas.compat.numpy import is_numpy_dev\n"
        "ImportError: cannot import name 'is_numpy_dev'\n"
    )
    res = AnalysisRunResult(
        ok=False,
        commands=[RunCommandResult("python code/main.py", False, 1, 0.5, False, tail)],
    )
    reopened = _reopen_failing_tasks(proj, res)
    after = (proj / "specs" / "001-feature" / "tasks.md").read_text(encoding="utf-8")
    assert "- [ ] T001" in after
    assert "- [ ] T002" in after, "the project's own ingest.py (in the tail) reopens"
    # The pandas library frame did not add a spurious task or crash.
    assert "pandas" not in after
    assert reopened >= 2


# ---------------------------------------------------------------------------
# B2 — run-book / CLI (argparse) mismatch is diagnosed for the implementer
# ---------------------------------------------------------------------------

_ARGPARSE_TAIL_REQUIRED = (
    "usage: extract_metrics.py [-h] --input INPUT --output OUTPUT\n"
    "                          [--extension EXTENSION]\n"
    "extract_metrics.py: error: the following arguments are required: --input, --output\n"
)
_ARGPARSE_TAIL_UNRECOGNIZED = (
    "usage: simulation_runner.py [-h] [--iterations ITERATIONS]\n"
    "simulation_runner.py: error: unrecognized arguments: --icc 0.1 --alpha 0.05\n"
)


def test_b2_detects_argparse_runbook_mismatch() -> None:
    """A quickstart command whose argparse rejects the args ('the following
    arguments are required' / 'unrecognized arguments') is a run-book/CLI drift —
    re-running never succeeds and editing the script body won't help. The detector
    surfaces (command, usage, error) for each (live PROJ-148/239/585)."""
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/extract_metrics.py", False, 2, 0.1, False,
                _ARGPARSE_TAIL_REQUIRED,
            ),
            RunCommandResult(
                "python code/simulation_runner.py --icc 0.1 --alpha 0.05",
                False, 2, 0.1, False, _ARGPARSE_TAIL_UNRECOGNIZED,
            ),
            RunCommandResult(  # an ordinary crash — NOT a CLI mismatch
                "python code/train.py", False, 1, 0.1, False,
                "Traceback ...\nValueError: shapes not aligned\n",
            ),
        ],
    )
    mm = _runbook_cli_mismatches(res)
    cmds = {c for c, _u, _e in mm}
    assert cmds == {
        "python code/extract_metrics.py",
        "python code/simulation_runner.py --icc 0.1 --alpha 0.05",
    }, "only the two argparse-mismatch commands (not the ValueError crash)"
    # usage + error are carried through
    by_cmd = {c: (u, e) for c, u, e in mm}
    assert "--input INPUT --output OUTPUT" in by_cmd["python code/extract_metrics.py"][0]
    assert "required" in by_cmd["python code/extract_metrics.py"][1]
    assert "unrecognized arguments" in by_cmd[
        "python code/simulation_runner.py --icc 0.1 --alpha 0.05"][1]


def test_b2_feedback_names_the_cli_mismatch(tmp_path: Path) -> None:
    """The execution feedback the implementer reads must call out the run-book/CLI
    mismatch explicitly (command + the script's real usage + the argparse error),
    so the implementer reconciles the quickstart and the script's argparse instead
    of pointlessly editing the script body."""
    mem = tmp_path / ".specify" / "memory"
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/extract_metrics.py", False, 2, 0.1, False,
                _ARGPARSE_TAIL_REQUIRED,
            ),
        ],
    )
    failures = ["python code/extract_metrics.py -> rc=2\n    " + _ARGPARSE_TAIL_REQUIRED]
    _write_execution_feedback(mem, res, failures)
    fb = (mem / _FEEDBACK_FILENAME).read_text(encoding="utf-8")
    assert "RUN-BOOK" in fb and "CLI" in fb
    assert "extract_metrics.py" in fb
    assert "--input INPUT --output OUTPUT" in fb  # the real usage is shown
    assert "the following arguments are required" in fb  # the argparse error is shown


# ---------------------------------------------------------------------------
# B3 — script-missing self-heal appends a SELF-OWNING reconciliation task
# ---------------------------------------------------------------------------


def test_b3_script_missing_selfheal_is_self_owning(tmp_path: Path) -> None:
    """A run-book command naming a script NO task created (script_missing) must get
    a reconciliation task that (a) names the EXACT run-book path and (b) is
    self-owning — a second identical failure round must NOT append a duplicate (the
    PROJ-552 stall was the loop never converging). Guards convergence within a
    spec cycle."""
    pid = "PROJ-B3-scriptmissing"
    tasks_md = (
        "- [X] T001 Build `code/main.py`\n"
        "- [X] T002 Produce `data/results.json`\n"
    )
    proj = _mk_project(tmp_path, pid, tasks_md)
    missing = "code/reproducibility/checksum_generator.py"
    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                f"python {missing}", False, 2, 0.1, False,
                "[script missing]", script_missing=True,
            ),
        ],
    )

    first = _reopen_failing_tasks(proj, res)
    after1 = (proj / "specs" / "001-feature" / "tasks.md").read_text(encoding="utf-8")
    assert first >= 1
    assert "Reconcile run-book" in after1
    assert missing in after1, "the reconciliation task must name the exact run-book path"

    # Second identical round: the appended task now OWNS the path → no duplicate.
    second = _reopen_failing_tasks(proj, res)
    after2 = (proj / "specs" / "001-feature" / "tasks.md").read_text(encoding="utf-8")
    assert after2.count("Reconcile run-book vs implementation for `%s`" % missing) == 1, (
        "self-heal must not append a duplicate reconciliation task each round"
    )
    assert second == 0, "a converged self-heal reopens nothing new on the next round"
