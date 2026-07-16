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


# A checked-in, STABLE quickstart fixture — a multi-step run-book with setup noise
# (cd / venv / pip / source) that must be filtered, a line-continuation to join, and
# a `python -c` smoke line. Decoupled from any live project file (issue #1139).
_QUICKSTART_FIXTURE = """# Quickstart
## Setup
```bash
cd code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Run the analysis
```bash
cd code
python download_data.py --out data/raw
python preprocess.py --in data/raw --out data/processed
python analyze.py \\
    --in data/processed --out results/metrics.json
python make_figures.py --in results/metrics.json --out figures/
python -c "import json; print(json.load(open('results/metrics.json')))"
```
"""


def test_extract_run_commands_filters_setup_keeps_python() -> None:
    """extract_run_commands keeps ONLY runnable `python` commands (joining
    line-continuations) and drops the venv/pip/cd/source setup lines. Exercised on
    a fixed fixture so the assertion never drifts with live project state."""
    cmds = extract_run_commands(_QUICKSTART_FIXTURE)
    assert cmds == [
        "python download_data.py --out data/raw",
        "python preprocess.py --in data/raw --out data/processed",
        "python analyze.py  --in data/processed --out results/metrics.json",
        "python make_figures.py --in results/metrics.json --out figures/",
        "python -c \"import json; print(json.load(open('results/metrics.json')))\"",
    ]
    assert not any("pip" in c or c.startswith("cd ") or "venv" in c for c in cmds)


def test_extract_run_commands_on_real_552_quickstart() -> None:
    """Regression: the live PROJ-552 quickstart yields RUNNABLE commands (the
    hollow-implementation finding — code existed, nothing ran it).

    The exact command COUNT is intentionally NOT asserted: the pipeline rewrites
    this quickstart as the project advances, so a hard-coded `>= 5` (plus a
    'download' step) from an older, longer version went red when the run-book
    legitimately got leaner (issue #1139 CI2). Only stable properties are checked.
    """
    repo = Path(__file__).resolve().parents[2]
    qs = repo / ("projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/"
                 "specs/010-quantifying-the-complexity-of-knot-diagr/quickstart.md")
    if not qs.is_file():
        return  # 552 spec dir may be renamed later; skip gracefully
    cmds = extract_run_commands(qs.read_text(encoding="utf-8"))
    assert cmds, "the real quickstart must yield >=1 runnable command (not zero)"
    assert all(c.startswith(("python ", "python3 ")) for c in cmds)
    assert any("main.py" in c for c in cmds)  # the analysis entrypoint is present


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


def test_overall_deadline_reads_analysis_deadline_env(tmp_path, monkeypatch) -> None:
    """run_analysis caps a single analysis at LLMXIVE_ANALYSIS_DEADLINE_S (SEPARATE
    from the run-loop wall budget) so a long execute_and_gate can NEVER overrun the
    CI job, while the wall budget can grow independently for more task throughput.
    With a tiny deadline it fires after the first command -> deadline_exceeded."""
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

    # The explicit analysis-deadline override fires.
    monkeypatch.setenv("LLMXIVE_ANALYSIS_DEADLINE_S", "0.01")
    res = ar.run_analysis(proj)  # overall_deadline_s=None -> resolves from env
    assert res.deadline_exceeded is True
    assert "deadline" in (res.reason or "").lower()

    # Falls back to the run-loop wall budget when the override is unset.
    monkeypatch.delenv("LLMXIVE_ANALYSIS_DEADLINE_S", raising=False)
    monkeypatch.setenv("LLMXIVE_RUN_WALL_BUDGET_S", "0.01")
    assert ar.run_analysis(proj).deadline_exceeded is True

    # Neither set → the sane 2700s default must NOT trip on a fast run.
    monkeypatch.delenv("LLMXIVE_RUN_WALL_BUDGET_S", raising=False)
    assert ar.run_analysis(proj).deadline_exceeded is False


def test_pythonpath_carries_both_project_dir_and_code_dir(tmp_path, monkeypatch) -> None:
    """Generated analysis code mixes two absolute-import styles within ONE project:
    bare `from data_loader import X` (needs code/ on the path) AND
    `from code.data_loader import X` (needs the PROJECT dir on the path, since
    code/ is a package). The runner MUST place BOTH on PYTHONPATH so neither style
    ModuleNotFoundErrors — otherwise the import randomly fails and the execution
    fix-loop can't converge (the PROJ-261 7-round thrash that never reached
    research_complete)."""
    import os
    import types

    from llmxive.execution import analysis_runner as ar

    proj = tmp_path / "projects" / "PROJ-901-pythonpath"
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / "code").mkdir()
    (proj / "code" / "main.py").write_text("x=1\n", encoding="utf-8")
    (proj / "specs" / "001-x" / "quickstart.md").write_text(
        "```bash\npython code/main.py\n```\n", encoding="utf-8")

    captured: dict = {}

    def _fake_run(project_dir, args, timeout_s, extra_env=None):
        captured["env"] = extra_env or {}
        return types.SimpleNamespace(
            ok=True, returncode=0, duration_s=0.01, timed_out=False, stdout="", stderr="",
        )

    monkeypatch.setattr(ar.sandbox, "run_in_venv", _fake_run)
    ar.run_analysis(proj)

    parts = captured["env"].get("PYTHONPATH", "").split(os.pathsep)
    assert str((proj / "code").resolve()) in parts, parts
    assert str(proj.resolve()) in parts, parts


def test_phantom_declared_deliverable_not_in_code_does_not_gate(tmp_path, monkeypatch) -> None:
    """A declared deliverable the code never references is a tasks-back-fill
    PHANTOM (endemic to reprocessed code papers: the back-fill invents deliverable
    filenames independently of the adapted code's real outputs). The code RUNS and
    writes real artifacts, so the gate must PASS despite the phantom — only
    deliverables the code actually writes are gated."""
    import types

    from llmxive.execution import analysis_runner as ar

    proj = tmp_path / "projects" / "PROJ-902-phantom"
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / "code").mkdir()
    (proj / "data").mkdir()
    # The code writes data/real.csv; it NEVER mentions data/phantom.csv.
    (proj / "code" / "run.py").write_text(
        "open('data/real.csv','w').write('a,b\\n1,2\\n')\n", encoding="utf-8")
    (proj / "specs" / "001-x" / "quickstart.md").write_text(
        "```bash\npython code/run.py\n```\n", encoding="utf-8")
    (proj / "specs" / "001-x" / "tasks.md").write_text(
        "# Tasks\n- [X] T001 produce data/phantom.csv\n", encoding="utf-8")

    def _fake_run(project_dir, args, timeout_s, extra_env=None):
        (project_dir / "data" / "real.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        return types.SimpleNamespace(
            ok=True, returncode=0, duration_s=0.01, timed_out=False, stdout="", stderr="")

    monkeypatch.setattr(ar.sandbox, "run_in_venv", _fake_run)
    res = ar.run_analysis(proj)
    assert res.ok is True, f"phantom deliverable must not gate; reason={res.reason!r}"
    assert "data/real.csv" in res.artifacts_produced


def test_code_referenced_declared_deliverable_still_gates_when_absent(tmp_path, monkeypatch) -> None:
    """A declared deliverable the code DOES reference but does NOT produce is a
    GENUINE gate failure (the code intended it but didn't write it) — the
    phantom-guard must not mask this."""
    import types

    from llmxive.execution import analysis_runner as ar

    proj = tmp_path / "projects" / "PROJ-903-realmiss"
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / "code").mkdir()
    (proj / "data").mkdir()
    # Code references data/wanted.csv (intends it) but writes data/other.csv instead.
    (proj / "code" / "run.py").write_text(
        "# intended output: data/wanted.csv\nopen('data/other.csv','w').write('x\\n')\n",
        encoding="utf-8")
    (proj / "specs" / "001-x" / "quickstart.md").write_text(
        "```bash\npython code/run.py\n```\n", encoding="utf-8")
    (proj / "specs" / "001-x" / "tasks.md").write_text(
        "# Tasks\n- [X] T001 produce data/wanted.csv\n", encoding="utf-8")

    def _fake_run(project_dir, args, timeout_s, extra_env=None):
        (project_dir / "data" / "other.csv").write_text("x\n", encoding="utf-8")
        return types.SimpleNamespace(
            ok=True, returncode=0, duration_s=0.01, timed_out=False, stdout="", stderr="")

    monkeypatch.setattr(ar.sandbox, "run_in_venv", _fake_run)
    res = ar.run_analysis(proj)
    assert res.ok is False
    assert "data/wanted.csv" in (res.reason or "")


def test_snapshot_artifacts_detects_code_output_and_results_dirs(tmp_path: Path) -> None:
    """The artifact detector must see real outputs written to results/ or
    code/output/ — not only data/ and figures/. PROJ-492 (a CPU-tractable
    crossing candidate) writes code/output/summary_report.csv; when only
    data/figures were scanned it was falsely gated 'produced no artifacts' and
    stalled at in_progress despite a real computed result."""
    from llmxive.execution.analysis_runner import _snapshot_artifacts

    proj = tmp_path / "projects" / "PROJ-492-x"
    (proj / "code" / "output").mkdir(parents=True)
    (proj / "results").mkdir(parents=True)
    (proj / "data").mkdir(parents=True)
    (proj / "figures").mkdir(parents=True)
    (proj / "code" / "output" / "summary_report.csv").write_text("a,b\n1,2\n")
    (proj / "results" / "metrics.json").write_text('{"r2": 0.78}')
    (proj / "data" / "clean.parquet").write_bytes(b"PARQ\x00data")
    # excluded: empty file + .gitkeep must NOT count as produced artifacts
    (proj / "code" / "output" / "empty.csv").write_text("")
    (proj / "figures" / ".gitkeep").write_text("")

    snap = _snapshot_artifacts(proj)
    assert "code/output/summary_report.csv" in snap
    assert "results/metrics.json" in snap
    assert "data/clean.parquet" in snap
    assert "code/output/empty.csv" not in snap        # empty -> excluded
    assert not any(k.endswith(".gitkeep") for k in snap)  # .gitkeep -> excluded
