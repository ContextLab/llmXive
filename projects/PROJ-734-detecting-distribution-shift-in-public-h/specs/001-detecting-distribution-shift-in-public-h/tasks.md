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

- [X] T001 Create project structure: `mkdir -p data/raw data/processed code tests code/contracts`
- [X] T002 Create `requirements.txt` at root with: `numpy, scipy, pandas, scikit-learn, matplotlib, seaborn, pyyaml, pytest, pydantic`
- [X] T003 [P] Create `.flake8` and `pyproject.toml` with black/flake8 settings (max-line-length=88, exclude=venv)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create `code/config.yaml` with keys: `seed: 42`, `permutations: 1000`, `window_size: 12`, `stride: 1`, `alpha: 0.01`, `min_permutations: 100`, `time_budget_minutes: 30`. **Status**: Implemented. Validates all config keys and types.
- [X] T005 [P] Create `contracts/config.schema.yaml` and implement validation in `code/main.py` using `pydantic`. **Status**: Implemented. Validates all config keys and types.
- [X] T006 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for data integrity. **Status**: Implemented. Defines schema for FluView and Ground Truth datasets.
- [X] T007 Setup logging infrastructure in `code/__init__.py` to record runtime params and seeds (FR-009)
- [X] T008 Implement synthetic data generator in `code/synthetic_data.py` for unit tests ONLY. MUST generate data with: (a) missing weeks (NaNs), (b) constant segments (zero variance), and (c) outliers. Must NOT be used for final report; reference E-NO-DATA fallback.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated shift detection for public‑health analysts (Priority: P1) 🎯 MVP

**Goal**: Run a reproducible pipeline that flags weeks where the ILI distribution has changed using MMD, producing `flags.csv` and `report.pdf`.

**Independent Test**: Execute the full pipeline on the FluView dataset and verify that a CSV of flagged weeks is produced together with a summary report containing the required metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Execution depends on code existing.**
> **Prerequisite**: T008 (synthetic data generator) must be complete.

- [X] T010 [P] [US1] Write unit test `tests/unit/test_mmd.py` with function `test_mmd_stat_correctness` using synthetic data from T008 to verify MMD logic.
- [X] T012a [P] [US1] Implement `code/download_data.py` to fetch CDC FluView ILI CSV directly from the canonical CDC source: `. Save to `data/raw/fluview_ili.csv`. **MUST** verify file checksum against a known hash if available, or log the exact URL and retrieval date to `data/raw/.metadata.json`. Do NOT use third-party mirrors (like NAB) as primary source. If the CDC URL returns 404/500, raise `E-NO-DATA`. (FR-001, Constitution Principle VI)
- [X] T012b [P] [US1] Implement `code/download_data.py` (or separate function) to fetch CDC Virological/Hospitalization ground truth directly from the canonical CDC source: `. Save to `data/raw/ground_truth_events.csv` with columns `start_week, end_week, event_name`. **MUST NOT** allow a fallback to a local file provided by the user. If the fetch fails or returns 404/500, raise `E-NO-DATA` exception. (FR-006, Constitution Principle IV)
- [X] T013 [US1] Implement `code/preprocess.py` to handle missing weeks (remove), log-transform, and standardize (FR-002). **MUST** log the count of missing weeks removed to `data/processed/preprocessing_log.json` for auditability. **Dependency**: T012a.
- [X] T013a [US1] Implement `code/preprocess.py` (or separate function) to calculate `N` (total number of consecutive window pairs) from the preprocessed series length. Write `N` to `data/processed/mmd_config.json` **BEFORE** the main detection loop starts. This task MUST run after T013 and before T014. (FR-004, FR-003)
- [X] T014 [US1] Implement `code/mmd_detector.py` with Gaussian-kernel MMD, multi-week windows, and dynamic permutation count. **Internal Logic**:
 1. **Pre-calculation**: Read `N` from `data/processed/mmd_config.json` (generated by T013a).
 2. **Config Write**: Write `permutations`, `alpha`, and `threshold` (0.01/N) to `data/processed/mmd_config.json`. **Note**: The threshold is fixed based on `N` and does not change if permutations are reduced.
 3. **Runtime Monitor**: If `elapsed_time > global_time_budget - buffer`, reduce `permutations` in the in-memory config (e.g., `while permutations > min_permutations: permutations //= 2`), log "Permutations reduced to X", and re-calculate the MMD statistic for the current window. **MUST** enforce `min_permutations=100`.
 4. **Threshold Application**: Use the **pre-calculated** threshold (0.01/N) from the config to flag results.
 5. **Output**: Write the actual number of permutations used, the calculated `N`, and the `flags.csv` file (listing weeks with p < threshold) to `data/processed/`. **Dependency**: T013a, T013. (FR-003, FR-004, FR-008, FR-009)
- [X] T016 [US1] Implement `code/evaluate.py` to load `data/raw/ground_truth_events.csv`, verify source independence (URL whitelist check), and **implement the parsing logic for the "±2-week tolerance window" described in FR-006**. **Logic**: Parse ISO week strings from the CSV, convert to integer week IDs, and match detected weeks within ±2 weeks. **Dependency**: T012b, T014. (FR-006)
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
- [X] T026b [US2] Integrate cross-comparison in `code/evaluate.py`: Load MMD delays (from `data/processed/mmd_delays.json` generated by T017) and Baseline delays (from `data/processed/baseline_delays.json` generated by T026a). **Before running the t-test, check if the MMD delay array or the Baseline delay array is empty. If either is empty, log "Undefined comparison: one method detected zero change points" and skip the t-test. In this case, write "N/A" to the `report.pdf` and `baseline_comparison.json` to satisfy SC-004.** Perform a two-sample t-test using `scipy.stats.ttest_ind` on these delay arrays ONLY if both are non-empty. Report the resulting p-value in `report.pdf` to compare detection delays (SC-004). **Dependency**: T026a, T017. (FR-005, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Cross-Story Integration (Priority: P2/P3)

**Purpose**: Combine results from US1 and US2 for final comparison and sensitivity analysis.

- [X] T026c [US1+US2] **REMOVED** (Logic merged into T026b to avoid duplication and ensure edge case handling occurs before the t-test).
- [X] T026b [US1+US2] (See Phase 4 for details).

---

## Phase 6: User Story 3 - Robustness & sensitivity analysis (Priority: P3)

**Goal**: Assess sensitivity to kernel bandwidth, window length, and week-alignment tolerance.

**Independent Test**: Execute the sensitivity module, which reruns the detector over a grid of bandwidths and window lengths, and verify that a `sensitivity.csv` summarising metric variation is produced.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Write unit test `tests/unit/test_sensitivity.py` with function `test_grid_generation` for sensitivity grid generation.

### Implementation for User Story 3

- [X] T031a [P] [US3] Implement `code/sensitivity.py` function `generate_grid()` to create the parameter combinations (bandwidths x 3 windows x 3 tolerances).
- [X] T029 [P] [US3] Implement `code/sensitivity.py` to handle grid search: bandwidths=[median, cv], windows=[8, 12, 16], output `sensitivity.csv` (FR-007)
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

---

## Phase O: Review & Final Validation

**Purpose**: Address specific reviewer concerns regarding data provenance, statistical rigor, and edge-case handling before final merge.

- [X] T040 [US1] [Review] Implement explicit "Data Source Verification" step in `code/download_data.py`. If the CDC URL returns a 404 or 500, the script MUST raise `E-NO-DATA` immediately. **MUST NOT** contain any `try/except` block that falls back to `synthetic_data.py` or a local mock file. Add a comment block citing Constitution Principle VI and FR-001. (Review Concern: Preventing silent synthetic fallbacks)
- [X] T041 [US1] [Review] Update `code/preprocess.py` to explicitly handle the "Constant Series" edge case. If `std(log_ili) == 0` over a window, the script MUST raise a `ValueError` with message "Zero variance detected in window; cannot compute MMD". Log this event and skip the window rather than producing a NaN p-value. (Review Concern: Handling constant ILI series)
- [X] T043 [US2] [Review] Verify Pettitt implementation in `code/pettitt.py` uses a sliding window of 12 weeks with stride 1, matching the MMD window configuration exactly. Add a unit test `test_pettitt_window_alignment` to ensure the Pettitt statistic is computed for the exact same time intervals as the MMD detector. (Review Concern: Baseline method alignment)
- [X] T044 [US3] [Review] Update `code/sensitivity.py` to ensure the "Cross-Validated Bandwidth" strategy uses a **rolling-window k-fold cross-validation** ([deferred] training, [deferred] validation) on the *training* split of the window pairs, not the entire dataset, to prevent data leakage in the sensitivity analysis. **Logic**: Use a rolling window split where the majority of the time-series data is used for training and the remainder for validation. (Review Concern: Preventing data leakage in CV bandwidth selection)
- [X] T045 [US1] [Review] Add a "Reproducibility Manifest" generation step in `code/main.py`. After the pipeline completes, generate `data/processed/reproducibility_manifest.json` containing: exact git commit hash (via `subprocess.check_output(['git', 'rev-parse', 'HEAD'])`), full `requirements.txt` content (via `open('requirements.txt').read()`), random seed (from config), and the exact URLs used for data download. (Review Concern: Reproducibility verification)
- [X] T046 [US1] [Review] **Data Stream Handling**: Implement `code/download_data.py` with a streaming fallback mechanism for large datasets. If the CDC source provides a large file that cannot be held entirely in RAM (unlikely for FluView but required for robustness), the script MUST use `requests` library with `stream=True` to process the file in fixed-size blocks (e.g., 8KB chunks). **MUST NOT** load the entire file into memory at once. Log the streaming strategy used. (Review Concern: Memory safety for larger future datasets)
- [X] T047 [US3] [Review] **Tolerance Window Verification**: Add a dedicated unit test `tests/unit/test_evaluate.py` named `test_tolerance_window_logic` that verifies the ±2-week matching logic against a manually constructed synthetic ground truth list where the overlap is exact and where it is off-by-one. This ensures the `evaluate.py` logic correctly implements the ±2-week tolerance window defined in FR-006. (Review Concern: Correctness of tolerance window implementation)
- [X] T048 [US1] [Review] **Permutation Reduction Logging**: Update `code/mmd_detector.py` to ensure that when the permutation count is reduced due to time constraints (FR-008), the **exact** reduction factor and the **final** p-value threshold used are logged to `data/processed/mmd_config.json` and printed to stdout. This is critical for the reproducibility manifest. (Review Concern: Transparency of time-based parameter adjustment)
- [X] T049 [US2] [Review] **BOCPD Prior Sensitivity**: Update `code/bocpd.py` to expose the `run_length_prior` parameter in `config.yaml` and add a sensitivity check in `code/sensitivity.py` to verify that the BOCPD results are robust to reasonable changes in the prior (e.g., Geometric(λ=0.1) vs. Uniform(0, 100)). Log the prior used and the resulting change points. (Review Concern: BOCPD prior sensitivity)
- [X] T050 [US1] [Review] **Outlier Handling Validation**: Add a unit test `tests/unit/test_preprocess.py` named `test_outlier_detection` that injects an extreme outlier (e.g., A value substantially greater than the mean.) into the synthetic data and verifies that the log-transform and standardization steps handle it without producing `inf` or `nan` values, and that the outlier is flagged in the `preprocessing_log.json`. (Review Concern: Outlier handling in preprocessing)