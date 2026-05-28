"""Unit tests for the per-domain calibration anchors (spec 015 T066)."""

from __future__ import annotations

import re

import pytest

from llmxive.calibration.domains import (
    ANCHOR_PAPERS,
    AnchorPaper,
    CalibrationDomain,
    all_domains,
    get_anchor,
    held_out_domain,
)
from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS


def test_one_anchor_per_librarian_default_field():
    """Every field in LIBRARIAN_DEFAULT_FIELDS MUST have exactly one
    anchor (the calibration harness iterates ANCHOR_PAPERS expecting
    coverage of every field)."""
    fields_with_anchors = {a.field_name for a in ANCHOR_PAPERS}
    expected = set(LIBRARIAN_DEFAULT_FIELDS)
    missing = expected - fields_with_anchors
    extra = fields_with_anchors - expected
    assert not missing, f"missing anchors for fields: {missing}"
    assert not extra, f"unexpected anchor fields: {extra}"
    assert len(ANCHOR_PAPERS) == len(LIBRARIAN_DEFAULT_FIELDS)


def test_exactly_one_anchor_is_held_out():
    """The held-out generality test (T069) requires EXACTLY one
    anchor flagged held_out=True. Zero → no generality test possible;
    more than one → ambiguous which field to use."""
    held = [a for a in ANCHOR_PAPERS if a.held_out]
    assert len(held) == 1


def test_held_out_domain_returns_consistent_field_name():
    assert held_out_domain() in {a.field_name for a in ANCHOR_PAPERS}
    # And the returned name's anchor IS the held-out one.
    held_anchor = get_anchor(held_out_domain())
    assert held_anchor.held_out is True


@pytest.mark.parametrize("anchor", ANCHOR_PAPERS, ids=lambda a: a.field_name)
def test_anchor_has_required_fields_populated(anchor: AnchorPaper):
    """Every anchor MUST have title, authors, year, DOI, URL, and
    abstract_summary populated. Missing fields = unusable calibration
    anchor."""
    assert anchor.title.strip()
    assert anchor.authors and all(a.strip() for a in anchor.authors)
    assert 1900 <= anchor.year <= 2025, f"implausible year: {anchor.year}"
    assert anchor.doi.strip()
    assert anchor.url.startswith("http"), (
        f"URL must be http(s); got {anchor.url!r}"
    )
    assert len(anchor.abstract_summary) >= 20  # substantive description


@pytest.mark.parametrize("anchor", ANCHOR_PAPERS, ids=lambda a: a.field_name)
def test_anchor_doi_shape_is_plausible(anchor: AnchorPaper):
    """DOI must match the canonical CrossRef pattern OR the arXiv DOI
    pattern. Catches typos that would break the maintainer's lookup
    step in T068."""
    # CrossRef DOIs start with 10.
    # arXiv DOIs look like 10.48550/arXiv.NNNN.NNNNN
    crossref_re = re.compile(r"^10\.\d{4,9}/")
    assert crossref_re.match(anchor.doi), (
        f"DOI for {anchor.field_name!r} doesn't match `10.NNNN/...`: "
        f"{anchor.doi!r}"
    )


def test_get_anchor_returns_correct_anchor():
    bio = get_anchor("biology")
    assert bio.field_name == "biology"
    assert bio.title.lower().startswith("a programmable")  # Doudna+Charpentier


def test_get_anchor_raises_on_unknown_field():
    with pytest.raises(ValueError, match="no anchor paper for field"):
        get_anchor("astrology")  # not a field


def test_all_domains_returns_one_per_field_in_order():
    domains = all_domains()
    assert len(domains) == len(LIBRARIAN_DEFAULT_FIELDS)
    assert [d.field_name for d in domains] == list(LIBRARIAN_DEFAULT_FIELDS)
    for d in domains:
        assert isinstance(d, CalibrationDomain)
        assert d.anchor.field_name == d.field_name
        # HF-daily + backlog filled in by the driver at calibration time,
        # so they're empty here.
        assert d.hf_daily_sample is None
        assert d.backlog_samples == []


def test_calibration_domain_accepts_driver_provided_samples():
    """The driver fills in hf_daily_sample + backlog_samples at
    calibration time; verify the shape is mutable."""
    d = all_domains()[0]
    d.hf_daily_sample = {
        "title": "Some HF Daily Paper",
        "url": "https://huggingface.co/papers/2024.01.01",
        "abstract": "An abstract.",
    }
    d.backlog_samples = ["projects/PROJ-042-test"]
    assert d.hf_daily_sample["title"] == "Some HF Daily Paper"
    assert d.backlog_samples == ["projects/PROJ-042-test"]
