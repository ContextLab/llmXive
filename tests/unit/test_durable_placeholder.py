"""Spec 020 T016 — durable placeholder + rendered view (C6; FR-007/008, SC-007).

Offline. In the canonical STORED form a VERIFIED claim is a durable ``{{claim:id}}``
placeholder (never the baked value); ``strip_claim_artifacts(preserve_pointers=True)``
keeps it; ``render_view`` substitutes the value for review/publish; and a stored doc
round-trips the loop without any verified value baked into prose (so it is never
re-extracted as a new claim).
"""

from __future__ import annotations

from llmxive.claims.gate import CLAIM_MARKER_PREFIX, strip_claim_artifacts
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.claims.pointer import render, render_view, substitute_pointers, to_pointer


def _verified(raw: str, value: str) -> Claim:
    return Claim(
        claim_id=compute_claim_id(ClaimKind.NUMERIC, raw, ""),
        kind=ClaimKind.NUMERIC, raw_text=raw, canonical=raw, context="",
        artifact_path="a.md", source_type="external", status=ClaimStatus.VERIFIED,
        resolved_value=value, evidence={"source_id": "OEIS:A002863"}, resolver="oeis",
        attempts=1, updated_at="", source_hash=None,
    )


RAW = "There are 27,635 prime knots with 13 crossings."


def test_render_keeps_placeholder_in_canonical_form() -> None:
    claim = _verified(RAW, "9988")
    text = substitute_pointers(RAW, [(RAW, claim.claim_id)])  # {{claim:id}}
    out, report = render(text, {claim.claim_id: claim}, placeholder_verified=True)
    assert out == to_pointer(claim.claim_id)        # durable placeholder, not the value
    assert "9988" not in out and "27,635" not in out  # no value baked into prose
    assert report.blocked is False


def test_legacy_render_still_bakes_value() -> None:
    # Default (placeholder_verified=False) is unchanged — the proven-good behavior.
    claim = _verified(RAW, "9988")
    text = substitute_pointers(RAW, [(RAW, claim.claim_id)])
    out, _ = render(text, {claim.claim_id: claim})
    assert "9988" in out
    assert to_pointer(claim.claim_id) not in out


def test_strip_preserves_durable_pointer() -> None:
    claim = _verified(RAW, "9988")
    stored = f"Intro. {to_pointer(claim.claim_id)} Outro."
    # With preserve_pointers the durable placeholder survives a strip pass.
    assert to_pointer(claim.claim_id) in strip_claim_artifacts(stored, preserve_pointers=True)
    # Default still removes stray pointers (legacy behavior, existing tests).
    assert to_pointer(claim.claim_id) not in strip_claim_artifacts(stored)
    # Transient markers are removed in both modes.
    marked = f"X {CLAIM_MARKER_PREFIX} c_12345678 — status=pending]"
    assert CLAIM_MARKER_PREFIX not in strip_claim_artifacts(marked, preserve_pointers=True)


def test_render_view_substitutes_value() -> None:
    claim = _verified(RAW, "9988")
    stored = to_pointer(claim.claim_id)
    view = render_view(stored, {claim.claim_id: claim})
    assert "9988" in view                       # value substituted for the human view
    assert to_pointer(claim.claim_id) not in view


def test_round_trip_never_bakes_value() -> None:
    # The canonical stored form round-trips: strip(preserve) -> render(placeholder)
    # yields the same placeholder, with no value ever appearing in the stored prose.
    claim = _verified(RAW, "9988")
    stored = to_pointer(claim.claim_id)
    for _ in range(3):
        cleaned = strip_claim_artifacts(stored, preserve_pointers=True)
        rendered, _r = render(cleaned, {claim.claim_id: claim}, placeholder_verified=True)
        assert rendered == to_pointer(claim.claim_id)
        assert "9988" not in rendered
        stored = rendered
