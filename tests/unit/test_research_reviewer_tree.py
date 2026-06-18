"""Reviewer input fidelity: the code/data tree-listing the research panel sees.

Pins the PROJ-552 bug where `_summarize_tree`'s 25-file cap (and the failure to
exclude `.venv`/`__pycache__`) hid most of a project's authored source, so the
implementation_correctness reviewer falsely reported core files "missing" and
cast a blocking `minor_revision`. The listing must exclude virtualenvs/caches and
show the WHOLE authored tree.
"""

from __future__ import annotations

import json
from pathlib import Path

from llmxive.agents.research_reviewer import _execution_evidence, _summarize_tree


def _make_project(tmp_path: Path) -> Path:
    code = tmp_path / "code"
    # 40 authored analysis modules — comfortably past the old 25 cap.
    (code / "analysis").mkdir(parents=True)
    for i in range(40):
        (code / "analysis" / f"mod_{i:02d}.py").write_text("x = 1\n", encoding="utf-8")
    # Files in late-alphabet dirs that the old cap dropped entirely.
    for sub, fn in [("data", "parser.py"), ("download", "knot_atlas_loader.py"), ("filter", "f.py")]:
        (code / sub).mkdir(parents=True)
        (code / sub / fn).write_text("y = 2\n", encoding="utf-8")
    # Noise that must NEVER appear: a virtualenv + bytecode cache.
    (code / ".venv" / "lib" / "site-packages" / "numpy").mkdir(parents=True)
    for i in range(500):
        (code / ".venv" / "lib" / "site-packages" / "numpy" / f"f{i}.py").write_text("", encoding="utf-8")
    (code / "__pycache__").mkdir()
    (code / "__pycache__" / "mod_00.cpython-311.pyc").write_bytes(b"\x00")
    return tmp_path


def test_tree_excludes_venv_and_cache_and_shows_late_alphabet_dirs(tmp_path: Path) -> None:
    out = _summarize_tree(_make_project(tmp_path) / "code")
    assert ".venv" not in out and "site-packages" not in out
    assert "__pycache__" not in out and ".pyc" not in out
    # The files the old 25-cap dropped (and the reviewer called "missing"):
    assert "data/parser.py" in out
    assert "download/knot_atlas_loader.py" in out
    assert "filter/f.py" in out
    # All 40 analysis modules are visible (no premature truncation).
    assert out.count("analysis/mod_") == 40


def test_execution_evidence_reports_pass_and_artifacts(tmp_path: Path) -> None:
    repo = tmp_path
    es_dir = repo / "state" / "execution_status"
    es_dir.mkdir(parents=True)
    (es_dir / "PROJ-Z.json").write_text(
        json.dumps({"ok": True, "artifacts": ["data/processed/x.csv", "data/plots/y.png"]}),
        encoding="utf-8",
    )
    out = _execution_evidence("PROJ-Z", repo)
    assert "PASSED" in out and "ok=True" in out
    assert "data/processed/x.csv" in out and "data/plots/y.png" in out

    # No record → honest "not gated yet", never a crash.
    assert "not been gated" in _execution_evidence("PROJ-NONE", repo)
