"""Regression (spec 023 defect #19): the PROJ-552 spec regeneration loop.

THE BUG (observed live): the spec panel's WRITING/REQUIREMENT kickback routed
to "project_initialized", whose agent is the SPECIFIER — which unconditionally
minted a fresh ``specs/NNN`` dir and regenerated the whole document. Each
near-converged panel run (e.g. one writing nit left at the round cap) was
followed by a brand-new document with a fresh crop of nits: PROJ-552 reached
``specs/010`` with concern counts oscillating 24→10→3→5→4→1→11 instead of
converging. Three coupled fixes, each pinned here:

1. Routing: spec-panel WRITING/REQUIREMENT → "specified" (clarifier + spec
   panel re-run; the SpecReviser edits spec.md IN PLACE). Paper twin:
   "paper_specified". Only idea-root severities regenerate.
2. Specifier re-entry: when the project pointer names a feature dir with a
   mature spec.md, the specifier REUSES it (no create-new-feature.sh mint)
   and revises that spec as its base. Paper twin identical.
3. Diagnosis hand-off: a doc-stage kickback persists the panel's unresolved
   concerns to ``.specify/memory/kickback_feedback.md``; every speckit
   command injects it via ``render_recent_comments_block``; the graph
   deletes it once the panel converges.

Real helpers, real tmp project trees, real project_store saves — no mocks of
the units under test.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.convergence import reviewspecs
from llmxive.convergence.types import Severity
from llmxive.pipeline._kickback import KickbackDecision
from llmxive.pipeline.graph import (
    KICKBACK_FEEDBACK_FILENAME,
    _write_doc_kickback_feedback,
)
from llmxive.speckit._comments_context import render_recent_comments_block
from llmxive.speckit.paper_specify_cmd import PaperSpecifierAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.speckit.specify_cmd import SpecifierAgent
from llmxive.state import project as project_store
from llmxive.types import BackendName, Project, Stage

_SPEC_BODY = (
    "# Feature Specification: Knot Diagram Complexity\n\n"
    "## Requirements\n\n- FR-001: classify >= 95% of diagrams within 60s.\n"
)


def _ctx(project_id: str, project_dir: Path, *, agent_name: str) -> SlashCommandContext:
    return SlashCommandContext(
        project_id=project_id,
        project_dir=project_dir,
        run_id="r",
        task_id="t",
        inputs=[],
        expected_outputs=[],
        prompt_template_path=project_dir / "ignored.md",
        default_backend=BackendName.DARTMOUTH,
        fallback_backends=[],
        default_model="m",
        prompt_version="1.0.0",
        agent_name=agent_name,
    )


def _save_project(
    repo: Path,
    project_id: str,
    *,
    research_dir: str | None = None,
    paper_dir: str | None = None,
) -> None:
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    project = Project(
        id=project_id,
        title="Knot Diagram Complexity",
        field="topology",
        current_stage=Stage.BRAINSTORMED,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=research_dir,
        speckit_paper_dir=paper_dir,
    )
    project_store.save(project, repo_root=repo)


# ──────────────────────────────────────────────────────────────────────
# 1. Routing: writing/requirement residue revises IN PLACE.
# ──────────────────────────────────────────────────────────────────────


def test_spec_panel_writing_residue_does_not_regenerate():
    spec = reviewspecs._spec_research_spec()
    for sev in (Severity.WRITING, Severity.REQUIREMENT):
        assert spec.kickback_routing[sev] == "specified", (
            f"spec panel {sev}: doc-level residue must re-run the clarifier "
            "+ spec panel on the SAME document — routing to "
            "'project_initialized' re-runs the specifier, which regenerates "
            "a fresh specs/NNN dir (the PROJ-552 oscillation loop)"
        )
    # Idea-root causes still regenerate via the idea stage.
    for sev in (Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL):
        assert spec.kickback_routing[sev] == "flesh_out_in_progress"


def test_paper_spec_panel_writing_residue_does_not_regenerate():
    spec = reviewspecs._spec_paper_spec()
    for sev in (Severity.WRITING, Severity.REQUIREMENT):
        assert spec.kickback_routing[sev] == "paper_specified"
    for sev in (Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL):
        assert spec.kickback_routing[sev] == "clarified"


# ──────────────────────────────────────────────────────────────────────
# 2. Specifier re-entry reuses the pointer dir (no fresh mint).
# ──────────────────────────────────────────────────────────────────────


class TestSpecifierReuse:
    def test_mechanical_step_reuses_pointer_dir(self, tmp_path: Path) -> None:
        """With a mature pointer spec, NO create-new-feature.sh run happens —
        the fixture tree has no script at all, so reaching the script would
        raise; getting the pointer dir back proves the reuse path."""
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        feature = proj_dir / "specs" / "010-knots"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(_SPEC_BODY, encoding="utf-8")
        _save_project(
            tmp_path, project_id,
            research_dir=f"projects/{project_id}/specs/010-knots",
        )
        agent = SpecifierAgent.__new__(SpecifierAgent)
        out = agent.mechanical_step(_ctx(project_id, proj_dir, agent_name="specifier"))
        assert out["REUSED_FEATURE_DIR"] is True
        assert out["FEATURE_DIR"] == f"projects/{project_id}/specs/010-knots"
        assert out["FEATURE_NUM"] == "010"
        # No sibling dir was minted.
        assert sorted(p.name for p in (proj_dir / "specs").iterdir()) == ["010-knots"]

    def test_no_pointer_is_not_reusable(self, tmp_path: Path) -> None:
        project_id = "PROJ-553-fresh"
        proj_dir = tmp_path / "projects" / project_id
        proj_dir.mkdir(parents=True)
        _save_project(tmp_path, project_id, research_dir=None)
        agent = SpecifierAgent.__new__(SpecifierAgent)
        assert agent._reusable_feature_dir(
            _ctx(project_id, proj_dir, agent_name="specifier")
        ) is None

    def test_empty_spec_is_not_reusable(self, tmp_path: Path) -> None:
        project_id = "PROJ-554-empty"
        proj_dir = tmp_path / "projects" / project_id
        feature = proj_dir / "specs" / "001-x"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text("   \n", encoding="utf-8")
        _save_project(
            tmp_path, project_id, research_dir=f"projects/{project_id}/specs/001-x",
        )
        agent = SpecifierAgent.__new__(SpecifierAgent)
        assert agent._reusable_feature_dir(
            _ctx(project_id, proj_dir, agent_name="specifier")
        ) is None

    def test_build_prompt_revision_base_is_own_spec(self, tmp_path: Path) -> None:
        """On reuse, the revision base is the CURRENT dir's spec.md (the
        sibling-only ``_find_prior_spec`` would miss it)."""
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        feature = proj_dir / "specs" / "010-knots"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(_SPEC_BODY, encoding="utf-8")
        (proj_dir / "idea").mkdir(parents=True)
        (proj_dir / "idea" / "idea.md").write_text("# Idea\nKnots.\n", encoding="utf-8")
        # build_prompt renders the real specifier prompt from the repo root
        # (tmp_path here) — provide a minimal real template.
        prompts_dir = tmp_path / "agents" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "specifier.md").write_text(
            "# Specifier\nDraft spec.md for the idea.\n", encoding="utf-8"
        )
        _save_project(
            tmp_path, project_id,
            research_dir=f"projects/{project_id}/specs/010-knots",
        )
        agent = SpecifierAgent.__new__(SpecifierAgent)
        ctx = _ctx(project_id, proj_dir, agent_name="specifier")
        out = agent.mechanical_step(ctx)
        messages = agent.build_prompt(ctx, out)
        user = messages[-1].content
        assert "Prior spec (revision base)" in user
        assert "classify >= 95% of diagrams within 60s" in user


class TestPaperSpecifierReuse:
    def test_mechanical_step_reuses_paper_pointer_dir(self, tmp_path: Path) -> None:
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        paper_feature = proj_dir / "paper" / "specs" / "002-paper"
        paper_feature.mkdir(parents=True)
        (paper_feature / "spec.md").write_text("# Paper spec\nBody.\n", encoding="utf-8")
        _save_project(
            tmp_path, project_id,
            paper_dir=f"projects/{project_id}/paper/specs/002-paper",
        )
        agent = PaperSpecifierAgent.__new__(PaperSpecifierAgent)
        out = agent.mechanical_step(_ctx(project_id, proj_dir, agent_name="paper_specifier"))
        assert out["REUSED_FEATURE_DIR"] is True
        assert out["FEATURE_DIR"] == f"projects/{project_id}/paper/specs/002-paper"
        assert sorted(p.name for p in (proj_dir / "paper" / "specs").iterdir()) == [
            "002-paper"
        ]

    def test_research_spec_resolved_by_pointer_not_first_glob(self, tmp_path: Path) -> None:
        """Defect #17 class inside the paper specifier: the research spec
        feeding the paper must come from the pointer dir, not specs/001."""
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        stale = proj_dir / "specs" / "001-knots"
        live = proj_dir / "specs" / "010-knots"
        stale.mkdir(parents=True)
        live.mkdir(parents=True)
        (stale / "spec.md").write_text("# STALE spec 001\n", encoding="utf-8")
        (live / "spec.md").write_text("# LIVE spec 010\n", encoding="utf-8")
        _save_project(
            tmp_path, project_id,
            research_dir=f"projects/{project_id}/specs/010-knots",
        )
        agent = PaperSpecifierAgent.__new__(PaperSpecifierAgent)
        resolved = agent._research_spec_path(_ctx(project_id, proj_dir, agent_name="paper_specifier"))
        assert resolved is not None
        assert resolved.parent.name == "010-knots"
        assert "LIVE" in resolved.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────
# 3. Doc-stage kickback diagnosis: persisted, injected, consumed.
# ──────────────────────────────────────────────────────────────────────


def _decision(**overrides) -> KickbackDecision:
    kwargs = {
        "to_stage": "specified",
        "escalate": False,
        "stage_label": "spec",
        "reason": "2 concern(s) remained unresolved after 3 round(s)",
        "count": 1,
        "unresolved_concerns": (
            "testability: 'a specified threshold' lacks a concrete value",
            "writing: SC-003 wording is ambiguous",
        ),
    }
    kwargs.update(overrides)
    return KickbackDecision(**kwargs)


class TestDocKickbackFeedback:
    def test_written_note_carries_reason_and_concerns(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "projects" / "PROJ-552-knots"
        project_dir.mkdir(parents=True)
        _write_doc_kickback_feedback(project_dir, _decision())
        note = project_dir / ".specify" / "memory" / KICKBACK_FEEDBACK_FILENAME
        body = note.read_text(encoding="utf-8")
        assert "IN-PLACE revision" in body
        assert "a specified threshold" in body
        assert "SC-003" in body
        assert "do NOT regenerate" in body

    def test_comments_block_injects_note(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "projects" / "PROJ-552-knots"
        project_dir.mkdir(parents=True)
        # No reviews dir at all: the kickback note must still surface.
        _write_doc_kickback_feedback(project_dir, _decision())
        block = render_recent_comments_block(project_dir)
        assert "Unresolved panel concerns" in block
        assert "a specified threshold" in block

    def test_comments_block_prepends_note_before_comments(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "projects" / "PROJ-552-knots"
        reviews = project_dir / "reviews" / "research"
        reviews.mkdir(parents=True)
        (reviews / "ada__2026-06-01__research.md").write_text("nice idea", encoding="utf-8")
        _write_doc_kickback_feedback(project_dir, _decision())
        block = render_recent_comments_block(project_dir)
        assert block.index("Unresolved panel concerns") < block.index(
            "Recent reviewer / personality comments"
        )

    def test_comments_block_empty_without_note_or_reviews(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "projects" / "PROJ-552-knots"
        project_dir.mkdir(parents=True)
        assert render_recent_comments_block(project_dir) == ""
