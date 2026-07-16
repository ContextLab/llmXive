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
from llmxive.execution.stage import _reopen_failing_tasks


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
