# Tasks: Evaluating the Robustness of Statistical Methods to Common Data Errors

**Input**: Design documents from `/specs/001-evaluate-statistical-robustness/`
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

- [ ] T001 [P] Create project directory structure with exact tree: `data/raw`, `data/derived`, `code`, `results`, `tests`. **MUST include creating empty `__init__.py` files in `code/` and `tests/` directories** to ensure Python package recognition.
- [ ] T002 [P] Initialize Python 3.11 project with dependencies: pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, pytest
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes ground-truth data generation (FR-006, FR-007) and skeleton creation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining valid tabular dataset structures
- [ ] T005 [P] Create `contracts/injection.schema.yaml` defining error types (replacement, misclassification, MCAR) and rates [0.01, 0.05, 0.10, 0.20]
- [ ] T006 [P] Create `contracts/result.schema.yaml` defining output metrics (p-value, CI bounds, effect size, Type I flag)
- [ ] T007 [P] Create `code/download.py` skeleton (empty file with imports and main function stub)
- [ ] T008 [P] Create `code/inject.py` skeleton (empty file with imports and main function stub)
- [ ] T009 [P] Create `code/analyze.py` skeleton (empty file with imports and main function stub)
- [ ] T010 [P] Create `code/simulate.py` skeleton (empty file with imports and main function stub)
- [ ] T011 [P] Create `code/visualize.py` skeleton (empty file with imports and main function stub)
- [ ] T012 [P] Create `code/main.py` skeleton (CLI entry point stub)
- [ ] T013 [P] [FR-006] Implement `code/simulate.py` to generate synthetic datasets with **known population parameters** across a grid: iterate over `effect_sizes=[0.2, 0.5, 0.8]` and `variances=[1.0, 2.0]` (mean=0 fixed). Output CSVs to `data/derived/synthetic_grid/` and write a `synthetic_metadata.json` file mapping each file to its exact parameters (mean, variance, effect_size) for downstream consumption.
- [ ] T014 [P] [FR-007] Implement `code/simulate.py` to generate null-hypothesis datasets using **BOTH** methods: (1) label permutation and (2) equal-mean simulation. Output both sets of CSVs to `data/derived/null_hypothesis/` and log the method used for each file.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Benchmarking Data with Controlled Error Injection (Priority: P1) 🎯 MVP

**Goal**: Create a reproducible pipeline that takes clean public datasets and systematically injects specific data errors to establish ground-truth baselines.

**Independent Test**: Run the injection script on a single small CSV file, verify the output contains exactly the specified percentage of modified rows, and confirm original parameters are recoverable from the unmodified subset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for `code/inject.py` random value replacement logic in `tests/unit/test_injection.py`. **Function name**: `test_replacement_preserves_distribution`. **Assertion**: `assert injected_count == total_rows * rate` and `assert original_mean == unmodified_subset_mean`.
- [ ] T016 [P] [US1] Unit test for `code/inject.py` category misclassification logic in `tests/unit/test_injection.py`. **Function name**: `test_misclassification_shifts_frequencies`. **Assertion**: `assert abs(new_freq - expected_shifted_freq) < tolerance`.
- [ ] T017 [P] [US1] Unit test for `code/inject.py` MCAR missingness logic in `tests/unit/test_injection.py`. **Function name**: `test_mcar_introduces_nans`. **Assertion**: `assert nan_count == total_cells * rate`.
- [ ] T018 [P] [US1] Integration test verifying `code/download.py` correctly validates datasets against `contracts/dataset.schema.yaml` in `tests/integration/test_download.py`. **Function name**: `test_download_validates_schema`.

### Implementation for User Story 1

- [ ] T019 [US1] Implement `code/download.py` to fetch **10 specific diverse public datasets** from UCI (Iris, Wine, Wine Quality, Adult, Heart Disease, Breast Cancer, Ionosphere, Vehicle, SPECTF, Seeds). **MUST use explicit URLs or `datasets.load_dataset()` calls** for each. Ensure N ≥ 30. Do NOT read from `research.md` at runtime.
- [ ] T020 [US1] Implement `code/inject.py` to replace values from a uniform distribution spanning observed min/max, **explicitly iterating over `error_rates = [0.01, 0.05, 0.10, 0.20]`** for each dataset.
- [ ] T021 [US1] Implement `code/inject.py` to misclassify categorical values based on observed frequency distributions, **explicitly iterating over `error_rates = [0.01, 0.05, 0.10, 0.20]`** for each dataset.
- [ ] T022 [US1] Implement `code/inject.py` to introduce MCAR missingness (NaN) randomly across rows/columns, **explicitly iterating over `error_rates = [0.01, 0.05, 0.10, 0.20]`** for each dataset.
- [ ] T023 [US1] Ensure `code/inject.py` logs the specific error rate and seed for every generated file in `data/derived/`.
- [ ] T024 [US1] Add validation logic to ensure injected data adheres to `contracts/injection.schema.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Standard Statistical Tests on Corrupted Data (Priority: P2)

**Goal**: Run standard statistical tests on clean and error-injected datasets to calculate empirical Type I error rates, CI coverage, and effect size bias.

**Independent Test**: Run the analysis script on a simulated dataset with known parameters; verify it outputs correct p-values, CIs, and effect sizes for both clean and corrupted versions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US2] Unit test for `code/analyze.py` t-test execution and metric extraction in `tests/unit/test_analyze.py`. **Function name**: `test_ttest_returns_pvalue_and_ci`. **Assertion**: `assert 0 <= p_value <= 1` and `len(ci) == 2`.
- [ ] T026 [P] [US2] Unit test for `code/analyze.py` linear regression and effect size bias calculation in `tests/unit/test_analyze.py`. **Function name**: `test_regression_calculates_bias`. **Assertion**: `assert bias == estimated_coef - truth_coef`.
- [ ] T027 [P] [US2] Unit test for `code/analyze.py` chi-squared test execution in `tests/unit/test_analyze.py`. **Function name**: `test_chi_squared_returns_statistic`. **Assertion**: `assert statistic >= 0`.

### Implementation for User Story 2

- [ ] T028 [P] [US2] Implement `code/analyze.py` to perform t-tests and ANOVA on numerical subsets, handling small N gracefully.
- [ ] T029 [P] [US2] Implement `code/analyze.py` to perform chi-squared tests on categorical subsets, skipping invalid combinations.
- [ ] T030 [US2] Implement `code/analyze.py` to perform linear regression and calculate **Sample Mean Deviation** against the **known ground-truth effect size** read dynamically from `synthetic_metadata.json` (generated by T013), not hardcoded values.
- [ ] T031 [US2] **Prerequisite Step**: Implement **listwise deletion** in `code/analyze.py`: explicitly call `df.dropna()` to remove rows with any NaN values **BEFORE** executing any statistical tests (T028/T029), as per spec assumptions.
- [ ] T032 [US2] Ensure `code/analyze.py` outputs results conforming to `contracts/result.schema.yaml` (p-value, CI, effect size, Type I flag).
- [ ] T033 [US2] Implement `code/simulate.py` full nested loop logic: iterate through datasets × error_types × **`error_rates = [0.01, 0.05, 0.10, 0.20]`** × iterations. **(Dependency: Requires T024 completion)**.
- [ ] T034 [US2] Implement aggregation logic in `code/simulate.py` to calculate empirical Type I error rates (proportion of rejections) across iterations.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize and Aggregate Degradation Metrics (Priority: P3)

**Goal**: Aggregate results across simulation runs and error rates, generating visualizations (degradation curves) and summary tables.

**Independent Test**: Feed the visualization script a JSON log of simulation results; verify it produces a PNG plot with error rate on x-axis and Type I error rate on y-axis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Unit test for `code/visualize.py` line graph generation in `tests/unit/test_visualize.py`. **Function name**: `test_plot_generates_file`. **Assertion**: `assert os.path.exists(output_path)`.
- [ ] T036 [P] [US3] Unit test for `code/visualize.py` summary table generation in `tests/unit/test_visualize.py`. **Function name**: `test_table_generates_correct_rows`. **Assertion**: `assert len(rows) == expected_count`.

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement `code/visualize.py` to plot degradation curves (Error Rate vs. Type I Error) for each test type.
- [ ] T038 [P] [US3] Implement `code/visualize.py` to plot degradation curves (Error Rate vs. CI Coverage) for each test type.
- [ ] T039 [US3] Implement `code/visualize.py` to generate comparative summary tables showing coverage failure rates across tests and error levels.
- [ ] T040 [US3] Ensure all plots are saved to `results/` with descriptive filenames including dataset and error type.
- [ ] T041 [US3] Implement a final aggregation step in `code/main.py` to compile all results into a single `results/summary.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T043 [P] Implement chunked reading in `code/download.py` and `code/inject.py` to ensure memory usage < 7GB on CI
- [ ] T044 [P] Implement a **pre-run benchmark** step in `code/simulate.py` to calculate a fixed `MAX_ITERATIONS` constant that guarantees the **full** simulation suite completes within 6 hours. **DO NOT** use dynamic runtime limiting that cuts off iterations; use the benchmark to set a safe, deterministic iteration count upfront.
- [ ] T045 [P] Additional unit tests for edge cases (N < 10, categorical-only data for t-test) in `tests/unit/`
- [ ] T046 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data injection logic (T024) for full simulation loop (T033), but analysis scripts (T028-T032) can run on existing clean data.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 analysis results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (Download/Inject/Analyze scripts)
- Services before visualization
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004-T014) can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - T019-T024 (US1) can run in parallel
  - T028-T032 (US2 analysis logic) can run in parallel (on clean data)
  - T033 (Full simulation loop) must wait for T024 (US1 completion)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/inject.py random value replacement logic in tests/unit/test_injection.py (test_replacement_preserves_distribution)"
Task: "Unit test for code/inject.py category misclassification logic in tests/unit/test_injection.py (test_misclassification_shifts_frequencies)"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to fetch specific real datasets from UCI (Iris, Wine, etc.)"
Task: "Implement code/inject.py to replace values from a uniform distribution"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify injection rates match)
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
   - Developer A: User Story 1 (Data Injection)
   - Developer B: User Story 2 (Statistical Analysis logic on clean data)
   - Developer C: User Story 3 (Visualization logic)
3. Full simulation loop (T033) starts only after Developer A completes T024.
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All tasks must run on CPU-only CI (no GPU, no 8-bit quantization, no large LLMs). Use `scipy` and `statsmodels` in default precision.
- **CRITICAL**: Dataset downloads must use real URLs (UCI) or `datasets.load_dataset()`. No fake/synthetic data for inputs. T019 explicitly lists 10 datasets.
- **CRITICAL**: Ensure simulation iterations are deterministic and complete within 6 hours via pre-run benchmark (T044).
- **CRITICAL**: Explicitly implement listwise deletion (dropna) for missing data handling (T031) BEFORE running tests.
- **CRITICAL**: Explicitly iterate over error_rates = [0.01, 0.05, 0.10, 0.20] in all relevant tasks.
- **CRITICAL**: Synthetic data generation (T013) must use a grid of parameters, not a single hardcoded set.
- **CRITICAL**: Null-hypothesis generation (T014) must implement BOTH methods.
- **CRITICAL**: Validation metrics (T030) must read truth from `synthetic_metadata.json`, not hardcoded values.