"""Unit tests for the calibration flaw injectors (spec 015 T063).

Verifies each of the 6 injectors:
- Is deterministic (same input → same output).
- Actually mutates the artifact (or no-ops with an honest reason).
- Tags the right expected_lens.
- The registry exposes all 6 with consistent lens metadata.
"""

from __future__ import annotations

from llmxive.calibration.injectors import (
    INJECTORS,
    Injection,
    inject_circular_rq,
    inject_fabricated_data,
    inject_fr_without_task,
    inject_gutted_requirement,
    inject_nonexistent_citation,
    inject_plan_tasks_contradiction,
)

# --- circular RQ ----------------------------------------------------------


def test_circular_rq_rewrites_existing_research_question_line():
    idea = (
        "# Idea\n\n"
        "Research question: Does X cause Y under condition Z?\n\n"
        "Background: Prior work [Smith2020] suggests..."
    )
    out = inject_circular_rq(idea)
    assert isinstance(out, Injection)
    assert out.expected_lens == "rq_validity"
    # The new RQ line is circular.
    assert "accurate because it is accurate" in out.text
    # The original RQ wording is replaced.
    assert "Does X cause Y under condition Z" not in out.text
    # Original kept for diff display.
    assert out.original == idea


def test_circular_rq_prepends_when_no_research_question_line():
    idea = "# Idea\n\nBackground: Prior work."
    out = inject_circular_rq(idea)
    # The first line is now the circular RQ.
    assert out.text.startswith(
        "Research question: Why is the model accurate?"
    )


def test_circular_rq_is_deterministic():
    idea = "Research question: does X cause Y?"
    a = inject_circular_rq(idea)
    b = inject_circular_rq(idea)
    assert a.text == b.text
    assert a.expected_lens == b.expected_lens


# --- FR without task ------------------------------------------------------


def test_fr_without_task_injects_sentinel():
    tasks = "## Tasks\n- T001 [FR-001]: implement X\n"
    out = inject_fr_without_task(tasks)
    assert out.expected_lens == "coverage"
    # Sentinel mentions FR-999 + the missing-task assertion.
    assert "FR-999" in out.text
    # Original tasks still present.
    assert "T001 [FR-001]" in out.text


def test_fr_without_task_does_not_drop_any_existing_task():
    tasks = (
        "## Tasks\n"
        "- T001 [FR-001]: A\n- T002 [FR-002]: B\n- T003 [FR-003]: C\n"
    )
    out = inject_fr_without_task(tasks)
    for tid in ("T001", "T002", "T003"):
        assert tid in out.text


# --- gutted requirement ---------------------------------------------------


def test_gutted_requirement_weakens_must_to_should():
    tasks = (
        "## Tasks\n- T001: The system MUST validate input. "
        "Each test SHALL exist for every FR-001 case.\n"
    )
    out = inject_gutted_requirement(tasks)
    assert out.expected_lens == "constraint_preservation"
    # MUST replaced with should.
    assert "MUST" not in out.text
    assert "should" in out.text
    # SHALL replaced with may.
    assert "SHALL" not in out.text
    # Description mentions the number of weakenings.
    assert "markers weakened" in out.description


def test_gutted_requirement_is_honest_about_no_op():
    """If there's nothing to weaken, the injector says so explicitly
    rather than silently emitting the unmodified text."""
    tasks = "## Tasks\n- T001: implement the thing.\n"  # no strength markers
    out = inject_gutted_requirement(tasks)
    assert "[INJECTION NO-OP]" in out.description
    # text unchanged on no-op
    assert out.text == tasks


# --- fabricated data ------------------------------------------------------


def test_fabricated_data_replaces_existing_dataset_id():
    plan = (
        "# Plan\n## Data\n- Primary dataset: OpenNeuro ds002800 "
        "(structural MRI)."
    )
    out = inject_fabricated_data(plan)
    assert out.expected_lens == "data_resources"
    assert "ds999999" in out.text
    assert "FABRICATED" in out.text
    # The original ds002800 is replaced (not duplicated).
    assert "ds002800" not in out.text


def test_fabricated_data_appends_datasets_section_when_absent():
    plan = "# Plan\n\nMethodology: regression analysis."
    out = inject_fabricated_data(plan)
    assert "## Datasets" in out.text
    assert "ds999999" in out.text


# --- nonexistent citation -------------------------------------------------


def test_nonexistent_citation_injects_bracketed_marker():
    paper = (
        "Our experiments show robust effects. We replicate the finding "
        "across three samples."
    )
    out = inject_nonexistent_citation(paper)
    assert out.expected_lens == "claim_accuracy"
    assert "[FabricatedAuthor2024]" in out.text


def test_nonexistent_citation_appends_when_no_period():
    """If the paper text has no period, the injector appends instead of
    splitting mid-sentence."""
    paper = "Abstract without any periods just a fragment"
    out = inject_nonexistent_citation(paper)
    assert "[FabricatedAuthor2024]" in out.text


# --- plan↔tasks contradiction --------------------------------------------


def test_plan_tasks_contradiction_appends_assertion():
    plan = "# Plan\n## Methodology\nUnsupervised clustering of samples."
    out = inject_plan_tasks_contradiction(plan)
    assert out.expected_lens == "plan_consistency"
    assert "supervised regression" in out.text
    assert "INJECTED METHODOLOGY ASSERTION" in out.text


# --- registry contract ----------------------------------------------------


def test_registry_exposes_all_six_injectors():
    assert len(INJECTORS) == 6
    expected = {
        "circular_rq", "fr_without_task", "gutted_requirement",
        "fabricated_data", "nonexistent_citation", "plan_tasks_contradiction",
    }
    assert set(INJECTORS) == expected


def test_registry_lens_metadata_matches_each_injector_output():
    """The registry's recorded expected_lens MUST match what the injector
    actually emits — a drift here would silently misattribute calibration
    misses to the wrong lens."""
    samples = {
        "circular_rq": "Research question: x",
        "fr_without_task": "- T001 [FR-001]: do X",
        "gutted_requirement": "The system MUST do X.",
        "fabricated_data": "## Data\n- OpenNeuro ds002800",
        "nonexistent_citation": "We show X. Therefore Y.",
        "plan_tasks_contradiction": "## Methodology\nclustering",
    }
    for name, (fn, registered_lens) in INJECTORS.items():
        out = fn(samples[name])  # type: ignore[operator]
        assert isinstance(out, Injection)
        assert out.expected_lens == registered_lens, (
            f"Injector {name!r}: registry says {registered_lens!r} but "
            f"emitter returned {out.expected_lens!r}"
        )
