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

- [X] T004 Create `code/config.py` to define constants (paths, filter params, seeds, band definitions, ICA params, chunk sizes, epsilon, **window_size=4**, **epoch_duration=300**). **CRITICAL**: The `overlap` parameter MUST be defined as `OVERLAP_DEFERRED` (placeholder) and MUST NOT be set to a concrete value (e.g., 0.5) until the spec resolves the [deferred] status. The config task must explicitly state: "OVERLAP: DEFERRED - Must be resolved in spec before execution." **Must run after Phase 1 setup is complete.**
- [X] T005 [P] Implement `code/utils/eeg_helpers.py` with band-pass, notch, and variance rejection utilities. **Must run after `code/config.py` file exists.**
- [X] T006 [P] Implement `code/utils/stats_helpers.py` with Bonferroni, permutation, and MDES utilities. **Must run after `code/config.py` file exists.**
- [X] T007 [P] Create `code/01_download_data.py` to fetch PhysioNet EEG Motor Movement/Imagery data and verify checksums (FR-001). **Logic**: Download raw data; if fetch fails, raise `RuntimeError` immediately. Log detected task names to `data/interim/detected_tasks.log`. Halt if task names do not match expected set. **Must run after Phase 1 setup is complete.**
- [X] T008a [US0] Create `code/00_feasibility_check_join.py` to join EEG and RT datasets on `participant_id`. **Checks**: Verify RT dataset contains "Simple Reaction Time" task; verify demographic metadata. **CRITICAL**: Explicitly filter out participants with missing RT data immediately after the join; log to `data/interim/feasibility_exclusion_log.csv`. **Deliverable**: If join fails or tasks mismatch, generate `data/processed/feasibility_report.md` and **log a warning**. If the spec assumes alignment, proceed with caution but flag the report. **Output**: `data/interim/joined_metadata.csv` on success (excluding missing RT participants). **Must run after T007 completes.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Band-Power Features and Behavioral Metrics (Priority: P1) 🎯 MVP

**Goal**: Ingest raw EEG and behavioral data, preprocess, extract PSD features, and compute median RTs.

**Independent Test**: Run on a subset of PhysioNet data; verify `data/processed/features_clr.csv` contains one row per participant with delta/theta/alpha/beta/gamma power and median RT, no nulls.

### Implementation for User Story 1

- [ ] T010a [US1] Implement `code/02_preprocess_eeg.py`: Apply **1–40 Hz** band-pass filter, **50/60 Hz** notch, and **bad channel rejection** (variance > 3 SD). Apply **ICA** to remove ocular/muscle artifacts using MNE's default ICA implementation with **0.99 variance retention** (configurable in `config.py`). **Mandatory Logic**: Participants are excluded from the final table if the ratio of rejected channels exceeds 0.30 (>30%). **Note**: ICA failure (non-convergence) is logged but does NOT trigger immediate exclusion unless it results in >30% channel rejection or prevents artifact removal (handled by the channel rejection rule). **Output**: `data/interim/cleaned_eeg_final/` directory containing `.fif` files for retained participants AND `data/interim/exclusion_log.csv` (columns: `participant_id`, `reason`, `channels_rejected_ratio`). **This task guarantees the exclusion log exists even if ICA fails for some participants.** **Dependencies**: T005/T006 provide code utilities (implicit code dependency); T007/T008a provide data availability (explicit data dependency). **Must run after T007, T008a, T005, T006 complete.**
- [ ] T012 [US1] Implement `code/03_extract_features.py`: Compute Welch's PSD on continuous **5-minute epochs** using **4-second windows** with **[deferred] overlap** (configurable in `config.py`, per Spec FR-003 and Constitution Principle VI) and aggregate power into **delta, theta, alpha, low-beta, high-beta, and gamma** bands (FR-003). **Note**: **Chunked processing** must be implemented to handle large datasets within RAM (process in batches of participants). **Aggregation**: Use **global mean aggregation** across channels as per Constitution Principle VI. **Input**: Must read `data/interim/exclusion_log.csv` to filter out excluded participants before processing (handle missing/empty file gracefully by creating an empty filter). **Output**: `data/interim/eeg_psd.csv` containing **raw power values for all six bands** (delta, theta, alpha, low_beta, high_beta, gamma) with no nulls. **Must run after T010a, T007, T008a complete.**
- [ ] T013 [P] [US1] Implement behavioral parsing: extract median RT, exclude outliers (<100ms, >2000ms), exclude participants if <70% trials remain (FR-004). **Output**: `data/interim/behavioral_metrics.csv` (columns: `participant_id`, `median_rt`, `n_trials`, `n_trials_excluded`) AND `data/interim/behavioral_exclusion_log.csv` (columns: `participant_id`, `reason`). **Dependencies**: T007/T008a provide data. T013 is independent of T010 (EEG processing). **Must run after T007 and T008a complete.**
- [ ] T015 [US1] Implement relative power calculation (band/total) AND apply **Centered Log-Ratio (CLR) transformation** as mandated by Plan Phase 1 (FR-010). **Input**: `data/interim/eeg_psd.csv` (from T012) and `data/interim/behavioral_metrics.csv` (from T013). **Process**: Calculate relative power (band power / total power across 1-40 Hz), then apply CLR transformation to handle compositional data constraints. **Output**: `data/processed/features_clr.csv` containing **CLR-transformed relative power values** (no raw relative power only). **Must run after T012, T013, T007, T008a complete.**
- [ ] T035a [US1] Validate schema of `data/processed/features_clr.csv` (no nulls, correct columns, valid RT range **100ms to 2000ms** as per FR-004 outlier exclusion). **Must run after T015 completes.**

**Parallel Execution Note**: Tasks T012 (EEG PSD) and T013 (Behavioral Metrics) are independent of each other. T012 depends on T010a (which now includes exclusion), and T013 depends on T008a. Once their respective prerequisites are met, T012 and T013 can be executed in parallel. T015 depends on the completion of both.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

**Goal**: Fit Linear/LASSO models, perform correlations, permutation tests, and non-linear checks.

**Independent Test**: Run modeling script on `features_clr.csv`; verify `data/processed/model_results.json` contains R², RMSE, p-values, and Bonferroni flags.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `code/04_modeling.py`: Fit Multiple Linear Regression with k-fold cross-validation (depends on `data/processed/features_clr.csv`) (FR-005). **Constraint**: Implement **chunked processing** for memory efficiency (process in batches of 100 participants). **Output**: `data/interim/split_indices.json`, `data/processed/model_results.json` (partial). **Must run after T015, T007, T008a complete.**
- [X] T018 [US2] Implement LASSO regression with lambda tuning to minimize RMSE (FR-005). **Must run after T017 completes.**
- [ ] T019 [US2] Calculate and log Adjusted R² and optimal lambda to `data/processed/model_results.json`. **Must run after T018 completes.**
- [ ] T020 [P] [US2] Implement Pearson correlation tests between CLR-transformed relative band powers and median RT (depends on `data/processed/features_clr.csv`) (FR-006). **Must run after T015 completes.**
- [X] T021 [US2] Apply Bonferroni correction for 6 bands (0.05/6 = 0.0083) as per Spec FR-006 and flag significant results. **Must run after T020 completes.**
- [ ] T022a [US2] Implement Permutation Test (Part 1): **Generate Null Distribution**. **Mandatory**: Perform **[deferred] shuffles** (N=10000) of RT values across the **entire dataset** (stratified if applicable) to simulate the null hypothesis. **Scope**: Re-train the model using the **full 5-fold cross-validation process** (not just test set) for each shuffle to generate the null distribution of R². **Input**: `data/interim/split_indices.json`, `data/processed/model_results.json`, and model objects from **T017/T018** (for model structure) and lambda value from **T019**. **Constraint**: If the test set size is < 10 samples, raise a clear error or reduce permutations with a warning to ensure statistical validity. **Output**: `data/interim/permutation_null_distribution.npy`. **Must run after T017, T018, T019, T007, T008a complete.**
- [ ] T022b [US2] Implement Permutation Test (Part 2): **Calculate Significance**. Compare the observed R² against the null distribution from T022a to calculate the p-value. **Output**: Append permutation results to `data/processed/model_results.json`. **Must run after T022a completes.**
- [ ] T023 [US2] Perform post-hoc power analysis to estimate the **required sample size (N)** to detect an effect size of R² = 0.10 with power ≥ 0.80 using `statsmodels.stats.power` and report in `data/processed/model_results.json` (FR-011). **If the result is non-significant, report the null result with effect sizes and confidence intervals, and EXPLICITLY STATE in the output that "The hypothesis was not supported" as per Spec Edge Cases.** **Must run after T019 completes.**
- [X] T024 [P] [US2] Implement non-linear interaction analysis (polynomial terms for alpha and beta, degree configurable in `config.py`) and F-test comparison (FR-012). **Decision Criterion**: Report if the model explains significantly more variance with **p < 0.05**. **Must run after T019 completes.**
- [ ] T025 [US2] Generate `data/processed/correlations.csv` and `data/processed/non_linear_comparison.json`. **Must run after T021 and T024 complete.**
- [ ] T035b [US2] Validate schema of `data/processed/model_results.json` and `data/processed/correlations.csv`. **Must run after T025 completes.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Re-run analysis with alternative parameters to test stability.

**Independent Test**: Run robustness script; verify `data/processed/robustness_report.csv` shows R² variation across window lengths and ICA status.

### Implementation for User Story 3

- [X] T026a [US3] Implement `code/05_robustness_preprocess.py`: **Re-run the Preprocessing step ONLY** (logic from T010a) with `--no-ica` flag. **Dependency**: Must run after T010a scripts are implemented and raw data (T007/T008) is available. **Constraint**: All robustness artifacts MUST be written to `data/interim/robustness/no_ica/` subdirectories. **Output**: `data/interim/robustness/no_ica/cleaned_eeg/` directory containing `.fif` files. **Must run after T010a scripts are implemented and T007/T008 data is available.**
- [X] T026b [US3] Implement `code/05_robustness_preprocess.py`: **Re-run the Preprocessing step ONLY** (logic from T010a) with `--window-size 2` flag (using 2-second windows instead of 4-second). **Dependency**: Must run after T010a scripts are implemented and raw data (T007/T008) is available. **Constraint**: All robustness artifacts MUST be written to `data/interim/robustness/window_2s/` subdirectories. **Output**: `data/interim/robustness/window_2s/cleaned_eeg/` directory containing `.fif` files. **Must run after T010a scripts are implemented and T007/T008 data is available.**
- [ ] T026c_1 [US3] Implement `code/05_robustness_features.py` (Part 1): **Re-run `code/03_extract_features.py`** (using the logic from T012) on the robustness data from T026a (no-ica) and T026b (window-2s) separately to generate raw PSD. **Input**: `data/interim/robustness/no_ica/cleaned_eeg/` and `data/interim/robustness/window_2s/cleaned_eeg/`. **Output**: `data/interim/robustness/no_ica/eeg_psd_raw.csv` and `data/interim/robustness/window_2s/eeg_psd_raw.csv`. **Must run after T026a and T026b complete.**
- [ ] T026c_2 [US3] Implement `code/05_robustness_features.py` (Part 2): **Apply relative power and CLR transformation** (logic from T015) to the raw PSD from T026c_1. **Input**: `data/interim/robustness/no_ica/eeg_psd_raw.csv`, `data/interim/robustness/window_2s/eeg_psd_raw.csv`, and `data/interim/behavioral_metrics.csv` (from T013). **Output**: `data/interim/robustness/no_ica/features_clr.csv` and `data/interim/robustness/window_2s/features_clr.csv`. **Dependencies**: T026c_1, T013. **Must run after T026c_1 and T013 complete.**
- [ ] T026d [US3] Implement `code/05_robustness_modeling.py`: **Re-run `code/04_modeling.py`** on the robustness features from T026c_2 to generate robustness metrics (FR-008). **Input**: `data/interim/robustness/no_ica/features_clr.csv` and `data/interim/robustness/window_2s/features_clr.csv`. **Output**: `data/interim/robustness/robustness_report.csv` containing R² stability metrics and percentage difference in alpha power means. **Must run after T026c_2 complete.**
- [X] T027 [US3] Compare R² stability and report percentage difference in alpha power means (FR-008). **Must run after T026d completes.**
- [X] T028a [US3] Implement `code/06_sensitivity_sweep.py`: **Sweep p-value threshold across a range of low to moderate significance levels.** and record count of significant correlations at each step (FR-009). **Must run after T025, T007, T008a complete.**
- [ ] T028b [US3] Generate sensitivity plot AND a **text-based sensitivity analysis report**. **Mandatory**: The report MUST explicitly state the exact threshold in the narrative format: "Significant at p<0.04, non-significant at p<0.03" (as per Spec Edge Cases). **Must run after T028a completes.**
- [ ] T030 [US3] Generate `data/processed/robustness_report.csv` and `data/processed/sensitivity_plot.png`. **Must run after T027 and T028b complete.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Validation

**Purpose**: Aggregate results and verify success criteria.

- [ ] T031 [US3] Implement `code/07_generate_report.py` to aggregate all metrics into `data/processed/final_report.md`. **Must run after T030 completes.**
- [ ] T032 [US3] Verify SC-001 to SC-005: Adjusted R², Bonferroni p-value, stability metrics, sensitivity threshold, and CPU feasibility. **Mechanism**: Run pipeline with `time` and `psutil` monitoring, log max RAM and total duration to `data/processed/verification_log.json` (keys: `max_ram_gb`, `total_duration_sec`). **Task must REPORT** these metrics; **IF max_ram_gb > 7 OR total_duration_sec > 21600 (6h), the task MUST exit with code 1 (FAIL)**. **Must run after T031, T007, T008a complete.**
- [X] T033 [P] Run unit tests for `utils/` helpers. **Must run after T005/T006 code is committed.**
- [X] T034 [US3] Run integration test `tests/integration/test_pipeline.py` to ensure end-to-end flow. **Must run after T030 completes.**
- [X] T036 [US3] Run contract tests for `feature_schema` and `result_schema`. **Must run after T015, T019, T007, T008a complete.**

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
- **User Story 2 (P2)**: Depends on US1 output (`features_clr.csv`)
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
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `features_clr.csv`)
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
- **CRITICAL**: Primary analysis uses **5-minute epochs** with **4-second windows** (Spec FR-003) with **[deferred] overlap** (configurable via config.py); robustness check uses short time windows (Spec FR-008).
- **REVISED**: T017 clarified to ensure 5-fold CV is implemented correctly with stratified splits if needed to maintain class balance (though continuous RT does not have classes, ensure fold distribution is representative) and explicitly saves `split_indices.json`.
- **REVISED**: T022a clarified to explicitly state **[deferred] shuffles** (N=10000) on the **entire dataset** (full 5-fold CV) to generate a valid null distribution for the model's R², preventing data leakage and ensuring statistical validity.
- **REVISED**: T023 clarified to use `statsmodels.stats.power` or equivalent to calculate **required sample size (N)** for R²=0.10 with power ≥ 0.80, ensuring the calculation accounts for the actual N available after exclusion criteria, and appends to `model_results.json`. **Explicitly states hypothesis rejection if non-significant**.
- **REVISED**: T024 clarified to specify polynomial degree (configurable) for non-linear terms and to use an F-test for model comparison as per FR-012.
- **REVISED**: T028 clarified to explicitly state the sweep range (to 0.10) and step size (0.01).
- **REVISED**: T026 clarified to ensure robustness analysis includes both window size variation and ICA removal as distinct test conditions with isolated artifacts (`data/interim/robustness/`). **T026a handles No-ICA (Preprocessing only), T026b handles Window-2s (Preprocessing only).**
- **REVISED**: T010 clarified to ensure ICA is applied as the primary cleaning method per Spec FR-002 and Constitution Principle VI, with explicit handling for ocular artifacts and **implementation of `--no-ica` flag**, and **explicit constraint that primary run MUST use ICA**. **Merged T010a and T010b into T010a to ensure exclusion log is always generated. ICA failure does NOT trigger exclusion unless >30% channels rejected.**
- **REVISED**: T012 clarified to ensure Welch's PSD uses **5-minute epochs** with **4-second windows** with **[deferred] overlap** (configurable via config.py) as the primary configuration, with robustness checks using 2-second windows, and explicitly verifies the generation of all six band columns.
- **REVISED**: T015 clarified to ensure relative power calculation is performed **AND CLR transformation is applied** as per Plan Phase 1, and the output file contains **CLR-transformed relative power values**. **Zero handling: use epsilon from config.py.**
- **REVISED**: T020 clarified to ensure Pearson correlations are computed on CLR-transformed relative band powers (band/total) as per FR-010 and Plan Phase 1.
- **REVISED**: T028 clarified to ensure sensitivity analysis sweeps p-value thresholds from 0.01 to 0.10 in 0.01 increments and includes the mandatory narrative format.
- **REVISED**: T030 clarified to ensure `robustness_report.csv` and `sensitivity_plot.png` are generated with all required metrics.
- **REVISED**: T031 clarified to ensure `final_report.md` aggregates all metrics from previous phases into a comprehensive summary.
- **REVISED**: T033 clarified to ensure unit tests cover all helper functions in `utils/`.
- **REVISED**: T034 clarified to ensure integration tests verify the end-to-end pipeline flow from data download to final report generation.
- **REVISED**: T036 clarified to ensure contract tests validate `feature_schema` and `result_schema` against generated data.
- **CRITICAL**: **NO SYNTHETIC FALLBACKS**. If real data fetch fails, the run MUST fail (T007).
- **CRITICAL**: **NO TOY DATASETS**. Use chunked processing for large datasets (T012, T017).
- **CRITICAL**: **TASK ALIGNMENT**. Verify "Simple RT" vs "Motor Imagery" explicitly (T008a).
- **CRITICAL**: **MINIMUM EPOCH**. Enforce 5-minute minimum (T012).
- **CRITICAL**: **POWER SANITY**. Report required sample size (N) in results (T023).
- **CRITICAL**: **ICA MANDATORY**. T010a must enforce ICA as a hard requirement for the primary pipeline; no fallback allowed. ICA failure = exclusion ONLY if >30% channels rejected.
- **CRITICAL**: **VALIDATION GATE**. T032 must fail the build if RAM/Duration limits are exceeded.
- **CRITICAL**: **FILENAME CONSISTENCY**. All tasks must use `features_clr.csv` where CLR transformation is applied.
- **CRITICAL**: **DEFERRED PARAMS**. T004 must not hardcode `overlap` value; it must be `OVERLAP_DEFERRED` until spec resolves.
- **CRITICAL**: **PERMUTATION SCOPE**. T022a must use full 5-fold CV and [deferred] shuffles.