# Tasks: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-data-scaling-on/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create root project directories: `code/`, `data/`, `results/`, `logs/`
- [X] T001b [P] Create `code/simulation/`, `code/preprocessing/`, `code/analysis/`, `code/visualization/` subdirectories. **Deliverable**: Verify directories exist: `code/simulation`, `code/preprocessing`, `code/analysis`, `code/visualization`.
- [X] T001c [P] Create `data/raw/`, `data/scaled/`, `data/config/` subdirectories
- [X] T001d [P] Create `results/figures/` and `data/scaled/{standardized,minmax,robust}/` subdirectories
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (numpy, scipy, pandas, scikit-learn, statsmodels, matplotlib, seaborn)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management for `SimulationConfig` entity in `code/simulation/config.py`
- [X] T005a [P] Create `code/simulation/logger.py` with `setup_logger` function that returns a logger instance configured with `logging.INFO` and a specific format string `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
- [X] T005b [P] Configure log levels for `code/simulation/logger.py` to handle `DEBUG`, `INFO`, `WARNING`, `ERROR` with file rotation to `logs/simulation.log` using `RotatingFileHandler` with `maxBytes=10MB` and `backupCount=5`. **Deliverable**: Ensure logger explicitly logs the random seed and simulation batch ID on every batch start as required by Constitution Principle VI. The `setup_logger` function must accept `batch_id` as an argument to ensure deterministic logging.
- [X] T006 [P] Create base test fixtures and seed management in `code/tests/conftest.py` (independent of T005, using standard library logging for fixtures)
- [X] T007 Setup environment configuration for CPU-only constraints (disable GPU, set parallelism limits) in `code/utils/env.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulation Engine for Null and Alternative Hypotheses (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets with controlled distributional properties where ground truth is known.

**Independent Test**: Generate a dataset with null hypothesis (mean diff = 0) and verify mean difference < 0.01; generate alternative (mean diff = 1.0) and verify |mean_diff - 1.0| < 0.05.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for null hypothesis generation in `code/tests/unit/simulation/test_generator.py`
- [X] T009 [P] [US1] Contract test for alternative hypothesis generation in `code/tests/unit/simulation/test_generator.py`
- [X] T010 [P] [US1] Test for skewness/heteroscedasticity parameter accuracy in `code/tests/unit/simulation/test_generator.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `generate_synthetic_data` function in `code/simulation/generator.py` supporting normal, skewed, and heteroscedastic distributions
- [X] T012 [US1] Implement ground truth validation logic in `code/simulation/generator.py` that returns a boolean and logs assertion failures if `mean_diff >= 0.01` for null or `|mean_diff - 1.0| >= 0.05` for alternative. **Deliverable**: Function returns `(bool, str)` where bool indicates validity and str contains error message if invalid.
- [X] T013 [US1] Add logic to handle zero-variance edge cases in `code/simulation/generator.py`: Log `WARNING` with message "Skipping iteration: zero variance detected" if `std_dev < 1e-9 ` and skip the specific iteration. **Condition**: `if std_dev < 1e-9 `. **Log Level**: `WARNING`.
- [X] T014 [US1] Implement data persistence to `data/synthetic/` with metadata. **Deliverable**: Save each batch as `data/synthetic/batch_{batch_id}_{seed}.parquet`. Columns must include: `seed` (int, MUST be populated for every row), `config_json` (string, JSON serialized config using `json.dumps(config, sort_keys=True)`), `ground_truth_label` (string: 'null' or 'alternative'), and the generated data columns. **Constraint**: Must record the random seed used for generation as per Constitution Principle VI. **Requirement**: The `seed` column MUST be populated for every row in the Parquet file.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Scaling Application and Statistical Testing Pipeline (Priority:P2)

**Goal**: Apply scaling methods (Standardization, Min-Max, Robust) and run parametric tests (t-test, ANOVA, Chi-squared).

**Independent Test**: Apply Standardization to a fixed dataset, verify (Wikipedia: Standard normal table, https://en.wikipedia.org/wiki/Standard_normal_table), and confirm t-test p-value stability compared to unscaled data.

### Tests for User Story 2

- [X] T015 [P] [US2] Contract test for Standardization scaling properties (mean=0, std=1) in `code/tests/unit/preprocessing/test_scaling.py`
- [X] T016 [P] [US2] Contract test for Min-Max scaling properties (min=0, max=1) in `code/tests/unit/preprocessing/test_scaling.py`
- [X] T017 [P] [US2] Contract test for Robust scaling (median/IQR) and zero-IQR handling in `code/tests/unit/preprocessing/test_scaling.py`
- [X] T018 [P] [US2] Test for p-value invariance under linear scaling transformations in `code/tests/unit/analysis/test_tests.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `standardize_data` function in `code/preprocessing/scaling.py`
- [X] T020 [P] [US2] Implement `min_max_scale` function in `code/preprocessing/scaling.py`
- [X] T021 [P] [US2] Implement `robust_scale` function in `code/preprocessing/scaling.py` with explicit zero-IQR handling: Log `WARNING` and skip the iteration if IQR is zero. **Action**: Do not return a constant; skip iteration entirely.
- [X] T022 [US2] Implement `run_t_test` and `run_anova` in `code/analysis/tests.py`
- [X] T023 [US2] Implement `run_chi_squared` in `code/analysis/tests.py` with automatic binning logic using **Sturges' rule** for continuous variables. **Deliverable**: Function must explicitly implement (Wikidata Q[identifier], [identifier]). **Edge Case**: If Sturges' rule results in zero-width bins or bins with zero expected frequency, implement logic to merge adjacent bins until valid counts are achieved.
- [X] T024 [US2] Create pipeline wrapper in `code/analysis/tests.py` to apply scaling then test, returning `TestResult` entities

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregation and Visualization of Inferential Validity (Priority: P3)

**Goal**: Aggregate a sufficient number of iterations to calculate Type I error rates and Power., then visualize against nominal alpha.

**Independent Test**: Feed a set of pre-calculated p-values into aggregation logic and verify error rate calculation and CI generation.

### Tests for User Story 3

- [X] T025 [P] [US3] Contract test for empirical error rate calculation (count < alpha / total) in `code/tests/unit/analysis/test_metrics.py`
- [X] T026 [P] [US3] Contract test for confidence interval calculation. **Deliverable**: Implement CI calculation using normal approximation and verify against known binomial values for n=100, p=0.05 (expected range: 0.001 to 0.149 using Clopper-Pearson exact method).

### Implementation for User Story 3

- [X] T027 [US3] Implement simulation loop orchestration in `code/main.py` (or `code/simulation/orchestrator.py`) to run `int(os.environ.get('SIMULATION_ITERATIONS', 10000))` iterations per config. **Depends on**: Completion of Phase 3 (US1) and Phase 4 (US2) implementation. **Output**: Append each `TestResult` to `results/simulation_results.csv`. **CSV Schema**: `iteration_id` (int), `seed` (int, MUST be populated for every row), `scaling_method` (string), `test_type` (string: 't-test', 'anova', 'chi2'), `p_value` (float), `t_statistic` (float, null if not t-test), `f_statistic` (float, null if not anova), `chi2_statistic` (float, null if not chi2), `ground_truth_label` (string). **Termination**: Stop when `SIMULATION_ITERATIONS` rows are written per config. **Constraint**: The `seed` column MUST be populated for every row.
- [X] T028 [US3] Implement checkpointing mechanism in `code/main.py` to save partial results and **report summary** (number of completed iterations) if loop exceeds a **predefined time threshold**, enforcing a **hard stop**. **Deliverable**: Report must explicitly state count of completed iterations and save partial CSV. **Constraint**: Measure wall-clock time using `time.time()`; stop if runtime > 5.5 hours to ensure compliance with FR-007 (6-hour limit). Save summary as JSON.
- [X] T029 [US3] Implement `calculate_aggregate_metrics` in `code/analysis/metrics.py` to compute Type I error and Power
- [X] T030 [US3] Implement `generate_error_rate_plot` in `code/visualization/plots.py` showing empirical rate vs with 95% CI
- [X] T031a [US3] Implement One-Way ANOVA analysis (statsmodels) in `code/analysis/metrics.py` for **synthetic data**: Perform One-Way ANOVA on aggregated error rates with `scaling_method` as the independent variable and `empirical_error_rate` as the dependent variable. **Input**: Aggregate error rates calculated from `results/simulation_results.csv` (long format). **Output**: `results/anova_synthetic.csv` containing F-statistic and p-value. **Rationale**: Mixed-effects models are inappropriate for synthetic data where 'dataset' is not a random variable (see plan Complexity Tracking). Use `statsmodels.formula.api.anova_lm`.
- [X] T032 [US3] Generate summary report comparing deviations of each scaling method from nominal. **Deliverable**: Create `results/summary_report.md` containing a table comparing mean deviations, p-values from ANOVA/mixed-effects models, and explicit compliance check against the ±0.005 tolerance (SC-004).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Real-World Dataset Validation (Priority: P4)

**Goal**: Ingest public datasets (UCI/OpenML) and validate simulation findings on real data.

**Independent Test**: Run pipeline on Iris dataset, verify scaling, testing, and report generation without crashing.

### Tests for User Story 4

- [X] T033 [P] [US4] Contract test for dataset ingestion (handle missing values, output clean DF) in `code/tests/unit/preprocessing/test_ingestion.py`
- [X] T034a [P] [US4] Integration test for full real-world pipeline on Iris dataset in `code/tests/integration/test_real_world.py`

### Implementation for User Story 4

- [X] T034a [US4] **Create Dataset Configuration**: Generate `data/config/datasets.yaml` containing the list of verified datasets (IDs: `uciml/iris`, `uciml/wine`, `uciml/breast-cancer-wisconsin`, `uciml/heart-statlog`, `uciml/ionosphere`, `uciml/credit-a`, `uciml/credit-g`, `uciml/hepatitis`, `uciml/horse-colic`, `openml/d/2`, `openml/d/3`, `openml/d/11`). Include metadata (source, expected size) for each. If any dataset is unavailable, the ingestion loop must log a warning and skip it (T034b) to ensure robustness; do not fall back to synthetic data.
- [X] T035 [US4] Implement `download_dataset` function in `code/preprocessing/ingestion.py` using specific verified URLs or `datasets.load_dataset` for the datasets listed in `data/config/datasets.yaml`. **Deliverable**: Function must read dataset list from `data/config/datasets.yaml`.
- [X] T036 [US4] Implement data cleaning and preprocessing (imputation/removal) in `code/preprocessing/ingestion.py`
- [X] T037 [US4] Create `RealWorldDataset` entity and metadata storage in `code/preprocessing/ingestion.py`
- [X] T034b [US4] **Orchestrate Real-World Dataset Ingestion**: Implement loop in `code/main.py` to iterate over the configuration list in `data/config/datasets.yaml`. Track metadata for each source (source, size, missing_rate, status) in `data/metadata/manifest.json`. **Logic**: If a dataset is unavailable, log a warning and skip it; do NOT fall back to synthetic data. **Depends on**: T034a, T035, T036. **Config**: Read dataset list from `data/config/datasets.yaml`. **JSON Schema**: `manifest.json` entries must have keys: `source` (string), `size` (int), `missing_rate` (float), `status` (string: 'success' or 'skipped').
- [X] T038 [US4] Reuse scaling and testing pipeline (US2) on real data in `code/main.py`. **Depends on**: Completion of Phase 4 (US2) implementation (T019-T024) and Phase 6 setup (T035-T036).
- [X] T039 [US4] Implement comparison report generation (p-values, effect sizes before/after scaling) in `code/analysis/metrics.py`
- [X] T031b [US4] [US4] Implement mixed-effects model analysis (statsmodels) in `code/analysis/metrics.py` for **real-world data**: Fit mixed-effects model with `scaling_method` as fixed effect, `dataset_id` as random effect. Dependent variable: `deviation` (calculated as `abs(empirical_rate - 0.05)`). **Input**: Aggregated error rates from `results/real_world_results.csv`. **Formula**: `deviation ~ scaling_method + (1|dataset_id)`. **Output**: `results/mixed_effects_summary.csv`. **Deliverable**: Function must return model summary and save to CSV. **Depends on**: T038.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` and `quickstart.md`. **Deliverable**: Add a section "Running the Simulation" to `quickstart.md` with the exact command `python code/main.py --a sufficient number of iterations` for quick validation.
- [X] T041 Code cleanup and refactoring of `code/simulation/generator.py` for performance. **Target**: Reduce simulation loop time significantly. or ensure < 6h runtime. **Actions**: Vectorize loops with NumPy, profile with cProfile. **Deliverable**: Refactored code with benchmark results showing runtime improvement.
- [X] T042a [P] Vectorize `generate_synthetic_data` in `code/simulation/generator.py` using NumPy array operations instead of Python loops. **Deliverable**: x speedup in generation step.
- [X] T042b [P] Parallelize simulation loop in `code/main.py` using `multiprocessing` (limited to a small number of workers for CPU constraint). **Deliverable**: Linear speedup up to 2 cores.
- [X] T043 [P] Additional unit tests for edge cases. **Deliverable**: Implement `test_generator_handles_zero_variance`, `test_scaling_handles_infinite_values`, and `test_chi_squared_binning_edge_cases` in `code/tests/unit/`.
- [X] T044 [P] Run quickstart.md validation. **Deliverable**: Execute `python code/main.py --iterations 100`; verify exit code 0, runtime < 30s, and `results/simulation_results.csv` has > 50 rows (use `wc -l` or Python one-liner). **Constraint**: Must be run in a clean environment (simulating fresh GitHub Actions runner) and verify reproducibility by re-running the command and comparing checksums of `results/simulation_results.csv`.
- [X] T045 [P] Verify all artifacts. **Deliverable**: Check that `results/figures/error_rate_plot.png` exists and is > 10KB; verify `results/summary_report.md` exists and contains the comparison table.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generator for testing
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 & US2 for data and tests
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US2 for scaling/testing logic

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US4 can start in parallel (if team capacity allows)
- US3 depends on results from US1/US2, so it should start after those are stable
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all scaling implementations in parallel (different files/functions):
Task: "Implement standardize_data function in code/preprocessing/scaling.py"
Task: "Implement min_max_scale function in code/preprocessing/scaling.py"
Task: "Implement robust_scale function in code/preprocessing/scaling.py"

# Launch all statistical tests in parallel:
Task: "Implement run_t_test and run_anova in code/analysis/tests.py"
Task: "Implement run_chi_squared in code/analysis/tests.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generator)
 - Developer B: User Story 2 (Scaling & Tests)
 - Developer C: User Story 4 (Real World Data)
3. Once A & B are stable, Developer D (or A) works on User Story 3 (Aggregation & Viz)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, cross-story dependencies that break independence
- **CRITICAL**: All simulation tasks must run on CPU-only CI with a minimal core allocation and standard memory limits. Do not use GPU-specific libraries or 8-bit quantization.
- **CRITICAL**: Do not fabricate data. Use real datasets for US4 and synthetic data with known ground truth for US1.
- **CRITICAL**: Dataset download tasks (T035) MUST use explicit URLs or `datasets.load_dataset` calls for the specific IDs listed; "download from UCI" without a URL is forbidden.
- **CRITICAL**: The simulation loop (T027) must run BEFORE the aggregation tasks (T029) to ensure data flow correctness.
- **CRITICAL**: Mixed-effects models (T031b) are required for real-world data; ANOVA is required for synthetic data (T031a) per plan Complexity Tracking.
- **CRITICAL**: T034a (datasets.yaml) must be created before T035 and T034b to ensure configuration availability.
- **CRITICAL**: T014 must be completed before T027 to ensure that the simulation loop can persist intermediate results to disk for checkpointing and reproducibility.
- **CRITICAL**: T031a and T031b must be implemented only after T027 and T038 have generated the necessary result files (`results/simulation_results.csv` and `results/real_world_results.csv`).
- **CRITICAL**: T034b must explicitly handle the case where a dataset from `data/config/datasets.yaml` is unavailable by logging a warning and skipping, NOT by falling back to synthetic data generation.
- **CRITICAL**: T040 must include a section in `quickstart.md` that explicitly lists the exact command to run the full simulation loop with a small subset (e.g., 100 iterations) for quick validation before the full [deferred]+ run.