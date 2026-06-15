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
