"""Paper-agent feature-dir pointer resolution (issue #1139, defect D2).

THE BUG: ``PaperWritingAgent`` and ``PaperFigureGenerationAgent`` resolved the
paper-stage spec/plan by globbing ``paper/specs/*/spec.md`` (or ``plan.md``) and
picking the FIRST (alphabetically-oldest) match. On a project that cycled
through convergence kickbacks the paper feature dirs accumulate
(``001-old``, ``010-current``); first-glob then resolves the STALE prior cycle
while the pipeline's authoritative ``speckit_paper_dir`` pointer references the
current one — so the writer/figure agents composed against a superseded
spec/plan (spec 023 defect #17).

These tests build a REAL tmp project tree with TWO paper feature dirs and a REAL
saved Project whose pointer references the CURRENT (010-current) dir, then call
the agents' real ``build_messages`` and assert the CURRENT spec/plan text is
injected — never the stale 001-old text.

The fallback in ``feature_dir_for`` picks the FIRST candidate (001-old here), so
selecting 010-current can only happen via the pointer — this is a strict
pointer-first assertion, not merely "pick the latest".
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents.base import AgentContext
from llmxive.agents.paper_figure_generation import PaperFigureGenerationAgent
from llmxive.agents.paper_writing import PaperWritingAgent
from llmxive.config import repo_root as _repo_root
from llmxive.state import project as project_store
from llmxive.types import AgentRegistryEntry, Project, Stage

# The real repo root, captured before any per-test LLMXIVE_REPO_ROOT override,
# so we can copy the genuine prompt templates into the hermetic tmp repo.
_REAL_REPO = _repo_root()

PROJECT_ID = "PROJ-900-paperptr"
OLD_SPEC_MARK = "STALE-OLD-SPEC-001-do-not-use"
OLD_PLAN_MARK = "STALE-OLD-PLAN-001-do-not-use"
CUR_SPEC_MARK = "CURRENT-SPEC-010-pointer-target"
CUR_PLAN_MARK = "CURRENT-PLAN-010-pointer-target"


def _build_repo(tmp_path: Path) -> Path:
    """Create a hermetic repo with two paper feature dirs + a pointer → 010."""
    repo = tmp_path
    # Real prompt templates (build_messages renders them via repo_root).
    (repo / "agents" / "prompts").mkdir(parents=True)
    for name in ("paper_writing.md", "paper_figure_generation.md"):
        shutil.copyfile(
            _REAL_REPO / "agents" / "prompts" / name,
            repo / "agents" / "prompts" / name,
        )

    paper_specs = repo / "projects" / PROJECT_ID / "paper" / "specs"
    old = paper_specs / "001-old"
    current = paper_specs / "010-current"
    old.mkdir(parents=True)
    current.mkdir(parents=True)
    (old / "spec.md").write_text(f"# {OLD_SPEC_MARK}\n", encoding="utf-8")
    (old / "plan.md").write_text(f"# {OLD_PLAN_MARK}\n", encoding="utf-8")
    (current / "spec.md").write_text(f"# {CUR_SPEC_MARK}\n", encoding="utf-8")
    (current / "plan.md").write_text(f"# {CUR_PLAN_MARK}\n", encoding="utf-8")

    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    project = Project(
        id=PROJECT_ID,
        title="Pointer resolution demo",
        field="testing",
        current_stage=Stage.PAPER_IN_PROGRESS,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_paper_dir=f"projects/{PROJECT_ID}/paper/specs/010-current",
    )
    project_store.save(project, repo_root=repo)
    return repo


def _entry(name: str, prompt_path: str) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        name=name,
        purpose="paper feature-dir pointer resolution test",
        prompt_path=prompt_path,
        prompt_version="1.0.0",
        default_backend="dartmouth",
        fallback_backends=[],
        default_model="openai.gpt-oss-120b",
        wall_clock_budget_seconds=60,
        paid_opt_in=False,
    )


def _user_message(messages: list) -> str:
    return next(m.content for m in messages if m.role == "user")


def test_paper_writing_uses_pointer_spec_and_plan(tmp_path: Path, monkeypatch) -> None:
    repo = _build_repo(tmp_path)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))

    ctx = AgentContext(
        project_id=PROJECT_ID,
        run_id="r",
        task_id="T001",
        inputs=[],
        metadata={"target_section": "introduction", "target_path": ""},
    )
    agent = PaperWritingAgent(_entry("paper_writer", "agents/prompts/paper_writing.md"))
    user = _user_message(agent.build_messages(ctx))

    assert CUR_SPEC_MARK in user, "writer must use the pointer (010-current) spec.md"
    assert CUR_PLAN_MARK in user, "writer must use the pointer (010-current) plan.md"
    assert OLD_SPEC_MARK not in user, "writer must NOT use the stale (001-old) spec.md"
    assert OLD_PLAN_MARK not in user, "writer must NOT use the stale (001-old) plan.md"


def test_paper_figure_generation_uses_pointer_plan(tmp_path: Path, monkeypatch) -> None:
    repo = _build_repo(tmp_path)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))

    ctx = AgentContext(
        project_id=PROJECT_ID,
        run_id="r",
        task_id="T002",
        inputs=[],
        metadata={"figure_id": "fig1", "target_path": "", "data_source_path": ""},
    )
    agent = PaperFigureGenerationAgent(
        _entry("paper_figure", "agents/prompts/paper_figure_generation.md")
    )
    user = _user_message(agent.build_messages(ctx))

    assert CUR_PLAN_MARK in user, "figure agent must use the pointer (010-current) plan.md"
    assert OLD_PLAN_MARK not in user, "figure agent must NOT use the stale (001-old) plan.md"
