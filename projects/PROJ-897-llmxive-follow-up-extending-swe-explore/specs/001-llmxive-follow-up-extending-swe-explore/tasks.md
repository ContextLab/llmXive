# Tasks: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Input**: Design documents from `/specs/001-iterative-exploration-benchmark/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/contract/`, `contracts/`, `docs/`, `paper/`

- [X] T002 {{claim:c_eea0cf13}} <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define paths (`data/raw/`, `data/curated/`, `data/results/`), random seeds, and model config (CPU-only)
- [X] T005 [P] Implement `code/utils/hash_artifacts.py` for automated SHA256 hashing of `data/` artifacts (Constitution Principle V)
- [X] T006 [P] Create `contracts/` directory with `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`
- [X] T007 Implement `code/utils/validation.py` for JSONL/Parquet schema validation against contracts
- [X] T008 Setup `pytest` configuration and `tests/contract/test_schemas.py` skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1) 🎯 MVP

**Goal**: Download SWE-Explore, derive ground truth, select "hard" instances based on initial coverage scores (FR-001), and Generate a set of synthetic ambiguous issues with structural obfuscations. (FR-009).

**Independent Test**: Verify the existence of `data/curated/hard_subset.jsonl`, `data/curated/synthetic_issues.jsonl`, and `data/curated/validation_report.md` with correct schemas and valid AST parsing for synthetic issues.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (Depends on T006 schema output)
- [X] T010 [P] [US1] Unit test for mutation logic (variable rename, comment removal) in `tests/unit/test_mutation.py`
- [X] T011 [P] [US1] Unit test for synthetic issue validity (AST parse check) in `tests/unit/test_synthetic_validity.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/download.py` to fetch `bench.final.public.jsonl` from HuggingFace
- [X] T013 [P] [US1] Implement `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` lists
- [X] T014a [US1] Implement `code/data/curate.py` Part A: **Filter** the bottom [deferred] of issues based on existing **`initial_coverage`** scores (read `HARD_INSTANCE_PERCENTILE` from `config.py`) to identify "Hard" instances per FR-001. Do NOT use complexity. Ensure this consumes `ground_truth_lines` from T013.
- [ ] T014b [US1] Implement `code/data/curate.py` Part B: Generate **up to 50** synthetic ambiguous issues by mutating variable names, removing comments, and applying **structural obfuscations (control flow reordering, API signature changes)** per FR-009. **Fallback Logic**: If the pool of solvable tasks is insufficient, proceed with N < 50, log a warning, and save the actual count in `data/curated/synthetic_issues_meta.json`. Ensure synthetic issues are syntactically valid (AST parseable). Save `ground_truth_lines` from original code for synthetic issues (FR-008). **Versioning**: Record original code hash and mutation parameters in metadata.
- [X] T014c [US1] Implement `code/data/curate.py` Part C: Validation logic to skip invalid mutations and log warnings.
- [X] T015a [US1] Implement `code/config.py` update to define `VALIDATION_SAMPLE_SIZE` (default N=20) and `HARD_INSTANCE_PERCENTILE` (default) to resolve "[deferred]" values before execution.
- [ ] T015 [US1] Implement `code/data/validate_hard.py` to generate `data/curated/validation_report.md` with manual inspection guide for the **`VALIDATION_SAMPLE_SIZE`** subset defined in `config.py`. **Logic**: Read `VALIDATION_SAMPLE_SIZE` from config. **Output format**: Markdown table with columns [IssueID, CoverageScore, MutationType, ValidityStatus, Notes].
- [ ] T016 [US1] Integrate `hash_artifacts.py` to hash `data/curated/` files after generation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Iterative Agent Execution Loop (Priority: P2)

**Goal**: Implement a CPU-tractable iterative agent loop with a bounded number of turns. with static analysis feedback, and a Static Multi-Query Baseline. Ensure both produce compatible schemas for pairing.

**Independent Test**: Run a single "hard" issue through the iterative loop and verify a limited number of turns, reformulated queries containing error messages, and correct logging of `query_history` and `error_signals`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for agent log schema in `tests/contract/test_agent_log_schema.py`
- [X] T019 [P] [US2] Integration test for agent loop termination (-turn limit, loop detection) in `tests/integration/test_agent_loop.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/agent/static_analysis.py` wrapper for `pylint`/`ast` to detect "missing import", "undefined variable", parse errors
- [X] T021 [P] [US2] Implement `code/agent/prompts.py` with templates for query reformulation based on static analysis signals
- [ ] T022 [US2] Implement `code/agent/base.py` for Static Multi-Query Baseline. **Requirement**: Run **3 parallel queries** per issue (matching iterative budget). Must operate on the same curated subset as T023 and produce output compatible with `agent_log_schema.yaml` for T031 pairing. Explicitly log `issue_id`, `query_count`, `retrieved_context_ids`, and `coverage_score` to enable 1:1 pairing with iterative results for the Wilcoxon signed-rank test.
- [X] T023 [US2] Implement `code/agent/iterative.py`:
 - Enforce 3-turn limit (FR-003)
 - Turn logic: Query -> Retrieve -> Static Analysis -> Reformulate (if error)
 - Detect repeated queries to break loops early
 - Log `query_history`, `static_analysis_signals`, `turn_reasons`
 - **Requirement**: Must operate on the same curated subset as T022 and produce output compatible with `agent_log_schema.yaml` for T031 pairing. Explicitly log the `issue_id` to enable 1:1 pairing with baseline results.
- [ ] T024 [US2] Implement `code/main.py` orchestration to run Baseline and Iterative agent on curated dataset. Output: `data/results/paired_metrics.json` containing merged results for T031, ensuring strict pairing by `issue_id`.
- [ ] T025 [US2] Implement turn-limit sweep logic: Reuse T023/T024 logic to execute **N=20 issues** (random sample from `data/curated/hard_subset.jsonl`) with **4 turns** per SC-006. Record results in `data/results/sweep_results.json` for stability comparison.
- [ ] T026 [US2] Integrate `hash_artifacts.py` to hash `data/results/agent_logs/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

**Goal**: Compute line-level coverage and ranking efficiency, apply Wilcoxon/Survival Analysis with Bonferroni correction, and frame results associatively.

**Independent Test**: Provide pre-computed metrics for a small set and verify the statistical test returns a p-value and correct conclusion (significant vs. non-significant) at p < 0.05 threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T028 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/metrics/coverage.py` to calculate % of `ground_truth_lines` retrieved
- [X] T030 [P] [US3] Implement `code/metrics/ranking.py` to calculate position of first relevant line (handle censored data with penalty N+1)
- [X] T031a [US3] Implement `code/analysis/stats.py` Part A: Calculate coverage metrics and apply **Wilcoxon signed-rank test** for paired coverage data.
- [X] T031b [US3] Implement `code/analysis/stats.py` Part B: Calculate ranking metrics. **Primary Method**: Apply **Wilcoxon signed-rank test** with tie-handling (continuity correction) per FR-006. **Fallback**: If ties/censoring exceed a substantial proportion, apply **exact permutation test** or **Survival Analysis (Cox)** for censored data.
- [~] T031c [US3] Implement `code/analysis/stats.py` Part C: Apply **Bonferroni correction** to the family of tests (coverage + ranking) per SC-004. Frame all results as **"associational differences"** per FR-007. Output `data/results/final_metrics.json`.
- [X] T032 [US3] Implement `code/analysis/plots.py` for visualization of coverage and survival curves
- [~] T033 [US3] Integrate `hash_artifacts.py` to hash final `data/results/final_metrics.json`
- [X] T034a [US3] Implement `code/analysis/report_generator.py` template for generating the final paper draft.
- [~] T034 [US3] Generate `paper/draft.md` using `code/analysis/report_generator.py` (T034a). **Mandatory**: Populate sections: Abstract, Methods, Results (with p-values from `data/results/final_metrics.json`), and Discussion. **Constraint**: All findings MUST be framed as **associational differences**; explicitly avoid causal claims per FR-007. The report generator must enforce this linguistic constraint on all result descriptions.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T035 [P] Documentation updates in `docs/` (Quickstart, Data Model, Research)
- [~] T036 Code cleanup and refactoring
- [~] T037 Performance optimization (memory management for CPU model)
- [~] T038 [P] Additional unit tests in `tests/unit/`
- [X] T039 [US2/US3] Implement runtime monitor in `code/main.py` to track total execution time. **Logic**: If elapsed time > 5.5 hours (SC-005), abort remaining non-critical sweeps or reduce sample size to ensure completion within 6 hours.
- [~] T040 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 for results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for mutation logic in tests/unit/test_mutation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/derive_gt.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Feasibility**: Ensure all model tasks use CPU-only, <1B param or 4-bit quantized models on 2-core/7GB RAM. No CUDA/GPU.
- **Constraint Preservation**: All tasks must strictly implement the metrics and counts defined in FR-001, FR-002, SC-004, and FR-007. Do not substitute proxies (e.g., complexity for coverage) without explicit spec authorization.
- **Data Integrity**: All analysis tasks must consume REAL data from `data/curated/`. No synthetic/fake input data generation tasks are permitted.
- **Execution Order**: Tasks producing results (T024) MUST follow tasks generating those results (T022, T023). Tasks verifying results (T031) MUST follow result generation.