"""F11: the REAL LLMReviewer -> chat_with_model_fallback -> _walker_route -> route_chat
path, driven by the REAL run_convergence engine (including its ThreadPoolExecutor panel
dispatch), against the REAL lane audit sink + Attempt credit ledger.

No mock at any layer: a scripted backend supplies model replies in the exact formats the
PRODUCTION parsers accept, a real temp git repo backs the lane log, and a real (aged)
snapshot drives the FR-002 reroute by making `independent_review`'s freshness bound
unsatisfiable while `deep_review` still resolves.

This file also owns `_run_panel_with_one_open_concern`, which Task 5's three ENGINE-driven
reviser tests use (they are part of Task 5's acceptance but can only run once the real
panel exists).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.convergence.engine import run_convergence
from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    PROPOSAL_LENSES,
    PROPOSAL_MAX_ROUNDS,
    PROPOSAL_STAGE,
    build_proposal_review_spec,
    run_proposal_review,
)
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.credit_ledger import AttemptCreditLedger
from llmxive.self_improvement.invocation_identity import build_invocation_identity
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import LaneRouteContext, proposal_call_ceiling

_CLOCK = lambda: "2026-07-25T00:00:00+00:00"  # noqa: E731
_BUDGET = 1000.0                 # generous: this suite is about routing, not starvation
_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))
#: The real repo, so the REAL Task-7 lens prompts are loaded.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROPOSAL = "# Proposal\n\nNarrow the retry loop.\n"


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def lane(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    cfg = LaneLogConfig()                       # local-only (no remote) for the test
    bootstrap_lane_log(tmp_path, config=cfg)
    sink = EventStoreRouteAudit(repo=tmp_path, problem_id="P1", attempt_id="A1",
                                actor="lane", clock=_CLOCK, config=cfg)
    # BOTH ledgers bind the SAME immutable AttemptConfigured pair (Slice 1A T13), so each
    # must present the same (ceiling, budget) — a mismatch is AttemptConfigMismatch.
    ledger = AttemptCreditLedger(repo=tmp_path, problem_id="P1", attempt_id="A1",
                                 attempt_budget_credits=_BUDGET,
                                 call_ceiling=LANE_ATTEMPT_CEILING, actor="lane",
                                 clock=_CLOCK, config=cfg)
    calls = LaneCallLedger(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="lane", clock=_CLOCK,
        config=cfg,
        call_ceiling=LANE_ATTEMPT_CEILING,  # the WHOLE-Attempt figure, never a component
        attempt_budget_credits=_BUDGET,     # the SAME budget the credit ledger binds
    )
    ctx = LaneRouteContext(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="lane", clock=_CLOCK,
        route_audit=sink, reservation_authority=ledger, call_ledger=calls, config=cfg,
    )
    return tmp_path, ctx


# --- Step 0 helpers: a real aged snapshot + production-parseable replies -------------


def _aged_snapshot(age_s: float):
    """The offline snapshot served from a STALE last-known-good catalog.

    Derived from the same snapshot the rest of the suite runs on (conftest's autouse
    `runtime_snapshot` stub) rather than hand-built, so this test cannot drift from the
    catalog every other test sees. `independent_review` pins `max_catalog_age_s=900` +
    `require_fresh_snapshot`; `deep_review` pins neither, so attempt 1 raises a REAL
    `ModelUnavailable` out of real selection logic — exactly FR-002's reroute trigger —
    while the fallback still resolves.

    BOTH fields matter: `select._fresh_enough` only treats a component as stale when its
    source is `last_known_good` (`select.py:107`). `age_s` is meaningless for a `live`
    fetch — it is fresh by definition — so aging a live component changes nothing.
    """
    import llmxive.model_selection.route as route_mod

    base = route_mod.runtime_snapshot()
    sources = dict(base.sources)
    sources["catalog"] = replace(sources["catalog"], source="last_known_good", age_s=age_s)
    return replace(base, sources=sources)


def _accept_reply(lens: str) -> str:
    return (
        "---\n"
        f"reviewer_name: {lens}\n"
        "reviewer_kind: llm\n"
        f"stage: {PROPOSAL_STAGE}\n"
        "artifact_path: proposal.md\n"
        "artifact_hash: 0000000000000000000000000000000000000000000000000000000000000000\n"
        "verdict: accept\n"
        "concerns: []\n"
        "---\n"
        f"The {lens} lens is satisfied: the proposal states its evidence and scope.\n"
    )


def _concern_reply(lens: str, severity: str = "requirement") -> str:
    # An EXPLICIT id, so R3's verdict matching is deterministic. Without one the parser
    # mints a uuid and the re-review could never match its own prior concern.
    #
    # `requirement` by default, NOT `writing`: the engine advances a non-review stage on
    # writing-ONLY residue after the cap (spec-023 defect #24), so a writing-severity
    # fixture would silently exercise the lenient path in every test here. The strict path
    # is the one that matters for a gate; the lenient one gets its own explicit test.
    return (
        "---\n"
        f"reviewer_name: {lens}\n"
        "reviewer_kind: llm\n"
        f"stage: {PROPOSAL_STAGE}\n"
        "artifact_path: proposal.md\n"
        "artifact_hash: 0000000000000000000000000000000000000000000000000000000000000000\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        f"  - id: {lens}-c1\n"
        f"    severity: {severity}\n"
        "    location: \"proposal.md:1\"\n"
        f"    text: \"[{lens}] State the evidence for the claimed pain explicitly.\"\n"
        "---\n"
        f"The {lens} lens needs one clarification before it can accept.\n"
    )


_CONCERN_ID_RE = re.compile(r"\[concern (\S+)\]")


def _reviser_reply(user_text: str, *, proposal: str = "# Revised\n\nNarrowed, with evidence.\n",
                   answer_ids: bool = True) -> str:
    """The reviser's SHARED two-part contract (Task 5): a small fenced json change-log,
    then the full artifact VERBATIM between ===BEGIN_ARTIFACT=== markers."""
    ids = _CONCERN_ID_RE.findall(user_text) if answer_ids else []
    entries = ", ".join(
        # NOTE the asymmetry: `{{` escapes a brace in the f-string segment, but the
        # closing segment is a PLAIN string, where `}}` would be two literal braces.
        f'{{"concern_id": "{cid}", "response": "Added the evidence paragraph.", '
        '"what_changed": "New section 2 cites the run log.", '
        '"artifacts_changed": ["proposal.md"]}'
        for cid in ids
    )
    return (
        "```json\n"
        '{"responses": [' + entries + "]}\n"
        "```\n\n"
        "===BEGIN_ARTIFACT proposal.md===\n"
        + proposal +
        "===END_ARTIFACT===\n"
    )


class _ScriptedPanelBackend:
    """A REAL backend object (not a mock): it implements `chat` and returns text the
    PRODUCTION parsers accept. It serves as the `dartmouth` backend, so `_walker_route`
    threads it in as the serving backend for the offline snapshot's chain."""

    name = "dartmouth"

    def __init__(self, *, raise_concerns: bool = False, reviser_replies=None,
                 concern_severity: str = "requirement"):
        self.raise_concerns = raise_concerns
        self.concern_severity = concern_severity
        #: optional iterator of raw reviser reply strings, for the malformed-reply tests
        self._reviser_replies = iter(reviser_replies) if reviser_replies else None
        self.reviewer_calls: list[tuple[str, str]] = []
        self.reviser_calls: list[str] = []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None,
             deadline_s=None, **_kw):
        system = messages[0].content
        user = messages[-1].content if len(messages) > 1 else ""

        if "author of a self-improvement proposal" in system:
            self.reviser_calls.append(user)
            if self._reviser_replies is not None:
                text = next(self._reviser_replies)
            else:
                text = _reviser_reply(user)
            return ChatResponse(text=text, model=model, backend="dartmouth")

        # Parse the TITLE line, not a substring scan: the lens prompts deliberately
        # cross-reference each other ("that is `diagnosis-correctness`"), so `lens in
        # system` misattributes a reviewer to whichever lens name appears first.
        title = re.match(r"# Panel Reviewer — (\S+) ", system)
        assert title is not None, f"unrecognized system prompt: {system[:120]!r}"
        lens = title.group(1)
        assert lens in PROPOSAL_LENSES, f"unknown lens {lens!r}"
        kind = "rereview" if "# Your prior concerns" in user else "identify"
        self.reviewer_calls.append((lens, kind))
        # R3 is a closed-set diff-check: accept, so the prior concern resolves.
        if kind == "identify" and self.raise_concerns:
            text = _concern_reply(lens, self.concern_severity)
        else:
            text = _accept_reply(lens)
        return ChatResponse(text=text, model=model, backend="dartmouth")


def _use_aged_snapshot(monkeypatch, age_s: float = 1800.0):
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot",
                        lambda: _aged_snapshot(age_s))


# --- the two panel tests ------------------------------------------------------------


def test_full_proposal_panel_audits_every_call_and_records_the_reroute(lane, monkeypatch):
    repo, ctx = lane
    _use_aged_snapshot(monkeypatch)
    backend = _ScriptedPanelBackend()

    outcome = run_proposal_review(
        backend=backend, repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=ctx, artifacts={"proposal.md": _PROPOSAL},
    )

    assert not outcome.failed_closed and outcome.result is not None
    assert outcome.result.converged

    events = read(repo, "P1")
    kinds = [e.event_type for e in events]
    # every lens rerouted -> one explicit record per lens, and BOTH legs are audited
    assert kinds.count("ReviewRerouted") == len(PROPOSAL_LENSES)
    assert "SelectionFailure" in kinds and "ChainResolved" in kinds
    assert "DispatchCompleted" in kinds

    # the fallback leg named by an explicit reroute record yields a degraded identity
    rr = next(e for e in events if e.event_type == "ReviewRerouted")
    ii = build_invocation_identity(events, route_id=rr.payload["fallback_route_id"],
                                   attempt_id="A1")
    assert ii is not None and ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == "independent_review"
    assert ii.serving_endpoint and ii.vendor        # full selection provenance present
    # F5: the joined primary_failure carries ALL FOUR spec fields, the last two sourced
    # from the primary leg's real SelectionFailure — not duplicated into the reroute record
    assert set(ii.degradation.primary_failure) == {
        "exception_type", "message", "requirement_digest", "snapshot_provenance"}
    assert ii.degradation.primary_failure["requirement_digest"]

    # the ceiling accounted BOTH legs of every reviewer op, and it is the DURABLE count
    # read back from the lane log (round-4 F1)
    assert ctx.calls_used() >= 2 * len(PROPOSAL_LENSES)
    # The Attempt's bound limit is the WHOLE-Attempt figure; a proposal-only run must also
    # stay inside its own stage COMPONENT, which is the tighter of the two checks.
    assert ctx.calls_used() <= proposal_call_ceiling(len(PROPOSAL_LENSES),
                                                     PROPOSAL_MAX_ROUNDS)
    assert ctx.calls_used() <= LANE_ATTEMPT_CEILING
    # and NOTHING routed without first being admitted: every route id the router touched
    # (resolved a chain for, or failed selection on) has a durable LaneCallClaimed
    claimed = {e.payload["route_id"] for e in events if e.event_type == "LaneCallClaimed"}
    routed = {e.payload["route_id"] for e in events
              if e.event_type in {"ChainResolved", "SelectionFailure"}}
    assert routed <= claimed, f"routed without a ceiling claim: {sorted(routed - claimed)}"

    # the whole panel really ran through the production reviewer path
    assert {lens for lens, _ in backend.reviewer_calls} == set(PROPOSAL_LENSES)


def test_reviser_calls_are_audited_too(lane, monkeypatch):
    # F3: the reviser is a lane LLM call — its route must appear in the SAME audit
    # stream, with its spend on the SAME Attempt. Drive a run whose R1 raises a concern
    # per lens so R2 (the reviser) actually executes.
    repo, ctx = lane
    _use_aged_snapshot(monkeypatch)
    backend = _ScriptedPanelBackend(raise_concerns=True)

    outcome = run_proposal_review(
        backend=backend, repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=ctx, artifacts={"proposal.md": _PROPOSAL},
    )
    assert not outcome.failed_closed
    assert backend.reviser_calls, "the reviser never ran — R2 was not exercised"

    events = read(repo, "P1")
    audited_routes = {e.payload["route_id"] for e in events
                      if e.event_type == "ChainResolved"}
    reroute_legs = set()
    for e in events:
        if e.event_type == "ReviewRerouted":
            reroute_legs.add(e.payload["primary_route_id"])
            reroute_legs.add(e.payload["fallback_route_id"])
    # At least one audited route belongs to NO reviewer reroute pair — that is the
    # reviser's own routed call, proving it was audited like every other lane call.
    assert audited_routes - reroute_legs, "the reviser's route was not audited"
    # and it was charged against the same Attempt ceiling as the panel
    assert ctx.calls_used() > 2 * len(PROPOSAL_LENSES)

    # the reviser does NOT reroute (the producer has no independence constraint), so its
    # route resolved a chain on the FIRST leg — no ReviewRerouted names it
    reviser_routes = audited_routes - reroute_legs
    assert not (reviser_routes & reroute_legs)


# --- Task 5's ENGINE-driven reviser contract ----------------------------------------


def _run_panel_with_one_open_concern(lane, monkeypatch, *, reviser_replies=None,
                                     reviser_raises=None,
                                     concern_severity: str = "requirement"):
    """Build the REAL proposal ReviewSpec with a scripted panel whose R1 raises exactly one
    concern per lens, then call the REAL `run_convergence`.

    `reviser_replies` / `reviser_raises` script the RESERVER's side only; the reviewers go
    through the full production routing path either way.
    """
    _repo, ctx = lane
    _use_aged_snapshot(monkeypatch)
    backend = _ScriptedPanelBackend(raise_concerns=True, reviser_replies=reviser_replies,
                                    concern_severity=concern_severity)
    if reviser_raises is not None:
        def _boom(*a, **kw):
            raise reviser_raises
        monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback",
                            _boom)
    spec = build_proposal_review_spec(
        backend=backend, repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=ctx,
    )
    return run_convergence(spec, {"proposal.md": _PROPOSAL}), backend


def test_one_malformed_reviser_reply_then_a_good_one_recovers(lane, monkeypatch):
    """engine.py:519-533 gives the reviser ONE retry. The lane reviser's malformed error
    must be the type + message that retry recognizes."""
    replies = ["garbage, no json and no artifact markers",
               _reviser_reply("[concern worthwhile-improvement-c1] "
                              "[concern diagnosis-correctness-c1] "
                              "[concern tractability-c1] [concern testability-c1] "
                              "[concern blast-radius-sanity-c1]")]
    result, backend = _run_panel_with_one_open_concern(lane, monkeypatch,
                                                       reviser_replies=replies)
    assert len(backend.reviser_calls) == 2       # retried, not aborted
    # The engine returns no artifacts (ConvergenceResult has no such field); the revision
    # is observable through the change-log it produced.
    assert result.response_history, "the retry produced no responses"
    assert all(r.response != "<missing>" for r in result.response_history)
    assert result.converged


def test_two_malformed_reviser_replies_degrade_to_no_change(lane, monkeypatch):
    """Issue #355's contract: after the retry, a RECOGNIZED malformed reply is 'no artifact
    change this round' — the bounded loop carries the concerns forward. It must NOT crash
    the panel and must NOT file an engine-failure issue."""
    replies = ["garbage, no json"] * 6           # every attempt in every round
    result, backend = _run_panel_with_one_open_concern(lane, monkeypatch,
                                                       reviser_replies=replies)
    assert len(backend.reviser_calls) >= 2       # it retried rather than crashing
    assert not result.converged                  # concerns carried forward
    assert result.concern_history                # and they are on the record


def test_writing_only_residue_still_advances_the_proposal(lane, monkeypatch):
    """The OTHER side of the two-tier bar, pinned explicitly so it is a decision rather
    than an accident.

    `self_improvement_proposal` is not in the engine's `_REVIEW_STAGES`, so after the cap a
    residue of ONLY writing-level concerns advances (spec-023 defect #24: kicking back on
    prose polish burned the PROJ-552 doc panels to their cap). The Task-7 lens prompts
    route anything substantive to `requirement` or worse, so in practice this allowance
    covers genuinely cosmetic residue — which is the intent.

    **Open for maintainer review**: if the lane's proposal gate should instead hold the
    strict `research_review`/`paper_review` bar, that is a one-line change to the engine's
    `_REVIEW_STAGES` (or a `ReviewSpec` flag) — NOT something this suite should decide by
    picking a fixture severity.
    """
    replies = ["garbage, no json"] * 8
    result, _ = _run_panel_with_one_open_concern(lane, monkeypatch, reviser_replies=replies,
                                                  concern_severity="writing")
    assert result.converged, "writing-only residue should advance a doc-authoring stage"
    assert result.concern_history, "…but the concerns are still on the record"


def test_a_backend_outage_is_a_CLEAN_ABORT_not_a_malformed_reply(lane, monkeypatch):
    """BackendError subclasses RuntimeError, so the engine checks it FIRST (engine.py:525).
    A lane reviser outage must abort cleanly, never be retried as malformed output."""
    from llmxive.backends.base import BackendUnavailable

    with pytest.raises(BackendUnavailable):
        _run_panel_with_one_open_concern(lane, monkeypatch,
                                          reviser_raises=BackendUnavailable("breaker open"))
