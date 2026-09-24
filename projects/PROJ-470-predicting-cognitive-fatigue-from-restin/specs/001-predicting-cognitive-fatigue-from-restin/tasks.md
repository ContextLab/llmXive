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
- [X] T004 [P] Initialize Python virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `pyyaml`, `pytest`, `nolds`, `statsmodels`, `psutil`, `pyentropy`. **Verification**: Run `pip list` in the venv and assert all dependencies are installed with pinned versions. **Note**: Removed `lempel-ziv-complexity` and `pyriemann` to align with plan's Technical Context (`nolds`, `pyentropy`) and avoid scope creep.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys with exact float values: `filter_low` (float 1.0), `filter_high` (float 40.0), `artifact_threshold_uV` (integer 100), `random_seed` (integer 42), `notch_frequency` (float 50.0). **Note**: The `notch_frequency` key is required by FR-002 (50 Hz notch) and SC-004 (VIF diagnostics). **Note**: `random_seed` is required by Constitution Principle I (Reproducibility) to ensure deterministic re-runs of the entire pipeline, covering any stochastic elements (e.g., data shuffling, random initialization in statistical models). **Note**: This configuration supports the full pipeline including the VIF diagnostics required by SC-004, which will be calculated in T024.
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Implementation Detail**: Create a logging utility that writes exclusion events to `data/processed/exclusion_log.csv` with columns `[participant_id, reason, timestamp]`. The script MUST write this file to disk on every log entry. **Verification**: Create `tests/unit/test_logging.py` that triggers a log entry and asserts `data/processed/exclusion_log.csv` is created with the correct format and columns. The test MUST verify the file exists in `data/processed/` and not a temporary directory.
- [X] T007 [P] Implement `code/report.py` skeleton with ingestion logic for analysis tables. **Implementation Detail**: Create a minimal `code/report.py` that can read `data/analysis/*.csv` files and render them into a markdown string. This stub must be functional enough for T025 verification but does not need full report generation logic yet. **Verification**: Create `tests/unit/test_report_stub.py` that creates a dummy `data/analysis/sensitivity_table.csv` (mocked for existence only, not logic), runs `code/report.py`, and asserts the output contains the CSV data formatted as a markdown table. The test MUST mock the file existence to avoid dependency on future artifacts.
- [X] T008 [P] Generate `docs/quickstart.md` based on the completed research and design artifacts. **Dependency**: This task must run AFTER `research.md` and `data-model.md` are generated. **Implementation Detail**: The task MUST generate a complete `docs/quickstart.md` file containing: 1. Environment setup instructions (venv creation, requirements install). 2. Data download command (`python code/download.py`). 3. Preprocessing command (`python code/preprocess.py`). 4. Feature extraction command (`python code/features.py`). 5. Analysis command (`python code/analysis.py`). 6. Report generation command (`python code/report.py`). **Verification**: Assert `docs/quickstart.md` exists and contains step-by-step instructions for running the pipeline, matching the commands in `code/`.
- [X] T009 [S] Implement `code/download.py` to fetch the full public EEG dataset. **CRITICAL**: The script MUST identify and fetch the 'PhysioNet Sleep-EDF Database Expanded' (or the specific HuggingFace mirror if PhysioNet is unreachable) containing BOTH resting-state EEG AND paired pre/post fatigue ratings. **Logic**: The script MUST fetch the FULL dataset (not a sample) and validate the presence of `eeg_data` and `fatigue_rating` variables. **Failure Condition**: If the dataset lacks these variables, the script MUST raise an exception, exit with code 1, and print a clear error message listing the available variables. **Note**: T009 does NOT perform N-count checks; these are handled by T010. T009 MUST ensure the full dataset is written to `data/raw/` and generates `data/raw/download_manifest.json` listing all participant files on success. **Atomicity**: The script MUST write the manifest to a temporary file first and then use `os.replace` to atomically rename it to `download_manifest.json` to prevent race conditions. **Output Artifact**: `data/raw/download_manifest.json` (only on success). **Verification**: 1. Assert the script performs an HTTP HEAD request to the metadata URL before downloading. 2. Verify that `data/raw/download_manifest.json` exists ONLY if the download succeeds. 3. Verify that the script halts with a clear error if variables are missing.
- [X] T010 [P] **Data Validation Gate (Implementation)**. Implement validation logic to check dataset variables and N count. **CRITICAL**: This task MUST implement the FR-001 requirement to "halt with a clear error message listing the available variables" if the dataset lacks `eeg_data` or `fatigue_rating`. **Logic**: 1. Check for presence of required variables in the downloaded dataset. If missing, print error listing available variables and exit with code 1. 2. Count participants. If N < 30, print error "Sample size N < 30" and exit with code 1. 3. **MUST write** `data/processed/validation_report.json` to disk on success. **Dependency**: Runs after T009 (Download) but BEFORE T018/T019/T021 (Analysis). **Output**: `data/processed/validation_report.json` (on success). **Verification**: 1. Assert that if the dataset lacks variables, the script exits with code 1 and the error message explicitly lists "Available variables: [list]". 2. Assert that if N < 30, the script exits with code 1 and the error message explicitly states "Sample size N < 30". 3. Assert that `data/processed/validation_report.json` is created and contains the validation summary on success.
- [X] T011 [P] **Data Validation Gate (Verification)**. Verify the validation logic halts correctly. **Verification**: Assert that if the dataset lacks variables, the script exits with code 1 and the error message lists the available variables. Assert that if N < 30, the script exits with code 1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample EEG file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

- [X] T012a [S] **Sample File Creation for Verification**. Create a single sample EEG file from the full dataset for T012 verification. **Implementation Detail**: This task MUST read `data/raw/download_manifest.json` (created by T009) and copy the first available subject's data file to `data/raw/sample_eeg_verification.fif`. **Verification**: Assert `data/raw/sample_eeg_verification.fif` exists and is a valid copy of a file listed in the manifest. **Note**: This sample file is for T012 verification ONLY. The full analysis (T018+) uses the full dataset from T009.
- [X] T012 [US1] [Depends: T012a] Implement `code/preprocess.py` to apply a bandpass filter (1-40 Hz) and remove line noise per FR-002. **Implementation Detail**: The script MUST read the sample file path `data/raw/sample_eeg_verification.fif` (created by T012a) for verification. **Verification**:
 1. Run the preprocessing pipeline on the sample file `data/raw/sample_eeg_verification.fif`.
 2. Assert that `data/processed/cleaned_eeg_verification.fif` exists after the run.
 3. Compute the PSD of the raw and filtered segments. Assert that the peak power at 50Hz in the filtered signal is at least 20dB lower than the raw signal.
- [X] T013 [US1] [Depends: T012, T006] Implement **Epoch Rejection** in `code/preprocess.py` to exclude epochs >±100µV per FR-002. **Verification**: Assert `data/processed/exclusion_log.csv` contains entries for rejected epochs with reason "amplitude_threshold".
- [X] T014 [US1] [Depends: T012, T006] Implement **Segment Length Validation** in `code/preprocess.py` to exclude segments <120 seconds per FR-002. **Verification**: Assert `data/processed/exclusion_log.csv` contains entries for rejected segments with reason "segment_too_short".

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments.

- [X] T016 [US2] [S] [Depends: T012] Implement `code/features.py` to calculate BOTH Lempel-Ziv complexity AND Permutation Entropy per channel per FR-003. Output to `data/analysis/complexity_metrics.csv`. **Algorithm**: Use median quantization for LZC (via `nolds`). Use embedding dimension=3, delay=1 for PE (via `pyentropy`). **Implementation Detail**: This task MUST be the sole producer of `data/analysis/complexity_metrics.csv`. It must process the FULL dataset (not just the sample). **Verification**: Assert `data/analysis/complexity_metrics.csv` exists and contains columns `participant_id`, `channel`, `segment_id`, `lzc_value`, AND `pe_value`.
- [X] T017 [US2] [Depends: T016] **Feature Verification**. Verify that the calculated LZC and PE values fall within mathematically defined ranges. **Verification**: Create `tests/unit/test_features.py` that loads `complexity_metrics.csv` and asserts that all LZC values are < 1.0 and all PE values are < 2.585 (log2(6)). Log a warning if the spec lacks explicit bounds, but the test MUST assert these mathematical limits.

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

- [X] T018 [US3] [Depends: T010] Implement `code/analysis.py` validation: Check for existence of processed data files (`data/processed/cleaned_eeg.fif` (full), `data/analysis/complexity_metrics.csv`, `data/processed/fatigue_scores.csv`). **CRITICAL**: The system MUST fail if these files are missing, as no analysis can proceed. **Logic**: 1. Check for presence of required files. If missing, print error listing available files and exit with code 1. **Note**: Variable validation and N-count are handled by T010.
- [X] T019 [US3] [Depends: T018] Implement **Delta Calculation** in `code/analysis.py` to compute delta scores (Post - Pre) for both complexity and fatigue. **CRITICAL**: The script MUST verify that the complexity and fatigue data are paired by `participant_id` and that both pre and post segments exist for each participant before calculating deltas. If pairing is incomplete, exit with code 1 and print "Paired data missing". **Implementation Detail**: The script MUST load fatigue scores from `data/processed/fatigue_scores.csv` and complexity metrics from `data/analysis/complexity_metrics.csv`. **Verification**: Assert `data/analysis/delta_scores.csv` is created with correct delta values and that the input data was verified as paired.
- [X] T020 [US3] [Depends: T019] Implement **Correlation Computation** in `code/analysis.py` for Pearson/Spearman correlation (paired) per FR-004. **Verification**: Assert `data/analysis/correlation_results.csv` contains Pearson/Spearman coefficients and p-values for the validated paired data.
- [X] T024 [US3] [S] [Depends: T019, T020] Implement Collinearity diagnostics (VIF < 5) per SC-004. **Implementation Detail**: Calculate VIF for all available predictors (Fatigue_Delta, Pre_Complexity, and any available covariates: age, time_of_day, medication_status) using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Logic**: 1. Identify which covariate columns exist in the input data. 2. Calculate VIF for the full set of available predictors. 3. If VIF >= 5 for any predictor, log the failure to `data/analysis/vif_diagnostics.log` with a warning flag AND list the collinear predictors. 4. **HARD HALT**: If any predictor has VIF >= 5, the script MUST exit with code 1 and log "Collinearity violation: VIF >= 5 for [predictor_name]. Study invalid per SC-004." 5. If all predictors pass (VIF < 5), output a list of `valid_predictors` to `data/analysis/vif_valid_predictors.json`. **Verification**: Run the analysis on the combined predictor set and assert that the calculated VIF for each predictor is logged. Log the VIF values to `data/analysis/vif_diagnostics.log`. Assert that if any VIF >= 5, the script halts with exit code 1. Assert that `vif_valid_predictors.json` contains the list of predictors with VIF < 5 (only if all pass).
- [X] T021 [US3] [S] [Depends: T024 Success] Implement **ANCOVA Model** in `code/analysis.py` for robustness and confound control per FR-004. **Implementation Detail**: Use `statsmodels` to fit `Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates`. **Logic**: 1. **Check for existence of `data/analysis/vif_valid_predictors.json`**. If this file is missing (indicating T024 failed with VIF >= 5), the script MUST NOT run. **Note**: T021 is conditional on T024 success. If T024 halts the pipeline, T021 is not executed. 2. If the file exists, read it. 3. Load `Pre_Complexity` from `data/analysis/complexity_metrics.csv` (T016) and `Fatigue_Delta` from `data/analysis/delta_scores.csv` (T019). 4. Check if covariate columns (age, time_of_day, medication_status) exist in the input data. If a column is missing, log a warning and exclude it from the model. 5. Use only the predictors validated by T024 (VIF < 5). **Dependency Note**: T021 depends on T016 to ensure `Pre_Complexity` is available from `complexity_metrics.csv`. **Failure Condition**: If `vif_valid_predictors.json` contains an empty list (all predictors failed VIF check), the script MUST halt with exit code 1 and log "No valid predictors for ANCOVA". **Verification**: Assert `data/analysis/ancova_results.csv` contains model coefficients and p-values. Assert that the model used only the predictors listed in `vif_valid_predictors.json`. Assert that if T024 fails, T021 is not executed.
- [X] T022 [US3] [Depends: T020] Implement Benjamini‑Hochberg correction for multiple comparisons across electrodes per FR-005. **Implementation Detail**: Use `statsmodels.stats.multitest.multipletests` to apply BH correction to p-values from T020. **Output**: `data/analysis/bh_corrected_pvalues.csv`. **Verification**: Assert `data/analysis/bh_corrected_pvalues.csv` exists and contains corrected p-values for all electrodes.
- [X] T023 [US3] [Depends: T020] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`. **Logic**: The sensitivity analysis MUST be performed on the **raw p-values** from `correlation_results.csv` (T020), NOT the BH-corrected values. Count the number of electrodes with p < 0.05 and p < 0.01 in the raw results. **Verification**: Assert `data/analysis/sensitivity_table.csv` exists and contains counts of significant electrodes at both thresholds based on raw p-values.
- [X] T025 [US3] [Depends: T020, T021, T022, T023, T024] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, and confidence intervals, the sensitivity analysis table, the VIF diagnostics, and the correlation analysis per US‑3, FR-004, and the research review. Output to `docs/final_report.md`. **Scope Note**: This report MUST include all spec-authorized metrics (LZC, PE, Correlation, ANCOVA, BH, VIF, Sensitivity). **Verification**: Assert `docs/final_report.md` contains the required sections: "Correlation Results", "ANCOVA Results", "Sensitivity Analysis", "VIF Diagnostics", and "Correlation Analysis". Assert it cites the correct data files (`correlation_results.csv`, `bh_corrected_pvalues.csv`, `sensitivity_table.csv`, `vif_diagnostics.log`, `complexity_metrics.csv`), and includes the sensitivity table, VIF diagnostics, the correlation analysis, and the ANCOVA results.
- [X] T026 [P] **Monitoring Infrastructure**. Implement `code/utils/monitor.py` to capture peak RSS and total runtime during pipeline execution. **Implementation Detail**: Use `psutil` for cross-platform memory tracking (`psutil.Process().memory_info().rss`) and `time` for runtime. **Output**: `data/analysis/resource_usage.json` with keys `peak_rss_gb` (float) and `total_runtime_hours` (float). **Verification**: Assert `code/utils/monitor.py` exists and can be imported. Assert it outputs `data/analysis/resource_usage.json` with keys `peak_rss_gb` (float) and `total_runtime_hours` (float).
- [X] T027 [US3] [Depends: T026] Verify total pipeline memory usage ≤ 7 GB (SC-003, DC-001) using the monitoring infrastructure. **Verification**: Run the full pipeline and assert `data/analysis/resource_usage.json` shows `peak_rss_gb` <= 7.0.
- [X] T028 [US3] [Depends: T026] Verify total pipeline runtime ≤ 6 hours (SC-002). **Verification**: Run the full pipeline and assert `data/analysis/resource_usage.json` shows `total_runtime_hours` <= 6.0.

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

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- [S] tasks = sequential, requires locking or unique filenames
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Note**: Task T029 (Topological Discrimination) has been REMOVED as it was unauthorized scope creep not present in spec.md. T024 (VIF) now runs before T021 (ANCOVA) and includes a hard fail condition for VIF >= 5, with T021 explicitly handling the skip case (by not running if T024 halts). T023 now uses raw p-values for sensitivity analysis. T009 now implements FR-001 variable validation logic (no hardcoded ID) and uses a specific PhysioNet dataset. T026 is completed with `psutil`. T017 now uses mathematically defined bounds (PE < 2.585). T021 now handles empty predictor lists and T024 failure gracefully (by not running). T012 now reads sample path from T012a. T019 explicitly references `data/processed/fatigue_scores.csv`. The final report (T025) now strictly covers spec-authorized metrics. T004 uses `nolds` and `pyentropy`. T006, T010, and T016 now explicitly mandate writing their output artifacts to disk. T009 and T012a are separated to ensure full dataset download vs sample verification.