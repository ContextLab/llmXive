# Tasks: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-variable-select/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-504-evaluating-the-impact-of-variable-select/` at repository root
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

- [X] T001 Create project structure per implementation plan: `projects/PROJ-504-evaluating-the-impact-of-variable-select/` containing `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/integration/`. Includes explicit validation logic to ensure the directory structure exists and is writable before proceeding (FR-001)
- [X] T002 Initialize Python project with `requirements.txt` pinning versions (e.g., `scikit-learn>=1.4.0 `, `statsmodels>=0.14.0 `, `openml>=0.14.0 `, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`) (FR-002)
- [X] T003 [P] Configure linting and formatting by creating `code/pyproject.toml` with `[tool.black]` section ( (Wikipedia: Python (programming language), https://en.wikipedia.org/wiki/Python_(programming_language)), line-length = 88) and `code/.flake8` file with `[flake8]` section (max-line-length = 88, extend-ignore = E203) to enforce style consistency (FR-003)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Pilot Run, Performance Optimizations, and Data Hygiene.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T004 (Pilot Run) acts as a Gate: Abort if pilot fails.** **T045/T046 (Optimizations) must be implemented here to ensure -hour runtime for Phase simulations.**

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] **Pilot Run & Gate**: Implement `code/verify.py` to run a small-scale simulation (e.g., a limited set of datasets) to verify runtime and CI width. **Gate**: If runtime > 5.5h or CI width > 0.1, abort and log error. If successful, write the validated `simulations_per_condition` count (target: a substantial cohort) to `code/config.py` for downstream tasks. (Plan Feasibility, FR-002, SC-003)
- [X] T005 [P] Setup `data/raw/` and `data/processed/` directory structure with `.gitkeep`
- [X] T006 [P] Create `code/data/__init__.py` and `code/analysis/__init__.py`
- [X] T007 [P] Create base configuration loader in `code/config.py` to manage seeds and paths; must load keys: `seed`, `openml_ids`, `snr_levels`, `sparsity_levels`, `output_path`, and `simulations_per_condition` (populated by T004) (FR-006)
- [X] T008 Create base data models in `code/models.py`: `SimulatedDataset` (fields: X, Y, true_coefficients, snr, sparsity, seed, dataset_id) and `PowerMetric` (fields: method, snr, sparsity, alpha, power_rate, ci_lower, ci_upper) (FR-007)
- [X] T009 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T010 [P] Setup environment configuration management for CI limits: explicitly configure and expose 'vCPU' and 'RAM' constraints in `code/config.py` and `code/utils/limits.py` for downstream tasks to reference (FR-008, SC-003, SC-004)
- [X] T045 [P] **Performance Optimization**: Implement `code/utils/watchdog.py` and `code/analysis/selectors.py` with **early stopping** for stepwise selection and **predictor pruning** logic. These optimizations are **required** for the 6-hour runtime (SC-003) and MUST be implemented here, before Phase 3. (FR-008, Plan Feasibility)
- [X] T046 [P] **Early Stopping Logic**: Implement specific early stopping logic in `code/analysis/selectors.py` for Forward Stepwise selection (stop if AIC does not improve for N steps) and predictor pruning (remove highly correlated predictors before stepwise) to reduce computational load and meet acceptable runtime constraints.. **This logic is imported by T019/T020 and must be available before Phase 3 starts.** (FR-008, Plan Feasibility)
- [X] T051 [P] **Data Hygiene**: Implement explicit SHA-256 checksum generation for all raw OpenML files upon download in `code/data/downloader.py`; store checksums in `state/checksums.json` and verify before simulation (Constitution Principle III)
- [X] T052 [P] **Data Validation**: Add a `code/data/validator.py` script that runs after T018 to verify all 10 datasets meet the minimum row/column constraints and condition number thresholds before proceeding to simulation (FR-001, Edge Case: Perfect multicollinearity)
- [X] T057 [P] **Runtime Watchdog**: Implement a `code/utils/watchdog.py` module that monitors total runtime and triggers a graceful shutdown with a partial results save if the **6**-hour limit is approached (FR-008, SC-003)
- [X] T058 [P] **Memory Monitoring**: Enhance `code/data/simulators.py` to include a `tracemalloc` snapshot at the start and end of each batch of simulations; write peak memory usage to `data/processed/memory_profile.log` and abort if > 6.5 GB (SC-004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline & Simulation Loop (Priority: P1) 🎯 MVP

**Goal**: Download a set of real OpenML regression datasets for evaluation. The research question focuses on assessing the generalizability of the proposed method across diverse regression tasks. The method involves selecting representative datasets from the OpenML repository and applying the evaluation protocol. References: DOI:10.21105/joss.01686., extract covariance structures, and simulate synthetic outcome vectors across multiple SNR and Sparsity levels with ground-truth coefficients.

**Independent Test**: Verify that 10 datasets with ≥100 rows and ≥3 predictors are loaded, and that a large set of synthetic outcome vectors (Multiple simulations across conditions) are generated and stored in `data/processed/` with correct metadata.

### Tests for User Story 1 (TDD-First) ⚠️

> **NOTE: Write these tests FIRST (TDD-First), ensure they FAIL before implementation**

- [X] T011 [TDD-First] [P] [US1] Unit test for OpenML downloader in `tests/unit/test_downloader.py`: function `test_downloader_fetches_10_datasets` asserts `len(datasets) == 10` and `all(d.n_rows >= 100)` and `all(d.n_features >= 3)` (FR-001)
- [X] T012 [TDD-First] [P] [US1] Unit test for simulator in `tests/unit/test_simulators.py`: function `test_simulator_generates_correct_snr` asserts generated Y variance matches SNR target within tolerance (FR-002)
- [X] T013 [TDD-First] [P] [US1] Integration test for full download+simulate pipeline in `tests/integration/test_pipeline.py`: function `test_pipeline_generates_expected_rows` asserts `len(results_df) == <count from config>` (derived from T004) (FR-002, US-1)

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `code/data/downloader.py` to fetch regression datasets from OpenML with retry logic with **time-based exponential backoff** (limited retry attempts) and checksumming; validate ≥ 100 rows and ≥ 3 predictors; raise hard failure if retries exhausted (FR-001, Edge Case: API timeout)
- [X] T015 [P] [US1] Implement `code/data/downloader.py` logic to skip datasets with condition number > 10^10 and log warning to `code/utils/logger.py` (FR-001)
- [X] T018 [US1] Implement logic in `code/data/pipeline.py` to **fetch exactly 10 datasets** from OpenML. **Retry Logic**: If <10 valid datasets are found, retry fetching from a pre-defined backup list of OpenML IDs. **Selection**: Select the first 10 valid datasets from the sorted list of fetched IDs. **Fail Hard**: If <10 valid datasets are found after all retries, abort. (FR-001, Edge Case: API timeout, Coverage-4bca829c)
- [X] T016 [P] [US1] Implement `code/data/simulators.py` configuration to support low to moderate SNR levels and Sparsity levels **{, 0.2, 0.4}**; **Must read `simulations_per_condition` from `code/config.py` (populated by T004)**; MUST run after T018 and T004 (FR-002, Plan Feasibility)
- [X] T019 [US1] Implement `code/data/simulators.py` to generate synthetic Y vectors using real X covariance and ground-truth coefficients; includes memory-efficient chunking (process a batch of simulations) and monitoring via `psutil` to abort if RAM exceeds a defined safety threshold consistent with system constraints. **Depends on T046** (Early Stopping Logic) being completed in Phase 2. (FR-002, SC-004, Plan Feasibility)
- [X] T017 [US1] Implement `code/data/simulators.py` to record true coefficients and **the exact number of synthetic outcome vectors generated per simulation run** in the result metadata for every run (FR-002, Constitution Principle VI)
- [X] T053 [US1] Enhance `code/data/simulators.py` logging to explicitly record: (a) exact simulation count (from T004), (b) random seed, (c) covariance source (dataset ID and name), (d) SNR/Sparsity params for **every single run** (Constitution Principle VI)
- [X] T054 [US1] Add a verification task in `code/verify.py` to randomly sample a representative subset of rows from `data/processed/simulation_results.csv` and confirm that `dataset_name` and `dataset_id` are present and non-null for each (T015, Constitution Principle VI)
- [X] T020 [US1] Create `data/processed/` storage logic in `code/data/storage.py` to save results as Parquet/CSV with deterministic seeds; explicitly enforce the **multiple datasets** constraint and **simulation count from T004** rule before writing simulation results; MUST run after T019, T016, T018; includes explicit mandate to checksum all derived files in `data/processed/` per Constitution Principle III (FR-002, SC-004, Constitution III)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Power Metric Computation (Priority: P2)

**Goal**: Apply Forward Stepwise, Backward Elimination, and LASSO selection methods to each simulated dataset, refit OLS, and calculate empirical power (proportion of true non-zero coefficients selected AND significant).

**Independent Test**: Run selection methods on a subset of simulations and verify that Power = (True Positives / Total True Non-Zero Coefficients) matches expected values within ±0.01 tolerance

### Tests for User Story 2 (TDD-First) ⚠️

- [X] T021 [TDD-First] [P] [US2] Unit test for selection methods in `tests/unit/test_selectors.py`: function `test_forward_stepwise_selects_correct_vars`
- [X] T022 [TDD-First] [P] [US2] Unit test for power calculation in `tests/unit/test_metrics.py`: function `test_power_calculation_matches_ground_truth`
- [X] T023 [TDD-First] [P] [US2] Integration test for selection+refit pipeline in `tests/integration/test_selectors.py`: function `test_full_selection_pipeline`
- [X] T059 [US2] Add a contract test in `tests/contract/test_schema.py` to validate that `data/processed/simulation_results.csv` strictly adheres to the `simulation_result.schema.yaml` (T026, Constitution Principle VII)

### Implementation for User Story 2 (Implementation MUST follow tests)

- [X] T024 [P] [US2] Implement `code/analysis/selectors.py` for Forward Stepwise selection using CPU-only execution and **AIC criterion** (Per plan.md Decision Rationale to resolve Spec FR-003 ambiguity) (FR-003)
- [X] T025 [P] [US2] Implement `code/analysis/selectors.py` for Backward Elimination selection using CPU-only execution (FR-003)
- [X] T026 [P] [US2] Implement `code/analysis/selectors.py` for LASSO selection using CPU-only execution (FR-003)
- [X] T027 [US2] Implement `code/analysis/metrics.py` to record selected variables, decision thresholds, and collinearity diagnostics (VIF/condition number) directly into the main simulation results dataframe (Parquet/CSV) at **`data/processed/simulation_results.csv`**; **Do NOT write to `results/` directory**; MUST run after T024-T026 to ensure data availability (FR-003, FR-007, Constitution Principle IV, VII)
- [X] T028 [US2] Implement `code/analysis/metrics.py` to refit OLS on variables selected by Forward Stepwise, Backward Elimination, AND LASSO; calculate p-values for power determination; **PRIMARY METRIC**: Empirical Power (proportion of true non-zero coefficients selected AND significant with p < 0.05) (FR-004, FR-009)
- [X] T029 [US2] Implement `code/analysis/metrics.py` to calculate empirical power as proportion of true non-zero coefficients selected AND significant (p < 0.05) per Spec FR-004; includes logic to filter `true_coefficients != 0` before calculating the denominator (FR-004)
- [X] T030 [US2] Implement `code/analysis/metrics.py` to calculate VIF or condition number for all datasets as collinearity diagnostics (FR-007)
- [X] T032 [US2] Add explicit handling in `code/analysis/metrics.py` to exclude true-zero coefficients from the power denominator, treating them as true negatives; MUST be implemented and logically integrated before T029 to ensure mathematical validity (FR-004, Edge Case: Zero true coefficient)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Visualization (Priority: P3)

**Goal**: Compare power rates across methods using Kruskal-Wallis and Dunn's post-hoc tests, perform sensitivity analysis on alpha thresholds, and generate power curves.

**Independent Test**: Provide a CSV of simulation-level mean power and verify that p-values are corrected (Holm) and plots are generated for all SNR/Sparsity/Alpha combinations.

### Tests for User Story 3 (TDD-First) ⚠️

- [X] T033 [TDD-First] [P] [US3] Unit test for Kruskal-Wallis and Dunn's test in `tests/unit/test_comparators.py`: function `test_kruskal_wallis_correctness`
- [X] T034 [TDD-First] [P] [US3] Unit test for plot generation in `tests/unit/test_plots.py`: function `test_plot_generation_saves_file`
- [X] T035 [TDD-First] [P] [US3] Integration test for statistical analysis pipeline in `tests/integration/test_comparators.py`: function `test_full_statistical_pipeline`
- [X] T060 [US3] Add a unit test in `tests/unit/test_comparators.py` to verify that Dunn's post-hoc test correctly applies Holm correction by comparing against a known synthetic dataset with known p-values (T033, FR-005)

### Implementation for User Story 3

- [X] T036 [US3] Validate `data/processed/simulation_results.csv` contains required columns (method, snr, sparsity, power_rate) and sufficient rows to ensure simulation-level granularity is preserved for T037 (FR-005)
- [X] T055 [US3] Add a pre-check in `code/analysis/comparators.py` to assert that the input dataframe contains **individual simulation-level rows** (n=24,000) and NOT aggregated means before running Kruskal-Wallis; fail loudly if aggregated data is detected (FR-005, SC-002)
- [X] T037 [P] [US3] Implement `code/analysis/comparators.py` to perform Kruskal-Wallis tests on the **simulation-level data** (n=24,000 rows) from `data/processed/simulation_results.csv` per Spec FR-005; unit of analysis is individual simulation; MUST run after T036 to ensure input data validity (FR-005)
- [X] T038 [US3] Implement `code/analysis/comparators.py` to run Dunn's post-hoc analysis with Holm correction for multiplicity on simulation-level data per Spec FR-005 (FR-005)
- [X] T039 [US3] Implement `code/analysis/comparators.py` to perform sensitivity analysis on Alpha across a range of representative values as required by FR-006 (FR-006)
- [X] T040 [US3] Implement `code/viz/plots.py` to generate Power vs. SNR curves for each selection method, explicitly faceted or differentiated by Sparsity level **AND Alpha thresholds (including 0.05 and 0.10) will be evaluated to determine the optimal significance level for the analysis.** in the code logic (FR-003, US-3)
- [X] T041 [US3] Implement `code/viz/plots.py` to save all plots to `results/plots/`
- [X] T042 [US3] Generate final summary report as Markdown at `results/final_report.md` with sections: 'Executive Summary', 'Statistical Results (Kruskal-Wallis, Dunn)', 'Power Curves', and 'Methodology Notes'; include a verification step to ensure summary stats match `data/processed/simulation_results.csv` by **computing mean power per condition and comparing to CSV rows** (FR-005)
- [X] T050 [US3] Ensure sensitivity analysis in `code/analysis/comparators.py` explicitly iterates over a set of candidate values and generates separate power curves for each. **Note**: This task is redundant with T039 but included for explicit report generation of sensitivity metrics (FR-006)
- [X] T056 [US3] Implement a "Sensitivity Report" task in `code/analysis/comparators.py` that explicitly compares power rates at Alpha=0.01, 0.05, and 0.10 and writes a summary CSV to `results/sensitivity_report.csv` (FR-006, SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `README.md` and `docs/`
- [ ] T044 Code cleanup and refactoring in `code/`
- [ ] T047 [P] Additional unit tests in `tests/unit/`
- [ ] T048 Run quickstart.md validation
- [ ] T049 Verify reproducibility by re-running pipeline with pinned seeds and comparing checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes T045/T046 (Optimizations) which are prerequisites for Phase 3.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion (including T045/T046).
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metric computation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD-First)
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
Task: "Unit test for OpenML downloader in tests/unit/test_downloader.py"
Task: "Unit test for simulator in tests/unit/test_simulators.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/downloader.py"
Task: "Implement code/data/simulators.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Pilot Run T004 and Optimizations T045/T046)
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
- [TDD-First] indicates tests define interface before implementation
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence