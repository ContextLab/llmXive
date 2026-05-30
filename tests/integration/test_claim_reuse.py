"""T034 (US4) — verified-claim reuse + FR-015 invalidation.

Real registry + real signed receipts, no mocks. Where a "resolver was not
re-invoked" assertion is needed, the REAL ``resolve`` function is wrapped by a
counter (it still runs when called) — never replaced by a fake resolver.
"""

from __future__ import annotations

import glob
import os

import llmxive.claims.service as svc
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.results import harness
from llmxive.state import claims as claim_store


def _count_wrap_resolve(monkeypatch):
    """Wrap the REAL svc.resolve with an invocation counter (not a mock)."""
    calls: list[int] = []
    real = svc.resolve

    def counting(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(svc, "resolve", counting)
    return calls


def test_external_verified_claim_reused_without_reresolution(tmp_path, monkeypatch):
    proj = "PROJ-901-reuse"
    value = "9988"
    evidence = {"source_id": "numeric:doi:10.5281/zenodo.x", "ok": True}
    claim = Claim(
        claim_id="c_aaaaaaaa",
        kind=ClaimKind.NUMERIC,
        raw_text="9,988 prime knots at 13 crossings",
        canonical="count(prime_knots, crossings=13)=9988",
        context="validation benchmark",
        artifact_path=f"projects/{proj}/spec.md",
        source_type="external",
        status=ClaimStatus.VERIFIED,
        resolved_value=value,
        evidence=evidence,
        resolver="resolve_numeric_or_citation",
        attempts=1,
        updated_at="2026-05-30T00:00:00Z",
        source_hash=svc._source_hash_from_evidence(evidence, value),
    )
    claim_store.upsert(proj, claim, repo_root=tmp_path)

    calls = _count_wrap_resolve(monkeypatch)

    out1 = svc.resolve_registered_claims(
        [claim], project_id=proj, backend=None, model=None, repo_root=tmp_path
    )
    out2 = svc.resolve_registered_claims(
        [claim], project_id=proj, backend=None, model=None, repo_root=tmp_path
    )

    # Verified + unchanged source → resolver NEVER invoked across both passes.
    assert calls == []
    # Identical value rendered both times, straight from the registry.
    assert out1[0].resolved_value == value
    assert out2[0].resolved_value == value
    assert out1[0].status == ClaimStatus.VERIFIED


def test_result_claim_reused_then_invalidated_when_receipt_removed(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_RECEIPT_KEY", "test-receipt-key-do-not-ship")
    proj = "PROJ-902-results"

    receipt = harness.mint_receipt(
        value="0.42",
        kind="scalar",
        producer={"script_path": "code/run.py", "code_sha": "abc123", "entrypoint": "main", "seed": 0},
        inputs={"dataset_id": "knots-13", "data_sha256": "deadbeef", "params": {}},
        env_sha="env-sha",
        captured={"stdout_path": "out.txt", "return_repr": "0.42"},
        repo_root=tmp_path,
        project_id=proj,
    )

    claim = Claim(
        claim_id="c_bbbbbbbb",
        kind=ClaimKind.RESULT,
        raw_text="accuracy was 0.42",
        canonical="0.42",
        context="results section",
        artifact_path=f"projects/{proj}/implementation_plan.md",
        source_type="result",
        status=ClaimStatus.VERIFIED,
        resolved_value="0.42",
        evidence={
            "result_id": receipt.result_id,
            "output_sha256": receipt.output_sha256,
            "source": f"result:{receipt.result_id}",
        },
        resolver="resolve_result",
        attempts=1,
        updated_at="2026-05-30T00:00:00Z",
        source_hash=receipt.output_sha256,
    )
    claim_store.upsert(proj, claim, repo_root=tmp_path)

    calls = _count_wrap_resolve(monkeypatch)

    # Pass 1: receipt intact → reuse, resolver not invoked.
    out1 = svc.resolve_registered_claims(
        [claim], project_id=proj, backend=None, model=None, repo_root=tmp_path
    )
    assert calls == []
    assert out1[0].status == ClaimStatus.VERIFIED

    # The execution artifact is removed (FR-015: underlying receipt changes).
    removed = glob.glob(str(tmp_path / "state" / "results" / proj / "*.yaml"))
    assert removed, "receipt file should have been minted"
    for path in removed:
        os.remove(path)

    # Pass 2: result no longer backed → invalidate → resolver invoked → blocked.
    out2 = svc.resolve_registered_claims(
        [claim], project_id=proj, backend=None, model=None, repo_root=tmp_path
    )
    assert calls == [1]  # invalidation forced exactly one real re-resolution
    assert out2[0].status == ClaimStatus.NOT_ENOUGH_INFO
    assert out2[0].resolved_value is None
