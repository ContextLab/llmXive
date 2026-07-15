# Tasks: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

**Input**: Design documents from `/specs/001-evaluating-llm-code-simplification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3) or **[Shared]** if used across stories
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

- [X] T001 Create project structure per implementation plan (code/, data/, results/, state/)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (datasets, transformers, accelerate, torch-cpu, scikit-learn, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Setup `checksum.py` script for artifact versioning (Constitution Principle V)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/utils/sandbox.py` with hard 5s timeout and 500MB memory limit wrappers (FR-005)
- [X] T006 Implement `code/utils/logger.py` for structured JSON logging of pipeline stages
- [X] T007 Create `code/data/download.py` to fetch `codeparrot/codesearchnet-python` via `datasets` library (FR-001)
- [ ] T008 Create `code/data/extract.py` to parse raw parquet and isolate top-level function definitions via `ast` (US-1)
- [X] T009 Create `code/data/validate.py` for syntax checking and import mocking (FR-001, FR-010)
- [ ] T010 Create `code/data/preprocess.py` to sanitize code (remove I/O/network calls, mock stdlib) (FR-011)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and sanitize a stratified sample of executable Python functions from CodeSearchNet.

**Independent Test**: Verify `data/raw` contains valid parquet, `data/processed` contains exactly 200 sanitized, executable functions with logs of exclusions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for `download.py` to verify file count and checksum in `tests/unit/test_download.py`; tests components of the full pipeline flow
- [ ] T012 [P] [US1] Unit test for `validate.py` to ensure `SyntaxError` functions are excluded in `tests/unit/test_validate.py`; tests components of the full pipeline flow
- [ ] T013 [P] [US1] Integration test for the full pipeline (download -> validate -> preprocess) in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T014a [US1] Define strata boundaries (0-10, 11-50, 51+ LOC) and sampling weights for 200 functions in `code/data/sample.py` (FR-008)
- [~] T014b [US1] Implement sampling function to extract 200 functions from the **validated pool (output of T009, filtered for <=3 external imports)** in `code/data/sample.py` (FR-001, FR-008). **Output**: `data/processed/validated_functions.jsonl`. **Verify**: Count == 200.
- [~] T014c [US1] Generate the stratified pilot sample of 50 functions from `data/processed/validated_functions.jsonl` in `code/data/sample.py` (FR-008). **Output**: `data/processed/pilot_sample.jsonl`. **Verify**: 50 functions distributed across strata.
- [X] T015 [Shared] Implement functional equivalence check logic (AST diff + Type-aware random inputs) in `code/benchmark/equivalence.py` with clear I/O contracts (Input: original_code, simplified_code, random_inputs; Output: bool, drift_log). **Deliverable**: `code/benchmark/equivalence.py`. **Verify**: Run on a set of pairs, expect matches. **Note**: This logic MUST be invoked during Phase 4 (Simplification) to satisfy FR-007 and is used by T016 and T033. (FR-006, FR-007, FR-012)
- [ ] T017 [US1] Implement full data pipeline orchestrator in `code/main_data.py` to produce `data/processed/functions.jsonl`
- [X] T018 [US1] Add logging for exclusion reasons (syntax error, import failure, equivalence drift) in `code/utils/logger.py`

**Checkpoint**: At this point, User Stories should be fully functional and testable independently with a validated dataset (simplification logic pending).

---

## Phase 4: User Story 2 - LLM-Driven Simplification Execution (Priority: P2)

**Goal**: Load a CPU-quantized LLM (<3B params) and generate simplified code for the validated functions.

**Independent Test**: Run on 5 functions; verify output is valid Python, distinct from input, and generated within 60s per function.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for `loader.py` to verify model loads in 4-bit precision on CPU within 7GB RAM in `tests/unit/test_model_loader.py`
- [X] T020 [P] [US2] Unit test for `simplify.py` to ensure retry logic handles generation failures in `tests/unit/test_simplify.py`
- [X] T021 [P] [US2] Integration test for simplification of a batch of functions in `tests/integration/test_simplification.py`

### Implementation for User Story 2

- [ ] T016 [US2] **Pilot Gate**: Execute pilot validation on `data/processed/pilot_sample.jsonl` (50 functions) to verify ≥10 valid, equivalent pairs per stratum. **Mandatory Step**: Invoke T015 equivalence check logic for each pair. **Output**: `results/pilot_validation_report.json`. **Verify**: Report contains ≥10 valid pairs per stratum. (FR-008, FR-006) <!-- ATOMIZE: requested -->
- [ ] T022 [P] [US2] Implement `code/models/loader.py` to load CodeLlama model (4-bit, CPU) with `accelerate` (FR-002)
- [X] T023 [US2] Implement `code/models/simplify.py` with the standard simplification prompt and retry logic (configurable retry limit) (FR-002, US-2)
- [X] T024 [US2] Implement AST validation for generated code in `code/models/simplify.py`; **integrate into T023 retry loop (a limited number of retries) before discard** (US-2)
- [~] T025 [US2] Create `code/main_simplify.py` to process `data/processed/validated_functions.jsonl` and output `data/processed/simplified_functions.jsonl`
- [ ] T026 [US2] Add functional drift detection: run equivalence check (T015) on simplified code; log pairs with drift in `results/simplification_log.json` (FR-007)

**Checkpoint**: Pilot validation passed. Proceed to full simplification.

### Phase 4 Checkpoint: Valid Pairs Generation

- [~] T026b [US2] **Filter Drifted Pairs**: Create `code/main_filter_drift.py` to filter `data/processed/simplified_functions.jsonl` based on T026 logs. **Mandatory**: Log exclusion reason as 'equivalence_unverifiable' (if AST diff insufficient) or 'drift_detected' per FR-012. **Output**: `data/processed/valid_pairs.jsonl`. **Verify**: `valid_pairs.jsonl` exists and contains >= 10 pairs per stratum. **Blocks Phase 5**. (FR-007, FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, producing a final set of valid (Original, Simplified) pairs and a validated pilot.

---

## Phase 5: User Story 3 - Performance Benchmarking and Statistical Analysis (Priority: P3)

**Goal**: Benchmark original vs. simplified code (iterations each), compute metrics, and perform statistical significance testing.

**Independent Test**: Run benchmark on a known pair; verify a sufficient number of iterations recorded, mean/std calculated, and p-value output matches expected.

**⚠️ DEPENDENCY**: This phase depends on the completion of T026b (Phase 4) which produces `data/processed/valid_pairs.jsonl`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for `runner.py` to verify a sufficient number of iterations and timeout enforcement in `tests/unit/test_benchmark_runner.py`
- [~] T029 [P] [US3] Unit test for `stats.py` to verify Shapiro-Wilk and conditional t-test/Wilcoxon logic in `tests/unit/test_stats.py`
- [~] T030 [P] [US3] Integration test for full benchmark and stats pipeline in `tests/integration/test_benchmark_stats.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement `code/benchmark/runner.py` to execute code repeatedly using `time.perf_counter()` and `tracemalloc`. **Integrate sandbox.py wrappers into a multi-iteration loop to enforce 5s/500MB limits on EVERY iteration** (FR-003, FR-005, FR-009)
- [X] T032 [US3] Implement `code/benchmark/stats.py` with Shapiro-Wilk normality check, t-test/Wilcoxon selection, and Bonferroni correction. **Perform statistical tests on the distribution of N=200 means (not raw iterations)** as required by FR-009 and SC-001/SC-002. (FR-004, SC-001, SC-002)
- [~] T033 [US3] Create `code/main_benchmark.py` to orchestrate the full run: load **`data/processed/valid_pairs.jsonl`** (output of T026b), run benchmarks, aggregate means, run stats
- [ ] T034 [US3] Generate `results/summary.csv` with mean deltas, std, p-values, and significance flags (US-3)
- [ ] T035b [US3] Generate `results/statistical_summary.json` with p-values and significance flags derived from SC-001/SC-002 metrics (NO narrative text) (SC-001, SC-002)

**Checkpoint**: All user stories should now be independently functional. The pipeline produces the final research results.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T036 [P] Documentation updates in `docs/` (Quickstart, API reference)
- [~] T037 Code cleanup and refactoring for readability <!-- ATOMIZE: requested -->
- [~] T038 Performance optimization for the benchmark loop (multiprocessing) to meet a target runtime.
- [~] T039 [P] Additional unit tests (if requested) in `tests/unit/`
- [~] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (validated functions)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 output (simplified functions)
 - *Note: US3 depends on the existence of pairs from US1+US2, but the code for US3 can be written in parallel with US2 implementation.*

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
Task: "Unit test for download.py"
Task: "Unit test for validate.py"

# Launch all models for User Story 1 together:
Task: "Create download.py"
Task: "Create extract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify 200 valid functions)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (LLM Simplification)
 - Developer C: User Story 3 (Benchmarking & Stats)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability; [Shared] indicates cross-story utility
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Reminder**: All tasks must run on CPU-only CI with limited computational resources (a small number of cores and restricted memory). No GPU, no 8-bit/4-bit CUDA loading, no large models.
- **Plan Note**: The plan's "Trimmed Mean" strategy contradicts spec FR-009. Tasks are implemented per FR-009 (Mean/Std). **Plan.md is flagged for update** to resolve this conflict before execution.