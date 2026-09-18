---
description: "Task list template for feature implementation"
---

# Tasks: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

**Input**: Design documents from `/specs/001-detecting-distribution-shift/`
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

- [X] T001 [P] Create project structure: `mkdir -p data/raw data/processed code tests code/contracts`
- [X] T002 [P] Create `requirements.txt` at root with: `numpy, scipy, pandas, scikit-learn, matplotlib, seaborn, pyyaml, pytest, pydantic`
- [X] T003 [P] Create `.flake8` and `pyproject.toml` with black/flake8 settings (max-line-length=88, exclude=venv)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.
**⚠️ CRITICAL**: These tasks MUST complete before Phase 3 begins. No user story work can begin until this phase is complete.

- [X] T004 Create `code/config.yaml` with keys: `seed: 42`, `permutations: 1000`, `window_size: 12`, `stride: 1`, `alpha: 0.01`, `min_permutations: 100`, `time_budget_minutes: 30`. **Status**: Implemented. Validates all config keys and types.
- [X] T005 [P] Create `contracts/config.schema.yaml` and implement validation in `code/main.py` using `pydantic`. **MUST** explicitly define the schema keys: `seed` (int), `permutations` (int), `window_size` (int), `stride` (int), `alpha` (float), `min_permutations` (int), `time_budget_minutes` (int). **Do NOT** mark as implemented until the schema file exists and `code/main.py` validates against it. (FR-009, Plan.md)
- [X] T006 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for data integrity. **Status**: Implemented. Defines schema for FluView and Ground Truth datasets.
- [X] T007 [P] Setup logging infrastructure in `code/__init__.py` to record runtime params and seeds (FR-009)
- [X] T008 [P] Implement synthetic data generator in `code/synthetic_data.py` for unit tests ONLY. MUST generate data with: (a) missing weeks (NaNs), (b) constant segments (zero variance), and (c) outliers. **STRICTLY FOR UNIT TESTS ONLY**. **MUST NOT** be used for final report; reference E-NO-DATA fallback. (FR-001, Constitution Principle VI)
- [ ] T012a [P] [US1] Implement `code/download_data.py` to fetch CDC FluView ILI CSV directly from the canonical CDC source: `. Save to `data/raw/fluview_ili.csv`. **MUST** verify file extension is `.csv` and content is tabular. If the URL returns 404/500, raise `E-NO-DATA`. **MUST NOT** use third-party mirrors. (FR-001, Constitution Principle VI)
- [ ] T012b [US1] Implement `code/download_data.py` (or separate function) to fetch CDC Virological/Hospitalization ground truth directly from the canonical CDC source: `. Save to `data/raw/ground_truth_events.csv` with columns `start_week, end_week, event_name`. **MUST** define the URL as a constant in the script and verify it is reachable (HTTP 200) before fetching. **MUST NOT** allow a fallback to a local file provided by the user. If the fetch fails or returns 404/500, raise `E-NO-DATA` exception. (FR-006, Constitution Principle VI)
- [ ] T013 [US1] Implement `code/preprocess.py` to handle missing weeks (remove), log-transform, and standardize (FR-002). **MUST** log the count of missing weeks removed to `data/processed/preprocessing_log.json` for auditability. **Blocking**: T012a. (FR-002)
- [ ] T013a [US1] Implement `code/preprocess.py` (or separate function) to calculate `N` (total number of consecutive window pairs) from the preprocessed series length. Write `N` to `data/processed/mmd_config.json` under the key `total_window_pairs`. **MUST** enforce strict ordering: T013 -> T013a -> T014. (FR-004, FR-003)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Automated shift detection for public‑health analysts (Priority: P1) 🎯 MVP

**Goal**: Run a reproducible pipeline that flags weeks where the ILI distribution has changed using MMD, producing `flags.csv` and `report.pdf`.

**Independent Test**: Execute the full pipeline on the FluView dataset and verify that a CSV of flagged weeks is produced together with a summary report containing the required metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Execution depends on code existing.**
> **Prerequisite**: T008 (synthetic data generator) must be complete.

- [X] T010 [P] [US1] Write unit test `tests/unit/test_mmd.py` with function `test_mmd_stat_correctness` using synthetic data from T008 to verify MMD logic.
- [X] T014 [US1] Implement `code/mmd_detector.py` with Gaussian-kernel MMD, multi-week windows, and dynamic permutation count. **Internal Logic**:
 1. **Pre-calculation**: Read `total_window_pairs` (N) from `data/processed/mmd_config.json` (generated by T013a).
 2. **Config Write**: Write `permutations`, `alpha`, and `threshold` (a small significance level divided by N) to `data/processed/mmd_config.json`. **Note**: The threshold is fixed based on `N` and does not change if permutations are reduced.
 3. **Runtime Monitor**: If `elapsed_time > global_time_budget - buffer`, reduce `permutations` in the in-memory config (e.g., `while permutations > min_permutations: permutations //= 2`), log "Permutations reduced to X", and re-calculate the MMD statistic for the current window. **MUST** enforce `min_permutations=100`.
 4. **Threshold Application**: Use the **pre-calculated** threshold (0.01/N) from the config to flag results.
 5. **Output**: Write the actual number of permutations used, the calculated `N`, and the `flags.csv` file (listing weeks with p < threshold) to `data/processed/`. **MUST** log the reduced permutation count and the final p-value threshold to `data/processed/mmd_config.json` and stdout for reproducibility. **Dependency**: T013a, T013. (FR-003, FR-004, FR-008, FR-009)
- [X] T016 [US1] Implement `code/evaluate.py` to load `data/raw/ground_truth_events.csv`, verify source independence (URL whitelist check), and **implement the parsing logic for the "±2-week tolerance window" described in FR-006**. **Logic**: Parse ISO week strings from the CSV, convert to integer week IDs, and match detected weeks within ±2 weeks. **Edge Case Handling**: If `ground_truth_events.csv` is missing or empty, log a warning "No ground truth events found; precision/recall/delay metrics cannot be computed" and output a report with these metrics marked as "N/A" or "Unavailable". **Dependency**: T012b, T014. (FR-006)
- [X] T017 [US1] Implement metrics calculation (precision, recall, detection delay within ±2 weeks) in `code/evaluate.py`. **MUST** output `data/processed/mmd_delays.json` containing the array of detection delays for comparison. **Dependency**: T016, T014. (FR-006)
- [X] T018 [US1] Implement `code/report_generator.py` to produce `report.pdf` with metrics (FR-006). **Dependency**: T017.
- [X] T011 [US1] Write integration test `tests/integration/test_pipeline.py` with function `test_full_pipeline_flags` to verify full flow. **Dependency**: Requires T012a/b (data download) and T013-T018 (implementation) to be complete.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline change‑point comparison (Priority: P2)

**Goal**: Compare MMD performance against Pettitt and Bayesian Online Change-Point Detection (BOCPD).

**Independent Test**: Run the baseline methods on the same pre‑processed series and verify that their detected change points are reported alongside the MMD results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Write unit test `tests/unit/test_baselines.py` with function `test_pettitt_rolling_window` for Pettitt rolling-window.
- [X] T021 [P] [US2] Write unit test `tests/unit/test_baselines.py` with function `test_bocpd_gaussian` for BOCPD.

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement Pettitt **rolling-window** test in `code/pettitt.py`: window=12, stride=1, compute Pettitt statistic for every window (FR-005)
- [X] T023 [P] [US2] Implement BOCPD (Gaussian observation model) in `code/bocpd.py` (FR-005)
- [X] T024 [US2] Integrate baselines execution into `code/main.py` after preprocessing. **Dependency**: T022, T023.
- [X] T025 [US2] Output `baselines.csv` containing detected change weeks and statistics (test statistic, posterior run-length). **Schema**: `method, week_id, statistic, run_length`. (FR-005)
- [X] T026a [US2] Implement logic in `code/evaluate.py` to compute detection delays from `baselines.csv` alone (independent of MMD). Output `data/processed/baseline_delays.json`. **Dependency**: T025.
- [ ] T049 [US2] [Review] **BOCPD Prior Sensitivity**: Update `code/config.yaml` to expose the `run_length_prior` parameter. **MUST** add key `run_length_prior: { geometric_lambda: 0.1 }` to `code/config.yaml`. **MUST** be completed before T029/T031a to ensure the sensitivity grid can vary this parameter. (FR-007, SC-005)
- [X] T026b [US1+US2] [Review] **Load and Validate Delay Arrays**: Load MMD delays (from `data/processed/mmd_delays.json`) and Baseline delays (from `data/processed/baseline_delays.json`). **MUST** check if either array is empty. If empty, log "Undefined comparison: one method detected zero change points" and skip the t-test. Write "N/A" to `report.pdf` and `baseline_comparison.json`. **Dependency**: T026a, T017.
- [X] T026c [US1+US2] [Review] **Compute and Report t-test**: Perform a two-sample t-test using `scipy.stats.ttest_ind` on the delay arrays (only if both are non-empty). Report the resulting p-value in `report.pdf` to compare detection delays (SC-004). **Dependency**: T026b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Cross-Story Integration (Priority: P2/P3)

**Purpose**: Combine results from US1 and US2 for final comparison and sensitivity analysis.

- [X] T026b [US1+US2] (See Phase 4 for details - Moved here for logical grouping).
- [X] T026c [US1+US2] (See Phase 4 for details - Moved here for logical grouping).

---

## Phase 6: User Story 3 - Robustness & sensitivity analysis (Priority: P3)

**Goal**: Assess sensitivity to kernel bandwidth, window length, and week-alignment tolerance.

**Independent Test**: Execute the sensitivity module, which reruns the detector over a grid of bandwidths and window lengths, and verify that a `sensitivity.csv` summarising metric variation is produced.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Write unit test `tests/unit/test_sensitivity.py` with function `test_grid_generation` for sensitivity grid generation.

### Implementation for User Story 3

- [ ] T031a [P] [US3] Implement `code/sensitivity.py` function `generate_grid()` to create the parameter combinations. **MUST** use `bandwidths=['median', 'cv']`, `window_sizes=[8, 12, 16]`, and `tolerances=[1, 2, 3]`. **Dependency**: T049.
- [ ] T029 [P] [US3] Implement `code/sensitivity.py` to handle grid search and timeout mechanism. **MUST** implement a timeout mechanism in `code/sensitivity.py` for the grid search loop. **MUST** use the config key `config.sensitivity.timeout_minutes` (default 5). If a single configuration exceeds this timeout, abort that configuration, log "Configuration skipped due to timeout", and proceed to the next grid point. **MUST** output `sensitivity.csv` (FR-007). **Dependency**: T031a.
- [X] T030 [US3] Implement week-alignment tolerance sweep (±1, ±2, ±3 weeks) in `code/sensitivity.py` and output `tolerance_sensitivity.csv` with metric variations (FR-010)
- [X] T031b [US3] Execute sensitivity grid in `code/main.py` using the grid from T031a. **Dependency**: T031a.
- [X] T032 [US3] Aggregate metrics for all configurations into `sensitivity.csv`. **Schema**: `bandwidth_type, window_size, tolerance_weeks, precision, recall, detection_delay, fpr`. (FR-007, FR-010)
- [X] T033 [US3] Update `report.pdf` to include sensitivity analysis summary and variation plots: (1) Line plot of precision vs window size, (2) Heatmap of recall vs bandwidth. (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Update `quickstart.md` (add run instructions) and `README.md` (add project overview)
- [X] T036a [P] Refactor `code/mmd_detector.py` to implement vectorized MMD kernel function using NumPy broadcasting.
- [X] T036b [P] Benchmark `code/mmd_detector.py` before and after vectorization; verify runtime reduction of at least 50% on a standard dataset.
- [X] T037 [P] Add unit tests `test_constant_series` and `test_outlier_handling` in `tests/unit/` using synthetic data from T008.
- [X] T038 Run `pytest` in `code/` and verify exit code 0
- [X] T039 [P] Verify all `data/` artifacts have `sha256sum` and update `state/projects/PROJ-734-detecting-distribution-shift-in-public-h.yaml` with hashes. **Logic**: If data files are missing (E-NO-DATA), hash the `data/raw/.metadata.json` file instead and log "Data unavailable, hashed metadata". (Constitution Principle V)
- [X] T040 [US1] [Review] Implement explicit "Data Source Verification" step in `code/download_data.py`. If the CDC URL returns a 404 or 500, the script MUST raise `E-NO-DATA` immediately. **MUST NOT** contain any `try/except` block that falls back to `synthetic_data.py` or a local mock file. Add a comment block citing Constitution Principle VI and FR-001. (Review Concern: Preventing silent synthetic fallbacks)
- [X] T041 [US1] [Review] Update `code/preprocess.py` to explicitly handle the "Constant Series" edge case. If `std(log_ili) == 0` over a window, the script MUST raise a `ValueError` with message "Zero variance detected in window; cannot compute MMD". Log this event and skip the window rather than producing a NaN p-value. (Review Concern: Handling constant ILI series)
- [X] T043 [US2] [Review] Verify Pettitt implementation in `code/pettitt.py` uses a sliding window of a defined duration with stride 1, matching the MMD window configuration exactly. Add a unit test `test_pettitt_window_alignment` to ensure the Pettitt statistic is computed for the exact same time intervals as the MMD detector. (Review Concern: Baseline method alignment)
- [X] T044 [US3] [Review] Update `code/sensitivity.py` to ensure the "Cross-Validated Bandwidth" strategy uses a **rolling-window k-fold cross-validation** on the *training* split of the window pairs, not the entire dataset, to prevent data leakage in the sensitivity analysis. **Logic**: Use a rolling window split where the majority of the time-series data is used for training and the remainder for validation, ensuring no temporal overlap. (Review Concern: Preventing data leakage in CV bandwidth selection)
- [X] T045 [US1] [Review] Add a "Reproducibility Manifest" generation step in `code/main.py`. After the pipeline completes, generate `data/processed/reproducibility_manifest.json` containing: exact git commit hash (via `subprocess.check_output(['git', 'rev-parse', 'HEAD'])`), full `requirements.txt` content (via `open('requirements.txt').read()`), random seed (from config), and the exact URLs used for data download. (Review Concern: Reproducibility verification)
- [X] T047 [US3] [Review] **Tolerance Window Verification**: Add a dedicated unit test `tests/unit/test_evaluate.py` named `test_tolerance_window_logic` that verifies the ±2-week matching logic against a manually constructed synthetic ground truth list where the overlap is exact and where it is off-by-one. This ensures the `evaluate.py` logic correctly implements the ±2-week tolerance window defined in FR-006. (Review Concern: Correctness of tolerance window implementation)
- [X] T048 [US1] [Review] **Permutation Reduction Logging**: Update `code/mmd_detector.py` to ensure that when the permutation count is reduced due to time constraints (FR-008), the **exact** reduction factor and the **final** p-value threshold used are logged to `data/processed/mmd_config.json` and printed to stdout. This is critical for the reproducibility manifest. (Review Concern: Transparency of time-based parameter adjustment)
- [X] T050 [US1] [Review] **Outlier Handling Validation**: Add a unit test `tests/unit/test_preprocess.py` named `test_outlier_detection` that injects an extreme outlier (e.g., A value substantially greater than the mean.) into the synthetic data and verifies that the log-transform and standardization steps handle it without producing `inf` or `nan` values, and that the outlier is flagged in the `preprocessing_log.json`. (Review Concern: Outlier handling in preprocessing)
- [X] T052 [US3] [Review] **Cross-Validation Data Leakage Audit**: Add a dedicated unit test `tests/unit/test_sensitivity.py` named `test_cv_data_leakage` that constructs a synthetic time-series with a known injected shift. Verify that when `code/sensitivity.py` runs the cross-validated bandwidth selection, the validation split does NOT contain data from the same temporal window as the training split, ensuring no look-ahead bias. (FR-007, Review Concern: Preventing data leakage in CV bandwidth selection)
