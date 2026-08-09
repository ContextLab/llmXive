# Tasks: Evaluating Robustness of Statistical Methods to Non-Independence

**Input**: Design documents from `/specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence/`
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

- [ ] T001 Create project structure by explicitly creating directories: `src/`, `src/data/`, `src/synthesis/`, `src/analysis/`, `src/viz/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/`, `state/`. **Output**: Generate `state/structure_manifest.json` listing all created paths to verify completion.
- [X] T002 Initialize Python project with pinned `requirements.txt` (numpy, pandas, scipy, statsmodels, arch, yfinance, requests, pyyaml, matplotlib, seaborn, xarray)
- [X] T003 [P] Create `ruff.toml` configuration file with strict linting rules (E, F, W, I, N, C, UP) and `black` integration.
- [X] T004 [P] Create `pytest.ini` configuration file with test paths, markers, and verbosity settings.
- [X] T005 [P] Implement `src/utils/config.py` for random seed management and global constants. **Dependency**: Required by T007 and T008.
- [X] T006 [P] Implement `src/utils/logging.py` with structured logging for warnings and errors, including log file rotation. **Dependency**: Required by T007 and T008.
- [X] T007 Create base data schemas in `src/data/schemas.py` using Pydantic: `TimeSeries`, `SyntheticData`, `TestResult`, `ErrorRateSummary` with all required fields defined in the spec.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Implement `src/data/ingestion.py` with strict URL validation and checksumming logic (FR-001)
- [X] T009 Implement `src/data/preprocessing.py` skeleton with ADF logic and explicit placeholder for **linear regression residuals** (NO DFA) for detrending (FR-002). **Constraint**: Spec FR-002 mandates linear regression residuals for stationary series; ignore Plan's mention of DFA.
- [X] T010 [P] Implement `src/data/metrics.py` utility functions (ACF, Hurst, Spectral Density) to be called by T010a and T010b. **Note**: This task provides the functions, not the execution flow.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest diverse public time series, handle missing values, ensure stationarity (ADF/differencing or detrending), and compute initial metrics.

**Independent Test**: Can be fully tested by running the data ingestion and preprocessing module against a fixed set of public URLs and verifying that the output is a clean, stationary (or differenced), detrended time series with no missing values and a documented preprocessing path.

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for `src/data/ingestion.py` verifying checksums and error on missing files in `tests/unit/test_ingestion.py` <!-- ATOMIZE: requested -->
- [X] T012 [P] [US1] Unit test for `src/data/preprocessing.py` verifying ADF logic and differencing loops in `tests/unit/test_preprocessing.py`
- [X] T013 [P] [US1] Integration test for full NOAA/Yahoo/UK Grid pipeline in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/data/ingestion.py` to download multiple distinct public datasets from authorized sources.:
 1. NOAA Global Summary (URL: `)
 2. Yahoo Finance (yfinance package for AAPL/SPY)
 3. UK National Grid Load (URL: `https://www.nationalgrideso.com/document/174276/download`)
 4. NOAA Station USW00014895 (URL: `)
 5. NOAA Station USW00014833 (URL: `)
 **Constraint**: Must fail loudly on download error; no synthetic fallbacks.
- [X] T015 [US1] Implement linear interpolation for missing values in `src/data/preprocessing.py` (FR-002).
- [X] T016 [US1] Implement ADF test logic in `src/data/preprocessing.py`. If p < 0.05, apply differencing until stationarity. If p ≥ 0.05, **detrend using linear regression residuals** (FR-002). **Constraint**: Explicitly exclude DFA for detrending; use linear regression residuals only.
- [ ] T018a [US1] Add logic to resample datasets to a **consistent frequency (e.g., hourly, daily) based on the dataset's native resolution** before stationarity testing (US1-AC3). **Rule**: Resample to hourly if native frequency < 1h, else daily. **Output**: Write to `data/processed/resampled_{source}.csv`.
- [ ] T010a [US1] Compute ACF, Hurst, and Spectral Density **peak ratio** for **REAL series only** (post-preprocessing) and store in `data/processed/metrics_real.json`. **Input**: Reads from `data/processed/resampled_*.csv` after T018a. **Dependency**: T018a. **Output Schema**: JSON list of objects with keys: `source`, `length`, `hurst`, `acf_max_lag1`, `acf_max_lag20`, `spectral_peak_ratio`. **Constraint**: Must run BEFORE T019a to ensure metrics exist before shuffling.
- [X] T019a [US1] Implement shuffling (permutation) logic in `src/data/preprocessing.py` to generate and store **[deferred] shuffled versions** for **every real time series** to create a null distribution (FR-003, Constitution Principle VII). **Constraint**: Must run after T010a; output to `data/processed/null_distributions/real/`.
- [ ] T020 [US1] Add edge case handling: skip datasets < 25 points with a warning log (Edge Case 1). **Log Format**: `WARNING: Skipping dataset {id}: length < 25`.
- [ ] T021 [US1] Add edge case handling: detect unit roots that cannot be detrended and log the differencing count (Edge Case 2). **Log Format**: `WARNING: Dataset {id} required {count} differences to achieve stationarity`.
- [ ] T022 [US1] Add edge case handling: fallback to variance-based metric if spectral density **peak ratio** calculation fails due to numerical instability (Edge Case 3). **Log Format**: `WARNING: Spectral density failed for {id}, using variance-based fallback`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Ground-Truth Generation and Autocorrelation Quantification (Priority: P2)

**Goal**: Generate synthetic fGn/ARFIMA data with known H and mean=0, compute metrics, and create shuffled null distributions.

**Independent Test**: Can be fully tested by generating a synthetic fGn series with H=0.8 and mean=0, verifying that the generated series has H ≈ 0.8 (within 0.05) and mean ≈ 0 (within 0.01), and confirming that the shuffled versions exhibit an average ACF lag-1 statistically indistinguishable from zero.

### Tests for User Story 2

- [X] T023 [P] [US2] Unit test for `src/synthesis/generators.py` verifying H=0.5, 0.7, 0.8, 0.9 generation accuracy in `tests/unit/test_synthesis.py` <!-- ATOMIZE: requested -->
- [X] T024 [P] [US2] Unit test for shuffling logic ensuring ACF lag-1 is zero in `tests/unit/test_synthesis.py`
- [X] T025 [P] [US2] Baseline validity test: Run [deferred] trials on H=0.5 data and verify rejection rate is within 95% Clopper-Pearson CI of 0.05 in `tests/integration/test_baseline_validity.py`

### Implementation for User Story 2

- [X] T026 [US2] Implement `src/synthesis/generators.py` to generate fractional Gaussian noise (fGn) or ARFIMA processes with H ∈ {, 0.7, 0.8, 0.9} and mean=0 (FR-007).
- [ ] T027 [US2] Implement logic to generate synthetic series with varying lengths for the N-variation grid: **{100, 500, 1000, 5000, 10000}** (Plan). **Output**: Write to `data/processed/synthetic_grid.csv` with columns: `hurst`, `length`, `file_path`.
- [ ] T010b [US2] Compute ACF, Hurst, and Spectral Density **peak ratio** for **SYNTHETIC series only** and store in `data/processed/metrics_synthetic.json`. **Input**: Reads from `data/processed/` after T026. **Dependency**: T026. **Output Schema**: JSON list of objects with keys: `source`, `length`, `hurst`, `acf_max_lag1`, `acf_max_lag20`, `spectral_peak_ratio`. **Constraint**: Must run after T026.
- [ ] T019b [US2] Implement shuffling logic in `src/synthesis/generators.py` to generate and store **[deferred] shuffled versions** for **every synthetic series** to create a null distribution (FR-003, Constitution Principle VII). **Constraint**: Must run after T010b; output to `data/processed/null_distributions/synthetic/`.
- [ ] T029 [US2] Implement `src/synthesis/validation.py` to run the **[deferred]-trial** baseline check on H=0.5 data **before proceeding** to Hurst analysis (FR-008, US2-AC7). **GATE**: This task must write `data/results/baseline_status.json` with a "PASS" status if the rejection rate is within the Clopper-Pearson CI. **Output Schema**: JSON with keys: `status`, `rejection_rate`, `ci_lower`, `ci_upper`. Phase 5 tasks (T037a) MUST NOT start until this file exists with "PASS".
- [ ] T030 [US2] [P] Read metrics from T010b output for synthetic series; verify ACF, Hurst, and spectral density **peak ratio** are computed (FR-002).
- [ ] T031 [US2] Implement calculation of theoretical VIF and N_eff for synthetic series in `src/synthesis/generators.py` (FR-007).
- [ ] T032 [US2] Add logic to verify generated series mean is within 0.01 of 0 and H is within 0.05 of target (US2-AC1..4).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 3 - Hypothesis Testing (Priority: P3)

**Goal**: Apply t-tests/F-tests and calculate Type I error rates.

**Independent Test**: Can be fully tested by running the analysis on synthetic data with H=0.5 (independent-like) and verifying the error rate is within the [deferred]-trial Clopper-Pearson binomial confidence interval of 0.05.

### Tests for User Story 3

- [ ] T033 [P] [US3] Unit test for `src/analysis/hypothesis_tests.py` verifying one-sample t-test and F-test logic in `tests/unit/test_hypothesis.py`
- [ ] T034 [P] [US3] Unit test for `src/analysis/regression.py` verifying VIF and N_eff calculation in `tests/unit/test_regression.py`
- [ ] T035 [P] [US3] Integration test for full Monte Carlo loop (multiple trials) and regression output in `tests/integration/test_pipeline.py`

### Implementation for User Story 3 (Tests)

- [ ] T036 [US3] Implement `src/analysis/hypothesis_tests.py` to apply one-sample t-tests and F-tests to synthetic series (mean=0) (FR-004). **Constraint**: Explicitly exclude two-sample t-test.
- [ ] T037 [US3] Implement Monte Carlo loop orchestration to run a sufficient number of trials per configuration to ensure statistical robustness (H, N) and calculate observed rejection rate at α=0.05 (US3-AC1). **Dependency**: Requires T036. **Dependency**: Requires T029 (Baseline Gate) to pass.
- [ ] T038 [US3] Implement logic to compare observed test statistics against the null distribution from shuffled versions (generated in T019a/T019b) to isolate inflation (US3-AC5).

**Checkpoint**: Hypothesis testing logic is ready; Analysis phase blocked by T029 Gate.

---

## Phase 5b: User Story 3 - Regression & Analysis (Priority: P3)

**Goal**: Perform regression analysis and visualizations.

**Dependency**: This phase is BLOCKED until T029 (Baseline Gate) passes.

### Implementation for User Story 3 (Analysis)

- [ ] T037b [US3] Implement explicit feature filtering logic in `src/analysis/regression.py` to **exclude** Max_ACF_Lag1 and spectral density metrics from the input features. **Output**: Write filtered feature list to `data/results/filtered_features.json`.
- [ ] T037a [US3] Implement **Linear Regression** model in `src/analysis/regression.py` to regress error rate vs. Hurst exponent (synthetic) or estimated Hurst (real). **Input**: Read error rates from `data/results/error_rates.csv` and filtered features from `data/results/filtered_features.json`. **Dependency**: Requires T029 (Gate) and T037b (Filtering). **Constraint**: Must wait for T029 (Gate) and T037b (Filtering). **Note**: Spec FR-005 mandates Linear Regression. **Mandated by FR-005: Use Linear Regression (not GLM or non-linear)**. **Output**: Save regression coefficients and VIF/N_eff to `data/results/regression_model.json`. **Output Schema**: JSON with keys: `slope`, `intercept`, `p_value`, `vif`, `n_eff`, `r_squared`.
- [ ] T037c [US3] Implement calculation of Variance Inflation Factor (VIF) and Effective Sample Size (N_eff) in the regression model (FR-005).
- [ ] T039 [US3] Implement visualization logic in `src/viz/plots.py` for ACF plots, scatter plots (rejection rate vs. H), and QQ-plots (FR-006).
- [ ] T039b [US3] Implement visualization logic in `src/viz/plots.py` specifically for **VIF curves** (FR-006).
- [ ] T040 [US3] Implement performance validation and runtime enforcement: Measure and log total pipeline runtime to ensure it fits within the GitHub Actions time limit (SC-004). **Logic**: If runtime > 6h, exit with code 1. **Output**: Write results to `data/results/performance_validation.json`. **Output Schema**: JSON with keys: `total_runtime_seconds`, `peak_memory_mb`, `dataset_count`, `status`.
- [ ] T041 [US3] Implement output of results to `data/results/final_summary.json` including regression slopes, p-values, VIF, N_eff, and error rates. **Schema**: Must be a single JSON file with defined keys for all metrics (US3-AC2, US3-AC3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates: Generate `quickstart.md` and update `README.md` with pipeline usage instructions
- [ ] T043 Code cleanup and refactoring for memory efficiency (ensure < 7 GB RAM usage)
- [ ] T044 Performance optimization: Vectorize Monte Carlo loops where possible to meet 6h runtime goal
- [ ] T045 [P] Run full contract test suite in `tests/contract/` to verify schema compliance
- [ ] T046 Security hardening: Verify no API keys are hardcoded; ensure `.env` usage for any secrets
- [ ] T047 Run quickstart.md validation to ensure end-to-end reproducibility

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Produces the cleaned, stationary data required by US3.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Generates synthetic ground truth and null distributions required for US3 validation.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on outputs from US1 (real data metrics + real nulls from T019a) and US2 (synthetic data + nulls from T019b) to perform regression and comparison. **GATE**: T037a requires T029 success (baseline_status.json).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Schemas before logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for ingestion in tests/unit/test_ingestion.py"
Task: "Unit test for preprocessing in tests/unit/test_preprocessing.py"

# Launch all implementation tasks for US1 (sequential due to data flow):
Task: "Implement ingestion" -> Task: "Implement preprocessing" -> Task: "Resample (T018a)" -> Task: "Compute Metrics (T010a)" -> Task: "Generate real nulls (T019a)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Preprocessing) including T010a (metrics) and T019a (nulls).
4. **STOP and VALIDATE**: Verify raw data is ingested, cleaned, stationary, metrics computed, and nulls generated.
5. Deploy/demo if ready (as a data pipeline).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (synthetic generation) → Deploy/Demo
4. Add User Story 3 → Test independently (analysis) → Deploy/Demo
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Real Data Pipeline + T019a)
 - Developer B: User Story 2 (Synthetic Generation & T019b)
 - Developer C: User Story 3 (Analysis & Regression)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Constraint**: All data loaders must fail loudly; no synthetic fallbacks allowed. Real data must be streamed or sampled explicitly if too large.
- **Critical Compute Constraint**: The full pipeline must complete within 6 hours on a CPU-only runner. Optimize loops and vectorize where possible.
- **Critical Metric Constraint**: T010a and T010b must compute "spectral density peak ratio" explicitly, not just density.
- **Critical Architecture Constraint**: T037b explicitly filters forbidden metrics before T037a regression.
- **Critical Gate Constraint**: T029 must pass before T037a starts.
- **Plan Note**: The Plan.md 'Technical Context' and 'Fr/Sc Coverage Matrix' contain contradictions (DFA vs Linear Regression, GLM vs Linear Regression) that conflict with Spec FR-002 and FR-005. The **Spec governs**; tasks implement the Spec (Linear Regression residuals, Linear Regression model).