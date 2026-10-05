# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `/specs/001-cognitive-fatigue-from-restin/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (requires locking or unique filenames to avoid race conditions)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project directory structure: `projects/PROJ-470-predicting-cognitive-fatigue-from-restin/`, `data/raw/`, `data/processed/`, `code/`, `tests/unit/`, `tests/integration/`, `docs/`. **Verification**: Create `tests/unit/test_setup.py` that uses Python's `os.path.exists` to assert the existence of directories `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `docs`. Assert the test fails if any are missing.
- [X] T002 [P] Create code skeleton files: `code/config.yaml`, `code/download.py`, `code/preprocess.py`, `code/features.py`, `code/analysis.py`, `code/report.py`, `code/models/__init__.py`. **Verification**: Run a Python script `tests/unit/test_skeleton.py` that uses `os.path.exists` to assert that all listed files in `code/` exist. Assert the test fails if any are missing.
- [X] T003 [P] Create docs skeleton files: `docs/README.md`, `docs/quickstart.md`. **Verification**: Run a Python script `tests/unit/test_docs_skeleton.py` that uses `os.path.exists` to assert that `docs/README.md` and `docs/quickstart.md` exist.
- [X] T004 [P] Initialize Python virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `pyyaml`, `pytest`, `nolds`, `statsmodels`, `psutil`, `pyentropy`. **Verification**: Run `pip list` in the venv and assert all dependencies are installed with pinned versions. **Note**: `pyriemann` has been removed as it was only required for the removed topological metrics (T029), which are now out of scope.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys with exact float values: `filter_low` (float 1.0), `filter_high` (float 40.0), `artifact_threshold_uV` (integer 100), `random_seed` (integer 42), `notch_frequency` (float, default 50.0). **Note**: The `notch_frequency` key is required by FR-002 (line noise) and must be configurable to support datasets with 50 Hz or 60 Hz mains. **Note**: `random_seed` is required by Constitution Principle I (Reproducibility) to ensure deterministic re-runs of the entire pipeline, covering any stochastic elements (e.g., data shuffling, random initialization in statistical models). **Note**: This configuration supports the full pipeline including the VIF diagnostics required by SC-004, which will be calculated in T024.
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Implementation Detail**: Create a logging utility that writes exclusion events to `data/processed/exclusion_log.csv` with columns `[participant_id, reason, timestamp]`. The script MUST write this file to disk on every log entry. **Verification**: Create `tests/unit/test_logging.py` that triggers a log entry and asserts `data/processed/exclusion_log.csv` is created with the correct format and columns. The test MUST verify the file exists in `data/processed/` and not a temporary directory.
- [X] T007 [P] Implement `code/report.py` skeleton with ingestion logic for analysis tables. **Implementation Detail**: Create a minimal `code/report.py` that can read `data/analysis/*.csv` files and render them into a markdown string. This stub must be functional enough for T025 verification but does not need full report generation logic yet. **Verification**: Create `tests/unit/test_report_stub.py` that creates a dummy `data/analysis/sensitivity_table.csv` (mocked for existence only, not logic), runs `code/report.py`, and asserts the output contains the CSV data formatted as a markdown table. The test MUST mock the file existence to avoid dependency on future artifacts.
- [X] T008 [P] Generate `docs/quickstart.md` based on the completed research and design artifacts. **Dependency**: This task must run AFTER `research.md` and `data-model.md` are generated. **Implementation Detail**: The task MUST generate a complete `docs/quickstart.md` file containing: 1. Environment setup instructions (venv creation, requirements install). 2. Data download command (`python code/download.py`). 3. Preprocessing command (`python code/preprocess.py`). 4. Feature extraction command (`python code/features.py`). 5. Analysis command (`python code/analysis.py`). 6. Report generation command (`python code/report.py`). **Verification**: Assert `docs/quickstart.md` exists and contains step-by-step instructions for running the pipeline, matching the commands in `code/`.
- [X] T009 [S] **Data Retrieval, Validation, and Extraction**. Implement `code/download.py` to fetch the public EEG dataset from **HuggingFace** (strictly no fallbacks). **CRITICAL**: The script MUST identify and fetch the specific dataset containing BOTH resting-state EEG AND paired pre/post fatigue ratings. **Dataset ID**: `sleep-fatigue-eeg` (Verified source for this project). **Logic**:
 1. Fetch the FULL dataset from HuggingFace `sleep-fatigue-eeg`.
 2. Validate the presence of `eeg_data` and `fatigue_rating` variables.
 3. Count participants. If N < 30, raise an exception, exit with code 1, and print "Sample size N < 30".
 4. If variables are missing, raise an exception, exit with code 1, and print "Missing required variables: [list]".
 5. **Output 1**: `data/raw/download_manifest.json` (atomic write) listing all participant files.
 6. **Output 2**: `data/processed/fatigue_scores.csv` with columns `participant_id`, `timepoint` (pre/post), `fatigue_score`.
 7. **Output 3**: `data/processed/validation_report.json` with keys `n_participants`, `variables_found`, `status`.
 **Failure Condition**: If any step fails, the script MUST halt with a clear error. **Verification**: 1. Assert the script performs an HTTP HEAD request to the HuggingFace URL before downloading. 2. Verify that `data/raw/download_manifest.json`, `data/processed/fatigue_scores.csv`, and `data/processed/validation_report.json` exist ONLY if the download and validation succeed. 3. Verify that the script halts with a clear error if variables are missing or N < 30.
- [X] T026 [P] **Monitoring Infrastructure (Instrumentation) [SC-002] [SC-003]**. Implement `code/utils/monitor.py` to capture peak RSS and total runtime during pipeline execution. **Implementation Detail**: Use `psutil` for cross-platform memory tracking (`psutil.Process().memory_info().rss`) and `time` for runtime. This module MUST be imported and executed as a wrapper around the main pipeline execution (T009-T025) to capture metrics for the entire run. **Output**: `data/analysis/resource_usage.json` with keys `peak_rss_gb` (float) and `total_runtime_hours` (float). **Verification**: Assert `code/utils/monitor.py` exists and can be imported. Assert it outputs `data/analysis/resource_usage.json` with keys `peak_rss_gb` (float) and `total_runtime_hours` (float).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample EEG file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

- [ ] T012 [US1] [S] [Depends: T009] Implement `code/preprocess.py` to apply a bandpass filter (1-40 Hz) and remove line noise per FR-002. **Implementation Detail**: The script MUST read the full dataset from `data/raw/download_manifest.json` (created by T009). **Verification**:
 1. Generate a synthetic EEG signal (120s, 50Hz noise) within `tests/unit/test_preprocess.py` for deterministic verification.
 2. Run the preprocessing pipeline on this synthetic signal.
 3. Assert that `data/processed/cleaned_eeg_verification.fif` exists after the run.
 4. Compute the PSD of the raw and filtered segments. Assert that the peak power at 50Hz in the filtered signal is at least 20dB lower than the raw signal.
- [ ] T013 [US1] [Depends: T012, T006] Implement **Epoch Rejection** in `code/preprocess.py` to exclude epochs >±100µV per FR-002. **Verification**: Assert `data/processed/exclusion_log.csv` exists and contains valid columns `[participant_id, reason, timestamp]`. If no epochs are rejected, the file should exist but be empty (header only).
- [ ] T014 [US1] [Depends: T012, T006] Implement **Segment Length Validation** in `code/preprocess.py` to exclude segments <120 seconds per FR-002. **Verification**: Assert `data/processed/exclusion_log.csv` exists and contains valid columns `[participant_id, reason, timestamp]`. If no segments are rejected, the file should exist but be empty (header only).
- [X] T015a [US1] [P] [Depends: T012, T013, T014] **Preprocessing Core Function**. Implement `code/preprocess.py` with a pure function `process_segment(raw_data, config)` that applies bandpass filter, notch filter, re-reference, and artifact rejection (±100 µV) to a single segment. **CRITICAL**: This function MUST be stateless and perform **NO FILE I/O**. It must return the processed numpy array and metadata dictionary only. **Verification**: Assert the function returns processed data and metadata without creating any files.
- [ ] T015b [US1] [S] [Depends: T015a] **Full Dataset Preprocessing**. Implement the parallel execution strategy in `code/preprocess.py` to process the entire dataset downloaded in T009. **Implementation Detail**: Iterate through all participants in `data/raw/download_manifest.json`. Use `multiprocessing.Pool` to call the `process_segment` function (from T015a) in parallel. Each worker MUST generate a unique output filename using the pattern `data/processed/cleaned_eeg/{participant_id}_{segment_id}.fif` to prevent race conditions. **Output**: `data/processed/cleaned_eeg/` directory containing per-subject `.fif` files. **Verification**: Assert the output files exist for all N participants (where N >= 30). Assert the exclusion log contains entries for any rejected segments.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments.

- [ ] T016 [US2] [S] [Depends: T015b] Implement `code/features.py` to calculate BOTH Lempel-Ziv complexity AND Permutation Entropy per channel per FR-003. Output to `data/analysis/complexity_metrics.csv`. **Algorithm**: Use median quantization for LZC (via `nolds`). Use embedding dimension=3, delay=1 for PE (via `pyentropy`). **Implementation Detail**: This task MUST be the sole producer of `data/analysis/complexity_metrics.csv`. It must process the FULL dataset (not just the sample) from `data/processed/cleaned_eeg/`. **Verification**: Assert `data/analysis/complexity_metrics.csv` exists and contains columns `participant_id`, `channel`, `segment_id`, `lzc_value`, AND `pe_value`.
- [X] T017 [US2] [Depends: T016] **Feature Verification**. Verify that the calculated LZC and PE fall within mathematically defined ranges. **Verification**: Create `tests/unit/test_features.py` that loads `complexity_metrics.csv` and asserts that all LZC values are < 1.0, all PE values are < 2.585. Log a warning if the spec lacks explicit bounds, but the test MUST assert these mathematical limits.

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

- [X] T018 [US3] [Depends: T009, T015b, T011] Implement `code/analysis.py` validation: Check for existence of processed data files (`data/processed/cleaned_eeg/`, `data/analysis/complexity_metrics.csv`, `data/processed/fatigue_scores.csv`). **CRITICAL**: The system MUST fail if these files are missing, as no analysis can proceed. **Logic**: 1. Check for presence of required files. If missing, print error listing available files and exit with code 1. **Note**: Variable validation and N-count are handled by T009.
- [~] T019 [US3] [Depends: T018] Implement **Delta Calculation** in `code/analysis.py` to compute delta scores (Post - Pre) for both complexity and fatigue. **CRITICAL**: The script MUST verify that the complexity and fatigue data are paired by `participant_id` and that both pre and post segments exist for each participant before calculating deltas. If pairing is incomplete, exit with code 1 and print "Paired data missing". **Implementation Detail**: The script MUST load fatigue scores from `data/processed/fatigue_scores.csv` and complexity metrics from `data/analysis/complexity_metrics.csv`. **Verification**: Assert `data/analysis/delta_scores.csv` is created with correct delta values and that the input data was verified as paired.
- [~] T020a [US3] [S] [Depends: T019] Implement **Raw Correlation Calculation** in `code/analysis.py` for Pearson/Spearman correlation (paired) per FR-004. **Implementation Detail**: Calculate correlations and save the RAW p-values and coefficients to `data/analysis/raw_correlation_results.csv` BEFORE any correction. **Verification**: Assert `data/analysis/raw_correlation_results.csv` exists and contains Pearson/Spearman coefficients and raw p-values. <!-- FAILED: unspecified -->
- [X] T020b [US3] [S] [Depends: T020a] Implement **Benjamini-Hochberg Correction** in `code/analysis.py` for multiple comparisons across electrodes per FR-005. **Implementation Detail**: Use `statsmodels.stats.multitest.multipletests` to apply BH correction to p-values from `raw_correlation_results.csv` (T020a). **Output**: `data/analysis/bh_corrected_pvalues.csv`. **Verification**: Assert `data/analysis/bh_corrected_pvalues.csv` exists and contains corrected p-values for all electrodes.
- [ ] T024 [US3] [S] [Depends: T019, T020a] Implement Collinearity diagnostics (VIF < 5) per SC-004. **Implementation Detail**: Calculate VIF for all available predictors (Fatigue_Delta, Pre_Complexity, and any available covariates: age, time_of_day, medication_status) using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Logic**: 1. Identify which covariate columns exist in the input data. If covariates missing, calculate VIF only on core predictors (Fatigue_Delta, Pre_Complexity) and log a warning. 2. Calculate VIF for the full set of available predictors. 3. **MUST write** `data/analysis/vif_diagnostics.log` with ALL VIF values. 4. **MUST write** `data/analysis/vif_valid_predictors.json` with the list of predictors having VIF < 5. 5. If VIF >= 5 for any predictor, log the failure to `data/analysis/vif_diagnostics.log` with a warning flag AND list the collinear predictors. 6. **DO NOT EXIT**: If any predictor has VIF >= 5, log the violation but **continue** execution. 7. If all predictors pass (VIF < 5), output a list of `valid_predictors` to `data/analysis/vif_valid_predictors.json`. **Verification**: Run the analysis on the combined predictor set and assert that the calculated VIF for each predictor is logged to `vif_diagnostics.log`. Assert that `vif_valid_predictors.json` contains the list of predictors with VIF < 5 (or an empty list if none pass).
- [ ] T021 [US3] [S] [Depends: T024] Implement **ANCOVA Model** in `code/analysis.py` for robustness and confound control per FR-004. **Implementation Detail**: Use `statsmodels` to fit `Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates`. **Logic**: 1. **Check for existence of `data/analysis/vif_valid_predictors.json`**. 2. If this file exists and is NOT empty, load it and use the listed predictors for the ANCOVA model. 3. If this file is missing or empty (indicating VIF >= 5 for all predictors), log a warning "No valid predictors for ANCOVA (VIF >= 5). Skipping ANCOVA." and **skip** the ANCOVA step (do not crash). 4. Load `Pre_Complexity` from `data/analysis/complexity_metrics.csv` (T016) and `Fatigue_Delta` from `data/analysis/delta_scores.csv` (T019). 5. Check if covariate columns (age, time_of_day, medication_status) exist in the input data. If a column is missing, log a warning and exclude it from the model. 6. Use only the predictors validated by T024 (VIF < 5). **Failure Condition**: None. If T024 fails (VIF >= 5), T021 logs a warning and skips. **Verification**: Assert `data/analysis/ancova_results.csv` contains model coefficients and p-values if predictors were valid. Assert that if T024 fails, T021 logs a warning and does not crash.
- [ ] T030 [US3] [S] [Depends: T020a, T029] **Topological Stability Analysis**. IMPLEMENTATION REMOVED: This task is deleted as it relies on T029 (Topological metrics), which is out of scope (FR-003).
- [X] T023 [US3] [Depends: T020a, T020b] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`. **Logic**: The sensitivity analysis MUST be performed on **BOTH** raw p-values (from `raw_correlation_results.csv`) AND BH-corrected p-values (from `bh_corrected_pvalues.csv`). Count the number of electrodes with p < 0.05 and p < 0.01 for both sets. **Output**: `data/analysis/sensitivity_table_raw.csv` and `data/analysis/sensitivity_table_corrected.csv`. **Verification**: Assert both tables exist and contain counts of significant electrodes at both thresholds.
- [X] T025 [US3] [Depends: T020a, T020b, T021, T023, T024] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, and confidence intervals, the sensitivity analysis table, the VIF diagnostics, and the correlation analysis per US‑3, FR-004, and the research review. Output to `docs/final_report.md`. **Scope Note**: This report MUST include all spec-authorized metrics (LZC, PE, Correlation, ANCOVA, BH, VIF, Sensitivity). **Verification**: Assert `docs/final_report.md` contains the required sections: "Correlation Results", "ANCOVA Results", "Sensitivity Analysis", "VIF Diagnostics", and "Correlation Analysis". Assert it cites the correct data files (`raw_correlation_results.csv`, `bh_corrected_pvalues.csv`, `sensitivity_table_raw.csv`, `sensitivity_table_corrected.csv`, `vif_diagnostics.log`, `complexity_metrics.csv`), and includes the sensitivity table, VIF diagnostics, the correlation analysis, and the ANCOVA results.
- [ ] T027 [US3] [Depends: T026] Verify total pipeline memory usage ≤ 7 GB (SC-003, DC-001) using the monitoring infrastructure. **Verification**: Run the full pipeline and assert `data/analysis/resource_usage.json` exists and contains `peak_rss_gb` <= 7.0.
- [ ] T028 [US3] [Depends: T026] Verify total pipeline runtime ≤ 6 hours (SC-002). **Verification**: Run the full pipeline and assert `data/analysis/resource_usage.json` exists and contains `total_runtime_hours` <= 6.0.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
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
 - Developer A: User Story 1 (Data/Preprocessing)
 - Developer B: User Story 2 (Complexity)
 - Developer C: User Story 3 (Analysis/Reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, requires locking or unique filenames
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Note**: Phase 6 (T029-T031) has been PERMANENTLY DELETED. The tasks introducing 'Spectral Slope' and 'Regime Classification' were unauthorized scope creep and have been removed to strictly comply with FR-003 (LZC/PE only).
- **Revision Note**: T010 and T012a have been deleted. T009 now produces `validation_report.json` and `fatigue_scores.csv`. T012 uses synthetic data for verification.
- **Revision Note**: T015 has been atomized into T015a (Pure Function) and T015b (Parallel Orchestrator). T015a is now marked [P] as a stateless function, and T015b handles the sequential iteration and parallel execution logic.
- **Revision Note**: T009 strictly mandates HuggingFace 'sleep-fatigue-eeg' as the single canonical source; no PhysioNet fallbacks are permitted.
- **Revision Note**: T024 guarantees production of `vif_valid_predictors.json` (even if empty) without halting, ensuring T021 dependency is robust and testable.
- **Revision Note**: T023 now performs sensitivity analysis on BOTH raw and BH-corrected p-values to ensure robustness of corrected results.
- **Revision Note**: `pyriemann` removed from requirements as it was only used for deleted topological tasks.