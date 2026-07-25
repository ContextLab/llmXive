# Self-Improvement Lane — Slice 1A: Durable Substrate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the self-improvement lane's durable persistence substrate — a **genuine git-ref compare-and-swap event log** (extracted as a shared primitive from the 026 credit ledger), the singleton `LaneCoordinator` with real ownership-checked claim/release transitions, the `AttemptCreditLedger` (the slice-0 `ReservationAuthority`), and the event-sourced `RouteAudit` sink whose dispatch claim is a cross-process CAS — so later slices persist and enforce on a correct foundation.

**Architecture:** Almost all of `model_selection/ledger_transport.py` is domain-agnostic git-CAS plumbing (a zero-internal-import leaf). Task 1 extracts that into `src/llmxive/git_event_log.py` — a ref-parameterized append-only CAS core — and rewires the credit ledger as a thin wrapper (its behavior stays byte-for-byte, gated by its own tests). The lane then builds every projection (`LaneCoordinator`, `AttemptCreditLedger`, audit stream) on that same core, on a dedicated lane ref, with an **authoritative per-stream sequence** the core assigns inside the CAS (so ordering never depends on wall-clock timestamps). The credit-ledger's proven CAS gives the lane real cross-process serialization, durable-on-commit semantics, and idempotent retries for free.

**Tech Stack:** Python ≥ 3.11; `pytest`; git plumbing via `subprocess` (the credit-ledger pattern); package roots `llmxive.git_event_log` and `llmxive.self_improvement`. No new third-party deps.

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from spec 025 rev 14 and the slice-0 contracts.

- **The money-path stays byte-for-byte green (Task 1 acceptance bar).** The extraction MUST NOT change any git-observable artifact of the credit ledger (blob content, tree shape, commit message, ref name, validation, CAS/retry structure). These test files MUST pass **without any edits**, both before (baseline) and after Task 1: `tests/integration/test_credit_ledger_transport.py`, `tests/integration/test_credit_reservations.py`, `tests/integration/test_model_selection_execute.py`, `tests/unit/test_ledger_config_from_env.py`, `tests/unit/test_model_selection_attempt_hooks.py`, `tests/unit/test_model_selection_inventory.py`, `tests/unit/test_paid_credits.py`.
- **Real git-ref CAS, no `-X theirs` (FR-008).** Every claim/mutation reads the authoritative tip, rebuilds the projection, verifies its revision precondition, and advances the ref by fast-forward (`update-ref` CAS locally / FF-push remote); a non-fast-forward refetches and recomputes. Conflicts are NEVER resolved by a whole-tree merge. Two processes on separate clones competing for one ref: exactly one wins.
- **Authoritative ordering, never timestamps (fixes the ordering bug).** Lane projections order events by the core-assigned monotonic `seq`, established inside the successful CAS at the verified parent — NOT by `(timestamp, event_id)`. Projections validate `seq` continuity: it starts at 0, increments by exactly 1, has no gaps or forks; an out-of-order or duplicate `seq` is a fail-closed corruption.
- **Deterministic idempotency (FR-009).** Each side-effecting operation derives a **deterministic `event_id`** from its semantics (never the revision). A retried or re-invoked identical operation re-derives the same `event_id`; the core returns idempotently (comparing the semantic payload, excluding `seq`, `timestamp`, and the revision anchors), never a duplicate and never a spurious append-only raise.
- **Ownership-checked coordinator transitions (FR-008).** A claim requires `active_problem_id is None` (idle) at the CAS. A release requires the current `active_problem_id`/`active_attempt_id` to EQUAL the releasing pair (a stale delayed release MUST NOT clear a newer claim); an already-idle coordinator is an idempotent success only when durable history proves this exact release already landed.
- **Event fields (FR-011).** Every event carries `event_id`, `event_type`, `problem_id` (or the coordinator-stream sentinel), optional `attempt_id`, the applicable `expected_lane_revision`/`expected_problem_revision` + `resulting_*_revision` (the store stamps `expected_*_revision == seq` and `resulting_*_revision == seq + 1` inside the CAS), `timestamp`, `actor`, `payload`, `schema_version`, and `seq`. Validation enforces: known `event_type`; exactly one revision scope (coordinator XOR problem); a `schema_version` the reader supports; the on-disk path stream matches the serialized stream; a legal state transition. An unknown `event_type` is rejected on read (it must not silently advance a safety-critical projection).
- **AttemptCreditLedger states are exactly `{open, retained, reconciled, released}` (FR-033).** A reservation record is `{reservation_id, call_id, reserved_credits, state}` — the reserved worst-case envelope, **no exact-actual-cost field** (F3). Counting states (against the cap) = `{open, retained, reconciled}`; `released` (never dispatched) does not count. Saga rollbacks per FR-033(b): over-budget → refuse (skip); Attempt reserved but 026 refuses → `release`; both reserved but dispatch fails → both `retained`; a candidate that never dispatched → `released`, one that dispatched → `retained`.
- **ReservationAuthority collision semantics (slice-0 `attempt_hooks.ReservationAuthority.reserve`).** Repeated `reservation_id` + same `(credits, call_id)` → idempotent success, no double-count; same id + different identity → integrity raise; concurrent duplicates → exactly one durable reservation; an ordinary budget denial returns `False` (never raises).
- **RouteAudit is durable-on-commit and the claim is a real CAS (slice-0 `attempt_hooks.RouteAudit`; F8).** `record`/`claim_dispatch` return only AFTER the ref-CAS commit lands — a local file that never reached the ref is NOT durable evidence. `claim_dispatch(DispatchStarted) -> bool`: `True` = this call committed the event (own the dispatch); `False` = a byte-identical event already committed (replay, MUST NOT re-dispatch); a conflicting payload under the same `event_id` → raise. Exactly one claimant wins across processes (the ref-CAS).
- **DispatchUnknown reconciliation is conservative + atomic (FR-033a; F4, F5, F7).** A dispatch is "dangling" only if ALL hold: the event is in THIS attempt's stream; there is no `DispatchCompleted`; there is no terminal `CandidateOutcome` (`advance`/`abort`/`skip`) for it; there is no existing `DispatchUnknown`; and it is older than a **conservative timeout** bounded by the real call envelope (`deadline_s × (retries + 1)` + margin) — this is honestly a timeout, NOT durable proof the owner is dead (F5); durable owner-liveness would need an owner/lease field on the slice-0 `DispatchStarted` (a protected-surface change, deferred). Reconciling appends ONE `DispatchUnknown` event that **atomically** drives BOTH the audit resolution AND the matching reservation's `open → retained` (via `project_reservations`) — no two-write crash window (F4). Slice 1A records this durable unknown+retained state; the Attempt-fail-closed lifecycle transition is Slice 1B (the contract is not "fails the Attempt closed yet").
- **Route through the chokepoint; no model-id literals in lane code (SC-008, FR-001).** `model_selection/enforcement.py` verifies this. (Slice 1A adds no model ids.)
- **Real tests, no mocks (Constitution III).** Protocol test doubles with real logic, temp-git-repo fixtures, and **multi-clone concurrency tests** (two clones of one bare remote competing on the ref) are required where the guarantee is cross-process. `unittest.mock` is not the primary path.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push.**

## Scope boundary

This plan is **Slice 1A: the durable substrate only.** The proposal-review convergence wiring (threading `route_audit`/`reservation_authority` through the reviewer + reviser, the explicit reroute/degradation event, the complete `InvocationIdentity`, the `self_improvement_proposal` `ReviewSpec` + prompts, the real `run_convergence` integration test) is **Slice 1B**, a separate plan that consumes this substrate's `EventStoreRouteAudit` + `AttemptCreditLedger` interfaces. US1's discovery *logic* (error mining, issue ranking, proposer + deterministic pre-gates) is a further follow-up.

## File Structure

- `src/llmxive/git_event_log.py` — the extracted ref-agnostic git-CAS core: `LogRef`, `AppendResult`, `append_to_log`, `read_log`, `sync_and_verify`, `bootstrap_log`, `GitLogError`/`GitLogAuthError`/`GitLogContention`, and the moved git-plumbing helpers.
- `src/llmxive/model_selection/ledger_transport.py` — **rewired** to thin wrappers over the core (behavior unchanged); keeps the credit schema (`_validate_event`, the constants), `LedgerConfig`, `ledger_config_from_env`, `bootstrap_ledger`, `LedgerError`/… (subclassing the core's).
- `src/llmxive/self_improvement/events.py` — lane `Event` record (FR-011) + `validate_lane_event` + `derive_event_id` + JSON (de)serialization.
- `src/llmxive/self_improvement/lane_log.py` — the lane's store on the dedicated ref: `LANE_REF`, `LaneLogConfig(remote, expected_anchor)`, `bootstrap_lane_log`, `append`/`read` (config-threaded, seq-ordered), `LaneRevisionConflict`; thin wrappers over the shared `git_event_log` core.
- `src/llmxive/self_improvement/coordinator.py` — `LaneCoordinator` projection + `project_coordinator` + `cas_claim`/`cas_release` (ownership-checked).
- `src/llmxive/self_improvement/credit_ledger.py` — `AttemptCreditLedger` (`ReservationAuthority`) + projection + `reconcile`.
- `src/llmxive/self_improvement/audit_sink.py` — `EventStoreRouteAudit` (`RouteAudit`) + `reconcile_unknown`.
- `src/llmxive/self_improvement/__init__.py` — public exports.

---

### Task 1: Extract the ref-agnostic git-CAS core `git_event_log.py`

**Files:**
- Create: `src/llmxive/git_event_log.py`
- Modify: `src/llmxive/model_selection/ledger_transport.py` (rewire to thin wrappers)
- Test: `tests/integration/test_git_event_log.py` (new — the core's own behavior, incl. `seq`/`created`/`identity_exclude`)
- Gate (no edits): the seven money-path test files listed in Global Constraints.

**Interfaces:**
- Produces (in `git_event_log.py`):
  - `@dataclass(frozen=True) class LogRef`: `ref: str`, `event_dir: str`, `remote: str | None = None`, `expected_anchor: str | None = None`, `git_identity: Mapping[str, str] = <default>`. (Generalizes `LedgerConfig` with `ref` + `event_dir` — the two values `ledger_transport` held as module globals.)
  - `@dataclass(frozen=True) class AppendResult`: `commit: str`, `seq: int`, `created: bool` (`True` = this call committed the event; `False` = idempotent no-op / already present).
  - `append_to_log(repo, *, log: LogRef, validate: Callable[[dict], None], message_fn: Callable[[dict], str], event: dict | None = None, prepare: Callable[[list[dict]], dict | None] | None = None, predicate: Callable[[list[dict]], tuple[bool, str]] | None = None, now_field: str | None = None, finalize: Callable[[dict, int], dict] | None = None, identity_exclude: frozenset[str] = frozenset(), _after_parent: Callable[[], None] | None = None, max_retries: int = 8) -> AppendResult` — the current `append_event` seven-step CAS loop, ref-parameterized. `_after_parent` is a **TEST-ONLY seam (F6)**: if set, the core calls it AFTER `parent`/`seq` are fixed and BEFORE `_append_commit` + the ref-CAS, so two workers can block on a shared barrier there (guaranteeing they built from the SAME parent) and then race the actual `update-ref`/FF-push — deterministically exercising the non-fast-forward retry path. It defaults `None` (no-op) and is never used in production. New, all applied INSIDE each CAS attempt after `parent = _rev(...)` is fixed (so a retry recomputes from the true new tip):
    1. `seq = len(read_log(...))` at that parent (returned in `AppendResult.seq`).
    2. `if now_field: built.setdefault(now_field, <iso now>)` — the credit wrapper passes `now_field="ts"` to keep its timestamp stamping byte-for-byte; the lane passes `None` and supplies its own FR-011 `timestamp`.
    3. `if finalize: built = finalize(built, seq)` — the LANE stamps `seq` + the FR-011 `expected_*_revision = seq` and `resulting_*_revision = seq + 1` into the body here (the credit wrapper passes `finalize=None`, so its body is unchanged).
    4. `validate(built)`; then the **append-only guard compares canonical bodies with the `identity_exclude` fields removed from BOTH the built and the committed event**, so a semantic retry that differs ONLY in `identity_exclude` fields (the lane's `seq`/`timestamp`/revision anchors) returns idempotently (`created=False`, `seq` = the committed event's `seq`); a genuinely different semantic body raises `GitLogError`.

    When `now_field=None`, `finalize=None`, and `identity_exclude=frozenset()`, none of steps 1-4 change anything and the guard compares the full body — **byte-for-byte as the credit ledger today** (the credit wrapper instead passes `now_field="ts"`, which reproduces exactly the old `built.setdefault("ts", ...)`). The core NEVER hard-codes a `"ts"`/`"timestamp"` field name (F2).
  - `read_log(repo, *, log: LogRef, validate: Callable[[dict], None]) -> list[dict]` — the current `read_events` loop, `event_dir`/`validate` parameterized.
  - `sync_and_verify(repo, *, log: LogRef) -> None`, `bootstrap_log(repo, *, log: LogRef, message: str, remote: str | None = None) -> str` — ref-parameterized `_sync_and_verify`/`bootstrap_ledger`.
  - `class GitLogError(RuntimeError)`, `class GitLogAuthError(GitLogError)`, `class GitLogContention(GitLogError)`, `class GitLogDenied(GitLogError)` (raised when a `predicate` returns `(False, reason)` — the generalization of the credit ledger's `LedgerDenied`); moved helpers `_git`, `_rev`, `_canonical`, `_read_event_blob`, `_append_commit`, `_fetch_authoritative`, `_remote_ledger_oid`, `_is_ancestor`, `_push_fast_forward`, `sync_and_verify`, and the marker/id constants (`_AUTH_FAIL_MARKERS`, `_NON_FF_MARKERS`, `_PUSH_DENY_MARKERS`, `_ZERO_OID`, `_SAFE_ID`, `_DEFAULT_GIT_IDENTITY`) — each gaining a `ref`/`event_dir`/`message_fn` parameter in place of the module global it closed over. See the extraction blueprint (`.superpowers`/scratch `extraction-design.md`) for the exact verbatim bodies and the generic/credit-specific split.
- `ledger_transport.py` keeps `LEDGER_REF`, `SCHEMA_REVISION`, `_EVENT_DIR`, `_validate_event` + its four schema constants, `LedgerConfig`, `ledger_config_from_env`, `bootstrap_ledger`, `fetch_ledger`. **`LedgerError`/`LedgerAuthError`/`LedgerContention` are ALIASES of the core's `GitLogError`/`GitLogAuthError`/`GitLogContention` (`LedgerError = GitLogError`, `LedgerAuthError = GitLogAuthError`, `LedgerContention = GitLogContention`) — NOT subclasses (F8).** The core raises the base classes, so every existing `except LedgerError/LedgerAuthError/LedgerContention` site must still catch them; only aliasing guarantees this (a subclass would fail to catch a base-class instance raised by the core, silently changing money-path failure handling). `LedgerDenied = GitLogDenied` is also an ALIAS (F8): the core raises `GitLogDenied` when a `predicate` returns `(False, reason)`, and existing `except LedgerDenied` sites must catch it. `append_event`/`read_events` become thin wrappers passing `LEDGER_REF`/`_EVENT_DIR`/`_validate_event`/`_message_fn`, `now_field="ts"`, `finalize=None`, `identity_exclude=frozenset()`, and returning `AppendResult.commit`.

- [ ] **Step 1: Baseline the money-path tests (they must already be green).**

Run: `pytest tests/integration/test_credit_ledger_transport.py tests/integration/test_credit_reservations.py tests/unit/test_ledger_config_from_env.py -q`
Expected: PASS. Record the counts — these must be identical after the refactor.

- [ ] **Step 2: Write the new core's failing test** (the behavior the credit path does NOT exercise — `seq`, `created`, `identity_exclude`):

```python
# tests/integration/test_git_event_log.py
import subprocess

import pytest

from llmxive.git_event_log import GitLogError, LogRef, append_to_log, read_log

def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path

LOG = LogRef(ref="refs/llmxive/test-log", event_dir="test/v1")
_NOVALIDATE = lambda e: None
_MSG = lambda e: f"test {e['event_id']}"

def _append(repo, event):
    return append_to_log(repo, log=LOG, validate=_NOVALIDATE, message_fn=_MSG, event=dict(event),
                         now_field="ts", finalize=lambda ev, seq: {**ev, "seq": seq},
                         identity_exclude=frozenset({"seq", "ts"}))

def test_seq_is_authoritative_and_monotonic(repo):
    r0 = _append(repo, {"event_id": "a", "payload": 1})
    r1 = _append(repo, {"event_id": "b", "payload": 2})
    assert (r0.seq, r0.created) == (0, True)
    assert (r1.seq, r1.created) == (1, True)
    events = read_log(repo, log=LOG, validate=_NOVALIDATE)
    assert [e["seq"] for e in events] == [0, 1]  # stored, authoritative

def test_semantic_retry_is_idempotent_despite_different_ts(repo):
    r0 = _append(repo, {"event_id": "a", "payload": 1, "ts": "2026-07-24T00:00:00+00:00"})
    r1 = _append(repo, {"event_id": "a", "payload": 1, "ts": "2026-07-24T09:99:99+00:00"})  # ts differs
    assert r0.created is True and r1.created is False       # idempotent no-op
    assert r1.seq == r0.seq == 0                            # returns the committed seq
    assert len(read_log(repo, log=LOG, validate=_NOVALIDATE)) == 1

def test_conflicting_semantic_body_still_raises(repo):
    _append(repo, {"event_id": "a", "payload": 1})
    with pytest.raises(GitLogError, match="append-only"):
        _append(repo, {"event_id": "a", "payload": 999})   # same id, different semantic payload
```

- [ ] **Step 3: Extract + rewire.**

Perform the mechanical move per the blueprint: create `git_event_log.py` with the generic helpers + the new features (`AppendResult{commit,seq,created}`, `now_field`, `finalize`, `identity_exclude`), and rewire `ledger_transport.append_event`/`read_events` as thin wrappers. The credit wrapper (`now_field="ts"`, `finalize=None`, `identity_exclude=frozenset()`, returns `.commit`) must produce byte-identical git artifacts. Key wrapper shape (from the blueprint):

```python
# ledger_transport.py (rewired)
from llmxive.git_event_log import (
    AppendResult, GitLogAuthError, GitLogContention, GitLogDenied, GitLogError, LogRef,
    append_to_log, read_log,
)

# F8: ALL FOUR are ALIASES, not subclasses — the core raises the base classes, and every
# existing `except LedgerError/LedgerAuthError/LedgerContention/LedgerDenied` site must
# still catch them (a subclass would NOT catch a base-class instance the core raised).
LedgerError = GitLogError
LedgerAuthError = GitLogAuthError
LedgerContention = GitLogContention
LedgerDenied = GitLogDenied  # the credit pricing-predicate rejection; core raises it on predicate False

def _message_fn(event: dict) -> str:
    return f"ledger: {event.get('type', '?')} {event.get('reservation_id', '?')} {event['event_id']}"

def _log_ref(config: "LedgerConfig", ref: str = LEDGER_REF) -> LogRef:
    return LogRef(ref=ref, event_dir=_EVENT_DIR, remote=config.remote,
                  expected_anchor=config.expected_anchor, git_identity=_GIT_IDENTITY)

def read_events(repo: Path, *, ref: str = LEDGER_REF) -> list[dict]:
    return read_log(repo, log=LogRef(ref=ref, event_dir=_EVENT_DIR, git_identity=_GIT_IDENTITY),
                    validate=_validate_event)

def append_event(repo, event=None, *, prepare=None, config=None, predicate=None, max_retries=8) -> str:
    config = config or LedgerConfig()
    return append_to_log(repo, log=_log_ref(config), validate=_validate_event, message_fn=_message_fn,
                         event=event, prepare=prepare, predicate=predicate, now_field="ts",
                         max_retries=max_retries).commit  # now_field="ts" == the old built.setdefault("ts",…)
```

Add an exception-compat test to `tests/integration/test_git_event_log.py` (F8): force the core to raise `GitLogContention`/`GitLogAuthError` (e.g. a contention beyond `max_retries`, or an unbootstrapped remote) and assert `except LedgerContention`/`except LedgerAuthError`/`except LedgerError` (the `ledger_transport` names) each catch it.

- [ ] **Step 4: Run the new core tests AND re-run the full money-path gate (no edits).**

Run: `pytest tests/integration/test_git_event_log.py -q` → PASS (3 passed).
Run: `pytest tests/integration/test_credit_ledger_transport.py tests/integration/test_credit_reservations.py tests/integration/test_model_selection_execute.py tests/unit/test_ledger_config_from_env.py tests/unit/test_model_selection_attempt_hooks.py tests/unit/test_model_selection_inventory.py tests/unit/test_paid_credits.py -q`
Expected: PASS with the SAME counts as Step 1's baseline. **If any money-path test needed an edit, the extraction changed behavior — revert and redo; never edit these tests.**

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/git_event_log.py src/llmxive/model_selection/ledger_transport.py tests/integration/test_git_event_log.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "refactor(025 slice-1A T1): extract ref-agnostic git_event_log CAS core (credit ledger byte-for-byte)"
```

---

### Task 2: Lane `Event` record + validation + deterministic idempotency key

**Files:**
- Create: `src/llmxive/self_improvement/__init__.py`, `src/llmxive/self_improvement/events.py`
- Test: `tests/unit/test_self_improvement_events.py`

**Interfaces:**
- Produces:
  - `COORDINATOR_STREAM = "coordinator"`, `SCHEMA_VERSION = 1`, `SEQ_FIELD = "seq"`.
  - `KNOWN_EVENT_TYPES_V1: frozenset[str]` — the **Slice-1A (schema v1)** event-type vocabulary (coordinator: `ClaimAcquired`, `ClaimReleased`, `MonitorStarted`, `PromotionEnabledSet`; credit: `AttemptCreditReserved`/`Released`/`Retained`/`Reconciled`; audit: `ChainResolved`, `SelectionFailure`, `ReservationOpened`, `DispatchStarted`, `DispatchCompleted`, `DispatchUnknown`, `CandidateOutcome`; lifecycle: `ProblemDiscovered`, `Proposed`, `ProposalVerified`, `Rejected`). It is NOT the full spec-025 set (F9); a type outside it is rejected on read, so any later slice adding a type MUST bump `SCHEMA_VERSION` and extend this set + the projection handlers together.
  - `@dataclass(frozen=True) class Event` (FR-011): `event_id`, `event_type`, `stream` (a `problem_id` or `COORDINATOR_STREAM`), `actor`, `payload: Mapping`, `timestamp`, `schema_version=SCHEMA_VERSION`, `attempt_id: str | None = None`, and the four CAS anchors `expected_lane_revision`/`resulting_lane_revision`/`expected_problem_revision`/`resulting_problem_revision: int | None = None` plus `seq: int | None = None`. The store stamps all of them inside the CAS from the authoritative parent so that `seq == expected_*_revision` and `resulting_*_revision == seq + 1` (event seq=N transforms revision N → N+1); exactly one scope (lane XOR problem) is populated, matching the stream. `None` before append.
  - `derive_event_id(stream, idempotency_key) -> str` — `sha256(f"{stream}\x00{idempotency_key}")`.
  - `validate_lane_event(raw: dict) -> None` — fail-closed one-event schema (F9): required fields present; `event_type ∈ KNOWN_EVENT_TYPES_V1`; `schema_version == SCHEMA_VERSION`; the stream's revision scope (lane for coordinator, problem otherwise) has BOTH `expected_` and `resulting_` set, the OTHER scope has neither, and `expected == seq` and `resulting == seq + 1`; `event_id` is a safe path segment; `timestamp` parses ISO-8601. Raises `ValueError`. (Cross-event LEGAL TRANSITIONS are enforced by the projections — Tasks 4/6 — not here.)
  - `event_to_json(event) -> str` (canonical, sorted keys, compact), `event_from_json(text) -> Event`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_events.py
import pytest

from llmxive.self_improvement.events import (
    COORDINATOR_STREAM, SCHEMA_VERSION, Event, derive_event_id, event_from_json, event_to_json,
    validate_lane_event,
)

def _raw(**kw):
    # a valid problem-stream event at revision 0 (seq=0, expected=0, resulting=1)
    base = {"event_id": "e1", "event_type": "ProblemDiscovered", "problem_id": "prob-1", "actor": "disc",
            "payload": {}, "timestamp": "2026-07-24T00:00:00+00:00", "schema_version": SCHEMA_VERSION,
            "attempt_id": None, "expected_problem_revision": 0, "resulting_problem_revision": 1, "seq": 0}
    base.update(kw)
    return base

def test_valid_event_passes():
    validate_lane_event(_raw())  # no raise

def test_event_id_deterministic_and_scoped():
    a = derive_event_id("prob-1", "discover")
    assert a == derive_event_id("prob-1", "discover") != derive_event_id("prob-2", "discover")

def test_round_trip_carries_all_revision_anchors():
    e = event_from_json(event_to_json(Event(**_raw())))
    assert e.seq == 0 and e.expected_problem_revision == 0 and e.resulting_problem_revision == 1

def test_validate_rejects_unknown_type():
    with pytest.raises(ValueError, match="event_type"):
        validate_lane_event(_raw(event_type="TotallyMadeUp"))

def test_validate_rejects_both_revision_scopes():
    with pytest.raises(ValueError, match="must NOT set"):
        validate_lane_event(_raw(expected_lane_revision=0, resulting_lane_revision=1))  # + the problem scope

def test_validate_rejects_wrong_scope_for_coordinator():
    # a coordinator event must carry the LANE revision scope, not the problem scope
    with pytest.raises(ValueError, match="lane-stream event must set"):
        validate_lane_event(_raw(problem_id=COORDINATOR_STREAM))  # base has problem-scope revisions → wrong

def test_validate_accepts_a_supported_prior_schema_version_note():
    # F7: SUPPORTED_SCHEMA_VERSIONS (not `== SCHEMA_VERSION`) is what makes append-only
    # history readable across future bumps; today it is frozenset({1}).
    from llmxive.self_improvement.events import SUPPORTED_SCHEMA_VERSIONS
    assert SCHEMA_VERSION in SUPPORTED_SCHEMA_VERSIONS

def test_validate_rejects_off_by_one_resulting_revision():
    with pytest.raises(ValueError, match="resulting==seq"):
        validate_lane_event(_raw(resulting_problem_revision=5))  # must be seq+1 == 1

def test_validate_rejects_bad_schema_version():
    with pytest.raises(ValueError, match="schema_version"):
        validate_lane_event(_raw(schema_version=999))
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/unit/test_self_improvement_events.py -q` → FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/__init__.py
"""The autonomous self-improvement lane (spec 025). Slice 1A: durable substrate."""
```

```python
# src/llmxive/self_improvement/events.py
"""The lane's append-only event record (FR-011) + fail-closed validation (F9) + its
deterministic idempotency key (FR-009). Ordering is by the store-assigned ``seq``
(never timestamps); ``validate_lane_event`` rejects any event that could corrupt a
projection."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

COORDINATOR_STREAM = "coordinator"
SCHEMA_VERSION = 1  # the version NEW events are written with
#: Versions a reader accepts (F7): append-only history means older events of a PRIOR
#: version stay readable forever, so a reader NEVER rejects on `!= SCHEMA_VERSION`. Adding
#: an event TYPE (same record shape) extends `KNOWN_EVENT_TYPES_V1` WITHOUT a version bump;
#: only a change to the record SHAPE bumps `SCHEMA_VERSION` and adds the new version here
#: with its own validator/projection support (so v1 events keep validating under their rules).
SUPPORTED_SCHEMA_VERSIONS = frozenset({1})
SEQ_FIELD = "seq"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")

# The event vocabulary THIS schema version understands (F9). It is deliberately the
# Slice-1A subset — NOT the full spec-025 transition set. A fail-closed reader rejects
# any type outside it, so EVERY later slice that introduces a new event type (e.g.
# Slice 1B's reroute/degradation event, or the implementation/promotion lifecycle) MUST
# bump SCHEMA_VERSION and extend BOTH this set AND the projection handlers together.
KNOWN_EVENT_TYPES_V1 = frozenset({
    "ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet",
    "AttemptCreditReserved", "AttemptCreditReleased", "AttemptCreditRetained", "AttemptCreditReconciled",
    "ChainResolved", "SelectionFailure", "ReservationOpened", "DispatchStarted",
    "DispatchCompleted", "DispatchUnknown", "CandidateOutcome",
    "ProblemDiscovered", "Proposed", "ProposalVerified", "Rejected",
})

@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    problem_id: str  # FR-011: a problem_id, or COORDINATOR_STREAM for coordinator events
    actor: str
    payload: Mapping[str, Any]
    timestamp: str
    schema_version: int = SCHEMA_VERSION
    attempt_id: str | None = None
    # CAS anchors (FR-011). All three are stamped by the store INSIDE the successful
    # CAS from the authoritative parent: seq == expected_*_revision, and
    # resulting_*_revision == seq + 1 (event seq=N transforms revision N → N+1).
    # Exactly one revision SCOPE is populated (coordinator → *_lane_revision; per-Problem
    # → *_problem_revision), matching the stream. `None` before the append assigns them.
    expected_lane_revision: int | None = None
    resulting_lane_revision: int | None = None
    expected_problem_revision: int | None = None
    resulting_problem_revision: int | None = None
    seq: int | None = None

def derive_event_id(stream: str, idempotency_key: str) -> str:
    return hashlib.sha256(f"{stream}\x00{idempotency_key}".encode()).hexdigest()

def _as_dict(e: Event) -> dict[str, Any]:
    return {"event_id": e.event_id, "event_type": e.event_type, "problem_id": e.problem_id, "actor": e.actor,
            "payload": dict(e.payload), "timestamp": e.timestamp, "schema_version": e.schema_version,
            "attempt_id": e.attempt_id, "expected_lane_revision": e.expected_lane_revision,
            "resulting_lane_revision": e.resulting_lane_revision,
            "expected_problem_revision": e.expected_problem_revision,
            "resulting_problem_revision": e.resulting_problem_revision, "seq": e.seq}

def validate_lane_event(raw: dict) -> None:
    """Fail-closed schema validation, run at the write boundary (after the store stamps
    seq + the revision fields) AND on every read. Rejects any event that could corrupt a
    projection (F9). Note: this validates ONE event's shape; LEGAL STATE TRANSITIONS
    across events are enforced by the projections (they are the recovery authority) —
    see project_coordinator / project_reservations."""
    for key in ("event_id", "event_type", "problem_id", "actor", "payload", "timestamp", "schema_version"):
        if key not in raw:
            raise ValueError(f"lane event missing required field {key!r}")
    if raw["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:  # F7: never reject prior-version history
        raise ValueError(f"lane event schema_version {raw['schema_version']!r} not in {SUPPORTED_SCHEMA_VERSIONS}")
    if raw["event_type"] not in KNOWN_EVENT_TYPES_V1:
        raise ValueError(f"lane event_type {raw['event_type']!r} not in KNOWN_EVENT_TYPES_V1")
    if not _SAFE_ID.match(str(raw["event_id"])):
        raise ValueError(f"lane event_id {raw['event_id']!r} must match {_SAFE_ID.pattern}")
    is_coord = raw["problem_id"] == COORDINATOR_STREAM
    scope = "lane" if is_coord else "problem"
    other = "problem" if is_coord else "lane"
    exp, res = raw.get(f"expected_{scope}_revision"), raw.get(f"resulting_{scope}_revision")
    if exp is None or res is None:
        raise ValueError(f"{scope}-stream event must set expected_/resulting_{scope}_revision")
    if raw.get(f"expected_{other}_revision") is not None or raw.get(f"resulting_{other}_revision") is not None:
        raise ValueError(f"{scope}-stream event must NOT set the {other} revision scope")
    seq = raw.get("seq")
    if seq is None or exp != seq or res != seq + 1:
        raise ValueError(f"revision anchors inconsistent: seq={seq}, expected={exp}, resulting={res} "
                         "(require expected==seq and resulting==seq+1)")
    try:
        datetime.fromisoformat(str(raw["timestamp"]))
    except ValueError as exc:
        raise ValueError(f"lane event timestamp {raw['timestamp']!r} is not ISO-8601") from exc

def event_to_json(event: Event) -> str:
    return json.dumps(_as_dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def event_from_json(text: str) -> Event:
    d = json.loads(text)
    return Event(event_id=d["event_id"], event_type=d["event_type"], problem_id=d["problem_id"], actor=d["actor"],
                 payload=d["payload"], timestamp=d["timestamp"], schema_version=d["schema_version"],
                 attempt_id=d.get("attempt_id"), expected_lane_revision=d.get("expected_lane_revision"),
                 resulting_lane_revision=d.get("resulting_lane_revision"),
                 expected_problem_revision=d.get("expected_problem_revision"),
                 resulting_problem_revision=d.get("resulting_problem_revision"), seq=d.get("seq"))
```

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/unit/test_self_improvement_events.py -q` → PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/__init__.py src/llmxive/self_improvement/events.py tests/unit/test_self_improvement_events.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T2): lane Event record + fail-closed validation + idempotency key"
```

---

### Task 3: Lane store on the shared CAS core (`lane_log.py`)

**Files:**
- Create: `src/llmxive/self_improvement/lane_log.py`
- Test: `tests/integration/test_self_improvement_lane_log.py` (incl. a **two-clone** concurrency test)

**Interfaces:**
- Consumes: `LogRef`, `AppendResult`, `append_to_log`, `read_log`, `GitLogContention` (Task 1); `Event`, `validate_lane_event`, `event_to_json`, `event_from_json`, `SEQ_FIELD`, `COORDINATOR_STREAM` (Task 2).
- Produces:
  - `LANE_REF = "refs/llmxive/self-improvement"`; `@dataclass LaneLogConfig(remote, expected_anchor)` (parallel to `LedgerConfig`, F4); `bootstrap_lane_log(repo, *, config) -> str` (F3 — one-time genesis, fail-closed-until-bootstrapped, idempotent, concurrent-safe, anchor-pinning); internal `_log_ref(problem_id, config) -> LogRef` with `event_dir = f"self-improvement/events/{problem_id}"` (per-Problem subtree → per-stream `seq`; all streams share the ONE ref so lane mutations serialize globally, giving the coordinator its singleton and each Problem its own revision line).
  - `class LaneRevisionConflict(RuntimeError)` — the caller's `expected_revision`/precondition lost; recompute (FR-008).
  - `read(repo, problem_id, *, config=LaneLogConfig()) -> list[Event]` — `read_log` mapped to `Event`s, **ordered by `seq`** (never timestamps). A gap/dup/fork in the sequence raises `GitLogError` (corruption is fail-closed, distinct from a `LaneRevisionConflict`).
  - `append(repo, event: Event, *, expected_revision: int | None, precondition: Callable[[list[Event]], tuple[bool, str]] | None = None, config=LaneLogConfig(), _after_parent=None) -> AppendResult` — wraps `append_to_log` with the lane `LogRef`, `validate=validate_lane_event`, `finalize=_finalize` (stamps `seq` + `expected/resulting_*_revision`), `identity_exclude=_IDENTITY_EXCLUDE`, and a `predicate` that (per CAS attempt, against the freshly-read, seq-sorted stream) FIRST validates sequence continuity (F7 — a corrupt stream fails closed before any revision/precondition check), then, if `expected_revision is not None`, `len(events) == expected_revision`, then `precondition(events)`. A predicate `False` surfaces as `GitLogDenied` → `LaneRevisionConflict`; `expected_revision=None` is an unconditional append (for audit events). The event carries the single FR-011 `timestamp` (no `ts`). Returns the `AppendResult` with the authoritative `seq`.

- [ ] **Step 1: Write the failing test** (including the cross-process guarantee)

```python
# tests/integration/test_self_improvement_lane_log.py
import subprocess
import threading

import pytest

from llmxive.git_event_log import GitLogError
from llmxive.self_improvement.events import Event
from llmxive.self_improvement.lane_log import (
    LaneLogConfig, LaneRevisionConflict, append, bootstrap_lane_log, read,
)

def _git(repo, *a):
    return subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

@pytest.fixture
def bare_remote(tmp_path):
    r = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(r)], check=True)
    return r

def _clone(bare, dst):
    subprocess.run(["git", "clone", "-q", str(bare), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    return dst

def _ev(eid, rev, problem_id="prob-1"):
    return Event(event_id=eid, event_type="Proposed", problem_id=problem_id, actor="a", payload={},
                 timestamp=f"2026-07-24T00:00:{rev:02d}+00:00", attempt_id="A1", expected_problem_revision=rev)

# ---- F3: bootstrap contract ----

def test_append_before_bootstrap_fails_closed(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    with pytest.raises(GitLogError):  # unbootstrapped remote ref → fail closed (GitLogAuthError)
        append(c, _ev("e0", 0), expected_revision=0, config=LaneLogConfig(remote="origin"))

def test_bootstrap_then_append_pins_anchor(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    anchor = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    cfg = LaneLogConfig(remote="origin", expected_anchor=anchor)  # pin the history anchor (F4)
    assert append(c, _ev("e0", 0), expected_revision=0, config=cfg).seq == 0
    assert append(c, _ev("e1", 1), expected_revision=1, config=cfg).seq == 1
    assert [e.seq for e in read(c, "prob-1", config=cfg)] == [0, 1]

def test_bootstrap_is_idempotent(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    a1 = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    a2 = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))  # repeat → same anchor, no 2nd genesis
    assert a1 == a2

def test_two_concurrent_bootstrappers_converge(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    a1 = bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    a2 = bootstrap_lane_log(c2, config=LaneLogConfig(remote="origin"))  # loser observes the winner's ref
    assert a1 == a2  # exactly ONE genesis ref survives

def test_wrong_expected_anchor_fails_closed(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    with pytest.raises(GitLogError):  # a pinned anchor that isn't the real ref → fail closed
        read(c, "prob-1", config=LaneLogConfig(remote="origin", expected_anchor="0" * 40))

# ---- FR-008: revision CAS on the bootstrapped ref ----

@pytest.fixture
def env(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    anchor = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    return c, LaneLogConfig(remote="origin", expected_anchor=anchor)

def test_stale_revision_loses(env):
    c, cfg = env
    append(c, _ev("e0", 0), expected_revision=0, config=cfg)
    with pytest.raises(LaneRevisionConflict):
        append(c, _ev("e1", 0), expected_revision=0, config=cfg)  # actual rev is 1

# ---- F6: TRUE barrier-driven race, deterministic via the core _after_parent seam ----

def test_barrier_seam_race_exactly_one_wins(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    c2 = _clone(bare_remote, tmp_path / "c2")
    cfg = LaneLogConfig(remote="origin")
    at_parent = threading.Barrier(2)  # both block here AFTER fixing the same genesis parent
    outcomes, lock = [], threading.Lock()

    def _worker(clone, tag):
        fired = {"once": False}

        def _seam():  # one-shot: block only on the FIRST attempt (a retry must not re-wait)
            if not fired["once"]:
                fired["once"] = True
                try:
                    at_parent.wait()
                except threading.BrokenBarrierError:
                    pass

        try:
            r = append(clone, _ev(f"from-{tag}", 0), expected_revision=0, config=cfg, _after_parent=_seam)
            with lock:
                outcomes.append(("ok", r))
        except LaneRevisionConflict as exc:
            with lock:
                outcomes.append(("conflict", exc))

    ts = [threading.Thread(target=_worker, args=(c, t)) for c, t in ((c1, "c1"), (c2, "c2"))]
    for th in ts:
        th.start()
    for th in ts:
        th.join()
    oks = [o for k, o in outcomes if k == "ok"]
    conflicts = [o for k, o in outcomes if k == "conflict"]
    # both built from the SAME parent (barrier) then raced the ACTUAL update-ref/FF-push:
    # exactly one wins, the loser hits non-fast-forward → recompute → predicate fails → conflict.
    assert len(oks) == 1 and len(conflicts) == 1
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/integration/test_self_improvement_lane_log.py -q` → FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/lane_log.py
"""The lane's append-only store on the DEDICATED authoritative ref (FR-009 rev-15): thin
wrappers over the shared git_event_log CAS core. Per-Problem subtrees give each Problem
(and the coordinator) an authoritative, gap-checked ``seq`` line; the single ref
serializes all lane mutations (FR-008). Bootstrapped once, fetched by the transport,
FAILS CLOSED until bootstrapped, and supports ``expected_anchor`` pinning."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llmxive.git_event_log import (
    AppendResult, GitLogDenied, GitLogError, LogRef, append_to_log, bootstrap_log, read_log,
)
from llmxive.self_improvement.events import (
    COORDINATOR_STREAM, SEQ_FIELD, Event, event_from_json, event_to_json, validate_lane_event,
)

LANE_REF = "refs/llmxive/self-improvement"
_LANE_GENESIS_MSG = "bootstrap self-improvement lane log v1"

@dataclass(frozen=True)
class LaneLogConfig:
    """Remote identity + pinned history anchor for the lane ref — parallel to
    ``LedgerConfig`` (F4). Threaded through EVERY lane bootstrap/read/append (and the
    coordinator/ledger/audit APIs) so a caller can PIN the history anchor — critical for
    an autonomous self-modifying system. Default is local-only (tests / single runner)."""
    remote: str | None = None
    expected_anchor: str | None = None
#: Fields excluded from the append-only IDENTITY comparison (F5): the store-assigned
#: ``seq``, the FR-011 ``timestamp`` (one canonical field — NO duplicate ``ts``, F2), and
#: the four CAS revision ANCHORS — none is part of an operation's semantic identity, so a
#: re-invoked operation whose event lands at a DIFFERENT revision/time is still an
#: idempotent no-op, not a spurious append-only raise.
_IDENTITY_EXCLUDE = frozenset({
    SEQ_FIELD, "timestamp", "expected_lane_revision", "resulting_lane_revision",
    "expected_problem_revision", "resulting_problem_revision",
})

class LaneRevisionConflict(RuntimeError):
    """The CAS precondition (expected_revision or a caller precondition) no longer holds
    against the authoritative tip — recompute and retry/yield (FR-008); never force."""

def _log_ref(problem_id: str, config: LaneLogConfig) -> LogRef:
    # ONE ref; per-Problem (and coordinator) subtree → per-stream seq line.
    return LogRef(ref=LANE_REF, event_dir=f"self-improvement/events/{problem_id}",
                  remote=config.remote, expected_anchor=config.expected_anchor)

def bootstrap_lane_log(repo: Path, *, config: LaneLogConfig) -> str:
    """One-time creation of the authoritative lane ref (F3), mirroring the credit ledger's
    ``bootstrap_ledger``: a genesis anchor commit on ``LANE_REF``. Invoked ONCE by a
    privileged setup workflow — NOT by an ordinary lane call; every remote read/append
    FAILS CLOSED until it has run, exactly like the credit ledger. Idempotent (a repeat
    returns the same anchor, no second genesis); two concurrent bootstrappers converge on
    ONE ref (FF-push CAS); a divergent/wrong existing ref fails closed. Returns the genesis
    anchor OID — PIN it as ``LaneLogConfig.expected_anchor`` thereafter. The ref is
    protected: only the trusted lane transport advances it, fast-forward only."""
    return bootstrap_log(repo, log=_log_ref(COORDINATOR_STREAM, config), message=_LANE_GENESIS_MSG,
                         remote=config.remote)

def _message(event: dict) -> str:
    return f"self-improvement: {event.get('event_type', '?')} {event['event_id']}"

def _sorted_by_seq(raw: list[dict]) -> list[dict]:
    return sorted(raw, key=lambda r: r.get("seq", -1))  # seq is the AUTHORITATIVE order

def _to_json(raw: dict) -> str:
    return json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _check_continuity(raw_sorted: list[dict], problem_id: str) -> None:
    seqs = [r.get("seq") for r in raw_sorted]
    if seqs != list(range(len(raw_sorted))):
        # A gap/dup/fork is corruption of the authoritative sequence — fail closed,
        # never retry (a GitLogError propagates out of the CAS loop; NOT a conflict).
        raise GitLogError(f"corrupt sequence in stream {problem_id!r}: {seqs}")

def read(repo: Path, problem_id: str, *, config: LaneLogConfig = LaneLogConfig()) -> list[Event]:
    raw = read_log(repo, log=_log_ref(problem_id, config), validate=validate_lane_event)
    raw_sorted = _sorted_by_seq(raw)
    _check_continuity(raw_sorted, problem_id)
    return [event_from_json(_to_json(r)) for r in raw_sorted]

def _finalize(built: dict, seq: int) -> dict:
    scope = "lane" if built["problem_id"] == COORDINATOR_STREAM else "problem"
    return {**built, SEQ_FIELD: seq,
            f"expected_{scope}_revision": seq, f"resulting_{scope}_revision": seq + 1}

def append(repo: Path, event: Event, *, expected_revision: int | None,
           precondition: Callable[[list[Event]], tuple[bool, str]] | None = None,
           config: LaneLogConfig = LaneLogConfig(),
           _after_parent: Callable[[], None] | None = None) -> AppendResult:
    """CAS-append one lane event. ``expected_revision=None`` = an UNCONDITIONAL append
    (audit events carry no revision precondition — just the ref-CAS + idempotency). Raises
    ``LaneRevisionConflict`` when the revision/precondition lost; a corrupt sequence raises
    ``GitLogError`` (fail closed). ``_after_parent`` is a TEST-ONLY seam (F6) forwarded to
    the core so a barrier can make the non-fast-forward race deterministic."""
    raw = json.loads(event_to_json(event))  # carries `timestamp`; NO duplicate `ts` (F2)

    def _predicate(existing: list[dict]) -> tuple[bool, str]:
        ordered = _sorted_by_seq(existing)
        _check_continuity(ordered, event.problem_id)                     # F7: BEFORE any other check
        if expected_revision is not None and len(ordered) != expected_revision:
            return (False, f"stale revision: expected {expected_revision}, actual {len(ordered)}")
        if precondition is not None:
            return precondition([event_from_json(_to_json(r)) for r in ordered])
        return (True, "")

    try:
        return append_to_log(
            repo, log=_log_ref(event.problem_id, config), validate=validate_lane_event,
            message_fn=_message, event=raw, predicate=_predicate, finalize=_finalize,
            identity_exclude=_IDENTITY_EXCLUDE, _after_parent=_after_parent,
        )
    except GitLogDenied as exc:      # predicate returned False → a lane CAS conflict
        raise LaneRevisionConflict(str(exc)) from exc
    # a GitLogError from _check_continuity (corruption) propagates unchanged — fail closed.
```

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/integration/test_self_improvement_lane_log.py -q` → PASS (3 passed), including the two-clone CAS test.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/lane_log.py tests/integration/test_self_improvement_lane_log.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T3): lane store on the shared CAS core (seq-ordered, two-clone CAS)"
```

---

### Task 4: `LaneCoordinator` projection

**Files:**
- Create: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/unit/test_self_improvement_coordinator.py`

**Interfaces:**
- Consumes: `Event`, `COORDINATOR_STREAM` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class LaneCoordinator`: `lane_revision`, `active_problem_id`, `active_attempt_id`, `monitored_attempts: tuple[str, ...]`, `promotion_enabled`, `last_autonomous_merge_at`, `policy_version` (FR-007 / Key Entities line 224).
  - `EMPTY_COORDINATOR`.
  - `project_coordinator(events: list[Event]) -> LaneCoordinator` — pure fold, `lane_revision = len(events)`. `ClaimAcquired` sets active ids; `ClaimReleased` clears them; `MonitorStarted` appends; `PromotionEnabledSet` sets flag/policy. **An unknown `event_type` here raises `ValueError`** (F9: never silently advance the safety-critical projection — validation already gates writes, but a projection over a corrupted/newer stream must fail closed, not shrug).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_coordinator.py
import pytest

from llmxive.self_improvement.coordinator import EMPTY_COORDINATOR, project_coordinator
from llmxive.self_improvement.events import COORDINATOR_STREAM, Event

def _ev(eid, etype, payload, seq):
    return Event(event_id=eid, event_type=etype, problem_id=COORDINATOR_STREAM, actor="coord",
                 payload=payload, timestamp="2026-07-24T00:00:00+00:00", expected_lane_revision=seq, seq=seq)

def test_empty_is_genesis():
    assert project_coordinator([]) == EMPTY_COORDINATOR

def test_claim_then_release_returns_idle():
    events = [_ev("e1", "ClaimAcquired", {"problem_id": "P1", "attempt_id": "A1"}, 0),
              _ev("e2", "ClaimReleased", {"problem_id": "P1", "attempt_id": "A1"}, 1)]
    c = project_coordinator(events)
    assert c.lane_revision == 2 and c.active_problem_id is None and c.active_attempt_id is None

def test_claim_sets_active():
    c = project_coordinator([_ev("e1", "ClaimAcquired", {"problem_id": "P1", "attempt_id": "A1"}, 0)])
    assert c.active_problem_id == "P1" and c.active_attempt_id == "A1" and c.lane_revision == 1

def test_projection_rejects_unknown_event_type():
    bad = Event(event_id="x", event_type="SomethingFromTheFuture", problem_id=COORDINATOR_STREAM, actor="c",
                payload={}, timestamp="2026-07-24T00:00:00+00:00", expected_lane_revision=0, seq=0)
    with pytest.raises(ValueError, match="unknown coordinator event"):
        project_coordinator([bad])

def test_projection_rejects_illegal_transitions():  # F3: the projection is the recovery authority
    # release while idle
    with pytest.raises(ValueError, match="ClaimReleased while idle"):
        project_coordinator([_ev("e1", "ClaimReleased", {"problem_id": "P1", "attempt_id": "A1"}, 0)])
    # claim while already active
    with pytest.raises(ValueError, match="ClaimAcquired while active"):
        project_coordinator([_ev("e1", "ClaimAcquired", {"problem_id": "P1", "attempt_id": "A1"}, 0),
                             _ev("e2", "ClaimAcquired", {"problem_id": "P2", "attempt_id": "A2"}, 1)])
    # release by a non-owner
    with pytest.raises(ValueError, match="non-owner"):
        project_coordinator([_ev("e1", "ClaimAcquired", {"problem_id": "P1", "attempt_id": "A1"}, 0),
                             _ev("e2", "ClaimReleased", {"problem_id": "PX", "attempt_id": "AX"}, 1)])
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/unit/test_self_improvement_coordinator.py -q` → FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/coordinator.py
"""The singleton LaneCoordinator (FR-007): a projection over the coordinator stream
that serializes the pre-merge pipeline, plus its ownership-checked CAS transitions
(FR-008). Slice 1A delivers the projection + claim/release; the label/comment side
effect (US2) is a later slice."""

from __future__ import annotations

from dataclasses import dataclass, replace

from llmxive.self_improvement.events import Event

_COORDINATOR_TYPES = {"ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet"}

@dataclass(frozen=True)
class LaneCoordinator:
    lane_revision: int
    active_problem_id: str | None
    active_attempt_id: str | None
    monitored_attempts: tuple[str, ...]
    promotion_enabled: bool
    last_autonomous_merge_at: str | None
    policy_version: int

EMPTY_COORDINATOR = LaneCoordinator(0, None, None, (), False, None, 0)

def project_coordinator(events: list[Event]) -> LaneCoordinator:
    """Fold the coordinator stream, enforcing the LEGAL TRANSITION MATRIX (F3). The
    projection is the recovery authority, so it fails closed on any illegal history —
    a stray/duplicate/out-of-order transition RAISES, it is never ignored."""
    c = EMPTY_COORDINATOR
    for e in events:
        if e.event_type not in _COORDINATOR_TYPES:
            raise ValueError(f"unknown coordinator event {e.event_type!r} — fail closed")
        p = e.payload
        if e.event_type == "ClaimAcquired":
            if c.active_problem_id is not None:  # only idle → claimed
                raise ValueError(f"illegal transition ClaimAcquired while active ({c.active_problem_id!r})")
            c = replace(c, active_problem_id=p["problem_id"], active_attempt_id=p["attempt_id"])
        elif e.event_type == "ClaimReleased":
            if c.active_problem_id is None:  # only active → idle
                raise ValueError("illegal transition ClaimReleased while idle")
            if (c.active_problem_id, c.active_attempt_id) != (p["problem_id"], p["attempt_id"]):
                raise ValueError("illegal transition ClaimReleased by a non-owner")
            c = replace(c, active_problem_id=None, active_attempt_id=None)
        elif e.event_type == "MonitorStarted":
            c = replace(c, monitored_attempts=(*c.monitored_attempts, p["attempt_id"]))
        elif e.event_type == "PromotionEnabledSet":
            c = replace(c, promotion_enabled=bool(p["promotion_enabled"]),
                        policy_version=int(p.get("policy_version", c.policy_version)))
        c = replace(c, lane_revision=c.lane_revision + 1)
    return c
```

(Drop the first `test_unknown_type_fails_closed` if it duplicates `test_projection_rejects_unknown_event_type` — keep the clearer one. `test_claim_then_release_returns_idle`, `test_claim_sets_active`, `test_empty_is_genesis`, and the reject test are the load-bearing ones.)

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/unit/test_self_improvement_coordinator.py -q` → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/coordinator.py tests/unit/test_self_improvement_coordinator.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T4): LaneCoordinator projection (fail-closed on unknown type)"
```

---

### Task 5: Ownership-checked coordinator CAS (`cas_claim` / `cas_release`)

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/integration/test_self_improvement_coordinator_cas.py` (incl. the **delayed-stale-release** regression, F6)

**Interfaces:**
- Consumes: `project_coordinator` (Task 4); `append`, `read`, `LaneRevisionConflict` (Task 3); `Event`, `COORDINATOR_STREAM`, `derive_event_id` (Task 2).
- Produces:
  - `cas_claim(repo, *, problem_id, attempt_id, actor, timestamp, config=LaneLogConfig()) -> LaneCoordinator` — reads the coordinator stream; builds a `ClaimAcquired` event (idempotency key `("claim", problem_id, attempt_id)`, `expected_lane_revision = current.lane_revision`); appends with a precondition that admits the claim iff **the claim already landed (idempotent) OR the lane is idle** (`active_problem_id is None`). Raises `LaneRevisionConflict` when the lane is occupied by a different Problem or the revision moved. Returns the new projection.
  - `cas_release(repo, *, problem_id, attempt_id, actor, timestamp, config=LaneLogConfig()) -> LaneCoordinator` — appends `ClaimReleased` (idempotency key `("release", problem_id, attempt_id)`) with an **ownership precondition** (F6): admit iff **this exact release already landed (idempotent) OR the current active pair equals `(problem_id, attempt_id)`**. A delayed release from an old `(P1,A1)` MUST NOT clear a newer `(P2,A2)` claim → it fails the precondition → `LaneRevisionConflict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_coordinator_cas.py
import subprocess

import pytest

from llmxive.self_improvement.coordinator import cas_claim, cas_release
from llmxive.self_improvement.lane_log import LaneRevisionConflict

def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path

TS = "2026-07-24T00:00:00+00:00"

def test_claim_when_idle_then_occupied_blocks_others(repo):
    c = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert c.active_problem_id == "P1" and c.lane_revision == 1
    with pytest.raises(LaneRevisionConflict):
        cas_claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)

def test_claim_is_idempotent_on_reinvocation(repo):
    a = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    b = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # re-invoked
    assert a == b and b.lane_revision == 1  # no duplicate event, same projection

def test_release_requires_ownership_stale_release_cannot_clear_newer_claim(repo):
    # F6 regression: P1/A1 claims, releases (lane idle), P2/A2 claims; a DELAYED
    # duplicate release from P1/A1 must NOT clear P2/A2's active claim.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    with pytest.raises(LaneRevisionConflict):
        cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # stale, wrong owner
    # sanity: the correct owner can release
    c = cas_release(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    assert c.active_problem_id is None

def test_release_is_idempotent_for_the_true_owner(repo):
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    c = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # re-invoked
    assert c.active_problem_id is None and c.lane_revision == 2  # no third event
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/integration/test_self_improvement_coordinator_cas.py -q` → FAIL (`ImportError`).

- [ ] **Step 3: Write minimal implementation** (append to `coordinator.py`)

```python
from pathlib import Path

from llmxive.self_improvement.events import COORDINATOR_STREAM, derive_event_id
from llmxive.self_improvement.lane_log import LaneLogConfig, append, read

def _coord_event(event_type, idem, payload, actor, timestamp, expected_rev):
    return Event(
        event_id=derive_event_id(COORDINATOR_STREAM, "\x00".join(idem)), event_type=event_type,
        problem_id=COORDINATOR_STREAM, actor=actor, payload=payload, timestamp=timestamp,
        expected_lane_revision=expected_rev,
    )

def cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str,
              config: LaneLogConfig = LaneLogConfig()) -> LaneCoordinator:
    events = read(repo, COORDINATOR_STREAM, config=config)
    event = _coord_event("ClaimAcquired", ("claim", problem_id, attempt_id),
                         {"problem_id": problem_id, "attempt_id": attempt_id},
                         actor, timestamp, project_coordinator(events).lane_revision)

    def _idle_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if any(e.event_id == event.event_id for e in evs):
            return (True, "")  # this exact claim already landed → idempotent
        pid = project_coordinator(evs).active_problem_id
        return (pid is None, "" if pid is None else f"lane occupied by {pid!r}")

    append(repo, event, expected_revision=project_coordinator(events).lane_revision,
           precondition=_idle_or_landed, config=config)
    return project_coordinator(read(repo, COORDINATOR_STREAM, config=config))

def cas_release(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str,
                config: LaneLogConfig = LaneLogConfig()) -> LaneCoordinator:
    events = read(repo, COORDINATOR_STREAM, config=config)
    event = _coord_event("ClaimReleased", ("release", problem_id, attempt_id),
                         {"problem_id": problem_id, "attempt_id": attempt_id},
                         actor, timestamp, project_coordinator(events).lane_revision)

    def _owns_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if any(e.event_id == event.event_id for e in evs):
            return (True, "")  # this exact release already landed → idempotent
        c = project_coordinator(evs)
        owns = c.active_problem_id == problem_id and c.active_attempt_id == attempt_id
        return (owns, "" if owns else f"release owner mismatch (active={c.active_problem_id!r})")

    append(repo, event, expected_revision=project_coordinator(events).lane_revision,
           precondition=_owns_or_landed, config=config)
    return project_coordinator(read(repo, COORDINATOR_STREAM, config=config))
```

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/integration/test_self_improvement_coordinator_cas.py -q` → PASS (4 passed, incl. the stale-release regression).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/coordinator.py tests/integration/test_self_improvement_coordinator_cas.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T5): ownership-checked coordinator CAS (F6 stale-release guard, F5 idempotent)"
```

---

### Task 6: `AttemptCreditLedger` reservation projection (with transition matrix)

**Files:**
- Create: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/unit/test_self_improvement_credit_projection.py`

**Interfaces:**
- Produces: `STATE_OPEN`/`STATE_RETAINED`/`STATE_RECONCILED`/`STATE_RELEASED`; `COUNTING_STATES = frozenset({open, retained, reconciled})`; `@dataclass(frozen=True) class AttemptReservation(reservation_id, call_id, reserved_credits, state)`; `project_reservations(events, attempt_id) -> dict[str, AttemptReservation]` — folds events with matching `attempt_id`, **enforcing the legal transition matrix (F3)**: `AttemptCreditReserved` seeds `open` (a duplicate reserve for an existing id → raise); `Retained` requires `open → retained`; `Released` requires `open → released` (a dispatched reservation is never released); `Reconciled` requires `retained → reconciled`; `DispatchUnknown` (carrying a `reservation_id`) drives `open → retained` and is a no-op if already `retained` (this is the atomic F4 reconcile effect). Any OTHER transition (a transition for an unknown id, `released → retained`, `reconciled → *`, etc.) RAISES `ValueError` — a stray transition fails closed, never ignored. `counting_total(reservations) -> float`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_credit_projection.py
import pytest

from llmxive.self_improvement.credit_ledger import (
    STATE_OPEN, STATE_RECONCILED, STATE_RELEASED, STATE_RETAINED, counting_total, project_reservations,
)
from llmxive.self_improvement.events import Event

def _ev(eid, etype, rid, seq, attempt="A1", credits=2.5, call_id="c1"):
    payload = {"reservation_id": rid}
    if etype == "AttemptCreditReserved":
        payload |= {"call_id": call_id, "reserved_credits": credits}
    return Event(event_id=eid, event_type=etype, problem_id="P1", actor="exec", payload=payload,
                 timestamp="2026-07-24T00:00:00+00:00", attempt_id=attempt,
                 expected_problem_revision=seq, resulting_problem_revision=seq + 1, seq=seq)

def test_reserve_retain_reconcile_advances():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0), _ev("e2", "AttemptCreditRetained", "r1", 1),
              _ev("e3", "AttemptCreditReconciled", "r1", 2)]
    assert project_reservations(events, "A1")["r1"].state == STATE_RECONCILED

def test_released_excluded_from_counting():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=10.0),
              _ev("e2", "AttemptCreditReserved", "r2", 1, credits=5.0),
              _ev("e3", "AttemptCreditReleased", "r2", 2)]
    res = project_reservations(events, "A1")
    assert res["r2"].state == STATE_RELEASED and counting_total(res) == 10.0

def test_dispatch_unknown_retains_the_reservation():  # F4 atomic effect
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0),
              _ev("e2", "DispatchUnknown", "r1", 1)]  # payload carries reservation_id
    assert project_reservations(events, "A1")["r1"].state == STATE_RETAINED

def test_projection_rejects_illegal_transitions():  # F3
    with pytest.raises(ValueError, match="unknown reservation"):
        project_reservations([_ev("e1", "AttemptCreditRetained", "ghost", 0)], "A1")
    with pytest.raises(ValueError, match="illegal"):  # reserve twice
        project_reservations([_ev("e1", "AttemptCreditReserved", "r1", 0),
                              _ev("e2", "AttemptCreditReserved", "r1", 1)], "A1")
    with pytest.raises(ValueError, match="illegal"):  # released -> retained
        project_reservations([_ev("e1", "AttemptCreditReserved", "r1", 0),
                              _ev("e2", "AttemptCreditReleased", "r1", 1),
                              _ev("e3", "AttemptCreditRetained", "r1", 2)], "A1")
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/unit/test_self_improvement_credit_projection.py -q` → FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/credit_ledger.py
"""The Attempt-scoped credit ledger (FR-033) — the concrete lane ``ReservationAuthority``.
An event-sourced projection over the per-Problem stream's ``AttemptCredit*`` (+ the
reconcile-driving ``DispatchUnknown``) events, enforcing a fail-closed transition matrix."""

from __future__ import annotations

from dataclasses import dataclass, replace

from llmxive.self_improvement.events import Event

STATE_OPEN, STATE_RETAINED, STATE_RECONCILED, STATE_RELEASED = "open", "retained", "reconciled", "released"
COUNTING_STATES = frozenset({STATE_OPEN, STATE_RETAINED, STATE_RECONCILED})

@dataclass(frozen=True)
class AttemptReservation:
    reservation_id: str
    call_id: str
    reserved_credits: float
    state: str

def project_reservations(events: list[Event], attempt_id: str) -> dict[str, AttemptReservation]:
    out: dict[str, AttemptReservation] = {}
    for e in events:
        if e.attempt_id != attempt_id:
            continue
        if e.event_type == "AttemptCreditReserved":
            rid = str(e.payload["reservation_id"])
            if rid in out:
                raise ValueError(f"illegal duplicate AttemptCreditReserved for {rid!r}")
            out[rid] = AttemptReservation(rid, str(e.payload["call_id"]),
                                          float(e.payload["reserved_credits"]), STATE_OPEN)
            continue
        transitions = {  # event_type -> {from_state: to_state}
            "AttemptCreditRetained": {STATE_OPEN: STATE_RETAINED},
            "AttemptCreditReleased": {STATE_OPEN: STATE_RELEASED},
            "AttemptCreditReconciled": {STATE_RETAINED: STATE_RECONCILED},
            "DispatchUnknown": {STATE_OPEN: STATE_RETAINED, STATE_RETAINED: STATE_RETAINED},
        }.get(e.event_type)
        if transitions is None:
            continue  # not a reservation-affecting event (audit/other)
        rid = e.payload.get("reservation_id")
        if rid is None:
            continue  # e.g. a free-candidate DispatchUnknown has no reservation
        rid = str(rid)
        if rid not in out:
            raise ValueError(f"illegal {e.event_type} for unknown reservation {rid!r}")
        cur = out[rid].state
        if cur not in transitions:
            raise ValueError(f"illegal transition {e.event_type} from {cur!r} for {rid!r}")
        out[rid] = replace(out[rid], state=transitions[cur])
    return out

def counting_total(reservations: dict[str, AttemptReservation]) -> float:
    return sum(r.reserved_credits for r in reservations.values() if r.state in COUNTING_STATES)
```

- [ ] **Step 4: Run test to verify it passes** — PASS (4 passed).

- [ ] **Step 5: Commit** — `feat(025 slice-1A T6): AttemptCreditLedger projection + fail-closed transition matrix`.

### Task 7: `AttemptCreditLedger.reserve` (in-process lock + budget CAS + collision)

**Files:**
- Modify: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/integration/test_self_improvement_credit_ledger.py` (incl. a `ThreadPoolExecutor` panel test AND a two-clone over-budget test)

**Interfaces:**
- Produces: `class AttemptCreditLedger` implementing the slice-0 `ReservationAuthority`. Constructor `(*, repo, problem_id, attempt_id, attempt_budget_credits, actor, clock, config=LaneLogConfig())`; holds a `threading.Lock`. `reserve(credits, *, reservation_id, call_id) -> bool` — under the lock, a bounded retry loop: project the Attempt's reservations from `read(problem_id)`; same `(credits, call_id)` under an existing id → `True` (idempotent); different identity → `raise ValueError` (integrity); `counting_total + credits > budget` → `False`; else `append` an `AttemptCreditReserved` event (`expected_revision = len(read)`) with a precondition re-checking the budget against fresh events (so a **cross-clone** competitor that consumed the budget flips this to `False` on recompute); on `LaneRevisionConflict` retry; after the cap `raise LaneContention`. The in-process `Lock` makes the concurrent PANEL (one process, one shared ledger instance) atomic (US1 scenario 5); the ref-CAS + budget-recheck precondition makes CROSS-clone reservers safe.
- Produces: `class LaneContention(RuntimeError)`.

- [ ] **Steps:** Tests: (1) within-budget True / over-budget False / at-budget True; (2) idempotent same identity; (3) conflicting identity raises; (4) `ThreadPoolExecutor(2)` sharing one ledger, budget admits one → exactly one `True`; (5) **barrier-driven two-clone race** (F6): two clones of one bare remote both reserving the last credits, each syncing the same parent then released together by a `threading.Barrier` — the ref-CAS + budget-recheck admits at most the remaining budget (the loser recomputes and returns `False`, never both `True`). RED (`ImportError`) → GREEN. Commit `feat(025 slice-1A T7): AttemptCreditLedger.reserve — lock + ref-CAS budget guard + collision`.

The reserve body (append-with-budget-precondition + retry):

```python
    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        with self._lock:
            for _ in range(_MAX_RETRIES):
                events = read(self._repo, self._problem_id, config=self._config)
                res = project_reservations(events, self._attempt_id)
                existing = res.get(reservation_id)
                if existing is not None:
                    if existing.call_id == call_id and existing.reserved_credits == credits:
                        return True
                    raise ValueError(f"reservation {reservation_id!r} COLLISION — integrity violation")
                if counting_total(res) + credits > self._budget:
                    return False
                event = self._reserve_event(reservation_id, call_id, credits, len(events))

                def _budget_ok(evs, _c=credits, _rid=reservation_id):
                    r = project_reservations([event_from_json_or_pass(e) for e in evs], self._attempt_id)
                    if _rid in r:
                        return (True, "")  # already landed → idempotent
                    return (counting_total(r) + _c <= self._budget, "precondition: over budget")

                try:
                    append(self._repo, event, expected_revision=len(events),
                           precondition=_budget_ok, config=self._config)
                    return True
                except LaneRevisionConflict:
                    continue
            raise LaneContention(f"reserve CAS did not converge for {reservation_id!r}")
```

(The precondition receives already-typed `Event`s from `lane_log.append`'s wrapper — the `[event_from_json_or_pass(e) ...]` shim is illustrative; `append`'s `precondition` signature is `Callable[[list[Event]], tuple[bool,str]]`, so the body just calls `project_reservations(evs, self._attempt_id)` directly. Match the exact `precondition` type from Task 3.)

### Task 8: `AttemptCreditLedger.release` / `mark_retained`

**Files:** Modify `credit_ledger.py`; extend `tests/integration/test_self_improvement_credit_ledger.py`.

**Interfaces:** Two more `ReservationAuthority` methods on `AttemptCreditLedger`, each idempotent, each appending via a shared `_cas_append` (unconditional append + already-landed precondition; retry on conflict):
- `release(reservation_id)` — under the lock, read+project; append `AttemptCreditReleased` ONLY when the reservation is currently `open` (`open → released`). Absent / already-`released` / `retained` / `reconciled` → no-op (a DISPATCHED reservation is never released — FR-033).
- `mark_retained(reservation_id)` — under the lock; append `AttemptCreditRetained` ONLY when currently `open` (`open → retained`). Otherwise no-op.

- [ ] **Step 1: failing test**

```python
# add to tests/integration/test_self_improvement_credit_ledger.py
from llmxive.self_improvement.credit_ledger import STATE_RELEASED, STATE_RETAINED, project_reservations
from llmxive.self_improvement.lane_log import LaneLogConfig, read

def _state(repo, rid):
    return project_reservations(read(repo, "P1"), "A1")[rid].state

def test_release_frees_budget_retain_keeps_it(repo):
    led = _ledger(repo, budget=10.0)
    led.reserve(6.0, reservation_id="r1", call_id="c1"); led.release("r1")
    assert _state(repo, "r1") == STATE_RELEASED
    led.reserve(6.0, reservation_id="r2", call_id="c2"); led.mark_retained("r2")
    assert _state(repo, "r2") == STATE_RETAINED

def test_dispatched_reservation_is_never_released(repo):  # FR-033
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1"); led.mark_retained("r1"); led.release("r1")
    assert _state(repo, "r1") == STATE_RETAINED  # release was a no-op

def test_release_and_retain_are_idempotent(repo):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1"); led.release("r1"); led.release("r1")
    assert _state(repo, "r1") == STATE_RELEASED

def test_release_versus_retain_race_exactly_one_transition_lands(repo):
    # F1: two concurrent operations on ONE open reservation via the SHARED ledger. The
    # in-process lock serializes them: the first (release OR retain) transitions open→X;
    # the loser acquires the lock, sees the reservation is no longer `open`, and NO-OPs
    # per its contract. Exactly ONE transition event lands.
    import threading
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    barrier = threading.Barrier(2)

    def _release():
        barrier.wait(); led.release("r1")

    def _retain():
        barrier.wait(); led.mark_retained("r1")

    ts = [threading.Thread(target=_release), threading.Thread(target=_retain)]
    for t in ts: t.start()
    for t in ts: t.join()

    final = _state(repo, "r1")
    assert final in (STATE_RELEASED, STATE_RETAINED)  # whichever won
    # exactly one transition event (not both) — the loser no-op'd
    kinds = [e.event_type for e in read(repo, "P1") if e.event_type.startswith("AttemptCredit")]
    assert kinds == ["AttemptCreditReserved", f"AttemptCredit{'Released' if final == STATE_RELEASED else 'Retained'}"]
```

- [ ] **Step 2-4:** RED (`AttributeError`) → implement → GREEN.

```python
    # The legal SOURCE state for each transition event (F1). The precondition admits a
    # transition iff the exact event already landed (idempotent) OR the reservation is
    # currently in the required source state — checked FRESH inside every CAS attempt,
    # because a concurrent worker may have moved the state after the outer read.
    _FROM_STATES = {
        "AttemptCreditReleased": frozenset({STATE_OPEN}),
        "AttemptCreditRetained": frozenset({STATE_OPEN}),
        "AttemptCreditReconciled": frozenset({STATE_RETAINED}),
    }

    def _cas_append(self, event_type: str, idem: tuple[str, ...], payload: dict) -> None:
        rid = str(payload["reservation_id"])
        for _ in range(_MAX_RETRIES):
            events = read(self._repo, self._problem_id, config=self._config)
            eid = derive_event_id(self._problem_id, "credit\x00" + "\x00".join((self._attempt_id, *idem)))
            landed = any(e.event_id == eid for e in events)
            cur = project_reservations(events, self._attempt_id).get(rid)
            # Not-yet-landed AND no longer in a legal source state → a concurrent legal
            # transition won (e.g. release lost to a retain); no-op per the idempotent
            # method contract, NOT a retry-to-contention.
            if not landed and (cur is None or cur.state not in self._FROM_STATES[event_type]):
                return
            event = Event(event_id=eid, event_type=event_type, problem_id=self._problem_id,
                          actor=self._actor, payload=payload, timestamp=self._clock(),
                          attempt_id=self._attempt_id, expected_problem_revision=len(events))

            def _may_transition(evs, _e=eid, _rid=rid, _et=event_type):
                if any(x.event_id == _e for x in evs):
                    return (True, "")  # this exact transition already landed → idempotent
                r = project_reservations(evs, self._attempt_id).get(_rid)
                if r is None:
                    return (False, "unknown reservation")
                ok = r.state in self._FROM_STATES[_et]
                return (ok, "" if ok else f"illegal transition from {r.state}")

            try:
                append(self._repo, event, expected_revision=None, precondition=_may_transition,
                       config=self._config)
                return
            except LaneRevisionConflict:
                continue  # revision moved; the top-of-loop re-check decides no-op vs retry
        raise LaneContention(f"{event_type} CAS did not converge for {self._attempt_id!r}")

    def release(self, reservation_id: str) -> None:
        with self._lock:
            r = project_reservations(read(self._repo, self._problem_id, config=self._config),
                                     self._attempt_id).get(reservation_id)
            if r is None or r.state != STATE_OPEN:
                return
            self._cas_append("AttemptCreditReleased", ("release", reservation_id),
                             {"reservation_id": reservation_id})

    def mark_retained(self, reservation_id: str) -> None:
        with self._lock:
            r = project_reservations(read(self._repo, self._problem_id, config=self._config),
                                     self._attempt_id).get(reservation_id)
            if r is None or r.state != STATE_OPEN:
                return
            self._cas_append("AttemptCreditRetained", ("retain", reservation_id),
                             {"reservation_id": reservation_id})
```

- [ ] **Step 5: Commit** — `feat(025 slice-1A T8): AttemptCreditLedger.release/mark_retained (open-only, idempotent)`.

### Task 9: `AttemptCreditLedger.reconcile`

**Files:** Modify `credit_ledger.py`; extend the integration test.

**Interfaces:** `reconcile(reconciled_ledger_ids: set[str]) -> list[str]` — under the lock, for each `retained` reservation whose id is in `reconciled_ledger_ids` (the 026 ids `reservations.reconcile_settled` moved to `reconciled`), append `AttemptCreditReconciled` (`retained → reconciled`); returns the moved ids; idempotent (already-`reconciled` skipped). This is the consumer of "reconciliation consumes the `route_audit` reservation events + 026's `reconcile_settled`" (the 026 wiring is at the call boundary — slice 1B).

- [ ] **Steps:** test that `reconcile({"r1"})` moves only `r1` `retained → reconciled`, leaves an unlisted `retained` id alone, and is idempotent on re-run. Impl:

```python
    def reconcile(self, reconciled_ledger_ids: set[str]) -> list[str]:
        with self._lock:
            res = project_reservations(read(self._repo, self._problem_id, config=self._config), self._attempt_id)
            moved: list[str] = []
            for rid, r in res.items():
                if r.state == STATE_RETAINED and rid in reconciled_ledger_ids:
                    self._cas_append("AttemptCreditReconciled", ("reconcile", rid), {"reservation_id": rid})
                    moved.append(rid)
            return moved
```

Commit `feat(025 slice-1A T9): AttemptCreditLedger.reconcile (retained→reconciled, idempotent)`.

---

### Task 10: `EventStoreRouteAudit.record` (durable-on-commit)

**Files:**
- Modify: `src/llmxive/self_improvement/lane_log.py` — `append` accepts `expected_revision: int | None = None`; `None` means an **unconditional append** (no revision precondition — just the ref-CAS + idempotency), for audit events that carry no revision precondition. (One-line change to `_predicate`: skip the length check when `expected_revision is None`.)
- Create: `src/llmxive/self_improvement/audit_sink.py`
- Test: `tests/integration/test_self_improvement_audit_sink.py`

**Interfaces:**
- Consumes: the slice-0 audit dataclasses (`from llmxive.model_selection.attempt_hooks import ...`), `ModelRef`, `SnapshotProvenance`; `append`, `read`, `LaneRevisionConflict` (Task 3); `Event`, `derive_event_id` (Task 2).
- Produces:
  - `class EventStoreRouteAudit` implementing the slice-0 `RouteAudit`. Constructor `(*, repo, problem_id, attempt_id, actor, clock, config=LaneLogConfig())`.
  - `def record(self, event) -> None` — build the lane `Event` (`event_type = type(event).__name__`, `event_id = derive_event_id(problem_id, "audit\x00" + event.event_id)`, `payload = _audit_payload(event)`, and ALL revision fields left `None` — the store's `_finalize` stamps the real `expected_problem_revision`/`resulting_problem_revision` inside the CAS, F8), then `append(..., expected_revision=None)` in a bounded retry loop (on `LaneRevisionConflict` from a concurrent append, recompute + retry). **`append` only returns after the ref-CAS commit lands — that is the durability point (F8).** A conflicting payload under the same `event_id` raises `GitLogError`/append-only, which `emit_audit` in `execute` normalizes to route-fatal `RouteAuditError`.
  - `_audit_payload(event) -> dict` — JSON-safe projection (scalars verbatim; `ModelRef`→its 5 fields; `candidates`→list; `snapshot_provenance`→`{k: {source, observed_at, age_s}}`), plus `audit_event_id = event.event_id` for correlation.

**Why the ref-CAS, not O_EXCL (F8):** a bare local file that never reached the protected ref is NOT durable evidence — a later commit failure would orphan it, and a replay would treat the orphan as committed and (via `claim_dispatch`) return `False`, preventing a dispatch whose evidence never persisted. Routing `record`/`claim_dispatch` through `append_to_log` means the outcome is returned ONLY after the ref moved.

- [ ] **Steps:** Tests: `record` persists to the stream + is idempotent on a byte-identical replay; a conflicting payload under the same audit `event_id` → `emit_audit(sink, conflict)` raises `RouteAuditError`. RED → GREEN. Commit `feat(025 slice-1A T10): EventStoreRouteAudit.record (durable-on-commit via ref-CAS)`.

### Task 11: `EventStoreRouteAudit.claim_dispatch` (cross-process CAS boundary)

**Files:** Modify `audit_sink.py`; extend the test.

**Interfaces:**
- `def claim_dispatch(self, event: DispatchStarted) -> bool` — `append` the `DispatchStarted` (retry loop as in `record`) and return `AppendResult.created`: `True` = THIS call committed it (own the dispatch); `False` = a byte-identical `DispatchStarted` already committed (replay — MUST NOT re-dispatch); a conflicting payload raises. The ref-CAS makes exactly one claimant win **across processes** (not just threads) — strictly stronger than the O_EXCL boundary, and durable by construction.

- [ ] **Steps:** Tests: first claim `True`, byte-identical replay `False`; conflicting payload (different `reservation_id`) raises; **barrier-driven two-clone race** (F6): two clones of one bare remote both claiming the SAME `DispatchStarted`, synced to the same parent then released together by a `threading.Barrier` → exactly one gets `True` (the ref-CAS), the other `False`. RED → GREEN. Commit `feat(025 slice-1A T11): claim_dispatch cross-process CAS (durable, two-clone exactly-once)`.

### Task 12: `DispatchUnknown` reconciliation — atomic + conservative-timeout (F4, F5, F7)

**Files:** Modify `audit_sink.py`; extend the test.

**Scope (narrowed per F4):** Slice 1A records the durable **`DispatchUnknown` + `retained`** reconciliation state; it does NOT itself perform the Attempt-fail-closed lifecycle transition (that is Slice 1B). The one thing it DOES guarantee is that the unknown-mark and the reservation-retain are **atomic**: they are the SAME single event.

**Interfaces:**
- `def dangling_dispatches(events: list[Event], *, attempt_id: str, now: str, timeout_s: float) -> list[dict]` — a `DispatchStarted` is dangling ONLY if ALL hold (F7): its `attempt_id` matches; there is NO `DispatchCompleted` for its `(route_id, candidate_index)`; there is NO terminal `CandidateOutcome` (`outcome ∈ {advance, abort, skip}`) for it (a failed candidate is a KNOWN outcome, not unknown); there is NO existing `DispatchUnknown` for it; and its `timestamp` is older than `now - timeout_s`.
  **`timeout_s` is a CONSERVATIVE TIMEOUT, NOT proof the owner is dead (F5).** It is bounded by the real worst-case call envelope — `options.deadline_s × (retries + 1)` plus a margin — so a still-running valid call is never marked before it could possibly have finished. It is honestly a timeout, not liveness. A stronger durable-liveness mechanism (an owner/run id + a durable lease-expiry or run-terminal event on `DispatchStarted`) requires adding fields to the slice-0 `DispatchStarted` — a protected-surface change out of Slice 1A's scope — and is noted for a later slice; until then, reconciliation is a conservative timeout by design.
- `def reconcile_unknown(repo, *, problem_id, attempt_id, actor, clock, now, timeout_s, config=LaneLogConfig()) -> list[str]` — for each dangling dispatch, append **ONE `DispatchUnknown` event** (carrying its `route_id`/`candidate_index`/`candidate`/`reservation_id`) via `record`. That single durable event drives BOTH projections atomically (F4): the audit projection sees the dispatch resolved as `DispatchUnknown`, and `project_reservations` (Task 6) transitions the reservation `open → retained`. There is no separate `mark_retained` call, so no crash window between two writes. Returns the reconciled `route_id`s. Idempotent (a byte-identical `DispatchUnknown` re-append is a no-op; a second run finds nothing dangling).

- [ ] **Steps:** Tests: a `DispatchStarted` past the timeout with no completion/terminal-outcome → one `DispatchUnknown` recorded AND `project_reservations` shows the reservation `retained` (assert BOTH from the single event); a `DispatchStarted` WITHIN the timeout → not marked; a `DispatchStarted` + `CandidateOutcome("advance")` → not unknown (known failure); a `DispatchStarted` + `DispatchCompleted` → not unknown; a dispatch under a DIFFERENT `attempt_id` → untouched; a **crash-safety** test: since the retain rides on the same event, there is no state where `DispatchUnknown` exists without `retained` (assert the projection invariant on a stream containing the single event); idempotent on re-run. RED → GREEN. Commit `feat(025 slice-1A T12): atomic DispatchUnknown reconciliation (single event drives unknown+retained; conservative timeout)`.

---

## Final verification (before the whole-branch review)

- [ ] Package exports (`src/llmxive/self_improvement/__init__.py`): `Event`, `derive_event_id`, `validate_lane_event`, `LANE_REF`, `append`, `read`, `LaneRevisionConflict`, `LaneCoordinator`, `project_coordinator`, `cas_claim`, `cas_release`, `AttemptCreditLedger`, `EventStoreRouteAudit`, `reconcile_unknown`. Test they import.
- [ ] **Money-path gate re-run, no edits** (the Task-1 acceptance bar, re-confirmed after all substrate work): the seven files in Global Constraints pass with the Step-1 baseline counts.
- [ ] `ruff check` clean on every touched file.
- [ ] Full non-slow suite green: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → 0 failed (network-restricted-sandbox artifacts itemized).
- [ ] `enforcement.py` guard passes: no model-id literal in lane code.
- [ ] Commit discipline honored (`PRE_COMMIT_ALLOW_NO_CONFIG=1`, trailer, HEAD moved); **nothing pushed**.

## Findings-to-tasks traceability

**Round 1 (structural) — resolved:** genuine ref-CAS (T1/T3), 1A/1B split, ownership-checked release (T5), seq ordering (T1/T3), audit durability tied to committed ref state (T10/T11), attempt-scoped/terminal-aware DispatchUnknown (T12), multi-clone tests; convergence wiring (reservation authority, mandatory audit, reviser, InvocationIdentity, real `run_convergence`) assigned to **Slice 1B**.

**Round 2 (schema + recovery refinements):**

| # | Finding | Resolved by |
|-|-|-|
| 1 | FR-011 resulting fields + off-by-one | T2 `Event` carries all 4 revision anchors; the core (T1 `finalize`) stamps `expected==seq`, `resulting==seq+1` inside the CAS; `validate_lane_event` enforces it; audit events get REAL revisions, no placeholder |
| 2 | timestamp idempotency (`ts` vs `timestamp`) | T3 uses the single FR-011 `timestamp` (no duplicate `ts`); `_IDENTITY_EXCLUDE` excludes `timestamp` |
| 3 | legal transitions unenforced | T4 coordinator + T6 reservation transition matrices; a stray/illegal transition RAISES (projections are the recovery authority); corruption tests both |
| 4 | reconciliation not atomic | T12 appends ONE `DispatchUnknown` event that drives both audit-unknown AND reservation-`retained` (via T6 projection) — no two-write window; contract narrowed (no Attempt-fail-closed in 1A) |
| 5 | elapsed time ≠ owner dead | T12 reframed as a **conservative timeout** (`deadline_s × (retries+1)` envelope), explicitly not liveness; durable owner-lease deferred (needs a slice-0 `DispatchStarted` field) |
| 6 | multi-clone test was sequential | T3/T7/T11 add **barrier-driven** concurrent races (sync same parent → barrier → concurrent ref-advance) |
| 7 | seq corruption not checked in-append | T3 `append` predicate validates seq continuity FIRST, inside every CAS attempt (fail closed) |
| 8 | exception compat under-specified | T1 makes `LedgerError`/`LedgerAuthError`/`LedgerContention`/`LedgerDenied` ALIASES of the core `GitLog*` (not subclasses) + `except`-still-catches tests |
| 9 | `KNOWN_EVENT_TYPES` not "full" | renamed `KNOWN_EVENT_TYPES_V1`; note requires later slices to bump `SCHEMA_VERSION` + extend the set AND projections together |
| 10 | cleanup | EOF fixed; no duplicate task headings (verified); the empty "unknown type" test removed; Tasks 6/8/9 fully inlined (no reference to deleted history) |

**Round 3 (blockers + storage/spec alignment):**

| # | Finding | Resolved by |
|-|-|-|
| 1 | Task 8 precondition inverted (could never append) | T8 `_cas_append` admits (already-landed) OR (reservation in the required source state), re-checked fresh in-CAS; **release-vs-retain race test** added |
| 2 | dedicated-ref design conflicted with the spec | **Spec 25 amended to rev 15** (FR-007/008/009 + header) to authorize the dedicated ref, its bootstrap/protection/fetch rules, and snapshots-as-projections; the plan cites it |
| 3 | lane ref had no bootstrap contract | T3 adds `bootstrap_lane_log` (genesis/idempotent/concurrent-safe/anchor-pin/fail-closed-until-bootstrapped) + bootstrap tests (empty remote, repeat, two concurrent, append-before-bootstrap-fails-closed) |
| 4 | remote anchor verification lost at the lane API | `LaneLogConfig(remote, expected_anchor)` threaded through bootstrap/read/append/coordinator/ledger/audit; anchor-pinning + wrong-anchor-fails-closed tests |
| 5 | `problem_id` persisted as `stream` | the persisted `Event` field is now `problem_id` (COORDINATOR_STREAM sentinel), per FR-011 |
| 6 | barrier tests didn't reach the real push race | core `_after_parent` TEST-ONLY seam; T3/T7/T11 barrier tests block both workers at the same fixed parent, then race the actual `update-ref`/FF-push |
| 7 | schema-version bump would break mixed history | `SUPPORTED_SCHEMA_VERSIONS` (reader never rejects prior-version events); a vocabulary extension needs no bump — only a record-SHAPE change adds a version + its validator |
| 8 | Task 10 still described placeholder revisions | audit events are built with ALL revision fields `None`; the store's `_finalize` stamps the real anchors inside the CAS |
| 9 | stale global-constraint summaries | idempotency excludes `seq`/`timestamp`/anchors (not "seq and ts"); the resulting revision is `seq + 1` (not `seq`) |
