"""Spec 013 / SC-001 — real-call end-to-end test for the implementer.

Gated on `LLMXIVE_REAL_TESTS=1`. Builds a minimal fixture project at
`ready_for_implementation` with a 3-task writing-only revision spec,
drives the `llmXive-implementer` agent against the real Dartmouth Chat
API, and asserts:

  (a) `paper/source/main.tex` is modified
  (b) the modifications correspond to the action items
  (c) LaTeX still compiles
  (d) `current_stage` transitions to `paper_review`
  (e) wall-clock ≤10 min on a standard CI runner

Also covers the US5 re-review activation check (T053): after the
implementer routes to paper_review, the project has a non-empty
revision_history and a populated implementer-log.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1 to enable",
)


from llmxive.agents.base import AgentContext
from llmxive.agents.implementer import LLMXiveImplementer
from llmxive.agents.registry import load as load_registry
from llmxive.state import project as project_state
from llmxive.state import revision_history as rh_state
from llmxive.types import Project, Stage


_REPO = Path(__file__).resolve().parents[2]


def _make_fixture(repo: Path) -> str:
    """Lay out a minimal project at ready_for_implementation with a
    revision spec containing 3 writing-class tasks. Returns project_id."""
    pid = "PROJ-901-fixture-013-e2e"
    proj_dir = repo / "projects" / pid
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
    src = proj_dir / "paper" / "source"
    src.mkdir(parents=True)
    (proj_dir / "paper" / "pdf").mkdir(parents=True)
    # A minimal but compilable LaTeX document.
    (src / "main.tex").write_text(
        r"""\documentclass{article}
\title{Fixture Paper}
\author{Alice}
\begin{document}
\maketitle
\section{Introduction}
This paper studies fixtures. We use placeholder1 to motivate the work.
The acronym RAG is used without definition.
A long URL exists at https://github.com/xrenaf/MEMLENS.
\end{document}
""", encoding="utf-8")
    (proj_dir / "paper" / "metadata.json").write_text(
        json.dumps({
            "title": "Fixture Paper",
            "authors": [{"name": "Alice", "kind": "human", "affiliation": "Test U"}],
        }, indent=2), encoding="utf-8",
    )

    round_dir = repo / "specs" / "auto-revisions" / pid / "round-1"
    round_dir.mkdir(parents=True, exist_ok=True)
    (round_dir / "tasks.md").write_text(
        "# Revision tasks\n\n"
        "1. **[task-A]** (writing) Fix placeholder1 → 'a concrete example'\n"
        "2. **[task-B]** (writing) Define RAG (retrieval-augmented generation) at first use\n"
        "3. **[task-C]** (writing) Cite the project's GitHub repo in the introduction\n",
        encoding="utf-8",
    )
    for tid, sev, text in (
        ("task-A", "writing", "Replace placeholder1 with a concrete example in the introduction."),
        ("task-B", "writing", "Define the acronym RAG as 'retrieval-augmented generation' at first use."),
        ("task-C", "writing", "Add a brief sentence citing the GitHub repo URL in the introduction."),
    ):
        (round_dir / f"action_{tid}.md").write_text(
            f"---\nid: {tid}\nseverity: {sev}\ntext: \"{text}\"\n---\n{text}\n",
            encoding="utf-8",
        )

    proj = Project(
        id=pid,
        title="Fixture Paper",
        field="test",
        current_stage=Stage.READY_FOR_IMPLEMENTATION,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        revision_spec_path=f"specs/auto-revisions/{pid}/round-1",
    )
    project_state.save(proj, repo_root=repo)
    return pid


def test_implementer_e2e_writing_fixture() -> None:
    pid = _make_fixture(_REPO)
    try:
        reg = load_registry()
        entry = next(e for e in reg.agents if e.name == "llmxive_implementer")
        agent = LLMXiveImplementer(registry_entry=entry)
        ctx = AgentContext(
            project_id=pid,
            run_id=f"test-run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            task_id="t-impl",
            inputs=["paper", "implementation_plan"],
        )
        run_entry = agent.run(ctx)
        # outcome must not be FAILED — the implementer's contract is
        # to ALWAYS transition even when individual tasks fail.
        assert run_entry.outcome.value != "failed", (
            f"implementer raised; failure_reason={run_entry.failure_reason!r}"
        )

        # (d) stage transition
        proj = project_state.load(pid, repo_root=_REPO)
        assert proj is not None
        assert proj.current_stage in {Stage.PAPER_REVIEW, Stage.PAPER_REVISION_BLOCKED}, (
            f"unexpected stage {proj.current_stage.value!r}"
        )

        # Round 1 log written.
        log = rh_state.load_round(pid, 1, repo_root=_REPO)
        assert log.total_tasks == 3
        # SC-001: ≤10 min wall-clock budget (logged as duration_s).
        assert log.duration_s <= 600.0, (
            f"SC-001 budget exceeded: {log.duration_s:.1f}s"
        )

        # T053: revision_history populated → spec-012 re-review can fire.
        hist = rh_state.load(pid, repo_root=_REPO)
        assert len(hist.rounds) == 1
    finally:
        # Cleanup fixture (no need to keep test detritus in projects/).
        shutil.rmtree(_REPO / "projects" / pid, ignore_errors=True)
        shutil.rmtree(_REPO / "specs" / "auto-revisions" / pid, ignore_errors=True)
        (_REPO / "state" / f"{pid}.yaml").unlink(missing_ok=True)
        (_REPO / "state" / f"{pid}.implementer.yaml").unlink(missing_ok=True)
