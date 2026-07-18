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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data hygiene, configuration, and streaming adaptations.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management for `SimulationConfig` entity in `code/simulation/config.py`
- [X] T005a [P] Create `code/simulation/logger.py` with `setup_logger` function that returns a logger instance configured with `logging.INFO` and a specific format string `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
- [X] T005b [P] Configure log levels for `code/simulation/logger.py` to handle `DEBUG`, `INFO`, `WARNING`, `ERROR` with file rotation to `logs/simulation.log` using `RotatingFileHandler` with `maxBytes=10MB` and `backupCount=5`. **Deliverable**: Ensure logger explicitly logs the random seed and simulation batch ID on every batch start as required by Constitution Principle VI. The `setup_logger` function must accept `batch_id` as an argument to ensure deterministic logging.
- [X] T006 [P] Create base test fixtures and seed management in `code/tests/conftest.py` (independent of T005, using standard library logging for fixtures)
- [X] T007 Setup environment configuration for CPU-only constraints (disable GPU, set parallelism limits) in `code/utils/env.py`
- [ ] T024 [US4] **Implement Strict Streaming Loader**: Refactor `code/preprocessing/ingestion.py` to use `datasets.load_dataset(..., streaming=True)` for large public datasets. **Requirement**: Do not load the full dataset into memory. **Logic**: Iterate over the streaming object in chunks to compute necessary statistics (mean, variance) or to sample a fixed number of rows. **Constraint**: If a full dataset cannot be processed within the specified time limit, the code must explicitly sample a well-defined subset. (e.g., `itertools.islice` the first N rows) and log the sample size and limitation. **Prohibition**: Do NOT use `generate_synthetic_data` as a fallback if streaming fails. **CRITICAL PREREQUISITE**: This task MUST be completed before T035 and T038.
- [ ] T025 [US4] **Enforce Fail-Loudly Data Fetch**: Remove any `try/except` blocks in `code/preprocessing/ingestion.py` that catch download errors and substitute synthetic data. **Action**: If `datasets.load_dataset` or a URL fetch fails, the function must raise a `RuntimeError` with a clear message identifying the missing source. **Rationale**: Prevents silent fabrication where real data fails and the pipeline continues with fake data. **CRITICAL PREREQUISITE**: This task MUST be completed before T035 and T038.
- [ ] T026 [US4] Adapt `code/analysis/tests.py` to accept chunked/streamed data via a `data_stream` or `sample_size` argument. Implement a 'sample-and-test' strategy: stream N=5000 rows, then run the standard test.
- [ ] T027 [US4] **Create Verified Dataset Configuration**: Generate `data/config/datasets.yaml` containing the list of verified datasets (IDs from `research.md`). **Validation**: Programmatically verify that all IDs are unique and accessible before proceeding. If any dataset is unavailable, log a warning and skip it during ingestion.
- [ ] T028 [US4] **Add Verification Task for Real Data**: Create a task `code/tests/unit/preprocessing/test_real_data_integrity.py` that asserts the loaded data is not synthetic by checking for specific statistical properties or source ID verification.

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

- [ ] T011 [US1] Implement `generate_synthetic_data` function in `code/simulation/generator.py` that accepts arbitrary distributional moments: `mean`, `variance`, `skewness`, `kurtosis` as explicit float arguments. Map variance to the scale parameter of scipy.stats.norm (for normal distributions). If skewness=0 and kurtosis=3, default to Normal distribution. **Deliverable**: Function signature `generate_synthetic_data(mean, var, skew, kurt, n, seed)`.
- [X] T012 [US1] Implement ground truth validation logic in `code/simulation/generator.py` that returns a boolean and logs assertion failures if `mean_diff >= 0.01` for null or `|mean_diff - 1.0| >= 0.05` for alternative. **Deliverable**: Function returns `(bool, str)` where bool indicates validity and str contains error message if invalid.
- [X] T013 [US1] Add logic to handle zero-variance edge cases in `code/simulation/generator.py`: Log `WARNING` with message "Skipping iteration: zero variance detected" if `std_dev < 1e-9 ` and skip the specific iteration. **Condition**: `if std_dev < 1e-9 `. **Log Level**: `WARNING`.
- [X] T014 [US1] Implement data persistence to `data/synthetic/` with metadata. **Deliverable**: Save each batch as `data/synthetic/batch_{batch_id}_{seed}.parquet`. Columns must include: `seed` (int), `config_json` (string, JSON serialized config), `ground_truth_label` (string: 'null' or 'alternative'), and the generated data columns.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Scaling Application and Statistical Testing Pipeline (Priority:P2)

**Goal**: Apply scaling methods (Standardization, Min-Max, Robust) and run parametric tests (t-test, ANOVA, Chi-squared).

**Independent Test**: Apply Standardization to a fixed dataset, verify (Wikipedia: Standard normal table), and confirm t-test p-value stability compared to unscaled data.

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
- [ ] T023 [US2] Implement `run_chi_squared` in `code/analysis/tests.py` with binning logic based on theoretical quantiles derived from the config's ground-truth parameters (mean, variance). If a bin has an expected count < 5, merge with the left neighbor; if the left neighbor is empty or < 5, merge with the right neighbor. If both fail, log "Bin merge failed" and skip the iteration.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregation and Visualization of Inferential Validity (Priority: P3)

**Goal**: Aggregate a sufficient number of iterations to calculate Type I error rates and Power., then visualize against nominal alpha.

**Independent Test**: Feed a set of pre-calculated p-values into aggregation logic and verify that the calculated empirical error rate matches the proportion of p-values < 0.05, and that the confidence interval calculation runs successfully.

### Tests for User Story 3

- [X] T025 [P] [US3] Contract test for empirical error rate calculation (count < alpha / total) in `code/tests/unit/analysis/test_metrics.py`
- [ ] T026a [US3] **Production CI Implementation**: Implement `calculate_confidence_interval` in `code/analysis/metrics.py` using the Clopper-Pearson exact method.
- [ ] T026b [US3] **Verification Test**: Implement a test in `code/tests/unit/analysis/test_metrics.py` that verifies the Clopper-Pearson implementation against known binomial values for n=100, p=0.05 (expected range: a low-order magnitude to a small threshold).

### Implementation for User Story 3

- [X] T027a [US3] Validate simulation iteration threshold.
- [ ] T027b [US3] **Global Budget Enforcer**: Implement a wrapper in `code/main.py` that measures total wall-clock time for the simulation loop and terminates after 6 hours.
- [ ] T028 [US3] Implement simulation loop orchestration in `code/main.py`. Iterate over all combinations of distribution types, scaling methods, and test types.. Persist results to `results/simulation_results.csv`.
- [X] T029 [US3] Implement `calculate_aggregate_metrics` in `code/analysis/metrics.py` to compute Type I error and Power
- [X] T030 [US3] Implement `generate_error_rate_plot` in `code/visualization/plots.py` showing empirical rate vs with 95% CI (using Clopper-Pearson).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Real-World Dataset Validation (Priority: P4)

**Goal**: Ingest public datasets (UCI/OpenML) and validate simulation findings on real data.

**Independent Test**: Run pipeline on Iris dataset, verify scaling, testing, and report generation without crashing.

### Tests for User Story 4

- [X] T033 [P] [US4] Contract test for dataset ingestion (handle missing values, output clean DF) in `code/tests/unit/preprocessing/test_ingestion.py`
- [X] T034a [P] [US4] Integration test for full real-world pipeline on Iris dataset in `code/tests/integration/test_real_world.py`

### Implementation for User Story 4

- [ ] T035 [US4] Implement `download_dataset` function in `code/preprocessing/ingestion.py` using specific verified URLs or `datasets.load_dataset`.
- [ ] T036 [US4] Implement data cleaning and preprocessing (imputation/removal) in `code/preprocessing/ingestion.py`
- [X] T037 [US4] Create `RealWorldDataset` entity and metadata storage in `code/preprocessing/ingestion.py`
- [ ] T038 [US4] Reuse scaling and testing pipeline on real data. Apply streaming or materialize a fixed sample size (N=5000) if streaming is incompatible.
- [X] T039 [US4] Implement comparison report generation in `code/analysis/metrics.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` and `quickstart.md`.
- [X] T041 Code cleanup and refactoring of `code/simulation/generator.py` for performance.
- [X] T042a [P] Vectorize `generate_synthetic_data` in `code/simulation/generator.py` using NumPy array operations instead of Python loops.
- [X] T042b [P] Parallelize simulation loop in `code/main.py` using `multiprocessing`.
- [X] T043 [P] Additional unit tests for edge cases.
- [X] T044 [P] Run quickstart.md validation.

---

## Phase 8: Review Resolution & Data Integrity (Revision Pass)

**Purpose**: Improvements to ensure data integrity and compliance with specific review concerns.

### Implementation for Review Resolution

- [ ] T046 [US4] Implement Streaming Loaders
- [ ] T047 [US4] Enforce Fail-Loudly Data Fetch
- [ ] T048 [US4] Update Dataset Configuration (using verified IDs from research.md).
- [ ] T034b [US4] Validate the configuration in `data/config/datasets.yaml` created by T027.
- [ ] T049 [US4] Add Verification Task for Real Data
- [ ] T050 [US4] Refine Real-World Pipeline Logic
