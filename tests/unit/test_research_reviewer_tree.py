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


def test_doc_contents_surfaces_file_bodies_for_verification(tmp_path: Path) -> None:
    """Reviewers must SEE doc content (not just listings) to verify fixes —
    pins the data_quality holdout ('license present but content not shown')."""
    from llmxive.agents.research_reviewer import _doc_contents

    proj = tmp_path
    rdir = proj / "docs" / "reproducibility"
    rdir.mkdir(parents=True)
    (rdir / "data_license.md").write_text("Knot Atlas: CC-BY-4.0; KnotInfo: public.", encoding="utf-8")
    (proj / "README.md").write_text("# Knot Complexity\nReproduce via quickstart.", encoding="utf-8")
    out = _doc_contents(proj)
    assert "CC-BY-4.0" in out               # license CONTENT, not just the name
    assert "data_license.md" in out
    assert "Reproduce via quickstart" in out  # top-level README content


def test_doc_contents_prioritizes_referenced_and_small_over_redundant_bulk(
    tmp_path: Path,
) -> None:
    """A project can accumulate 100+ reproducibility docs that blow any prompt
    budget. The concise, spec-mandated artifacts (and a doc they point to) must
    still be shown IN FULL; only long redundant narratives get omitted. Pins the
    PROJ-552 input-coverage bug where alphabetical truncation hid validation_scope
    / sample_size / dataset_counts so data_quality falsely inferred 'not shown'."""
    from llmxive.agents.research_reviewer import _doc_contents

    rdir = tmp_path / "docs" / "reproducibility"
    rdir.mkdir(parents=True)
    # 60 redundant verbose narratives (large) — the proliferation that buries docs.
    for i in range(60):
        (rdir / f"narrative_addendum_{i:02d}.md").write_text("padding. " * 600, "utf-8")
    # The concise spec-mandated artifact, and the sibling it points to for detail.
    (rdir / "validation_scope.md").write_text(
        "Counts per crossing number are in dataset_counts.md.\nCOUNTS_POINTER\n", "utf-8"
    )
    (rdir / "dataset_counts.md").write_text("Crossing 10: 1234 knots.\nCOUNTS_TABLE\n", "utf-8")

    # spec/tasks reference validation_scope.md by name -> one-hop pulls in
    # dataset_counts.md even though spec/tasks never name it directly.
    out = _doc_contents(
        tmp_path, prioritize_text="see docs/reproducibility/validation_scope.md", max_total=12000
    )
    assert "COUNTS_POINTER" in out   # directly spec-referenced doc shown in full
    assert "COUNTS_TABLE" in out     # its one-hop sibling prioritized & shown
    assert "additional" in out and "omitted" in out  # bulk narratives dropped, flagged


def test_advisory_comments_surfaced_as_context_not_gating(tmp_path: Path, monkeypatch) -> None:
    """Human + simulated-personality reviews must reach the gating reviewer as
    ADVISORY context (review -> consider comments -> revise), separate from the
    gating panel — they inform the review without being a panel verdict. Pins
    the user-requested handling: advisory comments influence the evaluation,
    they are not discarded (fix #2) nor are they a gating vote."""
    import shutil
    import yaml
    from llmxive.agents.research_reviewer import ResearchReviewerAgent
    from llmxive.agents.base import AgentContext
    from llmxive.config import repo_root as _rr

    # Self-contained repo: copy the real prompt tree so render_prompt resolves
    # under tmp_path (build_messages uses ONE repo root for project + prompts).
    shutil.copytree(_rr() / "agents", tmp_path / "agents")

    proj = "PROJ-902-advisory"
    base = tmp_path / "projects" / proj
    (base / "specs" / "001-x").mkdir(parents=True)
    (base / "specs" / "001-x" / "spec.md").write_text("# Spec\nq", encoding="utf-8")
    (base / "specs" / "001-x" / "tasks.md").write_text("- [x] T001 do it", encoding="utf-8")
    (base / "code").mkdir(); (base / "data").mkdir(); (base / "docs").mkdir()
    rdir = base / "reviews" / "research"
    rdir.mkdir(parents=True)
    rec = {
        "reviewer_name": "marie-curie-simulated", "reviewer_kind": "human",
        "artifact_path": f"projects/{proj}/specs/001-x/tasks.md", "artifact_hash": "a" * 64,
        "score": 0.0, "verdict": "minor_revision", "reviewed_at": "2026-06-19T00:00:00Z",
        "prompt_version": "1.0.0", "model_name": "m", "backend": "dartmouth",
    }
    (rdir / "marie-curie-simulated__2026-06-19__research.md").write_text(
        "---\n" + yaml.safe_dump(rec) + "---\n\nEstablish the PRECISION of braid-index measurements.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "llmxive.agents.research_reviewer._repo_root", lambda: tmp_path
    )
    from dataclasses import dataclass

    @dataclass
    class _E:
        name: str = "research_reviewer_data_quality_research"
        prompt_path: str = "agents/prompts/research_reviewer_data_quality_research.md"
        prompt_version: str = "1.0.0"

    agent = object.__new__(ResearchReviewerAgent)
    agent.entry = _E()
    user = agent.build_messages(
        AgentContext(project_id=proj, run_id="x", task_id="x", inputs=[])
    )[-1].content
    assert "# advisory comments" in user
    assert "PRECISION of braid-index" in user        # surfaced to the reviewer
    assert "CONSIDER the advisory" in user            # review -> consider -> revise
    # advisory must NOT be presented as a gating-panel verdict
    panel = user.split("# advisory comments")[0]
    assert "marie-curie" not in panel
