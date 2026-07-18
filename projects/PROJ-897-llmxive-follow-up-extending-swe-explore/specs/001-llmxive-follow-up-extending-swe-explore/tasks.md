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

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/contract/`, `contracts/`, `docs/`, `paper/` AND configure linting (ruff/flake8) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Implement `code/config.py` to define paths (`data/raw/`, `data/curated/`, `data/results/`), random seeds, model config (CPU-only), AND critical thresholds: `COMPLEXITY_THRESHOLD` (for hard instance selection), `HARD_INSTANCE_PERCENTILE`, `VALIDATION_SAMPLE_SIZE` (See T013, T014).
- [X] T003 [P] Implement `code/utils/hash_artifacts.py` for automated SHA256 hashing of `data/` artifacts (Constitution Principle V)
- [X] T004 [P] Create `contracts/` directory with `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`
- [X] T005 [P] Implement `code/utils/validation.py` for JSONL/Parquet schema validation against contracts
- [X] T006 [P] Setup `pytest` configuration and `tests/contract/test_schemas.py` skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1) 🎯 MVP

**Goal**: Download SWE-Explore, derive ground truth, select "hard" instances based on **Cyclomatic Complexity** (Plan Phase 0, overriding Spec FR-001 to avoid tautology), and generate synthetic ambiguous issues.

**Independent Test**: Verify the existence of `data/curated/hard_subset.jsonl`, `data/curated/non_hard_subset.jsonl`, `data/curated/synthetic_issues.jsonl`, and `data/curated/validation_report.md` with correct schemas and valid AST parsing for synthetic issues.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (Depends on T004 schema output)
- [X] T008 [P] [US1] Unit test for mutation logic (variable rename, comment removal) in `tests/unit/test_mutation.py`
- [X] T009 [P] [US1] Unit test for synthetic issue validity (AST parse check) in `tests/unit/test_synthetic_validity.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `code/data/download.py` to fetch `bench.final.public.jsonl` from HuggingFace
- [X] T011 [P] [US1] Implement `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` lists
- [X] T012 [US1] Implement `code/data/curate.py` Part A: **Filter** the raw dataset to create two subsets:
 1. **Hard Subset**: Select issues with **Cyclomatic Complexity** (calculated via `networkx`) above `COMPLEXITY_THRESHOLD` (read from `config.py` T002).
 2. **Non-Hard Subset**: Select the remaining solvable issues.
 **CRITICAL**: **Per Plan Phase 0 override of Spec FR-001**, do NOT use `initial_coverage` to avoid tautology.
 Save both as immutable JSONL files: `data/curated/hard_subset.jsonl` and `data/curated/non_hard_subset.jsonl`.
- [X] T013 [US1] Implement `code/data/curate.py` Part B: **Generate Synthetic Ambiguous Issues**.
 - Input: `data/curated/non_hard_subset.jsonl` (T012 output).
 - Logic: Apply mutations (rename [deferred] of variables, remove all comments, and apply structural obfuscation via control flow reordering) to generate **up to 50** issues.
 - Constraint: If the pool of solvable tasks is insufficient, **log a warning** and proceed with the available count (do not raise RuntimeError).
 - Output: `data/curated/synthetic_issues.jsonl`.
 - Oracle: Derive `ground_truth_lines` from the original unmutated code (FR-008).
 - Validity: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations and log warnings.
- [X] T014 [US1] Implement `code/data/curate.py` Part C: **Metadata & Versioning**.
 - Save `data/curated/synthetic_issues_meta.json` containing original code hashes, mutation parameters, and the exact count generated.
 - Run `hash_artifacts.py` on `data/curated/` files.
- [X] T015 [US1] Implement `code/data/validate_hard.py` to generate `data/curated/validation_report.md`.
 - Input: `data/curated/hard_subset.jsonl`.
 - Logic: Select `VALIDATION_SAMPLE_SIZE` (from config.py T002) random issues.
 - Output: Markdown table with columns [IssueID, ComplexityScore, CoverageScore, Notes].
 - **Note**: This report is a **tool for manual inspection**, not an automated validation result.
- [X] T016 [US1] **Manual Human Inspection Gate**: Implement logic to wait for human sign-off.
 - **Action**: The pipeline halts here. A human must review `validation_report.md` (T015).
 - **Deliverable**: Human creates `data/curated/validation_approved.flag` file upon approval.
 - **Dependency**: Phase 4 (Agent Execution) depends on the existence of this flag file.
 - **Derived Constraint**: **Per Plan Phase 0**, manual inspection must block execution until approved.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (pending manual gate)

---

## Phase 4: User Story 2 - Iterative Agent Execution Loop (Priority: P2)

**Goal**: Implement a CPU-tractable iterative agent loop with a bounded number of turns, static analysis feedback, and a Static Multi-Query Baseline. Ensure both produce compatible schemas for pairing.

**Independent Test**: Run a single "hard" issue through the iterative loop and verify a limited number of turns, reformulated queries containing error messages, and correct logging of `query_history` and `error_signals`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for agent log schema in `tests/contract/test_agent_log_schema.py`
- [X] T018 [P] [US2] Integration test for agent loop termination (3-turn limit, loop detection) in `tests/integration/test_agent_loop.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/agent/static_analysis.py` wrapper for `pylint`/`ast` to detect "missing import", "undefined variable", parse errors
- [X] T020 [P] [US2] Implement `code/agent/prompts.py` with templates for query reformulation based on static analysis signals
- [X] T021 [US2] **Data Locking & Subset Consistency**:
 - **Action**: Before running agents, copy `data/curated/hard_subset.jsonl` to a locked execution directory (e.g., `data/results/locked_hard_subset.jsonl`).
 - **Purpose**: Ensure T022 (Baseline) and T023 (Iterative) consume the **exact same** file instance to enable 1:1 pairing.
 - **Dependency**: Depends on T012 (data generation) and T016 (manual gate approval).
 - **Prerequisite**: Phase 4 agents depend on this task.
- [X] T022 [P] [US2] Implement `code/agent/base.py` for Static Multi-Query Baseline.
 - **Requirement**: Run **3 parallel queries** per issue using `asyncio.gather` to match iterative budget.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Output**: `data/results/baseline_logs.jsonl` compatible with `agent_log_schema.yaml`.
 - **Logging**: Explicitly log `issue_id`, `query_count`, `retrieved_context_ids`, and `coverage_score`.
- [X] T023 [US2] Implement `code/agent/iterative.py`:
 - **Requirement**: Enforce 3-turn limit (FR-003).
 - **Turn Logic**: Query -> Retrieve -> Static Analysis -> Reformulate (if error).
 - **Loop Detection**: Detect repeated queries to break loops early.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Output**: `data/results/iterative_logs.jsonl` compatible with `agent_log_schema.yaml`.
 - **Logging**: Explicitly log `issue_id`, `query_history`, `static_analysis_signals`, `turn_reasons`.
- [X] T024 [US2] **Turn-Limit Sweep**:
 - **Logic**: Reuse T022/T023 logic to execute **N=20 issues** (random sample with **seed 42**, stratified by complexity quartiles from `data/curated/hard_subset.jsonl`) with **4 turns** per SC-006.
 - **Output**: `data/results/sweep_results.json` containing columns: `issue_id`, `turns_used`, `coverage`, `stability_flag`.
 - **Dependency**: Depends on T012 (stratification) and T021 (locked data).
- [X] T025 [US2] Integrate `hash_artifacts.py` to hash `data/results/agent_logs/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

**Goal**: Compute line-level coverage and ranking efficiency, apply Survival Analysis (for ranking) and Wilcoxon (for coverage) with Bonferroni correction, and frame results associatively.

**Independent Test**: Provide pre-computed metrics for a small set and verify the statistical test returns a p-value and correct conclusion (significant vs. non-significant) at p < 0.05 threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T027 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/metrics/coverage.py` to calculate % of `ground_truth_lines` retrieved
- [X] T029 [P] [US3] Implement `code/metrics/ranking.py` to calculate position of first relevant line (handle censored data with penalty N+1)
- [X] T030a [P] [US3] Implement `code/analysis/stats.py` Part A: **Coverage Analysis**.
 - **Method**: Apply **Wilcoxon signed-rank test** to paired coverage data (Baseline vs. Iterative).
 - **Output**: P-value and effect size.
- [X] T030b [P] [US3] Implement `code/analysis/stats.py` Part B: **Ranking Efficiency Analysis**.
 - **Primary Method**: Apply **Survival Analysis (Cox proportional hazards)** to handle censored ranking data (where no relevant lines found), as mandated by Plan Phase 2.
 - **Fallback**: If censoring is negligible, use Wilcoxon signed-rank test with continuity correction.
 - **Event Definition**: "first relevant line found".
 - **Censoring Handling**: Assign `N+1` where `N` is total lines.
 - **Output**: Hazard ratio and p-value.
 - **Note**: **Per Plan Phase 2 override of Spec FR-006**.
- [X] T030c [US3] Implement `code/analysis/stats.py` Part C: **Multiplicity Correction & Framing**.
 - **Correction**: Apply **Bonferroni correction** to the family of tests: **Coverage (T030a)** and **Ranking (T030b)**.
 - **Framing**: Frame all results as **"associational differences"** per FR-007.
 - **Output**: `data/results/final_metrics.json`.
 - **Dependency**: Depends on T030a and T030b.
- [X] T031 [US3] Implement `code/analysis/plots.py` for visualization of coverage and survival curves
- [X] T032 [US3] Integrate `hash_artifacts.py` to hash final `data/results/final_metrics.json`
- [X] T033a [US3] Implement `code/analysis/report_generator.py` Part A: **Data Extraction**.
 - Logic: Extract p-values, effect sizes, and metrics from `data/results/final_metrics.json`.
 - **Dependency**: Depends on T030c.
- [X] T033b [US3] Implement `code/analysis/report_generator.py` Part B: **Template Filling**.
 - Logic: Populate sections: Abstract, Methods, Results, Discussion using extracted data.
 - **Constraint**: Enforce "associational differences" language in Results/Discussion.
- [X] T033c [US3] Implement `code/analysis/report_generator.py` Part C: **Final Assembly & Validation**.
 - Logic: Assemble `paper/draft.md` and validate against schema.
- [X] T034 [US3] **Generate Results Summary**:
 - **Action**: Execute T033a -> T033b -> T033c pipeline.
 - **Output**: `paper/results_summary.md` (containing Abstract draft, Methods summary, Results, Discussion).
 - **Constraint**: Scope limited to spec requirements (SC-004, FR-007); no full manuscript generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Update `docs/quickstart.md` with execution instructions and data flow diagrams.
- [X] T036 Refactor `code/agent/iterative.py` to reduce cyclomatic complexity below 15.
- [X] T037 Optimize memory usage in `code/metrics/coverage.py` by processing lines in chunks.
- [X] T038 [P] Add unit tests for `code/analysis/stats.py` (Wilcoxon and Survival Analysis logic).
- [X] T039 [US2/US3] Implement runtime monitor in `code/main.py` to track total execution time. **Logic**: If elapsed time > 5.5 hours (SC-005), abort remaining non-critical sweeps or reduce sample size to ensure completion within 6 hours.
- [ ] T040 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data (specifically `hard_subset.jsonl` and `validation_approved.flag`)
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
4. **STOP and VALIDATE**: Test User Story 1 independently (and pass manual gate T016)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Pass Manual Gate → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Curation)
 - Developer B: User Story 2 (Agent Execution)
 - Developer C: User Story 3 (Analysis)
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
- **Constraint Preservation**: All tasks must strictly implement the metrics and counts defined in FR-001, FR-002, SC-004, and FR-007.
 - **Hard Instance Selection**: Must use **Cyclomatic Complexity** (Plan Phase 0) NOT `initial_coverage` (Spec FR-001) to avoid tautology.
 - **Synthetic Issues**: Must generate **up to 50**; fail loudly if insufficient (removed).
 - **Statistics**: Coverage uses Wilcoxon; Ranking uses Survival Analysis (Plan Phase 2).
 - **Correction**: Bonferroni applied to Coverage and Ranking tests.
- **Data Integrity**: All analysis tasks must consume REAL data from `data/curated/`. No synthetic/fake input data generation tasks are permitted.
- **Execution Order**: Tasks producing results (T023) MUST follow tasks generating those results (T021, T022). Tasks verifying results (T030) MUST follow result generation.
- **Manual Gate**: Phase 4 cannot start until `data/curated/validation_approved.flag` exists (T016).