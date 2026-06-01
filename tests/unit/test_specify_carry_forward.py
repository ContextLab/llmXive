"""Spec-015 convergence-quality regression: the Specifier must SEED/REVISE
from the prior mature spec on a post-kickback regeneration (specs/001 →
specs/002), instead of regenerating from scratch and ratcheting quality DOWN.

THE FLAW (verified on PROJ-552): a spec-stage convergence kickback routes
spec → flesh_out → project_initialize → specify, and the Specifier regenerated
the spec FROM SCRATCH from the realigned idea, ignoring the prior mature spec.
On PROJ-552 the prior spec (specs/001) was mature (13 FRs, 13 SCs, 0 unresolved
clarifications) and the regenerated spec (specs/002) collapsed (10 FRs, 5 SCs)
and re-introduced 3 `[NEEDS CLARIFICATION]` markers. Convergence is supposed to
monotonically improve; a kickback made it strictly worse.

THE FIX: when generating a spec, if a PRIOR non-empty spec.md exists (i.e. this
is a post-kickback REGENERATION, not a first-time spec), inject it into the
Specifier's prompt as a "revision base" with instructions to PRESERVE accumulated
detail while realigning to the (updated) idea. First-time specs are UNCHANGED.

These tests use real file IO (tmp_path) and the real SpecifierAgent.build_prompt
/ _find_prior_spec — no mocks of the unit under test. The only stub is the
system-prompt template loader (the real specifier.md lives in the source repo,
not under tmp_path's synthetic repo root), mirroring the phase4 planner tests.
"""

from __future__ import annotations

from pathlib import Path

import llmxive.speckit.specify_cmd as specify_cmd
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.speckit.specify_cmd import SpecifierAgent, _find_prior_spec
from llmxive.types import BackendName

# A rich, mature prior spec: 13 distinct FR lines + several SC lines + a
# resolved clarification, modeled on the PROJ-552 specs/001 spec.
RICH_SPEC = """# Feature Specification: Quantifying Knot Diagram Complexity

## User Scenarios

### User Story 1 - Compute complexity (Priority: P1)

A researcher loads a knot diagram and obtains a reproducible complexity score.

## Functional Requirements

- **FR-001**: System MUST parse a knot diagram from a PD-code input.
- **FR-002**: System MUST compute the crossing number for the diagram.
- **FR-003**: System MUST compute the writhe of the diagram.
- **FR-004**: System MUST compute the Gauss code from the PD-code.
- **FR-005**: System MUST normalize the diagram to a canonical form.
- **FR-006**: System MUST report a scalar complexity score in [0, 1].
- **FR-007**: System MUST be deterministic across repeated runs.
- **FR-008**: System MUST reject malformed PD-codes with a clear error.
- **FR-009**: System MUST handle diagrams with up to 20 crossings.
- **FR-010**: System MUST persist intermediate invariants for audit.
- **FR-011**: System MUST expose a stable Python API surface.
- **FR-012**: System MUST log every computation step for reproducibility.
- **FR-013**: System MUST validate inputs against the Rolfsen table.

## Success Criteria

- **SC-001**: 100% of valid PD-codes produce a score without error.
- **SC-002**: Identical inputs yield identical scores across 1000 runs.
- **SC-003**: Malformed inputs are rejected within 50 ms.
- **SC-004**: Scores correlate (r > 0.8) with crossing number on the test set.
- **SC-005**: The API documentation covers every public function.

## Edge Cases

- The unknot (zero crossings) yields a complexity score of exactly 0.
- A diagram exceeding 20 crossings raises a documented capacity error.

## Key Entities

- KnotDiagram: a parsed PD-code with crossings and arcs.
- ComplexityScore: a scalar in [0, 1] with provenance metadata.
"""


def _ctx(project_id: str, project_dir: Path) -> SlashCommandContext:
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
        agent_name="specifier",
    )


def _seed_project(tmp_path: Path, project_id: str) -> Path:
    """Build a minimal project tree: idea/ + .specify/templates/spec-template.md."""
    proj = tmp_path / "projects" / project_id
    (proj / "idea").mkdir(parents=True)
    (proj / "idea" / "idea.md").write_text(
        "# Realigned Idea\n\nQuantify knot diagram complexity, scoped to the "
        "Rolfsen table to address the panel's scope-drift concern.\n",
        encoding="utf-8",
    )
    (proj / ".specify" / "templates").mkdir(parents=True)
    (proj / ".specify" / "templates" / "spec-template.md").write_text(
        "# Feature Specification: [TITLE]\n\n## Functional Requirements\n\n"
        "- **FR-001**: [placeholder]\n",
        encoding="utf-8",
    )
    return proj


# ──────────────────────────────────────────────────────────────────────
# Helper-level: find the prior mature spec dir.
# ──────────────────────────────────────────────────────────────────────


class TestFindPriorSpec:
    def test_returns_prior_when_current_is_002(self, tmp_path: Path) -> None:
        """specs/001 rich + specs/002 (current, empty) → returns specs/001/spec.md."""
        proj = tmp_path / "projects" / "PROJ-552-knots"
        d1 = proj / "specs" / "001-knots"
        d2 = proj / "specs" / "002-knots"
        d1.mkdir(parents=True)
        d2.mkdir(parents=True)
        (d1 / "spec.md").write_text(RICH_SPEC, encoding="utf-8")
        # d2 is the current dir this invocation is writing to: empty so far.
        prior = _find_prior_spec(current_feature_dir=d2)
        assert prior == d1 / "spec.md"

    def test_returns_none_when_only_current_dir(self, tmp_path: Path) -> None:
        """First-time spec: only the current dir exists (empty) → None."""
        proj = tmp_path / "projects" / "PROJ-552-knots"
        d1 = proj / "specs" / "001-knots"
        d1.mkdir(parents=True)
        # No spec.md written yet — this IS the dir being written to.
        prior = _find_prior_spec(current_feature_dir=d1)
        assert prior is None

    def test_skips_empty_prior_spec(self, tmp_path: Path) -> None:
        """A prior dir with an empty/whitespace spec.md is NOT a revision base."""
        proj = tmp_path / "projects" / "PROJ-552-knots"
        d1 = proj / "specs" / "001-knots"
        d2 = proj / "specs" / "002-knots"
        d1.mkdir(parents=True)
        d2.mkdir(parents=True)
        (d1 / "spec.md").write_text("   \n\n", encoding="utf-8")
        prior = _find_prior_spec(current_feature_dir=d2)
        assert prior is None

    def test_picks_highest_numbered_prior(self, tmp_path: Path) -> None:
        """With 001, 002 both non-empty and 003 current → returns 002 (highest prior)."""
        proj = tmp_path / "projects" / "PROJ-552-knots"
        d1 = proj / "specs" / "001-knots"
        d2 = proj / "specs" / "002-knots"
        d3 = proj / "specs" / "003-knots"
        for d in (d1, d2, d3):
            d.mkdir(parents=True)
        (d1 / "spec.md").write_text("# old\n" + RICH_SPEC, encoding="utf-8")
        (d2 / "spec.md").write_text(RICH_SPEC, encoding="utf-8")
        prior = _find_prior_spec(current_feature_dir=d3)
        assert prior == d2 / "spec.md"


# ──────────────────────────────────────────────────────────────────────
# build_prompt: revision base injected on regeneration, absent on first run.
# ──────────────────────────────────────────────────────────────────────


class TestBuildPromptRevisionBase:
    def test_regeneration_injects_revision_base(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        proj = _seed_project(tmp_path, "PROJ-552-knots")
        d1 = proj / "specs" / "001-knots"
        d2 = proj / "specs" / "002-knots"
        d1.mkdir(parents=True)
        d2.mkdir(parents=True)
        (d1 / "spec.md").write_text(RICH_SPEC, encoding="utf-8")
        # The mechanical step created the new dir (002) — that's where we write.

        # Stub the system-prompt loader (real specifier.md lives in source repo).
        monkeypatch.setattr(specify_cmd, "render_prompt", lambda *a, **k: "stub system")

        ctx = _ctx("PROJ-552-knots", proj)
        mech = {"FEATURE_DIR": str(d2), "BRANCH_NAME": "002-knots", "FEATURE_NUM": "002"}
        msgs = SpecifierAgent().build_prompt(ctx, mech)
        user = msgs[-1].content

        # Prior spec content is present (a distinctive FR line unique to it).
        assert "**FR-013**: System MUST validate inputs against the Rolfsen table." in user
        # The revision-base block + preserve-detail instructions are present.
        assert "revision base" in user.lower()
        assert "preserve EVERY still-valid" in user
        # It must NOT re-introduce NEEDS CLARIFICATION for resolved items.
        assert "NEEDS CLARIFICATION" in user  # appears in the instruction text
        # And the at-least-as-complete guarantee is stated.
        assert "at least as complete" in user.lower()

    def test_first_time_has_no_revision_base(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Genuine first-time spec: only the current dir, no prior non-empty
        spec → behavior UNCHANGED (no revision-base block)."""
        proj = _seed_project(tmp_path, "PROJ-700-fresh")
        d1 = proj / "specs" / "001-fresh"
        d1.mkdir(parents=True)
        # No prior spec.md anywhere; 001 is the dir being written to.

        monkeypatch.setattr(specify_cmd, "render_prompt", lambda *a, **k: "stub system")

        ctx = _ctx("PROJ-700-fresh", proj)
        mech = {"FEATURE_DIR": str(d1), "BRANCH_NAME": "001-fresh", "FEATURE_NUM": "001"}
        msgs = SpecifierAgent().build_prompt(ctx, mech)
        user = msgs[-1].content

        assert "revision base" not in user.lower()
        assert "preserve EVERY still-valid" not in user
        assert "# Prior spec" not in user
        # The idea is still injected (unchanged first-time behavior).
        assert "Realigned Idea" in user
