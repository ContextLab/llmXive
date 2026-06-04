"""Spec 020 T014 — frozen, value-independent claim cache (C4/C5; FR-009/010/011).

Offline. A VERIFIED record is immutable and value-independent: a rephrased twin
adopts the frozen value with NO call to ``resolve()``; a transient resolver
failure never re-opens it; a genuinely distinct subject does NOT collide.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from llmxive.claims import service as svc
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.state import claims as store


def _claim(raw: str, *, status: ClaimStatus, value: str | None,
           kind: ClaimKind = ClaimKind.NUMERIC) -> Claim:
    return Claim(
        claim_id=compute_claim_id(kind, raw, ""),
        kind=kind, raw_text=raw, canonical=raw, context="",
        artifact_path="projects/PROJ-x/specs/plan.md", source_type="external",
        status=status, resolved_value=value, evidence={"source_id": "OEIS:A002863"},
        resolver="oeis", attempts=1, updated_at="2026-06-04T00:00:00Z",
        source_hash=None,
    )


def test_load_verified_by_subject_indexes_only_verified(tmp_path: Path) -> None:
    store.upsert("PROJ-x", _claim("9,988 prime knots at 13 crossings",
                                  status=ClaimStatus.VERIFIED, value="9988"),
                 repo_root=tmp_path)
    store.upsert("PROJ-x", _claim("some pending knot fact at 7 crossings",
                                  status=ClaimStatus.PENDING, value=None),
                 repo_root=tmp_path)
    idx = store.load_verified_by_subject("PROJ-x", repo_root=tmp_path)
    keys = {sk for (_kind, sk) in idx}
    assert any("knot" in k and "13" in k for k in keys)
    assert all(c.status == ClaimStatus.VERIFIED for c in idx.values())


def test_rephrased_twin_adopts_frozen_value_no_resolve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A VERIFIED record exists; a PENDING rephrasing of the SAME fact is resolved.
    store.upsert("PROJ-x", _claim("9,988 prime knots at 13 crossings",
                                  status=ClaimStatus.VERIFIED, value="9988"),
                 repo_root=tmp_path)
    rephrase = _claim("at 13 crossings there are 27,635 prime knots",
                      status=ClaimStatus.PENDING, value=None)
    store.upsert("PROJ-x", rephrase, repo_root=tmp_path)

    def _boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("resolve() called on a fact with a frozen twin (FR-011)")

    monkeypatch.setattr(svc, "resolve", _boom)
    out = svc.resolve_registered_claims(
        [rephrase], project_id="PROJ-x", backend=None, model=None, repo_root=tmp_path,
    )
    assert out[0].status == ClaimStatus.VERIFIED
    assert out[0].resolved_value == "9988"  # frozen value, not re-resolved


def test_transient_failure_does_not_reopen_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The same claim_id is VERIFIED in the registry; a later round must NOT
    # re-resolve it even if the resolver would now transiently fail.
    verified = _claim("9,988 prime knots at 13 crossings",
                      status=ClaimStatus.VERIFIED, value="9988")
    store.upsert("PROJ-x", verified, repo_root=tmp_path)

    def _boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("resolve() re-opened a VERIFIED record (FR-011)")

    monkeypatch.setattr(svc, "resolve", _boom)
    out = svc.resolve_registered_claims(
        [verified], project_id="PROJ-x", backend=None, model=None, repo_root=tmp_path,
    )
    assert out[0].resolved_value == "9988"


def test_distinct_subject_does_not_collide(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # FR-009 edge case: a different subject (12 crossings, not 13) must NOT be
    # served the frozen 13-crossing value — the freeze must not collapse subjects.
    store.upsert("PROJ-x", _claim("9,988 prime knots at 13 crossings",
                                  status=ClaimStatus.VERIFIED, value="9988"),
                 repo_root=tmp_path)
    other = _claim("the number of prime knots at 12 crossings",
                   status=ClaimStatus.PENDING, value=None)

    captured: list[str] = []

    def _resolve(claim: Claim, **k: Any) -> Any:
        captured.append(claim.canonical)
        from llmxive.claims.models import Verdict
        return Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence=None, resolver="x")

    monkeypatch.setattr(svc, "resolve", _resolve)
    out = svc.resolve_registered_claims(
        [other], project_id="PROJ-x", backend=None, model=None, repo_root=tmp_path,
    )
    # The distinct subject was actually resolved (not adopted) and did NOT inherit 9988.
    assert captured == ["the number of prime knots at 12 crossings"]
    assert out[0].resolved_value != "9988"
