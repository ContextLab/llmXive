"""Contract tests for panel prompt files (spec 015 T049-T053).

Asserts that every lens named in the ReviewSpec registry resolves to a real
prompt file on disk, that each file references the shared protocol block
(Constitution Principle I: SSoT), and that the shared block itself defines
the severity vocabulary the engine expects.

This test catches drift between the registry (`reviewspecs.py`) and the
prompt files: if someone adds a lens to the registry without authoring the
prompt, or renames a prompt without updating the registry, this fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.convergence.reviewspecs import reviewable_stages, reviewspec_for
from llmxive.convergence.types import Severity

REPO_ROOT = Path(__file__).resolve().parents[2]
PANELS_DIR = REPO_ROOT / "agents" / "prompts" / "panels"
SHARED_BLOCK = REPO_ROOT / "agents" / "prompts" / "_shared" / "panel_review_block.md"

# Stages that REUSE the existing research/paper specialist prompts rather than
# adding new panel prompts (the formal-review unit stages from `reviewspec_for`
# whose reviewers like `research_reviewer`/`paper_reviewer` already exist).
REUSE_STAGES = frozenset({"research_review", "paper_review"})

# Lens → expected prompt-file name relative to PANELS_DIR. Lenses NOT in this
# map are assumed reused-from-existing (research/paper specialists). The map
# is the SSoT for file-naming: T054-T059 wiring code reads it (or this same
# pattern) to render prompts.
_STAGE_PREFIX: dict[str, str] = {
    "flesh_out_complete": "idea",
    "clarified": "spec",
    "planned": "plan",
    "tasked": "tasks",
    "paper_clarified": "paper_spec",
    "paper_planned": "paper_plan",
    "paper_tasked": "paper_tasks",
}

# A few lens names need explicit overrides (the natural `panel_<stage>_<lens>.md`
# would double-prefix, e.g. "panel_plan_plan_consistency.md" — we drop the
# inner "plan_" to keep the filename readable).
_FILENAME_OVERRIDES: dict[tuple[str, str], str] = {
    ("planned", "plan_consistency"): "panel_plan_consistency.md",
    ("paper_planned", "plan_constitution_consistency"): (
        "panel_paper_plan_constitution_consistency.md"
    ),
}


def _prompt_path_for(stage: str, lens: str) -> Path:
    override = _FILENAME_OVERRIDES.get((stage, lens))
    if override is not None:
        return PANELS_DIR / override
    prefix = _STAGE_PREFIX[stage]
    return PANELS_DIR / f"panel_{prefix}_{lens}.md"


def test_shared_block_exists_and_defines_severity_vocabulary():
    """The SSoT panel protocol block must exist and enumerate the severity
    vocabulary the convergence engine consumes (FR-027/FR-030)."""
    assert SHARED_BLOCK.exists(), f"missing SSoT block: {SHARED_BLOCK}"
    text = SHARED_BLOCK.read_text()
    for sev in Severity:
        assert f"`{sev.value}`" in text, (
            f"shared block must enumerate severity '{sev.value}'"
        )
    # Must describe both R1 (identify) and R3 (re-review) phases.
    assert "Identify (R1)" in text, "shared block must define R1 contract"
    assert "Re-review (R3)" in text, "shared block must define R3 contract"


@pytest.mark.parametrize("stage", sorted(set(reviewable_stages()) - REUSE_STAGES))
def test_every_registry_lens_has_a_prompt_file(stage):
    """For every reviewable stage with a new panel, every lens in the
    registry MUST resolve to a real prompt file on disk."""
    spec = reviewspec_for(stage)
    assert spec is not None, f"{stage}: registry returned None"
    for reviewer in spec.reviewers:
        path = _prompt_path_for(stage, reviewer.name)
        assert path.exists(), (
            f"stage {stage!r} lens {reviewer.name!r} expects "
            f"{path.relative_to(REPO_ROOT)} — file missing"
        )


@pytest.mark.parametrize("stage", sorted(set(reviewable_stages()) - REUSE_STAGES))
def test_every_panel_prompt_references_shared_block(stage):
    """Every panel prompt must reference the SSoT block (Principle I) so the
    engine can locate the shared protocol when rendering."""
    spec = reviewspec_for(stage)
    assert spec is not None
    for reviewer in spec.reviewers:
        path = _prompt_path_for(stage, reviewer.name)
        text = path.read_text()
        assert "_shared/panel_review_block.md" in text, (
            f"{path.name}: must reference the SSoT shared block"
        )
        # And must declare its lens + output format sections so the engine's
        # render pass can find them.
        assert "## Lens" in text, f"{path.name}: missing '## Lens' section"
        assert "## Output format" in text, (
            f"{path.name}: missing '## Output format' section"
        )


def test_reuse_stages_skip_panel_prompts():
    """`research_review` / `paper_review` reuse existing specialist prompts —
    they MUST NOT have new files under panels/. Lens names are short-form
    (e.g. ``code_quality``); the existing files use the disambiguating
    ``_research`` / ``_paper`` suffix when the same lens applies to both
    panels (``code_quality_research.md`` vs ``code_quality_paper.md``).
    The T058/T059 wiring code resolves short→long based on the panel context.
    """
    prompts_dir = REPO_ROOT / "agents" / "prompts"
    for stage in REUSE_STAGES:
        spec = reviewspec_for(stage)
        assert spec is not None
        role = "research_reviewer" if stage == "research_review" else "paper_reviewer"
        suffix = "_research" if stage == "research_review" else "_paper"
        for reviewer in spec.reviewers:
            lens = reviewer.name
            candidates = [
                prompts_dir / f"{role}_{lens}.md",          # unsuffixed
                prompts_dir / f"{role}_{lens}{suffix}.md",  # disambiguated
                prompts_dir / f"{lens}.md",                 # generic
            ]
            found = [c for c in candidates if c.exists()]
            assert found, (
                f"reuse-stage {stage!r} lens {lens!r}: tried "
                f"{[c.name for c in candidates]} — none exist"
            )
