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

- [ ] T001 Create project structure per implementation plan: `projects/PROJ-504-evaluating-the-impact-of-variable-select/` containing `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/integration/` (FR-001)
- [X] T002 Initialize Python project with `requirements.txt` pinning versions (e.g., `scikit-learn>=1.4.0`, `statsmodels>=0.14.0`, `openml>=0.14.0`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`) (FR-002)
- [X] T003 [P] Configure linting and formatting by creating `code/pyproject.toml` with `[tool.black]` section (target-version = 3.11, line-length = 88) and `code/.flake8` file with `[flake8]` section (max-line-length = 88, extend-ignore = E203) to enforce style consistency (FR-003)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup `data/raw/` and `data/processed/` directory structure with `.gitkeep`
- [X] T005 [P] Create `code/data/__init__.py` and `code/analysis/__init__.py`
- [X] T006 [P] Create base configuration loader in `code/config.py` to manage seeds and paths; must load keys: `seed`, `openml_ids`, `snr_levels`, `sparsity_levels`, `output_path` (FR-006)
- [X] T007 Create base data models in `code/models.py`: `SimulatedDataset` (fields: X, Y, true_coefficients, snr, sparsity, seed, dataset_id) and `PowerMetric` (fields: method, snr, sparsity, alpha, power_rate, ci_lower, ci_upper) (FR-007)
- [X] T008 Setup error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T009 [P] Setup environment configuration management for CI limits: explicitly configure and expose 'vCPU' and 'RAM' constraints in `code/config.py` and `code/utils/limits.py` for downstream tasks to reference (FR-008, SC-003, SC-004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline & Simulation Loop (Priority: P1) 🎯 MVP

**Goal**: Download a set of real OpenML regression datasets for evaluation. The research question focuses on assessing the generalizability of the proposed method across diverse regression tasks. The method involves selecting representative datasets from the OpenML repository and applying the evaluation protocol. References: DOI:10.21105/joss.01686., extract covariance structures, and simulate synthetic outcome vectors across 4 SNR and Sparsity levels with ground-truth coefficients.

**Independent Test**: Verify that 10 datasets with ≥100 rows and ≥3 predictors are loaded, and that A large set of synthetic outcome vectors (Multiple simulations across 12 conditions) are generated and stored in `data/processed/` with correct metadata.

### Tests for User Story 1 (TDD-First) ⚠️

> **NOTE: Write these tests FIRST (TDD-First), ensure they FAIL before implementation**

- [X] T010 [TDD-First] [P] [US1] Unit test for OpenML downloader in `tests/unit/test_downloader.py`: function `test_downloader_fetches_10_datasets` asserts `len(datasets) == 10` and `all(d.n_rows >= 100)` and `all(d.n_features >= 3)` (FR-001)
- [X] T011 [TDD-First] [P] [US1] Unit test for simulator in `tests/unit/test_simulators.py`: function `test_simulator_generates_correct_snr` asserts generated Y variance matches SNR target within tolerance (FR-002)
- [X] T012 [TDD-First] [P] [US1] Integration test for full download+simulate pipeline in `tests/integration/test_pipeline.py`: function `test_pipeline_generates_expected_rows` asserts `len(results_df) == 24000` (200 sims * 10 datasets * 4 SNR * 3 Sparsity) (FR-002, US-1)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data/downloader.py` to fetch regression datasets from OpenML with retry logic with **time-based exponential backoff** (limited retry attempts) and checksumming; validate ≥ 100 rows and ≥ 3 predictors; raise hard failure if retries exhausted (FR-001, Edge Case: API timeout)
- [X] T014 [P] [US1] Implement `code/data/downloader.py` logic to skip datasets with condition number > 10^10 and log warning to `code/utils/logger.py` (FR-001)
- [ ] T019 [US1] Create `data/processed/` storage logic in `code/data/storage.py` to save results as Parquet/CSV with deterministic seeds; explicitly enforce the ** datasets** constraint and ** simulations per condition** rule before writing simulation results (FR-002)
- [X] T016 [US1] Implement `code/data/simulators.py` configuration to support low to moderate SNR levels and Sparsity levels **{0.2, 0.4}** (FR-002)
- [X] T015 [US1] Implement `code/data/simulators.py` to generate synthetic Y vectors using real X covariance and ground-truth coefficients; includes memory-efficient chunking (process a batch of simulations) and monitoring via `psutil` to abort if RAM exceeds a defined safety threshold consistent with system constraints. (FR-002, SC-004)
- [X] T017 [US1] Implement `code/data/simulators.py` to record true coefficients and simulation metadata for every run (FR-002)
- [X] T018 [US1] Implement logic in `code/data/pipeline.py` to select a representative subset of valid datasets from the fetched pool, ensuring the count constraint (FR-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Power Metric Computation (Priority: P2)

**Goal**: Apply Forward Stepwise, Backward Elimination, and LASSO selection methods to each simulated dataset, refit OLS, and calculate empirical power (proportion of true non-zero coefficients selected AND significant).

**Independent Test**: Run selection methods on a subset of simulations and verify that Power = (True Positives / Total True Non-Zero Coefficients) matches expected values within ±0.01 tolerance.

### Tests for User Story 2 (TDD-First) ⚠️

- [X] T021 [TDD-First] [P] [US2] Unit test for selection methods in `tests/unit/test_selectors.py`: function `test_forward_stepwise_selects_correct_vars`
- [X] T022 [TDD-First] [P] [US2] Unit test for power calculation in `tests/unit/test_metrics.py`: function `test_power_calculation_matches_ground_truth`
- [ ] T023 [TDD-First] [P] [US2] Integration test for selection+refit pipeline in `tests/integration/test_selectors.py`: function `test_full_selection_pipeline`

### Implementation for User Story 2 (Implementation MUST follow tests)

- [ ] T027 [US2] Implement `code/analysis/metrics.py` to record selected variables, decision thresholds, and collinearity diagnostics (VIF/condition number) directly into the main simulation results dataframe (Parquet/CSV) at **`data/processed/simulation_results.csv`**; **Do NOT write to `results/` directory** (FR-003, FR-007, Constitution Principle IV, VII)
- [ ] T024 [P] [US2] Implement `code/analysis/selectors.py` for Forward Stepwise selection using CPU-only execution and **AIC criterion** (FR-003)
- [ ] T025 [P] [US2] Implement `code/analysis/selectors.py` for Backward Elimination selection using CPU-only execution (FR-003)
- [ ] T026 [P] [US2] Implement `code/analysis/selectors.py` for LASSO selection using CPU-only execution (FR-003)
- [ ] T028 [US2] Implement `code/analysis/metrics.py` to refit OLS on variables selected by Forward Stepwise, Backward Elimination, AND LASSO; calculate p-values for power determination; **PRIMARY METRIC**: Empirical Power (proportion of true non-zero coefficients selected AND significant with p < 0.05) (FR-004, FR-009)
- [ ] T029 [US2] Implement `code/analysis/metrics.py` to calculate empirical power as proportion of true non-zero coefficients selected AND significant (p < 0.05) per Spec FR-004; includes logic to filter `true_coefficients != 0` before calculating the denominator (FR-004)
- [ ] T030 [US2] Implement `code/analysis/metrics.py` to calculate VIF or condition number for all datasets as collinearity diagnostics (FR-007)
- [ ] T032 [US2] Add explicit handling in `code/analysis/metrics.py` to exclude true-zero coefficients from the power denominator, treating them as true negatives (FR-004, Edge Case: Zero true coefficient)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Visualization (Priority: P3)

**Goal**: Compare power rates across methods using Kruskal-Wallis and Dunn's post-hoc tests, perform sensitivity analysis on alpha thresholds, and generate power curves.

**Independent Test**: Provide a CSV of simulation-level mean power and verify that p-values are corrected (Holm) and plots are generated for all SNR/Sparsity/Alpha combinations.

### Tests for User Story 3 (TDD-First) ⚠️

- [ ] T033 [TDD-First] [P] [US3] Unit test for Kruskal-Wallis and Dunn's test in `tests/unit/test_comparators.py`: function `test_kruskal_wallis_correctness`
- [ ] T034 [TDD-First] [P] [US3] Unit test for plot generation in `tests/unit/test_plots.py`: function `test_plot_generation_saves_file`
- [ ] T035 [TDD-First] [P] [US3] Integration test for statistical analysis pipeline in `tests/integration/test_comparators.py`: function `test_full_statistical_pipeline`

### Implementation for User Story 3

- [ ] T036 [US3] Validate `data/processed/simulation_results.csv` contains required columns (method, snr, sparsity, power_rate) and sufficient rows to ensure simulation-level granularity is preserved for T037 (FR-005)
- [ ] T037 [P] [US3] Implement `code/analysis/comparators.py` to perform Kruskal-Wallis tests on the **simulation-level data** (n=24,000 rows) from `data/processed/simulation_results.csv` per Spec FR-005; unit of analysis is individual simulation (FR-005)
- [ ] T038 [US3] Implement `code/analysis/comparators.py` to run Dunn's post-hoc analysis with Holm correction for multiplicity on simulation-level data per Spec FR-005 (FR-005)
- [ ] T039 [US3] Implement `code/analysis/comparators.py` to perform sensitivity analysis on Alpha across a range of representative values (FR-006)
- [ ] T040 [US3] Implement `code/viz/plots.py` to generate Power vs. SNR curves for each selection method, explicitly faceted or differentiated by Sparsity level **AND Alpha thresholds {, conventional significance levels, 0.10}** in the code logic (FR-003, US-3)
- [ ] T041 [US3] Implement `code/viz/plots.py` to save all plots to `results/plots/`
- [ ] T042 [US3] Generate final summary report as Markdown at `results/final_report.md` with sections: 'Executive Summary', 'Statistical Results (Kruskal-Wallis, Dunn)', 'Power Curves', and 'Methodology Notes'; include a verification step to ensure summary stats match `data/processed/simulation_results.csv` by **computing mean power per condition and comparing to CSV rows** (FR-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `README.md` and `docs/`
- [ ] T044 Code cleanup and refactoring in `code/`
- [ ] T045 Performance optimization to ensure completion within 6 hours on 2 vCPUs (FR-008); parallelize SNR/Sparsity loops using `joblib.Parallel` with `n_jobs=2` and profile execution time
- [ ] T046 [P] Additional unit tests in `tests/unit/`
- [ ] T047 Run quickstart.md validation
- [ ] T048 Verify reproducibility by re-running pipeline with pinned seeds and comparing checksums
- [ ] T049 [P] Implement runtime profiling in `code/utils/profiler.py` to measure total execution time per phase and ensure the full pipeline completes within 6 hours (FR-008); add logging for slow steps to identify bottlenecks
- [ ] T050 [US3] Ensure sensitivity analysis in `code/analysis/comparators.py` explicitly iterates over a range of Alpha values and generates separate power curves for each (FR-006)

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
- [TDD-First] indicates tests define interface before implementation
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence