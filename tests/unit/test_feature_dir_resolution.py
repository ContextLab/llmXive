"""Feature-directory resolution regression tests (spec-015 kickback bug).

THE BUG: most speckit stages resolved their "feature directory" by globbing
``specs/*/`` and picking the FIRST (oldest) match, ignoring the project's
authoritative ``speckit_research_dir`` / ``speckit_paper_dir`` pointer. When a
convergence kickback regenerates the spec (specs/001 → specs/002), those stages
then built the plan/tasks/implementation against the SUPERSEDED specs/001 spec.

These tests exercise the REAL shared helper + the REAL project_store.save/load
(no mocks of the unit under test). They build a real tmp project tree with BOTH
``specs/001-x/spec.md`` and ``specs/002-x/spec.md`` and a real saved Project
whose pointer references specs/002 — the converged spec.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.speckit._feature_dir import resolve_feature_dir
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.state import project as project_store
from llmxive.types import BackendName, Project, Stage


def _ctx(project_id: str, project_dir: Path, *, agent_name: str = "planner") -> SlashCommandContext:
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


def _write_two_research_specs(project_dir: Path) -> tuple[Path, Path]:
    """Create specs/001-x/spec.md (superseded) and specs/002-x/spec.md (current)."""
    d1 = project_dir / "specs" / "001-knots"
    d2 = project_dir / "specs" / "002-knots"
    d1.mkdir(parents=True)
    d2.mkdir(parents=True)
    (d1 / "spec.md").write_text("# Spec 001 — fabricated 27,635 knots\n", encoding="utf-8")
    (d2 / "spec.md").write_text("# Spec 002 — converged 9,988 knots\n", encoding="utf-8")
    return d1, d2


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
# Research-track: authoritative-pointer wins over the first/oldest glob.
# ──────────────────────────────────────────────────────────────────────

class TestResearchPointer:
    def test_pointer_to_002_returns_002_not_001(self, tmp_path: Path) -> None:
        """The regression that matters: pointer = specs/002 → resolve to 002,
        NOT the alphabetically-first specs/001."""
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/002-knots",
        )
        ctx = _ctx(project_id, proj_dir)
        resolved = resolve_feature_dir(ctx)
        assert resolved == d2
        assert resolved != d1
        assert resolved.name == "002-knots"

    def test_pointer_to_001_returns_001(self, tmp_path: Path) -> None:
        """Pointer honored both directions — not merely 'always pick latest'."""
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        d1, _d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/001-knots",
        )
        ctx = _ctx(project_id, proj_dir)
        assert resolve_feature_dir(ctx) == d1


# ──────────────────────────────────────────────────────────────────────
# Paper-track: speckit_paper_dir pointer under projects/<id>/paper/.
# ──────────────────────────────────────────────────────────────────────

class TestPaperPointer:
    def test_paper_pointer_to_002_returns_paper_002(self, tmp_path: Path) -> None:
        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        paper_dir = proj_dir / "paper"
        pd1 = paper_dir / "specs" / "001-paper"
        pd2 = paper_dir / "specs" / "002-paper"
        pd1.mkdir(parents=True)
        pd2.mkdir(parents=True)
        (pd1 / "spec.md").write_text("# Paper spec 001\n", encoding="utf-8")
        (pd2 / "spec.md").write_text("# Paper spec 002\n", encoding="utf-8")
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/001-x",
            paper_dir=f"projects/{project_id}/paper/specs/002-paper",
        )
        ctx = _ctx(project_id, proj_dir, agent_name="paper_planner")
        resolved = resolve_feature_dir(ctx, paper=True)
        assert resolved == pd2
        assert resolved.name == "002-paper"


# ──────────────────────────────────────────────────────────────────────
# Fallback: pointer unset (legacy project) → pick the LATEST, never the first.
# ──────────────────────────────────────────────────────────────────────

class TestGlobFallback:
    def test_unset_pointer_picks_latest_not_first(self, tmp_path: Path) -> None:
        project_id = "PROJ-100-legacy"
        proj_dir = tmp_path / "projects" / project_id
        d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(tmp_path, project_id, research_dir=None)
        ctx = _ctx(project_id, proj_dir)
        resolved = resolve_feature_dir(ctx)
        assert resolved == d2, "fallback must pick the LATEST spec dir, not the oldest"
        assert resolved != d1

    def test_no_saved_project_falls_back_to_latest_glob(self, tmp_path: Path) -> None:
        """FileNotFoundError on project load → glob fallback (still latest)."""
        project_id = "PROJ-101-noproject"
        proj_dir = tmp_path / "projects" / project_id
        _d1, d2 = _write_two_research_specs(proj_dir)
        # No project state saved at all.
        ctx = _ctx(project_id, proj_dir)
        assert resolve_feature_dir(ctx) == d2

    def test_pointer_set_but_missing_on_disk_falls_back_to_latest(self, tmp_path: Path) -> None:
        """A stale pointer (dir deleted) must not crash — fall back to glob."""
        project_id = "PROJ-102-stale"
        proj_dir = tmp_path / "projects" / project_id
        _d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/099-gone",
        )
        ctx = _ctx(project_id, proj_dir)
        assert resolve_feature_dir(ctx) == d2

    def test_fallback_prefers_dir_with_spec_md(self, tmp_path: Path) -> None:
        """When the latest dir lacks spec.md but an earlier one has it, prefer
        the spec.md-bearing dir (matches the legacy ghost-slug guard)."""
        project_id = "PROJ-103-ghost"
        proj_dir = tmp_path / "projects" / project_id
        d1 = proj_dir / "specs" / "001-real"
        d2 = proj_dir / "specs" / "002-ghost"
        d1.mkdir(parents=True)
        d2.mkdir(parents=True)
        (d1 / "spec.md").write_text("# real spec\n", encoding="utf-8")
        # d2 is a ghost dir with no spec.md.
        _save_project(tmp_path, project_id, research_dir=None)
        ctx = _ctx(project_id, proj_dir)
        assert resolve_feature_dir(ctx) == d1


# ──────────────────────────────────────────────────────────────────────
# Missing dirs → FileNotFoundError.
# ──────────────────────────────────────────────────────────────────────

class TestMissing:
    def test_no_specs_dir_raises(self, tmp_path: Path) -> None:
        project_id = "PROJ-104-empty"
        proj_dir = tmp_path / "projects" / project_id
        proj_dir.mkdir(parents=True)
        _save_project(tmp_path, project_id, research_dir=None)
        ctx = _ctx(project_id, proj_dir)
        with pytest.raises(FileNotFoundError):
            resolve_feature_dir(ctx)

    def test_paper_no_specs_dir_raises(self, tmp_path: Path) -> None:
        project_id = "PROJ-105-emptypaper"
        proj_dir = tmp_path / "projects" / project_id
        (proj_dir / "paper").mkdir(parents=True)
        _save_project(tmp_path, project_id, research_dir=None, paper_dir=None)
        ctx = _ctx(project_id, proj_dir, agent_name="paper_planner")
        with pytest.raises(FileNotFoundError):
            resolve_feature_dir(ctx, paper=True)


# ──────────────────────────────────────────────────────────────────────
# Stages now delegate to the shared helper.
# ──────────────────────────────────────────────────────────────────────

class TestStagesDelegate:
    def test_plan_cmd_resolves_via_pointer(self, tmp_path: Path) -> None:
        from llmxive.speckit.plan_cmd import PlannerAgent

        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        _d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/002-knots",
        )
        ctx = _ctx(project_id, proj_dir)
        assert PlannerAgent()._feature_dir(ctx) == d2

    def test_tasks_cmd_resolves_via_pointer(self, tmp_path: Path) -> None:
        from llmxive.speckit.tasks_cmd import TaskerAgent

        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        _d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/002-knots",
        )
        ctx = _ctx(project_id, proj_dir, agent_name="tasker")
        assert TaskerAgent()._feature_dir(ctx) == d2

    def test_implement_cmd_resolves_via_pointer(self, tmp_path: Path) -> None:
        from llmxive.speckit.implement_cmd import ImplementerAgent

        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        _d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/002-knots",
        )
        ctx = _ctx(project_id, proj_dir, agent_name="implementer")
        assert ImplementerAgent()._feature_dir(ctx) == d2

    def test_clarify_cmd_spec_path_resolves_via_pointer(self, tmp_path: Path) -> None:
        from llmxive.speckit.clarify_cmd import ClarifierAgent

        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        _d1, d2 = _write_two_research_specs(proj_dir)
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/002-knots",
        )
        ctx = _ctx(project_id, proj_dir, agent_name="clarifier")
        assert ClarifierAgent()._spec_path(ctx) == d2 / "spec.md"

    def test_paper_plan_cmd_resolves_via_pointer(self, tmp_path: Path) -> None:
        from llmxive.speckit.paper_plan_cmd import PaperPlannerAgent

        project_id = "PROJ-552-knots"
        proj_dir = tmp_path / "projects" / project_id
        paper_dir = proj_dir / "paper"
        pd1 = paper_dir / "specs" / "001-paper"
        pd2 = paper_dir / "specs" / "002-paper"
        pd1.mkdir(parents=True)
        pd2.mkdir(parents=True)
        (pd1 / "spec.md").write_text("# paper 001\n", encoding="utf-8")
        (pd2 / "spec.md").write_text("# paper 002\n", encoding="utf-8")
        _save_project(
            tmp_path,
            project_id,
            research_dir=f"projects/{project_id}/specs/001-x",
            paper_dir=f"projects/{project_id}/paper/specs/002-paper",
        )
        ctx = _ctx(project_id, proj_dir, agent_name="paper_planner")
        assert PaperPlannerAgent()._feature_dir(ctx) == pd2
