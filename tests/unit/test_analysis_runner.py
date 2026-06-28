"""Unit tests for the analysis-execution run-book parser (spec 023 defect #25).

The execution stage runs ``quickstart.md``'s ordered ``python`` commands in
the project venv and gates ``research_complete`` on real artifacts. These
tests cover the PURE parsing/verification helpers (no subprocess); the
end-to-end venv run is exercised by the real-call suite + the live 552 run.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.execution.analysis_runner import (
    declared_deliverables,
    extract_run_commands,
)


def test_extract_run_commands_keeps_python_only_in_order() -> None:
    qs = (
        "# Quickstart\n\n"
        "## Setup\n```bash\npip install -r requirements.txt\nmkdir -p data/raw\n```\n"
        "## Run\n```bash\n# download\npython code/download/loader.py\n"
        "cd code\npython code/data/parser.py\necho done\n```\n"
        "## Verify\n```bash\npython -c \"import code.x\"\n```\n"
    )
    cmds = extract_run_commands(qs)
    assert cmds == [
        "python code/download/loader.py",
        "python code/data/parser.py",
        'python -c "import code.x"',
    ]


def test_extract_run_commands_joins_line_continuations() -> None:
    qs = "```bash\npython code/run.py \\\n  --flag value\n```\n"
    cmds = extract_run_commands(qs)
    # Joined to ONE command on one line (exact inner spacing is irrelevant —
    # shlex collapses it at run time).
    assert len(cmds) == 1
    assert cmds[0].startswith("python code/run.py")
    assert cmds[0].split() == ["python", "code/run.py", "--flag", "value"]


def test_extract_run_commands_skips_pip_and_venv_and_comments() -> None:
    qs = (
        "```bash\n"
        "pip install -r requirements.txt\n"
        "python -m venv .venv\n"
        "# python code/should_be_ignored.py\n"
        "python3 code/real.py\n"
        "```\n"
    )
    cmds = extract_run_commands(qs)
    assert cmds == ["python3 code/real.py"]


def test_extract_run_commands_empty_when_no_bash_blocks() -> None:
    assert extract_run_commands("# Just prose, no code blocks.") == []


def test_declared_deliverables_finds_data_and_figure_paths() -> None:
    tasks = (
        "- [ ] T018 Save raw data to data/raw/knot_atlas_raw.json and "
        "cleaned data to data/processed/knots_cleaned.csv\n"
        "- [ ] T024 Save plots to data/plots/crossing_vs_braid.png at 1200x900\n"
        "- [ ] T030 Write docs/reproducibility/notes.md\n"  # not a data/figure root
    )
    decl = declared_deliverables(tasks)
    assert "data/raw/knot_atlas_raw.json" in decl
    assert "data/processed/knots_cleaned.csv" in decl
    assert "data/plots/crossing_vs_braid.png" in decl
    # docs/ is neither a data/ nor figures/ rooted deliverable
    assert not any("notes.md" in d for d in decl)


def test_declared_deliverables_excludes_gitkeep() -> None:
    tasks = "- [ ] T001 create data/raw/.gitkeep and figures/.gitkeep\n"
    assert declared_deliverables(tasks) == set()


def test_extract_run_commands_on_real_552_quickstart() -> None:
    """Regression: the live PROJ-552 quickstart yields runnable commands
    (the hollow-implementation finding — code existed, nothing ran it)."""
    repo = Path(__file__).resolve().parents[2]
    qs = repo / ("projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/"
                 "specs/010-quantifying-the-complexity-of-knot-diagr/quickstart.md")
    if not qs.is_file():
        return  # 552 spec dir may be renamed later; skip gracefully
    cmds = extract_run_commands(qs.read_text(encoding="utf-8"))
    assert len(cmds) >= 5
    assert all(c.startswith(("python ", "python3 ")) for c in cmds)
    assert any("download" in c for c in cmds)  # the data-download step is present


def test_resolve_script_token_set(tmp_path) -> None:
    """Spec 023 #25: run-book paths drift from the implementer's file names
    (planner writes quickstart before code exists). Resolve by underscore-
    token set so renamed/moved scripts aren't false 'missing' failures."""
    from llmxive.execution.analysis_runner import _resolve_script
    code = tmp_path / "code"
    (code / "filter").mkdir(parents=True)
    (code / "reproducibility").mkdir(parents=True)
    (code / "filter" / "hyperbolic_filter.py").write_text("x")
    (code / "reproducibility" / "validation_status_generator.py").write_text("x")
    (code / "exact.py").write_text("x")
    # exact path
    assert _resolve_script(tmp_path, "code/exact.py") == "code/exact.py"
    # word-order swap (token-set EQUAL), different dir
    assert _resolve_script(tmp_path, "code/data/filter_hyperbolic.py") == \
        "code/filter/hyperbolic_filter.py"
    # subset (validation_status ⊆ validation_status_generator)
    assert _resolve_script(tmp_path, "code/x/validation_status.py") == \
        "code/reproducibility/validation_status_generator.py"
    # genuinely missing -> None (a real gap, not drift)
    assert _resolve_script(tmp_path, "code/analysis/correlation.py") is None


def test_overall_deadline_reads_wall_budget_env(tmp_path, monkeypatch) -> None:
    """run_analysis caps its overall deadline at LLMXIVE_RUN_WALL_BUDGET_S so a
    long execute_and_gate can NEVER overrun the CI job (the old 5h default let a
    single analysis blow past the 120-min job timeout -> the whole run was
    cancelled mid-step, losing all committed progress). With a tiny budget the
    deadline fires after the first command and the run reports deadline_exceeded."""
    import time
    import types

    from llmxive.execution import analysis_runner as ar

    proj = tmp_path / "projects" / "PROJ-900-deadline"
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / "code").mkdir()
    (proj / "code" / "a.py").write_text("x=1\n", encoding="utf-8")
    (proj / "code" / "b.py").write_text("x=2\n", encoding="utf-8")
    (proj / "specs" / "001-x" / "quickstart.md").write_text(
        "```bash\npython code/a.py\npython code/b.py\n```\n", encoding="utf-8")

    def _fake_run(project_dir, args, timeout_s, extra_env=None):
        time.sleep(0.05)  # advance real monotonic time past the tiny deadline
        return types.SimpleNamespace(
            ok=True, returncode=0, duration_s=0.05, timed_out=False,
            stdout="", stderr="",
        )
    monkeypatch.setattr(ar.sandbox, "run_in_venv", _fake_run)

    monkeypatch.setenv("LLMXIVE_RUN_WALL_BUDGET_S", "0.01")  # deadline from env
    res = ar.run_analysis(proj)  # overall_deadline_s=None -> resolves from env
    assert res.deadline_exceeded is True
    assert "deadline" in (res.reason or "").lower()

    # Control: no env + the sane default (2700s) must NOT trip on a fast run.
    monkeypatch.delenv("LLMXIVE_RUN_WALL_BUDGET_S", raising=False)
    res2 = ar.run_analysis(proj)
    assert res2.deadline_exceeded is False
