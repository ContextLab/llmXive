"""Offline integration test: the SHIPPED production run-time feature-flag combo.

``llmxive.cli._cmd_run`` turns on three feature flags in production via
``os.environ.setdefault`` (``cli.py`` ~L75/L81/L89)::

    LLMXIVE_GROUNDING_GUARD=1   # F-19 factual-grounding guard (LLM + real HTTP)
    LLMXIVE_CLAIM_LAYER=1       # spec 016 claim-verification layer
    LLMXIVE_CLAIM_FILL=1        # spec 017/018 authoritative-fill + mode routing

Every consumer defaults those flags OFF, and ``tests/conftest.py``'s autouse
``_isolate_run_side_effect_flags`` fixture *snapshots and restores* the three
keys around each offline test (so an in-process ``_cmd_run`` call cannot leak
them into a network-free reviser suite that asserts exact backend call counts).
The side effect: the FLAG-ON production combination was exercised ONLY under
``LLMXIVE_REAL_TESTS=1`` (the ``tests/real_call`` + ``slow`` suites) — never by
the fast per-PR ``-m "not slow"`` gate. So the shipped runtime config's
flag-gated branches were never asserted by the offline gate (issue #1139, D17).

This module closes that gap. Each test EXPLICITLY opts in to the relevant flag
with ``monkeypatch.setenv`` — which wins for the duration of the test body,
regardless of the autouse restore that runs at teardown — then drives the REAL
flag-gated consumer branch, stubbing ONLY the network/LLM boundary that branch
reaches (the claim-processing service, the grounding pass, ``fill_claim``, the
mode selector). Each positive case asserts the guarded branch was ENTERED and
behaved (the stub really ran + the branch's own logic mutated the output); each
negative control proves the flag genuinely gates the branch (boundary NOT called
+ output untouched). Nothing here touches the real network.
"""

from __future__ import annotations

import pytest

from llmxive.agents.citation_guard import GuardReport
from llmxive.claims import resolve as resolve_mod
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, Verdict
from llmxive.claims.pointer import GateReport
from llmxive.convergence.revisers import _self_consistency as sc
from llmxive.fill.models import FillProvenance, FillResult

_ARTIFACT_PATH = "projects/PROJ-001-demo/specs/spec.md"
_PROJECT_ID = "PROJ-001-demo"  # what _extract_project_id pulls from the path


def _numeric_claim(*, kind: ClaimKind = ClaimKind.NUMERIC) -> Claim:
    """A minimal, valid non-RESULT claim for the resolver-path tests."""
    return Claim(
        claim_id="c_test",
        kind=kind,
        raw_text="9987 knots",
        canonical="9987 knots",
        context="the smallest example has 9987 knots",
        artifact_path=_ARTIFACT_PATH,
        source_type="external",
        status=ClaimStatus.NOT_ENOUGH_INFO,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=1,
        updated_at="2026-07-15T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# LLMXIVE_CLAIM_LAYER — _self_consistency._verify_claims (cli.py L81; branch L336)
# Boundary stubbed: llmxive.claims.service.process_document (LLM extract + HTTP resolve)
# ---------------------------------------------------------------------------

def test_claim_layer_branch_runs_when_flag_on(monkeypatch, tmp_path):
    monkeypatch.setenv("LLMXIVE_CLAIM_LAYER", "1")

    calls: list[tuple[str, str]] = []

    def fake_process_document(text, *, artifact_path, project_id, backend,
                              model, repo_root, stage_label=None):
        calls.append((artifact_path, project_id))
        return ("VERIFIED " + text, [], GateReport(blocked=False))

    monkeypatch.setattr(
        "llmxive.claims.service.process_document", fake_process_document
    )

    artifacts = {_ARTIFACT_PATH: "the answer is 42"}
    out = sc._verify_claims(artifacts, backend=object(), model="m", repo_root=tmp_path)

    # Branch ENTERED (flag on + backend present): the service really ran, on the
    # right path/project (real _extract_project_id + per-artifact loop executed).
    assert calls == [(_ARTIFACT_PATH, _PROJECT_ID)]
    # Real merge logic ran: the rewritten body replaced the original.
    assert out[_ARTIFACT_PATH] == "VERIFIED the answer is 42"


def test_claim_layer_branch_skipped_when_flag_off(monkeypatch, tmp_path):
    monkeypatch.delenv("LLMXIVE_CLAIM_LAYER", raising=False)

    def boom(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("process_document called with LLMXIVE_CLAIM_LAYER off")

    monkeypatch.setattr("llmxive.claims.service.process_document", boom)

    artifacts = {_ARTIFACT_PATH: "the answer is 42"}
    out = sc._verify_claims(artifacts, backend=object(), model="m", repo_root=tmp_path)

    assert out == artifacts  # flag gates the branch: body untouched, no call


# ---------------------------------------------------------------------------
# LLMXIVE_GROUNDING_GUARD — _self_consistency._ground_factual_claims
# (cli.py L75; branch L410). Boundary: grounding_guard.verify_grounding_and_clean
# ---------------------------------------------------------------------------

def test_grounding_guard_branch_runs_when_flag_on(monkeypatch, tmp_path):
    monkeypatch.setenv("LLMXIVE_GROUNDING_GUARD", "1")

    calls: list[str] = []

    def fake_verify(text, *, backend, model, repo_root):
        calls.append(text)
        return ("[UNVERIFIED] " + text, GuardReport(flagged_count=1, flagged_values=["42"]))

    monkeypatch.setattr(
        "llmxive.agents.grounding_guard.verify_grounding_and_clean", fake_verify
    )

    artifacts = {_ARTIFACT_PATH: "42 knots per Smith 2004"}
    out = sc._ground_factual_claims(artifacts, backend=object(), model="m", repo_root=tmp_path)

    # Branch ENTERED: the grounding pass really ran on the real artifact body.
    assert calls == ["42 knots per Smith 2004"]
    # Real flagged-count logic ran: the flagged rewrite replaced the body.
    assert out[_ARTIFACT_PATH] == "[UNVERIFIED] 42 knots per Smith 2004"


def test_grounding_guard_branch_skipped_when_flag_off(monkeypatch, tmp_path):
    monkeypatch.delenv("LLMXIVE_GROUNDING_GUARD", raising=False)

    def boom(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("verify_grounding_and_clean called with guard flag off")

    monkeypatch.setattr(
        "llmxive.agents.grounding_guard.verify_grounding_and_clean", boom
    )

    artifacts = {_ARTIFACT_PATH: "42 knots per Smith 2004"}
    out = sc._ground_factual_claims(artifacts, backend=object(), model="m", repo_root=tmp_path)

    assert out == artifacts  # flag gates the branch: body untouched, no call


# ---------------------------------------------------------------------------
# LLMXIVE_CLAIM_FILL — claims.resolve._maybe_fill (cli.py L89; branch L164)
# Boundary stubbed: llmxive.fill.service.fill_claim (OEIS/Wikipedia/Wikidata fetch)
# ---------------------------------------------------------------------------

def _filled_result() -> FillResult:
    prov = FillProvenance(
        value="9988",
        source_id="A002863",
        url="https://oeis.org/A002863",
        quote="13 9988",
        channel="oeis",
        conflicts=[],
    )
    return FillResult.filled("9988", prov, ["oeis"])


def test_claim_fill_branch_upgrades_verdict_when_flag_on(monkeypatch, tmp_path):
    monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

    calls: list[str] = []

    def fake_fill_claim(claim, *, backend, model, repo_root):
        calls.append(claim.claim_id)
        return _filled_result()

    monkeypatch.setattr("llmxive.fill.service.fill_claim", fake_fill_claim)

    claim = _numeric_claim()
    original = Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence=None, resolver="resolve_numeric_or_citation")
    out = resolve_mod._maybe_fill(claim, original, backend=object(),
                                  model="m", repo_root=tmp_path)

    # Branch ENTERED: fill_claim really ran, and the real upgrade logic converted
    # a NOT_ENOUGH_INFO verdict into a VERIFIED one carrying fill provenance.
    assert calls == ["c_test"]
    assert out.status == ClaimStatus.VERIFIED
    assert out.value == "9988"
    assert out.resolver == "fill:oeis"
    assert out.evidence["filled"] is True
    assert out.evidence["fill"]["source_id"] == "A002863"


def test_claim_fill_branch_skipped_when_flag_off(monkeypatch, tmp_path):
    monkeypatch.delenv("LLMXIVE_CLAIM_FILL", raising=False)

    def boom(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("fill_claim called with LLMXIVE_CLAIM_FILL off")

    monkeypatch.setattr("llmxive.fill.service.fill_claim", boom)

    claim = _numeric_claim()
    original = Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence=None, resolver="resolve_numeric_or_citation")
    out = resolve_mod._maybe_fill(claim, original, backend=object(),
                                  model="m", repo_root=tmp_path)

    assert out is original  # flag gates the branch: verdict unchanged, no call


def test_claim_fill_never_fills_result_claims_even_when_flag_on(monkeypatch, tmp_path):
    # spec 017 T019 constraint: RESULT claims are never filled. Even with the
    # flag ON the branch is entered but the RESULT guard short-circuits BEFORE
    # the fill_claim boundary — real flag-gated logic, still no network.
    monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

    def boom(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("fill_claim called for a RESULT claim")

    monkeypatch.setattr("llmxive.fill.service.fill_claim", boom)

    claim = _numeric_claim(kind=ClaimKind.RESULT)
    original = Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence=None, resolver="resolve_result")
    out = resolve_mod._maybe_fill(claim, original, backend=object(),
                                  model="m", repo_root=tmp_path)

    assert out is original


# ---------------------------------------------------------------------------
# LLMXIVE_CLAIM_FILL — mode routing in claims.resolve.resolve (branch L644)
# Boundary stubbed: llmxive.verify.mode.select_mode (LLM mode classifier)
# ---------------------------------------------------------------------------

def test_resolve_mode_routing_runs_when_fill_flag_on(monkeypatch, tmp_path):
    monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

    sentinel = Verdict(status=ClaimStatus.VERIFIED, value="7",
                       evidence={"mode": "computational"}, resolver="compute")
    mode_calls: list[str] = []
    comp_calls: list[str] = []

    def fake_select_mode(claim, *, backend=None, model=None, repo_root=None):
        mode_calls.append(claim.claim_id)
        return "computational"

    def fake_resolve_computational(claim, *, backend, model, repo_root):
        comp_calls.append(claim.claim_id)
        return sentinel

    monkeypatch.setattr("llmxive.verify.mode.select_mode", fake_select_mode)
    monkeypatch.setattr(
        "llmxive.claims.resolve._resolve_computational", fake_resolve_computational
    )

    out = resolve_mod.resolve(_numeric_claim(), backend=object(),
                              model="m", repo_root=tmp_path)

    # Branch ENTERED: the fill-gated mode routing ran (select_mode consulted,
    # computational resolver dispatched) and its verdict was returned as-is.
    assert mode_calls == ["c_test"]
    assert comp_calls == ["c_test"]
    assert out is sentinel


def test_resolve_mode_routing_skipped_when_fill_flag_off(monkeypatch, tmp_path):
    monkeypatch.delenv("LLMXIVE_CLAIM_FILL", raising=False)

    def boom_select_mode(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("select_mode called with LLMXIVE_CLAIM_FILL off")

    fallback = Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence=None, resolver="stub_resolver")

    monkeypatch.setattr("llmxive.verify.mode.select_mode", boom_select_mode)
    # Stub the normal kind-dispatch so the off-path stays network-free.
    monkeypatch.setattr(
        "llmxive.claims.resolve.select_resolver",
        lambda kind: (lambda claim, *, backend, model, repo_root: fallback),
    )

    out = resolve_mod.resolve(_numeric_claim(), backend=object(),
                              model="m", repo_root=tmp_path)

    assert out is fallback  # flag gates mode routing: fell straight to dispatch


# ---------------------------------------------------------------------------
# Capstone: the exact three-flag production combination active together.
# ---------------------------------------------------------------------------

def test_all_three_production_flags_active_together(monkeypatch, tmp_path):
    """Mirror cli._cmd_run: all three flags ON at once, every guarded branch runs."""
    monkeypatch.setenv("LLMXIVE_GROUNDING_GUARD", "1")
    monkeypatch.setenv("LLMXIVE_CLAIM_LAYER", "1")
    monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

    entered: set[str] = set()

    def fake_process_document(text, *, artifact_path, project_id, backend,
                              model, repo_root, stage_label=None):
        entered.add("claim_layer")
        return ("VERIFIED " + text, [], GateReport(blocked=False))

    def fake_verify(text, *, backend, model, repo_root):
        entered.add("grounding_guard")
        return ("[UNVERIFIED] " + text, GuardReport(flagged_count=1, flagged_values=["x"]))

    def fake_fill_claim(claim, *, backend, model, repo_root):
        entered.add("claim_fill")
        return _filled_result()

    monkeypatch.setattr("llmxive.claims.service.process_document", fake_process_document)
    monkeypatch.setattr(
        "llmxive.agents.grounding_guard.verify_grounding_and_clean", fake_verify
    )
    monkeypatch.setattr("llmxive.fill.service.fill_claim", fake_fill_claim)

    artifacts = {_ARTIFACT_PATH: "the answer is 42"}
    assert sc._verify_claims(
        artifacts, backend=object(), model="m", repo_root=tmp_path
    )[_ARTIFACT_PATH] == "VERIFIED the answer is 42"
    assert sc._ground_factual_claims(
        artifacts, backend=object(), model="m", repo_root=tmp_path
    )[_ARTIFACT_PATH] == "[UNVERIFIED] the answer is 42"

    original = Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence=None, resolver="resolve_numeric_or_citation")
    filled = resolve_mod._maybe_fill(_numeric_claim(), original, backend=object(),
                                     model="m", repo_root=tmp_path)
    assert filled.status == ClaimStatus.VERIFIED

    # All three shipped flag-gated branches were exercised in one offline test.
    assert entered == {"claim_layer", "grounding_guard", "claim_fill"}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
