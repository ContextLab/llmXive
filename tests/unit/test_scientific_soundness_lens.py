"""Unit tests for the scientific_soundness panel lens (spec 015 hardening, B1).

The lens adds a subject-matter-soundness check to BOTH the spec panel
(``clarified``) and the plan panel (``planned``) — catching circular /
tautological validations the existing consistency/coverage/scope lenses miss
(motivated by PROJ-552). These tests verify the WIRING and prompt existence /
contract — NOT whether a live model catches circularity (that is
model-dependent and belongs to real-call calibration runs, not the offline
gate).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.convergence.llm_reviewer import _prompt_path_for
from llmxive.convergence.reviewspecs import reviewspec_for

REPO_ROOT = Path(__file__).resolve().parents[2]

# Lens counts BEFORE adding scientific_soundness: spec + plan panels each had 4.
_BASELINE_LENS_COUNT = 4


@pytest.mark.parametrize("stage", ["clarified", "planned"])
def test_panel_includes_scientific_soundness_and_count_went_up(stage):
    """Both the spec (clarified) and plan (planned) panels must now include the
    scientific_soundness lens, raising each panel's lens count by exactly 1."""
    spec = reviewspec_for(stage)
    assert spec is not None
    names = [r.name for r in spec.reviewers]
    assert "scientific_soundness" in names, f"{stage}: {names}"
    assert len(names) == _BASELINE_LENS_COUNT + 1, (
        f"{stage}: expected {_BASELINE_LENS_COUNT + 1} lenses, got {len(names)}: {names}"
    )
    # No accidental duplicate registration.
    assert names.count("scientific_soundness") == 1


@pytest.mark.parametrize("stage", ["clarified", "planned"])
def test_scientific_soundness_prompt_resolves_to_nonempty_file(stage):
    """_prompt_path_for must resolve the lens to an EXISTING, non-empty prompt
    file for both the spec and plan stages."""
    path = _prompt_path_for(stage=stage, lens="scientific_soundness", repo_root=REPO_ROOT)
    assert path.exists(), f"{stage}: missing prompt file {path}"
    assert path.read_text().strip(), f"{stage}: prompt file is empty {path}"


@pytest.mark.parametrize("stage", ["clarified", "planned"])
def test_scientific_soundness_prompt_honors_panel_contract(stage):
    """The new prompt must mirror the existing lens prompts: reference the SSoT
    panel-review block and declare the '## Lens' + '## Output format' sections
    the engine's render pass expects."""
    path = _prompt_path_for(stage=stage, lens="scientific_soundness", repo_root=REPO_ROOT)
    text = path.read_text()
    assert "_shared/panel_review_block.md" in text, (
        f"{path.name}: must reference the SSoT shared panel-review block"
    )
    assert "## Lens" in text, f"{path.name}: missing '## Lens' section"
    assert "## Output format" in text, f"{path.name}: missing '## Output format' section"


@pytest.mark.parametrize("stage", ["clarified", "planned"])
def test_scientific_soundness_prompt_is_domain_general(stage):
    """The lens must be GENERAL across all 9 research domains — it must NOT
    hardcode a single field (e.g. knot theory). Guard against the specific
    PROJ-552 terms leaking into the general prompt."""
    path = _prompt_path_for(stage=stage, lens="scientific_soundness", repo_root=REPO_ROOT)
    text = path.read_text().lower()
    for term in ("knot", "braid", "seifert", "arc index", "crossing number"):
        assert term not in text, (
            f"{path.name}: domain-specific term {term!r} leaked into a "
            f"general-purpose lens prompt"
        )
    # And it must actually express the circularity/independence focus.
    assert "circular" in text or "tautolog" in text
    assert "independent" in text
