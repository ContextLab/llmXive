# Feature Specification: Autonomous Self-Improvement Lane

**Feature Branch**: `025-self-improvement-lane`
**Created**: 2026-07-16
**Status**: Draft (revision 2 — reworked after design review of rev 1)
**Input**: GitHub issue [#1242](https://github.com/ContextLab/llmXive/issues/1242) and its [design comment](https://github.com/ContextLab/llmXive/issues/1242#issuecomment-4987730544). Add two cron jobs: (1) learn from recurring errors and suggest an improvement *to llmXive* that can be planned/implemented/tested; (2) peruse open issues and submit high-value work to the pipeline. Unlike sandboxed research projects, success in these jobs changes **llmXive itself**.

## Overview

llmXive advances research projects through a ~34-state lifecycle, committing every artifact to git. Those projects are **sandboxed** under `projects/`: their agents never modify the platform. This feature adds a distinct **self-improvement lane** whose successful output is a **branch/PR against llmXive itself**.

The lane's safety case rests on **data contracts and trust boundaries**, not on adjectives. Every promotion decision is grounded in: a **stable two-part identity** (identity is not derived from mutable evidence); a **transactional, commit-persisted, append-only** state model; a **pre-implementation proposal gate** with an independent assessor and numeric thresholds; **five isolated trust domains** so candidate code can never touch a secret or the evaluator; a **typed, executable evaluation contract** (fails-at-base / passes-at-head) rather than "reread the logs"; and **concrete, attributed rollback thresholds** with ancestry checks. Live auto-merge to `main` is gated behind a **default-off flag** *and* explicit shadow-mode quality thresholds; until then the loop runs for real against a disposable canary branch and never mutates `main`.

Governed by the constitution ([.specify/memory/constitution.md](../../.specify/memory/constitution.md)): Single Source of Truth (I), Verified Accuracy (II), Real-World Testing (III), Cost Effectiveness / Free-First (IV), Fail Fast (V), Convergent Review (VI).

## Scope & Dependencies

**In scope**: the two discovery crons; the candidate lifecycle and transactional store; the pre-implementation proposal gate; the isolated implementation executor; the trusted evaluation + promotion path (shadow → canary branch); post-merge monitoring + auto-revert + circuit breakers; the default-off live-main flag; About-page/docs; the GitHub App setup walkthrough.

**Out of scope (separate prerequisite work)**: the **platform-wide model-selection consolidation**. Re-pointing *every* model-selection site (registry defaults, router peer chains `MODEL_FALLBACKS`, the execution tier-ladder, catalog filtering, and the many direct model pins) is a broad refactor not required to deliver the two crons. This spec **consumes** a minimal `select(requirement) -> ModelChain` interface (FR-001–FR-004); the full migration of existing call sites is deferred to its **own spec `026-model-selection-consolidation` with its own PR, which lands first** (maintainer decision, 2026-07-16). Spec 025 depends on 026: the lane's model calls use the consolidated `select()` mechanism delivered by 026.

**Reuse (Constitution I — do NOT reinvent)**: failure fingerprinting `advance_ledger.classify_message`; severity `web_data._activity_severity`; run-log reader `web_data._recent_activity`; GitHub `gh` wrapper pattern (`integrations/issues.py`); model router `backends/router.chat_with_model_fallback`; credit guard `backends/credits.paid_opt_in_enabled()`; the in-host lease `pipeline/project_lease.py`; the CAS persistence script `scripts/ci/commit-and-push.sh`.

## User Scenarios & Testing *(mandatory)*

The stories map 1:1 to the delivery slices (see "Delivery Slices"), each independently testable and shippable.

### User Story 1 - Observation-only discovery (Priority: P1)

Both crons run end-to-end to produce **proposal-verified candidates** — clustering real errors and ranking real issues, assessed by a proposer and an *independent* assessor against numeric thresholds — but take **no external action**: no branches, no PRs, no issue labels, no merges. Output is canonical candidate snapshots + append-only events committed to the repo.

**Why this priority**: Delivers the issue's core value (surface the platform's most consequential recurring defects and highest-value backlog work, with reproducible evidence) at zero external risk. Everything downstream builds on this store.

**Independent Test**: Run each cron against live `state/run-log` + `state/advance_errors` and the live open-issue set; assert candidates carry a stable `candidate_id`, an `evidence_digest`, a proposal, an evaluation contract, rubric scores, and a machine-readable accept/reject; assert soft kickbacks and automated/bot issues are excluded; assert re-running does not create duplicates.

**Acceptance Scenarios**:

1. **Given** a hard failure recurring across ≥3 distinct projects, **When** the error cron runs, **Then** one candidate is emitted whose `candidate_id = hash(schema_version, "errors", "<fingerprint>@<fp_schema_version>")` and whose evidence (run/project refs) is stored as append-only events, not in the identity.
2. **Given** the same cluster grows by one project on the next run, **When** the cron runs, **Then** the *same* `candidate_id` is updated (new `evidence_digest`, new event appended, `revision` incremented) — no duplicate candidate.
3. **Given** a cluster of only `StagePanelKickback`/`StagePanelEscalation` soft mechanics, **When** the cron runs, **Then** no candidate is emitted.
4. **Given** a proposal that fails the independent assessor's thresholds, **When** assessment runs, **Then** the candidate is marked `rejected` with a machine-readable reason and is NOT advanced to `claimed`.

---

### User Story 2 - Transactional claiming (Priority: P1)

At most one candidate at a time is atomically **claimed**: the lane acquires an in-host lease, compare-and-swaps the candidate snapshot against the latest `main`, applies a `self-improvement:claimed` label + proposal comment on the source issue (if any), and records the claim as one recoverable transaction — with defined reconciliation if either half (state commit / label) fails.

**Why this priority**: Two independent crons plus "one active candidate" plus mutable files plus issue-label side effects is a distributed-transaction problem; without it, concurrent runs silently drop work (the documented D16 race) or double-claim.

**Independent Test**: Simulate two concurrent claim attempts and assert exactly one wins (lease + CAS); kill a claim between the state commit and the label call and assert the reconciliation step converges (either completes the label or rolls the claim back), never leaving an orphaned claim.

**Acceptance Scenarios**:

1. **Given** two concurrent discovery runs, **When** both attempt to claim, **Then** the in-host lease + CAS-against-`main` admit exactly one; the loser observes the claim and yields.
2. **Given** a claim whose state commit landed but whose label call failed, **When** reconciliation runs, **Then** it re-applies the label (idempotently) or marks the claim incomplete — provenance is never overwritten in place.
3. **Given** an already-claimed source issue or one in cooldown, **When** discovery runs, **Then** it is not re-enqueued.
4. **Given** a candidate advancing, **When** each transition occurs, **Then** an append-only event `state/self-improvement/events/<id>/<event-id>.json` is written and the snapshot `state/self-improvement/candidates/<id>.json` is a projection rebuildable from those events.

---

### User Story 3 - Bounded draft PRs (Priority: P2)

The executor drains a claimed candidate: branches from `base_sha` in an isolated worktree, runs the implementer under a strict diff policy + budgets in the **implementation trust domain** (no production/repo secrets), runs offline tests, and opens a **draft PR** — with no merge. Candidates outside the supported envelope route to a human lane instead of counting as failures.

**Why this priority**: Turns a verified proposal into a concrete, reviewable change to llmXive itself — while keeping candidate code away from every secret and never yet touching a protected branch.

**Independent Test**: Feed a claimed candidate to the executor; assert branch creation from `base_sha`, diff obeys the allowlist + caps, a forbidden-path or over-cap diff is rejected with a machine reason, tests run with no secrets present, and a draft PR is opened. Assert an out-of-envelope candidate is routed to `unsupported_scope`/human_lane, not rejected+cooled.

**Acceptance Scenarios**:

1. **Given** a claimed candidate, **When** the executor runs, **Then** a branch `bot/self-improvement/<id>` is created from `base_sha` in an isolated checkout with no production secrets available to candidate code.
2. **Given** an implementer diff editing `.github/workflows/**`, secrets/auth, branch protection, the self-improvement policy/eval baseline, dep locks, or generated corpora, **When** the diff policy runs, **Then** the candidate is rejected before any test executes.
3. **Given** a legitimate issue requiring a change outside the supported diff surface, **When** the executor evaluates scope, **Then** it is routed to `unsupported_scope` (a labeled human-lane issue), not repeatedly rejected/cooled as an implementation failure.
4. **Given** a passing bounded implementation, **When** the executor completes, **Then** a **draft** PR is opened linking candidate id, evidence, evaluation contract, and offline-gate results.

---

### User Story 4 - Trusted promotion into a canary branch (Priority: P2)

A candidate is promoted into the **canary branch** only after a **typed evaluation contract** proves the change (fails-at-base / passes-at-head where replayable) with zero material regression, all required checks pass **from named trusted GitHub Apps** (no name spoofing), and the checks themselves run from **trusted code pinned to a main SHA** — never from the PR. Promotion uses an App token and never executes candidate code.

**Why this priority**: This is the autonomous promotion boundary. Its integrity depends on the trust domains and the executable metric, not on "tests pass".

**Independent Test**: In shadow mode, run the full gate on a candidate branch; assert promotion to the canary branch occurs only when every required trusted-App check is green AND the evaluation contract shows base-fails/head-passes with no material regression; assert a candidate whose `base_reproducer` does not fail at `base_sha` cannot promote.

**Acceptance Scenarios**:

1. **Given** a candidate with a valid `base_reproducer` failing at `base_sha` and passing at head, all trusted-App required checks green, and no material regression, **When** promotion runs in shadow mode, **Then** it merges into the canary branch (never `main` — the live flag is off).
2. **Given** a check reported by an App **not** on the trusted-App allowlist but with a required check name, **When** promotion evaluates gates, **Then** the spoofed check is not accepted and promotion is blocked.
3. **Given** a candidate whose tests pass but whose `base_reproducer` does not fail at `base_sha` (no demonstrated defect), **When** promotion runs, **Then** it is blocked (observational-only candidates require a separately-defined observational canary).
4. **Given** the evaluation shows target improvement but a regression in the trusted regression suite, **When** promotion runs, **Then** the merge is blocked.

---

### User Story 5 - Post-merge monitoring, attributed auto-revert & circuit breakers (Priority: P2)

After promotion (to the canary target in shadow mode), the lane monitors health over a **concretely-defined window with minimum sample sizes**, attributes failures to the candidate (excluding provider/model outages), checks ancestry before reverting, and auto-reverts genuine regressions. Repeated failures trip a global circuit breaker.

**Why this priority**: Makes autonomy *safe*. A blanket "failures rose 20%" is unsafe at small counts; attribution and ancestry prevent reverting for reasons unrelated to the change.

**Independent Test**: In shadow mode, inject a deliberate regression on the merged canary and assert an attributed, ancestry-checked revert is created+merged within the health window; assert a provider-outage transient does NOT trigger a revert; assert two reverts in the breaker window disable promotion while discovery continues.

**Acceptance Scenarios**:

1. **Given** a merged candidate whose target metric worsens beyond both the absolute and relative thresholds over ≥ the minimum observations, **When** monitoring runs, **Then** an ancestry-checked revert is created and merged automatically.
2. **Given** post-merge failures explained by a model/provider outage (transient class), **When** attribution runs, **Then** the failures are NOT attributed to the candidate and no revert occurs.
3. **Given** a human change landed on the target after the autonomous merge, **When** revert is considered, **Then** the lane does not blind-revert; it re-derives against current head (ancestry) or escalates.
4. **Given** two automatic reverts within the breaker window, **When** the next candidate is ready, **Then** promotion is disabled (discovery continues) until the manual re-enable procedure is followed.

---

### User Story 6 - Live-main promotion, metric-gated (Priority: P3)

Promotion targets `main` only when: the `LLMXIVE_SELF_IMPROVEMENT_LIVE` flag is on; a GitHub App identity + branch protection are configured; **and** shadow-mode has met explicit quality thresholds (proposal precision, 7/30-day retention, false-revert rate). Absent any of these while live, promotion fails closed.

**Why this priority**: The final, highest-consequence step. It must be earned by measured shadow-mode performance, not merely toggled.

**Independent Test**: With the flag on but the App/branch-protection absent, assert promotion refuses (fail-closed). With shadow metrics below threshold, assert live promotion is withheld.

**Acceptance Scenarios**:

1. **Given** the live flag on but no configured App/branch-protection, **When** promotion runs, **Then** it refuses rather than merging with a weaker guarantee.
2. **Given** the live flag on, App+protection configured, and shadow metrics ≥ thresholds, **When** promotion runs, **Then** the merge targets `main` via the App (author ≠ merger).
3. **Given** shadow metrics below the configured thresholds, **When** live promotion is attempted, **Then** it is withheld and the reason recorded.

---

### Edge Cases

- **Evidence growth vs identity**: a candidate's evidence set grows or reorders → `candidate_id` MUST stay stable (identity excludes evidence); only `evidence_digest`/`revision` change.
- **State committed but label failed (and reverse)**: reconciliation must converge without overwriting provenance.
- **Concurrent crons**: lost-update (D16) prevented by lease + CAS + append-only events under one concurrency group.
- **Corrupt/partial state**: a malformed JSONL line or missing ledger field is skipped, not fatal.
- **Ledger/run-log double counting**: cumulative `consecutive_count` is NOT summed with time-bounded run-log events; distinct affected projects is the primary support metric.
- **Incomplete issue pagination**: a truncated open-issue view fails closed (no candidates) until a terminal-page marker is observed.
- **Non-existent error classes**: the classifier has no security/data-loss class; eligibility must not reference them (see FR-013).
- **Small/zero baseline**: below the minimum sample size, ordinary-metric reverts are withheld; only high-severity sentinel signals act immediately.
- **Provider outage vs real regression**: transient/provider failures are not attributed to a candidate.
- **Human change after autonomous merge**: ancestry check prevents blind revert.
- **Check-name spoofing**: only checks from named trusted Apps are accepted.
- **Unsupported scope**: out-of-envelope candidates route to a human lane, not endless reject/cooldown.
- **Catalog absence**: a model absent from the live catalog is handled per the defined semantics (FR-004), not silently assumed available.
- **Recursive self-reference**: a generation may not modify the discovery/promoter/evaluator it depends on in the same generation.

## Requirements *(mandatory)*

### Model-selection interface (minimal; full consolidation deferred to a separate spec)

- **FR-001**: The lane MUST consume a single `select(requirement) -> ModelChain` helper mapping a call's requirements (capability tier, `independent_of`, `allow_paid`, `budget_hint`) to an ordered model chain; it MUST prefer free models and include a paid model only when `allow_paid` AND the credit guard (`paid_opt_in_enabled()` + budget headroom) permit.
- **FR-002**: Verifier **independence** MUST be characterized and recorded along ALL of: model id, provider/backend, prompt version, and the exact context supplied, plus a distinct verifier identity. `independent_of` (different model id) is necessary but NOT sufficient; **deterministic checks remain authoritative** over any LLM verifier.
- **FR-003**: The full migration of the existing selection sites (registry defaults, `MODEL_FALLBACKS`, execution tier-ladder, catalog filtering, direct pins) is OUT of scope here and specified separately; this spec MUST NOT silently change their default behavior (qwen3.5-122b remains the default).
- **FR-004**: Catalog semantics MUST be explicit: absence of a model from a successfully-fetched live catalog is treated as **unavailable for new selection** (distinct from the existing `is_free_model` static-allowlist fallback used only for known-free classification); model-availability MUST be treated as **timestamped, re-checked evidence**, never a durable assumption.

### Identity & deduplication

- **FR-005**: Candidate identity MUST use two separate identifiers: `candidate_id = hash(schema_version, source_kind, canonical_source_key)` (stable) and `evidence_digest = hash(canonicalized_evidence)` (mutable). Evidence MUST be appended as events; it MUST NOT be part of `candidate_id`.
- **FR-006**: `canonical_source_key` MUST be `github:<owner>/<repo>#<number>` for issues and `<fingerprint>@<fingerprint_schema_version>` for errors (so a classifier change is a new key, not a silent redefinition).

### Persistence, concurrency & provenance (transaction model)

- **FR-007**: Lane state MUST be persisted by committing to the repo via the existing `scripts/ci/commit-and-push.sh` (CAS rebase); writing files in an Actions runner without committing persists nothing.
- **FR-008**: Canonical snapshots live at `state/self-improvement/candidates/<id>.json` (no month partition); append-only events at `state/self-improvement/events/<id>/<event-id>.json`. The snapshot MUST be a projection rebuildable from events; provenance MUST NEVER be overwritten in place.
- **FR-009**: Snapshots MUST carry `schema_version`, `revision`, `updated_at`, and a `lease`. Discovery and promotion MUST be serialized under ONE GitHub `concurrency` group and MUST use `pipeline/project_lease.py` (in-host mutual exclusion) plus CAS-against-`main` (cross-runner).
- **FR-010**: Claiming MUST be one recoverable transaction (CAS the snapshot + commit state + apply the `self-improvement:claimed` label). Reconciliation MUST be defined for "state committed but label failed" and the reverse, converging idempotently.
- **FR-011**: At most one candidate MUST be in an active state (`claimed` through post-merge `monitoring`, i.e. before a terminal `retained`/`reverted`/off-ramp) at a time; automated submissions MUST NOT refill the queue.

### Discovery — errors (Cron 1)

- **FR-012**: The cron MUST read a bounded window of `state/run-log/<YYYY-MM>/*.jsonl` and current `state/advance_errors/` records, fingerprint failures ONLY via `advance_ledger.classify_message`, and exclude expected mechanics via the existing severity (`ok`/`soft`/`hard`; only `hard` eligible).
- **FR-013**: Eligibility MUST use only classes that exist in the canonical classifier (`transient/permanent/invariant/deterministic_repair/emitter_context`); it MUST NOT reference nonexistent "security"/"data-loss" error classes. A candidate MUST require ≥3 distinct affected projects, OR 2 projects + ≥5 recent occurrences; a single-project cluster qualifies ONLY if its class is `invariant` OR it originates from a defined high-severity sentinel signal (below).
- **FR-014**: High-severity emergency signals (which may bypass minimum-sample rules for immediate action) MUST come from **separate deterministic sentinel inputs** (e.g. an `InvariantEvent` from the existing invariant class; explicitly-defined `SecurityEvent`/`DataIntegrityEvent` sources such as a security scan or data-integrity assertion) — NOT from free-text exception classification.

### Discovery — issues (Cron 2)

- **FR-015**: The cron MUST enumerate the **complete** open-issue set via explicit API pagination and MUST observe a terminal-page marker before producing any candidate (a truncated view fails closed).
- **FR-016**: A deterministic filter MUST exclude bot-authored issues, `human-submission`/`new-paper` labels, issue #1242 itself, already-claimed/cooldown issues, and issues already satisfied by `main`; remaining issues are deterministically ranked; a proposer assesses ≤ top 10; an independent verifier re-ranks ≤ top 3; ≤ 1 candidate/day is enqueued.
- **FR-017**: Issue/PR text handling MUST enforce concrete properties (replacing "inert"): no shell interpolation; no privileged tools during assessment; bounded text length; structured quoting; untrusted text MUST NOT be copied into control fields without validation; and a candidate MUST have deterministic corroboration before implementation.
- **FR-018**: Enqueued issues MUST become `ImprovementCandidate`s (NOT routed through `_create_brainstormed_project`), marked `self-improvement:claimed`.

### Proposal gate (pre-implementation)

- **FR-019**: The lifecycle MUST be `discovered → proposed → proposal_verified → claimed → implementing → canary → merged → monitoring → retained | reverted`, with off-ramps `rejected | unsupported_scope | circuit_broken | cooldown` reachable from the appropriate earlier states. An **independent assessor** MUST evaluate the proposal BEFORE implementation.
- **FR-020**: Advancement to `claimed` MUST require: impact, confidence, tractability, testability each ≥ a defined threshold; blast_radius ≤ a defined maximum; a reproducible base failure (a `base_reproducer` that fails at `base_sha`) UNLESS the candidate is explicitly classified `observational`; a supported diff surface; estimated file/line + budget bounds; a deterministic verifier rubric; and a machine-readable rejection reason on failure.

### Trust domains (execution boundary)

- **FR-021**: The lane MUST enforce five isolated trust domains with explicit secret/token/network posture:
  - **Discovery**: issue read + model key (if required); NO repository write token.
  - **Implementation**: isolated environment; model access only during generation; NO production/repository secrets.
  - **Candidate testing**: NO secrets; read-only checkout; NO privileged cache restore; outbound network denied.
  - **Trusted evaluation**: policy/replay definitions loaded from a **pinned trusted `main` SHA**, never from the PR.
  - **Promotion**: GitHub App token only; MUST NEVER execute candidate code.
- **FR-022**: Required status checks MUST be accepted ONLY from a named trusted-GitHub-App allowlist (a candidate MUST NOT be able to spoof a required check by name). The protected policy/replay code MUST NOT be modifiable by the candidate branch.
- **FR-023**: The network posture MUST name a concrete mechanism: since GitHub-hosted runners lack a workflow-level outbound allowlist, the design MUST split networked generation from offline execution (or name the container/firewall used). Candidate-testing jobs MUST run with outbound network denied.

### Evaluation contract (executable canary)

- **FR-024**: Each candidate MUST carry a typed `EvaluationContract`: `base_reproducer` (command/fixture that fails at `base_sha`); `head_expectation` (expected pass at head); `target_metric` = {name, numerator, denominator, direction, min_effect}; `regression_suite` (trusted checks unrelated to the target); `replay_mode` ∈ {deterministic_replay, shadow_execution, not_replayable}.
- **FR-025**: Promotion MUST require "fails on base, passes on head" wherever the contract's `replay_mode` supports it. "Tests pass" alone is insufficient. Candidates without a valid reproducer MUST remain observational-only or proposal-only.
- **FR-026**: Historical run logs MUST NOT be used as a canary signal (they are outputs, not replayable inputs). The canary branch's health signal MUST be defined as either mirrored production state/traffic executed from it, or deterministic replay only.

### Rollback thresholds & attribution

- **FR-027**: Rollback MUST define concretely: health-window duration; minimum number of relevant observations and minimum sample size; BOTH absolute and relative failure thresholds; zero/small-baseline behavior (withhold ordinary-metric reverts below minimum sample; high-severity sentinels may act immediately); and explicit target-metric and global-metric formulas.
- **FR-028**: Failures MUST be attributed to the candidate and MUST exclude model/provider outages (transient class). A revert MUST perform an ancestry check (only revert a change still present / of which head is a descendant) and MUST NOT blind-revert when a subsequent human change has landed — it re-derives or escalates.
- **FR-029**: Circuit breakers MUST enforce: ≤1 active candidate; ≤1 autonomous merge / 24h; two automatic reverts within a defined breaker window disables promotion (discovery continues) until a defined manual re-enable procedure; three failed attempts per candidate → a 30-day cooldown.

### Rollout & operations

- **FR-030**: Live auto-merge to `main` MUST be gated by the default-off `LLMXIVE_SELF_IMPROVEMENT_LIVE` flag AND explicit shadow-mode quality thresholds (proposal precision, 7/30-day retention, false-revert rate). With the flag off, the merge target is a disposable canary branch and `main` is never modified. When live, if the App/branch-protection is absent, promotion MUST fail closed.
- **FR-031**: Both crons MUST be idempotent, bounded, least-privilege, individually manually dispatchable, and share the single concurrency group.
- **FR-032**: Every proposal, decision, patch, verification, canary measurement, merge, and revert MUST be recorded as immutable append-only provenance.
- **FR-033**: The About page and relevant documentation MUST describe the lane (behavior, safety envelope, trust domains, flag/identity config). A step-by-step GitHub App setup walkthrough MUST be provided.

### Key Entities

- **ImprovementCandidate** (snapshot): `schema_version`, `candidate_id`, `evidence_digest`, `source_kind`(`errors`|`issue`), `source_key`, `title`, `status`, `revision`, `created_at`, `updated_at`, `lease`, `attempt_count`, `rejection_reason`, `proposer`{model, backend, prompt_version}, `verifier`{model, backend, prompt_version, identity}, `evaluator_version`, rubric scores {impact, confidence, tractability, testability}, `blast_radius`, `base_sha`, `branch`, `pr_number`, `parent_id`, `evaluation_contract`, `budget`{wall_clock_s, model_credits}, `budget_usage`, `promotion_mode`(`shadow`|`live`), `unsupported_reason`.
- **EvidenceEvent** (append-only): a single reproducible observation — run id, project id, issue URL, fingerprint@schema, and/or commit SHA — plus timestamp; the ordered set yields `evidence_digest`.
- **EvaluationContract**: `base_reproducer`, `head_expectation`, `target_metric`{name, numerator, denominator, direction, min_effect}, `regression_suite`, `replay_mode`.
- **ModelRequirement / ModelChain**: capability tier (`cheap`|`standard`|`deep`|`vision`), `independent_of`, `allow_paid`, `budget_hint` → ordered primary + fallbacks (free-first).
- **HighSeverityEvent**: a deterministic sentinel (`InvariantEvent`/`SecurityEvent`/`DataIntegrityEvent`) that may authorize immediate action outside ordinary sample-size rules.
- **ProvenanceRecord**: an immutable, appended audit entry per lifecycle event.

## Success Criteria *(mandatory)*

- **SC-001**: A candidate's `candidate_id` is invariant under evidence growth/reordering while `evidence_digest`/`revision` change — verified by re-running discovery with added evidence and asserting a single stable id.
- **SC-002**: Concurrent discovery/promotion never lose or double-write state — verified by a concurrency test (lease + CAS + append-only events) and a kill-between-commit-and-label reconciliation test.
- **SC-003**: No candidate is implemented before an independent assessor accepts it against the numeric thresholds AND (unless observational) a `base_reproducer` fails at `base_sha` — verified against proposal-gate tests.
- **SC-004**: Candidate code and tests execute with no secrets, no repo-write token, and outbound network denied; required checks are accepted only from named trusted Apps — verified against trust-domain tests (secret-absence + spoofed-check rejection).
- **SC-005**: Promotion occurs only on fails-at-base/passes-at-head (where replayable) with no material regression from trusted-App checks — verified on a real candidate branch in shadow mode.
- **SC-006**: A harmful retained change is auto-reverted within the defined window with correct attribution (provider outages excluded) and ancestry checks; repeated failures trip the breaker — verified against injected-regression + injected-outage shadow runs.
- **SC-007**: Expected pipeline mechanics never generate candidates (zero soft-sourced candidates); the eligibility logic references only existing classifier classes — verified against the severity set + classifier.
- **SC-008**: Model selection returns a free chain by default and paid only under explicit allowance + budget headroom; verifier independence records model+backend+prompt-version — verified against the selection interface + credit guard.
- **SC-009 (acceptance demo for #1242)**: The lane runs end-to-end in shadow mode — real discovery → proposal-verified candidate → claimed transaction → bounded implementation branch → trusted evaluation (base-fails/head-passes) → promotion into the canary branch → injected-regression attributed auto-revert — captured as concrete evidence on the PR.

## Delivery Slices

1. **Observation-only** — canonical store + append-only events; error mining; issue ranking; proposer + independent assessor; NO labels/branches/merges. (US1)
2. **Claiming** — transactional claim/lease/CAS/reconciliation; proposal comment + label; one active candidate. (US2)
3. **Bounded draft PRs** — isolated implementation trust domain; diff policy + budgets; offline tests; draft PR; `unsupported_scope` routing. (US3)
4. **Trusted promotion into canary** — typed evaluation contract; trusted-App required checks from pinned main SHA; promotion by App token; merge to canary branch. (US4)
5. **Post-merge monitoring** — concrete thresholds; attribution; ancestry; injected-regression auto-revert; circuit breakers. (US5)
6. **Live-main promotion** — enabled ONLY after shadow precision/retention/false-revert thresholds are met AND flag on AND App+protection configured; else fail closed. (US6)
7. **Model-selection consolidation** — the platform-wide multi-site migration, delivered as **separate spec 026 + its own PR that lands before this lane** (a prerequisite dependency of the lane's model calls, not built here).

## Assumptions

- The `gh` CLI is available/authenticated in the cron environment (as in `maintenance.yml` / `integrations/issues.py`).
- A Dartmouth API key is present for free-model calls; `LLMXIVE_PAID_OPT_IN` is OFF by default and gated by the credit guard.
- **Model availability is timestamped evidence, not a durable assumption.** Verified by real calls on **2026-07-16**: `qwen.qwen3.5-122b` (default), `openai.gpt-oss-120b`, `google.gemma-4-31B-it` all live and free (cost 0) and passed code-reasoning + strict-JSON probes; `qwen.qwen3-vl:32b` available for the vision tier. This MUST be re-checked at runtime.
- Live auto-merge is disabled until the maintainer creates the GitHub App, stores its secrets, and configures branch protection; until then the loop targets a disposable `self-improvement/canary` branch and never mutates `main`.
- The lane reuses `advance_ledger.classify_message`, `web_data._activity_severity` / `_recent_activity`, the `gh` wrapper, `router`/`backends`, `credits`, `project_lease.py`, and `commit-and-push.sh` (Constitution I).
- The self-improvement lane is separate from `Project`/`Stage`; it never routes work through the sandboxed research-project intake.
