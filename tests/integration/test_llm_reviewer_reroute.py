"""LLMReviewer's lane context + FR-002 two-attempt reroute (spec 025 slice 1B, Task 4).

Integration, because the call ledger is durable — these need a real git repo and real
prompt files on disk. The router boundary is injected so a specific profile can fail; the
real routing path itself is covered by the Task 3 suite.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from llmxive.backends.base import ChatMessage
from llmxive.model_selection.attempt_hooks import RouteAuditError
from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import LaneRouteContext

LENS = "worthwhile-improvement"
STAGE = "self_improvement_proposal"
_BUDGET = 50.0  # ONE AttemptConfigured record binds this with the ceiling.
#: A lane reviewer must name at least one producer family to differ FROM.
_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))
#: Every family in the offline snapshot's free Dartmouth chain (tests/conftest.py's autouse
#: stub). Excluding all of them leaves selection nothing eligible, which is how a test drives
#: a REAL ModelUnavailable out of the real path instead of raising one by hand.
_ALL_FAMILIES = frozenset({"glm-5.3", "qwen3.5", "gemma-4", "gpt-oss"})
_MSGS = [ChatMessage(role="user", content="review this")]


def _clock():
    return "2026-07-25T00:00:00+00:00"


class _Sink:
    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True


class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass


@pytest.fixture
def repo_root(tmp_path):
    # REAL prompt files at the convention path: _load_system_prompt reads the per-lens
    # prompt AND the SSoT shared block, so both must exist. The lane log lives on the same
    # repo because the call ledger is durable.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    panels = tmp_path / "agents" / "prompts" / "panels"
    panels.mkdir(parents=True)
    (panels / f"panel_si_proposal_{LENS}.md").write_text(
        "# Panel Reviewer — lens\n\n## Lens\nJudge it.\n"
    )
    shared = tmp_path / "agents" / "prompts" / "_shared"
    shared.mkdir(parents=True)
    (shared / "panel_review_block.md").write_text("## Output format\nUse the protocol.\n")
    return tmp_path


class _RecordingCtx(LaneRouteContext):
    """A REAL subclass, not a mock and not attribute patching — LaneRouteContext is frozen,
    so assigning to ctx.record_reroute would raise FrozenInstanceError. It captures the
    reroute calls instead of persisting them; the durable persistence path has its own test
    in the Task 2 suite."""

    def __init__(self, **kw):
        super().__init__(**kw)
        object.__setattr__(self, "recorded", [])
        object.__setattr__(self, "record_error", None)

    def record_reroute(self, **kw):
        if self.record_error is not None:
            raise self.record_error
        self.recorded.append(kw)


def _ctx(repo_root, ceiling=10, cls=_RecordingCtx):
    ledger = LaneCallLedger(repo=repo_root, problem_id="P1", attempt_id="A1",
                            call_ceiling=ceiling, attempt_budget_credits=_BUDGET,
                            actor="reviewer", clock=_clock, config=LaneLogConfig())
    return cls(repo=repo_root, problem_id="P1", attempt_id="A1", actor="reviewer",
               clock=_clock, route_audit=_Sink(), reservation_authority=_Budget(),
               call_ledger=ledger)


def _reviewer(repo_root, **kw):
    from llmxive.convergence.llm_reviewer import LLMReviewer

    return LLMReviewer(lens=LENS, stage=STAGE, backend=object(), repo_root=Path(repo_root), **kw)


def _patch_router(monkeypatch, fn):
    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", fn)


class _Reply:
    def __init__(self, text):
        self.text = text


# ---- the non-lane path is untouched ----


def test_no_context_uses_the_unchanged_single_call(repo_root, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        return _Reply("plain")

    _patch_router(monkeypatch, _fake)
    reviewer = _reviewer(repo_root, profile="deep_review")
    assert reviewer._call_backend([]) == "plain"
    assert len(calls) == 1
    # the legacy path passes NO lane params at all
    assert calls[0].get("route_audit") is None and calls[0].get("route_id") is None
    assert "reraise_model_unavailable" not in calls[0]


# ---- configuration validation: what EXECUTES must match what gets RECORDED ----


def test_the_two_sanctioned_lane_configurations_are_accepted(repo_root):
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    # proposal: degrade to deep_review on ModelUnavailable
    _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
              independence_against=base, route_context=_ctx(repo_root))
    # patch: no fallback at all — fail closed
    _reviewer(repo_root, profile="independent_review", fallback_profile=None,
              independence_against=base, route_context=_ctx(repo_root))


def test_an_unsanctioned_fallback_profile_is_refused(repo_root):
    # record_reroute would assert independent_review -> deep_review while THIS reviewer ran
    # independent_review -> vision. The event validator cannot see the discrepancy: it only
    # ever inspects what record_reroute wrote.
    with pytest.raises(ValueError, match="sanctioned fallback"):
        _reviewer(repo_root, profile="independent_review", fallback_profile="vision",
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=_ctx(repo_root))


def test_a_lane_reviewer_with_a_non_independent_primary_is_refused(repo_root):
    with pytest.raises(ValueError, match="must use profile"):
        _reviewer(repo_root, profile="deep_review", fallback_profile="deep_review",
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=_ctx(repo_root))


def test_a_lane_reviewer_without_a_baseline_is_refused(repo_root):
    with pytest.raises(ValueError, match="at least one producer family"):
        _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=None, route_context=_ctx(repo_root))


def test_an_empty_family_baseline_is_refused(repo_root):
    # independent_review requires a family DIFFERENCE. With no producer family to differ
    # from, the constraint is satisfied by any model and FR-002's guarantee is void.
    with pytest.raises(ValueError, match="at least one producer family"):
        _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=IndependenceBaseline(), route_context=_ctx(repo_root))


@pytest.mark.parametrize("lane_only", [
    {"independence_against": IndependenceBaseline(families=frozenset({"qwen3.5"}))},
    {"fallback_profile": "deep_review"},
])
def test_lane_only_arguments_without_a_route_context_are_refused(repo_root, lane_only):
    # Without a context the lane path never runs, so these would be silently ignored — a
    # reviewer that looks independence-constrained and is not.
    with pytest.raises(ValueError, match="requires a route_context"):
        _reviewer(repo_root, profile="deep_review", **lane_only)


def test_an_ordinary_non_lane_reviewer_is_still_accepted(repo_root):
    _reviewer(repo_root, profile="deep_review")


# ---- the FR-002 two-attempt reroute ----


def test_reroute_records_an_explicit_event_and_uses_two_route_ids(repo_root, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        return _Reply("fallback-body")

    _patch_router(monkeypatch, _fake)
    ctx = _ctx(repo_root)
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    reviewer = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                         independence_against=base, route_context=ctx)

    assert reviewer._call_backend([]) == "fallback-body"
    assert len(calls) == 2
    # attempt 1: constrained, raw-ModelUnavailable enabled, both hooks present
    assert calls[0]["profile"] == "independent_review"
    assert calls[0]["independence_against"] is base
    assert calls[0]["reraise_model_unavailable"] is True
    assert calls[0]["route_audit"] is ctx.route_audit
    assert calls[0]["reservation_authority"] is ctx.reservation_authority
    # attempt 2: unconstrained, must NOT re-raise — a second miss is a real outage
    assert calls[1]["profile"] == "deep_review"
    assert calls[1].get("independence_against") is None
    assert calls[1].get("reraise_model_unavailable") in (False, None)
    # DISTINCT route ids, both charged against the ceiling
    assert calls[0]["route_id"] != calls[1]["route_id"]
    assert ctx.calls_used() == 2
    # the degradation is recorded EXPLICITLY, not left to be inferred
    assert len(ctx.recorded) == 1
    assert ctx.recorded[0]["lens"] == LENS
    assert ctx.recorded[0]["primary_route_id"] == calls[0]["route_id"]
    assert ctx.recorded[0]["fallback_route_id"] == calls[1]["route_id"]
    assert ctx.recorded[0]["exception_type"] == "ModelUnavailable"


def test_successful_primary_never_reroutes_or_records(repo_root, monkeypatch):
    _patch_router(monkeypatch, lambda backend, messages, **kw: _Reply("independent-body"))
    ctx = _ctx(repo_root)
    reviewer = _reviewer(
        repo_root, profile="independent_review", fallback_profile="deep_review",
        independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
        route_context=ctx,
    )
    assert reviewer._call_backend([]) == "independent-body"
    assert ctx.recorded == [] and ctx.calls_used() == 1


def test_without_a_fallback_profile_model_unavailable_is_not_rerouted(repo_root):
    # The future PATCH binding: required independence, NO fallback -> fail closed.
    #
    # NO injected router here, deliberately. `_route_review` passes
    # `reraise_model_unavailable=self._fallback_profile is not None`, so with no fallback the
    # real wrapper CONVERTS ModelUnavailable to BackendUnavailable and the `except
    # ModelUnavailable` branch never sees it. A fake that raised the raw exception itself
    # would drive that unreachable branch and pin a contract production can't produce.
    # Excluding every family in the offline snapshot leaves nothing eligible, which is a real
    # ModelUnavailable out of real selection logic — the exact patch-review failure mode.
    from llmxive.backends.base import BackendUnavailable

    ctx = _ctx(repo_root)
    reviewer = _reviewer(
        repo_root, profile="independent_review", fallback_profile=None,
        independence_against=IndependenceBaseline(families=_ALL_FAMILIES), route_context=ctx,
    )
    with pytest.raises(BackendUnavailable):   # NOT ModelUnavailable: disjoint types, so this
        reviewer._call_backend(_MSGS)         # fails loudly if the reviewer ever asks for raw
    assert ctx.recorded == [], "a lens with no fallback must never record a degradation"
    assert ctx.calls_used() == 1, "the failed primary is one charged call, and only one"


def test_a_failed_reroute_record_aborts_before_the_fallback_dispatches(repo_root, monkeypatch):
    # If the ReviewRerouted record cannot become durable, the fallback MUST NOT run --
    # otherwise the review silently claims an independence it did not have.
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        return _Reply("fallback-body")  # must never be reached

    _patch_router(monkeypatch, _fake)
    ctx = _ctx(repo_root)
    object.__setattr__(ctx, "record_error", RouteAuditError("lane ref unreachable"))
    reviewer = _reviewer(
        repo_root, profile="independent_review", fallback_profile="deep_review",
        independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
        route_context=ctx,
    )
    with pytest.raises(RouteAuditError):
        reviewer._call_backend([])
    assert len(calls) == 1 and calls[0]["profile"] == "independent_review"


def test_a_fallback_that_also_finds_nothing_is_an_outage_not_a_second_degrade(
    repo_root, monkeypatch
):
    # The fallback runs with reraise off, so a second miss converts to BackendUnavailable
    # and reaches the engine's clean-abort path rather than degrading again.
    from llmxive.backends.base import BackendUnavailable

    def _fake(backend, messages, **kw):
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        raise BackendUnavailable("no usable candidate")

    _patch_router(monkeypatch, _fake)
    ctx = _ctx(repo_root)
    reviewer = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                         independence_against=_BASELINE, route_context=ctx)
    with pytest.raises(BackendUnavailable):
        reviewer._call_backend([])
    assert len(ctx.recorded) == 1  # the degradation that DID happen is still recorded


# ---- durable operation identity ----


def test_distinct_logical_calls_get_distinct_operation_ids(repo_root, monkeypatch):
    # identify / the action-items resubmit / rereview are THREE logical calls. If they
    # shared an operation_id the durable claim would treat the later ones as REPLAYS,
    # returning the first route_id, and the dispatch gate would refuse to dispatch them.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        return _Reply("body")

    _patch_router(monkeypatch, _fake)
    ctx = _ctx(repo_root)
    reviewer = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                         independence_against=_BASELINE, route_context=ctx)
    msgs = [ChatMessage(role="user", content="review this")]
    reviewer._call_backend(msgs, kind="identify")
    reviewer._call_backend([*msgs, ChatMessage(role="user", content="no action items")],
                           kind="identify_resubmit")
    reviewer._call_backend(msgs, kind="rereview")
    assert len(set(seen)) == 3 and ctx.calls_used() == 3


def test_the_kind_alone_separates_two_calls_with_identical_messages(repo_root, monkeypatch):
    # The digest covers the messages, so without `kind` in the operation id an identify and
    # a rereview over the same artifacts would collide.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        return _Reply("body")

    _patch_router(monkeypatch, _fake)
    ctx = _ctx(repo_root)
    reviewer = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                         independence_against=_BASELINE, route_context=ctx)
    msgs = [ChatMessage(role="user", content="identical")]
    reviewer._call_backend(msgs, kind="identify")
    reviewer._call_backend(msgs, kind="rereview")
    assert len(set(seen)) == 2


def test_a_restart_replays_the_same_logical_call_onto_the_same_route_id(repo_root, monkeypatch):
    # Retry stability across a RESTART: identical (lens, kind, messages) with a FRESH
    # context -> the same durable claim, the same route_id, no extra ceiling charge.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        return _Reply("body")

    _patch_router(monkeypatch, _fake)
    msgs = [ChatMessage(role="user", content="review this")]
    ctx = None
    for _ in range(2):  # two processes, two contexts, one claim
        ctx = _ctx(repo_root)
        _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=_BASELINE,
                  route_context=ctx)._call_backend(msgs, kind="identify")
    assert len(set(seen)) == 1 and ctx.calls_used() == 1


def test_an_in_process_repeat_is_a_new_logical_call(repo_root, monkeypatch):
    # The counterpart: within ONE process an identical re-issue is a genuinely new call
    # (the first already dispatched), so it gets its own route_id and ceiling charge.
    # Without this the engine's reviser retry would be refused at the dispatch gate.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        return _Reply("body")

    _patch_router(monkeypatch, _fake)
    ctx = _ctx(repo_root)
    reviewer = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                         independence_against=_BASELINE, route_context=ctx)
    msgs = [ChatMessage(role="user", content="review this")]
    reviewer._call_backend(msgs, kind="identify")
    reviewer._call_backend(msgs, kind="identify")
    assert len(set(seen)) == 2 and ctx.calls_used() == 2
