"""Tests for the golden + weak project fixtures (spec 015 T072).

Covers the three-shape mix the calibration set uses:
- 3 follow-up (cites anchor paper explicitly)
- 3 theory/simulation (no external data)
- 3 public-data (cites an open-access dataset URL)
- 1 weak control (subtly flawed; no calibration markers in title/body)
"""

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
    (non-weak) golden project."""
    golden_fields = {p.field_name for p in GOLDEN_PROJECTS if not p.weak}
    assert golden_fields == set(LIBRARIAN_DEFAULT_FIELDS)


def test_three_shapes_are_evenly_distributed_among_goldens():
    """The 9 goldens are 3 follow-up + 3 theory + 3 public-data so the
    panel exercises a realistic mix."""
    counts: dict[str, int] = {}
    for p in GOLDEN_PROJECTS:
        if p.weak:
            continue
        counts[p.shape] = counts.get(p.shape, 0) + 1
    assert counts.get("followup", 0) == 3
    assert counts.get("theory", 0) == 3
    assert counts.get("data", 0) == 3


def test_exactly_one_weak_project_exists():
    weak = [p for p in GOLDEN_PROJECTS if p.weak]
    assert len(weak) == 1
    assert weak[0].expected_kickback_lens is not None


def test_weak_project_id_does_not_leak_calibration_intent():
    """The weak project's id, slug, and title MUST NOT contain
    calibration-tagging words like 'weak', 'calibration', 'control',
    'deliberately'. The panel reads these — leakage lets it game the
    judgement."""
    weak = weak_project()
    forbidden = ("weak", "calibration", "control", "deliberately", "negative")
    blob = f"{weak.project_id} {weak.slug} {weak.title}".lower()
    for word in forbidden:
        assert word not in blob, (
            f"weak project's identity leaks calibration intent via "
            f"{word!r}: {blob!r}"
        )


def test_all_project_ids_are_unique():
    ids = [p.project_id for p in GOLDEN_PROJECTS]
    assert len(ids) == len(set(ids))


def test_all_project_ids_match_schema():
    """Project IDs MUST match PROJ-\\d{3,}-<slug> per the global ID schema."""
    import re
    pat = re.compile(r"^PROJ-\d{3,}-[a-z0-9-]+$")
    for p in GOLDEN_PROJECTS:
        assert pat.match(p.project_id), (
            f"project_id {p.project_id!r} doesn't match schema "
            f"(expected PROJ-\\d{{3,}}-<slug>)"
        )


@pytest.mark.parametrize("project", GOLDEN_PROJECTS, ids=lambda p: p.project_id)
def test_idea_md_has_minimum_required_content(project: GoldenProject):
    """Every idea_md (golden or weak) MUST have the minimum
    research-question + methods content."""
    assert "Research question:" in project.idea_md
    assert "Methods:" in project.idea_md
    assert "Feasibility:" in project.idea_md
    # No placeholder markers anywhere.
    for marker in ("TODO", "TBD", "FIXME", "<placeholder>"):
        assert marker not in project.idea_md, (
            f"{project.project_id!r} has placeholder {marker!r}"
        )


@pytest.mark.parametrize(
    "project",
    [p for p in GOLDEN_PROJECTS if not p.weak and p.shape == "followup"],
    ids=lambda p: p.project_id,
)
def test_followup_shape_cites_anchor(project: GoldenProject):
    """Follow-up projects MUST cite their anchor's DOI + title."""
    assert project.anchor.doi in project.idea_md
    assert project.anchor.title in project.idea_md


@pytest.mark.parametrize(
    "project",
    [p for p in GOLDEN_PROJECTS if not p.weak and p.shape == "theory"],
    ids=lambda p: p.project_id,
)
def test_theory_shape_does_not_require_external_data(project: GoldenProject):
    """Theory/simulation projects MUST flag they need no external data."""
    body = project.idea_md.lower()
    # The shape helper inserts a "no external data" sentence; verify.
    assert "no external data" in body or "theoretical" in body


@pytest.mark.parametrize(
    "project",
    [p for p in GOLDEN_PROJECTS if not p.weak and p.shape == "data"],
    ids=lambda p: p.project_id,
)
def test_data_shape_cites_a_data_url(project: GoldenProject):
    """Public-data projects MUST cite an https:// URL for the source."""
    assert "https://" in project.idea_md
    # And label the source explicitly (the data_idea helper inserts
    # "Data source: ... (URL)").
    assert "Data source:" in project.idea_md


@pytest.mark.parametrize(
    "project",
    [p for p in GOLDEN_PROJECTS if not p.weak],
    ids=lambda p: p.field_name,
)
def test_golden_anchor_matches_field(project: GoldenProject):
    """Every golden project's anchor MUST match its declared field."""
    by_field = {a.field_name: a for a in ANCHOR_PAPERS}
    assert project.anchor == by_field[project.field_name]


def test_weak_project_carries_hidden_flaws():
    """The weak project's body MUST contain detectable signals for at
    least 2 of the 3 hidden flaws (circular RQ + fabricated dataset
    + methodology looseness) — without these the panel has nothing to
    flag and the calibration loses its signal.

    The signals are detectable to a CAREFUL reader; they are NOT
    obvious to a panel scanning for "calibration" / "weak" markers.
    """
    weak = weak_project()
    body = weak.idea_md.lower()

    # Circular-RQ signal: the body says some variant of "detectable
    # because <same word as 'detectable' translated to 'signatures' /
    # 'reveal'>" — the self-verifying structure.
    has_circular = (
        "detectable" in body
        and ("signature" in body or "reveal" in body)
        and "because" in body
    )

    # Fabricated-dataset signal: a HuggingFace-shaped reference that
    # doesn't actually exist — the calibration target.
    has_fake_data = "spurcor-research/spurcorbench" in body

    flaws_found = sum([has_circular, has_fake_data])
    assert flaws_found >= 2, (
        f"weak project body must contain at least 2 of the 3 hidden "
        f"flaws; found {flaws_found}. circular={has_circular} "
        f"fake_data={has_fake_data}"
    )


def test_golden_for_field_lookup():
    """Look up biology — should be the TCGA tumor-suppressor data project."""
    bio = golden_for_field("biology")
    assert bio.field_name == "biology"
    assert bio.shape == "data"
    assert "TCGA" in bio.idea_md or "Genomic Data Commons" in bio.idea_md


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
