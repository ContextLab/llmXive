"""Spec 020 T015 — value-independent fill cache key (C7; FR-012, strong form).

Offline. The fill verdict key is keyed on the value-EXCLUDED ``subject_key``, so:
- the SAME claim keyed before resolution (value=None) and after (value set) shares
  one entry (the verdict cached during resolution is found next round);
- two *different asserted values* of the SAME subject ("49 …" vs "9,988 …") share
  one entry — the cached verdict carries the subject's correct value;
- rephrasings of the same fact share; genuinely distinct subjects still differ.

This relies on ``pointer.asserted_value`` robustly separating the answer from
qualifier numbers (incl. comma-less prose like "… 13 is 27635").
"""

from __future__ import annotations

from dataclasses import replace

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.service import _cache_key_parts


def _claim(raw: str, *, value: str | None = None) -> Claim:
    return Claim(
        claim_id=compute_claim_id(ClaimKind.NUMERIC, raw, ""),
        kind=ClaimKind.NUMERIC, raw_text=raw, canonical=raw, context="",
        artifact_path="a.md", source_type="external", status=ClaimStatus.PENDING,
        resolved_value=value, evidence=None, resolver=None, attempts=0, updated_at="",
    )


def test_key_independent_of_resolved_value() -> None:
    # Same claim, before vs after resolution → SAME key (FR-012 core).
    pending = _claim("There are 9,988 prime knots with 13 crossings.", value=None)
    verified = replace(pending, status=ClaimStatus.VERIFIED, resolved_value="9988")
    assert _cache_key_parts(pending) == _cache_key_parts(verified)
    # And the asserted value is not a key component at all.
    assert _cache_key_parts(pending)[2] is None


def test_rephrasings_of_same_fact_still_share_key() -> None:
    # No regression of the existing rephrase-robustness requirement.
    c1 = _claim("There are 27,635 prime knots with 13 crossings.")
    c2 = _claim("The number of prime knots at crossing number 13 is 27,635.")
    assert _cache_key_parts(c1) == _cache_key_parts(c2)


def test_different_asserted_values_same_subject_share_key() -> None:
    # FR-012 strong form: a wrong "49" and the correct "9,988" for the SAME subject
    # (prime knots at 13 crossings) MUST share the cache entry — the verdict carries
    # the subject's correct value, which then corrects either phrasing.
    wrong = _claim("There are 49 prime knots at 13 crossings.")
    right = _claim("There are 9,988 prime knots at 13 crossings.")
    assert _cache_key_parts(wrong) == _cache_key_parts(right)


def test_comma_less_answer_collides_with_grouped() -> None:
    # The disambiguation fix: a comma-less answer ("… 13 is 27635") keys identically
    # to the thousands-grouped phrasing of the same fact.
    grouped = _claim("There are 27,635 prime knots at 13 crossings.")
    commaless = _claim("The number of prime knots at crossing number 13 is 27635.")
    assert _cache_key_parts(grouped) == _cache_key_parts(commaless)


def test_distinct_subjects_still_differ() -> None:
    # 12 vs 13 crossings are different facts → different keys (no false collision).
    c1 = _claim("There are 9,988 prime knots with 12 crossings.")
    c2 = _claim("There are 27,635 prime knots with 13 crossings.")
    assert _cache_key_parts(c1) != _cache_key_parts(c2)
