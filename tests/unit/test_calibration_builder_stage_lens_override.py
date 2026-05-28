"""Tests for the per-stage expected-lens override in the calibration
builder.

Real calibration run 26592405739 surfaced a stage↔lens mapping bug: the
``gutted_requirement`` injector's default ``expected_lens`` is
``constraint_preservation`` (a TASKS-stage lens), but the injector was
also registered for the SPEC stage. SPEC's panel doesn't run
``constraint_preservation`` (its lenses are ``requirements_coverage`` /
``internal_consistency`` / ``testability`` / ``scope``), so the
"missed" verdict was a false negative caused by the calibration set
itself, not by the panel's prompts.

The fix: ``_STAGE_INJECTORS`` entries are now
``(injector_name, expected_lens_override | None)`` tuples; the builder
uses the override when set, else falls back to the injector's default
lens.
"""

from __future__ import annotations

from llmxive.calibration.builder import build_set_for_stage


def test_spec_gutted_requirement_uses_requirements_coverage_lens():
    """On the SPEC stage, ``gutted_requirement`` MUST be expected to
    surface under ``requirements_coverage`` (the lens that's actually
    in the spec-stage panel), NOT ``constraint_preservation`` (which is
    a tasks-stage lens)."""
    entries = build_set_for_stage("spec")
    negative = next(
        e for e in entries if e.label == "negative_gutted_requirement"
    )
    assert negative.expected_lens == "requirements_coverage", (
        "Spec stage's gutted_requirement injection must be expected to "
        "fire under requirements_coverage (a real spec-panel lens), not "
        "constraint_preservation (which exists only on the tasks panel)."
    )


def test_tasks_gutted_requirement_keeps_constraint_preservation_lens():
    """On the TASKS stage, the injector keeps its default
    ``constraint_preservation`` lens (the real tasks-panel lens)."""
    entries = build_set_for_stage("tasks")
    negative = next(
        e for e in entries if e.label == "negative_gutted_requirement"
    )
    assert negative.expected_lens == "constraint_preservation"


def test_every_negative_expected_lens_is_real_for_its_stage():
    """Regression: every (stage, injector) pair must produce an
    ``expected_lens`` that the corresponding stage's reviewspec
    actually defines. This locks in the per-stage override invariant.
    """
    # Stage → set of valid lens names.
    stage_lenses = {
        "idea": {"rq_validity", "novelty", "feasibility", "idea_quality"},
        "spec": {
            "requirements_coverage", "internal_consistency",
            "testability", "scope",
        },
        "plan": {
            "methodology", "spec_coverage", "data_resources",
            "plan_consistency",
        },
        "tasks": {
            "coverage", "ordering", "executability",
            "constraint_preservation",
        },
        # The paper stage is a composite calibration set covering
        # paper-spec / paper-plan / paper-tasks / paper-implement panels.
        # For now its only injector is ``nonexistent_citation`` whose
        # lens (``claim_accuracy``) lives on the paper_implement panel.
        "paper": {"claim_accuracy"},
    }
    for stage, lenses in stage_lenses.items():
        entries = build_set_for_stage(stage)
        for e in entries:
            if e.expected_lens is None:
                # Positives have no expected lens.
                continue
            assert e.expected_lens in lenses, (
                f"stage={stage!r} entry={e.label!r} expects lens "
                f"{e.expected_lens!r} which is NOT in that stage's "
                f"valid lenses {sorted(lenses)!r}"
            )


def test_positive_entries_have_no_expected_lens():
    """Positives are clean artifacts — they should produce no concerns,
    so they have no ``expected_lens``."""
    for stage in ("idea", "spec", "plan", "tasks", "paper"):
        entries = build_set_for_stage(stage)
        positives = [e for e in entries if e.label == "positive"]
        assert len(positives) == 1
        assert positives[0].expected_lens is None
