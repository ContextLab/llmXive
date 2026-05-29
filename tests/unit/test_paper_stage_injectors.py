"""Tests for the per-paper-stage injectors authored post-2026-05-29.

Original calibration repro: all 4 paper-track panels (paper_spec /
paper_plan / paper_tasks / paper_implement) were given the same
``nonexistent_citation`` injection whose ``expected_lens`` is
``claim_accuracy``. But ``claim_accuracy`` only exists on
paper_implement's panel — the other 3 panels structurally CAN'T flag
the injection, so they always reported 0/1 caught.

Fix: per-paper-stage injectors that target a lens actually in the
corresponding panel:
  * ``unsupported_claim`` → claims_supported  (paper_spec)
  * ``orphan_plan_section`` → spec_section_coverage  (paper_plan)
  * (paper_tasks reuses ``fr_without_task`` → coverage)
  * ``nonexistent_citation`` → claim_accuracy  (paper_implement only)
"""

from __future__ import annotations

from llmxive.calibration.builder import build_set_for_stage
from llmxive.calibration.injectors import (
    INJECTORS,
    inject_orphan_plan_section,
    inject_unsupported_claim,
)

# --- injector implementations -------------------------------------------


def test_unsupported_claim_appends_a_quantitative_claim_marker():
    seed = (
        "# Spec\n\n## Functional Requirements\n- **FR-001**: System "
        "MUST emit a verdict.\n"
    )
    injection = inject_unsupported_claim(seed)
    # The injection appends rather than replaces, so the original is
    # still parseable.
    assert seed in injection.text
    assert "INJECTED CLAIM" in injection.text
    # Sentinel marker so the maintainer can spot the injection in
    # adjudication.
    assert "75.3%" in injection.text
    assert injection.expected_lens == "claims_supported"
    assert "claims_supported" in injection.description.lower()


def test_orphan_plan_section_adds_unauthorized_section():
    seed = (
        "# Plan\n\n## Methodology\nWe use SGD with momentum.\n"
    )
    injection = inject_orphan_plan_section(seed)
    assert seed in injection.text
    assert "Real-time deployment evaluation" in injection.text
    assert "INJECTED" in injection.text
    assert injection.expected_lens == "spec_section_coverage"


# --- registry integration -----------------------------------------------


def test_both_new_injectors_registered():
    assert "unsupported_claim" in INJECTORS
    assert "orphan_plan_section" in INJECTORS
    fn, lens = INJECTORS["unsupported_claim"]
    assert lens == "claims_supported"
    fn, lens = INJECTORS["orphan_plan_section"]
    assert lens == "spec_section_coverage"


# --- per-stage builder wiring -------------------------------------------


def test_paper_spec_uses_unsupported_claim():
    entries = build_set_for_stage("paper_spec")
    labels = [e.label for e in entries]
    assert "positive" in labels
    assert "negative_unsupported_claim" in labels
    # Crucially: paper_spec must NOT carry nonexistent_citation anymore
    # (it can't flag it; that was the original calibration bug).
    assert "negative_nonexistent_citation" not in labels


def test_paper_plan_uses_orphan_plan_section():
    entries = build_set_for_stage("paper_plan")
    labels = [e.label for e in entries]
    assert "negative_orphan_plan_section" in labels
    assert "negative_nonexistent_citation" not in labels


def test_paper_tasks_uses_fr_without_task_overridden_to_coverage():
    """paper_tasks reuses the existing fr_without_task injector but
    its expected_lens is overridden to 'coverage' (the paper_tasks
    panel includes the 'coverage' lens)."""
    entries = build_set_for_stage("paper_tasks")
    labels = [e.label for e in entries]
    assert "negative_fr_without_task" in labels
    fr_entry = next(e for e in entries if e.label == "negative_fr_without_task")
    assert fr_entry.expected_lens == "coverage"


def test_paper_implement_keeps_nonexistent_citation():
    """paper_implement is the ONLY paper stage that should carry
    nonexistent_citation (its panel includes claim_accuracy)."""
    entries = build_set_for_stage("paper_implement")
    labels = [e.label for e in entries]
    assert "negative_nonexistent_citation" in labels
    nc_entry = next(e for e in entries if e.label == "negative_nonexistent_citation")
    assert nc_entry.expected_lens == "claim_accuracy"


def test_every_paper_stage_expected_lens_matches_its_panel():
    """End-to-end: every per-paper-stage expected_lens MUST be in
    that stage's panel's lens set. Catches the original bug class
    where an injector's expected lens didn't exist on the panel."""
    paper_panel_lenses = {
        "paper_spec": {
            "reader_scenario_coverage", "claims_supported",
            "required_sections_figures", "scope_vs_research",
        },
        "paper_plan": {
            "paper_structure", "spec_section_coverage",
            "plan_constitution_consistency",
        },
        "paper_tasks": {
            "coverage", "ordering", "executability",
            "constraint_preservation",
        },
        "paper_implement": {
            "claim_accuracy", "scientific_evidence",
            "writing_quality", "figure_critic",
        },
    }
    for stage, panel_lenses in paper_panel_lenses.items():
        for entry in build_set_for_stage(stage):
            if entry.expected_lens is None:
                continue  # positives have no expected lens
            assert entry.expected_lens in panel_lenses, (
                f"stage={stage!r} entry={entry.label!r} expects lens "
                f"{entry.expected_lens!r} which is NOT in that "
                f"stage's panel {sorted(panel_lenses)!r} — this is "
                f"the original calibration bug."
            )
