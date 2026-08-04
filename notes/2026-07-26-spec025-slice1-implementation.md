# Spec 025 slice 1A/1B implementation — running notes

**Branch:** `025-self-improvement-lane`. **Nothing pushed** (rebase onto `origin/main`
at PR time only; local `main` lags and cron commits constantly).

## Where things stand

Plans (both maintainer-reviewed through **round 7**, all findings resolved):
- `docs/superpowers/plans/2026-07-24-025-slice1a-durable-substrate.md` — **14 tasks**
- `docs/superpowers/plans/2026-07-25-025-slice1b-proposal-convergence.md` — **10 tasks**
- Spec is at **rev 16** (`specs/025-self-improvement-lane/spec.md`).

### Implementation progress

| Task | State | Commit |
|-|-|-|
| 1A T1 — extract `git_event_log.py`, rewire `ledger_transport` | DONE | `7a179b49c8` (+ plan fix `a20e005857`) |
| 1A T2 — lane `Event` + validation + `TYPE_VALIDATORS` | DONE | `a270b6927e` |
| T1/T2 round-8 review: two fail-open gaps closed | DONE | `abdb8d1536` (+ plan `6e805708de`) |
| 1A T3 — `lane_log.py` on the shared core | DONE | `aba549ffa6` (+ plan/notes `c1040ab7ae`) |
| 1A T4 — `LaneCoordinator` projection + coordinator payload schemas | DONE | `0ec22fc977` |
| 1A T5 — ownership-checked coordinator CAS | DONE | `173285d0c1` |
| 1A T6 — `AttemptCreditLedger` reservation projection | DONE | `bae0284ae1` |
| 1A T7–T9 — reserve / release / mark_retained / reconcile | DONE | `a5862186b7` |
| 1A T10–T12 — `EventStoreRouteAudit` + atomic `DispatchUnknown` | DONE | `37e5d8fe28` |
| 1A T13–T14 — `AttemptConfig` + `LaneCallLedger` | DONE | (this commit) |
| **Slice 1A COMPLETE** | — | — |
| 1B T1–T10 | not started | — |

## Money-path acceptance bar (T1)

The seven files in the plan's Global Constraints MUST pass with **no edits**:
baseline **135 passed** (42 + 93) before the extraction, **135 passed** after.
Re-run this whenever `git_event_log.py` or `ledger_transport.py` changes:

```
python -m pytest tests/integration/test_credit_ledger_transport.py \
  tests/integration/test_credit_reservations.py \
  tests/integration/test_model_selection_execute.py \
  tests/unit/test_ledger_config_from_env.py \
  tests/unit/test_model_selection_attempt_hooks.py \
  tests/unit/test_model_selection_inventory.py tests/unit/test_paid_credits.py -q
```

## Decisions made DURING implementation (plans updated to match)

1. **Ledger exceptions are SUBCLASSES + boundary translation, not aliases.**
   Rounds 2–6 specified `LedgerError = GitLogError` etc. so `except Ledger*` would
   still catch what the core raises. Correct as far as it goes — but aliases make
   `type(exc).__name__` report `GitLogContention`, and `execute` formats that name
   into its candidate notes, so `test_reserve_ledger_error_skips_not_aborts`
   (money path, uneditable) failed. Now: `Ledger*` subclass `GitLog*` (multiple
   inheritance, so `except GitLog*` also works) **plus** `_as_ledger_error()`
   wrapping every entry point that calls the core, so no base instance escapes.
   Plan corrected in `a20e005857`.

2. **`read_log` deliberately does NOT sync/verify.** Only `append_to_log` and an
   explicit `sync_and_verify`/`fetch_ledger` do — matching the credit ledger's
   existing split. A test that expects the pinned-anchor check on a bare read is
   wrong (I wrote one; fixed).

3. **Barrier seams need a PER-THREAD one-shot**, not a shared `Event` flag: with a
   shared flag one thread sets it and waits while the other skips the wait, and the
   first blocks until `BrokenBarrierError`. Use `{thread_ident} -> already_waited`
   under a lock so each worker waits exactly once, on its first attempt.

4. **Absence and failure must never collapse** (round-8). `[]`/`None` from the log
   means "no claim, no reservation, no spend" to every projection, so an operational
   failure reported that way is fail-OPEN. Discriminators, established empirically:
   `rev-parse --verify --quiet` exits **128** on operational failure but **1 for BOTH**
   a missing ref and an unreadable object → disambiguate with `show-ref` (exit 1 = ref
   truly absent). `ls-tree` exits 0 with EMPTY output for an absent path, 128 on
   failure — so it is both the checked listing in `read_log` and the existence test in
   `_read_event_blob` (`cat-file` cannot tell the cases apart; both exit 128).

5. **Presence is not a schema** (round-8). The envelope validates TYPES: non-empty
   strings, non-bool non-negative ints (`True == 1` and hashes as 1 — a boolean `seq`
   would order the projection as position 1), and tz-aware timestamps (FR-011 is an
   instant, not a date).

6. **`_finalize` stamps ALL FOUR revision anchors** (T3), not just the target scope's two.
   The plan's version left the other scope as the caller passed it, so a coordinator event
   built by the plan's own `_ev` helper (which pre-fills `expected_problem_revision`)
   failed validation with "lane-stream event must NOT set the problem revision scope". The
   store is the sole authority for these fields, so it writes the target scope and clears
   the other. Verified load-bearing by reverting it (1 test fails).

7. **`config=LaneLogConfig()` as a signature default is ruff B008.** Resolved the way the
   sibling `ledger_transport._log_ref` already does it: `config: LaneLogConfig | None =
   None`, resolved inside `_log_ref`. Plan signatures updated to match.

8. **Coordinator payload schemas live in `TYPE_VALIDATORS`, not the projection** (T4).
   `ClaimAcquired`/`ClaimReleased` carry the OWNERSHIP record the fold reads and
   `cas_release` compares, so a missing/empty id is refused at the write boundary rather
   than surfacing as a KeyError once durable. The payload `attempt_id` cross-checks the
   envelope's (so `cas_claim`/`cas_release` MUST set `Event.attempt_id`); the payload
   `problem_id` does NOT (envelope = `COORDINATOR_STREAM`, payload = the CLAIMED Problem).

9. **Delayed duplicate release = idempotent no-op** (T5) — MAINTAINER-DECIDED 2026-07-26.
   The plan contradicted itself: its precondition (`landed OR owns`) admits the case while
   the next sentence and its test expected `LaneRevisionConflict`. Both are safe (neither
   clears the newer claim); the no-op wins because the release IS already durable, so
   raising would manufacture a failure for a legitimate retry. A genuine NON-owner (record
   never landed, someone else active) still conflicts. Idempotency keys are
   `(op, problem_id, attempt_id)`, which is sound only because Attempt ids are single-use
   ("a crashed Attempt is a failed Attempt") — do not reuse an attempt_id after a release.

## Known-failing, NOT caused by this work

`tests/unit/test_dataset_sources.py::test_openml_*` (2) fail in this sandbox: they are
real-network calls to openml.org. Verified independent by stashing all lane work and
re-running — same two failures. Do not "fix" by weakening; they need network.

## Standing constraints (do not drift)

- Commit each task with `PRE_COMMIT_ALLOW_NO_CONFIG=1`, trailer
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved.
- **Never weaken a test** — fix the code so existing tests pass.
- Behavior-preserving when the new hooks/params are absent; the full non-slow suite
  must stay green.
- No model-id literals outside the canonical `model_selection` layer
  (`enforcement.py` enforces it statically).
- Real tests, no mocks. Protocol test doubles implementing real logic are fine;
  `unittest.mock` is not the primary path.

10. **Disable the guard, re-run the test** — the habit that caught the most. Applied to
    every safety mechanism in T3–T14. It found that `reserve`'s two-clone race passed with
    the budget precondition STUBBED OUT (`expected_revision=len(events)` was doing the
    work), and that the in-process `Lock` is not load-bearing for either ledger — the
    ref-CAS is. Docstrings now say which mechanism provides which guarantee.

11. **`expected_revision` is wrong for the per-Attempt ledgers.** It compares the length of
    the WHOLE per-Problem stream, which also carries the audit sink's unconditional
    appends — so `reserve`/`claim` would lose their retry budget to events with no bearing
    on money or the ceiling, then raise `LaneContention` on the money path. Both pass
    `expected_revision=None` and let their precondition (recomputed inside every CAS
    attempt) be the invariant. The coordinator KEEPS its revision CAS — the lane revision
    is the thing it is actually guarding.

12. **Constructing a ledger now WRITES.** `AttemptCreditLedger`/`LaneCallLedger` call
    `bind_attempt_config` in `__init__`, so an `AttemptConfigured` event appears in the
    stream before any reservation or claim. Tests that asserted an empty stream need to
    assert "no credit event" instead.

13. **Terminal audit dispositions are mutually exclusive** (round-9 blocker). `record` +
    `reconcile_unknown` both appended unconditionally, so a completion landing between
    reconciliation's read and its append left TWO contradictory terminal records for one
    dispatch (and the reverse order did the same). Terminal records now carry a CAS
    precondition keyed `(attempt, route, candidate)`; `record` raises on a loss (route-fatal
    via `emit_audit`), `reconcile_unknown` skips (a real completion winning is correct). One
    `_terminal_key` serves the dangling scan AND the precondition so they cannot drift.

14. **Attempt scoping had to hold in the STORAGE key, not just the query** (round-9). The
    review found the resolution scan unscoped; fixing it surfaced the deeper half: the lane
    `event_id` hashed `"audit\0" + slice0_id`, and the slice-0 id is
    `route_id:candidate_index:kind` with NO attempt — so two Attempts sharing a
    caller-supplied route key derived the same lane id and the second died on the
    append-only guard. The attempt is now in the hash. Caught by writing the cross-Attempt
    test the review asked for.

15. **`reconcile_timeout_s` is the only sanctioned way to get a timeout.** A free-form
    number cannot establish "never before it could have finished". `deadline_s=None` —
    `route_chat`'s DEFAULT — raises rather than inventing a floor that merely looks
    conservative.

16. **`_cas_append` returns `created`,** so `reconcile`'s returned ids mean "this call
    transitioned them", not "these are now reconciled". Two concurrent identical reconciles
    no longer both claim the same work.

17. **A test that injects the boundary it claims to test proves nothing** (round-12).
    The patch fail-closed test faked `chat_with_model_fallback`, raised raw
    `ModelUnavailable` itself, and asserted raw `ModelUnavailable` — but `_route_review`
    passes `reraise_model_unavailable=(fallback is not None)`, so with no fallback the REAL
    wrapper converts to `BackendUnavailable` and `except ModelUnavailable` is unreachable.
    The fix is the general one: excluding every family in the offline snapshot makes real
    selection raise a real `ModelUnavailable` (`select.py:197`), so the wrapper's own
    conversion runs. Prefer starving the real path over injecting the exception.

18. **Adding a model-id/family literal to ANY file — tests included — restales the 026
    migration manifest.** `test_committed_manifest_is_current_with_the_live_scan` is the
    only thing that catches it, and it lives in `tests/unit`, not in any focused selection.
    Regenerate with `python -m llmxive.model_selection.inventory` in the SAME commit. Run
    the full `tests/unit` sweep after any task that adds a test file, not a `-k` filter.

19. **Only the DISPATCH was ever meant to be bespoke** (T5). The plan's reason for not
    reusing `run_with_self_consistency` is the CALL COUNT (three per `revise()` breaks the
    ceiling's `+2`) — nothing more. It nonetheless reinvented the wire contract, the parse,
    the change-log assembly, and the token budget, and each reinvention reintroduced a
    defect `convergence/revisers/` had already fixed: a `ValidationError` that bypasses the
    engine's retry, a discarded-revision-on-one-unanswered-concern, JSON-escaping a whole
    markdown document, and spec-023 defect #20's CoT truncation at 32K. The reviser stack
    is `RESPONSE_FORMAT_BLOCK` → `parse_reviser_response` + `pick_expected_artifact` →
    `build_concern_responses`, and a new reviser should reuse all of it.
    **Reviewer = `REASONING_MAX_TOKENS` (32K); reviser = `GENERATION_MAX_TOKENS` (131K).**
    They are different calls — do not "harmonize" them.

20. **A hand-built dict defeats the guard that makes a payload safe** (T6, fixing a 1A
    blocker). `_jsonable` RAISES on unknown types — but its `SnapshotProvenance` branch
    built its result dict field-by-field instead of recursing, so `observed_at`'s
    `datetime` never met the guard and surfaced as a `TypeError` at `json.dumps`, which
    nothing normalizes into `RouteAuditError`. Every composite branch must recurse.
    **The reason it survived 1A: the test passed `observed_at=TS`, a STRING.** These
    dataclasses are plain and frozen with no runtime type check, so a wrong type in a
    fixture makes a whole failure class invisible. Build audit fixtures from the REAL
    slice-0 dataclasses through the REAL `_audit_payload`, and run constructed lane events
    through the REAL `validate_lane_event`.

21. **Check whether the WRITER already refuses it before calling a reader check
    load-bearing** (T6). `_validate_review_rerouted` recomputes both route-id legs from the
    envelope `attempt_id`, so a foreign-attempt or borrowed-leg reroute cannot be
    persisted; two of the plan's reader-side cases model post-write corruption, not a
    reachable path. Keeping them is right (the log is a file on a git ref), but the test
    must construct such input through an explicit `_corrupt()` helper and assert the writer
    refuses it too — otherwise it silently implies the reader is the only guard.

22. **Derive `seq` and the CAS parent from ONE observation of the ref** (T9, fixing a 1A
    blocker). `append_to_log` read events via `read_log` (its own `_rev`) and the parent
    via a SECOND `_rev`. A writer landing between them leaves `seq` stale while `parent`
    is fresh — so `update-ref`'s compare-and-swap PASSES and two events durably share a
    seq. A CAS is only as correct as the snapshot its precondition was computed from.

23. **A retry budget must EXCEED the writer count, and needs jitter** (T9, 1A blocker).
    `max_retries=8` equalled `engine._PANEL_MAX_CONCURRENCY=8`. Losing every race to every
    peer is a legal interleaving, not an anomaly. Without jitter the losers re-read and
    re-commit in lockstep and collide again.

24. **`read_log` was O(n) subprocesses, so appends were O(n²)** (T9). One `git cat-file`
    per event × a full read per append: 245 ms/append at 30 events, 1206 ms at 120. One
    `git cat-file --batch` makes it flat (115→152 ms). Use binary I/O — `--batch` sizes
    are BYTE counts.

25. **The integration test is what found all three.** None were reachable by a unit test:
    they need real concurrency, a real git ref, and a real panel. When a slice's substrate
    is "already signed off", the end-to-end test is still the first thing that has ever
    actually exercised it.

26. **Check what the engine RETURNS before asserting on it** (T9). `ConvergenceResult` has
    no `artifacts` field — the revised artifacts never leave `run_convergence`. Observable
    output is `response_history` / `concern_history` / `verdict_history`.

27. **Two ledgers gate a paid dispatch.** 026's DAILY ledger runs first and fails closed
    when unconfigured, so a lane paid-path test that does not stand one up never reaches
    the Attempt authority and proves nothing. Raise the daily cap far above the Attempt
    budget, or it is ambiguous which ledger refused.

28. **A green test on THIS machine can be a red test everywhere else** (round-17 F3). The
    paid panel test passed locally only because this machine holds Dartmouth credentials,
    so `execute`'s two pre-authority balance reads succeeded — by making LIVE NETWORK
    CALLS. Anywhere else they fail closed, every paid candidate is skipped before the
    Attempt authority, and the suite passes while proving nothing. When a test depends on
    an external credential, inject through the documented seam AND assert the seam was
    used, or it silently reports the environment instead of the code.

29. **Two arguments describing one fact will eventually disagree** (round-17 F2).
    `proposer_baseline` and `proposer_route_id` both described the proposal's author.
    Nothing forced agreement, so a caller could exclude the wrong family and a reviewer
    of the author's OWN family would satisfy selection — with every individual record
    still true. DERIVE from the durable source and refuse a contradicting argument.

30. **`True == 1` in Python, so a bool passes an integer index check.** Any validated
    index needs `isinstance(x, int) and not isinstance(x, bool)`.

31. **Prefer a policy FIELD to a hard-coded name set** (round-17 F1). The strict
    convergence bar lived as `_REVIEW_STAGES` in `engine.py`; a new judgment stage
    inherited the lenient authoring default just by not being listed there — which is how
    the proposal gate came to treat unresolved concerns as acceptance. Migrated to
    `ReviewSpec.strict_acceptance` and DELETED the set, so there is one mechanism, and
    guarded the partition in both directions.

32. **Inject the failure at the layer your claim is about** (round-18). The clean-abort
    test patched `chat_with_model_fallback`, ABOVE the router, so selection and the
    dispatch lifecycle never ran — it could only ever prove the `LaneCallClaimed` ceiling
    charge while its name promised the route-audit trail. Failing at the BACKEND instead
    runs the real path and produces the whole trail (`ChainResolved`, `SelectionFailure`,
    `ReviewRerouted`, `DispatchStarted`, `CandidateOutcome`). The general form: a test
    that stubs above the thing it names proves the stub, and the honest fix is usually to
    lower the injection point rather than to lower the claim.

## Spec gap found before the lifecycle slice (fixed: spec rev 17, FR-034)

Raised in the 2026-07-30 review and CONFIRMED — the transition table left `proposed` with
only two exits, `ProposalVerified` and `Rejected`, so an operational failure during proposal
review had no legal transition at all. Two spec passages already routed such failures to
`eval_failed`/`impl_failed` (FR-033b's `ChainExhausted` line; the LLM-call-ceiling row),
and NEITHER is reachable from `proposed` — a live internal contradiction, not just an
omission. The proposal ceiling term `4N + R·(2N+2)` is spent while the Attempt is at
`proposed`, so the ceiling row was unreachable exactly where it was most likely to fire.

Two things the original finding did not include, both folded into rev 17:

1. **The same gap exists at the PATCH review.** There an infrastructure abort WOULD have had
   a transition — `eval_failed` — but a counted one, so a provider outage would consume the
   Problem's quality-failure budget and push it toward a 30-day cooldown. Fixing only the
   proposal side would have left the two judgment reviews classifying identical failures
   differently. `FR-034` spans both.
2. **An uncounted terminal with no bound is a live-lock.** FR-001 already ruled that a
   transient/availability condition "does NOT by itself count as an Attempt-quality failure
   or a cooldown event", so `review_aborted` must not touch the quality counter — but then a
   permanent outage re-proposes the same Problem forever. It carries its own looser bound
   (5 → 7-day operational cooldown) on a SEPARATE counter.

The naming follows a distinction the spec already made: `*_failed` = the lane reached a
substantive negative answer; `*_aborted` (`promotion_aborted`, now `review_aborted`) = the
lane could not reach an answer. `rejected` is substantive — recording it for an
infrastructure abort would assert a verdict no panel gave.

### Rev 18 — the rev-17 review found the fix was half-right

Six findings, all confirmed. Two mattered structurally:

**`ModelUnavailable` was missing from an "exhaustive" list.** rev 17 enumerated
`ChainExhausted` and forgot 026's *central* fail-closed signal. The classification has to be
STAGE-AWARE, which is why it was easy to miss: the same exception is non-terminal on the
proposal PRIMARY leg (it triggers the FR-002 reroute) and terminal everywhere else — the
proposal FALLBACK leg, the patch review, and any reviser call. The patch case is the one
#1242 explicitly requires (fail closed when no independent family is live), so the single
most important safety path in the spec still had no legal Attempt outcome after rev 17.
Lesson: **"exhaustive" is a claim to verify against the dependency's error taxonomy**, not a
word to write.

**You cannot durably record "the log is broken" in the broken log.** rev 17 listed lane
event-log integrity failure as a `review_aborted` cause. Unimplementable: writing the
terminal, reconstructing unresolved dispatches, and even testing whether a claim is held all
require the log just declared untrustworthy. Any implementation would have had to write into
a store it called corrupt, trust a projection it called unrebuildable, or claim a terminal it
never recorded. New FR-035 splits three things rev 17 had as one: ordinary CAS contention
(retry — already FR-008), operational failure over a HEALTHY log (`ReviewAborted`), and ref
integrity/availability failure (run-level QUARANTINE — fail closed, no terminal, no
coordinator mutation, escalate; the Attempt stays honestly unresolved). The general form:
**an error class whose blast radius is the whole store cannot be recorded as one record's
outcome.**

FR-035 also forced out a **pre-existing** wedge, unrelated to rev 17: a crash anywhere
between `ClaimGranted` and a terminal leaves `active_problem_id` set forever, because the
claim CAS requires it be `None`, `project_lease` is documented as in-host contention only
(NOT cross-runner correctness), and no reaper exists. "The Attempt remains unresolved until
repair" is only safe if something can later resolve it — hence `claimed_at` + an explicit
`ClaimExpired` event (2 h, chosen to exceed the largest Attempt wall-clock budget with
margin). Found only because F2's fix depended on it.

Also: wall-clock expiry added to the classification and the two review budgets finally
defined in the Policy Contract (wall-clock is called the PRIMARY bound, yet only
implementation and evaluation had budgets); `ReviewAborted` restricted to `proposed`/
`implementing` (rev 17 allowed `claimed`, where no review runs); `rejected` re-described as a
substantive negative determination — **panel OR deterministic pre-gate** — since rev 17's
"asserts a panel judgment" contradicted its own next paragraph; and the cooldown key
`(problem_id,"cooldown")` corrected to `(problem_id,"cooldown",cause,epoch)`, which had
allowed exactly ONE cooldown per Problem for all time and conflated both causes.

### Rev 19 — the fix for rev 18 opened two gaps of its own

**A liveness-based reclaim is a concurrency primitive, and I added one without stating its
invariant.** `ClaimExpired` (rev 18) frees a wedged slot by declaring a claim dead after a
timeout — but the original run may still be ALIVE, so it can append its own terminal
concurrently with the reclaimer's. Result: two terminals on one Attempt, and a run that has
been reclaimed still operating as though it held the lane. Ref-level CAS does NOT save this:
it ORDERS the two appends, it does not reject either. Nor do the per-transition idempotency
keys — those guard REPEATS of one transition, not two DIFFERENT terminals racing.

Rev 19 states the missing invariant: **exactly one terminal per Attempt**, every terminal
append CAS-conditioned on the Attempt having none, first writer wins, loser discards. Plus
the three consequences: the reclaimer re-verifies expiry + no-terminal INSIDE the committing
CAS; the loser performs no further side effect; and **a run must re-confirm it still holds
the claim immediately before each irreversible side effect**. That last one is the real
lesson — without it the reclaim would have reintroduced precisely the concurrent-writer
hazard the singleton coordinator exists to prevent, i.e. the "fix" would have been strictly
worse than the wedge. **General form: adding a timeout-based takeover to a mutual-exclusion
scheme silently converts it from "one writer" to "one writer who must keep proving it."**

**Two magic numbers became derived.** `claim_expiry` was a literal 2 h that cleared the
105-min post-claim wall-clock sum by 15 min — and would have become WRONG the instant anyone
raised a phase budget, with nothing to catch it. Now `2 × (implementation + patch_review +
evaluation)`, post-claim phases only (the claim is granted AFTER the proposal review), so it
self-adjusts. `K` is now the smallest integer with `K × controller_cadence > 24 h`, which at
the 6 h cadence evaluates to the same 5 — but now the spec carries the INVARIANT ("only an
outage lasting beyond a day cools down a Problem") instead of the number. Same discipline the
LLM-call ceiling row already used; I should have applied it when I introduced them.

Also repaired the revision-history header, which had accumulated unclosed `Prior revision N (`
parens (unbalanced by 2 before rev 19); the block is now balanced.

### Rev 20 — three defects in my own rev-19 fix

**"Re-confirm immediately before" is check-then-act.** I wrote it as if narrowing a race
closed it. `ClaimExpired` can land after the confirmation and before the GitHub call, so a
superseded worker still mutates the external system; no value of "immediately" fixes a
check-then-act. The correct shape is **fencing**: a monotonic `claim_generation` on every
grant/reclaim, every lane-log append generation-stamped and CAS-REJECTED if superseded, and
generation-stamped side-effect intents where **reclaim blocks until an outstanding intent is
observed and closed**. That last rule is what actually prevents two concurrent actors —
the reclaimer never starts a competing mutation.

Also worth stating plainly because I nearly overclaimed again: **you cannot fence a system
that does not participate.** GitHub will not check our token, so an already-issued call
cannot be rejected. The spec now says exactly what IS guaranteed (two actors never issue
concurrently; anything landed is discovered; a superseded worker can never record lane
state) instead of the false "a stale worker cannot mutate GitHub".

**Off-by-one in the cadence derivation.** K observations at cadence c span **(K−1)·c**, not
K·c. K=5 at 6 h is 24 h elapsed, not the 30 h I claimed. K=5 survives (re-derived from
`(K−1)c ≥ 24h`) but the justification was wrong. Fixed properly by not relying on tick
arithmetic at all: the rule is now `count ≥ K` AND a MEASURED `now − streak_started_at ≥
24 h`. Tick arithmetic assumes an even cadence that skipped/retried/manually-dispatched runs
violate — a burst of 5 aborts in 2 h would have tripped a count-only rule.

**A "derived" number that didn't cover what it claimed.** `claim_expiry` summed
implementation + patch review + evaluation and omitted publish and candidate testing — and
publish had NO wall-clock cap at all, so no honest total was even computable. Deriving a
value is not the same as deriving it from the RIGHT set; I checked the formula was a formula
and not that its terms were complete. Now: publish capped (10 min), one authoritative
`max_claim_hold_time` over every post-claim phase + overhead (3 h 15 m), and liveness moved
to a **renewable heartbeat** (5 min beat, 15 min expiry) with the hold time as a separate
cap — which also dissolves the original tension, since crash recovery (~15 min) no longer
trades off against never reclaiming a live-but-slow run.

### PROJ-317 contributing.md — reported as a regression, actually a case collision

Flagged as an uncommitted rewrite deleting the operational sections. It was not. BOTH
`docs/contributing.md` and `docs/CONTRIBUTING.md` were tracked in HEAD as distinct blobs
(`6f3aee2456` detailed, `67f63263e6` boilerplate), and the reported diff was exactly
`6f3aee2456..67f63263e6` — one tracked path being overwritten on disk by the other. With
`core.ignorecase=true` only one physical file can exist, so the tree is PERMANENTLY dirty and
see-saws: restoring one instantly dirties the other. Nothing was ever deleted.

All 6 projects with this doc use lowercase, so the uppercase file was the anomaly and it held
the boilerplate. Dropped the uppercase path; kept the detailed guide. **Diagnose a dirty file
before restoring it** — `git checkout` here would have looked like it worked and fixed
nothing.

### Rev 21 — the delayed-worker impossibility, and two consequences of fixing it

**Observation is asymmetric, and rev 20 leaned on the half that does not hold.** I wrote that
intent reconciliation is "deterministic and terminating, because every side effect is keyed."
True for a POSITIVE observation: seeing the effect present is conclusive. Seeing it ABSENT is
not — it cannot distinguish "never landed" from "not landed YET" while a stale worker's call
is still in flight. A reclaimer treating absence as proof closes the intent as not-landed,
reclaims, and then the delayed call lands against a lane that recorded the opposite. No
amount of care on OUR side resolves it, because the missing information lives in the network.

Two mechanisms, in preference order. **(a) Externally enforced preconditions** — generation-
scoped branch namespaces (`…/<attempt-id>/g<generation>`) mean a delayed worker can only ever
write inside its own dead generation, which the new owner never touches; that needs no external
cooperation at all, it just makes the two actors' namespaces disjoint. **(b) Quarantine** where
no enforceable precondition exists: mark the intent `ambiguous`, block reclaim, leave the
Attempt honestly unresolved. The forbidden move is declaring "did not land" on an inference the
lane cannot support. *(Rev 21 also listed expected-`head_sha` merges under (a) and treated the
namespace as making absence decidable. Both were wrong — see rev 22 below.)*

**Extending the claim through `promoting`/`promotion_requested` forced a naming fix.** The
claim is held until `PromotionObserved` clears the slot, so heartbeats and expiry must span
those states too. But then `ClaimExpired` could not terminate at `review_aborted` — misnamed
where no review runs, and it would re-introduce the `claimed` mislabeling rev 18 removed —
and `impl_failed` would be worse, since counting an abandonment lets a crashed runner eat a
Problem's quality budget, exactly what FR-001 forbids. Hence `attempt_abandoned`: operational,
uncounted, valid from every claim-holding state. **A terminal state's NAME is part of its
contract; reusing a near-fit one silently misreports why the Attempt ended.**

**FR-036: every new bound turned out to be a clock comparison.** Heartbeats, `claim_expiry`,
`max_claim_hold_time`, `streak_started_at`, `cooldown_until` — all durations, all measured on
independent runners. `seq` stays the SOLE ordering authority (timestamps never order events),
and every safety-critical comparison pads by the skew in the direction that avoids the worse
error — reclaim needs `elapsed ≥ claim_expiry + max_clock_skew`, never less. *(The rev-21
validation rule this section described was withdrawn in rev 22 — see below.)*

### Rev 22 — two "resolutions" that resolved nothing

**A precondition that constrains CONTENT is not a fence.** Rev 21 claimed expected-`head_sha`
made a merge from a superseded generation fail at GitHub. GitHub's own docs say `sha` is "SHA
that pull request head must match to allow merge" — it pins WHICH COMMIT merges, not WHICH
ACTOR merges, and GitHub has never heard of `claim_generation`. A stale worker merging its own
dead generation's PR passes the check (nobody touched that head) and lands in the shared
target. **Ask of every "externally enforced" precondition: enforced against WHAT? If the answer
is a property of the payload rather than of the caller, it is not fencing anything.** Merge and
revert are now `ambiguous` → quarantined, with a stated bar any future escape must clear.

**Containment is not decidability, and conflating them cost the whole argument.** Generation-
scoped namespaces are genuinely good — a stale push can only ever write a dead namespace. But
the push can still ARRIVE, arbitrarily late; it is contained, not absent. Rev 21 filed it under
"absence becomes decidable", which is false. Reclaim is safe there because the landing is
HARMLESS, not because it cannot happen — a different justification, and only writing it down
correctly reveals which operations still lack one. Hence four dispositions (`landed`,
`rejected`, `contained`, `ambiguous`); the two-way split is what produced both errors.

**Validating a clock against itself.** Rev 21 rejected an append more than `max_clock_skew`
"ahead of the appending process's own clock" — the same process that generated the timestamp,
so the comparison is vacuous. Worse, its companion rule (reject anything trailing the ref's
latest) meant one fast-skewed runner's FIRST event poisons the ref and then rejects every
correctly-timed runner forever. **A validation rule needs an independent referent or it is
decoration.** The authority is now GitHub's server clock, read from the `Date` header of a call
the run already makes; no trusted offset ⇒ no lane work.

**A budget that stops before the work does.** `max_claim_hold_time` still ended at evaluation
even though rev 21 had just extended the claim through `promoting`/`promotion_requested` in the
same revision. Two edits, one revision, contradicting each other. Fixed with explicit
`promotion` and `intent_reconciliation` terms (3 h 40 min) — and `intent_reconciliation` was
previously *inside* `overhead`, where nobody could see it was too small.

### `cas_claim` now returns a typed outcome (rev 22 — changed, not just pinned)

`cas_claim`'s idempotency branch asks "did THIS event already land", not "do I own the claim
now". So a replay arriving after the claim was released and the lane re-granted returns
NORMALLY while another Attempt owns the lane. That call is legitimately not an error — nothing
was written and nothing is wrong — so raising would be the wrong shape. What was wrong is
making every caller re-derive ownership by comparing projection fields.

Both entry points now return `ClaimOutcome(acquired, owner_problem_id, owner_attempt_id,
coordinator)`. `acquired` answers the only question a caller has: does the pair I named hold
the lane NOW? False after a release, False for a superseded replay. **Done now, before
lifecycle callers exist** — grep confirmed the only consumers were tests, so the change cost
one afternoon instead of an audit of every call site. The FR-035 fencing token
(`claim_generation`) belongs on this record and joins it with that slice; it is deliberately
absent rather than faked, since the coordinator stream does not carry generations yet.

## Carried forward to whichever slice owns lifecycle reconciliation

Maintainer reminder at 1A sign-off (2026-07-27): **production reconciliation must compute
its timeout with `reconcile_timeout_s()` from the SAME `deadline_s` + `retries` the lane
call uses.** Neither 1A nor 1B owns lifecycle reconciliation, so this is not a blocker for
either — but a timeout chosen independently of the real call configuration cannot support
"never before it could have finished", and it silently stops holding if the lane's deadline
later changes. Stated on `reconcile_unknown`'s docstring, which is where an integrator will
land.

## Next step

**Slice 1A is SIGNED OFF** (maintainer, 2026-07-27): 14/14 tasks, round-9 clean, "no
remaining correctness findings — the substrate is ready for Slice 1B".

**Slice 1B is SIGNED OFF** (maintainer, 2026-07-29, re-confirmed 2026-07-30 after the
round-18 clean-abort precision fix): 10/10 tasks plus 4 fixes to already-signed-off 1A
substrate that the first real end-to-end panel exposed (duplicate `seq`, `GitLogContention`,
O(n²) appends, the audit sink's non-recursive `_jsonable`). "No remaining correctness
findings ... ready for the next implementation phase."

Next is the **Attempt-lifecycle slice**, which owns the seam 1B deliberately left open (the
Attempt-level abort record, round-17 F5). Blocked on a spec amendment first — see
"Spec gap found before the lifecycle slice" below.

### The six persistent untracked artifacts — classified (2026-07-30)

Verified against what git already tracks, so the branch can be published without guessing:

| Artifact | Count | Category | Action |
|-|-|-|-|
| `state/run-log/2026-07/local-*.jsonl` | 3 | TRACKED category — 12,382 files tracked under `2026-07/`, 18 `local-*` tracked repo-wide; `.gitignore` excludes only `in-progress/` and `.invalid/` | Leave for the cron's own commit to main |
| `state/convergence-cache/*.json` | 2 | TRACKED category — thousands already committed | Leave for the cron's own commit to main |
| `notes/2026-07-15-issue-1139-audit-T+7min.md` | 1 | User's unrelated work, untracked at session start | Never commit |

The five state files are legitimate pipeline output of a kind git already tracks, so
`.gitignore`-ing them would be wrong — it would stop the pipeline committing real state.
They are simply not THIS branch's content, and untracked files are not published with a
branch, so they do not block the PR. The actual risk is accidental sweeping (which is
exactly what happened once, in `8097c5b183`), and the guard against that is committing with
explicit paths — `git commit -o <path> …` — never `git add -A` / `git commit -a`.

**Do not re-commit `notes/2026-07-15-issue-1139-audit-T+7min.md`.** It is unrelated user
work that was untracked at session start; `8097c5b183` swept it in and `git rm --cached`
put it back to untracked (contents never inspected or altered). It is still in that
commit's history — if the branch is squashed or rebased at PR time, confirm it does not
reappear in the tree.

## Slice 2, Task 1 — spec rev 23 (2026-08-02)

Rev 23 lands before any Slice-2 code, as every prior round has. Its cause is different from
the last one: **rev 22's text was largely sound; the Slice-2 PLAN was drafted on a false
premise about the store.** The draft assumed the coordinator stream and each Problem stream
lived on separate refs. They are subtrees of ONE ref (`lane_log._log_ref`), which means a
commit can touch several streams at once under a single ref compare-and-swap. Two things
the draft was about to write into the spec were therefore simply untrue — an "honest limit"
that the generation check is advisory, and a compensating `ClaimReleasedByReclaimer`
transition to repair a terminal-without-release wedge. The first became BINDING; the second
was deleted, because the state it repaired is unreachable once terminal and release are one
transaction.

**What was a plan defect, and what was a spec defect.** Worth separating, because the two
have different lessons.

Plan defects: the false premise above; writing `PromotionObserved` as a coordinator-only
append *after* the transaction mechanism already existed; and an invariant claiming "a crash
at ANY seam leaves no events", which is false after a successful push and contradicted the
plan's own `_after_push` test.

Spec defects, all four genuine and all found by reading the spec against the plan:
1. The `PromotionObserved` row described "one coordinator CAS" and a `merged+monitoring`
   state. It is a three-event cross-stream transaction. Now `†◇`, `To` = `monitoring`, with
   an explicit `MonitorStarted` ownership precondition — which is also what makes the two
   coordinator events' ORDER semantically required rather than conventional.
2. The `†` paragraph tied claim release to pre-merge off-ramps and to terminals. Both false:
   `PromotionObserved` releases without being terminal, and several `†` rows are reachable
   from pre-claim states where there is nothing to release. Effects are CONDITIONAL, and the
   condition is read from the Attempt's own state, never from the coordinator.
3. `last_autonomous_merge_at` was a bare field name in three places with no definition.
4. FR-036 bounded no clock regression at all.

**Two things the plan asked for that the spec did not contain.** Recorded because a plan
step whose premise is wrong is worth catching at execution rather than propagating:
- Step 2 said to put the terminal-and-release note "under the transition table" while Step
  2b said to put the matrix "into FR-035, immediately after the note above". Both are in
  FR-035 (normative content belongs with the requirement), with the marker legend under the
  table pointing there.
- Step 2c said to REPLACE a sentence claiming `last_autonomous_merge_at` advances
  monotonically. No such sentence existed — the claim was in the review discussion, not in
  the spec. The definition was ADDED to FR-007 instead, which is what the step was for.

**Also corrected while making the table machine-comparable.** The plan's Step 2b edit 2 says
to delete "the trailing sentence" describing `PromotionObserved` as a single coordinator
CAS. That sentence had two clauses joined by a semicolon, and the first — that the
intent/observed split closes the crash gap between the side effect and the recorded state —
is still true. It was restored as its own sentence, with a parenthetical recording what was
removed and why.

The half-open interval `[N, N+1)` in the new FR-036 sampling text was rewritten as prose:
correct notation, but its unbalanced `)` defeats the paren-balance check the plan's Step 6
runs, and a check that has to be special-cased stops being a check.

**Deferred, not skipped.** Step 6's second command runs `parse_spec_transitions()` against
the amended table. That helper is written in the transition-table task, so the command runs
at that task's Step 5 (Task 4 Step 5 at the time; **Task 5 Step 5** after the renumbering
below). The first command passed here: 28 rows, every row exactly 6 fields, parens balanced.

## Slice 2 — maintainer decisions on the thirteen open questions (2026-08-02)

All thirteen resolved; every proposed direction approved. Four changed the plan and one
changed the spec (rev 24). The full text of each question and its ruling now lives in the
plan under "Maintainer decisions (2026-08-02)"; what is worth recording HERE is the work
they caused and the two premises that turned out to be wrong.

**Spec rev 24** — one normative change, from decision 1: the time authority MUST be read
under an authenticated request. Rev 23 said `GET /rate_limit` supplies the instant without
saying under what identity, and the unauthenticated path's 60/hr allowance is per IP and
shared with every other tenant of the runner's address. That would make "the lane has no
trusted time" a state an unrelated workload could induce, on the one input that decides
whether a live claim-holder is evicted.

**Task renumbering** — decision 7 split the pre-existing `append_to_log` rewind fix into its
own task ahead of the transaction work, so Tasks 2–13 became 3–14. The new **Task 2** fixes
`update-ref` with no expected-old value, introduces `Seam` and `_after_push` on
`append_to_log`, and gates on `append_to_log`'s complete consumer set. Task 1 (the spec
amendment, already committed) is unchanged.

**Two premises in the questions were wrong**, both found by checking rather than assuming —
same class as Task 1's Step 2c:
- Decision 12 asks that "existing 1A projection tests" pass unchanged. There are none:
  `grep -rn project_attempt src/ tests/` returns nothing, because this slice introduces the
  function. The compatibility requirement is real, so it is discharged by PINNING
  `project_attempt`'s error messages in the task that writes them.
- Question 10 asks for an audit of `cas_release`'s callers. Done, and the answer is that
  there are no production callers at all — it is exported and reached only by tests. The
  change is additive at every call site. That is worth knowing before an implementer goes
  looking for breakage.

## Slice 2 implementation log

**Task 2 — the ref-rewind fix (`66a8eada95`).** `_sync_local_ref` replaces `append_to_log`'s
bare post-push `update-ref`. Verified load-bearing by restoring the bare call and watching
the regression test fail, then restoring the fix. Reused the module's existing
`_is_ancestor` rather than the plan's second raw `merge-base` call.

*One of my own tests passed against unfixed code first.* `_empty_commit_on` built the
"ours" and "unrelated" sibling commits with identical tree, parent, message and identity —
`commit-tree` is deterministic, so within one second they were the SAME object and the
divergence case was an ancestor of itself. Fixed with a required `message` parameter plus
an explicit `assert unrelated != ours`. Worth remembering: a git fixture that builds two
"different" commits needs something to actually differ.

**Task 3 — multi-subtree transactions.** `_commit_events` (many `(event_dir, event)` pairs,
one commit), `append_transaction` + `TransactionResult` in `git_event_log.py`, `append_many`
in `lane_log.py`. `_identity_body` lifted out of `append_to_log`'s closure so both writers
share one definition of event identity.

Two things the plan's test code got wrong, both found by running it:

- **Replay tests that stamp `seq` must also exclude it from identity.** A replay observes a
  longer stream, so the rebuilt event carries a different `seq` than the stored one, and
  the append-only guard fires before the replay path is ever reached. The plan's
  `test_a_replay_reports_the_STORED_seqs_not_recomputed_ones` passed `finalize` with no
  `identity_exclude`, so it could not have reached the branch it was written to test.
  `_seq` and `_EXCL` now travel together, which is the pairing `lane_log._IDENTITY_EXCLUDE`
  already makes in production.
- **A replay must re-read `expected_revisions`.** They are an assertion about the log's
  CURRENT shape, checked before anything else, so a retry quoting the ORIGINAL numbers is
  asserting something false and correctly loses. Every `cas_*` caller reads them fresh;
  the lost-ack tests now do the same, and a new test pins that stale ones are refused.

Atomicity verified load-bearing (Step 9): replacing `append_many`'s body with two
sequential `append` calls makes `test_a_crash_before_the_ref_moves_leaves_NEITHER_stream`
fail with the coordinator event durable and the Problem event missing — the exact
half-state. Restored and re-verified. *The first attempt at this substitution silently
failed to match, and the test "passed" — a passing test after a no-op edit proves nothing;
always confirm the edit landed before believing the result.*

**Task 4 — the authoritative clock.** `policy.py` (the Policy Contract's first consumer is
the clock, so the module is born here) + `clock.py`: `GitHubDateClock` with bracketed
monotonic sampling, `FixedAnchorClock`, `parse_http_date`, `NoTrustedTimeError`.

*A real gap in the plan's design, exposed by implementation.* The plan bounded the clamp's
MAGNITUDE (`MAX_CLOCK_REGRESSION_S`) but not its DURATION — and the duration is what its own
rationale argues about ("an unbounded clamp converts an authority fault into a lane that
looks healthy and makes no progress"). An authority that is STUCK, serving the same instant
forever, sits a CONSTANT distance behind the floor: it never trips the magnitude check, and
every refresh re-anchors to the same stale value, so emitted time stands still indefinitely
while every call still succeeds. Expiry stops approaching, hold time stops accruing,
cooldowns stop maturing, and nothing raises. Fixed with `_clamped_since`: a clamp held
continuously for longer than the same tolerance fails closed. Two new tests cover it (the
stuck authority raises; a brief clamp is still absorbed).

*A test fake that modelled the wrong fault.* The plan's non-regression test repeated
`EARLIER_HDR` forever, which is a STOPPED authority, then asserted "elapsed monotonic time
walks out of the clamp on its own" — which a stopped authority never does. Corrected to a
stepped-back-then-ticking authority (a third, later header), with the stopped case split
into its own test where it belongs.

Six mutations run, each killing at least one dedicated test: no floor clamp (5 fail), no
magnitude bound (1), no duration bound (1), no header-resolution floor (2), no header
centring (2), and reading the wall clock (10, including the grep guard). Real-call suite
verified against live GitHub with a token from `gh auth token` — 4 passed, including that an
unauthenticated run against the REAL endpoint still raises rather than quietly succeeding.

**Wrong test paths in the plan, fixed while wiring decision 3's gate.** The plan named
`tests/unit/test_model_selection_ledger_transport.py` as the ledger gate; no such file
exists. The credit ledger reaches the shared transport through
`model_selection/ledger_transport.py`, and its suite is
`tests/integration/test_credit_ledger_transport.py`. `grep -rl append_to_log src/` also
turned up a THIRD consumer the plan never mentioned — `self_improvement/audit_sink.py` —
now included in the gate. Its tests are `tests/integration/test_self_improvement_audit_sink.py`.

**Task 5 — the transition table as data.** `lifecycle.py` (22 transitions, `walk_attempt`
as the ONE fold, `project_attempt` on top of it, `TransitionOutcome`, `Step`,
`NonTransition`) + `tests/helpers/lane_lifecycle.py` + 51 model tests. The deferred Task 1
Step 6 drift check is discharged here and reports what it was specified to: **22**
attempt-transition rows parsed from the spec, `PromotionObserved` effects
`('MonitorStarted', 'ClaimReleased')`, attempt-scoped non-transitions
`['ClaimHeartbeat', 'PublishRequested→Published']`.

*One helper knew a rule the other did not.* The plan's `_history` stamped
`claim_generation` on `ClaimGranted`/`ClaimHeartbeat`; its `drive` did not. But
`walk_attempt` reads that field on every grant, so every `drive()`-built history that
reaches `claimed` — which is most of the exhaustive grid — would have died on a missing
payload, and died as a bare `ValueError` that `pytest.raises(IllegalTransition)` does not
catch. Two helpers, one rule, only one of them holding it. The rule now lives in
`attempt_event` (`_GENERATION_DEFAULT`), where both get it and an explicit `payload=`
still overrides — which is what the stale-generation test needs.

*The fold had two refusal types.* `payload_field` raises a bare `ValueError`, and every
caller of this fold catches `IllegalTransition`; a `ClaimGranted` with no
`claim_generation` is a record no writer can produce, so refusing it as a different
exception type means `cas_attempt_transition` does not recognise it as "this history is
untrustworthy" and does not handle it. Added `_required_field` (one wrapper, both call
sites) plus a parameterized test for the grant and the beat.

*A docstring that claimed a branch it does not reach.* `project_attempt`'s "only
non-transition events" guard is unreachable through the current vocabulary — every declared
non-transition is legal only in a claim-holding state, so a beats-only stream already fails
inside `walk_attempt`. The guard is kept (the alternative failure mode is an
`AttributeError` on `last`), but the test now says it asserts the OUTCOME, not that line.

Smaller corrections to the plan's code, all found by running it: missing `deque`/`Iterator`
imports in `lifecycle.py` and five missing imports in the test module; `__all__` omitting 9
of the names the Produces block promises; `TransitionOutcome` promised by Task 5 but only
written in Task 7's prose (now declared once, in Task 5); and `_SPEC` as a bare relative
path — anchored on the test tree's own location instead, deliberately NOT on
`config.repo_root()`, which `LLMXIVE_REPO_ROOT` redirects to a synthetic DATA root with no
`specs/` in it.

Eight mutations run, each killing at least one test (Step 6 table in the plan). `git diff`
proves nothing about restoration for a file that is still untracked, so the harness
compares a sha256 against the pre-mutation digest and refuses to run a mutation whose
anchor did not match.

Two tests the plan did not have, added because the names they cover were otherwise
unasserted: `holds_claim` (declared as "the ONE reading" with three callers, but nothing
called it — including its `None` case) and `counts_against_operational` (the random walk
pinned the quality counter only, so the FR-034 split between the two ledgers went
unchecked). 52 model tests total.

**Task 5 follow-up (review): the projection reported a release that never happened.**
`AttemptProjection.releases_claim` was `last.releases_claim` — the ROW's declaration. But a
coordinator effect is conditional on the Attempt holding the lane at the state the
transition LEAVES (the spec's own words: the dagger marks "must not leave the lane
occupied", not "always mutates the coordinator"). So `ReviewAborted` from `proposed`,
`ScopeUnsupported` from `proposal_verified`, and a pre-claim `BreakerTripped` all reported
`True` while emitting nothing. That is the exact false positive the plan's
`assert_lane_consistent` case 12j exists to catch — reintroduced one layer up, at the fold's
output.

Renamed to `released_claim` (past tense: the row says `releases`, the projection says what
happened) and computed through a new named predicate
`released_claim(transition, state_before)`. Removal was the other option offered and was
rejected: nothing consumes the field today, but removing it leaves the CLASS unaddressed —
the next caller who wants that answer recomputes it from the row and gets the same three
false positives. `holds_claim(state_before)` is now the one gate both this and Task 7's
`_claim_required` consult; they differ only in which declaration they read, and the plan's
Task 7 docstring now says so (they agree on every current row, since every row declaring an
effect declares a release — a future `◇`-only row is when they must not be collapsed).

Two stale comments corrected in the same pass, before Task 7 is written against them:
`PromotionObserved`'s ordering rationale (it is MONITORSTARTED's ownership check, not the
release's, that rejects the reversed order — releasing first leaves MonitorStarted with no
owner to match), and `project_attempt`'s "last transition, not last event" note, which
justified itself with a heartbeat AFTER a terminal — a history `walk_attempt` refuses. The
real reason is a heartbeat DURING a held claim, which is legal and can be the final record
on the stream.

Seven tests added (59 total), including the derived non-holding set asserted by equality so
a row reachable from a new non-holding state shows up in review rather than silently
widening the exemption. Mutations now ten: dropping the `holds_claim` gate and having the
projection read the row directly kill DIFFERENT tests, so the predicate being right does not
prove the fold uses it.

**Task 6 — the Attempt event vocabulary + write-boundary validators.** 24 types added to
`KNOWN_EVENT_TYPES_V1` (the 22 transitions minus the 3 already there, plus `ClaimHeartbeat`,
`MonitorEnded`, `SideEffectRequested`, `SideEffectObserved`, `Cooldown`), each with a
validator; `MonitorStarted` gained required `problem_id` + `merged_at`;
`coordinator._coord_event` became `events.coord_event` alongside `COORDINATOR_KEYS` +
`coordinator_event_id`.

*Two questions the plan's Task 6 did not answer, both forced by what the fold does.*

- **Nineteen types would have had no validator.** The plan tabulates payload key sets for
  seven types; the other nineteen are plain transitions. A type in the vocabulary with no
  validator is a payload nobody checks — and `walk_attempt` reads these payloads. They now
  share `_validate_attempt_transition` (names its Problem, names its Attempt, payload agrees
  with envelope on both), NOT `_exact_keys`: the house rule scopes exactness to events
  binding a limit or a routing identity, and fixing a key set here would mean guessing the
  per-transition fields the spec's own idempotency keys imply (`head_sha`, `reason`) and
  rejecting records the table requires. `test_every_attempt_event_type_has_a_payload_validator`
  is the guard. `ClaimGranted` additionally requires `claim_generation`, the one field the
  fold reads; Task 8 adds the four claim terms and makes it exact.

- **`SideEffect*`/`Cooldown` must NOT carry an ENVELOPE `attempt_id`.** `project_attempt`
  selects a history as `[e for e in stream if e.attempt_id == attempt_id]` and fails closed
  on any type outside `ATTEMPT_EVENT_TYPES`, so one of these filed under an Attempt's
  envelope makes every LATER projection of that Attempt raise — permanently (append-only),
  leaving it unable to record even its own terminal. Their association lives in the payload.
  This is a DECISION, flagged for the maintainer: it is the only reading consistent with
  the fold and with Task 5's own comment that "nothing lands on the Attempt's own stream"
  for the publish saga, but Task 9 is what will actually read these back.

*Three transport fixtures the plan did not look at.* `test_self_improvement_lane_log.py`'s
`_ev`/`_gapped` and `test_self_improvement_lane_transaction.py`'s `_prob` build
`event_type="Proposed"` with `payload={}` as a generic problem-stream record. `Proposed` is
validated from this task on, so those fixtures were exercising the store with a record the
store is now supposed to refuse — 24 failures, all fixed by giving them a well-formed
identity pair rather than by exempting `Proposed`.

`coord_event`'s signature changed with the move: the free `idem` tuple became
`(event_type, *, problem_id, attempt_id, ...)` with the key read from `COORDINATOR_KEYS`.
Keeping `idem` a parameter would have left the `"claim"`/`"release"` literals at the call
sites, which is the duplication declaring the keys was supposed to remove.

`_instant` was extracted from `validate_lane_event`'s envelope timestamp check (messages
unchanged) so the envelope and every payload moment — `merged_at`, `cooldown_until` — are
one rule rather than three.

Eleven mutations run for Task 6, all killed (table in the plan's new Step 5 — Task 6 had no
verification step). The FIRST anchor failed to match and the harness refused to score it
rather than reporting a pass; that guard is now the reusable part
(`scratchpad/mutate.py` + a per-task spec module), since the same silent no-op already cost
a wasted "verification" in Task 3.

## Task 6 review — two contract gaps (2026-08-03)

**1. `ReviewAborted.stage` was not tied to the lifecycle state.** `_one_of` accepted both
`"proposal"` and `"patch"` from either source state, so a durable `stage="patch"` recorded
from `proposed` — a review that provably never ran — passed validation AND projection.
FR-034's operational streak, which decides whether a Problem cools down, is read straight
off these records.

The write boundary structurally cannot catch it: it sees ONE record, the term is from the
legal vocabulary, and the state it contradicts is not in the record. Only `walk_attempt`
knows the state being left. Fixed there.

Fixed as the CLASS, not the instance — a `if event_type == "ReviewAborted"` branch in the
fold would have left the next multi-source witnessed row unchecked:

- `StateWitness(field, by_state)` is declared ON THE ROW, so the fold looks it up rather
  than branching on a name.
- `_validate_declarations(transitions)` runs AT IMPORT and refuses a malformed table:
  `by_state` must cover `from_states` exactly (add a source state to a witnessed row and
  the fold would otherwise silently stop checking it) and must cover the field's
  write-boundary vocabulary exactly. It takes the table as an ARGUMENT so the rule can be
  exercised against malformed tables — a check run only over the one table that satisfies
  it has no evidence it does anything.
- `events._REVIEW_STAGES` became public `REVIEW_STAGES` and `lifecycle` imports it, so the
  `_one_of` set and the state map are ONE declaration. Two copies drift into a `stage` the
  validator accepts and the fold refuses — which does not reject the append, it WEDGES
  every later projection of the Attempt it landed on.
- `test_every_multi_source_transition_has_DECIDED_about_a_state_witness` enumerates all 7
  multi-source rows and requires each be witnessed or explicitly listed. The near miss is
  `ClaimExpired.reason`: it looks like a discriminator, but both values are possible from
  all four claim-holding states, so it names the CAUSE, not the source.

*Test helpers had to change too.* A witness term depends on the SOURCE state, so
`attempt_event` cannot supply it the way it supplies `claim_generation`. Without that,
`drive(REVIEW_ABORTED)` yields a history the fold refuses for a MISSING `stage` — which
still satisfies a `pytest.raises` looking for "already terminal", i.e. two existing grid
tests would have kept passing for the wrong reason. `build_history` is now the ONE
state-tracking builder; `drive`, the random walks, and `_history` all route through it.

**2. Spec/code divergence on `Cooldown` — and the blind spot that hid it.** The spec table
declared `Cooldown` AND `OperationalCooldown`; the code declares only `Cooldown` with
`cause` as the discriminator (which rev 18 had already put in the idempotency key). The
unified form is right — two schemas for one record is a Constitution I duplication — but
until now it was a PLAN decision contradicting a normative table.

The reason nothing caught it: the drift test excludes `‡` rows because they are not Attempt
transitions, and excluding the COLUMNS silently excluded the NAMES. Extending the check
found a SECOND divergence the review did not mention — `PromotionReenabled (manual)` also
names no record; the coordinator event that re-enables promotion after a breaker is slice
1A's `PromotionEnabledSet`.

- Spec amended to **rev 25**: one `Cooldown` row, and `PromotionEnabledSet (manual
  re-enable)`.
- `parse_spec_transitions` returns every `‡` row's event name as a third element;
  `test_every_non_attempt_row_names_a_record_something_can_WRITE` checks it against
  `KNOWN_EVENT_TYPES_V1`. `PublishRequested→Published` is excluded explicitly (it names the
  publish SAGA, not one event type) so a future non-literal cell forces a decision.
- `_event_name` strips a trailing parenthetical GLOSS, scoped to the Event column — a `‡`
  row's From cell is a prose condition that is itself parenthesised, and stripping there
  would erase it.
- Verified non-vacuous by restoring BOTH old spec strings one at a time: each fails the new
  test, spec sha256-restored after.

14 lifecycle mutations now (10 + 4 new), all killed.
