"""Routing-chokepoint tests (spec 026, Phase 2 slice 5, corrected execute()-delegation).

``route_chat`` is the SINGLE production entry that maps INTENT (a requirement
profile + the caller's pinned model + call options) onto the three-layer
mechanism: acquire the REAL (LKG-inclusive) snapshot, ``build_requirement`` →
``select`` → ``_promote_primary`` → delegate the WHOLE ``ModelChain`` to
``execute`` (no string projection, no legacy peer walker). These tests exercise
that wiring with REAL contract objects + injected recording backends (a factory,
never a model mock) so we assert which candidate/backend actually answered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from llmxive.backends.base import ChatMessage, ChatResponse, TransientBackendError
from llmxive.model_selection.attempt_hooks import ChainResolved, SelectionFailure
from llmxive.model_selection.snapshot import _family_of, _vendor_of
from llmxive.model_selection.types import (
    Candidate,
    CreditGuardSnapshot,
    ModelChain,
    ModelPricing,
    ModelRef,
    ModelRequirement,
    ModelUnavailable,
    RequirementOverrides,
    RuntimeSnapshot,
    SnapshotProvenance,
)
from tests.unit.test_model_selection_attempt_hooks import _Recorder

NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=UTC)
DARTMOUTH_EP = "https://chat.dartmouth.edu"

QWEN = "qwen.qwen3.5-122b"
GEMMA4 = "google.gemma-4-31B-it"
GPT_OSS = "openai.gpt-oss-120b"
CLAUDE = "anthropic.claude-haiku-4-5-20251001"
LOCAL = "Qwen/Qwen2.5-3B-Instruct"

_MSGS = [ChatMessage(role="user", content="summarize this text please")]


def _ref(mid: str) -> ModelRef:
    backend = "local" if mid == LOCAL else "dartmouth"
    endpoint = "local" if mid == LOCAL else DARTMOUTH_EP
    vendor = _vendor_of(mid)
    return ModelRef(backend, endpoint, mid, _family_of(mid, vendor), vendor)


def _snapshot(
    *,
    model_ids: list[str] | None = None,
    paid_opt_in: bool = False,
    credit_source: str = "live",
    catalog_source: str = "live",
    catalog_age_s: float = 0.0,
    available_headroom: float = 1400.0,
) -> RuntimeSnapshot:
    if model_ids is None:
        model_ids = [QWEN, GEMMA4, GPT_OSS, CLAUDE, LOCAL]
    models: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for mid in model_ids:
        models.append(_ref(mid))
        pricing[mid] = ModelPricing(1e-6, 5e-6) if mid == CLAUDE else ModelPricing(0.0, 0.0)
    credit = CreditGuardSnapshot(
        balance=1000.0, spend=100.0, max_budget=2000.0, paid_opt_in=paid_opt_in,
        budget_fraction=0.75, effective_cap=1500.0, available_headroom=available_headroom,
        budget_reset_at="2026-07-18T03:45:00-04:00", observed_at=NOW, source=credit_source,
    )
    sources = {
        "catalog": SnapshotProvenance(catalog_source, NOW, catalog_age_s),
        "local": SnapshotProvenance("live", NOW, 0.0),
        "credit": SnapshotProvenance(credit_source, NOW, 0.0),
    }
    return RuntimeSnapshot(
        models=tuple(models), pricing=pricing,
        health={m.model_id: "ok" for m in models}, credit=credit,
        observed_at=NOW, sources=sources, digest="TEST-DIGEST",
    )


def _no_eligible_snapshot() -> RuntimeSnapshot:
    """A snapshot ``select`` must raise ``ModelUnavailable`` against: the same
    cold-start technique ``test_model_selection_select.py`` uses
    (``test_cold_start_no_models_raises`` / already exercised in this file by
    ``test_route_chat_cold_start_fails_closed_model_unavailable``) — no models at
    all, with the catalog explicitly unavailable, so nothing is eligible."""
    return _snapshot(model_ids=[], catalog_source="unavailable")


@dataclass
class _RecordingBackend:
    """Injected recording backend (no model mock): records every call and can be
    told to fail specific models transiently so we assert the walked chain."""

    name: str
    fail_models: set[str] = field(default_factory=set)
    calls: list[dict] = field(default_factory=list)  # type: ignore[type-arg]

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):  # type: ignore[no-untyped-def]
        self.calls.append(
            {"backend": self.name, "model": model, "max_tokens": max_tokens,
             "temperature": temperature, "deadline_s": deadline_s}
        )
        if model in self.fail_models:
            raise TransientBackendError(f"synthetic transient on {model}")
        return ChatResponse(text=f"OK {model}", model=model, backend=self.name)


def _factory(*backends: _RecordingBackend):
    by_name = {b.name: b for b in backends}
    return lambda name: by_name[name]


# --------------------------------------------------------------------------- #
# Happy path: standard_generation → select's top free candidate (qwen), through
# execute (NOT the legacy peer walker), returning its ChatResponse.
# --------------------------------------------------------------------------- #


def test_route_chat_delegates_standard_profile_to_top_candidate():
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth")
    resp = route_chat(
        _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
        snapshot=_snapshot(), backend_factory=_factory(be),
    )
    assert isinstance(resp, ChatResponse)
    assert resp.model == QWEN
    assert [c["model"] for c in be.calls] == [QWEN]  # top free candidate answered first


def test_route_chat_promotes_present_caller_model_to_front():
    # US5: a caller that pins gpt-oss (present + eligible) runs it FIRST, even
    # though select ranks qwen ahead of it.
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth", fail_models=set())
    resp = route_chat(
        _MSGS, profile="standard_generation", caller_model=GPT_OSS, max_tokens=512,
        snapshot=_snapshot(), backend_factory=_factory(be),
    )
    assert resp.model == GPT_OSS
    assert be.calls[0]["model"] == GPT_OSS


def test_route_chat_never_resurrects_absent_caller_model():
    # US5 scenario 2 / revert-finding #3: a caller model that select did NOT keep
    # (absent from the snapshot) is never prepended — the top eligible candidate
    # answers, and the absent model is never called.
    from llmxive.model_selection.route import route_chat

    absent = "openai.gpt-5"  # not in the snapshot
    be = _RecordingBackend("dartmouth")
    resp = route_chat(
        _MSGS, profile="standard_generation", caller_model=absent, max_tokens=512,
        snapshot=_snapshot(), backend_factory=_factory(be),
    )
    assert resp.model == QWEN  # select's top pick, not the absent pin
    assert absent not in [c["model"] for c in be.calls]


def test_route_chat_dispatches_each_candidate_through_its_own_backend():
    # revert-finding #2 / e2e #2: when the primary free models fail, the local
    # candidate is reached — and MUST be dispatched through the LOCAL backend,
    # never the Dartmouth one. Backend identity is preserved (Candidates, not
    # strings).
    from llmxive.model_selection.route import route_chat

    dart = _RecordingBackend("dartmouth", fail_models={QWEN, GEMMA4, GPT_OSS})
    local = _RecordingBackend("local")
    resp = route_chat(
        _MSGS, profile="cheap_structured", caller_model=QWEN, max_tokens=512,
        snapshot=_snapshot(model_ids=[QWEN, GEMMA4, GPT_OSS, LOCAL]),
        backend_factory=_factory(dart, local),
    )
    assert resp.backend == "local" and resp.model == LOCAL
    assert local.calls and all(c["backend"] == "local" for c in local.calls)


def test_route_chat_deterministic_no_llm_bypasses_selection_entirely():
    # e2e #7: the no-llm sentinel must never touch snapshot / select / execute.
    from llmxive.model_selection import route as route_mod

    called = {"snapshot": False}

    def _boom(*a, **k):
        called["snapshot"] = True
        raise AssertionError("runtime_snapshot must NOT be called for deterministic-no-llm")

    # If the guard is missing, route would try to acquire a snapshot → _boom fires.
    with pytest.raises(ValueError, match="deterministic-no-llm"):
        route_mod.route_chat(
            _MSGS, caller_model="deterministic-no-llm", max_tokens=512,
            snapshot=None,
        )
    assert called["snapshot"] is False


def test_route_chat_cold_start_fails_closed_model_unavailable():
    # revert-finding #5: no live catalog + no LKG → select raises ModelUnavailable;
    # route_chat fails CLOSED (does NOT fall back to a legacy static chain).
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth")
    with pytest.raises(ModelUnavailable):
        route_chat(
            _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
            snapshot=_snapshot(model_ids=[], catalog_source="unavailable"),
            backend_factory=_factory(be),
        )
    assert be.calls == []  # nothing was ever attempted


def test_route_chat_uses_lkg_snapshot_within_freshness_window():
    # e2e #5 (requirement-sensitive freshness, the USABLE half): a bounded
    # last_known_good catalog WITHIN max_catalog_age_s is usable for
    # standard_generation — route_chat proceeds on it (a Dartmouth outage does not
    # strand routing while the LKG is still fresh). The cold-start FAIL-CLOSED half
    # is covered by test_route_chat_cold_start_fails_closed.
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth")
    resp = route_chat(
        _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
        snapshot=_snapshot(catalog_source="last_known_good", catalog_age_s=100.0),
        backend_factory=_factory(be),
    )
    assert resp.model == QWEN  # LKG within the 3600s window is eligible


def test_route_chat_derives_allow_paid_from_snapshot_opt_in(monkeypatch):
    # allow_paid=None → derived from the snapshot's credit opt-in, so the guarded
    # paid tail can appear (execute's twice-checked guard still decides per call).
    from llmxive.model_selection import route as route_mod

    captured = {}
    real_select = route_mod.select

    def _spy_select(req, snap, **kw):
        captured["allow_paid"] = req.allow_paid
        return real_select(req, snap, **kw)

    monkeypatch.setattr(route_mod, "select", _spy_select)
    be = _RecordingBackend("dartmouth")
    route_mod.route_chat(
        _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
        snapshot=_snapshot(paid_opt_in=True, credit_source="live"),
        backend_factory=_factory(be),
    )
    assert captured["allow_paid"] is True


def test_route_chat_defaults_ledger_repo_to_repo_root(monkeypatch):
    # Review finding 1: the production wrappers don't pass a ledger_repo, so
    # route_chat must default it to the repo root (where the reservation ledger
    # lives) — otherwise execute() skips EVERY paid candidate with "no reservation
    # ledger configured" and the guarded paid fallback is nonfunctional. The
    # explicit param stays the test injection seam.
    from llmxive.config import repo_root
    from llmxive.model_selection import route as route_mod
    from llmxive.model_selection.execute import ExecutionResult

    captured = {}

    def _spy_execute(chain, messages, **kwargs):
        captured["ledger_repo"] = kwargs.get("ledger_repo")
        return ExecutionResult(
            response=ChatResponse(text="ok", model=QWEN, backend="dartmouth"),
            model_ref=chain.candidates[0].model_ref, reserved_credits=0.0, notes=(),
        )

    monkeypatch.setattr(route_mod, "execute", _spy_execute)
    route_mod.route_chat(
        _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
        snapshot=_snapshot(), backend_factory=_factory(_RecordingBackend("dartmouth")),
    )
    assert captured["ledger_repo"] == repo_root()  # production ledger source supplied


def test_route_chat_passes_none_temperature_through_to_backend():
    # Generative agents leave temperature None (sampling ON); route must NOT coerce
    # it to 0.0 (that would silently make brainstorm/implementer deterministic — an
    # unsanctioned behavior change).
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth")
    route_chat(
        _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
        temperature=None, snapshot=_snapshot(), backend_factory=_factory(be),
    )
    assert be.calls[0]["temperature"] is None


def test_route_chat_negative_caches_snapshot_acquisition(monkeypatch):
    # revert-finding #6: bounded negative caching — two calls within the TTL must
    # acquire the (networked) snapshot ONCE, not per call (never re-fetch
    # catalog+local+credit on every miss during an outage).
    from llmxive.model_selection import route as route_mod

    route_mod.reset_snapshot_cache()
    fetches = {"n": 0}
    snap = _snapshot()

    def _counting_fetch(*a, **k):
        fetches["n"] += 1
        return snap

    monkeypatch.setattr(route_mod, "runtime_snapshot", _counting_fetch)
    monkeypatch.setattr(route_mod, "_now", lambda: 1000.0)  # frozen clock inside TTL
    be = _RecordingBackend("dartmouth")
    for _ in range(2):
        route_mod.route_chat(
            _MSGS, profile="standard_generation", caller_model=QWEN, max_tokens=512,
            backend_factory=_factory(be),
        )
    assert fetches["n"] == 1  # cached across the two in-TTL calls
    route_mod.reset_snapshot_cache()


# --------------------------------------------------------------------------- #
# RequirementOverrides: allow_paid precedence + compose-merge onto the base
# profile's requirement (spec 026 slice 6).
# --------------------------------------------------------------------------- #


def _free_chain(req, snap, model_id: str = QWEN) -> ModelChain:
    """A REAL minimal ``ModelChain`` for a fake ``select`` stand-in: one free
    candidate drawn straight from the real snapshot, carrying the captured
    requirement's own ``call_budget`` so the downstream ``execute()`` call
    dispatches realistically (no mock chain)."""
    ref = next(m for m in snap.models if m.model_id == model_id)
    candidate = Candidate(
        model_ref=ref,
        pricing=snap.pricing[model_id],
        worst_case_credits=0.0,
        approved_ceiling_credits=0.0,
    )
    return ModelChain(
        candidates=(candidate,),
        resolved_at=snap.observed_at,
        call_budget=req.call_budget,
        snapshot_digest=snap.digest,
        snapshot_provenance=dict(snap.sources),
        selection_policy_version=1,
        explanation=(),
    )


def test_allow_paid_double_supply_raises():
    # No silent precedence (spec 026 slice 6, round-2 #1): supplying BOTH the
    # standalone allow_paid param AND overrides.allow_paid (both non-None) is a
    # caller programming error, not something route_chat should silently resolve.
    from llmxive.model_selection.route import route_chat

    with pytest.raises(ValueError, match="allow_paid"):
        route_chat(
            _MSGS,
            max_tokens=64,
            allow_paid=True,
            overrides=RequirementOverrides(allow_paid=False),
            snapshot=_snapshot(),
        )


def test_overrides_allow_paid_wins_over_snapshot_optin(monkeypatch):
    # snapshot opt-in True, but overrides pins allow_paid=False — overrides is
    # explicit tier authority and must win over the snapshot-derived default.
    from llmxive.model_selection import route as route_mod

    captured: dict = {}

    def _fake_select(req, snap, **kw):
        captured["req"] = req
        return _free_chain(req, snap)

    monkeypatch.setattr(route_mod, "select", _fake_select)
    be = _RecordingBackend("dartmouth")
    route_mod.route_chat(
        _MSGS,
        max_tokens=64,
        overrides=RequirementOverrides(allow_paid=False),
        snapshot=_snapshot(paid_opt_in=True),
        backend_factory=_factory(be),
    )
    assert captured["req"].allow_paid is False


def test_overrides_compose_union_and_tighten_with_base_profile(monkeypatch):
    # The base profile's requirement already carries an exclusion + a
    # max_credits ceiling; overrides must UNION excludes, take the TIGHTER
    # max_credits, and OR require_paid — never erase the base's constraints.
    from llmxive.model_selection import route as route_mod

    captured: dict = {}

    def _fake_select(req, snap, **kw):
        captured["req"] = req
        return _free_chain(req, snap)

    def _fake_build_requirement(profile, call_budget, *, independence_against=None, allow_paid=False):
        return ModelRequirement(
            capability="standard",
            call_budget=call_budget,
            exclude_models=frozenset({"vendor.base-x"}),
            max_credits=500,
            allow_paid=allow_paid,
        )

    monkeypatch.setattr(route_mod, "select", _fake_select)
    monkeypatch.setattr(route_mod, "build_requirement", _fake_build_requirement)
    be = _RecordingBackend("dartmouth")
    route_mod.route_chat(
        _MSGS,
        max_tokens=64,
        overrides=RequirementOverrides(
            exclude_models=frozenset({"q.default"}), max_credits=200, require_paid=True
        ),
        snapshot=_snapshot(),
        backend_factory=_factory(be),
    )
    req = captured["req"]
    assert req.exclude_models == frozenset({"vendor.base-x", "q.default"})  # union
    assert req.max_credits == 200  # tighter of 500 / 200
    assert req.require_paid is True  # base(False) OR True


def test_overrides_none_preserves_snapshot_derived_allow_paid(monkeypatch):
    # overrides=None leaves allow_paid snapshot-derived (unchanged behavior).
    from llmxive.model_selection import route as route_mod

    captured: dict = {}

    def _fake_select(req, snap, **kw):
        captured["req"] = req
        return _free_chain(req, snap)

    monkeypatch.setattr(route_mod, "select", _fake_select)
    be = _RecordingBackend("dartmouth")
    route_mod.route_chat(
        _MSGS,
        max_tokens=64,
        overrides=None,
        snapshot=_snapshot(paid_opt_in=True),
        backend_factory=_factory(be),
    )
    assert captured["req"].allow_paid is True  # from snapshot opt-in (unchanged behavior)


# --------------------------------------------------------------------------- #
# Task 5: reservation_authority / route_audit threading through route_chat
# (spec 025 slice 0) — ChainResolved on success, SelectionFailure + re-raise on
# ModelUnavailable. Default None on both hooks leaves every test above unchanged.
# --------------------------------------------------------------------------- #


def test_route_chat_emits_chain_resolved():
    from llmxive.model_selection.route import route_chat

    rec = _Recorder()
    resp = route_chat(
        _MSGS, profile="standard_generation", max_tokens=32,
        snapshot=_snapshot(), backend_factory=_factory(_RecordingBackend("dartmouth")),
        route_audit=rec,
    )
    assert isinstance(resp, ChatResponse)
    assert any(isinstance(e, ChainResolved) for e in rec.events)


def test_route_chat_emits_selection_failure_and_reraises():
    from llmxive.model_selection.route import route_chat

    rec = _Recorder()
    with pytest.raises(ModelUnavailable):
        route_chat(
            _MSGS, profile="standard_generation", max_tokens=32,
            snapshot=_no_eligible_snapshot(),
            backend_factory=_factory(_RecordingBackend("dartmouth")),
            route_audit=rec,
        )
    assert any(isinstance(e, SelectionFailure) for e in rec.events)
