# Self-Improvement Lane — Slice 2: Attempt Lifecycle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Attempt lifecycle a durable, executable state machine — the transition table as DATA with a fold that fails closed on any illegal history — and give it the four mechanisms rev 22 specified: claim generations, renewable heartbeats with skew-padded expiry, side-effect intents with the four dispositions, and authoritative time. Closes the seam Slice 1B deliberately left open: a proposal review now has somewhere to record its verdict.

**Architecture:** Everything is a projection over the existing append-only lane log — no new store, no new ref. The Attempt machine lives on the per-Problem stream; the claim lives on the coordinator stream; that split is load-bearing and is why the fencing guarantee is stated carefully (Global Constraints). Slice 1A's CAS discipline (`append(..., expected_revision, precondition)`) is the only write path, and the terminal-slot precondition is what makes reclaim safe. `coordinator.py` is EXTENDED (generations, heartbeats, expiry) rather than shadowed by a parallel claim module.

**Tech Stack:** Python ≥ 3.11; `pytest`; packages `llmxive.self_improvement`. No new third-party dependencies — the model tests are exhaustive table enumeration plus seeded random walks, not `hypothesis` (deterministic, no dep, and reproducible from the seed printed on failure).

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from spec 025 rev 22.

- **The transition table is DATA, declared once (Constitution I).** `TRANSITIONS` in `lifecycle.py` is the single source of truth for from-states, event, to-state, idempotency key, terminal?, counted?. No function re-encodes a transition in an `if` chain; no test hard-codes a table row it could read. The spec's table and `TRANSITIONS` are checked against each other by a test that parses the spec (Task 3, Step 6) — a spec/code drift is a FAILING TEST, not a review finding.
- **Fail closed on any illegal history.** `project_attempt` RAISES on an unknown event type, an out-of-order `seq`, a transition not in the table, or a second terminal. It never ignores, never "best-effort skips". This matches `project_coordinator` (`coordinator.py:40-83`), which is the house pattern.
- **Exactly one terminal per Attempt (FR-035).** Every terminal append is CAS-conditioned on the freshly-rebuilt projection having NO terminal for that Attempt. First writer wins; the loser discards its own terminal and performs NO further side effect. This guards two DIFFERENT terminals racing, which per-transition idempotency keys do not.
- **Cross-stream generation checks are ADVISORY; the hard guarantee is the single-stream terminal-slot CAS.** The coordinator stream and the Problem stream are separate refs (`lane_log._log_ref`), so an Attempt-stream append CANNOT atomically verify the coordinator's current `claim_generation`. A stale generation is therefore rejected on a best-effort read, and safety does not depend on it: the terminal-slot CAS runs inside ONE stream and decides the race. **Do not describe the generation stamp as atomic fencing across streams** — that would be exactly the content-vs-actor overclaim rev 22 removed.
- **`seq` is the SOLE ordering authority (FR-009/FR-036).** Timestamps measure DURATIONS only. Any code that sorts by timestamp is a defect. Heartbeat liveness is observable through `seq` alone, which is the one liveness signal that survives total loss of trusted time.
- **Authoritative time or no lane work (FR-036).** Every recorded instant is authority-derived (GitHub server clock via the `Date` response header, offset sampled at run start and re-measured each `heartbeat_interval`). A run that cannot establish an offset MUST NOT claim, heartbeat, reclaim, or terminalize. Comparing a writer's timestamp against that same writer's clock is the vacuous check rev 22 withdrew — do not reintroduce it.
- **Skew padding always favours the safe error (FR-036).** Reclaim requires `elapsed ≥ claim_expiry + max_clock_skew`; `max_claim_hold_time` and the operational-cooldown floor pad the same way. Padding is NEVER applied in the direction that makes a bound trip sooner.
- **Four dispositions, and `ambiguous` is not a guess (FR-035, rev 22).** An outstanding intent resolves to `landed` / `rejected` / `contained` / `ambiguous`. Pushes are **`contained`** (a late push can still arrive; it is harmless because the namespace is dead). Merges and reverts are **`ambiguous` → quarantine** — expected-`head_sha` constrains which COMMIT merges, never which ACTOR, so it fences nothing. Declaring "did not land" without an externally enforced precondition is forbidden.
- **Reclaim BLOCKS on an unreconciled intent.** `ClaimExpired`'s CAS precondition includes "no `SideEffectRequested` lacking its matching `SideEffectObserved`". A reclaimer facing one MUST reconcile it (or quarantine) and reclaim in a SUBSEQUENT CAS.
- **Policy values are bound to the CLAIM, not read live.** `claim_expiry_s`, `max_claim_hold_time_s`, `max_clock_skew_s`, and `policy_version` are recorded on `ClaimGranted` and read from there by the reclaimer, so a policy edit mid-claim cannot retroactively expire a live run. Same discipline as `bind_attempt_config` (Slice 1A Task 13).
- **Exact policy values (Policy Contract v1, rev 22).** `heartbeat_interval` = 5 min; `claim_expiry` = 15 min; `max_clock_skew` = 5 min; `max_claim_hold_time` = **3 h 40 min** = 220 min = `(45×2) + 10 + 20 + 30 + 30 + 15 + 10 + 15`; quality cap M = 3 → 30-day cooldown; operational K = 5 CONSECUTIVE **AND** ≥ 24 h since `streak_started_at` → 7-day cooldown. `max_claim_hold_time` is DERIVED in code from the named phase constants, never written as a literal 220 (Constitution I — the LLM-call-ceiling row is the precedent).
- **Counted vs uncounted terminals (transition table).** Counted toward the per-Problem quality cap: `impl_failed`, `publish_failed`, `test_failed`, `eval_failed`, `reverted`. NOT counted: `rejected`, `unsupported_scope`, `superseded`, `review_aborted`, `attempt_abandoned`. The two counters never cross-contaminate, in either direction.
- **Attempt state ≠ Problem disposition.** `cooldown` is keyed by `problem_id` and belongs to the Problem, not the Attempt. Two enums, no shared namespace — collapsing them is how a per-Problem rest gets misread as an Attempt outcome.
- **Default-off.** The lifecycle driver is gated by `LLMXIVE_SELF_IMPROVEMENT_ENABLED` (default off). No scheduler lane is registered in this slice. Distinct from `LLMXIVE_SELF_IMPROVEMENT_LIVE` (FR-029, slice 6) — that one gates live merges to `main`; this one gates the lane running at all.
- **No external side effects in this slice.** No GitHub call, no push, no merge. Intents and dispositions are lane-log logic exercised through a `Reconciler` Protocol test double with real logic. The publisher/promotion domains arrive in slices 3–4.
- **Real tests, no mocks (Constitution III).** Real temp-git repos, the real lane log, real CAS. Protocol test doubles implementing real logic are fine; `unittest.mock` is not the primary path. The one network-touching test (`GitHubDateClock` against `api.github.com`) lives in `tests/real_call` and is skipped without `LLMXIVE_REAL_TESTS=1`.
- **Behavior-preserving for existing callers.** The full non-slow suite (`pytest tests/unit tests/contract tests/integration -m "not slow"`) MUST stay green after every task.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push** — rebase onto `origin/main` at PR time only. Commit explicit paths (`git commit -o <path>`), never `git add -A`: six untracked pipeline artifacts live in the tree and must not be swept.

## Dependencies + scope boundary

**Consumes (Slice 1A/1B, already delivered):** `lane_log.append/read/bootstrap_lane_log`, `LaneLogConfig`, `LaneRevisionConflict`, `LaneContention`; `Event`, `derive_event_id`, `validate_lane_event`, `KNOWN_EVENT_TYPES_V1`, `TYPE_VALIDATORS`, `_require`, `_exact_keys`, `_same_attempt`, `payload_field`, `COORDINATOR_STREAM`, `SCHEMA_VERSION`; `LaneCoordinator`, `ClaimOutcome`, `project_coordinator`, `cas_claim`, `cas_release`; `bind_attempt_config`/`require_attempt_config`.

**Produces (consumed by later slices):** `AttemptState`, `ProblemDisposition`, `TRANSITIONS`, `project_attempt`, `cas_attempt_transition`, `IllegalTransition`; `AuthoritativeClock`, `GitHubDateClock`, `NoTrustedTimeError`; `cas_heartbeat`, `cas_reclaim`, `ClaimTerms`; `IntentDisposition`, `record_intent`, `observe_intent`, `unreconciled_intents`, `Reconciler`, `LaneQuarantine`; `problem_cooldown`, `CooldownState`.

**In scope:** the complete machine (every row of the transition table is declared and enforced), the claim mechanics, time, intents, the two counters, monitoring removal, the merge timestamp, and the proposal-stage terminals (`ProposalVerified` / `Rejected` / `ReviewAborted`) that 1B has no home for.

**Out of scope (later slices):** the implementer, the candidate publisher, container testing, evaluation, promotion/revert side effects, discovery + issue ranking. Those transitions are DECLARED in `TRANSITIONS` (so the machine is complete and the model tests exercise it) but no producer drives them in this slice. A transition with no producer is not dead code — it is the contract the next slice implements against.

**Deliberately NOT changed:** `run_proposal_review` and the 1B convergence wiring keep their current signatures; Task 11 adds the terminal write at the ONE call site that already computes the verdict.

## File Structure

- `src/llmxive/self_improvement/clock.py` — `AuthoritativeClock` protocol, `GitHubDateClock`, `FixedOffsetClock` (test/CI double with real logic), `NoTrustedTimeError`, `parse_http_date`. One responsibility: producing an instant the whole lane can compare.
- `src/llmxive/self_improvement/lifecycle.py` — `AttemptState`, `ProblemDisposition`, `Transition`, `TRANSITIONS`, `TERMINAL_STATES`, `COUNTED_TERMINALS`, `project_attempt`, `cas_attempt_transition`, `IllegalTransition`. One responsibility: what may legally happen to an Attempt.
- `src/llmxive/self_improvement/intents.py` — `IntentDisposition`, `IntentRecord`, `Reconciler`, `record_intent`, `observe_intent`, `unreconciled_intents`, `LaneQuarantine`. One responsibility: the saga's intent bookkeeping and its four outcomes.
- `src/llmxive/self_improvement/cooldown.py` — `CooldownCause`, `CooldownState`, `problem_cooldown`, `cas_cooldown`. One responsibility: the two independent counters.
- `src/llmxive/self_improvement/coordinator.py` — **modified**: `claim_generation` on `LaneCoordinator`; `ClaimTerms`; `cas_heartbeat`; `cas_reclaim`; `cas_release_terminal`; `ClaimOutcome.generation`; `MonitorEnded` + `last_autonomous_merge_at` folding.
- `src/llmxive/self_improvement/events.py` — **modified**: new event types + validators (vocabulary extension only; `SCHEMA_VERSION` stays 1, per Slice 1A's F7 rule).
- `src/llmxive/self_improvement/__init__.py` — **modified**: exports.
- `specs/025-self-improvement-lane/spec.md` — **modified** (Task 1, rev 23): three gaps this plan found while grounding.

---

### Task 1: Spec amendment (rev 23) — three gaps found while grounding the plan

Every prior round amended the spec before implementing against it. Grounding this plan against the real substrate surfaced three things rev 22 does not cover. Land them first so the code is implementing a spec that is true.

**Files:**
- Modify: `specs/025-self-improvement-lane/spec.md`
- Modify: `notes/2026-07-26-spec025-slice1-implementation.md`

**Interfaces:** none (documentation).

- [ ] **Step 1: Add the cross-stream honesty statement to FR-035**

Under the fencing protocol's "Generation-stamped appends" bullet, append:

> **Cross-stream limit (rev 23).** The coordinator and each Problem are SEPARATE refs, so an Attempt-stream append cannot atomically read the coordinator's current `claim_generation`. The generation stamp is therefore an ADVISORY staleness filter — it rejects a superseded writer that loses the race to read, not one that wins it. Safety does not rest on it: the exactly-one-terminal CAS runs inside a SINGLE stream and is what actually decides a reclaim race. Describing the stamp as cross-stream fencing would repeat the content-vs-actor error rev 22 corrected.

- [ ] **Step 2: Add the terminal-Attempt release transition**

The reclaim rules cover "claim held, Attempt NOT terminal". They do not cover a run that wrote its terminal and then died before `ClaimReleased` — the lane wedges exactly as FR-035 says it must not. Add to the transition table, after the `ClaimExpired` row:

```
|(claim held; the claimed Attempt IS terminal; no unreconciled intent)|ClaimReleasedByReclaimer|(Attempt unchanged)|`(attempt_id,"reclaim-release",generation)`|`ClaimReleased` + `claim_generation`++ — frees a slot whose Attempt already ended|no terminal is written (one exists); an unreconciled or `ambiguous` intent BLOCKS this, exactly as it blocks `ClaimExpired`|
```

And a note under the table:

> **Releasing a terminal Attempt's claim (rev 23).** `ClaimExpired` writes a terminal, so it cannot help an Attempt that already has one — and "exactly one terminal" means it must not try. A crash between the terminal append and `ClaimReleased` therefore had no recovery path, wedging the lane on the very failure FR-035 exists to prevent. This row is deliberately weaker than `ClaimExpired`: it needs no expiry (the Attempt is over, so no live run can be harmed) but it keeps the unreconciled-intent block, because an outstanding side effect is outstanding regardless of the Attempt's state.

- [ ] **Step 3: Add the two Policy Contract rows**

```
|`LLMXIVE_SELF_IMPROVEMENT_ENABLED` (new in rev 23)|**Default OFF.** Gates whether the lane runs AT ALL. Distinct from `LLMXIVE_SELF_IMPROVEMENT_LIVE` (FR-029), which gates live merges to `main` at slice 6: a lane can be enabled and still never touch `main`. Off ⇒ the driver is a no-op and no lane event is written.|
|Claim-bound policy (new in rev 23)|`claim_expiry`, `max_claim_hold_time`, `max_clock_skew`, and `policy_version` are RECORDED ON `ClaimGranted` and read from there by any later reclaimer, so a policy edit mid-claim cannot retroactively expire a live run. Same discipline as the durably-bound per-Attempt limits (FR-033).|
```

- [ ] **Step 4: Update the rev-22 status line to rev 23**

Prepend a rev-23 summary to the `**Status**:` line in the same cumulative style (newest first), naming the three gaps above and that they were found by grounding the Slice-2 plan against the substrate rather than by review.

- [ ] **Step 5: Verify the table is still well-formed**

```bash
python3 -c "
lines=open('specs/025-self-improvement-lane/spec.md').read().split('\n')
bad=[(i,len(l.strip().split('|'))-2) for i,l in enumerate(lines,1)
     if l.strip().startswith('|') and l.strip().endswith('|')
     and not set(l.strip())<=set('|- ') and 290<i<345
     and len(l.strip().split('|'))-2!=6]
print('rows with != 6 fields:', bad); assert not bad
txt=open('specs/025-self-improvement-lane/spec.md').read()
assert txt.count('(')==txt.count(')'), 'paren delta'
print('OK')
"
```
Expected: `rows with != 6 fields: []` then `OK`.

- [ ] **Step 6: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o specs/025-self-improvement-lane/spec.md \
  notes/2026-07-26-spec025-slice1-implementation.md \
  -m "spec(025 rev-23): cross-stream fencing limit, terminal-Attempt release, lane flag"
git log --oneline -1
```

---

### Task 2: Authoritative clock (FR-036)

Everything downstream is a duration, so this comes first.

**Files:**
- Create: `src/llmxive/self_improvement/clock.py`
- Test: `tests/unit/test_self_improvement_clock.py`
- Test: `tests/real_call/test_self_improvement_clock_real.py`

**Interfaces:**
- Consumes: nothing from the lane (deliberately standalone — it is the one module with no lane dependency).
- Produces: `AuthoritativeClock` (Protocol, `__call__() -> str`), `GitHubDateClock`, `FixedOffsetClock`, `NoTrustedTimeError`, `parse_http_date`.

**Why a `Callable[[], str]` shape:** `bind_attempt_config` and every other 1A entry point already take `clock: Callable[[], str]`. The authoritative clock satisfies that contract exactly, so it drops into existing call sites without a parallel API (Constitution I).

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_self_improvement_clock.py
"""FR-036 authoritative time. The lane compares durations across independent runners, so
every recorded instant must come from ONE authority — rev 21's check compared a writer's
timestamp against that same writer's clock, which cannot detect skew at all."""
from __future__ import annotations

import datetime as dt

import pytest

from llmxive.self_improvement.clock import (
    FixedOffsetClock,
    GitHubDateClock,
    NoTrustedTimeError,
    parse_http_date,
)

DATE_HDR = "Fri, 31 Jul 2026 12:00:00 GMT"


def test_parse_http_date_yields_an_aware_utc_instant():
    got = parse_http_date(DATE_HDR)
    assert got == dt.datetime(2026, 7, 31, 12, 0, 0, tzinfo=dt.timezone.utc)


@pytest.mark.parametrize("bad", ["", "not a date", "Fri, 31 Jul 2026", "1753963200"])
def test_parse_http_date_refuses_anything_it_cannot_parse(bad):
    # Fail closed: a silently-wrong offset poisons every duration in the lane.
    with pytest.raises(NoTrustedTimeError):
        parse_http_date(bad)


def test_the_clock_reports_authority_time_not_local_time():
    # Local clock is 30 min FAST; the authority says 12:00. The stamp follows the AUTHORITY.
    local = [dt.datetime(2026, 7, 31, 12, 30, 0, tzinfo=dt.timezone.utc)]
    clock = GitHubDateClock(fetch_date_header=lambda: DATE_HDR, local_now=lambda: local[0])
    assert clock().startswith("2026-07-31T12:00:00")

    # ...and it TRACKS local elapsed time, rather than pinning to the sample forever.
    local[0] += dt.timedelta(minutes=2)
    assert clock().startswith("2026-07-31T12:02:00")


def test_the_offset_is_re_measured_after_the_refresh_interval():
    headers = [DATE_HDR, "Fri, 31 Jul 2026 13:00:00 GMT"]
    calls = []

    def fetch():
        calls.append(1)
        return headers[min(len(calls) - 1, 1)]

    local = [dt.datetime(2026, 7, 31, 12, 0, 0, tzinfo=dt.timezone.utc)]
    clock = GitHubDateClock(fetch_date_header=fetch, local_now=lambda: local[0],
                            refresh_interval_s=300)
    clock()
    local[0] += dt.timedelta(seconds=299)
    clock()
    assert len(calls) == 1, "re-measured before the interval elapsed"
    local[0] += dt.timedelta(seconds=2)
    clock()
    assert len(calls) == 2, "did not re-measure after the interval elapsed"


def test_a_clock_that_cannot_reach_the_authority_raises_and_never_falls_back():
    # The forbidden behavior is silently using the local clock: that is precisely the
    # untrusted input FR-036 exists to exclude.
    def boom():
        raise OSError("network down")

    clock = GitHubDateClock(fetch_date_header=boom)
    with pytest.raises(NoTrustedTimeError):
        clock()


def test_a_stale_offset_is_not_reused_when_re_measurement_fails():
    headers = [DATE_HDR]

    def fetch():
        if headers:
            return headers.pop()
        raise OSError("network down")

    local = [dt.datetime(2026, 7, 31, 12, 0, 0, tzinfo=dt.timezone.utc)]
    clock = GitHubDateClock(fetch_date_header=fetch, local_now=lambda: local[0],
                            refresh_interval_s=300)
    assert clock().startswith("2026-07-31T12:00:00")
    local[0] += dt.timedelta(seconds=400)
    with pytest.raises(NoTrustedTimeError):
        clock()  # refresh due, refresh failed -> no trusted time, NOT the stale offset


def test_fixed_offset_clock_is_a_real_implementation_not_a_stub():
    clock = FixedOffsetClock(offset_s=-1800,
                             local_now=lambda: dt.datetime(2026, 7, 31, 12, 30,
                                                           tzinfo=dt.timezone.utc))
    assert clock().startswith("2026-07-31T12:00:00")
```

```python
# tests/real_call/test_self_improvement_clock_real.py
"""The authority is real: GitHub actually serves a usable Date header (Constitution III)."""
from __future__ import annotations

import datetime as dt
import os

import pytest

from llmxive.self_improvement.clock import GitHubDateClock, parse_http_date

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call suite")


def test_github_serves_a_parseable_date_header_close_to_local_time():
    clock = GitHubDateClock()
    stamped = dt.datetime.fromisoformat(clock())
    assert stamped.tzinfo is not None
    drift = abs((stamped - dt.datetime.now(dt.timezone.utc)).total_seconds())
    # 5 min is max_clock_skew: if a healthy developer machine exceeds it against the real
    # authority, the policy value is wrong and this test is the place to find out.
    assert drift < 300, f"local clock differs from GitHub by {drift}s"


def test_the_raw_header_is_what_we_think_it_is():
    raw = GitHubDateClock()._fetch()
    assert parse_http_date(raw).tzinfo == dt.timezone.utc
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/unit/test_self_improvement_clock.py -q`
Expected: collection error, `ModuleNotFoundError: llmxive.self_improvement.clock`.

- [ ] **Step 3: Implement**

```python
# src/llmxive/self_improvement/clock.py
"""FR-036: authoritative time. Lane runs execute on independent GitHub runners with
independent clocks, and every bound the lane enforces (heartbeat renewal, ``claim_expiry``,
``max_claim_hold_time``, ``streak_started_at``, ``cooldown_until``) is a DURATION. Comparing
runners' timestamps therefore requires one clock they share.

Rev 21 tried to validate a timestamp against "the appending process's own clock" — the same
process that generated it, so the comparison is vacuous — and to reject anything trailing the
ref's latest, which let one fast-skewed runner poison the ref and reject correctly-timed
runners indefinitely. Both are withdrawn. The authority here is GitHub's server clock, which
every lane run can already reach because the lane is GitHub-native.

``seq`` remains the SOLE ordering authority (FR-009). Nothing here orders events."""

from __future__ import annotations

import datetime as dt
import email.utils
import urllib.request
from typing import Callable, Protocol

#: Read from any authenticated response; ``/rate_limit`` is documented as not counting
#: against the rate limit, so a run that has not yet called the API pays nothing for it.
RATE_LIMIT_URL = "https://api.github.com/rate_limit"

#: Policy Contract: re-measure each ``heartbeat_interval`` so a long run cannot drift.
DEFAULT_REFRESH_INTERVAL_S = 300


class NoTrustedTimeError(RuntimeError):
    """No authority-derived instant is available, so the run performs NO lane work.

    Deliberately fatal rather than degrading to the local clock: a silently-wrong offset
    poisons every duration the lane derives, and the failure mode is EVICTING A LIVE
    CLAIM-HOLDER. A run that cannot establish time needs no special recovery — the claim it
    does not take cannot wedge, and a claim it already holds is recovered by ordinary
    expiry."""


class AuthoritativeClock(Protocol):
    """Satisfies the ``clock: Callable[[], str]`` contract every 1A entry point already
    takes, so this drops in without a parallel time API (Constitution I)."""

    def __call__(self) -> str: ...


def parse_http_date(raw: str) -> dt.datetime:
    """Parse an RFC 7231 ``Date`` header into an aware UTC instant, or raise.

    Fails closed on anything unparseable: a header we cannot read is not a weaker
    authority, it is NO authority."""
    parsed = email.utils.parsedate_to_datetime(raw) if raw else None
    if parsed is None:
        raise NoTrustedTimeError(f"unparseable Date header: {raw!r}")
    return parsed.astimezone(dt.timezone.utc)


def _default_fetch() -> str:
    with urllib.request.urlopen(RATE_LIMIT_URL, timeout=10) as resp:  # noqa: S310
        header = resp.headers.get("Date")
    if not header:
        raise NoTrustedTimeError(f"{RATE_LIMIT_URL} returned no Date header")
    return header


class GitHubDateClock:
    """Authority-derived instants, sampled as an OFFSET rather than per-call.

    Sampling an offset (not stamping each event with a fresh fetch) keeps the clock cheap
    and monotonic between refreshes while still tracking real elapsed time: the local clock
    measures the interval, the authority fixes the origin. A local clock that is wrong by a
    constant is therefore harmless; one that drifts is caught at the next refresh."""

    def __init__(self, *, fetch_date_header: Callable[[], str] | None = None,
                 local_now: Callable[[], dt.datetime] | None = None,
                 refresh_interval_s: int = DEFAULT_REFRESH_INTERVAL_S) -> None:
        self._fetch = fetch_date_header or _default_fetch
        self._local_now = local_now or (lambda: dt.datetime.now(dt.timezone.utc))
        self._refresh_interval_s = refresh_interval_s
        self._offset: dt.timedelta | None = None
        self._sampled_local: dt.datetime | None = None

    def _sample(self) -> None:
        local = self._local_now()
        try:
            header = self._fetch()
        except NoTrustedTimeError:
            raise
        except Exception as exc:  # network, HTTP, DNS — all mean the same thing here
            # The stale offset is NOT reused: "we had time once" is not "we have time now".
            self._offset = self._sampled_local = None
            raise NoTrustedTimeError(f"could not reach the time authority: {exc}") from exc
        self._offset = parse_http_date(header) - local
        self._sampled_local = local

    def _due(self, local: dt.datetime) -> bool:
        if self._offset is None or self._sampled_local is None:
            return True
        return (local - self._sampled_local).total_seconds() > self._refresh_interval_s

    def __call__(self) -> str:
        if self._due(self._local_now()):
            self._sample()
        assert self._offset is not None  # _sample either set it or raised
        return (self._local_now() + self._offset).isoformat()


class FixedOffsetClock:
    """A REAL clock with a known offset — for tests and for a runner whose offset was
    established elsewhere. Not a stub: it runs the same arithmetic as
    :class:`GitHubDateClock`, it simply does not fetch."""

    def __init__(self, *, offset_s: float,
                 local_now: Callable[[], dt.datetime] | None = None) -> None:
        self._offset = dt.timedelta(seconds=offset_s)
        self._local_now = local_now or (lambda: dt.datetime.now(dt.timezone.utc))

    def __call__(self) -> str:
        return (self._local_now() + self._offset).isoformat()


__all__ = [
    "RATE_LIMIT_URL",
    "AuthoritativeClock",
    "FixedOffsetClock",
    "GitHubDateClock",
    "NoTrustedTimeError",
    "parse_http_date",
]
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/unit/test_self_improvement_clock.py -q`
Expected: `7 passed`.

- [ ] **Step 5: Run the real-call test once, manually**

Run: `LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_self_improvement_clock_real.py -q`
Expected: `2 passed`. If it fails on drift, report the measured drift — do NOT widen the assertion; a drift over `max_clock_skew` against the real authority means the policy value is wrong.

- [ ] **Step 6: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/clock.py \
  tests/unit/test_self_improvement_clock.py tests/real_call/test_self_improvement_clock_real.py \
  -m "feat(025 slice-2): authoritative clock (FR-036) — GitHub server time, fail closed"
```

---

### Task 3: The transition table as data + `project_attempt`

**Files:**
- Create: `src/llmxive/self_improvement/lifecycle.py`
- Test: `tests/unit/test_self_improvement_lifecycle_model.py`

**Interfaces:**
- Consumes: `Event`, `payload_field`, `COORDINATOR_STREAM` (Slice 1A).
- Produces: `AttemptState`, `ProblemDisposition`, `Transition`, `TRANSITIONS`, `TERMINAL_STATES`, `COUNTED_TERMINALS`, `project_attempt`, `IllegalTransition`, `legal_events_from`.

- [ ] **Step 1: Write the failing model tests**

```python
# tests/unit/test_self_improvement_lifecycle_model.py
"""The Attempt machine as a MODEL, driven exhaustively rather than by hand-picked paths.

Exhaustive enumeration + seeded random walks rather than `hypothesis`: no new dependency,
fully deterministic, and the seed is printed on failure so any counterexample replays."""
from __future__ import annotations

import random

import pytest

from llmxive.self_improvement.lifecycle import (
    COUNTED_TERMINALS,
    TERMINAL_STATES,
    TRANSITIONS,
    AttemptState,
    IllegalTransition,
    legal_events_from,
    project_attempt,
)

from tests.helpers.lane_lifecycle import attempt_event, drive  # Task 3 Step 3 helper


def test_every_transition_names_states_that_exist():
    for t in TRANSITIONS:
        assert t.to_state in AttemptState, t
        for s in t.from_states:
            assert s in AttemptState, t


def test_every_non_terminal_state_can_be_left():
    # A state with no outgoing transition is a silent dead end — an Attempt that reaches it
    # is stuck forever with no terminal, which the lane cannot represent.
    for state in AttemptState:
        if state in TERMINAL_STATES:
            continue
        assert legal_events_from(state), f"{state} is a non-terminal dead end"


def test_every_terminal_state_is_truly_terminal():
    for state in TERMINAL_STATES:
        assert not legal_events_from(state), f"{state} is terminal but has outgoing edges"


def test_counted_terminals_are_a_strict_subset_of_terminals():
    assert COUNTED_TERMINALS < TERMINAL_STATES
    # The uncounted operational terminals, named explicitly (spec table): counting one of
    # these would let infrastructure burn a Problem's quality budget (FR-001).
    for uncounted in (AttemptState.REJECTED, AttemptState.UNSUPPORTED_SCOPE,
                      AttemptState.SUPERSEDED, AttemptState.REVIEW_ABORTED,
                      AttemptState.ATTEMPT_ABANDONED):
        assert uncounted not in COUNTED_TERMINALS


def test_idempotency_keys_are_unique_per_transition():
    keys = [t.key_suffix for t in TRANSITIONS]
    assert len(keys) == len(set(keys)), "two transitions share an idempotency key"


@pytest.mark.parametrize("state", list(AttemptState))
def test_every_illegal_event_from_every_state_is_refused(state):
    # The whole (state x event) grid, not a sampled corner of it.
    legal = legal_events_from(state)
    for t in TRANSITIONS:
        if t.event in legal:
            continue
        with pytest.raises(IllegalTransition):
            project_attempt(drive(state) + [attempt_event(t.event)])


def test_a_second_terminal_is_refused_whichever_two_they_are():
    for first in sorted(TERMINAL_STATES, key=lambda s: s.value):
        history = drive(first)
        for t in TRANSITIONS:
            if t.to_state not in TERMINAL_STATES:
                continue
            with pytest.raises(IllegalTransition):
                project_attempt(history + [attempt_event(t.event)])


def test_random_walks_never_violate_the_invariants():
    rng = random.Random(20260731)
    for trial in range(500):
        state, history = AttemptState.PROPOSED, [attempt_event("Proposed")]
        for _ in range(12):
            options = legal_events_from(state)
            if not options:
                break
            event = rng.choice(sorted(options))
            history.append(attempt_event(event))
            state = project_attempt(history).state
        result = project_attempt(history)
        assert result.state is state, f"trial {trial}: fold disagreed with the walk"
        assert result.is_terminal == (state in TERMINAL_STATES)
        assert result.counts_against_quality == (state in COUNTED_TERMINALS)


def test_the_code_table_matches_the_spec_table():
    """Spec/code drift is a FAILING TEST, not a review finding."""
    import re
    from pathlib import Path

    text = Path("specs/025-self-improvement-lane/spec.md").read_text()
    rows = [ln for ln in text.split("\n")
            if ln.startswith("|") and ln.count("|") == 7 and "Idempotency key" not in ln]
    spec_events = {
        m.group(1) for ln in rows
        for m in [re.match(r"\|[^|]*\|([A-Za-z]+)", ln)] if m
    }
    code_events = {t.event for t in TRANSITIONS}
    missing = spec_events - code_events - {"Event"}
    assert not missing, f"spec transitions with no TRANSITIONS row: {sorted(missing)}"
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/unit/test_self_improvement_lifecycle_model.py -q`
Expected: collection error, `ModuleNotFoundError: llmxive.self_improvement.lifecycle`.

- [ ] **Step 3: Write the test helper**

`tests/` is a package (`tests/__init__.py`) and cross-test imports in this repo use the
`from tests.<pkg>.<mod> import ...` form, so `tests/helpers/` needs an `__init__.py` — an
empty file, created in this step. (`tests/fixtures/` is DATA and deliberately not a
package; do not put the helper there.)

```bash
touch tests/helpers/__init__.py
```

```python
# tests/helpers/lane_lifecycle.py
"""Shared drivers for the lifecycle model tests: build a synthetic history that REACHES a
given state, using only the declared table — so the helper cannot encode a path the machine
does not actually allow."""
from __future__ import annotations

from collections import deque

from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lifecycle import (
    TRANSITIONS,
    AttemptState,
    legal_events_from,
)

TS = "2026-07-31T12:00:00+00:00"


def attempt_event(event_type: str, *, attempt_id: str = "A1", problem_id: str = "P1",
                  payload: dict | None = None) -> Event:
    body = {"problem_id": problem_id, "attempt_id": attempt_id, **(payload or {})}
    return Event(
        event_id=derive_event_id(problem_id, f"{event_type}\x00{attempt_id}"),
        event_type=event_type, problem_id=problem_id, actor="test",
        payload=body, timestamp=TS, attempt_id=attempt_id,
    )


def _shortest_paths() -> dict[AttemptState, list[str]]:
    """BFS over the declared table. Derived, never hand-written: a hand-written path would
    silently stop testing a transition the table later changes."""
    start = AttemptState.PROPOSED
    paths: dict[AttemptState, list[str]] = {start: ["Proposed"]}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for event in sorted(legal_events_from(state)):
            nxt = next(t.to_state for t in TRANSITIONS
                       if t.event == event and state in t.from_states)
            if nxt not in paths:
                paths[nxt] = paths[state] + [event]
                queue.append(nxt)
    return paths


_PATHS = _shortest_paths()


def drive(state: AttemptState) -> list[Event]:
    """A minimal legal history ending in ``state``."""
    if state not in _PATHS:
        raise AssertionError(f"{state} is unreachable from PROPOSED — the table is wrong")
    return [attempt_event(e) for e in _PATHS[state]]
```

- [ ] **Step 4: Implement the table + fold**

```python
# src/llmxive/self_improvement/lifecycle.py
"""The Attempt state machine (spec 025 Transition Table), declared ONCE as data.

The table is the contract. A function that re-encoded a row in an ``if`` chain would be a
second source of truth that can disagree with this one (Constitution I), so nothing below
branches on a specific state name — every decision is a lookup.

Attempt states are NOT Problem dispositions: ``cooldown`` is keyed by ``problem_id`` and
lives in :mod:`cooldown`. Collapsing them is how a Problem's rest gets misreported as an
Attempt's outcome."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from llmxive.self_improvement.events import Event, payload_field


class IllegalTransition(ValueError):
    """The history is not something the machine could have produced. Always raised, never
    downgraded to a skip: a projection that tolerates an impossible history is a projection
    that cannot be used for recovery."""


class AttemptState(enum.StrEnum):
    PROPOSED = "proposed"
    PROPOSAL_VERIFIED = "proposal_verified"
    CLAIMED = "claimed"
    IMPLEMENTING = "implementing"
    PROMOTING = "promoting"
    PROMOTION_REQUESTED = "promotion_requested"
    MONITORING = "monitoring"
    REVERT_REQUESTED = "revert_requested"
    # --- terminals ---
    REJECTED = "rejected"
    REVIEW_ABORTED = "review_aborted"
    ATTEMPT_ABANDONED = "attempt_abandoned"
    IMPL_FAILED = "impl_failed"
    PUBLISH_FAILED = "publish_failed"
    TEST_FAILED = "test_failed"
    EVAL_FAILED = "eval_failed"
    UNSUPPORTED_SCOPE = "unsupported_scope"
    SUPERSEDED = "superseded"
    PROMOTION_ABORTED = "promotion_aborted"
    REVERTED = "reverted"
    RETAINED = "retained"
    CIRCUIT_BROKEN = "circuit_broken"


class ProblemDisposition(enum.StrEnum):
    """Per-PROBLEM, deliberately a separate namespace from :class:`AttemptState`."""

    ACTIVE = "active"
    COOLDOWN = "cooldown"


@dataclass(frozen=True)
class Transition:
    event: str
    from_states: frozenset[AttemptState]
    to_state: AttemptState
    key_suffix: str          # the idempotency key's second element, per the spec table
    releases_claim: bool     # the spec table's † marker


def _t(event: str, froms: tuple[AttemptState, ...], to: AttemptState, key: str,
       *, releases: bool = False) -> Transition:
    return Transition(event, frozenset(froms), to, key, releases)


S = AttemptState

TRANSITIONS: tuple[Transition, ...] = (
    _t("Proposed", (), S.PROPOSED, "proposed"),
    _t("ProposalVerified", (S.PROPOSED,), S.PROPOSAL_VERIFIED, "verified"),
    _t("Rejected", (S.PROPOSED, S.PROPOSAL_VERIFIED), S.REJECTED, "reject"),
    _t("ReviewAborted", (S.PROPOSED, S.IMPLEMENTING), S.REVIEW_ABORTED, "reviewabort",
       releases=True),
    _t("ClaimGranted", (S.PROPOSAL_VERIFIED,), S.CLAIMED, "claim"),
    _t("Implementing", (S.CLAIMED,), S.IMPLEMENTING, "impl"),
    _t("ImplementationFailed", (S.CLAIMED, S.IMPLEMENTING), S.IMPL_FAILED, "implfail",
       releases=True),
    _t("PublishFailed", (S.IMPLEMENTING,), S.PUBLISH_FAILED, "pubfail", releases=True),
    _t("TestingFailed", (S.IMPLEMENTING,), S.TEST_FAILED, "testfail", releases=True),
    _t("EvaluationFailed", (S.IMPLEMENTING,), S.EVAL_FAILED, "evalfail", releases=True),
    _t("ScopeUnsupported", (S.PROPOSAL_VERIFIED, S.CLAIMED, S.IMPLEMENTING),
       S.UNSUPPORTED_SCOPE, "unsupported", releases=True),
    _t("FreshnessStale", (S.CLAIMED, S.IMPLEMENTING), S.SUPERSEDED, "stale", releases=True),
    _t("EvaluationPassed", (S.IMPLEMENTING,), S.PROMOTING, "eval"),
    _t("PromotionRequested", (S.PROMOTING,), S.PROMOTION_REQUESTED, "promo-req"),
    _t("PromotionObserved", (S.PROMOTION_REQUESTED,), S.MONITORING, "promo-obs"),
    _t("PromotionAborted", (S.PROMOTION_REQUESTED,), S.PROMOTION_ABORTED, "promo-abort",
       releases=True),
    _t("RevertRequested", (S.MONITORING,), S.REVERT_REQUESTED, "revert-req"),
    _t("RevertObserved", (S.REVERT_REQUESTED,), S.REVERTED, "revert-obs"),
    _t("RevertAborted", (S.REVERT_REQUESTED,), S.MONITORING, "revert-abort"),
    _t("Retained", (S.MONITORING,), S.RETAINED, "retain"),
    _t("BreakerTripped",
       (S.PROPOSED, S.PROPOSAL_VERIFIED, S.CLAIMED, S.IMPLEMENTING, S.PROMOTING,
        S.PROMOTION_REQUESTED), S.CIRCUIT_BROKEN, "breaker", releases=True),
    # FR-035: the one terminal written by a DIFFERENT run than the one that abandoned it.
    _t("ClaimExpired",
       (S.CLAIMED, S.IMPLEMENTING, S.PROMOTING, S.PROMOTION_REQUESTED),
       S.ATTEMPT_ABANDONED, "claimexpired", releases=True),
)

TERMINAL_STATES: frozenset[AttemptState] = frozenset({
    S.REJECTED, S.REVIEW_ABORTED, S.ATTEMPT_ABANDONED, S.IMPL_FAILED, S.PUBLISH_FAILED,
    S.TEST_FAILED, S.EVAL_FAILED, S.UNSUPPORTED_SCOPE, S.SUPERSEDED, S.PROMOTION_ABORTED,
    S.REVERTED, S.RETAINED, S.CIRCUIT_BROKEN,
})

#: Counted toward the per-Problem QUALITY cap (M=3 → 30-day cooldown). The operational
#: terminals are deliberately absent: counting one would let a provider outage or a crashed
#: runner consume a Problem's quality budget, which FR-001 forbids.
COUNTED_TERMINALS: frozenset[AttemptState] = frozenset({
    S.IMPL_FAILED, S.PUBLISH_FAILED, S.TEST_FAILED, S.EVAL_FAILED, S.REVERTED,
})

#: Uncounted terminals that feed the OPERATIONAL streak instead (FR-034).
OPERATIONAL_TERMINALS: frozenset[AttemptState] = frozenset({
    S.REVIEW_ABORTED, S.ATTEMPT_ABANDONED,
})

_BY_EVENT: dict[str, Transition] = {t.event: t for t in TRANSITIONS}
ATTEMPT_EVENT_TYPES: frozenset[str] = frozenset(_BY_EVENT)


def legal_events_from(state: AttemptState) -> frozenset[str]:
    return frozenset(t.event for t in TRANSITIONS if state in t.from_states)


@dataclass(frozen=True)
class AttemptProjection:
    attempt_id: str
    state: AttemptState
    revision: int
    claim_generation: int | None
    releases_claim: bool

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def counts_against_quality(self) -> bool:
        return self.state in COUNTED_TERMINALS

    @property
    def counts_against_operational(self) -> bool:
        return self.state in OPERATIONAL_TERMINALS


def project_attempt(events: list[Event]) -> AttemptProjection:
    """Fold one Attempt's events into its state, enforcing the table. Fails closed on any
    history the machine could not have produced — an unknown event, a transition with no
    row, or a second terminal."""
    if not events:
        raise IllegalTransition("an Attempt projection needs at least its Proposed event")
    state: AttemptState | None = None
    attempt_id = events[0].attempt_id
    generation: int | None = None
    for position, e in enumerate(events):
        if e.attempt_id != attempt_id:
            raise IllegalTransition(
                f"event {position} belongs to {e.attempt_id!r}, not {attempt_id!r}")
        transition = _BY_EVENT.get(e.event_type)
        if transition is None:
            raise IllegalTransition(f"unknown Attempt event {e.event_type!r} — fail closed")
        if state is None:
            if transition.from_states:
                raise IllegalTransition(
                    f"an Attempt cannot open with {e.event_type!r}")
        elif state in TERMINAL_STATES:
            raise IllegalTransition(
                f"{attempt_id!r} is already terminal at {state.value!r}; "
                f"{e.event_type!r} would be a SECOND terminal")
        elif state not in transition.from_states:
            raise IllegalTransition(
                f"illegal transition {e.event_type!r} from {state.value!r}")
        if e.event_type in ("ClaimGranted", "ClaimExpired"):
            generation = payload_field(e, "claim_generation")
        state = transition.to_state
    assert state is not None
    return AttemptProjection(
        attempt_id=attempt_id, state=state, revision=len(events),
        claim_generation=generation, releases_claim=_BY_EVENT[events[-1].event_type].releases_claim,
    )


__all__ = [
    "ATTEMPT_EVENT_TYPES",
    "COUNTED_TERMINALS",
    "OPERATIONAL_TERMINALS",
    "TERMINAL_STATES",
    "TRANSITIONS",
    "AttemptProjection",
    "AttemptState",
    "IllegalTransition",
    "ProblemDisposition",
    "Transition",
    "legal_events_from",
    "project_attempt",
]
```

- [ ] **Step 5: Run the model tests**

Run: `python -m pytest tests/unit/test_self_improvement_lifecycle_model.py -q`
Expected: all pass. If `test_every_non_terminal_state_can_be_left` fails, a state was added without an exit — fix the TABLE, never the test.

- [ ] **Step 6: Verify the model tests are load-bearing**

Temporarily delete the `elif state in TERMINAL_STATES:` branch in `project_attempt`, re-run, and confirm `test_a_second_terminal_is_refused_whichever_two_they_are` FAILS. Restore it and confirm `git diff` on `lifecycle.py` is empty. A model test that passes against a broken machine is decoration.

- [ ] **Step 7: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/lifecycle.py \
  tests/helpers/__init__.py tests/helpers/lane_lifecycle.py \
  tests/unit/test_self_improvement_lifecycle_model.py \
  -m "feat(025 slice-2): Attempt transition table as data + fail-closed projection"
```

---

### Task 4: Attempt event vocabulary + validators

**Files:**
- Modify: `src/llmxive/self_improvement/events.py`
- Test: `tests/unit/test_self_improvement_events.py` (extend)

**Interfaces:**
- Consumes: `KNOWN_EVENT_TYPES_V1`, `TYPE_VALIDATORS`, `_require`, `_exact_keys`, `_same_attempt`, `_positive_int` (Slice 1A Task 2).
- Produces: the new event types, validated at the write boundary.

- [ ] **Step 1: Write the failing tests**

Extend `tests/unit/test_self_improvement_events.py` with one test per new type asserting (a) a well-formed payload validates, (b) a missing required key raises, (c) an EXTRA key raises (`_exact_keys` house style — extras make the contract untestable), and (d) the envelope `attempt_id` must match the payload's.

**First, the coverage gap.** `KNOWN_EVENT_TYPES_V1` currently holds only four Attempt events (`ProblemDiscovered`, `Proposed`, `ProposalVerified`, `Rejected`). Every OTHER transition in `TRANSITIONS` — `ClaimGranted`, `Implementing`, `ImplementationFailed`, `PublishFailed`, `TestingFailed`, `EvaluationFailed`, `ScopeUnsupported`, `FreshnessStale`, `EvaluationPassed`, `PromotionRequested`, `PromotionObserved`, `PromotionAborted`, `RevertRequested`, `RevertObserved`, `RevertAborted`, `Retained`, `BreakerTripped`, `ReviewAborted`, `ClaimExpired` — must be added, or Task 5's CAS rejects them at the write boundary. Pin it so the two cannot drift:

```python
def test_every_declared_transition_has_a_writable_event_type():
    from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES
    missing = ATTEMPT_EVENT_TYPES - KNOWN_EVENT_TYPES_V1
    assert not missing, f"transitions the store would refuse to write: {sorted(missing)}"
```

**Second, the dual-stream names.** `ClaimGranted`/`ClaimExpired` (Attempt stream) and `ClaimAcquired`/`ClaimExpired` (coordinator stream) describe the same real-world moment from two sides, and `ClaimExpired` is literally the same name on both. That is intentional — a claim change is genuinely two facts on two refs — but it must be documented at the definition, or a reader will treat one as a duplicate of the other and delete it:

> `ClaimGranted`/`ClaimExpired` on a Problem stream are ATTEMPT transitions (they move the Attempt). `ClaimAcquired`/`ClaimReleased`/`ClaimExpired` on the coordinator stream are LANE mutations (they move the singleton). Neither is derivable from the other, because they live on different refs with independent revisions — which is the same reason the generation check is advisory (Global Constraints).

New types and their exact payload key sets:

| Event | Payload keys |
|-|-|
| `ReviewAborted` | `problem_id`, `attempt_id`, `stage`, `cause`, `unresolved_dispatches` |
| `ClaimHeartbeat` | `problem_id`, `attempt_id`, `claim_generation`, `tick` |
| `ClaimExpired` | `problem_id`, `attempt_id`, `claim_generation`, `reason` |
| `MonitorEnded` | `problem_id`, `attempt_id`, `outcome` |
| `SideEffectRequested` | `problem_id`, `attempt_id`, `claim_generation`, `effect`, `idempotency_key` |
| `SideEffectObserved` | `problem_id`, `attempt_id`, `claim_generation`, `effect`, `idempotency_key`, `disposition` |
| `Cooldown` | `problem_id`, `cause`, `epoch`, `cooldown_until` |

Constrained vocabularies, validated (a free-form string here is how a typo becomes a silent new category):
- `ReviewAborted.stage` ∈ `{"proposal", "patch"}`; `cause` ∈ the seven FR-034 causes: `{"model_unavailable", "chain_exhausted", "route_audit_fatal", "route_replay", "unresolved_dispatch", "budget_ceiling", "wall_clock"}`.
- `ClaimExpired.reason` ∈ `{"heartbeat_lapsed", "hold_time_exceeded"}`.
- `SideEffect*.effect` ∈ `{"publish", "merge", "revert"}`.
- `SideEffectObserved.disposition` ∈ `{"landed", "rejected", "contained", "ambiguous"}`.
- `Cooldown.cause` ∈ `{"quality", "operational"}`; `epoch` a non-negative int.
- `MonitorEnded.outcome` ∈ `{"retained", "reverted"}`.

Plus one test that pins the relationship a reviewer would otherwise read as duplication:

```python
def test_side_effect_intents_are_not_attempt_transitions():
    """`PromotionRequested` (a TRANSITION) and `SideEffectRequested{effect:"merge"}` (the
    saga's fencing record) are different layers, and the machine must not confuse them: the
    transition moves the Attempt, the intent is what blocks a reclaim until reconciled."""
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES
    assert "SideEffectRequested" not in ATTEMPT_EVENT_TYPES
    assert "SideEffectObserved" not in ATTEMPT_EVENT_TYPES
    assert "PromotionRequested" in ATTEMPT_EVENT_TYPES
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/unit/test_self_improvement_events.py -q`
Expected: failures naming the unknown event types.

- [ ] **Step 3: Implement**

Add each type to `KNOWN_EVENT_TYPES_V1` with a comment marking it a Slice-2 vocabulary extension (record SHAPE unchanged ⇒ `SCHEMA_VERSION` stays 1, per Slice 1A's F7 rule). Write one `_validate_*` per type following the existing house style — `_same_attempt(raw)`, `_exact_keys(payload, frozenset({...}), "<Type>")`, `_require(payload, key, str)`, and a membership check against a module-level frozenset for each constrained vocabulary. Register all of them in `TYPE_VALIDATORS`.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/unit/test_self_improvement_events.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/events.py \
  tests/unit/test_self_improvement_events.py \
  -m "feat(025 slice-2): Attempt lifecycle event vocabulary + write-boundary validators"
```

---

### Task 5: `cas_attempt_transition` — the terminal-slot CAS

**Files:**
- Modify: `src/llmxive/self_improvement/lifecycle.py`
- Test: `tests/integration/test_self_improvement_lifecycle_cas.py`

**Interfaces:**
- Consumes: `lane_log.append/read`, `LaneRevisionConflict`, `derive_event_id`.
- Produces: `cas_attempt_transition(repo, *, problem_id, attempt_id, event_type, payload, actor, clock, config=None) -> AttemptProjection`.

- [ ] **Step 1: Write the failing tests**

Real temp-git repos throughout. The cases:

1. A legal transition appends and advances the projection.
2. An illegal transition raises `LaneRevisionConflict` and appends NOTHING (assert the event count is unchanged — a rejected CAS never writes).
3. Re-invoking the same transition is idempotent: no second event, same projection.
4. **Two different terminals racing**: write `ReviewAborted`, then attempt `ImplementationFailed`; assert the second raises, the log holds exactly one terminal, and the projection still reports the FIRST.
5. The loser's own idempotent replay after losing still raises (it did not land; it must not appear to have).
6. A transition whose `from_states` no longer match because another writer advanced the Attempt raises rather than overwriting.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_lifecycle_cas.py -q`
Expected: `ImportError: cannot import name 'cas_attempt_transition'`.

- [ ] **Step 3: Implement**

```python
def cas_attempt_transition(repo: Path, *, problem_id: str, attempt_id: str,
                           event_type: str, payload: Mapping[str, Any], actor: str,
                           clock: Callable[[], str],
                           config: LaneLogConfig | None = None) -> AttemptProjection:
    """Append one Attempt transition under the table's rules, or raise
    :class:`LaneRevisionConflict`.

    The precondition is re-evaluated against the projection the CAS commits against — never
    a stale read — so a terminal that landed while this caller was deciding defeats it. That
    is the whole mechanism behind FR-035's "exactly one terminal": ref-level CAS ORDERS two
    concurrent terminals, it does not reject either, so the rejection has to happen here."""
    transition = _BY_EVENT.get(event_type)
    if transition is None:
        raise IllegalTransition(f"unknown Attempt event {event_type!r}")
    events = read(repo, problem_id, config=config)
    mine = [e for e in events if e.attempt_id == attempt_id]
    event = Event(
        event_id=derive_event_id(problem_id, f"{transition.key_suffix}\x00{attempt_id}"),
        event_type=event_type, problem_id=problem_id, actor=actor,
        payload={"problem_id": problem_id, "attempt_id": attempt_id, **payload},
        timestamp=clock(), attempt_id=attempt_id,
    )

    def _legal_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if any(e.event_id == event.event_id for e in evs):
            return (True, "")  # this exact transition already landed → idempotent
        history = [e for e in evs if e.attempt_id == attempt_id]
        if not history:
            return (not transition.from_states, "an Attempt cannot open with this event")
        try:
            current = project_attempt(history)
        except IllegalTransition as exc:      # a history we cannot trust → refuse to add to it
            return (False, f"unprojectable history: {exc}")
        if current.is_terminal:
            return (False, f"{attempt_id!r} already terminal at {current.state.value!r}")
        if current.state not in transition.from_states:
            return (False, f"illegal from {current.state.value!r}")
        return (True, "")

    append(repo, event, expected_revision=len(events), precondition=_legal_or_landed,
           config=config)
    return project_attempt(
        [e for e in read(repo, problem_id, config=config) if e.attempt_id == attempt_id])
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_lifecycle_cas.py -q`
Expected: all pass.

- [ ] **Step 5: Verify the terminal slot is load-bearing**

Temporarily remove the `if current.is_terminal:` branch, re-run, and confirm case 4 FAILS with two terminals in the log. Restore; confirm an empty `git diff`.

- [ ] **Step 6: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/lifecycle.py \
  tests/integration/test_self_improvement_lifecycle_cas.py \
  -m "feat(025 slice-2): terminal-slot CAS — exactly one terminal per Attempt (FR-035)"
```

---

### Task 6: Claim generations + claim-bound terms

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/integration/test_self_improvement_coordinator_cas.py` (extend)

**Interfaces:**
- Produces: `LaneCoordinator.claim_generation`, `ClaimOutcome.generation`, `ClaimTerms`, `cas_claim(..., terms=)`.

- [ ] **Step 1: Write the failing tests**

1. A fresh lane has `claim_generation == 0`; the first `ClaimGranted` makes it 1.
2. `ClaimOutcome.generation` reports it (the field rev 22 deliberately left off until now).
3. Generation is monotonic across claim/release cycles and NEVER resets — three cycles yield 1, 2, 3.
4. `ClaimTerms` (expiry, hold time, skew, policy version) round-trips through the `ClaimGranted` payload and is what a later reader sees, **not** the current module constants: write a claim, then re-read it with different module constants patched in via the injected policy object, and assert the CLAIM's terms win. This is the row Task 1 Step 3 added — a policy edit mid-claim must not retroactively expire a live run.
5. A `ClaimGranted` whose payload omits any term is refused at the write boundary.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: `AttributeError: 'LaneCoordinator' object has no attribute 'claim_generation'`.

- [ ] **Step 3: Implement**

- Add `claim_generation: int` to `LaneCoordinator` and to `EMPTY_COORDINATOR` (0).
- In `project_coordinator`, increment it on **both** `ClaimAcquired` and `ClaimExpired` — never reset (it is the fencing token; a reset makes two different claims indistinguishable).
- Add `generation: int` to `ClaimOutcome`, populated by `_outcome`, and delete the docstring paragraph that says the field is deferred.
- Add:

```python
@dataclass(frozen=True)
class ClaimTerms:
    """The policy a claim was granted UNDER, recorded on the claim itself.

    Read by any later reclaimer from the ``ClaimGranted`` payload rather than from live
    policy, so editing the Policy Contract while a run holds the lane cannot retroactively
    expire it. Same discipline as ``bind_attempt_config``."""

    claim_expiry_s: int
    max_claim_hold_time_s: int
    max_clock_skew_s: int
    policy_version: int
```

- `cas_claim` gains a required `terms: ClaimTerms` keyword and writes its four fields into the `ClaimAcquired` payload.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: all pass, including the seven pre-existing cases.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/coordinator.py \
  tests/integration/test_self_improvement_coordinator_cas.py \
  -m "feat(025 slice-2): claim generations + claim-bound policy terms (FR-035)"
```

---

### Task 7: Heartbeats, expiry, and reclaim

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Create: `src/llmxive/self_improvement/policy.py`
- Test: `tests/integration/test_self_improvement_claim_liveness.py`

**Interfaces:**
- Produces: `cas_heartbeat`, `cas_reclaim`, `cas_release_terminal`, `HEARTBEAT_INTERVAL_S`, `CLAIM_EXPIRY_S`, `MAX_CLOCK_SKEW_S`, `MAX_CLAIM_HOLD_TIME_S`, `reclaimable`.

- [ ] **Step 1: Write `policy.py` first — derived, not literal**

```python
# src/llmxive/self_improvement/policy.py
"""Policy Contract v1 constants that the lifecycle needs, DERIVED where the spec derives
them (Constitution I — the LLM-call-ceiling row is the precedent). Writing 220 as a literal
would let a phase budget change without the total following it."""

MINUTE = 60

HEARTBEAT_INTERVAL_S = 5 * MINUTE
CLAIM_EXPIRY_S = 3 * HEARTBEAT_INTERVAL_S          # tolerate two missed beats
MAX_CLOCK_SKEW_S = 5 * MINUTE

#: Post-claim phase budgets (Policy Contract "Wall-clock budget / Attempt").
IMPLEMENTATION_S = 45 * MINUTE
IMPL_REGEN_RETRIES = 1                              # hard max 1 in v1
PUBLISH_S = 10 * MINUTE
CANDIDATE_TESTING_S = 20 * MINUTE
PATCH_REVIEW_S = 30 * MINUTE
EVALUATION_S = 30 * MINUTE
PROMOTION_S = 15 * MINUTE
INTENT_RECONCILIATION_S = 10 * MINUTE
CLAIM_OVERHEAD_S = 15 * MINUTE                      # CAS retries + git/GitHub round-trips

#: THE authoritative post-claim budget (FR-035). The claim is granted at
#: proposal_verified → claimed, so the proposal review is excluded.
MAX_CLAIM_HOLD_TIME_S = (
    IMPLEMENTATION_S * (1 + IMPL_REGEN_RETRIES)
    + PUBLISH_S + CANDIDATE_TESTING_S + PATCH_REVIEW_S + EVALUATION_S
    + PROMOTION_S + INTENT_RECONCILIATION_S + CLAIM_OVERHEAD_S
)

QUALITY_FAILURE_CAP = 3
QUALITY_COOLDOWN_S = 30 * 24 * 3600
OPERATIONAL_STREAK_CAP = 5
OPERATIONAL_ELAPSED_FLOOR_S = 24 * 3600
OPERATIONAL_COOLDOWN_S = 7 * 24 * 3600
```

Its test asserts the derivation matches the spec's stated total exactly:

```python
def test_the_hold_time_matches_the_spec_total():
    from llmxive.self_improvement import policy
    assert policy.MAX_CLAIM_HOLD_TIME_S == 220 * 60      # 3 h 40 min, spec rev 22
    assert policy.CLAIM_EXPIRY_S == 15 * 60
```

- [ ] **Step 2: Write the failing liveness tests**

Time is injected via `FixedOffsetClock` with a controllable local clock, so these are deterministic and exercise the REAL arithmetic:

1. A beat inside the interval renews: after `claim_expiry`+skew of ELAPSED time but with beats every 5 min, `reclaimable(...)` is False.
2. No beat for `claim_expiry + max_clock_skew` ⇒ reclaimable. At exactly `claim_expiry` alone ⇒ NOT reclaimable (the padding is not optional, and it pads toward not-evicting).
3. Past `max_claim_hold_time` ⇒ reclaimable **even while beating**. This is the pair of assertions rev 22 corrected: heartbeating protects a slow run from the expiry bound, not from the hold-time cap.
4. `cas_reclaim` writes `ClaimExpired` + releases + increments the generation, and terminates the Attempt at `attempt_abandoned`.
5. The reclaim race: the original run's own terminal lands first ⇒ the reclaimer's terminal CAS loses, and it appends NO coordinator mutation either. Assert the log holds exactly one terminal and the lane is still occupied.
6. Following case 5, `cas_release_terminal` (Task 1 Step 2's new row) frees the lane without writing a terminal — assert `active_problem_id is None`, exactly one terminal still, and the generation incremented.
7. `cas_reclaim` on an Attempt with an unreconciled intent is REFUSED (wired in Task 8).

- [ ] **Step 3: Implement**

`reclaimable(coordinator_events, *, attempt_events, now, terms)` returns `(bool, reason)` using the CLAIM's terms:

```python
def reclaimable(*, claimed_at: str, last_beat: str | None, now: str,
                terms: ClaimTerms) -> tuple[bool, str]:
    """Two independent bounds; either one trips. Padding always favours NOT evicting a live
    holder, because that is the worse error (FR-036)."""
    beat = _parse(last_beat or claimed_at)
    since_beat = (_parse(now) - beat).total_seconds()
    held = (_parse(now) - _parse(claimed_at)).total_seconds()
    if since_beat >= terms.claim_expiry_s + terms.max_clock_skew_s:
        return (True, "heartbeat_lapsed")
    if held >= terms.max_claim_hold_time_s + terms.max_clock_skew_s:
        return (True, "hold_time_exceeded")
    return (False, "")
```

`cas_heartbeat` appends `ClaimHeartbeat{claim_generation, tick}` conditioned on the caller still holding the claim AT the stamped generation. `cas_reclaim` performs the Attempt terminal FIRST (so the terminal-slot CAS decides the race), then the coordinator release — and on losing the terminal CAS it makes no coordinator mutation at all. Document that ordering and why:

> The Attempt terminal is written BEFORE the coordinator release because the terminal slot is the only single-stream arbiter available; releasing first would free the lane on the strength of a decision that has not yet been made.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_claim_liveness.py tests/unit/test_self_improvement_policy.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/coordinator.py \
  src/llmxive/self_improvement/policy.py \
  tests/unit/test_self_improvement_policy.py \
  tests/integration/test_self_improvement_claim_liveness.py \
  -m "feat(025 slice-2): renewable heartbeats, skew-padded expiry, reclaim (FR-035/036)"
```

---

### Task 8: Side-effect intents and the four dispositions

**Files:**
- Create: `src/llmxive/self_improvement/intents.py`
- Modify: `src/llmxive/self_improvement/coordinator.py` (reclaim precondition)
- Test: `tests/integration/test_self_improvement_intents.py`

**Interfaces:**
- Produces: `IntentDisposition`, `IntentRecord`, `Reconciler`, `record_intent`, `observe_intent`, `unreconciled_intents`, `LaneQuarantine`, `EFFECT_DISPOSITION_POLICY`.

- [ ] **Step 1: Write the failing tests**

1. `record_intent` writes `SideEffectRequested` stamped with the current generation.
2. `unreconciled_intents` finds it; after `observe_intent(..., landed)` it is empty.
3. Each of the four dispositions round-trips and is refused if not in the vocabulary.
4. **A `publish` intent may be closed as `contained`** — and the record says `contained`, NOT `rejected`. Assert the disposition literally, because collapsing these two is the rev-22 error.
5. **A `merge` intent may NOT be closed as `contained` or `rejected`** — `observe_intent` raises `ValueError` naming the missing precondition. The only legal negative outcome for a merge is `ambiguous`.
6. An `ambiguous` observation raises `LaneQuarantine` and BLOCKS reclaim: `cas_reclaim` refuses while it stands.
7. A `contained` observation does NOT block reclaim.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_intents.py -q`
Expected: `ModuleNotFoundError: llmxive.self_improvement.intents`.

- [ ] **Step 3: Implement**

```python
class IntentDisposition(enum.StrEnum):
    """How an outstanding side-effect intent resolved (spec rev 22).

    FOUR, not two: rev 21 had only "decidable vs ambiguous" and mis-sorted both of its own
    mechanisms into the decidable half."""

    LANDED = "landed"        # observed present — always conclusive, needs no precondition
    REJECTED = "rejected"    # an external precondition now makes landing IMPOSSIBLE
    CONTAINED = "contained"  # may still land, but only where it is HARMLESS
    AMBIGUOUS = "ambiguous"  # none of the above → quarantine, never a guess


#: What each effect may legally resolve to. A negative outcome is only expressible where the
#: lane can actually justify it:
#:   publish → CONTAINED, because a generation-scoped branch makes a late push harmless.
#:             NOT `rejected`: the push can still arrive. Containment is not decidability.
#:   merge/revert → AMBIGUOUS, because expected-`head_sha` constrains which COMMIT merges,
#:             never which ACTOR, so nothing prevents a superseded worker's merge. Promoting
#:             either of these to REJECTED requires a real-call-tested precondition that is
#:             evaluated by GitHub at effect time, flippable by the RECLAIMER, and terminal
#:             on read-back (spec rev 22). Until that test exists, quarantine stands.
EFFECT_DISPOSITION_POLICY: dict[str, frozenset[IntentDisposition]] = {
    "publish": frozenset({IntentDisposition.LANDED, IntentDisposition.CONTAINED}),
    "merge": frozenset({IntentDisposition.LANDED, IntentDisposition.AMBIGUOUS}),
    "revert": frozenset({IntentDisposition.LANDED, IntentDisposition.AMBIGUOUS}),
}
```

`observe_intent` validates the disposition against `EFFECT_DISPOSITION_POLICY` and raises `ValueError` with the reason when a caller asks for one the effect cannot support. `AMBIGUOUS` additionally raises `LaneQuarantine` after appending the record — the record is durable so the quarantine is visible and repairable; the raise stops the run. `unreconciled_intents` returns intents with no `SideEffectObserved` **plus** those observed `AMBIGUOUS`, and `cas_reclaim`'s precondition consumes it.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_intents.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/intents.py \
  src/llmxive/self_improvement/coordinator.py \
  tests/integration/test_self_improvement_intents.py \
  -m "feat(025 slice-2): side-effect intents + the four dispositions (FR-035 rev 22)"
```

---

### Task 9: The two counters and cooldown epochs

**Files:**
- Create: `src/llmxive/self_improvement/cooldown.py`
- Test: `tests/integration/test_self_improvement_cooldown.py`

**Interfaces:**
- Produces: `CooldownCause`, `CooldownState`, `problem_cooldown`, `cas_cooldown`.

- [ ] **Step 1: Write the failing tests**

1. Three counted terminals ⇒ quality cooldown, 30 days, `cause="quality"`, `epoch=0`.
2. Two counted terminals ⇒ no cooldown.
3. Five consecutive operational terminals spanning **exactly 24 h** ⇒ operational cooldown (`≥` is inclusive). Spanning 23 h 50 m ⇒ NO cooldown, and a sixth abort past the floor then trips it.
4. Five operational terminals crammed into 2 h ⇒ **no** cooldown. This is the case count-only logic got wrong.
5. **The counters never cross-contaminate**: five operational terminals leave the quality counter at 0, and three counted failures leave the operational streak at 0.
6. A substantive determination (`ProposalVerified` / `Rejected` / any `*_failed`) RESETS the operational streak.
7. Cooldown expiry also resets the streak, and a second quality cooldown gets `epoch=1` — assert the two events have DIFFERENT ids (the rev-18 bug was one cooldown per Problem for all time).

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_cooldown.py -q`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`problem_cooldown(events, *, now)` folds all Attempts for the Problem via `project_attempt`, using `COUNTED_TERMINALS` and `OPERATIONAL_TERMINALS` from `lifecycle.py` — never a re-listed set. The operational rule requires BOTH `streak >= OPERATIONAL_STREAK_CAP` AND `now - streak_started_at >= OPERATIONAL_ELAPSED_FLOOR_S + MAX_CLOCK_SKEW_S` (padded toward not-cooling-down). `cas_cooldown` uses idempotency key `(problem_id, "cooldown", cause, epoch)`.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_cooldown.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/cooldown.py \
  tests/integration/test_self_improvement_cooldown.py \
  -m "feat(025 slice-2): independent quality/operational counters + cooldown epochs (FR-034)"
```

---

### Task 10: Monitoring removal + the merge timestamp

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/integration/test_self_improvement_coordinator_cas.py` (extend)

**Interfaces:**
- Produces: `MonitorEnded` folding; `last_autonomous_merge_at` set at `PromotionObserved`.

- [ ] **Step 1: Write the failing tests**

1. `MonitorStarted` then `MonitorEnded` removes the Attempt from `monitored_attempts`; an unrelated monitored Attempt is untouched.
2. `MonitorEnded` for an Attempt that was never monitored RAISES (fail closed — it means the projection and the caller disagree about what is being monitored).
3. `PromotionObserved` sets `last_autonomous_merge_at` to the event's authority-derived timestamp.
4. The `PromotionObserved` CAS does BOTH the slot clear and the monitoring add in ONE append (the spec's "one coordinator CAS") — assert a single event and both effects.
5. `last_autonomous_merge_at` advances monotonically across two promotions and is never moved backwards by an out-of-order replay (`seq` decides, not the timestamp).

- [ ] **Step 2: Run, implement, run**

Expected after implementation: all pass, plus the pre-existing coordinator cases.

- [ ] **Step 3: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/coordinator.py \
  tests/integration/test_self_improvement_coordinator_cas.py \
  -m "feat(025 slice-2): monitoring removal + autonomous-merge timestamp"
```

---

### Task 11: The adversarial suite

The four scenarios the rev-22 review named. Each has a definite expected outcome now, which it did not before rev 22.

**Files:**
- Create: `tests/integration/test_self_improvement_adversarial.py`

**Interfaces:** consumes everything from Tasks 2–10.

- [ ] **Step 1: Write the four tests**

```python
"""Adversarial lifecycle scenarios (spec 025 rev 22 review, item 6).

Each pins a claim the spec makes about a DELAYED or HOSTILE actor. They are written as
whole-scenario tests rather than unit tests because every one of them is about the
interaction between two mechanisms — which is exactly where rev 21's errors lived."""


def test_a_stale_push_is_contained_not_rejected(repo, clock):
    """Generation 1 records a publish intent, is reclaimed, and its push lands LATE.

    The push still arrives — containment is not decidability — but it arrives in a dead
    namespace the live generation never touches, so reclaim is safe on HARMLESSNESS."""
    # g1 claims, records a publish intent, then goes silent past expiry.
    # A reclaimer observes the intent: publish may resolve CONTAINED.
    # Assertions:
    #   - the observed disposition is CONTAINED, never REJECTED
    #   - the branch name for g1 ends in "/g1" and for g2 in "/g2" (disjoint namespaces)
    #   - reclaim SUCCEEDS once the intent is closed as contained
    #   - a late push recreating the g1 ref does NOT affect the g2 projection
    #   - GC of the dead ref is idempotent: running it twice, and after a late recreate,
    #     never raises and never reports the absence as evidence of anything


def test_a_stale_merge_quarantines_and_refuses_to_guess(repo, clock):
    """The rev-22 critical finding, as an executable assertion.

    expected-head_sha constrains which COMMIT merges, not which ACTOR, so nothing stops a
    superseded worker's merge. The lane must record uncertainty, not a wrong answer."""
    # g1 reaches promotion_requested and records a merge intent, then goes silent.
    # Assertions:
    #   - observe_intent(..., CONTAINED) raises ValueError (merge cannot be contained)
    #   - observe_intent(..., REJECTED) raises ValueError (no enforceable precondition)
    #   - observe_intent(..., AMBIGUOUS) raises LaneQuarantine AND leaves a durable record
    #   - cas_reclaim is REFUSED while the ambiguous intent stands
    #   - NO terminal was written: the Attempt is still promotion_requested, honestly
    #     unresolved, which is the truth


def test_a_fast_clock_cannot_poison_the_ref_or_wedge_the_lane(repo):
    """Rev 21's validation let one fast-skewed runner reject every correct runner forever."""
    # A runner whose authority offset is 30 min fast attempts an append.
    # Assertions:
    #   - the append is REJECTED (beyond max_clock_skew from the authority)
    #   - a correctly-timed runner appends successfully IMMEDIATELY afterwards — the ref
    #     was not poisoned, which is the regression this test exists for
    #   - repeated rejection at the SAME ref position escalates to quarantine rather than
    #     blocking healthy writers indefinitely
    #   - a runner with NO trusted time performs no lane work at all: it raises
    #     NoTrustedTimeError before appending, and the event count is unchanged


def test_promotion_time_expiry_abandons_only_when_nothing_is_in_flight(repo, clock):
    """The claim spans promoting/promotion_requested (rev 21), so hold-time exhaustion must
    be reachable there — but what it DOES depends on whether a merge is outstanding."""
    # Case A: past max_claim_hold_time at `promoting`, NO intent outstanding.
    #   - reclaim SUCCEEDS -> attempt_abandoned
    #   - attempt_abandoned is UNCOUNTED against quality and DOES feed the operational streak
    # Case B: past max_claim_hold_time at `promotion_requested` WITH a merge intent.
    #   - reclaim is REFUSED, quarantine is raised, no terminal is written
    #   - i.e. the hold-time cap does not override the unreconciled-intent block
```

Fill in each body against the real modules; the comments above are the required assertions, not placeholders to leave in.

- [ ] **Step 2: Run**

Run: `python -m pytest tests/integration/test_self_improvement_adversarial.py -q`
Expected: `4 passed`.

- [ ] **Step 3: Verify each is load-bearing**

For each of the four, break the mechanism it pins (allow `merge` → `CONTAINED` in `EFFECT_DISPOSITION_POLICY`; drop the skew check; drop the unreconciled-intent precondition; let hold-time bypass the intent block), confirm the matching test FAILS, then restore and confirm an empty `git diff`. Record the four observed failure messages in the notes — a scenario test that passes against a broken mechanism is the most expensive kind of decoration.

- [ ] **Step 4: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o tests/integration/test_self_improvement_adversarial.py \
  -m "test(025 slice-2): adversarial suite — stale push/merge, clock poisoning, promotion expiry"
```

---

### Task 12: Wire the proposal verdict + the default-off driver

Closes the 1B seam: a proposal review currently computes a verdict with nowhere to record it.

**Files:**
- Modify: `src/llmxive/convergence/self_improvement_specs.py`
- Create: `src/llmxive/self_improvement/driver.py`
- Modify: `src/llmxive/self_improvement/__init__.py`
- Test: `tests/integration/test_self_improvement_proposal_review.py` (extend)
- Test: `tests/unit/test_self_improvement_exports.py` (extend)

**Interfaces:**
- Produces: `lane_enabled()`, `run_lifecycle_tick(...)`.

- [ ] **Step 1: Write the failing tests**

1. A panel that ACCEPTS writes `ProposalVerified`; the projection reports `proposal_verified`.
2. A panel that does NOT converge writes `Rejected` — substantive, uncounted.
3. A `ChainExhausted` during the proposal review writes `ReviewAborted{stage:"proposal", cause:"chain_exhausted"}` — NOT `Rejected`. This is the FR-034 distinction the whole review-abort thread exists for: routing an infrastructure abort to `rejected` records a verdict no panel gave.
4. Every unresolved `dispatch_started` is resolved to `dispatch_unknown` BEFORE the terminal is decided (the transition table's reconciliation column).
5. `run_lifecycle_tick` with `LLMXIVE_SELF_IMPROVEMENT_ENABLED` unset is a NO-OP: assert the lane log is byte-identical afterwards (no event, not even a read-repair).
6. `ClaimOutcome`, `AttemptState`, `IntentDisposition`, `GitHubDateClock` and the rest of the Task-3–9 surface are importable from `llmxive.self_improvement` (extend `EXPECTED`).

- [ ] **Step 2: Run, implement, run**

`lane_enabled()` reads the env var with an explicit default of off. `run_lifecycle_tick` returns immediately when disabled — before constructing a clock, so a disabled lane needs no network either.

- [ ] **Step 3: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/driver.py \
  src/llmxive/self_improvement/__init__.py \
  src/llmxive/convergence/self_improvement_specs.py \
  tests/integration/test_self_improvement_proposal_review.py \
  tests/unit/test_self_improvement_exports.py \
  -m "feat(025 slice-2): record proposal verdicts + default-off lifecycle driver"
```

---

## Final verification

- [ ] **Full non-slow suite**

```bash
python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
```
Expected: green. Not just the lane subset — this slice touches `events.py` and `coordinator.py`, which other suites import.

- [ ] **Lint**

```bash
python -m ruff check src/llmxive/self_improvement tests/unit tests/integration tests/helpers
```
Expected: `All checks passed!`

- [ ] **No model-id literals introduced**

```bash
python -m pytest tests/unit/test_model_selection_enforcement.py -q
```
Expected: green (static check; the lane must express intent as profiles only).

- [ ] **Spec/code drift check**

```bash
python -m pytest tests/unit/test_self_improvement_lifecycle_model.py::test_the_code_table_matches_the_spec_table -q
```

- [ ] **Real-call clock check, run manually once**

```bash
LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_self_improvement_clock_real.py -q
```

- [ ] **Docs updated in the same commits as the code** (CLAUDE.md rule): `notes/2026-07-26-spec025-slice1-implementation.md` gains a Slice-2 section covering the two design problems this plan found while grounding (cross-stream generation checks are advisory; a crash between terminal and release wedged the lane) and the four load-bearing verifications from Task 11 Step 3.

- [ ] **Nothing swept**: `git status --short` still shows exactly the six untracked pipeline artifacts, unchanged.

- [ ] **Do NOT push.** Rebase onto `origin/main` at PR time.

## Open questions for the maintainer

1. **`GET /rate_limit` unauthenticated** is what the clock falls back to when the run has made no API call yet. In CI the lane will already hold a token, so the authenticated response's `Date` is free — but the unauthenticated path is subject to a 60/hr per-IP limit that a busy shared runner could exhaust. Should the clock REQUIRE a token (fail closed rather than fall back), given FR-036 already says no trusted time ⇒ no lane work?
2. **`MAX_CLAIM_HOLD_TIME_S` = 3 h 40 min** is a long wedge if a run dies at minute 1 without ever beating. The heartbeat bound (15 min) covers that case, so the hold time only bites a run that beats but never progresses. Confirm that is the intended trade.
3. **Task 1 amends the spec again (rev 23).** If you would rather review rev 23 before any Slice-2 code lands, Task 1 is separable — it touches only the spec and notes.
