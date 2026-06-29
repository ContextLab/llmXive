# Tasks: Evaluating the Effectiveness of Code Simplification on LLM Performance

**Input**: Design documents from `/specs/001-eval-code-simplification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
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

## Phase 0: Research (Blocking Prerequisites)

**Purpose**: Dataset verification, model feasibility check, power analysis (FR-010), statistical design

**⚠️ CRITICAL**: No Phase 1 work can begin until this phase is complete

- [ ] T001 [P] Verify HumanEval dataset availability and version from HuggingFace Datasets; record version in data/README.md
- [ ] T002 [P] Verify StarCoder-1.3B 4-bit GGUF model source and CPU feasibility; document in research.md
- [ ] T003 [P] Create power/sample-size justification in research.md (FR-010: document minimum detectable effect for n=164 at power≥0.8)
- [ ] T004 [P] Document statistical design in research.md (McNemar's for pass@1, Wilcoxon for latency, Bonferroni for multiple hypotheses)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T005 Create project structure per implementation plan: data/raw/, data/processed/, data/logs/, code/, tests/, state/
- [ ] T006 [P] Initialize Python version project with requirements.txt dependencies (datasets, transformers, llama-cpp-python, ast, scipy, matplotlib, pandas, pytest)
- [ ] T007 [P] Configure linting and formatting tools (ruff, black)
- [ ] T008 [P] Create quickstart.md in specs/001-eval-code-simplification/ with setup instructions and CLI usage examples

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create base data models in code/models.py for three Key Entities: HumanEvalProblem (problem_id, prompt_code, reference_solution), SimplifiedProblem (problem_id, simplified_code), InferenceResult (problem_id, pass@1, token_count, inference_time_ms, status)
- [ ] T010 [P] Setup environment configuration management in code/config.py (paths, timeouts, model settings)
- [ ] T011 [P] Configure error handling and logging infrastructure in code/logger.py
- [ ] T012 Create schema validation tests in tests/contract/test_schemas.py and contracts/ directory structure with schema definitions
- [ ] T013 Setup state tracking for artifact versioning in state/map.json

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Benchmark Comparison (Priority: P1) 🎯 MVP

**Goal**: Execute full end-to-end pipeline on HumanEval subset with raw and AST-simplified inputs, producing paired result tables for accuracy and latency comparison

**Independent Test**: Run the "run-benchmark" command and verify two CSV files are produced (one for raw inputs, one for simplified inputs) each containing pass@1 scores and per-sample latency with matching problem IDs

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Contract test for data schema validation in tests/contract/test_data_schemas.py
- [ ] T015 [P] [US1] Integration test for full benchmark pipeline in tests/integration/test_benchmark_pipeline.py

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement HumanEval dataset download in code/download.py (FR-001: load from datasets.load_dataset('openai_humaneval'))
- [ ] T017 [US1] Implement AST-based simplification pipeline in code/simplify.py (FR-002: dead-code removal, boolean reduction)
- [ ] T018 [US1] Implement parse failure logging in code/simplify.py (FR-007: log to data/logs/parse_failures.log with problem_id, error_type, timestamp, stack_trace; VERIFY all fields present in output)
- [ ] T019 [US1] Implement semantic change detection in code/simplify.py (FR-008: run test harness, write to data/logs/flagged_snippets.csv with problem_id, error_type, code_diff; VERIFY all fields present in output)
- [ ] T020 [US1] Implement CPU-only inference runner in code/inference.py (FR-003: 4-bit StarCoder-1.3B via llama.cpp on CPU, respecting 7GB RAM limit; NO CUDA/device_map="cuda")
- [ ] T021 [US1] Implement per-sample timeout enforcement in code/inference.py (FR-009: 30-second timeout, log failure with inference_time_ms=30000)
- [ ] T022 [US1] Implement paired benchmark execution in code/main.py (orchestrate raw and simplified runs with matching problem IDs)
- [ ] T023 [US1] Create result table generation in code/main.py (output data/processed/results_raw.csv and data/processed/results_simplified.csv)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Metric Logging & Token Accounting (Priority: P2)

**Goal**: Log precise token counts and wall-clock inference time for every sample to support statistical testing and visualization

**Independent Test**: After a benchmark run, open the generated log file and confirm that for every problem there is a line containing both token_count and inference_time_ms

**⚠️ DEPENDENCY**: This phase requires US1 inference output (T020 completed); cannot run in parallel with US1

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US2] Contract test for metrics schema in tests/contract/test_metrics_schema.py
- [ ] T025 [P] [US2] Unit test for token counting accuracy in tests/unit/test_token_counter.py

### Implementation for User Story 2

- [ ] T026 [US2] Implement token counter in code/inference.py (count tokens of input prompt for each sample; DEPENDS ON T020)
- [ ] T027 [US2] Implement wall-clock timer in code/inference.py (measure inference_time_ms for each sample; DEPENDS ON T020)
- [ ] T028 [US2] Implement metrics CSV writer in code/inference.py (FR-004: write metrics_raw.csv and metrics_simplified.csv with problem_id, pass@1, token_count, inference_time_ms; VERIFY all required columns present)
- [ ] T029 [US2] Add validation for non-negative integer token_count in code/inference.py
- [ ] T030 [US2] Add validation for numeric inference_time_ms in code/inference.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Visualization (Priority: P3)

**Goal**: Generate reproducible statistical report (McNemar's test for pass@1, paired Wilcoxon signed-rank test for latency with Bonferroni correction for 3 hypotheses) and Matplotlib plot comparing accuracy and latency improvements

**Independent Test**: Run the "analyze-results" script and verify that a file analysis_report.pdf is created containing test statistics, p-values, effect sizes, and visualizations

**⚠️ DEPENDENCY**: This phase requires US1 and US2 CSV outputs (T023, T028 completed); cannot start after Foundational phase alone

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for report schema in tests/contract/test_report_schema.py
- [ ] T032 [P] [US3] Unit test for statistical calculations in tests/unit/test_statistical_tests.py

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement McNemar's test for binary pass@1 scores in code/analyze.py (FR-005; NOTE: spec.md FR-005 specifies Wilcoxon but plan.md Technical Context specifies McNemar's for binary data - follow plan.md)
- [ ] T034 [US3] Implement paired Wilcoxon signed-rank test for inference times in code/analyze.py (FR-005)
- [ ] T035 [US3] Implement Bonferroni correction for 3 hypotheses (accuracy, latency, token reduction) in code/analyze.py (FR-005)
- [ ] T036 [US3] Implement effect size calculation (rank-biserial correlation) in code/analyze.py (FR-006; use rank-biserial for Wilcoxon, not Cohen's d)
- [ ] T037 [US3] Implement token count ratio computation in code/analyze.py (SC-003: ratio for all paired problems; NOTE: descriptive, not gating per plan.md SC-003 Clarification)
- [ ] T038 [US3] Implement drop rate calculation in code/analyze.py (SC-005: parse failures + semantic changes)
- [ ] T039 [US3] Implement Matplotlib visualization in code/analyze.py (FR-006: two side-by-side bar charts for accuracy and latency)
- [ ] T040 [US3] Implement PDF report generation in code/analyze.py (FR-006: analysis_report.pdf with test statistics, p-values, effect sizes, figures)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Run unit tests for all modules in code/ (tests/unit/)
- [ ] T042 [P] Run contract tests for data schemas (tests/contract/)
- [ ] T043 [P] Run integration tests for full pipeline (tests/integration/)
- [ ] T044 [P] Documentation updates in README.md (quickstart reference)
- [ ] T045 Code cleanup: ruff linting pass (zero warnings/errors)
- [ ] T046 Code cleanup: black formatting pass (no formatting diffs)
- [ ] T047 Code cleanup: no TODO/FIXME comments remaining in code/
- [ ] T048 [P] Verify quickstart.md validation passes
- [ ] T049 Run end-to-end benchmark on full HumanEval (a standard problem set) and verify output files
- [ ] T050 [P] Verify analysis_report.pdf contains all required statistical tables and figures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Phase 1 (Setup)**: Depends on Phase 0 completion - BLOCKS all user stories
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (Phase 3): Can start after Phase 2 - No dependencies on other stories
  - User Story 2 (Phase 4): Requires US1 inference output (T020); CANNOT run in parallel with US1
  - User Story 3 (Phase 5): Requires US1 and US2 CSV outputs (T023, T028); CANNOT run in parallel with US1 or US2
- **Phase 6 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
  - Requires T016 (download) before T017 (simplify) before T020 (inference)
- **User Story 2 (P2)**: Requires US1 inference output (T020) - CANNOT run in parallel with US1
  - Requires T020 (inference) before T026-T030 (metrics logging)
- **User Story 3 (P3)**: Requires US1 and US2 CSV outputs (T023, T028) - CANNOT run in parallel with US1 or US2
  - Requires T023, T028 (result CSVs) before T033-T040 (analysis)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] can run in parallel
- All Phase 1 tasks marked [P] can run in parallel
- All Phase 2 tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- **IMPORTANT**: User stories CANNOT run in parallel due to data dependencies (US1→US2→US3)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schemas.py"
Task: "Integration test for full benchmark pipeline in tests/integration/test_benchmark_pipeline.py"

# Launch foundational tasks for User Story 1:
Task: "Implement HumanEval dataset download in code/download.py"
Task: "Implement AST-based simplification pipeline in code/simplify.py"
Task: "Implement CPU-only inference runner in code/inference.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0-2 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Sequential Team Strategy

Due to data dependencies, sequential execution is required:

1. Team completes Phase 0-2 together
2. Once Foundational is done:
   - Developer A: User Story 1 (benchmark pipeline) → BLOCKS US2/US3
   - After US1 complete: Developer B: User Story 2 (metrics logging) → BLOCKS US3
   - After US2 complete: Developer C: User Story 3 (statistical analysis)
3. Stories complete and integrate sequentially

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Feasibility Check**: StarCoder-1.3B 4-bit via llama.cpp on CPU fits within 7GB RAM limit; HumanEval (the complete problem set) can be processed within maximum job duration limit
- **Avoid**: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Path**: T016 → T017 → T020 → T023 → T028 → T033-T040 (download → simplify → infer → results → metrics → report)
- **Statistical Test Clarification**: McNemar's test for binary pass@1 (per plan.md Technical Context); Wilcoxon for continuous latency metrics; Bonferroni for 3 hypotheses (accuracy, latency, token reduction)
- **Token Reduction Clarification**: SC-003 is descriptive, not gating - analysis proceeds on full paired dataset regardless of token reduction outcome (per plan.md SC-003 Clarification)
