# Feature Specification: Autonomous Self-Improvement Lane

**Feature Branch**: `025-self-improvement-lane`
**Created**: 2026-07-16
**Status**: Draft (revision 3 — reworked after design reviews of rev 1 and rev 2)
**Input**: GitHub issue [#1242](https://github.com/ContextLab/llmXive/issues/1242) and its [design comment](https://github.com/ContextLab/llmXive/issues/1242#issuecomment-4987730544). Add two cron jobs: (1) learn from recurring errors and suggest an improvement *to llmXive* that can be planned/implemented/tested; (2) peruse open issues and submit high-value work to the pipeline. Unlike sandboxed research projects, success in these jobs changes **llmXive itself**.

## Overview

llmXive advances research projects through a ~34-state lifecycle, committing every artifact to git. Those projects are **sandboxed** under `projects/`: their agents never modify the platform. This feature adds a distinct **self-improvement lane** whose successful output is a **branch/PR against llmXive itself**.

The lane's safety case rests on **data contracts, trust boundaries, and a versioned numeric policy** — never on adjectives. Its load-bearing guarantees:

- **Problem vs. attempt identity** — a stable `problem_id` (per issue/fingerprint) aggregates evidence; each fix try is a separate `ImprovementAttempt` with its own base SHA, branch, PR, and evaluation contract.
- **Genuine optimistic concurrency** — append-only events + per-record `expected_revision` fast-forward pushes; correctness does NOT depend on `commit-and-push.sh`'s `-X theirs` (which is not per-record CAS) nor on the in-host lease (which only guards same-filesystem processes).
- **Seven isolated trust domains** — discovery/persistence/claiming/implementation/candidate-testing/trusted-evaluation/promotion — so candidate code never touches a secret, a repo-write token, or the evaluator, and privileged persistence never runs an LLM or candidate command.
- **A safely-executable evaluation harness** — the trusted harness (pinned `main`) executes the untrusted system-under-test (candidate head) in a network-denied container; `base_reproducer`s are structured, allowlisted invocations, never free-form command strings.
- **A versioned, protected numeric policy** (see "Policy Contract v1") — every threshold is a concrete default, immutable by candidate branches.

Live auto-merge to `main` is gated behind a **default-off flag** *and* explicit shadow-mode quality thresholds; until then the loop runs for real against a disposable canary branch and never mutates `main`.

Governed by the constitution ([.specify/memory/constitution.md](../../.specify/memory/constitution.md)): Single Source of Truth (I), Verified Accuracy (II), Real-World Testing (III), Cost Effectiveness / Free-First (IV), Fail Fast (V), Convergent Review (VI).

## Scope & Dependencies

**In scope**: the two discovery crons; the Problem/Attempt store; the pre-implementation proposal gate; the isolated implementation executor; the trusted evaluation + promotion path (shadow → canary branch); post-merge monitoring + attributed auto-revert + circuit breakers; the default-off live-main flag; the versioned policy; About-page/docs; the GitHub App setup walkthrough.

**Out of scope — prerequisite `026-model-selection-consolidation` (own spec + PR, lands first; maintainer decision 2026-07-16)**: the platform-wide migration of every model-selection site (registry defaults, `MODEL_FALLBACKS`, execution tier-ladder, catalog filtering, ~20 direct pins).

**026 dependency contract (minimal, so 025 can be planned before 026 lands)**:
- **Import**: `from llmxive.backends.model_selection import select, ModelRequirement, ModelChain, ModelUnavailable`.
- **`select(req: ModelRequirement) -> ModelChain`**: pure, deterministic given the same live-catalog snapshot; returns an ordered chain (primary + fallbacks).
- **Types**: `ModelRequirement(capability: Literal["cheap","standard","deep","vision"], independent_of: str|None, allow_paid: bool, budget_hint: int|None)`; `ModelChain(models: list[str], resolved_at: datetime, catalog_digest: str)`.
- **Errors**: `ModelUnavailable` when no model satisfies the requirement (e.g. `allow_paid=False` and every free tier model is absent from the live catalog).
- **Availability semantics**: absence from a successfully-fetched live catalog = **unavailable for new selection**; `ModelChain.resolved_at`/`catalog_digest` make availability **timestamped evidence**, re-checked per call.
- **Slice sequencing**: delivery slices 1–2's *deterministic* parts (run-log/ledger clustering, issue filtering/ranking/pagination, the store, the transaction protocol) need **no** model and MAY proceed before 026 lands; the *LLM* parts (proposer, independent assessor, implementer, LLM verifier) are **blocked on 026** and MUST import the contract above rather than call the router directly.

**Reuse (Constitution I)**: `advance_ledger.classify_message`; `web_data._activity_severity` / `_recent_activity`; the `gh` wrapper pattern; `credits.paid_opt_in_enabled()`; `project_lease.py` (in-host mutual exclusion only — NOT cross-runner correctness); `scripts/ci/commit-and-push.sh` (append-only event/blob writes only — NOT as the per-record CAS mechanism).

## User Scenarios & Testing *(mandatory)*

Stories map 1:1 to delivery slices; each is independently testable.

### User Story 1 - Observation-only discovery (Priority: P1)

Both crons run end-to-end to produce **proposal-verified candidate attempts** — clustering real errors and ranking real issues, assessed by a proposer and an *independent* assessor against the numeric policy — with **no issue/branch/PR/promotion side effects**. (This is not "zero risk": it commits Problem/Attempt state to the repo through the privileged **persistence** domain.)

**Why this priority**: Delivers the issue's core value (surface the platform's most consequential recurring defects and highest-value backlog work, with reproducible evidence) without any external mutation beyond committed state.

**Independent Test**: Run each cron against live `state/run-log` + `state/advance_errors` and the live open-issue set; assert Problems carry a stable `problem_id`, Attempts carry an `evidence_digest` (order-independent), a proposal, an evaluation contract, rubric scores, and a machine-readable accept/reject against the policy; assert only `StagePanelKickback` is excluded (escalations are eligible); assert re-running does not create duplicate Problems.

**Acceptance Scenarios**:

1. **Given** a hard failure recurring across ≥3 distinct projects, **When** the error cron runs, **Then** one `ImprovementProblem` is emitted with `problem_id = hash(schema_version, "errors", "<fingerprint>@<fp_schema_version>")` and evidence stored as append-only events, and one `proposed` Attempt.
2. **Given** the same cluster grows/reorders on the next run, **When** the cron runs, **Then** the `problem_id` is unchanged and the `evidence_digest` (hash of the deduplicated, canonically-sorted, normalized evidence set) reflects only genuine membership changes — order does not affect it.
3. **Given** a cluster of only `StagePanelKickback` soft mechanics, **When** the cron runs, **Then** no Problem is emitted; **Given** a `StagePanelEscalation` (panel-engine hard failure), **Then** it IS eligible evidence.
4. **Given** a proposal below any policy threshold, **When** the independent assessor runs, **Then** the Attempt is `rejected` with a machine-readable reason and is NOT advanced toward `claimed`.

---

### User Story 2 - Transactional claiming (Priority: P1)

At most one Problem is `claimed`/active at a time, established by a genuine optimistic-concurrency transaction: read `expected_revision=N`, fetch latest `main`, rebuild the snapshot from events, verify still `N`, push the claim event + label as a fast-forward; on any mismatch, discard and recompute (never `-X theirs`).

**Why this priority**: Two independent crons + "one active" + mutable projections + issue-label side effects is a distributed transaction; without real CAS, `commit-and-push.sh` lets two ticks both land and the second silently overwrites the first snapshot.

**Independent Test**: Simulate two concurrent claims sharing the same `expected_revision`; assert exactly one fast-forwards and the other detects the revision moved and recomputes; kill a claim between the state push and the label call and assert reconciliation converges idempotently.

**Acceptance Scenarios**:

1. **Given** two concurrent claim attempts at `expected_revision=N`, **When** both persist, **Then** exactly one push fast-forwards to `N+1`; the loser's push is rejected (non-fast-forward) or its rebuilt revision ≠ N, so it discards and recomputes.
2. **Given** a claim whose state event landed but whose label call failed, **When** reconciliation runs, **Then** it re-applies the label idempotently or records the claim incomplete — provenance events are never overwritten.
3. **Given** an already-claimed source or one in cooldown, **When** discovery runs, **Then** it is not re-enqueued.
4. **Given** any transition, **When** it occurs, **Then** an append-only event (`event_id`, `event_type`, `problem_id`, optional `attempt_id`, `expected_revision`/`resulting_revision`, `timestamp`, `actor`, `payload`, `schema_version`) is written and the snapshot is a projection rebuildable from events.

---

### User Story 3 - Bounded draft PRs (Priority: P2)

The executor drains a claimed Attempt: branches `bot/self-improvement/<problem-id>/<attempt-id>` from `base_sha` in an isolated worktree (implementation trust domain — no prod/repo secrets), runs the implementer under the policy's diff envelope + budgets, runs offline tests in a **network-denied container**, and opens a **draft PR**. Out-of-envelope work routes to a human lane.

**Why this priority**: Turns a verified proposal into a concrete, reviewable change while keeping candidate code away from every secret and any protected branch.

**Independent Test**: Feed a claimed Attempt to the executor; assert branch creation from `base_sha`, diff obeys the envelope, a forbidden-path/over-cap diff is rejected with a machine reason before any test runs, tests run with no secrets and `--network none`, and a draft PR is opened. Assert an out-of-envelope Attempt routes to `unsupported_scope`.

**Acceptance Scenarios**:

1. **Given** a claimed Attempt, **When** the executor runs, **Then** a branch `bot/self-improvement/<problem-id>/<attempt-id>` is created from `base_sha`; candidate code has no production/repo secrets.
2. **Given** an implementer diff editing `.github/workflows/**`, secrets/auth, branch protection, the policy/eval baseline, dep locks, or generated corpora, **When** the diff policy runs, **Then** the Attempt is rejected before any test executes.
3. **Given** an issue-derived candidate needing a change outside the supported surface, **When** scope is evaluated, **Then** it routes to `unsupported_scope` — for a source-issue candidate via a human-lane label/comment on that issue; for an **error-derived** candidate (no source issue) the **claiming** domain opens a new human-lane issue. Neither counts as an implementation failure/cooldown.
4. **Given** a passing bounded implementation, **When** the executor completes, **Then** a **draft** PR is opened linking `problem_id`/`attempt_id`, evidence, evaluation contract, and offline-gate results.

---

### User Story 4 - Trusted promotion into a canary branch (Priority: P2)

An Attempt promotes into the **canary branch** only after the trusted harness (pinned `main`) runs the candidate head's `EvaluationContract` — proving **fails-at-base / passes-at-head** via a structured, allowlisted `base_reproducer` — with no material regression per the policy, all required checks green **from named trusted GitHub Apps**, using an App token that never executes candidate code.

**Why this priority**: The autonomous promotion boundary. Integrity depends on the trust split (trusted harness/fixtures from pinned main; untrusted system-under-test + candidate tests from head) and an executable, non-free-form metric.

**Independent Test**: In shadow mode, run the harness on an Attempt; assert promotion occurs only when the allowlisted `base_reproducer` fails at `base_sha`, passes at head, the regression suite is clean, and every required check comes from a trusted App; assert a free-form command `base_reproducer` is refused.

**Acceptance Scenarios**:

1. **Given** an Attempt whose allowlisted `base_reproducer` fails at `base_sha` and passes at head, all trusted-App checks green, no material regression, **When** promotion runs in shadow mode, **Then** it merges into the canary branch (never `main`).
2. **Given** a check reported by an App not on the trusted allowlist but using a required check name, **When** gates are evaluated, **Then** the spoofed check is rejected and promotion blocked.
3. **Given** a `base_reproducer` that is a free-form command string (not a trusted test id or structured harness invocation), **When** it is validated, **Then** it is refused (never executed).
4. **Given** target improvement but a newly-failing trusted regression check (material regression), **When** promotion runs, **Then** the merge is blocked.

---

### User Story 5 - Post-merge monitoring, attributed auto-revert & circuit breakers (Priority: P2)

After promotion (canary target in shadow), the lane monitors the operational canary over the policy's window/min-observations, **corroborates** attribution (a transient error class alone is NOT sufficient), checks ancestry, and auto-reverts genuine, causally-attributed regressions. Repeated failures trip the breaker.

**Why this priority**: Makes autonomy safe. Excluding all transient-class failures would be a false-negative path (a candidate can break routing → transient failures); a blanket "20% up" is unsafe at small counts.

**Independent Test**: Inject a deliberate regression on the merged canary and assert an ancestry-checked, corroboration-backed revert within the window; assert a provider outage WITHOUT corroboration does not trigger a revert; assert a candidate-caused transient-class failure WITH corroboration does; assert two reverts in the breaker window disable promotion while discovery continues.

**Acceptance Scenarios**:

1. **Given** a merged Attempt whose target worsens beyond both absolute and relative thresholds over ≥ the minimum observations, **When** monitoring runs, **Then** an ancestry-checked revert is created and merged.
2. **Given** post-merge transient-class failures, **When** attribution runs, **Then** a revert occurs ONLY if ≥1 corroboration signal holds (base/control fails contemporaneously; provider health evidence; same failure on unrelated main/canary; failure before candidate code is reached) — the class alone is insufficient either way.
3. **Given** a human change landed on the target after the autonomous merge, **When** revert is considered, **Then** the lane does not blind-revert; it re-derives against current head (ancestry) or escalates.
4. **Given** two automatic reverts within the breaker window, **When** the next Attempt is ready, **Then** promotion is disabled (discovery continues) until the manual re-enable procedure.

---

### User Story 6 - Live-main promotion, metric-gated (Priority: P3)

Promotion targets `main` only when the `LLMXIVE_SELF_IMPROVEMENT_LIVE` flag is on, a GitHub App + branch protection are configured, and shadow-mode has met the policy's live-eligibility thresholds. Absent any, promotion fails closed.

**Independent Test**: Flag on but App/protection absent → promotion refuses. Shadow metrics below threshold → live promotion withheld.

**Acceptance Scenarios**:

1. **Given** the live flag on but no App/protection, **When** promotion runs, **Then** it refuses (fail-closed).
2. **Given** the live flag on, App+protection configured, and shadow metrics ≥ the policy thresholds, **When** promotion runs, **Then** the merge targets `main` via the App (author ≠ merger).
3. **Given** shadow metrics below threshold, **When** live promotion is attempted, **Then** it is withheld and the reason recorded.

---

### Edge Cases

- **Recurrence after retention**: a `retained` problem's fingerprint returns months later → a NEW `ImprovementAttempt` under the same `problem_id`, with fresh `base_sha`/branch/PR/contract; "first fix failed" vs "problem recurred" is distinguished by attempt lineage + disposition.
- **Freshness / drift**: before implementation or promotion, if `main` has moved past the freshness bound from `base_sha` or any touched file changed, the Attempt is recreated (new `base_sha`) and base/head evaluation re-run.
- **Discovery has no write token**: discovery emits a schema-validated artifact only; the separate persistence domain validates + commits it.
- **Concurrent writers same revision**: detected by the fetch-rebuild-verify-fast-forward protocol; the loser recomputes.
- **Evidence order/dupes**: `evidence_digest` is over a deduplicated, canonically-sorted, normalized set — order-independent.
- **Escalation is hard**: only `StagePanelKickback` is soft.
- **Transient ≠ outage**: provider-outage exclusion requires corroboration; a candidate-caused transient failure is still attributed.
- **Sentinel scope**: a high-severity sentinel may block/breaker/quarantine/attributed-revert/notify — it never fast-tracks proposal/implementation/evaluation/merge.
- **Observational candidates**: no reproducible base failure → draft-PR + human-lane only; never auto-promote in v1.
- **Incomplete pagination**: a truncated open-issue view fails closed until a terminal-page marker.
- **Non-existent classes**: eligibility references only the real classifier classes; no security/data-loss error classes exist.
- **Recursive self-reference**: a generation may not modify the discovery/persistence/promoter/evaluator/policy it depends on.

## Requirements *(mandatory)*

### Model-selection dependency (026)

- **FR-001**: All LLM calls in the lane MUST go through the 026 `select(ModelRequirement) -> ModelChain` contract (import path + types + errors + availability semantics per "Scope & Dependencies"); the lane MUST NOT call the router/backends directly or embed a model ranking.
- **FR-002**: Verifier **independence** MUST be recorded along model id, provider/backend, prompt version, supplied context, and verifier identity; `independent_of` is necessary but not sufficient. **Deterministic checks are authoritative** over any LLM verifier.
- **FR-003**: Slices 1–2's deterministic components MUST be implementable and testable without any model; only proposer/assessor/implementer/verifier calls depend on 026.

### Identity: Problem vs. Attempt

- **FR-004**: `problem_id = hash(schema_version, source_kind, canonical_source_key)` is stable; `canonical_source_key` = `github:<owner>/<repo>#<n>` for issues, `<fingerprint>@<fp_schema_version>` for errors. `fp_schema_version` is bumped whenever `classify_message`'s fingerprint set/semantics change (a semantics change starts a new Problem).
- **FR-005**: Each fix try is an `ImprovementAttempt(attempt_id, problem_id, base_sha, branch, pr_number, evaluator_version, evaluation_contract, status, attempt_count)`; branches are `bot/self-improvement/<problem-id>/<attempt-id>`; `parent_id` links a retry to its predecessor Attempt.
- **FR-006**: `evidence_digest` MUST be the hash of the **deduplicated, canonically-sorted, normalized** evidence-reference set — independent of event/insertion order.

### Persistence, concurrency & provenance (real optimistic concurrency)

- **FR-007**: State MUST persist via append-only events at `state/self-improvement/events/<problem-id>/<event-id>.json`; snapshots at `state/self-improvement/problems/<problem-id>.json` and `.../attempts/<attempt-id>.json` are projections rebuildable from events; provenance is NEVER overwritten.
- **FR-008**: A mutation MUST use optimistic concurrency: (1) read `expected_revision=N`; (2) create the event with `expected_revision=N`, `resulting_revision=N+1`; (3) fetch latest `main`; (4) rebuild the snapshot from events and verify it is still `N`; (5) push ONLY as a fast-forward from the expected ref; (6) on any mismatch or non-fast-forward, discard and recompute — MUST NOT resolve the conflict with `-X theirs`. Correctness MUST NOT depend on scheduled workflows being the only writers.
- **FR-009**: The in-host `project_lease` MAY reduce same-runner contention and a shared GitHub `concurrency` group MAY reduce cross-runner contention, but neither is the correctness mechanism (FR-008 is).
- **FR-010**: Events MUST carry: `event_id`, `event_type`, `problem_id`, optional `attempt_id`, `expected_revision`, `resulting_revision`, `timestamp`, `actor` (trust-domain identity), `payload`, `schema_version`.
- **FR-011**: At most one Problem MUST be in an active state (`claimed` through post-merge `monitoring`) at a time; automated submissions MUST NOT refill the queue.

### Trust domains (seven)

- **FR-012**: The lane MUST enforce seven isolated domains with explicit posture:
  |Domain|Secrets/tokens|Network|Runs LLM?|Runs candidate code?|
  |-|-|-|-|-|
  |Discovery|issue-read + model key|as model needs|yes|no (produces schema-validated artifact only)|
  |Persistence|narrow `contents: write`|none|no|no (validates + commits the artifact)|
  |Claiming|`issues: write`|GitHub API|no|no (labels/comments)|
  |Implementation|model key during generation only; NO prod/repo secrets|as model needs|yes (generation)|no|
  |Candidate-testing|NONE; read-only checkout; checkout creds disabled|**denied** (`--network none`, no docker socket, no cred mounts, `permissions: {}`)|no|**yes** (untrusted)|
  |Trusted-evaluation|fixtures/baselines from pinned `main`|denied|no|orchestrates the untrusted SUT|
  |Promotion|GitHub App token only|GitHub API|no|**never**|
- **FR-013**: Required status checks MUST be accepted ONLY from a named trusted-GitHub-App allowlist (no name-spoofing); protected policy/replay/harness code MUST NOT be modifiable by a candidate branch.
- **FR-014**: The offline test mechanism MUST be concrete: a pinned prebuilt container run with `--network none`, no Docker socket, no credential mounts, `permissions: {}`, and checkout credentials disabled. Splitting networked generation from testing is necessary but NOT sufficient by itself.

### Discovery — errors (Cron 1)

- **FR-015**: Read a bounded window of `state/run-log/<YYYY-MM>/*.jsonl` + `state/advance_errors/`; fingerprint ONLY via `advance_ledger.classify_message`; exclude only `StagePanelKickback` (soft) via `web_data._activity_severity`; `StagePanelEscalation` and all other `hard` outcomes are eligible. Do NOT sum cumulative `consecutive_count` with time-bounded events; distinct affected projects is the primary support metric.
- **FR-016**: Eligibility uses only real classifier classes; a candidate requires ≥3 distinct projects, OR 2 projects + ≥5 recent occurrences; a single-project cluster qualifies ONLY if class `invariant` OR it originates from a deterministic high-severity sentinel (FR-025).

### Discovery — issues (Cron 2)

- **FR-017**: Enumerate the COMPLETE open-issue set via explicit API pagination; a terminal-page marker MUST be observed before any candidate is produced (a truncated view fails closed).
- **FR-018**: A deterministic filter excludes bot-authored issues, `human-submission`/`new-paper`, issue #1242, already-claimed/cooldown, and issues **already satisfied by `main`** (defined: closed-as-completed / referenced by a merged PR, OR — once a reproducer exists — a `base_reproducer` that does not fail at current `main`). Remaining issues are ranked by a **defined deterministic formula** (weighted maintainer labels, recency, evidence/reproduction signals, affected-surface path mentions, capped discussion count, estimated scope) with a **stable tie-break by ascending issue number**; a proposer assesses ≤ top 10; an independent verifier re-ranks ≤ top 3; ≤ 1 candidate/day enqueued.
- **FR-019**: An enqueued issue creates a `discovered`/`proposed` Attempt (NOT via `_create_brainstormed_project`); the `self-improvement:claimed` label + comment are applied ONLY after the US2 claim transaction succeeds (claiming domain).
- **FR-020**: Issue/PR text handling MUST enforce: no shell interpolation; no privileged tools during assessment; bounded text length; structured quoting; untrusted text MUST NOT be copied into control fields without validation; and **deterministic corroboration** (a reproducible base failure, unless explicitly `observational`) is required before implementation.

### Proposal gate (pre-implementation)

- **FR-021**: Lifecycle: `discovered → proposed → proposal_verified → claimed → implementing → canary → merged → monitoring → retained | reverted`, off-ramps `rejected | unsupported_scope | circuit_broken | cooldown`. An **independent assessor** MUST evaluate the proposal BEFORE implementation.
- **FR-022**: Advancement to `claimed` MUST meet the Policy Contract: rubric thresholds; blast-radius maximum; a reproducible base failure (unless `observational`); a supported diff surface; estimated file/line + budget bounds; a deterministic verifier rubric; and a machine-readable rejection reason otherwise.

### Evaluation contract (safely executable)

- **FR-023**: Each Attempt MUST carry a typed `EvaluationContract`: `base_reproducer`, `head_expectation`, `target_metric` {name, numerator, denominator, direction, min_effect}, `regression_suite` (trusted, pinned-`main` checks), `replay_mode` ∈ {deterministic_replay, mirrored_workload, not_replayable}.
- **FR-024**: `base_reproducer` MUST be one of: (a) a trusted test identifier from an allowlist; (b) a structured invocation interpreted by the trusted harness; or (c) a fixture generated into the protected replay corpus by a separate trusted process. A **free-form command string MUST NEVER be executed**. The trusted harness (pinned `main`) executes the untrusted SUT (candidate head); candidate-provided tests are advisory/untrusted.
- **FR-025**: High-severity sentinels (`InvariantEvent` from the existing `invariant` class; explicitly-defined `SecurityEvent`/`DataIntegrityEvent` deterministic sources) MAY trigger ONLY: block promotion, trip a breaker, quarantine an Attempt, revert a causally-attributed change, or notify/escalate. They MUST NOT bypass the proposal, implementation, evaluation, or merge gates.
- **FR-026**: Promotion requires fails-at-base/passes-at-head where `replay_mode` supports it; "tests pass" alone is insufficient; an `observational` Attempt (no reproducible base failure) is draft-PR + human-lane only and MUST NOT auto-promote in v1. Historical run logs MUST NOT be a canary signal.

### Canary model & retention

- **FR-027**: The operational canary for **retention** MUST be a **mirrored_workload** canary: real scheduled workloads execute from the canary branch over the window (so 7/30-day retention is meaningful). `deterministic_replay` is used ONLY for pre-merge base/head evaluation and MUST NOT be counted as retention; an Attempt whose change lacks a mirrored-workload signal is NOT live-eligible (stays shadow/observational).

### Rollback thresholds & attribution

- **FR-028**: Rollback thresholds come from the Policy Contract: health window + minimum observations; BOTH absolute and relative regression thresholds; zero/small-baseline behavior (withhold ordinary-metric reverts below the minimum sample; sentinels act immediately); explicit `target_metric` and `material_regression` formulas.
- **FR-029**: A revert MUST be causally attributed: excluding a failure as a provider/model outage REQUIRES ≥1 corroboration signal (contemporaneous base/control failure; provider health evidence; same failure on unrelated main/canary; failure before candidate code is reached). Error class alone (transient/unknown) is insufficient in either direction. A revert MUST pass an ancestry check and MUST NOT blind-revert over a subsequent human change.
- **FR-030**: Circuit breakers per the Policy Contract: ≤1 active Problem; ≤1 autonomous merge/24h; N auto-reverts in the breaker window disables promotion (discovery continues) until a defined manual re-enable; M failed Attempts per Problem → 30-day cooldown.

### Rollout & operations

- **FR-031**: Live auto-merge to `main` MUST be gated by the default-off `LLMXIVE_SELF_IMPROVEMENT_LIVE` flag AND the Policy Contract's live-eligibility thresholds (shadow sample minimum, proposal precision, 7/30-day retention, max false-revert rate). Flag off → merge target is a disposable canary branch; `main` is never modified. Flag on but App/branch-protection absent → fail closed.
- **FR-032**: Both crons MUST be idempotent, bounded, least-privilege, individually manually dispatchable, and share the single concurrency group; every proposal/decision/patch/verification/canary/merge/revert is immutable append-only provenance.
- **FR-033**: The About page + docs MUST describe the lane (behavior, safety envelope, seven trust domains, policy, flag/identity config); a step-by-step GitHub App setup walkthrough MUST be provided.
- **FR-034**: The Policy Contract MUST be a **versioned, protected artifact** (its own module + `policy_version`); candidate branches MUST NOT modify it; changing it is a normal reviewed human/PR change, never an autonomous one.

### Key Entities

- **ImprovementProblem**: `schema_version`, `problem_id`, `source_kind`(`errors`|`issue`), `canonical_source_key`, `title`, `evidence_digest`, evidence aggregate (via events), `current_disposition`, `revision`, `created_at`, `updated_at`, `cooldown_until`.
- **ImprovementAttempt**: `attempt_id`, `problem_id`, `parent_id`, `status`, `base_sha`, `branch`, `pr_number`, `proposer`{model, backend, prompt_version}, `verifier`{model, backend, prompt_version, identity}, `evaluator_version`, `evaluation_contract`, rubric scores {impact, confidence, tractability, testability}, `blast_radius`, `budget`{wall_clock_s, model_credits}, `budget_usage`, `promotion_mode`(`shadow`|`live`|`observational`), `unsupported_reason`, `attempt_count`, `created_at`, `updated_at`.
- **Event** (append-only): fields per FR-010.
- **EvaluationContract**: fields per FR-023.
- **PolicyContract**: `policy_version` + every numeric threshold below (protected).
- **ModelRequirement / ModelChain**: per the 026 dependency contract.
- **HighSeverityEvent**: a deterministic sentinel (`InvariantEvent`/`SecurityEvent`/`DataIntegrityEvent`) with the limited action set of FR-025.

## Policy Contract v1 (protected defaults; `policy_version = 1`)

These are concrete, versioned defaults, immutable by candidate branches (FR-034). Values are provisional starting points, tunable only via a reviewed human PR.

|Parameter|Default|
|-|-|
|Rubric minimum (impact, confidence, tractability, testability; 1–5)|each ≥ 3|
|Blast-radius maximum (1–5, lower safer)|≤ 2|
|Diff envelope|≤ 8 files, ≤ 300 changed lines|
|Base-failure requirement|valid `base_reproducer` fails at `base_sha`, unless `observational`|
|Health window|max(24h, next 3 mirrored-workload ticks)|
|Minimum observations before an ordinary-metric revert|5 relevant runs|
|Relative regression threshold (global hard-failure rate)|head − base ≥ +20% relative|
|Absolute regression threshold (dual-gate with relative)|AND ≥ +3 absolute failures|
|`material_regression`|any newly-failing trusted `regression_suite` check, OR the dual-gate global threshold met over ≥ min observations|
|Cost/runtime regression|> +25% over the Attempt's budget baseline|
|Freshness bound|recreate Attempt if `base_sha` > 200 commits behind `main` OR any touched file changed on `main` since `base_sha`|
|Breaker window|7 days|
|Auto-reverts to disable promotion|2 within the breaker window|
|Failed Attempts per Problem → cooldown|3 → 30-day cooldown|
|Provider-outage exclusion|requires ≥ 1 corroboration signal (FR-029)|
|Live-eligibility: shadow sample minimum|≥ 10 shadow-promoted Attempts observed|
|Live-eligibility: proposal precision|≥ 0.80 (verified/accepted)|
|Live-eligibility: 7-day retention|≥ 0.90|
|Live-eligibility: 30-day retention|≥ 0.80|
|Live-eligibility: max false-revert rate|≤ 0.10|

## Success Criteria *(mandatory)*

- **SC-001**: A Problem's `problem_id` is invariant under evidence growth/reordering while `evidence_digest`/`revision` change; a recurrence after `retained` produces a NEW Attempt under the same `problem_id` — verified by re-running discovery.
- **SC-002**: Concurrent mutations sharing `expected_revision` never lose/duplicate state (exactly one fast-forwards; the other recomputes); a kill-between-commit-and-label reconciles idempotently — verified by concurrency + fault-injection tests.
- **SC-003**: No Attempt is implemented before the independent assessor accepts it against the Policy Contract AND (unless `observational`) a `base_reproducer` fails at `base_sha` — verified against proposal-gate tests with the v1 thresholds.
- **SC-004**: Candidate code executes with no secrets, no repo-write token, and `--network none`; required checks are accepted only from named trusted Apps; a free-form `base_reproducer` is refused — verified against trust-domain + harness tests.
- **SC-005**: Promotion occurs only on fails-at-base/passes-at-head (where replayable) with no material regression per the v1 formula from trusted-App checks — verified on a real Attempt branch in shadow mode.
- **SC-006**: A causally-attributed harmful change is auto-reverted within the v1 window (provider outages without corroboration excluded; candidate-caused transient failures with corroboration included) with ancestry checks; repeated failures trip the breaker — verified against injected-regression + injected-outage shadow runs.
- **SC-007**: Only `StagePanelKickback` is excluded as soft; escalations are eligible; eligibility references only real classifier classes — verified against `_activity_severity` + the classifier.
- **SC-008**: All lane LLM calls resolve through the 026 `select()` contract; verifier independence records model+backend+prompt-version+identity — verified against the dependency contract.
- **SC-009 (acceptance demo for #1242)**: The lane runs end-to-end in shadow mode — real discovery → proposal-verified Attempt → claimed transaction → bounded implementation branch → trusted evaluation (base-fails/head-passes) → promotion into the canary branch → injected-regression attributed auto-revert — captured as concrete evidence on the PR.

## Delivery Slices

1. **Observation-only** — store + append-only events + optimistic-concurrency protocol; error mining; issue ranking/pagination; proposer + independent assessor; discovery/persistence domains; NO labels/branches/merges. (US1)
2. **Claiming** — the claim transaction (fetch-rebuild-verify-fast-forward), reconciliation, label/comment; one active Problem. (US2)
3. **Bounded draft PRs** — implementation domain; diff policy + budgets; network-denied container tests; draft PR; `unsupported_scope` routing (incl. error-derived human-lane issue). (US3)
4. **Trusted promotion into canary** — `EvaluationContract`; trusted harness + allowlisted `base_reproducer`; trusted-App required checks; App-token merge to canary. (US4)
5. **Post-merge monitoring** — policy thresholds; corroborated attribution; ancestry; auto-revert; breakers. (US5)
6. **Live-main promotion** — enabled only after the v1 live-eligibility thresholds are met AND flag on AND App+protection; else fail closed. (US6)
7. **Model-selection consolidation** — separate spec 026 + its own PR, landing before this lane (dependency, not built here).

## Assumptions

- The `gh` CLI is available/authenticated in the cron environment.
- A Dartmouth API key is present for free-model calls; `LLMXIVE_PAID_OPT_IN` is OFF by default and gated by the credit guard.
- **Model availability is timestamped evidence.** Verified by real calls on **2026-07-16**: `qwen.qwen3.5-122b` (default), `openai.gpt-oss-120b`, `google.gemma-4-31B-it` all live and free (cost 0) and passed code-reasoning + strict-JSON probes; `qwen.qwen3-vl:32b` for vision. Re-checked at runtime via the 026 contract.
- Live auto-merge is disabled until the maintainer creates the GitHub App, stores its secrets, and configures branch protection; until then the loop targets a disposable `self-improvement/canary` branch and never mutates `main`.
- Spec 026 lands first and provides the `select()` contract; slices 1–2's deterministic parts may be built before it.
- The lane reuses `advance_ledger.classify_message`, `web_data._activity_severity`/`_recent_activity`, the `gh` wrapper, `credits`, `project_lease` (contention only), and `commit-and-push.sh` (append-only writes only), per Constitution I.
- The self-improvement lane is separate from `Project`/`Stage`; it never routes work through the sandboxed research-project intake.
