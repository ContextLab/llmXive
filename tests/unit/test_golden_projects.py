"""Tests for the golden + weak project fixtures (spec 015 T072)."""

from __future__ import annotations

import pytest

from llmxive.calibration.domains import ANCHOR_PAPERS
from llmxive.calibration.golden_projects import (
    GOLDEN_PROJECTS,
    GoldenProject,
    all_golden,
    golden_for_field,
    weak_project,
)
from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS


def test_one_golden_per_librarian_field():
    """Every LIBRARIAN_DEFAULT_FIELDS field MUST have exactly one
    golden (non-weak) project. T073's per-domain traversal iterates
    these expecting one per field."""
    golden_fields = {p.field_name for p in GOLDEN_PROJECTS if not p.weak}
    assert golden_fields == set(LIBRARIAN_DEFAULT_FIELDS)


def test_exactly_one_weak_project_exists():
    weak = [p for p in GOLDEN_PROJECTS if p.weak]
    assert len(weak) == 1
    assert weak[0].project_id == "PROJ-999-deliberately-weak"
    assert weak[0].expected_kickback_lens is not None


def test_all_project_ids_are_unique():
    ids = [p.project_id for p in GOLDEN_PROJECTS]
    assert len(ids) == len(set(ids))


def test_all_project_ids_match_schema():
    """Project IDs MUST match PROJ-\\d{3,}-<slug> per the global ID
    schema; mismatched IDs would fail the state-validation gate."""
    import re
    pat = re.compile(r"^PROJ-\d{3,}-[a-z0-9-]+$")
    for p in GOLDEN_PROJECTS:
        assert pat.match(p.project_id), (
            f"project_id {p.project_id!r} doesn't match schema "
            f"(expected PROJ-\\d{{3,}}-<slug>)"
        )


@pytest.mark.parametrize("project", GOLDEN_PROJECTS, ids=lambda p: p.project_id)
def test_idea_md_has_substantive_content(project: GoldenProject):
    """Every idea_md MUST cite its anchor paper (golden only) AND
    state the research question, hypothesis, and methods — the
    minimum the spec panel needs to evaluate downstream."""
    # Even the weak project has a research-question line (it's the
    # CIRCULAR one — the calibration target).
    assert "Research question:" in project.idea_md
    if not project.weak:
        # Golden projects cite their anchor explicitly.
        assert project.anchor.doi in project.idea_md
        assert project.anchor.title in project.idea_md
        # And describe a real method.
        assert "Methods:" in project.idea_md
        assert "Feasibility:" in project.idea_md
        # No placeholder markers in golden projects.
        for marker in ("TODO", "TBD", "FIXME", "<placeholder>"):
            assert marker not in project.idea_md, (
                f"golden {project.project_id!r} has placeholder {marker!r}"
            )


@pytest.mark.parametrize(
    "project",
    [p for p in GOLDEN_PROJECTS if not p.weak],
    ids=lambda p: p.field_name,
)
def test_golden_anchor_matches_field(project: GoldenProject):
    """Every golden project's anchor MUST match its declared field."""
    by_field = {a.field_name: a for a in ANCHOR_PAPERS}
    assert project.anchor == by_field[project.field_name]


def test_weak_project_text_contains_expected_flaw_signals():
    """The weak project's idea_md MUST contain detectable signals for
    the flaws it carries (circular RQ + fabricated data + plan↔tasks
    contradiction) — without these the panel has nothing to flag."""
    weak = weak_project()
    body = weak.idea_md.lower()
    # Circular RQ signal.
    assert "accurate" in body and "because" in body
    # Fabricated-data signal.
    assert "fabricated" in body or "not a real dataset" in body
    # Plan↔tasks contradiction signal.
    assert "contradiction" in body or "contradict" in body


def test_golden_for_field_lookup():
    bio = golden_for_field("biology")
    assert bio.field_name == "biology"
    assert "CRISPR" in bio.title


def test_golden_for_field_raises_on_unknown():
    with pytest.raises(ValueError, match="no golden project for field"):
        golden_for_field("astrology")


def test_all_golden_returns_stable_order():
    a = all_golden()
    b = all_golden()
    assert [p.project_id for p in a] == [p.project_id for p in b]
    # All 10 (9 golden + 1 weak).
    assert len(a) == 10


def test_weak_project_lookup():
    w = weak_project()
    assert w.weak is True
    assert w.expected_kickback_lens == "rq_validity"
