"""T003 — unit tests for claims/models.py (spec 016 foundational)."""

from __future__ import annotations

import pytest

from llmxive.claims.models import (
    Claim,
    ClaimKind,
    ClaimStatus,
    Verdict,
    compute_claim_id,
)


class TestClaimKind:
    def test_all_seven_members(self):
        names = {m.name for m in ClaimKind}
        assert names == {"NUMERIC", "MAGNITUDE", "RELATIONAL", "CAUSAL", "ENTITY_FACT", "CITATION", "RESULT"}

    def test_string_value_lowercase(self):
        assert ClaimKind.NUMERIC == "numeric"
        assert ClaimKind.RESULT == "result"


class TestClaimStatus:
    def test_all_five_members(self):
        names = {m.name for m in ClaimStatus}
        assert names == {"PENDING", "VERIFIED", "REFUTED", "NOT_ENOUGH_INFO", "UNRESOLVABLE"}

    def test_string_value_lowercase(self):
        assert ClaimStatus.PENDING == "pending"
        assert ClaimStatus.NOT_ENOUGH_INFO == "not_enough_info"


class TestVerdict:
    def test_construction(self):
        v = Verdict(status=ClaimStatus.VERIFIED, value="42", evidence={"source": "x"}, resolver="librarian")
        assert v.status == ClaimStatus.VERIFIED
        assert v.value == "42"
        assert v.evidence == {"source": "x"}
        assert v.resolver == "librarian"

    def test_frozen(self):
        v = Verdict(status=ClaimStatus.PENDING, value=None, evidence=None, resolver=None)
        with pytest.raises((AttributeError, TypeError)):
            v.status = ClaimStatus.VERIFIED  # type: ignore[misc]

    def test_nullable_fields(self):
        v = Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None, evidence=None, resolver=None)
        assert v.value is None
        assert v.evidence is None
        assert v.resolver is None


class TestComputeClaimId:
    def test_stable_deterministic(self):
        id1 = compute_claim_id(ClaimKind.NUMERIC, "accuracy=0.95", "our model achieved")
        id2 = compute_claim_id(ClaimKind.NUMERIC, "accuracy=0.95", "our model achieved")
        assert id1 == id2

    def test_starts_with_c_underscore(self):
        cid = compute_claim_id(ClaimKind.CITATION, "doi:10.1234/x", "cited in intro")
        assert cid.startswith("c_")
        assert len(cid) == 10  # "c_" + 8 hex chars

    def test_hex_chars_only_after_prefix(self):
        cid = compute_claim_id(ClaimKind.RESULT, "metric=99", "we observed")
        hex_part = cid[2:]
        assert len(hex_part) == 8
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_differs_on_kind_change(self):
        id1 = compute_claim_id(ClaimKind.NUMERIC, "x=1", "ctx")
        id2 = compute_claim_id(ClaimKind.MAGNITUDE, "x=1", "ctx")
        assert id1 != id2

    def test_differs_on_canonical_change(self):
        id1 = compute_claim_id(ClaimKind.NUMERIC, "x=1", "ctx")
        id2 = compute_claim_id(ClaimKind.NUMERIC, "x=2", "ctx")
        assert id1 != id2

    def test_differs_on_context_change(self):
        id1 = compute_claim_id(ClaimKind.NUMERIC, "x=1", "ctx_a")
        id2 = compute_claim_id(ClaimKind.NUMERIC, "x=1", "ctx_b")
        assert id1 != id2


class TestClaim:
    def _make(self, **overrides) -> Claim:
        defaults = dict(
            claim_id="c_deadbeef",
            kind=ClaimKind.NUMERIC,
            raw_text="accuracy was 95%",
            canonical="accuracy=0.95",
            context="our model achieved 95%",
            artifact_path="projects/PROJ-001/specs/spec.md",
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-05-30T00:00:00Z",
        )
        defaults.update(overrides)
        return Claim(**defaults)

    def test_construction(self):
        c = self._make()
        assert c.claim_id == "c_deadbeef"
        assert c.kind == ClaimKind.NUMERIC
        assert c.status == ClaimStatus.PENDING
        assert c.attempts == 0

    def test_mutable(self):
        c = self._make()
        c.status = ClaimStatus.VERIFIED
        assert c.status == ClaimStatus.VERIFIED

    def test_all_fields_accessible(self):
        c = self._make(resolved_value="0.95", evidence={"url": "x"}, resolver="grounding")
        assert c.resolved_value == "0.95"
        assert c.evidence == {"url": "x"}
        assert c.resolver == "grounding"


# --- Claim identity must be idempotent under re-extraction (the ID-churn bug) ---
#
# `context` is the LLM's own free-text quote of the surrounding artifact text. The
# claims layer INJECTS `[UNRESOLVED-CLAIM: <id> - ...]` markers back INTO that same
# artifact, so on the next tick the quoted context contains the marker minted on the
# previous tick -> a different hash -> a NEW claim id for the SAME claim. A
# self-referential feedback loop: the registry accumulated 20,272 entries for only
# 13,894 distinct canonical claims (one claim seen under 59 ids), the cache never
# hit, and every claim was re-resolved from scratch every tick. Identity must ignore
# the markers the layer itself stamps.

def test_claim_id_ignores_injected_claim_markers() -> None:
    from llmxive.claims.models import ClaimKind, compute_claim_id

    clean = "the audit reports precision >= 85% on the held-out set"
    marked = (
        "the audit reports precision >= 85% "
        "[UNRESOLVED-CLAIM: c_b60fadb6 — status=not_enough_info] on the held-out set"
    )
    assert compute_claim_id(ClaimKind.NUMERIC, "precision >= 85%", clean) == compute_claim_id(
        ClaimKind.NUMERIC, "precision >= 85%", marked
    )


def test_claim_id_ignores_claim_pointers_and_whitespace() -> None:
    from llmxive.claims.models import ClaimKind, compute_claim_id

    a = compute_claim_id(ClaimKind.NUMERIC, "N >= 20", "the set contains {{claim:c_44abad1e}} items")
    b = compute_claim_id(ClaimKind.NUMERIC, "N >= 20", "the  set contains   items")
    assert a == b


def test_claim_id_still_distinguishes_genuinely_different_context() -> None:
    from llmxive.claims.models import ClaimKind, compute_claim_id

    a = compute_claim_id(ClaimKind.NUMERIC, "p < 0.05", "reported for the ablation study")
    b = compute_claim_id(ClaimKind.NUMERIC, "p < 0.05", "reported for the main experiment")
    assert a != b
