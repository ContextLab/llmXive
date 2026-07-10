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

- [ ] T001 [P] Create project directory structure with exact tree: `data/raw`, `data/processed`, `code`, `results`, `tests`. **MUST include creating empty `__init__.py` files in `code/` and `tests/` directories** to ensure Python package recognition. **Note**: The path `data/processed` is used for error-injected data as per Plan.md Project Structure, replacing the previous `data/derived` convention.
- [ ] T002 [P] Initialize Python project with dependencies: pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, pytest
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes ground-truth data generation (FR-006, FR-007) and skeleton creation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining valid tabular dataset structures
- [ ] T005a [P] Create `contracts/injection.schema.yaml` defining error types (replacement, misclassification, MCAR) and rates `[0.01, 0.05, 0.10, 0.20]`. **MUST explicitly state that these rates must be applied to ALL three error types** (replacement, misclassification, MCAR) as required by FR-002 and Constitution Principle VI.
- [ ] T005b [P] [TDD] Write a unit test in `tests/unit/test_schema_validation.py` that loads `contracts/injection.schema.yaml` and asserts that the `error_rates` field exactly matches `[0.01, 0.05, 0.10, 0.20]`. **This test must be written BEFORE implementation tasks T020-T022 to ensure schema consistency.**
- [ ] T006 [P] Create `contracts/result.schema.yaml` defining output metrics (p-value, CI bounds, effect size, Type I flag)
- [ ] T007 [P] Create `code/download.py` skeleton (empty file with imports and main function stub)
- [ ] T008 [P] Create `code/inject.py` skeleton (empty file with imports and main function stub)
- [ ] T009 [P] Create `code/analyze.py` skeleton (empty file with imports and main function stub)
- [ ] T010 [P] Create `code/simulate.py` skeleton (empty file with imports and main function stub)
- [ ] T011 [P] Create `code/visualize.py` skeleton (empty file with imports and main function stub)
- [ ] T012 [P] Create `code/main.py` skeleton (CLI entry point stub)
- [ ] T013 [P] [FR-006] Implement `code/simulate.py` to generate synthetic datasets with **known population parameters** across an expanded grid: iterate over `effect_sizes=[0.2, 0.5, 0.8]`, `variances=[1.0, 2.0, 4.0]`, **`sample_sizes=[30, 100, 500]`**, and **`skewness=[0, 1, -1]`**. Output CSVs to `data/processed/synthetic_grid/` and write a `synthetic_metadata.json` file mapping each file to its exact parameters (mean, variance, effect_size, sample_size, skewness) for downstream consumption.
- [ ] T014 [P] [FR-007] Implement `code/simulate.py` to generate null-hypothesis datasets using **BOTH** methods: (1) label permutation and (2) equal-mean simulation. Output both sets of CSVs to `data/processed/null_hypothesis/` and log the method used for each file.

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

### Implementation for User Story 1

- [ ] T018a [P] [US1] Write stubs for integration tests for `code/download.py` schema validation in `tests/integration/test_download.py`. **Function name**: `test_download_validates_schema`. **Note**: This task creates the test file that will assert `code/download.py` validates datasets against `contracts/dataset.schema.yaml` once T019 is implemented. No dependency on T019 completion required for file creation (TDD flow).
- [ ] T019 [US1] Implement `code/download.py` to fetch **5-10 diverse public datasets** from UCI. **Initial list**: Iris, Wine, Wine Quality, Adult, Heart Disease, Breast Cancer, Ionosphere, Vehicle, SPECTF, Seeds. **Algorithm**: 
    1. Load the initial list.
    2. Verify diversity: count numerical-only, categorical-only, and mixed datasets.
    3. **If diversity constraint (at least 2 numerical-only, 2 categorical-only) is NOT met**: Dynamically fetch additional datasets from the UCI Machine Learning Repository API (using `datasets.load_dataset()` or direct CSV fetch) until the constraint is satisfied.
    4. Save all valid datasets to `data/raw/` with checksums.
    **MUST use explicit URLs or `datasets.load_dataset()` calls for each.** Do NOT read from `research.md` at runtime.
- [ ] T020 [US1] Implement `code/inject.py` to replace values from a uniform distribution spanning observed min/max, **explicitly iterating over `error_rates = [, 0.05, 0.10, 0.20]`** for each dataset. Output to `data/processed/`.
- [ ] T021 [US1] Implement `code/inject.py` to misclassify categorical values based on observed frequency distributions, **explicitly iterating over `error_rates = [0.01, 0.05, 0.10, 0.20]`** for each dataset. Output to `data/processed/`.
- [ ] T022 [US1] Implement `code/inject.py` to introduce MCAR missingness (NaN) randomly across rows/columns, **explicitly iterating over `error_rates = [0.01, 0.05, 0.10, 0.20]`** for each dataset. Output to `data/processed/`.
- [ ] T023 [US1] Ensure `code/inject.py` logs the specific error rate and seed for every generated file in `data/processed/`.
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

- [ ] T028 [US2] Implement `code/analyze.py` to perform **all** statistical tests. **MUST implement four distinct functions**: `run_ttest()`, `run_anova()`, `run_chi_squared()`, `run_regression()`. **Input Scope**: Must process **BOTH** `data/raw/` (clean datasets) AND `data/processed/` (corrupted datasets generated by T030). **Dependency**: T019 (clean data) and T024 (injection validation). **Logic**: For corrupted data, this task MUST execute **after** T030 (Data Generation) completes the injection loop. **Output**: Save individual test results (p-value, CI, effect size) to `results/raw_metrics/` for each dataset/error combination.
- [ ] T029a [US2] [Prerequisite] Implement **listwise deletion** utility function in `code/analyze.py` named `handle_missing_data()`. **Action**: Explicitly call `df.dropna()` to remove rows with any NaN values **BEFORE** executing any statistical tests. **MUST calculate and output a `power_loss_metric` (sample size reduction)** to explicitly distinguish power loss from Type I error stability, as required by Spec Assumptions. **Dependency**: T028 (Analysis logic) must call this function. **Note**: This is a distinct helper task to ensure T028 remains focused on statistical logic.
- [ ] T029b [US2] [Validation] Implement logic in `code/analyze.py` to calculate **Sample Mean Deviation** against the **known ground-truth effect size** read dynamically from `synthetic_metadata.json` (generated by T013). **MUST explicitly read the 'effect_size' field from metadata.** **MUST also calculate and output `ci_coverage_frequency` (proportion of intervals containing the true value)** to satisfy SC-002. **Explicit Verification**: Calculate the deviation from the theoretical high coverage target and assert it is within a tight tolerance. **Input Scope**: Must process **BOTH** clean and corrupted datasets. **Requires T030 (corrupted data generation) for the corrupted subset.**
- [ ] T030 [US2] **Data Generation & Injection Loop**: Implement `code/simulate.py` full nested loop logic: iterate through datasets × error_types × **`error_rates = [0.01, 0.05, 0.10, 0.20]`** × iterations. **Dependency**: Requires T024 (injection validation) and T028 (Analysis logic for clean baseline). **Action**: Generates the corrupted datasets required for T028 to analyze. **Output**: Writes corrupted CSVs to `data/processed/` and logs generation parameters. **Note**: This task generates data but does NOT perform aggregation; aggregation is handled in T032.
- [ ] T032 [US2] Implement aggregation logic in `code/simulate.py` to calculate empirical Type I error rates (proportion of rejections) AND **confidence interval coverage rates** (proportion of intervals containing the true population parameter) across iterations. **MUST output `ci_coverage_rate`** to satisfy FR-004 and SC-002. **Requires T030 (full simulation loop) and T028 (Analysis results)** to be complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize and Aggregate Degradation Metrics (Priority: P3)

**Goal**: Aggregate results across simulation runs and error rates, generating visualizations (degradation curves) and summary tables.

**Independent Test**: Feed the visualization script a JSON log of simulation results; verify it produces a PNG plot with error rate on x-axis and Type I error rate on y-axis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for `code/visualize.py` line graph generation in `tests/unit/test_visualize.py`. **Function name**: `test_plot_generates_file`. **Assertion**: `assert os.path.exists(output_path)`.
- [ ] T034 [P] [US3] Unit test for `code/visualize.py` summary table generation in `tests/unit/test_visualize.py`. **Function name**: `test_table_generates_correct_rows`. **Assertion**: `assert len(rows) == expected_count`.

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement `code/visualize.py` to plot degradation curves (Error Rate vs. Type I Error) for each test type.
- [ ] T036 [P] [US3] Implement `code/visualize.py` to plot degradation curves (Error Rate vs. CI Coverage) for each test type.
- [ ] T037 [US3] Implement `code/visualize.py` to generate comparative summary tables showing coverage failure rates across tests and error levels.
- [ ] T038 [US3] Ensure all plots are saved to `results/` with descriptive filenames including dataset and error type.
- [ ] T039 [US3] Implement a final aggregation step in `code/main.py` to compile all results into a single `results/summary.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T041 [P] Implement chunked reading in `code/download.py` and `code/inject.py` to ensure memory usage < 7GB on CI
- [ ] T042 [P] Implement a **pre-run benchmark** step in `code/simulate.py` to calculate a fixed `MAX_ITERATIONS` constant that guarantees the **full** simulation suite completes within 6 hours. **DO NOT** use dynamic runtime limiting that cuts off iterations; use the benchmark to set a safe, deterministic iteration count upfront.
- [ ] T043 [P] Additional unit tests for edge cases (N < 10, categorical-only data for t-test) in `tests/unit/`
- [ ] T044 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data injection logic (T024) for full simulation loop (T030), but analysis scripts (T028-T029b) can run on existing clean data (`data/raw`).
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
  - T018a-T024 (US1) can run in parallel
  - T028-T029b (US2 analysis logic) can run in parallel (on clean data `data/raw`)
  - T030 (Full simulation loop) must wait for T024 (US1 completion) and T028 (Analysis logic)
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
3. Full simulation loop (T030) starts only after Developer A completes T024 and Developer B completes T028 (clean baseline).
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
- **CRITICAL**: Dataset downloads must use real URLs (UCI) or `datasets.load_dataset()`. No fake/synthetic data for inputs. T019 explicitly lists 10 datasets but includes a verification step for diversity and a fallback mechanism.
- **CRITICAL**: Ensure simulation iterations are deterministic and complete within 6 hours via pre-run benchmark (T042).
- **CRITICAL**: Explicitly implement listwise deletion (dropna) for missing data handling (T029a) BEFORE running tests, and measure power loss.
- **CRITICAL**: Explicitly iterate over error_rates = [0.01, 0.05, 0.10, 0.20] in all relevant tasks.
- **CRITICAL**: Synthetic data generation (T013) must use an expanded grid (effect_size, variance, sample_size, skewness) for robust validation.
- **CRITICAL**: Null-hypothesis generation (T014) must implement BOTH methods.
- **CRITICAL**: Validation metrics (T029b) must read truth from `synthetic_metadata.json`, not hardcoded values, and MUST include CI coverage calculation and 95% target verification.
- **CRITICAL**: T030 (Simulation Loop) MUST precede T028 (Analysis of corrupted data) to ensure data availability. Clean data analysis can proceed earlier.
- **CRITICAL**: T032 explicitly calculates CI coverage rates to satisfy FR-004 and SC-002.
- **CRITICAL**: All paths must use `data/processed` for injected data as per Plan.md, not `data/derived`.
- **CRITICAL**: T005b ensures schema consistency via unit test.
- **CRITICAL**: T028 is now a SINGLE task implementing ALL statistical tests to avoid duplication ambiguity.
- **CRITICAL**: T029a is a distinct prerequisite task for listwise deletion, resolving the duplicate task concern.
- **CRITICAL**: T030 is pure data generation; T032 is pure aggregation, resolving the circular dependency concern.