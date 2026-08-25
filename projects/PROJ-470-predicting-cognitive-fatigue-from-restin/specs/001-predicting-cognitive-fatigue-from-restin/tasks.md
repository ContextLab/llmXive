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
- [X] T008 [P] Create integration test file: `tests/integration/test_preprocess.py`.   **Verification**: Assert that the file exists.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys: `filter_low` (value 1), `filter_high` (value 40), `artifact_threshold_uV` (value 100), `random_seed` (integer), `notch_frequency` (value 50). **Note**: This configuration supports the full pipeline including the VIF diagnostics required by SC-004, which will be calculated in T037/T038.
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Verification**: Create `tests/unit/test_logging.py` that triggers a log entry and asserts `logs/exclusion_log.csv` is created with the correct format.
- [X] T007 [P] Implement `code/report.py` skeleton with ingestion logic for analysis tables. **Implementation Detail**: Create a minimal `code/report.py` that can read `data/analysis/*.csv` files and render them into a markdown string. This stub must be functional enough for T021 verification but does not need full report generation logic yet. **Verification**: Create `tests/unit/test_report_stub.py` that creates a dummy `data/analysis/sensitivity_table.csv`, runs `code/report.py`, and asserts the output contains the CSV data formatted as a markdown table.
- [X] T029a [P] Generate `docs/quickstart.md` based on the completed research and design artifacts. **Dependency**: This task must run AFTER `research.md` and `data-model.md` are generated.  **Implementation Detail**: The task MUST generate a complete `docs/quickstart.md` file containing: 1. Environment setup instructions (venv creation, requirements install). 2. Data download command (`python code/download.py`). 3. Preprocessing command (`python code/preprocess.py`). 4. Feature extraction command (`python code/features.py`). 5. Analysis command (`python code/analysis.py`). 6. Report generation command (`python code/report.py`). **Verification**: Assert `docs/quickstart.md` exists and contains step-by-step instructions for running the pipeline, matching the commands in `code/`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample EEG file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] Unit test for bandpass filter attenuation in `tests/unit/test_preprocess.py`. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_bandpass_attenuation` and assert it fails initially, then passes after implementation.
- [X] T009 [P] Integration test for data download and checksum verification in `tests/integration/test_download.py`. **Verification**: Run `pytest tests/integration/test_download.py` and assert it fails initially, then passes after implementation.
- [X] T027a [P] Unit test for missing data edge case in `tests/unit/test_preprocess.py::test_missing_data`. **Implementation Detail**: Create a test that attempts to load a non-existent file path (e.g., `data/raw/nonexistent.fif`) and asserts that `code/preprocess.py` raises a `FileNotFoundError` with a clear message. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_missing_data` and assert that the preprocessing script raises a clear error when a required EEG file is absent.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download.py` to fetch a public EEG dataset. **Target Dataset**: PhysioNet Sleep-EDF (ID: `sleep-edf`). **Metadata URL**: https://physionet.org/files/sleep-edf/1.0.0/. **CRITICAL**: The script MUST identify a valid dataset and validate the presence of both resting-state EEG and paired pre/post fatigue ratings per FR-001 BEFORE downloading the full dataset. If the dataset lacks the required variables, the script MUST halt with a clear error message listing available variables. **Output Artifact (Failure)**: The script MUST exit with code 1 and print a clear error message. **NO** specific JSON/CSV artifacts are required on failure; the error message is sufficient. **Output Artifact (Success)**: The script MUST write `data/raw/download_manifest.json` and `data/processed/participant_exclusion_log.csv` only upon successful validation and download. **Verification**:
 1. Assert the script performs an HTTP HEAD request to the metadata URL before downloading.
 2. Verify that the script exits with code 1 and produces a clear error message if structural validation fails.
 3. Verify that `data/raw/download_manifest.json` exists ONLY if the download succeeds.
 4. Verify that `data/processed/participant_exclusion_log.csv` exists ONLY if the download succeeds.

- [ ] T011 [US1] [Depends: T010] Implement `code/preprocess.py` to apply a bandpass filter (1-40 Hz) and remove line noise per FR-002. **Verification**:
 1. Check if `data/processed/cleaned_eeg.fif` exists. If not, the test MUST fail with a `FileNotFoundError`.
 2. Run the preprocessing pipeline on a single sample EEG file from the real dataset. Compute the PSD of the raw and filtered segments. Assert that the peak power at 50Hz in the filtered signal is at least 20dB lower than the raw signal.

- [ ] T012 [US1] [Depends: T011] Implement artifact rejection logic in `code/preprocess.py` to exclude epochs >±100µV and segments <120 seconds per FR-002. Log exclusion counts and reasons to `logs/exclusion_log.csv`. **Verification**: Assert `logs/exclusion_log.csv` exists and contains columns `[participant_id, reason, timestamp]`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] Unit test for LZC calculation on known signal in `tests/unit/test_features.py`.
- [X] T014 [P] Unit test for permutation entropy on known signal in `tests/unit/test_features.py`.

### Implementation for User Story 2

- [ ] T015 [US2] [Depends: T011] Implement `code/features.py` to calculate Lempel-Ziv complexity per channel per FR-003. Output to `data/processed/lzc_metrics.csv`.
- [ ] T016 [US2] [Depends: T011] Implement `code/features.py` to calculate Permutation Entropy per channel per FR-003. Output to `data/processed/pe_metrics.csv`.

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] Unit test for Benjamini‑Hochberg correction implementation in `tests/unit/test_analysis.py`.
- [X] T018 [P] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis.py`.

### Implementation for User Story 3

- [ ] T019 [US3] [Depends: T010] Implement `code/analysis.py` validation: Check for columns representing paired pre/post fatigue ratings. **CRITICAL**: The system MUST fail if paired data is missing, as NO cross-sectional fallback is permitted per FR-004. The script MUST exit with code 1 and log a clear error message if the required variables are missing. Do NOT implement any logic for single-timepoint data.
- [ ] T020 [US3] [Depends: T019] Implement `code/analysis.py` for Pearson/Spearman correlation (paired) per FR-004. Calculate delta scores (Post - Pre) for both complexity and fatigue.
- [ ] T021 [P] Implement Benjamini‑Hochberg correction for multiple comparisons across electrodes per FR-005.
- [ ] T022 [P] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`.
- [ ] T023 [US3] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, confidence intervals, and the sensitivity analysis table per US‑3 and FR-004. Output to `docs/final_report.md`. **Scope Note**: This report MUST NOT include any topological interpretation or stability metrics; those are OFF-SCOPE.
- [ ] T026a [US3] [Depends: T015, T016] Enforce N ≥ 30 constraint as a blocking gate before analysis.
- [ ] T027 [P] Verify total pipeline memory usage ≤ 7 GB (SC-003, DC-001) using lightweight monitoring. **Verification**: Run the full pipeline and measure peak RSS.
- [ ] T036 [US3] [Depends: T026a, T019, T020, T021, T022, T023, T027] Verify total pipeline runtime ≤ 6 hours (SC-002).
- [ ] T037 [P] Implement VIF calculations for collinearity diagnostics.
- [ ] T038 [P] Implement Collinearity diagnostics (VIF < 5) per SC-004. **Verification**: Run the analysis on the combined predictor set and assert that the calculated VIF for each predictor is < 5. Log the VIF values to `data/analysis/vif_diagnostics.csv`. If any VIF >= 5, the script must log a warning and proceed, but the report must explicitly state the collinearity issue.

**Note**: Tasks T040, T041, and T042 have been REMOVED. The "Topological Stability Metrics" and "Topological Interpretation" functionality is OFF-SCOPE for this project as it is not mandated by FR-003 (which specifies only Lempel-Ziv and Permutation Entropy) and constitutes unauthorized scope creep.