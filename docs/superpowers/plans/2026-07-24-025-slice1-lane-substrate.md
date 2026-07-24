# Self-Improvement Lane — Slice 1: Durable Substrate + Credit/Audit + Proposal Reroute — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the self-improvement lane's durable substrate (append-only event store + optimistic-concurrency CAS + singleton `LaneCoordinator`) and the two concrete slice-0-protocol implementations (`AttemptCreditLedger` = the `ReservationAuthority`; an event-sourced `RouteAudit` sink with atomic `claim_dispatch`), plus the proposal-review two-attempt independence reroute in `convergence/` — so later slices have the persistence, credit-guard, audit, and independence machinery they consume.

**Architecture:** A new `src/llmxive/self_improvement/` package holds a git-native, append-only event store (modeled on `model_selection/ledger_transport.py`'s `_append_commit` + `update-ref` CAS, but writing the spec's working-tree event files under `state/self-improvement/` and CASing against the branch). Projections (`LaneCoordinator`, `AttemptCreditLedger`, audit-derived `InvocationIdentity`) are pure folds over those events, exactly as `reservations.project()` folds credit events. The `AttemptCreditLedger` and the `RouteAudit` sink are the concrete lane implementations of the slice-0 `ReservationAuthority`/`RouteAudit` protocols, so `execute()` consumes them unchanged. The proposal reroute is entirely in `convergence/` + a small `backends/router.py` plumbing gap: reviewers already route through `route_chat`, so the two-attempt reroute is new wiring in `LLMReviewer` + a new `self_improvement_proposal` `ReviewSpec` builder — `run_convergence` itself is unchanged.

**Tech Stack:** Python ≥ 3.11; `pytest`; git plumbing via `subprocess` (mirroring `ledger_transport`); the package root is `llmxive.self_improvement` and `llmxive.convergence`. No new third-party deps.

## Global Constraints

Every task's requirements implicitly include this section. Exact values are copied verbatim from spec 025 rev 14 (`specs/025-self-improvement-lane/spec.md`) and the slice-0 contracts.

- **Route through the chokepoint (SC-008, FR-001).** All lane LLM calls resolve through the 026 `route_chat` chokepoint — never the router/backends directly. **No model-id literal anywhere in lane code** (`model_selection/enforcement.py` statically verifies this; do not add any pin). Reviewers express intent purely via `profile`.
- **Append-only, provenance never overwritten (FR-009).** State persists via append-only event JSON files; snapshots (`coordinator.json`, `problems/`, `attempts/`) are projections rebuilt from events. Each mutation with a side effect uses a **deterministic idempotency key** so retries are safe.
- **Event paths (FR-007, FR-009).** Coordinator record: `state/self-improvement/coordinator.json`. Coordinator event stream: `state/self-improvement/events/coordinator/<event-id>.json`. Per-Problem events: `state/self-improvement/events/<problem-id>/<event-id>.json`.
- **Event fields (FR-011).** Every event carries `event_id` (deterministic idempotency key), `event_type`, `problem_id` (or the coordinator stream sentinel), optional `attempt_id`, the applicable `expected_lane_revision` (coordinator events) and/or `expected_problem_revision` (per-Problem events) + `resulting_*_revision`, `timestamp`, `actor` (trust-domain identity), `payload`, `schema_version`.
- **CAS discipline (FR-008).** Every claim/promotion CASes: read `expected_*_revision=R`; fetch main; rebuild the entire projection; verify `R` **and** the required precondition; fast-forward push; on mismatch/non-fast-forward, discard and recompute. **MUST NOT resolve conflicts with `-X theirs`** (this is why `scripts/ci/commit-and-push.sh` cannot be reused — its `-X theirs` merge lets a loser replay stale state over a winner).
- **AttemptCreditLedger states are exactly `{open, retained, reconciled, released}` (FR-033 (c), Key Entities).** A reservation record is `{reservation_id, call_id, reserved_credits, state}` — it **accounts the reserved worst-case envelope; there is NO exact-actual-cost field** (F3). A dispatched candidate goes `open → retained → reconciled`; a candidate that never dispatched goes `open → released`. `attempt_budget_credits` bounds worst-case *reserved* spend (conservative — can never under-count).
- **ReservationAuthority collision semantics (slice-0 `attempt_hooks.ReservationAuthority.reserve` docstring).** A repeated `reservation_id` with the SAME `(credits, call_id)` identity → idempotent success WITHOUT a second hold or double-count. The same `reservation_id` with DIFFERENT `credits`/identity → integrity violation, RAISE (never silently overwrite). Concurrent duplicates settle on exactly ONE durable reservation (compare-and-swap / unique-insert). `reserve` MUST NOT raise for an ordinary budget denial (return `False`).
- **RouteAudit collision/atomicity semantics (slice-0 `attempt_hooks.RouteAudit` docstring).** `record`: a byte-identical replay of an `event_id` → idempotent success (no duplicate, no error); a DIFFERENT payload under the same `event_id` → integrity violation, RAISE. `claim_dispatch(DispatchStarted) -> bool`: `True` = first claim (own the dispatch); `False` = byte-identical replay already recorded (MUST NOT re-dispatch); a DIFFERENT payload under the same `event_id` → RAISE (never a silent `False`); atomic under concurrent workers (CAS / unique-insert). A sink infrastructure failure RAISES.
- **Reservation ordering saga (FR-033 (b)).** Per paid candidate `execute` (i) twice-checks the paid guard; (ii) reserves `worst_case_credits × retries` against the Attempt budget via `reservation_authority` (CAS on the Attempt-ledger revision); (iii) reserves the same against 026's daily ledger; (iv) dispatches. Rollbacks: Attempt-reserve over budget → refuse (skip); Attempt reserved but 026 refuses → **release** the Attempt reservation (skip); both reserved but dispatch fails → both **retained**; a candidate that never dispatched → **released**, one that dispatched but failed → **retained**.
- **InvocationIdentity (Key Entities line 227).** A durable record of ONE producer/reviewer LLM invocation: `actor_instance_id`, `model`, `backend`, `family`, `prompt_digest`, `context_digest`, `selection_policy_version`, `snapshot_digest`, `route_outcome` (includes `independence_degraded` for a proposal reviewer that took the reroute fallback). **Sourced from `route_chat`'s mandatory `route_audit` sink** (FR-033a) — the audit events, not a separate channel.
- **Proposal reroute (FR-002, Self-improvement ReviewSpec table line 279-280).** No new canonical profile: reuse the delivered `independent_review` (required family, fresh-required) and `deep_review` (no constraint). Attempt 1: `independent_review` + `independence_against(<producer baseline>)`; on **`ModelUnavailable`** → attempt 2: `deep_review` + record a structured `independence_degraded` outcome — **degrade, never fail closed** (a proposal produces/merges no code). The `independence_degraded` structure is `{primary_profile: "independent_review", fallback_profile: "deep_review", primary_failure: {exception_type, message, requirement_digest, snapshot_provenance}, relaxed_constraints: ["family_independence", "snapshot_freshness"]}` — `relaxed_constraints` is factual (what the fallback always relaxes), NOT a causal claim.
- **LLM-call ceiling is stage-specific (Policy Contract line 313).** The proposal review is NOT single-route: each reviewer operation is up to two `route_chat` invocations (`independent_review` then `deep_review`), so the proposal ceiling is `4N + R·(2N + 2)` (vs the patch `2N + R·(N + 2)`). Slice 1 wires the two-attempt reroute; it does not change `run_convergence`'s round cap (`max_rounds = 3`).
- **Behavior-preserving defaults.** `LLMReviewer` with no independence params, and `chat_with_model_fallback` with no new params, MUST behave byte-for-byte as today. The full non-slow suite (`pytest tests/unit tests/contract tests/integration -m "not slow"`) MUST stay green after every task.
- **Real tests, no mocks (Constitution III).** Test doubles that implement a Protocol with real logic (an in-memory budget, a scripted backend, a temp-git-repo ledger) are acceptable; `unittest.mock` is not the primary path. Reuse the slice-0 real doubles (`ScriptedBackend`, `_Budget`, the temp `repo` git fixture) where they fit.
- **Commit discipline.** Commit each task with `PRE_COMMIT_ALLOW_NO_CONFIG=1` and the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push** (local `main` lags; rebase onto `origin/main` at PR time only).

## Scope boundary (what this plan does NOT build)

Spec 025's US1 also includes **error mining, issue ranking/pagination, and the proposer + deterministic pre-gates** (the discovery-domain *logic*). Those consume this substrate and are a **follow-up plan**. This plan delivers only the five infrastructure components: event store, singleton `LaneCoordinator`, `AttemptCreditLedger`, event-sourced `RouteAudit` sink, and the proposal reroute. The **patch** review's fail-closed independence binding (`self_improvement_patch`) shares the `LLMReviewer` mechanism built here but its ReviewSpec + use (pre-merge gate) is a later slice; this plan builds the mechanism and the **proposal** ReviewSpec only.

## File Structure

- `src/llmxive/self_improvement/__init__.py` — package exports (the public names later slices import).
- `src/llmxive/self_improvement/events.py` — the lane `Event` dataclass (FR-011 fields) + JSON (de)serialization + `derive_event_id` (deterministic idempotency key). One responsibility: the event record + its identity.
- `src/llmxive/self_improvement/event_store.py` — `read_events`, `append_event` (git-native CAS), `LaneRevisionConflict`. The append-only durability + optimistic-concurrency primitive. One responsibility: persistence + CAS.
- `src/llmxive/self_improvement/coordinator.py` — `LaneCoordinator` projection dataclass + `project_coordinator` + `claim_precondition_idle` + `cas_transition`. One responsibility: the singleton coordinator record + its CAS discipline.
- `src/llmxive/self_improvement/credit_ledger.py` — `AttemptCreditLedger` (implements `ReservationAuthority`): `reserve`/`release`/`mark_retained` + `project_reservations` + `reconcile`. One responsibility: the Attempt-scoped credit guard.
- `src/llmxive/self_improvement/audit_sink.py` — `EventStoreRouteAudit` (implements `RouteAudit`): `record` + `claim_dispatch` + `reconcile_unknown`. One responsibility: durable audit + the atomic dispatch boundary.
- `src/llmxive/self_improvement/invocation_identity.py` — `InvocationIdentity` dataclass + `build_invocation_identity`. One responsibility: the audit-derived provenance record.
- `src/llmxive/convergence/self_improvement_specs.py` — `build_proposal_review_spec`. One responsibility: the `self_improvement_proposal` `ReviewSpec` builder.
- **Modify** `src/llmxive/backends/router.py` — plumb `independence_against` / `route_audit` / `route_id` / `reraise_model_unavailable` through `chat_with_model_fallback`.
- **Modify** `src/llmxive/convergence/llm_reviewer.py` — add optional independence params to `LLMReviewer.__init__` + the two-attempt reroute in a `_route_review` helper used by `_call_backend`.

Tests live under `tests/unit/` (pure projections, serialization, collision semantics) and `tests/integration/` (git-repo CAS, `execute()` with the real ledger + sink, proposal `run_convergence` reroute).

---

# Subsystem A — Durable substrate (event store + singleton coordinator)

### Task 1: Lane `Event` record + deterministic idempotency key

**Files:**
- Create: `src/llmxive/self_improvement/__init__.py`
- Create: `src/llmxive/self_improvement/events.py`
- Test: `tests/unit/test_self_improvement_events.py`

**Interfaces:**
- Produces:
  - `COORDINATOR_STREAM: str = "coordinator"` — the sentinel stream id for coordinator events (per-Problem streams use the `problem_id`).
  - `SCHEMA_VERSION: int = 1`.
  - `@dataclass(frozen=True) class Event` with fields (FR-011): `event_id: str`, `event_type: str`, `stream: str` (the `problem_id` or `COORDINATOR_STREAM`), `actor: str`, `payload: Mapping[str, object]`, `timestamp: str`, `schema_version: int = SCHEMA_VERSION`, `attempt_id: str | None = None`, `expected_lane_revision: int | None = None`, `expected_problem_revision: int | None = None`, `resulting_lane_revision: int | None = None`, `resulting_problem_revision: int | None = None`.
  - `derive_event_id(stream: str, idempotency_key: str) -> str` — `sha256(f"{stream}\x00{idempotency_key}")` hex, the deterministic idempotency key (FR-009: "deterministic idempotency key ... so retries are safe").
  - `event_to_json(event: Event) -> str` — canonical JSON (sorted keys, `ensure_ascii=False`, `separators=(",", ":")`), the on-disk body.
  - `event_from_json(text: str) -> Event`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_events.py
import json

from llmxive.self_improvement.events import (
    COORDINATOR_STREAM, SCHEMA_VERSION, Event, derive_event_id, event_from_json, event_to_json,
)


def _event(**kw) -> Event:
    base = dict(
        event_id="e1", event_type="ProblemDiscovered", stream="prob-123",
        actor="discovery", payload={"title": "flaky test"}, timestamp="2026-07-24T00:00:00+00:00",
    )
    base.update(kw)
    return Event(**base)


def test_event_id_is_deterministic_and_stream_scoped():
    a = derive_event_id("prob-123", "discover")
    assert a == derive_event_id("prob-123", "discover")            # stable
    assert a != derive_event_id("prob-999", "discover")            # stream-scoped
    assert a != derive_event_id("prob-123", "proposed")            # key-scoped
    assert len(a) == 64 and all(c in "0123456789abcdef" for c in a)  # sha256 hex


def test_event_round_trips_through_canonical_json():
    e = _event(attempt_id="att-1", expected_problem_revision=3, resulting_problem_revision=4)
    text = event_to_json(e)
    # canonical: sorted keys, compact separators
    assert text == json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert event_from_json(text) == e
    assert e.schema_version == SCHEMA_VERSION


def test_coordinator_stream_sentinel():
    assert COORDINATOR_STREAM == "coordinator"
    e = _event(stream=COORDINATOR_STREAM, expected_lane_revision=0, resulting_lane_revision=1)
    assert event_from_json(event_to_json(e)) == e
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_events.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.self_improvement'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/__init__.py
"""The autonomous self-improvement lane (spec 025). Slice 1: durable substrate,
Attempt credit ledger, event-sourced route-audit sink, proposal reroute."""
```

```python
# src/llmxive/self_improvement/events.py
"""The lane's append-only event record (FR-011) + its deterministic idempotency
key (FR-009). One event = one JSON blob on disk; every projection in the package
is a pure fold over a stream of these."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

#: Sentinel stream id for the singleton-coordinator event stream (FR-007). A
#: per-Problem stream uses the problem_id itself.
COORDINATOR_STREAM = "coordinator"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Event:
    """One append-only lane event (FR-011). ``stream`` is the coordinator sentinel
    or a ``problem_id``; the revision fields are the CAS anchors (coordinator events
    carry ``*_lane_revision``, per-Problem events carry ``*_problem_revision``)."""

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
    resulting_lane_revision: int | None = None
    resulting_problem_revision: int | None = None


def derive_event_id(stream: str, idempotency_key: str) -> str:
    """The deterministic idempotency key (FR-009): stable per (stream, key), so a
    retried side effect re-derives the SAME event_id and the append-only store
    no-ops it instead of duplicating."""
    return hashlib.sha256(f"{stream}\x00{idempotency_key}".encode()).hexdigest()


def _as_dict(event: Event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "stream": event.stream,
        "actor": event.actor,
        "payload": dict(event.payload),
        "timestamp": event.timestamp,
        "schema_version": event.schema_version,
        "attempt_id": event.attempt_id,
        "expected_lane_revision": event.expected_lane_revision,
        "expected_problem_revision": event.expected_problem_revision,
        "resulting_lane_revision": event.resulting_lane_revision,
        "resulting_problem_revision": event.resulting_problem_revision,
    }


def event_to_json(event: Event) -> str:
    """Canonical on-disk body: sorted keys + compact separators, so byte-identity
    is meaningful for the append-only idempotency check."""
    return json.dumps(_as_dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def event_from_json(text: str) -> Event:
    d = json.loads(text)
    return Event(
        event_id=d["event_id"], event_type=d["event_type"], stream=d["stream"],
        actor=d["actor"], payload=d["payload"], timestamp=d["timestamp"],
        schema_version=d["schema_version"], attempt_id=d.get("attempt_id"),
        expected_lane_revision=d.get("expected_lane_revision"),
        expected_problem_revision=d.get("expected_problem_revision"),
        resulting_lane_revision=d.get("resulting_lane_revision"),
        resulting_problem_revision=d.get("resulting_problem_revision"),
    )
```

(Note: `field` import is unused — drop it; keep imports ruff-clean.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_events.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/__init__.py src/llmxive/self_improvement/events.py tests/unit/test_self_improvement_events.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T1): lane Event record + deterministic idempotency key"
```

---

### Task 2: Event store — filesystem append + read (no CAS yet)

**Files:**
- Create: `src/llmxive/self_improvement/event_store.py`
- Test: `tests/integration/test_self_improvement_event_store.py`

**Interfaces:**
- Consumes: `Event`, `event_to_json`, `event_from_json`, `COORDINATOR_STREAM` (Task 1).
- Produces:
  - `stream_dir(repo: Path, stream: str) -> Path` — `repo / "state/self-improvement/events" / stream`.
  - `read_events(repo: Path, stream: str) -> list[Event]` — every `*.json` under the stream dir, sorted by `(timestamp, event_id)` (deterministic; ties broken by id).
  - `write_event_file(repo: Path, event: Event) -> Path` — writes `state/self-improvement/events/<stream>/<event_id>.json` (creating dirs); **byte-identical existing file → no-op; different body under the same path → raise `LaneAppendError`** (append-only immutability, mirroring `ledger_transport` lines 518-530). This is the pure-filesystem layer; Task 3 adds the git CAS commit on top.
  - `class LaneAppendError(RuntimeError)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_event_store.py
import pytest

from llmxive.self_improvement.events import Event
from llmxive.self_improvement.event_store import (
    LaneAppendError, read_events, stream_dir, write_event_file,
)


def _ev(eid: str, stream: str = "prob-1", ts: str = "2026-07-24T00:00:00+00:00", **kw) -> Event:
    return Event(event_id=eid, event_type="X", stream=stream, actor="a", payload={"k": eid},
                 timestamp=ts, **kw)


def test_write_then_read_round_trips(tmp_path):
    write_event_file(tmp_path, _ev("e1"))
    write_event_file(tmp_path, _ev("e2", ts="2026-07-24T00:00:01+00:00"))
    got = read_events(tmp_path, "prob-1")
    assert [e.event_id for e in got] == ["e1", "e2"]
    assert (stream_dir(tmp_path, "prob-1") / "e1.json").exists()


def test_read_is_deterministically_sorted(tmp_path):
    # same timestamp → tie-broken by event_id
    write_event_file(tmp_path, _ev("bbb"))
    write_event_file(tmp_path, _ev("aaa"))
    assert [e.event_id for e in read_events(tmp_path, "prob-1")] == ["aaa", "bbb"]


def test_identical_reappend_is_idempotent_noop(tmp_path):
    write_event_file(tmp_path, _ev("e1"))
    write_event_file(tmp_path, _ev("e1"))  # byte-identical → no error
    assert len(read_events(tmp_path, "prob-1")) == 1


def test_conflicting_reappend_raises(tmp_path):
    write_event_file(tmp_path, _ev("e1", actor="a"))
    with pytest.raises(LaneAppendError, match="append-only"):
        write_event_file(tmp_path, _ev("e1", actor="DIFFERENT"))


def test_missing_stream_reads_empty(tmp_path):
    assert read_events(tmp_path, "never-written") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_event_store.py -q`
Expected: FAIL — `ImportError: cannot import name 'read_events'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/event_store.py
"""The lane's append-only event store + optimistic-concurrency CAS (FR-008/009).

Persistence is git-native and append-only, modeled on
``model_selection/ledger_transport.py`` (the ONLY existing per-record CAS pattern
in the repo — ``scripts/ci/commit-and-push.sh`` uses ``-X theirs``, which FR-008
forbids). Unlike the credit ledger's hidden dedicated ref, lane events are the
spec's working-tree-visible files under ``state/self-improvement/`` (FR-009), so a
successful append is a normal commit on the current branch. Task 2 is the
filesystem layer; Task 3 adds the commit + revision CAS.

A future refactor could extract a shared git-CAS core from ``ledger_transport``;
kept separate here to avoid touching the financial ledger path."""

from __future__ import annotations

from pathlib import Path

from llmxive.self_improvement.events import Event, event_from_json, event_to_json

_EVENTS_ROOT = "state/self-improvement/events"


class LaneAppendError(RuntimeError):
    """An append-only violation: a different body for an already-written event_id."""


def stream_dir(repo: Path, stream: str) -> Path:
    return Path(repo) / _EVENTS_ROOT / stream


def read_events(repo: Path, stream: str) -> list[Event]:
    d = stream_dir(repo, stream)
    if not d.is_dir():
        return []
    events = [event_from_json(p.read_text(encoding="utf-8")) for p in d.glob("*.json")]
    return sorted(events, key=lambda e: (e.timestamp, e.event_id))


def _atomic_write_or_check(path: Path, body: str) -> bool:
    """ATOMIC exclusive create (``open(..., "x")`` == O_EXCL): the FIRST caller to
    create ``path`` returns ``True``; a caller finding it already present returns
    ``False`` iff the existing body is byte-identical, else raises ``LaneAppendError``
    (append-only, fail closed). O_EXCL is atomic across processes AND threads, so
    this is the concurrency-safe claim primitive the audit sink's ``claim_dispatch``
    builds on (Task 11) — not a read-then-write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8") as fh:  # noqa: PTH123 — need O_EXCL semantics
            fh.write(body)
        return True
    except FileExistsError:
        existing = path.read_text(encoding="utf-8")
        if existing == body:
            return False  # idempotent re-append (byte-identical)
        raise LaneAppendError(
            f"path {path.name!r} already exists with DIFFERENT content "
            "(append-only violation) — failing closed"
        ) from None


def write_event_file(repo: Path, event: Event) -> Path:
    """Append-only write of one event (atomic; byte-identical re-append is a no-op,
    conflicting body raises ``LaneAppendError``)."""
    path = stream_dir(repo, event.stream) / f"{event.event_id}.json"
    _atomic_write_or_check(path, event_to_json(event))
    return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_event_store.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/event_store.py tests/integration/test_self_improvement_event_store.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T2): lane event store filesystem append/read (append-only)"
```

---

### Task 3: Event store — git-native commit + revision CAS

**Files:**
- Modify: `src/llmxive/self_improvement/event_store.py`
- Test: `tests/integration/test_self_improvement_event_store_cas.py`

**Interfaces:**
- Consumes: `write_event_file`, `read_events` (Task 2).
- Produces:
  - `class LaneRevisionConflict(RuntimeError)` — the CAS lost (the rebuilt revision ≠ `expected_revision`, or the precondition failed). The caller recomputes.
  - `append_event(repo: Path, event: Event, *, expected_revision: int, revision_of: Callable[[list[Event]], int], precondition: Callable[[list[Event]], tuple[bool, str]] | None = None) -> int` — the CAS transaction: (1) `read_events(event.stream)`; (2) `rev = revision_of(events)`; (3) if `rev != expected_revision` → `LaneRevisionConflict`; (4) if `precondition` and it returns `(False, reason)` → `LaneRevisionConflict(reason)`; (5) `write_event_file` (byte-identical re-append is an idempotent no-op → return `expected_revision + 1`); (6) `_commit_event(repo, event)`; (7) return `expected_revision + 1`. `revision_of` is injected because each projection counts revisions its own way (the coordinator counts coordinator events; a Problem counts its own). Distributed FF-push is layered by the caller/persistence domain; slice-1 tests the logical revision CAS.
  - `_commit_event(repo: Path, event: Event) -> None` — `git add <path>` + `git -c user.name=... -c user.email=... commit -m "self-improvement: <event_type> <event_id>"` in `repo`. Skips cleanly (returns) if `repo` is not a git work tree (pure-filesystem tests) — detected via `git rev-parse --is-inside-work-tree`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_event_store_cas.py
import subprocess

import pytest

from llmxive.self_improvement.events import Event
from llmxive.self_improvement.event_store import (
    LaneRevisionConflict, append_event, read_events,
)


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "root")
    return tmp_path


def _ev(eid, rev, stream="prob-1"):
    return Event(event_id=eid, event_type="X", stream=stream, actor="a", payload={},
                 timestamp=f"2026-07-24T00:00:{rev:02d}+00:00", expected_problem_revision=rev,
                 resulting_problem_revision=rev + 1)


def _count(events):  # revision = number of events in the stream
    return len(events)


def test_append_advances_revision_and_commits(repo):
    assert append_event(repo, _ev("e0", 0), expected_revision=0, revision_of=_count) == 1
    assert append_event(repo, _ev("e1", 1), expected_revision=1, revision_of=_count) == 2
    assert [e.event_id for e in read_events(repo, "prob-1")] == ["e0", "e1"]
    # each append made a commit
    log = subprocess.run(["git", "log", "--oneline"], cwd=str(repo), capture_output=True, text=True).stdout
    assert log.count("self-improvement:") == 2


def test_stale_expected_revision_loses_the_cas(repo):
    append_event(repo, _ev("e0", 0), expected_revision=0, revision_of=_count)
    # a writer still thinking rev is 0 must lose (actual rev is now 1)
    with pytest.raises(LaneRevisionConflict):
        append_event(repo, _ev("e1", 0), expected_revision=0, revision_of=_count)


def test_precondition_failure_loses_the_cas(repo):
    def _never(events):
        return (False, "precondition: lane not idle")
    with pytest.raises(LaneRevisionConflict, match="not idle"):
        append_event(repo, _ev("e0", 0), expected_revision=0, revision_of=_count, precondition=_never)


def test_identical_reappend_is_idempotent(repo):
    append_event(repo, _ev("e0", 0), expected_revision=0, revision_of=_count)
    # a retry re-deriving the SAME event at the SAME expected_revision is a no-op success
    assert append_event(repo, _ev("e0", 0), expected_revision=0, revision_of=_count) == 1
    assert len(read_events(repo, "prob-1")) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_event_store_cas.py -q`
Expected: FAIL — `ImportError: cannot import name 'append_event'`.

- [ ] **Step 3: Write minimal implementation** (append to `event_store.py`)

```python
import subprocess
from collections.abc import Callable


class LaneRevisionConflict(RuntimeError):
    """The optimistic-concurrency CAS lost: the rebuilt revision no longer equals
    ``expected_revision``, or the transition precondition failed. The caller must
    discard, refetch/rebuild, and recompute (FR-008) — never force the write."""


def _is_git_worktree(repo: Path) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(repo), capture_output=True, text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _commit_event(repo: Path, event: Event) -> None:
    if not _is_git_worktree(repo):
        return  # pure-filesystem context (unit tests) — the file write is the durability
    rel = f"{_EVENTS_ROOT}/{event.stream}/{event.event_id}.json"
    subprocess.run(["git", "add", "--", rel], cwd=str(repo), check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=llmxive-self-improvement", "-c", "user.email=self-improvement@llmxive",
         "commit", "-q", "-m", f"self-improvement: {event.event_type} {event.event_id}"],
        cwd=str(repo), check=True, capture_output=True, text=True,
    )


def append_event(
    repo: Path,
    event: Event,
    *,
    expected_revision: int,
    revision_of: Callable[[list[Event]], int],
    precondition: Callable[[list[Event]], tuple[bool, str]] | None = None,
) -> int:
    """CAS-append ``event`` to its stream. Rebuilds the stream, verifies
    ``expected_revision`` (+ any ``precondition``) against it, then writes + commits.
    Returns the resulting revision. Raises :class:`LaneRevisionConflict` if the CAS
    lost. A byte-identical re-append at the same revision is an idempotent no-op
    (returns ``expected_revision + 1`` without a second commit)."""
    events = read_events(repo, event.stream)
    already = any(e.event_id == event.event_id for e in events)
    if not already:
        rev = revision_of(events)
        if rev != expected_revision:
            raise LaneRevisionConflict(
                f"stale expected_revision {expected_revision} (actual {rev}) for stream {event.stream!r}"
            )
        if precondition is not None:
            ok, reason = precondition(events)
            if not ok:
                raise LaneRevisionConflict(reason)
    path_existed = (stream_dir(repo, event.stream) / f"{event.event_id}.json").exists()
    write_event_file(repo, event)  # byte-identical → no-op; conflicting → LaneAppendError
    if not path_existed:
        _commit_event(repo, event)
    return expected_revision + 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_event_store_cas.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/event_store.py tests/integration/test_self_improvement_event_store_cas.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T3): event-store git commit + revision CAS (LaneRevisionConflict)"
```

---

### Task 4: `LaneCoordinator` projection

**Files:**
- Create: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/unit/test_self_improvement_coordinator.py`

**Interfaces:**
- Consumes: `Event`, `COORDINATOR_STREAM` (Task 1); `read_events` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class LaneCoordinator` with fields (FR-007 / Key Entities line 224): `lane_revision: int`, `active_problem_id: str | None`, `active_attempt_id: str | None`, `monitored_attempts: tuple[str, ...]`, `promotion_enabled: bool`, `last_autonomous_merge_at: str | None`, `policy_version: int`.
  - `EMPTY_COORDINATOR: LaneCoordinator` — `lane_revision=0`, all ids `None`/empty, `promotion_enabled=False`, `policy_version=0` (the genesis projection before any event).
  - `project_coordinator(events: list[Event]) -> LaneCoordinator` — pure fold over the coordinator stream. `lane_revision` = count of applied coordinator events. Event types handled (slice-1 subset): `"ClaimAcquired"` (sets `active_problem_id`/`active_attempt_id` from payload), `"ClaimReleased"` (clears them — the off-ramp CAS, transition-table preamble line 238), `"MonitorStarted"` (appends `attempt_id` to `monitored_attempts`), `"PromotionEnabledSet"` (sets `promotion_enabled`/`policy_version` from payload). Unknown event types advance `lane_revision` but change no field (forward-compatible).
  - `coordinator_revision(events: list[Event]) -> int` — `len(events)` (the `revision_of` for the coordinator stream; matches `project_coordinator(...).lane_revision`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_coordinator.py
from llmxive.self_improvement.coordinator import (
    EMPTY_COORDINATOR, coordinator_revision, project_coordinator,
)
from llmxive.self_improvement.events import COORDINATOR_STREAM, Event


def _ev(eid, etype, payload):
    return Event(event_id=eid, event_type=etype, stream=COORDINATOR_STREAM, actor="coord",
                 payload=payload, timestamp=f"2026-07-24T00:00:{eid[-1]}0+00:00")


def test_empty_projection_is_genesis():
    c = project_coordinator([])
    assert c == EMPTY_COORDINATOR
    assert c.lane_revision == 0 and c.active_problem_id is None and c.promotion_enabled is False


def test_claim_then_release_round_trips_active_ids():
    events = [
        _ev("e1", "ClaimAcquired", {"problem_id": "P1", "attempt_id": "A1"}),
        _ev("e2", "ClaimReleased", {"problem_id": "P1", "attempt_id": "A1"}),
    ]
    c = project_coordinator(events)
    assert c.lane_revision == 2
    assert c.active_problem_id is None and c.active_attempt_id is None  # released → idle


def test_claim_sets_active_and_revision_matches_helper():
    events = [_ev("e1", "ClaimAcquired", {"problem_id": "P1", "attempt_id": "A1"})]
    c = project_coordinator(events)
    assert c.active_problem_id == "P1" and c.active_attempt_id == "A1"
    assert c.lane_revision == coordinator_revision(events) == 1


def test_monitor_and_promotion_events():
    events = [
        _ev("e1", "MonitorStarted", {"attempt_id": "A1"}),
        _ev("e2", "MonitorStarted", {"attempt_id": "A2"}),
        _ev("e3", "PromotionEnabledSet", {"promotion_enabled": True, "policy_version": 2}),
    ]
    c = project_coordinator(events)
    assert c.monitored_attempts == ("A1", "A2")
    assert c.promotion_enabled is True and c.policy_version == 2


def test_unknown_event_advances_revision_only():
    events = [_ev("e1", "SomeFutureEvent", {"whatever": 1})]
    c = project_coordinator(events)
    assert c.lane_revision == 1 and c.active_problem_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_coordinator.py -q`
Expected: FAIL — `ModuleNotFoundError: ... coordinator`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/coordinator.py
"""The singleton LaneCoordinator (FR-007) — a projection over the coordinator
event stream that serializes the pre-merge pipeline (FR-008: all claims CAS
against ``lane_revision``). Slice 1 delivers the projection + the CAS primitive;
the claim/label side effect (US2) is a later slice."""

from __future__ import annotations

from dataclasses import dataclass, replace

from llmxive.self_improvement.events import Event


@dataclass(frozen=True)
class LaneCoordinator:
    lane_revision: int
    active_problem_id: str | None
    active_attempt_id: str | None
    monitored_attempts: tuple[str, ...]
    promotion_enabled: bool
    last_autonomous_merge_at: str | None
    policy_version: int


EMPTY_COORDINATOR = LaneCoordinator(
    lane_revision=0, active_problem_id=None, active_attempt_id=None,
    monitored_attempts=(), promotion_enabled=False, last_autonomous_merge_at=None, policy_version=0,
)


def coordinator_revision(events: list[Event]) -> int:
    """The coordinator's CAS anchor (== ``project_coordinator(events).lane_revision``)."""
    return len(events)


def project_coordinator(events: list[Event]) -> LaneCoordinator:
    c = EMPTY_COORDINATOR
    for e in events:
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
        # unknown types: advance revision only (forward-compatible)
        c = replace(c, lane_revision=c.lane_revision + 1)
    return c
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_coordinator.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/coordinator.py tests/unit/test_self_improvement_coordinator.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T4): LaneCoordinator projection (FR-007)"
```

---

### Task 5: Coordinator CAS transition primitive (FR-008)

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/integration/test_self_improvement_coordinator_cas.py`

**Interfaces:**
- Consumes: `project_coordinator`, `coordinator_revision` (Task 4); `append_event`, `read_events`, `LaneRevisionConflict` (Tasks 2-3); `Event`, `COORDINATOR_STREAM`, `derive_event_id` (Task 1).
- Produces:
  - `cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str) -> LaneCoordinator` — the FR-008 claim discipline: read current coordinator events; rebuild; require `expected_lane_revision = current.lane_revision` **and** the precondition `active_problem_id is None` (idle); append a `ClaimAcquired` event via `append_event` (idempotency key `("claim", problem_id, attempt_id)`); return the new projection. Raises `LaneRevisionConflict` if not idle or the revision moved (the loser recomputes/yields — US2 scenario 1). Because the claim is a deterministic idempotency key, a retried claim of the SAME (problem, attempt) is a no-op (US2 scenario 2: "re-applied idempotently").
  - `cas_release(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str) -> LaneCoordinator` — the off-ramp CAS (transition preamble line 238): append `ClaimReleased`, clearing `active_*`. Idempotency key `("release", problem_id, attempt_id)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_coordinator_cas.py
import subprocess

import pytest

from llmxive.self_improvement.coordinator import cas_claim, cas_release
from llmxive.self_improvement.event_store import LaneRevisionConflict


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "root")
    return tmp_path


TS = "2026-07-24T00:00:00+00:00"


def test_claim_when_idle_succeeds_and_occupies(repo):
    c = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="disc", timestamp=TS)
    assert c.active_problem_id == "P1" and c.active_attempt_id == "A1" and c.lane_revision == 1


def test_second_claim_of_different_problem_loses_when_occupied(repo):
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="disc", timestamp=TS)
    # lane is now occupied by P1 → a claim of a DIFFERENT problem must lose (US2 scenario 1)
    with pytest.raises(LaneRevisionConflict):
        cas_claim(repo, problem_id="P2", attempt_id="A2", actor="disc", timestamp=TS)


def test_claim_is_idempotent_on_retry(repo):
    a = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="disc", timestamp=TS)
    b = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="disc", timestamp=TS)  # retry
    assert a == b and b.lane_revision == 1  # no duplicate event, same projection


def test_release_frees_the_lane_for_the_next_claim(repo):
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="disc", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="disc", timestamp=TS)
    c = cas_claim(repo, problem_id="P2", attempt_id="A2", actor="disc", timestamp=TS)
    assert c.active_problem_id == "P2" and c.lane_revision == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: FAIL — `ImportError: cannot import name 'cas_claim'`.

- [ ] **Step 3: Write minimal implementation** (append to `coordinator.py`)

```python
from pathlib import Path

from llmxive.self_improvement.event_store import append_event, read_events
from llmxive.self_improvement.events import COORDINATOR_STREAM, Event, derive_event_id


def _coordinator_event(event_type: str, idem: tuple[str, ...], payload: dict, actor: str,
                       timestamp: str, expected_lane_revision: int) -> Event:
    eid = derive_event_id(COORDINATOR_STREAM, "\x00".join(idem))
    return Event(
        event_id=eid, event_type=event_type, stream=COORDINATOR_STREAM, actor=actor,
        payload=payload, timestamp=timestamp, expected_lane_revision=expected_lane_revision,
        resulting_lane_revision=expected_lane_revision + 1,
    )


def cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str) -> LaneCoordinator:
    """Claim the singleton pre-merge pipeline (FR-008). Fails closed (raises
    ``LaneRevisionConflict``) unless the lane is idle at the observed revision."""
    events = read_events(repo, COORDINATOR_STREAM)
    current = project_coordinator(events)
    event = _coordinator_event(
        "ClaimAcquired", ("claim", problem_id, attempt_id),
        {"problem_id": problem_id, "attempt_id": attempt_id}, actor, timestamp, current.lane_revision,
    )

    def _idle(evs: list[Event]) -> tuple[bool, str]:
        pid = project_coordinator(evs).active_problem_id
        if pid is not None:
            return (False, f"lane not idle (active_problem_id={pid!r})")
        return (True, "")

    append_event(repo, event, expected_revision=current.lane_revision,
                 revision_of=coordinator_revision, precondition=_idle)
    return project_coordinator(read_events(repo, COORDINATOR_STREAM))


def cas_release(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str) -> LaneCoordinator:
    """Release the pre-merge singleton (off-ramp CAS, transition preamble line 238)."""
    events = read_events(repo, COORDINATOR_STREAM)
    current = project_coordinator(events)
    event = _coordinator_event(
        "ClaimReleased", ("release", problem_id, attempt_id),
        {"problem_id": problem_id, "attempt_id": attempt_id}, actor, timestamp, current.lane_revision,
    )
    append_event(repo, event, expected_revision=current.lane_revision, revision_of=coordinator_revision)
    return project_coordinator(read_events(repo, COORDINATOR_STREAM))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/coordinator.py tests/integration/test_self_improvement_coordinator_cas.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T5): coordinator CAS claim/release discipline (FR-008)"
```

---

# Subsystem B — Credit ledger + event-sourced audit sink + InvocationIdentity

**Concurrency model (read once).** Within one Attempt's proposal/patch convergence, the lane injects ONE `AttemptCreditLedger` instance as `reservation_authority` into every panel `route_chat` call; the panel runs reviewers concurrently in ONE process (a `ThreadPoolExecutor`). So the ledger's budget invariant is made atomic **in-process by a `threading.Lock`** on the shared instance (this is what satisfies US1 scenario 5's "two concurrent panel reviewers"); the event-store revision CAS (Task 3) is the cross-process backstop (retry-on-conflict). The audit sink's `claim_dispatch` is atomic across threads AND processes via the O_EXCL `_atomic_write_or_check` primitive (Task 2) — a genuine unique-insert, not a read-then-write.

Add `stream_revision` to `event_store.py` (used as `revision_of` for per-Problem streams; the coordinator has its own equal-valued `coordinator_revision`):

```python
# append to src/llmxive/self_improvement/event_store.py
def stream_revision(events: list[Event]) -> int:
    """A stream's CAS anchor = its event count (per-Problem streams; FR-011
    ``expected_problem_revision``)."""
    return len(events)
```

Include this one-liner in Task 6's commit.

### Task 6: `AttemptCreditLedger` reservation projection

**Files:**
- Create: `src/llmxive/self_improvement/credit_ledger.py`
- Modify: `src/llmxive/self_improvement/event_store.py` (add `stream_revision`)
- Test: `tests/unit/test_self_improvement_credit_projection.py`

**Interfaces:**
- Consumes: `Event` (Task 1); `read_events` (Task 2).
- Produces:
  - State constants: `STATE_OPEN = "open"`, `STATE_RETAINED = "retained"`, `STATE_RECONCILED = "reconciled"`, `STATE_RELEASED = "released"`, `COUNTING_STATES = frozenset({STATE_OPEN, STATE_RETAINED, STATE_RECONCILED})` (a `released` reservation never dispatched → does NOT count against the cap; `open`/`retained`/`reconciled` all count — FR-033 (b)/(c)).
  - `@dataclass(frozen=True) class AttemptReservation`: `reservation_id: str`, `call_id: str`, `reserved_credits: float`, `state: str`. (Exactly the FR-033 record — NO exact-actual-cost field.)
  - `RESERVATION_EVENT_STATE: dict[str, str]` mapping `event_type → state`: `{"AttemptCreditReserved": STATE_OPEN, "AttemptCreditReleased": STATE_RELEASED, "AttemptCreditRetained": STATE_RETAINED, "AttemptCreditReconciled": STATE_RECONCILED}`.
  - `project_reservations(events: list[Event], attempt_id: str) -> dict[str, AttemptReservation]` — fold the events whose `attempt_id` matches and whose `event_type` is a reservation event; `AttemptCreditReserved` creates the record (with `call_id`/`reserved_credits` from payload), later events advance only its `state`. Ignore a state event for an unknown `reservation_id` (out-of-order safety).
  - `counting_total(reservations: dict[str, AttemptReservation]) -> float` — `sum(r.reserved_credits for r in reservations.values() if r.state in COUNTING_STATES)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_credit_projection.py
from llmxive.self_improvement.credit_ledger import (
    STATE_OPEN, STATE_RECONCILED, STATE_RELEASED, STATE_RETAINED,
    counting_total, project_reservations,
)
from llmxive.self_improvement.events import Event


def _ev(eid, etype, rid, attempt="A1", credits=2.5, call_id="c1"):
    payload = {"reservation_id": rid}
    if etype == "AttemptCreditReserved":
        payload |= {"call_id": call_id, "reserved_credits": credits}
    return Event(event_id=eid, event_type=etype, stream="P1", actor="exec", payload=payload,
                 timestamp=f"2026-07-24T00:00:{eid[-1]}0+00:00", attempt_id=attempt)


def test_reserve_then_retain_then_reconcile_advances_state():
    events = [
        _ev("e1", "AttemptCreditReserved", "r1"),
        _ev("e2", "AttemptCreditRetained", "r1"),
        _ev("e3", "AttemptCreditReconciled", "r1"),
    ]
    res = project_reservations(events, "A1")
    assert res["r1"].state == STATE_RECONCILED
    assert res["r1"].reserved_credits == 2.5 and res["r1"].call_id == "c1"


def test_released_does_not_count_but_open_retained_reconciled_do():
    events = [
        _ev("e1", "AttemptCreditReserved", "r1", credits=10.0),
        _ev("e2", "AttemptCreditReserved", "r2", credits=5.0),
        _ev("e3", "AttemptCreditReleased", "r2"),            # never dispatched → freed
        _ev("e4", "AttemptCreditReserved", "r3", credits=3.0),
        _ev("e5", "AttemptCreditRetained", "r3"),            # dispatched → still counts
    ]
    res = project_reservations(events, "A1")
    assert res["r1"].state == STATE_OPEN and res["r2"].state == STATE_RELEASED
    assert counting_total(res) == 13.0  # r1(open 10) + r3(retained 3); r2 released excluded


def test_projection_is_attempt_scoped():
    events = [_ev("e1", "AttemptCreditReserved", "r1", attempt="A1"),
              _ev("e2", "AttemptCreditReserved", "r9", attempt="A2")]
    assert set(project_reservations(events, "A1")) == {"r1"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_credit_projection.py -q`
Expected: FAIL — `ModuleNotFoundError: ... credit_ledger`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/credit_ledger.py
"""The Attempt-scoped credit ledger (FR-033) — the concrete lane implementation of
the slice-0 ``ReservationAuthority`` protocol. An event-sourced projection over the
per-Problem stream's ``AttemptCredit*`` events; the per-Attempt cap is enforced
atomically across the concurrent panel by an in-process lock (Task 7)."""

from __future__ import annotations

from dataclasses import dataclass

from llmxive.self_improvement.events import Event

STATE_OPEN = "open"
STATE_RETAINED = "retained"
STATE_RECONCILED = "reconciled"
STATE_RELEASED = "released"
#: A `released` reservation never dispatched → does NOT count against the Attempt
#: cap; open/retained/reconciled all count (FR-033 (b)/(c)).
COUNTING_STATES = frozenset({STATE_OPEN, STATE_RETAINED, STATE_RECONCILED})

RESERVATION_EVENT_STATE = {
    "AttemptCreditReserved": STATE_OPEN,
    "AttemptCreditReleased": STATE_RELEASED,
    "AttemptCreditRetained": STATE_RETAINED,
    "AttemptCreditReconciled": STATE_RECONCILED,
}


@dataclass(frozen=True)
class AttemptReservation:
    """One Attempt-scoped reservation record (FR-033 Key Entities): it accounts the
    reserved worst-case envelope — there is NO exact-actual-cost field (F3)."""

    reservation_id: str
    call_id: str
    reserved_credits: float
    state: str


def project_reservations(events: list[Event], attempt_id: str) -> dict[str, AttemptReservation]:
    out: dict[str, AttemptReservation] = {}
    for e in events:
        if e.attempt_id != attempt_id or e.event_type not in RESERVATION_EVENT_STATE:
            continue
        rid = str(e.payload["reservation_id"])
        state = RESERVATION_EVENT_STATE[e.event_type]
        if e.event_type == "AttemptCreditReserved":
            out[rid] = AttemptReservation(
                reservation_id=rid, call_id=str(e.payload["call_id"]),
                reserved_credits=float(e.payload["reserved_credits"]), state=state,
            )
        elif rid in out:  # advance state only; ignore a stray transition for an unknown id
            from dataclasses import replace
            out[rid] = replace(out[rid], state=state)
    return out


def counting_total(reservations: dict[str, AttemptReservation]) -> float:
    return sum(r.reserved_credits for r in reservations.values() if r.state in COUNTING_STATES)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_credit_projection.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/credit_ledger.py src/llmxive/self_improvement/event_store.py tests/unit/test_self_improvement_credit_projection.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T6): AttemptCreditLedger reservation projection + stream_revision"
```

---

### Task 7: `AttemptCreditLedger.reserve` (ReservationAuthority — budget CAS + collision)

**Files:**
- Modify: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/integration/test_self_improvement_credit_ledger.py`

**Interfaces:**
- Consumes: `project_reservations`, `counting_total`, states (Task 6); `append_event`, `read_events`, `stream_revision`, `LaneRevisionConflict` (Tasks 2-3); `derive_event_id`, `Event` (Task 1).
- Produces:
  - `class AttemptCreditLedger` — implements the slice-0 `ReservationAuthority` protocol. Constructor: `AttemptCreditLedger(*, repo: Path, problem_id: str, attempt_id: str, attempt_budget_credits: float, actor: str, clock: Callable[[], str])` — `problem_id` is the event stream; `clock()` returns an ISO-8601 timestamp (injected for determinism). Holds a `threading.Lock`.
  - `def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool` — under the lock, a bounded CAS-retry loop: project the Attempt's reservations; if `reservation_id` present with SAME `(credits, call_id)` → return `True` (idempotent, no double-count); if present with DIFFERENT identity → `raise ValueError` (integrity); if `counting_total + credits > attempt_budget_credits` → return `False` (budget denial, never raise); else append an `AttemptCreditReserved` event at `expected_revision = stream_revision(events)`; on `LaneRevisionConflict`, recompute and retry (a cross-process writer landed); after the retry cap raise `LaneContention`.
  - `class LaneContention(RuntimeError)`.
  - A private `_append(self, event_type, idem_suffix, payload) -> None` used by Tasks 7-9 that builds the per-Problem `Event` (with `attempt_id`, `expected_problem_revision`, `resulting_problem_revision`, `derive_event_id(problem_id, "credit\x00" + attempt_id + "\x00" + "\x00".join(idem_suffix))`) and CAS-appends it, retrying on `LaneRevisionConflict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_credit_ledger.py
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from llmxive.self_improvement.credit_ledger import AttemptCreditLedger


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "root")
    return tmp_path


def _ledger(repo, budget=10.0):
    return AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                               attempt_budget_credits=budget, actor="exec",
                               clock=lambda: "2026-07-24T00:00:00+00:00")


def test_reserve_within_budget_succeeds_over_budget_denies(repo):
    led = _ledger(repo, budget=10.0)
    assert led.reserve(6.0, reservation_id="r1", call_id="c1") is True
    assert led.reserve(6.0, reservation_id="r2", call_id="c2") is False  # 6+6 > 10 → deny (no raise)
    assert led.reserve(4.0, reservation_id="r3", call_id="c3") is True   # 6+4 == 10 → admitted


def test_reserve_is_idempotent_on_same_identity(repo):
    led = _ledger(repo)
    assert led.reserve(3.0, reservation_id="r1", call_id="c1") is True
    assert led.reserve(3.0, reservation_id="r1", call_id="c1") is True   # replay → no double-count
    # only one reservation exists; budget still admits another 7
    assert led.reserve(7.0, reservation_id="r2", call_id="c2") is True


def test_reserve_conflicting_identity_raises(repo):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    with pytest.raises(ValueError, match="COLLISION|integrity"):
        led.reserve(9.0, reservation_id="r1", call_id="c1")  # same id, different credits


def test_concurrent_panel_reservers_never_exceed_budget(repo):
    # US1 scenario 5: two concurrent reviewers share ONE ledger; the lock makes the
    # budget invariant atomic — the sum of admitted envelopes never exceeds the cap.
    led = _ledger(repo, budget=10.0)

    def _try(i):
        return led.reserve(6.0, reservation_id=f"r{i}", call_id=f"c{i}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(_try, range(2)))
    assert results.count(True) == 1 and results.count(False) == 1  # exactly one wins (6+6 > 10)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_credit_ledger.py -q`
Expected: FAIL — `ImportError: cannot import name 'AttemptCreditLedger'`.

- [ ] **Step 3: Write minimal implementation** (append to `credit_ledger.py`)

```python
import threading
from collections.abc import Callable
from pathlib import Path

from llmxive.self_improvement.event_store import (
    LaneRevisionConflict, append_event, read_events, stream_revision,
)
from llmxive.self_improvement.events import Event, derive_event_id

_MAX_CAS_RETRIES = 8


class LaneContention(RuntimeError):
    """The reservation CAS could not converge within the retry budget (sustained
    cross-process contention) — fail closed rather than force the write."""


class AttemptCreditLedger:
    """The Attempt-scoped ``ReservationAuthority`` (FR-033). One instance per Attempt
    is shared across the concurrent review panel; the ``threading.Lock`` makes the
    budget invariant atomic in-process, the event-store revision CAS backstops
    cross-process writers."""

    def __init__(self, *, repo: Path, problem_id: str, attempt_id: str,
                 attempt_budget_credits: float, actor: str, clock: Callable[[], str]) -> None:
        self._repo = repo
        self._stream = problem_id
        self._attempt_id = attempt_id
        self._budget = float(attempt_budget_credits)
        self._actor = actor
        self._clock = clock
        self._lock = threading.Lock()

    def _build_event(self, event_type: str, idem_suffix: tuple[str, ...], payload: dict,
                     expected_revision: int) -> Event:
        eid = derive_event_id(self._stream, "credit\x00" + "\x00".join((self._attempt_id, *idem_suffix)))
        return Event(
            event_id=eid, event_type=event_type, stream=self._stream, actor=self._actor,
            payload=payload, timestamp=self._clock(), attempt_id=self._attempt_id,
            expected_problem_revision=expected_revision, resulting_problem_revision=expected_revision + 1,
        )

    def _cas_append(self, event_type: str, idem_suffix: tuple[str, ...], payload: dict) -> None:
        for _ in range(_MAX_CAS_RETRIES):
            events = read_events(self._repo, self._stream)
            rev = stream_revision(events)
            try:
                append_event(self._repo, self._build_event(event_type, idem_suffix, payload, rev),
                             expected_revision=rev, revision_of=stream_revision)
                return
            except LaneRevisionConflict:
                continue
        raise LaneContention(f"credit {event_type} CAS did not converge for {self._attempt_id!r}")

    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        with self._lock:
            for _ in range(_MAX_CAS_RETRIES):
                events = read_events(self._repo, self._stream)
                res = project_reservations(events, self._attempt_id)
                existing = res.get(reservation_id)
                if existing is not None:
                    if existing.call_id == call_id and existing.reserved_credits == credits:
                        return True  # idempotent replay — no second hold, no double count
                    raise ValueError(
                        f"reservation {reservation_id!r} COLLISION: existing "
                        f"(credits={existing.reserved_credits}, call_id={existing.call_id!r}) != "
                        f"requested (credits={credits}, call_id={call_id!r}) — integrity violation"
                    )
                if counting_total(res) + credits > self._budget:
                    return False  # budget denial — MUST NOT raise (skip/advance the candidate)
                rev = stream_revision(events)
                payload = {"reservation_id": reservation_id, "call_id": call_id, "reserved_credits": credits}
                try:
                    append_event(
                        self._repo,
                        self._build_event("AttemptCreditReserved", ("reserve", reservation_id), payload, rev),
                        expected_revision=rev, revision_of=stream_revision,
                    )
                    return True
                except LaneRevisionConflict:
                    continue  # a cross-process writer landed — recompute budget + re-decide
            raise LaneContention(f"reserve CAS did not converge for {reservation_id!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_credit_ledger.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/credit_ledger.py tests/integration/test_self_improvement_credit_ledger.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T7): AttemptCreditLedger.reserve — budget CAS + collision semantics"
```

---

### Task 8: `AttemptCreditLedger.release` + `mark_retained`

**Files:**
- Modify: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/integration/test_self_improvement_credit_ledger.py` (extend)

**Interfaces:**
- Produces (methods on `AttemptCreditLedger`, completing the `ReservationAuthority` protocol):
  - `def release(self, reservation_id: str) -> None` — under the lock: if the reservation is currently `open`, append `AttemptCreditReleased` (`open → released`). Idempotent (already `released`/absent → no-op; already `retained`/`reconciled` → no-op, because a dispatched reservation is never released — FR-033 (b)/(c)).
  - `def mark_retained(self, reservation_id: str) -> None` — under the lock: if the reservation is currently `open`, append `AttemptCreditRetained` (`open → retained`). Idempotent (already `retained`/`reconciled` → no-op).

- [ ] **Step 1: Write the failing test**

```python
# add to tests/integration/test_self_improvement_credit_ledger.py
from llmxive.self_improvement.credit_ledger import (
    STATE_RELEASED, STATE_RETAINED, counting_total, project_reservations,
)
from llmxive.self_improvement.event_store import read_events


def _state(repo, rid):
    return project_reservations(read_events(repo, "P1"), "A1")[rid].state


def test_release_frees_budget_retain_keeps_it(repo):
    led = _ledger(repo, budget=10.0)
    led.reserve(6.0, reservation_id="r1", call_id="c1")
    led.release("r1")                              # never dispatched
    assert _state(repo, "r1") == STATE_RELEASED
    assert counting_total(project_reservations(read_events(repo, "P1"), "A1")) == 0.0
    led.reserve(6.0, reservation_id="r2", call_id="c2")
    led.mark_retained("r2")                        # dispatched → retained, still counting
    assert _state(repo, "r2") == STATE_RETAINED
    assert counting_total(project_reservations(read_events(repo, "P1"), "A1")) == 6.0


def test_mark_retained_then_release_is_a_noop_dispatched_never_released(repo):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    led.mark_retained("r1")
    led.release("r1")                              # FR-033: a dispatched reservation is never released
    assert _state(repo, "r1") == STATE_RETAINED


def test_release_and_retain_are_idempotent(repo):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    led.release("r1")
    led.release("r1")                              # no second event, no error
    assert _state(repo, "r1") == STATE_RELEASED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_credit_ledger.py -k "release or retained" -q`
Expected: FAIL — `AttributeError: 'AttemptCreditLedger' object has no attribute 'release'`.

- [ ] **Step 3: Write minimal implementation** (append methods to `AttemptCreditLedger`)

```python
    def release(self, reservation_id: str) -> None:
        with self._lock:
            res = project_reservations(read_events(self._repo, self._stream), self._attempt_id)
            r = res.get(reservation_id)
            if r is None or r.state != STATE_OPEN:
                return  # idempotent: only open→released; a dispatched reservation is never released
            self._cas_append("AttemptCreditReleased", ("release", reservation_id),
                             {"reservation_id": reservation_id})

    def mark_retained(self, reservation_id: str) -> None:
        with self._lock:
            res = project_reservations(read_events(self._repo, self._stream), self._attempt_id)
            r = res.get(reservation_id)
            if r is None or r.state != STATE_OPEN:
                return  # idempotent: only open→retained
            self._cas_append("AttemptCreditRetained", ("retain", reservation_id),
                             {"reservation_id": reservation_id})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_credit_ledger.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/credit_ledger.py tests/integration/test_self_improvement_credit_ledger.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T8): AttemptCreditLedger.release/mark_retained (open→released/retained)"
```

---

### Task 9: `AttemptCreditLedger.reconcile` (retained → reconciled)

**Files:**
- Modify: `src/llmxive/self_improvement/credit_ledger.py`
- Test: `tests/integration/test_self_improvement_credit_ledger.py` (extend)

**Interfaces:**
- Produces:
  - `def reconcile(self, reconciled_ledger_ids: set[str]) -> list[str]` — FR-033 (c)/(d): for each `retained` reservation whose `reservation_id` is in `reconciled_ledger_ids` (the 026 daily-ledger reservation ids that `reservations.reconcile_settled` has moved to `reconciled`), append `AttemptCreditReconciled` (`retained → reconciled`). Returns the ids moved. Idempotent (already `reconciled` → skipped). This is the consumer side of "its reconciliation consumes the route_audit reservation events + 026's `reconcile_settled`" (Key Entities line 229): the caller passes 026's reconciled ids; slice-1 keeps the 026 wiring at the call boundary.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/integration/test_self_improvement_credit_ledger.py
from llmxive.self_improvement.credit_ledger import STATE_RECONCILED


def test_reconcile_moves_retained_to_reconciled(repo):
    led = _ledger(repo, budget=100.0)
    for rid in ("r1", "r2"):
        led.reserve(3.0, reservation_id=rid, call_id=f"c{rid}")
        led.mark_retained(rid)
    moved = led.reconcile({"r1"})                  # 026 reconciled r1 only
    assert moved == ["r1"]
    assert _state(repo, "r1") == STATE_RECONCILED
    assert _state(repo, "r2") == STATE_RETAINED    # not in the set → unchanged
    assert led.reconcile({"r1"}) == []             # idempotent: already reconciled
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_credit_ledger.py -k reconcile -q`
Expected: FAIL — `AttributeError: ... 'reconcile'`.

- [ ] **Step 3: Write minimal implementation** (append method)

```python
    def reconcile(self, reconciled_ledger_ids: set[str]) -> list[str]:
        with self._lock:
            res = project_reservations(read_events(self._repo, self._stream), self._attempt_id)
            moved: list[str] = []
            for rid, r in res.items():
                if r.state == STATE_RETAINED and rid in reconciled_ledger_ids:
                    self._cas_append("AttemptCreditReconciled", ("reconcile", rid),
                                     {"reservation_id": rid})
                    moved.append(rid)
            return moved
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_credit_ledger.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/credit_ledger.py tests/integration/test_self_improvement_credit_ledger.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T9): AttemptCreditLedger.reconcile (retained→reconciled)"
```

---

### Task 10: `EventStoreRouteAudit.record` (durable audit sink)

**Files:**
- Create: `src/llmxive/self_improvement/audit_sink.py`
- Test: `tests/integration/test_self_improvement_audit_sink.py`

**Interfaces:**
- Consumes: the slice-0 event dataclasses (`from llmxive.model_selection.attempt_hooks import ChainResolved, SelectionFailure, ReservationOpened, DispatchStarted, DispatchCompleted, DispatchUnknown, CandidateOutcome`), `ModelRef`, `SnapshotProvenance`; `_atomic_write_or_check`, `stream_dir`, `_commit_event`, `LaneAppendError` (Tasks 2-3); `Event`, `derive_event_id` (Task 1).
- Produces:
  - `class EventStoreRouteAudit` — implements the slice-0 `RouteAudit` protocol. Constructor: `EventStoreRouteAudit(*, repo: Path, problem_id: str, attempt_id: str, actor: str, clock: Callable[[], str])`.
  - `def record(self, event) -> None` — serialize the slice-0 audit event to a lane `Event` (`event_type = type(event).__name__`, lane `event_id = derive_event_id(problem_id, "audit\x00" + event.event_id)`, `payload = _audit_payload(event)` — a JSON-safe dict of the audit event's fields, `ModelRef`/`SnapshotProvenance` flattened), then `_atomic_write_or_check` (byte-identical → idempotent no-op; conflict → `LaneAppendError`, which `emit_audit` in `execute` normalizes to `RouteAuditError`), and `_commit_event` on first write. The original audit `event_id` is stored in `payload["audit_event_id"]` so projections can correlate.
  - `_audit_payload(event) -> dict` — module helper producing a stable JSON dict: scalar fields verbatim; a `ModelRef` → `{"backend","serving_endpoint","model_id","model_family","vendor"}`; a `candidates` tuple → list of those dicts; a `snapshot_provenance` mapping → `{k: {"source","observed_at" (isoformat), "age_s"}}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_audit_sink.py
import subprocess

import pytest

from llmxive.model_selection.attempt_hooks import CandidateOutcome, DispatchCompleted
from llmxive.model_selection.attempt_hooks import RouteAuditError, emit_audit
from llmxive.model_selection.types import ModelRef
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.event_store import read_events


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "root")
    return tmp_path


def _ref():
    return ModelRef(backend="dartmouth", serving_endpoint="dartmouth", model_id="qwen.qwen3.5-122b",
                    model_family="qwen3.5", vendor="qwen")


def _sink(repo):
    return EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1", actor="reviewer",
                               clock=lambda: "2026-07-24T00:00:00+00:00")


def test_record_persists_and_is_idempotent(repo):
    sink = _sink(repo)
    ev = CandidateOutcome(route_id="R", candidate_index=0, candidate=_ref(), outcome="success", reason="")
    sink.record(ev)
    sink.record(ev)  # byte-identical replay → idempotent no-op
    events = [e for e in read_events(repo, "P1") if e.event_type == "CandidateOutcome"]
    assert len(events) == 1 and events[0].payload["outcome"] == "success"


def test_conflicting_payload_under_same_audit_id_raises_via_emit_audit(repo):
    sink = _sink(repo)
    sink.record(DispatchCompleted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="x"))
    conflict = DispatchCompleted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="DIFFERENT")
    # same audit event_id ("R:candidate:0:dispatch-completed"), different payload → integrity raise;
    # emit_audit normalizes the sink's LaneAppendError to route-fatal RouteAuditError.
    with pytest.raises(RouteAuditError):
        emit_audit(sink, conflict)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_audit_sink.py -q`
Expected: FAIL — `ModuleNotFoundError: ... audit_sink`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/audit_sink.py
"""The event-sourced ``RouteAudit`` sink (FR-033a) — the concrete lane
implementation of the slice-0 ``RouteAudit`` protocol. ``record`` durably persists
each audit event (append-only, collision-raising); ``claim_dispatch`` (Task 11) is
the atomic dispatch boundary. Together they populate the credit reconciliation
(reservation events) and ``InvocationIdentity`` (chain provenance) channels."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path

from llmxive.model_selection.attempt_hooks import DispatchStarted
from llmxive.model_selection.types import ModelRef, SnapshotProvenance
from llmxive.self_improvement.event_store import _atomic_write_or_check, _commit_event, stream_dir
from llmxive.self_improvement.events import Event, derive_event_id


def _ref_dict(ref: ModelRef) -> dict:
    return {"backend": ref.backend, "serving_endpoint": ref.serving_endpoint,
            "model_id": ref.model_id, "model_family": ref.model_family, "vendor": ref.vendor}


def _prov_dict(prov: Mapping[str, SnapshotProvenance]) -> dict:
    return {k: {"source": v.source, "observed_at": v.observed_at.isoformat(), "age_s": v.age_s}
            for k, v in prov.items()}


def _audit_payload(event) -> dict:
    out: dict = {"audit_event_id": event.event_id}
    for f in fields(event):
        if f.name == "event_id":
            continue
        val = getattr(event, f.name)
        if isinstance(val, ModelRef):
            val = _ref_dict(val)
        elif f.name == "candidates":
            val = [_ref_dict(r) for r in val]
        elif f.name == "snapshot_provenance":
            val = _prov_dict(val)
        elif isinstance(val, tuple):
            val = list(val)
        out[f.name] = val
    return out


class EventStoreRouteAudit:
    def __init__(self, *, repo: Path, problem_id: str, attempt_id: str, actor: str,
                 clock: Callable[[], str]) -> None:
        self._repo = repo
        self._stream = problem_id
        self._attempt_id = attempt_id
        self._actor = actor
        self._clock = clock

    def _lane_event(self, event) -> Event:
        return Event(
            event_id=derive_event_id(self._stream, "audit\x00" + event.event_id),
            event_type=type(event).__name__, stream=self._stream, actor=self._actor,
            payload=_audit_payload(event), timestamp=self._clock(), attempt_id=self._attempt_id,
        )

    def _write(self, event) -> bool:
        lane = self._lane_event(event)
        from llmxive.self_improvement.events import event_to_json
        created = _atomic_write_or_check(
            stream_dir(self._repo, self._stream) / f"{lane.event_id}.json", event_to_json(lane)
        )
        if created:
            _commit_event(self._repo, lane)
        return created

    def record(self, event) -> None:
        self._write(event)  # bool ignored — record is idempotent either way; conflict raises LaneAppendError

    def claim_dispatch(self, event: DispatchStarted) -> bool:  # Task 11
        raise NotImplementedError
```

(`is_dataclass` import is unused here — drop it to stay ruff-clean; it appears because a later revision may use it. Keep imports minimal.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_audit_sink.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/audit_sink.py tests/integration/test_self_improvement_audit_sink.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T10): EventStoreRouteAudit.record (durable, collision-raising)"
```

---

### Task 11: `EventStoreRouteAudit.claim_dispatch` (atomic dispatch boundary)

**Files:**
- Modify: `src/llmxive/self_improvement/audit_sink.py`
- Test: `tests/integration/test_self_improvement_audit_sink.py` (extend)

**Interfaces:**
- Produces:
  - `def claim_dispatch(self, event: DispatchStarted) -> bool` — the atomic claim (slice-0 contract): `_write(event)` returns `True` iff THIS call created the `DispatchStarted` file (O_EXCL first-writer) → own the dispatch; a byte-identical existing file → `_write` returns `False` → replay (caller MUST NOT re-dispatch); a DIFFERENT payload under the same `event_id` → `_write` raises `LaneAppendError` (a conflicting dispatch masquerading as a replay), which `execute` normalizes to route-fatal `RouteAuditError`. The O_EXCL create is atomic across concurrent workers (a genuine unique-insert), so exactly one claimant gets `True`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/integration/test_self_improvement_audit_sink.py
from concurrent.futures import ThreadPoolExecutor

from llmxive.model_selection.attempt_hooks import DispatchStarted


def test_claim_dispatch_first_true_replay_false(repo):
    sink = _sink(repo)
    ds = DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id=None)
    assert sink.claim_dispatch(ds) is True     # first claim owns the dispatch
    assert sink.claim_dispatch(ds) is False    # byte-identical replay → do NOT re-dispatch


def test_claim_dispatch_conflicting_payload_raises(repo):
    sink = _sink(repo)
    sink.claim_dispatch(DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="a"))
    from llmxive.self_improvement.event_store import LaneAppendError
    with pytest.raises(LaneAppendError):
        sink.claim_dispatch(DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="b"))


def test_claim_dispatch_is_atomic_under_concurrency(repo):
    # O_EXCL unique-insert: race N threads on ONE DispatchStarted → exactly one True.
    sink = _sink(repo)
    ds = DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id=None)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _i: sink.claim_dispatch(ds), range(8)))
    assert results.count(True) == 1  # exactly one claimant won the dispatch
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_audit_sink.py -k claim -q`
Expected: FAIL — `NotImplementedError`.

- [ ] **Step 3: Write minimal implementation** (replace the `claim_dispatch` stub)

```python
    def claim_dispatch(self, event: DispatchStarted) -> bool:
        # The O_EXCL create in _write IS the atomic claim: True = this caller created
        # the DispatchStarted (own the dispatch); False = a byte-identical replay
        # already recorded (MUST NOT re-dispatch); a conflicting payload raises
        # LaneAppendError (→ route-fatal RouteAuditError via execute's emit path).
        return self._write(event)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_audit_sink.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/audit_sink.py tests/integration/test_self_improvement_audit_sink.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T11): EventStoreRouteAudit.claim_dispatch (atomic O_EXCL boundary)"
```

---

### Task 12: `DispatchUnknown` reconciliation

**Files:**
- Modify: `src/llmxive/self_improvement/audit_sink.py`
- Test: `tests/integration/test_self_improvement_audit_sink.py` (extend)

**Interfaces:**
- Produces (module functions):
  - `def dangling_dispatches(events: list[Event]) -> list[dict]` — from a stream's audit events, return the payloads of every `DispatchStarted` that has NO matching `DispatchCompleted` (same `route_id` + `candidate_index`, matched via `payload["route_id"]`/`payload["candidate_index"]`) and no existing `DispatchUnknown` — the crash-window residue (FR-033a: "an unresolved `dispatch_started → dispatch_unknown`").
  - `def reconcile_unknown(repo: Path, *, problem_id: str, attempt_id: str, actor: str, clock: Callable[[], str]) -> list[str]` — for each dangling `DispatchStarted`, `record` a `DispatchUnknown` (built from the DispatchStarted's `route_id`/`candidate_index`/`candidate`/`reservation_id`). Returns the `route_id`s reconciled. Idempotent (a second run finds none dangling). The lane then fails the Attempt closed and leaves the reservation `retained` (the credit ledger's `mark_retained` already ran pre-dispatch/at the crash).

- [ ] **Step 1: Write the failing test**

```python
# add to tests/integration/test_self_improvement_audit_sink.py
from llmxive.model_selection.attempt_hooks import DispatchStarted
from llmxive.self_improvement.audit_sink import reconcile_unknown


def test_reconcile_marks_dangling_dispatch_unknown(repo):
    sink = _sink(repo)
    # a DispatchStarted with no DispatchCompleted = a crash between dispatch and completion
    sink.claim_dispatch(DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="x"))
    moved = reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="recon",
                              clock=lambda: "2026-07-24T00:01:00+00:00")
    assert moved == ["R"]
    types = [e.event_type for e in read_events(repo, "P1")]
    assert "DispatchUnknown" in types
    # idempotent: a second reconcile finds nothing dangling
    assert reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="recon",
                             clock=lambda: "2026-07-24T00:02:00+00:00") == []


def test_completed_dispatch_is_not_dangling(repo):
    sink = _sink(repo)
    sink.claim_dispatch(DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="x"))
    from llmxive.model_selection.attempt_hooks import DispatchCompleted
    sink.record(DispatchCompleted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id="x"))
    assert reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="recon",
                             clock=lambda: "2026-07-24T00:01:00+00:00") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_audit_sink.py -k reconcile_marks -q`
Expected: FAIL — `ImportError: cannot import name 'reconcile_unknown'`.

- [ ] **Step 3: Write minimal implementation** (append to `audit_sink.py`)

```python
from llmxive.model_selection.attempt_hooks import DispatchUnknown
from llmxive.self_improvement.event_store import read_events


def dangling_dispatches(events: list[Event]) -> list[dict]:
    started: dict[tuple, dict] = {}
    completed: set[tuple] = set()
    unknown: set[tuple] = set()
    for e in events:
        p = e.payload
        if e.event_type in {"DispatchStarted", "DispatchCompleted", "DispatchUnknown"}:
            key = (p["route_id"], p["candidate_index"])
            if e.event_type == "DispatchStarted":
                started[key] = p
            elif e.event_type == "DispatchCompleted":
                completed.add(key)
            else:
                unknown.add(key)
    return [p for key, p in started.items() if key not in completed and key not in unknown]


def reconcile_unknown(repo: Path, *, problem_id: str, attempt_id: str, actor: str,
                      clock: Callable[[], str]) -> list[str]:
    sink = EventStoreRouteAudit(repo=repo, problem_id=problem_id, attempt_id=attempt_id,
                                actor=actor, clock=clock)
    moved: list[str] = []
    for p in dangling_dispatches(read_events(repo, problem_id)):
        ref = ModelRef(**p["candidate"])
        sink.record(DispatchUnknown(route_id=p["route_id"], candidate_index=p["candidate_index"],
                                    candidate=ref, reservation_id=p.get("reservation_id")))
        moved.append(p["route_id"])
    return moved
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_audit_sink.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/audit_sink.py tests/integration/test_self_improvement_audit_sink.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T12): DispatchUnknown reconciliation (crash-window residue)"
```

---

### Task 13: `InvocationIdentity` + `build_invocation_identity`

**Files:**
- Create: `src/llmxive/self_improvement/invocation_identity.py`
- Test: `tests/unit/test_self_improvement_invocation_identity.py`

**Interfaces:**
- Consumes: the lane audit `Event`s for one `route_id` (from `read_events`, filtered).
- Produces:
  - `@dataclass(frozen=True) class IndependenceDegraded`: `primary_profile: str`, `fallback_profile: str`, `primary_failure: Mapping[str, object]` (`{exception_type, message, requirement_digest, snapshot_provenance}`), `relaxed_constraints: tuple[str, ...]` (`("family_independence", "snapshot_freshness")`).
  - `@dataclass(frozen=True) class InvocationIdentity` (Key Entities line 227): `actor_instance_id: str`, `model: str`, `backend: str`, `family: str`, `prompt_digest: str`, `context_digest: str`, `selection_policy_version: int`, `snapshot_digest: str`, `route_outcome: str`, `degradation: IndependenceDegraded | None = None`.
  - `def build_invocation_identity(audit_events: list[Event], *, route_id: str) -> InvocationIdentity | None` — from the audit events sharing `route_id`: use the `ChainResolved` (prompt/context/snapshot digests, `selection_policy_version`) + the `DispatchCompleted` candidate (model/backend/family that ACTUALLY ran); `actor_instance_id = route_id`. `route_outcome`: if a `SelectionFailure` event ALSO exists for this `route_id` → `"independence_degraded"` with `degradation` built from the SelectionFailure payload (`primary_profile="independent_review"`, `fallback_profile="deep_review"`, `primary_failure` = its `{exception_type, message, requirement_digest, snapshot_provenance}`, `relaxed_constraints=("family_independence","snapshot_freshness")`); else `"success"`. Returns `None` if there is no successful `DispatchCompleted` (nothing ran) — the caller treats that as a failed logical call.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_invocation_identity.py
from llmxive.self_improvement.events import Event
from llmxive.self_improvement.invocation_identity import build_invocation_identity


def _audit(etype, payload, eid="x"):
    return Event(event_id=eid, event_type=etype, stream="P1", actor="a", payload=payload,
                 timestamp="2026-07-24T00:00:00+00:00", attempt_id="A1")


_REF = {"backend": "dartmouth", "serving_endpoint": "dartmouth", "model_id": "gemma-3-27b",
        "model_family": "gemma", "vendor": "google"}


def _chain_resolved(route_id):
    return _audit("ChainResolved", {"route_id": route_id, "prompt_digest": "pd", "context_digest": "cd",
                                    "snapshot_digest": "sd", "selection_policy_version": 3,
                                    "candidates": [_REF]}, eid="c")


def _completed(route_id):
    return _audit("DispatchCompleted", {"route_id": route_id, "candidate_index": 0,
                                        "candidate": _REF, "reservation_id": None}, eid="d")


def _selection_failure(route_id):
    return _audit("SelectionFailure", {"route_id": route_id, "exception_type": "ModelUnavailable",
                                       "message": "no independent family live", "requirement_digest": "rq",
                                       "snapshot_provenance": {}}, eid="s")


def test_normal_success_identity():
    ii = build_invocation_identity([_chain_resolved("R"), _completed("R")], route_id="R")
    assert ii is not None
    assert ii.model == "gemma-3-27b" and ii.family == "gemma" and ii.backend == "dartmouth"
    assert ii.prompt_digest == "pd" and ii.selection_policy_version == 3
    assert ii.route_outcome == "success" and ii.degradation is None
    assert ii.actor_instance_id == "R"


def test_reroute_records_independence_degraded():
    # attempt-1 (independent_review) → SelectionFailure; attempt-2 (deep_review) → success,
    # both under the SAME route_id → the projection derives independence_degraded.
    events = [_selection_failure("R"), _chain_resolved("R"), _completed("R")]
    ii = build_invocation_identity(events, route_id="R")
    assert ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == "independent_review"
    assert ii.degradation.fallback_profile == "deep_review"
    assert ii.degradation.primary_failure["exception_type"] == "ModelUnavailable"
    assert ii.degradation.relaxed_constraints == ("family_independence", "snapshot_freshness")


def test_no_dispatch_returns_none():
    assert build_invocation_identity([_selection_failure("R")], route_id="R") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_invocation_identity.py -q`
Expected: FAIL — `ModuleNotFoundError: ... invocation_identity`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/invocation_identity.py
"""The audit-derived ``InvocationIdentity`` (FR-002/FR-033a, Key Entities line 227)
— sourced ENTIRELY from ``route_chat``'s ``route_audit`` events for one route_id,
because ``route_chat``'s bare ``ChatResponse`` carries none of it. ``route_outcome``
is derived: a SelectionFailure + a successful DispatchCompleted under one route_id is
the two-attempt reroute's fingerprint → ``independence_degraded`` (FR-002)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from llmxive.self_improvement.events import Event

_RELAXED = ("family_independence", "snapshot_freshness")


@dataclass(frozen=True)
class IndependenceDegraded:
    primary_profile: str
    fallback_profile: str
    primary_failure: Mapping[str, object]
    relaxed_constraints: tuple[str, ...]


@dataclass(frozen=True)
class InvocationIdentity:
    actor_instance_id: str
    model: str
    backend: str
    family: str
    prompt_digest: str
    context_digest: str
    selection_policy_version: int
    snapshot_digest: str
    route_outcome: str
    degradation: IndependenceDegraded | None = None


def build_invocation_identity(audit_events: list[Event], *, route_id: str) -> InvocationIdentity | None:
    evs = [e for e in audit_events if e.payload.get("route_id") == route_id]
    chain = next((e for e in evs if e.event_type == "ChainResolved"), None)
    completed = next((e for e in evs if e.event_type == "DispatchCompleted"), None)
    if chain is None or completed is None:
        return None  # nothing actually ran → a failed logical call, no identity
    ref = completed.payload["candidate"]  # the model that ACTUALLY ran
    failure = next((e for e in evs if e.event_type == "SelectionFailure"), None)
    if failure is not None:
        p = failure.payload
        degradation = IndependenceDegraded(
            primary_profile="independent_review", fallback_profile="deep_review",
            primary_failure={"exception_type": p["exception_type"], "message": p["message"],
                             "requirement_digest": p["requirement_digest"],
                             "snapshot_provenance": p.get("snapshot_provenance", {})},
            relaxed_constraints=_RELAXED,
        )
        outcome = "independence_degraded"
    else:
        degradation = None
        outcome = "success"
    cp = chain.payload
    return InvocationIdentity(
        actor_instance_id=route_id, model=ref["model_id"], backend=ref["backend"],
        family=ref["model_family"], prompt_digest=cp["prompt_digest"], context_digest=cp["context_digest"],
        selection_policy_version=int(cp["selection_policy_version"]), snapshot_digest=cp["snapshot_digest"],
        route_outcome=outcome, degradation=degradation,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_invocation_identity.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/invocation_identity.py tests/unit/test_self_improvement_invocation_identity.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T13): InvocationIdentity + audit-derived route_outcome"
```

---

### Task 14: Integration — `execute()` drives the real ledger + sink end to end

**Files:**
- Test: `tests/integration/test_self_improvement_execute_wiring.py`
- (No production change — this proves the slice-0 `execute()` consumes the Task 7/11 implementations unchanged.)

**Interfaces:**
- Consumes: `execute` (`llmxive.model_selection.execute`), `AttemptCreditLedger`, `EventStoreRouteAudit`, `read_events`, `project_reservations`. Reuse the slice-0 paid-chain integration fixtures (copy the minimal `_paid_chain`/`ScriptedBackend`/`_observer`/`_balance` helpers from `tests/integration/test_model_selection_execute.py`, or import them if exposed).

**Interfaces produced:** none (test-only). This task's deliverable is the proof that the two protocol implementations satisfy `execute()`'s expectations: a paid dispatch opens an Attempt reservation (`open`), the success path retains it (`mark_retained` → `retained`), and the audit stream carries the full outbox lifecycle (`ChainResolved → DispatchStarted → DispatchCompleted → CandidateOutcome`), from which `build_invocation_identity` reconstructs the winner.

- [ ] **Step 1: Write the failing test** (the wiring may reveal a payload-shape mismatch between what `execute` emits and what the sink/ledger expect — that is exactly what this task catches)

```python
# tests/integration/test_self_improvement_execute_wiring.py
# Reuse the slice-0 paid fixtures. Import the helpers already used by
# tests/integration/test_model_selection_execute.py (repo, _paid_chain, _observer,
# _balance, _ok_factory, MSG, LOCAL_CFG, NOW, CLAUDE) — see that file for the exact
# definitions; this test constructs the REAL lane ledger + sink as the hooks.
import subprocess

import pytest

from llmxive.model_selection.execute import execute
from llmxive.model_selection.types import ExecutionOptions
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.credit_ledger import STATE_RETAINED, project_reservations
from llmxive.self_improvement.event_store import read_events
from llmxive.self_improvement.invocation_identity import build_invocation_identity

# ... (paste the slice-0 _paid_chain / _ok_factory / _observer / _balance / repo fixture
#      / MSG / LOCAL_CFG / NOW / CLAUDE helpers here, or refactor them into a shared
#      tests/integration/_execute_fixtures.py in this task and import from both files.)


def test_execute_opens_retains_reservation_and_records_full_audit_lifecycle(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    clock = lambda: "2026-07-24T00:00:00+00:00"
    ledger = AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                                 attempt_budget_credits=1000.0, actor="exec", clock=clock)
    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1", actor="exec", clock=clock)

    result = execute(
        _paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
        backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
        credit_observer=_observer(), balance_fetch=_balance(), now=NOW,
        reservation_authority=ledger, route_audit=sink, route_id="R1",
    )
    assert result.reservation_id is not None

    # The Attempt reservation was opened, then retained on the success path.
    res = project_reservations(read_events(repo, "P1"), "A1")
    assert res[result.reservation_id].state == STATE_RETAINED

    # The full outbox lifecycle is durable in the audit stream.
    types = {e.event_type for e in read_events(repo, "P1")}
    assert {"ChainResolved", "DispatchStarted", "DispatchCompleted", "CandidateOutcome"} <= types

    # InvocationIdentity reconstructs the winner from the audit events alone.
    ii = build_invocation_identity(read_events(repo, "P1"), route_id="R1")
    assert ii is not None and ii.model == CLAUDE and ii.route_outcome == "success"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_execute_wiring.py -q`
Expected: initially FAIL — either an import/fixture gap or a payload-shape mismatch surfaced by real wiring. Fix the **code** (the sink/ledger payload shapes) until the test passes; never weaken the assertions.

- [ ] **Step 3 (if the wiring test reveals a defect): fix the implementation**

If `execute` emits a field the sink's `_audit_payload` mishandles, or the ledger's `call_id` (derived by `execute` from `route_id`) does not round-trip, fix `audit_sink.py`/`credit_ledger.py` — the wiring test is the authority on the real contract. Re-run until green.

- [ ] **Step 4: Run the full focused suite**

Run: `pytest tests/integration/test_self_improvement_execute_wiring.py tests/integration/test_self_improvement_credit_ledger.py tests/integration/test_self_improvement_audit_sink.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_self_improvement_execute_wiring.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(025 slice-1 T14): execute() drives the real AttemptCreditLedger + EventStoreRouteAudit"
```

---

# Subsystem C — Proposal-review two-attempt independence reroute

**Why this is entirely in `convergence/` + one router plumbing gap (FR-002, spec line 283).** Convergence reviewers ALREADY route through `route_chat` (via `chat_with_model_fallback` → `_walker_route` → `route_chat`), and `route_chat` already accepts `independence_against` + `route_audit` + `route_id`. But `chat_with_model_fallback`/`_walker_route` do NOT forward those params, and `_walker_route` converts `ModelUnavailable` → `BackendUnavailable` before the reviewer can see it. So the reroute needs (1) that plumbing gap closed, and (2) new wiring in `LLMReviewer` — `run_convergence` itself is unchanged. No new canonical profile: reuse the delivered `independent_review` + `deep_review`.

### Task 15: Plumb `independence_against` / `route_audit` / `route_id` / `reraise_model_unavailable` through the router

**Files:**
- Modify: `src/llmxive/backends/router.py` (`chat_with_model_fallback` lines 289-317; `_walker_route` lines 230-286)
- Test: `tests/unit/test_router_independence_plumbing.py`

**Interfaces:**
- Consumes: `route_chat` (already called by `_walker_route`); `IndependenceBaseline`, `ModelUnavailable` (`model_selection.types`); `RouteAudit` (`model_selection.attempt_hooks`).
- Produces (extended signatures — all new params default to a behavior-preserving no-op):
  - `chat_with_model_fallback(backend, messages, *, model, max_tokens=None, temperature=None, overrides=None, profile="standard_generation", independence_against: "IndependenceBaseline | None" = None, route_audit=None, route_id: str | None = None, reraise_model_unavailable: bool = False) -> ChatResponse` — forwards the four new params to `_walker_route`.
  - `_walker_route(..., independence_against=None, route_audit=None, route_id=None, reraise_model_unavailable=False)` — forwards `independence_against`/`route_audit`/`route_id` to `route_chat`, and splits the exception handler: `ModelUnavailable` propagates unchanged when `reraise_model_unavailable=True` (the reroute needs the RAW exception), else converts to `BackendUnavailable` as today; `ChainExhausted` always converts to `BackendUnavailable` (a real outage, never a reroute trigger).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_router_independence_plumbing.py
import pytest

from llmxive.backends.base import BackendUnavailable
from llmxive.backends.router import chat_with_model_fallback
from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable


class _CaptureBackend:
    name = "dartmouth"


def test_new_params_default_to_behavior_preserving(monkeypatch):
    # With no new params, _walker_route calls route_chat with exactly the prior kwargs.
    seen = {}

    def _fake_route_chat(messages, **kw):
        seen.update(kw)
        class R: text = "ok"
        return R()

    monkeypatch.setattr("llmxive.model_selection.route.route_chat", _fake_route_chat)
    chat_with_model_fallback(_CaptureBackend(), [], model=None, max_tokens=64, profile="deep_review")
    assert seen["independence_against"] is None and seen["route_audit"] is None and seen["route_id"] is None


def test_independence_and_audit_are_forwarded(monkeypatch):
    seen = {}

    def _fake_route_chat(messages, **kw):
        seen.update(kw)
        class R: text = "ok"
        return R()

    monkeypatch.setattr("llmxive.model_selection.route.route_chat", _fake_route_chat)
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    sink = object()
    chat_with_model_fallback(_CaptureBackend(), [], model=None, max_tokens=64,
                             profile="independent_review", independence_against=base,
                             route_audit=sink, route_id="RID")
    assert seen["independence_against"] is base and seen["route_audit"] is sink and seen["route_id"] == "RID"


def test_reraise_model_unavailable_lets_it_through(monkeypatch):
    def _boom(messages, **kw):
        raise ModelUnavailable("no independent family live")

    monkeypatch.setattr("llmxive.model_selection.route.route_chat", _boom)
    # default: converted to BackendUnavailable (unchanged behavior)
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_CaptureBackend(), [], model=None, max_tokens=64, profile="independent_review")
    # reroute caller: raw ModelUnavailable propagates
    with pytest.raises(ModelUnavailable):
        chat_with_model_fallback(_CaptureBackend(), [], model=None, max_tokens=64,
                                 profile="independent_review", reraise_model_unavailable=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_router_independence_plumbing.py -q`
Expected: FAIL — `TypeError: chat_with_model_fallback() got an unexpected keyword argument 'independence_against'`.

- [ ] **Step 3: Write minimal implementation**

Update `chat_with_model_fallback` (add the four params + forward them):

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
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
) -> ChatResponse:
    return _walker_route(
        backend, messages, model=model,
        max_tokens=REASONING_MAX_TOKENS if max_tokens is None else max_tokens,
        temperature=temperature, overrides=overrides, profile=profile,
        independence_against=independence_against, route_audit=route_audit,
        route_id=route_id, reraise_model_unavailable=reraise_model_unavailable,
    )
```

Update `_walker_route` (add the four params; forward the first three to `route_chat`; split the except):

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
            independence_against=independence_against, route_audit=route_audit, route_id=route_id,
        )
    except ModelUnavailable as exc:
        if reraise_model_unavailable:
            raise  # the reroute (FR-002) needs the RAW ModelUnavailable to trigger attempt 2
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate (outage or ineligible): {exc}"
        ) from exc
    except ChainExhausted as exc:
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate (outage or ineligible): {exc}"
        ) from exc
```

Add module-top typing imports guarded to avoid the import cycle (the router imports `model_selection` function-locally elsewhere): use string annotations (already shown with quotes) so no new module-top import of `model_selection` is needed. `IndependenceBaseline`/`RouteAudit`/`ModelUnavailable` remain function-locally imported (as today).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_router_independence_plumbing.py -q`
Expected: PASS (3 passed).

Also run the existing router/reviewer suites to confirm behavior preservation:
Run: `pytest tests/unit/test_backends_router.py tests/unit -k walker -q`
Expected: PASS (no regressions).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/backends/router.py tests/unit/test_router_independence_plumbing.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T15): plumb independence_against/route_audit/route_id + reraise through the router"
```

---

### Task 16: `LLMReviewer` two-attempt independence reroute

**Files:**
- Modify: `src/llmxive/convergence/llm_reviewer.py` (`__init__` lines 819-877; `_call_backend` lines 1148-1167)
- Test: `tests/unit/test_llm_reviewer_reroute.py`

**Interfaces:**
- Consumes: `chat_with_model_fallback` (Task 15); `IndependenceBaseline`, `ModelUnavailable` (`model_selection.types`); `RouteAudit` (`model_selection.attempt_hooks`).
- Produces (extended `LLMReviewer.__init__` — all new params default to `None`, preserving the single-attempt path byte-for-byte):
  - New `__init__` keyword params: `independence_against: IndependenceBaseline | None = None`, `fallback_profile: str | None = None`, `route_audit: RouteAudit | None = None`. Stored as `self._independence_against`, `self._fallback_profile`, `self._route_audit`.
  - `_call_backend(self, messages) -> str` — unchanged when `self._independence_against is None` (the single `chat_with_model_fallback(profile=self._profile)` call). When set, delegates to `_route_review`.
  - `_route_review(self, messages) -> str` — the two-attempt reroute (FR-002): mint one `route_id = uuid.uuid4().hex` shared across both attempts (so the audit stream correlates them → `independence_degraded`); attempt 1 = `chat_with_model_fallback(profile=self._profile, independence_against=self._independence_against, route_audit=self._route_audit, route_id=route_id, reraise_model_unavailable=True)`; on `ModelUnavailable` → attempt 2 = `chat_with_model_fallback(profile=self._fallback_profile, route_audit=self._route_audit, route_id=route_id)` (no independence constraint). Returns the response text.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_llm_reviewer_reroute.py
from pathlib import Path

import pytest

from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable


def _reviewer(tmp_path, monkeypatch, **kw):
    # Stub the eager system-prompt load so we can construct a reviewer without prompt files.
    monkeypatch.setattr("llmxive.convergence.llm_reviewer._load_system_prompt", lambda **_k: "SYS")
    from llmxive.convergence.llm_reviewer import LLMReviewer
    return LLMReviewer(lens="worthwhile-improvement", stage="self_improvement_proposal",
                       backend=object(), repo_root=Path(tmp_path), **kw)


def test_no_independence_uses_single_attempt_unchanged(tmp_path, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        class R: text = "ok"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    r = _reviewer(tmp_path, monkeypatch, profile="deep_review")
    assert r._call_backend([]) == "ok"
    assert len(calls) == 1 and calls[0]["profile"] == "deep_review"
    assert "independence_against" not in calls[0] or calls[0]["independence_against"] is None


def test_reroute_falls_back_and_shares_route_id(tmp_path, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        class R: text = "fallback-ok"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    sink = object()
    r = _reviewer(tmp_path, monkeypatch, profile="independent_review",
                  fallback_profile="deep_review", independence_against=base, route_audit=sink)
    assert r._call_backend([]) == "fallback-ok"
    assert len(calls) == 2
    # attempt 1 constrained + reraise; attempt 2 unconstrained; SAME route_id + sink on both
    assert calls[0]["profile"] == "independent_review" and calls[0]["reraise_model_unavailable"] is True
    assert calls[0]["independence_against"] is base
    assert calls[1]["profile"] == "deep_review"
    assert calls[0]["route_id"] == calls[1]["route_id"]
    assert calls[0]["route_audit"] is sink and calls[1]["route_audit"] is sink


def test_reroute_returns_attempt1_when_independent_family_is_live(tmp_path, monkeypatch):
    def _fake(backend, messages, **kw):
        class R: text = "independent-ok"
        return R()  # attempt 1 succeeds → no fallback

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    r = _reviewer(tmp_path, monkeypatch, profile="independent_review", fallback_profile="deep_review",
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})))
    assert r._call_backend([]) == "independent-ok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_llm_reviewer_reroute.py -q`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'independence_against'`.

- [ ] **Step 3: Write minimal implementation**

In `LLMReviewer.__init__`, add the three keyword params (after `overrides`) and store them:

```python
        independence_against: "IndependenceBaseline | None" = None,
        fallback_profile: str | None = None,
        route_audit: "RouteAudit | None" = None,
    ) -> None:
        ...  # existing attribute assignments unchanged
        self._independence_against = independence_against
        self._fallback_profile = fallback_profile
        self._route_audit = route_audit
```

Replace `_call_backend` (keep the single-attempt path identical when independence is off):

```python
    def _call_backend(self, messages: list[ChatMessage]) -> str:
        if self._independence_against is None:
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides, profile=self._profile,
            )
            return getattr(response, "text", "") or ""
        return self._route_review(messages)

    def _route_review(self, messages: list[ChatMessage]) -> str:
        # FR-002 two-attempt reroute (proposal review): ONE route_id is shared across
        # both attempts so the route_audit stream correlates the failed independent
        # attempt with the fallback success → independence_degraded (built by
        # build_invocation_identity). No new profile — reuse the delivered two.
        import uuid

        from llmxive.model_selection.types import ModelUnavailable

        route_id = uuid.uuid4().hex
        try:
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides, profile=self._profile,
                independence_against=self._independence_against, route_audit=self._route_audit,
                route_id=route_id, reraise_model_unavailable=True,
            )
        except ModelUnavailable:
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides,
                profile=self._fallback_profile, route_audit=self._route_audit, route_id=route_id,
            )
        return getattr(response, "text", "") or ""
```

(`IndependenceBaseline`/`RouteAudit` used only in string annotations → no new module-top import needed; `ModelUnavailable` is imported function-locally, as the router does, to avoid the import cycle.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_llm_reviewer_reroute.py -q`
Expected: PASS (3 passed).

Confirm behavior preservation of the existing reviewer suite:
Run: `pytest tests/unit -k llm_reviewer -q`
Expected: PASS (no regressions — the default path is unchanged).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/llm_reviewer.py tests/unit/test_llm_reviewer_reroute.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T16): LLMReviewer two-attempt independence reroute (FR-002)"
```

---

### Task 17: `build_proposal_review_spec` + proposal-lens prompts

**Files:**
- Create: `src/llmxive/convergence/self_improvement_specs.py`
- Create: 5 proposal-lens prompt files (path per `_load_system_prompt`'s convention — see Step 1)
- Test: `tests/unit/test_self_improvement_review_spec.py`

**Interfaces:**
- Consumes: `LLMReviewer` (Task 16); `ReviewSpec`, `Reviser` (`convergence.types`); `IndependenceBaseline`; `RouteAudit`.
- Produces:
  - `PROPOSAL_STAGE = "self_improvement_proposal"`.
  - `PROPOSAL_LENSES: tuple[str, ...] = ("worthwhile-improvement", "diagnosis-correctness", "tractability", "testability", "blast-radius-sanity")` (the exact proposal lens set, Self-improvement ReviewSpec table line 278).
  - `build_proposal_review_spec(*, backend, repo_root: Path, proposer_baseline: IndependenceBaseline, reviser: Reviser, route_audit: RouteAudit | None = None) -> ReviewSpec` — one `LLMReviewer` per lens, each built with `stage=PROPOSAL_STAGE`, `profile="independent_review"`, `fallback_profile="deep_review"`, `independence_against=proposer_baseline`, `route_audit=route_audit` (the two-attempt reroute enabled); `reviser=reviser` (the proposer); `max_rounds=3`; `stage=PROPOSAL_STAGE`; `advance_stage=None` (slice-1 does not wire the pipeline transition). The lens set and independence binding are the binding SHAPE (spec line 283).

**Sub-step (Step 0, do first): confirm the prompt path convention.** Read `_load_system_prompt` in `convergence/llm_reviewer.py` to find where it reads `(stage, lens)` prompts from (e.g. `agents/prompts/<stage>/<lens>.md` under `repo_root`). Create the 5 files at that exact path for `stage="self_improvement_proposal"` and each lens, each a real review-lens system prompt (per-lens judgment guidance + a good/bad example), matching the house style of the existing research/paper reviewer prompts. This is required because `LLMReviewer.__init__` eager-loads the prompt (fail-fast) — a proposal reviewer cannot be constructed without it.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_review_spec.py
from pathlib import Path

from llmxive.convergence.self_improvement_specs import (
    PROPOSAL_LENSES, PROPOSAL_STAGE, build_proposal_review_spec,
)
from llmxive.model_selection.types import IndependenceBaseline


class _Reviser:
    def revise(self, artifacts, concerns):
        return {}


def test_proposal_spec_wires_every_lens_with_the_reroute():
    baseline = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    sink = object()
    spec = build_proposal_review_spec(
        backend=object(), repo_root=Path("."), proposer_baseline=baseline,
        reviser=_Reviser(), route_audit=sink,
    )
    assert spec.stage == PROPOSAL_STAGE and spec.max_rounds == 3
    assert tuple(r.name for r in spec.reviewers) == PROPOSAL_LENSES
    for r in spec.reviewers:
        assert r._profile == "independent_review" and r._fallback_profile == "deep_review"
        assert r._independence_against is baseline and r._route_audit is sink
```

(This test loads real prompt files created in Step 0; it constructs real `LLMReviewer`s — no mock.)

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_review_spec.py -q`
Expected: FAIL — `ModuleNotFoundError: ... self_improvement_specs`.

- [ ] **Step 3: Write minimal implementation** (after Step 0's prompt files exist)

```python
# src/llmxive/convergence/self_improvement_specs.py
"""The self-improvement lane's `run_convergence` ReviewSpec builders (FR-019,
Constitution VI). Slice 1: the PROPOSAL review (`self_improvement_proposal`) with
the FR-002 two-attempt independence reroute wired into every lens. The PATCH review
(`self_improvement_patch`, fail-closed single-attempt independence) reuses the same
LLMReviewer mechanism and is a later slice."""

from __future__ import annotations

from pathlib import Path

from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import Reviser, ReviewSpec
from llmxive.model_selection.attempt_hooks import RouteAudit
from llmxive.model_selection.types import IndependenceBaseline

PROPOSAL_STAGE = "self_improvement_proposal"
#: The proposal lens set (Self-improvement ReviewSpec table line 278). Finalizable
#: in slice 1; the SHAPE (five lenses + the reroute binding) is binding.
PROPOSAL_LENSES = (
    "worthwhile-improvement", "diagnosis-correctness", "tractability",
    "testability", "blast-radius-sanity",
)


def build_proposal_review_spec(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    reviser: Reviser,
    route_audit: RouteAudit | None = None,
) -> ReviewSpec:
    reviewers = [
        LLMReviewer(
            lens=lens, stage=PROPOSAL_STAGE, backend=backend, repo_root=repo_root,
            profile="independent_review", fallback_profile="deep_review",
            independence_against=proposer_baseline, route_audit=route_audit,
        )
        for lens in PROPOSAL_LENSES
    ]
    return ReviewSpec(
        stage=PROPOSAL_STAGE, artifacts=[], reviewers=reviewers, reviser=reviser,
        kickback_routing={}, overflow_goal="", advance_stage=None, max_rounds=3,
    )
```

(Confirm the exact `ReviewSpec(...)` required-field set against `convergence/types.py:295-313` during implementation — the fields `stage`/`artifacts`/`reviewers`/`reviser`/`kickback_routing`/`overflow_goal`/`advance_stage`/`max_rounds` are shown in the research extract; supply any additional required fields with their documented defaults.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_review_spec.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/self_improvement_specs.py agents/prompts tests/unit/test_self_improvement_review_spec.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1 T17): self_improvement_proposal ReviewSpec + proposal-lens prompts"
```

---

### Task 18: Integration — the reroute records `independence_degraded` through the real audit sink

**Files:**
- Test: `tests/integration/test_self_improvement_reroute_audit.py`

**Interfaces:**
- Consumes: `LLMReviewer` (Task 16), `EventStoreRouteAudit` (Tasks 10-11), `build_invocation_identity` (Task 13), `read_events`. Uses a real `RuntimeSnapshot` (from the `model_selection` snapshot test helpers) crafted so `select(independent_review, independence_against=<producer family>)` raises `ModelUnavailable` (no independent family live) but `select(deep_review)` succeeds — driving attempt 1 → `ModelUnavailable` → attempt 2 (fallback) through the REAL `route_chat`.

This is the end-to-end proof of Subsystem C: the reroute's two attempts, recorded through the real `EventStoreRouteAudit`, are read back by `build_invocation_identity` as `route_outcome = "independence_degraded"` (FR-002) — no mock at any layer.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_reroute_audit.py
# Build a snapshot whose ONLY live model is in the producer's family, so
# independent_review(independence_against=producer) has no eligible candidate
# (ModelUnavailable) but deep_review does. Reuse the model_selection snapshot
# builders (see tests/unit/test_model_selection_route.py::_snapshot for the shape).
import subprocess
from pathlib import Path

import pytest

from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.event_store import read_events
from llmxive.self_improvement.invocation_identity import build_invocation_identity
from llmxive.model_selection.types import IndependenceBaseline


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "root")
    return tmp_path


def test_route_chat_reroute_audit_yields_independence_degraded(repo):
    # Drive the reroute's TWO real route_chat calls (mirroring LLMReviewer._route_review)
    # against a snapshot fresh enough for deep_review but too stale for independent_review
    # (independent_review sets require_fresh_snapshot=True, max_catalog_age_s=900; deep_review
    # inherits max_catalog_age_s=3600). A catalog age of 1800s therefore FAILS attempt 1
    # (ModelUnavailable → route_chat emits SelectionFailure) and PASSES attempt 2 (deep_review
    # → ChainResolved + dispatch). This is a family-agnostic, deterministic reroute trigger.
    # Both calls share ONE route_id + the REAL sink → build_invocation_identity reads
    # independence_degraded (FR-002). No mock at any layer.
    from llmxive.backends.base import ChatMessage
    from llmxive.model_selection.route import route_chat
    from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable

    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1", actor="reviewer",
                                clock=lambda: "2026-07-24T00:00:00+00:00")
    snap = _stale_snapshot(age_s=1800.0)  # helper: adapt _snapshot(...) with a stale catalog age (see note)
    backend = ScriptedBackend({"*": "review body: this improvement is worthwhile."})
    msgs = [ChatMessage(role="user", content="review this proposal")]
    route_id = "review-route-1"

    with pytest.raises(ModelUnavailable):  # attempt 1: independent_review is fresh-required → too stale
        route_chat(msgs, profile="independent_review", max_tokens=64,
                   independence_against=IndependenceBaseline(), snapshot=snap,
                   route_audit=sink, route_id=route_id, backend_factory=lambda _n: backend)
    resp = route_chat(msgs, profile="deep_review", max_tokens=64, snapshot=snap,
                      route_audit=sink, route_id=route_id, backend_factory=lambda _n: backend)
    assert resp.text  # attempt 2 (deep_review) succeeds on the same snapshot

    events = read_events(repo, "P1")
    kinds = {e.event_type for e in events}
    assert "SelectionFailure" in kinds and "ChainResolved" in kinds  # both attempts audited
    ii = build_invocation_identity(events, route_id=route_id)  # shared route_id → correlated
    assert ii is not None and ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == "independent_review"
    assert ii.degradation.primary_failure["exception_type"] == "ModelUnavailable"
```

**Note for the implementer:** `ScriptedBackend` is the real offline backend already used by `tests/integration/test_model_selection_execute.py`; import or copy it. `_stale_snapshot(age_s)` is a small helper you write by adapting the existing `tests/unit/test_model_selection_route.py::_snapshot` builder so the catalog `SnapshotProvenance` reports `age_s=1800.0` (any value strictly between 900 and 3600 works) with an otherwise-eligible `deep`-capable model live — its precise contract: `select("independent_review", …)` raises `ModelUnavailable` on it while `select("deep_review", …)` returns a chain. If the offline snapshot cannot be aged this way, the equivalent family trigger (an `IndependenceBaseline(families=<every live deep family>)`) also forces attempt-1 `ModelUnavailable`; use whichever the existing snapshot fixtures make cleanest. This test drives `route_chat` (not `_route_review`) directly because the two-call structure is what `_route_review` performs — Task 16 already covers the reviewer's control flow; Task 18's unique value is proving REAL `route_chat` audit emission → the REAL sink → `independence_degraded`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_reroute_audit.py -q`
Expected: FAIL until the snapshot + backend fixtures are wired and Subsystem C is complete.

- [ ] **Step 3: Wire the fixtures + confirm the end-to-end path** (no new production code — this test exercises Tasks 10-16 together).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_reroute_audit.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_self_improvement_reroute_audit.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(025 slice-1 T18): reroute records independence_degraded end-to-end through the real audit sink"
```

---

## Final verification (before the whole-branch review)

- [ ] Package exports: fill `src/llmxive/self_improvement/__init__.py` with the public names later slices import (`Event`, `derive_event_id`, `read_events`, `append_event`, `LaneRevisionConflict`, `LaneAppendError`, `LaneCoordinator`, `project_coordinator`, `cas_claim`, `cas_release`, `AttemptCreditLedger`, `EventStoreRouteAudit`, `reconcile_unknown`, `InvocationIdentity`, `build_invocation_identity`). Add a test asserting they import.
- [ ] `ruff check` clean on every touched file (drop the unused `field`/`is_dataclass` imports flagged in Tasks 1/10).
- [ ] Full non-slow suite green: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → 0 failed (network-restricted-sandbox dataset/HTTP failures are environment artifacts — itemize any).
- [ ] `enforcement.py` guard passes: no model-id literal was introduced in lane code (`pytest tests/unit -k enforcement -q`).
- [ ] Commit discipline honored on every task (`PRE_COMMIT_ALLOW_NO_CONFIG=1`, trailer, HEAD moved); **nothing pushed**.

---

