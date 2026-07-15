# Tasks: Evaluating the Impact of LLM-Generated Code on Memory Usage

**Input**: Design documents from `/specs/001-eval-llm-memory-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/` with `data/`, `code/`, `tests/`, `state/` subdirectories
- [ ] T001b [P] Create `requirements.txt` with pinned versions for: transformers, datasets, memory-profiler, scikit-learn, statsmodels, lifelines, networkx, pandas, numpy
- [ ] T002 Initialize Python 3.11 virtual environment and install dependencies <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T003 [P] Configure linting (ruff/flake) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/`, `data/processed/`, `state/`, and `code/` directories
- [X] T005 [P] Create `code/config.py` with random seeds, model parameters, timeouts (60s per exec), and CI memory limits (GB)
- [ ] T006 [P] Create `code/utils.py` with error handling (SyntaxError, Timeout, OOM), retry logic, and CSV I/O helpers
- [X] T007 Create `code/profiling_env.yaml` to record runner OS, CPU model, and Python version
- [ ] T008 Implement `code/download.py` to fetch HumanEval/MBPP from HuggingFace with version pinning and checksum verification
- [~] T009 Implement `state/` versioning logic to compute and record SHA-256 hashes for artifacts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Profile Memory Usage for Code Solutions (Priority: P1) 🎯 MVP

**Goal**: Generate LLM code solutions and profile their memory consumption against human-written references.

**Independent Test**: Run the profiling harness on a representative set of benchmark problems and produce a CSV file with peak memory measurements for both LLM and human solutions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test for `code/download.py` ensuring dataset loads without auth
- [X] T011 [P] [US1] Contract test for memory measurement schema in `tests/contract/test_memory_schema.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/generate.py` with CPU-tractable model logic: Use 'TinyLlama' as primary model based on Plan.md CPU feasibility constraints (fits available RAM); Attempt `load_in_8bit=True` first, fallback to float16 if bitsandbytes unavailable; Do NOT fallback to Phi-2 as Plan explicitly deems it too large; Requires: T008
- [ ] T013 [US1] Implement `code/profile.py` harness using `tracemalloc` (steady-state) and `memory_profiler` (peak) with -run median logic
- [ ] T014 [US1] Implement stability check in `code/profile.py`: Calculate Interquartile Range (IQR) of 3 runs; re-run if IQR > 15% of median (max 2 retries); Use IQR per Plan.md override of Spec A; Requires: T013
- [ ] T015 [US1] Implement timeout handling in `code/profile.py`: Terminate execution >60s, record status='timeout', and calculate 'Total Resource Cost' as composite penalty (7GB * 60s) for censored data handling; Requires: T013
- [ ] T016 [US1] Implement error handling in `code/profile.py`: catch `SyntaxError`, record status='N/A', and continue to next problem
- [~] T017 [US1] Implement `code/utils.py` logic to write `data/processed/memory_measurements.csv` with schema: problem_id, source_type, peak_memory, steady_state, status, total_resource_cost

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Statistical Analysis on Memory Differences (Priority: P2)

**Goal**: Run statistical tests to determine if LLM code exhibits systematically different memory patterns.

**Independent Test**: Provide a CSV of paired measurements and receive a report with p-values, effect sizes, and corrected significance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Wilcoxon signed-rank test implementation in `tests/unit/test_stats.py`
- [X] T019 [P] [US2] Integration test for full analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [~] T020 [US2] Create `code/analyze.py` skeleton with data loading for `data/processed/memory_measurements.csv`; Requires: T017
- [X] T021 [US2] Implement statistical analysis in `code/analyze.py`: PRIMARY method is Kaplan-Meier estimator for censored data (timeouts/OOMs) per Plan.md; Fallback to Tobit regression if KM unavailable; Fallback to Wilcoxon signed-rank test if both KM and Tobit unavailable; Exclude zero-differences; Handle ties by average ranks; Requires: T020
- [X] T022 [US2] Implement Wilcoxon signed-rank test on uncensored subset (excluding zero-differences) in `code/analyze.py`
- [X] T023 [US2] Implement multiple-comparison correction (Holm-Bonferroni) for ≥3 tests in `code/analyze.py`
- [ ] T024 [US2] Implement effect size calculation (Cohen's d or rank-biserial correlation) in `code/analyze.py`
- [ ] T025 [US2] Generate statistical report JSON/CSV with raw/corrected p-values, effect sizes, and confidence intervals

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Code Feature Correlations with Memory Usage (Priority: P3)

**Goal**: Extract static code features and analyze their correlation with memory usage.

**Independent Test**: Provide code solutions and receive regression analysis output showing feature coefficients and VIF diagnostics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for feature extraction (LOC, Complexity) in `tests/unit/test_features.py`

### Implementation for User Story 3

- [ ] T027 [US3] Create `code/features.py` to extract Lines of Code (LOC) from code text; Requires: T012
- [ ] T028 [US3] Create `code/features.py` to calculate Cyclomatic Complexity using `networkx`; Requires: T012
- [ ] T029 [US3] Create `code/features.py` to count library imports and reference `data/dataset_manifest.yaml` for versioning traceability per Constitution Principle VII; Requires: T012
- [ ] T030 [US3] Implement `memory_per_loc` calculation (peak_memory_bytes / LOC) as a DESCRIPTIVE metric ONLY; explicitly exclude from regression analysis per Plan.md to prevent spurious correlations; Requires: T027, T017
- [ ] T031 [US3] Implement regression analysis in `code/analyze.py` using extracted features (LOC, Complexity, Imports) as predictors against residual memory; Requires: T027, T028, T029, T017
- [ ] T032 [US3] Implement Variance Inflation Factor (VIF) calculation in `code/analyze.py` and flag predictors with VIF > 5
- [ ] T033 [US3] Generate feature correlation report with coefficients, standard errors, and VIF flags

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `README.md` with usage instructions and setup steps
- [ ] T034b [P] Update `code/` docstrings and API documentation
- [ ] T035 Code cleanup and refactoring in `code/`
- [ ] T036 Performance optimization to ensure N=50 completes within 6 hours
- [ ] T037 [P] Additional unit tests in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T017)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data (T017) and code artifacts (T012)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Feature extraction tasks (T027-T029) can run in parallel (but require Phase 3 data)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/download.py ensuring dataset loads without auth"
Task: "Contract test for memory measurement schema in tests/contract/test_memory_schema.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generate.py with CPU-tractable model logic"
Task: "Implement code/profile.py harness using tracemalloc and memory_profiler"
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
 - Developer A: User Story 1 (Generation + Profiling)
 - Developer B: User Story 2 (Statistical Analysis)
 - Developer C: User Story 3 (Feature Extraction)
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