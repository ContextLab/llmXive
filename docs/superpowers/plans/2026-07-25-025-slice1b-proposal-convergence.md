# Self-Improvement Lane — Slice 1B: Proposal Convergence Wiring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the proposal review onto the Slice-1A substrate — a **lane route context** that carries the mandatory `route_audit` sink AND the `reservation_authority` into every lane LLM call (reviewers *and* the reviser), the FR-002 **two-attempt independence reroute** with an **explicit** `ReviewRerouted` event, the complete `InvocationIdentity`, the `self_improvement_proposal` `ReviewSpec` + lens prompts, and a real `run_convergence` integration test.

**Architecture:** Convergence reviewers already reach `route_chat` (via `chat_with_model_fallback` → `_walker_route`), but that wrapper drops the five spec-025 params. Task 3 closes that gap once, in `_walker_route` + `chat_with_model_fallback`. Everything lane-specific is then new code: `LaneRouteContext` (the three mandatory hooks + durable route admission), a reroute-aware `LLMReviewer` path, a lane reviser, and a lane entry point that owns fail-closed handling. `run_convergence` itself is **unchanged** — the lane builds independence-aware reviewers *before* handing them to the existing engine.

**Tech Stack:** Python ≥ 3.11; `pytest`; packages `llmxive.self_improvement`, `llmxive.convergence`, `llmxive.backends.router`. No new third-party deps.

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from spec 025 rev 16 and the slice-0/1A contracts.

- **Mandatory audit — no silently-unaudited lane call (FR-033a, F3).** `build_proposal_review_spec` REQUIRES a `LaneRouteContext`; there is no `route_audit=None` default anywhere on the lane path. The context reaches **both** the reviewers and the reviser. A `route_audit` exception is never swallowed: a pre-dispatch failure is route-fatal.
- **Attempt budget on every lane call (FR-033, F2).** `reservation_authority` is threaded through the SAME path as `route_audit` — reviewers and reviser alike. `execute` gates the ENTIRE reservation path on `if not candidate.pricing.is_free:` (`execute.py:403`), so the authority is **never consulted for a free candidate** — it is not called with 0, it is not called at all. (That is also what makes Slice 1A T7's strictly-positive `reserve()` contract safe.) It MUST still be injected on every lane call, so a paid candidate can never dispatch outside the Attempt cap.
- **Two-attempt reroute, no new profile (FR-002, ReviewSpec table lines 279-280).** Attempt 1: the delivered **`independent_review`** profile (`required_independence={family}`, `require_fresh_snapshot=True`, `max_catalog_age_s=900`) + `independence_against(<proposer baseline>)`. On **`ModelUnavailable`** → attempt 2: the delivered **`deep_review`** profile (no family constraint, `max_catalog_age_s=3600`) — **degrade, never fail closed** (a proposal produces/merges no code). Only a raw `ModelUnavailable` triggers the reroute: `ChainExhausted`, `RouteAuditError`, and `RouteReplayError` MUST NOT.
- **The degradation record is an EXPLICIT, SCHEMA-CHECKED event, never an inference (F10, F6).** A `ReviewRerouted` lane event names `{operation_id, lens, primary_profile, fallback_profile, primary_route_id, fallback_route_id, primary_failure {exception_type, message}, relaxed_constraints}`, and its payload is validated at the write boundary against the one sanctioned reroute. `relaxed_constraints = ["family_independence", "snapshot_freshness"]` is FACTUAL (what the fallback always relaxes), NOT a causal claim — `ModelUnavailable` carries only a textual reason and four documented causes, so the code cannot infer WHICH constraint failed.
- **If a mandatory provenance record cannot be made durable, the route fails (FR-033a, F4).** This covers the `ReviewRerouted` record as much as the audit sink's own events: `record_reroute` normalizes every persistence failure to `RouteAuditError`, and the fallback leg does not dispatch until the record has landed. A review that ran on the fallback with no durable record would be claiming an independence it never had.
- **Degradation provenance carries all four FR-002 fields (F5).** `primary_failure = {exception_type, message, requirement_digest, snapshot_provenance}` (spec line 149). The last two are **joined** from the primary leg's `SelectionFailure` (which slice-0 already emits, `route.py:236-240`) rather than duplicated into the reroute payload — two copies of the same fact can disagree; a join cannot.
- **Stage-specific LLM-call ceiling (Policy Contract line 313), enforced DURABLY per Attempt.** The proposal review is NOT single-route: every reviewer operation is up to two logical `route_chat` invocations, so the proposal ceiling is **`4N + R·(2N + 2)`** (N = panel size, R = `max_rounds`); with N=5, R=3 that is **56**. The `2N` term is R1 (each reviewer: normal call + at most one action-item resubmit), doubled by the reroute; the `+2` is the reviser's at-most-two attempts per round (the engine's malformed-reply retry) and is NOT doubled (the producer has no independence constraint, hence no reroute). **A logical `route_chat` invocation is the unit** — 026's provider-level transient retries are internal and do NOT count. Line 313 scopes the ceiling to the **Attempt**, which outlives any panel process, so admission is a CAS append to the lane log (Slice 1A's `LaneCallLedger`), never an in-memory counter (round-4 F1). Exceeding it fails the Attempt.
- **Every lane route id is retry-stable and comes from the ledger.** `LaneRouteContext.claim_route` is the only place a lane `route_id` is minted, and it derives it deterministically from `(attempt_id, operation_id, leg)`. A replayed logical call therefore re-presents the SAME id, which is what lets slice-0's `claim_dispatch` recognize the replay instead of dispatching twice (`route.py:291-293`). Callers derive `operation_id` from their own content and pass it through `next_operation_id`, which distinguishes a legitimate in-process repeat (the engine's reviser retry) from a restart replay.
- **A convergence run is NOT resumed across processes; a crashed Attempt fails closed (spec FR-033(d), FR-033a).** This is the invariant that makes the operation-id scheme above sufficient, so it is stated here rather than left implicit (round-5 review F2). Spec 025 line 220: "The Attempt ledger is per-Attempt: **a crashed Attempt is a failed Attempt** whose reservations reconcile against the 026 ledger." Line 212's route-replay disposition says the same from the other side: "an unresolved `dispatch_started` with no `dispatch_completed` becomes `dispatch_unknown` and **the Attempt fails closed**." There is no partially-executed panel that a second process picks up mid-run: `run_proposal_review` drives R1→R3 within one process, and a crash ends that Attempt. A retry is a NEW Attempt with a NEW `attempt_id`, hence a disjoint route-id space. Consequently the only cross-process re-presentation of an existing `attempt_id` is a **duplicate/zombie worker**, and for that the correct behavior is exactly what the scheme produces: the same operation re-derives the same `route_id`, `claim_dispatch` reports a replay, and the Attempt fails closed. **Any future slice that introduces resumable convergence MUST replace the in-process repeat counter with a durable workflow position** (stage, run, round, lens, kind, retry ordinal) — a content digest plus a process-local ordinal cannot tell "resumed after a completed identical call" from "replay of a crashed one". Do not add resume without doing that first.
- **The lane reviser makes EXACTLY ONE `route_chat` call per `revise()`.** The existing `convergence/revisers/*` classes route through `invoke_reviser_backend` → `run_with_self_consistency`, which makes up to THREE calls per `revise()` (first pass + self-consistency audit + corrective re-pass, `_self_consistency.py:147-236`). That would break the `+2`-per-round ceiling term above, so the lane reviser MUST NOT use that path.
- **Convergence types cannot carry the degradation.** `Concern` and `Verdict` are pydantic `_Strict` models (`model_config = ConfigDict(extra="forbid")`, `types.py:128-129`), so no field may be added to them. Provenance lives in lane events (above) — this is why `InvocationIdentity` is sourced from the audit stream, not from `ConvergenceResult`.
- **`run_convergence` is UNCHANGED.** No new parameter, no new branch. Independence is wired into the `Reviewer` objects at construction, before `spec.reviewers` is handed to the engine (spec line 283: "a **025 slice-1 task entirely in `convergence/`**").
- **Behavior-preserving for every existing caller.** With the new params omitted, `chat_with_model_fallback`/`_walker_route`/`LLMReviewer` behave byte-for-byte as today; the research/paper pipeline is untouched. The full non-slow suite (`pytest tests/unit tests/contract tests/integration -m "not slow"`) MUST stay green after every task.
- **Route through the chokepoint; no model-id literals in lane code (SC-008, FR-001).** Reviewers express intent purely via `profile`; `model_selection/enforcement.py` statically verifies no pin is introduced.
- **Real tests, no mocks (Constitution III).** Protocol test doubles with real logic, real temp-git repos, the real `EventStoreRouteAudit`/`AttemptCreditLedger`, and the REAL `run_convergence` engine. `unittest.mock` is not the primary path.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push.**

## Dependencies + scope boundary

**Consumes (Slice 1A, must be implemented first):** `EventStoreRouteAudit(*, repo, problem_id, attempt_id, actor, clock, config=LaneLogConfig())` (implements slice-0 `RouteAudit`), `AttemptCreditLedger(*, repo, problem_id, attempt_id, attempt_budget_credits, actor, clock, config=LaneLogConfig())` (implements slice-0 `ReservationAuthority`), `LaneCallLedger(*, repo, problem_id, attempt_id, call_ceiling, attempt_budget_credits, actor, clock, config=LaneLogConfig())` + `LaneCallCeilingExceeded` (Slice 1A **Task 14**), `bind_attempt_config`/`AttemptConfigMismatch` (**Task 13** — the ceiling and the credit budget are bound durably, so a ledger presenting a different value fails closed at construction), `LaneLogConfig`, `lane_log.append/read`, `LaneRevisionConflict`, `LaneContention`, `Event`, `derive_event_id`, `derive_route_id`, `LEGS`, `KNOWN_EVENT_TYPES_V1`, `TYPE_VALIDATORS`, `_require`.

**Out of scope (later slices):** the **patch** review (`self_improvement_patch` — fail-closed single-attempt independence; it reuses the `LLMReviewer` mechanism built here but is the pre-merge gate, US3+); the Attempt lifecycle transitions (`proposal_verified`/`rejected` state writes — Slice 1A deliberately deferred Attempt-failure semantics); discovery logic (error mining, issue ranking, the proposer that CREATES a proposal). This plan wires the REVIEW of a proposal, not its creation.

**Deliberately NOT changed:** `reasoning_chat` (`router.py:320-349`) and `invoke_reviser_backend` (`_self_consistency.py:147-179`) keep their current unplumbed behavior. They serve the research/paper pipeline, whose calls are NOT lane calls — the mandatory-sink requirement is scoped to lane LLM calls (SC-008). The lane reviser reaches `route_chat` through the plumbed `chat_with_model_fallback` instead.

## File Structure

- `src/llmxive/self_improvement/route_context.py` — `LaneRouteContext` (the three mandatory hooks, `next_operation_id`, `claim_route`, `record_reroute`) + the ceiling arithmetic (`proposal_call_ceiling`, `patch_call_ceiling`, `attempt_call_ceiling`). One responsibility: what every lane LLM call needs. `LaneCallCeilingExceeded` is re-exported from Slice 1A's `call_ledger`, not redefined.
- `src/llmxive/self_improvement/events.py` — **modified**: add `ReviewRerouted` to `KNOWN_EVENT_TYPES_V1` (a vocabulary extension — no `SCHEMA_VERSION` bump, per Slice 1A's F7 rule) and register its validator in `TYPE_VALIDATORS`.
- `src/llmxive/self_improvement/invocation_identity.py` — `InvocationIdentity`, `IndependenceDegraded`, `InvocationIdentityError`, `build_invocation_identity`. One responsibility: the audit-derived provenance record.
- `src/llmxive/convergence/lane_reviser.py` — `LaneProposalReviser` (implements `Reviser`; exactly one routed call per `revise()`).
- `src/llmxive/convergence/self_improvement_specs.py` — `PROPOSAL_STAGE`, `PROPOSAL_LENSES`, `build_proposal_review_spec`, `run_proposal_review`.
- `src/llmxive/backends/router.py` — **modified**: `_walker_route` + `chat_with_model_fallback` forward the five spec-025 params.
- `src/llmxive/convergence/llm_reviewer.py` — **modified**: `LLMReviewer.__init__` accepts the lane context + independence params; `_route_review` implements the two-attempt reroute; `_STAGE_PREFIX` gains the lane stage.
- `agents/prompts/panels/panel_si_proposal_<lens>.md` × 5 — the proposal lens prompts.

---

### Task 1: `ReviewRerouted` event type

**Files:**
- Modify: `src/llmxive/self_improvement/events.py`
- Test: `tests/unit/test_self_improvement_events.py` (extend)

**Interfaces:**
- Consumes: `KNOWN_EVENT_TYPES_V1`, `SCHEMA_VERSION`, `SUPPORTED_SCHEMA_VERSIONS`, `TYPE_VALIDATORS`, `_require` (Slice 1A Task 2).
- Produces: `"ReviewRerouted"` added to `KNOWN_EVENT_TYPES_V1`. **No `SCHEMA_VERSION` bump** — per Slice 1A's F7 rule, extending the event VOCABULARY does not change the record SHAPE, and bumping would make a reader reject prior-version history.
- Produces: `_validate_review_rerouted`, **registered in Slice 1A's `TYPE_VALIDATORS`** (round-4 review F6). Adding the type to the vocabulary alone leaves the payload unchecked, and this is not a passive record: Task 6 reads `p["primary_profile"]`/`p["primary_failure"]`/`p["relaxed_constraints"]` to build the degradation provenance, so a missing key becomes a `KeyError` inside the projection and a wrong value becomes **false provenance about which safeguards were relaxed**. The contract:

  | Key | Rule |
  |-|-|
  | `operation_id`, `lens` | non-empty `str` |
  | `primary_route_id`, `fallback_route_id` | non-empty `str`, and **distinct** (the two legs are two logical calls) |
  | `primary_profile` | exactly `"independent_review"` (FR-002's required-family leg) |
  | `fallback_profile` | exactly `"deep_review"` (FR-002's named fallback) |
  | `primary_failure` | mapping with non-empty `str` `exception_type` + `message`; `exception_type` must be exactly `"ModelUnavailable"` — FR-002 reroutes on nothing else, so any other value means the reroute fired for an unsanctioned reason |
  | `relaxed_constraints` | exactly `["family_independence", "snapshot_freshness"]`, in order — the fallback ALWAYS relaxes both, so any other list is a false claim about what was given up |

  The profile/exception/constraint values are pinned to **v1's sanctioned reroute** deliberately. A later stage that reroutes differently must EXTEND this validator (adding its own sanctioned combination) — never bypass it.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/test_self_improvement_events.py
def test_review_rerouted_is_a_known_event_type():
    # Slice 1B: the explicit FR-002 degradation record (F10) — a VOCABULARY extension,
    # so SCHEMA_VERSION must NOT change (Slice 1A F7: a bump would invalidate history).
    from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1, SCHEMA_VERSION
    assert "ReviewRerouted" in KNOWN_EVENT_TYPES_V1
    assert SCHEMA_VERSION == 1

_OP = "op-1"

def _reroute_payload(**kw):
    from llmxive.self_improvement.events import derive_route_id
    base = {
        "operation_id": _OP, "lens": "worthwhile-improvement",
        "primary_profile": "independent_review", "fallback_profile": "deep_review",
        "primary_route_id": derive_route_id("A1", _OP, "primary"),
        "fallback_route_id": derive_route_id("A1", _OP, "fallback"),
        "primary_failure": {"exception_type": "ModelUnavailable", "message": "no independent family live"},
        "relaxed_constraints": ["family_independence", "snapshot_freshness"],
    }
    base.update(kw)
    return base

def _reroute_event(**kw):
    return _raw(event_type="ReviewRerouted", attempt_id="A1", payload=_reroute_payload(**kw))

def test_review_rerouted_event_validates():
    from llmxive.self_improvement.events import validate_lane_event
    validate_lane_event(_reroute_event())  # no raise

def test_review_rerouted_route_ids_are_recomputed_at_write_time():
    # Round-6 hardening: the same binding build_invocation_identity checks at projection
    # time is now enforced at WRITE time, so a foreign/borrowed leg never becomes durable.
    from llmxive.self_improvement.events import derive_route_id, validate_lane_event
    foreign = derive_route_id("A2", _OP, "primary")
    with pytest.raises(ValueError, match="primary_route_id"):
        validate_lane_event(_reroute_event(primary_route_id=foreign))
    with pytest.raises(ValueError, match="attempt_id"):
        validate_lane_event(_raw(event_type="ReviewRerouted", attempt_id=None,
                                 payload=_reroute_payload()))

def test_review_rerouted_is_registered_for_payload_validation():
    # F6: vocabulary membership alone leaves the payload unchecked.
    from llmxive.self_improvement.events import TYPE_VALIDATORS
    assert "ReviewRerouted" in TYPE_VALIDATORS

def test_review_rerouted_rejects_unknown_keys():
    # Round-5 F6: the schema is EXACT, not merely "required fields present" — otherwise a
    # typo'd key is indistinguishable from a new one and the contract is untestable.
    from llmxive.self_improvement.events import validate_lane_event
    with pytest.raises(ValueError, match="unexpected ReviewRerouted payload keys"):
        validate_lane_event(_reroute_event(surprise="extra"))
    with pytest.raises(ValueError, match="unexpected ReviewRerouted primary_failure keys"):
        validate_lane_event(_reroute_event(
            primary_failure={"exception_type": "ModelUnavailable", "message": "x", "extra": 1}))

@pytest.mark.parametrize("bad, why", [
    # both legs the same id: caught by the write-time derivation check (two identical ids
    # cannot both be correct derivations), with the distinctness guard behind it
    ({"primary_route_id": "same", "fallback_route_id": "same"}, "route_id"),
    ({"primary_profile": "deep_review"}, "primary_profile"),
    ({"fallback_profile": "standard_generation"}, "fallback_profile"),
    ({"primary_failure": {"exception_type": "ChainExhausted", "message": "x"}}, "ModelUnavailable"),
    ({"primary_failure": {"message": "x"}}, "exception_type"),
    ({"relaxed_constraints": ["family_independence"]}, "relaxed_constraints"),
    ({"relaxed_constraints": ["snapshot_freshness", "family_independence"]}, "relaxed_constraints"),
    ({"lens": ""}, "lens"),
])
def test_review_rerouted_rejects_malformed_payloads(bad, why):
    # Each of these would otherwise land durably and then either KeyError inside
    # build_invocation_identity or assert a FALSE claim about what the fallback relaxed.
    from llmxive.self_improvement.events import validate_lane_event
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_reroute_event(**bad))

def test_review_rerouted_rejects_a_missing_key():
    from llmxive.self_improvement.events import validate_lane_event
    payload = _reroute_payload()
    del payload["fallback_route_id"]
    with pytest.raises(ValueError, match="fallback_route_id"):
        validate_lane_event(_raw(event_type="ReviewRerouted", attempt_id="A1", payload=payload))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_events.py -k review_rerouted -q`
Expected: FAIL — `AssertionError` (`"ReviewRerouted" not in KNOWN_EVENT_TYPES_V1`).

- [ ] **Step 3: Write minimal implementation**

In `src/llmxive/self_improvement/events.py`, add the type to the existing frozenset AND register its payload validator (Slice 1A Task 2 built both the frozenset and the `TYPE_VALIDATORS` table + the `_require` helper; validators receive the WHOLE raw event):

```python
KNOWN_EVENT_TYPES_V1 = frozenset({
    "ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet",
    "AttemptCreditReserved", "AttemptCreditReleased", "AttemptCreditRetained", "AttemptCreditReconciled",
    "LaneCallClaimed",
    "ChainResolved", "SelectionFailure", "ReservationOpened", "DispatchStarted",
    "DispatchCompleted", "DispatchUnknown", "CandidateOutcome",
    "ProblemDiscovered", "Proposed", "ProposalVerified", "Rejected",
    # Slice 1B (FR-002): the EXPLICIT proposal-review degradation record. Its payload is
    # schema-checked by _validate_review_rerouted below (F6). `relaxed_constraints` is
    # FACTUAL (what the fallback always relaxes), NOT a causal claim about which
    # constraint made the primary fail. A vocabulary extension only — the record SHAPE is
    # unchanged, so SCHEMA_VERSION stays 1 (F7).
    "ReviewRerouted",
})

#: The ONE sanctioned proposal reroute (FR-002). Pinned, not merely documented: a record
#: naming other profiles would assert a degradation that never happened.
_REROUTE_PRIMARY_PROFILE = "independent_review"
_REROUTE_FALLBACK_PROFILE = "deep_review"
_REROUTE_TRIGGER = "ModelUnavailable"
_REROUTE_RELAXED = ["family_independence", "snapshot_freshness"]

#: The EXACT key set (round-5 F6). "Required fields" alone would let extras ride along:
#: harmless today, but it makes the contract untestable and future schema evolution
#: ambiguous — a reader could not tell a typo'd key from a new one. Matches the house
#: style of the convergence types (`extra="forbid"`, `types.py:128-129`).
_REROUTE_KEYS = frozenset({
    "operation_id", "lens", "primary_profile", "fallback_profile",
    "primary_route_id", "fallback_route_id", "primary_failure", "relaxed_constraints",
})
_REROUTE_FAILURE_KEYS = frozenset({"exception_type", "message"})

def _validate_review_rerouted(raw: Mapping[str, Any]) -> None:
    """FR-002's degradation record. Task 6 builds `IndependenceDegraded` straight out of
    this payload, so an unchecked key is either a KeyError in the projection or — worse —
    a FALSE claim about which safeguards the fallback gave up."""
    payload = raw["payload"]
    _exact_keys(payload, _REROUTE_KEYS, "ReviewRerouted payload")
    for key in ("operation_id", "lens", "primary_route_id", "fallback_route_id"):
        _require(payload, key, str)
    # Round-6 hardening: recompute BOTH legs at WRITE time from the envelope's attempt_id,
    # the same check build_invocation_identity performs at projection time. The projection
    # already fails closed, so this is defense in depth — but a record that can never
    # become durable is strictly better than one that is rejected only when read.
    attempt_id = raw.get("attempt_id")
    if not attempt_id:
        raise ValueError("a ReviewRerouted event must carry its envelope attempt_id")
    for key, leg in (("primary_route_id", "primary"), ("fallback_route_id", "fallback")):
        expected = derive_route_id(attempt_id, payload["operation_id"], leg)
        if payload[key] != expected:
            raise ValueError(
                f"{key}={payload[key]!r} is not attempt {attempt_id!r}'s {leg} claim for "
                f"operation {payload['operation_id']!r} — expected {expected!r}"
            )
    if payload["primary_route_id"] == payload["fallback_route_id"]:
        raise ValueError("primary_route_id and fallback_route_id must be distinct "
                         "(the two legs are two logical route_chat invocations)")
    primary = _require(payload, "primary_profile", str)
    if primary != _REROUTE_PRIMARY_PROFILE:
        raise ValueError(f"primary_profile must be {_REROUTE_PRIMARY_PROFILE!r}, got {primary!r}")
    fallback = _require(payload, "fallback_profile", str)
    if fallback != _REROUTE_FALLBACK_PROFILE:
        raise ValueError(f"fallback_profile must be {_REROUTE_FALLBACK_PROFILE!r}, got {fallback!r}")
    failure = _require(payload, "primary_failure", Mapping)
    _exact_keys(failure, _REROUTE_FAILURE_KEYS, "ReviewRerouted primary_failure")
    for key in ("exception_type", "message"):
        _require(failure, key, str)
    if failure["exception_type"] != _REROUTE_TRIGGER:
        raise ValueError(f"primary_failure.exception_type must be {_REROUTE_TRIGGER!r} — FR-002 "
                         f"reroutes on nothing else; got {failure['exception_type']!r}")
    relaxed = _require(payload, "relaxed_constraints", list)
    if relaxed != _REROUTE_RELAXED:
        raise ValueError(f"relaxed_constraints must be exactly {_REROUTE_RELAXED} (the fallback "
                         f"always relaxes both, in that order), got {relaxed!r}")

TYPE_VALIDATORS["ReviewRerouted"] = _validate_review_rerouted

# (`_exact_keys`, `_require`, and `derive_route_id` all come from Slice 1A Task 2.)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_events.py -q`
Expected: PASS (all, including the 16 new cases: 2 vocabulary/registration + 1 valid payload + 1 write-time route-id binding + 8 parametrized malformed + 1 missing-key + 2 unknown-key + 1 missing-envelope-attempt).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/events.py tests/unit/test_self_improvement_events.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T1): ReviewRerouted event type (vocabulary extension, no schema bump)"
```

---

### Task 2: `LaneRouteContext` — mandatory hooks + durable route admission

**Files:**
- Create: `src/llmxive/self_improvement/route_context.py`
- Test: `tests/integration/test_self_improvement_route_context.py`

**Interfaces:**
- Consumes: slice-0 `RouteAudit`/`ReservationAuthority` protocols and `RouteAuditError`; Slice-1A `LaneCallLedger`, `LaneCallCeilingExceeded`, `LaneLogConfig`, `lane_log.append`, `LaneContention`, `LaneRevisionConflict`, `Event`, `derive_event_id`, `GitLogError`.
- Produces:
  - `def proposal_call_ceiling(panel_size, max_rounds) -> int` — `4N + R·(2N + 2)`, and `def patch_call_ceiling(panel_size, max_rounds) -> int` — `2N + R·(N + 2)` (Policy Contract line 313). **Stage COMPONENTS, not limits.**
  - `def attempt_call_ceiling(*, proposal_panel, patch_panel, max_rounds, impl_regen_retries=1) -> int` — the WHOLE line-313 expression: `proposer + implementer·(1 + impl_regen_retries) + proposal component + patch component`. **This is the only value that may be written into `AttemptConfigured`** (round-5 review F1).
    **Why this replaces the round-4 wiring:** every `LaneCallLedger` in the round-4 plan was constructed with `proposal_call_ceiling(...)` — 56. That was survivable while the ceiling was per-panel, but round-5's `AttemptConfig` makes the first bound value **immutable for the Attempt**, which turns it into two defects: (a) the proposer's and implementer's calls, claimed against the same Attempt, eat the proposal panel's allowance; and (b) when a later slice tries to bind the real whole-Attempt figure, `AttemptConfigMismatch` rejects it because 56 was bound first. Spec 025 defines ONE per-Attempt ceiling spanning all stages, so that is what gets bound.
  - `IMPL_REGEN_RETRIES = 1` (Policy Contract line 312).
  - `PATCH_LENSES` and `LANE_ATTEMPT_CEILING` are produced by **Task 7** (`self_improvement_specs.py`), which already owns `PROPOSAL_LENSES`/`PROPOSAL_MAX_ROUNDS` and can import this module — `route_context` must NOT import it back (cycle). `LANE_ATTEMPT_CEILING` = `attempt_call_ceiling(proposal_panel=len(PROPOSAL_LENSES), patch_panel=len(PATCH_LENSES), max_rounds=PROPOSAL_MAX_ROUNDS)` = **90** for the canonical panels (`N_p = N_q = 5`, `R = 3`). Every lane ledger in this plan binds THAT.
  - Re-export of `LaneCallCeilingExceeded` for the lane's callers — **imported from `self_improvement.call_ledger`, not redefined** (round-4 F1: the ceiling is a substrate condition).
  - `@dataclass(frozen=True) class LaneRouteContext`: fields `repo: Path`, `problem_id: str`, `attempt_id: str`, `actor: str`, `clock: Callable[[], str]`, `route_audit: RouteAudit`, `reservation_authority: ReservationAuthority`, `call_ledger: LaneCallLedger`, `config: LaneLogConfig = LaneLogConfig()`. All three hooks are **REQUIRED** (no `None` default — F2/F3/F1: there is no unaudited, unbudgeted, or unadmitted lane call). **Frozen** — it holds no mutable counter any more, because the spend now lives in the durable log.
  - `def next_operation_id(self, base: str) -> str` — resolves a caller's content-derived `base` into this call's operation id: the first use in a process returns it unchanged, each in-process repeat appends `#1`, `#2`, …. **This is not decoration — it is what keeps the durable claim correct in both directions.** A pure content digest gives the two properties we need (distinct logical calls differ; a RESTART re-derives the same id so `claim_dispatch` recognizes the replay), but two callers legitimately re-issue an *identical* call inside one process: the engine re-invokes `revise(artifacts, concerns)` with byte-identical arguments after a malformed reply (`engine.py:519-533`), and a round with no artifact change can produce a rereview prompt identical to the previous round's. Those are new logical calls that already dispatched once, so they need new ids and their own ceiling charge — the ceiling's `+2` per round exists exactly for the reviser's second attempt. Without the sequencer they would replay the first claim, receive the first `route_id`, and be REFUSED at the dispatch gate.
  - `def claim_route(self, *, operation_id: str, leg: str = "primary") -> str` — delegates to `call_ledger.claim(...)`: CAS-admits ONE logical `route_chat` invocation against the **Attempt's** ceiling and returns its retry-stable `route_id`. Raises `LaneCallCeilingExceeded` when the Attempt is spent. Every lane call obtains its route id here, so admission cannot be bypassed. **Replaces the round-3 `next_route_id()`** (round-4 F1): that minted a fresh `uuid4` behind an in-memory counter, so a restart / a retry on another runner / a duplicate worker each got a fresh ceiling AND a fresh route id — the second defeating slice-0's dispatch-idempotency gate on exactly the retry it was built for.
  - `def calls_used(self) -> int` — delegates to the ledger; the DURABLE count, not a local tally.
  - `def record_reroute(self, *, operation_id, lens, primary_route_id, fallback_route_id, exception_type, message) -> None` — appends the `ReviewRerouted` lane event (Task 1) via `lane_log.append(..., expected_revision=None)` with `event_id = derive_event_id(problem_id, f"reroute\x00{primary_route_id}")` (deterministic → an idempotent re-record is a no-op), `primary_profile="independent_review"`, `fallback_profile="deep_review"`, `relaxed_constraints=["family_independence", "snapshot_freshness"]`.
    **A persistence failure here is route-fatal (round-4 F4).** `lane_log.append` raises `GitLogError`/`GitLogAuthError`/`LaneRevisionConflict`/`LaneContention` — none of which `run_proposal_review` (Task 8) classifies, so they would escape raw and bypass the fail-closed contract that mandatory-provenance failures are route-fatal (FR-033a). `record_reroute` therefore normalizes every persistence failure to **`RouteAuditError`**, and Task 4 calls it BEFORE dispatching the fallback: **if the degradation record cannot become durable, the fallback MUST NOT run.** A silently-unrecorded reroute is a review that claims independence it did not have.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_route_context.py
"""The lane context is now backed by the DURABLE call ledger (round-4 F1), so these are
integration tests against a real git repo — an in-memory counter is exactly what the
review rejected."""
import subprocess

import pytest

from llmxive.model_selection.attempt_hooks import RouteAuditError
from llmxive.self_improvement.call_ledger import (
    LaneCallCeilingExceeded, LaneCallLedger, derive_route_id,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import (
    LaneRouteContext, attempt_call_ceiling, patch_call_ceiling, proposal_call_ceiling,
)

_CLOCK = lambda: "2026-07-25T00:00:00+00:00"

class _Sink:
    """A REAL in-memory RouteAudit double (no mock): records + always claims."""
    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True

class _Budget:
    """A REAL in-memory ReservationAuthority double."""
    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass

@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path

_BUDGET = 50.0   # the Attempt credit budget; ONE AttemptConfigured record binds it
                 # together with the call ceiling (Slice 1A Task 13), so every
                 # ledger for this Attempt must present the SAME pair.

def _ctx(repo, ceiling=4):
    ledger = LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                            attempt_budget_credits=_BUDGET, actor="reviewer", clock=_CLOCK,
                            config=LaneLogConfig())
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="reviewer", clock=_CLOCK,
        route_audit=_Sink(), reservation_authority=_Budget(), call_ledger=ledger,
    )

def test_stage_components_match_the_spec_formulas():
    # Policy Contract line 313: proposal run = 4N + R*(2N + 2) (the reroute doubles every
    # reviewer term); patch run = 2N + R*(N + 2) (single-route, fail closed).
    assert proposal_call_ceiling(5, 3) == 56
    assert proposal_call_ceiling(1, 1) == 4 * 1 + 1 * (2 * 1 + 2)  # == 8
    assert patch_call_ceiling(5, 3) == 31
    assert patch_call_ceiling(1, 1) == 2 * 1 + 1 * (1 + 2)         # == 5

def test_the_ATTEMPT_ceiling_is_the_whole_line_313_expression():
    # F1: this — not a stage component — is what AttemptConfigured binds. Spec 025 line
    # 313: proposer + implementer*(1 + impl_regen_retries) + proposal + patch.
    total = attempt_call_ceiling(proposal_panel=5, patch_panel=5, max_rounds=3)
    assert total == 1 + 2 + 56 + 31 == 90
    # and it is STRICTLY larger than any one stage — binding a component would both
    # starve the other stages and permanently lock out the real figure (immutable record)
    assert total > proposal_call_ceiling(5, 3) and total > patch_call_ceiling(5, 3)

def test_impl_regen_retries_moves_the_attempt_ceiling():
    from llmxive.self_improvement.route_context import IMPL_REGEN_RETRIES
    assert IMPL_REGEN_RETRIES == 1                       # Policy Contract line 312 (hard max 1)
    assert attempt_call_ceiling(proposal_panel=5, patch_panel=5, max_rounds=3,
                                impl_regen_retries=0) == 89

def test_each_operation_leg_gets_a_distinct_durable_route_id(repo):
    ctx = _ctx(repo, ceiling=3)
    a = ctx.claim_route(operation_id="lens-a")
    b = ctx.claim_route(operation_id="lens-b")
    c = ctx.claim_route(operation_id="lens-a", leg="fallback")
    assert len({a, b, c}) == 3 and ctx.calls_used() == 3

def test_a_replayed_operation_reuses_its_route_id_and_is_not_recharged(repo):
    # F1's second half: retry-stability. A fresh context (a restart) claiming the SAME
    # logical operation must get the SAME route id back — that is what lets slice-0's
    # claim_dispatch recognize the retry instead of dispatching twice.
    ctx = _ctx(repo, ceiling=3)
    first = ctx.claim_route(operation_id="lens-a")
    assert _ctx(repo, ceiling=3).claim_route(operation_id="lens-a") == first
    assert first == derive_route_id("A1", "lens-a", "primary")
    assert ctx.calls_used() == 1

def test_a_DUPLICATE_WORKER_replays_instead_of_double_dispatching(repo):
    # F2: this is the ONLY way a fresh process legitimately re-presents an existing
    # attempt_id (spec 025 line 220: "a crashed Attempt is a failed Attempt"; a retry gets
    # a NEW attempt_id). The zombie must land on the SAME route_id so slice-0's
    # claim_dispatch reports a replay — never a second dispatch on a fresh id.
    first = _ctx(repo, ceiling=5)
    rid = first.claim_route(operation_id=first.next_operation_id("lens-a:identify:deadbeef"))

    zombie = _ctx(repo, ceiling=5)          # a second process for the SAME attempt
    zid = zombie.claim_route(operation_id=zombie.next_operation_id("lens-a:identify:deadbeef"))

    assert zid == rid, "the duplicate worker minted a NEW route — it would dispatch twice"
    assert zombie.calls_used() == 1, "the replay consumed a second call from the ceiling"

def test_next_operation_id_separates_in_process_repeats_but_not_restarts(repo):
    # The engine re-invokes revise() with byte-identical arguments after a malformed reply
    # (engine.py:519-533); that is a NEW logical call and must not replay the first claim.
    ctx = _ctx(repo, ceiling=5)
    a = ctx.next_operation_id("reviser:abc")
    b = ctx.next_operation_id("reviser:abc")
    assert a == "reviser:abc" and b == "reviser:abc#1" and a != b
    assert ctx.claim_route(operation_id=a) != ctx.claim_route(operation_id=b)
    assert ctx.calls_used() == 2
    # a RESTART starts the sequence over, so the bare base replays the original claim
    fresh = _ctx(repo, ceiling=5)
    assert fresh.next_operation_id("reviser:abc") == "reviser:abc"
    assert fresh.claim_route(operation_id="reviser:abc") == ctx.claim_route(operation_id=a)
    assert fresh.calls_used() == 2   # the replay charged nothing

def test_a_restarted_context_does_not_get_a_fresh_ceiling(repo):
    # THE F1 regression: an in-memory counter would let every new context spend anew.
    _ctx(repo, ceiling=2).claim_route(operation_id="a")
    _ctx(repo, ceiling=2).claim_route(operation_id="b")
    with pytest.raises(LaneCallCeilingExceeded):
        _ctx(repo, ceiling=2).claim_route(operation_id="c")

def test_hooks_are_required(repo):
    # F1/F2/F3: a lane context CANNOT be built without the audit sink, the reservation
    # authority, AND the call ledger — no unaudited/unbudgeted/unadmitted lane call.
    with pytest.raises(TypeError):
        LaneRouteContext(repo=repo, problem_id="P1", attempt_id="A1", actor="a", clock=_CLOCK)

def test_record_reroute_persists_the_explicit_event(repo):
    ctx = _ctx(repo)
    ctx.record_reroute(operation_id="op-1", lens="worthwhile-improvement",
                       primary_route_id="r1", fallback_route_id="r2",
                       exception_type="ModelUnavailable", message="none live")
    rerouted = [e for e in read(repo, "P1") if e.event_type == "ReviewRerouted"]
    assert len(rerouted) == 1
    assert rerouted[0].payload["relaxed_constraints"] == ["family_independence", "snapshot_freshness"]
    # idempotent: the same reroute re-recorded is a no-op, not a second event
    ctx.record_reroute(operation_id="op-1", lens="worthwhile-improvement",
                       primary_route_id="r1", fallback_route_id="r2",
                       exception_type="ModelUnavailable", message="none live")
    assert len([e for e in read(repo, "P1") if e.event_type == "ReviewRerouted"]) == 1

def test_a_reroute_persistence_failure_is_route_fatal(repo, monkeypatch):
    # F4: lane_log.append raises GitLog*/LaneRevisionConflict, which run_proposal_review
    # does NOT classify — they would escape raw and bypass the fail-closed contract.
    # record_reroute normalizes them, so the caller (Task 4) can refuse to run the
    # fallback when the degradation record did not become durable.
    from llmxive.git_event_log import GitLogAuthError

    def _boom(*a, **kw):
        raise GitLogAuthError("push denied")

    monkeypatch.setattr("llmxive.self_improvement.route_context.append", _boom)
    with pytest.raises(RouteAuditError):
        _ctx(repo).record_reroute(operation_id="op-1", lens="l", primary_route_id="r1",
                                  fallback_route_id="r2", exception_type="ModelUnavailable",
                                  message="none live")
```

**Three corrections applied during implementation:**

1. **The test's `record_reroute` calls must pass DERIVED route ids.** The draft above uses `primary_route_id="r1"`/`fallback_route_id="r2"`, but Task 1's write-time hardening recomputes both legs from the envelope `attempt_id` + `operation_id` — so those literals are rejected at the write boundary. The shipped test uses `derive_route_id("A1", operation_id, leg)`, and an added case asserts that an underived id is refused (which is the stronger contract, and the reason Task 1 added the check).
2. **The persistence-failure test induces a REAL failure, not a monkeypatched one.** The draft patched `route_context.append` to raise. Instead the context points at a remote whose lane ref was never bootstrapped, so `sync_and_verify` fails closed with a genuine `GitLogAuthError` — same code path, no patching (Constitution III).
3. **`derive_route_id` is imported from `events`, not `call_ledger`.** The draft's import works by accident (`call_ledger` imports the name) but names the wrong owner.

**Note on "frozen — holds no mutable counter":** the SPEND counter is gone (it is durable now), but `next_operation_id` still needs a process-local repeat sequencer, so the frozen dataclass carries a `_repeats: dict` field (`compare=False`, `repr=False`). Mutating a dict inside a frozen dataclass is fine — frozen binds the fields, not their contents. The two are different things and the docstring says so.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_route_context.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.self_improvement.route_context'`. Then PASS at **13 passed**; removing `record_reroute`'s error normalization fails 2 of them.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/route_context.py
"""What EVERY lane LLM call carries (FR-033a): the mandatory durable audit sink, the
Attempt credit authority, and the Attempt call ledger that admits the call and hands back
its route id.

All three hooks are REQUIRED, not optional (maintainer review F1/F2/F3): a lane call that
skipped one would be an unaudited routing decision, an unbudgeted paid dispatch, or a call
outside the Attempt's ceiling. Admission is DURABLE — it lives in the append-only lane log,
not in this object — because Policy Contract line 313 scopes the ceiling to the ATTEMPT,
which outlives any one panel process (round-4 F1). That also makes route ids retry-stable,
which is what lets slice-0's ``claim_dispatch`` gate recognize a replayed call."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.git_event_log import GitLogError
from llmxive.model_selection.attempt_hooks import (
    ReservationAuthority, RouteAudit, RouteAuditError,
)
from llmxive.self_improvement.call_ledger import LaneCallCeilingExceeded, LaneCallLedger
from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lane_log import (
    LaneContention, LaneLogConfig, LaneRevisionConflict, append,
)

__all__ = ["IMPL_REGEN_RETRIES", "LaneCallCeilingExceeded", "LaneRouteContext",
           "attempt_call_ceiling", "patch_call_ceiling", "proposal_call_ceiling"]

#: The constraints the FR-002 fallback ALWAYS relaxes — factual (what changed), NOT a
#: causal claim about which one made the primary attempt fail (ModelUnavailable carries
#: only a textual reason and four documented causes).
RELAXED_CONSTRAINTS = ("family_independence", "snapshot_freshness")
PRIMARY_PROFILE = "independent_review"
FALLBACK_PROFILE = "deep_review"

#: Policy Contract line 313: "impl_regen_retries = 1 (hard max 1)".
IMPL_REGEN_RETRIES = 1

def proposal_call_ceiling(panel_size: int, max_rounds: int) -> int:
    """The PROPOSAL stage COMPONENT ``4N + R*(2N + 2)`` (Policy Contract line 313): every
    reviewer operation is up to TWO logical route_chat invocations (the FR-002 reroute), so
    each reviewer term doubles; the reviser's ``+2`` (producer — no independence, no
    reroute) does not.

    **This is a component, NOT the Attempt's limit** (round-5 F1) — see
    :func:`attempt_call_ceiling`. Binding it as the Attempt ceiling would both let the
    proposal panel eat the proposer's and implementer's allowance and, because
    ``AttemptConfigured`` is immutable, permanently lock out the real figure."""
    return 4 * panel_size + max_rounds * (2 * panel_size + 2)

def patch_call_ceiling(panel_size: int, max_rounds: int) -> int:
    """The PATCH stage component ``2N + R*(N + 2)`` (Policy Contract line 313). The patch
    review is single-route (fail closed, no reroute), so its reviewer term does NOT double.
    Used only as a term of :func:`attempt_call_ceiling`; the patch stage itself is a later
    slice."""
    return 2 * panel_size + max_rounds * (panel_size + 2)

def attempt_call_ceiling(*, proposal_panel: int, patch_panel: int, max_rounds: int,
                         impl_regen_retries: int = IMPL_REGEN_RETRIES) -> int:
    """THE per-Attempt ceiling — the whole Policy Contract line 313 expression:

        ``proposer + implementer·(1 + impl_regen_retries)
          + [proposal: 4N_p + R·(2N_p + 2)] + [patch: 2N_q + R·(N_q + 2)]``

    This is the number that goes into ``AttemptConfigured``. Spec 025 defines ONE ceiling
    per Attempt covering every stage, not a per-stage sub-budget, and the record is
    immutable once bound — so a stage component must never be written as the Attempt's
    limit (round-5 F1)."""
    return (
        1                                                        # the proposer's one call
        + (1 + impl_regen_retries)                               # implementer + regenerations
        + proposal_call_ceiling(proposal_panel, max_rounds)
        + patch_call_ceiling(patch_panel, max_rounds)
    )

@dataclass(frozen=True)
class LaneRouteContext:
    repo: Path
    problem_id: str
    attempt_id: str
    actor: str
    clock: Callable[[], str]
    route_audit: RouteAudit                      # REQUIRED (F3) — mandatory durable sink
    reservation_authority: ReservationAuthority  # REQUIRED (F2) — Attempt budget gate
    call_ledger: LaneCallLedger                  # REQUIRED (F1) — durable Attempt ceiling
    config: LaneLogConfig = LaneLogConfig()
    #: In-process repeat counter for `next_operation_id` (see its docstring). Not state the
    #: lane depends on for correctness — the ledger is — just a within-process disambiguator.
    #: The panel dispatches reviewers on a ThreadPoolExecutor (`engine.py:85-133`), so it is
    #: lock-guarded.
    _seq: dict[str, int] = field(default_factory=dict, init=False, repr=False, compare=False)
    _seq_lock: threading.Lock = field(default_factory=threading.Lock, init=False,
                                      repr=False, compare=False)

    def next_operation_id(self, base: str) -> str:
        """Resolve a caller's content-derived ``base`` into the operation id for THIS call.

        A pure content digest is right for the two cases that matter — distinct logical
        calls have distinct content, and a RESTART replaying the same call re-derives the
        same id (so slice-0's ``claim_dispatch`` recognizes the replay). But it is wrong for
        a caller that legitimately re-issues an IDENTICAL call within one process, and there
        are two such callers: the engine's malformed-reply reviser retry re-invokes
        ``revise(artifacts, concerns)`` with byte-identical arguments (``engine.py:519-533``),
        and a round that produced no artifact change can hand a reviewer a rereview prompt
        identical to the previous round's. Those are genuinely NEW logical calls — the first
        one dispatched — so they need new ids and a new ceiling charge (the ceiling's ``+2``
        per round exists precisely to pay for the reviser's second attempt). Without this
        they would replay the first claim, get the first ``route_id`` back, and be REFUSED at
        the dispatch gate.

        So: the FIRST use of a base in this process returns it unchanged; each repeat
        appends ``#1``, ``#2``, …. A fresh process starts again at the bare base.

        **Why a process-local ordinal is sufficient here, and exactly when it stops being
        sufficient (round-5 review F2).** An ordinal cannot, in general, tell "resumed after
        a completed identical call" from "replay of a crashed one" — both present the same
        content in a fresh process. It is sufficient in THIS design because spec 025 has no
        resumable convergence: "a crashed Attempt is a failed Attempt" (line 220) and an
        unresolved dispatch "fails the Attempt closed" (line 212). One ``run_proposal_review``
        drives R1→R3 in one process; a retry is a NEW Attempt with a NEW ``attempt_id`` and
        therefore a disjoint route-id space. So the only way an existing ``attempt_id`` is
        re-presented from a fresh process is a DUPLICATE/ZOMBIE worker — and for that, bare-base
        re-derivation is precisely the behavior we want: same ``route_id`` → ``claim_dispatch``
        reports a replay → the Attempt fails closed instead of double-dispatching.

        If a later slice ever makes convergence resumable, this method MUST be replaced by a
        durable workflow position (stage, run, round, lens, call kind, retry ordinal) — which
        also means the engine must pass round metadata down. Do not add resume without it."""
        with self._seq_lock:
            n = self._seq.get(base, 0)
            self._seq[base] = n + 1
        return base if n == 0 else f"{base}#{n}"

    def claim_route(self, *, operation_id: str, leg: str = "primary") -> str:
        """Admit ONE logical route_chat invocation against the ATTEMPT's ceiling and return
        its retry-stable route id. Every lane call obtains its id here, so neither the
        ceiling nor the id stability can be bypassed. Raises ``LaneCallCeilingExceeded``.

        ``operation_id`` must come from :meth:`next_operation_id`. Both legs of one FR-002
        reroute share ONE resolved operation id and differ only by ``leg``."""
        return self.call_ledger.claim(operation_id=operation_id, leg=leg)

    def calls_used(self) -> int:
        """The DURABLE spend for this Attempt (read from the log, not a local tally)."""
        return self.call_ledger.calls_used()

    def record_reroute(self, *, operation_id: str, lens: str, primary_route_id: str,
                       fallback_route_id: str, exception_type: str, message: str) -> None:
        """Append the EXPLICIT ``ReviewRerouted`` record (F10) — the projection never has
        to infer a degradation from an accidental event pattern.

        Any persistence failure is normalized to ``RouteAuditError`` (F4). The raw
        ``GitLog*``/``Lane*`` types are NOT in ``run_proposal_review``'s classification set
        (Task 8), so they would escape as unclassified errors and bypass FR-033a's rule
        that a mandatory-provenance failure is route-fatal. The caller (Task 4) records
        BEFORE dispatching the fallback, so a reroute that cannot be made durable stops the
        review instead of silently producing a review that claims independence it lacked."""
        event = Event(
            event_id=derive_event_id(self.problem_id, f"reroute\x00{primary_route_id}"),
            event_type="ReviewRerouted", problem_id=self.problem_id, actor=self.actor,
            payload={
                "operation_id": operation_id, "lens": lens,
                "primary_profile": PRIMARY_PROFILE, "fallback_profile": FALLBACK_PROFILE,
                "primary_route_id": primary_route_id, "fallback_route_id": fallback_route_id,
                "primary_failure": {"exception_type": exception_type, "message": message},
                "relaxed_constraints": list(RELAXED_CONSTRAINTS),
            },
            timestamp=self.clock(), attempt_id=self.attempt_id,
        )
        try:
            append(self.repo, event, expected_revision=None, config=self.config)
        except (GitLogError, LaneRevisionConflict, LaneContention, ValueError) as exc:
            # GitLogError (+ its auth/contention subclasses): the ref could not be read or
            # advanced. LaneRevisionConflict/LaneContention: the CAS never landed.
            # ValueError: the payload failed Task 1's schema — a malformed provenance
            # record must fail the route, never be skipped.
            raise RouteAuditError(
                f"could not durably record the FR-002 reroute for {lens!r} "
                f"(primary route {primary_route_id}): {type(exc).__name__}: {exc}"
            ) from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_route_context.py -q`
Expected: PASS (11 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/route_context.py tests/integration/test_self_improvement_route_context.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T2): LaneRouteContext — mandatory hooks, durable route admission, route-fatal reroute records"
```

---

### Task 3: Router plumbing — forward the five spec-025 params

**Files:**
- Modify: `src/llmxive/backends/router.py` (`_walker_route` lines 230-286; `chat_with_model_fallback` lines 289-317)
- Test: `tests/unit/test_router_lane_plumbing.py`

**Interfaces:**
- Produces (extended signatures — every new param defaults to a behavior-preserving no-op):
  - `chat_with_model_fallback(backend, messages, *, model, max_tokens=None, temperature=None, overrides=None, profile="standard_generation", independence_against=None, route_audit=None, reservation_authority=None, route_id=None, reraise_model_unavailable=False) -> ChatResponse` — forwards the five new params to `_walker_route`.
  - `_walker_route(..., independence_against=None, route_audit=None, reservation_authority=None, route_id=None, reraise_model_unavailable=False)` — forwards the first four to `route_chat` (which already accepts all of them, `route.py:244-265`) and **splits the exception handler**: `ModelUnavailable` propagates RAW when `reraise_model_unavailable=True` (the FR-002 reroute needs it), else converts to `BackendUnavailable` exactly as today; `ChainExhausted` ALWAYS converts to `BackendUnavailable` (a real outage — never a reroute trigger).
- **Not changed:** `reasoning_chat` (`router.py:320-349`) and `chat_with_fallback` (`router.py:352-407`) — they serve the research/paper pipeline, whose calls are not lane calls (see the scope boundary).
- Import note: `router.py` imports `model_selection` symbols **function-locally** (`router.py:265`, `router.py:391`) to avoid an import cycle. Keep that pattern — annotate the new params with STRING annotations (`"IndependenceBaseline | None"`, `"RouteAudit | None"`, `"ReservationAuthority | None"`); add NO module-top `model_selection` import.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_router_lane_plumbing.py
import pytest

from llmxive.backends.base import BackendUnavailable
from llmxive.backends.router import chat_with_model_fallback
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable

class _Backend:
    name = "dartmouth"

class _Resp:
    text = "ok"

def _patch_route_chat(monkeypatch, fn):
    # route_chat is imported function-locally inside _walker_route, so patch it on the
    # module where it is DEFINED (that is the object the local import resolves to).
    monkeypatch.setattr("llmxive.model_selection.route.route_chat", fn)

def test_defaults_are_behavior_preserving(monkeypatch):
    seen = {}

    def _fake(messages, **kw):
        seen.update(kw)
        return _Resp()

    _patch_route_chat(monkeypatch, _fake)
    chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64, profile="deep_review")
    # the five new params arrive at route_chat as its own defaults (None) — unchanged path
    assert seen["independence_against"] is None
    assert seen["route_audit"] is None
    assert seen["reservation_authority"] is None
    assert seen["route_id"] is None

def test_all_five_params_are_forwarded(monkeypatch):
    seen = {}

    def _fake(messages, **kw):
        seen.update(kw)
        return _Resp()

    _patch_route_chat(monkeypatch, _fake)
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    sink, budget = object(), object()
    chat_with_model_fallback(
        _Backend(), [], model=None, max_tokens=64, profile="independent_review",
        independence_against=base, route_audit=sink, reservation_authority=budget, route_id="RID",
    )
    assert seen["independence_against"] is base
    assert seen["route_audit"] is sink
    assert seen["reservation_authority"] is budget
    assert seen["route_id"] == "RID"
    assert seen["profile"] == "independent_review"

def test_model_unavailable_converts_by_default_but_reraises_when_asked(monkeypatch):
    def _boom(messages, **kw):
        raise ModelUnavailable("no independent family live")

    _patch_route_chat(monkeypatch, _boom)
    # default: the existing outage-classification contract is preserved
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64, profile="independent_review")
    # the FR-002 reroute needs the RAW exception to trigger attempt 2
    with pytest.raises(ModelUnavailable):
        chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64,
                                 profile="independent_review", reraise_model_unavailable=True)

def test_chain_exhausted_always_converts_even_when_reraise_is_set(monkeypatch):
    # ChainExhausted is a real outage (the chain RAN and none succeeded) — it must NEVER
    # become a reroute trigger, even for a caller that asked for raw ModelUnavailable.
    def _boom(messages, **kw):
        raise ChainExhausted("every candidate advanced")

    _patch_route_chat(monkeypatch, _boom)
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64,
                                 profile="independent_review", reraise_model_unavailable=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_router_lane_plumbing.py -q`
Expected: FAIL — `TypeError: chat_with_model_fallback() got an unexpected keyword argument 'independence_against'`.

- [ ] **Step 3: Write minimal implementation**

Replace `chat_with_model_fallback`'s signature + body (keeping its docstring, extended with a sentence naming the five new params as spec-025 lane plumbing):

```python
def chat_with_model_fallback(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    independence_against: "IndependenceBaseline | None" = None,
    route_audit: "RouteAudit | None" = None,
    reservation_authority: "ReservationAuthority | None" = None,
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
) -> ChatResponse:
    return _walker_route(
        backend, messages, model=model,
        max_tokens=REASONING_MAX_TOKENS if max_tokens is None else max_tokens,
        temperature=temperature, overrides=overrides, profile=profile,
        independence_against=independence_against, route_audit=route_audit,
        reservation_authority=reservation_authority, route_id=route_id,
        reraise_model_unavailable=reraise_model_unavailable,
    )
```

Replace `_walker_route`'s signature + the `route_chat` call + the except block (keep the rest of the docstring/body):

```python
def _walker_route(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int,
    temperature: float | None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    independence_against: "IndependenceBaseline | None" = None,
    route_audit: "RouteAudit | None" = None,
    reservation_authority: "ReservationAuthority | None" = None,
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
) -> ChatResponse:
    from llmxive.model_selection.execute import ChainExhausted
    from llmxive.model_selection.route import route_chat
    from llmxive.model_selection.types import ModelUnavailable

    injected_name = getattr(backend, "name", None) or "dartmouth"

    def factory(name: str) -> BaseBackend:
        return backend if name == injected_name else make_backend(name)

    try:
        return route_chat(
            messages, profile=profile, caller_model=model, max_tokens=max_tokens,
            temperature=temperature, backend_factory=factory, overrides=overrides,
            independence_against=independence_against, route_audit=route_audit,
            reservation_authority=reservation_authority, route_id=route_id,
        )
    except ModelUnavailable as exc:
        # Spec 025 FR-002: the proposal reroute needs the RAW ModelUnavailable to trigger
        # its second attempt. Every other caller keeps the outage-classification contract.
        if reraise_model_unavailable:
            raise
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc
    except ChainExhausted as exc:
        # ALWAYS a clean run-loop abort — the chain ran and none succeeded. Never a
        # reroute trigger, even when reraise_model_unavailable is set.
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc
```

- [ ] **Step 4: Run test to verify it passes + confirm no regression**

Run: `pytest tests/unit/test_router_lane_plumbing.py -q`
Expected: PASS (4 passed).

Run: `pytest tests/unit -k "router or walker or reviewer" -q`
Expected: PASS — the default path is byte-for-byte unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/backends/router.py tests/unit/test_router_lane_plumbing.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T3): plumb independence/audit/authority/route_id + raw-ModelUnavailable through the router"
```

---

### Task 4: `LLMReviewer` — lane context + two-attempt independence reroute

**Files:**
- Modify: `src/llmxive/convergence/llm_reviewer.py` (`_STAGE_PREFIX` ~lines 100-147; `LLMReviewer.__init__` lines 819-877; the three `_call_backend` call sites at lines 962, 991, 1021; `_call_backend` lines 1148-1167)
- Test: `tests/integration/test_llm_reviewer_reroute.py` (integration: the durable call ledger needs a real git repo)

**Interfaces:**
- Consumes: `LaneRouteContext` (Task 2); `chat_with_model_fallback` with the five new params (Task 3); `IndependenceBaseline`, `ModelUnavailable` (`model_selection.types`); `RouteAuditError` (slice-0).
- Produces:
  - `_STAGE_PREFIX` gains `"self_improvement_proposal": "si_proposal"` → the lane's per-lens prompt path becomes `<repo_root>/agents/prompts/panels/panel_si_proposal_<lens>.md` (`_prompt_path_for`, `llm_reviewer.py:150-165`). Without this entry `_prompt_path_for` raises `ValueError("unknown stage ...")` and a lane reviewer cannot be constructed at all.
  - `LLMReviewer.__init__` gains three keyword params, all defaulting to `None` so every existing call site is byte-for-byte unchanged: `route_context: "LaneRouteContext | None" = None`, `independence_against: "IndependenceBaseline | None" = None`, `fallback_profile: str | None = None`. Stored as `self._route_context`, `self._independence_against`, `self._fallback_profile`.
  - `_call_backend(self, messages, *, kind: str = "identify") -> str` — when `self._route_context is None`, the EXISTING single unrouted call, unchanged (`kind` is ignored there, so no existing caller changes behavior). Otherwise delegates to `_route_review`.
  - `_operation_id(self, kind, messages) -> str` = `f"{lens}:{kind}:{sha256(canonical(messages))[:16]}"` — the deterministic identity of ONE logical review call. **Why not the round-3 `primary_route_id`:** with the durable ledger (round-4 F1) the operation id is the CLAIM KEY, so it must be (a) distinct per logical call and (b) identical across a retry. A digest of `(lens, kind, messages)` is both; a fresh uuid is neither. The `kind` label is what keeps the reviewer's THREE logical calls — identify (`:962`), the action-items resubmit (`:991`), rereview (`:1021`) — from collapsing into one claim, which would hand the later calls the first call's `route_id` and make slice-0's `claim_dispatch` refuse to dispatch them as replays.
  - `_route_review(self, messages, *, kind) -> str` — the lane path:
    1. `operation_id = self._operation_id(kind, messages)`; `primary_route_id = ctx.claim_route(operation_id=operation_id, leg="primary")` (durable admission against the Attempt ceiling);
    2. attempt 1 = `chat_with_model_fallback(..., profile=self._profile, independence_against=self._independence_against, route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority, route_id=primary_route_id, reraise_model_unavailable=bool(self._fallback_profile))`;
    3. on `ModelUnavailable` **and** `self._fallback_profile is not None` → `fallback_route_id = ctx.claim_route(operation_id=operation_id, leg="fallback")`; **then `ctx.record_reroute(...)` BEFORE the fallback dispatch** (F4 — a `RouteAuditError` from the record is deliberately NOT caught, so a reroute that cannot be made durable stops the review instead of producing one that claims independence it lacked); attempt 2 = same call with `profile=self._fallback_profile`, **no** `independence_against`, and `reraise_model_unavailable=False` (a fallback that ALSO finds nothing is a genuine outage → `BackendUnavailable` → the engine's clean-abort path, not a second degrade).
    - With `fallback_profile=None` (the future **patch** review's fail-closed binding), `reraise_model_unavailable` is `False`, so a `ModelUnavailable` converts to `BackendUnavailable` and the run aborts — no promotion. The same class serves both bindings.
  - The two legs share ONE `operation_id` and differ by `leg`, so the ledger charges both (the ceiling's `4N` term) while the `ReviewRerouted` `event_id` stays deterministic for an idempotent re-record.
  - **`_validate_lane_configuration` runs in `__init__` (round-11 F1/F2).** `record_reroute` writes ONE hard-coded provenance and the event validator can only check what was written, never what actually ran — so a reviewer built with `profile="deep_review", fallback_profile="vision"` would execute that pair and durably assert the sanctioned one, undetectably. Exactly three configurations are accepted: **proposal** (`independent_review` + non-empty family baseline + `deep_review` fallback), **patch** (same, `fallback_profile=None`), and **non-lane** (no lane-only arguments at all). The baseline must name ≥1 family because `independent_review` requires a family DIFFERENCE — an empty baseline is satisfied by any model, voiding FR-002. Lane-only arguments without a `route_context` are refused rather than silently ignored. A later stage that reroutes differently must extend `record_reroute` AND the event validator AND this check together.
  - **The sanctioned profile/trigger/relaxed-constraint values are PUBLIC in `events.py`** (`REROUTE_PRIMARY_PROFILE`, `REROUTE_FALLBACK_PROFILE`, `REROUTE_TRIGGER`, `REROUTE_RELAXED_CONSTRAINTS`) and imported by both `route_context.record_reroute` (what gets written) and this check (what executes). They were previously defined twice — which is precisely the mechanism by which the two could drift apart.
  - **`_operation_id` digests via `model_selection.route.messages_digest`** (promoted from `_messages_digest`), the same canonical projection used for `prompt_digest`. A local `json.dumps(..., default=str)` works for today's text-only lane prompts but falls back to object repr for multimodal `content` — making a durable route identity depend on a dataclass's string form, or embedding raw bytes in it.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_llm_reviewer_reroute.py
import subprocess
from pathlib import Path

import pytest

from llmxive.model_selection.attempt_hooks import RouteAuditError
from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import LaneRouteContext

LENS = "worthwhile-improvement"
STAGE = "self_improvement_proposal"

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
    # REAL prompt files at the convention path (no mock): _load_system_prompt reads the
    # per-lens prompt + the SSoT shared block, so both must exist. The lane log lives on
    # the same repo (the call ledger is durable — round-4 F1).
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    panels = tmp_path / "agents" / "prompts" / "panels"
    panels.mkdir(parents=True)
    (panels / f"panel_si_proposal_{LENS}.md").write_text("# Panel Reviewer — lens\n\n## Lens\nJudge it.\n")
    shared = tmp_path / "agents" / "prompts" / "_shared"
    shared.mkdir(parents=True)
    (shared / "panel_review_block.md").write_text("## Output format\nUse the protocol.\n")
    return tmp_path

class _RecordingCtx(LaneRouteContext):
    """A REAL subclass (not a mock, and not attribute patching — ``LaneRouteContext`` is
    frozen, so assigning to ``ctx.record_reroute`` would raise ``FrozenInstanceError``).
    It captures the reroute calls instead of persisting them; the durable persistence path
    has its own test in Task 2."""

    def __init__(self, **kw):
        super().__init__(**kw)
        object.__setattr__(self, "recorded", [])
        object.__setattr__(self, "record_error", None)

    def record_reroute(self, **kw):
        if self.record_error is not None:
            raise self.record_error
        self.recorded.append(kw)

_BUDGET = 50.0   # the Attempt credit budget; ONE AttemptConfigured record binds it
                 # together with the call ceiling (Slice 1A Task 13), so every
                 # ledger for this Attempt must present the SAME pair.

def _ctx(repo_root, ceiling=10, cls=_RecordingCtx):
    ledger = LaneCallLedger(repo=repo_root, problem_id="P1", attempt_id="A1",
                            call_ceiling=ceiling, attempt_budget_credits=_BUDGET,
                            actor="reviewer", clock=lambda: "2026-07-25T00:00:00+00:00",
                            config=LaneLogConfig())
    return cls(
        repo=repo_root, problem_id="P1", attempt_id="A1", actor="reviewer",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )

def _reviewer(repo_root, **kw):
    from llmxive.convergence.llm_reviewer import LLMReviewer
    return LLMReviewer(lens=LENS, stage=STAGE, backend=object(), repo_root=Path(repo_root), **kw)

def test_no_context_uses_the_unchanged_single_call(repo_root, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        class R: text = "plain"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    r = _reviewer(repo_root, profile="deep_review")
    assert r._call_backend([]) == "plain"
    assert len(calls) == 1
    # the legacy path passes NO lane params
    assert calls[0].get("route_audit") is None and calls[0].get("route_id") is None

def test_reroute_records_an_explicit_event_and_uses_two_route_ids(repo_root, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        class R: text = "fallback-body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    recorded = ctx.recorded          # the subclass captures the explicit record
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=base, route_context=ctx)

    assert r._call_backend([]) == "fallback-body"
    assert len(calls) == 2
    # attempt 1: constrained + raw-ModelUnavailable enabled; hooks present
    assert calls[0]["profile"] == "independent_review"
    assert calls[0]["independence_against"] is base
    assert calls[0]["reraise_model_unavailable"] is True
    assert calls[0]["route_audit"] is ctx.route_audit
    assert calls[0]["reservation_authority"] is ctx.reservation_authority
    # attempt 2: unconstrained, must NOT re-raise (a second miss is a real outage)
    assert calls[1]["profile"] == "deep_review"
    assert calls[1].get("independence_against") is None
    assert calls[1]["reraise_model_unavailable"] is False
    # DISTINCT route ids, both charged against the ceiling
    assert calls[0]["route_id"] != calls[1]["route_id"]
    assert ctx.calls_used() == 2
    # the degradation is recorded EXPLICITLY (F10), not left to be inferred
    assert len(recorded) == 1
    assert recorded[0]["lens"] == LENS
    assert recorded[0]["primary_route_id"] == calls[0]["route_id"]
    assert recorded[0]["fallback_route_id"] == calls[1]["route_id"]
    assert recorded[0]["exception_type"] == "ModelUnavailable"

def test_successful_primary_never_reroutes_or_records(repo_root, monkeypatch):
    def _fake(backend, messages, **kw):
        class R: text = "independent-body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    recorded = ctx.recorded
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=ctx)
    assert r._call_backend([]) == "independent-body"
    assert recorded == [] and ctx.calls_used() == 1

def test_without_a_fallback_profile_model_unavailable_is_not_rerouted(repo_root, monkeypatch):
    # The future PATCH binding: required independence, NO fallback → fail closed.
    def _fake(backend, messages, **kw):
        assert kw["reraise_model_unavailable"] is False  # converts to BackendUnavailable
        raise ModelUnavailable("no independent family live")

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    r = _reviewer(repo_root, profile="independent_review", fallback_profile=None,
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=ctx)
    with pytest.raises(ModelUnavailable):
        r._call_backend([])

def test_a_failed_reroute_record_aborts_BEFORE_the_fallback_dispatches(repo_root, monkeypatch):
    # F4: if the ReviewRerouted record cannot become durable, the fallback MUST NOT run —
    # otherwise the review silently claims an independence it did not have. record_reroute
    # normalizes the persistence failure to RouteAuditError (Task 2), which Task 8 then
    # classifies as route-fatal.
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        class R: text = "fallback-body"   # must never be reached
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    object.__setattr__(ctx, "record_error", RouteAuditError("lane ref unreachable"))
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=ctx)
    with pytest.raises(RouteAuditError):
        r._call_backend([])
    assert len(calls) == 1 and calls[0]["profile"] == "independent_review"  # no fallback dispatch

def test_distinct_logical_calls_get_distinct_operation_ids(repo_root, monkeypatch):
    # F1 corollary: identify / the action-items resubmit / rereview are THREE logical calls.
    # If they shared an operation_id the durable claim would treat the later ones as
    # REPLAYS — returning the first route_id, which would make slice-0's claim_dispatch
    # refuse to dispatch them at all.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        class R: text = "body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  route_context=ctx)
    msgs = [ChatMessage(role="user", content="review this")]
    r._call_backend(msgs, kind="identify")
    r._call_backend([*msgs, ChatMessage(role="user", content="no action items")], kind="identify_resubmit")
    r._call_backend(msgs, kind="rereview")
    assert len(set(seen)) == 3 and ctx.calls_used() == 3

def test_a_RESTART_replays_the_same_logical_call_onto_the_same_route_id(repo_root, monkeypatch):
    # Retry stability across a RESTART: identical (lens, kind, messages) with a FRESH
    # context → the same durable claim, the same route_id, no extra ceiling charge. That
    # is what lets slice-0's claim_dispatch recognize the replay.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        class R: text = "body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    msgs = [ChatMessage(role="user", content="review this")]
    for _ in range(2):                       # two processes, two contexts, one claim
        ctx = _ctx(repo_root)
        _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  route_context=ctx)._call_backend(msgs, kind="identify")
    assert len(set(seen)) == 1 and ctx.calls_used() == 1

def test_an_IN_PROCESS_repeat_is_a_new_logical_call(repo_root, monkeypatch):
    # The counterpart: within ONE process an identical re-issue is a genuinely new call
    # (the first one already dispatched), so it gets its own route_id and ceiling charge.
    # Without this, the engine's reviser retry would be refused at the dispatch gate.
    seen = []

    def _fake(backend, messages, **kw):
        seen.append(kw["route_id"])
        class R: text = "body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  route_context=ctx)
    msgs = [ChatMessage(role="user", content="review this")]
    r._call_backend(msgs, kind="identify")
    r._call_backend(msgs, kind="identify")
    assert len(set(seen)) == 2 and ctx.calls_used() == 2
```

(`ChatMessage` imports from `llmxive.backends.base` — add it to the test file's imports.)

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_llm_reviewer_reroute.py -q`
Expected: FAIL — `ValueError: unknown stage 'self_improvement_proposal'` (the `_STAGE_PREFIX` gap) or `TypeError: __init__() got an unexpected keyword argument 'route_context'`.

- [ ] **Step 3: Write minimal implementation**

Add the lane stage to `_STAGE_PREFIX` (`llm_reviewer.py` ~lines 100-147):

```python
    # Spec 025 slice 1B: the self-improvement lane's proposal review. Its per-lens
    # prompts live at agents/prompts/panels/panel_si_proposal_<lens>.md.
    "self_improvement_proposal": "si_proposal",
```

Add the three params to `LLMReviewer.__init__` (after `overrides`) and store them:

```python
        # Spec 025 slice 1B: the lane's mandatory routing context (audit sink + Attempt
        # credit authority + route-id/ceiling). None = a NON-lane reviewer (research /
        # paper panels), whose call path stays byte-for-byte unchanged.
        route_context: "LaneRouteContext | None" = None,
        # FR-002: the producer baseline this lens must differ from, and the profile to
        # degrade to when no independent family is selectable. fallback_profile=None
        # means FAIL CLOSED (the patch-review binding).
        independence_against: "IndependenceBaseline | None" = None,
        fallback_profile: str | None = None,
    ) -> None:
        ...  # existing assignments unchanged
        self._route_context = route_context
        self._independence_against = independence_against
        self._fallback_profile = fallback_profile
```

Replace `_call_backend` and add `_route_review` (keep the existing docstring on the legacy branch):

```python
    def _call_backend(self, messages: list[ChatMessage], *, kind: str = "identify") -> str:
        """``kind`` names WHICH logical review call this is. It is unused on the legacy
        path (so every existing caller is unaffected) and forms part of the lane's durable
        operation id — the reviewer makes THREE distinct logical calls (identify, the
        action-items resubmit, rereview) and they must not collide into one claim."""
        if self._route_context is not None:
            return self._route_review(messages, kind=kind)
        response = chat_with_model_fallback(
            self._backend, messages, model=None, max_tokens=self._max_tokens,
            temperature=self._temperature, overrides=self._overrides, profile=self._profile,
        )
        return getattr(response, "text", "") or ""

    def _operation_id(self, kind: str, messages: list[ChatMessage]) -> str:
        """The DETERMINISTIC identity of one logical review call (round-4 F1). Digesting the
        messages makes it DISTINCT per call (each round's rereview prompt differs) and
        STABLE across a restart (identical inputs → identical id → the call ledger replays
        the same claim and the same route_id instead of re-charging the ceiling). The
        context's ``next_operation_id`` then disambiguates a legitimate in-process repeat
        (see its docstring) — without it, a round that produced no artifact change could
        hand this lens a rereview prompt identical to the previous round's, and the second
        one would be refused at the dispatch gate as a replay."""
        import hashlib
        import json

        payload = json.dumps([[m.role, m.content] for m in messages],
                             sort_keys=True, default=str, ensure_ascii=False)
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self._route_context.next_operation_id(f"{self._lens}:{kind}:{digest}")

    def _route_review(self, messages: list[ChatMessage], *, kind: str) -> str:
        """The lane path (spec 025 FR-002): every call carries the mandatory audit sink +
        Attempt credit authority, and a proposal lens performs the TWO-ATTEMPT reroute —
        ``independent_review`` (required family) first, then, on a raw ``ModelUnavailable``,
        ``deep_review`` with an EXPLICIT ``ReviewRerouted`` record. No new profile is
        introduced; both are delivered 026 profiles."""
        from llmxive.model_selection.types import ModelUnavailable

        ctx = self._route_context
        assert ctx is not None  # guarded by the caller
        operation_id = self._operation_id(kind, messages)
        primary_route_id = ctx.claim_route(operation_id=operation_id, leg="primary")
        try:
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides, profile=self._profile,
                independence_against=self._independence_against,
                route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
                route_id=primary_route_id,
                # Only a lens WITH a fallback needs the raw exception; a fail-closed lens
                # (patch review) keeps the standard BackendUnavailable conversion.
                reraise_model_unavailable=self._fallback_profile is not None,
            )
        except ModelUnavailable as exc:
            if self._fallback_profile is None:
                raise
            fallback_route_id = ctx.claim_route(operation_id=operation_id, leg="fallback")
            # RECORD FIRST (F4). record_reroute raises RouteAuditError if the degradation
            # cannot be made durable, and we deliberately do NOT catch it: a fallback that
            # ran with no durable record would be a review claiming an independence it
            # never had. Task 8 classifies the RouteAuditError as route-fatal.
            ctx.record_reroute(
                operation_id=operation_id, lens=self._lens,
                primary_route_id=primary_route_id, fallback_route_id=fallback_route_id,
                exception_type=type(exc).__name__, message=str(exc),
            )
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides,
                profile=self._fallback_profile,  # no independence constraint on the fallback
                route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
                route_id=fallback_route_id,
                # A fallback that ALSO finds nothing is a genuine outage, not a second
                # degrade → let it convert to BackendUnavailable (engine clean-abort).
            )
        return getattr(response, "text", "") or ""
```

Then label the three existing call sites so their claims stay distinct (`llm_reviewer.py:962`, `:991`, `:1021`):

```python
        response_text = self._call_backend(messages, kind="identify")            # ~962
        response_text = self._call_backend(resubmit, kind="identify_resubmit")   # ~991
        response_text = self._call_backend(messages, kind="rereview")            # ~1021
```

(`LaneRouteContext`/`IndependenceBaseline` appear only in STRING annotations, so no module-top import is added — matching the file's existing function-local `model_selection` import discipline.)

- [ ] **Step 4: Run test to verify it passes + confirm no regression**

Run: `pytest tests/integration/test_llm_reviewer_reroute.py -q`
Expected: PASS (8 passed).

Run: `pytest tests/unit -k llm_reviewer -q`
Expected: PASS — the non-lane path is unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/llm_reviewer.py tests/integration/test_llm_reviewer_reroute.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T4): LLMReviewer lane context + two-attempt reroute with explicit ReviewRerouted"
```

---

### Task 5: `LaneProposalReviser` — the routed, single-call reviser

**Files:**
- Create: `src/llmxive/convergence/lane_reviser.py`
- Test: `tests/integration/test_lane_reviser.py`

**Interfaces:**
- Consumes: `LaneRouteContext` (Task 2); `chat_with_model_fallback` (Task 3); `Concern`, `ConcernResponse` (`convergence.types`).
- Produces:
  - `class LaneProposalReviser` — structurally conforms to `convergence.types.Reviser`: `revise(self, artifacts: dict[str, str], concerns: list[Concern]) -> tuple[dict[str, str], list[ConcernResponse]]`.
  - Constructor: `LaneProposalReviser(*, backend, route_context: LaneRouteContext, artifact_key: str = "proposal.md", profile: str = "deep_code", max_tokens: int = GENERATION_MAX_TOKENS, temperature: float = 0.0)`.
    **`max_tokens` corrected during implementation (round-13).** The round-12 plan said `32_768`, which is `REASONING_MAX_TOKENS` — the budget for a short structured reasoning call. A revision turn REGENERATES the whole proposal plus a change-log, and spec-023 defect #20 is exactly what 32K produces: a reasoning model's hidden chain-of-thought consumes the budget before the artifact block closes, the reply truncates mid-document, and it parses as malformed (`revisers/_self_consistency.py:154-160`). Every other reviser's revision turn passes `GENERATION_MAX_TOKENS` (131_072) via `invoke_reviser_backend`; this one must too. Pinned by an assertion in the single-call test.
  - **Exactly ONE `chat_with_model_fallback` call per `revise()`** (the ceiling's `+2`-per-round term is the ENGINE's malformed-reply retry, `engine.py:521-533` — not an internal self-consistency loop). It does NOT use `invoke_reviser_backend`/`run_with_self_consistency`, which would make up to three calls per `revise()`.
  - It carries the lane context on every call: `route_audit`, `reservation_authority`, and a `route_id` from `ctx.claim_route(operation_id=..., leg="primary")`. The reviser's operation id is `f"reviser:{round_digest}"` where `round_digest` digests `(artifacts, concerns)` — distinct per round (each round's concern set differs) and stable across a retry, exactly like the reviewer's. It passes **no** `independence_against` (the producer has no independence constraint) and no `fallback_profile` (no reroute — hence the ceiling's `+2` is not doubled).
  - **Response contract: the package's SHARED two-part one — corrected during implementation (round-13).** The round-12 plan invented a fourth wire format (`{"proposal": "<full revised proposal markdown>", ...}` in one fenced ```json block) that nothing else in the repo speaks. Only the DISPATCH needed to be bespoke (the call count); the wire format did not. Use the shared stack every other reviser uses:
    - **prompt**: append `RESPONSE_FORMAT_BLOCK` (`revisers/_reviser_response.py:53`) to the user turn — a small fenced ```json change-log, then each full artifact VERBATIM between `===BEGIN_ARTIFACT <path>===` / `===END_ARTIFACT===` markers. The system turn is persona only; restating the format is how the reviser and the parser drift apart.
    - **parse**: `parse_reviser_response(text, expected_artifacts=[artifact_key])` → `pick_expected_artifact` (which tolerates a hallucinated dir slug, spec-023 defect #20c).
    - **change-log**: `build_concern_responses(responses_raw, concerns, default_artifacts=[artifact_key])`.

    This is not merely tidier. A proposal is a DOCUMENT containing quotes, backslashes, `$` and fenced code; embedding it in a JSON string re-introduces exactly the escaping failures the delimited markers exist to eliminate (`_reviser_response.py:85-86` — "the body is taken literally; quotes, $, backslashes and blank lines are fine and need NO escaping"). A round-trip test with all four pins it.
  - **Malformed replies raise `RuntimeError` with one of the engine's two RECOGNIZED message signatures (round-4 review F3):**
    - unparseable / missing block → `RuntimeError("lane reviser backend did not return parseable JSON ...")`
    - parsed but no usable proposal body → `RuntimeError("lane reviser response JSON has no usable ...")`
  - **An unanswered concern is NOT a malformed reply — MAINTAINER-DECIDED 2026-07-28 (round-13).** The round-12 plan raised `no usable` when the answered ids did not exactly match the raised ids, which would discard a revision that addressed every OTHER concern (and would also fire on a harmless superset). `build_concern_responses` instead pads `response="<missing>"`, and `engine.py:627-628` then forces that concern OPEN at R3 deterministically — no lenient re-reviewer can mark it resolved. Identical honesty guarantee, strictly more work preserved.
    Related bug the same change fixes: `ConcernResponse.response`/`what_changed` are `Field(min_length=1)` (`convergence/types.py:184-185`), so the round-12 code's `r.get("response", "")` raises a pydantic **`ValidationError`** whenever the model omits a field — not a `RuntimeError`, so it would skip the engine's retry AND escape the run with no provenance, the very failure class F3 exists to prevent. The shared helper substitutes `"<empty>"`, as every other reviser does.

    The round-3 plan said `ValueError`, which is **wrong twice over**: `engine.py:527` catches `RuntimeError`, so a `ValueError` skips the one-retry path entirely; and `_abort_provenance` (`engine.py:442`) catches only `BackendUnavailable`/`TransientBackendError`, so it would escape the whole run with no provenance. Worse, after the retry the engine calls `is_malformed_reply_error` (`revisers/_reviser_response.py:473-496`), which returns `True` only when the message contains `"parseable"` or `"no usable"` — anything else is re-raised as a genuine engine defect and files a spurious engine-failure issue. The two strings above are therefore CONTRACT, not prose: `is_malformed_reply_error` is the SSoT classifier shared by every reviser, and this one must satisfy it.

- [ ] **Step 0 (do first): confirm the exception contract against the engine.** Read `engine.py:518-553` and `revisers/_reviser_response.py:473-496`. Verify (a) the retry loop catches `RuntimeError` and re-raises `BackendError` first, and (b) `is_malformed_reply_error` keys on `"parseable"` / `"no usable"`. If either has changed, the messages below must change with it — assert the CURRENT behavior, never weaken the test.

- [ ] **Step 1: Write the failing test**

```python
"""The lane's proposal reviser: ONE routed call per revise() (spec 025 slice 1B, Task 5).

Integration, because the call ledger is durable — these need a real git repo. The router
boundary is injected so a specific reply can be scripted; the real routing path is covered
by the Task 3 suite.

The reviser speaks the SAME wire contract as every other reviser in the package
(``RESPONSE_FORMAT_BLOCK`` → ``parse_reviser_response`` → ``build_concern_responses``);
only the DISPATCH is bespoke, because the shared ``run_with_self_consistency`` path makes up
to three LLM calls per ``revise()`` and the proposal ceiling's ``+2``-per-round term pays for
exactly two.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from llmxive.convergence.types import Concern
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import LaneRouteContext

_BUDGET = 50.0  # ONE AttemptConfigured record binds this with the ceiling.


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
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ctx(repo, ceiling=10):
    ledger = LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                            attempt_budget_credits=_BUDGET, actor="proposer",
                            clock=lambda: "2026-07-25T00:00:00+00:00", config=LaneLogConfig())
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="proposer",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )


def _concern(cid="c1"):
    return Concern(id=cid, reviewer="worthwhile-improvement", severity="requirement",
                   artifact="proposal.md", text="Blast radius is unbounded.")


def _body(proposal="# Revised\n\nScoped to one module.", *, responses=None, cid="c1"):
    """A reply in the package's SHARED two-part contract: a small fenced ```json change-log,
    then the full artifact VERBATIM between ===BEGIN_ARTIFACT=== markers."""
    if responses is None:
        responses = [{"concern_id": cid, "response": "Scoped it.",
                      "what_changed": "Added a blast-radius section.",
                      "artifacts_changed": ["proposal.md"]}]
    return (
        "```json\n" + json.dumps({"responses": responses}) + "\n```\n\n"
        "===BEGIN_ARTIFACT proposal.md===\n" + proposal + "\n===END_ARTIFACT===\n"
    )


def _reviser(repo, monkeypatch, fake):
    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", fake)
    from llmxive.convergence.lane_reviser import LaneProposalReviser

    ctx = _ctx(repo)
    return LaneProposalReviser(backend=object(), route_context=ctx), ctx


def _replying(text):
    def _fake(backend, messages, **kw):
        class R:
            pass

        R.text = text
        return R()

    return _fake


# ---- the single-call contract ----


def test_revise_makes_exactly_one_routed_call_with_the_lane_hooks(repo, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)

        class R:
            text = _body()

        return R()

    rev, ctx = _reviser(repo, monkeypatch, _fake)
    updated, responses = rev.revise({"proposal.md": "# Original"}, [_concern()])

    # ONE call — NOT the 3-call self-consistency path (that would break the ceiling's +2).
    assert len(calls) == 1 and ctx.calls_used() == 1
    assert calls[0]["route_audit"] is ctx.route_audit
    assert calls[0]["reservation_authority"] is ctx.reservation_authority
    assert calls[0]["route_id"]
    assert calls[0].get("independence_against") is None  # the producer has no constraint
    # A revision turn REGENERATES the whole proposal: it needs the GENERATION budget, not
    # the reasoning one. At 32K a reasoning model's hidden CoT eats the budget before the
    # artifact block closes and the reply truncates into a malformed parse — spec-023
    # defect #20 (revisers/_self_consistency.py:154-160).
    from llmxive.backends.router import GENERATION_MAX_TOKENS, REASONING_MAX_TOKENS

    assert calls[0]["max_tokens"] == GENERATION_MAX_TOKENS != REASONING_MAX_TOKENS
    assert updated["proposal.md"].startswith("# Revised")
    assert [r.concern_id for r in responses] == ["c1"]


def test_the_engines_second_attempt_is_a_new_logical_call(repo, monkeypatch):
    # engine.py:519-533 re-invokes revise() with BYTE-IDENTICAL arguments after a malformed
    # reply. That is a new logical call (the first already dispatched), so it must get its own
    # route_id and its own ceiling charge — which is exactly what the ceiling's +2 pays for.
    # Without next_operation_id it would replay the first claim and be refused at the gate.
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)

        class R:
            text = _body()

        return R()

    rev, ctx = _reviser(repo, monkeypatch, _fake)
    args = ({"proposal.md": "# Original"}, [_concern()])
    rev.revise(*args)
    rev.revise(*args)

    assert calls[0]["route_id"] != calls[1]["route_id"]
    assert ctx.calls_used() == 2


# ---- the malformed-reply contract the ENGINE recognizes ----


@pytest.mark.parametrize("text, marker", [
    ("no json block and no artifact markers here", "parseable"),   # nothing to parse
    ('```json\n{"responses": []}\n```', "no usable"),              # parsed, but no artifact
])
def test_malformed_replies_raise_the_ENGINE_RECOGNIZED_error(repo, monkeypatch, text, marker):
    # F3: the engine catches RuntimeError (engine.py:527) and then classifies with
    # is_malformed_reply_error, which keys on "parseable" / "no usable". A ValueError —
    # or a RuntimeError with any other message — skips the retry and/or files a spurious
    # engine-failure issue.
    from llmxive.convergence.revisers._reviser_response import is_malformed_reply_error

    rev, _ = _reviser(repo, monkeypatch, _replying(text))
    with pytest.raises(RuntimeError) as excinfo:
        rev.revise({"proposal.md": "# Original"}, [_concern()])
    assert marker in str(excinfo.value)
    assert is_malformed_reply_error(excinfo.value)   # the SSoT classifier accepts it


def test_an_unanswered_concern_pads_missing_and_keeps_the_revision(repo, monkeypatch):
    # MAINTAINER-DECIDED 2026-07-28: the SSoT governs. Discarding a revision because ONE
    # concern of many went unanswered would throw away every fix it DID make. Instead
    # build_concern_responses pads "<missing>", and engine.py:627 then forces that concern
    # open at R3 deterministically — no re-reviewer leniency can mark it resolved, so the
    # honesty guarantee is identical while the useful work survives.
    rev, _ = _reviser(repo, monkeypatch, _replying(_body(cid="WRONG-ID")))
    updated, responses = rev.revise(
        {"proposal.md": "# Original"}, [_concern("c1"), _concern("c2")]
    )

    assert updated["proposal.md"].startswith("# Revised"), "the revision must be KEPT"
    by_id = {r.concern_id: r for r in responses}
    assert set(by_id) == {"c1", "c2"}, "exactly one response per raised concern"
    # "<missing>" is not decoration: engine.py:627-628 keys on this exact string.
    assert by_id["c1"].response == "<missing>"
    assert by_id["c2"].response == "<missing>"


def test_empty_response_fields_become_the_shared_placeholder(repo, monkeypatch):
    # ConcernResponse.response/what_changed are min_length=1 (types.py:184-185), so passing
    # the model's omitted field through as "" raises a pydantic ValidationError — which is
    # NOT a RuntimeError, so it would skip the engine's retry AND escape the run with no
    # provenance. build_concern_responses substitutes "<empty>", the same as every other
    # reviser.
    reply = _body(responses=[{"concern_id": "c1", "response": "", "what_changed": "   "}])
    rev, _ = _reviser(repo, monkeypatch, _replying(reply))
    _, responses = rev.revise({"proposal.md": "# Original"}, [_concern()])

    assert [r.response for r in responses] == ["<empty>"]
    assert [r.what_changed for r in responses] == ["<empty>"]


def test_a_verbatim_markdown_proposal_survives_the_round_trip(repo, monkeypatch):
    # WHY the delimited contract rather than {"proposal": "<markdown>"}: a proposal is a
    # document containing quotes, backslashes, $ and fenced code. Embedding it in a JSON
    # string re-introduces the escaping failures the ===BEGIN_ARTIFACT=== markers exist to
    # eliminate (_reviser_response.py:85-86 — the body is taken literally).
    tricky = (
        "# Revised\n\n"
        'He said "no \\ escape" and $PATH stayed intact.\n\n'
        "```python\n"
        'print({"nested": "json-ish", "backslash": "\\\\"})\n'
        "```\n\n"
        "Trailing prose."
    )
    rev, _ = _reviser(repo, monkeypatch, _replying(_body(tricky)))
    updated, _ = rev.revise({"proposal.md": "# Original"}, [_concern()])

    assert updated["proposal.md"] == tricky


def test_other_artifacts_are_carried_through_untouched(repo, monkeypatch):
    rev, _ = _reviser(repo, monkeypatch, _replying(_body()))
    updated, _ = rev.revise(
        {"proposal.md": "# Original", "notes.md": "keep me"}, [_concern()]
    )
    assert updated["notes.md"] == "keep me"


def test_conforms_to_the_reviser_protocol(repo):
    from llmxive.convergence.lane_reviser import LaneProposalReviser
    from llmxive.convergence.types import Reviser

    assert isinstance(LaneProposalReviser(backend=object(), route_context=_ctx(repo)), Reviser)
```

**And the same contract driven through the REAL engine** (the only proof that the retry and the graceful degradation actually engage — F3):

```python
# append to tests/integration/test_self_improvement_proposal_review.py (Task 9's file)
def test_one_malformed_reviser_reply_then_a_good_one_recovers(repo, monkeypatch):
    """engine.py:519-533 gives the reviser ONE retry. The lane reviser's malformed error
    must be the type + message that retry recognizes."""
    replies = iter(["garbage, no json", _body()])
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        class R: text = next(replies)
        return R()

    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", _fake)
    result = _run_panel_with_one_open_concern(repo, monkeypatch)
    assert len(calls) == 2                       # retried, not aborted
    assert result.artifacts["proposal.md"].startswith("# Revised")

def test_two_malformed_reviser_replies_degrade_to_no_change(repo, monkeypatch):
    """Issue #355's contract: after the retry, a RECOGNIZED malformed reply is 'no artifact
    change this round' — the bounded loop carries the concerns forward. It must NOT crash
    the panel and must NOT file an engine-failure issue."""
    def _fake(backend, messages, **kw):
        class R: text = "garbage, no json"
        return R()

    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", _fake)
    result = _run_panel_with_one_open_concern(repo, monkeypatch)   # no exception
    assert result.artifacts["proposal.md"] == "# Original"          # unchanged
    assert not result.converged                                     # concerns carried forward

def test_a_backend_outage_is_a_CLEAN_ABORT_not_a_malformed_reply(repo, monkeypatch):
    """BackendError subclasses RuntimeError, so the engine checks it FIRST (engine.py:525).
    A lane reviser outage must abort cleanly, never be retried as malformed output."""
    from llmxive.backends.base import BackendUnavailable

    def _fake(backend, messages, **kw):
        raise BackendUnavailable("breaker open")

    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", _fake)
    with pytest.raises(BackendUnavailable):
        _run_panel_with_one_open_concern(repo, monkeypatch)
```

`_run_panel_with_one_open_concern(repo, monkeypatch)` is a Task-9 helper: it builds the real proposal `ReviewSpec` with a scripted reviewer panel whose R1 raises exactly one concern, then calls `run_convergence`. Write it once in Task 9 and import it here — do NOT duplicate the body.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_lane_reviser.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.convergence.lane_reviser'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""The self-improvement lane's proposal reviser (spec 025 FR-019): the proposer
addressing the panel's concerns inside the shared ``run_convergence`` loop.

**Only the DISPATCH is bespoke.** The wire contract, the parse, and the change-log
assembly are the package's shared ones (``RESPONSE_FORMAT_BLOCK`` →
``parse_reviser_response`` → ``build_concern_responses``), so the lane speaks the format
every other reviser speaks and inherits their accumulated defect fixes rather than
re-earning them. What this reviser does NOT reuse is
``invoke_reviser_backend``/``run_with_self_consistency`` (``revisers/_self_consistency.py``):
that path makes up to THREE LLM calls per ``revise()``, which would break the documented
proposal ceiling ``4N + R*(2N + 2)`` whose ``+2`` models the ENGINE's at-most-two reviser
attempts per round (``engine.py:519-533``). This reviser makes EXACTLY ONE routed call per
``revise()`` and raises on a malformed reply so the engine's own retry provides the second.

**Malformed-reply contract (round-4 review F3).** The engine's retry loop catches
``RuntimeError`` (``engine.py:527``) after re-raising ``BackendError`` first, and then
classifies with ``is_malformed_reply_error`` (``revisers/_reviser_response.py:473-496``),
which keys on the substrings ``"parseable"`` and ``"no usable"``. So every malformed-reply
raise below is a ``RuntimeError`` carrying one of those two signatures — NOT a
``ValueError``, which would skip the retry entirely and escape the run
(``_abort_provenance`` catches only ``BackendUnavailable``/``TransientBackendError``), and
not some other ``RuntimeError`` message, which would be re-raised as a genuine engine defect
and file a spurious engine-failure issue.

An UNANSWERED concern is deliberately NOT one of those failures (maintainer-decided
2026-07-28). ``build_concern_responses`` pads it as ``response="<missing>"`` and
``engine.py:627-628`` then forces that concern open at R3 deterministically — no lenient
re-reviewer can mark it resolved. Raising instead would discard a revision that may have
addressed every OTHER concern, which is strictly worse for convergence at identical honesty.

Every call carries the lane's mandatory audit sink + Attempt credit authority (F2/F3): the
reviser is a lane LLM call like any other, and its spend counts against the Attempt.
"""

from __future__ import annotations

import hashlib
import json

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import GENERATION_MAX_TOKENS, chat_with_model_fallback
from llmxive.convergence.revisers._reviser_response import (
    RESPONSE_FORMAT_BLOCK,
    build_concern_responses,
    parse_reviser_response,
    pick_expected_artifact,
)
from llmxive.convergence.types import Concern, ConcernResponse
from llmxive.self_improvement.route_context import LaneRouteContext

#: The two message signatures ``is_malformed_reply_error`` recognizes. Keep in sync with
#: ``revisers/_reviser_response.py:473-496`` — Task 5 Step 0 re-verifies them.
_UNPARSEABLE = "lane reviser backend did not return parseable JSON"
_NO_USABLE = "lane reviser response JSON has no usable"

#: Persona only. The RESPONSE FORMAT is appended to the user turn from the shared
#: ``RESPONSE_FORMAT_BLOCK``, exactly as every other reviser does it — the format is not
#: restated here, because a second copy is how the reviser and the parser drift apart.
_SYSTEM = (
    "You are the author of a self-improvement proposal for llmXive, an autonomous "
    "research platform. A review panel raised concerns about your proposal. Revise it so "
    "that every concern is addressed, and report exactly what you changed.\n\n"
    "Keep the proposal concrete and tightly scoped: an automated implementer will build "
    "it, and a pre-merge panel will review the resulting patch before anything lands. A "
    "concern you cannot address without changing the proposal's premise should be answered "
    "honestly in `response` rather than papered over."
)


class LaneProposalReviser:
    """Conforms structurally to :class:`llmxive.convergence.types.Reviser`.

    ``max_tokens`` defaults to :data:`GENERATION_MAX_TOKENS`, not the reasoning budget: a
    revision turn REGENERATES the whole proposal plus a change-log, and spec-023 defect #20
    is precisely what happens at 32K — a reasoning model's hidden chain-of-thought consumes
    the budget before the artifact block closes, so the reply truncates mid-document and
    parses as malformed (``revisers/_self_consistency.py:154-160``).
    """

    def __init__(self, *, backend: object, route_context: LaneRouteContext,
                 artifact_key: str = "proposal.md", profile: str = "deep_code",
                 max_tokens: int = GENERATION_MAX_TOKENS, temperature: float = 0.0) -> None:
        self._backend = backend
        self._route_context = route_context
        self._artifact_key = artifact_key
        self._profile = profile
        self._max_tokens = max_tokens
        self._temperature = temperature

    def revise(self, artifacts: dict[str, str], concerns: list[Concern],
               ) -> tuple[dict[str, str], list[ConcernResponse]]:
        ctx = self._route_context
        messages = [
            ChatMessage(role="system", content=_SYSTEM),
            ChatMessage(role="user", content=self._compose(artifacts, concerns)),
        ]
        response = chat_with_model_fallback(
            self._backend, messages, model=None, max_tokens=self._max_tokens,
            temperature=self._temperature, profile=self._profile,
            route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
            route_id=ctx.claim_route(operation_id=self._operation_id(artifacts, concerns)),
        )
        return self._parse(getattr(response, "text", "") or "", artifacts, concerns)

    def _operation_id(self, artifacts: dict[str, str], concerns: list[Concern]) -> str:
        """Deterministic per REVISION ROUND: each round's (artifacts, concerns) pair differs,
        so rounds get distinct claims, while a restart re-derives the same claim and the same
        route_id (round-4 F1). ``next_operation_id`` then separates the ENGINE's second
        attempt: ``engine.py:519-533`` re-invokes ``revise()`` with byte-identical arguments
        after a malformed reply, and that IS a new logical call (the first one dispatched) —
        it must get a new route_id and its own ceiling charge, which is exactly what the
        ceiling's ``+2`` per round pays for."""
        payload = json.dumps(
            {"artifacts": artifacts, "concerns": sorted(c.id for c in concerns)},
            sort_keys=True, ensure_ascii=False,
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self._route_context.next_operation_id(f"reviser:{digest}")

    def _compose(self, artifacts: dict[str, str], concerns: list[Concern]) -> str:
        body = artifacts.get(self._artifact_key, "")
        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"
        return (
            f"# Current proposal (`{self._artifact_key}`)\n\n"
            f"{body or '(the proposal is empty)'}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Task\n\n"
            f"Revise the proposal to address every panel concern. The ONLY editable "
            f"artifact is:\n- {self._artifact_key}\n\n"
            + RESPONSE_FORMAT_BLOCK
        )

    def _parse(self, text: str, artifacts: dict[str, str], concerns: list[Concern],
               ) -> tuple[dict[str, str], list[ConcernResponse]]:
        # BOTH raises below are RuntimeErrors carrying one of the two signatures
        # is_malformed_reply_error recognizes (F3). A ValueError here would skip the
        # engine's one retry entirely and escape the run without provenance.
        try:
            artifacts_by_path, responses_raw = parse_reviser_response(
                text, expected_artifacts=[self._artifact_key]
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"{_UNPARSEABLE}: {exc}; first 200 chars of the reply: {text[:200]!r}"
            ) from exc

        # `pick_expected_artifact` tolerates a hallucinated directory slug on the BEGIN
        # line (spec 023 defect #20c) and re-keys the body to the canonical path.
        body = pick_expected_artifact(artifacts_by_path, self._artifact_key)
        if not isinstance(body, str) or not body.strip():
            raise RuntimeError(
                f"{_NO_USABLE} {self._artifact_key!r} body — the reply parsed but carried "
                f"no revised proposal (artifacts present: {sorted(artifacts_by_path)!r})"
            )

        # SSoT padding: one response per concern, "<missing>" for an unanswered one (which
        # engine.py:627 then forces open at R3), "<empty>" for an omitted field. Passing the
        # model's raw "" straight through would raise a pydantic ValidationError — not a
        # RuntimeError, so it would bypass the engine's retry entirely.
        responses = build_concern_responses(
            responses_raw, concerns, default_artifacts=[self._artifact_key]
        )
        return {**artifacts, self._artifact_key: body}, responses


__all__ = ["LaneProposalReviser"]
```

(Confirm `ConcernResponse`'s exact field set against `convergence/types.py:169-197` while implementing; supply any additional required field with its documented default.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_lane_reviser.py -q`
Expected: PASS (9 passed: 1 single-call + 1 second-attempt-identity + 2 parametrized malformed + 1 unanswered-concern-pads + 1 empty-field-placeholder + 1 verbatim-round-trip + 1 other-artifacts + 1 protocol).

- [ ] **Step 4b: Run the ENGINE-driven contract tests** (they live in Task 9's file and only pass once Task 9's helper exists — run them at the end of Task 9, and record here that they are part of THIS task's acceptance):

Run: `pytest tests/integration/test_self_improvement_proposal_review.py -k reviser -q`
Expected: PASS (3 passed: retry-recovers, two-malformed-degrades, outage-is-a-clean-abort).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/lane_reviser.py tests/integration/test_lane_reviser.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T5): LaneProposalReviser — one routed call per revise, lane hooks carried"
```

---

### Task 6: Complete `InvocationIdentity` from the explicit events

**Files:**
- Create: `src/llmxive/self_improvement/invocation_identity.py`
- Test: `tests/unit/test_self_improvement_invocation_identity.py`

**Interfaces:**
- Consumes: lane `Event`s (Slice 1A) — the audit events `EventStoreRouteAudit` recorded, plus `ReviewRerouted` (Task 1).
- Produces:
  - `class InvocationIdentityError(ValueError)` — the durable audit stream cannot yield ONE unambiguous identity for this route (duplicate authoritative events, a mismatched Attempt, or a reroute whose primary leg has no `SelectionFailure`). Fail closed: an ambiguous identity is worse than none, because it is provenance that LOOKS authoritative.
  - `@dataclass(frozen=True) class IndependenceDegraded`: `primary_profile: str`, `fallback_profile: str`, `primary_failure: Mapping[str, object]`, `relaxed_constraints: tuple[str, ...]`.
    **`primary_failure` carries all FOUR spec fields (round-4 review F5).** Spec 025 FR-002 (line 149) specifies `primary_failure: {exception_type, message, requirement_digest, snapshot_provenance}`; the round-3 plan stored only the first two. The missing two are **not duplicated into the `ReviewRerouted` payload** — slice-0 already emits them: `_select_audited` (`route.py:236-240`) emits a `SelectionFailure` for the primary leg carrying `requirement_digest` and the full `snapshot_provenance`. So `build_invocation_identity` **joins** the reroute's `primary_route_id` to that `SelectionFailure` and merges the four fields. One source of truth, an explicit reroute decision, and no divergence risk between two copies.
    The join **fails closed** (`InvocationIdentityError`) when: the referenced primary `SelectionFailure` is missing; its `exception_type` is not `ModelUnavailable`; or its Attempt id does not match this route's.
  - `@dataclass(frozen=True) class InvocationIdentity` — the Key-Entities field set (spec line 227) PLUS the provenance the maintainer review required: `actor_instance_id: str`, `model: str`, `backend: str`, `serving_endpoint: str`, `vendor: str`, `family: str`, `prompt_digest: str`, `context_digest: str`, `selection_policy_version: int`, `snapshot_digest: str`, `snapshot_provenance: Mapping[str, Mapping[str, object]]`, `route_outcome: str`, `degradation: IndependenceDegraded | None = None`. (`serving_endpoint`, `vendor`, and `snapshot_provenance` are what make "reproduce *why that model was chosen*" actually checkable.)
  - `build_invocation_identity(events: list[Event], *, route_id: str, attempt_id: str) -> InvocationIdentity | None` — from the events whose `payload["route_id"] == route_id`: the `ChainResolved` supplies the digests, `selection_policy_version`, `snapshot_digest`, `snapshot_provenance`; the `DispatchCompleted` supplies the `candidate` that ACTUALLY ran (model/backend/serving_endpoint/vendor/family); `actor_instance_id = route_id`. `route_outcome` is `"independence_degraded"` **iff a `ReviewRerouted` event names this `route_id` as its `fallback_route_id`** — read from the EXPLICIT record (F10), never inferred from a `SelectionFailure`+success coincidence. Returns `None` when there is no `ChainResolved`+`DispatchCompleted` pair (nothing ran → a failed logical call, no identity).
  - **Selection is uniqueness-checked, not `next()` (round-4 review F8).** `next()` silently resolves a corrupt stream by list order, so a duplicated or conflicting event would quietly pick one and produce authoritative-looking provenance. The rule is **exactly one** `ChainResolved` for the route (`route.py:393` emits it once per `route_chat` — the two-pass `exclude_leader` path emits only `SelectionFailure`s in pass 1, so a second one means corruption), **at most one** `DispatchCompleted` (`execute` returns on the first success), and **zero or one** `ReviewRerouted` naming this route as its fallback. More than one of any → `InvocationIdentityError`. Zero `DispatchCompleted` → `None` (nothing ran), which is not corruption.
  - **Attempt binding.** `attempt_id` is now a REQUIRED argument, and every event the identity is built from must carry it (`Event.attempt_id`). A route id colliding across Attempts, or an event mis-filed under the wrong Attempt, would otherwise attribute one Attempt's model choice to another. Mismatch → `InvocationIdentityError`.

- [ ] **Step 1: Write the failing test**

```python
"""Audit-derived InvocationIdentity (spec 025 slice 1B, Task 6).

Every audit event here is built from the REAL slice-0 dataclass through the REAL
``_audit_payload`` projection, and every constructed event is run through the REAL
``validate_lane_event``. Hand-written payload dicts would let this suite pass against a
shape production never emits — which is exactly how the sink's ``snapshot_provenance``
datetime bug survived Slice 1A.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    DispatchCompleted,
    SelectionFailure,
)
from llmxive.model_selection.types import ModelRef, SnapshotProvenance
from llmxive.self_improvement.audit_sink import _audit_payload
from llmxive.self_improvement.events import (
    REROUTE_FALLBACK_PROFILE,
    REROUTE_PRIMARY_PROFILE,
    REROUTE_RELAXED_CONSTRAINTS,
    REROUTE_TRIGGER,
    Event,
    derive_route_id,
    event_to_json,
    validate_lane_event,
)
from llmxive.self_improvement.invocation_identity import (
    InvocationIdentityError,
    build_invocation_identity,
)

TS = "2026-07-25T00:00:00+00:00"
OBSERVED = datetime(2026, 7, 25, tzinfo=UTC)
_MODEL = ModelRef(backend="dartmouth", serving_endpoint="chat", model_id="gemma-3-27b",
                  model_family="gemma", vendor="google")
_PROV = {"catalog": SnapshotProvenance(source="live", observed_at=OBSERVED, age_s=0.0)}
#: The projected form the identity actually reads back out of the log.
_PROV_JSON = {"catalog": {"source": "live", "observed_at": OBSERVED.isoformat(), "age_s": 0.0}}


def _raw_ev(etype, payload, eid, *, attempt="A1"):
    """A lane Event, NOT run through the write-boundary validator.

    Use only to model a stream that is already CORRUPT — see `_corrupt` below."""
    return Event(event_id=eid, event_type=etype, problem_id="P1", actor="a", payload=payload,
                 timestamp=TS, attempt_id=attempt, seq=0,
                 expected_problem_revision=0, resulting_problem_revision=1)


def _ev(etype, payload, eid, *, attempt="A1"):
    """Build a lane Event and PROVE it is well-formed against the real write-boundary
    validator, so a synthetic event in this file can never drift from a persisted one."""
    ev = _raw_ev(etype, payload, eid, attempt=attempt)
    validate_lane_event(json.loads(event_to_json(ev)))
    return ev


def _corrupt(event: Event, **changes) -> Event:
    """Mutate a validated event into one the writer would REFUSE.

    `_validate_review_rerouted` recomputes both route ids from the envelope `attempt_id` at
    WRITE time, so a reroute with a foreign attempt or a borrowed primary leg cannot be
    persisted at all. The reader still checks, because the log is a file on a git ref and a
    reader at a trust boundary should not assume its input was written by this code. These
    tests therefore model post-write corruption, NOT a reachable production path — which is
    exactly why they must bypass validation to construct their input.
    """
    return replace(event, **changes)


def _chain(route_id, eid="c"):
    return _ev("ChainResolved", _audit_payload(ChainResolved(
        route_id=route_id, requirement_digest="rq-1", prompt_digest="pd",
        context_digest="cd", snapshot_digest="sd", snapshot_provenance=_PROV,
        selection_policy_version=3, resolved_at=TS, explanation=("only free family",),
        candidates=(_MODEL,),
    )), eid)


def _done(route_id, eid="d", attempt="A1"):
    return _ev("DispatchCompleted", _audit_payload(DispatchCompleted(
        route_id=route_id, candidate_index=0, candidate=_MODEL, reservation_id=None,
    )), eid, attempt=attempt)


def _selfail(route_id, exception_type=REROUTE_TRIGGER, eid="s", message="none live"):
    return _ev("SelectionFailure", _audit_payload(SelectionFailure(
        route_id=route_id, exception_type=exception_type, message=message,
        requirement_digest="rq-1", snapshot_provenance=_PROV,
    )), eid)


_OP = "worthwhile-improvement:identify:abc123"
#: The two legs of _OP under attempt A1 — the ONLY route ids a valid reroute can name.
_R_PRIMARY = derive_route_id("A1", _OP, "primary")
_R_FALLBACK = derive_route_id("A1", _OP, "fallback")


def _rerouted(primary=_R_PRIMARY, fallback=_R_FALLBACK, operation_id=_OP, message="none live",
              eid="rr"):
    # Built from the SSoT constants `record_reroute` writes and `_validate_review_rerouted`
    # enforces, so this fixture cannot encode a combination production would refuse.
    return _ev("ReviewRerouted", {
        "operation_id": operation_id, "lens": "worthwhile-improvement",
        "primary_profile": REROUTE_PRIMARY_PROFILE,
        "fallback_profile": REROUTE_FALLBACK_PROFILE,
        "primary_route_id": primary, "fallback_route_id": fallback,
        "primary_failure": {"exception_type": REROUTE_TRIGGER, "message": message},
        "relaxed_constraints": list(REROUTE_RELAXED_CONSTRAINTS)}, eid)


def _build(events, route_id="R"):
    return build_invocation_identity(events, route_id=route_id, attempt_id="A1")


def test_success_identity_carries_full_selection_provenance():
    ii = _build([_chain("R"), _done("R")])
    assert ii is not None
    assert (ii.model, ii.family, ii.backend) == ("gemma-3-27b", "gemma", "dartmouth")
    assert (ii.serving_endpoint, ii.vendor) == ("chat", "google")   # reproduce WHY
    assert ii.snapshot_provenance == _PROV_JSON
    assert (ii.prompt_digest, ii.context_digest, ii.snapshot_digest) == ("pd", "cd", "sd")
    assert ii.selection_policy_version == 3
    assert ii.route_outcome == "success" and ii.degradation is None
    assert ii.actor_instance_id == "R"


def test_degradation_joins_the_primary_leg_SelectionFailure():
    # F5: FR-002 (spec line 149) requires primary_failure to carry FOUR fields. The last
    # two live on the primary leg's SelectionFailure (route.py:236-240) — join, don't
    # duplicate, so the two records can never disagree.
    events = [_selfail(_R_PRIMARY), _rerouted(), _chain(_R_FALLBACK), _done(_R_FALLBACK)]
    ii = _build(events, route_id=_R_FALLBACK)
    assert ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == REROUTE_PRIMARY_PROFILE
    assert ii.degradation.fallback_profile == REROUTE_FALLBACK_PROFILE
    assert ii.degradation.relaxed_constraints == REROUTE_RELAXED_CONSTRAINTS
    pf = ii.degradation.primary_failure
    assert pf["exception_type"] == REROUTE_TRIGGER
    assert pf["message"] == "none live"
    assert pf["requirement_digest"] == "rq-1"          # from the SelectionFailure
    assert pf["snapshot_provenance"] == _PROV_JSON     # from the SelectionFailure


def test_a_reroute_without_its_primary_SelectionFailure_fails_closed():
    # An unjoinable degradation record cannot describe WHY the primary failed; emitting a
    # partial identity would be provenance that looks authoritative but isn't.
    with pytest.raises(InvocationIdentityError, match="SelectionFailure"):
        _build([_rerouted(), _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_a_reroute_whose_primary_failed_for_another_reason_fails_closed():
    with pytest.raises(InvocationIdentityError, match="ModelUnavailable"):
        _build([_selfail(_R_PRIMARY, exception_type="ChainExhausted"), _rerouted(),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_a_reroute_whose_failure_message_diverges_fails_closed():
    # F4: exception_type + message exist on BOTH records. Two sources for one fact can
    # disagree; a silent disagreement is exactly the provenance drift the join removes.
    with pytest.raises(InvocationIdentityError, match="divergent degradation provenance"):
        _build([_selfail(_R_PRIMARY, message="no independent family"),
                _rerouted(message="something else entirely"),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_a_reroute_from_ANOTHER_attempt_cannot_mark_this_route_degraded():
    # F3: ReviewRerouted keys on fallback_route_id, not route_id, so the scoped Attempt
    # check never saw it. A foreign reroute must not classify this route.
    foreign = _corrupt(_rerouted(), attempt_id="A2")
    with pytest.raises(InvocationIdentityError, match="attempt"):
        _build([_selfail(_R_PRIMARY), foreign, _chain(_R_FALLBACK), _done(_R_FALLBACK)],
               route_id=_R_FALLBACK)


def test_a_reroute_borrowing_a_foreign_primary_leg_fails_closed():
    # Both legs must be THIS Attempt's own claims for the named operation.
    borrowed_primary = derive_route_id("A2", _OP, "primary")
    borrowed = _corrupt(_rerouted(), payload={**_rerouted().payload,
                                              "primary_route_id": borrowed_primary})
    with pytest.raises(InvocationIdentityError, match="primary_route_id"):
        _build([_selfail(borrowed_primary), borrowed,
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_the_WRITER_already_refuses_both_of_those_corruptions():
    # The two tests above bypass validation on purpose. This one proves WHY that was
    # necessary: `_validate_review_rerouted` recomputes both legs from the envelope
    # attempt_id, so neither record can be persisted in the first place. The reader's
    # checks are defense-in-depth at a trust boundary, not the only guard.
    foreign = _corrupt(_rerouted(), attempt_id="A2")
    borrowed = _corrupt(_rerouted(), payload={**_rerouted().payload,
                                              "primary_route_id": derive_route_id(
                                                  "A2", _OP, "primary")})
    for bad in (foreign, borrowed):
        with pytest.raises(ValueError, match="ReviewRerouted payload invalid"):
            validate_lane_event(json.loads(event_to_json(bad)))


def test_a_selection_failure_alone_does_not_imply_degradation():
    # F10: no inference from an event PATTERN — without an explicit ReviewRerouted record
    # naming this route as the fallback leg, the outcome is a plain success.
    ii = _build([_selfail("R"), _chain("R"), _done("R")])
    assert ii.route_outcome == "success" and ii.degradation is None


def test_no_dispatch_yields_no_identity():
    assert _build([_chain("R")]) is None


def test_no_chain_resolved_yields_no_identity():
    assert _build([_done("R")]) is None


def test_events_for_another_route_are_ignored():
    ii = _build([_chain("R"), _done("R"), _chain("OTHER", eid="c2"), _done("OTHER", eid="d2")])
    assert ii is not None and ii.actor_instance_id == "R"


# ---- F8: uniqueness + Attempt binding ----


def test_duplicate_chain_resolved_is_corruption():
    # next() would silently take the first. route.py:393 emits exactly ONE per route_chat.
    with pytest.raises(InvocationIdentityError, match="ChainResolved"):
        _build([_chain("R"), _chain("R", eid="c2"), _done("R")])


def test_duplicate_dispatch_completed_is_corruption():
    with pytest.raises(InvocationIdentityError, match="DispatchCompleted"):
        _build([_chain("R"), _done("R"), _done("R", eid="d2")])


def test_two_reroutes_naming_the_same_fallback_is_corruption():
    with pytest.raises(InvocationIdentityError, match="ReviewRerouted"):
        _build([_selfail(_R_PRIMARY), _rerouted(), _rerouted(eid="rr2"),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_two_selection_failures_for_the_primary_leg_is_corruption():
    with pytest.raises(InvocationIdentityError, match="SelectionFailure"):
        _build([_selfail(_R_PRIMARY), _selfail(_R_PRIMARY, eid="s2"), _rerouted(),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_an_event_from_another_attempt_fails_closed():
    with pytest.raises(InvocationIdentityError, match="attempt"):
        _build([_chain("R"), _done("R", eid="d2", attempt="A2")])
```

(`_ev` builds every event with `attempt_id="A1"`; `replace` is `dataclasses.replace`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_invocation_identity.py -q`
Expected: FAIL — `ModuleNotFoundError: ... invocation_identity`.

- [ ] **Step 3: Write minimal implementation**

```python
"""The audit-derived ``InvocationIdentity`` (spec 025 Key Entities line 227) — sourced
ENTIRELY from the lane's durable audit events for one ``route_id``, because
``route_chat``'s bare ``ChatResponse`` carries none of it.

``route_outcome`` is read from the EXPLICIT ``ReviewRerouted`` record (maintainer review
F10) — never inferred from a "SelectionFailure + success" event pattern, which could
coincide for unrelated reasons.

Everything here fails CLOSED. Ambiguous provenance is worse than none: it still looks
authoritative, so a reader would trust a claim about which model reviewed what, under which
constraints, that the log does not actually support.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from llmxive.self_improvement.events import Event, derive_route_id


class InvocationIdentityError(ValueError):
    """The audit stream cannot yield ONE unambiguous identity for this route (duplicate
    authoritative events, an Attempt mismatch, or a reroute whose primary leg has no
    usable ``SelectionFailure``). Fail closed: ambiguous provenance is worse than none,
    because it still LOOKS authoritative."""


@dataclass(frozen=True)
class IndependenceDegraded:
    """What a sanctioned FR-002 reroute gave up, and why."""

    primary_profile: str
    fallback_profile: str
    #: All FOUR spec fields (FR-002, spec line 149): exception_type + message from the
    #: reroute record, requirement_digest + snapshot_provenance JOINED from the primary
    #: leg's SelectionFailure (route.py:236-240) rather than duplicated.
    primary_failure: Mapping[str, object]
    relaxed_constraints: tuple[str, ...]


@dataclass(frozen=True)
class InvocationIdentity:
    """Who ran this logical call, on what, and under which selection inputs.

    ``serving_endpoint``, ``vendor`` and ``snapshot_provenance`` are what make "reproduce
    *why that model was chosen*" actually checkable — the model id alone cannot say whether
    the catalog was live or served from last-known-good.
    """

    actor_instance_id: str
    model: str
    backend: str
    serving_endpoint: str
    vendor: str
    family: str
    prompt_digest: str
    context_digest: str
    selection_policy_version: int
    snapshot_digest: str
    snapshot_provenance: Mapping[str, Mapping[str, object]]
    route_outcome: str
    degradation: IndependenceDegraded | None = None


def _exactly_one(events: list[Event], event_type: str, route_id: str) -> Event | None:
    """Return the single event of ``event_type``, or None if there are none. More than one
    is CORRUPTION (F8) — never silently resolved by list order the way ``next()`` would."""
    matches = [e for e in events if e.event_type == event_type]
    if len(matches) > 1:
        raise InvocationIdentityError(
            f"route {route_id!r} has {len(matches)} {event_type} events; exactly one is "
            "authoritative — refusing to pick one by list order"
        )
    return matches[0] if matches else None


def _primary_failure(events: list[Event], reroute_payload: Mapping[str, object],
                     attempt_id: str) -> dict[str, object]:
    """FR-002's four-field ``primary_failure`` (F5): the reroute record's exception_type +
    message, JOINED to the primary leg's ``SelectionFailure`` for the requirement digest and
    snapshot provenance that slice-0 already emits (``route.py:236-240``). Joining beats
    duplicating — two copies could disagree and only one would be the real selection input.

    Fails closed if the primary leg has no ``SelectionFailure``, if that failure was not a
    ``ModelUnavailable`` (FR-002 sanctions the reroute for nothing else), or if it belongs
    to another Attempt."""
    primary_route_id = reroute_payload["primary_route_id"]
    scoped = [e for e in events
              if e.event_type == "SelectionFailure"
              and e.payload.get("route_id") == primary_route_id]
    failure = _exactly_one(scoped, "SelectionFailure", str(primary_route_id))
    if failure is None:
        raise InvocationIdentityError(
            f"reroute names primary route {primary_route_id!r} but no SelectionFailure was "
            "recorded for it — the degradation cannot say WHY the primary leg failed"
        )
    if failure.attempt_id != attempt_id:
        raise InvocationIdentityError(
            f"primary SelectionFailure for {primary_route_id!r} belongs to attempt "
            f"{failure.attempt_id!r}, not {attempt_id!r}"
        )
    if failure.payload.get("exception_type") != "ModelUnavailable":
        raise InvocationIdentityError(
            f"primary leg {primary_route_id!r} failed with "
            f"{failure.payload.get('exception_type')!r}; FR-002 reroutes ONLY on "
            "ModelUnavailable"
        )
    # F4: the reroute record and the SelectionFailure both carry exception_type + message.
    # That is two sources for one fact, and two sources can DISAGREE — a reroute claiming
    # one failure while the selection audit records another is exactly the kind of quiet
    # provenance drift this join was meant to remove. Require them to agree exactly.
    declared = reroute_payload["primary_failure"]
    for field in ("exception_type", "message"):
        if declared[field] != failure.payload.get(field):
            raise InvocationIdentityError(
                f"reroute for primary route {primary_route_id!r} declares {field}="
                f"{declared[field]!r} but its SelectionFailure recorded "
                f"{failure.payload.get(field)!r} — divergent degradation provenance"
            )
    return {
        "exception_type": failure.payload["exception_type"],   # the SELECTION audit is
        "message": failure.payload["message"],                 # authoritative; the reroute
        "requirement_digest": failure.payload["requirement_digest"],   # copy was verified
        "snapshot_provenance": failure.payload["snapshot_provenance"],  # equal just above
    }


def _degradation(events: list[Event], route_id: str,
                 attempt_id: str) -> IndependenceDegraded | None:
    """The explicit ``ReviewRerouted`` record naming ``route_id`` as its FALLBACK leg, or
    ``None``. Never inferred from an event pattern (F10)."""
    # F3: a ReviewRerouted keys on fallback_route_id, NOT route_id, so the caller's scoped
    # Attempt check never sees it. Without the checks below, a reroute recorded under
    # ANOTHER Attempt could classify this route as independence_degraded.
    reroutes = [e for e in events
                if e.event_type == "ReviewRerouted"
                and e.payload.get("fallback_route_id") == route_id]
    if len(reroutes) > 1:
        raise InvocationIdentityError(
            f"route {route_id!r} is named as the fallback leg by {len(reroutes)} "
            "ReviewRerouted records — conflicting degradation history"
        )
    if not reroutes:
        return None

    rerouted = reroutes[0]
    if rerouted.attempt_id != attempt_id:
        raise InvocationIdentityError(
            f"route {route_id!r} is named as the fallback leg by a ReviewRerouted filed "
            f"under attempt {rerouted.attempt_id!r}, not {attempt_id!r}"
        )
    # BOTH legs must be this Attempt's own claims — a reroute that borrows another
    # Attempt's primary leg would attribute a degradation that never happened here.
    payload = rerouted.payload
    for field, leg in (("primary_route_id", "primary"), ("fallback_route_id", "fallback")):
        expected = derive_route_id(attempt_id, payload["operation_id"], leg)
        if payload[field] != expected:
            raise InvocationIdentityError(
                f"reroute {field}={payload[field]!r} is not attempt {attempt_id!r}'s "
                f"{leg} claim for operation {payload['operation_id']!r}"
            )
    return IndependenceDegraded(
        primary_profile=payload["primary_profile"],
        fallback_profile=payload["fallback_profile"],
        primary_failure=_primary_failure(events, payload, attempt_id),
        relaxed_constraints=tuple(payload["relaxed_constraints"]),
    )


def build_invocation_identity(events: list[Event], *, route_id: str,
                              attempt_id: str) -> InvocationIdentity | None:
    """The identity of the call that ran on ``route_id``, or ``None`` when none did.

    ``None`` means the route resolved no chain or dispatched nothing — a failed logical
    call has no identity, which is different from an ambiguous one (that raises)."""
    scoped = [e for e in events if e.payload.get("route_id") == route_id]
    for event in scoped:                                   # F8: Attempt binding
        if event.attempt_id != attempt_id:
            raise InvocationIdentityError(
                f"route {route_id!r} has a {event.event_type} filed under attempt "
                f"{event.attempt_id!r}, not {attempt_id!r} — refusing to attribute it"
            )
    chain = _exactly_one(scoped, "ChainResolved", route_id)
    completed = _exactly_one(scoped, "DispatchCompleted", route_id)
    if chain is None or completed is None:
        return None  # nothing actually ran → a failed logical call, no identity

    degradation = _degradation(events, route_id, attempt_id)
    ref, resolved = completed.payload["candidate"], chain.payload
    return InvocationIdentity(
        actor_instance_id=route_id,
        model=ref["model_id"],
        backend=ref["backend"],
        serving_endpoint=ref["serving_endpoint"],
        vendor=ref["vendor"],
        family=ref["model_family"],
        prompt_digest=resolved["prompt_digest"],
        context_digest=resolved["context_digest"],
        selection_policy_version=int(resolved["selection_policy_version"]),
        snapshot_digest=resolved["snapshot_digest"],
        snapshot_provenance=resolved.get("snapshot_provenance", {}),
        route_outcome="independence_degraded" if degradation is not None else "success",
        degradation=degradation,
    )


__all__ = [
    "IndependenceDegraded",
    "InvocationIdentity",
    "InvocationIdentityError",
    "build_invocation_identity",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_invocation_identity.py -q`
Expected: PASS (17 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/invocation_identity.py tests/unit/test_self_improvement_invocation_identity.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T6): complete InvocationIdentity from explicit audit + reroute events"
```

---

### Task 7: Proposal lens prompts + `build_proposal_review_spec`

**Files:**
- Create: `agents/prompts/panels/panel_si_proposal_worthwhile-improvement.md`, `..._diagnosis-correctness.md`, `..._tractability.md`, `..._testability.md`, `..._blast-radius-sanity.md`
- Create: `src/llmxive/convergence/self_improvement_specs.py`
- Test: `tests/integration/test_self_improvement_review_spec.py`

**Interfaces:**
- Consumes: `LLMReviewer` with the lane params (Task 4); `LaneProposalReviser` (Task 5); `LaneRouteContext` + `attempt_call_ceiling` (Task 2); `ReviewSpec` (`convergence/types.py:295-313`).
- Produces (beyond the spec builder): `PATCH_LENSES` and `LANE_ATTEMPT_CEILING` — see Task 2's interface block for why the patch lens NAMES must be declared before the patch slice exists.
- Produces:
  - `PROPOSAL_STAGE = "self_improvement_proposal"` (matches the `_STAGE_PREFIX` entry from Task 4).
  - `PROPOSAL_LENSES: tuple[str, ...] = ("worthwhile-improvement", "diagnosis-correctness", "tractability", "testability", "blast-radius-sanity")` — the exact lens set from the Self-improvement ReviewSpec table (spec line 278).
  - `PROPOSAL_MAX_ROUNDS = 3` (table line 281 — the engine default).
  - `build_proposal_review_spec(*, backend, repo_root: Path, proposer_baseline: IndependenceBaseline, route_context: LaneRouteContext, artifact_key: str = "proposal.md") -> ReviewSpec` — **`route_context` is REQUIRED** (F3: no silently-unaudited panel). Builds one `LLMReviewer` per lens with `stage=PROPOSAL_STAGE`, `profile="independent_review"`, `fallback_profile="deep_review"`, `independence_against=proposer_baseline`, `route_context=route_context`; the `reviser` is a `LaneProposalReviser` sharing the SAME context (so its spend and provenance land on the same Attempt); `max_rounds=PROPOSAL_MAX_ROUNDS`. Every required `ReviewSpec` field is supplied.

- [ ] **Step 0 (do first): match the ReviewSpec conventions + author the prompts.**
  (a) Read `src/llmxive/convergence/reviewspecs.py`'s `build_research_review_reviewspec` (lines 733-757) for the house convention of `kickback_routing` and `overflow_goal`, and read the `Severity` type in `convergence/types.py`. The proposal review's non-convergence outcome is `rejected` (pre-claim — spec transition table line 245), so map EVERY `Severity` member to `"rejected"` and give `overflow_goal` the same short-phrase shape the research builder uses.
  (b) Author the 5 lens prompts at the paths above, matching the house structure verified in `agents/prompts/panels/panel_spec_requirements_coverage.md`: `# Panel Reviewer — <lens> (Self-improvement proposal stage)`, then `## Lens` (the bulk — the rule, edge cases, what NOT to flag, concrete examples of what satisfies it), `## Inputs` (terse), `## Output format` (defer to `[_shared/panel_review_block.md](../_shared/panel_review_block.md)` + a one-line severity hint). Lens intents: **worthwhile-improvement** (is this change worth making at all — real recurring pain, not a nit); **diagnosis-correctness** (does the proposal's causal story actually explain the cited evidence); **tractability** (can this be implemented + evaluated within the Attempt's budget/blast-radius envelope); **testability** (is there a concrete failing-at-base / passing-at-head signal, not just "tests pass"); **blast-radius-sanity** (is the proposed surface narrow, reversible, and outside the protected model-execution surface).

- [ ] **Step 1: Write the failing test**

```python
"""The self_improvement_proposal ReviewSpec (spec 025 slice 1B, Task 7).

Integration, because the builder resolves REAL prompt files from the REAL repo root: a
missing or misnamed lens prompt must fail here rather than at runtime, inside an Attempt
that has already spent its budget getting there.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    PATCH_LENSES,
    PROPOSAL_LENSES,
    PROPOSAL_MAX_ROUNDS,
    PROPOSAL_STAGE,
    build_proposal_review_spec,
)
from llmxive.convergence.types import Severity
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import (
    LaneRouteContext,
    patch_call_ceiling,
    proposal_call_ceiling,
)

_BUDGET = 50.0   # the Attempt credit budget; ONE AttemptConfigured record binds it
                 # together with the call ceiling (Slice 1A Task 13), so every
                 # ledger for this Attempt must present the SAME pair.
_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))
#: The real repo, so the builder resolves the real prompt files.
_REPO_ROOT = Path(__file__).resolve().parents[2]


class _Sink:
    def record(self, event) -> None: ...
    def claim_dispatch(self, event) -> bool: return True


class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool: return True
    def release(self, reservation_id) -> None: ...
    def mark_retained(self, reservation_id) -> None: ...


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ctx(repo):
    ledger = LaneCallLedger(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane",
        clock=lambda: "2026-07-25T00:00:00+00:00", config=LaneLogConfig(),
        call_ceiling=LANE_ATTEMPT_CEILING,      # the WHOLE-Attempt figure, never a component
        attempt_budget_credits=_BUDGET,
    )
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )


def test_spec_wires_every_lens_with_the_reroute_and_the_shared_context(repo):
    ctx = _ctx(repo)
    spec = build_proposal_review_spec(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=ctx,
    )
    assert spec.stage == PROPOSAL_STAGE and spec.max_rounds == PROPOSAL_MAX_ROUNDS
    assert tuple(r.name for r in spec.reviewers) == PROPOSAL_LENSES
    for r in spec.reviewers:
        assert r._profile == "independent_review" and r._fallback_profile == "deep_review"
        assert r._independence_against is _BASELINE
        assert r._route_context is ctx          # the SAME context across the panel
    # the reviser shares the context too (F3: its calls are audited + budgeted)
    assert spec.reviser is not None and spec.reviser._route_context is ctx
    assert spec.artifacts == ["proposal.md"]


def test_every_lens_prompt_actually_loads_from_the_real_repo(repo):
    # `LLMReviewer.__init__` loads its prompt eagerly (llm_reviewer.py:962), so a missing
    # panel_si_proposal_<lens>.md already fails CONSTRUCTION rather than surfacing
    # mid-Attempt — good, and the reason every test in this file that builds a spec is
    # also a prompt-existence test. This one additionally checks the CONTENT contract:
    # the lens is actually addressed, and the SSoT output protocol got concatenated.
    spec = build_proposal_review_spec(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=_ctx(repo),
    )
    from llmxive.convergence.llm_reviewer import _load_system_prompt

    for reviewer in spec.reviewers:
        prompt = _load_system_prompt(stage=PROPOSAL_STAGE, lens=reviewer.name,
                                     repo_root=_REPO_ROOT)
        assert reviewer.name in prompt, f"{reviewer.name}'s prompt does not name its lens"
        # the SSoT output protocol is CONCATENATED by the loader, never restated per lens
        assert "Concerns" in prompt, "the shared panel-review block did not get appended"


def test_context_is_mandatory():
    # F3: there is no way to build an unaudited/unbudgeted proposal panel.
    with pytest.raises(TypeError):
        build_proposal_review_spec(
            backend=object(), repo_root=_REPO_ROOT,
            proposer_baseline=IndependenceBaseline(), )  # no route_context


def test_the_bound_ceiling_is_the_WHOLE_attempt_not_this_panel():
    # F1: AttemptConfigured binds ONE immutable number for the whole Attempt. Binding the
    # proposal component would starve the proposer/implementer/patch stages AND make the
    # real figure unbindable later.
    assert proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS) == 56  # N=5, R=3
    assert len(PATCH_LENSES) == 5                        # the ceiling's N_q
    assert LANE_ATTEMPT_CEILING == 90
    assert LANE_ATTEMPT_CEILING > proposal_call_ceiling(len(PROPOSAL_LENSES),
                                                        PROPOSAL_MAX_ROUNDS)
    # and it is the SUM of the whole Attempt, not just the bigger component
    assert LANE_ATTEMPT_CEILING == (
        1 + 2
        + proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS)
        + patch_call_ceiling(len(PATCH_LENSES), PROPOSAL_MAX_ROUNDS)
    )


def test_every_severity_routes_to_rejected():
    # A proposal is pre-claim work with nothing behind it: there is no lesser outcome to
    # route a writing-class concern to, the way the doc stages have.
    from llmxive.convergence.self_improvement_specs import _kickback_routing

    routing = _kickback_routing()
    assert set(routing) == set(Severity), "every severity must be explicit, not a fallback"
    assert set(routing.values()) == {"rejected"}


def test_the_overflow_goal_is_a_summarizer_instruction_not_a_stage(repo):
    # engine._maybe_reduce passes overflow_goal straight to the SSoT summarizer as its
    # goal. A stage name there would tell the summarizer to preserve the word "rejected",
    # degrading the exact artifact the five lenses read.
    spec = build_proposal_review_spec(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=_ctx(repo),
    )
    assert spec.overflow_goal != "rejected"
    assert "preserve" in spec.overflow_goal
    for must_survive in ("causal claim", "evidence", "file/test list"):
        assert must_survive in spec.overflow_goal
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_review_spec.py -q`
Expected: FAIL — `ModuleNotFoundError: ... self_improvement_specs`.

- [ ] **Step 3: Write minimal implementation**

```python
"""The self-improvement lane's ``run_convergence`` ReviewSpec builders (FR-019,
Constitution VI). Slice 1B delivers the PROPOSAL review (`self_improvement_proposal`)
with the FR-002 two-attempt reroute wired into every lens and the lane's mandatory
routing context shared by the whole panel AND the reviser.

The PATCH review (`self_improvement_patch`) reuses the same ``LLMReviewer`` mechanism
with ``fallback_profile=None`` (required independence, FAIL CLOSED) and is a later slice.

``run_convergence`` itself is unchanged: independence is wired at reviewer CONSTRUCTION,
before the panel reaches the engine (spec line 283).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.convergence.lane_reviser import LaneProposalReviser
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import ReviewSpec, Severity
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.route_context import LaneRouteContext, attempt_call_ceiling

PROPOSAL_STAGE = "self_improvement_proposal"
#: The proposal lens set (Self-improvement ReviewSpec table, spec line 278).
PROPOSAL_LENSES = (
    "worthwhile-improvement", "diagnosis-correctness", "tractability",
    "testability", "blast-radius-sanity",
)
#: The PATCH lens set (same table, line 278). The patch `ReviewSpec` BUILDER is a later
#: slice; the lens NAMES are declared now because the Attempt ceiling below needs N_q and
#: `AttemptConfigured` binds that ceiling IMMUTABLY (round-5 F1). The later slice MUST
#: build its panel from this tuple — if it uses a different size, the ceiling bound for
#: every Attempt today is wrong for the Attempt it governs.
PATCH_LENSES = (
    "implementation-correctness", "safety-blast-radius", "test-adequacy",
    "spec-adherence", "security-of-diff",
)
# `safety-blast-radius` is the spec's identifier as of rev 16. Through rev 15 the table
# read `safety/blast-radius`, which cannot be a lens name: the name is used verbatim as a
# ReviewSpec reviewer name AND as a prompt filename segment (`panel_<prefix>_<lens>.md`),
# so the `/` would create a subdirectory. Amended rather than mapped, so there is ONE
# identifier — see spec 025 rev 16, "Lens names are path-safe MACHINE IDENTIFIERS".
PROPOSAL_MAX_ROUNDS = 3          # table line 281 (the engine default)
#: A proposal the panel does not accept is REJECTED pre-claim (transition table line 245).
PROPOSAL_KICKBACK_STAGE = "rejected"

#: THE per-Attempt LLM-call ceiling (Policy Contract line 313) — the value bound into
#: `AttemptConfigured`. It spans EVERY stage of the Attempt, not just this panel: a stage
#: component would starve the other stages and, because the record is immutable, would
#: permanently lock out the real figure. == 90 for the canonical 5-lens panels at R=3.
LANE_ATTEMPT_CEILING = attempt_call_ceiling(
    proposal_panel=len(PROPOSAL_LENSES),
    patch_panel=len(PATCH_LENSES),
    max_rounds=PROPOSAL_MAX_ROUNDS,
)

#: What the SSoT summarizer must preserve when an oversized artifact is reduced
#: (``engine._maybe_reduce`` passes this straight through as the summarization goal).
#: It is an INSTRUCTION, not a stage name: these three things are exactly what the five
#: lenses read, so losing any of them to a summary would leave the panel judging a
#: proposal it can no longer check.
PROPOSAL_OVERFLOW_GOAL = (
    "preserve the causal claim, every cited evidence reference, and the "
    "file/test list verbatim"
)


def _kickback_routing() -> dict[Severity, str]:
    """Every severity routes to ``rejected``.

    The doc stages route different severities to different prior stages because they have
    somewhere lesser to go — a writing-class concern re-clarifies in place. A proposal has
    no such gradation: it is pre-claim work with nothing behind it, so ANY unresolved
    concern at the cap means this proposal is not pursued (transition table line 245).
    Every member is listed rather than relying on ``_nearest_routing``'s fallback, because
    "all severities are the same outcome here" is the actual policy and should read that
    way.
    """
    return dict.fromkeys(Severity, PROPOSAL_KICKBACK_STAGE)


def build_proposal_review_spec(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,       # REQUIRED (F3) — no unaudited lane panel
    artifact_key: str = "proposal.md",
) -> ReviewSpec:
    """The `self_improvement_proposal` panel: five lenses, each family-independent from
    the proposer with a sanctioned degrade, plus the lane reviser — all sharing ONE
    routing context so every call lands on the same Attempt's audit stream and budget."""
    reviewers = [
        LLMReviewer(
            lens=lens, stage=PROPOSAL_STAGE, backend=backend, repo_root=repo_root,
            profile="independent_review",       # attempt 1: required family independence
            fallback_profile="deep_review",     # attempt 2 on ModelUnavailable: degrade
            independence_against=proposer_baseline,
            route_context=route_context,
        )
        for lens in PROPOSAL_LENSES
    ]
    reviser = LaneProposalReviser(
        backend=backend, route_context=route_context, artifact_key=artifact_key,
    )
    return ReviewSpec(
        stage=PROPOSAL_STAGE,
        artifacts=[artifact_key],
        reviewers=reviewers,
        reviser=reviser,
        kickback_routing=_kickback_routing(),
        overflow_goal=PROPOSAL_OVERFLOW_GOAL,
        advance_stage=None,                     # the lifecycle transition is a later slice
        max_rounds=PROPOSAL_MAX_ROUNDS,
    )


__all__ = [
    "LANE_ATTEMPT_CEILING",
    "PATCH_LENSES",
    "PROPOSAL_KICKBACK_STAGE",
    "PROPOSAL_LENSES",
    "PROPOSAL_MAX_ROUNDS",
    "PROPOSAL_OVERFLOW_GOAL",
    "PROPOSAL_STAGE",
    "build_proposal_review_spec",
]
```

(`_kickback_routing()` is the small helper Step 0(a) defines by reading the `Severity` literal and the research builder's convention. `overflow_goal` was corrected during implementation — see round 15.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_review_spec.py -q`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/self_improvement_specs.py agents/prompts/panels tests/integration/test_self_improvement_review_spec.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T7): self_improvement_proposal ReviewSpec + 5 lens prompts"
```

---

### Task 8: `run_proposal_review` — the lane entry point that fails closed

**Files:**
- Modify: `src/llmxive/convergence/self_improvement_specs.py`
- Test: `tests/integration/test_run_proposal_review.py`

**Interfaces:**
- Consumes: `build_proposal_review_spec` (Task 7); `run_convergence` (`engine.py:393`); `RouteAuditError`, `RouteReplayError` (slice-0 `attempt_hooks`); `LaneCallCeilingExceeded` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class ProposalReviewOutcome`: `result: ConvergenceResult | None`, `failed_closed: bool`, `failure_kind: str` (`""` | `"audit_fatal"` | `"replay"` | `"ceiling"`), `failure_detail: str`, `producer_identity: InvocationIdentity | None`.
  - `run_proposal_review(*, backend, repo_root, proposer_baseline, route_context, artifacts, artifact_key="proposal.md", producer=None, proposer_route_id=None, constitution=None, advisory=None) -> ProposalReviewOutcome` — builds the spec and calls `run_convergence(spec, artifacts, producer=producer, constitution=..., advisory=...)`, then owns the lane's **fail-closed** classification.
  - **Producer provenance (round-4 review F7).** Two separate things, both required by FR-002:
    1. `producer` is forwarded to `run_convergence` (`engine.py:399/421`). Spec line 150 is explicit that this exclusion is *necessary-not-sufficient* and MUST NOT be relied on — it drops reviewers whose **lens name** equals the string, so it excludes nothing unless a lens is literally named that. Real independence comes from the family constraint (Task 4). It is passed anyway because it is the documented secondary guard and costs one argument; the docstring says exactly this so nobody later mistakes it for the safeguard.
    2. `proposer_route_id`, when given, resolves the proposer's **full `InvocationIdentity`** out of the same lane log via `build_invocation_identity` (Task 6) and carries it on the outcome. An `IndependenceBaseline` alone is not durable producer provenance — it records the families to avoid, not which model actually authored the proposal, with what prompt, under which snapshot. Supplying a `proposer_route_id` that does not resolve to an identity is a **fail-closed error** (`InvocationIdentityError`), never a silent `None`: a proposal whose author cannot be identified must not be reviewed as if it could. Omitting the argument entirely is allowed at this slice — the proposer itself lands in a later slice — and yields `producer_identity=None`.

    The classification:
    - `RouteAuditError` → `failed_closed=True, failure_kind="audit_fatal"`. **Why here:** the engine's `_abort_provenance` (`engine.py:433-448`) catches ONLY `BackendUnavailable`/`TransientBackendError`, so these lane errors would otherwise propagate raw with no provenance. Per FR-033a an audit-abort is a failed logical call — NOT a `ModelUnavailable`, so it never triggers the reroute and never advances a candidate.
    - `RouteReplayError` → `failed_closed=True, failure_kind="replay"`. Per FR-033a's route-replay disposition: never rerouted, never chain-advanced, reservation stays `retained`, reconciled from durable dispatch state — and explicitly **never retried** as a transient error.
    - `LaneCallCeilingExceeded` → `failed_closed=True, failure_kind="ceiling"` (Policy Contract line 313).
    - `BackendUnavailable`/`TransientBackendError` are **not** caught here — they propagate as the existing clean abort, with the engine recording them via `on_abort`.
      **They do NOT park this Attempt to resume (corrected — the earlier wording contradicted the Global Constraints).** "Park and resume next tick" is the NON-lane convergence contract; on the lane it is incompatible with the operation-id design. A resumed process re-derives the SAME operation ids, so `claim_route` returns the ORIGINAL `route_id`s and `claim_dispatch` correctly reports them as REPLAYS — the panel would not resume, it would refuse to dispatch. The postcondition is therefore explicit: **the clean abort ends the Attempt.** The outer lifecycle owner fails/terminates it, its reservations reconcile against the 026 ledger, and any later retry is a NEW Attempt with a NEW `attempt_id` and hence a disjoint route-id space (spec 025 line 220: "a crashed Attempt is a failed Attempt"). Task 8 need not catch these; it must document that.
  - The Attempt-lifecycle write (`proposal_verified` / `rejected` / `*_failed`) is deliberately NOT performed here — Slice 1A scoped Attempt-failure semantics out. This function reports the outcome; a later slice consumes it.

- [ ] **Step 1: Write the failing test**

```python
"""`run_proposal_review` — the lane entry point that fails closed (spec 025 slice 1B, T8).

The engine's `_abort_provenance` catches only `BackendUnavailable`/`TransientBackendError`,
so the three lane-fatal conditions would otherwise propagate raw with no provenance. This
suite pins that classification, and pins what is deliberately NOT caught.

`run_convergence` itself is substituted here so a specific failure can be raised from
inside it; the REAL engine drives the same entry point in Task 9's suite.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    ProposalReviewOutcome,
)
from llmxive.convergence.types import ConvergenceResult
from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    DispatchCompleted,
    RouteAuditError,
    RouteReplayError,
)
from llmxive.model_selection.types import (
    IndependenceBaseline,
    ModelRef,
    SnapshotProvenance,
)
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import LaneCallCeilingExceeded, LaneRouteContext

_CLOCK = lambda: "2026-07-25T00:00:00+00:00"  # noqa: E731
_OBSERVED = datetime(2026, 7, 25, tzinfo=UTC)
_BUDGET = 50.0   # the Attempt credit budget; ONE AttemptConfigured record binds it
                 # together with the call ceiling (Slice 1A Task 13), so every
                 # ledger for this Attempt must present the SAME pair.

#: The producer baseline every call site in this file shares. It MUST name at least one
#: family: Task 4 refuses `IndependenceBaseline()` at construction, because
#: `independent_review` asks for a family DIFFERENCE and with nothing to differ from, any
#: model satisfies it. Shared as a constant so a later edit cannot leave one call site
#: quietly empty — an empty baseline here would not test fail-closed routing at all, it
#: would raise while building the panel, before the code under test ever ran.
_PROPOSER_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))

#: The real repo, so the builder resolves the real lens prompts.
_REPO_ROOT = Path(__file__).resolve().parents[2]

_SENTINEL_RESULT = ConvergenceResult(stage="self_improvement_proposal", converged=True,
                                     rounds_used=1)


class _Sink:
    def record(self, event) -> None: ...
    def claim_dispatch(self, event) -> bool: return True


class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool: return True
    def release(self, reservation_id) -> None: ...
    def mark_retained(self, reservation_id) -> None: ...


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ctx(repo):
    ledger = LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1",
                            call_ceiling=LANE_ATTEMPT_CEILING,
                            attempt_budget_credits=_BUDGET, actor="lane",
                            clock=_CLOCK, config=LaneLogConfig())
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane",
        clock=_CLOCK, route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )


def _write_proposer_route(repo, *, route_id, attempt="A1"):
    """Write a REAL ChainResolved + DispatchCompleted pair through the REAL sink, so the
    identity this test resolves comes out of the production write path."""
    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id=attempt,
                                actor="proposer", clock=_CLOCK, config=LaneLogConfig())
    model = ModelRef(backend="dartmouth", serving_endpoint="chat", model_id="qwen3.5-122b",
                     model_family="qwen3.5", vendor="qwen")
    prov = {"catalog": SnapshotProvenance(source="live", observed_at=_OBSERVED, age_s=0.0)}
    sink.record(ChainResolved(
        route_id=route_id, requirement_digest="rq-1", prompt_digest="pd",
        context_digest="cd", snapshot_digest="sd", snapshot_provenance=prov,
        selection_policy_version=3, resolved_at=_CLOCK(), explanation=("only free family",),
        candidates=(model,),
    ))
    sink.record(DispatchCompleted(route_id=route_id, candidate_index=0, candidate=model,
                                  reservation_id=None))



def _run(repo, monkeypatch, boom, **kw):
    from llmxive.convergence import self_improvement_specs as mod

    def _fake_run_convergence(spec, artifacts, **kwargs):
        if boom is not None:
            raise boom
        return _SENTINEL_RESULT

    monkeypatch.setattr(mod, "run_convergence", _fake_run_convergence)
    return mod.run_proposal_review(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_PROPOSER_BASELINE,
        route_context=_ctx(repo), artifacts={"proposal.md": "# P"}, **kw,
    )


# ---- the three lane-fatal classifications ----


def test_audit_fatal_fails_closed(repo, monkeypatch):
    out = _run(repo, monkeypatch, RouteAuditError("sink down"))
    assert out.failed_closed and out.failure_kind == "audit_fatal" and out.result is None
    assert "sink down" in out.failure_detail


def test_replay_fails_closed_and_is_never_retried(repo, monkeypatch):
    out = _run(repo, monkeypatch, RouteReplayError("already dispatched"))
    assert out.failed_closed and out.failure_kind == "replay"


def test_ceiling_fails_closed(repo, monkeypatch):
    out = _run(repo, monkeypatch, LaneCallCeilingExceeded("out of calls"))
    assert out.failed_closed and out.failure_kind == "ceiling"


def test_a_clean_run_reports_the_engines_result_verbatim(repo, monkeypatch):
    out = _run(repo, monkeypatch, None)
    assert out.result is _SENTINEL_RESULT
    assert not out.failed_closed and out.failure_kind == "" and out.failure_detail == ""


def test_backend_unavailable_is_not_swallowed(repo, monkeypatch):
    # The engine already records + re-raises this clean abort; the lane must NOT convert it
    # into a fail-closed outcome. The abort ENDS this Attempt — it does not park it for a
    # later tick, because a resumed process would re-derive the same operation ids and the
    # dispatch gate would refuse them as replays. A retry is a NEW attempt_id.
    from llmxive.backends.base import BackendUnavailable
    with pytest.raises(BackendUnavailable):
        _run(repo, monkeypatch, BackendUnavailable("breaker open"))


def test_an_unexpected_error_is_not_misclassified(repo, monkeypatch):
    # Only the three named lane conditions are classified. Anything else is a genuine
    # defect and must surface, not be laundered into a tidy failure_kind.
    with pytest.raises(ZeroDivisionError):
        _run(repo, monkeypatch, ZeroDivisionError("engine defect"))


# ---- producer provenance (F7) ----


def test_producer_is_forwarded_to_the_engine(repo, monkeypatch):
    # F7: the documented secondary guard. NOT the safeguard — that is the family
    # constraint — but it must actually reach run_convergence.
    from llmxive.convergence import self_improvement_specs as mod
    seen = {}

    def _fake_run_convergence(spec, artifacts, **kwargs):
        seen.update(kwargs)
        return _SENTINEL_RESULT

    monkeypatch.setattr(mod, "run_convergence", _fake_run_convergence)
    mod.run_proposal_review(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_PROPOSER_BASELINE,
        route_context=_ctx(repo), artifacts={"proposal.md": "# P"}, producer="proposer",
    )
    assert seen["producer"] == "proposer"


def test_an_unresolvable_proposer_route_id_fails_closed(repo, monkeypatch):
    # F7: a proposal whose author cannot be identified must not be reviewed as if it could.
    from llmxive.self_improvement.invocation_identity import InvocationIdentityError
    with pytest.raises(InvocationIdentityError, match="no durable author provenance"):
        _run(repo, monkeypatch, None, proposer_route_id="never-dispatched")


def test_a_resolvable_proposer_route_id_is_carried_on_the_outcome(repo, monkeypatch):
    # Write a real ChainResolved + DispatchCompleted pair for the proposer's route, then
    # assert the outcome carries the FULL identity — not just the baseline.
    _write_proposer_route(repo, route_id="PR-1")
    out = _run(repo, monkeypatch, None, proposer_route_id="PR-1")
    assert out.producer_identity is not None
    assert out.producer_identity.actor_instance_id == "PR-1"
    assert out.producer_identity.model == "qwen3.5-122b"
    assert out.producer_identity.family == "qwen3.5"
    assert out.producer_identity.route_outcome == "success"


def test_omitting_the_proposer_route_id_is_allowed_and_yields_no_identity(repo, monkeypatch):
    # The proposer itself lands in a later slice; this slice must not require it.
    out = _run(repo, monkeypatch, None)
    assert out.producer_identity is None


def test_the_identity_is_resolved_BEFORE_the_panel_runs(repo, monkeypatch):
    # Fail-closed ordering: an unidentifiable author must abort before any reviewer call is
    # dispatched, or the Attempt pays its whole budget for a review it cannot attribute.
    from llmxive.convergence import self_improvement_specs as mod
    from llmxive.self_improvement.invocation_identity import InvocationIdentityError
    ran = []

    monkeypatch.setattr(mod, "run_convergence",
                        lambda spec, artifacts, **kw: ran.append(1) or _SENTINEL_RESULT)
    ctx = _ctx(repo)
    with pytest.raises(InvocationIdentityError):
        mod.run_proposal_review(
            backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_PROPOSER_BASELINE,
            route_context=ctx, artifacts={"proposal.md": "# P"},
            proposer_route_id="never-dispatched",
        )
    assert ran == [], "the panel ran despite an unresolvable author"
    assert ctx.calls_used() == 0, "the Attempt was charged for an aborted review"


def test_a_fail_closed_outcome_still_carries_the_producer_identity(repo, monkeypatch):
    # The identity is durable provenance about the AUTHOR; a lane failure during review
    # does not make it unknown, and dropping it would lose the one thing that says who
    # wrote the proposal this Attempt failed on.
    _write_proposer_route(repo, route_id="PR-1")
    out = _run(repo, monkeypatch, RouteAuditError("sink down"), proposer_route_id="PR-1")
    assert out.failed_closed and out.producer_identity is not None
    assert out.producer_identity.actor_instance_id == "PR-1"


def test_the_outcome_is_frozen():
    from dataclasses import FrozenInstanceError

    out = ProposalReviewOutcome(None, True, "ceiling", "detail")
    with pytest.raises(FrozenInstanceError):
        out.failure_kind = "replay"
```

`_write_proposer_route(repo, *, route_id)` appends a `ChainResolved` and a `DispatchCompleted` for `route_id` under `attempt_id="A1"` using `lane_log.append(..., expected_revision=None)` and the same `_REF`/`_PROV` payload shapes as Task 6's tests. `_SENTINEL_RESULT` is a minimal real `ConvergenceResult` (built from `convergence.types`, not a mock).

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_run_proposal_review.py -q`
Expected: FAIL — `AttributeError: module ... has no attribute 'run_proposal_review'`.

- [ ] **Step 3: Write minimal implementation** (append to `self_improvement_specs.py`)

```python
"""The self-improvement lane's ``run_convergence`` ReviewSpec builders (FR-019,
Constitution VI). Slice 1B delivers the PROPOSAL review (`self_improvement_proposal`)
with the FR-002 two-attempt reroute wired into every lens and the lane's mandatory
routing context shared by the whole panel AND the reviser.

The PATCH review (`self_improvement_patch`) reuses the same ``LLMReviewer`` mechanism
with ``fallback_profile=None`` (required independence, FAIL CLOSED) and is a later slice.

``run_convergence`` itself is unchanged: independence is wired at reviewer CONSTRUCTION,
before the panel reaches the engine (spec line 283).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.lane_reviser import LaneProposalReviser
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import ConvergenceResult, ReviewSpec, Severity
from llmxive.model_selection.attempt_hooks import RouteAuditError, RouteReplayError
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.invocation_identity import (
    InvocationIdentity,
    InvocationIdentityError,
    build_invocation_identity,
)
from llmxive.self_improvement.lane_log import read
from llmxive.self_improvement.route_context import (
    LaneCallCeilingExceeded,
    LaneRouteContext,
    attempt_call_ceiling,
)

PROPOSAL_STAGE = "self_improvement_proposal"
#: The proposal lens set (Self-improvement ReviewSpec table, spec line 278).
PROPOSAL_LENSES = (
    "worthwhile-improvement", "diagnosis-correctness", "tractability",
    "testability", "blast-radius-sanity",
)
#: The PATCH lens set (same table, line 278). The patch `ReviewSpec` BUILDER is a later
#: slice; the lens NAMES are declared now because the Attempt ceiling below needs N_q and
#: `AttemptConfigured` binds that ceiling IMMUTABLY (round-5 F1). The later slice MUST
#: build its panel from this tuple — if it uses a different size, the ceiling bound for
#: every Attempt today is wrong for the Attempt it governs.
PATCH_LENSES = (
    "implementation-correctness", "safety-blast-radius", "test-adequacy",
    "spec-adherence", "security-of-diff",
)
# `safety-blast-radius` is the spec's identifier as of rev 16. Through rev 15 the table
# read `safety/blast-radius`, which cannot be a lens name: the name is used verbatim as a
# ReviewSpec reviewer name AND as a prompt filename segment (`panel_<prefix>_<lens>.md`),
# so the `/` would create a subdirectory. Amended rather than mapped, so there is ONE
# identifier — see spec 025 rev 16, "Lens names are path-safe MACHINE IDENTIFIERS".
PROPOSAL_MAX_ROUNDS = 3          # table line 281 (the engine default)
#: A proposal the panel does not accept is REJECTED pre-claim (transition table line 245).
PROPOSAL_KICKBACK_STAGE = "rejected"

#: THE per-Attempt LLM-call ceiling (Policy Contract line 313) — the value bound into
#: `AttemptConfigured`. It spans EVERY stage of the Attempt, not just this panel: a stage
#: component would starve the other stages and, because the record is immutable, would
#: permanently lock out the real figure. == 90 for the canonical 5-lens panels at R=3.
LANE_ATTEMPT_CEILING = attempt_call_ceiling(
    proposal_panel=len(PROPOSAL_LENSES),
    patch_panel=len(PATCH_LENSES),
    max_rounds=PROPOSAL_MAX_ROUNDS,
)

#: What the SSoT summarizer must preserve when an oversized artifact is reduced
#: (``engine._maybe_reduce`` passes this straight through as the summarization goal).
#: It is an INSTRUCTION, not a stage name: these three things are exactly what the five
#: lenses read, so losing any of them to a summary would leave the panel judging a
#: proposal it can no longer check.
PROPOSAL_OVERFLOW_GOAL = (
    "preserve the causal claim, every cited evidence reference, and the "
    "file/test list verbatim"
)


def _kickback_routing() -> dict[Severity, str]:
    """Every severity routes to ``rejected``.

    The doc stages route different severities to different prior stages because they have
    somewhere lesser to go — a writing-class concern re-clarifies in place. A proposal has
    no such gradation: it is pre-claim work with nothing behind it, so ANY unresolved
    concern at the cap means this proposal is not pursued (transition table line 245).
    Every member is listed rather than relying on ``_nearest_routing``'s fallback, because
    "all severities are the same outcome here" is the actual policy and should read that
    way.
    """
    return dict.fromkeys(Severity, PROPOSAL_KICKBACK_STAGE)


def build_proposal_review_spec(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,       # REQUIRED (F3) — no unaudited lane panel
    artifact_key: str = "proposal.md",
) -> ReviewSpec:
    """The `self_improvement_proposal` panel: five lenses, each family-independent from
    the proposer with a sanctioned degrade, plus the lane reviser — all sharing ONE
    routing context so every call lands on the same Attempt's audit stream and budget."""
    reviewers = [
        LLMReviewer(
            lens=lens, stage=PROPOSAL_STAGE, backend=backend, repo_root=repo_root,
            profile="independent_review",       # attempt 1: required family independence
            fallback_profile="deep_review",     # attempt 2 on ModelUnavailable: degrade
            independence_against=proposer_baseline,
            route_context=route_context,
        )
        for lens in PROPOSAL_LENSES
    ]
    reviser = LaneProposalReviser(
        backend=backend, route_context=route_context, artifact_key=artifact_key,
    )
    return ReviewSpec(
        stage=PROPOSAL_STAGE,
        artifacts=[artifact_key],
        reviewers=reviewers,
        reviser=reviser,
        kickback_routing=_kickback_routing(),
        overflow_goal=PROPOSAL_OVERFLOW_GOAL,
        advance_stage=None,                     # the lifecycle transition is a later slice
        max_rounds=PROPOSAL_MAX_ROUNDS,
    )


@dataclass(frozen=True)
class ProposalReviewOutcome:
    """What the lane learned from one proposal review.

    ``failed_closed`` distinguishes "the panel reached a verdict" from "the lane refused to
    produce one". Both are honest outcomes; only the first carries a ``result``.

    The Attempt-lifecycle write (``proposal_verified`` / ``rejected`` / ``*_failed``) is
    deliberately NOT performed here — Slice 1A scoped Attempt-failure semantics out. This
    reports the outcome; a later slice consumes it.
    """

    result: ConvergenceResult | None
    failed_closed: bool
    failure_kind: str      # "" | "audit_fatal" | "replay" | "ceiling"
    failure_detail: str
    producer_identity: InvocationIdentity | None = None


def run_proposal_review(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,
    artifacts: dict[str, str],
    artifact_key: str = "proposal.md",
    producer: str | None = None,
    proposer_route_id: str | None = None,
    constitution: str | None = None,
    advisory: list[str] | None = None,
) -> ProposalReviewOutcome:
    """Run the proposal panel through the SHARED, UNMODIFIED ``run_convergence`` and own
    the lane's fail-closed classification. The engine's ``_abort_provenance``
    (``engine.py:433-448``) catches only ``BackendUnavailable``/``TransientBackendError``,
    so the three lane-fatal conditions are classified here instead of propagating raw.

    ``producer`` is forwarded to the engine's self-review exclusion. Spec 025 line 150 is
    explicit that this is NECESSARY-NOT-SUFFICIENT: ``engine.py:421`` drops reviewers whose
    LENS NAME equals the string, so it excludes nothing unless a lens is literally named
    that. Real independence comes from the family constraint on each reviewer (Task 4) —
    never treat this argument as the safeguard.

    ``proposer_route_id`` resolves the proposer's full ``InvocationIdentity`` from the same
    lane log (F7): an ``IndependenceBaseline`` records which families to avoid, not who
    actually authored the proposal. An id that does not resolve raises — a proposal whose
    author cannot be identified must not be reviewed as though it could. It is resolved
    BEFORE the panel is built, so that refusal costs nothing.

    ``BackendUnavailable``/``TransientBackendError`` are deliberately NOT caught: they are
    the engine's existing clean abort, already recorded via ``on_abort``. On the lane that
    abort ENDS the Attempt rather than parking it — a resumed process re-derives the same
    operation ids, so ``claim_route`` hands back the ORIGINAL route ids and the dispatch
    gate correctly refuses them as replays. Any retry is a NEW Attempt with a new
    ``attempt_id`` and a disjoint route-id space (spec 025 line 220).
    """
    producer_identity = None
    if proposer_route_id is not None:
        producer_identity = build_invocation_identity(
            read(route_context.repo, route_context.problem_id, config=route_context.config),
            route_id=proposer_route_id, attempt_id=route_context.attempt_id,
        )
        if producer_identity is None:
            raise InvocationIdentityError(
                f"proposer route {proposer_route_id!r} has no completed dispatch in the lane "
                "log — refusing to review a proposal with no durable author provenance"
            )
    spec = build_proposal_review_spec(
        backend=backend, repo_root=repo_root, proposer_baseline=proposer_baseline,
        route_context=route_context, artifact_key=artifact_key,
    )
    try:
        result = run_convergence(spec, artifacts, producer=producer,
                                 constitution=constitution, advisory=advisory)
    except RouteAuditError as exc:
        # FR-033a: route-fatal. NOT a ModelUnavailable → never reroutes, never advances.
        return ProposalReviewOutcome(None, True, "audit_fatal", str(exc), producer_identity)
    except RouteReplayError as exc:
        # FR-033a route-replay disposition: a failed logical call — reservation stays
        # retained, reconcile from durable dispatch state, NEVER retry as transient.
        return ProposalReviewOutcome(None, True, "replay", str(exc), producer_identity)
    except LaneCallCeilingExceeded as exc:
        return ProposalReviewOutcome(None, True, "ceiling", str(exc), producer_identity)
    return ProposalReviewOutcome(result, False, "", "", producer_identity)


__all__ = [
    "LANE_ATTEMPT_CEILING",
    "PATCH_LENSES",
    "PROPOSAL_KICKBACK_STAGE",
    "PROPOSAL_LENSES",
    "PROPOSAL_MAX_ROUNDS",
    "PROPOSAL_OVERFLOW_GOAL",
    "PROPOSAL_STAGE",
    "ProposalReviewOutcome",
    "build_proposal_review_spec",
    "run_proposal_review",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_run_proposal_review.py -q`
Expected: PASS (13 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/self_improvement_specs.py tests/integration/test_run_proposal_review.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T8): run_proposal_review entry point with lane fail-closed classification"
```

---

### Task 9: Integration — the REAL `run_convergence` panel, end to end

**Files:**
- Test: `tests/integration/test_self_improvement_proposal_review.py`

**Interfaces:** none produced (test-only). This is the F11 proof: the production reviewer path — `LLMReviewer` → `chat_with_model_fallback` → `_walker_route` → `route_chat` → the REAL `EventStoreRouteAudit`/`AttemptCreditLedger` — driven by the REAL `run_convergence` engine (including its `ThreadPoolExecutor` panel dispatch), with the reroute exercised.

- [ ] **Step 0 (do first): get the exact panel reply format.** Read `agents/prompts/_shared/panel_review_block.md` and `llm_reviewer.py`'s identify/re-review PARSERS. Craft `ScriptedBackend` replies that the PRODUCTION parsers accept for both `identify` (R1 concerns) and `rereview` (R3 verdicts), plus a `LaneProposalReviser`-shaped ```json reply for R2. **Never weaken a parser to make the test pass** — if a reply does not parse, fix the reply.

- [ ] **Step 1: Write the failing test**

```python
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
        '{"concern_id": "%s", "response": "Added the evidence paragraph.", '
        '"what_changed": "New section 2 cites the run log.", '
        '"artifacts_changed": ["proposal.md"]}' % cid
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
    repo, ctx = lane
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
```

**Also write `_run_panel_with_one_open_concern(repo, monkeypatch)` here** — it builds the real proposal `ReviewSpec` with a scripted panel whose R1 raises exactly one concern, then calls `run_convergence` and returns its result. Task 5's three ENGINE-driven reviser tests live in this file and use it (they are part of Task 5's acceptance but can only run once this helper exists). Write it once; do not duplicate the body.

**Note for the implementer:** `_ScriptedPanelBackend(raise_concerns: bool = False)`, `_aged_snapshot(age_s)`, and `_repo_root_with_prompts()` are the three helpers Step 0 produces. Reuse the existing real doubles (`ScriptedBackend` from `tests/integration/test_model_selection_execute.py`, the `_snapshot` builder from `tests/unit/test_model_selection_route.py`); `_repo_root_with_prompts()` returns the actual repo root (`llmxive.config.repo_root()`) so the REAL Task-7 prompts are loaded. `_ScriptedPanelBackend` must return: production-parseable R1 identify replies (zero concerns when `raise_concerns=False`, one concern per lens when `True`), a `LaneProposalReviser`-shaped ```json reply for R2, and passing R3 verdicts.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_proposal_review.py -q`
Expected: FAIL until the helpers exist and Tasks 1-8 are complete.

- [ ] **Step 3: Wire the helpers + make it pass** (no production change expected — this test exercises Tasks 1-8 together; if it reveals a wiring defect, fix the CODE, never the assertions).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_proposal_review.py -q`
Expected: PASS (6 passed — the 2 panel tests, Task 5's 3 engine-driven reviser tests, and the writing-residue policy test).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_self_improvement_proposal_review.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(025 slice-1B T9): real run_convergence proposal panel — audited calls + recorded reroute"
```

---

### Task 10: Integration — concurrent panel reviewers compete for the last Attempt credits

**Files:**
- Test: `tests/integration/test_self_improvement_proposal_credits.py`

**Interfaces:** none produced (test-only). This is the F2 proof the maintainer required: "an integration test that runs the convergence panel ITSELF with concurrent paid reviewer operations competing for the final Attempt credits. A direct `execute()` test is necessary but not sufficient."

**How paid candidates become eligible — read this before writing the fixture.** The round-4 review asked for a `RequirementOverrides(allow_paid=True)` threaded through the lane, on the premise that all six profiles default `allow_paid=False` so nothing paid can ever be selected. **That premise does not hold, and the override would be the wrong fix.** `route_chat` treats the profile's `allow_paid` as a DEFAULT and overrides it per call: when the caller passes neither `allow_paid` nor `overrides.allow_paid`, it uses `allow_paid_eff = snap.credit.paid_opt_in` (`route.py:343-360`) and hands that to `build_requirement(...)`, whose `**overrides` go through `replace(req, ...)` (`profiles.py:56-82`). `_walker_route` passes neither (`backends/router.py:272-281`), so the lane's calls already inherit the process opt-in. Hard-coding `allow_paid=True` in the lane would be a policy REGRESSION — it would assert "the lane always allows paid" instead of deferring to `LLMXIVE_PAID_OPT_IN`, which is exactly what FR-033 keys on. (It could not actually overspend — `select.py:139` still requires `credit.source == "live" and credit.paid_opt_in` — but it would state the wrong intent.)

What IS required, and what the round-3 plan left implicit, is the **snapshot contract** for the fixture. `_paid_only_snapshot()` MUST produce a `RuntimeSnapshot` whose `credit` has `source="live"` AND `paid_opt_in=True`, and whose candidates are priced non-free; if either credit field is wrong, `paid_admissible` is `False`, every candidate is filtered, and the test fails with `ModelUnavailable` having proven nothing about the ledger. Assert that contract in the fixture itself so a future edit cannot silently defang the test.

- [ ] **Step 1: Write the failing test**

```python
"""F2: the Attempt budget binds through the PANEL, not just through a direct execute()
call. The engine dispatches the 5 lenses through a real ThreadPoolExecutor
(engine.py:85-133, cap 8), all sharing ONE AttemptCreditLedger, so this exercises the
genuine concurrent-reservation path with paid opt-in ON.
"""

from __future__ import annotations

import subprocess
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    PROPOSAL_LENSES,
    run_proposal_review,
)
from llmxive.model_selection.types import (
    IndependenceBaseline,
    ModelPricing,
    worst_case_credits,
)
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.credit_ledger import (
    AttemptCreditLedger,
    counting_total,
    project_reservations,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import LaneRouteContext

from .test_self_improvement_proposal_review import (  # the SSoT scripted panel
    _ScriptedPanelBackend,
)

_CLOCK = lambda: "2026-07-25T00:00:00+00:00"  # noqa: E731
_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))
_REPO_ROOT = Path(__file__).resolve().parents[2]
#: `route_chat`'s own default (route.py:254). The retry envelope reserves
#: `worst_case x retries`, so the budget arithmetic must use the SAME number.
_ROUTE_RETRIES = 3


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


class _ThreadRecordingAuthority:
    """A REAL delegating ReservationAuthority (not a mock): every call goes to the genuine
    AttemptCreditLedger; this only RECORDS who called and what came back, so the test can
    prove the authority was actually exercised concurrently and that some candidate was
    genuinely refused by the cap."""

    def __init__(self, inner):
        self._inner = inner
        self._lock = threading.Lock()
        self.threads: set[int] = set()
        self.admitted: list[tuple[str, float]] = []
        self.refused: list[tuple[str, float]] = []

    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        ok = self._inner.reserve(credits, reservation_id=reservation_id, call_id=call_id)
        with self._lock:
            self.threads.add(threading.get_ident())
            (self.admitted if ok else self.refused).append((reservation_id, credits))
        return ok

    def release(self, reservation_id) -> None:
        self._inner.release(reservation_id)

    def mark_retained(self, reservation_id) -> None:
        self._inner.mark_retained(reservation_id)


def _paid_only_snapshot(*, paid_opt_in: bool = True):
    """The offline chain repriced so EVERY candidate is paid, with a live credit guard.

    Asserts its own contract at the end: `select.py:139` admits a paid candidate only when
    `credit.source == "live" and credit.paid_opt_in`, so a wrong credit field would filter
    every candidate and the test would pass by proving nothing about the ledger.
    """
    import llmxive.model_selection.route as route_mod

    base = route_mod.runtime_snapshot()
    pricing = {mid: ModelPricing(1e-6, 5e-6) for mid in base.pricing}
    # The DAILY (026) cap is raised far above the Attempt budget on purpose: two ledgers
    # gate a paid call, and this test is about the ATTEMPT one. Leaving the daily cap near
    # the Attempt budget would make it ambiguous which ledger refused a candidate.
    credit = replace(base.credit, source="live", paid_opt_in=paid_opt_in,
                     max_budget=1_000_000.0, effective_cap=750_000.0,
                     available_headroom=750_000.0, spend=0.0)
    snap = replace(base, pricing=pricing, credit=credit,
                   sources={**base.sources,
                            "credit": replace(base.sources["credit"], source="live")})

    assert snap.credit.source == "live"
    assert snap.credit.paid_opt_in is paid_opt_in
    assert snap.pricing and all(not p.is_free for p in snap.pricing.values()), \
        "a free candidate would dispatch without ever consulting the Attempt authority"
    return snap


def _worst_case_envelope(snap, *, max_tokens: int) -> float:
    """One candidate's RESERVED envelope, from the snapshot's own prices and the real
    call budget — never a hard-coded credit figure (F9).

    Uses the largest lens prompt as the input sample, so the derived budget admits at least
    a few whole envelopes rather than being accidentally too small for any of them.
    """
    from llmxive.backends.base import ChatMessage
    from llmxive.convergence.llm_reviewer import _load_system_prompt
    from llmxive.model_selection.tokens import call_budget_for

    biggest = max(
        (_load_system_prompt(stage="self_improvement_proposal", lens=lens,
                             repo_root=_REPO_ROOT) for lens in PROPOSAL_LENSES),
        key=len,
    )
    budget = call_budget_for([ChatMessage(role="system", content=biggest)], max_tokens)
    per_call = max(
        c for c in (worst_case_credits(p, budget) for p in snap.pricing.values())
        if c is not None
    )
    # execute.py:178 — a paid candidate reserves worst_case x retries.
    return per_call * _ROUTE_RETRIES


def _reviewer_max_tokens() -> int:
    """The token bound a lane reviewer actually routes with, read off the REAL class
    rather than restated as a literal that could drift."""
    from llmxive.convergence.llm_reviewer import LLMReviewer

    reviewer = LLMReviewer(lens=PROPOSAL_LENSES[0], stage="self_improvement_proposal",
                           backend=object(), repo_root=_REPO_ROOT)
    return reviewer._max_tokens


def _local_production_ledger(monkeypatch, repo):
    """Point the 026 PRODUCTION credit ledger at the temp repo, local-only.

    Two ledgers gate a paid dispatch: 026's daily ledger and this lane's Attempt ledger.
    Without this the daily one fails closed first (`ledger_config_from_env` raises unless
    `LLMXIVE_CREDIT_LEDGER_ANCHOR` is pinned), every paid candidate is SKIPPED before the
    Attempt authority is ever consulted, and the test passes while proving nothing.

    Both remain REAL — a real git-CAS ledger in a real temp repo. Only the *location* is
    redirected: `LLMXIVE_REPO_ROOT` so `execute`'s `ledger_repo = repo_root()` resolves to
    the temp repo rather than the developer's actual checkout (which it would otherwise
    write reservations into), and a local-only `LedgerConfig` so no remote fetch is
    attempted.
    """
    # `importlib`, not `import ... as` or a dotted monkeypatch string: the package
    # re-exports the `execute` FUNCTION under the same name as its module, so both of
    # those resolve to the function and setattr fails.
    import importlib

    from llmxive.model_selection.ledger_transport import LedgerConfig

    execute_mod = importlib.import_module("llmxive.model_selection.execute")

    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    monkeypatch.setattr(execute_mod, "ledger_config_from_env",
                        lambda **_kw: LedgerConfig(remote=None))


def _paid_ctx(repo, *, budget: float):
    """The full paid wiring: a REAL AttemptCreditLedger behind a recording delegate, the
    REAL audit sink, and the REAL call ledger — all on one temp git repo."""
    cfg = LaneLogConfig()
    inner = AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                                attempt_budget_credits=budget,
                                call_ceiling=LANE_ATTEMPT_CEILING, actor="lane",
                                clock=_CLOCK, config=cfg)
    authority = _ThreadRecordingAuthority(inner)
    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1",
                                actor="lane", clock=_CLOCK, config=cfg)
    call_ledger = LaneCallLedger(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane", clock=_CLOCK, config=cfg,
        call_ceiling=LANE_ATTEMPT_CEILING,  # the WHOLE-Attempt figure, never a component
        attempt_budget_credits=budget,      # the SAME budget the credit ledger binds
    )
    ctx = LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane", clock=_CLOCK,
        route_audit=sink, reservation_authority=authority, call_ledger=call_ledger,
        config=cfg,
    )
    return ctx, authority


def test_concurrent_panel_reviewers_never_exceed_the_attempt_budget(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    _local_production_ledger(monkeypatch, repo)
    snap = _paid_only_snapshot()             # asserts its own contract
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)

    # Derive the budget from the SNAPSHOT's real prices + the call's token bound, not a
    # magic number (F9): room for ~2 of the 5 concurrent worst-case envelopes, so some
    # reviewers are admitted and some are genuinely refused by the cap.
    budget = 2 * _worst_case_envelope(snap, max_tokens=_reviewer_max_tokens())
    ctx, authority = _paid_ctx(repo, budget=budget)

    # Starving some lenses means those routes fail; whether the panel as a whole returns
    # or aborts is nondeterministic, so accept either and assert on the DURABLE state.
    from llmxive.backends.base import BackendUnavailable
    try:
        run_proposal_review(
            backend=_ScriptedPanelBackend(), repo_root=_REPO_ROOT,
            proposer_baseline=_BASELINE, route_context=ctx,
            artifacts={"proposal.md": "# Proposal\n\nNarrow the retry loop.\n"},
        )
    except BackendUnavailable:
        pass

    events = read(repo, "P1", config=LaneLogConfig())
    reservations = project_reservations(events, "A1")

    # 1. THE invariant (US1 scenario 5): reserved envelopes never exceed the cap, no matter
    #    how the 5 concurrent reviewers interleaved.
    assert counting_total(reservations) <= budget

    # 2. The authority was genuinely exercised, CONCURRENTLY (F9: without this, "no
    #    dispatch happened at all" would pass assertion 1 vacuously).
    assert len(authority.threads) > 1, "reviewers did not compete from separate threads"

    # 3. At least one paid dispatch actually COMPLETED — the budget bound is meaningless if
    #    nothing ever ran.
    completed = [e for e in events if e.event_type == "DispatchCompleted"]
    assert completed, "no paid dispatch completed — the test proved nothing about the cap"

    # 4. At least one candidate was REFUSED by the Attempt cap (that is the behavior under
    #    test; if everything fit, the budget was too generous).
    assert authority.refused, "no reservation was refused — tighten the budget"

    # 5. Every paid DispatchStarted is backed by a real reservation, and no reservation
    #    exists that the projection doesn't know about (no silent unpriced dispatch).
    started = [e for e in events if e.event_type == "DispatchStarted"]
    paid_started = [e for e in started if e.payload.get("reservation_id")]
    assert paid_started, "expected paid dispatches in a paid-only chain"
    for e in paid_started:
        assert e.payload["reservation_id"] in reservations

    # 6. The admitted envelopes sum EXACTLY to the durable projection — the recorded
    #    decisions and the persisted state cannot drift.
    assert counting_total(reservations) == pytest.approx(
        sum(c for rid, c in authority.admitted
            if rid in reservations and reservations[rid].state != "released")
    )
    for r in reservations.values():
        assert r.state in {"open", "retained", "reconciled", "released"}


def test_with_paid_opt_in_OFF_no_paid_candidate_ever_dispatches(repo, monkeypatch):
    """The other half of the F2 contract: paid eligibility follows the PROCESS opt-in
    (route.py:353), so with the opt-in off the same paid-only chain must select nothing and
    open no reservation — never a paid dispatch, never a charge."""
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    _local_production_ledger(monkeypatch, repo)
    snap = _paid_only_snapshot(paid_opt_in=False)
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)
    # A budget large enough that ONLY the opt-in can be what blocks a reservation.
    ctx, authority = _paid_ctx(repo, budget=1000.0)

    # With a paid-only chain and the opt-in OFF, selection finds nothing eligible for
    # EVERY lens → ModelUnavailable → BackendUnavailable, which Task 8 propagates as a
    # clean abort. Assert the exception, THEN the durable state — which is what actually
    # proves the budget invariant (round-11 F4).
    from llmxive.backends.base import BackendUnavailable

    with pytest.raises(BackendUnavailable):
        run_proposal_review(
            backend=_ScriptedPanelBackend(), repo_root=_REPO_ROOT,
            proposer_baseline=_BASELINE, route_context=ctx,
            artifacts={"proposal.md": "# Proposal"},
        )

    events = read(repo, "P1", config=LaneLogConfig())
    assert not project_reservations(events, "A1"), "a paid reservation opened with opt-in OFF"
    assert not authority.admitted, "the Attempt authority admitted a reservation with opt-in OFF"
    assert not [e for e in events if e.event_type == "DispatchStarted"]
```

**Notes for the implementer:**
- **A test that starves the panel must expect the EXCEPTION, not an outcome (round-11 F4).** `run_proposal_review` returns an outcome only when the panel actually ran. Anything that makes every lens fail to route — a paid-only chain with the opt-in off, a budget so tight the Attempt authority refuses every reservation, a ceiling exhausted mid-panel — ends in `ModelUnavailable` → `BackendUnavailable` (or `LaneCallCeilingExceeded`), which Task 8 propagates. Write those as `pytest.raises(...)` and then assert on the DURABLE events and reservations; that is what proves the budget invariant anyway, and it does not depend on a return value the API never promised. Assigning `outcome = run_proposal_review(...)` in such a test silently makes every assertion after it unreachable.
- **Every lane reviewer needs a non-empty producer baseline.** `IndependenceBaseline()` is refused at construction (Task 4): `independent_review` requires a family DIFFERENCE, so an empty baseline would leave FR-002's independence satisfied by any model. Fixtures must pass real families.
- `_paid_only_snapshot(paid_opt_in=True)` mirrors the paid-candidate fixtures in `tests/integration/test_model_selection_execute.py`. It MUST end with an in-fixture assertion of its own contract — `snap.credit.source == "live"` and `snap.credit.paid_opt_in is paid_opt_in`, and every candidate priced non-free — so a later edit cannot silently turn this into a test that passes by selecting nothing.
- `_worst_case_envelope(snap, max_tokens)` computes one candidate's reserved envelope from the snapshot's own prices and the call budget, using the SAME helper `execute` uses. Do not hard-code a credit figure.
- The reviewers whose reservation is refused skip/advance and ultimately surface as a clean abort — assert the invariants above, not a particular per-lens outcome, since the interleaving is genuinely nondeterministic.
- If assertion 4 proves flaky because the panel serializes in practice, fix the BUDGET (tighten it) — never delete the assertion.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_proposal_credits.py -q`
Expected: FAIL until the helpers exist and Tasks 1-8 are complete.

- [ ] **Step 3: Wire the helpers + make it pass** (fix the CODE if the invariant is violated — never relax the assertion).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_proposal_credits.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_self_improvement_proposal_credits.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(025 slice-1B T10): concurrent panel reviewers never exceed the Attempt budget"
```

---

## Final verification (before the whole-branch review)

- [ ] Package exports (`src/llmxive/self_improvement/__init__.py`): add `LaneRouteContext`, `proposal_call_ceiling`, `patch_call_ceiling`, `attempt_call_ceiling`, `InvocationIdentity`, `IndependenceDegraded`, `InvocationIdentityError`, `build_invocation_identity`. (`LaneCallCeilingExceeded`, `LaneCallLedger`, `derive_route_id` are already exported by Slice 1A — re-export, never redefine.) Test they import.
- [ ] `ruff check` clean on every touched file.
- [ ] Full non-slow suite green: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → 0 failed (network-restricted-sandbox artifacts itemized).
- [ ] `enforcement.py` guard passes: no model-id literal in lane code (`pytest tests/unit -k enforcement -q`).
- [ ] Behavior preservation spot-check: `pytest tests/unit -k "router or llm_reviewer or convergence" -q` → the research/paper path is unchanged.
- [ ] Prompt-eval gate: `agents/prompts/**` changed, so the promptfoo eval (`.github/workflows/prompt-eval.yml`) applies to the 5 new lens prompts — confirm they follow the house structure Step 0(b) verified.
- [ ] Commit discipline honored on every task; **nothing pushed**.

## Requirement traceability

| Source | Requirement | Task |
|-|-|-|
| Round-1 review F2 | `reservation_authority` threaded to reviewers AND reviser; panel-level concurrent-credit test | T2, T3, T4, T5, T7, **T10** |
| Round-1 review F3 | Mandatory audit (no `route_audit=None` default); reviser covered | T2 (required fields), T5, T7 (required param) |
| Round-1 review F10 | EXPLICIT reroute/degradation event; complete `InvocationIdentity` (endpoint/vendor/provenance) | T1, T2 (`record_reroute`), T4, T6 |
| Round-1 review F11 | Real production reviewer path through `run_convergence` | **T9** |
| FR-002 | Two-attempt reroute, `independent_review` → `deep_review`, degrade-never-fail-closed, no new profile | T4, T7 |
| FR-002 (patch binding) | Same mechanism, `fallback_profile=None` → fail closed | T4 (covered by test; the patch ReviewSpec is a later slice) |
| FR-033a | Route-fatal audit abort; route-replay disposition | T8 |
| Policy Contract line 313 | Stage-specific ceiling `4N + R·(2N+2)`; reviser is ONE call | T2, T5, T9 |
| ReviewSpec table lines 273-283 | Stage, lens set, reviser, profiles, independence binding, `max_rounds=3` | T7 |
| Key Entities line 227 | `InvocationIdentity` sourced from the audit sink | T6 |
| SC-008 | All lane calls via `route_chat`; no model-id literals | T3, T4, T5 + final verification |

## Round-4 review (the 1B findings)

| # | Finding | Resolved by |
|-|-|-|
| 1 | the call ceiling was in-memory, so NOT per-Attempt | **Slice 1A T14** `LaneCallLedger` (durable CAS admission + retry-stable `route_id`s); T2's `LaneRouteContext` now holds it and is frozen; T4/T5 claim per logical call; `next_operation_id` separates a legitimate in-process repeat from a restart replay |
| 2 | "paid is ineligible, add `RequirementOverrides(allow_paid=True)`" | **Premise corrected** (T10): `route_chat` derives `allow_paid` from `snap.credit.paid_opt_in` when the caller passes neither (`route.py:343-360`), and `build_requirement`'s `**overrides` replace the profile default — so the profile's `allow_paid=False` does not govern, and hard-coding `True` would assert the wrong policy. The real gap (the fixture's implicit snapshot contract) is fixed, plus the requested paid-opt-in-OFF counterpart test |
| 3 | the lane reviser raised the wrong exception type | T5 raises `RuntimeError` with the two signatures `is_malformed_reply_error` recognizes; the reasoning is documented at the raise sites; **3 ENGINE-driven tests** (retry recovers / two malformed degrade / outage is a clean abort) live in T9's file |
| 4 | reroute-record persistence failures bypassed the fail-closed classification | T2's `record_reroute` normalizes `GitLog*`/`Lane*`/`ValueError` to `RouteAuditError`; T4 records BEFORE the fallback dispatch and does not catch it, with a test asserting the fallback never runs |
| 5 | degradation provenance was missing 2 of the 4 spec fields | T6 JOINS the reroute's `primary_route_id` to its `SelectionFailure` (which already carries `requirement_digest` + `snapshot_provenance`, `route.py:236-240`) instead of duplicating; fails closed on missing / non-`ModelUnavailable` / wrong-Attempt |
| 6 | `ReviewRerouted` payload validation was nominal | **Slice 1A T2** adds the `TYPE_VALIDATORS` mechanism; **T1** registers `_validate_review_rerouted` pinning the required keys, distinct route ids, both profiles, the `ModelUnavailable` trigger, and the exact relaxed-constraint list |
| 7 | `producer` not passed; producer identity thin | T8 forwards `producer` (documented as necessary-not-sufficient) and resolves an optional `proposer_route_id` to a full `InvocationIdentity`, failing closed when it does not resolve |
| 8 | `next()` silently resolved duplicate authoritative events | T6 `_exactly_one` + the reroute-count check + Attempt binding; 4 corruption tests |
| 9 | the paid concurrency invariant was too weak | T10 adds: multi-thread authority use, ≥1 completed paid dispatch, ≥1 cap refusal, every paid `DispatchStarted` backed by a reservation, admitted envelopes summing exactly to the projection — and derives the budget from the snapshot's prices instead of the unexplained `2.5` |
| 10 | 1A's bootstrap concurrency test was sequential | **Slice 1A** T1 `_after_probe` seam + T3's real two-clone bootstrap race |

## Round-5 review

| # | Finding | Resolved by |
|-|-|-|
| 1 | the durable ceiling was checked against a constructor-local bound | **Slice 1A T13** `AttemptConfig` binds the ceiling AND the credit budget in ONE `AttemptConfigured` record; every ledger enforces the bound value and fails closed at construction on a mismatch. Every `LaneCallLedger` construction in this plan now passes both limits |
| 2 | `next_operation_id` is not restart-safe for a legitimately repeated call | **Concern adopted, remedy scoped.** A durable workflow position is the right answer *if* convergence is resumable — but spec 025 says it is not: "a crashed Attempt is a failed Attempt" (line 220) and an unresolved dispatch "fails the Attempt closed" (line 212), and a retry is a NEW `attempt_id` with a disjoint route-id space. The invariant is now an explicit Global Constraint and a docstring paragraph, the ONLY cross-process case (a duplicate/zombie worker) has a test asserting it replays rather than double-dispatches, and both places carry an explicit instruction: any future slice that adds resumable convergence MUST first replace the ordinal with a durable position (which also means the engine must pass round metadata down) |
| 3 | the reroute event escaped the scoped Attempt check | T6 checks `reroute.attempt_id`, and that BOTH legs are this Attempt's own claims for the named operation (`derive_route_id`); 2 new tests beside the cross-Attempt `DispatchCompleted` one |
| 4 | "one source of truth" still allowed two copies to disagree | T6 requires the reroute's `exception_type`/`message` to equal the `SelectionFailure`'s exactly, then reads all four fields from the selection audit; divergence fails closed |
| 5 | `LaneCallClaimed` validation checked only basic types | **Slice 1A T2**: validators now receive the whole event, so payload-vs-envelope `attempt_id` agreement, `leg ∈ LEGS`, and `route_id == derive_route_id(...)` are all enforced; cross-event ceiling consistency is finding 1's `AttemptConfig` |
| 6 | the "pinned" `ReviewRerouted` schema accepted extra keys | T1 rejects unknown keys in both the payload and `primary_failure` (matching the convergence types' `extra="forbid"` house style), with tests |

## Round-6 review

| # | Finding | Resolved by |
|-|-|-|
| 1 | `AttemptConfigured.call_ceiling` was being populated with the PROPOSAL component (56) | T2 adds `attempt_call_ceiling(...)` — the whole Policy Contract line-313 expression (`proposer + implementer·(1 + impl_regen_retries) + proposal + patch`) — and T7 exports `LANE_ATTEMPT_CEILING` (= **90** for the canonical 5-lens panels at R=3). Every ledger in this plan binds THAT; `proposal_call_ceiling`/`patch_call_ceiling` remain as components with docstrings saying they must never be bound. T7 declares `PATCH_LENSES` because the immutable record needs `N_q` before the patch slice exists — the later patch builder MUST consume that tuple |
| 2 | the credit budget accepted `nan`/`inf` | **Slice 1A T13/T2** — finite/bool/numeric checks at both boundaries plus `allow_nan=False` in the canonical serializers |
| 3 | `AttemptConfigured` / `LaneCallClaimed` accepted unknown keys | **Slice 1A T2** — shared `_exact_keys`, both schemas pinned |
| — | hardening suggestion (adopted) | T1's `ReviewRerouted` validator now enforces the envelope `attempt_id` and recomputes BOTH route ids at WRITE time — the same binding `build_invocation_identity` checks at projection time, so a foreign/borrowed leg can never become durable in the first place |

## Round-7 review

| # | Finding | Resolved by |
|-|-|-|
| 1 | individual reservation AMOUNTS were unvalidated | **Slice 1A T7** `reserve()` rejects non-finite, `bool`, and `<= 0` amounts with `ValueError` (never `False` — that would read as a routine budget skip), and **T2** registers an `AttemptCreditReserved` payload validator so a persisted record carries the same guarantee. Tests: `-1/0/nan/±inf/True` each raise before any append and leave state + budget unchanged, plus a projection test pinning WHY (a negative amount lowers `counting_total` and hands back spent budget) |
| 2 | `PATCH_LENSES` was not literally the spec's identifier | **Spec 025 amended to rev 16**: `safety/blast-radius` → `safety-blast-radius`, plus a new rule that lens names are path-safe machine identifiers (a lens name is a `ReviewSpec` reviewer name AND a prompt filename segment, so `/` would create a subdirectory). Amended rather than mapped — one identifier, nothing to drift |
| — | found while verifying finding 1 | This plan's Global Constraints claimed "free candidates reserve 0, so the mechanism is inert". Wrong: `execute.py:403` gates the whole reservation path on `if not candidate.pricing.is_free:`, so the authority is never called at all for a free candidate. Corrected — and it is what makes the strictly-positive contract safe |

## Round-11 review (Slice 1B Tasks 1-4, mid-implementation)

| # | Finding | Resolved by |
|-|-|-|
| 1 | **High** — a lane reviewer could EXECUTE one profile pair while durably RECORDING the sanctioned one (`record_reroute` hard-codes the provenance; the event validator only ever sees what was written, so nothing downstream could detect it) | **T4** `_validate_lane_configuration` in `LLMReviewer.__init__` accepts exactly three configurations — proposal / patch / non-lane — and refuses everything else at construction. The sanctioned values became PUBLIC in `events.py` and are now imported by both `record_reroute` (what is written) and the check (what executes); they had been defined twice, which is the mechanism by which they could drift. Lane-only arguments without a `route_context` are refused rather than silently ignored |
| 2 | **High** — an EMPTY producer-family baseline silently defeats FR-002 (`independent_review` requires a family difference; with nothing to differ from, any model satisfies it) | **T4** same check: a lane reviewer needs a baseline naming ≥1 family. **T7**'s builder inherits this by construction, and T10's fixtures were corrected — one of them passed `IndependenceBaseline()` |
| 3 | **Medium** — the plan contradicted its own non-resumable-Attempt contract ("the run parks to resume next tick") | **T8 wording corrected.** A clean abort ENDS the Attempt; park-and-resume is the NON-lane contract. On the lane a resumed process re-derives the same operation ids, so `claim_dispatch` reports REPLAYS and the panel refuses to dispatch rather than resuming. The outer lifecycle owner fails the Attempt; a retry is a NEW `attempt_id` with a disjoint route-id space |
| 4 | **Medium** — T10's paid-opt-out test assigned `outcome = run_proposal_review(...)` for a scenario that raises, making every later assertion unreachable | **T10 rewritten** to `pytest.raises(BackendUnavailable)` then assert the durable events/reservations — which is what proves the budget invariant anyway. A general implementer note now covers every starve-the-panel variant (tight budget, exhausted ceiling) |
| 5 | **Low** — operation identity used `json.dumps(..., default=str)`, which falls back to object repr for multimodal content | **T4** digests via `model_selection.route.messages_digest`, promoted from `_messages_digest` — the canonical projection already used for `prompt_digest`, which hashes image bytes instead of relying on repr |

## Round-12 review (Slice 1B Tasks 1-4 + plan, post-fix)

| # | Finding | Resolved by |
|-|-|-|
| 1 | Round-11 finding 2 was applied INCOMPLETELY — three lane call sites still built panels with `IndependenceBaseline()`, which Task 4 now refuses at construction. Those tests would have died while building the panel, before reaching the behavior they name | **T8** gained a shared `_PROPOSER_BASELINE` constant (used by `_run` and the producer-forwarding test) so one edit cannot leave a call site empty again; **T10**'s paid concurrency test takes a real family. The intentionally-empty one in `test_context_is_mandatory` stays: it fails at the signature, before any baseline check |
| 2 | T4's patch fail-closed test injected the router, raised raw `ModelUnavailable` itself, and expected raw `ModelUnavailable` — bypassing the wrapper it claimed to test. `_route_review` passes `reraise_model_unavailable=(fallback is not None)`, so with no fallback the real wrapper CONVERTS to `BackendUnavailable` and the `except ModelUnavailable` branch is unreachable. The test pinned a contract production cannot produce | **T4 test rewritten to drive the REAL wrapper**: no injected router, `independence_against` excludes every family in the offline snapshot, so real selection raises a real `ModelUnavailable` (`select.py:197`) and the wrapper converts it. Asserts `BackendUnavailable` (a disjoint type, so asking for raw fails loudly), no reroute record, and exactly one charged call. Verified load-bearing — forcing `reraise_model_unavailable=True` fails it |
| 3 | **Low** — the reroute constants were documented as public but missing from `events.__all__` | Added all four to `__all__`. They are genuinely public surface: three separate modules (the validator, `record_reroute`, and T4's configuration check) share them as the single source of truth |

## Round-13 (Task 5 implementation — three corrections found against the reviser package)

All three are the same shape: the round-12 plan reinvented something `convergence/revisers/`
had already solved, and each reinvention silently reintroduced a defect that package had
already fixed. Only the DISPATCH (one routed call per `revise()`) ever needed to be bespoke.

| # | Finding | Resolved by |
|-|-|-|
| 1 | **Correctness** — `ConcernResponse(response=r.get("response", ""))` raises a pydantic `ValidationError` when the model omits a field (both fields are `Field(min_length=1)`, `types.py:184-185`). `ValidationError` is not a `RuntimeError`, so it skips the engine's retry AND escapes the run with no provenance — exactly the failure class F3 exists to prevent | `build_concern_responses` (the SSoT every reviser uses) substitutes `"<empty>"`. Regression test asserts it; verified load-bearing (bypassing the helper reproduces the `ValidationError`) |
| 2 | **Correctness** — an unanswered concern raised `no usable`, discarding a revision that may have addressed every OTHER concern, and also firing on a harmless superset of ids. MAINTAINER-DECIDED 2026-07-28 | The same helper pads `response="<missing>"`; `engine.py:627-628` then forces that concern open at R3 deterministically. Identical honesty, more work preserved |
| 3 | **Correctness** — the plan invented a fourth wire format (`{"proposal": "<markdown>"}` in one json fence) that nothing else in the repo speaks, embedding a whole document inside a JSON string. That re-introduces the escaping failures the `===BEGIN_ARTIFACT===` markers exist to eliminate — a proposal contains quotes, backslashes, `$` and fenced code | Adopted the shared stack: `RESPONSE_FORMAT_BLOCK` (prompt) → `parse_reviser_response` + `pick_expected_artifact` (parse) → `build_concern_responses` (change-log). A round-trip test feeds all four hazards through verbatim. Bonus: `parse_reviser_response`'s own failure message already contains `"parseable"`, so `is_malformed_reply_error` accepts it |
| 4 | **Correctness** — `max_tokens=32_768` is `REASONING_MAX_TOKENS`. Spec-023 defect #20 is precisely what that value does to a revision turn: the reasoning model's hidden CoT consumes the budget before the artifact block closes, so the reply truncates mid-document and parses as malformed (`_self_consistency.py:154-160`) | Defaults to `GENERATION_MAX_TOKENS` (131_072), as every other reviser's revision turn does. Pinned by an assertion in the single-call test |
| — | Step 0 re-verified against the live engine | (a) `engine.py:525` re-raises `BackendError` first, `:527` gives one retry for any `RuntimeError`; (b) `is_malformed_reply_error` keys on `"no usable"` / `"parseable"` and excludes `BackendError`. Both unchanged — the plan's contract holds |

## Round-14 (Task 6 implementation)

| # | Finding | Resolved by |
|-|-|-|
| 1 | **Blocker, Slice 1A** — the lane's MANDATORY audit sink could not write a real `snapshot_provenance`. `SnapshotProvenance.observed_at` is a `datetime`, and `_jsonable`'s branch hand-built its dict instead of recursing, so the datetime slipped past the function's own unknown-type guard and exploded later at `json.dumps` as a `TypeError` nothing normalizes into `RouteAuditError`. Both events carrying provenance (`ChainResolved`, `SelectionFailure`) were unwritable — and `SelectionFailure` is exactly what Task 6's degradation join reads | Fixed in `2c8daa7058`: every composite branch recurses, `datetime` projects to ISO-8601. Slice 1A's test had passed `observed_at=TS` (a **string**) into a dataclass with no runtime type check, asserting a shape production never produces; it now uses a real datetime and asserts the round-trip, plus a new `SelectionFailure` test |
| 2 | Two of the plan's fail-closed cases are UNREACHABLE at write time | `_validate_review_rerouted` (Task 1) recomputes both legs from the envelope `attempt_id`, so a foreign-attempt or borrowed-primary-leg reroute cannot be persisted. The reader's checks are kept as defense-in-depth at a trust boundary (the log is a file on a git ref), but the tests now construct their input through an explicit `_corrupt()` helper that documents this, and a new test asserts the WRITER refuses both. Silently `replace()`-ing a validated event would have implied the reader was the only guard |
| — | test construction hardened | Every audit event in the suite is built from the REAL slice-0 dataclass through the REAL `_audit_payload`, and every event is run through the REAL `validate_lane_event`. Hand-written payload dicts are what let finding 1 survive Slice 1A |

## Round-15 (Task 7 implementation)

| # | Finding | Resolved by |
|-|-|-|
| 1 | **Correctness** — the plan's code set `overflow_goal=PROPOSAL_KICKBACK_STAGE`, i.e. the string `"rejected"`. `overflow_goal` is NOT a stage: `engine._maybe_reduce` (`engine.py:431`) passes it straight to the SSoT summarizer as its `goal`, so an oversized proposal would be summarized with the instruction "rejected" — degrading the exact artifact the five lenses read. The plan's own Step 0(a) prose already prescribed the right thing ("the same short-phrase shape the research builder uses"); only the code block disagreed | `PROPOSAL_OVERFLOW_GOAL` = "preserve the causal claim, every cited evidence reference, and the file/test list verbatim" — the three things the lens set actually reads. A test asserts it is not the stage name |
| 2 | `_kickback_routing` maps EVERY `Severity` member, where the doc stages map only WRITING..FATAL | Deliberate and documented: `kickback.py:_nearest_routing` would resolve the gaps anyway, but a proposal is pre-claim work with nothing behind it, so there is no lesser outcome a writing-class concern could route to. Listing all seven makes "all severities are the same outcome here" read as the policy it is |
| — | prompt existence is enforced at CONSTRUCTION | `LLMReviewer.__init__` loads its prompt eagerly (`llm_reviewer.py:962`), so a missing `panel_si_proposal_<lens>.md` fails the builder rather than surfacing mid-Attempt. Verified by removing one prompt: 3 tests fail. The dedicated prompt test therefore checks CONTENT (the lens is addressed; the SSoT block got concatenated) rather than mere existence |
| — | **Open, not blocking** — the 5 new lens prompts have no promptfoo coverage | `eval/promptfoo/promptfooconfig.yaml` gates ONE prompt (`research_reviewer_idea_quality.md`), not a glob over `agents/prompts/**`, so nothing fails — but nothing checks these five either. Adding lane-panel eval cases needs real LLM calls and belongs with the first live proposal run, not Task 7 |

## Round-16 (Tasks 8-10 implementation — what the REAL panel found)

Task 9 is the F11 integration proof, and it earned its keep: driving the production path
end to end surfaced **three defects no unit test had reached**, two of them in Slice 1A
substrate that was already signed off.

| # | Finding | Resolved by |
|-|-|-|
| 1 | **Blocker, Slice 1A — duplicate `seq` under concurrency.** `append_to_log` derived the next `seq` from `read_log` (which does its OWN `_rev`) and the CAS parent from a SECOND `_rev`. A writer landing between the two left `seq` stale while `parent` was fresh, so `update-ref`'s compare-and-swap SUCCEEDED and two events durably shared a seq. The reader then rejected the whole stream as `corrupt sequence [.. 7, 7, 8]` — after the damage was committed. Surfaced immediately by the panel's 5-thread `ThreadPoolExecutor` | `_read_log_at(tip=...)` extracted from `read_log`; the append loop now reads the ref ONCE and derives both from that single observation. Regression test: 8 writers × 4 appends on one stream, asserting contiguous seqs — fails 3/3 against the old code |
| 2 | **Blocker, Slice 1A — the retry budget equalled the concurrency cap.** `max_retries=8` vs `engine._PANEL_MAX_CONCURRENCY=8`. Losing every race to every peer is a legal interleaving, not an anomaly, so a healthy 5-reviewer panel raised `GitLogContention` | `_DEFAULT_MAX_RETRIES = 32` (4x the cap) plus jittered backoff — without jitter the losers re-read and re-commit in lockstep and collide again. Same regression test covers it (fails 3/3 with the old bound + no jitter) |
| 3 | **Performance, Slice 1A — O(n²) appends.** `read_log` spawned one `git cat-file` PER EVENT, and every append does a full read. Measured: 245 ms/append at 30 events → 1206 ms at 120, i.e. per-append cost growing linearly with log size. A real Attempt (90-call ceiling, ~5 audit events per call) would have spent minutes of pure git overhead before a single model was called | One `git cat-file --batch` for the whole listing (binary I/O — `--batch` sizes are byte counts). 87s → 16s for 120 appends, and per-append cost is now FLAT (115→152 ms). Task 9's suite went 746s → 98s |
| 4 | **Honesty gap in the shared engine.** Its own comment says the `<missing>` guard covers "the reviser call failed" — but the failure path set `responses = []`, so `unaddressed` (`engine.py:627`) had nothing to key on and a lenient R3 could pass concerns nobody addressed. The comment described an intent the code did not implement | The degrade path now pads via the SSoT `build_concern_responses([], open_concerns)`, so the existing deterministic guard covers the failure it always claimed to |
| 5 | Plan errors corrected against the real APIs | `ConvergenceResult` has **no `artifacts` field** — Task 5's engine-driven tests asserted `result.artifacts[...]`; rewritten against `response_history`, which is what the engine actually returns. `AttemptCreditLedger` requires `call_ceiling` (both ledgers bind the SAME immutable pair) — the Task 9 fixture omitted it. Task 10's `_paid_only_snapshot` needed the DAILY cap raised far above the Attempt budget, or it is ambiguous which of the two ledgers refused a candidate |
| 6 | Task 10 could not reach the Attempt authority at all | Two ledgers gate a paid dispatch. 026's daily ledger fails closed first (`ledger_config_from_env` raises unless the anchor is pinned), so every paid candidate was SKIPPED before the Attempt authority was consulted and the test proved nothing. Now a REAL local-only production ledger in the temp repo (`LLMXIVE_REPO_ROOT` redirected so it cannot write into the developer's checkout) |
| — | `_REVIEW_STAGES` and the proposal gate | `self_improvement_proposal` is not in the engine's strict set, so writing-ONLY residue advances after the cap. The Task-7 prompts route anything substantive to `requirement`+, so this covers genuinely cosmetic residue — but it is now pinned by an EXPLICIT test rather than left to a fixture's severity choice. **Flagged for maintainer review**: if the lane's gate should hold the strict `research_review` bar, that is a one-line change |
| — | pre-existing ruff errors in `engine.py` | Fixed while touching the file: targeted `# noqa: RUF001/RUF003` on the four non-breaking-hyphen sites, which are DELIBERATE (the regexes must match what LLMs actually emit — changing the character would break them) |

## Round-17 review (Slice 1B, post-implementation) — 3 correctness + 2 provenance

| # | Finding | Resolved by |
|-|-|-|
| 1 | **Blocker — unresolved writing concerns were treated as proposal ACCEPTANCE.** `self_improvement_proposal` was absent from the engine's hard-coded `_REVIEW_STAGES`, so the doc-authoring allowance advanced it on writing-only residue. That contradicts spec 025 (unanimous acceptance; a panel that does not accept must not reach `claimed`) AND Task 7's own routing, which sends every unresolved severity — writing included — to `rejected`. The prior test codified the violation | Migrated the strict bar from the hard-coded stage-name SET to a `ReviewSpec.strict_acceptance` field (the reviewer's preferred shape), set on `research_review`, `paper_review`, and the proposal gate; `_REVIEW_STAGES` deleted, so there is ONE mechanism. The test now asserts writing residue does NOT converge and routes to `rejected`. A registry guard pins the partition in BOTH directions — losing a strict stage, or accidentally making an authoring stage strict (which would re-introduce spec-023 defect #24) |
| 2 | **High — the independence baseline was not bound to the durable proposer identity.** `proposer_baseline` (family exclusion) and `proposer_route_id` (the real author) described the same fact with nothing forcing agreement. A caller could resolve a gemma author while passing a qwen baseline; a gemma reviewer then satisfies selection while being the author's OWN family. FR-002 defeated, with every individual record still true | The durable identity now DERIVES the baseline (`_baseline_for`): the author's family is added, extra caller families are preserved, and a supplied baseline that OMITS the author's family raises `ProposerBaselineMismatch` rather than being silently overridden — a caller believing something different about authorship has a bug worth surfacing. Proven by an EMPTY supplied baseline still yielding the author's family |
| 3 | **High — Task 10's paid concurrency proof did not actually reach the Attempt authority.** Reproduced exactly: `authority.threads == set()`. The paid path makes TWO live balance reads (`execute.py:179`, `:192`) BEFORE consulting `reservation_authority`, and both fail closed. The test passed locally ONLY because that machine holds Dartmouth credentials — so it was making live network calls — and failed everywhere else while appearing green | A controlled balance injected through `balance_fetch`'s documented seam (`credits.fetch_credit_balance`), with the daily headroom far above the Attempt budget so the Attempt cap is unambiguously the binding constraint. Everything else stays REAL. Verified with the live fetch forcibly broken. Now genuinely: 5 distinct threads, 2 paid dispatches completed, 9 reservations refused by the cap, counting_total 1052.3 ≤ budget 1056.2. A new assertion fails the test if the balance seam is ever bypassed |
| 4 | **Medium — `InvocationIdentity` trusted the completed candidate without checking it came from the resolved chain.** A malformed stream could attribute execution to a model selection never chose — and that `family` is the security-relevant independence provenance FR-002 is judged on, which finding 2 now derives a whole review's exclusion from | `_completed_candidate_from_chain` requires the index in range AND a field-for-field ModelRef match against `ChainResolved.candidates[index]`. Corruption tests for out-of-range, wrong-candidate-at-valid-index, and a bool index (`True == 1` would otherwise index the chain) |
| 5 | **Medium — clean-abort provenance was claimed but not wired.** The docstring said aborts are "already recorded via `on_abort`"; no `on_abort` is passed | Claim CORRECTED and the gap explicitly assigned. States precisely what IS durable (per-route `ChainResolved`/`SelectionFailure`/`CandidateOutcome` + the `LaneCallClaimed` ceiling charge) and what is NOT (an Attempt-level abort record), and assigns the latter to the lifecycle-owning slice, which alone has the terminal-state vocabulary and the authority to move it. A test pins both halves so the corrected claim cannot rot |
