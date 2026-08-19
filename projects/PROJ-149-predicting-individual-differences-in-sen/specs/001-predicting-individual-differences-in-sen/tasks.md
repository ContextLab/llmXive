# Tasks: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

**Input**: Design documents from `/specs/001-predict-sensory-speed-from-eeg/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create project directory structure (`code/`, `tests/`, `data/raw/`, `data/interim/`, `data/processed/`, `code/utils/`)
- [X] T001b Create `code/requirements.txt` with pinned versions (mne, scikit-learn, pandas, numpy, scipy, matplotlib, seaborn, pyyaml)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to define constants (paths, filter params, seeds, band definitions, ICA params, chunk sizes, **EPSILON=1e-9**). **CRITICAL**: Do NOT define a default value for `OVERLAP`. The task MUST require the user to explicitly set `OVERLAP` in `config.py` before execution. If `OVERLAP` is not set, the code MUST raise a `ValueError` with message "OVERLAP not set in config.py. Spec is [deferred]. Please set OVERLAP or amend spec." **MUST** define `EPSILON` for log-transform stability. **Must run after Phase 1 setup is complete.**
- [X] T005 [P] Implement `code/utils/eeg_helpers.py` with band-pass, notch, and variance rejection utilities. **Must run after `code/config.py` file exists.**
- [X] T006 [P] Implement `code/utils/stats_helpers.py` with Bonferroni, permutation, and MDES utilities. **Must run after `code/config.py` file exists.**
- [ ] T007 [P] Create `code/01_download_data.py` to fetch PhysioNet EEG Motor Movement/Imagery data and verify checksums (FR-001). **Logic**: Download raw data; if fetch fails, raise `RuntimeError` immediately. Log detected task names to `data/interim/detected_tasks.log`. Halt if task names do not match expected set. **Must run after Phase 1 setup is complete.**
- [ ] T008a [US0] Create `code/00_feasibility_check_join.py` to join EEG and RT datasets on `participant_id`. **Checks**: Verify RT dataset contains "Simple Reaction Time" task; verify demographic metadata. **CRITICAL**: Explicitly filter out participants with missing RT data immediately after the join; log to `data/interim/feasibility_exclusion_log.csv`. **Deliverable**: If join fails or tasks mismatch, generate `data/processed/feasibility_report.md` and **exit with code 1** (HALT). If the spec assumes alignment, proceed with caution but flag the report. **Output**: `data/interim/joined_metadata.csv` on success (excluding missing RT participants). **Must run after T007 completes.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Band-Power Features and Behavioral Metrics (Priority: P1) 🎯 MVP

**Goal**: Ingest raw EEG and behavioral data, preprocess, extract PSD features, and compute median RTs.

**Independent Test**: Run on a subset of PhysioNet data; verify `data/processed/features.csv` contains one row per participant with delta/theta/alpha/beta/gamma power and median RT, no nulls.

### Implementation for User Story 1

- [X] T010a [US1] Implement `code/02_preprocess_eeg.py` (Part 1): **Preprocessing**. Apply **1–40 Hz** band-pass filter, **50/60 Hz** notch, and **bad channel rejection**. **Definition**: Reject channels with variance exceeding a statistically significant threshold from the mean variance across all channels in the current session. **Config**: Use `config.BAD_CHANNEL_THRESHOLD_STD` (or equivalent) for the threshold. If not set, raise `ValueError`. **Output**: `data/interim/preprocessed_eeg/` directory containing `.fif` files. **Dependencies**: T005/T006 provide code utilities; T007/T008a provide data availability. **Must run after T007, T008a, T005, T006 complete.**
- [X] T010b [US1] Implement `code/02_preprocess_eeg.py` (Part 2): **ICA Application**. Apply **ICA** to remove ocular/muscle artifacts using MNE's default ICA implementation with **0.99 variance retention** (configurable in `config.py`). **Output**: `data/interim/ica_cleaned_eeg/` directory containing `.fif` files. **Must run after T010a completes.**
- [ ] T010c [US1] Implement `code/02_preprocess_eeg.py` (Part 3): **Exclusion Logic & Logging**. Exclude participants if the ratio of rejected channels exceeds 0.30 (>30%). **Output**: `data/interim/exclusion_log.csv` (columns: `participant_id`, `reason`, `channels_rejected_ratio`) and `data/interim/cleaned_eeg_final/` directory containing `.fif` files for retained participants. **Must run after T010b completes.**
- [ ] T012 [US1] Implement `code/03_extract_features.py`: Compute Welch's PSD on continuous **5-minute epochs** using **4-second windows** with **overlap read from `config.overlap`** (must be explicitly set; if undefined, raise `ValueError` with message "OVERLAP not set in config.py. Spec is [deferred]. Please set OVERLAP or amend spec.") and aggregate power into **delta, theta, alpha, low-beta, high-beta, and gamma** bands (FR-003). **Mandatory**: Calculate relative power (band/total) and apply **Centered Log-Ratio (CLR) transformation** by adding `config.EPSILON` (1e-9) to all values before log to handle compositional data constraints (FR-010). **Input**: Must read `data/interim/exclusion_log.csv` to filter out excluded participants. **Error Handling**: If `data/interim/exclusion_log.csv` is missing, raise `FileNotFoundError` with message "Exclusion log missing. Ensure T010c completed successfully." **Output**: `data/processed/features_clr.csv` containing **CLR-transformed relative power values** (final merged table with behavioral metrics). **Verification**: Output MUST match `contracts/feature_schema.schema.yaml`. **Must run after T010c, T007, T008a, T013 complete.**
- [ ] T013 [P] [US1] Implement behavioral parsing: extract median RT, exclude outliers (<100ms, >2000ms), exclude participants if <70% trials remain (FR-004). **Output**: `data/interim/behavioral_metrics.csv` (columns: `participant_id`, `median_rt`, `n_trials`, `n_trials_excluded`) AND `data/interim/behavioral_exclusion_log.csv` (columns: `participant_id`, `reason`). **Dependencies**: T007/T008a provide data. T013 is independent of T010 (EEG processing). **Must run after T007 and T008a complete.**
- [ ] T035a [US1] Validate schema of `data/processed/features_clr.csv` (no nulls, correct columns, valid RT range **100ms to 2000ms** as per FR-004 outlier exclusion). **Mandatory**: Run `pytest tests/contract/test_feature_schema.py`. **If the test file is missing, create it based on the schema definition in `contracts/feature_schema.schema.yaml` and then run it.** **Must run after T012 completes.**

**Parallel Execution Note**: Tasks T010a, T010b, T010c are sequential within the preprocessing pipeline. T012 depends on T013 (behavioral metrics) and T010c (EEG features). T013 is independent of T010. **T012 CANNOT run until T013 completes.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

**Goal**: Fit Linear/LASSO models, perform correlations, permutation tests, and non-linear checks.

**Independent Test**: Run modeling script on `features.csv`; verify `data/processed/model_results.json` contains R², RMSE, p-values, and Bonferroni flags.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `code/04_modeling.py`: Fit Multiple Linear Regression and LASSO models with -fold cross-validation (depends on `data/processed/features_clr.csv`) (FR-005). **Constraint**: Implement **chunked processing** for memory efficiency (process in batches of participants). **Tuning**: Tune lambda to minimize RMSE. **Split**: Perform a standard train/test split BEFORE 5-fold CV on the training set to create a held-out test set. **Output**: `data/interim/split_indices.json` (containing train/test indices), `data/processed/model_results.json` (containing Adjusted R², optimal lambda, RMSE for both models, and test set metrics). **Schema**: Output must match `contracts/result_schema.schema.yaml`. **Must run after T012, T013, T007, T008a complete.**
- [ ] T020 [P] [US2] Implement Pearson correlation tests between CLR-transformed relative band powers and median RT (depends on `data/processed/features_clr.csv`) (FR-006). **Output**: `data/interim/correlations_raw.csv` with columns `[band, r_value, p_value, n_trials]` (comma-delimited) and log the uncorrected p-values. **Must run after T012 completes.**

- [ ] T021 [US2] Apply Bonferroni correction for 6 bands (0.05/6 = 0.0083) as per Spec FR-006 and flag significant results. **Must run after T020 completes.**
- [ ] T022a [US2] Implement Permutation Test (Part 1): **Generate Null Distribution**. **Mandatory**: Perform a sufficient number of shuffles (configurable in `config.py`, default 10000) of RT values **only on the held-out test set** (from `data/interim/split_indices.json`) to simulate the null hypothesis. **Scope**: For each shuffle, **evaluate the pre-trained model** (from T017) on the shuffled test set to generate the null distribution of R². **Do NOT re-train the model or run 5-fold CV for each shuffle.** **Prerequisite Check**: Verify existence of `split_indices.json` and `model_results.json`. If missing, raise `RuntimeError` with message "Prerequisite artifacts missing. Ensure T017 completed successfully." **Input**: `data/interim/split_indices.json`, `data/processed/model_results.json`, and model objects from **T017**. **Constraint**: If the test set size is < 10 samples, raise a clear error or reduce permutations with a warning to ensure statistical validity. **Output**: `data/interim/permutation_null_distribution.npy` (numpy array of shape (N,)) where N is the number of shuffles performed. **Must run after T017 completes.**
- [ ] T022b [US2] Implement Permutation Test (Part 2): **Calculate Significance**. Compare the observed R² against the null distribution from T022a to calculate the p-value using the formula: `p = (count(null_R2 >= observed_R2) + 1) / (N + 1)` where **N** is the number of shuffles performed. **Output**: **Update** `data/processed/model_results.json` to include the key `permutation_p_value`. **Must run after T022a completes.**
- [ ] T023 [US2] Perform post-hoc power analysis to estimate the **required sample size (N)** to detect an effect size of R² = 0.10 with power ≥ 0.80 using `statsmodels.stats.power` and report in `data/processed/model_results.json` (FR-011). **If the result is non-significant, report the null result with effect sizes and confidence intervals, and EXPLICITLY STATE in the output that "The hypothesis was not supported" as per Spec Edge Cases.** **Output**: Append `post_hoc_power_analysis` object with keys `required_n`, `power`, `effect_size` to `data/processed/model_results.json`. **Must run after T017 completes.**
- [ ] T024 [P] [US2] Implement non-linear interaction analysis (polynomial terms for alpha and beta, degree configurable in `config.py`) and F-test comparison (FR-012). **Decision Criterion**: Report if the model explains significantly more variance with **p < 0.05**. **Must run after T017 completes.**

- [ ] T025 [US2] Generate `data/processed/correlations.csv` and `data/processed/non_linear_comparison.json`. **Must run after T021 and T024 complete.**

- [ ] T035b [US2] Validate schema of `data/processed/model_results.json` and `data/processed/correlations.csv`. **Must run after T025 completes.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Re-run analysis with alternative parameters to test stability.

**Independent Test**: Run robustness script; verify `data/processed/robustness_report.csv` shows R² variation across window lengths and ICA status.

### Implementation for User Story 3

- [ ] T025a [US3] Create `code/05_robustness_full_pipeline.py`. **Purpose**: A unified script that can run the full pipeline (Preprocessing -> Features -> Modeling) with flags to alter parameters (e.g., `--no-ica`, `--window-size 2`). **Dependencies**: Depends on the **implementation** (code existence) of T010, T012, T017 logic, not their execution. **Output**: The script itself. **Must run after T017, T012, T010a/b/c implementations are complete.**
- [ ] T026a [US3] Implement `code/05_robustness_full_pipeline.py` (No-ICA): **Re-run the Full Robustness Pipeline** (Preprocessing without ICA, Feature Extraction, Modeling) with `--no-ica` flag. **Dependency**: Must run after T025a, T007/T008 data is available. **Constraint**: All robustness artifacts MUST be written to `data/interim/robustness/no_ica/` subdirectories. **Dependencies**: T025a (script exists), T007, T008a (raw data). **Output**: `data/interim/robustness/no_ica/features_clr.csv` and `data/interim/robustness/no_ica/model_results.json`. **Must run after T025a, T007, T008a complete.**
- [ ] T026b [US3] Implement `code/05_robustness_full_pipeline.py` (Window-2s): **Re-run the Full Robustness Pipeline** (Preprocessing with 2s windows, Feature Extraction, Modeling) with `--window-size 2` flag. **Dependency**: Must run after T025a, T007/T008 data is available. **Constraint**: All robustness artifacts MUST be written to `data/interim/robustness/window_2s/` subdirectories. **Dependencies**: T025a (script exists), T007, T008a (raw data). **Output**: `data/interim/robustness/window_2s/features_clr.csv` and `data/interim/robustness/window_2s/model_results.json`. **Must run after T025a, T007, T008a complete.**
- [ ] T027 [US3] Compare R² stability and report percentage difference in alpha power means (FR-008). **Input**: `data/interim/robustness/no_ica/model_results.json` and `data/interim/robustness/window_2s/model_results.json`. **Output**: `data/interim/robustness/robustness_report.csv` containing R² stability metrics and percentage difference in alpha power means. **Must run after T026a and T026b complete.**

- [ ] T028a [US3] Implement `code/06_sensitivity_sweep.py`: **Sweep p-value threshold from 0.01 to 0.10 with a step size of 0.01** and record count of significant correlations at each step (FR-009). **Must run after T025, T007, T008a complete.**

- [ ] T028b [US3] Generate sensitivity plot AND a **text-based sensitivity analysis report**. **Mandatory**: The report MUST explicitly state the exact threshold in the narrative format: "Significant at p<0.04, non-significant at p<0.03" (as per Spec Edge Cases). **Must run after T028a completes.**

- [ ] T030 [US3] Generate `data/processed/robustness_report.csv` and `data/processed/sensitivity_plot.png`. **Must run after T027 and T028b complete.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Validation

**Purpose**: Aggregate results and verify success criteria.

- [ ] T031 [US3] Implement `code/07_generate_report.py` to aggregate all metrics into `data/processed/final_report.md`. **Must run after T030 completes.**

- [ ] T032 [US3] Verify SC-001 to SC-005: Adjusted R², Bonferroni p-value, stability metrics, sensitivity threshold, and CPU feasibility. **Mechanism**: **Wrap the primary pipeline execution (T010-T017) in a `psutil` monitor script that logs `max_rss` and `elapsed_time` to a temp file every 1s**, then reads this file to determine pass/fail. Log max RAM and total duration to `data/processed/verification_log.json` (keys: `max_ram_gb`, `total_duration_sec`). **Task must REPORT** these metrics; **IF max_ram_gb > 7 OR total_duration_sec > 21600 (6h), the task MUST exit with code 1 (FAIL)**. **Note**: This hard fail applies ONLY to the Primary Pipeline; robustness checks (T026) are optional and excluded from this hard fail unless explicitly run as part of primary validation. **Must run after T031, T007, T008a complete.**

- [X] T033 [P] Run unit tests for `utils/` helpers. **Must run after T005/T006 code is committed.**
- [X] T034 [US3] Run integration test `tests/integration/test_pipeline.py` to ensure end-to-end flow. **Must run after T030 completes.**
- [X] T036 [US3] Run contract tests for `feature_schema` and `result_schema`. **Must run after T012, T017, T007, T008a complete.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 output (`features.csv`)
- **User Story 3 (P3)**: Depends on US1 output (preprocessing) and US2 output (modeling)

### Within Each User Story

- Models before services (scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 tasks can start in parallel if US1 is done
- All tests for a user story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `features.csv`)
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
 - Developer B: User Story 2 (once US1 data ready)
 - Developer C: User Story 3 (once US2 results ready)
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
- **CRITICAL**: Do NOT use `load_in_8bit` or GPU-specific code. All processing must run on CPU-only CI.
- **CRITICAL**: Ensure `code/00_feasibility_check_join.py` and `code/00_feasibility_check_report.py` run AFTER `code/01_download_data.py` to prevent wasted compute on missing data.
- **CRITICAL**: Primary analysis uses **5-minute epochs** with **4-second windows** (Spec FR-003) with **overlap explicitly set in config.py** (T004 fallback for [deferred] removed; must be set); robustness check uses short time windows (Spec FR-008).
- **REVISED**: T017 clarified to ensure 5-fold CV is implemented correctly with stratified splits if needed to maintain class balance (though continuous RT does not have classes, ensure fold distribution is representative) and explicitly saves `split_indices.json`.
- **REVISED**: T022a clarified to explicitly state **configurable shuffles** (default 10000) on the **held-out test set** (evaluating pre-trained model, NOT re-training) to generate a valid null distribution for the model's R², preventing data leakage and ensuring statistical validity and feasibility. Formula uses actual N.
- **REVISED**: T023 clarified to use `statsmodels.stats.power` or equivalent to calculate **required sample size (N)** for R²=0.10 with power ≥ 0.80, ensuring the calculation accounts for the actual N available after exclusion criteria, and appends to `model_results.json`. **Explicitly states hypothesis rejection if non-significant**.
- **REVISED**: T024 clarified to specify polynomial degree (configurable) for non-linear terms and to use an F-test for model comparison as per FR-012.
- **REVISED**: T028 clarified to explicitly state the sweep range (to 0.10) and step size (0.01).
- **REVISED**: T026 clarified to ensure robustness analysis includes both window size variation and ICA removal as distinct test conditions with isolated artifacts (`data/interim/robustness/`). **T026a handles No-ICA (Full Pipeline), T026b handles Window-2s (Full Pipeline).**
- **REVISED**: T010 clarified to ensure ICA is applied as the primary cleaning method per Spec FR-002 and Constitution Principle VI, with explicit handling for ocular artifacts and **implementation of `--no-ica` flag**, and **explicit constraint that primary run MUST use ICA**. **Merged T010a and T010b into T010a/b/c to ensure exclusion log is always generated. ICA failure does NOT trigger exclusion unless >30% channels rejected.**
- **REVISED**: T012 clarified to ensure Welch's PSD uses **5-minute epochs** with **4-second windows** with **overlap from `config.overlap`** (must be set, error if undefined) as the primary configuration, with robustness checks using 2-second windows, and explicitly verifies the generation of all six band columns. **Includes CLR transformation** and **epsilon handling**.
- **REVISED**: T030 clarified to ensure `robustness_report.csv` and `sensitivity_plot.png` are generated with all required metrics.
- **REVISED**: T031 clarified to ensure `final_report.md` aggregates all metrics from previous phases into a comprehensive summary.
- **REVISED**: T033 clarified to ensure unit tests cover all helper functions in `utils/`.
- **REVISED**: T034 clarified to ensure integration tests verify the end-to-end pipeline flow from data download to final report generation.
- **REVISED**: T036 clarified to ensure contract tests validate `feature_schema` and `result_schema` against generated data.
- **CRITICAL**: **NO SYNTHETIC FALLBACKS**. If real data fetch fails, the run MUST fail (T007).
- **CRITICAL**: **NO TOY DATASETS**. Use chunked processing for large datasets (T012, T017).
- **CRITICAL**: **TASK ALIGNMENT**. Verify "Simple RT" vs "Motor Imagery" explicitly (T008a).
- **CRITICAL**: **MINIMUM EPOCH**. Enforce 5-minute minimum (T012).
- **CRITICAL**: **POWER SANITY**. Report required sample size (N) and observed power in results (T023).
- **CRITICAL**: **ICA MANDATORY**. T010 must enforce ICA as a hard requirement for the primary pipeline; no fallback allowed. ICA failure = exclusion ONLY if >30% channels rejected.
- **CRITICAL**: **VALIDATION GATE**. T032 must fail the build if RAM/Duration limits are exceeded (Primary Pipeline only).
- **CRITICAL**: **FILENAME CONSISTENCY**. All tasks must use `features_clr.csv` where CLR transformation is applied.
- **CRITICAL**: **DEFERRED PARAMS**. T004 must not hardcode `overlap` value; it must require explicit user configuration.
- **CRITICAL**: **PERMUTATION SCOPE**. T022a must use held-out test set shuffling and training set re-training (evaluated only, no re-training).
- **CRITICAL**: **BAD CHANNEL THRESHOLD**. T010a must use a configurable threshold from `config.py` to satisfy the "statistically significant" requirement without hardcoding a specific value like 3 SD.