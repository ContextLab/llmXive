"""Integration: subject-keyed VERIFIED reuse in ``process_document`` (FR-015).

A reviser REPHRASE of an already-verified fact yields a NEW ``claim_id`` (the id
is a hash of the raw text), so the ``claim_id``-keyed reuse in
``resolve_registered_claims`` misses it and the fact is re-resolved from scratch
every convergence round. ``process_document`` step 2 now carries a prior
VERIFIED claim's value/evidence onto a fresh claim with the SAME
``(kind, subject_key)`` so the resolve step reuses it.

This is VALUE-IDENTICAL — resolution is by subject, so re-resolving would yield
the same value — and only triggers for a keyword-set-preserving rephrase (the
subject_key is the sorted, singularized content-word set + qualifier numbers,
asserted value excluded). The test proves reuse (not re-resolution) by asserting
the rephrase claim carries the seed twin's EXACT evidence dict, which only a copy
— never a fresh resolution — would produce.

Real filesystem, deterministic extraction backend, no model mocks.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.claims.canonical import subject_key
from llmxive.claims.classify import classify
from llmxive.claims.models import Claim, ClaimStatus, compute_claim_id
from llmxive.state import claims as _claim_store

# Same fact, two phrasings with the SAME content-word set (reordered) → identical
# subject_key but distinct claim_id (different raw text).
_VERIFIED = (
    "The number of prime knots at crossing number 13 is 9,988 "
    "(sequence A002863 in the OEIS)."
)
_REPHRASE = (
    "At crossing number 13, the number of prime knots is 9,988 "
    "(sequence A002863 in the OEIS)."
)

_SEED_EVIDENCE = {
    "filled": True,
    "fill": {
        "value": "9988",
        "source_id": "A002863",
        "url": "https://oeis.org/A002863",
        "quote": "... 2176, 9988, 46972 ... (sequence A002863 in the OEIS).",
        "channel": "oeis",
        "conflicts": [],
    },
}


class _ExtractsRephraseBackend:
    """Deterministic backend that extracts ONLY the rephrase as a single claim.
    If the resolve step were (wrongly) invoked for it, the canned extraction YAML
    is not a resolver verdict, so the claim could never become VERIFIED=9988 by
    that path — VERIFIED=9988 therefore proves the subject-keyed reuse fired."""

    def chat(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        yaml_doc = (
            "claims:\n"
            f"  - claim_text: '{_REPHRASE}'\n"
            f"    canonical: '{_REPHRASE}'\n"
            "    context: ''\n"
        )

        class _R:
            text = yaml_doc

        return _R()


def _seed_verified_twin(project_id: str, repo_root: Path) -> Claim:
    kind = classify(_VERIFIED, _VERIFIED)
    claim = Claim(
        claim_id=compute_claim_id(kind, _VERIFIED, ""),
        kind=kind,
        raw_text=_VERIFIED,
        canonical=_VERIFIED,
        context="",
        artifact_path=f"projects/{project_id}/specs/spec.md",
        source_type="external",
        status=ClaimStatus.VERIFIED,
        resolved_value="9988",
        evidence=_SEED_EVIDENCE,
        resolver="fill",
        attempts=1,
        updated_at="2026-06-02T00:00:00Z",
        source_hash="seedhash-abc123",
    )
    _claim_store.upsert(project_id, claim, repo_root=repo_root)
    return claim


def test_rephrased_claim_reuses_verified_subject_twin(tmp_path: Path) -> None:
    from llmxive.claims.service import process_document

    project_id = "PROJ-REUSE-1"
    (tmp_path / "state" / "claims").mkdir(parents=True, exist_ok=True)
    twin = _seed_verified_twin(project_id, tmp_path)

    # Precondition (self-validating): the rephrase is a genuine REPHRASE — a
    # different claim_id but the SAME (kind, subject_key) as the seed twin.
    rephrase_kind = classify(_REPHRASE, _REPHRASE)
    rephrase_id = compute_claim_id(rephrase_kind, _REPHRASE, "")
    assert rephrase_id != twin.claim_id
    twin_probe = Claim(
        claim_id=rephrase_id, kind=rephrase_kind, raw_text=_REPHRASE,
        canonical=_REPHRASE, context="", artifact_path="x", source_type="external",
        status=ClaimStatus.PENDING, resolved_value=None, evidence=None,
        resolver=None, attempts=0, updated_at="2026-06-02T00:00:00Z",
    )
    assert subject_key(twin_probe) == subject_key(twin), "rephrase must share subject_key"

    doc = "# Spec\n\n" + _REPHRASE + "\n"
    _rendered, claims, _gate = process_document(
        doc,
        artifact_path=f"projects/{project_id}/specs/001/spec.md",
        project_id=project_id,
        backend=_ExtractsRephraseBackend(),
        model=None,
        repo_root=tmp_path,
    )

    # The rephrase claim came back VERIFIED=9988 by REUSING the twin — proven by
    # the EXACT seed evidence dict (a fresh resolution could not reproduce it).
    matched = [c for c in claims if c.claim_id == rephrase_id]
    assert matched, "the rephrase claim should be among the resolved claims"
    rc = matched[0]
    assert rc.status == ClaimStatus.VERIFIED
    assert rc.resolved_value == "9988"
    assert rc.evidence == _SEED_EVIDENCE  # carried verbatim → reuse, not re-resolve
    assert rc.source_hash == "seedhash-abc123"


def test_no_verified_twin_is_byte_identical_behavior(tmp_path: Path) -> None:
    """Pure strengthening: with no prior VERIFIED subject-twin, the new claim is
    registered unchanged (PENDING) — the reuse never fires."""
    from llmxive.claims.service import process_document

    project_id = "PROJ-REUSE-2"
    (tmp_path / "state" / "claims").mkdir(parents=True, exist_ok=True)

    doc = "# Spec\n\n" + _REPHRASE + "\n"
    _rendered, claims, _gate = process_document(
        doc,
        artifact_path=f"projects/{project_id}/specs/001/spec.md",
        project_id=project_id,
        backend=_ExtractsRephraseBackend(),
        model=None,
        repo_root=tmp_path,
    )
    # No twin → the claim is NOT pre-verified from a twin (it is resolved via the
    # offline path, which cannot reach OEIS here → not VERIFIED=9988-by-reuse).
    rephrase_id = compute_claim_id(classify(_REPHRASE, _REPHRASE), _REPHRASE, "")
    matched = [c for c in claims if c.claim_id == rephrase_id]
    assert matched
    assert matched[0].evidence != _SEED_EVIDENCE  # never carried a twin's evidence
