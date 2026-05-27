# Research: Phase 4 Validation & Hardening

Phase 0 output for [plan.md](./plan.md). Each decision is grounded in the real code surfaces inspected during planning.

## R1 — Where do the FR-006 / FR-007 Planner gates attach?

**Decision**: Add one module `src/llmxive/speckit/_research_guard.py` exposing `assert_artifact_set_complete(files: dict[str,str])` (FR-005), `assert_urls_reachable(research_md_text, *, timeout=10)` (FR-006), and `assert_data_model_contracts_consistent(files: dict[str,str])` (FR-007). Call all three from `PlannerAgent.write_artifacts` (`plan_cmd.py:119`) — the completeness check FIRST (so a no-marker / partial response fails before per-file work), then **after** the per-file `refuse_if_diff` + `guard_emit` loop, the consistency + URL checks operating on the already-parsed `files` dict. On any violation, unlink all artifacts written this invocation (fail-closed), then raise — matching how `guard_emit` unlinks + raises `TemplateRefused`. The completeness gate (FR-005) is the analyze-F2 remediation: today `_split_multi_file` silently returns `{plan.md: text}` when no FILE markers are present, so a malformed/partial response would otherwise advance with an incomplete set.

**Rationale**: `write_artifacts` is the single choke point that has the full multi-file `files` mapping in hand (so FR-007 can compare `data-model.md` against `contracts/*`) and the raw `research.md` text (so FR-006 can scan URLs). Raising here propagates to the `SlashCommandAgent` base, which records `outcome: failed` and holds the stage at `clarified` — the exact behavior the existing template guard already relies on (verified: `plan_cmd.py` calls `guard_emit`, which raises `TemplateRefused`; the spec-011 plan documents that this yields `failed` + no advance).

**Alternatives considered**: (a) a separate `reference_validator`-style agent — rejected: that agent runs much later (review phase) and would not hold the *plan* stage; FR-006 must gate at plan time. (b) a validation-harness-only post-check — rejected by the 2026-05-21 clarification (the user chose to harden the agent so production gates at runtime).

## R2 — FR-006 URL extraction + reachability strategy

**Decision**: Extract candidate references from `research.md` with a URL regex (`https?://…`) plus bare `arXiv:NNNN.NNNNN` / `doi:…` identifiers normalized to `https://arxiv.org/abs/<id>` and `https://doi.org/<doi>`. For each, issue an HTTP `HEAD` (fall back to `GET` with `Range: bytes=0-0` when HEAD is 405/501) using stdlib `urllib.request` with a 10s timeout and a descriptive User-Agent. Accept only final status in **200–399**. Anything else — 4xx, 5xx, timeout, connection error, DNS failure, malformed URL — raises `UnreachableReference(url, reason)`. **No retries** (per clarification: hard-fail any non-2xx/3xx, transient or not).

**Rationale**: Stdlib only (Principle IV — no `requests` dependency). HEAD-first minimizes bandwidth; GET-range fallback handles servers that reject HEAD. The strict no-retry rule is the user's explicit choice; the accepted tradeoff (a transiently-down legitimate source fails the run) is documented in the spec's Assumptions. arXiv/doi normalization catches the common citation forms the LLM emits.

**Alternatives considered**: `requests` with retry/backoff — rejected (adds a dependency and contradicts the no-retry clarification). Treating bare identifiers as un-checkable — rejected: arXiv/doi are the most common citation forms and are cheaply verifiable.

## R3 — FR-007 data-model ↔ contracts consistency strategy

**Decision**: Parse entity names from `data-model.md` headings (`### <Entity>` / `## <Entity>` lines, and bolded `**<Entity>**:` list items, mirroring the spec-template's "Key Entities" style). Parse schema names from `contracts/*.yaml` filenames (`<schema>.schema.yaml` → `<schema>`) and from each YAML's top-level `title`/`$id` if present. A mismatch is: an entity with no corresponding schema, OR a schema with no corresponding entity (case-insensitive, hyphen/underscore/space-insensitive comparison). Any mismatch raises `InconsistentDataModel(missing_schemas, orphan_schemas)`.

**Rationale**: The Planner's own output contract (`agents/prompts/planner.md`) says `data-model.md` entity definitions must match `contracts/` schemas and that computational projects MUST include ≥1 schema — so the gate enforces a contract the prompt already states. Name-normalized matching tolerates the LLM's cosmetic naming variance (e.g., `Dipole Prediction` heading vs `dipole-prediction.schema.yaml`).

**Alternatives considered**: deep field-level schema/entity diffing — rejected as over-strict for v1 (the LLM's field naming varies legitimately); name-level correspondence is the testable invariant the spec states (FR-007: "an entity with no schema, or a schema with no entity").

## R4 — Per-round Tasker inspection capture (FR-003/FR-004) without changing decision logic

**Decision**: The Tasker's analyze loop (`tasks_cmd.py:188`, `for round_idx in range(TASKER_MAX_REVISION_ROUNDS)`) accumulates a list of round dicts `{round_index, analyze_report, mode_b_patch, verdict, files_rewritten, diffs}` on the agent instance. `_inspection.capture` gains an optional `rounds` parameter persisted under a new top-level `rounds` key in the record (the existing required keys are unchanged, so spec-011 records stay valid). The Planner record simply has `rounds: []`.

**Rationale**: This is observability, not a decision-logic change — FR-017 forbids changing what the Tasker *decides*, not whether it *records* what it did. Spec 011 established the same precedent (the inspection hook was added as instrumentation, not a bug fix). Capturing per-round detail is required by FR-004 ("the Tasker record MUST nest one sub-record per analyze round") and SC-009 (reconstruct every analyze round from the record alone).

**Alternatives considered**: writing per-round detail only to `tasker_rounds.yaml` and referencing it from the inspection record — rejected: SC-009 requires the inspection record be self-contained ("without consulting any other file").

## R5 — Does `--max-tasks 2` drive the whole phase?

**Decision**: Yes. The Tasker runs Mode-A generation **and** the entire Mode-A→Mode-B analyze loop within a single agent invocation (confirmed: the `range(TASKER_MAX_REVISION_ROUNDS)` loop is inside one `tasks_cmd` call, writing `tasker_rounds.yaml`/`human_input_needed.yaml` at the end). The orchestrator (`cli.py`, `for _ in range(max(1, args.max_tasks))`) advances one agent per step, routing by `current_stage`: `clarified`→Planner, `planned`→Tasker. So two steps (Planner, Tasker) carry a canonical from `clarified` to `analyzed`. This matches issue #48's "N = number of agents in this phase" = 2 and spec 011's `--max-tasks 2`.

**Rationale**: Verified directly in `cli.py` and `tasks_cmd.py`. No need to special-case per-round budgeting at the orchestrator level; the 900s budget applies per Tasker round inside the single invocation (FR-021).

**Alternatives considered**: raising `--max-tasks` to cover each round — rejected: rounds are internal to the one Tasker step, not separate orchestrator steps.

## R6 — FR-010 data-flow ordering check (no existing code gate)

**Decision**: Implement the ordering check as a function in `scripts/validate_phase4.py` (and unit-test it) rather than as a new Tasker gate. It parses `tasks.md` task lines, identifies producer tasks (those whose description writes/creates a path or downloads a dataset) and consumer tasks (those referencing the same path/dataset), and asserts no consumer precedes its producer for the two invariants the spec names: dataset-download-before-use and directory-create-before-write. A violation is reported as a finding (fails the validation for that canonical) and named in the phase report.

**Rationale**: `tasks_cmd.py` has no ordering validator today and FR-017 limits Tasker changes to the two pre-authorized Planner gates plus real bugs. A weak/heuristic ordering check living in the agent could cause false `human_input_needed` escalations in production; keeping it in the validation layer (where it gates the *validation*, not production) is the conservative choice and still satisfies FR-010/SC-004 ("verified automatically").

**Alternatives considered**: adding the ordering gate to the Tasker — deferred; if the validation finds real ordering defects on the canonicals, that is evidence to justify a future agent-side gate (separate spec), but it is not needed to validate Phase 4.

## R7 — Reset semantic (FR-018) — what to delete, what to keep

**Decision**: The driver deletes, under `projects/<id>/specs/001-<slug>/`: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, the `contracts/` directory, `tasks.md`, and `../.specify/memory/{tasker_rounds.yaml,human_input_needed.yaml}`. It PRESERVES `spec.md` (the Planner's input). Deleted paths are recorded under the inspection record's `reset_artifacts` key. The reset only fires when `current_stage == clarified` (FR-019: if state already advanced, the driver declines and reports "already past this phase").

**Rationale**: `spec.md` is the upstream Phase-3 product and the Planner's sole document input (`plan_cmd.build_prompt` reads `spec.md`); wiping it would destroy the input and break reproducibility. This differs from spec 011's reset (which wiped the whole `specs/<n>-<slug>/` because Phase 3 *created* it).

**Alternatives considered**: git-stash instead of delete — rejected: the inspection `reset_artifacts` record + git history already make wiped work recoverable; stashing complicates the clean-state guarantee.
