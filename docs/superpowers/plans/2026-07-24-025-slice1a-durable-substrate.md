# Self-Improvement Lane — Slice 1A: Durable Substrate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the self-improvement lane's durable persistence substrate — a **genuine git-ref compare-and-swap event log** (extracted as a shared primitive from the 026 credit ledger), the singleton `LaneCoordinator` with real ownership-checked claim/release transitions, the `AttemptCreditLedger` (the slice-0 `ReservationAuthority`), the `LaneCallLedger` (the durable per-Attempt LLM-call ceiling), and the event-sourced `RouteAudit` sink whose dispatch claim is a cross-process CAS — so later slices persist and enforce on a correct foundation.

**Architecture:** Almost all of `model_selection/ledger_transport.py` is domain-agnostic git-CAS plumbing (a zero-internal-import leaf). Task 1 extracts that into `src/llmxive/git_event_log.py` — a ref-parameterized append-only CAS core — and rewires the credit ledger as a thin wrapper (its behavior stays byte-for-byte, gated by its own tests). The lane then builds every projection (`LaneCoordinator`, `AttemptCreditLedger`, audit stream) on that same core, on a dedicated lane ref, with an **authoritative per-stream sequence** the core assigns inside the CAS (so ordering never depends on wall-clock timestamps). The credit-ledger's proven CAS gives the lane real cross-process serialization, durable-on-commit semantics, and idempotent retries for free.

**Tech Stack:** Python ≥ 3.11; `pytest`; git plumbing via `subprocess` (the credit-ledger pattern); package roots `llmxive.git_event_log` and `llmxive.self_improvement`. No new third-party deps.

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from spec 025 rev 16 and the slice-0 contracts.

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
- **The LLM-call ceiling is per *Attempt*, so admission is DURABLE and cross-process (Policy Contract line 313; round-4 review F1).** Spec 025 line 313 scopes the ceiling to the Attempt — "Per Attempt: `proposer + implementer·(1 + impl_regen_retries) + [proposal: 4N_p + R·(2N_p + 2)] + [patch: 2N_q + R·(N_q + 2)]`" — NOT to one panel process. An in-memory counter would reset on every restart, retry-on-another-runner, or duplicate worker, letting one Attempt spend the ceiling repeatedly. Every logical `route_chat` invocation therefore CAS-appends a `LaneCallClaimed` event whose predicate counts prior claims for that Attempt and denies at the ceiling (Task 14), where the ceiling itself comes from the Attempt's ONE durable `AttemptConfigured` record (Task 13) — never from whichever worker's constructor argument happened to arrive first. The claim key is deterministic, so the same logical operation replays to the SAME claim and the SAME `route_id` instead of minting a fresh one — which is also what makes slice-0's dispatch idempotency reachable across a retry (`route.py:291-293`: "a caller MAY inject a durable id instead — a retried logical invocation replays the identical event ids rather than minting new ones").
- **An Attempt's LIMITS are as durable as its spend (round-5 review F1).** The call ceiling AND the credit budget are bound ONCE per Attempt by a single `AttemptConfigured` record (Task 13); every ledger verifies its constructor argument against that record and fails closed on any difference, in either direction. A durable count checked against a constructor-local bound is not a durable cap — a restarted worker, a config change, or a competing worker could simply present a bigger number.
- **Route through the chokepoint; no model-id literals in lane code (SC-008, FR-001).** `model_selection/enforcement.py` verifies this. (Slice 1A adds no model ids.)
- **Real tests, no mocks (Constitution III).** Protocol test doubles with real logic, temp-git-repo fixtures, and **multi-clone concurrency tests** (two clones of one bare remote competing on the ref) are required where the guarantee is cross-process. `unittest.mock` is not the primary path.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push.**

## Scope boundary

This plan is **Slice 1A: the durable substrate only.** The proposal-review convergence wiring (threading `route_audit`/`reservation_authority` through the reviewer + reviser, the explicit reroute/degradation event, the complete `InvocationIdentity`, the `self_improvement_proposal` `ReviewSpec` + prompts, the real `run_convergence` integration test) is **Slice 1B**, a separate plan that consumes this substrate's `EventStoreRouteAudit` + `AttemptCreditLedger` interfaces. US1's discovery *logic* (error mining, issue ranking, proposer + deterministic pre-gates) is a further follow-up.

## File Structure

- `src/llmxive/git_event_log.py` — the extracted ref-agnostic git-CAS core: `LogRef`, `AppendResult`, `append_to_log`, `read_log`, `sync_and_verify`, `bootstrap_log`, `GitLogError`/`GitLogAuthError`/`GitLogContention`, and the moved git-plumbing helpers.
- `src/llmxive/model_selection/ledger_transport.py` — **rewired** to thin wrappers over the core (behavior unchanged); keeps the credit schema (`_validate_event`, the constants), `LedgerConfig`, `ledger_config_from_env`, `bootstrap_ledger`, and `LedgerError`/`LedgerAuthError`/`LedgerContention`/`LedgerDenied` as **SUBCLASSES of the core's, plus exhaustive core→ledger translation at every entry point** (`_as_ledger_error`). See Task 1's interface block: aliases were the plan through round 6 and are WRONG — implementation proved it.
- `src/llmxive/self_improvement/events.py` — lane `Event` record (FR-011) + `validate_lane_event` (envelope + a per-type payload-validator table) + `derive_event_id` + JSON (de)serialization.
- `src/llmxive/self_improvement/lane_log.py` — the lane's store on the dedicated ref: `LANE_REF`, `LaneLogConfig(remote, expected_anchor)`, `bootstrap_lane_log`, `append`/`read` (config-threaded, seq-ordered), `LaneRevisionConflict`; thin wrappers over the shared `git_event_log` core.
- `src/llmxive/self_improvement/coordinator.py` — `LaneCoordinator` projection + `project_coordinator` + `cas_claim`/`cas_release` (ownership-checked).
- `src/llmxive/self_improvement/credit_ledger.py` — `AttemptCreditLedger` (`ReservationAuthority`) + projection + `reconcile`.
- `src/llmxive/self_improvement/attempt_config.py` — the **durable per-Attempt safety limits** (Task 13): `AttemptConfig`, `AttemptConfigMismatch`, `bind_attempt_config`, `load_attempt_config`. ONE `AttemptConfigured` event fixes the call ceiling AND the credit budget for an Attempt; every later worker verifies against it instead of trusting its own constructor argument.
- `src/llmxive/self_improvement/call_ledger.py` — the **durable per-Attempt LLM-call admission ledger** (Task 14): `LaneCallLedger`, `LaneCallCeilingExceeded`, `project_call_claims`. Enforces Policy Contract line 313's ceiling across processes and mints retry-stable `route_id`s (`derive_route_id` lives in `events.py`, see Task 2).
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
  - `read_log(repo, *, log: LogRef, validate: Callable[[dict], None]) -> list[dict]` — the current `read_events` loop, `event_dir`/`validate` parameterized. **LOCAL by design: it does NOT fetch or verify the anchor even when `log.remote` is set** (round-8 F3), mirroring the credit ledger's split where syncing is the caller's explicit decision. The consequence is sharp — on a fresh checkout with `remote=` set it returns `[]`, because an ordinary clone does not fetch these refs — so **Task 3's public `read()` MUST call `sync_and_verify` first**, with a test proving it.
  - **Absence and failure must never collapse (round-8 F2).** `None`/`[]` propagates as "empty log", and an empty log means "no claim, no reservation, no spend" to every projection — so an operational failure reported that way is fail-OPEN on an admission decision. Established discriminators: `rev-parse --verify --quiet` exits 128 for an operational failure and **1 for BOTH a missing ref and an unreadable object**, so `_rev` disambiguates with `show-ref` (which reports on the REF independently of object readability) and returns `None` ONLY for a genuinely absent ref; `ls-tree` in `read_log` is **checked** (a failed listing has empty stdout); and `_read_event_blob` — the append-only guard's read, where reporting failure as absence would let a caller append OVER a committed event — tests existence with `ls-tree` (exit 0 + empty output = absent; 128 = failure) because `cat-file` cannot distinguish the two.
  - `sync_and_verify(repo, *, log: LogRef) -> None`, `bootstrap_log(repo, *, log: LogRef, message: str, remote: str | None = None, _after_probe: Callable[[], None] | None = None) -> str` — ref-parameterized `_sync_and_verify`/`bootstrap_ledger`. `_after_probe` is a **TEST-ONLY seam (round-4 review F10)**, the bootstrap counterpart of `_after_parent`: `bootstrap_ledger`'s race window is between its remote/local existence probe and the `update-ref` + FF-push that follow (`ledger_transport.py:381-407`), so the core calls `_after_probe()` AFTER the probe decides "not yet bootstrapped" and BEFORE `commit-tree`/`update-ref`/`_push_fast_forward`. Two workers can block on a shared barrier there, guaranteeing both probed an empty ref, and then genuinely race the push — so the "exactly one genesis, the loser adopts it" branch (`ledger_transport.py:402-407`) is actually executed instead of assumed. Defaults `None` (no-op); never used in production.
  - `class GitLogError(RuntimeError)`, `class GitLogAuthError(GitLogError)`, `class GitLogContention(GitLogError)`, `class GitLogDenied(GitLogError)` (raised when a `predicate` returns `(False, reason)` — the generalization of the credit ledger's `LedgerDenied`); moved helpers `_git`, `_rev`, `_canonical`, `_read_event_blob`, `_append_commit`, `_fetch_authoritative`, `_remote_ledger_oid`, `_is_ancestor`, `_push_fast_forward`, `sync_and_verify`, and the marker/id constants (`_AUTH_FAIL_MARKERS`, `_NON_FF_MARKERS`, `_PUSH_DENY_MARKERS`, `_ZERO_OID`, `_SAFE_ID`, `_DEFAULT_GIT_IDENTITY`) — each gaining a `ref`/`event_dir`/`message_fn` parameter in place of the module global it closed over. See the extraction blueprint (`.superpowers`/scratch `extraction-design.md`) for the exact verbatim bodies and the generic/credit-specific split.
- `ledger_transport.py` keeps `LEDGER_REF`, `SCHEMA_REVISION`, `_EVENT_DIR`, `_validate_event` + its four schema constants, `LedgerConfig`, `ledger_config_from_env`, `bootstrap_ledger`, `fetch_ledger`, plus thin private shims preserving the pre-extraction signatures the money-path tests import (`_rev(repo, ref)`, `_append_commit(repo, parent, event)`, `_push_fast_forward(repo, remote, commit)`, `_remote_ledger_oid(repo, remote)`).
- **`LedgerError`/`LedgerAuthError`/`LedgerContention`/`LedgerDenied` are SUBCLASSES of the core's `GitLog*` — plus EXHAUSTIVE translation at every entry point that calls the core (`_as_ledger_error`).** Rounds 2–6 specified plain ALIASES, reasoning that the core raises the BASE class so only aliasing keeps `except Ledger*` catching it. That reasoning is sound but incomplete, and **implementation disproved the conclusion**: aliases make `type(exc).__name__` report `GitLogContention`, `execute` formats that name into its candidate notes, and the money-path assertion `"LedgerContention" in str(...)` fails (`test_model_selection_execute.py::test_reserve_ledger_error_skips_not_aborts`). A domain's error NAME is observable, not just its catchability. Subclassing alone would reintroduce the original defect; subclassing + translating at the single boundary that calls the core keeps both properties, since no `GitLog*` base instance ever reaches a credit caller. Use multiple inheritance (`LedgerAuthError(LedgerError, GitLogAuthError)`) so `except GitLogAuthError` also still works. `append_event`/`read_events` become thin wrappers passing `LEDGER_REF`/`_EVENT_DIR`/`_validate_event`/`_message_fn`, `now_field="ts"`, `finalize=None`, `identity_exclude=frozenset()`, and returning `AppendResult.commit`.

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
  - `KNOWN_EVENT_TYPES_V1: frozenset[str]` — the **Slice-1A (schema v1)** event-type vocabulary (coordinator: `ClaimAcquired`, `ClaimReleased`, `MonitorStarted`, `PromotionEnabledSet`; credit: `AttemptCreditReserved`/`Released`/`Retained`/`Reconciled`; **Attempt limits: `AttemptConfigured`** (Task 13); **call admission: `LaneCallClaimed`** (Task 14); audit: `ChainResolved`, `SelectionFailure`, `ReservationOpened`, `DispatchStarted`, `DispatchCompleted`, `DispatchUnknown`, `CandidateOutcome`; lifecycle: `ProblemDiscovered`, `Proposed`, `ProposalVerified`, `Rejected`). It is NOT the full spec-025 set (F9); a type outside it is rejected on read. Adding a type is a **vocabulary** extension (the record SHAPE is unchanged) and MUST NOT bump `SCHEMA_VERSION` — a bump would make a reader reject prior-version history (F7); extend this set and the projection handlers together.
  - `@dataclass(frozen=True) class Event` (FR-011): `event_id`, `event_type`, `stream` (a `problem_id` or `COORDINATOR_STREAM`), `actor`, `payload: Mapping`, `timestamp`, `schema_version=SCHEMA_VERSION`, `attempt_id: str | None = None`, and the four CAS anchors `expected_lane_revision`/`resulting_lane_revision`/`expected_problem_revision`/`resulting_problem_revision: int | None = None` plus `seq: int | None = None`. The store stamps all of them inside the CAS from the authoritative parent so that `seq == expected_*_revision` and `resulting_*_revision == seq + 1` (event seq=N transforms revision N → N+1); exactly one scope (lane XOR problem) is populated, matching the stream. `None` before append.
  - `derive_event_id(stream, idempotency_key) -> str` — `sha256(f"{stream}\x00{idempotency_key}")`.
  - `validate_lane_event(raw: dict) -> None` — fail-closed one-event schema (F9). **TYPES, not just presence** (round-8 F1): `event_id`/`event_type`/`problem_id`/`actor` are non-empty `str`; `schema_version`/`seq`/the populated revision anchors are non-negative `int` and **not `bool`** (`True == 1` and hashes as 1, so a boolean `seq` passes every arithmetic check and then orders the projection as position 1 — a corruption of the ORDERING authority); `attempt_id` is `None` or a non-empty `str` (the projections filter on it); the `timestamp` must carry a time AND a timezone (FR-011 records an INSTANT — `"2026-07-24"` parses fine and would order runners by an unrecorded offset). Then: `event_type ∈ KNOWN_EVENT_TYPES_V1`; `schema_version == SCHEMA_VERSION`; the stream's revision scope (lane for coordinator, problem otherwise) has BOTH `expected_` and `resulting_` set, the OTHER scope has neither, and `expected == seq` and `resulting == seq + 1`; `event_id` is a safe path segment; `timestamp` parses ISO-8601. **Then, if the `event_type` has an entry in `TYPE_VALIDATORS`, that validator checks the event itself** (payload contents plus payload-vs-envelope agreement). Raises `ValueError`. (Cross-event LEGAL TRANSITIONS are enforced by the projections — Tasks 4/6 — not here.)
  - `derive_route_id(attempt_id, operation_id, leg) -> str` — `sha256(f"{attempt_id}\x00{operation_id}\x00{leg}")[:32]`, the retry-stable route id for one logical `route_chat` call. **Lives here, beside `derive_event_id`** (round-5 F5): it is a pure hash with no dependencies, and `validate_lane_event` must recompute it to check a `LaneCallClaimed` payload — importing it from `call_ledger` would be a cycle (`call_ledger` imports `events`).
  - `LEGS = ("primary", "fallback")` — FR-002's two reroute legs; the only legal `leg` values. Also here (not in `call_ledger`) so the validator can enforce membership.
  - `TYPE_VALIDATORS: dict[str, Callable[[Mapping], None]]` — the per-type schema table (round-4 F6). **Each validator receives the WHOLE raw event, not just the payload** (round-5 F5): several invariants are cross-field — `payload["attempt_id"]` must equal the envelope's `attempt_id`, and a projection that counts by the PAYLOAD's attempt id while the envelope says otherwise would misattribute the record. A payload-only signature cannot express that.
    The envelope check alone accepts ANY payload, so a safety-relevant event with missing/wrong-typed keys validates, lands durably, and only explodes later as a `KeyError` inside a projection — or, worse, projects false provenance. A type **not** in this table is envelope-only by design (the audit mirror events are re-serializations of slice-0 dataclasses that were already type-checked at construction); a type that carries a **safety claim a projection will act on** MUST have an entry. Slice 1A registers `AttemptConfigured` (Task 13) and `LaneCallClaimed` (Task 14); Slice 1B registers `ReviewRerouted`. Each validator raises `ValueError` naming the offending key.
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

# ---- F6: per-type payload validation ----

def _claim_payload(**kw):
    from llmxive.self_improvement.events import derive_route_id
    base = {"attempt_id": "A1", "operation_id": "op-1", "leg": "primary",
            "route_id": derive_route_id("A1", "op-1", "primary"), "call_ceiling": 56}
    base.update(kw)
    return base

def _claim_event(**kw):
    return _raw(event_type="LaneCallClaimed", attempt_id="A1", payload=_claim_payload(**kw))

def test_lane_call_claimed_payload_validates():
    validate_lane_event(_claim_event())

@pytest.mark.parametrize("bad", [
    {"route_id": None},        # missing
    {"route_id": ""},          # empty
    {"route_id": "r" * 32},    # well-formed but NOT derived from this (attempt, op, leg)
    {"leg": "tertiary"},       # not one of LEGS
    {"call_ceiling": 0},       # non-positive
    {"call_ceiling": "56"},    # wrong type
    {"call_ceiling": True},    # bool is an int in Python — must still be rejected
])
def test_lane_call_claimed_payload_rejects_malformed(bad):
    # F6: the ENVELOPE alone would accept every one of these; the projection would then
    # KeyError (or route on a bogus id) long after the event became durable.
    payload = _claim_payload(**bad)
    for k, v in bad.items():
        if v is None:
            payload.pop(k)     # also cover the MISSING-key case
    with pytest.raises(ValueError, match="LaneCallClaimed payload invalid"):
        validate_lane_event(_raw(event_type="LaneCallClaimed", attempt_id="A1", payload=payload))

def test_a_claim_whose_payload_attempt_disagrees_with_the_envelope_is_rejected():
    # F5: project_call_claims filters by the PAYLOAD's attempt_id. If the envelope says
    # something else, the claim is counted against one Attempt while the event records
    # another — a silent misattribution of a safety limit.
    with pytest.raises(ValueError, match="disagrees with the event"):
        validate_lane_event(_raw(event_type="LaneCallClaimed", attempt_id="A2",
                                 payload=_claim_payload()))

def test_attempt_configured_validates_and_rejects_malformed():
    from llmxive.self_improvement.events import validate_lane_event as v
    ok = {"attempt_id": "A1", "call_ceiling": 56, "attempt_budget_credits": 50.0}
    v(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=ok))
    for bad in ({**ok, "call_ceiling": 0}, {**ok, "attempt_budget_credits": -1.0}):
        with pytest.raises(ValueError, match="AttemptConfigured payload invalid"):
            v(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=bad))

def test_the_new_safety_events_reject_unknown_keys():
    # F3: AttemptConfigured binds MONEY and a call cap; LaneCallClaimed binds routing
    # identity. Both get the same exact-schema rule ReviewRerouted already has — an
    # unrecognized key is indistinguishable from a typo, and once it is in append-only
    # history readers must guess at semantics nobody defined.
    with pytest.raises(ValueError, match="unexpected LaneCallClaimed payload keys"):
        validate_lane_event(_claim_event(surprise="extra"))
    cfg = {"attempt_id": "A1", "call_ceiling": 56, "attempt_budget_credits": 50.0,
           "surprise": "extra"}
    with pytest.raises(ValueError, match="unexpected AttemptConfigured payload keys"):
        validate_lane_event(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=cfg))

@pytest.mark.parametrize("budget", [float("nan"), float("inf"), True])
def test_attempt_configured_rejects_a_non_finite_budget(budget):
    # F2 at the EVENT boundary (bind_attempt_config guards the API boundary separately):
    # a hand-written or corrupted record must not be able to install an unbounded cap.
    payload = {"attempt_id": "A1", "call_ceiling": 56, "attempt_budget_credits": budget}
    with pytest.raises(ValueError, match="AttemptConfigured payload invalid"):
        validate_lane_event(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=payload))

def test_the_canonical_serializer_refuses_non_finite_numbers():
    # F2: json.dumps emits bare `NaN`/`Infinity` by default — valid to Python, invalid
    # JSON to everyone else. The ref must never carry it.
    from llmxive.self_improvement.events import Event, event_to_json
    ev = Event(**_raw(payload={"credits": float("nan")}))
    with pytest.raises(ValueError, match="not JSON compliant"):
        event_to_json(ev)

@pytest.mark.parametrize("credits, why", [
    (-1.0, "> 0"),               # REOPENS spent budget: counting_total goes DOWN
    (0.0, "> 0"),                # a paid dispatch the Attempt cap can never bind
    (float("nan"), "FINITE"),    # every later comparison is False -> always admit
    (float("inf"), "FINITE"),
    (True, "not a bool"),
])
def test_attempt_credit_reserved_rejects_unsafe_amounts(credits, why):
    # F1: project_reservations SUMS reserved_credits into counting_total, which IS the
    # number the Attempt cap compares against. A bad amount here is a money defect, so
    # the event must not rest on trusted construction.
    payload = {"reservation_id": "r1", "call_id": "c1", "reserved_credits": credits}
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_raw(event_type="AttemptCreditReserved", attempt_id="A1",
                                 payload=payload))

def test_attempt_credit_reserved_requires_an_envelope_attempt_and_exact_keys():
    ok = {"reservation_id": "r1", "call_id": "c1", "reserved_credits": 2.5}
    validate_lane_event(_raw(event_type="AttemptCreditReserved", attempt_id="A1", payload=ok))
    with pytest.raises(ValueError, match="envelope attempt_id"):
        validate_lane_event(_raw(event_type="AttemptCreditReserved", attempt_id=None, payload=ok))
    with pytest.raises(ValueError, match="unexpected AttemptCreditReserved payload keys"):
        validate_lane_event(_raw(event_type="AttemptCreditReserved", attempt_id="A1",
                                 payload={**ok, "surprise": 1}))

def test_types_without_a_validator_are_envelope_only():
    # By design: the audit-mirror types re-serialize already-typed slice-0 dataclasses.
    from llmxive.self_improvement.events import TYPE_VALIDATORS
    assert "ChainResolved" not in TYPE_VALIDATORS
    validate_lane_event(_raw(event_type="ChainResolved", payload={"anything": 1}))
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
import math
import re
from collections.abc import Callable, Mapping
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
# extend BOTH this set AND the projection handlers together. Adding a type does NOT bump
# SCHEMA_VERSION — the record SHAPE is unchanged, and a bump would make a reader reject
# prior-version history (F7).
KNOWN_EVENT_TYPES_V1 = frozenset({
    "ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet",
    "AttemptCreditReserved", "AttemptCreditReleased", "AttemptCreditRetained", "AttemptCreditReconciled",
    "AttemptConfigured",  # Task 13: the durable per-Attempt safety limits
    "LaneCallClaimed",    # Task 14: durable per-Attempt LLM-call admission
    "ChainResolved", "SelectionFailure", "ReservationOpened", "DispatchStarted",
    "DispatchCompleted", "DispatchUnknown", "CandidateOutcome",
    "ProblemDiscovered", "Proposed", "ProposalVerified", "Rejected",
})

LEGS = ("primary", "fallback")   # FR-002's two-attempt reroute; nothing else is a leg

def derive_route_id(attempt_id: str, operation_id: str, leg: str) -> str:
    """The RETRY-STABLE route id for one logical route_chat call (Task 14). Deterministic in
    the Attempt + operation + leg, so a replay re-derives it rather than minting a fresh
    uuid. Defined HERE, beside derive_event_id, because validate_lane_event must recompute
    it to verify a LaneCallClaimed payload — call_ledger imports events, so the reverse
    import would be a cycle."""
    return hashlib.sha256(f"{attempt_id}\x00{operation_id}\x00{leg}".encode()).hexdigest()[:32]

def _require(payload: Mapping[str, Any], key: str, types: type | tuple[type, ...]) -> Any:
    """Fetch ``key`` from a payload, raising ValueError (never KeyError/TypeError) if it is
    absent or the wrong type — so a malformed payload is rejected AT THE WRITE BOUNDARY
    rather than exploding inside a projection later."""
    if key not in payload:
        raise ValueError(f"payload missing required key {key!r}")
    value = payload[key]
    if not isinstance(value, types) or (types is str and not value):
        raise ValueError(f"payload key {key!r} must be a non-empty {types}, got {value!r}")
    return value

def _exact_keys(mapping: Mapping[str, Any], allowed: frozenset[str], label: str) -> None:
    """Reject unknown keys (round-6 F3). Every event that binds a LIMIT or a ROUTING
    IDENTITY has an EXACT schema, not merely required fields: an unrecognized key cannot be
    told from a typo, and once it is in append-only history readers must guess at semantics
    nobody defined. (Matches the convergence types' ``extra="forbid"``, ``types.py:128``.)"""
    extra = set(mapping) - allowed
    if extra:
        raise ValueError(f"unexpected {label} keys {sorted(extra)} — the schema is exact")

def _positive_int(payload: Mapping[str, Any], key: str) -> int:
    value = _require(payload, key, int)
    if isinstance(value, bool) or value <= 0:   # bool IS an int in Python
        raise ValueError(f"payload key {key!r} must be a positive int, got {value!r}")
    return value

def _finite_number(payload: Mapping[str, Any], key: str, *, strictly_positive: bool) -> float:
    """A MONEY value must be a real, FINITE number (round-6 F2, round-7 F1).

    ``nan``/``inf`` slip past a naive ``value < 0`` guard — and NaN is the worst possible
    failure on this path: the ledger's admission test is ``counting_total + credits >
    budget``, and EVERY comparison against NaN is False, so the cap silently becomes
    "always admit". ``inf`` is an unbounded value by another name. ``bool`` is rejected
    because ``True`` is a perfectly good ``int`` to Python and a nonsense credit amount to
    us. A NEGATIVE reserved amount is rejected outright (``strictly_positive``): it would
    lower ``counting_total`` and hand back budget that was already consumed."""
    value = _require(payload, key, (int, float))
    if isinstance(value, bool):
        raise ValueError(f"payload key {key!r} must be a number, not a bool")
    if not math.isfinite(value):
        raise ValueError(f"payload key {key!r} must be FINITE, got {value!r} — a non-finite "
                         "credit value disables the cap (every comparison against NaN is False)")
    if strictly_positive:
        if value <= 0:
            raise ValueError(
                f"payload key {key!r} must be > 0, got {value!r} — a negative reservation "
                "REOPENS spent budget, and a zero one dispatches a paid call the Attempt "
                "cap can never bind"
            )
    elif value < 0:
        raise ValueError(f"payload key {key!r} must be non-negative, got {value!r}")
    return float(value)

def _finite_non_negative(payload: Mapping[str, Any], key: str) -> float:
    """A budget CEILING may legitimately be zero (an Attempt allowed no paid spend)."""
    return _finite_number(payload, key, strictly_positive=False)

def _finite_positive(payload: Mapping[str, Any], key: str) -> float:
    """A reserved AMOUNT may not be zero or negative — see :func:`_finite_number`."""
    return _finite_number(payload, key, strictly_positive=True)

def _same_attempt(raw: Mapping[str, Any]) -> str:
    """The payload's attempt_id MUST equal the envelope's (round-5 F5). Projections filter
    by the PAYLOAD's attempt id, so a disagreement would file a claim/limit under one
    Attempt while the event envelope says another — a silent misattribution."""
    payload = raw["payload"]
    attempt = _require(payload, "attempt_id", str)
    if raw.get("attempt_id") != attempt:
        raise ValueError(
            f"payload attempt_id {attempt!r} disagrees with the event's "
            f"attempt_id {raw.get('attempt_id')!r}"
        )
    return attempt

_ATTEMPT_CONFIG_KEYS = frozenset({"attempt_id", "call_ceiling", "attempt_budget_credits"})
_CALL_CLAIM_KEYS = frozenset({"attempt_id", "operation_id", "leg", "route_id", "call_ceiling"})
_CREDIT_RESERVED_KEYS = frozenset({"reservation_id", "call_id", "reserved_credits"})

def _validate_attempt_credit_reserved(raw: Mapping[str, Any]) -> None:
    """The reservation record (round-7 F1). ``project_reservations`` SUMS
    ``reserved_credits`` into ``counting_total``, which is the number the Attempt cap is
    compared against — so this payload carries a monetary safety claim and must not rest on
    trusted construction alone. A negative amount persisted here lowers the running total
    and hands back budget that was already spent; a NaN one makes every later comparison
    False. Note the Attempt binding is the ENVELOPE's ``attempt_id`` (the projection filters
    on ``Event.attempt_id``), so there is no payload copy to cross-check — but an event with
    no Attempt at all could never be projected, so require one."""
    payload = raw["payload"]
    _exact_keys(payload, _CREDIT_RESERVED_KEYS, "AttemptCreditReserved payload")
    if not raw.get("attempt_id"):
        raise ValueError("an AttemptCreditReserved event must carry its envelope attempt_id")
    _require(payload, "reservation_id", str)
    _require(payload, "call_id", str)
    _finite_positive(payload, "reserved_credits")

def _validate_attempt_configured(raw: Mapping[str, Any]) -> None:
    """Task 13's durable limits. These two numbers ARE the Attempt's safety envelope and
    they are IMMUTABLE once written, so they must be exactly well-formed before binding."""
    payload = raw["payload"]
    _exact_keys(payload, _ATTEMPT_CONFIG_KEYS, "AttemptConfigured payload")
    _same_attempt(raw)
    _positive_int(payload, "call_ceiling")
    _finite_non_negative(payload, "attempt_budget_credits")

def _validate_lane_call_claimed(raw: Mapping[str, Any]) -> None:
    """Task 14's admission record. The ceiling projection COUNTS these and the router ROUTES
    on the recorded ``route_id``, so every field it reads must be present, typed, and
    SELF-CONSISTENT (round-5 F5) — a claim whose route_id was not derived from its own
    (attempt, operation, leg) would route one logical call onto another's identity."""
    payload = raw["payload"]
    _exact_keys(payload, _CALL_CLAIM_KEYS, "LaneCallClaimed payload")
    attempt = _same_attempt(raw)
    operation_id = _require(payload, "operation_id", str)
    leg = _require(payload, "leg", str)
    if leg not in LEGS:
        raise ValueError(f"payload key 'leg' must be one of {LEGS}, got {leg!r}")
    route_id = _require(payload, "route_id", str)
    expected = derive_route_id(attempt, operation_id, leg)
    if route_id != expected:
        raise ValueError(
            f"route_id {route_id!r} was not derived from (attempt={attempt!r}, "
            f"operation={operation_id!r}, leg={leg!r}) — expected {expected!r}"
        )
    _positive_int(payload, "call_ceiling")

#: Per-type schemas (round-4 F6; whole-event signature per round-5 F5). The envelope check
#: accepts ANY payload, so an event carrying a SAFETY CLAIM a projection acts on needs its
#: own validator here — a missing/mistyped/inconsistent key would otherwise land durably and
#: surface as a KeyError inside the projection, or (worse) project false provenance. A type
#: ABSENT from this table is envelope-only BY DESIGN: the audit-mirror types (ChainResolved,
#: DispatchStarted, …) are re-serializations of slice-0 dataclasses already type-checked at
#: construction. Cross-EVENT invariants (e.g. one consistent call_ceiling across an
#: Attempt) are NOT here — they belong to the projections (Tasks 13/14).
TYPE_VALIDATORS: dict[str, Callable[[Mapping[str, Any]], None]] = {
    "AttemptConfigured": _validate_attempt_configured,
    "AttemptCreditReserved": _validate_attempt_credit_reserved,
    "LaneCallClaimed": _validate_lane_call_claimed,
    # Slice 1B registers "ReviewRerouted" here.
}

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
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError(f"lane event payload must be a mapping, got {type(payload).__name__}")
    validator = TYPE_VALIDATORS.get(raw["event_type"])  # F6: per-type schema
    if validator is not None:
        try:
            validator(raw)          # the WHOLE event — payload/envelope cross-checks (F5)
        except ValueError as exc:
            raise ValueError(f"{raw['event_type']} payload invalid: {exc}") from exc

def event_to_json(event: Event) -> str:
    # allow_nan=False (round-6 F2): Python's json happily emits bare `NaN`/`Infinity`,
    # which are NOT valid JSON — they round-trip through json.loads but break every other
    # reader of this append-only log. A non-finite number must never reach the ref at all.
    return json.dumps(_as_dict(event), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)

def event_from_json(text: str) -> Event:
    d = json.loads(text)
    return Event(event_id=d["event_id"], event_type=d["event_type"], problem_id=d["problem_id"], actor=d["actor"],
                 payload=d["payload"], timestamp=d["timestamp"], schema_version=d["schema_version"],
                 attempt_id=d.get("attempt_id"), expected_lane_revision=d.get("expected_lane_revision"),
                 resulting_lane_revision=d.get("resulting_lane_revision"),
                 expected_problem_revision=d.get("expected_problem_revision"),
                 resulting_problem_revision=d.get("resulting_problem_revision"), seq=d.get("seq"))
```

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/unit/test_self_improvement_events.py -q` → PASS (33 passed: the 27 above + 5 parametrized unsafe-reservation-amount cases + the exact-keys/envelope-attempt case).

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
  - `LANE_REF = "refs/llmxive/self-improvement"`; `@dataclass LaneLogConfig(remote, expected_anchor)` (parallel to `LedgerConfig`, F4); `bootstrap_lane_log(repo, *, config, _after_probe=None) -> str` (F3 — one-time genesis, fail-closed-until-bootstrapped, idempotent, concurrent-safe, anchor-pinning; `_after_probe` is Task 1's test-only race seam, F10); internal `_log_ref(problem_id, config) -> LogRef` with `event_dir = f"self-improvement/events/{problem_id}"` (per-Problem subtree → per-stream `seq`; all streams share the ONE ref so lane mutations serialize globally, giving the coordinator its singleton and each Problem its own revision line).
  - `class LaneRevisionConflict(RuntimeError)` — the caller's `expected_revision`/precondition lost; recompute (FR-008).
  - `class LaneContention(RuntimeError)` — a caller's bounded CAS retry loop never converged. Defined here (not per-ledger) so `AttemptCreditLedger` (Task 7), `LaneCallLedger` (Task 14), and the coordinator all raise the SAME type.
  - `read(repo, problem_id, *, config: LaneLogConfig | None = None) -> list[Event]` — **`sync_and_verify` FIRST** (round-8 F3: `read_log` is LOCAL, so a public read that skipped it would project a populated lane as EMPTY on any checkout that has not fetched the ref — and empty reads as "no claim, no reservation, no spend"; the sync also fails closed on an unbootstrapped remote and on a tip that does not descend from the pinned anchor), then `read_log` mapped to `Event`s, **ordered by `seq`** (never timestamps). A gap/dup/fork in the sequence raises `GitLogError` (corruption is fail-closed, distinct from a `LaneRevisionConflict`). `config=None` resolves to the local-only default inside `_log_ref`, exactly as `ledger_transport._log_ref` does — no public signature carries a constructor call as its default (ruff B008).
  - `append(repo, event: Event, *, expected_revision: int | None, precondition: Callable[[list[Event]], tuple[bool, str]] | None = None, config: LaneLogConfig | None = None, _after_parent=None) -> AppendResult` — wraps `append_to_log` with the lane `LogRef`, `validate=validate_lane_event`, `finalize=_finalize` (stamps `seq` + **all four** revision anchors — the target scope from the verified parent and the OTHER scope back to `None`, because the store is their sole authority and a value a caller pre-filled on the wrong scope would otherwise survive into history and fail validation), `identity_exclude=_IDENTITY_EXCLUDE`, and a `predicate` that (per CAS attempt, against the freshly-read, seq-sorted stream) FIRST validates sequence continuity (F7 — a corrupt stream fails closed before any revision/precondition check), then, if `expected_revision is not None`, `len(events) == expected_revision`, then `precondition(events)`. A predicate `False` surfaces as `GitLogDenied` → `LaneRevisionConflict`; `expected_revision=None` is an unconditional append (for audit events). The event carries the single FR-011 `timestamp` (no `ts`). Returns the `AppendResult` with the authoritative `seq`.

- [ ] **Step 1: Write the failing test** (including the cross-process guarantee)

```python
# tests/integration/test_self_improvement_lane_log.py
import subprocess
import threading

import pytest

from llmxive.git_event_log import GitLogError
from llmxive.self_improvement.events import Event
from llmxive.self_improvement.lane_log import (
    LANE_REF, LaneLogConfig, LaneRevisionConflict, append, bootstrap_lane_log, read,
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

def test_second_clone_adopts_the_existing_genesis(tmp_path, bare_remote):
    # SEQUENTIAL: the later bootstrapper observes an already-bootstrapped remote and
    # adopts it. This is the adoption path, NOT the concurrent race (see below).
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    a1 = bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    a2 = bootstrap_lane_log(c2, config=LaneLogConfig(remote="origin"))
    assert a1 == a2  # exactly ONE genesis ref survives

def test_two_concurrent_bootstrappers_race_the_push_and_converge(tmp_path, bare_remote):
    # F10: the REAL race. Both clones must get PAST the "is it bootstrapped?" probe
    # before either pushes — otherwise this only re-tests adoption. The `_after_probe`
    # seam (Task 1) releases both threads at exactly that point, so the loser genuinely
    # executes the non-fast-forward branch (`ledger_transport.py:402-407`).
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    barrier = threading.Barrier(2, timeout=30)
    out: dict[str, str] = {}
    errors: list[BaseException] = []

    def _boot(name, clone):
        try:
            out[name] = bootstrap_lane_log(
                clone, config=LaneLogConfig(remote="origin"), _after_probe=barrier.wait
            )
        except BaseException as exc:       # a raise here is a real failure, not a pass
            errors.append(exc)

    ts = [threading.Thread(target=_boot, args=(n, c)) for n, c in (("a", c1), ("b", c2))]
    for t in ts: t.start()
    for t in ts: t.join(timeout=60)

    assert not errors, f"concurrent bootstrap raised: {errors}"
    assert out["a"] == out["b"], "the two bootstrappers disagree on the genesis anchor"
    # and the bare remote holds exactly ONE genesis commit on the lane ref
    oid = subprocess.run(["git", "rev-parse", LANE_REF], cwd=str(bare_remote),
                         capture_output=True, text=True, check=True).stdout.strip()
    assert oid == out["a"]
    log = subprocess.run(["git", "rev-list", "--count", LANE_REF], cwd=str(bare_remote),
                         capture_output=True, text=True, check=True).stdout.strip()
    assert log == "1", f"expected a single genesis commit, got {log}"

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
    sync_and_verify,
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

class LaneContention(RuntimeError):
    """A caller's bounded CAS retry loop never converged. Defined HERE, once, because every
    lane CAS user raises it (`AttemptCreditLedger`, `LaneCallLedger`, the coordinator) —
    a per-module copy would give the same condition several unrelated types."""

def _log_ref(problem_id: str, config: LaneLogConfig | None = None) -> LogRef:
    # ONE ref; per-Problem (and coordinator) subtree → per-stream seq line. `None`
    # resolves to the local-only default HERE, as `ledger_transport._log_ref` does, so no
    # public signature carries a constructor call as its default.
    config = config or LaneLogConfig()
    return LogRef(ref=LANE_REF, event_dir=f"self-improvement/events/{problem_id}",
                  remote=config.remote, expected_anchor=config.expected_anchor)

def bootstrap_lane_log(repo: Path, *, config: LaneLogConfig,
                       _after_probe: Callable[[], None] | None = None) -> str:
    """One-time creation of the authoritative lane ref (F3), mirroring the credit ledger's
    ``bootstrap_ledger``: a genesis anchor commit on ``LANE_REF``. Invoked ONCE by a
    privileged setup workflow — NOT by an ordinary lane call; every remote read/append
    FAILS CLOSED until it has run, exactly like the credit ledger. Idempotent (a repeat
    returns the same anchor, no second genesis); two concurrent bootstrappers converge on
    ONE ref (FF-push CAS); a divergent/wrong existing ref fails closed. Returns the genesis
    anchor OID — PIN it as ``LaneLogConfig.expected_anchor`` thereafter. The ref is
    protected: only the trusted lane transport advances it, fast-forward only.

    ``_after_probe`` is the TEST-ONLY barrier seam (F10) forwarded to the core so two
    bootstrappers can be held past the existence probe and genuinely race the push."""
    return bootstrap_log(repo, log=_log_ref(COORDINATOR_STREAM, config), message=_LANE_GENESIS_MSG,
                         remote=config.remote, _after_probe=_after_probe)

def _message(event: dict) -> str:
    return f"self-improvement: {event.get('event_type', '?')} {event['event_id']}"

def _sorted_by_seq(raw: list[dict]) -> list[dict]:
    return sorted(raw, key=lambda r: r.get("seq", -1))  # seq is the AUTHORITATIVE order

def _to_json(raw: dict) -> str:
    # allow_nan=False mirrors event_to_json (round-6 F2) — the canonical form is the SAME
    # in both directions, and neither may produce non-standard JSON.
    return json.dumps(raw, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)

def _check_continuity(raw_sorted: list[dict], problem_id: str) -> None:
    seqs = [r.get("seq") for r in raw_sorted]
    if seqs != list(range(len(raw_sorted))):
        # A gap/dup/fork is corruption of the authoritative sequence — fail closed,
        # never retry (a GitLogError propagates out of the CAS loop; NOT a conflict).
        raise GitLogError(f"corrupt sequence in stream {problem_id!r}: {seqs}")

def _to_event(raw: dict) -> Event:
    """One stored record → an ``Event`` through the canonical form. The re-serialization
    is not just symmetry: a hand-corrupted blob carrying bare ``NaN`` parses in Python and
    would flow into a projection as a number every comparison answers False about.
    Corruption found on a read raises ``GitLogError`` — the same fail-closed type as a
    broken sequence, not a ``ValueError`` a caller could read as a schema complaint."""
    try:
        return event_from_json(_to_json(raw))
    except ValueError as exc:
        raise GitLogError(f"corrupt lane event {raw.get('event_id')!r}: {exc}") from exc

def read(repo: Path, problem_id: str, *, config: LaneLogConfig | None = None) -> list[Event]:
    """Synchronizes FIRST (round-8 F3): `read_log` is LOCAL by design, so a public read
    that skipped this would project an empty log on any checkout that has not fetched the
    ref — and empty means "no claim, no reservation, no spend" to every projection.
    `sync_and_verify` also fails closed on an unbootstrapped remote and on a tip that does
    not descend from the pinned anchor; local-only configs make it a no-op."""
    log = _log_ref(problem_id, config)
    sync_and_verify(repo, log=log)
    raw_sorted = _sorted_by_seq(read_log(repo, log=log, validate=validate_lane_event))
    _check_continuity(raw_sorted, problem_id)
    return [_to_event(r) for r in raw_sorted]

def _finalize(built: dict, seq: int) -> dict:
    """ALL FOUR anchors are written, not only this stream's scope: the store is their sole
    authority (FR-011 requires expected==seq and resulting==seq+1 against the VERIFIED
    parent), so an anchor a caller pre-filled — on either scope — is overwritten rather
    than trusted. Leaving the other scope alone would let a caller's leftover value
    survive into history and fail validation on a stream it does not belong to."""
    scope = "lane" if built["problem_id"] == COORDINATOR_STREAM else "problem"
    other = "problem" if scope == "lane" else "lane"
    return {**built, SEQ_FIELD: seq,
            f"expected_{scope}_revision": seq, f"resulting_{scope}_revision": seq + 1,
            f"expected_{other}_revision": None, f"resulting_{other}_revision": None}

def append(repo: Path, event: Event, *, expected_revision: int | None,
           precondition: Callable[[list[Event]], tuple[bool, str]] | None = None,
           config: LaneLogConfig | None = None,
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
            return precondition([_to_event(r) for r in ordered])
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

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/integration/test_self_improvement_lane_log.py -q` → PASS (**16 passed**), including BOTH barrier-driven races (the two-clone append CAS and the concurrent bootstrap push, F10) and, beyond the block above: the **round-8 F3 proof** that the public `read()` synchronizes (an ordinary second clone's raw `read_log` sees `[]` while `read()` returns the event) and fails closed on an unbootstrapped remote; per-stream `seq` lines + revision scopes across `prob-1`/`prob-2`/coordinator; lane-level idempotency (a replay differing only in store-owned fields is `created=False` at the original `seq`, while a different body under the same `event_id` raises); and a **plumbing-built gapped sequence** proving corruption fails closed on read AND that `append` checks continuity BEFORE the revision (with `expected_revision` deliberately set to the record count, which a later check would have accepted).

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
  - `project_coordinator(events: list[Event]) -> LaneCoordinator` — pure fold, `lane_revision = len(events)`. `ClaimAcquired` sets active ids; `ClaimReleased` clears them; `MonitorStarted` appends; `PromotionEnabledSet` sets flag/policy. **An unknown `event_type` here raises `ValueError`** (F9: never silently advance the safety-critical projection — validation already gates writes, but a projection over a corrupted/newer stream must fail closed, not shrug). It also refuses events **out of `seq` order** (`e.seq != position`): ORDER decides ownership, so a list sorted by anything else — a timestamp, say — would hand the claim to the wrong Attempt; `lane_log.read` guarantees the order, anything else must prove it. `promotion_enabled` is **not coerced** (`bool("false")` is `True` — coercion would open the autonomous-merge gate a record was written to close), and a payload field the fold reads raises `ValueError`, never `KeyError`.
  - **The four coordinator payloads gain `TYPE_VALIDATORS` entries** (in Task 2's `events.py`, where every payload schema lives — not restated in the projection). `ClaimAcquired`/`ClaimReleased` carry the lane's OWNERSHIP record: `project_coordinator` decides who holds the singleton from those two ids and `cas_release` compares them to refuse a stale release, so a missing/empty one is refused at the write boundary rather than exploding inside the fold once durable. The payload `attempt_id` is cross-checked against the envelope's (`_same_attempt`) — **so Task 5's `cas_claim`/`cas_release` MUST set `Event.attempt_id`** — while the payload `problem_id` deliberately is NOT (the envelope's is `COORDINATOR_STREAM`; the payload's is the CLAIMED Problem).

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

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/unit/test_self_improvement_coordinator.py tests/unit/test_self_improvement_events.py -q` → PASS (**87 passed**). Beyond the block above, the shipped suites cover: reclaiming the lane after a release (the singleton is a lock, not a one-shot); a release naming the right Problem but the WRONG Attempt (ownership is the PAIR); out-of-`seq`-order refusal; a payload missing the field the fold reads; `MonitorStarted` accumulation; `policy_version` carrying forward when a later flip omits it; the non-bool `promotion_enabled` refusal; and, in `events.py`, the four new coordinator payload schemas. The events suite's `_coord()` helper now carries a well-formed `ClaimAcquired` payload — `ClaimAcquired` HAS a schema now, and that helper's job is varying the ENVELOPE.

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
  - `cas_release(repo, *, problem_id, attempt_id, actor, timestamp, config: LaneLogConfig | None = None) -> LaneCoordinator` — appends `ClaimReleased` (idempotency key `("release", problem_id, attempt_id)`) with an **ownership precondition** (F6): admit iff **this exact release already landed (idempotent) OR the current active pair equals `(problem_id, attempt_id)`**. A release from a NON-OWNER — one whose own record never landed, while another Attempt holds the lane — fails the precondition → `LaneRevisionConflict`. Ownership is the PAIR, so an earlier Attempt on the same Problem is still a non-owner.
    **Maintainer-decided 2026-07-26** (an earlier revision of this line contradicted itself): a delayed DUPLICATE release, whose own record is already durable, is an **idempotent no-op** — it neither appends a second record nor raises, and the returned projection shows whoever holds the lane now, possibly another Attempt. It is reporting a fact, not requesting a change, and both readings satisfy the safety requirement (neither clears the newer claim); this one does not manufacture a failure for a legitimate retry of work that already succeeded.

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

def test_a_release_from_a_non_owner_cannot_clear_the_active_claim(repo):
    # F6 regression: a caller that believes it holds the lane must not evict the Attempt
    # that actually does. This release's own record never landed, so it is a non-owner.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    with pytest.raises(LaneRevisionConflict, match="owner mismatch"):
        cas_release(repo, problem_id="PX", attempt_id="AX", actor="d", timestamp=TS)
    assert project_coordinator(read(repo, COORDINATOR_STREAM)).active_problem_id == "P1"

def test_a_delayed_duplicate_release_does_not_disturb_a_newer_claim(repo):
    # The maintainer-decided case: P1/A1's release is ALREADY durable, so a delayed retry
    # is an idempotent no-op — no second record, no raise, and P2/A2 keeps the lane.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    late = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert (late.active_problem_id, late.active_attempt_id) == ("P2", "A2")
    assert late.lane_revision == 3  # no fourth record
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

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/integration/test_self_improvement_coordinator_cas.py -q` → PASS (**8 passed**), incl. the non-owner regression, the delayed-duplicate case, the right-Problem-wrong-Attempt refusal, a rejected CAS leaving NO record, the lane cycling through three Attempts, and a check that the claim record carries its Attempt on the ENVELOPE (the T4 validators cross-check it) with the store-stamped anchors `seq=0, expected=0, resulting=1`.

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

def test_a_negative_reservation_would_have_reopened_the_budget():
    # WHY Task 2 validates reserved_credits > 0 (round-7 F1), asserted directly so the
    # rationale cannot rot: counting_total SUMS the amounts, so a negative one hands back
    # budget that was already spent. The event validator makes this unreachable through
    # the real write path; this test pins the consequence it prevents.
    honest = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=40.0)]
    poisoned = [*honest, _ev("e2", "AttemptCreditReserved", "r2", 1, credits=-30.0)]
    assert counting_total(project_reservations(honest, "A1")) == 40.0
    assert counting_total(project_reservations(poisoned, "A1")) == 10.0   # 30 credits back

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
- Produces: `class AttemptCreditLedger` implementing the slice-0 `ReservationAuthority`. Constructor `(*, repo, problem_id, attempt_id, attempt_budget_credits, call_ceiling, actor, clock, config=LaneLogConfig())`; holds a `threading.Lock`.
  **Forward reference (round-5 F1):** as written here the budget is constructor-local, which lets a second worker present a larger one. **Task 13** binds both limits to a durable `AttemptConfigured` record and rewrites this constructor to enforce `bind_attempt_config(...).attempt_budget_credits`; the `call_ceiling` parameter above exists because ONE record binds both. Implement Task 7 as specified, then apply Task 13's change — Task 13 carries the regression test. `reserve(credits, *, reservation_id, call_id) -> bool` — **first validates the amount** (round-7 F1: finite, not `bool`, strictly `> 0`, else `ValueError` — NOT `False`, which would look like a routine budget skip); then, under the lock, a bounded retry loop: project the Attempt's reservations from `read(problem_id)`; same `(credits, call_id)` under an existing id → `True` (idempotent); different identity → `raise ValueError` (integrity); `counting_total + credits > budget` → `False`; else `append` an `AttemptCreditReserved` event (`expected_revision = len(read)`) with a precondition re-checking the budget against fresh events (so a **cross-clone** competitor that consumed the budget flips this to `False` on recompute); on `LaneRevisionConflict` retry; after the cap `raise LaneContention`. **Corrected during implementation:** the ref-CAS + budget-recheck precondition is what makes overspending impossible — in-process AND cross-clone. Verified by removing the `Lock`: both the shared-ledger panel test and the two-clone race still hold. The `Lock` is a CONTENTION measure (without it every thread in a wide panel reads, builds, loses the ref-CAS and retries — quadratic churn that can exhaust the retry budget and report `LaneContention` for mere crowding). Describe it that way; do not claim it as the safety mechanism.
- Consumes: `LaneContention` from `lane_log.py` (Task 3) — the shared "the CAS never converged" condition, defined ONCE beside `LaneRevisionConflict` because both ledgers (and any later CAS user) raise it. Do NOT redeclare it per module.

- [ ] **Steps:** Tests: (0) **amount validation (F1)** — `reserve(-1)`, `reserve(0)`, `reserve(nan)`, `reserve(inf)`, `reserve(-inf)`, `reserve(True)` each raise `ValueError` BEFORE any append, and leave both the reservation projection and the remaining budget byte-for-byte unchanged (assert `project_reservations(read(...))` is empty and a subsequent honest `reserve` for the FULL budget still succeeds); (1) within-budget True / over-budget False / at-budget True; (2) idempotent same identity; (3) conflicting identity raises; (4) `ThreadPoolExecutor(2)` sharing one ledger, budget admits one → exactly one `True`; (5) **barrier-driven two-clone race** (F6): two clones of one bare remote both reserving the last credits, each syncing the same parent then released together by a `threading.Barrier` — the ref-CAS + budget-recheck admits at most the remaining budget (the loser recomputes and returns `False`, never both `True`). RED (`ImportError`) → GREEN. Commit `feat(025 slice-1A T7): AttemptCreditLedger.reserve — lock + ref-CAS budget guard + collision`.

The reserve body (append-with-budget-precondition + retry):

```python
    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:   # `import math` at module top
        # Round-7 F1: validate the AMOUNT before anything else. The admission test is
        # `counting_total + credits > budget`, so an unchecked amount defeats the cap in
        # three different ways, and `False` (an ordinary budget denial) must never be the
        # answer to a malformed request — that would look like a routine skip.
        #   negative -> lowers counting_total, HANDING BACK budget already spent
        #   nan      -> every comparison is False, so the cap admits everything
        #   inf/0    -> a paid dispatch the Attempt cap can never meaningfully bind
        #   bool     -> True is an int to Python and a nonsense credit amount to us
        # allow_nan=False in the serializer would eventually reject nan/inf, but only as a
        # SERIALIZATION error, after admission was already decided — and it never catches
        # a negative. This is the ledger's own declared contract, so it is enforced here.
        if (
            isinstance(credits, bool)
            or not isinstance(credits, (int, float))
            or not math.isfinite(credits)
            or credits <= 0
        ):
            raise ValueError(
                f"reserved credits must be a finite number > 0, got {credits!r} "
                f"(reservation {reservation_id!r})"
            )
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
                    # AS SHIPPED: expected_revision=None, not len(events). A revision CAS
                    # here compares the length of the WHOLE per-Problem stream, which also
                    # carries Task 10's unconditional audit appends — so a busy route would
                    # spend reserve's retry budget losing to events with no bearing on
                    # money, then raise LaneContention on the money path. The budget
                    # precondition is the actual invariant and is recomputed inside every
                    # CAS attempt. This also makes the precondition the DECIDING check, so
                    # the two-clone race test genuinely proves it: with the budget check
                    # stubbed out, that test fails (with `expected_revision=len(events)` it
                    # passed either way, proving only the revision comparison).
                    append(self._repo, event, expected_revision=None,
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

    # NOTE (as shipped): `_FROM_STATES` is NOT declared — it would DUPLICATE the policy.
    # Its content is exactly `{et: _TRANSITIONS[et].keys()}`, and two copies of the legal
    # edges can drift into a state where the CAS admits a transition the projection then
    # rejects. `_cas_append` reads `_TRANSITIONS[event_type]` directly.

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
- ~~Modify `lane_log.py`~~ — **no change needed.** Task 3 already shipped `expected_revision: int | None` with `None` meaning an unconditional append. It stays keyword-REQUIRED rather than defaulting to `None`: a default would make "unconditional" the quiet fallback for a CAS primitive, so every call site states its intent and the audit sink passes `expected_revision=None` explicitly.
- Create: `src/llmxive/self_improvement/audit_sink.py`
- Test: `tests/integration/test_self_improvement_audit_sink.py`

**Interfaces:**
- Consumes: the slice-0 audit dataclasses (`from llmxive.model_selection.attempt_hooks import ...`), `ModelRef`, `SnapshotProvenance`; `append`, `read`, `LaneRevisionConflict` (Task 3); `Event`, `derive_event_id` (Task 2).
- Produces:
  - `class EventStoreRouteAudit` implementing the slice-0 `RouteAudit`. Constructor `(*, repo, problem_id, attempt_id, actor, clock, config=LaneLogConfig())`.
  - `def record(self, event) -> None` — build the lane `Event` (`event_type = type(event).__name__`, `event_id = derive_event_id(problem_id, "audit\x00" + event.event_id)`, `payload = _audit_payload(event)`, and ALL revision fields left `None` — the store's `_finalize` stamps the real `expected_problem_revision`/`resulting_problem_revision` inside the CAS, F8), then `append(..., expected_revision=None)`. **`append` only returns after the ref-CAS commit lands — that is the durability point (F8).** **No retry loop, as shipped:** with `expected_revision=None` and no precondition the append has nothing that can be denied, so `LaneRevisionConflict` is unreachable here — a loop catching it would be dead code carrying a comment about a case that cannot arise. Sustained contention surfaces as `GitLogContention` from the core's own bounded retry, and `emit_audit` makes that route-fatal like any other sink failure. A conflicting payload under the same `event_id` raises `GitLogError`/append-only, which `emit_audit` in `execute` normalizes to route-fatal `RouteAuditError`.
  - `_audit_payload(event) -> dict` — JSON-safe projection (scalars verbatim; `ModelRef`→its 5 fields; `candidates`→list; `snapshot_provenance`→`{k: {source, observed_at, age_s}}`), plus `audit_event_id = event.event_id` for correlation (the slice-0 id is carried under that name because the lane envelope has its OWN `event_id` — a hash of it — and two differently-scoped keys sharing a name is a trap for every reader). A field of an **unknown type RAISES** rather than being coerced with `str()`: the payload becomes immutable history, and an unparseable repr is worse than a refusal — `emit_audit` turns it into the route-fatal `RouteAuditError` that a mandatory sink owes its caller when it cannot faithfully record what it was given.

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
- **Round-9 review — terminal disposition is EXCLUSIVE (blocker).** As first shipped, `record` appended unconditionally and `reconcile_unknown` read the stream, computed the dangling set, then appended — so a `DispatchCompleted` landing in between produced TWO contradictory terminal records for one dispatch, and the reverse order did the same. A terminal record (`DispatchCompleted`, `DispatchUnknown`, or a terminal `CandidateOutcome`) now carries a CAS precondition: it may land only if no OTHER terminal record claims its `(attempt, route, candidate)` against the fresh parent. A byte-identical replay of the record's OWN id stays idempotent (checked first — its committed copy is itself a terminal record with that key). `record` RAISES when it loses, which `emit_audit` makes route-fatal; `reconcile_unknown` treats losing as a NORMAL outcome and skips that dispatch, because a real completion winning is the correct answer. One `_terminal_key` serves both the dangling scan and the precondition, so "resolved" and "refuse a second resolution" cannot drift apart.
- **Round-9 review — Attempt scoping, at TWO layers (high).** The resolution scan matched `DispatchCompleted`/`DispatchUnknown`/terminal `CandidateOutcome` across ALL Attempts while filtering only `DispatchStarted`, so A2's completion suppressed reconciliation of an identically keyed A1 dispatch. `_terminal_key` now carries `attempt_id`, making the match Attempt-scoped by construction. Implementation ALSO found the same bug one level deeper: the lane `event_id` was `derive_event_id(problem_id, "audit\0" + event.event_id)`, and the slice-0 id is `route_id:candidate_index:kind` with no Attempt in it — so two Attempts sharing a caller-supplied route key derived the SAME lane id with different payloads and the second died on the append-only guard. The Attempt is now part of that hash: scoping holds in the STORAGE key, not only in the queries over it.
- **Round-9 review — the conservative timeout is ENFORCED (medium).** `timeout_s` was accepted unvalidated, so zero or negative marked a still-running dispatch unknown immediately — the opposite of the documented guarantee. `_validated_timeout` rejects bool/non-numeric/non-finite/`<= 0`, and `reconcile_timeout_s(deadline_s=, retries=)` is THE reviewed derivation: `deadline_s * (retries + 1) * RECONCILE_SAFETY_FACTOR`. `deadline_s=None` — `route_chat`'s DEFAULT — RAISES, because an unbounded call has no worst case and no timeout can honestly assert the dispatch could not still be running.
- `def reconcile_unknown(repo, *, problem_id, attempt_id, actor, clock, now, timeout_s, config=LaneLogConfig()) -> list[str]` — for each dangling dispatch, append **ONE `DispatchUnknown` event** (carrying its `route_id`/`candidate_index`/`candidate`/`reservation_id`) via `record`. That single durable event drives BOTH projections atomically (F4): the audit projection sees the dispatch resolved as `DispatchUnknown`, and `project_reservations` (Task 6) transitions the reservation `open → retained`. There is no separate `mark_retained` call, so no crash window between two writes. Returns the reconciled `route_id`s. Idempotent (a byte-identical `DispatchUnknown` re-append is a no-op; a second run finds nothing dangling).

- [ ] **Steps:** Tests: a `DispatchStarted` past the timeout with no completion/terminal-outcome → one `DispatchUnknown` recorded AND `project_reservations` shows the reservation `retained` (assert BOTH from the single event); a `DispatchStarted` WITHIN the timeout → not marked; a `DispatchStarted` + `CandidateOutcome("advance")` → not unknown (known failure); a `DispatchStarted` + `DispatchCompleted` → not unknown; a dispatch under a DIFFERENT `attempt_id` → untouched; a **crash-safety** test: since the retain rides on the same event, there is no state where `DispatchUnknown` exists without `retained` (assert the projection invariant on a stream containing the single event); idempotent on re-run. RED → GREEN. Commit `feat(025 slice-1A T12): atomic DispatchUnknown reconciliation (single event drives unknown+retained; conservative timeout)`.

---

### Task 13: `AttemptConfig` — the Attempt's limits are durable, not constructor-local (round-5 F1)

**Files:**
- Create: `src/llmxive/self_improvement/attempt_config.py`
- Modify: `src/llmxive/self_improvement/credit_ledger.py` (Task 7's constructor binds through this)
- Test: `tests/integration/test_self_improvement_attempt_config.py`; extend `tests/integration/test_self_improvement_credit_ledger.py`

**Depends on:** Task 2 (`Event`, `derive_event_id`, `AttemptConfigured` + its validator), Task 3 (`append`/`read`), Task 6/7 (`AttemptCreditLedger`).

**Why.** Round-4 made the call *spend* durable but left the *limit* in a constructor argument, which reopens the same hole one level up:

```python
LaneCallLedger(..., call_ceiling=2).claim(operation_id="a")
LaneCallLedger(..., call_ceiling=2).claim(operation_id="b")
LaneCallLedger(..., call_ceiling=100).claim(operation_id="c")   # ADMITTED — cap defeated
```

A durable count checked against a mutable bound is not a durable cap. The same is true of `AttemptCreditLedger.attempt_budget_credits` (Task 7), which is likewise constructor-local — and that one guards *money*. Configuration drift, a redeployed worker with a different default, or a competing worker each silently raise the ceiling. Both limits therefore come from ONE durable record per Attempt: the first writer binds them via CAS, and every later worker must present the SAME values or fail closed.

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class AttemptConfig`: `attempt_id: str`, `call_ceiling: int`, `attempt_budget_credits: float`.
  - `class AttemptConfigMismatch(ValueError)` — a worker presented limits that differ from the Attempt's bound record. Fail closed: the safe move is to refuse the work, never to adopt the larger (or the smaller) number.
  - `def bind_attempt_config(repo, *, problem_id, attempt_id, call_ceiling, attempt_budget_credits, actor, clock, config=LaneLogConfig()) -> AttemptConfig` — CAS-appends ONE `AttemptConfigured` event with the deterministic `event_id = derive_event_id(problem_id, f"attempt-config\x00{attempt_id}")`. **Idempotent** when the presented values match the bound ones (returns them); raises `AttemptConfigMismatch` when they differ. Two concurrent binders converge on one record: exactly one CAS wins and the loser re-reads and compares.
  - `def load_attempt_config(events, attempt_id) -> AttemptConfig | None` — the bound record, or `None` if the Attempt was never configured. More than one `AttemptConfigured` for an Attempt is corruption → `AttemptConfigMismatch` (the deterministic `event_id` makes it unreachable, so reaching it means the log was tampered with).
  - `def require_attempt_config(events, attempt_id) -> AttemptConfig` — as above but raises `AttemptConfigMismatch` on `None`. **Fail-closed-until-bound is the rule**: no lane work runs against limits nobody wrote down.
- Modifies `AttemptCreditLedger.__init__` (Task 7): it keeps its `attempt_budget_credits` parameter, but the value it ENFORCES is now `bind_attempt_config(...).attempt_budget_credits`. A second ledger constructed with a different budget for the same Attempt raises `AttemptConfigMismatch` at construction, before it can admit a single reservation.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_attempt_config.py
"""F1: an Attempt's limits are DURABLE. A restart, a config change, or a competing worker
must not be able to raise (or lower) the ceiling or the credit budget."""
import subprocess
import threading

import pytest

from llmxive.self_improvement.attempt_config import (
    AttemptConfigMismatch, bind_attempt_config, load_attempt_config, require_attempt_config,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read

def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

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

_CLOCK = lambda: "2026-07-24T00:00:00+00:00"
_CFG = LaneLogConfig(remote="origin")

def _bind(repo, *, ceiling=56, budget=50.0):
    return bind_attempt_config(repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                               attempt_budget_credits=budget, actor="lane", clock=_CLOCK,
                               config=_CFG)

def test_binding_is_idempotent_for_identical_limits(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    first = _bind(c)
    assert _bind(c) == first
    assert len([e for e in read(c, "P1", config=_CFG)
                if e.event_type == "AttemptConfigured"]) == 1   # ONE record, not two

def test_a_LARGER_ceiling_is_rejected(tmp_path, bare_remote):
    # THE regression: this is the exact sequence that defeated the round-4 cap.
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    _bind(c, ceiling=2)
    with pytest.raises(AttemptConfigMismatch, match="call_ceiling"):
        _bind(c, ceiling=100)

def test_a_DIFFERENT_credit_budget_is_rejected(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    _bind(c, budget=50.0)
    with pytest.raises(AttemptConfigMismatch, match="attempt_budget_credits"):
        _bind(c, budget=500.0)

def test_a_SECOND_CLONE_sees_the_bound_limits(tmp_path, bare_remote):
    # Cross-process, not just cross-object.
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=_CFG)
    _bind(c1, ceiling=2)
    assert require_attempt_config(read(c2, "P1", config=_CFG), "A1").call_ceiling == 2
    with pytest.raises(AttemptConfigMismatch):
        _bind(c2, ceiling=100)

def test_two_concurrent_binders_converge_on_one_record(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=_CFG)
    barrier = threading.Barrier(2, timeout=30)
    out, errors = {}, []

    def _go(name, clone):
        try:
            barrier.wait()
            out[name] = _bind(clone)
        except BaseException as exc:
            errors.append(exc)

    ts = [threading.Thread(target=_go, args=(n, c)) for n, c in (("a", c1), ("b", c2))]
    for t in ts: t.start()
    for t in ts: t.join(timeout=60)
    assert not errors, f"concurrent bind raised: {errors}"
    assert out["a"] == out["b"]
    assert len([e for e in read(c1, "P1", config=_CFG)
                if e.event_type == "AttemptConfigured"]) == 1

@pytest.mark.parametrize("budget", [
    float("nan"),        # THE dangerous one: `total + credits > nan` is False -> always admit
    float("inf"),        # an unbounded cap by another name
    float("-inf"),
    True,                # bool IS an int in Python, and a nonsense credit budget
    "50",                # not a number at all
])
def test_a_non_finite_or_non_numeric_budget_is_refused(tmp_path, bare_remote, budget):
    # F2: `value < 0` does NOT reject nan/inf — verify with the real comparison, then the
    # real binder. A NaN budget would silently disable the money cap for the whole Attempt.
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    with pytest.raises(ValueError):
        _bind(c, budget=budget)
    assert not [e for e in read(c, "P1", config=_CFG) if e.event_type == "AttemptConfigured"]

def test_a_nan_budget_would_have_defeated_the_cap():
    # The reason the check above is REQUIRED, asserted directly so the rationale cannot
    # rot: every comparison against NaN is False, so the ledger's admission test passes
    # for any amount.
    import math
    nan = float("nan")
    assert not (nan < 0)                 # the naive guard lets it through
    assert not (10_000.0 + 1.0 > nan)    # ...and then the cap never denies anything
    assert not math.isfinite(nan)        # the check that actually catches it

@pytest.mark.parametrize("ceiling", [0, -1, True, 5.0, "56"])
def test_a_non_positive_or_non_int_ceiling_is_refused(tmp_path, bare_remote, ceiling):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    with pytest.raises(ValueError):
        _bind(c, ceiling=ceiling)

def test_an_unconfigured_attempt_fails_closed(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    assert load_attempt_config(read(c, "P1", config=_CFG), "A1") is None
    with pytest.raises(AttemptConfigMismatch, match="not configured"):
        require_attempt_config(read(c, "P1", config=_CFG), "A1")
```

And the credit-ledger half (append to `tests/integration/test_self_improvement_credit_ledger.py`):

```python
def test_a_second_ledger_with_a_different_budget_is_rejected(tmp_path, bare_remote):
    # F1: the credit budget guards MONEY; it must not be re-openable by a worker that
    # simply passes a bigger number.
    from llmxive.self_improvement.attempt_config import AttemptConfigMismatch
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    _ledger(c, budget=50.0)                       # binds
    with pytest.raises(AttemptConfigMismatch):
        _ledger(c, budget=500.0)                  # refuses at CONSTRUCTION, pre-reservation
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_attempt_config.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.self_improvement.attempt_config'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/attempt_config.py
"""The Attempt's DURABLE safety limits (round-5 review F1).

Round 4 made the call SPEND durable but left the LIMIT in a constructor argument — and a
durable count checked against a mutable bound is not a durable cap: a restarted worker, a
config change, or a competing worker could simply present a bigger ceiling. The same held
for the credit budget, which guards money. Both now come from ONE ``AttemptConfigured``
event per Attempt: the first writer binds them under the ref-CAS, and every later worker
must present identical values or fail closed."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lane_log import (
    LaneContention, LaneLogConfig, LaneRevisionConflict, append, read,
)

_MAX_RETRIES = 8

class AttemptConfigMismatch(ValueError):
    """A worker presented limits that differ from the Attempt's bound record (or the
    Attempt has none). Fail closed — never adopt the presented value, in EITHER direction:
    a larger ceiling defeats the cap, and a smaller one silently strands admitted work."""

@dataclass(frozen=True)
class AttemptConfig:
    attempt_id: str
    call_ceiling: int
    attempt_budget_credits: float

def _config_event_id(problem_id: str, attempt_id: str) -> str:
    return derive_event_id(problem_id, f"attempt-config\x00{attempt_id}")

def load_attempt_config(events: list[Event], attempt_id: str) -> AttemptConfig | None:
    """The Attempt's bound limits, or None if it was never configured. Two records for one
    Attempt is corruption — the deterministic event_id makes it unreachable through the
    CAS, so reaching it means the log was tampered with."""
    found = [e for e in events
             if e.event_type == "AttemptConfigured" and e.payload.get("attempt_id") == attempt_id]
    if not found:
        return None
    if len(found) > 1:
        raise AttemptConfigMismatch(
            f"attempt {attempt_id!r} has {len(found)} AttemptConfigured records — corrupt log"
        )
    p = found[0].payload
    return AttemptConfig(attempt_id, int(p["call_ceiling"]), float(p["attempt_budget_credits"]))

def require_attempt_config(events: list[Event], attempt_id: str) -> AttemptConfig:
    """Fail-closed read: no lane work runs against limits nobody wrote down."""
    cfg = load_attempt_config(events, attempt_id)
    if cfg is None:
        raise AttemptConfigMismatch(f"attempt {attempt_id!r} is not configured — bind its "
                                    "limits before claiming calls or reserving credits")
    return cfg

def _compare(bound: AttemptConfig, presented: AttemptConfig) -> AttemptConfig:
    for field in ("call_ceiling", "attempt_budget_credits"):
        if getattr(bound, field) != getattr(presented, field):
            raise AttemptConfigMismatch(
                f"attempt {bound.attempt_id!r} is bound to {field}="
                f"{getattr(bound, field)!r}; this worker presented "
                f"{getattr(presented, field)!r} — refusing to rebind a safety limit"
            )
    return bound

def bind_attempt_config(repo: Path, *, problem_id: str, attempt_id: str, call_ceiling: int,
                        attempt_budget_credits: float, actor: str, clock: Callable[[], str],
                        config: LaneLogConfig = LaneLogConfig()) -> AttemptConfig:
    """Bind (or verify) this Attempt's limits. Idempotent for identical values; raises
    ``AttemptConfigMismatch`` for any difference. Concurrent binders converge: exactly one
    CAS lands and the loser re-reads and compares."""
    # Round-6 F2: validate at the PUBLIC boundary as well as the event boundary. A caller
    # must be refused with a clear error before anything is serialized, and neither check
    # may be the only one — the event validator also guards a hand-written record.
    if isinstance(call_ceiling, bool) or not isinstance(call_ceiling, int) or call_ceiling <= 0:
        raise ValueError(f"call_ceiling must be a positive int, got {call_ceiling!r}")
    if isinstance(attempt_budget_credits, bool) or not isinstance(attempt_budget_credits, (int, float)):
        raise ValueError(f"attempt_budget_credits must be a number, got {attempt_budget_credits!r}")
    if not math.isfinite(attempt_budget_credits):
        # THE dangerous one: the ledger admits while `counting_total + credits > budget` is
        # False, and every comparison against NaN is False — a NaN budget admits everything.
        raise ValueError(
            f"attempt_budget_credits must be FINITE, got {attempt_budget_credits!r} — a "
            "non-finite budget disables the per-Attempt spend cap"
        )
    if attempt_budget_credits < 0:
        raise ValueError(f"attempt_budget_credits must be non-negative, got {attempt_budget_credits!r}")
    presented = AttemptConfig(attempt_id, call_ceiling, float(attempt_budget_credits))
    for _ in range(_MAX_RETRIES):
        events = read(repo, problem_id, config=config)
        bound = load_attempt_config(events, attempt_id)
        if bound is not None:
            return _compare(bound, presented)
        event = Event(
            event_id=_config_event_id(problem_id, attempt_id),
            event_type="AttemptConfigured", problem_id=problem_id, actor=actor,
            payload={"attempt_id": attempt_id, "call_ceiling": call_ceiling,
                     "attempt_budget_credits": float(attempt_budget_credits)},
            timestamp=clock(), attempt_id=attempt_id,
        )

        def _unbound(evs: list[Event], _a=attempt_id, _p=presented) -> tuple[bool, str]:
            fresh = load_attempt_config(evs, _a)
            if fresh is None:
                return (True, "")
            # A competitor bound it between our read and this CAS attempt. Identical
            # values → idempotent success; different → deny, and the loop's re-read
            # raises the mismatch with the real bound values in the message.
            return (fresh == _p, "precondition: attempt already bound to different limits")

        try:
            append(repo, event, expected_revision=None, precondition=_unbound, config=config)
            return presented
        except LaneRevisionConflict:
            continue        # re-read: either adopt the identical record or raise mismatch
    raise LaneContention(f"attempt-config CAS did not converge for {attempt_id!r}")
```

Then modify `AttemptCreditLedger.__init__` (Task 7) to bind through it:

```python
        # F1: the budget this ledger ENFORCES is the Attempt's durable one, not whatever
        # this worker was constructed with. A different value fails closed HERE, before a
        # single reservation can be admitted against a silently-raised cap.
        self._budget = bind_attempt_config(
            repo, problem_id=problem_id, attempt_id=attempt_id,
            call_ceiling=call_ceiling, attempt_budget_credits=attempt_budget_credits,
            actor=actor, clock=clock, config=config,
        ).attempt_budget_credits
```

**Note on the shared record.** `AttemptConfigured` binds BOTH limits, so whichever component constructs first must know both. `AttemptCreditLedger` and `LaneCallLedger` therefore both take `call_ceiling` AND `attempt_budget_credits` and pass both to `bind_attempt_config`; each then reads back only the field it enforces. That is deliberate — two records could drift apart, and the drift would be invisible until one limit was already exceeded.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_attempt_config.py tests/integration/test_self_improvement_credit_ledger.py -q`
Expected: PASS (6 config tests + 5 non-finite-budget cases + the NaN-rationale test + 5 bad-ceiling cases + the credit-ledger suite including the new mismatch test).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/attempt_config.py src/llmxive/self_improvement/credit_ledger.py tests/integration/test_self_improvement_attempt_config.py tests/integration/test_self_improvement_credit_ledger.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T13): durable per-Attempt limits — one AttemptConfigured record binds the ceiling + credit budget"
```

---

### Task 14: `LaneCallLedger` — durable per-Attempt LLM-call admission (round-4 F1)

**Files:**
- Create: `src/llmxive/self_improvement/call_ledger.py`
- Test: `tests/integration/test_self_improvement_call_ledger.py`

**Depends on:** Task 2 (`Event`, `derive_event_id`, `derive_route_id`, `LEGS`, `LaneCallClaimed` + its validator), Task 3 (`append`/`read`/`LaneRevisionConflict`/`LaneContention`), and **Task 13** (`load_attempt_config` — the ceiling is bound there, not by this constructor). Independent of Tasks 4–12.

**Why this is substrate, not panel state.** Policy Contract line 313 scopes the LLM-call ceiling to the **Attempt**: "Per Attempt: `proposer + implementer·(1 + impl_regen_retries) + [proposal: 4N_p + R·(2N_p + 2)] + [patch: 2N_q + R·(N_q + 2)]`". An in-memory counter enforces it only within ONE process: a restart, a retry on another runner, or a duplicate worker each start at zero, so a single Attempt can burn the ceiling over and over — exactly the runaway the backstop exists to prevent. Admission therefore lives in the same append-only CAS log as the credit ledger.

**Second benefit — retry-stable `route_id`s.** Because the claim key is deterministic, a replayed logical operation gets back the SAME `route_id` instead of a fresh `uuid4`. That is what makes slice-0's dispatch idempotency reachable across a retry: `route_chat` documents "a caller MAY inject a durable id instead (spec 025 slice 1 — a retried logical invocation replays the identical event ids rather than minting new ones)" (`route.py:291-293`), and `execute` derives the paid `reservation_id` from `route_id` whenever an audit sink is present — so a stable id means a retried call re-enters the SAME reserved envelope and hits the `claim_dispatch` replay gate instead of double-dispatching.

**Interfaces:**
- Produces:
  - (`LEGS` and `derive_route_id` are NOT produced here — Task 2 owns them in `events.py`, because `validate_lane_event` must recompute the route id to check a `LaneCallClaimed` payload and the reverse import would be a cycle. This module imports both.)
  - `class LaneCallCeilingExceeded(RuntimeError)` — this Attempt's ceiling is spent; the Attempt fails closed (Policy Contract line 313). **Defined here** (Slice 1B imports it from this module — it is a substrate condition, not a panel-local one).
  - `@dataclass(frozen=True) class CallClaim`: `operation_id: str`, `leg: str`, `route_id: str`, `seq: int`.
  - `def project_call_claims(events: list[Event], attempt_id: str) -> dict[tuple[str, str], CallClaim]` — the `LaneCallClaimed` events for THIS `attempt_id`, keyed `(operation_id, leg)`, in `seq` order. A duplicate key with a DIFFERENT `route_id` is corruption → `raise ValueError` (fail closed; the CAS makes it unreachable, so reaching it means the log was tampered with).
  - `class LaneCallLedger`: constructor `(*, repo, problem_id, attempt_id, call_ceiling, attempt_budget_credits, actor, clock, config=LaneLogConfig())`; holds a `threading.Lock` (same rationale as `AttemptCreditLedger`: the panel's `ThreadPoolExecutor` shares ONE instance). **The ceiling it enforces is `bind_attempt_config(...).call_ceiling`, not the constructor argument** (round-5 F1) — presenting a different value fails closed at construction. It takes `attempt_budget_credits` too because one `AttemptConfigured` record binds BOTH limits (see Task 13's note); it reads back only the ceiling.
    - `claim(self, *, operation_id: str, leg: str = "primary") -> str` — returns the `route_id` admitted for this logical call. **Idempotent:** an already-claimed `(operation_id, leg)` returns its recorded `route_id` and does NOT consume another call. Raises `LaneCallCeilingExceeded` when the Attempt is at its ceiling, `LaneContention` if the CAS never converges.
    - `calls_used(self) -> int` — `len(project_call_claims(read(...), attempt_id))`, the DURABLE count (not a local counter).

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_call_ledger.py
"""F1: the ceiling is per ATTEMPT and therefore durable + cross-process. A second
process (or a restarted one) must see the calls the first one already spent."""
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from llmxive.self_improvement.attempt_config import AttemptConfigMismatch
from llmxive.self_improvement.call_ledger import (
    LaneCallCeilingExceeded, LaneCallLedger, project_call_claims,
)
from llmxive.self_improvement.events import derive_route_id
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read

def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

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

_CLOCK = lambda: "2026-07-24T00:00:00+00:00"

def _ledger(repo, ceiling=3, cfg=None):
    # attempt_budget_credits is passed because ONE AttemptConfigured record binds BOTH
    # limits (Task 13); this ledger reads back only the ceiling.
    return LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                          attempt_budget_credits=50.0, actor="lane", clock=_CLOCK,
                          config=cfg or LaneLogConfig(remote="origin"))

def test_claim_charges_once_and_replays_the_same_route_id(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    led = _ledger(c)
    first = led.claim(operation_id="lens-a", leg="primary")
    again = led.claim(operation_id="lens-a", leg="primary")   # REPLAY, not a second call
    assert first == again == derive_route_id("A1", "lens-a", "primary")
    assert led.calls_used() == 1

def test_the_two_reroute_legs_are_distinct_claims(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    led = _ledger(c)
    p = led.claim(operation_id="lens-a", leg="primary")
    f = led.claim(operation_id="lens-a", leg="fallback")
    assert p != f and led.calls_used() == 2   # the ceiling's 4N term counts BOTH legs

def test_ceiling_fails_closed(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    led = _ledger(c, ceiling=2)
    led.claim(operation_id="a"); led.claim(operation_id="b")
    with pytest.raises(LaneCallCeilingExceeded):
        led.claim(operation_id="c")

def test_an_unknown_leg_is_rejected(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    with pytest.raises(ValueError, match="leg"):
        _ledger(c).claim(operation_id="a", leg="tertiary")

def test_a_RESTARTED_process_does_not_get_a_fresh_ceiling(tmp_path, bare_remote):
    # THE F1 regression: the whole point of durability. A brand-new ledger object (a
    # restart, a retry on another runner, a duplicate worker) must observe the calls
    # already spent — an in-memory counter would hand it a fresh budget.
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    _ledger(c, ceiling=2).claim(operation_id="a")
    _ledger(c, ceiling=2).claim(operation_id="b")
    with pytest.raises(LaneCallCeilingExceeded):
        _ledger(c, ceiling=2).claim(operation_id="c")

def test_a_SECOND_CLONE_shares_the_same_ceiling(tmp_path, bare_remote):
    # Cross-PROCESS, not just cross-object: two clones of one remote, one Attempt budget.
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    _ledger(c1, ceiling=2).claim(operation_id="a")
    _ledger(c2, ceiling=2).claim(operation_id="b")   # syncs c1's claim from the ref
    with pytest.raises(LaneCallCeilingExceeded):
        _ledger(c2, ceiling=2).claim(operation_id="c")

def test_a_LARGER_ceiling_cannot_reopen_a_spent_attempt(tmp_path, bare_remote):
    # THE round-5 F1 regression: with a constructor-local ceiling this sequence admitted
    # the third call. The limit is now bound durably, so the third LEDGER is refused at
    # construction — before it can claim anything.
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    _ledger(c, ceiling=2).claim(operation_id="a")
    _ledger(c, ceiling=2).claim(operation_id="b")
    with pytest.raises(AttemptConfigMismatch, match="call_ceiling"):
        _ledger(c, ceiling=100)

def test_a_second_clone_cannot_present_a_different_ceiling(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    _ledger(c1, ceiling=2).claim(operation_id="a")
    with pytest.raises(AttemptConfigMismatch):
        _ledger(c2, ceiling=100)

def test_concurrent_claimers_never_exceed_the_ceiling(tmp_path, bare_remote):
    # The panel's ThreadPoolExecutor shares ONE ledger; admission must be atomic.
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    led = _ledger(c, ceiling=4)
    ok, refused = [], []

    def _take(i):
        try:
            ok.append(led.claim(operation_id=f"op-{i}"))
        except LaneCallCeilingExceeded:
            refused.append(i)

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_take, range(10)))

    assert len(ok) == 4 and len(set(ok)) == 4      # exactly the ceiling, all distinct
    assert len(refused) == 6
    assert len(project_call_claims(read(c, "P1", config=LaneLogConfig(remote="origin")), "A1")) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_call_ledger.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.self_improvement.call_ledger'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/call_ledger.py
"""Durable per-Attempt admission for logical ``route_chat`` invocations (Policy Contract
line 313; round-4 review F1).

The ceiling is scoped to the ATTEMPT, so it cannot live in a process's memory: a restart,
a retry on another runner, or a duplicate worker would each start at zero and let one
Attempt spend the ceiling repeatedly. Every logical call therefore CAS-appends a
``LaneCallClaimed`` event to the authoritative lane ref, and the count of those events IS
the spend. The claim key is deterministic, so a replayed operation returns the SAME
``route_id`` — which is also what lets slice-0's dispatch-idempotency gate recognize a
retried call instead of double-dispatching it (``route.py:291-293``)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llmxive.self_improvement.attempt_config import bind_attempt_config
from llmxive.self_improvement.events import LEGS, Event, derive_event_id, derive_route_id
from llmxive.self_improvement.lane_log import (
    LaneContention, LaneLogConfig, LaneRevisionConflict, append, read,
)

_MAX_RETRIES = 8

class LaneCallCeilingExceeded(RuntimeError):
    """This Attempt has spent its logical-``route_chat`` ceiling (Policy Contract line
    313). The Attempt fails closed — never a silent extra call."""

@dataclass(frozen=True)
class CallClaim:
    operation_id: str
    leg: str
    route_id: str
    seq: int

def project_call_claims(events: list[Event], attempt_id: str) -> dict[tuple[str, str], CallClaim]:
    """The Attempt's admitted calls, keyed ``(operation_id, leg)``, in authoritative seq
    order. A duplicate key with a DIFFERENT route_id is corruption (the CAS makes it
    unreachable) → fail closed rather than silently pick one."""
    claims: dict[tuple[str, str], CallClaim] = {}
    for e in events:
        if e.event_type != "LaneCallClaimed" or e.payload.get("attempt_id") != attempt_id:
            continue
        p = e.payload
        key = (p["operation_id"], p["leg"])
        existing = claims.get(key)
        if existing is not None:
            if existing.route_id != p["route_id"]:
                raise ValueError(
                    f"corrupt call ledger: {key} claimed twice with different route ids "
                    f"({existing.route_id!r} then {p['route_id']!r})"
                )
            continue
        claims[key] = CallClaim(p["operation_id"], p["leg"], p["route_id"], int(e.seq))
    return claims

class LaneCallLedger:
    def __init__(self, *, repo: Path, problem_id: str, attempt_id: str, call_ceiling: int,
                 attempt_budget_credits: float, actor: str, clock: Callable[[], str],
                 config: LaneLogConfig = LaneLogConfig()) -> None:
        self._repo, self._problem_id, self._attempt_id = repo, problem_id, attempt_id
        self._actor, self._clock, self._config = actor, clock, config
        # F1: the ceiling this ledger ENFORCES is the Attempt's DURABLE one. Presenting a
        # different value raises AttemptConfigMismatch here, before a single call can be
        # admitted against a silently-raised cap. (bind_attempt_config validates
        # positivity, so the local check is gone — it lives in one place now.)
        self._ceiling = bind_attempt_config(
            repo, problem_id=problem_id, attempt_id=attempt_id, call_ceiling=call_ceiling,
            attempt_budget_credits=attempt_budget_credits, actor=actor, clock=clock,
            config=config,
        ).call_ceiling
        self._lock = threading.Lock()   # the panel shares ONE instance across its threads

    def calls_used(self) -> int:
        """The DURABLE spend — read from the log, never a local counter."""
        return len(project_call_claims(read(self._repo, self._problem_id, config=self._config),
                                       self._attempt_id))

    def claim(self, *, operation_id: str, leg: str = "primary") -> str:
        if leg not in LEGS:
            raise ValueError(f"unknown leg {leg!r} — must be one of {LEGS}")
        key = (operation_id, leg)
        route_id = derive_route_id(self._attempt_id, operation_id, leg)
        with self._lock:
            for _ in range(_MAX_RETRIES):
                events = read(self._repo, self._problem_id, config=self._config)
                claims = project_call_claims(events, self._attempt_id)
                landed = claims.get(key)
                if landed is not None:
                    return landed.route_id        # REPLAY — same id, not charged again
                if len(claims) >= self._ceiling:
                    raise LaneCallCeilingExceeded(
                        f"attempt {self._attempt_id!r} has spent its {self._ceiling} logical "
                        f"route_chat invocations (Policy Contract line 313) — failing closed"
                    )
                event = self._claim_event(operation_id, leg, route_id)

                def _admits(evs: list[Event], _k=key) -> tuple[bool, str]:
                    fresh = project_call_claims(evs, self._attempt_id)
                    if _k in fresh:
                        return (True, "")         # already landed → idempotent
                    return (len(fresh) < self._ceiling,
                            f"precondition: attempt at its {self._ceiling}-call ceiling")

                try:
                    # AS SHIPPED: expected_revision=None, for the same reason as the credit
                    # ledger — a revision CAS compares the whole per-Problem stream, which
                    # also carries audit appends, so admission would lose its retry budget
                    # to events that have nothing to do with the ceiling. `_admits` is the
                    # invariant and is recomputed inside every CAS attempt.
                    append(self._repo, event, expected_revision=None,
                           precondition=_admits, config=self._config)
                    return route_id
                except LaneRevisionConflict:
                    # Lost the CAS (a stale revision OR a competitor that just consumed the
                    # last call). Re-read: the loop's pre-check then either finds our claim
                    # already landed, admits us, or raises LaneCallCeilingExceeded — so a
                    # ceiling loss surfaces as the CEILING error, never as contention.
                    continue
            raise LaneContention(f"call-claim CAS did not converge for {key}")

    def _claim_event(self, operation_id: str, leg: str, route_id: str) -> Event:
        return Event(
            event_id=derive_event_id(self._problem_id,
                                     f"call\x00{self._attempt_id}\x00{operation_id}\x00{leg}"),
            event_type="LaneCallClaimed", problem_id=self._problem_id, actor=self._actor,
            payload={"attempt_id": self._attempt_id, "operation_id": operation_id,
                     "leg": leg, "route_id": route_id, "call_ceiling": self._ceiling},
            timestamp=self._clock(), attempt_id=self._attempt_id,
        )
```

**Note on cost.** A 5-lens/3-round proposal run claims up to 56 calls, so this adds up to 56 ref-CAS appends per Attempt — the same order as the credit ledger's reservation traffic, and the price of a ceiling that actually binds. If the concurrent test shows the `_MAX_RETRIES = 8` cap being hit under the panel's 8-way fan-out, raise the cap — do NOT weaken the precondition.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_call_ledger.py -q`
Expected: PASS (9 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/call_ledger.py tests/integration/test_self_improvement_call_ledger.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1A T14): durable per-Attempt call ledger — CAS admission + retry-stable route ids"
```

---

## Final verification (before the whole-branch review)

- [ ] Package exports (`src/llmxive/self_improvement/__init__.py`): `Event`, `derive_event_id`, `validate_lane_event`, `LANE_REF`, `append`, `read`, `LaneRevisionConflict`, `LaneContention`, `LaneCoordinator`, `project_coordinator`, `cas_claim`, `cas_release`, `AttemptCreditLedger`, `AttemptConfig`, `AttemptConfigMismatch`, `bind_attempt_config`, `load_attempt_config`, `require_attempt_config`, `LaneCallLedger`, `LaneCallCeilingExceeded`, `derive_route_id`, `project_call_claims`, `EventStoreRouteAudit`, `reconcile_unknown`. Test they import.
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
| 8 | exception compat under-specified | T1 gives the ledger its own `Ledger*` SUBCLASSES + exhaustive core→ledger translation at the boundary, with `except`-still-catches tests. (Rounds 2–6 said ALIASES; implementation showed that breaks `type(exc).__name__`, which `execute` reports — see T1's interface block.) |
| 9 | `KNOWN_EVENT_TYPES` not "full" | renamed `KNOWN_EVENT_TYPES_V1`; a later slice extends the set AND the projection handlers together. (Round 3 F7 then corrected the bump rule: a VOCABULARY extension must NOT bump `SCHEMA_VERSION` — only a record-SHAPE change does.) |
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

**Round 4 (cross-slice: the findings the 1B review assigned back to the substrate):**

| # | Finding | Resolved by |
|-|-|-|
| 1 | the LLM-call ceiling was in-memory, so NOT per-Attempt | **new T13** `LaneCallLedger`: a `LaneCallClaimed` CAS admission per logical call, counted from the durable log — plus retry-stable `route_id`s (`derive_route_id`), which is also what lets slice-0's dispatch-idempotency gate recognize a retried call. Regression tests: restarted-object, second-clone, and concurrent-claimer |
| 6 | `ReviewRerouted` payload validation was only nominal | T2 gains `TYPE_VALIDATORS` — a per-type schema table run by `validate_lane_event`, with `AttemptConfigured`/`LaneCallClaimed` registered here and `ReviewRerouted` registered by Slice 1B T1; unlisted types are envelope-only BY DESIGN (documented + tested). (Round 5 then widened the signature to the whole event and named the table `TYPE_VALIDATORS`.) |
| 10 | the bootstrap concurrency test was sequential | T1 adds the `_after_probe` seam (the bootstrap counterpart of `_after_parent`); T3's test now holds two clones past the existence probe and races the push, then asserts a single genesis commit on the bare remote. The old sequential case is kept, honestly renamed `test_second_clone_adopts_the_existing_genesis` |
| — | leftovers found while applying the above | File Structure said `Ledger*` "subclassing the core's", contradicting round-3 F8's ALIAS decision — corrected; row 9 above said a vocabulary extension bumps `SCHEMA_VERSION`, contradicting round-3 F7 — corrected; `LaneContention` was about to be declared in two modules — now defined once in `lane_log.py` |

**Round 5 (the substrate findings from the 1B review):**

| # | Finding | Resolved by |
|-|-|-|
| 1 | the durable call ledger checked its count against a CONSTRUCTOR-LOCAL ceiling, so a later worker could present a bigger one (and the same held for the credit budget, which guards money) | **new T13** `AttemptConfig`: ONE `AttemptConfigured` record per Attempt binds `call_ceiling` + `attempt_budget_credits` under the ref-CAS; T14's `LaneCallLedger` and T7's `AttemptCreditLedger` both enforce the BOUND value and raise `AttemptConfigMismatch` at construction on any difference. Tests: same-clone larger-ceiling, restarted-object, two-clone mismatch, concurrent binders, unconfigured-fails-closed, and the credit-budget counterpart |
| 5 | `LaneCallClaimed` validation checked only basic types | T2's validators now receive the **whole event**, so `payload["attempt_id"]` must equal the envelope's (the projection filters by the payload's, so a disagreement misattributes the claim); `leg ∈ LEGS`; and `route_id` must equal `derive_route_id(attempt, operation, leg)`. `derive_route_id` + `LEGS` moved to `events.py` to make that check possible without an import cycle. The cross-EVENT ceiling-consistency check is finding 1's `AttemptConfig`, where it belongs |

Renumbering note: round-4's Task 13 (`LaneCallLedger`) is now **Task 14**; the new `AttemptConfig` task takes 13, because the ledger's ceiling is read from it.

**Round 6:**

| # | Finding | Resolved by |
|-|-|-|
| 2 | the credit budget accepted `nan`/`inf` (and `bool`) | `nan < 0` is False, and the ledger admits while `counting_total + credits > budget` is False — so a NaN budget makes the money cap "always admit". T13 now validates `math.isfinite` + rejects `bool`/non-numeric at BOTH the `bind_attempt_config` API boundary and the `AttemptConfigured` event boundary, with a test that asserts the failure mode directly so the rationale cannot rot. T2's canonical serializers also pass `allow_nan=False`: `json.dumps` emits bare `NaN`/`Infinity` (invalid JSON that round-trips only in Python), so a non-finite number can never reach the ref |
| 3 | `AttemptConfigured` / `LaneCallClaimed` still accepted unknown keys | T2 adds a shared `_exact_keys` helper and pins both schemas, matching `ReviewRerouted`. An unrecognized key cannot be told from a typo, and in append-only history it forces later readers to guess at semantics nobody defined |

**Round 7:**

| # | Finding | Resolved by |
|-|-|-|
| 1 | individual reservation AMOUNTS were unvalidated (the budget was, the amounts were not) | T7 `reserve()` rejects non-finite, `bool`, and `<= 0` amounts with `ValueError` — never `False`, which would read as a routine budget skip — BEFORE any read or append; T2 registers an `AttemptCreditReserved` payload validator (`_finite_positive`) so a persisted record carries the same guarantee, since `project_reservations` SUMS `reserved_credits` into the number the cap is compared against. A negative amount was the live hole: it lowers `counting_total` and hands back budget already spent (`allow_nan=False` never catches it, and a serialization failure is not the ledger's declared contract anyway). T6 pins that consequence in a projection test |
