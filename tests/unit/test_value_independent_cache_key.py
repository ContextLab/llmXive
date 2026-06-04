"""Spec 020 T015 — fill cache key does not depend on the resolved value (C7; FR-012).

Offline. The maintainer's concrete concern: ``_cache_key_parts`` included
``resolved_value``, so the SAME claim keyed differently before resolution
(value=None) vs after (value set) — the verdict cached during resolution was
never found next round, forcing a fresh fill. The key now drops ``resolved_value``
so the pre- and post-resolution lookups of one fact share the entry, while
rephrasings still share and distinct facts still differ.

(The stronger "two *different asserted values* of the same subject share a key"
is intentionally NOT keyed here — it would need hardening the shared
``_asserted_value`` primitive; the practical waffling is closed by the subject-key
freeze + the git-tracked frozen store. See ``_cache_key_parts`` docstring.)
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


def test_distinct_subjects_still_differ() -> None:
    # 12 vs 13 crossings are different facts → different keys (no false collision).
    c1 = _claim("There are 9,988 prime knots with 12 crossings.")
    c2 = _claim("There are 27,635 prime knots with 13 crossings.")
    assert _cache_key_parts(c1) != _cache_key_parts(c2)
