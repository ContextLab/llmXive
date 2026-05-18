---
description: "Task list for spec 012 — paper review convergence"
---

# Tasks: Paper Review Convergence

**Input**: Design documents from `/specs/012-paper-review-convergence/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Real-call + unit tests are REQUIRED by Constitution III (Robustness & Reliability). Every core function MUST have at least one real-call test that exercises the actual Dartmouth backend and filesystem state. Pure-logic helpers (severity ordering, ID canonicalization, schema validators) MUST also have unit tests.

**Organization**: Tasks are grouped by user story so each can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US6)
- File paths are absolute or repo-relative.

## Path Conventions

Single-project Python module. Source under `src/llmxive/`. Tests under `tests/{unit,real_call,integration}/`. Prompts under `agents/prompts/`. Spec artifacts under `specs/012-paper-review-convergence/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Wire up the new Stage enum values and the canonical ID helper. Both are pure additions to existing files; no new packages.

- [ ] T001 Add three new Stage enum values to [src/llmxive/types.py](src/llmxive/types.py): `PAPER_REVISION_IN_PROGRESS`, `READY_FOR_IMPLEMENTATION`, `PAPER_REVISION_BLOCKED`. Keep alphabetical order within the enum.
- [ ] T002 Update [src/llmxive/agents/lifecycle.py](src/llmxive/agents/lifecycle.py) `ALLOWED_TRANSITIONS`: add `PAPER_REVIEW → {PAPER_ACCEPTED, PAPER_REVISION_IN_PROGRESS, BRAINSTORMED}`, `PAPER_REVISION_IN_PROGRESS → {READY_FOR_IMPLEMENTATION, PAPER_REVISION_BLOCKED}`, `READY_FOR_IMPLEMENTATION → {PAPER_REVIEW}`, `PAPER_REVISION_BLOCKED → {PAPER_REVIEW, PAPER_MINOR_REVISION, BRAINSTORMED}`. Remove the now-superseded direct `PAPER_REVIEW → PAPER_MINOR_REVISION/...` transitions (the new flow routes through PAPER_REVISION_IN_PROGRESS).
- [ ] T003 [P] Add `action_item_id(text: str) -> str` helper to [src/llmxive/types.py](src/llmxive/types.py). Implements canonicalize-then-sha1 per research R1 (lowercase, strip punctuation runs, strip `Section \d+\.\d+` and `Figure \d+` references, collapse whitespace, return first 12 hex chars).

**Checkpoint**: New stages exist in the enum + transition graph; canonical ID helper available.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add `ActionItem` schema + extend `ReviewRecord` with `action_items` field + shared re-review prompt snippet. Every user story depends on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add `ActionItem` pydantic model to [src/llmxive/types.py](src/llmxive/types.py) with fields `id: str` (regex `^[0-9a-f]{12}$`), `text: str` (≤500 chars, non-empty), `severity: Literal["writing", "science", "fatal"]`. Add a class-level method `from_text(text, severity)` that auto-computes the id via `action_item_id`.
- [ ] T005 Extend `ReviewRecord` in [src/llmxive/types.py](src/llmxive/types.py) with `action_items: list[ActionItem] = Field(default_factory=list)`. Add a model_validator: if `reviewer_kind == "llm"` and `verdict in {"minor_revision", "full_revision", "major_revision_writing", "major_revision_science", "fundamental_flaws", "reject"}`, MUST have `len(action_items) >= 1`. Otherwise the existing score↔verdict validator continues unchanged.
- [ ] T006 [P] Create [agents/prompts/_shared/rereview_block.md](agents/prompts/_shared/rereview_block.md) with the two-question protocol snippet per research R4. Include the `{prior_action_items_yaml}` placeholder. Add a top-of-file comment explaining this is a shared snippet (single source of truth) and listing the consumers (paper_reviewer prompts).
- [ ] T007 Unit test in [tests/unit/test_action_item_schema.py](tests/unit/test_action_item_schema.py): cover (a) valid ActionItem round-trips, (b) `id` regex validation rejects bad strings, (c) `text` length cap is enforced, (d) `severity` enum is enforced, (e) `from_text` produces the same id for canonicalization-equivalent inputs (e.g., "Missing β_k" and "missing β_k value in Section 4.1.").
- [ ] T008 [P] Unit test in [tests/unit/test_review_record_action_items.py](tests/unit/test_review_record_action_items.py): cover (a) ReviewRecord with empty action_items + verdict=accept is valid, (b) ReviewRecord with empty action_items + verdict=minor_revision RAISES ValidationError, (c) back-compat: a YAML file without action_items field loads with `action_items=[]`.
- [ ] T009 [P] Unit test in [tests/unit/test_action_item_id_canonicalize.py](tests/unit/test_action_item_id_canonicalize.py): assert canonicalize absorbs casing, leading/trailing whitespace, `Section X.Y` refs, `Figure N` refs, and adjacent punctuation; verify ID collision rate is acceptable on a corpus of synthetic action-item phrasings.

**Checkpoint**: Schema + ID generation + shared snippet are in place. The Stage enum and transition graph are consistent. From here, the user stories can be tackled in priority order.

---

## Phase 3: User Story 6 - Every review record carries structured action items (Priority: P1) 🎯 PREREQUISITE FOR ALL OTHER STORIES

**Goal**: Reviewers emit `action_items` in their YAML frontmatter; old records still load (back-compat). This is a structural prerequisite for US1, US2, US3, US4, US5.

**Independent Test**: Drive one specialist reviewer against a fixture project; assert the emitted ReviewRecord has parseable, schema-valid `action_items` matching what the LLM produced.

### Implementation for User Story 6

- [ ] T010 [US6] Update [agents/prompts/paper_reviewer.md](agents/prompts/paper_reviewer.md) (the lead reviewer prompt) to instruct the LLM to emit an `action_items` block in YAML frontmatter. Include the canonical severity definitions (writing / science / fatal) from contracts/action_item.md.
- [ ] T011 [US6] Update each of the 12 specialist prompts: [agents/prompts/paper_reviewer_claim_accuracy.md](agents/prompts/paper_reviewer_claim_accuracy.md), [agents/prompts/paper_reviewer_code_quality_paper.md](agents/prompts/paper_reviewer_code_quality_paper.md), [agents/prompts/paper_reviewer_data_quality_paper.md](agents/prompts/paper_reviewer_data_quality_paper.md), [agents/prompts/paper_reviewer_figure_critic.md](agents/prompts/paper_reviewer_figure_critic.md), [agents/prompts/paper_reviewer_jargon_police.md](agents/prompts/paper_reviewer_jargon_police.md), [agents/prompts/paper_reviewer_logical_consistency.md](agents/prompts/paper_reviewer_logical_consistency.md), [agents/prompts/paper_reviewer_overreach.md](agents/prompts/paper_reviewer_overreach.md), [agents/prompts/paper_reviewer_safety_ethics.md](agents/prompts/paper_reviewer_safety_ethics.md), [agents/prompts/paper_reviewer_scientific_evidence.md](agents/prompts/paper_reviewer_scientific_evidence.md), [agents/prompts/paper_reviewer_statistical_analysis.md](agents/prompts/paper_reviewer_statistical_analysis.md), [agents/prompts/paper_reviewer_text_formatting.md](agents/prompts/paper_reviewer_text_formatting.md), [agents/prompts/paper_reviewer_writing_quality.md](agents/prompts/paper_reviewer_writing_quality.md). Each gets the same shared `action_items` instruction block (use a shared include via render_prompt's template engine — single source of truth per Constitution I).
- [ ] T012 [US6] Modify [src/llmxive/agents/paper_reviewer.py](src/llmxive/agents/paper_reviewer.py) `handle_response`: parse `action_items` from the YAML frontmatter and include it in the `ReviewRecord.model_validate(front)` call. The existing score-normalization stays.
- [ ] T013 [US6] Real-call test in [tests/real_call/test_paper_reviewer_emits_action_items.py](tests/real_call/test_paper_reviewer_emits_action_items.py): drive ONE specialist (`paper_reviewer_jargon_police`) against PROJ-578 with the Dartmouth backend; assert the resulting review file has ≥1 action_item with valid id/text/severity AND the IDs round-trip through `action_item_id`. Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: Every new review record carries structured action_items. Old records still load. The pipeline can now reason about per-concern routing.

---

## Phase 4: User Story 1 - A genuinely-good paper converges to acceptance (Priority: P1) 🎯 MVP

**Goal**: When every specialist's most-recent verdict is `accept`, the project advances to `PAPER_ACCEPTED`. No more "but jargon_police always finds one nit" stall.

**Independent Test**: Drive a fixture project where every specialist's most-recent record has verdict=accept; assert the advancement evaluator transitions to PAPER_ACCEPTED.

### Implementation for User Story 1

- [ ] T014 [US1] Modify [src/llmxive/agents/advancement.py](src/llmxive/agents/advancement.py) `_all_specialists_accept`: change semantics from "every specialist has EVER accepted" to "every specialist's MOST-RECENT non-stale record has verdict=accept". Add helper `_most_recent_per_specialist(records, live_hash)` that returns one record per specialist (the latest by `reviewed_at` whose `artifact_hash == live_hash`).
- [ ] T015 [US1] Modify the PAPER_REVIEW branch in `advancement.py`: REMOVE the `accept_total >= PAPER_ACCEPT_THRESHOLD` gate (the all-accept gate is now the sole criterion). Keep the no-blocking-citations gate. On all-accept → transition to PAPER_ACCEPTED.
- [ ] T016 [US1] Unit test in [tests/unit/test_advancement_all_accept_gate.py](tests/unit/test_advancement_all_accept_gate.py): construct synthetic records covering (a) 12 specialists all accept → PAPER_ACCEPTED, (b) 11 accept + 1 minor_revision → NOT accepted, (c) 12 accept but 1 has stale artifact_hash → that specialist is treated as "no review" so 11 specialists effective → NOT accepted, (d) one specialist has 2 records (older=minor_revision, newer=accept) → MOST-RECENT is accept so passes for that specialist.
- [ ] T017 [US1] Real-call test in [tests/real_call/test_advancement_paper_accepted_real.py](tests/real_call/test_advancement_paper_accepted_real.py): use a real fixture project where all specialists accepted; run the advancement evaluator; assert the project transitions to PAPER_ACCEPTED and a publication-record artifact is emitted. Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: A paper that genuinely passes review can reach PAPER_ACCEPTED.

---

## Phase 5: User Story 4 - Severe science concerns reject the paper back to the backlog (Priority: P1)

**Goal**: When any specialist's most-recent action_items contains a `fatal` severity item, route to BRAINSTORMED with rejection rationale.

**Independent Test**: Construct synthetic reviews with one fatal action_item; assert project transitions to BRAINSTORMED + rejection rationale is appended to idea record.

### Implementation for User Story 4

- [ ] T018 [US4] Add `_max_severity_across_specialists(records, live_hash) -> Literal["writing", "science", "fatal"] | None` helper to [src/llmxive/agents/advancement.py](src/llmxive/agents/advancement.py). Returns None if all per-specialist most-recent verdicts are accept; otherwise the highest severity in any non-accept's action_items list. Severity ordering: `writing < science < fatal`.
- [ ] T019 [US4] In `advancement.py` PAPER_REVIEW branch: when `_max_severity_across_specialists` returns `fatal`, transition to BRAINSTORMED. Construct the rejection rationale by deduplicating `fatal` action_items across specialists and append to the idea record at `projects/<PROJ-ID>/idea/*.md` (use the canonical idea file matching the project's slug; if multiple, pick the first by mtime).
- [ ] T020 [US4] Unit test in [tests/unit/test_advancement_fatal_routing.py](tests/unit/test_advancement_fatal_routing.py): cover (a) one fatal among many writing/science → BRAINSTORMED, (b) zero fatal → not BRAINSTORMED, (c) rejection rationale text contains all unique fatal items by ID.
- [ ] T021 [US4] Real-call test in [tests/real_call/test_advancement_reject_to_brainstormed_real.py](tests/real_call/test_advancement_reject_to_brainstormed_real.py): construct a fixture project + force one fatal action_item via fixture review; run advancement; verify file system state (idea file has new rejection rationale section, project state is BRAINSTORMED). Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: Fatal-flagged papers are rejected to the backlog with traceable rationale.

---

## Phase 6: User Story 2 - Writing-only concerns trigger an auto-planned revision (Priority: P1)

**Goal**: When the max severity across specialists is `writing` (and not fatal), auto-kick a paper-revision spec pipeline. Project transitions to PAPER_REVISION_IN_PROGRESS → READY_FOR_IMPLEMENTATION.

**Independent Test**: Construct a fixture project + reviews with writing action_items; run advancement; verify the project transitions to PAPER_REVISION_IN_PROGRESS, then revision_planner runs the 5 stages, then transitions to READY_FOR_IMPLEMENTATION with revision_spec_path set.

### Implementation for User Story 2

- [ ] T022 [US2] Create [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py). Public API: `run_revision_pipeline(project_id, action_items, revision_kind) -> RevisionSpecResult`. Internals: invokes `llmxive.speckit.slash_command.run()` for each of `specify`, `clarify`, `plan`, `tasks`, `analyze` in sequence; each stage's output feeds the next; on success returns ready_for_implementation; on analyzer-stuck (3 iterations of remediation, still findings) returns blocked.
- [ ] T023 [US2] Add `RevisionSpecResult` dataclass to [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py) with fields `revision_spec_path`, `stage_results`, `final_outcome` (ready_for_implementation | paper_revision_blocked), `block_diagnostic` (None unless blocked).
- [ ] T024 [US2] Implement `_seed_specify_input(action_items)` in [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py): consolidate action_items (deduplicate by id, preserve severity ordering), build the specify input text "Address these reviewer-raised action items: ..." that becomes the spec's `$ARGUMENTS`.
- [ ] T025 [US2] Implement `_write_result_yaml(spec_dir, result)` in [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py): write a `result.yaml` to the revision spec dir per the contract at [specs/012-paper-review-convergence/contracts/revision_spec.md](specs/012-paper-review-convergence/contracts/revision_spec.md).
- [ ] T026 [US2] Implement `_update_index(repo_root, entry)` in [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py): atomically append to `state/revisions/index.yaml` so an implementer can discover ready or blocked revisions.
- [ ] T027 [US2] Modify [src/llmxive/agents/advancement.py](src/llmxive/agents/advancement.py) PAPER_REVIEW branch: when max severity is `writing` and no fatal, transition project to PAPER_REVISION_IN_PROGRESS, then immediately call `revision_planner.run_revision_pipeline(..., revision_kind="paper_writing")`. On success → transition to READY_FOR_IMPLEMENTATION with `revision_spec_path`. On blocked → transition to PAPER_REVISION_BLOCKED.
- [ ] T028 [US2] Add `revision_spec_path: str | None = None` field to the Project model in [src/llmxive/state/project.py](src/llmxive/state/project.py) (or wherever Project is defined). Default None. Set only when stage == READY_FOR_IMPLEMENTATION.
- [ ] T029 [US2] Unit test in [tests/unit/test_revision_planner_unit.py](tests/unit/test_revision_planner_unit.py): use a stubbed `slash_command.run` (NOT a mock of the LLM; the stub is at the slash-command-orchestrator level) to verify the 5-stage state machine; cover (a) all 5 succeed → ready_for_implementation result, (b) analyzer stuck → blocked result with diagnostic.
- [ ] T030 [US2] Real-call test in [tests/real_call/test_writing_revision_pipeline_real.py](tests/real_call/test_writing_revision_pipeline_real.py): drive a small fixture (home-grown project, not arxiv-intake) with writing action_items through the full pipeline; assert all 5 speckit artifacts exist; project state moves to READY_FOR_IMPLEMENTATION; revision_spec_path resolves to a real directory. Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: Writing-class revisions are auto-planned and the project is queued for implementation.

---

## Phase 7: User Story 3 - Mild science concerns trigger a major revision that re-enters research (Priority: P1)

**Goal**: When max severity is `science` (and not fatal), auto-kick a research-spec revision pipeline. Project routes through PAPER_REVISION_IN_PROGRESS to READY_FOR_IMPLEMENTATION.

**Independent Test**: Construct synthetic reviews with science action_items; run advancement; verify a research-revision spec is generated and project moves to READY_FOR_IMPLEMENTATION.

### Implementation for User Story 3

- [ ] T031 [US3] In [src/llmxive/agents/advancement.py](src/llmxive/agents/advancement.py) PAPER_REVIEW branch: when max severity is `science` and no fatal, transition to PAPER_REVISION_IN_PROGRESS and call `revision_planner.run_revision_pipeline(..., revision_kind="paper_science")`. On success → READY_FOR_IMPLEMENTATION. On blocked → PAPER_REVISION_BLOCKED.
- [ ] T032 [US3] In [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py): the `revision_kind="paper_science"` branch seeds the specify input differently — the action items are framed as research-question gaps rather than writing nits, and the spec is rooted at `specs/auto-revisions/<PROJ-ID>/round-<N>/` with a `kind: paper_science` marker.
- [ ] T033 [US3] Unit test in [tests/unit/test_revision_planner_science_kind.py](tests/unit/test_revision_planner_science_kind.py): verify the science branch passes the correct kind to slash_command.run and the generated spec contains a "research-question" framing.
- [ ] T034 [US3] Real-call test in [tests/real_call/test_science_revision_pipeline_real.py](tests/real_call/test_science_revision_pipeline_real.py): drive a fixture with one science action_item; assert science-revision spec is generated. Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: Science-class revisions re-enter the research-spec pipeline.

---

## Phase 8: User Story 5 - Re-review protocol (Priority: P2)

**Goal**: When a specialist has ≥1 prior review for the current project, that specialist's prompt switches to the two-question protocol. Without this, the convergence guarantee from US1/US2 is *eventual*; with it, convergence is *fast*.

**Independent Test**: Construct a fixture project with 1 prior round of reviews containing action_items. Drive a second round. For each specialist that has a prior record, assert its prompt includes the re-review block; assert the model emits verdict=accept when its prior items are addressed (use a fixture where the source was modified to address them).

### Implementation for User Story 5

- [ ] T035 [US5] Add `_prior_reviews_for_specialist(project_id, specialist_name) -> list[ReviewRecord]` helper to [src/llmxive/state/reviews.py](src/llmxive/state/reviews.py). Returns all prior records for THIS project AND THIS specialist, sorted by `reviewed_at` ascending. Empty list if none.
- [ ] T036 [US5] In [src/llmxive/agents/paper_reviewer.py](src/llmxive/agents/paper_reviewer.py) `build_messages`: when prior reviews exist for THIS specialist, render the shared `_shared/rereview_block.md` snippet (with `{prior_action_items_yaml}` substituted from the most-recent prior record's action_items) and prepend it to the user prompt. Otherwise, the prompt is unchanged.
- [ ] T037 [US5] Add `_load_rereview_snippet()` helper to [src/llmxive/agents/paper_reviewer.py](src/llmxive/agents/paper_reviewer.py) (or to `agents/prompts.py` if a render helper already exists). Returns the rendered snippet given prior action_items.
- [ ] T038 [US5] Unit test in [tests/unit/test_rereview_per_specialist_toggle.py](tests/unit/test_rereview_per_specialist_toggle.py): cover (a) specialist with no prior records → no rereview block in prompt, (b) specialist with 1 prior record → block IS present and action_items are listed, (c) specialist with 2+ prior records → ONLY the most-recent prior is included.
- [ ] T039 [US5] Real-call test in [tests/real_call/test_rereview_protocol_real.py](tests/real_call/test_rereview_protocol_real.py): drive a fixture project through round 1 (manufacture some action_items), then drive round 2 with the same source. Assert the round-2 review references prior action items by their IDs AND emits a verdict consistent with the two-question protocol (either accept-all-addressed, or list-unaddressed-with-original-IDs). Additionally, COMPUTE the ID-stability rate as `(# round-2 items whose id matches a round-1 item's id) / (# round-2 items)`; assert ≥0.8 per SC-005. Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: Re-review focuses on diff-check, not fresh critique. Convergence is fast, not just eventual.

---

## Phase 9: User Story 7 - arXiv-intake guardrail (Priority: P2)

**Goal**: arXiv-intake papers (frozen source) skip the writing-revision pipeline entirely. Action items are recorded as `upstream_feedback.yaml` annotations. Outcomes restricted to accept-with-caveats or reject.

**Independent Test**: Construct an arxiv-intake fixture with writing action_items; run advancement; assert `paper/source/` is unchanged AND `upstream_feedback.yaml` contains the consolidated action items AND project advances to PAPER_ACCEPTED with caveats noted (NOT PAPER_REVISION_IN_PROGRESS).

### Implementation for User Story 7

- [ ] T040 [US7] Create [src/llmxive/agents/upstream_feedback.py](src/llmxive/agents/upstream_feedback.py) with `record_round(project_id, action_items, verdict_class, note) -> Path`. Atomically appends a new Round to `projects/<PROJ-ID>/upstream_feedback.yaml`. Creates the file with `schema_version: 1` if absent. Uses an `.tmp + os.replace` pattern.
- [ ] T041 [US7] Add `is_arxiv_intake(project_dir: Path) -> bool` helper to [src/llmxive/state/project.py](src/llmxive/state/project.py) (single source of truth — paper_reviewer.py also uses this check; consolidate). Returns True iff `paper/metadata.json` exists AND `paper/specs/` does NOT exist.
- [ ] T042 [US7] In [src/llmxive/agents/advancement.py](src/llmxive/agents/advancement.py) PAPER_REVIEW branch: BEFORE dispatching to the revision_planner, call `is_arxiv_intake(project_dir)`. If True: call `upstream_feedback.record_round(...)` instead, then route by verdict_class — `writing` or `science` → PAPER_ACCEPTED with caveats; `fatal` → BRAINSTORMED. Never call `revision_planner.run_revision_pipeline` for arxiv-intake projects.
- [ ] T043 [US7] Add `ArxivIntakeError` exception class to [src/llmxive/agents/revision_planner.py](src/llmxive/agents/revision_planner.py). `run_revision_pipeline` raises this if called with an arxiv-intake project (defensive — should never happen, but fail fast per Constitution V).
- [ ] T044 [US7] Unit test in [tests/unit/test_upstream_feedback_writer.py](tests/unit/test_upstream_feedback_writer.py): cover (a) first call creates upstream_feedback.yaml with schema_version=1 + round 1, (b) second call appends round 2, (c) atomic write (write to .tmp then replace), (d) loaded YAML round-trips through the contract schema.
- [ ] T045 [US7] Real-call test in [tests/real_call/test_arxiv_intake_no_source_mutation.py](tests/real_call/test_arxiv_intake_no_source_mutation.py): parameterize over all 8 previously-failing arxiv-intake fixture projects (PROJ-564, 565, 566, 568, 570, 571, 576, 578). For each: drive advancement; assert (a) `paper/source/` directory tree is byte-identical before/after, (b) `upstream_feedback.yaml` has ≥1 round with the consolidated action items (or no annotation if all-accept), (c) project state is `PAPER_ACCEPTED` (with caveats) or `BRAINSTORMED`. This satisfies SC-002's "all 8 fixtures" claim. Gated on `LLMXIVE_REAL_TESTS=1`.

**Checkpoint**: arXiv-intake papers reach a terminal state without ever mutating their source.

---

## Phase 10: Integration & End-to-End

**Purpose**: Wire scheduler idempotency, full-cycle e2e test, and the manual unblock CLI.

- [ ] T046 In [src/llmxive/pipeline/scheduler.py](src/llmxive/pipeline/scheduler.py): when picking the next project, skip projects in PAPER_REVISION_IN_PROGRESS (the planner is already running for them, OR the planner errored without a clean state — either way the scheduler MUST NOT re-trigger). This is the idempotency guarantee from the spec clarification.
- [ ] T047 Integration test in [tests/integration/test_revision_in_progress_idempotency.py](tests/integration/test_revision_in_progress_idempotency.py): set a fixture project to PAPER_REVISION_IN_PROGRESS; run the scheduler twice; assert (a) the planner is called at most ONCE, (b) on the second tick the project is skipped, (c) no race-condition orphan state.
- [ ] T048 Add `llmxive project unblock <PROJ-ID>` CLI subcommand to [src/llmxive/cli.py](src/llmxive/cli.py): validates that `state/revisions/<PROJ-ID>/round-<N>.yaml` was modified since the block (mtime check); resets `current_stage` to PAPER_MINOR_REVISION; appends a history entry; refuses to no-op-unblock.
- [ ] T049 Unit test in [tests/unit/test_cli_project_unblock.py](tests/unit/test_cli_project_unblock.py): cover (a) unblock with modified action-items file succeeds + sets stage, (b) unblock with un-modified action-items file refuses with clear error, (c) unblock on a non-blocked project errors.
- [ ] T050 End-to-end real-call test in [tests/real_call/test_paper_review_convergence_e2e.py](tests/real_call/test_paper_review_convergence_e2e.py): cover BOTH branches required by SC-006: (a) **Success branch** — drive a small home-grown fixture through review → writing-revision → 5-stage auto-plan → `READY_FOR_IMPLEMENTATION` → (simulated) implementer runs `speckit-implement` → re-review (which uses per-specialist re-review protocol) → eventual `PAPER_ACCEPTED`. The full cycle MUST converge within ≤3 revision rounds (SC-001). (b) **Blocked branch** — drive a fixture whose action items are deliberately constructed to be unresolvable by the analyzer (e.g., circular references); assert the analyzer-stuck path lands the project at `PAPER_REVISION_BLOCKED` with a populated `block_diagnostic` field after ≤3 remediation iterations. Gated on `LLMXIVE_REAL_TESTS=1`.

---

## Phase 11: Polish & Cross-Cutting Concerns

- [ ] T051 [P] Update [agents/agents.yaml](agents/agents.yaml) registry: bump `prompt_version` for `paper_reviewer` and all 12 specialists from 1.0.0 → 1.1.0 (reflects the action_items emission change). Existing review records keep their 1.0.0 records unmodified per Constitution I.
- [ ] T052 [P] Update [src/llmxive/web_data.py](src/llmxive/web_data.py) `regenerate_web_data` to surface `upstream_feedback.yaml` content on project cards for arxiv-intake projects + surface PAPER_REVISION_IN_PROGRESS / READY_FOR_IMPLEMENTATION / PAPER_REVISION_BLOCKED as distinct stage badges. Keep the schema additive (web data consumers MUST tolerate old + new shapes).
- [ ] T053 [P] Update [README.md](README.md) "Review process" section to describe the new three-way classification + auto-planned revision + the convergence guarantee.
- [ ] T054 Verify Constitution III compliance: every core function added in this spec has at least one real-call test under `tests/real_call/`. Count: T013, T017, T021, T030, T034, T039, T045, T050 — 8 real-call tests covering 8 user-story-bearing surfaces. ✓
- [ ] T055 Run full test suite (`pytest tests/unit tests/integration` AND `LLMXIVE_REAL_TESTS=1 pytest tests/real_call`). All MUST pass. Per Constitution V, if anything fails, fix the underlying CODE and re-run; do NOT weaken the test.

**Checkpoint**: Code shipped, tests green, docs updated.

---

## Dependencies

```
Phase 1 (T001-T003)          ← prerequisite for everything
  → Phase 2 (T004-T009)      ← prerequisite for US1-US7
    → Phase 3 (US6: T010-T013)  ← MUST come first; US1-US5 require action_items
      → Phase 4 (US1: T014-T017)
      → Phase 5 (US4: T018-T021)
      → Phase 6 (US2: T022-T030)   ← uses revision_planner.py
      → Phase 7 (US3: T031-T034)   ← uses revision_planner.py (depends on Phase 6)
      → Phase 8 (US5: T035-T039)   ← uses per-specialist re-review (independent of US2/US3)
      → Phase 9 (US7: T040-T045)   ← arxiv-intake guardrail (independent)
    → Phase 10 (Integration: T046-T050)  ← wires the e2e test
      → Phase 11 (Polish: T051-T055)
```

## Parallel execution examples

Within Phase 3 (US6), prompt updates for the 12 specialists (T011) can each be split into a separate sub-task and run in parallel — they touch different files. Marked [P]-eligible.

Within Phase 11, T051/T052/T053 touch different files and can run in parallel.

The four real-call tests within different phases (T013, T017, T021, T030, T034, T039, T045) are independent fixture runs — if Dartmouth API is happy, they can run in parallel.

## Implementation strategy: MVP-first

**MVP scope** (delivers user value with minimum scope): Phase 1 + Phase 2 + Phase 3 (US6 — action items) + Phase 4 (US1 — all-accept gate). This alone unblocks the 4 already-accepted papers (PROJ-564, 565, 566, 576) immediately and lets them reach PAPER_ACCEPTED.

**Incremental delivery**:

1. **MVP** (Phases 1-4): action items + all-accept gate. Existing papers with mostly-accept verdicts converge. ~17 tasks.
2. **Reject path** (Phase 5): fatal items route to backlog. Catches PROJ-578 which has unverifiable model claims. ~4 tasks.
3. **Auto-revision pipelines** (Phases 6-7): writing + science revisions auto-plan. ~12 tasks.
4. **Re-review protocol** (Phase 8): convergence speedup. ~5 tasks.
5. **arXiv-intake guardrail** (Phase 9): prevents source mutation on third-party papers. ~6 tasks.
6. **E2E + integration** (Phase 10): scheduler idempotency, unblock CLI, full-cycle test. ~5 tasks.
7. **Polish** (Phase 11): registry bumps, web data, docs, full-suite verification. ~5 tasks.

Total: **55 tasks**.
