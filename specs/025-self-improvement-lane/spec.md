# Feature Specification: Autonomous Self-Improvement Lane

**Feature Branch**: `025-self-improvement-lane`
**Created**: 2026-07-16
**Status**: Draft (revision 6 — rev-5 + maintainer governance ruling: judgment reviews route through the shared `run_convergence` mechanism)
**Input**: GitHub issue [#1242](https://github.com/ContextLab/llmXive/issues/1242) and its [design comment](https://github.com/ContextLab/llmXive/issues/1242#issuecomment-4987730544). Add two cron jobs: (1) learn from recurring errors and suggest an improvement *to llmXive* that can be planned/implemented/tested; (2) peruse open issues and submit high-value work to the pipeline. Unlike sandboxed research projects, success in these jobs changes **llmXive itself**.

## Overview

llmXive advances research projects through a ~34-state lifecycle. Those projects are **sandboxed** under `projects/`: their agents never modify the platform. This feature adds a **self-improvement lane** whose successful output is a **branch/PR against llmXive itself**. Its safety case rests on data contracts, trust boundaries, and a versioned numeric policy — never on adjectives:

- **Global serialization** — a singleton **LaneCoordinator** record with a global `lane_revision`; all claims compare-and-swap against it (fixing the per-Problem CAS gap). The pre-merge pipeline is a strict singleton; post-merge monitoring is concurrent.
- **Problem vs. attempt identity** — a stable `problem_id` aggregates evidence; each fix try is a separate `ImprovementAttempt`.
- **Eight isolated trust domains** — discovery, persistence, claiming, implementation, **candidate-publisher**, candidate-testing, trusted-evaluation, promotion — so candidate code never touches a secret, a repo-write token, or the evaluator, and only non-candidate-executing domains hold credentials.
- **A paired-run operational canary** — a trusted controller on `main` materializes an immutable workload bundle and runs it against the control SHA and the candidate SHA in isolated namespaces; every metric is a **paired difference over identical inputs** (dissolving volume-normalization problems).
- **A safely-executable harness** — trusted harness (pinned `main`) runs the untrusted system-under-test (candidate head) in a hardened, network-denied, digest-pinned container; `base_reproducer`s are allowlisted/structured, never free-form commands.
- **A versioned, protected numeric policy** — every threshold, formula, and the issue-ranking function are concrete defaults, immutable by candidate branches.

Live auto-merge to `main` is gated behind a **default-off flag** *and* explicit shadow-mode quality thresholds; until then the loop runs for real against a disposable canary branch and never mutates `main`.

Governed by the constitution ([.specify/memory/constitution.md](../../.specify/memory/constitution.md)): Single Source of Truth (I), Verified Accuracy (II), Real-World Testing (III), Cost Effectiveness / Free-First (IV), Fail Fast (V), Convergent Review (VI). See "Constitution Compatibility."

## Scope & Dependencies

**In scope**: the two crons; the Problem/Attempt store + LaneCoordinator; the proposal gate; the implementation executor + candidate-publisher; the paired-run trusted evaluation + canary promotion; concurrent post-merge monitoring + attributed auto-revert + breakers; the default-off live-main flag; the versioned policy; About-page/docs; the GitHub App walkthrough.

**Out of scope — prerequisite `026-model-selection-consolidation`** (own spec + PR, lands first; maintainer decision 2026-07-16): the platform-wide migration of every model-selection site (registry defaults, `MODEL_FALLBACKS`, execution tier-ladder, catalog filtering, ~20 direct pins).

**026 dependency contract** (so 025 can be planned before 026 lands):
- **Import**: `from llmxive.backends.model_selection import select, ModelRequirement, ModelChain, ModelUnavailable`.
- **`select(req) -> ModelChain`**: deterministic given a live-catalog snapshot.
- **Types**: `ModelRequirement(capability: Literal["cheap","standard","deep","vision"], independent_of: str|None, allow_paid: bool, budget_hint: int|None)`; `ModelChain(models: list[str], resolved_at, catalog_digest)`.
- **Errors**: `ModelUnavailable` when no model satisfies the requirement.
- **Availability**: absence from a successfully-fetched live catalog = unavailable for new selection; `resolved_at`/`catalog_digest` make availability timestamped, re-checked per call. When `independent_of` cannot be honored (no distinct provider/model available), the lane **fails closed** (no LLM verification → the Attempt does not promote).
- **Slice sequencing**: slices 1–2's *deterministic* parts (clustering, filtering/ranking/pagination, store, transaction protocol) need no model and MAY precede 026; LLM parts (proposer, assessor, implementer, verifier) are blocked on 026 and MUST use this contract, never the router directly.

**Constitution Compatibility (governance — RESOLVED by maintainer ruling 2026-07-16: route via `run_convergence`)**: Constitution VI governs "every step that produces reviewable work," including code patches. Per the ruling, the lane's two **judgment reviews** — (1) the **proposal** ("is this a valid, worthwhile improvement to pursue?", before implementation) and (2) the **implemented patch** ("does this diff correctly and safely implement it?", before promotion) — route through the **shared `run_convergence`** mechanism (Constitution I + VI), NOT a bespoke assessor. The lane registers a self-improvement `ReviewSpec` (a new reviewable stage) with a code-patch reviewer panel; `run_convergence(spec, artifacts={proposal, diff, evidence}, producer=<implementer>)` returns `converged` (unanimous panel acceptance within the round cap, self-review prevented) as the review gate. The **deterministic policy pre-gates** (diff envelope, blast-radius, base-failure, evidence floor) and the **empirical trusted-evaluation harness** (offline paired tests + canary + trusted-App checks) are NOT "reviewable work" — they are mechanical/empirical guards that run alongside and compose with the convergence review. This satisfies Constitution VI with no category exception.
Separately, v1 evaluation is **offline-only** (FR-024): candidate code is exercised only against recorded response fixtures. Any change that cannot be exercised offline — notably changes to live model/provider-calling paths, or anything requiring a live external call to reproduce — is **`unsupported_scope`** in v1 (routed to humans), not merely "credential-touching source files." A trusted external-call broker is deferred to a future version.

**Reuse (Constitution I)**: `advance_ledger.classify_message`; `web_data._activity_severity`/`_recent_activity`; the `gh` wrapper; `credits.paid_opt_in_enabled()`; `project_lease.py` (in-host contention only — NOT cross-runner correctness); `scripts/ci/commit-and-push.sh` (append-only event/blob writes only — NOT the CAS mechanism).

## User Scenarios & Testing *(mandatory)*

Stories map 1:1 to delivery slices; each is independently testable.

### User Story 1 - Observation-only discovery (Priority: P1)

Both crons produce **proposal-verified candidate attempts** — clustering real errors, ranking real issues (by the policy's deterministic formula), passed through the deterministic policy pre-gates and then the shared `run_convergence` review panel — with **no issue/branch/PR/promotion side effects** (it does commit Problem/Attempt state through the privileged persistence domain).

**Independent Test**: Run each cron against live `state/run-log` + `state/advance_errors` + live open issues; assert stable `problem_id`, order-independent `evidence_digest`, an `EvaluationContract`, rubric scores, machine-readable accept/reject vs the policy; only `StagePanelKickback` excluded; re-run creates no duplicate Problems.

**Acceptance Scenarios**:
1. **Given** a hard failure across ≥3 projects, **When** the error cron runs, **Then** one `ImprovementProblem` (`problem_id = SHA256(canonical_json(schema_version, "errors", "<fingerprint>@<fp_schema_version>"))`) + one `proposed` Attempt, evidence as append-only events.
2. **Given** the cluster grows/reorders, **When** re-run, **Then** `problem_id` unchanged; `evidence_digest` = SHA-256 of the deduplicated, canonically-sorted, normalized evidence set (order-independent).
3. **Given** only `StagePanelKickback`, **Then** no Problem; **Given** a `StagePanelEscalation` (hard), **Then** eligible.
4. **Given** a proposal below any policy threshold, **When** the independent assessor runs, **Then** `rejected` with a machine-readable reason.

---

### User Story 2 - Global transactional claiming (Priority: P1)

At most one Problem occupies the pre-merge pipeline, established by CAS on the **singleton LaneCoordinator**: read `expected_lane_revision=R` and require `active_problem_id is None`; fetch `main`; rebuild the *entire* coordinator projection; verify still `R` and still idle; fast-forward push the claim + label; on any mismatch discard/recompute (never `-X theirs`).

**Independent Test**: Two concurrent workers claim **different** Problems at `lane_revision=R`; assert exactly one wins (the coordinator is a single record they both CAS) and the other recomputes and yields; kill a claim between the state push and the label call → reconciliation converges idempotently.

**Acceptance Scenarios**:
1. **Given** two concurrent claims of *different* Problems at `R`, **When** both persist, **Then** exactly one fast-forwards `lane_revision→R+1` and sets `active_problem_id`; the other's push is non-fast-forward or its rebuilt coordinator ≠ (R, idle) → it recomputes.
2. **Given** a claim whose coordinator event landed but whose label failed, **When** reconciliation runs, **Then** the label is re-applied idempotently (deterministic idempotency key) or the claim is recorded incomplete — events are never overwritten.
3. **Given** an already-claimed/cooldown source, **Then** not re-enqueued.
4. **Given** any transition, **Then** an append-only event (full field set, FR-011) is written and snapshots are projections rebuildable from events.

---

### User Story 3 - Bounded draft PRs via candidate-publisher (Priority: P2)

The implementation domain (no repo/prod secrets) produces a **validated patch bundle**; the separate **candidate-publisher** domain revalidates the envelope + forbidden paths, then — without executing any candidate code/hook/formatter — creates `bot/self-improvement/<problem-id>/<attempt-id>` from `base_sha`, pushes the exact validated tree, and opens a **draft PR** (branch/PR perms, cannot merge). Offline tests run earlier in a hardened container. Out-of-envelope work routes to a human lane.

**Independent Test**: Feed a claimed Attempt; assert the implementer runs with no secrets, the publisher rejects a forbidden-path/over-cap bundle before publishing, the published tree byte-matches the validated bundle digest, tests ran in the hardened container, and a draft PR is opened. Out-of-envelope → `unsupported_scope`.

**Acceptance Scenarios**:
1. **Given** a validated bundle, **When** the publisher runs, **Then** it creates the branch + draft PR from `base_sha` and pushes exactly the validated tree (digest match) without invoking candidate code.
2. **Given** a bundle editing `.github/workflows/**`, secrets/auth, branch protection, the policy/eval/harness baseline, dep locks, or generated corpora, **Then** it is rejected before publish.
3. **Given** an out-of-envelope candidate — source-issue: human-lane label/comment; **error-derived (no source issue)**: the claiming domain opens a new human-lane issue — neither counts as failure/cooldown.
4. **Given** a passing implementation, **Then** a **draft** PR linking `problem_id`/`attempt_id`, evidence, `EvaluationContract`, and gate results.

---

### User Story 4 - Trusted paired promotion into a canary branch (Priority: P2)

A trusted controller on `main` runs the Attempt's `EvaluationContract` **paired** (control SHA vs candidate SHA) over an immutable workload bundle in isolated namespaces, proving **fails-at-base / passes-at-head** via an allowlisted `base_reproducer` with no material paired regression; the promoter verifies every required check (head_sha, conclusion, trusted-App id, policy_version, non-stale) and merges with an App token that never executes candidate code.

**Independent Test**: In shadow mode, assert promotion only when the paired run shows base-fails/head-passes with no material regression, and every required check passes the full verification algorithm; a free-form `base_reproducer` or a spoofed/stale check blocks promotion.

**Acceptance Scenarios**:
1. **Given** an allowlisted `base_reproducer` failing at control and passing at candidate over W, a clean paired regression suite, and all required checks verified, **When** promotion runs in shadow, **Then** merge into the canary branch (never `main`).
2. **Given** a check whose creating App id is not on the trusted allowlist, or whose head_sha ≠ candidate head, or whose `policy_version` is wrong, **Then** it is not accepted and promotion is blocked.
3. **Given** a free-form command `base_reproducer`, **Then** it is refused (never executed).
4. **Given** paired target improvement but a newly-failing trusted regression check, **Then** blocked.

---

### User Story 5 - Concurrent post-merge monitoring & attributed auto-revert (Priority: P2)

After promotion, monitoring is **concurrent** (many merged Attempts monitored at once; only the pre-merge pipeline is singleton). Each Attempt's exposure interval + intervening changes are recorded; the lane corroborates attribution (transient class alone is insufficient), checks ancestry, and auto-reverts genuine, causally-attributed regressions. Repeated failures trip the breaker.

**Independent Test**: Inject a regression on a merged canary Attempt and assert an ancestry-checked, corroboration-backed revert within the window; a provider outage without corroboration does not revert; a candidate-caused transient failure with corroboration does; two reverts in the breaker window disable promotion while discovery continues; assert two Attempts can be monitored concurrently.

**Acceptance Scenarios**:
1. **Given** a merged Attempt whose paired target worsens beyond the policy thresholds over ≥ the minimum mature observations, **Then** an ancestry-checked revert is created + merged.
2. **Given** post-merge transient-class failures, **Then** a revert occurs ONLY with ≥1 corroboration signal (control fails on identical W; provider health; same failure on unrelated main/canary; failure before candidate code is reached).
3. **Given** a human change landed after the autonomous merge, **Then** no blind revert — re-derive against head (ancestry) or escalate.
4. **Given** two auto-reverts in the breaker window, **Then** promotion disabled (discovery continues) until manual re-enable.

---

### User Story 6 - Live-main promotion, metric-gated (Priority: P3)

Promotion targets `main` only when the flag is on, an App + branch protection are configured, and shadow-mode met the policy's live-eligibility thresholds. Absent any, fail closed.

**Acceptance Scenarios**:
1. Flag on, App/protection absent → refuse (fail-closed).
2. Flag on, configured, shadow metrics ≥ policy → merge to `main` via the App (author ≠ merger).
3. Shadow metrics below threshold → withheld, reason recorded.

---

### Edge Cases

- **Recurrence after `retained`**: same fingerprint returns → a NEW Attempt under the same `problem_id` with fresh base/branch/PR/contract; lineage distinguishes "first fix failed" from "problem recurred."
- **Freshness/drift**: before implement/promote, if `main` moved past the freshness bound from `base_sha` or any touched file changed, the old Attempt is terminated (`superseded`) and a new Attempt recreated + re-evaluated.
- **Global race on different Problems**: serialized by CAS on the singleton coordinator (blocker-1 test).
- **Persistence egress**: persistence commits to GitHub (GitHub-API egress only) — it is not `network:none`; only candidate-testing is `--network none`.
- **Artifacts crossing trust boundaries**: any artifact a candidate could influence (patch bundle, test output) is treated as untrusted by the privileged domain that consumes it and re-validated.
- **Harness import safety**: the trusted harness runs from a pinned-`main` checkout with a clean import path that excludes candidate-controlled paths; candidate code is imported only as the isolated SUT.
- **PR tampering**: a PR whose head_sha ≠ the recorded validated head, or manually modified, fails check verification → the Attempt is quarantined, not promoted.
- **No independent model available**: fail closed (no promotion).
- Plus: escalation-is-hard; transient≠outage; sentinel scope; observational never auto-promotes; incomplete-pagination fails closed; only real classifier classes; recursive-self-reference forbidden.

## Requirements *(mandatory)*

### Model-selection dependency (026)
- **FR-001**: All lane LLM calls MUST go through the 026 `select()` contract; the lane MUST NOT call the router/backends directly or embed a ranking. When `independent_of` cannot be satisfied, the lane fails closed.
- **FR-002**: The bespoke assessor is REPLACED by the shared `run_convergence` panel (FR-019, Constitution VI ruling). Reviewer/verifier **independence** within that panel MUST record model id, provider/backend, prompt + context digests, and reviewer identity; `independent_of` is necessary-not-sufficient; the deterministic pre-gates + empirical harness remain authoritative over any single LLM lens.
- **FR-003**: Slices 1–2 deterministic components MUST be implementable/testable with no model.

### Identity: Problem vs. Attempt
- **FR-004**: `problem_id = SHA256(canonical_json(schema_version, source_kind, canonical_source_key))`; key = `github:<owner>/<repo>#<n>` (issues) or `<fingerprint>@<fp_schema_version>` (errors). `fp_schema_version` bumps whenever `classify_message`'s fingerprint set/semantics change (a bump = a new Problem). All hashes are SHA-256 over canonical JSON.
- **FR-005**: Each try is an `ImprovementAttempt` (`attempt_id`, `problem_id`, `parent_id`, `base_sha`, `branch`, `pr_number`, `evaluator_version`, `evaluation_contract`, `status`); branches `bot/self-improvement/<problem-id>/<attempt-id>`; `attempt_count` increments when an Attempt enters `implementing`.
- **FR-006**: `evidence_digest = SHA256` of the deduplicated, canonically-sorted, normalized evidence-reference set — order-independent.

### Global concurrency & provenance
- **FR-007**: A singleton **LaneCoordinator** record (`state/self-improvement/coordinator.json`) holds `lane_revision`, `active_problem_id` + `active_attempt_id` (the pre-merge singleton), `monitored_attempts[]` (concurrent), `promotion_enabled`, `last_autonomous_merge_at`, `policy_version`. It is a projection rebuilt from a **dedicated coordinator event stream** at `state/self-improvement/events/coordinator/<event-id>.json` (coordinator events do not belong to any one Problem). Per-Problem events remain under `events/<problem-id>/`.
- **FR-008**: Every claim/promotion MUST CAS the coordinator: read `expected_lane_revision=R`; fetch `main`; rebuild the entire coordinator projection; verify `R` **and** the required precondition (`active_problem_id is None` for a claim); fast-forward push; on mismatch/non-fast-forward, discard and recompute. MUST NOT resolve conflicts with `-X theirs`. Correctness MUST NOT depend on schedules being the only writers; `project_lease` + a shared `concurrency` group reduce contention only.
- **FR-009**: State persists via append-only events at `state/self-improvement/events/<problem-id>/<event-id>.json`; snapshots (`problems/`, `attempts/`, `coordinator.json`) are projections; provenance is never overwritten. Each mutation with a side effect uses a **deterministic idempotency key** (per the transition table) so retries are safe.
- **FR-010**: Exclusivity is split: at most one Attempt in `claimed → implementing → promoting`; **multiple merged Attempts may be `monitoring` concurrently**, each recording its exposure interval + intervening changes for attribution.
- **FR-011**: Events carry `event_id` (deterministic idempotency key), `event_type`, `problem_id` (or the coordinator stream), optional `attempt_id`, the applicable `expected_lane_revision` (coordinator events) and/or `expected_problem_revision` (per-Problem events) + `resulting_*_revision`, `timestamp`, `actor` (trust-domain identity), `payload`, `schema_version`. A claim/promotion CASes the coordinator (`expected_lane_revision`); a Problem-scoped mutation CASes that Problem (`expected_problem_revision`).

### Trust domains (eight)
- **FR-012**: Eight isolated domains with explicit posture:
  |Domain|Secrets/tokens|Network|Runs LLM?|Runs candidate code?|
  |-|-|-|-|-|
  |Discovery|issue-read + model key|as model needs|yes|no (schema-validated artifact only)|
  |Persistence|narrow `contents: write`|**GitHub API only**|no|no (validates + commits artifact)|
  |Claiming|`issues: write`|GitHub API|no|no (labels/comments)|
  |Implementation|model key during generation only; NO prod/repo secrets|as model needs|yes (generation)|no|
  |Candidate-publisher|branch/PR write (cannot merge)|GitHub API|no|**no** (pushes validated tree, opens draft PR)|
  |Candidate-testing|NONE; read-only checkout; checkout creds disabled|**denied**|no|**yes** (untrusted, hardened container)|
  |Trusted-evaluation|fixtures/baselines from pinned `main`|controller egress for workload only|no|orchestrates the untrusted SUT|
  |Promotion|GitHub App token only|GitHub API|no|**never**|
- **FR-013**: The promoter MUST verify, for EVERY required check: exact candidate `head_sha`; completed status + accepted conclusion; check name; creating **GitHub App numeric id/slug** on the trusted allowlist; expected `evaluator_version`/`policy_version`; and MUST reject stale checks from an earlier head. Protected policy/eval/harness code MUST NOT be candidate-modifiable. The trusted harness MUST import from a pinned-`main` path that excludes candidate-controlled paths.
- **FR-014**: The candidate-testing container MUST be: a **digest-pinned** image; `--network none`; **non-root**; **read-only root fs** + trusted fixtures; a dedicated **size-limited output mount** (defined output schema + max artifact size); dropped Linux capabilities + `no-new-privileges`; **PID/memory/CPU/file-size/wall-clock limits**; no Docker socket; no credential mounts; no host workspace mount beyond the candidate tree; no shared caches with privileged jobs; `permissions: {}`. Artifacts leaving it are untrusted and re-validated by consumers.

### Discovery
- **FR-015**: (errors) Read a bounded window of run-log + `advance_errors`; fingerprint ONLY via `classify_message`; exclude ONLY `StagePanelKickback` (soft) via `_activity_severity`; escalations + other `hard` outcomes eligible; do NOT sum `consecutive_count` with time-bounded events (distinct projects = primary support). Eligibility uses only real classifier classes; ≥3 projects, OR 2 projects + ≥5 occurrences; single-project only if `invariant` or a deterministic high-severity sentinel (FR-023).
- **FR-016**: (issues) Enumerate the COMPLETE open set via explicit API pagination; a terminal-page marker MUST be observed before any candidate (truncation fails closed).
- **FR-017**: (issues) A deterministic filter excludes bot-authored, `human-submission`/`new-paper`, #1242, already-claimed/cooldown, and **already-satisfied-by-`main`** (closed-as-completed / referenced by a merged PR, OR — once a reproducer exists — a `base_reproducer` not failing at current `main`). Remaining issues are ranked by the **exact formula in the Policy Contract** (weights, normalization, caps, missing-value rules) with a stable ascending-issue-number tie-break; proposer assesses ≤ top 10; independent verifier re-ranks ≤ top 3; ≤ 1 candidate/day. An enqueued issue creates a `discovered/proposed` Attempt (NOT via `_create_brainstormed_project`); the `self-improvement:claimed` label/comment are applied ONLY after the US2 claim succeeds.
- **FR-018**: Issue/PR text handling MUST enforce: no shell interpolation; no privileged tools during assessment; bounded length; structured quoting; untrusted text not copied into control fields without validation; deterministic corroboration (a reproducible base failure, unless `observational`) before implementation.

### Proposal gate, evaluation & sentinels
- **FR-019**: Lifecycle + legal transitions are defined by the **Transition Table**. The two judgment reviews — the **proposal** (before implementation, gating `proposal_verified`) and the **implemented patch** (before promotion, gating `EvaluationPassed`) — MUST route through the shared `run_convergence` via a self-improvement `ReviewSpec` (`producer=<implementer>` prevents self-review); `converged` (unanimous acceptance within the cap) is the review gate. The **deterministic policy pre-gates** (rubric thresholds, blast-radius max, reproducible base failure unless `observational`, supported diff surface, file/line + budget bounds) run BEFORE convergence as mechanical eligibility guards with a machine-readable rejection; they are not themselves "review."
- **FR-020**: Each Attempt carries a typed `EvaluationContract` (`base_reproducer`, `head_expectation`, `target_metric`{name, numerator, denominator, direction, min_effect}, `regression_suite` = trusted pinned-`main` checks, `replay_mode` ∈ {deterministic_replay, mirrored_workload, not_replayable}). `base_reproducer` MUST be (a) a trusted test id from an allowlist, (b) a structured harness invocation, or (c) a fixture in the protected replay corpus — a **free-form command string MUST NEVER be executed**. The data model MUST distinguish **candidate-authored tests (advisory/untrusted)** from **trusted regression fixtures**.
- **FR-021**: Promotion requires paired fails-at-base/passes-at-head where `replay_mode` supports it; "tests pass" alone is insufficient; an `observational` Attempt is draft-PR + human-lane only and MUST NOT auto-promote in v1; historical run logs MUST NOT be a canary signal.
- **FR-022**: Evidence MUST be **redacted** (secret/PII scrubbing), size-capped, and retention-bounded before it is committed; compact logs may still carry secrets/PII.
- **FR-023**: High-severity sentinels (`InvariantEvent` from the `invariant` class; explicitly-defined deterministic `SecurityEvent`/`DataIntegrityEvent` sources) MAY ONLY block promotion, trip a breaker, quarantine an Attempt, revert a causally-attributed change, or notify/escalate — NEVER bypass the proposal/implementation/evaluation/merge gates.

### Operational canary (paired-run)
- **FR-024**: The operational canary MUST be a **paired-run** controlled from a trusted workflow on `main` (not by "creating a branch" — GitHub schedules run on the default branch, so the controller checks out/dispatches the recorded SHAs). v1 evaluation is **offline-only**: the controller (1) materializes an **immutable workload bundle W** = recorded real inputs + **recorded model/provider responses** harvested by the trusted controller from real recent runs (candidate code makes NO live external calls); (2) runs W against the **control SHA** and the **candidate SHA** via offline replay; (3) writes results to an **isolated per-Attempt namespace** (`state/self-improvement/canary/<attempt-id>/{control,candidate}/`) that MUST NOT mutate production/project state; (4) performs a **trusted paired comparison**. Control and candidate MUST see identical W.
- **FR-025**: The canary MUST use **immutable per-Attempt refs** `self-improvement/canary/<attempt-id>` (NOT one shared, reset branch — that would delete a still-monitored revision and make "revert" ambiguous). Monitoring targets the recorded candidate SHA; the ref is deleted only after the Attempt reaches `retained`/`reverted`. In live mode, paired monitoring uses the immutable base/candidate SHAs while `main` advances. **Retention** statistics come ONLY from `mirrored_workload` runs where W is **successively refreshed** across the window from real recent inputs (a single static corpus repeated for 30 days is NOT retention evidence); `deterministic_replay` is used ONLY for pre-merge base/head evaluation and MUST NOT count as retention. An Attempt whose change is exercisable only via a change to live-call paths (not reproducible offline) is `unsupported_scope` in v1.

### Rollback, attribution & rollout
- **FR-026**: Rollback thresholds + all formulas come from the Policy Contract (paired-difference `target_metric`, `material_regression`, absolute+relative dual-gate with volume normalization via identical W, min **mature** observations, censored 7/30-day cohorts, zero-denominator = withhold/fail-closed).
- **FR-027**: A revert MUST be causally attributed: excluding a failure as a provider/model outage REQUIRES ≥1 corroboration signal (FR/US5); error class alone is insufficient either direction. A revert MUST pass an ancestry check and MUST NOT blind-revert over **any later intervening change (human OR automated — another bot can create the same conflict)**; it re-derives against current head or escalates.
- **FR-028**: Circuit breakers per the Policy Contract (≤1 active pre-merge Attempt; ≤1 autonomous merge/24h; N auto-reverts in the breaker window → promotion disabled until manual re-enable; M failed Attempts/Problem → cooldown).
- **FR-029**: Live auto-merge to `main` gated by the default-off `LLMXIVE_SELF_IMPROVEMENT_LIVE` flag AND the Policy's live-eligibility thresholds. Flag off → canary branch target; `main` untouched. Flag on but App/branch-protection absent → fail closed.
- **FR-030**: Both crons idempotent, bounded, least-privilege, individually dispatchable, sharing one concurrency group; all provenance is immutable append-only.
- **FR-031**: About page + docs describe the lane (behavior, safety envelope, eight domains, policy, flag/identity); a step-by-step GitHub App setup walkthrough is provided.
- **FR-032**: The Policy Contract is a **versioned, protected module** (`policy_version`); candidate branches MUST NOT modify it; changes are normal reviewed human PRs.

### Key Entities
- **LaneCoordinator** (singleton): `lane_revision`, `active_problem_id`, `monitored_attempts[]`, `promotion_enabled`, `last_autonomous_merge_at`, `policy_version`.
- **ImprovementProblem**: `schema_version`, `problem_id`, `source_kind`, `canonical_source_key`, `title`, `evidence_digest`, evidence (via events), `current_disposition`, `revision`, timestamps, `cooldown_until`.
- **ImprovementAttempt**: fields per FR-005 + `proposer`/`verifier` {model, backend, prompt_digest, context_digest, identity}, rubric scores, `blast_radius`, `budget`/`budget_usage`, `promotion_mode` (`shadow`|`live`|`observational`), `unsupported_reason`, `exposure_interval`, timestamps.
- **Event** (append-only): fields per FR-011.
- **EvaluationContract**: fields per FR-020, with candidate-authored vs trusted fixtures distinguished.
- **PolicyContract**: `policy_version` + the tables below.
- **ModelRequirement/ModelChain**: per the 026 contract.
- **HighSeverityEvent**: deterministic sentinel with the limited action set of FR-023.

## Transition Table (legal transitions)

External side effects use **saga** (intent → side effect → observed) so a crash can be reconciled by observing whether the effect landed. Every **pre-merge off-ramp** (marked †) performs a `ClaimReleased` coordinator CAS that clears `active_problem_id` + `active_attempt_id`, so a terminal path can never leave the lane permanently occupied.

|From|Event|To|Idempotency key|Side effect|Reconciliation|
|-|-|-|-|-|-|
|∅|ProblemDiscovered|discovered|`(problem_id,"discover")`|write problem (no coordinator)|re-derive from events|
|discovered|Proposed|proposed|`(attempt_id,"proposed")`|write attempt|—|
|proposed|ProposalVerified|proposal_verified|`(attempt_id,"verified")`|record rubric|—|
|proposed/proposal_verified|Rejected|rejected (pre-claim)|`(attempt_id,"reject")`|— (no coordinator held)|—|
|proposal_verified|ClaimGranted|claimed|`(attempt_id,"claim",lane_rev)`|coordinator CAS: set `active_problem_id`+`active_attempt_id`; then label|re-apply label if missing|
|claimed|Implementing|implementing|`(attempt_id,"impl")`|— (`attempt_count`++)|—|
|claimed/implementing|ImplementationFailed †|impl_failed|`(attempt_id,"implfail")`|`ClaimReleased`|—|
|implementing|PublishRequested→Published|implementing(+PR)|`(attempt_id,"publish",head_sha)`|publisher: branch+draft PR|adopt existing branch/PR by head_sha|
|implementing|PublishFailed †|publish_failed|`(attempt_id,"pubfail")`|`ClaimReleased`|—|
|implementing|TestingFailed †|test_failed|`(attempt_id,"testfail")`|`ClaimReleased`|—|
|implementing|EvaluationFailed †|eval_failed|`(attempt_id,"evalfail")`|`ClaimReleased`|—|
|proposal_verified/claimed/implementing|ScopeUnsupported †|unsupported_scope|`(attempt_id,"unsupported")`|human-lane label or new issue; `ClaimReleased` if held|idempotent by marker|
|claimed/implementing|FreshnessStale †|superseded → new Attempt|`(attempt_id,"stale")`|close old; `ClaimReleased`; create + re-claim fresh Attempt|—|
|implementing|EvaluationPassed|promoting|`(attempt_id,"eval",head_sha)`|—|—|
|promoting|PromotionRequested|promotion_requested|`(attempt_id,"promo-req",head_sha)`|record intent (App merge side effect follows)|on crash, observe whether merge landed by head_sha|
|promotion_requested|PromotionObserved|merged+monitoring|`(attempt_id,"promo-obs",head_sha)`|**one coordinator CAS**: verify merge landed → clear active slot **and** add to `monitored_attempts` + record exposure interval|if merge did not land, retry/abort|
|monitoring|RevertRequested|revert_requested|`(attempt_id,"revert-req",reason)`|record intent (App revert side effect follows)|observe whether revert landed|
|revert_requested|RevertObserved|reverted|`(attempt_id,"revert-obs")`|verify revert landed; remove from `monitored_attempts`; delete canary ref|retry/abort|
|monitoring|Retained|retained|`(attempt_id,"retain")`|remove from `monitored_attempts`; delete canary ref|—|
|any pre-merge|BreakerTripped †|circuit_broken|`(attempt_id,"breaker")`|`promotion_enabled=false`; `ClaimReleased`|—|
|rejected/reverted / M failures per Problem|Cooldown|cooldown|`(problem_id,"cooldown")`|set `cooldown_until`|—|

`unsupported_scope`, `*_failed`, `retained`, `reverted`, `cooldown`, `circuit_broken` are terminal for that Attempt; a genuinely new proposal is a new Attempt (never a back-edge). `attempt_count` increments at `Implementing` and each `*_failed` counts toward the per-Problem failure cap. The intent/observed split closes the crash gap between the App merge/revert side effect and the recorded state; `PromotionObserved` merges "clear active slot" + "add to monitoring" into a single coordinator CAS.

## Policy Contract v1 (protected; `policy_version = 1`)

Concrete defaults, immutable by candidate branches (FR-032); tunable only via reviewed human PR.

**Thresholds**
|Parameter|Default|
|-|-|
|Rubric minimum (impact/confidence/tractability/testability, 1–5)|each ≥ 3|
|Blast-radius max (1–5, lower safer)|≤ 2|
|Diff envelope|≤ 8 files, ≤ 300 lines|
|Base-failure|valid allowlisted `base_reproducer` fails at control SHA, unless `observational`|
|`target_metric` promotion|paired: `candidate_rate − control_rate` in the improving direction ≥ `min_effect` (default `min_effect = 0.0` strict-better + CI lower bound > 0 over ≥ min mature obs)|
|Min mature paired observations (rate metrics)|≥ 20 (raised from 5)|
|`material_regression`|any newly-failing trusted `regression_suite` check on W, OR `(candidate_rate − control_rate)` in the worsening direction with the 95% CI excluding 0 over ≥ 20 paired obs|
|Cost/runtime regression|candidate median > 1.25 × control median on identical W|
|Freshness bound|recreate if `base_sha` > 200 commits behind `main` OR any touched file changed on `main` since `base_sha`|
|Breaker window|7 days|
|Auto-reverts → disable promotion|2 within the breaker window|
|Failed Attempts/Problem → cooldown|3 → 30-day cooldown|
|Provider-outage exclusion|requires ≥ 1 corroboration signal|
|Zero-denominator / immature cohort|withhold (fail-closed); do not promote/revert on no data|

**Budgets, caps & cadence**
|Parameter|Default|
|-|-|
|Wall-clock budget / Attempt|implementation ≤ 45 min; evaluation ≤ 30 min|
|Model-credit budget / Attempt|implementation ≤ 50 credits (~$0.05); evaluation ≤ 20|
|Issue text fed to an LLM|body ≤ 8,000 chars + up to 10 comments × ≤ 2,000 chars (truncated, structured-quoted)|
|Evidence per candidate|≤ 32 KB, secret/PII-redacted; retained 180 days|
|Candidate-testing container limits|wall-clock ≤ 20 min; memory ≤ 4 GB; CPU ≤ 2; PIDs ≤ 512; file-size ≤ 100 MB; output mount ≤ 4 MB (defined schema)|
|Controller / monitoring cadence|paired controller runs every 6 h (and on dispatch)|
|Health window (the SC-006 "v1 window")|max(24 h, next 3 mirrored-workload controller ticks)|
|Retention windows|7 days and 30 days (censored until matured)|
|Confidence-interval method|95% Wilson score interval on paired per-run rates; withhold if the interval is undefined (zero denominator)|

**Live-eligibility (shadow → live)**
|Parameter|Default|
|-|-|
|`beneficial_attempt_precision` = (retained Attempts with measured paired target improvement) / (all autonomously promoted Attempts with **mature** windows)|≥ 0.80|
|Mature promoted Attempts observed|≥ 10|
|7-day retention (censored cohort; matured only)|≥ 0.90|
|30-day retention (censored cohort; matured only)|≥ 0.80|
|`false_revert_rate` = (reverts where trusted paired re-evaluation shows the change did NOT cause the flagged regression) / (all autonomous reverts with mature confirmation)|≤ 0.10|

**Issue-ranking formula** (deterministic; missing value ⇒ 0; each term normalized to [0,1]):
`score = 0.30·label_weight + 0.20·recency + 0.20·repro_signal + 0.15·surface_match + 0.10·min(comment_count,10)/10 + 0.05·(1 − scope_estimate)`
Term definitions (all deterministic; NO model in the ranking):
- `label_weight` = max over the issue's labels of a fixed map `{security:1.0, data-loss:1.0, bug:0.9, regression:0.85, enhancement:0.5, documentation:0.3, question:0.2}`, default `0.4` for unmapped labels, `0.4` if none.
- `recency` = `exp(−age_days/30)`, `age_days` from `updated_at` (UTC).
- `repro_signal` = 1 if the body case-insensitively matches ANY of the fixed set {`"steps to reproduce"`, both `"expected"` and `"actual"`, a fenced code block ```` ``` ````, or `"Traceback (most recent call last)"`}, else 0.
- `surface_match` = |{`src/`,`tests/`,`.github/`} literally present in body| / 3.
- `scope_estimate` = `min(1, (min(distinct_file_paths_mentioned,8)/8 + min(body_len,8000)/8000)/2)` — a deterministic function of mentioned paths + body length (NOT model-derived).
- `comment_count` capped at 10.
- **Tie-break: ascending issue number.**

## Success Criteria *(mandatory)*

- **SC-001**: `problem_id` invariant under evidence growth/reorder while `evidence_digest`/`revision` change; recurrence after `retained` yields a new Attempt under the same `problem_id`.
- **SC-002**: Two workers claiming **different** Problems serialize on the singleton coordinator (exactly one wins; the other recomputes); kill-between-commit-and-label reconciles idempotently; every pre-merge off-ramp (reject/unsupported/stale/`*_failed`/breaker) releases the coordinator so the lane is never permanently occupied; a crash between the App merge/revert side effect and its recorded event reconciles via the saga's observed step.
- **SC-003**: No Attempt is implemented before the independent assessor accepts it vs the Policy AND (unless `observational`) an allowlisted `base_reproducer` fails at the control SHA.
- **SC-004**: Candidate code runs non-root, read-only-root, `--network none`, resource-capped, no secrets/socket/creds; the publisher pushes the exact validated tree without executing candidate code; a free-form `base_reproducer` and a spoofed/stale check are refused.
- **SC-005**: Promotion occurs only on **paired** base-fails/head-passes with no material paired regression and all required checks passing the full verification algorithm.
- **SC-006**: A causally-attributed harmful change is auto-reverted within the v1 window (provider outages without corroboration excluded; candidate-caused transient failures with corroboration included) with ancestry checks; two Attempts monitor concurrently; repeated failures trip the breaker.
- **SC-007**: Only `StagePanelKickback` is soft; escalations eligible; eligibility uses only real classifier classes.
- **SC-008**: All lane LLM calls resolve through the 026 `select()` contract; independence records model+backend+prompt/context digests+identity; no-independent-model ⇒ fail closed.
- **SC-009 (acceptance demo for #1242)**: The lane runs end-to-end in shadow mode — real discovery → proposal-verified Attempt → global claim → bounded implementation + published draft PR → trusted paired evaluation (base-fails/head-passes) → promotion into the canary branch → injected-regression attributed auto-revert — captured as concrete evidence on the PR.
- **SC-010**: Every boundary has a recovery test: state→label, patch→branch, branch→PR, check→merge, merge→monitor.
- **SC-011**: The proposal and patch judgment reviews route through the shared `run_convergence` (a self-improvement `ReviewSpec`); `converged` is the gate and self-review is prevented via `producer` — verified by a convergence-gated test (a patch the panel does not accept cannot reach `EvaluationPassed`).

## Delivery Slices

1. **Observation-only** — store + events + optimistic-concurrency + singleton coordinator; error mining; issue ranking/pagination; proposer + independent assessor; discovery/persistence domains; NO labels/branches/merges. (US1)
2. **Global claiming** — coordinator CAS transaction, reconciliation, label/comment. (US2)
3. **Bounded draft PRs** — implementation + candidate-publisher domains; hardened-container tests; diff policy + budgets; `unsupported_scope` routing. (US3)
4. **Trusted paired promotion** — controller + immutable workload + paired comparison; `EvaluationContract`; allowlisted `base_reproducer`; full check-verification; App-token merge to canary. (US4)
5. **Concurrent monitoring** — exposure intervals; corroborated attribution; ancestry; auto-revert; breakers. (US5)
6. **Live-main promotion** — v1 live-eligibility gates + flag + App/protection; else fail closed. (US6)
7. **Model-selection consolidation** — separate spec 026 + PR, lands first (dependency, not built here).

## Assumptions

- `gh` CLI available/authenticated; Dartmouth key present; `LLMXIVE_PAID_OPT_IN` OFF by default (credit-guarded).
- **Model availability is timestamped evidence.** Real-call verified 2026-07-16: `qwen.qwen3.5-122b` (default), `openai.gpt-oss-120b`, `google.gemma-4-31B-it` live+free (cost 0), passed code+JSON probes; `qwen.qwen3-vl:32b` for vision. Re-checked at runtime via 026.
- **Two separate prerequisites** (do not conflate): the **promotion identity** (a GitHub App, or a scoped promotion token) is needed from **slice 4** so the promotion domain performs ALL merges — including shadow merges into per-Attempt `self-improvement/canary/<attempt-id>` refs — as a non-candidate-executing, author≠merger identity; **branch protection + live-main authorization** (the default-off `LLMXIVE_SELF_IMPROVEMENT_LIVE` flag) is needed ONLY at **slice 6**. Until slice 6, promotion targets per-Attempt canary refs and never mutates `main`.
- Spec 026 lands first; slices 1–2 deterministic parts may precede it.
- Reuse per Constitution I: `classify_message`, `_activity_severity`/`_recent_activity`, `gh` wrapper, `credits`, `project_lease` (contention only), `commit-and-push.sh` (append-only writes only), and **`run_convergence`** (the judgment-review gate, per the Constitution VI ruling).
- The lane is separate from `Project`/`Stage`; it never routes work through the research-project intake. Its **judgment** review routes through the shared `run_convergence` (maintainer ruling 2026-07-16); the deterministic policy pre-gates + the empirical trusted-evaluation harness compose with it (see Constitution Compatibility).
