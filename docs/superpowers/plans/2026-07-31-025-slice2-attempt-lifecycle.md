# Self-Improvement Lane — Slice 2: Attempt Lifecycle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Attempt lifecycle a durable, executable state machine — the transition table as DATA with a fold that fails closed on any illegal history — and give it the four mechanisms rev 22 specified: claim generations, renewable heartbeats with skew-padded expiry, side-effect intents with the four dispositions, and authoritative time. Underneath all four, give the store the capability they actually need: **atomic transactions across the lane ref's subtrees**, so a mutation touching both the claim and an Attempt is one commit and one compare-and-swap. Closes the seam Slice 1B deliberately left open: a proposal review now has somewhere to record its verdict.

**Architecture:** Everything is a projection over the existing append-only lane log — no new store, no new ref. The Attempt machine lives on the per-Problem stream and the claim lives on the coordinator stream, but those streams are SUBTREES OF ONE REF, so a mutation spanning both is a single commit under a single compare-and-swap. Task 2 adds that transaction; every claim/terminal/reclaim path is built on it, which is what removes the crash windows a two-step sequence would need compensating repairs for. Slice 1A's CAS discipline (`append(..., expected_revision, precondition)`) remains the write path for single-stream events, and the terminal-slot precondition still arbitrates a reclaim race. `coordinator.py` is EXTENDED (generations, heartbeats, expiry) rather than shadowed by a parallel claim module.

**Tech Stack:** Python ≥ 3.11; `pytest`; packages `llmxive.self_improvement`. No new third-party dependencies — the model tests are exhaustive table enumeration plus seeded random walks, not `hypothesis` (deterministic, no dep, and reproducible from the seed printed on failure).

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from spec 025 rev 22.

- **The transition table is DATA, declared once (Constitution I).** `TRANSITIONS` in `lifecycle.py` is the single source of truth for from-states, event, to-state, idempotency key, terminal?, counted?. No function re-encodes a transition in an `if` chain; no test hard-codes a table row it could read. The spec's table and `TRANSITIONS` are checked against each other by a test that parses the spec (Task 4, Step 6) — a spec/code drift is a FAILING TEST, not a review finding.
- **Fail closed on any illegal history.** `project_attempt` RAISES on an unknown event type, an out-of-order `seq`, a transition not in the table, or a second terminal. It never ignores, never "best-effort skips". This matches `project_coordinator` (`coordinator.py:40-83`), which is the house pattern.
- **Exactly one terminal per Attempt (FR-035).** Every terminal append is CAS-conditioned on the freshly-rebuilt projection having NO terminal for that Attempt. First writer wins; the loser discards its own terminal and performs NO further side effect. This guards two DIFFERENT terminals racing, which per-transition idempotency keys do not.
- **Cross-stream preconditions are ENFORCED, because every stream is a subtree of ONE ref.** `lane_log._log_ref` builds `LogRef(ref=LANE_REF, event_dir=…/{problem_id})` — the coordinator and every Problem share `refs/llmxive/self-improvement`, and the module docstring states the consequence: "the single ref serializes all lane mutations (FR-008)". A mutation spanning the coordinator and a Problem is therefore ONE commit under ONE compare-and-swap (`append_many`, Task 2), and a predicate that reads the coordinator's `claim_generation` while writing an Attempt event is deciding against the exact parent the commit is built on. **Never describe a cross-stream check as advisory or best-effort** — it is binding, and the multi-step sequences that would have needed compensating recovery paths do not exist in this design.
- **All-or-nothing, never a compensating path.** Any operation that changes both the claim and the Attempt (grant, reclaim, terminal-plus-release, promotion-observed) is a single transaction. If a crash can leave one half durable and the other not, the operation is built wrong — fix the transaction, do not add a repair step. Every such operation carries crash tests at each seam (parent fixed, commit built, pushed-but-unacknowledged) asserting the complete transition or none of it, plus an idempotent retry after the last one. The complete set is the **Cross-stream invariant matrix** below; an operation that is not a row there touches exactly one stream.
- **"All or nothing" is about VISIBILITY, and visibility changes at the ref CAS.** Before it, nothing; after it, everything; a retry after a lost acknowledgement is a no-op returning the stored result. A crash AFTER a successful push leaves the transaction fully durable — saying otherwise is not a stronger guarantee, it is a false one, and it would send an implementer looking for a repair path that must not exist. See the matrix's commit-point note.
- **Coordinator effects are DECLARED IN THE TABLE, never written per call site.** `Transition.coordinator_effects` lists the coordinator events a transition emits in the same commit (`("ClaimReleased",)`, or `("MonitorStarted", "ClaimReleased")` for `PromotionObserved`). `cas_attempt_transition` emits exactly what the row declares. `terminal` and `releases_claim` are DERIVED properties, never separately-maintained fields — a transition is terminal iff its `to_state` is in `TERMINAL_STATES`, and it releases iff `"ClaimReleased"` is among its effects. Terminality and release are NOT the same predicate: `PromotionObserved` releases without being terminal, and `Rejected`/`Retained`/`RevertObserved` are terminal without releasing (nobody holds the lane at those points).
- **`last_autonomous_merge_at` is the instant on the LATEST merge event, not a running maximum.** The fold assigns it in `seq` order, so the highest-`seq` `MonitorStarted` wins outright. It is NOT claimed to increase numerically: two runners anchor their clocks independently, so a later-`seq` event can legitimately carry an earlier instant, and asserting numeric monotonicity would be asserting something the clock does not guarantee. `seq` decides — as everywhere else in the lane.
- **`seq` is the SOLE ordering authority (FR-009/FR-036).** Timestamps measure DURATIONS only; any code that sorts by timestamp is a defect. `seq` proves ORDER and proves that a recorded beat exists — it cannot prove that an EXPECTED beat is missing, which needs a trusted duration. So `seq` is not a fallback liveness signal: with no trusted time there is no reclaim, per the fail-closed rule below.
- **Per-Attempt `seq` is strictly increasing, NOT contiguous.** A Problem's stream carries every Attempt on that Problem plus Problem-level events, so one Attempt's events legitimately have gaps. `read()` already validates contiguity for the WHOLE stream (`lane_log._check_continuity`); `project_attempt` must therefore be fed from a complete, continuity-validated stream and enforce only that the filtered `seq` values strictly increase. Re-checking contiguity on the filtered subset would reject every healthy interleaved history.
- **Authoritative time or no lane work (FR-036).** Every recorded instant is authority-derived (GitHub server clock via the `Date` response header, offset sampled at run start and re-measured each `heartbeat_interval`). A run that cannot establish an offset MUST NOT claim, heartbeat, reclaim, or terminalize. Comparing a writer's timestamp against that same writer's clock is the vacuous check rev 22 withdrew — do not reintroduce it.
- **Skew padding always favours the safe error (FR-036).** Reclaim requires `elapsed ≥ claim_expiry + max_clock_skew`; `max_claim_hold_time` and the operational-cooldown floor pad the same way. Padding is NEVER applied in the direction that makes a bound trip sooner.
- **Four dispositions, and `ambiguous` is not a guess (FR-035, rev 22).** An outstanding intent resolves to `landed` / `rejected` / `contained` / `ambiguous`. Pushes are **`contained`** (a late push can still arrive; it is harmless because the namespace is dead). Merges and reverts are **`ambiguous` → quarantine** — expected-`head_sha` constrains which COMMIT merges, never which ACTOR, so it fences nothing. Declaring "did not land" without an externally enforced precondition is forbidden.
- **Reclaim BLOCKS on an unreconciled intent.** `ClaimExpired`'s CAS precondition includes "no `SideEffectRequested` lacking its matching `SideEffectObserved`". A reclaimer facing one MUST reconcile it (or quarantine) and reclaim in a SUBSEQUENT CAS.
- **Policy values are bound to the CLAIM, not read live — and the coordinator record is the ONE authority.** `claim_expiry_s`, `max_claim_hold_time_s`, `max_clock_skew_s`, and `policy_version` are recorded on the coordinator's `ClaimAcquired`, which is where the reclaimer reads them: a reclaimer arrives holding the coordinator's state, not the Attempt's. The Attempt-side `ClaimGranted` written in the SAME transaction carries the identical terms and generation, as the readable record on the Attempt's own timeline — a transaction-level invariant test asserts the two payloads agree field-for-field, and a mismatch is a bug in the writer, never a choice between two sources. A policy edit mid-claim therefore cannot retroactively expire a live run. Same discipline as `bind_attempt_config` (Slice 1A Task 13).
- **Exact policy values (Policy Contract v1, rev 22).** `heartbeat_interval` = 5 min; `claim_expiry` = 15 min; `max_clock_skew` = 5 min; `max_claim_hold_time` = **3 h 40 min** = 220 min = `(45×2) + 10 + 20 + 30 + 30 + 15 + 10 + 15`; quality cap M = 3 → 30-day cooldown; operational K = 5 CONSECUTIVE **AND** ≥ 24 h since `streak_started_at` → 7-day cooldown. `max_claim_hold_time` is DERIVED in code from the named phase constants, never written as a literal 220 (Constitution I — the LLM-call-ceiling row is the precedent).
- **Counted vs uncounted terminals (transition table).** Counted toward the per-Problem quality cap: `impl_failed`, `publish_failed`, `test_failed`, `eval_failed`, `reverted`. NOT counted: `rejected`, `unsupported_scope`, `superseded`, `review_aborted`, `attempt_abandoned`. The two counters never cross-contaminate, in either direction.
- **Attempt state ≠ Problem disposition.** `cooldown` is keyed by `problem_id` and belongs to the Problem, not the Attempt. Two enums, no shared namespace — collapsing them is how a per-Problem rest gets misread as an Attempt outcome.
- **Default-off.** The lifecycle driver is gated by `LLMXIVE_SELF_IMPROVEMENT_ENABLED` (default off). No scheduler lane is registered in this slice. Distinct from `LLMXIVE_SELF_IMPROVEMENT_LIVE` (FR-029, slice 6) — that one gates live merges to `main`; this one gates the lane running at all.
- **No external side effects in this slice.** No GitHub call, no push, no merge. Intents and dispositions are lane-log logic exercised through a `Reconciler` Protocol test double with real logic. The publisher/promotion domains arrive in slices 3–4.
- **Real tests, no mocks (Constitution III).** Real temp-git repos, the real lane log, real CAS. Protocol test doubles implementing real logic are fine; `unittest.mock` is not the primary path. The one network-touching test (`GitHubDateClock` against `api.github.com`) lives in `tests/real_call` and is skipped without `LLMXIVE_REAL_TESTS=1`.
- **Behavior-preserving for existing callers.** The full non-slow suite (`pytest tests/unit tests/contract tests/integration -m "not slow"`) MUST stay green after every task.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push** — rebase onto `origin/main` at PR time only. Commit explicit paths (`git commit -o <path>`), never `git add -A`: six untracked pipeline artifacts live in the tree and must not be swept.

## Cross-stream invariant matrix

Every operation that touches MORE THAN ONE stream is listed here, and this table is the
contract Tasks 6/7/9/11 implement and Task 12 attacks. An operation not on this list touches
exactly one stream and uses `lane_log.append`. Adding a cross-stream operation later means
adding a row here FIRST — a transaction whose invariants were never written down is how the
half-states this slice exists to eliminate get reintroduced.

Read the columns as: what lands, what is re-checked against the commit's own parent (never a
stale read), what must be true afterwards, and what a crash BEFORE the commit point leaves
behind. That last column is the same for every row on purpose — the identical answer is the
property the design buys.

|# |Operation (task)|Events in the ONE commit, IN ORDER|Precondition, re-evaluated at the parent|Post-state invariant|Crash BEFORE the commit point|
|-|-|-|-|-|-|
|1|**Claim grant** — `cas_claim` (Task 7)|coordinator `ClaimAcquired`; Problem `ClaimGranted`|lane free **AND** the Attempt is `proposal_verified`|the lane is held by exactly `(P,A)`; the Attempt is `claimed`; BOTH records carry the identical generation + terms|neither record; lane free; Attempt still `proposal_verified`|
|2|**Terminal + release** — `cas_attempt_transition` (Task 6)|Problem terminal; coordinator `ClaimReleased`|the Attempt has NO terminal, its state is in `from_states`, **AND** the lane is still held by that exact `(P,A)` pair|exactly one terminal; lane free|neither; Attempt non-terminal; lane still held|
|3|**Reclaim** — `cas_reclaim` (Task 9)|Problem `ClaimExpired`; coordinator `ClaimReleased`|the claim is still held by `(P,A)` AT the observed generation, the Attempt has NO terminal, **AND** it has no unreconciled intent|exactly one terminal (`attempt_abandoned`); lane free; the next claim takes the next generation|neither; Attempt non-terminal; lane still held by the original|
|4|**Promotion observed** — `cas_attempt_transition` (Task 11)|Problem `PromotionObserved`; coordinator `MonitorStarted`; coordinator `ClaimReleased`|the Attempt is `promotion_requested` **AND** the lane is still held by that exact `(P,A)` pair|the Attempt is `monitoring`; it IS in `monitored_attempts`; lane free; `last_autonomous_merge_at` is this event's instant|none of the three; Attempt still `promotion_requested`; lane still held; not monitored|

**The commit point, and what happens after it.** "All or nothing" is a claim about
VISIBILITY, and visibility changes at exactly one instant: the ref compare-and-swap — the
fast-forward push when the log has a remote, the local `update-ref` when it does not. An
earlier draft of this matrix said "a crash at ANY seam leaves no events", which is false
after that instant and contradicted this plan's own `_after_push` test: once the push
succeeds the whole transaction is durable, and only the local acknowledgement is missing.
The honest contract has three parts, and all three are tested (Task 2 Step 3):

- **Before the commit point:** no event of the transaction is visible to any reader. The
  commit object may exist and be unreachable; unreachable is not visible.
- **After the commit point:** EVERY event of the transaction is visible. Never a subset —
  that is what one commit buys.
- **A retry after a lost acknowledgement** (the process died between the successful push
  and its local ref update, or anywhere later) observes its own events already present and
  returns the STORED result with `created=False`, writing nothing and changing nothing.

The third part is what makes the second survivable: a durable transaction whose caller
never learned it landed is indistinguishable, to that caller, from one that never ran — so
the recovery path has to be the ordinary retry, and the retry has to be a no-op. There is
no separate "reconcile a lost acknowledgement" path, for the same reason there is no
compensating release: an operation that needs one is built wrong.

Three consequences the rows encode, which no task may quietly contradict:

- **Row 4 is a cross-stream operation like any other.** It was drafted as a coordinator-only
  append, which would have left the Attempt in `promotion_requested` while the coordinator
  believed it was monitored and the lane free — a claim released for an Attempt that never
  advanced. It writes THREE events, and the two coordinator events are ordered
  `MonitorStarted` then `ClaimReleased` because BOTH fold branches check ownership against
  the current holder: reversed, the release clears the slot and `MonitorStarted` then has no
  owner to match. That is only true because Task 11 ADDS the ownership check to
  `MonitorStarted` — an earlier draft asserted the order was enforced by the release's check
  alone, which is backwards (the release runs while the owner still exists, so the reversed
  order would have folded cleanly and the mutation test would have proved nothing).
- **Rows 2, 3 and 4 all release the claim, so the release is TABLE-DRIVEN, not a special
  case per call site.** `Transition.coordinator_effects` (Task 4) declares which coordinator
  events a transition emits, and `cas_attempt_transition` emits exactly those. No task
  hand-writes "and then release" — that is the duplication Constitution I forbids, and it is
  how row 4 came to be missing a release in the first place.
- **The crash column is identical everywhere because it is enforced identically.** One
  commit, one ref compare-and-swap. Each row's task carries a crash test at
  `_after_parent` and at `_before_ref_update`, and Task 12 re-attacks rows 2 and 3 under
  live contention.

## Task-boundary audit

Every test must be able to FAIL at the task that states it — a test that can only pass once
a later task lands is not a gate, it is a note. The dependency graph was checked
symbol-by-symbol across all thirteen tasks; four references cross a boundary, and all four
are deliberate:

|Reference|Where|Why it is not a forward dependency|
|-|-|-|
|`cas_claim` in Tasks 5, 6|prose + a `coord_event` call-site list|1A already ships it. Task 7 REPLACES it; it is not first created there. Task 6's tests use `seed_claim`, not `cas_claim`, so they do not depend on which version exists.|
|`cas_reclaim` in Task 6|an error-message string in `cas_attempt_transition`|A literal naming the function a caller should use instead. Nothing calls it.|
|`cas_reclaim` in Task 8|one sentence saying it does not exist yet|Task 8 was moved ahead of reclaim precisely so it does not depend on it; the sentence records that.|
|`TRANSITIONS` / `parse_spec_transitions` in Task 1|prose describing what Task 4 will compare, plus one verification command|Task 1 Step 6 already says to defer that command to Task 4 Step 5 if Task 1 runs first, and to note the deferral in the commit body.|

Two boundary defects the audit DID find, both now fixed: `CLAIM_HOLDING_STATES` was
specified inside Task 7 while belonging to Task 4's module (a Task-4 implementer reading
only their own brief would never have written it), and Task 6's claim setup depended on a
`cas_claim` that could not produce a claimed Attempt until Task 7 — resolved by the
`seed_claim` fixture rather than by reordering, since Task 7 needs Task 6's
`cas_attempt_transition` for its own preludes and the dependency runs both ways.

## Dependencies + scope boundary

**Consumes (Slice 1A/1B, already delivered):** `lane_log.append/read/bootstrap_lane_log`, `LaneLogConfig`, `LaneRevisionConflict`, `LaneContention`; `Event`, `derive_event_id`, `validate_lane_event`, `KNOWN_EVENT_TYPES_V1`, `TYPE_VALIDATORS`, `_require`, `_exact_keys`, `_same_attempt`, `payload_field`, `COORDINATOR_STREAM`, `SCHEMA_VERSION`; `LaneCoordinator`, `ClaimOutcome`, `project_coordinator`, `cas_claim`, `cas_release`; `bind_attempt_config`/`require_attempt_config`.

**Produces (consumed by later slices):** `TransactionResult`, `append_transaction`, `append_many`; `AttemptState`, `ProblemDisposition`, `TRANSITIONS`, `project_attempt`, `cas_attempt_transition`, `IllegalTransition`; `AuthoritativeClock`, `TimeSample`, `GitHubDateClock`, `FixedAnchorClock`, `NoTrustedTimeError`; `cas_heartbeat`, `cas_reclaim`, `ClaimTerms`, `assert_lane_consistent`, `LaneInconsistent`; `IntentDisposition`, `record_intent`, `observe_intent`, `unreconciled_intents`, `Reconciler`, `LaneQuarantine`; `problem_cooldown`, `CooldownState`.

**In scope:** the complete machine (every row of the transition table is declared and enforced), the claim mechanics, time, intents, the two counters, monitoring removal, the merge timestamp, and the proposal-stage terminals (`ProposalVerified` / `Rejected` / `ReviewAborted`) that 1B has no home for.

**Out of scope (later slices):** the implementer, the candidate publisher, container testing, evaluation, promotion/revert side effects, discovery + issue ranking. Those transitions are DECLARED in `TRANSITIONS` (so the machine is complete and the model tests exercise it) but no producer drives them in this slice. A transition with no producer is not dead code — it is the contract the next slice implements against.

**Deliberately NOT changed:** `run_proposal_review` and the 1B convergence wiring keep their current signatures; Task 13 adds the terminal write at the ONE call site that already computes the verdict.

## File Structure

- `src/llmxive/git_event_log.py` — **modified**: `TransactionResult`, `append_transaction`, and one shared tree builder (`_commit_events`) that both the single-event and multi-subtree writers call. One responsibility: git-native CAS over an append-only log, now across several subtrees of one ref.
- `src/llmxive/self_improvement/lane_log.py` — **modified**: `append_many`, the lane-level transaction with per-stream expected revisions and one predicate over every touched stream; `list_problem_streams` (a `git ls-tree` over the event dir — "which streams exist" is a question about the ref's tree, so the store answers it).
- `src/llmxive/self_improvement/policy.py` — the Policy Contract v1 constants, derived where the spec derives them. Created in Task 3 (the clock is the first consumer), extended in Task 9 with the phase budgets and counter caps. Imports nothing from the lane, so every other module may depend on it.
- `src/llmxive/self_improvement/clock.py` — `AuthoritativeClock` protocol, `TimeSample`, `GitHubDateClock`, `FixedAnchorClock` (test/CI double with real logic), `NoTrustedTimeError`, `parse_http_date`, `MAX_CLOCK_REGRESSION_S`. One responsibility: producing an instant the whole lane can compare — monotonic, floored, and fail-closed past the tolerance rather than frozen.
- `src/llmxive/self_improvement/lifecycle.py` — `AttemptState`, `ProblemDisposition`, `Transition`, `TRANSITIONS`, `TERMINAL_STATES`, `COUNTED_TERMINALS`, `project_attempt`, `cas_attempt_transition`, `IllegalTransition`. One responsibility: what may legally happen to an Attempt.
- `src/llmxive/self_improvement/intents.py` — `IntentDisposition`, `IntentRecord`, `Reconciler`, `record_intent`, `observe_intent`, `unreconciled_intents`, `LaneQuarantine`. One responsibility: the saga's intent bookkeeping and its four outcomes.
- `src/llmxive/self_improvement/cooldown.py` — `CooldownCause`, `CooldownState`, `problem_cooldown`, `cas_cooldown`. One responsibility: the two independent counters.
- `src/llmxive/self_improvement/coordinator.py` — **modified**: `claim_generation` on `LaneCoordinator`; `ClaimTerms`; `cas_heartbeat`; `cas_reclaim`; `ClaimOutcome.generation`; `MonitorEnded` + `last_autonomous_merge_at` folding; `assert_lane_consistent`/`LaneInconsistent`. No `cas_release_terminal` and no `cas_promotion_observed`: Task 2's transaction makes the state the first would repair unreachable, and the second is what `cas_attempt_transition` plus the table's declared effects already does.
- `src/llmxive/self_improvement/events.py` — **modified**: new event types + validators (vocabulary extension only; `SCHEMA_VERSION` stays 1, per Slice 1A's F7 rule); `MonitorStarted` gains `merged_at`; `_coord_event` becomes the public `coord_event` both `coordinator.py` and `lifecycle.py` build coordinator events with.
- `src/llmxive/self_improvement/__init__.py` — **modified**: exports.
- `specs/025-self-improvement-lane/spec.md` — **modified** (Task 1, rev 23): the store's real shape, terminal-and-release atomicity, and the clock's sampling construction.

---

### Task 1: Spec amendment (rev 23) — the store's real shape, and a clock that survives a clock change

Every prior round amended the spec before implementing against it. This round has a
different cause than the last: rev 22's own text is sound, but the Slice-2 plan drafted
against it rested on a **false premise about the store** — that the coordinator and each
Problem live on separate refs. They are subtrees of ONE ref
([`lane_log.py:70-76`](../../../src/llmxive/self_improvement/lane_log.py#L70-L76)), which
makes cross-stream atomicity available and therefore makes several "honest limits" the
draft was about to write into the spec simply untrue. Land the corrections first so the
code implements a spec that is true about its own substrate.

**Files:**
- Modify: `specs/025-self-improvement-lane/spec.md`
- Modify: `notes/2026-07-26-spec025-slice1-implementation.md`

**Interfaces:** none (documentation).

- [ ] **Step 1: State the store's real shape in FR-035, and make the fencing guarantee binding**

Under the fencing protocol's "Generation-stamped appends" bullet, append:

> **One ref, many subtrees (rev 23).** The coordinator stream and every per-Problem stream
> are SUBTREES of the single authoritative ref `refs/llmxive/self-improvement`, not separate
> refs. A commit may add blobs to several subtrees at once, and the ref compare-and-swap
> covers the whole commit, so any mutation spanning the claim and an Attempt is ONE
> transaction evaluated against ONE parent. The generation check is consequently BINDING,
> not advisory: a predicate that reads the coordinator's current `claim_generation` and
> writes an Attempt event is deciding against the exact parent its commit is built on, so a
> generation that moved underneath loses the CAS and the transaction is recomputed against
> the new tip. This is a genuine fencing token in the single-writer sense — unlike an
> expected-`head_sha` on an external API, which constrains WHICH COMMIT merges and never
> WHICH ACTOR (rev 22). The distinction is the substrate: the lane owns this ref and
> serializes every writer through it; it owns nothing about GitHub's merge endpoint.

- [ ] **Step 2: Make terminal-and-release atomic instead of adding a recovery path**

The reclaim rules cover "claim held, Attempt NOT terminal". A run that wrote its terminal
and then died before `ClaimReleased` would wedge the lane — `ClaimExpired` cannot help,
because it WRITES a terminal and one already exists. The draft plan answered that with a
new `ClaimReleasedByReclaimer` transition. **Do not add that row.** With Step 1's
transaction the gap is not repaired, it is unreachable: the terminal and the release are
committed together or not at all. Add instead, as a note under the transition table:

> **Terminal and release are ONE transaction (rev 23).** Every path that ends an Attempt
> while holding the claim — a normal terminal, and `ClaimExpired` on reclaim — writes the
> Attempt terminal and the coordinator's `ClaimReleased` in a SINGLE commit on the shared
> ref. There is therefore no state in which an Attempt is terminal while its claim is still
> held, and no compensating "release a terminal Attempt's claim" transition exists or is
> needed. A crash at any point leaves either both facts durable or neither. The
> exactly-one-terminal rule is unchanged and still decides a reclaim race: the reclaimer's
> transaction and the original run's terminal contend for the same slot at the same parent,
> and the loser's ENTIRE transaction — terminal and release alike — is discarded.

- [ ] **Step 2b: Add the cross-stream invariant matrix, and mark the table rows that carry
      coordinator effects**

Copy the plan's **Cross-stream invariant matrix** into FR-035 verbatim, immediately after
the note above — it is normative, not commentary: it is the exhaustive list of operations
that touch more than one stream, and an operation absent from it touches exactly one. Copy
its **commit-point note** with it; the three-part durability contract (nothing before the
ref CAS, everything after it, an idempotent retry on a lost acknowledgement) is the part
implementers will reason about during recovery, and stating only "all or nothing" invites
the false reading that a crash after a successful push leaves nothing behind.

Then make the transition table machine-comparable, because a drift test that compares only
event names is what let `PromotionObserved` claim "one coordinator CAS" while the code
released nothing. The six columns stay
(`From|Event|To|Idempotency key|Side effect|Reconciliation`) and the markers stay in the
Event cell. Six edits, all in `specs/025-self-improvement-lane/spec.md:300-331`:

1. **`◇` joins `†` as an effect marker.** `†` = emits the coordinator's `ClaimReleased` in
   the same transaction; `◇` = emits the coordinator's `MonitorStarted`. Amend the
   paragraph above the table, which currently ties `†` to "pre-merge off-ramp" and to
   terminals — no longer true once `PromotionObserved` releases:

   > A marked row emits coordinator events in the SAME transaction as the Attempt
   > transition: `†` a `ClaimReleased`, `◇` a `MonitorStarted`. Marked rows are mostly
   > pre-merge off-ramps, but not only: `PromotionObserved` is `†◇` and is neither an
   > off-ramp nor terminal — the merge has landed and the monitoring window is unattended,
   > so continuing to hold the singleton lane through it would block every other Problem
   > for the length of the window. Some `†` rows are reachable from pre-claim states
   > (`ScopeUnsupported` from `proposal_verified`; `ReviewAborted` from `proposed`), where
   > there is nothing to release and the effect is correctly skipped — the dagger marks
   > "must not leave the lane occupied", not "always mutates the coordinator".

2. **`PromotionObserved` becomes `PromotionObserved †◇`**, its `To` becomes `monitoring`,
   and its Side-effect cell becomes: `one transaction (matrix row 4): MonitorStarted then
   ClaimReleased`. The order is enforced by the fold: BOTH coordinator events check
   ownership against the current holder, so releasing first would leave `MonitorStarted`
   with no owner to match. State the `MonitorStarted` precondition explicitly beside
   `ClaimReleased`'s, since rev 23 is what adds it — monitoring may only begin for the
   Attempt that HOLDS the lane, because a `MonitorStarted` for an Attempt nobody claimed is
   the lane watching a merge it never promoted. Delete the trailing sentence of the
   `_failed` vs `_aborted` paragraph ("`PromotionObserved` merges 'clear active slot' +
   'add to monitoring' into a single coordinator CAS") — it is the sentence that described
   this as coordinator-only.

3. **`From` and `To` cells name states EXACTLY**, so the parser needs no per-row special
   cases. `To`: `rejected (pre-claim)` → `rejected`, `superseded → new Attempt` →
   `superseded`, `monitoring (quarantined)` → `monitoring`, `merged+monitoring` →
   `monitoring` (edit 2). `From`: `BreakerTripped`'s `any pre-merge` → the six states it
   actually means, `proposed/proposal_verified/claimed/implementing/promoting/promotion_requested`
   (that is what `TRANSITIONS` declares, and "any pre-merge" is the phrase under which a
   state could silently be added or dropped); `ClaimExpired`'s long parenthetical (the
   reclaim preconditions) moves to its Reconciliation cell, which already states them.
   Every rider moves to the Side-effect cell, which is prose by design — none of this
   content is lost, it moves to the columns the parser does not read.

   *(Running the parser against the amended table is how the last two of these surfaced;
   they were not in the review's list. Expect the same: run it before assuming the table
   is clean.)*

4. **`Proposed`'s `From` becomes `∅`.** It reads `discovered`, which is a PROBLEM state,
   not an `AttemptState` — `Proposed` is what opens an Attempt, and `TRANSITIONS` gives it
   no from-states for exactly that reason.

5. **Rows that are not Attempt transitions get `‡`**: `ProblemDiscovered`,
   `PublishRequested→Published`, `PromotionReenabled`, `Cooldown`, `OperationalCooldown`,
   `ClaimHeartbeat`. They belong in the table — they are real lane transitions — but they
   do not move an Attempt through `TRANSITIONS`, and the parser must exclude them by a
   DECLARED marker rather than by a name list living in a test file, which is the same
   drift in a new place.

6. **A one-line legend under the table** naming all three markers, so the next reader does
   not have to infer them from usage.

7. **`ClaimExpired`'s Side-effect cell drops the generation bump**: `` `ClaimReleased` +
   `claim_generation`++ `` becomes `` `ClaimReleased` (the next `ClaimAcquired` takes the
   next generation) ``. As written it implies a coordinator-side `ClaimExpired` event, and
   a coordinator event type whose only content is a number the next claim computes anyway
   is vocabulary with no reader. Keeping the two streams' vocabularies disjoint is also
   what makes "which stream is this event on?" answerable from the type alone.

A test then parses this table and compares COMPLETE ROWS — from-states, to-state,
idempotency key, and effects — against `TRANSITIONS` in both directions (Task 4). The
column set and the markers are therefore a contract: changing either means updating the
parser in the same commit.

- [ ] **Step 2c: Define `last_autonomous_merge_at` as a projection, not a maximum**

The spec says the field advances monotonically while also saying `seq` — not timestamp —
decides order. Those are different projections and only one can be implemented. Replace the
sentence with:

> `last_autonomous_merge_at` is the merge instant carried by the LATEST (highest-`seq`)
> `MonitorStarted`. It is NOT a running maximum, and it is not asserted to increase
> numerically: two runners anchor their clocks independently against the authority, each
> with its own sampling uncertainty, so a later-`seq` event may legitimately carry an
> earlier instant. `seq` decides, as it does everywhere else in the lane (FR-009). A
> consumer that needs "the latest merge we know of" wants this field; a consumer that needs
> "the newest instant ever recorded" wants a different projection and must derive it,
> because these two answer different questions and conflating them would make the record
> disagree with the event it came from.

- [ ] **Step 3: Correct FR-036's clock construction**

Rev 22 established the GitHub `Date` header as the authority. Its construction is
under-specified in one way that matters: an offset sampled against the LOCAL WALL clock and
re-derived from wall-clock elapsed time inherits every wall-clock discontinuity. A backward
system-clock adjustment (NTP step, a VM resuming, a manual correction) makes emitted
authority time move BACKWARD and can suppress the refresh that would have caught it; a
forward step produces a jump before the next refresh is due. Replace FR-036's sampling
paragraph with:

> **Sampling (rev 23).** The offset is established by bracketing the authority request with
> a MONOTONIC clock (`time.monotonic()`): read `t0`, issue the request, read `t1`, and take
> the authoritative instant to be the `Date` value at the midpoint `(t0+t1)/2`. An RFC 7231
> `Date` names a WHOLE SECOND, so the header for second N means the true instant lay in
> `[N, N+1)`: the anchor is centred at `N + 0.5 s` and the sample's uncertainty is
> `(t1−t0)/2 + 0.5 s`. That 0.5 s is a FLOOR no round trip can beat, and omitting it would
> both bias every anchor half a second early and understate the margin — each in the
> direction of evicting a live holder sooner. Emitted time is additionally floored at the
> highest value already emitted: a refresh installs a new measurement of a remote clock, and
> the elapsed time since the PREVIOUS anchor has already advanced the emitted instant, so a
> new anchor even slightly behind the old one regresses what callers see. That floor is
> BOUNDED by `max_clock_regression` = `max_clock_skew`: while clamped, emitted time stands
> still and every duration the lane derives stands still with it, so an unbounded clamp
> would convert an authority fault into a lane that appears healthy and makes no progress —
> expiry never approaching, cooldowns never maturing. A regression past the bound is not
> imprecision to absorb but an absence of trusted time, and the run therefore does no lane
> work. A sample whose round trip exceeds `max_sample_rtt` (2 s) is
> DISCARDED and retried; a run that cannot obtain a sample inside that bound has no trusted
> time and performs no lane work. Between samples, elapsed time is measured with the
> monotonic clock ONLY — never the wall clock — so emitted authority time is monotonic by
> construction and no system-clock adjustment can move it backward or forward. Refresh
> scheduling uses the same monotonic elapsed measurement, so a clock change cannot suppress
> a refresh. Sample uncertainty is charged against the safety margin: the effective skew
> allowance is `max_clock_skew + sample_uncertainty`, always padding toward NOT evicting a
> live holder.

- [ ] **Step 4: Add the two Policy Contract rows**

```
|`LLMXIVE_SELF_IMPROVEMENT_ENABLED` (new in rev 23)|**Default OFF.** Gates whether the lane runs AT ALL. Distinct from `LLMXIVE_SELF_IMPROVEMENT_LIVE` (FR-029), which gates live merges to `main` at slice 6: a lane can be enabled and still never touch `main`. Off ⇒ the driver is a no-op and no lane event is written.|
|Claim-bound policy (new in rev 23)|`claim_expiry`, `max_claim_hold_time`, `max_clock_skew`, and `policy_version` are RECORDED ON the coordinator's `ClaimAcquired` — the record a reclaimer already holds — and read from there rather than from live policy, so a policy edit mid-claim cannot retroactively expire a live run. The Attempt-side `ClaimGranted` written in the same transaction carries identical terms; the coordinator record is authoritative and the two agreeing is an invariant, not a fallback. Same discipline as the durably-bound per-Attempt limits (FR-033).|
```

Also add `max_sample_rtt` = 2 s and `max_clock_regression` = `max_clock_skew` (5 min,
derived) to the Policy Contract table, beside `max_clock_skew`.

- [ ] **Step 5: Update the rev-22 status line to rev 23**

Prepend a rev-23 summary to the `**Status**:` line in the same cumulative style (newest
first): the store is one ref with per-stream subtrees so cross-stream preconditions are
binding and claim/terminal mutations are single transactions; the compensating
release-a-terminal-Attempt transition was designed and then deleted as unreachable; the
cross-stream invariant matrix is now normative and `PromotionObserved` is one of its rows
(a three-event transaction, not the coordinator-only CAS the table described);
`last_autonomous_merge_at` is defined as the latest merge event's instant rather than a
running maximum; `MonitorStarted` gains an ownership precondition; FR-036's sampling is
monotonic, RTT-bounded, centred on the header's whole-second interval, floored so a refresh
cannot regress emitted time, and fail-closed past `max_clock_regression` so the floor cannot
freeze the lane. Say plainly which of these came from review findings against the PLAN (the
false architectural premise, the coordinator-only promotion, the impossible
crash-at-any-seam claim) rather than from the spec being wrong — and which were genuine spec
defects: the `PromotionObserved` row, the monotonicity claim, the `†` paragraph that tied
claim release to terminals, and the absent bound on clock regression.

- [ ] **Step 6: Verify the table is still well-formed**

Locate the table by its HEADER, not by line numbers — the amendments move it, and a
hard-coded range silently checks the wrong lines:

```bash
python3 -c "
lines=open('specs/025-self-improvement-lane/spec.md').read().split('\n')
start=next(i for i,l in enumerate(lines) if l.startswith('|') and 'Idempotency key' in l)
end=next(i for i in range(start,len(lines)) if not lines[i].strip().startswith('|'))
bad=[(i+1,len(lines[i].split('|'))-2) for i in range(start,end)
     if not set(lines[i].strip())<=set('|- ') and len(lines[i].split('|'))-2!=6]
print('rows with != 6 fields:', bad); assert not bad
print('table rows:', end-start-2)
txt=open('specs/025-self-improvement-lane/spec.md').read()
assert txt.count('(')==txt.count(')'), 'paren delta'
print('OK')
"
```
Expected: `rows with != 6 fields: []`, `table rows: 28`, then `OK`.

Then run the parser itself — the amendment is not done until the drift test can consume it.
This is the same check Task 4's test performs, run early so a table defect is found here
rather than five tasks later:

```bash
python3 -c "
import sys; sys.path.insert(0,'.')
from tests.helpers.lane_lifecycle import parse_spec_transitions
rows=parse_spec_transitions()
print('attempt-transition rows parsed:', len(rows))
assert len(rows)==22, sorted(rows)
assert rows['PromotionObserved'][3]==('MonitorStarted','ClaimReleased'), rows['PromotionObserved']
print('OK')
"
```
Expected: `attempt-transition rows parsed: 22` then `OK`. (Task 4 writes the helper; if
Task 1 runs first, defer this command to Task 4 Step 5 and note it in the commit body —
do not skip it.)

- [ ] **Step 7: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o specs/025-self-improvement-lane/spec.md \
  notes/2026-07-26-spec025-slice1-implementation.md \
  -m "spec(025 rev-23): one-ref transactions, cross-stream matrix, promotion release, clock floor"
git log --oneline -1
```

---

### Task 2: Atomic multi-subtree transactions on the lane ref

This is the foundation the rest of the slice rests on, and it exists because the first draft
of this plan asserted something false: that the coordinator and each Problem live on
SEPARATE refs, making cross-stream atomicity impossible. They do not.
[`lane_log._log_ref`](../../../src/llmxive/self_improvement/lane_log.py#L70-L76) builds
`LogRef(ref=LANE_REF, event_dir=f"self-improvement/events/{problem_id}", …)` — **one ref,
per-stream SUBTREES** — and the module docstring says so outright: "the single ref
serializes all lane mutations (FR-008)."

That changes the design. A git commit can add blobs to several subtrees at once, and
`update-ref <ref> <new> <expected-old>` (or the FF push) compares the WHOLE commit. So a
claim grant, and a reclaim's terminal-plus-release, can each be ONE transaction evaluated
against ONE parent — not a two-step sequence with a compensating recovery path for the
window in between. Generation checks stop being advisory: the predicate reads the
coordinator subtree and the Problem subtree at the exact common parent the commit is built
on, so a stale generation is REJECTED, not merely noticed.

**Files:**
- Modify: `src/llmxive/git_event_log.py`
- Modify: `src/llmxive/self_improvement/lane_log.py`
- Test: `tests/integration/test_git_event_log_transaction.py`
- Test: `tests/integration/test_self_improvement_lane_transaction.py`

**Interfaces:**
- Consumes: `LogRef`, `_rev`, `_read_log_at`, `_push_fast_forward`, `sync_and_verify`, `GitLogDenied`, `GitLogError`, `GitLogContention` (all existing, `git_event_log.py`).
- Produces: `TransactionResult(commit, seqs, created)`, `append_transaction(...)` in `git_event_log.py`; `append_many(...)` in `lane_log.py`.

- [ ] **Step 1: Refactor the tree builder to take many events (no behavior change)**

There must be ONE tree builder, not a single-event one and a multi-event copy (Constitution
I). `_append_commit` becomes a thin caller of a list-taking body. Replace the body of
`_append_commit` in `src/llmxive/git_event_log.py` with:

```python
def _write_blob(repo: Path, event: dict) -> str:
    """The canonical body of one event, written to the object store. Runs `hash-object`
    directly (not through `_git`) because the content goes in on stdin; the fixed identity
    env is irrelevant to a pure blob write."""
    proc = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=str(repo), input=_canonical(event), capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip()


def _commit_events(
    repo: Path, log: LogRef, parent: str | None,
    placed: list[tuple[str, dict]], message: str,
) -> str:
    """Build (WITHOUT touching the working tree) ONE commit that adds every event in
    ``placed`` — each a ``(event_dir, event)`` pair — onto ``parent``'s tree.

    Several event_dirs in one commit is the whole point: the lane's coordinator stream and
    its per-Problem streams are SUBTREES OF ONE REF, so a multi-stream mutation is a single
    tree write followed by a single ref compare-and-swap. Splitting it into two commits
    would reintroduce a window in which one half is durable and the other is not — the
    window that needs a compensating recovery path, which is what this exists to delete."""
    entries = [(event_dir, event, _write_blob(repo, event)) for event_dir, event in placed]
    with tempfile.TemporaryDirectory() as td:
        index = str(Path(td) / "index")
        env = {"GIT_INDEX_FILE": index}
        if parent is not None:
            _git(["read-tree", parent], cwd=repo, identity=log.git_identity, extra_env=env)
        for event_dir, event, blob_oid in entries:
            _git(
                ["update-index", "--add", "--cacheinfo",
                 f"100644,{blob_oid},{event_dir}/{event['event_id']}.json"],
                cwd=repo, identity=log.git_identity, extra_env=env,
            )
        tree = _git(["write-tree"], cwd=repo, identity=log.git_identity,
                    extra_env=env).stdout.strip()
    commit_args = ["commit-tree", tree, "-m", message]
    if parent is not None:
        commit_args += ["-p", parent]
    return _git(commit_args, cwd=repo, identity=log.git_identity).stdout.strip()


def _append_commit(
    repo: Path, log: LogRef, parent: str | None, event: dict, message: str
) -> str:
    """One event onto ``parent`` — the single-event case of :func:`_commit_events`."""
    return _commit_events(repo, log, parent, [(log.event_dir, event)], message)
```

- [ ] **Step 2: Run the existing suites to prove the refactor changed nothing**

The credit ledger and slice 1A both append through `_append_commit`; if the refactor altered
tree layout or commit shape, they fail here rather than in a later task.

Run: `python -m pytest tests/integration/test_self_improvement_lane_log.py tests/integration/test_self_improvement_coordinator_cas.py tests/unit/test_model_selection_ledger_transport.py -q`
Expected: green, unchanged.

- [ ] **Step 3: Write the failing transaction tests**

`tests/integration/test_git_event_log_transaction.py`, against real temp-git repos:

```python
"""Multi-subtree transactions on one ref (spec 025 slice 2, Task 2).

Every case here is about ONE question: can an observer ever see half of a transaction?
"""

from __future__ import annotations

import subprocess

import pytest

from llmxive.git_event_log import (
    GitLogDenied,
    GitLogError,
    LogRef,
    append_transaction,
    bootstrap_log,
    read_log,
)

REF = "refs/llmxive/txn-test"


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


def _log(stream: str) -> LogRef:
    return LogRef(ref=REF, event_dir=f"events/{stream}")


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_log(tmp_path, log=_log("coordinator"), message="genesis")
    return tmp_path


def _validate(event: dict) -> None:
    if "event_id" not in event:
        raise ValueError("event_id required")


def _read(repo, stream):
    return read_log(repo, log=_log(stream), validate=_validate)


def _txn(repo, pairs, *, prepare=None, **kw):
    return append_transaction(
        repo, log=_log("coordinator"), streams=["coordinator", "P1"],
        event_dir_for=lambda s: f"events/{s}",
        validate=_validate, message_fn=lambda evs: f"txn of {len(evs)}",
        prepare=prepare or (lambda observed: pairs), **kw,
    )


def test_one_commit_carries_both_streams(repo):
    result = _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})])
    assert result.created is True
    assert [e["event_id"] for e in _read(repo, "coordinator")] == ["c1"]
    assert [e["event_id"] for e in _read(repo, "P1")] == ["p1"]
    # ONE commit, not two: the ref advanced by exactly one.
    log = subprocess.run(["git", "rev-list", "--count", REF], cwd=str(repo),
                         capture_output=True, text=True, check=True).stdout.strip()
    assert log == "2"  # genesis + the transaction


def test_each_stream_gets_its_own_seq_line(repo):
    _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
         finalize=lambda e, seq: {**e, "seq": seq})
    _txn(repo, [("coordinator", {"event_id": "c2"}), ("P1", {"event_id": "p2"})],
         finalize=lambda e, seq: {**e, "seq": seq})
    # Independent 0,1 lines — NOT a shared counter across streams.
    assert [e["seq"] for e in _read(repo, "coordinator")] == [0, 1]
    assert [e["seq"] for e in _read(repo, "P1")] == [0, 1]


def test_two_events_on_the_SAME_stream_in_one_txn_get_consecutive_seqs(repo):
    _txn(repo, [("P1", {"event_id": "a"}), ("P1", {"event_id": "b"})],
         finalize=lambda e, seq: {**e, "seq": seq})
    assert [e["seq"] for e in _read(repo, "P1")] == [0, 1]


def test_seqs_are_keyed_by_stream_AND_id_so_a_shared_id_does_not_collapse(repo):
    # Ids are derived per stream in the lane, but this module cannot assume that. Keyed by
    # id alone, one of these two entries would silently overwrite the other and the caller
    # would be told a position that belongs to the other stream.
    result = _txn(repo, [("coordinator", {"event_id": "same"}), ("P1", {"event_id": "same"})],
                  finalize=lambda e, seq: {**e, "seq": seq})
    assert result.seqs == {("coordinator", "same"): 0, ("P1", "same"): 0}
    assert len(_read(repo, "coordinator")) == len(_read(repo, "P1")) == 1


def test_the_same_id_TWICE_on_one_stream_is_refused(repo):
    # One blob path cannot hold two events: `update-index --cacheinfo` would keep the last
    # while both seqs were consumed, leaving a gap that only surfaces later, elsewhere.
    with pytest.raises(GitLogError, match="twice"):
        _txn(repo, [("P1", {"event_id": "dup"}), ("P1", {"event_id": "dup"})],
             finalize=lambda e, seq: {**e, "seq": seq})
    assert _read(repo, "P1") == []


def test_a_replay_reports_the_STORED_seqs_not_recomputed_ones(repo):
    _txn(repo, [("P1", {"event_id": "a"})], finalize=lambda e, seq: {**e, "seq": seq})
    _txn(repo, [("P1", {"event_id": "filler"})], finalize=lambda e, seq: {**e, "seq": seq})
    again = _txn(repo, [("P1", {"event_id": "a"})], finalize=lambda e, seq: {**e, "seq": seq})
    # The stream is two long now, so a recomputed position would claim seq 2 for an event
    # that has occupied seq 0 since the first call.
    assert again.created is False and again.seqs == {("P1", "a"): 0}


def test_a_successful_push_never_rewinds_a_local_ref_that_moved(repo, bare_remote):
    """The pre-existing `append_to_log` defect, at the seam where it actually occurs.

    The window is between OUR push and OUR local update — not before the push, where a
    competing push would simply lose the fast-forward and force a retry. So the second
    writer completes its entire cycle (sync from the remote, commit on our pushed tip,
    push, update local) inside `_after_push`. Rewinding here would hide its event from
    every local read until the next fetch, and the read that matters is a claim decision."""
    ahead = {}

    def a_second_writer_finishes_first():
        ahead["commit"] = _independent_append(repo, "P1", {"event_id": "other"},
                                              remote=bare_remote)

    result = _txn(repo, [("P1", {"event_id": "ours"})], remote=bare_remote,
                  _after_push=a_second_writer_finishes_first)
    tip = _rev_parse(repo, LANE_REF)
    assert tip == ahead["commit"], "the local ref was rewound past a newer commit"
    assert _is_ancestor(repo, result.commit, tip), "our commit is not reachable locally"
    assert {e["event_id"] for e in _read(repo, "P1")} == {"other", "ours"}


def test_a_crash_after_the_push_leaves_the_transaction_DURABLE(repo, bare_remote):
    """The commit point is the push, so this crash is on the far side of it.

    The two crash tests above (`_after_parent`, `_before_ref_update`) assert ABSENCE
    because they fire before the ref moves. This one must assert PRESENCE. An earlier
    draft of the matrix claimed a crash "at any seam" left nothing — false here, and
    false in the direction that matters: an implementer who believed it would go looking
    for a repair path for events that are already correctly durable."""
    def die():
        raise RuntimeError("runner killed between the push and its local ref update")

    with pytest.raises(RuntimeError, match="runner killed"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             remote=bare_remote, _after_push=die)

    # Locally the ref never moved — the caller has no acknowledgement.
    # On the REMOTE, both events are durable, and BOTH of them: never a subset.
    assert _read_remote(bare_remote, "coordinator") == ["c1"]
    assert _read_remote(bare_remote, "P1") == ["p1"]


def test_a_retry_after_a_LOST_ACKNOWLEDGEMENT_is_a_no_op(repo, bare_remote):
    """The recovery path for the test above — and it is the ORDINARY retry, not a
    reconciler. A durable transaction whose caller never learned it landed is, to that
    caller, indistinguishable from one that never ran, so the retry has to be safe."""
    def die():
        raise RuntimeError("killed")

    pairs = [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})]
    with pytest.raises(RuntimeError):
        _txn(repo, pairs, remote=bare_remote, _after_push=die,
             finalize=lambda e, seq: {**e, "seq": seq})

    again = _txn(repo, pairs, remote=bare_remote,
                 finalize=lambda e, seq: {**e, "seq": seq})
    assert again.created is False, "the retry re-wrote a transaction that had landed"
    assert again.seqs == {("coordinator", "c1"): 0, ("P1", "p1"): 0}
    assert [e["event_id"] for e in _read(repo, "coordinator")] == ["c1"]
    assert [e["event_id"] for e in _read(repo, "P1")] == ["p1"]
    # And the ref advanced exactly once across BOTH calls.
    assert _commit_count(repo, LANE_REF) == _BOOTSTRAP_COMMITS + 1


@pytest.mark.parametrize("writer", ["append_to_log", "append_transaction"])
def test_both_writers_sync_the_local_ref_through_the_same_helper(writer, repo):
    """`_sync_local_ref` is the shared implementation, so it is tested once, directly, for
    the guarantee both writers depend on — and this asserts neither writer kept its own
    bare `update-ref` (the state the fix removes)."""
    import inspect
    from llmxive import git_event_log

    source = inspect.getsource(getattr(git_event_log, writer))
    assert "_sync_local_ref" in source
    assert '"update-ref", log.ref, new_commit]' not in source, "bare update-ref survives"


def test_sync_local_ref_leaves_a_newer_tip_alone_but_fails_on_divergence(repo):
    from llmxive.git_event_log import _sync_local_ref

    parent = _rev_parse(repo, LANE_REF)
    ours = _empty_commit_on(repo, parent)
    newer = _empty_commit_on(repo, ours)          # contains `ours`
    _force_ref(repo, LANE_REF, newer)
    _sync_local_ref(repo, _log(), ours, parent)   # no rewind, no raise
    assert _rev_parse(repo, LANE_REF) == newer

    unrelated = _empty_commit_on(repo, parent)    # does NOT contain `ours`
    _force_ref(repo, LANE_REF, unrelated)
    with pytest.raises(GitLogError, match="diverged"):
        _sync_local_ref(repo, _log(), ours, parent)


def test_the_predicate_sees_every_touched_stream_at_ONE_parent(repo):
    _txn(repo, [("coordinator", {"event_id": "c1", "generation": 1})])
    seen = {}

    def prepare(observed):
        seen.update({k: [e["event_id"] for e in v] for k, v in observed.items()})
        return [("P1", {"event_id": "p1"})]

    _txn(repo, None, prepare=prepare)
    # The Problem-stream write was decided while HOLDING an observation of the coordinator.
    # This is the capability the first draft of this plan wrongly believed impossible.
    assert seen == {"coordinator": ["c1"], "P1": []}


def test_a_prepare_that_denies_writes_nothing(repo):
    def prepare(observed):
        raise GitLogDenied("stale generation")

    with pytest.raises(GitLogDenied, match="stale generation"):
        _txn(repo, None, prepare=prepare)
    assert _read(repo, "coordinator") == [] and _read(repo, "P1") == []


def test_a_crash_after_the_parent_is_fixed_leaves_NO_transition(repo):
    boom = lambda: (_ for _ in ()).throw(RuntimeError("crash: parent fixed"))
    with pytest.raises(RuntimeError, match="parent fixed"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             _after_parent=boom)
    assert _read(repo, "coordinator") == [] and _read(repo, "P1") == []


def test_a_crash_after_the_commit_is_built_leaves_NO_transition(repo):
    # The commit OBJECT exists in the object store but is unreachable: the ref never moved,
    # so no reader can observe it. This is the seam a two-commit sequence could not survive.
    boom = lambda: (_ for _ in ()).throw(RuntimeError("crash: pre ref-update"))
    with pytest.raises(RuntimeError, match="pre ref-update"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             _before_ref_update=boom)
    assert _read(repo, "coordinator") == [] and _read(repo, "P1") == []


def test_a_replay_of_the_whole_transaction_is_an_idempotent_no_op(repo):
    pairs = [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})]
    first = _txn(repo, pairs)
    again = _txn(repo, pairs)
    assert again.created is False and again.commit == first.commit
    assert len(_read(repo, "coordinator")) == 1 and len(_read(repo, "P1")) == 1


def test_a_PARTIALLY_present_transaction_fails_closed(repo):
    # Half the ids already exist. Under the transaction that state is unreachable, so
    # encountering it means something outside the transaction wrote one of them — the log is
    # not what this caller thinks it is. Refuse; never "complete" the missing half.
    _txn(repo, [("coordinator", {"event_id": "c1"})])
    with pytest.raises(GitLogError, match="partially present"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})])
    assert _read(repo, "P1") == []


def test_a_same_id_replay_with_DIFFERENT_content_is_an_append_only_violation(repo):
    _txn(repo, [("coordinator", {"event_id": "c1", "v": 1})])
    with pytest.raises(GitLogError, match="append-only"):
        _txn(repo, [("coordinator", {"event_id": "c1", "v": 2})])


def test_a_concurrent_writer_forces_a_retry_and_the_predicate_re_runs(repo):
    # A barrier at the parent-fixed point lets a foreign event land underneath, so the
    # update-ref CAS must fail and prepare must be re-invoked against the NEW tip.
    calls = []

    def prepare(observed):
        calls.append(len(observed["coordinator"]))
        return [("coordinator", {"event_id": "mine"}), ("P1", {"event_id": "p1"})]

    fired = []

    def interlope():
        if fired:
            return
        fired.append(True)
        append_transaction(
            repo, log=_log("coordinator"), streams=["coordinator"],
            event_dir_for=lambda s: f"events/{s}", validate=_validate,
            message_fn=lambda evs: "foreign", prepare=lambda o: [("coordinator", {"event_id": "foreign"})],
        )

    _txn(repo, None, prepare=prepare, _after_parent=interlope)
    assert calls == [0, 1]  # re-decided against the foreign event, not layered over it
    assert {e["event_id"] for e in _read(repo, "coordinator")} == {"foreign", "mine"}
```

- [ ] **Step 4: Run to verify they fail**

Run: `python -m pytest tests/integration/test_git_event_log_transaction.py -q`
Expected: `ImportError: cannot import name 'append_transaction' from 'llmxive.git_event_log'`.

- [ ] **Step 5: Implement `append_transaction`**

Add to `src/llmxive/git_event_log.py`, and add `"TransactionResult"` and
`"append_transaction"` to `__all__`:

```python
@dataclass(frozen=True)
class TransactionResult:
    """``commit`` is the resulting tip. ``seqs`` maps ``(stream, event_id)`` to the position
    that event was assigned ON THAT STREAM. ``created`` is True iff THIS call moved the ref;
    False means every event was already present with identical content (an idempotent
    replay).

    Keyed by the PAIR, not by ``event_id`` alone: ids are derived per stream
    (``derive_event_id(stream, …)``) but nothing in this module guarantees two streams
    cannot present the same id, and an id-keyed mapping would silently collapse two entries
    into one — reporting a seq for a stream that never got it, and losing the other. The
    key is the identity of a blob's PATH, so that is what the mapping is keyed by."""

    commit: str
    seqs: Mapping[tuple[str, str], int]
    created: bool


def append_transaction(
    repo: Path,
    *,
    log: LogRef,
    streams: Sequence[str],
    event_dir_for: Callable[[str], str],
    validate: Callable[[dict], None],
    message_fn: Callable[[list[dict]], str],
    prepare: Callable[[dict[str, list[dict]]], list[tuple[str, dict]] | None],
    finalize: Callable[[dict, int], dict] | None = None,
    identity_exclude: frozenset[str] = frozenset(),
    _after_parent: Callable[[], None] | None = None,
    _before_ref_update: Callable[[], None] | None = None,
    _after_push: Callable[[], None] | None = None,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> TransactionResult:
    """Append events across SEVERAL subtrees of one ref as a single compare-and-swap.

    This is :func:`append_to_log` generalized along the axis that matters for a log whose
    streams share a ref: ``prepare`` receives EVERY stream in ``streams`` as observed at one
    parent, returns the events to write as ``(stream, event)`` pairs, and all of them land
    in ONE commit under ONE ref CAS. Either the whole set is durable or none of it is —
    there is no interval in which an observer sees half, and therefore nothing to
    compensate for after a crash.

    That property is what makes a cross-stream precondition ENFORCEABLE rather than
    advisory: a predicate that reads the coordinator's current claim generation and then
    writes an Attempt terminal is deciding against the same parent the commit is built on,
    so a generation that changed underneath loses the CAS and the whole transaction is
    recomputed.

    ``prepare`` is re-invoked on every attempt (fresh state per attempt), may return
    ``None`` for an idempotent no-op, and may raise :class:`GitLogDenied` to refuse.
    ``finalize(event, seq)`` receives the position on that event's OWN stream, counting
    events earlier in this same transaction. Ordering within a stream follows the order
    ``prepare`` returned.
    """
    for _attempt in range(max_retries):
        if _attempt:
            time.sleep(random.uniform(0, _RETRY_BACKOFF_S))
        sync_and_verify(repo, log=log)
        # ONE observation of the ref feeds the CAS parent AND every stream's next seq.
        parent = _rev(repo, log.ref, identity=log.git_identity)
        observed = {
            s: _read_log_at(
                repo,
                log=replace(log, event_dir=event_dir_for(s)),
                tip=parent,
                validate=validate,
            )
            for s in streams
        }
        pairs = prepare(observed)          # fresh per attempt; may raise GitLogDenied
        if pairs is None:
            return TransactionResult(parent or _ZERO_OID, {}, created=False)
        for stream, _ in pairs:
            if stream not in observed:
                raise GitLogError(
                    f"transaction wrote to stream {stream!r}, which was not declared in "
                    f"streams={list(streams)!r} — its state was never observed"
                )

        placed: list[tuple[str, dict]] = []
        seqs: dict[tuple[str, str], int] = {}
        used = {s: len(evs) for s, evs in observed.items()}
        for stream, event in pairs:
            built = dict(event)
            if finalize is not None:
                built = finalize(built, used[stream])
            validate(built)
            event_id = str(built["event_id"])
            if not _SAFE_ID.match(event_id):
                raise GitLogError(f"event_id {event_id!r} must match {_SAFE_ID.pattern}")
            # Two events at one path would write one blob: `update-index --cacheinfo`
            # keeps the LAST, so an event would vanish while its seq was still consumed —
            # a silent gap that only surfaces later as a continuity failure in an
            # unrelated read. Reject it where the mistake is, at the same path.
            if (stream, event_id) in seqs:
                raise GitLogError(
                    f"transaction writes {event_id!r} to stream {stream!r} twice — one "
                    "blob path cannot hold two events"
                )
            seqs[(stream, event_id)] = used[stream]
            used[stream] += 1
            placed.append((stream, event_dir_for(stream), built))

        # APPEND-ONLY + all-or-nothing replay. A transaction cannot leave SOME of its ids
        # present, so a mixed result means a writer outside this transaction produced one of
        # them: fail closed rather than "finish" a transaction that was never started.
        present, absent = [], []
        for stream, event_dir, built in placed:
            stored = None if parent is None else _read_event_blob(
                repo, replace(log, event_dir=event_dir), str(built["event_id"]), parent)
            if stored is None:
                absent.append((stream, built))
                continue
            if _identity_body(json.loads(stored), identity_exclude) != _identity_body(
                    built, identity_exclude):
                raise GitLogError(
                    f"event_id {built['event_id']!r} already exists with DIFFERENT content "
                    "(append-only violation) — failing closed"
                )
            present.append((stream, json.loads(stored)))
        if present and not absent:
            # The STORED seq, not the recomputed one: a replay observes a longer stream, so
            # `used[stream]` no longer names the position these events actually occupy.
            landed = {(s, str(b["event_id"])): int(b[SEQ_KEY]) for s, b in present}
            return TransactionResult(parent or _ZERO_OID, landed, created=False)
        if present and absent:
            raise GitLogError(
                f"transaction is partially present: {[b['event_id'] for _, b in present]} "
                f"already committed, {[b['event_id'] for _, b in absent]} absent — refusing "
                "to complete a transaction that was never atomically started"
            )

        if _after_parent is not None:
            _after_parent()  # TEST-ONLY barrier: parent + per-stream seqs are fixed

        new_commit = _commit_events(
            repo, log, parent, [(d, b) for _, d, b in placed],
            message_fn([b for _, _, b in placed]))

        if _before_ref_update is not None:
            _before_ref_update()  # TEST-ONLY: the commit exists but is UNREACHABLE

        if log.remote is not None:
            if _push_fast_forward(repo, log, log.remote, new_commit):
                if _after_push is not None:
                    _after_push()  # TEST-ONLY: durable on the remote, local ref not yet moved
                _sync_local_ref(repo, log, new_commit, parent)
                return TransactionResult(new_commit, seqs, created=True)
            continue
        proc = _git(
            ["update-ref", log.ref, new_commit, parent or _ZERO_OID],
            cwd=repo, identity=log.git_identity, check=False,
        )
        if proc.returncode == 0:
            return TransactionResult(new_commit, seqs, created=True)
    raise GitLogContention(
        f"could not fast-forward {log.ref} after {max_retries} attempts (sustained contention)"
    )
```

Four supporting edits in the same file:

0. **Fix the post-push local-ref rewind — in BOTH writers.** After a successful push,
   `append_to_log` runs `update-ref <ref> <new>` with NO expected-old value
   (`git_event_log.py:684-686`), which SETS the local ref regardless of where it now points.
   Two writers in one clone reach that: A pushes `P→C_A` and stalls before its local update;
   B syncs (local ref `= C_A`), builds `C_B` on it, pushes `C_A→C_B`, and updates local
   (`= C_B`); A then resumes and rewinds the local ref from `C_B` to `C_A`. B's event
   disappears from every local read until the next `sync_and_verify` — and the read that
   matters is a claim decision. It is a pre-existing defect, it is on the path this
   transaction copies, and this slice's whole premise is that the ref is the serialization
   point, so it gets fixed here rather than inherited:

```python
def _sync_local_ref(repo: Path, log: LogRef, commit: str, parent: str | None) -> None:
    """Point the local ref at what we just pushed, WITHOUT rewinding it.

    The CAS is the same one the local-only path uses. Failure is not an error here: the
    push already made ``commit`` durable, so a moved local ref means another writer in this
    clone got ahead of us, and the correct action is to leave their newer tip alone. What
    is NOT acceptable is a local ref that does not contain our commit at all — that is a
    divergence, not a race, and it fails closed."""
    proc = _git(["update-ref", log.ref, commit, parent or _ZERO_OID],
                cwd=repo, identity=log.git_identity, check=False)
    if proc.returncode == 0:
        return
    current = _rev(repo, log.ref, identity=log.git_identity)
    contains = _git(["merge-base", "--is-ancestor", commit, current or _ZERO_OID],
                    cwd=repo, identity=log.git_identity, check=False)
    if current is None or contains.returncode != 0:
        raise GitLogError(
            f"pushed {commit} but the local {log.ref} is {current} and does not contain it "
            "— local and remote have diverged"
        )
```

   `append_to_log` calls `_sync_local_ref(repo, log, new_commit, parent)` in place of its
   bare `update-ref`. One implementation, both writers.

Three more:

1. `from dataclasses import dataclass, field, replace` and
   `from collections.abc import Callable, Mapping, Sequence` at the top.
2. `SEQ_KEY = "seq"` as a module constant, used above — the core does not otherwise name
   the field, and hard-coding the string twice invites a silent divergence from
   `events.SEQ_FIELD`.
3. Lift the append-only body comparison out of `append_to_log`'s closure so both writers
   share ONE implementation (Constitution I):

```python
def _identity_body(doc: dict, identity_exclude: frozenset[str]) -> str:
    """The canonical body used for the append-only comparison, with the fields that are not
    part of an event's semantic identity removed from BOTH sides."""
    if not identity_exclude:
        return _canonical(doc)
    return _canonical({k: v for k, v in doc.items() if k not in identity_exclude})
```

and inside `append_to_log`, delete its local `_identity_body` and call the module-level one
with `identity_exclude` passed through.

- [ ] **Step 6: Run the core transaction tests**

Run: `python -m pytest tests/integration/test_git_event_log_transaction.py -q`
Expected: all pass.

- [ ] **Step 7: Write the lane-level wrapper and its tests**

`lane_log.append_many` gives the lane the same CAS discipline `append` has — per-stream
expected revisions plus one predicate over the whole observation.

```python
def append_many(repo: Path, events: Sequence[Event], *,
                expected_revisions: Mapping[str, int],
                precondition: Callable[[dict[str, list[Event]]], tuple[bool, str]] | None = None,
                config: LaneLogConfig | None = None,
                _after_parent: Callable[[], None] | None = None,
                _before_ref_update: Callable[[], None] | None = None) -> TransactionResult:
    """CAS-append several lane events ACROSS STREAMS as one transaction.

    The lane's streams are subtrees of ONE ref, so a mutation spanning the coordinator and a
    Problem is a single commit and a single compare-and-swap — which is what lets a
    precondition read one stream while writing another and have that read be BINDING.
    ``expected_revisions`` names the revision each touched stream must still be at;
    ``precondition`` sees every touched stream, keyed by stream id, at the common parent.
    Raises :class:`LaneRevisionConflict` when either loses."""
    streams = sorted({e.problem_id for e in events} | set(expected_revisions))
    if not events:
        raise ValueError("append_many requires at least one event")

    def _prepare(observed: dict[str, list[dict]]) -> list[tuple[str, dict]]:
        projected = {}
        for stream, raw in observed.items():
            ordered = _sorted_by_seq(raw)
            _check_continuity(ordered, stream)          # BEFORE any other check
            projected[stream] = [_to_event(r) for r in ordered]
        for stream, expected in expected_revisions.items():
            actual = len(projected[stream])
            if actual != expected:
                raise GitLogDenied(
                    f"stale revision on {stream!r}: expected {expected}, actual {actual}")
        if precondition is not None:
            ok, reason = precondition(projected)
            if not ok:
                raise GitLogDenied(reason)
        return [(e.problem_id, json.loads(event_to_json(e))) for e in events]

    try:
        return append_transaction(
            repo, log=_log_ref(COORDINATOR_STREAM, config), streams=streams,
            event_dir_for=lambda s: _log_ref(s, config).event_dir,
            validate=validate_lane_event, message_fn=_txn_message, prepare=_prepare,
            finalize=_finalize, identity_exclude=_IDENTITY_EXCLUDE,
            _after_parent=_after_parent, _before_ref_update=_before_ref_update,
        )
    except GitLogDenied as exc:
        raise LaneRevisionConflict(str(exc)) from exc


def _txn_message(events: list[dict]) -> str:
    return "self-improvement txn: " + " + ".join(
        f"{e.get('event_type', '?')} {e['event_id']}" for e in events)
```

`_finalize` is reused UNCHANGED: it stamps each event's own scope anchors from its
`problem_id` and nulls the other scope, which
[`events.py:509-511`](../../../src/llmxive/self_improvement/events.py#L509-L511) requires.
Do not widen that rule to let a transaction fill both scopes — the atomicity is carried by
the shared commit, and every event in a transaction is reachable from one tip, so nothing
needs a cross-scope anchor to prove it.

`tests/integration/test_self_improvement_lane_transaction.py` asserts, on real repos:

1. A coordinator event and a Problem event append in one transaction; `read()` on each
   stream returns its own event with `seq == 0` and the correct scope anchors set (and the
   other scope `None`).
2. Both blobs were added by the SAME commit: `git log --format=%H -1` matches
   `result.commit`, and `git show --name-only` lists both paths.
3. A stale `expected_revisions` entry for EITHER stream raises `LaneRevisionConflict` and
   writes nothing to either.
4. A `precondition` reading the coordinator stream and refusing (simulating a stale
   generation) blocks the Problem-stream write.
5. Crash at `_after_parent` and crash at `_before_ref_update`: both streams are unchanged (both seams are BEFORE the commit point).
5b. Crash at `_after_push`: both streams carry their event — the commit point has passed — and the following retry is a no-op returning `created=False`. The lane wrapper inherits this from the core, and inheriting it silently is how a plan comes to state the opposite.
6. A full replay is idempotent — no duplicate events on either stream.
7. A corrupt sequence on ANY touched stream raises `GitLogError` (fail closed) rather than
   `LaneRevisionConflict`, matching `append`'s split.

- [ ] **Step 8: Run the lane transaction tests**

Run: `python -m pytest tests/integration/test_self_improvement_lane_transaction.py -q`
Expected: all pass.

- [ ] **Step 9: Verify the atomicity is load-bearing, not incidental**

The crash tests must FAIL against a non-atomic implementation, or they are decoration.
Temporarily replace `append_many`'s body with two sequential `append` calls, re-run
`tests/integration/test_self_improvement_lane_transaction.py`, and confirm case 5 fails
with the coordinator event durable and the Problem event missing. Restore, re-run, and
confirm `git diff` is empty.

- [ ] **Step 10: Run the full non-slow suite**

This task edits the shared transport under the credit ledger AND slice 1A.

Run: `python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q`
Expected: green.

- [ ] **Step 11: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/git_event_log.py \
  src/llmxive/self_improvement/lane_log.py \
  tests/integration/test_git_event_log_transaction.py \
  tests/integration/test_self_improvement_lane_transaction.py \
  -m "feat(025 slice-2): atomic multi-subtree transactions on the lane ref"
git log --oneline -1
```

---

---
### Task 3: Authoritative clock (FR-036)

Everything downstream is a duration, so this comes early. The design point that makes or
breaks it: **the wall clock is never read.** An offset sampled against local wall time and
re-derived from wall-clock elapsed time inherits every wall-clock discontinuity — a backward
NTP step makes emitted authority time move BACKWARD and can suppress the very refresh that
would catch it. Elapsed time here is measured with `time.monotonic()` only, and the sample
is bracketed so its uncertainty is known rather than assumed.

**Files:**
- Create: `src/llmxive/self_improvement/clock.py`
- Test: `tests/unit/test_self_improvement_clock.py`
- Test: `tests/real_call/test_self_improvement_clock_real.py`

**Interfaces:**
- Consumes: nothing from the lane (deliberately standalone — it is the one module with no lane dependency).
- Produces: `AuthoritativeClock` (Protocol, `__call__() -> str`), `GitHubDateClock`, `FixedAnchorClock`, `NoTrustedTimeError`, `parse_http_date`, `TimeSample`.

**Why a `Callable[[], str]` shape:** `bind_attempt_config` and every other 1A entry point already take `clock: Callable[[], str]`. The authoritative clock satisfies that contract exactly, so it drops into existing call sites without a parallel API (Constitution I).

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_self_improvement_clock.py
"""FR-036 authoritative time. The lane compares durations across independent runners, so
every recorded instant must come from ONE authority — rev 21's check compared a writer's
timestamp against that same writer's clock, which cannot detect skew at all.

The wall clock is never consulted. These tests drive a fake MONOTONIC source; several of
them exist specifically because an earlier draft extrapolated from wall time and would have
emitted a backward-moving 'authoritative' clock on an ordinary NTP correction."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from llmxive.self_improvement.clock import (
    MAX_CLOCK_REGRESSION_S,
    FixedAnchorClock,
    GitHubDateClock,
    NoTrustedTimeError,
    parse_http_date,
)

DATE_HDR = "Fri, 31 Jul 2026 12:00:00 GMT"
LATER_HDR = "Fri, 31 Jul 2026 13:00:00 GMT"
#: One minute behind DATE_HDR — a regression INSIDE `MAX_CLOCK_REGRESSION_S` (300 s), so
#: the clamp absorbs it. The hour-long step is the fail-closed case, not this one.
EARLIER_HDR = "Fri, 31 Jul 2026 11:59:00 GMT"


class Mono:
    """A controllable monotonic source. Real logic: it only ever advances."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        assert seconds >= 0, "a monotonic source cannot go backward"
        self.t += seconds


def _clock(mono, headers, *, rtt=0.0, **kw):
    """A clock whose fetch consumes `headers` and burns `rtt` seconds of monotonic time,
    which is how the bracket sees a round trip at all."""
    seen = []

    def fetch():
        seen.append(1)
        mono.advance(rtt)
        return headers[min(len(seen) - 1, len(headers) - 1)]

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, **kw)
    clock.fetch_count = lambda: len(seen)
    return clock


def test_parse_http_date_yields_an_aware_utc_instant():
    assert parse_http_date(DATE_HDR) == dt.datetime(2026, 7, 31, 12, 0, tzinfo=dt.timezone.utc)


@pytest.mark.parametrize("bad", ["", "not a date", "Fri, 31 Jul 2026", "1753963200"])
def test_parse_http_date_refuses_anything_it_cannot_parse(bad):
    # Fail closed: a silently-wrong anchor poisons every duration in the lane.
    with pytest.raises(NoTrustedTimeError):
        parse_http_date(bad)


def test_the_clock_reports_authority_time_and_tracks_monotonic_elapsed():
    mono = Mono()
    clock = _clock(mono, [DATE_HDR])
    assert clock().startswith("2026-07-31T12:00:00")
    mono.advance(120)
    assert clock().startswith("2026-07-31T12:02:00")


def test_the_sample_is_taken_at_the_ROUND_TRIP_MIDPOINT():
    # A 10 s round trip means the header was true somewhere in that window; the midpoint is
    # the least-wrong estimate, and it is off by at most rtt/2 by construction.
    mono = Mono()
    clock = _clock(mono, [DATE_HDR], rtt=10.0, max_sample_rtt_s=30.0)
    stamped = dt.datetime.fromisoformat(clock())
    # 5 s of the round trip elapsed after the midpoint, so "now" is 12:00:05 — plus the
    # half-second that centres a whole-second header in the interval it names.
    assert stamped == dt.datetime(2026, 7, 31, 12, 0, 5, 500_000, tzinfo=dt.timezone.utc)
    assert clock.sample_uncertainty_s == pytest.approx(5.5)


def test_uncertainty_never_drops_below_the_HEADER_RESOLUTION():
    """A 4 ms round trip does not make the anchor accurate to 2 ms: the header names a
    WHOLE SECOND, so half a second of the estimate is unknowable no matter how fast the
    wire is. Understating it would shrink the reclaim margin, which pads the one way
    FR-036 forbids."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR], rtt=0.004)
    clock()
    assert clock.sample_uncertainty_s == pytest.approx(0.502)
    assert clock.sample_uncertainty_s >= 0.5


def test_the_header_instant_is_CENTRED_not_taken_at_face_value():
    """`Date: 12:00:00` means [12:00:00, 12:00:01). Anchoring at the left edge biases every
    stamp half a second early — always toward `elapsed` looking LARGER, i.e. toward
    evicting a live holder sooner."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR])
    stamped = dt.datetime.fromisoformat(clock())
    assert stamped == parse_http_date(DATE_HDR) + dt.timedelta(milliseconds=500)


def test_a_sample_whose_round_trip_blows_the_budget_is_discarded_and_retried():
    mono = Mono()
    rtts = [30.0, 0.2]

    def fetch():
        mono.advance(rtts.pop(0) if rtts else 0.2)
        return DATE_HDR

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, max_sample_rtt_s=2.0)
    clock()
    assert not rtts, "the over-budget sample was accepted instead of retried"
    assert clock.sample_uncertainty_s <= 1.0


def test_a_clock_that_only_ever_samples_slowly_has_NO_trusted_time():
    mono = Mono()

    def fetch():
        mono.advance(30.0)
        return DATE_HDR

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, max_sample_rtt_s=2.0)
    with pytest.raises(NoTrustedTimeError, match="round trip"):
        clock()


def test_emitted_time_never_moves_backward_across_a_refresh():
    # The authority itself steps BACKWARD by a minute (a load-balanced fleet with a
    # lagging node) — within tolerance, so it is absorbed rather than fatal. Emitted time
    # must not regress: the lane's durations would go negative.
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, EARLIER_HDR], refresh_interval_s=300)
    first = dt.datetime.fromisoformat(clock())
    mono.advance(400)
    second = dt.datetime.fromisoformat(clock())
    assert clock.fetch_count() == 2
    # Held at the floor, not advanced past it: the clamp is a floor on what was EMITTED,
    # and it is the only thing standing between a backward authority step and a negative
    # `since_beat`. Elapsed monotonic time walks out of the clamp on its own.
    assert second == first, f"authority time went backward: {first} -> {second}"
    mono.advance(4000)
    assert dt.datetime.fromisoformat(clock()) > second


def test_a_refresh_that_regresses_by_LESS_than_the_interval_is_still_clamped():
    """The case the 'a refresh only fires after 300 s, so small steps are absorbed'
    argument gets wrong. 300 s of elapsed time has already RAISED the emitted instant by
    300 s, so a new anchor must beat the old one plus 300 s — not merely the old one. A
    one-second backward step regresses emitted time, and only the floor stops it."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, "Fri, 31 Jul 2026 11:59:59 GMT"], refresh_interval_s=300)
    clock()
    mono.advance(299)
    mid = dt.datetime.fromisoformat(clock())     # still the first anchor: ~12:04:59.5
    assert clock.fetch_count() == 1
    mono.advance(2)
    after = dt.datetime.fromisoformat(clock())   # refresh: the authority is 1 s behind
    assert clock.fetch_count() == 2
    # Adopted naively, `after` would be ~11:59:59.5 — FIVE MINUTES behind `mid`, from an
    # authority that moved back by one second. Elapsed time since the new anchor is ~0.
    assert after == mid


def test_a_regression_PAST_THE_TOLERANCE_fails_closed_instead_of_freezing():
    """The clamp's own failure mode, bounded.

    While clamped, emitted time stands still — so expiry stops approaching, hold time
    stops accruing, and cooldowns stop maturing. That is the right trade for a small
    regression and the wrong one for a large one: an unbounded clamp turns an authority
    fault into a lane that looks healthy and makes no progress. Past the tolerance there
    is no trusted time, and FR-036 already says the run does no lane work."""
    mono = Mono()
    clock = _clock(mono, [LATER_HDR, DATE_HDR], refresh_interval_s=300)  # 1 h backward
    first = dt.datetime.fromisoformat(clock())
    mono.advance(400)
    with pytest.raises(NoTrustedTimeError, match="backward"):
        clock()
    # And it does not quietly recover from the poisoned sample: the next call re-samples.
    assert clock.fetch_count() == 2
    assert first is not None


def test_the_regression_tolerance_is_DERIVED_from_the_skew_allowance():
    from llmxive.self_improvement import clock as clock_mod, policy

    assert clock_mod.MAX_CLOCK_REGRESSION_S == policy.MAX_CLOCK_SKEW_S
    src = Path(clock_mod.__file__).read_text()
    assert "MAX_CLOCK_REGRESSION_S = policy.MAX_CLOCK_SKEW_S" in src, (
        "the tolerance must be derived from the skew allowance, not written as a literal")


def test_refresh_scheduling_uses_monotonic_elapsed():
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, LATER_HDR], refresh_interval_s=300)
    clock()
    mono.advance(299)
    clock()
    assert clock.fetch_count() == 1, "re-measured before the interval elapsed"
    mono.advance(2)
    clock()
    assert clock.fetch_count() == 2, "did not re-measure after the interval elapsed"


def test_a_clock_that_cannot_reach_the_authority_raises_and_never_falls_back():
    # The forbidden behavior is silently using the local clock: precisely the untrusted
    # input FR-036 exists to exclude.
    def boom():
        raise OSError("network down")

    with pytest.raises(NoTrustedTimeError):
        GitHubDateClock(fetch_date_header=boom, monotonic=Mono())()


def test_a_stale_anchor_is_not_reused_when_re_measurement_fails():
    mono = Mono()
    headers = [DATE_HDR]

    def fetch():
        if headers:
            return headers.pop()
        raise OSError("network down")

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, refresh_interval_s=300)
    assert clock().startswith("2026-07-31T12:00:00")
    mono.advance(400)
    with pytest.raises(NoTrustedTimeError):
        clock()  # refresh due, refresh failed -> no trusted time, NOT the stale anchor


def test_fixed_anchor_clock_is_a_real_implementation_not_a_stub():
    mono = Mono()
    clock = FixedAnchorClock(anchor=dt.datetime(2026, 7, 31, 12, 0, tzinfo=dt.timezone.utc),
                             monotonic=mono)
    assert clock().startswith("2026-07-31T12:00:00")
    mono.advance(90)
    assert clock().startswith("2026-07-31T12:01:30")
    assert clock.sample_uncertainty_s == 0.0
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


def test_a_real_round_trip_fits_inside_the_sampling_budget():
    # The 2 s max_sample_rtt is only a safe bound if real samples clear it comfortably.
    # The floor here is 0.5 s (the header's whole-second resolution) no matter how fast the
    # network is, so anything under 1.0 s means the round trip contributed under 0.5 s.
    clock = GitHubDateClock()
    clock()
    assert 0.5 <= clock.sample_uncertainty_s < 1.0, (
        f"real GitHub round trip gave +/-{clock.sample_uncertainty_s}s of uncertainty")


def test_the_raw_header_is_what_we_think_it_is():
    raw = GitHubDateClock()._fetch()
    assert parse_http_date(raw).tzinfo == dt.timezone.utc
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/unit/test_self_improvement_clock.py -q`
Expected: collection error, `ModuleNotFoundError: llmxive.self_improvement.clock`.

- [ ] **Step 3a: Create `policy.py` with the timing constants**

The clock is the Policy Contract's first consumer, so the module is born here and Task 9
appends the phase budgets to it. Splitting these across two modules — or letting the clock
keep private copies of `refresh_interval` and `max_sample_rtt` while `policy.py` declares
them again — is the Constitution I violation this plan keeps citing, one file away.

```python
# src/llmxive/self_improvement/policy.py
"""Policy Contract v1 constants, DERIVED where the spec derives them (Constitution I — the
LLM-call-ceiling row is the precedent). ONE module: every bound the lane enforces is read
from here, so a value cannot be edited in one consumer and not another.

Task 9 appends the post-claim phase budgets and the counter caps. This module imports
nothing from the lane, which is what lets `clock.py` depend on it without a cycle."""

MINUTE = 60

HEARTBEAT_INTERVAL_S = 5 * MINUTE
CLAIM_EXPIRY_S = 3 * HEARTBEAT_INTERVAL_S          # tolerate two missed beats
MAX_CLOCK_SKEW_S = 5 * MINUTE
MAX_SAMPLE_RTT_S = 2                                # Policy Contract `max_sample_rtt`
```

- [ ] **Step 3b: Implement the clock**

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

**The local WALL clock is never read.** An anchor is fixed against ``time.monotonic()`` and
every later instant is that anchor plus monotonic elapsed, so a system-clock adjustment —
an NTP step, a resumed VM, a manual correction — can neither move emitted time backward nor
suppress a refresh. The anchor's own uncertainty is measured rather than assumed: the
request is bracketed, the instant is taken at the round-trip midpoint, and a sample whose
round trip exceeds ``max_sample_rtt_s`` is discarded rather than trusted.

``seq`` remains the SOLE ordering authority (FR-009). Nothing here orders events."""

from __future__ import annotations

import datetime as dt
import email.utils
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from llmxive.self_improvement import policy

#: Read from any authenticated response; ``/rate_limit`` is documented as not counting
#: against the rate limit, so a run that has not yet called the API pays nothing for it.
RATE_LIMIT_URL = "https://api.github.com/rate_limit"

#: Policy Contract: re-measure each ``heartbeat_interval`` so a long run cannot drift. The
#: interval IS the heartbeat interval — imported, not restated, because a Policy Contract
#: value written down twice is a Policy Contract with two answers (Constitution I).
DEFAULT_REFRESH_INTERVAL_S = policy.HEARTBEAT_INTERVAL_S

#: Policy Contract ``max_sample_rtt``. A slower round trip means the midpoint estimate is
#: wider than the lane's safety margin can absorb, so the sample is worthless, not merely
#: imprecise.
DEFAULT_MAX_SAMPLE_RTT_S = float(policy.MAX_SAMPLE_RTT_S)

#: Attempts to land a sample inside the RTT budget before declaring no trusted time.
_SAMPLE_ATTEMPTS = 3

#: An RFC 7231 ``Date`` is whole seconds, so a header naming second N was true somewhere in
#: [N, N+1). That is a real uncertainty the anchor inherits no matter how fast the round
#: trip was, and it is the FLOOR on `sample_uncertainty_s` — a lane that treated a 5 ms
#: round trip as ±2.5 ms would be claiming a precision the wire format cannot express.
_HTTP_DATE_RESOLUTION_S = 1.0

#: Centre of that interval. Added to the parsed header so the estimate is unbiased; without
#: it every anchor sits half a second EARLY, which biases toward evicting sooner.
_HTTP_DATE_CENTRE = dt.timedelta(seconds=_HTTP_DATE_RESOLUTION_S / 2)

#: How far the authority may move BACKWARD before the clock stops clamping and fails
#: closed. DERIVED from the skew allowance, not chosen: `max_clock_skew` is already the
#: disagreement the lane tolerates between two clocks, and a clamp of at most that long is
#: absorbed by the same padding every bound is computed with (`elapsed >= claim_expiry +
#: max_clock_skew`). A regression larger than the lane's own tolerance is not imprecision
#: to absorb — it is an authority fault, and freezing lane time behind it would stall
#: expiry, hold time and cooldown maturation for as long as the fault lasted.
MAX_CLOCK_REGRESSION_S = policy.MAX_CLOCK_SKEW_S


class NoTrustedTimeError(RuntimeError):
    """No authority-derived instant is available, so the run performs NO lane work.

    Deliberately fatal rather than degrading to the local clock: a silently-wrong anchor
    poisons every duration the lane derives, and the failure mode is EVICTING A LIVE
    CLAIM-HOLDER. A run that cannot establish time needs no special recovery — the claim it
    does not take cannot wedge, and a claim it already holds is recovered by ordinary
    expiry. Total loss of trusted time therefore PREVENTS reclaim; it never licenses a
    fallback liveness signal, because ``seq`` can show that a beat happened but not that an
    expected one is missing."""


class AuthoritativeClock(Protocol):
    """Satisfies the ``clock: Callable[[], str]`` contract every 1A entry point already
    takes, so this drops in without a parallel time API (Constitution I)."""

    def __call__(self) -> str: ...

    @property
    def sample_uncertainty_s(self) -> float:
        """Half the round trip of the anchoring sample. The reclaimer ADDS this to
        ``max_clock_skew`` so imprecision always pads toward not evicting a live holder."""


@dataclass(frozen=True)
class TimeSample:
    """An authority instant, the monotonic reading it is anchored to, and how wide the
    estimate is. Immutable so a refresh REPLACES the sample rather than mutating half of
    it — a torn update would pair a new instant with an old anchor."""

    instant: dt.datetime
    monotonic_at: float
    uncertainty_s: float


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
    """Authority-derived instants, anchored by a bracketed sample and extrapolated with a
    MONOTONIC source.

    Sampling an anchor (rather than fetching per event) keeps the clock cheap while still
    tracking real elapsed time: the monotonic source measures the interval, the authority
    fixes the origin. Because the monotonic source cannot jump, emitted time is monotonic by
    construction — the property the whole lane's duration arithmetic assumes."""

    def __init__(self, *, fetch_date_header: Callable[[], str] | None = None,
                 monotonic: Callable[[], float] | None = None,
                 refresh_interval_s: int = DEFAULT_REFRESH_INTERVAL_S,
                 max_sample_rtt_s: float = DEFAULT_MAX_SAMPLE_RTT_S) -> None:
        self._fetch = fetch_date_header or _default_fetch
        self._monotonic = monotonic or time.monotonic
        self._refresh_interval_s = refresh_interval_s
        self._max_sample_rtt_s = max_sample_rtt_s
        self._sample: TimeSample | None = None
        #: The highest instant this clock has EMITTED. Not the highest sampled: what the
        #: rest of the lane must never see decrease is what it was told.
        self._floor: dt.datetime | None = None

    @property
    def sample_uncertainty_s(self) -> float:
        """0.0 only before the first sample — and no lane work happens before then, because
        every entry point stamps a time first. After sampling this is never 0: the header's
        one-second resolution alone contributes 0.5 s."""
        return 0.0 if self._sample is None else self._sample.uncertainty_s

    def _take_sample(self) -> TimeSample:
        """One bracketed measurement, retried while the round trip is over budget.

        The stale sample is dropped BEFORE the attempt: "we had time once" is not "we have
        time now", and keeping it would let a failed refresh extrapolate indefinitely from
        an anchor the lane can no longer confirm."""
        self._sample = None
        last = ""
        for _ in range(_SAMPLE_ATTEMPTS):
            start = self._monotonic()
            try:
                header = self._fetch()
            except NoTrustedTimeError:
                raise
            except Exception as exc:  # network, HTTP, DNS — all mean the same thing here
                raise NoTrustedTimeError(f"could not reach the time authority: {exc}") from exc
            end = self._monotonic()
            rtt = end - start
            if rtt > self._max_sample_rtt_s:
                last = f"round trip {rtt:.3f}s exceeds max_sample_rtt {self._max_sample_rtt_s}s"
                continue
            # Two independent uncertainties, and both are charged.
            #
            # (1) The header was true somewhere inside [start, end]; the midpoint is the
            #     least-wrong estimate and is off by at most rtt/2 BY CONSTRUCTION.
            # (2) An RFC 7231 `Date` is WHOLE SECONDS, so "12:00:03" means the real instant
            #     lay in [03.0, 04.0). The centre of that interval is +0.5 s and the
            #     half-width is 0.5 s. Taking the header at face value would bias every
            #     anchor 0.5 s early and understate the error — small, but it is a bias in
            #     the direction of evicting sooner, which is the one direction FR-036
            #     forbids.
            return TimeSample(
                instant=parse_http_date(header) + _HTTP_DATE_CENTRE,
                monotonic_at=(start + end) / 2,
                uncertainty_s=rtt / 2 + _HTTP_DATE_RESOLUTION_S / 2,
            )
        raise NoTrustedTimeError(
            f"no sample inside the budget after {_SAMPLE_ATTEMPTS} attempts: {last}")

    def _now(self) -> dt.datetime:
        sample = self._sample
        if sample is None or (self._monotonic() - sample.monotonic_at) > self._refresh_interval_s:
            sample = self._sample = self._take_sample()
        instant = sample.instant + dt.timedelta(
            seconds=self._monotonic() - sample.monotonic_at)
        # NON-REGRESSING ACROSS REFRESHES, but only up to a BOUND. Within one anchor the
        # monotonic source already guarantees this. Across anchors it does not: a fresh
        # sample is a new measurement of a remote clock, and an authority that moved
        # backward — or simply a sample whose error landed on the other side — installs an
        # origin behind the one already emitted.
        #
        # Clamping is right for a SMALL regression and wrong for a large one. While clamped,
        # emitted time stands still, so every duration the lane derives stands still with
        # it: expiry stops approaching, hold time stops accruing, cooldowns stop maturing.
        # An unbounded clamp therefore converts an authority fault into a silently frozen
        # lane, which is worse than the regression — the lane would look healthy and make no
        # progress. Past the bound this is not a clock with imprecision, it is no trusted
        # time, and FR-036 already says what to do about that.
        if self._floor is not None and instant < self._floor:
            behind = (self._floor - instant).total_seconds()
            if behind > MAX_CLOCK_REGRESSION_S:
                self._sample = None
                raise NoTrustedTimeError(
                    f"the authority moved {behind:.1f}s backward, past the "
                    f"{MAX_CLOCK_REGRESSION_S}s tolerance — refusing to freeze lane time "
                    "behind a clock that cannot be trusted")
            return self._floor
        self._floor = instant
        return instant

    def __call__(self) -> str:
        return self._now().isoformat()


class FixedAnchorClock:
    """A REAL clock anchored to a known instant — for tests and for a runner whose anchor
    was established elsewhere. Not a stub: it runs the SAME extrapolation as
    :class:`GitHubDateClock`, it simply never fetches."""

    def __init__(self, *, anchor: dt.datetime, monotonic: Callable[[], float] | None = None) -> None:
        self._monotonic = monotonic or time.monotonic
        self._sample = TimeSample(instant=anchor, monotonic_at=self._monotonic(),
                                  uncertainty_s=0.0)

    @property
    def sample_uncertainty_s(self) -> float:
        return 0.0

    def __call__(self) -> str:
        elapsed = self._monotonic() - self._sample.monotonic_at
        return (self._sample.instant + dt.timedelta(seconds=elapsed)).isoformat()


__all__ = [
    "DEFAULT_MAX_SAMPLE_RTT_S",
    "DEFAULT_REFRESH_INTERVAL_S",
    "MAX_CLOCK_REGRESSION_S",
    "RATE_LIMIT_URL",
    "AuthoritativeClock",
    "FixedAnchorClock",
    "GitHubDateClock",
    "NoTrustedTimeError",
    "TimeSample",
    "parse_http_date",
]
```

One subtlety the `test_emitted_time_never_moves_backward_across_a_refresh` case pins: a
refresh installs a NEW anchor, and if the fresh sample lands behind the extrapolation
already emitted — the authority moved, or this sample's error simply fell on the other side
of the last one's — naively adopting it regresses emitted time.

An earlier draft argued the regression was "absorbed" because a refresh only fires after
`refresh_interval_s` (300 s) of monotonic elapsed. That reasoning is wrong in the case that
matters: 300 s of elapsed time raises the extrapolated instant by 300 s, so the new anchor
must beat the OLD ANCHOR + 300 s, not the old anchor — a backward step of even one second
regresses the emitted value. The floor in `_now` is therefore an enforced invariant, not an
argument.

The clamp is also BOUNDED, which the same draft missed in the other direction. While
clamped, emitted time stands still — and every duration the lane derives stands still with
it, so expiry stops approaching, hold time stops accruing and cooldowns stop maturing. That
is the right trade for a regression inside `MAX_CLOCK_REGRESSION_S` (derived from
`max_clock_skew`, the disagreement the lane already pads every bound for) and the wrong one
past it, where an unbounded clamp would convert an authority fault into a lane that looks
healthy and makes no progress for as long as the fault lasts. Past the tolerance the clock
raises `NoTrustedTimeError` and drops its sample: this is not imprecision to absorb, it is
no trusted time, and FR-036 already says the run then does no lane work. A regression is
therefore either absorbed and visible as a stall in the stamps, or fatal and visible as a
raise — never silently rewritten backward into the log, where a duration would come out
negative.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/unit/test_self_improvement_clock.py -q`
Expected: all pass.

- [ ] **Step 5: Verify the monotonic discipline is load-bearing**

Temporarily change `_now` to extrapolate from `dt.datetime.now(dt.timezone.utc)` against a
stored wall anchor, re-run, and confirm `test_emitted_time_never_moves_backward_across_a_refresh`
and `test_refresh_scheduling_uses_monotonic_elapsed` FAIL. Restore.

Then, one at a time, restoring after each: delete the `self._floor` clamp and confirm BOTH
regression tests fail; remove the `MAX_CLOCK_REGRESSION_S` bound (clamp unconditionally) and
confirm `test_a_regression_PAST_THE_TOLERANCE_fails_closed_instead_of_freezing` fails —
this is the mutation that reproduces the frozen lane, so it is the one most worth seeing
fail; drop `_HTTP_DATE_RESOLUTION_S` from `uncertainty_s` and confirm
`test_uncertainty_never_drops_below_the_HEADER_RESOLUTION` fails; drop `_HTTP_DATE_CENTRE`
and confirm `test_the_header_instant_is_CENTRED_not_taken_at_face_value` fails. Each of the
four is a separate guarantee, so each needs a test that dies without it. Confirm
`git diff` is empty at the end. A grep guard belongs in the same commit:

```bash
grep -n "datetime.now\|utcnow" src/llmxive/self_improvement/clock.py
```
Expected: no match outside the real-call test — the module must never read wall time.

- [ ] **Step 6: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/clock.py \
  src/llmxive/self_improvement/policy.py \
  tests/unit/test_self_improvement_clock.py \
  tests/real_call/test_self_improvement_clock_real.py \
  -m "feat(025 slice-2): authoritative clock — monotonic elapsed, bracketed sampling (FR-036)"
```

---

### Task 4: The transition table as data + `project_attempt`

**Files:**
- Create: `src/llmxive/self_improvement/lifecycle.py`
- Test: `tests/unit/test_self_improvement_lifecycle_model.py`

**Interfaces:**
- Consumes: `Event`, `payload_field`, `COORDINATOR_STREAM` (Slice 1A).
- Produces: `AttemptState`, `ProblemDisposition`, `Transition`, `TRANSITIONS`, `TERMINAL_STATES`, `COUNTED_TERMINALS`, `OPERATIONAL_TERMINALS`, `CLAIM_HOLDING_STATES`, `project_attempt`, `IllegalTransition`, `legal_events_from`; `tests/helpers/lane_lifecycle.py` with `attempt_event`, `drive`, `parse_spec_transitions`.

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

from tests.helpers.lane_lifecycle import attempt_event, drive  # Task 4 Step 3 helper


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


def test_a_NON_CONTIGUOUS_seq_line_is_legal_because_streams_interleave():
    # A Problem's stream carries other Attempts and Problem-level events, so THIS Attempt's
    # events have gaps. Rejecting gaps would reject every healthy interleaved history.
    history = [attempt_event("Proposed", seq=0), attempt_event("ProposalVerified", seq=7),
               attempt_event("ClaimGranted", seq=40)]
    assert project_attempt(history).state is AttemptState.CLAIMED


@pytest.mark.parametrize("seqs", [(0, 0), (5, 3), (0, 1, 1)])
def test_a_seq_line_that_does_not_STRICTLY_increase_is_refused(seqs):
    events = ["Proposed", "ProposalVerified", "ClaimGranted"][: len(seqs)]
    history = [attempt_event(e, seq=s) for e, s in zip(events, seqs, strict=True)]
    with pytest.raises(IllegalTransition, match="authoritative order"):
        project_attempt(history)


def test_an_unsequenced_event_is_refused():
    # `seq` is stamped by the store inside the CAS, so a None here means the caller built
    # this history from something other than a committed, continuity-validated read.
    with pytest.raises(IllegalTransition, match="authoritative order"):
        project_attempt([attempt_event("Proposed", seq=None)])


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
    """Spec/code drift is a FAILING TEST, not a review finding.

    Compares COMPLETE ROWS in BOTH directions. An event-name-only comparison passes while
    the spec says `PromotionObserved` releases the claim and the code says it does not —
    which is precisely the defect this test exists to catch, so matching names is not
    enough. Every field the spec states is compared: from-states, to-state, idempotency
    key, and the effect markers († releases the claim, ◇ starts monitoring)."""
    from tests.helpers.lane_lifecycle import parse_spec_transitions

    spec_rows = parse_spec_transitions()
    assert spec_rows, "the spec transition table did not parse — the test is vacuous"
    code_rows = {
        t.event: (frozenset(s.value for s in t.from_states), t.to_state.value,
                  t.key_suffix, t.coordinator_effects)
        for t in TRANSITIONS
    }
    assert set(spec_rows) == set(code_rows), (
        f"only in spec: {sorted(set(spec_rows) - set(code_rows))}; "
        f"only in code: {sorted(set(code_rows) - set(spec_rows))}")
    mismatched = {e: (spec_rows[e], code_rows[e]) for e in spec_rows
                  if spec_rows[e] != code_rows[e]}
    assert not mismatched, f"spec/code row mismatch: {mismatched}"


def test_claim_holding_states_are_what_the_table_says():
    """Pins the CURRENT answer, so an accidental table edit shows up in review."""
    assert CLAIM_HOLDING_STATES == {
        AttemptState.CLAIMED, AttemptState.IMPLEMENTING,
        AttemptState.PROMOTING, AttemptState.PROMOTION_REQUESTED,
    }


def test_no_claim_holding_state_is_TERMINAL():
    """Pins the PROPERTY, so a DELIBERATE table edit that breaks the machine still fails
    even when someone updates the test above to match.

    A terminal reachable from `claimed` without releasing would wedge the lane at it: the
    Attempt could never move again and nothing would ever free the claim. That is what the
    derivation is really asserting, and why the set is computed rather than trusted."""
    assert not (CLAIM_HOLDING_STATES & TERMINAL_STATES)


def test_terminal_and_release_are_independent_predicates():
    """Neither derived property may be quietly re-implemented as the other. The two rows
    that prove they are different are the ones a `terminal == releases` shortcut breaks."""
    promo = next(t for t in TRANSITIONS if t.event == "PromotionObserved")
    assert promo.releases_claim and not promo.terminal
    retained = next(t for t in TRANSITIONS if t.event == "Retained")
    assert retained.terminal and not retained.releases_claim
    for t in TRANSITIONS:
        assert t.terminal == (t.to_state in TERMINAL_STATES)
        assert t.releases_claim == ("ClaimReleased" in t.coordinator_effects)
```

`parse_spec_transitions()` lives in the test helper (Step 3) so the parser has ONE
implementation — Task 1 writes the spec rows, this reads them, and nothing else may
re-derive the table's shape:

```python
_MARKER_EFFECTS = {"†": "ClaimReleased", "◇": "MonitorStarted"}

#: Marks a row that is a real lane transition but does NOT move an Attempt through
#: `TRANSITIONS` (Problem-level, coordinator-level, or non-state-changing).
_NOT_AN_ATTEMPT_TRANSITION = "‡"

#: Effect ORDER is fixed by the coordinator fold, not by the order markers happen to appear
#: in the spec cell: MonitorStarted must precede ClaimReleased or the release has no owner
#: to check against. Declaring it once here keeps the spec free of an ordering it should
#: not have to encode.
_EFFECT_ORDER = ("MonitorStarted", "ClaimReleased")

_SPEC = Path("specs/025-self-improvement-lane/spec.md")

SpecRow = tuple[frozenset[str], str, str, tuple[str, ...]]


def parse_spec_transitions() -> dict[str, SpecRow]:
    """Parse spec 025's Attempt transition table into rows comparable with `TRANSITIONS`.

    The spec's six columns are `From | Event | To | Idempotency key | Side effect |
    Reconciliation`; the effect markers live in the Event cell (`†` release, `◇` monitor,
    `‡` not an Attempt transition). Only the four machine-checkable fields come back — the
    last two columns are prose by design and comparing them would make the test a diff.

    A row that does not parse is an ERROR, never a skip. Silently dropping unparseable rows
    is how a drift test ends up comparing an empty set with an empty set and passing."""
    import re

    rows: dict[str, SpecRow] = {}
    inside = False
    for line in _SPEC.read_text().split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and "Idempotency key" in stripped:
            inside = True
            continue
        if not inside:
            continue
        if not stripped.startswith("|"):
            break
        if set(stripped) <= set("|- "):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 6:
            raise AssertionError(
                f"spec transition row has {len(cells)} cells, expected 6: {stripped!r}")
        froms, event_cell, to, key_cell, _side, _recon = cells
        if _NOT_AN_ATTEMPT_TRANSITION in event_cell:
            continue
        effects = tuple(
            name for name in _EFFECT_ORDER
            if name in {_MARKER_EFFECTS[m] for m in event_cell if m in _MARKER_EFFECTS})
        event = _clean(event_cell)
        if not event.isidentifier():
            raise AssertionError(f"unparseable Event cell: {event_cell!r}")
        # `(attempt_id,"promo-obs",head_sha)` → `promo-obs`: the suffix is the only part
        # `TRANSITIONS` carries, because the other elements are values, not declarations.
        key = re.search(r'"([^"]+)"', key_cell)
        if key is None:
            raise AssertionError(f"no quoted idempotency suffix in: {key_cell!r}")
        from_states = frozenset() if _clean(froms) == "∅" else frozenset(
            _clean(f) for f in froms.split("/"))
        rows[event] = (from_states, _clean(to), key.group(1), effects)
    if not rows:
        raise AssertionError(f"no transition rows parsed from {_SPEC} — the test is vacuous")
    return rows


def _clean(cell: str) -> str:
    """Strip markdown emphasis, code ticks, and the effect markers."""
    out = cell
    for junk in ("`", "*", *_MARKER_EFFECTS, _NOT_AN_ATTEMPT_TRANSITION):
        out = out.replace(junk, "")
    return out.strip()
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
from itertools import count
from pathlib import Path
from typing import Any

from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lifecycle import (
    TRANSITIONS,
    AttemptState,
    legal_events_from,
)

TS = "2026-07-31T12:00:00+00:00"

#: Distinguishes "caller said nothing" from "caller said None", which is itself a case the
#: invariant tests must be able to build.
_UNSET: Any = object()

_SEQ = count()


def attempt_event(event_type: str, *, attempt_id: str = "A1", problem_id: str = "P1",
                  payload: dict | None = None, seq: int | None = _UNSET) -> Event:
    """One Attempt event, sequenced the way the store sequences one.

    ``seq`` defaults to the next value from a monotonic counter, so histories built by
    repeated calls satisfy the strictly-increasing invariant `project_attempt` enforces
    without every caller threading positions. Pass ``seq=`` explicitly to build the
    out-of-order and gapped histories the invariant tests need — including ``seq=None``,
    which is why the default is a sentinel rather than ``None``."""
    body = {"problem_id": problem_id, "attempt_id": attempt_id, **(payload or {})}
    return Event(
        event_id=derive_event_id(problem_id, f"{event_type}\x00{attempt_id}"),
        event_type=event_type, problem_id=problem_id, actor="test",
        payload=body, timestamp=TS, attempt_id=attempt_id,
        seq=next(_SEQ) if seq is _UNSET else seq,
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
    key_suffix: str                       # the idempotency key's 2nd element, per the spec
    coordinator_effects: tuple[str, ...]  # the spec table's † and ◇ markers

    @property
    def terminal(self) -> bool:
        """DERIVED, never stored: a second field could disagree with ``to_state``, and the
        one place that must not have two answers is "may anything follow this?"."""
        return self.to_state in TERMINAL_STATES

    @property
    def releases_claim(self) -> bool:
        """Also derived — from the effect list that actually produces the release, so the
        predicate and the write can never disagree. Deliberately NOT a synonym for
        ``terminal``: ``PromotionObserved`` releases without ending the Attempt, and the
        monitoring-phase terminals end it without holding a claim to release."""
        return "ClaimReleased" in self.coordinator_effects


def _t(event: str, froms: tuple[AttemptState, ...], to: AttemptState, key: str,
       *, effects: tuple[str, ...] = ()) -> Transition:
    return Transition(event, frozenset(froms), to, key, effects)


_RELEASES = ("ClaimReleased",)


S = AttemptState

TRANSITIONS: tuple[Transition, ...] = (
    _t("Proposed", (), S.PROPOSED, "proposed"),
    _t("ProposalVerified", (S.PROPOSED,), S.PROPOSAL_VERIFIED, "verified"),
    _t("Rejected", (S.PROPOSED, S.PROPOSAL_VERIFIED), S.REJECTED, "reject"),
    _t("ReviewAborted", (S.PROPOSED, S.IMPLEMENTING), S.REVIEW_ABORTED, "reviewabort",
       effects=_RELEASES),
    _t("ClaimGranted", (S.PROPOSAL_VERIFIED,), S.CLAIMED, "claim"),
    _t("Implementing", (S.CLAIMED,), S.IMPLEMENTING, "impl"),
    _t("ImplementationFailed", (S.CLAIMED, S.IMPLEMENTING), S.IMPL_FAILED, "implfail",
       effects=_RELEASES),
    _t("PublishFailed", (S.IMPLEMENTING,), S.PUBLISH_FAILED, "pubfail", effects=_RELEASES),
    _t("TestingFailed", (S.IMPLEMENTING,), S.TEST_FAILED, "testfail", effects=_RELEASES),
    _t("EvaluationFailed", (S.IMPLEMENTING,), S.EVAL_FAILED, "evalfail", effects=_RELEASES),
    _t("ScopeUnsupported", (S.PROPOSAL_VERIFIED, S.CLAIMED, S.IMPLEMENTING),
       S.UNSUPPORTED_SCOPE, "unsupported", effects=_RELEASES),
    _t("FreshnessStale", (S.CLAIMED, S.IMPLEMENTING), S.SUPERSEDED, "stale",
       effects=_RELEASES),
    _t("EvaluationPassed", (S.IMPLEMENTING,), S.PROMOTING, "eval"),
    _t("PromotionRequested", (S.PROMOTING,), S.PROMOTION_REQUESTED, "promo-req"),
    # Matrix row 4. The claim ends here, not at a terminal: the merge has landed and the
    # monitoring window is unattended, so holding the singleton lane through it would block
    # every other Problem for the whole window. MonitorStarted precedes ClaimReleased
    # because the coordinator fold refuses a release by a non-owner.
    _t("PromotionObserved", (S.PROMOTION_REQUESTED,), S.MONITORING, "promo-obs",
       effects=("MonitorStarted", "ClaimReleased")),
    _t("PromotionAborted", (S.PROMOTION_REQUESTED,), S.PROMOTION_ABORTED, "promo-abort",
       effects=_RELEASES),
    _t("RevertRequested", (S.MONITORING,), S.REVERT_REQUESTED, "revert-req"),
    _t("RevertObserved", (S.REVERT_REQUESTED,), S.REVERTED, "revert-obs"),
    _t("RevertAborted", (S.REVERT_REQUESTED,), S.MONITORING, "revert-abort"),
    _t("Retained", (S.MONITORING,), S.RETAINED, "retain"),
    _t("BreakerTripped",
       (S.PROPOSED, S.PROPOSAL_VERIFIED, S.CLAIMED, S.IMPLEMENTING, S.PROMOTING,
        S.PROMOTION_REQUESTED), S.CIRCUIT_BROKEN, "breaker", effects=_RELEASES),
    # FR-035: the one terminal written by a DIFFERENT run than the one that abandoned it.
    _t("ClaimExpired",
       (S.CLAIMED, S.IMPLEMENTING, S.PROMOTING, S.PROMOTION_REQUESTED),
       S.ATTEMPT_ABANDONED, "claimexpired", effects=_RELEASES),
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


def _claim_holding_states() -> frozenset[AttemptState]:
    """Every state an Attempt can occupy while STILL HOLDING the lane: reachable from
    ``claimed`` without crossing a transition that releases.

    Walked, not listed. A hand-written set goes stale exactly when a phase is inserted
    between `claimed` and the release — the only time it ever changes — and a comment
    calling a hand-written set "derived" is worse than no comment, because it tells the
    next reader not to check."""
    holding, queue = {S.CLAIMED}, deque([S.CLAIMED])
    while queue:
        state = queue.popleft()
        for t in TRANSITIONS:
            if state in t.from_states and not t.releases_claim and t.to_state not in holding:
                holding.add(t.to_state)
                queue.append(t.to_state)
    return frozenset(holding)


#: Consumed by `coordinator.assert_lane_consistent` (Task 7) to decide whether a held claim
#: agrees with its Attempt's own timeline.
CLAIM_HOLDING_STATES: frozenset[AttemptState] = _claim_holding_states()

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
    history the machine could not have produced — an unknown event, an out-of-order ``seq``,
    a transition with no row, or a second terminal.

    ``events`` MUST be this Attempt's events filtered from a COMPLETE Problem stream as
    returned by :func:`lane_log.read`, which has already validated that the stream's ``seq``
    line is gap-free. What is checked here is only that the filtered sequence STRICTLY
    INCREASES: a Problem's stream carries every Attempt on that Problem plus Problem-level
    events, so one Attempt's events are legitimately non-contiguous, and re-checking
    contiguity on the subset would reject every healthy interleaved history. Strictly
    increasing is the real invariant — it catches a caller that concatenated two reads, sorted
    by timestamp, or fed events from a stream whose continuity was never established."""
    if not events:
        raise IllegalTransition("an Attempt projection needs at least its Proposed event")
    state: AttemptState | None = None
    attempt_id = events[0].attempt_id
    generation: int | None = None
    previous_seq = -1
    for position, e in enumerate(events):
        if e.attempt_id != attempt_id:
            raise IllegalTransition(
                f"event {position} belongs to {e.attempt_id!r}, not {attempt_id!r}")
        if e.seq is None or e.seq <= previous_seq:
            raise IllegalTransition(
                f"event {position} of {attempt_id!r} has seq {e.seq!r}, which does not "
                f"follow {previous_seq} — the history is not in authoritative order")
        previous_seq = e.seq
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
    "CLAIM_HOLDING_STATES",
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

### Task 5: Attempt event vocabulary + validators

**Files:**
- Modify: `src/llmxive/self_improvement/events.py`
- Test: `tests/unit/test_self_improvement_events.py` (extend)

**Interfaces:**
- Consumes: `KNOWN_EVENT_TYPES_V1`, `TYPE_VALIDATORS`, `_require`, `_exact_keys`, `_same_attempt`, `_positive_int` (Slice 1A Task 2).
- Produces: the new event types, validated at the write boundary.

- [ ] **Step 1: Write the failing tests**

Extend `tests/unit/test_self_improvement_events.py` with one test per new type asserting (a) a well-formed payload validates, (b) a missing required key raises, (c) an EXTRA key raises (`_exact_keys` house style — extras make the contract untestable), and (d) the envelope `attempt_id` must match the payload's.

**First, the coverage gap.** `KNOWN_EVENT_TYPES_V1` currently holds only four Attempt events (`ProblemDiscovered`, `Proposed`, `ProposalVerified`, `Rejected`). Every OTHER transition in `TRANSITIONS` — `ClaimGranted`, `Implementing`, `ImplementationFailed`, `PublishFailed`, `TestingFailed`, `EvaluationFailed`, `ScopeUnsupported`, `FreshnessStale`, `EvaluationPassed`, `PromotionRequested`, `PromotionObserved`, `PromotionAborted`, `RevertRequested`, `RevertObserved`, `RevertAborted`, `Retained`, `BreakerTripped`, `ReviewAborted`, `ClaimExpired` — must be added, or Task 6's CAS rejects them at the write boundary. Pin it so the two cannot drift:

```python
def test_every_declared_transition_has_a_writable_event_type():
    from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES
    missing = ATTEMPT_EVENT_TYPES - KNOWN_EVENT_TYPES_V1
    assert not missing, f"transitions the store would refuse to write: {sorted(missing)}"
```

**Second, the dual-stream names.** `ClaimGranted`/`ClaimExpired` (Attempt stream) and `ClaimAcquired`/`ClaimReleased` (coordinator stream) describe the same real-world moments from two sides. Neither is a duplicate of the other, and it must be documented at the definition, or a reader will delete one:

> `ClaimGranted`/`ClaimExpired` on a Problem stream are ATTEMPT transitions (they move the Attempt). `ClaimAcquired`/`ClaimReleased` on the coordinator stream are LANE mutations (they move the singleton). Neither is derivable from the other: they live on different STREAMS with independent revision lines, so each needs its own record. They are not independent in TIME, though — the pair is written in one transaction (Task 2), which is why no reconciler ever has to correlate them or handle seeing one without the other.
>
> **No event type appears on both streams.** `ClaimExpired` is an Attempt terminal only; a reclaim's coordinator side is the ordinary `ClaimReleased` every other release writes (rev 23). Rev 22's table implied a coordinator-side `ClaimExpired` carrying a generation bump, which would have been a second event type whose only content — the next generation — the next `ClaimAcquired` computes anyway. Keeping the streams' vocabularies disjoint also means "which stream is this?" is answerable from the event type alone.

Pin it, since the temptation to reuse a name here is exactly what rev 22 gave in to:

```python
def test_no_event_type_lives_on_both_streams():
    from llmxive.self_improvement.coordinator import _COORDINATOR_TYPES
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES
    assert not (ATTEMPT_EVENT_TYPES & _COORDINATOR_TYPES)
```

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

One EXISTING type also changes shape. `MonitorStarted` gains two required keys:
`merged_at` — the instant the promotion it is monitoring was observed, which is what
`last_autonomous_merge_at` folds to — and `problem_id`, without which the fold's new
ownership check (Task 11) cannot compare the PAIR and would fall back to matching an
`attempt_id` alone, the 1A F6 mistake. Its `_MONITOR_KEYS` becomes
`frozenset({"problem_id", "attempt_id", "merged_at"})`, and the five 1A call sites that
construct one (`tests/unit/test_self_improvement_coordinator.py:94-95`,
`tests/unit/test_self_improvement_events.py:325-329`) gain both fields plus a claim so the
ownership check is satisfiable. **Add the fields — do not make them optional.**
`MonitorStarted` has exactly one producer (Task 6's effect builder), which always knows
both; an optional field would exist solely so a record could be written without the value
the coordinator then needs, which is how `last_autonomous_merge_at` would end up `None` for
a merge that demonstrably happened.

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

Also **move `coordinator._coord_event` to `events.coord_event`** (same body, now public) and
have `coordinator.py` import it. Task 6's effect builders construct coordinator events, and
`events.py` is the module that owns event construction and the only one both can import
without a cycle (`coordinator.py` imports `lifecycle` from Task 7 onward). The alternative —
a second deterministic-id builder in `lifecycle.py` — is the duplication Constitution I
forbids, and two builders drifting on id derivation would mint duplicate records of one
decision. Update `coordinator.py`'s two call sites (`cas_claim`, `cas_release`); the
docstring moves with it.

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

### Task 6: `cas_attempt_transition` — the terminal-slot CAS

**Files:**
- Modify: `src/llmxive/self_improvement/lifecycle.py`
- Test: `tests/integration/test_self_improvement_lifecycle_cas.py`

**Interfaces:**
- Consumes: `lane_log.append/append_many/read`, `LaneRevisionConflict`, `derive_event_id`, `project_coordinator`, `COORDINATOR_STREAM`.
- Produces: `cas_attempt_transition(repo, *, problem_id, attempt_id, event_type, payload, actor, clock, config=None) -> AttemptProjection`; `_COORDINATOR_EFFECTS`; `seed_claim` in `tests/helpers/lane_lifecycle.py`.

**A transition emits its declared coordinator effects, atomically.** When the Attempt making
the transition currently holds the lane, `cas_attempt_transition` writes that row's
`coordinator_effects` in the SAME transaction (Task 2). That is not an optimization: writing
them separately creates a window in which an Attempt is terminal while its claim is still
held, and the only repair for that window would be a compensating transition — which spec
rev 23 explicitly declines to add because the transaction makes the window unreachable.
Callers therefore never release a claim by hand; there is one path, and which transitions
release is read from the table rather than re-decided here.

This is the ONE place matrix rows 2 and 4 are implemented — they differ only in what the
row declares. This task builds the mechanism and proves the WRITER: that a row's declared
effects are emitted, in the declared order, in one commit. Task 11 adds the coordinator-side
folding row 4 needs and proves the READER: that the reversed order is rejected, and that the
row's four facts land or none do. Anything that depends on Task 11's ownership check belongs
in Task 11 — a test that cannot fail at its own task is not a gate.

- [ ] **Step 1: Write the failing tests**

Real temp-git repos throughout. The cases:

1. A legal transition appends and advances the projection.
2. An illegal transition raises `LaneRevisionConflict` and appends NOTHING (assert the event count is unchanged — a rejected CAS never writes).
3. Re-invoking the same transition is idempotent: no second event, same projection.
4. **Two different terminals racing**: write `ReviewAborted`, then attempt `ImplementationFailed`; assert the second raises, the log holds exactly one terminal, and the projection still reports the FIRST.
5. The loser's own idempotent replay after losing still raises (it did not land; it must not appear to have).
6. A transition whose `from_states` no longer match because another writer advanced the Attempt raises rather than overwriting.
7. **A terminal by the claim HOLDER frees the lane in one commit** (matrix row 2): seed a claim with `seed_claim` (below), drive the Attempt to a terminal, then assert `project_coordinator(...).active_problem_id is None` AND that both the terminal and the `ClaimReleased` were added by the same commit (`git show --name-only` lists both paths).
8. **A terminal by a NON-holder writes no coordinator event**: with P2/A2 holding the lane, terminalize P1/A1 and assert the coordinator stream is untouched — a terminal must never evict someone else's claim.
9. **A crash between the halves is impossible**: repeat case 7 with `_before_ref_update` raising, and assert the Attempt is NOT terminal and the lane is still held. Neither half landed.
10. **Every declared effect has a builder** (`test_every_declared_effect_has_a_builder`): `{n for t in TRANSITIONS for n in t.coordinator_effects} == set(_COORDINATOR_EFFECTS)`, in both directions — a row naming an effect nobody builds, and a builder no row names, are both drift.
11. **A non-terminal transition that declares an effect still emits it**: `PromotionObserved` is not terminal but releases, so drive P1/A1 to `promotion_requested` while holding the lane, apply it, and assert the lane is free, the Attempt is `monitoring`, and all THREE events share one commit. This is the case a `transition.terminal`-gated release silently skips — the exact defect the matrix was added to prevent.

**The effect ORDER is proved in Task 11, not here.** What makes `MonitorStarted` before
`ClaimReleased` semantically required is the ownership precondition Task 11 adds to the
`MonitorStarted` fold; until it exists, `project_coordinator` accepts either order and a
mutation test would pass against a reversed table, proving nothing. Task 6 asserts the
`seq` order matches the row's declaration (a mechanical property of the writer, true now)
and Task 11 asserts the reversal is REJECTED. Splitting it this way is the point of the
task boundary: each task's tests must be able to fail at that task.

12. **Effects are emitted in the ROW's declared order**: in case 11's commit, the coordinator stream's `MonitorStarted` has a LOWER `seq` than its `ClaimReleased`, and the order of `writes` matches `transition.coordinator_effects` element for element. This pins the WRITER against the table. Whether the fold *rejects* the reversal is Task 11's case.

**Test fixture: `seed_claim`.** Several cases above need an Attempt that genuinely holds the
lane, which at this task nothing can produce: 1A's `cas_claim` writes only the coordinator's
`ClaimAcquired`, so the Attempt would still be `proposal_verified` and no claim-holding
transition would be legal — and Task 7's paired `cas_claim` does not exist yet. Rather than
order Task 6 after Task 7 (which needs `cas_attempt_transition` for its own preludes — the
dependency runs both ways), the tests seed the claim through `append_many` directly, which
Task 2 delivered:

```python
def seed_claim(repo, *, problem_id="P1", attempt_id="A1", generation=1, terms=None):
    """Put the lane in the state a paired claim leaves it in, WITHOUT going through
    `cas_claim`.

    Writes the same two records in the same one commit that Task 7's `cas_claim` will —
    so these tests assert against the claim's SHAPE rather than against whichever version
    of `cas_claim` exists when they run, and Task 7 replacing that function leaves them
    green. It is a fixture, not a second claim API: it takes no preconditions and lives in
    `tests/helpers/`, so nothing in `src/` can reach it."""
```

It writes `Proposed` and `ProposalVerified` on the Problem stream first (via
`cas_attempt_transition`, which this task is building and which needs no claim), then one
`append_many` carrying `ClaimAcquired` + `ClaimGranted`. Task 7's tests use the REAL
`cas_claim`; this fixture exists so Task 6 does not have to.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_lifecycle_cas.py -q`
Expected: `ImportError: cannot import name 'cas_attempt_transition'`.

- [ ] **Step 3: Implement**

```python
def _release_effect(problem_id: str, attempt_id: str, actor: str, timestamp: str) -> Event:
    """The coordinator's release. Carries NO generation: the fencing token advances on
    ``ClaimAcquired`` alone, so putting one here would be a second, unread copy of a
    number with one owner."""
    return coord_event("ClaimReleased", ("release", problem_id, attempt_id),
                        {"problem_id": problem_id, "attempt_id": attempt_id},
                        actor, timestamp, attempt_id)


def _monitor_effect(problem_id: str, attempt_id: str, actor: str, timestamp: str) -> Event:
    """Matrix row 4. ``merged_at`` is this transaction's instant — the SAME clock read the
    Attempt's ``PromotionObserved`` carries, because they are one commit. It is the value
    `last_autonomous_merge_at` folds to, so the coordinator never has to guess when the
    merge it is monitoring actually landed."""
    return coord_event("MonitorStarted", ("monitor", problem_id, attempt_id),
                        {"problem_id": problem_id, "attempt_id": attempt_id,
                         "merged_at": timestamp},
                        actor, timestamp, attempt_id)


#: Keyed by the exact names `Transition.coordinator_effects` uses. A row naming an effect
#: with no builder is caught by `test_every_declared_effect_has_a_builder`, not at runtime
#: in production — the table and this registry are two halves of one declaration.
_COORDINATOR_EFFECTS: dict[str, Callable[[str, str, str, str], Event]] = {
    "ClaimReleased": _release_effect,
    "MonitorStarted": _monitor_effect,
}


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
    if event_type == "ClaimExpired":
        # A reclaim's preconditions (expiry reached, no unreconciled intent, held at the
        # observed generation) are not decorations on this transition — they ARE the
        # reclaim. Reaching it through the generic path would skip them.
        raise IllegalTransition("ClaimExpired is written by cas_reclaim, not by this path")
    events = read(repo, problem_id, config=config)
    coordinator = project_coordinator(read(repo, COORDINATOR_STREAM, config=config))
    event = Event(
        event_id=derive_event_id(problem_id, f"{transition.key_suffix}\x00{attempt_id}"),
        event_type=event_type, problem_id=problem_id, actor=actor,
        payload={"problem_id": problem_id, "attempt_id": attempt_id, **payload},
        timestamp=clock(), attempt_id=attempt_id,
    )
    writes, expected = [event], {problem_id: len(events)}
    # Whatever the ROW declares, emitted in the ROW's order, in this same commit. Checked
    # against the pair, never the problem alone: an earlier Attempt on the same Problem is
    # a non-owner (the 1A F6 guard), and letting it release would evict a live run.
    holds = (coordinator.active_problem_id, coordinator.active_attempt_id) == (
        problem_id, attempt_id)
    if transition.coordinator_effects and holds:
        writes.extend(
            _COORDINATOR_EFFECTS[name](problem_id, attempt_id, actor, event.timestamp)
            for name in transition.coordinator_effects)
        expected[COORDINATOR_STREAM] = coordinator.lane_revision

    def _legal_or_landed(observed: dict[str, list[Event]]) -> tuple[bool, str]:
        evs = observed[problem_id]
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
        if COORDINATOR_STREAM in observed:
            # Re-checked against the SAME parent the commit is built on, so a claim that
            # changed hands while this caller was deciding defeats the release half — and
            # because it is one transaction, it defeats the terminal too.
            now_holding = project_coordinator(observed[COORDINATOR_STREAM])
            if (now_holding.active_problem_id, now_holding.active_attempt_id) != (
                    problem_id, attempt_id):
                return (False, "the claim moved: this Attempt no longer holds the lane")
        return (True, "")

    append_many(repo, writes, expected_revisions=expected, precondition=_legal_or_landed,
                config=config)
    return project_attempt(
        [e for e in read(repo, problem_id, config=config) if e.attempt_id == attempt_id])
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_lifecycle_cas.py -q`
Expected: all pass.

- [ ] **Step 5: Verify both guards are load-bearing**

Temporarily remove the `if current.is_terminal:` branch, re-run, and confirm case 4 FAILS
with two terminals in the log. Restore. Then temporarily split the write into two sequential
`append` calls (terminal, then release), re-run, and confirm case 9 FAILS with a terminal
Attempt whose claim is still held — the wedged state rev 23 says cannot exist. Restore;
confirm an empty `git diff`.

- [ ] **Step 6: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/lifecycle.py \
  tests/helpers/lane_lifecycle.py \
  tests/integration/test_self_improvement_lifecycle_cas.py \
  -m "feat(025 slice-2): terminal-slot CAS — exactly one terminal per Attempt (FR-035)"
```

---

### Task 7: Claim generations + claim-bound terms

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/integration/test_self_improvement_coordinator_cas.py` (extend)

**Interfaces:**
- Produces: `LaneCoordinator.claim_generation`, `ClaimOutcome.generation`, `ClaimOutcome.created`, `ClaimTerms`, `cas_claim(..., terms=)`, `assert_lane_consistent`, `LaneInconsistent`; `list_problem_streams` in `lane_log.py`.
- Consumes: `append_many` (Task 2), `CLAIM_HOLDING_STATES` + `TRANSITIONS` + `project_attempt` (Task 4), `cas_attempt_transition` (Task 6, for the `proposal_verified` preludes).

**`cas_claim` becomes a transaction, and stays the ONE way to claim.** Granting the lane is
two facts — the coordinator's `ClaimAcquired` and the Attempt's `ClaimGranted` — so it is
one `append_many` (Task 2). It is not a second claim API alongside the 1A one: the existing
function is REPLACED in place, because two ways to take the same lock is exactly the
duplication Constitution I forbids, and the older one would be the unsafe path.

- [ ] **Step 1: Write the failing tests**

1. A fresh lane has `claim_generation == 0`; the first `ClaimGranted` makes it 1.
2. `ClaimOutcome.generation` reports it (the field rev 22 deliberately left off until now).
3. Generation is monotonic across claim/release cycles and NEVER resets — three cycles yield 1, 2, 3.
4. `ClaimTerms` (expiry, hold time, skew, policy version) round-trips through the `ClaimGranted` payload and is what a later reader sees, **not** the current module constants: write a claim, then re-read it with different module constants patched in via the injected policy object, and assert the CLAIM's terms win. This is the row Task 1 Step 3 added — a policy edit mid-claim must not retroactively expire a live run.
5. A `ClaimGranted` whose payload omits any term is refused at the write boundary.
6. **Both records land in ONE commit** carrying IDENTICAL terms and generation — assert the two payloads agree field-for-field and that `git show --name-only` on `result.commit` lists both paths. This is the invariant that makes "the coordinator record is authoritative" safe to rely on rather than a coin flip between two sources.
7. **A claim on an Attempt that is not `proposal_verified` is refused**, and writes NOTHING to either stream. The claim is a transition in the table (`proposal_verified → claimed`), so it obeys the table like every other one.
8. **A crash at `_before_ref_update` leaves neither record.** The lane is unclaimed and the Attempt is still `proposal_verified`; a retry then succeeds normally.
9. **A replay after the generation moved on keeps the ORIGINAL generation**: claim P1/A1 (generation 1), release, claim P2/A2 (generation 2), then re-invoke the FIRST `cas_claim` verbatim. It must return `created=False` and `generation == 1` — not raise an append-only violation, not mint a record claiming generation 3, and **not report the coordinator's current 2**. Assert all three fields separately: `created` proves the transaction result was USED rather than discarded, `generation == 1` proves it came from the claim's own record rather than from `LaneCoordinator.claim_generation`, and `acquired is False` proves ownership still reflects now (P2/A2 holds the lane). A return path that re-derives everything from the current projection passes none of these.
9b. **A replay under a DIFFERENT actor is still a no-op**: re-invoke with `actor="runner-b"` where the stored pair says `actor="runner-a"`, and assert `created=False`, no new events, and the stored records STILL name `runner-a`. `actor` is part of an event's identity (`_IDENTITY_EXCLUDE` covers `seq`, `timestamp` and the revision anchors — not `actor`), so rebuilding with the caller's own identity would fail append-only validation. Recovery under a different runner identity is the normal case, not an exotic one: it is what a lost acknowledgement on a dead runner looks like.
9c. **The replay path is exercised through a real lost acknowledgement**, not only by calling twice: kill `cas_claim` at `_after_push`, then re-invoke from a second actor and assert 9b's outcome. Calling twice in one process proves the branch runs; this proves it runs on the state a crash actually leaves.
10. **A replay while the claim is still held is a plain no-op**: same call, same arguments, no new events on either stream, and `ClaimOutcome.acquired` is True.
10b. **A half-present claim raises `LaneInconsistent` rather than being completed**: hand-build (by direct `append`) a coordinator `ClaimAcquired` with no `ClaimGranted`, then invoke `cas_claim` for that pair. It must refuse — reconstructing the missing half from the surviving one would finish a transaction that was never atomically started.
11. **`assert_lane_consistent` accepts a lane written by `cas_claim`** — through a full claim/terminal/release cycle, and while idle, and with several Problems of which one is claimed.
12. **It refuses every half-state, in BOTH directions, in LIVE and COMPLETED claims.** By direct `append` (bypassing the transaction, which is the only way to build these):
    a. a coordinator `ClaimAcquired` with no Attempt-side `ClaimGranted` ⇒ raises;
    b. an Attempt-side `ClaimGranted` with NO coordinator record, **while the coordinator is idle** ⇒ raises. Losing the coordinator half is exactly what makes the lane look idle, so an early return on "idle" reports health precisely when the damage is worst;
    c. **an orphan `ClaimGranted` followed by a terminal** ⇒ raises. The Attempt is in no claim-holding state and the lane is idle, so NOTHING in any projection records that this claim ever existed — only the events do. A state-based checker passes this, which is why the pairing walk is over history;
    d. **a released claim whose `ClaimGranted` was later removed** (restore/hand-repair) ⇒ raises via the orphaned `ClaimAcquired`/`ClaimReleased`, again with no live state to inspect;
    e. **a completed pair whose terms or generation disagree** ⇒ raises. The write-time invariant (Task 7 test 6) is only real if something reads it back, and reading it back only in live claims means it is unchecked for every claim that ever ended;
    f. a `ClaimReleased` with no releasing Attempt transition, and a `MonitorStarted` with no `PromotionObserved` ⇒ raise. Rows 2/3/4 and row 4 respectively — every row that writes to both streams has a case here;
    g. a held claim whose Attempt is `terminal` / `monitoring` / `rejected` ⇒ raises (not merely `proposal_verified`, which was the only state an early draft rejected);
    h. a live coordinator and Attempt at DIFFERENT generations ⇒ raises naming both. Both halves are PRESENT here, so pairing accepts it and only the active-projection check catches it — which is why there are two checks and not one.
13. **It is not vacuous.** With an empty `problem_ids` and a lane carrying an orphaned coordinator record, it still raises (the orphan sweep runs over the coordinator stream regardless of what was scanned) — and `list_problem_streams` on a repo with three Problems returns three ids. A consistency checker that passes on an empty scan is worse than none, so the emptiness is tested rather than assumed.
14. **Every `_PAIRINGS` entry is exercised**: a parameterized test asserts that removing the coordinator partner of each pairing in turn raises, so a rule that is declared but never reachable is a failing test rather than dead configuration. And `{r for p in _PAIRINGS for r in p.rows}` covers every matrix row that writes to both streams — the matrix and the checker cannot drift apart silently.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: `AttributeError: 'LaneCoordinator' object has no attribute 'claim_generation'`.

- [ ] **Step 3: Implement**

- Add `claim_generation: int` to `LaneCoordinator` and to `EMPTY_COORDINATOR` (0).
- In `project_coordinator`, increment it on `ClaimAcquired` — and ONLY there. Never reset: it is the fencing token, and a reset makes two different claims indistinguishable.

  A generation identifies a CLAIM, and a released lane holds none, so a reclaim needs no
  bump of its own — the next `ClaimAcquired` takes the next number either way, and a stale
  worker at generation *g* is already defeated by "the lane is not held by me" before any
  generation is compared. Rev 22's table wrote `ClaimReleased` + `claim_generation`++ in
  the `ClaimExpired` row, which reads as a coordinator-side `ClaimExpired` event; Task 1
  amends that cell, because a second coordinator event type carrying a number the next
  claim would compute anyway is vocabulary with no reader. `ClaimExpired` stays an ATTEMPT
  event (it is the Attempt's terminal); the coordinator sees the ordinary `ClaimReleased`
  that every other release writes, which is also what keeps matrix rows 2, 3 and 4 the same
  shape.
- Add `generation: int` and `created: bool` to `ClaimOutcome`, and delete the docstring paragraph that says the generation field is deferred. Both come from THE CLAIM PAIR this call is about — never from the coordinator's running counter:

```python
@dataclass(frozen=True)
class ClaimOutcome:
    ...  # acquired / owner_problem_id / owner_attempt_id / coordinator unchanged

    #: The generation of the claim THIS call concerns, read from its own `ClaimAcquired`
    #: record. NOT `LaneCoordinator.claim_generation`, which is the counter's current
    #: value: after generation 1 was released and generation 2 granted elsewhere, a replay
    #: of the generation-1 claim must still report 1. The counter cannot answer a question
    #: about a past claim, and answering it from the counter is how a stale worker would be
    #: handed a fencing token that is not its own.
    generation: int

    #: True iff THIS call wrote the records. False for an idempotent replay — including a
    #: retry after a lost acknowledgement, which is the normal recovery path and must be
    #: distinguishable from a fresh grant by callers that log or meter claims.
    created: bool
```

  `_outcome` takes both explicitly (`_outcome(coordinator, problem_id, attempt_id, *, generation, created)`) rather than deriving them, because there is exactly one place each value is known — the transaction's own result and its own event pair — and a helper that guessed would be guessing about the past. `cas_release` (1A) passes the generation of the claim it is releasing and its own `AppendResult.created`.
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

- `cas_claim` gains a required `terms: ClaimTerms` keyword and becomes transactional:

```python
def cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str,
              timestamp: str, terms: ClaimTerms,
              config: LaneLogConfig | None = None) -> ClaimOutcome:
    """Take the singleton lane for ``(problem_id, attempt_id)`` and move that Attempt to
    ``claimed`` — ONE transaction over the coordinator and Problem subtrees.

    The two records are written together because a claim that exists on one stream and not
    the other is not a weaker claim, it is a corrupt one: a coordinator entry with no
    Attempt transition wedges the lane behind an Attempt that never started, and an Attempt
    transition with no coordinator entry lets a second runner claim the same lane."""
    coordinator_events = read(repo, COORDINATOR_STREAM, config=config)
    problem_events = read(repo, problem_id, config=config)
    current = project_coordinator(coordinator_events)
    acquired_id = derive_event_id(
        COORDINATOR_STREAM, f"claim\x00{problem_id}\x00{attempt_id}")
    granted_id = derive_event_id(problem_id, f"claim\x00{attempt_id}")
    stored = (next((e for e in coordinator_events if e.event_id == acquired_id), None),
              next((e for e in problem_events if e.event_id == granted_id), None))
    if all(stored):
        # A REPLAY reuses the STORED PAIR VERBATIM — generation, terms, timestamp, and
        # ACTOR. Two independent reasons, and the second is the one a first draft missed:
        #
        # (1) Recomputing `claim_generation + 1` builds a DIFFERENT body under the SAME id,
        #     which the append-only check rejects as a content violation — turning a
        #     harmless retry into a hard failure, and doing it only once the generation has
        #     advanced, which is exactly when a retry is most likely.
        # (2) `actor` is NOT in `lane_log._IDENTITY_EXCLUDE` (only `seq`, `timestamp` and
        #     the revision anchors are), so it IS part of an event's identity. Recovery
        #     routinely happens under a different trusted runner identity than the one that
        #     first wrote the claim, and rebuilding with the CURRENT caller's actor would
        #     make the cross-runner retry — the whole reason lost acknowledgements are
        #     survivable — fail append-only validation.
        #
        # The id is derived from (problem, attempt), so a second call for the same pair is
        # always a replay: the table forbids re-claiming an Attempt, which is `claimed` or
        # terminal by then, never `proposal_verified` again.
        acquired, granted = stored
    elif any(stored):
        # Exactly one half present, which no transaction could have produced. Refuse here
        # rather than reconstructing the missing half from the surviving one — that would
        # "complete" a transaction that was never atomically started, which is precisely
        # what `append_transaction`'s partial-presence guard exists to prevent.
        raise LaneInconsistent(
            f"claim {problem_id}/{attempt_id} is half-present: "
            f"ClaimAcquired={'yes' if stored[0] else 'no'}, "
            f"ClaimGranted={'yes' if stored[1] else 'no'}"
        )
    else:
        body = {"problem_id": problem_id, "attempt_id": attempt_id,
                "claim_generation": current.claim_generation + 1, **terms.as_payload()}
        acquired = Event(
            event_id=acquired_id,
            event_type="ClaimAcquired", problem_id=COORDINATOR_STREAM, actor=actor,
            payload=body, timestamp=timestamp, attempt_id=attempt_id)
        granted = Event(
            event_id=granted_id,
            event_type="ClaimGranted", problem_id=problem_id, actor=actor,
            payload=dict(body), timestamp=timestamp, attempt_id=attempt_id)

    def _free_and_verified(observed: dict[str, list[Event]]) -> tuple[bool, str]:
        if any(e.event_id == acquired.event_id for e in observed[COORDINATOR_STREAM]):
            return (True, "")                      # idempotent replay of THIS claim
        holder = project_coordinator(observed[COORDINATOR_STREAM])
        if holder.active_problem_id is not None:
            return (False, f"lane occupied by {holder.active_problem_id}/"
                           f"{holder.active_attempt_id}")
        history = [e for e in observed[problem_id] if e.attempt_id == attempt_id]
        if not history or project_attempt(history).state is not AttemptState.PROPOSAL_VERIFIED:
            return (False, f"{attempt_id!r} is not proposal_verified")
        return (True, "")

    result = append_many(repo, [acquired, granted],
                         expected_revisions={COORDINATOR_STREAM: current.lane_revision,
                                             problem_id: len(problem_events)},
                         precondition=_free_and_verified, config=config)
    # Ownership comes from the CURRENT projection — "who holds the lane now" is a question
    # about now. Generation and `created` come from THIS transaction and its own event
    # pair, because they are questions about THIS claim, and after a release-and-regrant
    # the coordinator's counter cannot answer either one. Discarding `result` and
    # re-deriving both from the projection is how a replay would report `created=True`
    # and somebody else's generation.
    return _outcome(project_coordinator(read(repo, COORDINATOR_STREAM, config=config)),
                    problem_id, attempt_id,
                    generation=payload_field(acquired, "claim_generation"),
                    created=result.created)
```

`ClaimTerms.as_payload()` returns the four fields as a dict, and BOTH events embed the same
`body` — one construction, so they cannot drift.

**This changes the 1A coordinator tests, and that is not a weakening.** Those tests claim
from an empty Problem stream, which the table now forbids; each needs a two-event prelude
(`Proposed`, `ProposalVerified`) via `cas_attempt_transition`. Add the prelude — do not relax
the precondition. Assertions about coordinator event COUNTS stay valid, since `_events()`
reads the coordinator stream only.

**Pre-transaction half-states: there are none to migrate, and that is a verified fact, not
an assumption.** 1A's `cas_claim` wrote ONLY the coordinator's `ClaimAcquired`, so a lane it
had ever run would hold exactly the half-state this task fuses: a claim with no
corresponding Attempt transition. It never ran — `git for-each-ref 'refs/llmxive/*'` and
`git ls-remote origin 'refs/llmxive/*'` are both EMPTY as of this plan, because the lane is
default-off and slices 1A/1B have not been merged. There is therefore no data migration,
and writing one would be writing a converter for records that do not exist.

What the slice owes instead is a detector, because "no history exists today" is a fact with
a shelf life and the failure it guards is silent:

The invariant being checked is HISTORICAL — "the events a transaction writes exist together
or not at all" — so the check has to be over the events, not over the state they fold to.
Two drafts got this wrong in the same way. The first returned early when the coordinator was
idle, which made it blind to the orphan it promised to catch (losing the coordinator half of
a claim is exactly what makes the lane look idle). The second scanned only Attempts
CURRENTLY in a claim-holding state, which misses every completed pair: an orphan
`ClaimGranted` followed by a terminal, a `ClaimAcquired` whose grant was removed after the
claim was released, mismatched terms in a historical pair. A restore or a hand repair
produces exactly those, and a current-state fold cannot see any of them — the whole point of
a released claim is that it left no current state behind.

Pairing is checkable directly because **every paired event id is derived, not random.**
`derive_event_id(COORDINATOR_STREAM, f"claim\x00{p}\x00{a}")` and
`derive_event_id(p, f"claim\x00{a}")` are computable from `(problem_id, attempt_id)` alone,
so for any record on one side the id of its partner is known without searching. The check is
therefore a walk over all history, matching by id — and a matrix row's events are its
pairing rule:

```python
@dataclass(frozen=True)
class _Pairing:
    """One matrix row's cross-stream correspondence: which Attempt-side facts demand a
    coordinator partner, how that partner's id is derived, and which payload fields the
    single transaction that wrote both means they must agree on."""

    rows: tuple[int, ...]
    matches: Callable[[Event], bool]
    coordinator_event: str
    coordinator_key: Callable[[str, str], tuple[str, ...]]
    compare: tuple[str, ...]

    def matching(self, history: list[Event]) -> list[Event]:
        return [e for e in history if self.matches(e)]


def _is_type(event_type: str) -> Callable[[Event], bool]:
    return lambda e: e.event_type == event_type


def _releases_the_claim(e: Event) -> bool:
    """Read from the TABLE, so rows 2, 3 and 4 share one rule and a transition that starts
    releasing later is covered without editing this file."""
    transition = _BY_EVENT.get(e.event_type)
    return transition is not None and transition.releases_claim


#: One entry per matrix row that writes to both streams: how to find the coordinator-side
#: partner of an Attempt-side fact, and what makes the pair well-formed. Declared here so
#: adding a cross-stream operation adds a pairing rule in the same edit — the matrix says
#: what must land together, and this is what checks that it did.
_PAIRINGS: tuple[_Pairing, ...] = (
    _Pairing(rows=(1,), matches=_is_type("ClaimGranted"),
             coordinator_event="ClaimAcquired",
             coordinator_key=lambda p, a: ("claim", p, a),
             compare=("claim_generation", "claim_expiry_s", "max_claim_hold_time_s",
                      "max_clock_skew_s", "policy_version")),
    _Pairing(rows=(2, 3, 4), matches=_releases_the_claim,
             coordinator_event="ClaimReleased",
             coordinator_key=lambda p, a: ("release", p, a), compare=()),
    _Pairing(rows=(4,), matches=_is_type("PromotionObserved"),
             coordinator_event="MonitorStarted",
             coordinator_key=lambda p, a: ("monitor", p, a), compare=()),
)

#: Coordinator types that MUST have an Attempt-side partner. Derived from `_PAIRINGS`, so a
#: new pairing brings its orphan check with it. `PromotionEnabledSet` and `MonitorEnded`
#: are deliberately absent — they are not written by a cross-stream transaction, and
#: demanding a partner for them would make the checker reject healthy lanes.
_PAIRED_COORDINATOR_TYPES: frozenset[str] = frozenset(
    p.coordinator_event for p in _PAIRINGS)


def assert_lane_consistent(repo: Path, *, problem_ids: Iterable[str],
                           config: LaneLogConfig | None = None) -> None:
    """Raise `LaneInconsistent` if any cross-stream transaction is half-present in the
    HISTORY, or if the active claim disagrees with its Attempt.

    Two independent checks, because they establish different things and neither implies
    the other:

    1. **Pairing over all history.** For every Attempt-side fact that a matrix row pairs
       with a coordinator record, the partner exists (by derived id) and agrees on the
       fields the row says are shared; and every coordinator claim/release/monitor record
       is consumed by exactly one such pair. This catches half-states in COMPLETED claims,
       which no projection retains — a released claim leaves no current state, so a
       state-based check cannot see that its grant was removed.
    2. **The active projection.** A held claim's Attempt must be in a claim-holding state
       at the coordinator's generation. This catches a live lane that the pairing check
       would accept because both halves are present but describe different claims.

    Fail closed and stop; a transaction with one half missing cannot be repaired by
    guessing which half was the truth.

    ``problem_ids`` is required, not discovered, because "which Problems exist" is a
    question about the ref's tree rather than about any one stream, and a checker that
    silently examined an empty set would pass vacuously — the failure mode this whole
    function exists to avoid. Task 13's driver passes `list_problem_streams(repo)`."""
    coordinator_events = read(repo, COORDINATOR_STREAM, config=config)
    by_id = {e.event_id: e for e in coordinator_events}
    consumed: set[str] = set()

    # (1) Pairing, over every Attempt that has EVER existed — not only live ones.
    for problem_id in problem_ids:
        for attempt_id, history in _attempts(read(repo, problem_id, config=config)):
            for pairing in _PAIRINGS:
                for event in pairing.matching(history):
                    partner_id = derive_event_id(
                        COORDINATOR_STREAM,
                        "\x00".join(pairing.coordinator_key(problem_id, attempt_id)))
                    partner = by_id.get(partner_id)
                    if partner is None:
                        raise LaneInconsistent(
                            f"{problem_id}/{attempt_id} has {event.event_type} but the "
                            f"coordinator has no {pairing.coordinator_event} for it — "
                            "half a transaction, which nothing that writes this lane can "
                            "produce")
                    if partner.event_type != pairing.coordinator_event:
                        raise LaneInconsistent(
                            f"{partner_id} is {partner.event_type}, expected "
                            f"{pairing.coordinator_event}")
                    for field in pairing.compare:
                        if payload_field(partner, field) != payload_field(event, field):
                            raise LaneInconsistent(
                                f"{problem_id}/{attempt_id}: {field} is "
                                f"{payload_field(event, field)!r} on {event.event_type} "
                                f"and {payload_field(partner, field)!r} on "
                                f"{partner.event_type} — one transaction wrote both, so "
                                "they cannot disagree")
                    consumed.add(partner_id)

    orphans = sorted(
        e.event_id for e in coordinator_events
        if e.event_type in _PAIRED_COORDINATOR_TYPES and e.event_id not in consumed)
    if orphans:
        raise LaneInconsistent(
            f"coordinator records with no Attempt-side partner: {orphans}. Either the "
            "Problem stream lost events, or it was not in problem_ids — both are reasons "
            "to stop rather than to continue.")

    # (2) The active claim, which pairing alone cannot validate: both halves can be
    # present and still describe different claims.
    coordinator = project_coordinator(coordinator_events)
    if coordinator.active_problem_id is None:
        return
    held = (coordinator.active_problem_id, coordinator.active_attempt_id)
    history = [e for e in read(repo, coordinator.active_problem_id, config=config)
               if e.attempt_id == coordinator.active_attempt_id]
    projection = project_attempt(history) if history else None
    if projection is None or projection.state not in CLAIM_HOLDING_STATES:
        raise LaneInconsistent(
            f"the coordinator holds {held} but that Attempt is "
            f"{projection.state.value if projection else None} on its own stream — "
            f"expected one of {sorted(s.value for s in CLAIM_HOLDING_STATES)}")
    if projection.claim_generation != coordinator.claim_generation:
        raise LaneInconsistent(
            f"{held} holds the lane at generation {projection.claim_generation} but the "
            f"coordinator is at {coordinator.claim_generation} — the two halves are from "
            "DIFFERENT claims, which no single transaction could have written")
```

`CLAIM_HOLDING_STATES` is imported from `lifecycle.py`, where Task 4 derives it from the
table. This task only consumes it — deriving it here would be the second declaration.

Two supporting helpers. `_attempts` groups a stream by `attempt_id` PRESERVING order, so
each group is still a valid `project_attempt` input (Problem-level events, which carry no
`attempt_id`, are skipped — they belong to the Problem, not to any Attempt):

```python
def _attempts(events: list[Event]) -> Iterator[tuple[str, list[Event]]]:
    grouped: dict[str, list[Event]] = {}
    for e in events:
        if e.attempt_id is not None:
            grouped.setdefault(e.attempt_id, []).append(e)
    return iter(grouped.items())
```

`list_problem_streams` belongs in `lane_log.py` beside `read` — "which streams exist" is a
question about the ref's tree, and the store is the only thing that knows its layout:

```python
def list_problem_streams(repo: Path, config: LaneLogConfig | None = None) -> tuple[str, ...]:
    """Every Problem stream with at least one event, EXCLUDING the coordinator.

    A `git ls-tree` over the event dir at the ref's tip — derived from the tree, never from
    a caller's list, because a caller's list is exactly what goes stale when a Problem is
    added by another runner."""
```

`_assert_terms_agree` re-checks the invariant Task 7 test 6 establishes at write time — that
the coordinator's `ClaimAcquired` and the Attempt's `ClaimGranted` carry identical terms and
generation — because "the two agreeing is an invariant, not a fallback" is only true if
something eventually reads both. Writing it once and never re-reading it is how an invariant
becomes an assumption.

Task 13's driver calls this once at startup with the full Problem set, before any lane work.
That is the whole migration story: prove the state cannot occur, detect it anyway in both
directions, refuse to run on it.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: all pass, including the ten pre-existing cases (each now carrying the
proposal-verified prelude).

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/coordinator.py \
  tests/integration/test_self_improvement_coordinator_cas.py \
  -m "feat(025 slice-2): claim generations + claim-bound policy terms (FR-035)"
```

---

### Task 8: Side-effect intents and the four dispositions

**Files:**
- Create: `src/llmxive/self_improvement/intents.py`
- Test: `tests/integration/test_self_improvement_intents.py`

Intents come BEFORE reclaim because reclaim's precondition consumes `unreconciled_intents`.
Nothing here references `cas_reclaim`, which does not exist yet; Task 9 wires the two
together and owns the tests that assert reclaim is actually blocked.

**Interfaces:**
- Produces: `IntentDisposition`, `IntentRecord`, `Reconciler`, `record_intent`, `observe_intent`, `unreconciled_intents`, `LaneQuarantine`, `EFFECT_DISPOSITION_POLICY`.

- [ ] **Step 1: Write the failing tests**

1. `record_intent` writes `SideEffectRequested` stamped with the current generation.
2. `unreconciled_intents` finds it; after `observe_intent(..., landed)` it is empty.
3. Each of the four dispositions round-trips and is refused if not in the vocabulary.
4. **A `publish` intent may be closed as `contained`** — and the record says `contained`, NOT `rejected`. Assert the disposition literally, because collapsing these two is the rev-22 error.
5. **A `merge` intent may NOT be closed as `contained` or `rejected`** — `observe_intent` raises `ValueError` naming the missing precondition. The only legal negative outcome for a merge is `ambiguous`.
6. An `ambiguous` observation raises `LaneQuarantine` AND leaves the intent in `unreconciled_intents` — it is durably recorded, so the quarantine is visible and repairable rather than only thrown.
7. A `contained` observation clears the intent: `unreconciled_intents` no longer reports it.
8. `unreconciled_intents` is generation-scoped — an intent from a superseded generation is still reported, because a stale worker's outstanding effect does not stop being outstanding when the claim moves.

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

`observe_intent` validates the disposition against `EFFECT_DISPOSITION_POLICY` and raises `ValueError` with the reason when a caller asks for one the effect cannot support. `AMBIGUOUS` additionally raises `LaneQuarantine` after appending the record — the record is durable so the quarantine is visible and repairable; the raise stops the run. `unreconciled_intents` returns intents with no `SideEffectObserved` **plus** those observed `AMBIGUOUS`. It is a pure projection over a stream's events, which is why it can be written and tested before any reclaim path exists; Task 9 calls it from `cas_reclaim`'s predicate.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_intents.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/intents.py \
  tests/integration/test_self_improvement_intents.py \
  -m "feat(025 slice-2): side-effect intents + the four dispositions (FR-035 rev 22)"
```

---

### Task 9: Heartbeats, expiry, and reclaim

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Modify: `src/llmxive/self_improvement/policy.py` (created in Task 3)
- Test: `tests/integration/test_self_improvement_claim_liveness.py`

**Interfaces:**
- Consumes: `append_many` (Task 2), `unreconciled_intents` (Task 8), `AuthoritativeClock.sample_uncertainty_s` (Task 3), `policy.MAX_CLOCK_SKEW_S` (Task 3).
- Produces: `cas_heartbeat`, `cas_reclaim`, `MAX_CLAIM_HOLD_TIME_S` and the phase budgets it derives from, the counter caps, `reclaimable`.

There is deliberately **no** `cas_release_terminal`. An Attempt that is terminal while its
claim is still held is unreachable once the terminal and the release share a transaction
(Task 6), so the repair entry point an earlier draft specified would be dead code guarding
a state the store cannot produce.

- [ ] **Step 1: EXTEND `policy.py` — derived, not literal**

Task 3 created the module with the timing constants the clock needs
(`HEARTBEAT_INTERVAL_S`, `CLAIM_EXPIRY_S`, `MAX_CLOCK_SKEW_S`, `MAX_SAMPLE_RTT_S`). Append
the phase budgets and counter caps below them; do not restate the four that already exist.

```python
# src/llmxive/self_improvement/policy.py  (appended)

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

Time is injected via `FixedAnchorClock` driven by a controllable monotonic source, so these are deterministic and exercise the REAL arithmetic:

1. A beat inside the interval renews: after `claim_expiry`+skew of ELAPSED time but with beats every 5 min, `reclaimable(...)` is False.
2. No beat for `claim_expiry + max_clock_skew` ⇒ reclaimable. At exactly `claim_expiry` alone ⇒ NOT reclaimable (the padding is not optional, and it pads toward not-evicting).
3. Past `max_claim_hold_time` ⇒ reclaimable **even while beating**. This is the pair of assertions rev 22 corrected: heartbeating protects a slow run from the expiry bound, not from the hold-time cap.
4. `cas_reclaim` writes exactly matrix row 3 — the Attempt's `ClaimExpired` terminal (`attempt_abandoned`) and the coordinator's `ClaimReleased` — in ONE commit, and the NEXT claim then takes the next generation. Assert the events written equal the `ClaimExpired` row's declaration, so the generic path and the reclaim path cannot drift apart.
4b. `cas_attempt_transition(event_type="ClaimExpired", ...)` RAISES and writes nothing, naming `cas_reclaim`. Reaching a reclaim through the generic path would skip the expiry and unreconciled-intent preconditions, which ARE the reclaim.
5. The reclaim race: the original run's own terminal lands first ⇒ the reclaimer's ENTIRE transaction loses — no `ClaimExpired`, no second release. Assert exactly one terminal (the original's) and that the lane is **free**, because the winning terminal carried its own release in the same commit (matrix row 2). An earlier draft asserted "still occupied" here, which was the pre-transaction answer and contradicted case 6 two lines later; under the matrix a terminal by the holder can never leave the lane held.
6. There is consequently nothing left for a second entry point to repair: assert that re-running `cas_reclaim` after case 5 is a no-op which raises rather than writing (the lane is free, so there is no claim to expire), and that the log still holds exactly one terminal. The wedged state an earlier draft planned a compensating transition for is unreachable, and this is the test that says so.
7. `cas_reclaim` on an Attempt with an unreconciled intent is REFUSED (Task 8's `unreconciled_intents`, already available).
8. A reclaim crashing at `_before_ref_update` leaves the Attempt non-terminal AND the lane still held by the original — never a terminal with a live claim, nor a free lane with a running Attempt.
9. The reclaimer's `sample_uncertainty_s` is ADDED to the skew margin: a clock reporting ±30 s of sampling uncertainty needs 30 s more elapsed time before the same claim becomes reclaimable. Imprecision must never make eviction happen sooner.

- [ ] **Step 3: Implement**

`reclaimable(coordinator_events, *, attempt_events, now, terms)` returns `(bool, reason)` using the CLAIM's terms:

```python
def reclaimable(*, claimed_at: str, last_beat: str | None, now: str,
                terms: ClaimTerms, sample_uncertainty_s: float = 0.0) -> tuple[bool, str]:
    """Two independent bounds; either one trips. Padding always favours NOT evicting a live
    holder, because that is the worse error (FR-036).

    ``sample_uncertainty_s`` is the reclaimer's own clock uncertainty (half its anchoring
    round trip, Task 3). It WIDENS the margin rather than narrowing it: a less certain clock
    must wait longer before evicting, never less."""
    margin = terms.max_clock_skew_s + sample_uncertainty_s
    beat = _parse(last_beat or claimed_at)
    since_beat = (_parse(now) - beat).total_seconds()
    held = (_parse(now) - _parse(claimed_at)).total_seconds()
    if since_beat >= terms.claim_expiry_s + margin:
        return (True, "heartbeat_lapsed")
    if held >= terms.max_claim_hold_time_s + margin:
        return (True, "hold_time_exceeded")
    return (False, "")
```

`cas_heartbeat` appends `ClaimHeartbeat{claim_generation, tick}` conditioned on the caller
still holding the claim AT the stamped generation.

`cas_reclaim` is ONE `append_many` carrying matrix row 3's two events — the Attempt's
`ClaimExpired` terminal and the coordinator's `ClaimReleased` — under a single predicate
that re-checks, at the commit's own parent, that (a) the claim is still held by the Attempt
being reclaimed at the generation observed, (b) that Attempt has no terminal yet, and (c) it
has no unreconciled intent. It is a separate entry point from `cas_attempt_transition`
because of (a) and (c): those preconditions are the reclaim, and a caller that could reach
`ClaimExpired` through the generic path would be reclaiming without them.
`cas_attempt_transition` therefore REFUSES `ClaimExpired` by name, pointing at
`cas_reclaim` — the events written are still exactly the ones the table's row declares, and
a test asserts that.

Document why there is no ordering to reason about:

> Reclaim has no step order because it has no steps: the terminal and the release are one
> commit under one compare-and-swap. An earlier draft wrote the terminal first "so
> the terminal slot decides the race" and then released — which is correct about the race
> and wrong about the crash, because a run that died between the two left a terminal Attempt
> holding a live claim. The transaction keeps the arbitration (the losing reclaimer's
> predicate fails against the winner's parent) and deletes the window: the loser discards
> all three events together.

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

### Task 10: The two counters and cooldown epochs

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

### Task 11: Matrix row 4 — promotion observed, monitoring removal, the merge timestamp

**Files:**
- Modify: `src/llmxive/self_improvement/coordinator.py`
- Test: `tests/integration/test_self_improvement_promotion_observed.py`
- Test: `tests/integration/test_self_improvement_coordinator_cas.py` (extend)

**Interfaces:**
- Consumes: `cas_attempt_transition` (Task 6) and the `PromotionObserved` row's declared effects; `append_many` (Task 2).
- Produces: `MonitorEnded` folding; the `MonitorStarted` ownership precondition; `last_autonomous_merge_at` folded from `MonitorStarted.merged_at`.

**This is a cross-stream transaction, not a coordinator append.** An earlier draft wrote only
the coordinator side, which would have left the Attempt in `promotion_requested` while the
coordinator believed it was monitored and the lane free — a claim released for an Attempt
that never advanced, and the exact half-state class this slice exists to remove. Four facts
land together (matrix row 4): the Attempt reaches `monitoring`, the claim is released, the
Attempt joins `monitored_attempts`, and `last_autonomous_merge_at` records the instant. The
mechanism is already built — Task 4 declares the effects, Task 6 emits them — so this task
adds the coordinator-side FOLDING and proves the row end-to-end.

- [ ] **Step 1: Write the failing tests**

Coordinator folding (`test_self_improvement_coordinator_cas.py`):

1. `MonitorStarted` then `MonitorEnded` removes the Attempt from `monitored_attempts`; an unrelated monitored Attempt is untouched.
2. `MonitorEnded` for an Attempt that was never monitored RAISES (fail closed — it means the projection and the caller disagree about what is being monitored).
3. `MonitorStarted` sets `last_autonomous_merge_at` to its `merged_at`.
4. **`last_autonomous_merge_at` is the LATEST event's instant, not the maximum.** Fold two `MonitorStarted` events where the second has a HIGHER `seq` and an EARLIER `merged_at` — reachable whenever two runners anchored their clocks independently — and assert the projection reports the SECOND one's value. A max-based projection passes every other case and fails only this one, which is why it is written explicitly rather than inferred from "monotonic".

Row 4 end-to-end (`test_self_improvement_promotion_observed.py`, real temp-git repos):

5. **One commit, four facts**: claim P1/A1, drive it to `promotion_requested`, apply `PromotionObserved`, then assert the Attempt is `monitoring`, `active_problem_id is None`, `"A1" in monitored_attempts`, `last_autonomous_merge_at == ` the transition's timestamp, and that `git show --name-only` on the resulting commit lists all THREE blobs.
6. **Crash at `_before_ref_update` leaves NONE of it**: the Attempt is still `promotion_requested`, the lane is still held, `monitored_attempts` is empty, and `last_autonomous_merge_at` is unchanged. Then a retry succeeds and case 5's assertions hold.
7. **Crash at `_after_parent` likewise**, and the retry is not a duplicate: exactly one `PromotionObserved`, one `MonitorStarted`, one `ClaimReleased`.
8. **Concurrency**: with the lane held by P1/A1, a concurrent writer appends an unrelated coordinator event between the read and the CAS (`_after_parent`), and `PromotionObserved` retries against the new tip and still lands exactly once with all four facts.
9. **A `PromotionObserved` by a non-holder writes no coordinator event and does not release anyone else's claim** — the same guard as Task 6 case 8, asserted here because this row is the one that releases a claim WITHOUT a terminal, so a mis-scoped release would leave a live Attempt lane-less rather than merely double-terminal.
10. **Idempotent replay**: re-applying `PromotionObserved` after it landed returns the same projection and adds no events — the claim is already released, so a second attempt must not try to release it again and trip the coordinator fold's non-owner check.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/integration/test_self_improvement_promotion_observed.py tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: failures on `monitored_attempts` still containing the Attempt after `MonitorEnded`, and on `last_autonomous_merge_at` being `None`.

- [ ] **Step 3: Implement**

In `coordinator.py`: add `"MonitorEnded"` to `_COORDINATOR_TYPES`, and in `project_coordinator`:

The `MonitorStarted` branch REPLACES the existing one; the `MonitorEnded` branch is new.
Shown at column 0 — they sit at the event loop's indentation, as `elif` arms beside
`ClaimAcquired`/`ClaimReleased`:

```python
if e.event_type == "MonitorStarted":
    attempt = payload_field(e, "attempt_id")
    # Monitoring starts for the Attempt whose promotion this transaction just observed,
    # which is by construction the claim HOLDER. Asserting it is what makes the ordering
    # inside row 4 semantically required rather than merely conventional: reversed, the
    # release clears the slot first and this check then has no owner to match. Without
    # it the fold accepts either order, and the mutation test in Step 5 proves nothing.
    # It is also a real corruption check on its own — a MonitorStarted for an Attempt
    # nobody claimed is monitoring a merge the lane never promoted.
    if (c.active_problem_id, c.active_attempt_id) != (payload_field(e, "problem_id"), attempt):
        raise ValueError(
            f"illegal transition MonitorStarted for {attempt!r}, which does not hold the "
            f"lane (held by {c.active_problem_id!r}/{c.active_attempt_id!r})")
    c = replace(c,
                monitored_attempts=(*c.monitored_attempts, attempt),
                # The LATEST merge event's instant — assignment, not max(). A later-`seq`
                # event may carry an earlier instant (two runners, two independently
                # anchored clocks), and `seq` is the ordering authority here as everywhere
                # else. Claiming numeric monotonicity would be claiming something the
                # clock does not guarantee.
                last_autonomous_merge_at=payload_field(e, "merged_at"))
elif e.event_type == "MonitorEnded":
    attempt = payload_field(e, "attempt_id")
    if attempt not in c.monitored_attempts:
        raise ValueError(
            f"illegal transition MonitorEnded for {attempt!r}, which is not monitored")
    c = replace(c, monitored_attempts=tuple(
        a for a in c.monitored_attempts if a != attempt))
```

No new CAS entry point: `PromotionObserved` goes through `cas_attempt_transition` like every
other transition, and the effects come from its row. A `cas_promotion_observed` would be a
second way to do what Task 6 already does — and the second way is always the one that
forgets an effect.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/integration/test_self_improvement_promotion_observed.py tests/integration/test_self_improvement_coordinator_cas.py -q`
Expected: all pass.

- [ ] **Step 5: Verify row 4's atomicity is load-bearing**

Temporarily strip `PromotionObserved`'s `coordinator_effects` back to `()` in `lifecycle.py`,
re-run, and confirm case 5 FAILS with the lane still held and nothing monitored — the
coordinator-only draft's exact outcome. Restore.

Then temporarily reverse the effect order to `("ClaimReleased", "MonitorStarted")` and
confirm case 5 FAILS inside `project_coordinator` with `MonitorStarted ... does not hold the
lane`. Restore. **Then delete the ownership check from the `MonitorStarted` fold branch and
confirm the REVERSED order now folds cleanly** — that is what proves the ordering is
enforced by the check rather than by wishful reading. Without this second mutation the order
test is self-confirming: the release's own owner check runs while the owner still exists, so
it can never be what rejects the reversal. Restore both; confirm `git diff` is empty.

- [ ] **Step 6: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o src/llmxive/self_improvement/coordinator.py \
  tests/integration/test_self_improvement_coordinator_cas.py \
  tests/integration/test_self_improvement_promotion_observed.py \
  -m "feat(025 slice-2): promotion-observed transaction — monitoring + release + merge instant"
```

---

### Task 12: The adversarial suite

The four scenarios the rev-22 review named, plus the one the rev-23 review implied. Each has
a definite expected outcome now, which it did not before rev 22.

**Files:**
- Create: `tests/integration/test_self_improvement_adversarial.py`

**Interfaces:** consumes everything from Tasks 2–11.

- [ ] **Step 1: Write the five tests**

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


def test_a_reclaim_racing_a_terminal_leaves_no_half_state(repo, clock):
    """Two writers decide the same Attempt's end at the same parent. Whoever loses must
    leave NOTHING — not a terminal without a release, not a release without a terminal.

    This is the rev-23 scenario: the earlier design wrote the terminal and the release as
    two commits and answered the crash window with a compensating transition. The
    transaction makes the window unreachable, so the assertion is about ABSENCE."""
    # The original run terminalizes while a reclaimer, holding the same parent, expires it.
    # Drive the race deterministically with the `_after_parent` barrier both writers share.
    # Assertions:
    #   - exactly ONE terminal exists on the Attempt stream
    #   - the coordinator shows exactly ONE ClaimReleased, and the lane is free
    #   - the loser wrote NEITHER of its two events (count both streams before and after)
    #   - the winning terminal and its release share a commit: `git show --name-only`
    #     on the coordinator's tip lists both paths
    #   - repeating the loser's call afterwards still raises — it did not land, and it must
    #     not come to appear as though it had


def test_a_promotion_racing_a_reclaim_leaves_no_half_state(repo, clock):
    """Matrix row 4 under contention — the row that releases WITHOUT a terminal.

    Row 2's race (above) is decided by the terminal slot. Row 4 has no terminal to
    arbitrate with, so its only guard is the ownership precondition re-evaluated at the
    commit's own parent. That makes it a genuinely different failure mode, not a
    re-run of the previous test with different event names."""
    # A run at `promotion_requested` observes its merge while a reclaimer, holding the same
    # parent, expires the claim past `max_claim_hold_time`. Drive it with `_after_parent`.
    # Assertions:
    #   - exactly one of the two lands, wholly
    #   - if PromotionObserved won: the Attempt is `monitoring`, "A1" is monitored,
    #     `last_autonomous_merge_at` is set, the lane is free, and NO ClaimExpired exists
    #   - if the reclaim won: the Attempt is `attempt_abandoned`, `monitored_attempts` is
    #     EMPTY, and `last_autonomous_merge_at` is unchanged — a monitoring record from a
    #     promotion that lost would be a merge the lane believes it is watching and is not
    #   - the coordinator carries exactly ONE ClaimReleased either way
    #   - the loser's replay still raises
```

Fill in each body against the real modules; the comments above are the required assertions, not placeholders to leave in.

- [ ] **Step 2: Run**

Run: `python -m pytest tests/integration/test_self_improvement_adversarial.py -q`
Expected: `6 passed`.

- [ ] **Step 3: Verify each is load-bearing**

For each of the six, break the mechanism it pins (allow `merge` → `CONTAINED` in `EFFECT_DISPOSITION_POLICY`; drop the skew check; drop the unreconciled-intent precondition; let hold-time bypass the intent block; split the terminal-plus-release transaction into two appends; drop the ownership re-check from `cas_attempt_transition`'s predicate), confirm the matching test FAILS, then restore and confirm an empty `git diff`. Record the six observed failure messages in the notes — a scenario test that passes against a broken mechanism is the most expensive kind of decoration.

- [ ] **Step 4: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -o tests/integration/test_self_improvement_adversarial.py \
  -m "test(025 slice-2): adversarial suite — stale push/merge, clock poisoning, promotion expiry, terminal race"
```

---

### Task 13: Wire the proposal verdict + the default-off driver

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
6. `ClaimOutcome`, `AttemptState`, `IntentDisposition`, `GitHubDateClock` and the rest of the Task-3–11 surface are importable from `llmxive.self_improvement` (extend `EXPECTED`).
7. **The tick calls `assert_lane_consistent` BEFORE any lane work, and refuses to run on a half-state**: seed a lane with a hand-built coordinator `ClaimAcquired` that has no `ClaimGranted`, enable the lane, and assert `run_lifecycle_tick` raises `LaneInconsistent` having written NOTHING. A driver that "recovers" from this by picking a side would be choosing which half of a claim to believe.

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

- [ ] **Every matrix row has its crash tests**

```bash
python -m pytest tests/integration/test_self_improvement_coordinator_cas.py \
  tests/integration/test_self_improvement_lifecycle_cas.py \
  tests/integration/test_self_improvement_claim_liveness.py \
  tests/integration/test_self_improvement_promotion_observed.py -q -k "crash or _before_ref_update or _after_parent"
```
Expected: at least one crash case per matrix row (claim, terminal, reclaim, promotion) — four rows, and a row with no crash test is a row whose atomicity nobody checked.

- [ ] **Docs updated in the same commits as the code** (CLAUDE.md rule): `notes/2026-07-26-spec025-slice1-implementation.md` gains a Slice-2 section covering (a) the false premise this plan was first drafted on — that the lane's streams are separate refs, when they are subtrees of one — and what it cost: an "honest limit" about advisory fencing and a compensating transition, both of which evaporated once the store was read correctly; (b) that the fix was a store capability, not a workaround; (c) that the SAME defect recurred one layer up — `PromotionObserved` was written as a coordinator-only append after the transaction existed, which is why the cross-stream invariant matrix is now a normative list rather than a set of individually-remembered cases; and (d) the load-bearing verifications from Task 2 Step 9, Task 3 Step 5, Task 6 Step 5, Task 11 Step 5, and Task 12 Step 3.

- [ ] **Nothing swept**: `git status --short` still shows exactly the six untracked pipeline artifacts, unchanged.

- [ ] **Do NOT push.** Rebase onto `origin/main` at PR time.

## Open questions for the maintainer

1. **`GET /rate_limit` unauthenticated** is what the clock falls back to when the run has made no API call yet. In CI the lane will already hold a token, so the authenticated response's `Date` is free — but the unauthenticated path is subject to a 60/hr per-IP limit that a busy shared runner could exhaust. Should the clock REQUIRE a token (fail closed rather than fall back), given FR-036 already says no trusted time ⇒ no lane work?
2. **`MAX_CLAIM_HOLD_TIME_S` = 3 h 40 min** is a long wedge if a run dies at minute 1 without ever beating. The heartbeat bound (15 min) covers that case, so the hold time only bites a run that beats but never progresses. Confirm that is the intended trade.
3. **Task 2 modifies `git_event_log.py`, which the 026 credit ledger also depends on.** The change is additive (`append_transaction` alongside `append_to_log`) plus one refactor of the shared tree builder, and Step 2 runs the ledger's suite before anything else is built on it. Confirm you are comfortable with slice-2 work touching that shared transport rather than adding a lane-only copy — the alternative duplicates the CAS loop, which is the Constitution I trade going the other way.
4. **`cas_claim` now requires the Attempt to be `proposal_verified`,** so the ten signed-off 1A coordinator tests each gain a two-event prelude. That is a contract change to signed-off code, made because a claim that skips the table is a claim the machine cannot reason about. Flagging it rather than doing it silently.
5. **Task 1 amends the spec again (rev 23).** If you would rather review rev 23 before any Slice-2 code lands, Task 1 is separable — it touches only the spec and notes. The invariant matrix you asked to review before Task 1 is in this plan, above; rev 23 copies it in verbatim.
6. **`MonitorStarted` gains a REQUIRED `merged_at`,** changing a 1A event's payload contract and five 1A test call sites. It has exactly one producer, which always knows the value, so an optional field would exist only to let the coordinator record a merge it cannot date. Same class of flag as item 4: a contract change to signed-off code, surfaced rather than slipped in.
7. **Task 2 now also fixes a PRE-EXISTING defect in `append_to_log`** — the post-push `update-ref` with no expected-old value, which lets a slow writer rewind the local ref past a newer commit from the same clone (`git_event_log.py:684-686`). It is on the code path this transaction copies and it affects the 026 credit ledger too, so it is fixed in the shared helper rather than worked around. If you would rather that landed as its own commit ahead of the slice, Task 2 Step 5 edit 0 is separable.
8. **`assert_lane_consistent` is a detector for a state that currently cannot exist.** Both `git for-each-ref 'refs/llmxive/*'` and `git ls-remote origin 'refs/llmxive/*'` are empty, so there is no lane history to migrate and no converter is written. The detector guards a future clone, restore, or hand-repair. Confirm you want it rather than a migration — writing a converter for records that do not exist would be the more expensive answer.
9. **`MonitorStarted` gains an ownership precondition in the coordinator fold** (finding 4's first option, not the second). It makes row 4's ordering semantically enforced rather than conventional, and it is a real corruption check on its own — a `MonitorStarted` for an unclaimed Attempt is the lane watching a merge it never promoted. The cost is a second contract change to a 1A event: its payload gains `problem_id` (the check compares the PAIR, per the 1A F6 guard) alongside `merged_at`, and the 1A folding tests need a claim prelude. If you would rather keep `MonitorStarted` unconditional, the fallback is to document the order as canonical and delete the reversal mutation test — say which.
10. **`policy.py` moves from Task 9 to Task 3.** The clock's `max_sample_rtt` and refresh interval ARE Policy Contract values, and the regression tolerance is derived from `max_clock_skew`; leaving `policy.py` in Task 9 would have the clock keeping private copies of contract values declared elsewhere. Task 9 now extends the module rather than creating it.
