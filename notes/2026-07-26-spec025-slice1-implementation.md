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

**Do not re-commit `notes/2026-07-15-issue-1139-audit-T+7min.md`.** It is unrelated user
work that was untracked at session start; `8097c5b183` swept it in and `git rm --cached`
put it back to untracked (contents never inspected or altered). It is still in that
commit's history — if the branch is squashed or rebased at PR time, confirm it does not
reappear in the tree.
