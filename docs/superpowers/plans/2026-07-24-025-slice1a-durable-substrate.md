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
- **Deterministic idempotency (FR-009).** Each side-effecting operation derives a **deterministic `event_id`** from its semantics (never the revision). A retried or re-invoked identical operation re-derives the same `event_id`; the core returns idempotently (comparing the semantic payload, excluding the core-assigned `seq` and `ts`), never a duplicate and never a spurious append-only raise.
- **Ownership-checked coordinator transitions (FR-008).** A claim requires `active_problem_id is None` (idle) at the CAS. A release requires the current `active_problem_id`/`active_attempt_id` to EQUAL the releasing pair (a stale delayed release MUST NOT clear a newer claim); an already-idle coordinator is an idempotent success only when durable history proves this exact release already landed.
- **Event fields (FR-011).** Every event carries `event_id`, `event_type`, `problem_id` (or the coordinator-stream sentinel), optional `attempt_id`, the applicable `expected_lane_revision`/`expected_problem_revision` + `resulting_*_revision` (the resulting revision is the core-assigned `seq`), `timestamp`, `actor`, `payload`, `schema_version`, and `seq`. Validation enforces: known `event_type`; exactly one revision scope (coordinator XOR problem); a `schema_version` the reader supports; the on-disk path stream matches the serialized stream; a legal state transition. An unknown `event_type` is rejected on read (it must not silently advance a safety-critical projection).
- **AttemptCreditLedger states are exactly `{open, retained, reconciled, released}` (FR-033).** A reservation record is `{reservation_id, call_id, reserved_credits, state}` — the reserved worst-case envelope, **no exact-actual-cost field** (F3). Counting states (against the cap) = `{open, retained, reconciled}`; `released` (never dispatched) does not count. Saga rollbacks per FR-033(b): over-budget → refuse (skip); Attempt reserved but 026 refuses → `release`; both reserved but dispatch fails → both `retained`; a candidate that never dispatched → `released`, one that dispatched → `retained`.
- **ReservationAuthority collision semantics (slice-0 `attempt_hooks.ReservationAuthority.reserve`).** Repeated `reservation_id` + same `(credits, call_id)` → idempotent success, no double-count; same id + different identity → integrity raise; concurrent duplicates → exactly one durable reservation; an ordinary budget denial returns `False` (never raises).
- **RouteAudit is durable-on-commit and the claim is a real CAS (slice-0 `attempt_hooks.RouteAudit`; F8).** `record`/`claim_dispatch` return only AFTER the ref-CAS commit lands — a local file that never reached the ref is NOT durable evidence. `claim_dispatch(DispatchStarted) -> bool`: `True` = this call committed the event (own the dispatch); `False` = a byte-identical event already committed (replay, MUST NOT re-dispatch); a conflicting payload under the same `event_id` → raise. Exactly one claimant wins across processes (the ref-CAS).
- **DispatchUnknown reconciliation is conservative (FR-033a; F7).** A dispatch is "dangling" only if ALL hold: the event is in THIS attempt's stream; there is no `DispatchCompleted`; there is no terminal `CandidateOutcome` (`advance`/`abort`/`skip`) for it; there is no existing `DispatchUnknown`; and the dispatch's lease/owner is durably expired/dead (never mark an actively-executing call). Reconciling one atomically records `DispatchUnknown`, marks the matching Attempt reservation `retained`, and fails the Attempt closed — it is not left to an unspecified caller.
- **Route through the chokepoint; no model-id literals in lane code (SC-008, FR-001).** `model_selection/enforcement.py` verifies this. (Slice 1A adds no model ids.)
- **Real tests, no mocks (Constitution III).** Protocol test doubles with real logic, temp-git-repo fixtures, and **multi-clone concurrency tests** (two clones of one bare remote competing on the ref) are required where the guarantee is cross-process. `unittest.mock` is not the primary path.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push.**

## Scope boundary

This plan is **Slice 1A: the durable substrate only.** The proposal-review convergence wiring (threading `route_audit`/`reservation_authority` through the reviewer + reviser, the explicit reroute/degradation event, the complete `InvocationIdentity`, the `self_improvement_proposal` `ReviewSpec` + prompts, the real `run_convergence` integration test) is **Slice 1B**, a separate plan that consumes this substrate's `EventStoreRouteAudit` + `AttemptCreditLedger` interfaces. US1's discovery *logic* (error mining, issue ranking, proposer + deterministic pre-gates) is a further follow-up.

## File Structure

- `src/llmxive/git_event_log.py` — the extracted ref-agnostic git-CAS core: `LogRef`, `AppendResult`, `append_to_log`, `read_log`, `sync_and_verify`, `bootstrap_log`, `GitLogError`/`GitLogAuthError`/`GitLogContention`, and the moved git-plumbing helpers.
- `src/llmxive/model_selection/ledger_transport.py` — **rewired** to thin wrappers over the core (behavior unchanged); keeps the credit schema (`_validate_event`, the constants), `LedgerConfig`, `ledger_config_from_env`, `bootstrap_ledger`, `LedgerError`/… (subclassing the core's).
- `src/llmxive/self_improvement/events.py` — lane `Event` record (FR-011) + `validate_lane_event` + `derive_event_id` + JSON (de)serialization.
- `src/llmxive/self_improvement/lane_log.py` — the lane's store: `LANE_REF`, `lane_log_ref(stream)`, `append(repo, event, *, expected_revision, precondition) -> AppendResult`, `read(repo, stream) -> list[Event]` (seq-ordered), `LaneRevisionConflict`; thin wrappers over the core.
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
  - `append_to_log(repo, *, log: LogRef, validate: Callable[[dict], None], message_fn: Callable[[dict], str], event: dict | None = None, prepare: Callable[[list[dict]], dict | None] | None = None, predicate: Callable[[list[dict]], tuple[bool, str]] | None = None, seq_field: str | None = None, identity_exclude: frozenset[str] = frozenset(), max_retries: int = 8) -> AppendResult` — the current `append_event` seven-step CAS loop, ref-parameterized. New: when `seq_field` is set, after `parent` is fixed the core computes `seq = len(read_log(...))` at that parent, embeds `event[seq_field] = seq` BEFORE `validate`/commit, and returns it; the **append-only guard compares bodies with `identity_exclude ∪ ({seq_field} if set)` fields removed from both sides** so a semantic retry (different `seq`/`ts`) returns idempotently (`created=False`, `seq` = the committed event's seq); a genuinely different semantic body still raises `GitLogError`. When `seq_field is None` and `identity_exclude` is empty, the guard compares the full body — **byte-for-byte as today**.
  - `read_log(repo, *, log: LogRef, validate: Callable[[dict], None]) -> list[dict]` — the current `read_events` loop, `event_dir`/`validate` parameterized.
  - `sync_and_verify(repo, *, log: LogRef) -> None`, `bootstrap_log(repo, *, log: LogRef, message: str, remote: str | None = None) -> str` — ref-parameterized `_sync_and_verify`/`bootstrap_ledger`.
  - `class GitLogError(RuntimeError)`, `class GitLogAuthError(GitLogError)`, `class GitLogContention(GitLogError)`; moved helpers `_git`, `_rev`, `_canonical`, `_read_event_blob`, `_append_commit`, `_fetch_authoritative`, `_remote_ledger_oid`, `_is_ancestor`, `_push_fast_forward`, `sync_and_verify`, and the marker/id constants (`_AUTH_FAIL_MARKERS`, `_NON_FF_MARKERS`, `_PUSH_DENY_MARKERS`, `_ZERO_OID`, `_SAFE_ID`, `_DEFAULT_GIT_IDENTITY`) — each gaining a `ref`/`event_dir`/`message_fn` parameter in place of the module global it closed over. See the extraction blueprint (`.superpowers`/scratch `extraction-design.md`) for the exact verbatim bodies and the generic/credit-specific split.
- `ledger_transport.py` keeps `LEDGER_REF`, `SCHEMA_REVISION`, `_EVENT_DIR`, `_validate_event` + its four schema constants, `LedgerConfig`, `ledger_config_from_env`, `bootstrap_ledger`, `fetch_ledger`; `LedgerError`/`LedgerAuthError`/`LedgerContention` become subclasses of (or aliases to) the core's `GitLog*`; `LedgerDenied` stays credit-specific. `append_event`/`read_events` become thin wrappers passing `LEDGER_REF`/`_EVENT_DIR`/`_validate_event`/`_message_fn`, `seq_field=None`, `identity_exclude=frozenset()`, and returning `AppendResult.commit`.

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
                         seq_field="seq", identity_exclude=frozenset({"seq", "ts"}))


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

Perform the mechanical move per the blueprint: create `git_event_log.py` with the generic helpers + the three new features (`seq`/`created`/`identity_exclude`), and rewire `ledger_transport.append_event`/`read_events` as thin wrappers. The credit wrapper (`seq_field=None`, `identity_exclude=frozenset()`, returns `.commit`) must produce byte-identical git artifacts. Key wrapper shape (from the blueprint):

```python
# ledger_transport.py (rewired)
from llmxive.git_event_log import AppendResult, LogRef, append_to_log, read_log

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
                         event=event, prepare=prepare, predicate=predicate, max_retries=max_retries).commit
```

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
  - `KNOWN_EVENT_TYPES: frozenset[str]` — the lane's full event-type vocabulary (coordinator: `ClaimAcquired`, `ClaimReleased`, `MonitorStarted`, `PromotionEnabledSet`; credit: `AttemptCreditReserved`/`Released`/`Retained`/`Reconciled`; audit: `ChainResolved`, `SelectionFailure`, `ReservationOpened`, `DispatchStarted`, `DispatchCompleted`, `DispatchUnknown`, `CandidateOutcome`; lifecycle: `ProblemDiscovered`, `Proposed`, `ProposalVerified`, `Rejected`). An event type outside this set is rejected on read.
  - `@dataclass(frozen=True) class Event` (FR-011): `event_id`, `event_type`, `stream` (a `problem_id` or `COORDINATOR_STREAM`), `actor`, `payload: Mapping`, `timestamp`, `schema_version=SCHEMA_VERSION`, `attempt_id: str | None = None`, `expected_lane_revision: int | None = None`, `expected_problem_revision: int | None = None`, `seq: int | None = None` (assigned by the store's CAS; `None` before append).
  - `derive_event_id(stream, idempotency_key) -> str` — `sha256(f"{stream}\x00{idempotency_key}")`.
  - `validate_lane_event(raw: dict) -> None` — fail-closed schema (F9): required fields present; `event_type ∈ KNOWN_EVENT_TYPES`; `schema_version == SCHEMA_VERSION`; **exactly one** of `expected_lane_revision`/`expected_problem_revision` is set (coordinator XOR problem scope), and it matches the stream kind (coordinator events carry `expected_lane_revision`, problem events carry `expected_problem_revision`); `event_id` is a safe path segment; `timestamp` parses ISO-8601. Raises `ValueError`.
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
    base = {"event_id": "e1", "event_type": "ProblemDiscovered", "stream": "prob-1", "actor": "disc",
            "payload": {}, "timestamp": "2026-07-24T00:00:00+00:00", "schema_version": SCHEMA_VERSION,
            "attempt_id": None, "expected_lane_revision": None, "expected_problem_revision": 0, "seq": 0}
    base.update(kw)
    return base


def test_event_id_deterministic_and_scoped():
    a = derive_event_id("prob-1", "discover")
    assert a == derive_event_id("prob-1", "discover") != derive_event_id("prob-2", "discover")


def test_round_trip_and_seq_assignment():
    e = event_from_json(event_to_json(Event(**{k: v for k, v in _raw().items()})))
    assert e.seq == 0 and e.schema_version == SCHEMA_VERSION


def test_validate_rejects_unknown_type():
    with pytest.raises(ValueError, match="event_type"):
        validate_lane_event(_raw(event_type="TotallyMadeUp"))


def test_validate_rejects_both_revision_scopes():
    with pytest.raises(ValueError, match="exactly one"):
        validate_lane_event(_raw(expected_lane_revision=0, expected_problem_revision=0))


def test_validate_rejects_wrong_scope_for_stream():
    # a coordinator-stream event must carry expected_lane_revision, not expected_problem_revision
    with pytest.raises(ValueError, match="scope"):
        validate_lane_event(_raw(stream=COORDINATOR_STREAM, expected_lane_revision=None,
                                 expected_problem_revision=0))


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
SCHEMA_VERSION = 1
SEQ_FIELD = "seq"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")

KNOWN_EVENT_TYPES = frozenset({
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
    stream: str
    actor: str
    payload: Mapping[str, Any]
    timestamp: str
    schema_version: int = SCHEMA_VERSION
    attempt_id: str | None = None
    expected_lane_revision: int | None = None
    expected_problem_revision: int | None = None
    seq: int | None = None


def derive_event_id(stream: str, idempotency_key: str) -> str:
    return hashlib.sha256(f"{stream}\x00{idempotency_key}".encode()).hexdigest()


def _as_dict(e: Event) -> dict[str, Any]:
    return {"event_id": e.event_id, "event_type": e.event_type, "stream": e.stream, "actor": e.actor,
            "payload": dict(e.payload), "timestamp": e.timestamp, "schema_version": e.schema_version,
            "attempt_id": e.attempt_id, "expected_lane_revision": e.expected_lane_revision,
            "expected_problem_revision": e.expected_problem_revision, "seq": e.seq}


def validate_lane_event(raw: dict) -> None:
    for key in ("event_id", "event_type", "stream", "actor", "payload", "timestamp", "schema_version"):
        if key not in raw:
            raise ValueError(f"lane event missing required field {key!r}")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"lane event schema_version {raw['schema_version']!r} != {SCHEMA_VERSION}")
    if raw["event_type"] not in KNOWN_EVENT_TYPES:
        raise ValueError(f"lane event_type {raw['event_type']!r} not in KNOWN_EVENT_TYPES")
    if not _SAFE_ID.match(str(raw["event_id"])):
        raise ValueError(f"lane event_id {raw['event_id']!r} must match {_SAFE_ID.pattern}")
    lane_rev, prob_rev = raw.get("expected_lane_revision"), raw.get("expected_problem_revision")
    if (lane_rev is None) == (prob_rev is None):
        raise ValueError("lane event must set exactly one of expected_lane_revision/expected_problem_revision")
    is_coord = raw["stream"] == COORDINATOR_STREAM
    if is_coord and lane_rev is None:
        raise ValueError("coordinator-stream event carries the wrong revision scope (needs expected_lane_revision)")
    if not is_coord and prob_rev is None:
        raise ValueError("problem-stream event carries the wrong revision scope (needs expected_problem_revision)")
    try:
        datetime.fromisoformat(str(raw["timestamp"]))
    except ValueError as exc:
        raise ValueError(f"lane event timestamp {raw['timestamp']!r} is not ISO-8601") from exc


def event_to_json(event: Event) -> str:
    return json.dumps(_as_dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def event_from_json(text: str) -> Event:
    d = json.loads(text)
    return Event(event_id=d["event_id"], event_type=d["event_type"], stream=d["stream"], actor=d["actor"],
                 payload=d["payload"], timestamp=d["timestamp"], schema_version=d["schema_version"],
                 attempt_id=d.get("attempt_id"), expected_lane_revision=d.get("expected_lane_revision"),
                 expected_problem_revision=d.get("expected_problem_revision"), seq=d.get("seq"))
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
  - `LANE_REF = "refs/llmxive/self-improvement"`; `lane_log_ref(stream, *, remote=None, expected_anchor=None) -> LogRef` with `event_dir = f"self-improvement/{stream}"` (per-stream subtree → per-stream `seq`; all streams share the ONE ref so lane mutations serialize globally on it, giving the coordinator its singleton and each Problem its own revision line).
  - `class LaneRevisionConflict(RuntimeError)` — the caller's `expected_revision`/precondition lost; recompute (FR-008).
  - `read(repo, stream, *, remote=None) -> list[Event]` — `read_log` mapped to `Event`s, **ordered by `seq`** (validate continuity: `[e.seq for e]` == `range(len)`; a gap/dup/fork raises `LaneRevisionConflict("corrupt sequence")`).
  - `append(repo, event: Event, *, expected_revision: int, precondition: Callable[[list[Event]], tuple[bool, str]] | None = None, remote=None) -> AppendResult` — wraps `append_to_log` with the lane `LogRef`, `validate=validate_lane_event`, `seq_field=SEQ_FIELD`, `identity_exclude=frozenset({"seq", "ts"})`, and a `predicate` that (per CAS attempt, against freshly-read events) checks `len(events) == expected_revision` AND `precondition(events)`; a predicate failure surfaces as `LaneRevisionConflict`. The event's on-disk `ts` is set from `event.timestamp`. Returns the `AppendResult` (with the authoritative `seq`).

- [ ] **Step 1: Write the failing test** (including the cross-process guarantee)

```python
# tests/integration/test_self_improvement_lane_log.py
import subprocess

import pytest

from llmxive.self_improvement.events import Event
from llmxive.self_improvement.lane_log import LaneRevisionConflict, append, read


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


def _ev(eid, rev, stream="prob-1"):
    return Event(event_id=eid, event_type="Proposed", stream=stream, actor="a", payload={},
                 timestamp=f"2026-07-24T00:00:{rev:02d}+00:00", attempt_id="A1", expected_problem_revision=rev)


def test_append_assigns_seq_and_reads_ordered(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c1")
    assert append(c, _ev("e0", 0), expected_revision=0, remote="origin").seq == 0
    assert append(c, _ev("e1", 1), expected_revision=1, remote="origin").seq == 1
    assert [e.seq for e in read(c, "prob-1")] == [0, 1]


def test_stale_revision_loses(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c1")
    append(c, _ev("e0", 0), expected_revision=0, remote="origin")
    with pytest.raises(LaneRevisionConflict):
        append(c, _ev("e1", 0), expected_revision=0, remote="origin")  # actual rev is 1


def test_two_clones_competing_on_one_ref_exactly_one_wins(tmp_path, bare_remote):
    # THE cross-process guarantee (FR-008): two independent clones both at revision 0
    # push different events to the SAME ref; the FF-push CAS admits exactly one, the
    # other must refetch + recompute (its expected_revision no longer holds).
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    r1 = append(c1, _ev("from-c1", 0), expected_revision=0, remote="origin")
    assert r1.seq == 0
    # c2 still thinks revision is 0 (hasn't fetched) → its CAS must lose, not merge.
    with pytest.raises(LaneRevisionConflict):
        append(c2, _ev("from-c2", 0), expected_revision=0, remote="origin")
    # after recomputing (fetch + rebuild), c2 appends at the true revision 1.
    assert append(c2, _ev("from-c2", 1), expected_revision=1, remote="origin").seq == 1
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/integration/test_self_improvement_lane_log.py -q` → FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/lane_log.py
"""The lane's append-only store: thin wrappers over the shared git_event_log CAS core
on a dedicated lane ref. Per-stream subtrees give each Problem (and the coordinator) an
authoritative, gap-checked ``seq`` line; the single ref serializes all lane mutations
(FR-008)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from llmxive.git_event_log import AppendResult, GitLogError, LogRef, append_to_log, read_log
from llmxive.self_improvement.events import (
    SEQ_FIELD, Event, event_from_json, event_to_json, validate_lane_event,
)

LANE_REF = "refs/llmxive/self-improvement"
#: Fields excluded from the append-only IDENTITY comparison (F5): the store-assigned
#: ``seq``, the wall-clock ``ts``, and the CAS revision ANCHORS — none is part of an
#: operation's semantic identity, so a re-invoked operation whose event lands at a
#: DIFFERENT revision is still an idempotent no-op, not a spurious append-only raise.
_IDENTITY_EXCLUDE = frozenset({
    SEQ_FIELD, "ts", "expected_lane_revision", "expected_problem_revision",
})


class LaneRevisionConflict(RuntimeError):
    """The CAS precondition (expected_revision or a caller precondition) no longer holds
    against the authoritative tip — recompute and retry/yield (FR-008); never force."""


def lane_log_ref(stream: str, *, remote: str | None = None, expected_anchor: str | None = None) -> LogRef:
    return LogRef(ref=LANE_REF, event_dir=f"self-improvement/{stream}", remote=remote,
                  expected_anchor=expected_anchor)


def _message(event: dict) -> str:
    return f"self-improvement: {event.get('event_type', '?')} {event['event_id']}"


def read(repo: Path, stream: str, *, remote: str | None = None) -> list[Event]:
    raw = read_log(repo, log=lane_log_ref(stream, remote=remote), validate=validate_lane_event)
    events = [event_from_json(_to_json(r)) for r in raw]
    events.sort(key=lambda e: e.seq if e.seq is not None else -1)
    if [e.seq for e in events] != list(range(len(events))):
        raise LaneRevisionConflict(f"corrupt sequence in stream {stream!r}: {[e.seq for e in events]}")
    return events


def _to_json(raw: dict) -> str:
    import json
    return json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append(repo: Path, event: Event, *, expected_revision: int,
           precondition: Callable[[list[Event]], tuple[bool, str]] | None = None,
           remote: str | None = None) -> AppendResult:
    log = lane_log_ref(event.stream, remote=remote)
    raw = _event_raw(event)

    def _predicate(existing: list[dict]) -> tuple[bool, str]:
        evs = [event_from_json(_to_json(r)) for r in existing]
        if len(evs) != expected_revision:
            return (False, f"stale revision: expected {expected_revision}, actual {len(evs)}")
        if precondition is not None:
            return precondition(evs)
        return (True, "")

    try:
        return append_to_log(
            repo, log=log, validate=validate_lane_event, message_fn=_message, event=raw,
            predicate=_predicate, seq_field=SEQ_FIELD, identity_exclude=_IDENTITY_EXCLUDE,
        )
    except GitLogError as exc:
        # A predicate rejection is surfaced by the core as a denial → the lane's conflict.
        if "stale revision" in str(exc) or "precondition" in str(exc).lower():
            raise LaneRevisionConflict(str(exc)) from exc
        raise


def _event_raw(event: Event) -> dict:
    import json
    raw = json.loads(event_to_json(event))
    raw.setdefault("ts", event.timestamp)  # the core stamps ts if absent; keep it deterministic
    return raw
```

(Note: confirm how the core surfaces a `predicate`-false result during implementation — if `append_to_log` raises a dedicated `GitLogDenied`, catch that directly instead of string-matching. Add `GitLogDenied` to the core in Task 1 if cleaner; the credit `LedgerDenied` can subclass it.)

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
    return Event(event_id=eid, event_type=etype, stream=COORDINATOR_STREAM, actor="coord",
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


def test_unknown_type_fails_closed():
    with pytest.raises(ValueError, match="unknown"):
        project_coordinator([_ev("e1", "MonitorStarted", {"attempt_id": "A1"}, 0),
                             Event(event_id="x", event_type="ClaimAcquired", stream=COORDINATOR_STREAM,
                                   actor="c", payload={"problem_id": "P", "attempt_id": "A"},
                                   timestamp="2026-07-24T00:00:00+00:00", expected_lane_revision=1, seq=1)])
    # (the assertion targets a genuinely-unknown type; see the fail-closed test below)


def test_projection_rejects_unknown_event_type():
    bad = Event(event_id="x", event_type="SomethingFromTheFuture", stream=COORDINATOR_STREAM, actor="c",
                payload={}, timestamp="2026-07-24T00:00:00+00:00", expected_lane_revision=0, seq=0)
    with pytest.raises(ValueError, match="unknown coordinator event"):
        project_coordinator([bad])
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
    c = EMPTY_COORDINATOR
    for e in events:
        if e.event_type not in _COORDINATOR_TYPES:
            raise ValueError(f"unknown coordinator event {e.event_type!r} — fail closed")
        p = e.payload
        if e.event_type == "ClaimAcquired":
            c = replace(c, active_problem_id=p["problem_id"], active_attempt_id=p["attempt_id"])
        elif e.event_type == "ClaimReleased":
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
  - `cas_claim(repo, *, problem_id, attempt_id, actor, timestamp, remote=None) -> LaneCoordinator` — reads the coordinator stream; builds a `ClaimAcquired` event (idempotency key `("claim", problem_id, attempt_id)`, `expected_lane_revision = current.lane_revision`); appends with a precondition that admits the claim iff **the claim already landed (idempotent) OR the lane is idle** (`active_problem_id is None`). Raises `LaneRevisionConflict` when the lane is occupied by a different Problem or the revision moved. Returns the new projection.
  - `cas_release(repo, *, problem_id, attempt_id, actor, timestamp, remote=None) -> LaneCoordinator` — appends `ClaimReleased` (idempotency key `("release", problem_id, attempt_id)`) with an **ownership precondition** (F6): admit iff **this exact release already landed (idempotent) OR the current active pair equals `(problem_id, attempt_id)`**. A delayed release from an old `(P1,A1)` MUST NOT clear a newer `(P2,A2)` claim → it fails the precondition → `LaneRevisionConflict`.

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
from llmxive.self_improvement.lane_log import append, read


def _coord_event(event_type, idem, payload, actor, timestamp, expected_rev):
    return Event(
        event_id=derive_event_id(COORDINATOR_STREAM, "\x00".join(idem)), event_type=event_type,
        stream=COORDINATOR_STREAM, actor=actor, payload=payload, timestamp=timestamp,
        expected_lane_revision=expected_rev,
    )


def cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str,
              remote: str | None = None) -> LaneCoordinator:
    events = read(repo, COORDINATOR_STREAM, remote=remote)
    event = _coord_event("ClaimAcquired", ("claim", problem_id, attempt_id),
                         {"problem_id": problem_id, "attempt_id": attempt_id},
                         actor, timestamp, project_coordinator(events).lane_revision)

    def _idle_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if any(e.event_id == event.event_id for e in evs):
            return (True, "")  # this exact claim already landed → idempotent
        pid = project_coordinator(evs).active_problem_id
        return (pid is None, "" if pid is None else f"lane occupied by {pid!r}")

    append(repo, event, expected_revision=project_coordinator(events).lane_revision,
           precondition=_idle_or_landed, remote=remote)
    return project_coordinator(read(repo, COORDINATOR_STREAM, remote=remote))


def cas_release(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str,
                remote: str | None = None) -> LaneCoordinator:
    events = read(repo, COORDINATOR_STREAM, remote=remote)
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
           precondition=_owns_or_landed, remote=remote)
    return project_coordinator(read(repo, COORDINATOR_STREAM, remote=remote))
```

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/integration/test_self_improvement_coordinator_cas.py -q` → PASS (4 passed, incl. the stale-release regression).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/coordinator.py tests/integration/test_self_improvement_coordinator_cas.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T5): ownership-checked coordinator CAS (F6 stale-release guard, F5 idempotent)"
```

---

### Task 6: `AttemptCreditLedger` reservation projection

**Files:**
- Create: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/unit/test_self_improvement_credit_projection.py`

**Interfaces:**
- Produces: `STATE_OPEN`/`STATE_RETAINED`/`STATE_RECONCILED`/`STATE_RELEASED`; `COUNTING_STATES = {open, retained, reconciled}`; `@dataclass(frozen=True) class AttemptReservation(reservation_id, call_id, reserved_credits, state)`; `RESERVATION_EVENT_STATE` map; `project_reservations(events, attempt_id) -> dict[str, AttemptReservation]` (fold events with matching `attempt_id` — `AttemptCreditReserved` seeds, later events advance `state`; a stray transition for an unknown id is ignored — but because events are now **seq-ordered by the store**, a `Reserved` always precedes its transitions, so the ordering bug is gone); `counting_total(reservations) -> float`. (Identical shape to the prior slice-1 design; the difference is the caller feeds `read(...)` output, which is seq-ordered.)

- [ ] **Step 1-5:** same structure as the standard projection test/impl (reserve→retain→reconcile advances state; released excluded from `counting_total`; attempt-scoped). Since `read()` guarantees seq order, add a test that a `Retained` event appearing at a LOWER seq than its `Reserved` is impossible through the store (the store's continuity check rejects it) — i.e. assert `project_reservations` is fed already-ordered input and document the invariant. Commit `feat(025 slice-1A T6): AttemptCreditLedger reservation projection`.

(Full test/impl bodies are the same as the reservation projection in the prior single-plan draft — `project_reservations`/`counting_total` over `AttemptCredit*` events — with NO timestamp sorting, relying on the store's seq order.)

### Task 7: `AttemptCreditLedger.reserve` (in-process lock + budget CAS + collision)

**Files:**
- Modify: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/integration/test_self_improvement_credit_ledger.py` (incl. a `ThreadPoolExecutor` panel test AND a two-clone over-budget test)

**Interfaces:**
- Produces: `class AttemptCreditLedger` implementing the slice-0 `ReservationAuthority`. Constructor `(*, repo, problem_id, attempt_id, attempt_budget_credits, actor, clock, remote=None)`; holds a `threading.Lock`. `reserve(credits, *, reservation_id, call_id) -> bool` — under the lock, a bounded retry loop: project the Attempt's reservations from `read(problem_id)`; same `(credits, call_id)` under an existing id → `True` (idempotent); different identity → `raise ValueError` (integrity); `counting_total + credits > budget` → `False`; else `append` an `AttemptCreditReserved` event (`expected_revision = len(read)`) with a precondition re-checking the budget against fresh events (so a **cross-clone** competitor that consumed the budget flips this to `False` on recompute); on `LaneRevisionConflict` retry; after the cap `raise LaneContention`. The in-process `Lock` makes the concurrent PANEL (one process, one shared ledger instance) atomic (US1 scenario 5); the ref-CAS + budget-recheck precondition makes CROSS-clone reservers safe.
- Produces: `class LaneContention(RuntimeError)`.

- [ ] **Steps:** Tests: (1) within-budget True / over-budget False / at-budget True; (2) idempotent same identity; (3) conflicting identity raises; (4) `ThreadPoolExecutor(2)` sharing one ledger, budget admits one → exactly one `True`; (5) **two clones** of one bare remote both reserving the last credits → the ref-CAS + budget-recheck admits at most the remaining budget (the loser recomputes and returns `False`, never both `True`). RED (`ImportError`) → GREEN. Commit `feat(025 slice-1A T7): AttemptCreditLedger.reserve — lock + ref-CAS budget guard + collision`.

The reserve body (append-with-budget-precondition + retry):

```python
    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        with self._lock:
            for _ in range(_MAX_RETRIES):
                events = read(self._repo, self._stream, remote=self._remote)
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
                           precondition=_budget_ok, remote=self._remote)
                    return True
                except LaneRevisionConflict:
                    continue
            raise LaneContention(f"reserve CAS did not converge for {reservation_id!r}")
```

(The precondition receives already-typed `Event`s from `lane_log.append`'s wrapper — the `[event_from_json_or_pass(e) ...]` shim is illustrative; `append`'s `precondition` signature is `Callable[[list[Event]], tuple[bool,str]]`, so the body just calls `project_reservations(evs, self._attempt_id)` directly. Match the exact `precondition` type from Task 3.)

### Task 8: `release` / `mark_retained`; Task 9: `reconcile`

**Files:** Modify `credit_ledger.py`; extend the integration test.

- `release(reservation_id)` — under the lock: only `open → released` (a dispatched reservation is never released; already-`retained`/`reconciled`/absent → no-op). `mark_retained(reservation_id)` — only `open → retained`. `reconcile(reconciled_ledger_ids: set[str]) -> list[str]` — `retained → reconciled` for ids in the set. All three append via the store (`_cas_append` with an already-landed-idempotent precondition), idempotent, states exactly `{open, retained, reconciled, released}`. Tests: release frees budget / retain keeps it; `mark_retained` then `release` is a no-op (dispatched never released, FR-033); reconcile moves only listed retained ids; all idempotent. Commit T8, then T9 separately.

---

### Task 10: `EventStoreRouteAudit.record` (durable-on-commit)

**Files:**
- Modify: `src/llmxive/self_improvement/lane_log.py` — `append` accepts `expected_revision: int | None = None`; `None` means an **unconditional append** (no revision precondition — just the ref-CAS + idempotency), for audit events that carry no revision precondition. (One-line change to `_predicate`: skip the length check when `expected_revision is None`.)
- Create: `src/llmxive/self_improvement/audit_sink.py`
- Test: `tests/integration/test_self_improvement_audit_sink.py`

**Interfaces:**
- Consumes: the slice-0 audit dataclasses (`from llmxive.model_selection.attempt_hooks import ...`), `ModelRef`, `SnapshotProvenance`; `append`, `read`, `LaneRevisionConflict` (Task 3); `Event`, `derive_event_id` (Task 2).
- Produces:
  - `class EventStoreRouteAudit` implementing the slice-0 `RouteAudit`. Constructor `(*, repo, problem_id, attempt_id, actor, clock, remote=None)`.
  - `def record(self, event) -> None` — build the lane `Event` (`event_type = type(event).__name__`, `event_id = derive_event_id(problem_id, "audit\x00" + event.event_id)`, `payload = _audit_payload(event)`, `expected_problem_revision` set to a placeholder that `append(expected_revision=None)` ignores), then `append(..., expected_revision=None)` in a bounded retry loop (on `LaneRevisionConflict` from a concurrent append, recompute + retry). **`append` only returns after the ref-CAS commit lands — that is the durability point (F8).** A conflicting payload under the same `event_id` raises `GitLogError`/append-only, which `emit_audit` in `execute` normalizes to route-fatal `RouteAuditError`.
  - `_audit_payload(event) -> dict` — JSON-safe projection (scalars verbatim; `ModelRef`→its 5 fields; `candidates`→list; `snapshot_provenance`→`{k: {source, observed_at, age_s}}`), plus `audit_event_id = event.event_id` for correlation.

**Why the ref-CAS, not O_EXCL (F8):** a bare local file that never reached the protected ref is NOT durable evidence — a later commit failure would orphan it, and a replay would treat the orphan as committed and (via `claim_dispatch`) return `False`, preventing a dispatch whose evidence never persisted. Routing `record`/`claim_dispatch` through `append_to_log` means the outcome is returned ONLY after the ref moved.

- [ ] **Steps:** Tests: `record` persists to the stream + is idempotent on a byte-identical replay; a conflicting payload under the same audit `event_id` → `emit_audit(sink, conflict)` raises `RouteAuditError`. RED → GREEN. Commit `feat(025 slice-1A T10): EventStoreRouteAudit.record (durable-on-commit via ref-CAS)`.

### Task 11: `EventStoreRouteAudit.claim_dispatch` (cross-process CAS boundary)

**Files:** Modify `audit_sink.py`; extend the test.

**Interfaces:**
- `def claim_dispatch(self, event: DispatchStarted) -> bool` — `append` the `DispatchStarted` (retry loop as in `record`) and return `AppendResult.created`: `True` = THIS call committed it (own the dispatch); `False` = a byte-identical `DispatchStarted` already committed (replay — MUST NOT re-dispatch); a conflicting payload raises. The ref-CAS makes exactly one claimant win **across processes** (not just threads) — strictly stronger than the O_EXCL boundary, and durable by construction.

- [ ] **Steps:** Tests: first claim `True`, byte-identical replay `False`; conflicting payload (different `reservation_id`) raises; **two clones** of one bare remote both claiming the SAME `DispatchStarted` → exactly one gets `True` (the ref-CAS), the other `False`. RED → GREEN. Commit `feat(025 slice-1A T11): claim_dispatch cross-process CAS (durable, two-clone exactly-once)`.

### Task 12: Conservative `DispatchUnknown` reconciliation (F7)

**Files:** Modify `audit_sink.py`; extend the test.

**Interfaces:**
- `def dangling_dispatches(events: list[Event], *, attempt_id: str, now: str, grace_s: float) -> list[dict]` — a `DispatchStarted` is dangling ONLY if ALL hold (F7): its `attempt_id` matches; there is NO `DispatchCompleted` for its `(route_id, candidate_index)`; there is NO terminal `CandidateOutcome` (`outcome ∈ {advance, abort, skip}`) for it (a failed candidate is a KNOWN outcome, not unknown); there is NO existing `DispatchUnknown` for it; and its `timestamp` is older than `now - grace_s` (the lease/liveness proxy — never mark an actively-executing call). `grace_s` defaults to a generous max-call duration.
- `def reconcile_unknown(repo, *, problem_id, attempt_id, actor, clock, now, grace_s, ledger: "AttemptCreditLedger | None" = None) -> list[str]` — for each dangling dispatch: `record` a `DispatchUnknown` AND (if `ledger`) `ledger.mark_retained(reservation_id)` — the reservation is `retained` (reconciliation-pending), never released; the Attempt then fails closed (the lifecycle transition is a later slice, but the durable retained+unknown state is written here, atomically per dispatch). Returns the reconciled `route_id`s. Idempotent.

- [ ] **Steps:** Tests: a `DispatchStarted` past the grace window with no completion/terminal-outcome → `DispatchUnknown` recorded + reservation `retained`; a `DispatchStarted` WITHIN the grace window → NOT marked (still executing); a `DispatchStarted` followed by `CandidateOutcome("advance")` → NOT unknown (known failure); a `DispatchStarted` + `DispatchCompleted` → NOT unknown; a dispatch under a DIFFERENT `attempt_id` → not touched; idempotent on re-run. RED → GREEN. Commit `feat(025 slice-1A T12): conservative DispatchUnknown reconciliation (F7 lease/terminal/attempt-scoped)`.

---

## Final verification (before the whole-branch review)

- [ ] Package exports (`src/llmxive/self_improvement/__init__.py`): `Event`, `derive_event_id`, `validate_lane_event`, `LANE_REF`, `append`, `read`, `LaneRevisionConflict`, `LaneCoordinator`, `project_coordinator`, `cas_claim`, `cas_release`, `AttemptCreditLedger`, `EventStoreRouteAudit`, `reconcile_unknown`. Test they import.
- [ ] **Money-path gate re-run, no edits** (the Task-1 acceptance bar, re-confirmed after all substrate work): the seven files in Global Constraints pass with the Step-1 baseline counts.
- [ ] `ruff check` clean on every touched file.
- [ ] Full non-slow suite green: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → 0 failed (network-restricted-sandbox artifacts itemized).
- [ ] `enforcement.py` guard passes: no model-id literal in lane code.
- [ ] Commit discipline honored (`PRE_COMMIT_ALLOW_NO_CONFIG=1`, trailer, HEAD moved); **nothing pushed**.

## Findings-to-tasks traceability (from the plan review)

| Finding | Resolved by |
|-|-|
| F1 — Task 3 was not a CAS | T1 extracts the real git-ref CAS; T3 builds the lane store on it; T3/T7/T11 multi-clone tests prove cross-process exactly-once |
| F4 — timestamp ordering unsound | T1 core assigns authoritative `seq`; T3 `read()` orders by `seq` + validates continuity; all projections consume seq-ordered input |
| F5 — retries not idempotent | T1 `identity_exclude` (seq/ts/revision anchors) + T5/T7/T8 already-landed preconditions |
| F6 — release could clear another's claim | T5 `cas_release` ownership precondition + stale-release regression test |
| F7 — DispatchUnknown misclassifies | T12 conservative conditions (attempt-scoped, no terminal outcome, lease/grace) + atomic retained |
| F8 — file-create ≠ durable | T10/T11 route `record`/`claim_dispatch` through the ref-CAS; return only after commit |
| F9 — schema/validation gaps | T2 `validate_lane_event` (known type, one revision scope, schema_version, path-stream) + T4 projection fails closed on unknown type |
| F2, F3, F10, F11 | **Slice 1B** (convergence wiring) — the follow-up plan |

