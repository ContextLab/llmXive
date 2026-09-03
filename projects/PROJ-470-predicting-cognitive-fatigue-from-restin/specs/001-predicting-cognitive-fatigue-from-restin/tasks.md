# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `/specs/001-cognitive-fatigue-from-restin/`
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

- [X] T001 [P] Create project directory structure: `projects/PROJ-470-predicting-cognitive-fatigue-from-restin/`, `data/raw/`, `data/processed/`, `code/`, `tests/unit/`, `tests/integration/`, `docs/`. **Verification**: Create `tests/unit/test_setup.py` that uses Python's `os.path.exists` to assert the existence of directories `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `docs`. Assert the test fails if any are missing.
- [X] T002 [P] Create code skeleton files: `code/config.yaml`, `code/download.py`, `code/preprocess.py`, `code/features.py`, `code/analysis.py`, `code/report.py`, `code/models/__init__.py`. **Verification**: Run a Python script `tests/unit/test_skeleton.py` that uses `os.path.exists` to assert that all listed files in `code/` exist. Assert the test fails if any are missing.
- [X] T003 [P] Create docs skeleton files: `docs/README.md`, `docs/quickstart.md`. **Verification**: Run a Python script `tests/unit/test_docs_skeleton.py` that uses `os.path.exists` to assert that `docs/README.md` and `docs/quickstart.md` exist.
- [X] T004 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `lempel-ziv-complexity`, `scipy`, `pyyaml`, `pytest`, `nolds`, `statsmodels`. **Verification**: Run `pip list` in the venv and assert all dependencies are installed with pinned versions.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys: `filter_low` (value 1), `filter_high` (value 40), `artifact_threshold_uV` (value 100), `random_seed` (integer), `notch_frequency` (value 50). **Note**: The `notch_frequency` key is required by FR-002 (50 Hz notch) and SC-004 (VIF diagnostics). **Note**: `random_seed` is required by Constitution Principle I (Reproducibility) to ensure deterministic re-runs of the entire pipeline, covering any stochastic elements (e.g., data shuffling, random initialization in statistical models). **Note**: This configuration supports the full pipeline including the VIF diagnostics required by SC-004, which will be calculated in T024.
- [ ] T006 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Implementation Detail**: Create a logging utility that writes exclusion events to `data/processed/exclusion_log.csv` with columns `[participant_id, reason, timestamp]`. **Verification**: Create `tests/unit/test_logging.py` that triggers a log entry and asserts `data/processed/exclusion_log.csv` is created with the correct format and columns. The test MUST verify the file exists in `data/processed/` and not a temporary directory.
- [X] T007 [P] Implement `code/report.py` skeleton with ingestion logic for analysis tables. **Implementation Detail**: Create a minimal `code/report.py` that can read `data/analysis/*.csv` files and render them into a markdown string. This stub must be functional enough for T025 verification but does not need full report generation logic yet. **Verification**: Create `tests/unit/test_report_stub.py` that creates a dummy `data/analysis/sensitivity_table.csv` (mocked for existence only, not logic), runs `code/report.py`, and asserts the output contains the CSV data formatted as a markdown table. The test MUST mock the file existence to avoid dependency on future artifacts.
- [X] T008 [P] Generate `docs/quickstart.md` based on the completed research and design artifacts. **Dependency**: This task must run AFTER `research.md` and `data-model.md` are generated. **Implementation Detail**: The task MUST generate a complete `docs/quickstart.md` file containing: 1. Environment setup instructions (venv creation, requirements install). 2. Data download command (`python code/download.py`). 3. Preprocessing command (`python code/preprocess.py`). 4. Feature extraction command (`python code/features.py`). 5. Analysis command (`python code/analysis.py`). 6. Report generation command (`python code/report.py`). **Verification**: Assert `docs/quickstart.md` exists and contains step-by-step instructions for running the pipeline, matching the commands in `code/`.
- [ ] T009 [P] Implement `code/download.py` to fetch a public EEG dataset. **CRITICAL**: The script MUST identify a valid dataset containing BOTH resting-state EEG AND paired pre/post fatigue ratings from a sustained attention task (e.g., PVT, Stroop) per FR-001. **Logic**: The script MUST search the HuggingFace Hub for datasets tagged with 'eeg' and 'fatigue'. If a dataset is found, download it. If no dataset is found, the script MUST exit with code 1 and print a clear error message listing the search terms used and the available datasets. **Validation Logic**: T009 does NOT perform variable validation or N-count checks; these are handled by T010. T009 MUST ensure the file is written to `data/raw/` and generates `data/raw/download_manifest.json` on success. **Sample Prep**: Upon successful download, the script MUST copy or symlink the first available subject's data file to `data/raw/sample_eeg.fif` for testing purposes. **Failure Condition**: If the download fails or no dataset is found, raise an exception. **Output Artifact**: `data/raw/download_manifest.json` (only on success) and `data/raw/sample_eeg.fif` (for testing). **Verification**: 1. Assert the script performs an HTTP HEAD request to the metadata URL before downloading. 2. Verify that `data/raw/download_manifest.json` exists ONLY if the download succeeds. 3. Verify that `data/raw/sample_eeg.fif` exists after a successful download. 4. Verify that the script does NOT exit with code 1 for variable mismatches (that is T010's job).
- [X] T010 [P] **Data Validation Gate (Implementation)**. Implement validation logic to check dataset variables and N count. **CRITICAL**: This task MUST implement the FR-001 requirement to "halt with a clear error message listing the available variables" if the dataset lacks `eeg_data` or `fatigue_rating`. **Logic**: 1. Check for presence of required variables in the downloaded dataset (e.g., `.mat`, `.csv`, or `.fif` metadata). If missing, print error listing available variables and exit with code 1. 2. Count participants. If N < 30, print error listing available variables and exit with code 1. **Dependency**: Runs after T009 (Download) but BEFORE T019/T020 (Analysis). **Output**: `data/processed/validation_report.json` (on success).
- [X] T011 [P] **Data Validation Gate (Verification)**. Verify the validation logic halts correctly. **Verification**: Assert that if the dataset lacks variables, the script exits with code 1 and the error message lists the available variables. Assert that if N < 30, the script exits with code 1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample EEG file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

- [X] T012 [US1] [Depends: T009] Implement `code/preprocess.py` to apply a bandpass filter (1-40 Hz) and remove line noise per FR-002. **Verification**:
 1. Check if `data/processed/cleaned_eeg.fif` exists. If not, the test MUST fail with a `FileNotFoundError`.
 2. Run the preprocessing pipeline on `data/raw/sample_eeg.fif` (created by T009). Compute the PSD of the raw and filtered segments. Assert that the peak power at 50Hz in the filtered signal is at least 20dB lower than the raw signal.
- [ ] T013 [US1] [Depends: T012, T006] Implement **Epoch Rejection** in `code/preprocess.py` to exclude epochs >±100µV per FR-002. **Verification**: Assert `data/processed/exclusion_log.csv` contains entries for rejected epochs with reason "amplitude_threshold". <!-- FAILED: unspecified -->
- [ ] T014 [US1] [Depends: T012, T006] Implement **Segment Length Validation** in `code/preprocess.py` to exclude segments <120 seconds per FR-002. **Verification**: Assert `data/processed/exclusion_log.csv` contains entries for rejected segments with reason "segment_too_short".

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments.

- [ ] T016 [US2] [Depends: T012] Implement `code/features.py` to calculate Lempel-Ziv complexity per channel per FR-003. Output to `data/analysis/complexity_metrics.csv`. **Algorithm**: Use median quantization. **Verification**: Assert `data/analysis/complexity_metrics.csv` exists and contains columns `participant_id`, `channel`, `segment_id`, `lzc_value`. **Note**: This task must NOT include Hurst exponent, DFA, or any other topological metrics.
- [ ] T017 [US2] [Depends: T012] Implement `code/features.py` to calculate Permutation Entropy per channel per FR-003. Output to `data/analysis/complexity_metrics.csv` (merged with LZC). **Algorithm**: Use embedding dimension=3, delay=1. **Verification**: Assert `data/analysis/complexity_metrics.csv` contains columns `participant_id`, `channel`, `segment_id`, `pe_value`. **Note**: This task must NOT include Hurst exponent, DFA, or any other topological metrics.

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

- [ ] T018 [US3] [Depends: T010] Implement `code/analysis.py` validation: Check for columns representing paired pre/post fatigue ratings. **CRITICAL**: The system MUST fail if paired data is missing, as NO cross-sectional fallback is permitted per FR-004. **Logic**: 1. Check for presence of required variables. If missing, print error listing available variables and exit with code 1. 2. Count participants. If N < 30, print error listing available variables and exit with code 1. **Note**: The error message must explicitly state "Paired data missing" if the pre/post pairing is incomplete.
- [ ] T019 [US3] [Depends: T018] Implement **Delta Calculation** in `code/analysis.py` to compute delta scores (Post - Pre) for both complexity and fatigue. **Verification**: Assert `data/analysis/delta_scores.csv` is created with correct delta values.
- [ ] T020 [US3] [Depends: T019] Implement **Correlation Computation** in `code/analysis.py` for Pearson/Spearman correlation (paired) per FR-004. **Verification**: Assert `data/analysis/correlation_results.csv` contains Pearson/Spearman coefficients and p-values.
- [ ] T021 [US3] [Depends: T020] Implement **ANCOVA Model** in `code/analysis.py` for robustness and confound control per FR-004. **Implementation Detail**: Use `statsmodels` to fit `Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates`. **Verification**: Assert `data/analysis/ancova_results.csv` contains model coefficients and p-values.
- [ ] T022 [US3] [Depends: T020] Implement Benjamini‑Hochberg correction for multiple comparisons across electrodes per FR-005. **Implementation Detail**: Use `statsmodels.stats.multitest.multipletests` to apply BH correction to p-values from T020. **Output**: `data/analysis/bh_corrected_pvalues.csv`. **Verification**: Assert `data/analysis/bh_corrected_pvalues.csv` exists and contains corrected p-values for all electrodes.
- [ ] T023 [US3] [Depends: T022] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`. **Logic**: The sensitivity analysis MUST be performed on the BH-corrected p-values from `bh_corrected_pvalues.csv`. **Verification**: Assert `data/analysis/sensitivity_table.csv` exists and contains counts of significant electrodes at both thresholds.
- [ ] T024 [US3] [Depends: T021, T020] Implement Collinearity diagnostics (VIF < 5) per SC-004. **Implementation Detail**: Calculate VIF for all predictors (Fatigue_Delta, Pre_Complexity, Covariates) used in the ANCOVA model (T021) using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Logic**: If VIF >= 5 for any predictor, the script MUST exit with code 1 and log the failure to `data/analysis/vif_diagnostics.log`. **Verification**: Run the analysis on the combined predictor set and assert that the calculated VIF for each predictor is < 5. Log the VIF values to `data/analysis/vif_diagnostics.log`.
- [ ] T025 [US3] [Depends: T020, T021, T022, T023, T024] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, and confidence intervals., the sensitivity analysis table, and the VIF diagnostics per US‑3 and FR-004. Output to `docs/final_report.md`. **Scope Note**: This report MUST include all spec-authorized metrics (LZC, PE, Correlation, ANCOVA, BH, VIF, Sensitivity) and MUST NOT include any topological interpretation or stability metrics. **Verification**: Assert `docs/final_report.md` contains the required sections: "Correlation Results", "ANCOVA Results", "Sensitivity Analysis", "VIF Diagnostics". Assert it cites the correct data files (`correlation_results.csv`, `bh_corrected_pvalues.csv`, `sensitivity_table.csv`, `vif_diagnostics.log`), and includes the sensitivity table and VIF diagnostics. **Note**: The verification MUST NOT check for a "Complexity Interpretation" section distinguishing adaptive vs. degenerative patterns, as this contradicts the Scope Note.
- [ ] T026 [P] **Monitoring Infrastructure**. Implement `code/utils/monitor.py` to capture peak RSS and total runtime during pipeline execution. **Verification**: Assert `code/utils/monitor.py` exists and can be imported. Assert it outputs `data/analysis/resource_usage.json` with keys `peak_rss_gb` (float) and `total_runtime_hours` (float).
- [ ] T027 [US3] [Depends: T026] Verify total pipeline memory usage ≤ 7 GB (SC-003, DC-001) using the monitoring infrastructure. **Verification**: Run the full pipeline and assert `data/analysis/resource_usage.json` shows `peak_rss_gb` <= 7.0.
- [ ] T028 [US3] [Depends: T026] Verify total pipeline runtime ≤ 6 hours (SC-002). **Verification**: Run the full pipeline and assert `data/analysis/resource_usage.json` shows `total_runtime_hours` <= 6.0.
