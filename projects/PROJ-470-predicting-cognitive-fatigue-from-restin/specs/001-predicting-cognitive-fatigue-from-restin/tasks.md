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
- [X] T004 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `lempel-ziv-complexity`, `scipy`, `pyyaml`, `pytest`, `nolds`, `pyRly`. **Verification**: Run `pip list` in the venv and assert all dependencies are installed with pinned versions.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys: `filter_low` (value 1), `filter_high` (value 40), `artifact_threshold_uV` (value 100), `random_seed` (integer), `notch_frequency` (value 50). **Note**: The `topology_embedding_dim` and `n_threshold` keys have been removed. `n_threshold` is a Success Criterion enforced by T026a, not a config parameter.
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Verification**: Create `tests/unit/test_logging.py` that triggers a log entry and asserts `logs/exclusion_log.csv` is created with the correct format.
- [X] T007 [P] Implement `code/report.py` skeleton with ingestion logic for analysis tables. **Implementation Detail**: Create a minimal `code/report.py` that can read `data/analysis/*.csv` files and render them into a markdown string. This stub must be functional enough for T021 verification but does not need full report generation logic yet. **Verification**: Create `tests/unit/test_report_stub.py` that creates a dummy `data/analysis/sensitivity_table.csv`, runs `code/report.py`, and asserts the output contains the CSV data formatted as a markdown table.
- [X] T029a [P] [Depends: Research/Design Phase Output] Generate `docs/quickstart.md` based on the completed research and design artifacts. **Dependency**: This task must run AFTER `research.md` and `data-model.md` are generated. **Implementation Detail**: The task MUST generate a complete `docs/quickstart.md` file containing: 1. Environment setup instructions (venv creation, requirements install). 2. Data download command (`python code/download.py`). 3. Preprocessing command (`python code/preprocess.py`). 4. Feature extraction command (`python code/features.py`). 5. Analysis command (`python code/analysis.py`). 6. Report generation command (`python code/report.py`). **Verification**: Assert `docs/quickstart.md` exists and contains step-by-step instructions for running the pipeline, matching the commands in `code/`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample EEG file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T008 [P] [US1] Unit test for bandpass filter attenuation in `tests/unit/test_preprocess.py`. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_bandpass_attenuation` and assert it fails initially, then passes after implementation.
- [X] T009 [P] [US1] Integration test for data download and checksum verification in `tests/integration/test_download.py`. **Verification**: Run `pytest tests/integration/test_download.py` and assert it fails initially, then passes after implementation.
- [X] T027a [P] [US1] Unit test for missing data edge case in `tests/unit/test_preprocess.py::test_missing_data`. **Implementation Detail**: Create a test that attempts to load a non-existent file path (e.g., `data/raw/nonexistent.fif`) and asserts that `code/preprocess.py` raises a `FileNotFoundError` with a clear message. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_missing_data` and assert that the preprocessing script raises a clear error when a required EEG file is absent.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download.py` to fetch a public EEG dataset. **Target Dataset**: PhysioNet Sleep-EDF (ID: `sleep-edf`). **Metadata URL**: `. **CRITICAL**: The script MUST validate the presence of both resting-state EEG and paired pre/post fatigue ratings per FR-001 BEFORE downloading the full dataset. **Implementation Detail**: The script MUST perform an HTTP HEAD request or a partial read of the metadata file at the specified URL. The script MUST check for ANY of the following column name variations for pre/post fatigue ratings: `pre_fatigue`, `fatigue_pre`, `baseline_fatigue`, `post_fatigue`, `fatigue_post`, `end_fatigue`. The script MUST identify missing values as `NaN`, empty string, or 'N/A'. **Structural Validation**: If the dataset *structurally* lacks the required variables (i.e., the columns are missing entirely from the metadata file), the script MUST exit with code 1 (halt) and print a clear error message to stderr listing available variables. **Participant Validation**: If the dataset structure is valid but specific participants have missing ratings, the script MUST identify these, exclude them, log the count, and proceed to download only the valid subset. **Output Artifact (Failure)**: The script MUST exit with code 1. **Output Artifact (Success)**: The script MUST write `data/raw/download_manifest.json` with schema: `{ "status": "success", "dataset_id": "sleep-edf", "participant_count": int, "variables_found": list, "timestamp": str }` AND `data/processed/participant_exclusion_log.csv` with schema: `[participant_id, reason, timestamp]`. **Verification**:
 1. Assert the script performs an HTTP HEAD request to the metadata URL before downloading.
 2. Verify that the script exits with code 1 and produces a clear error message if structural validation fails.
 3. Verify that `data/raw/download_manifest.json` exists and contains the correct schema when validation succeeds.
 4. Verify that `data/processed/participant_exclusion_log.csv` exists and contains the correct schema when participants are excluded.
 5. Verify that the script correctly distinguishes between structural failure (halt) and participant exclusion (log & continue).

- [ ] T011 [US1] [Depends: T010] Implement `code/preprocess.py` to apply a bandpass filter (1-40 Hz) and remove line noise per FR-002 and Constitution Principle VI. **Justification**: Line noise removal is a mandatory step per Constitution Principle VI and FR-002. **CRITICAL**: The script MUST apply a notch filter to remove line noise. [UNRESOLVED-CLAIM: c_9685947a — status=not_enough_info] The notch frequency MUST be read from `code/config.yaml` (default value set to 50 Hz). Output preprocessed data to `data/processed/cleaned_eeg.fif`. **Implementation Detail**: For synthetic testing, generate a signal with a standard sampling rate, consisting of a sine wave (frequency within a representative range, amplitude 1.0) plus white noise (standard deviation 0.1). **Verification**:
 1. **Synthetic Unit Test**: Run `tests/integration/test_preprocess.py::test_line_noise_attenuation` which generates the synthetic test signal described above (256 Hz, amplitude 1.0, noise_std 0.1). The test MUST run the preprocessing pipeline on this synthetic signal and compute the Power Spectral Density (PSD) using `scipy.signal.welch`. Assert that the peak power at 50Hz in the filtered signal is at least 20dB lower than the peak power at 50Hz in the raw synthetic signal. [UNRESOLVED-CLAIM: c_3daa54b7 — status=refuted]
 2. **Config Verification**: Assert that the `notch_frequency` used in the filter matches the value read from `code/config.yaml` (e.g., if config is set to 60Hz, the test signal must use 60Hz and show attenuation at 60Hz).
 3. **Real Data Integration Test**: Check if `data/processed/cleaned_eeg.fif` exists (produced by T010). If not, the test MUST fail with a clear error message "Input file `data/processed/cleaned_eeg.fif` not found. Ensure T010 completed successfully." If the file exists, run the preprocessing pipeline on a single sample EEG file from the real dataset. Compute the PSD of the raw and filtered segments. Assert that the peak power at the configured frequency in the filtered signal is at least 20dB lower than the raw signal. Both tests must pass.

- [X] T012 [US1] Implement artifact rejection logic in `code/preprocess.py` to exclude epochs >±100µV and segments <120 seconds per FR-002 and Edge Cases. Log exclusion counts and reasons to `logs/exclusion_log.csv`. **Verification**: Assert `logs/exclusion_log.csv` exists and contains columns `[participant_id, reason, timestamp]`. Additionally, assert that the `reason` column contains valid rejection reasons (e.g., 'amplitude > 100uV', 'segment < 120s').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments, ensuring reproducibility and correct artifact generation.

**Independent Test**: Run complexity calculation on a synthetic signal with known properties; verify output values fall within expected ranges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US2] Unit test for LZC calculation on known signal in `tests/unit/test_features.py`. **Verification**: Run `pytest tests/unit/test_features.py::test_lzc_known_signal` with a synthetic white noise signal (seed=42, amplitude=1, 256 Hz, 120s). Assert the output is a valid numeric float, positive, and not NaN.
- [X] T014 [P] [US2] Unit test for permutation entropy on known signal in `tests/unit/test_features.py`. **Implementation Detail**: Generate a synthetic white noise signal (seed=42, amplitude=1, 256 Hz, 120s, embedding dimension=3, time delay=1). Calculate permutation entropy. Assert the output is a valid numeric float, positive, and within the theoretical range (0 to log2(n!)) for the embedding dimension. **Verification**: Run `pytest tests/unit/test_features.py::test_pe_known_signal` and assert the output is a valid numeric float, positive, and not NaN.
- [X] T037 [US2] [P] Write unit and integration tests for Permutation Entropy calculation in `tests/unit/test_features.py` and `tests/integration/test_features.py`. **Verification**: Run `pytest tests/unit/test_features.py::test_pe_known_signal` and `tests/integration/test_features.py::test_pe_integration` and assert they pass.

### Implementation for User Story 2

- [ ] T015 [US2] [Depends: T011] Implement `code/features.py` to calculate Lempel‑Ziv complexity per channel per FR-003. Output to `data/processed/lzc_metrics.csv`. **Schema**: `participant_id` (str), `channel` (str), `lzc_value` (float64). **Implementation Detail**: The script MUST iterate over each participant in the preprocessed data (from `data/processed/cleaned_eeg.fif`), then over each channel, and calculate the LZC value. It MUST write each result to the CSV file. The sampling rate MUST be read from the preprocessed data file or config (default value unspecified). **Output Format**: Output a CSV file with a header row. **Verification**:
 1. Check if `data/processed/cleaned_eeg.fif` exists. If not, the test MUST fail with a `FileNotFoundError` and message "Input file `data/processed/cleaned_eeg.fif` not found. Ensure T011 completed successfully."
 2. If file exists, run the feature extraction.
 3. Check if `data/processed/lzc_metrics.csv` exists.
 4. Count unique `participant_id` entries. If count < 30, SKIP the integration test, log a warning "Insufficient sample size: N < 30", and do NOT fail. Do NOT use synthetic data for integration verification. However, for unit-level logic verification, synthetic data is permitted if real data is insufficient.
 5. If N ≥ 30, assert the output contains data for N ≥ 30 participants, contains valid numeric floats, positive values, and the correct column order (`participant_id`, `channel`, `lzc_value`). Synthetic data is NOT allowed to substitute for real data in integration tests.

- [ ] T016 [US2] [Depends: T011] Implement `code/features.py` to calculate Permutation Entropy per channel per FR-003. Output to `data/processed/pe_metrics.csv`. **Schema**: `participant_id` (str), `channel` (str), `pe_value` (float64). **Implementation Detail**: The script MUST iterate over each participant in the preprocessed data (from `data/processed/cleaned_eeg.fif`), then over each channel, and calculate the PE value. It MUST write each result to the CSV file. The sampling rate MUST be read from the preprocessed data file or config (default 256 Hz). [UNRESOLVED-CLAIM: c_d780506c — status=not_enough_info] **Output Format**: Output a CSV file with a header row. **Verification**:
 1. Check if `data/processed/cleaned_eeg.fif` exists. If not, the test MUST fail with a `FileNotFoundError` and message "Input file `data/processed/cleaned_eeg.fif` not found. Ensure T011 completed successfully."
 2. If file exists, run the feature extraction.
 3. Check if `data/processed/pe_metrics.csv` exists.
 4. Count unique `participant_id` entries. If count < 30, SKIP the integration test, log a warning "Insufficient sample size: N < 30", and do NOT fail. Do NOT use synthetic data for integration verification. However, for unit-level logic verification, synthetic data is permitted if real data is insufficient.
 5. If N ≥ 30, assert the output contains data for N ≥ 30 participants, contains valid numeric floats, positive values, and the correct column order (`participant_id`, `channel`, `pe_value`). Synthetic data is NOT allowed to substitute for real data in integration tests.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

**Independent Test**: Run analysis on mock dataset with known correlation values; verify reported p‑values and coefficients match mock truth.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US3] Unit test for Benjamini‑Hochberg correction implementation in `tests/unit/test_analysis.py`.
- [X] T018 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis.py`.
- [X] T027b [P] [US3] Unit test for analysis mode failure in `tests/unit/test_analysis.py::test_analysis_mode_failure`. **Implementation Detail**: Create a mock dataset with neither paired pre/post fatigue ratings nor baseline fatigue ratings. Run `code/analysis.py` and assert it exits with code 1 and writes `validation_report.json` with an informative error message. **Verification**: Run `pytest tests/unit/test_analysis.py::test_analysis_mode_failure` and assert that `code/analysis.py` exits with an informative error when neither paired nor baseline data are available.

### Implementation for User Story 3

- [ ] T019 [US3] [Depends: T010] Implement `code/analysis.py` validation: Check for columns representing paired pre/post fatigue ratings in the metadata dataframe. **CRITICAL**: The script MUST check for column names: `pre_fatigue`, `post_fatigue`, `fatigue_pre`, `fatigue_post`.
 - **Case A (Paired Data)**: If paired data exists, proceed to paired analysis. The primary statistical output MUST be Pearson or Spearman correlation between complexity changes (delta) and fatigue delta scores, as mandated by spec.md FR-004. The analysis MUST frame findings as associational rather than causal. [UNRESOLVED-CLAIM: c_19fadfb3 — status=not_enough_info]
 - **Case B (Cross-Sectional Fallback)**: If the dataset structure lacks the paired variables entirely, the script MUST pivot to a cross-sectional analysis (Baseline Complexity vs. Baseline Fatigue) as described in plan.md Summary. [UNRESOLVED-CLAIM: c_839b3a4e — status=not_enough_info]
 - **HALT LOGIC**: If the dataset structure lacks the required variables for BOTH paired and cross-sectional analysis, the script MUST exit with code 1 and log `validation_report.json` with error details: "ERROR: Dataset lacks required fatigue variables per FR-001/FR-004. Available variables: [list]." If the dataset structure is valid but specific participants are missing ratings, the script MUST exclude those participants, log them, and continue with the remaining valid pairs.
 - **NO FALLBACK**: The script MUST NOT attempt to fabricate data or use synthetic data to fill gaps.
 - **Verification**: Create `tests/unit/test_analysis.py::test_correlation_implementation` that verifies the Pearson/Spearman correlation is correctly applied and that the correlation coefficients and p-values are reported, not just a generic ANCOVA model. **CRITICAL**: Verify that the cross-sectional path is implemented and tested.

- [ ] T020 [US3] [Depends: T019, T026a] Implement `code/analysis.py` for Pearson/Spearman correlation (paired) per FR-004. **CRITICAL**: This task assumes T019 has validated the presence of paired data or initiated the cross-sectional fallback. The implementation MUST explicitly exclude participants with missing fatigue ratings and log the exclusion count per Edge Cases. **Verification**: Create `tests/unit/test_analysis.py::test_correlation_calculation` that runs on mock data with known correlation values and asserts the output matches. **CRITICAL**: Verify the correlation coefficients (r) and p-values are reported and match the mock truth. [UNRESOLVED-CLAIM: c_bc717bd2 — status=not_enough_info]

- [ ] T021 [P] [US3] Implement Benjamini‑Hochberg correction for multiple comparisons across electrodes per FR-005. **Verification**: Create `tests/unit/test_analysis.py::test_bh_correction` that runs the correction on a known set of p-values (e.g., a range of representative values) and asserts the adjusted p-values match the theoretical calculation.

- [ ] T022 [US3] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`. **Schema Requirement**: The CSV MUST contain columns: `threshold` (float), `count_significant` (int). **Verification**: Assert `data/analysis/sensitivity_table.csv` exists and contains the two specified columns with correct counts of significant electrodes at each threshold.

- [ ] T023 [US3] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, confidence intervals, and the sensitivity analysis table per US‑3 and FR-004. The report must strictly discuss correlation coefficients, p‑values, and confidence intervals. [UNRESOLVED-CLAIM: c_e816c6ed — status=not_enough_info] Output to `docs/final_report.md`. **Verification**: Assert `docs/final_report.md` exists and contains sections for "Correlation Analysis", "Statistical Significance", "Confidence Intervals", and "Sensitivity Analysis". Additionally, verify the content includes specific data points (e.g., "r =...", "p =...") and matches the schema validation using a mock data truth table generated within the test setup (e.g., expected r=0.45, p=0.02 for a specific mock dataset). Verify the Sensitivity Analysis section contains the table rendered from `data/analysis/sensitivity_table.csv` (ingested by `code/report.py`).

- [ ] T024 [P] [US3] Documentation updates in `docs/` covering pipeline parameters, data sources, and statistical interpretation guidelines. **Verification**: Assert `docs/README.md` contains a section "Pipeline Parameters" with a table of values from `code/config.yaml`. The verification MUST parse `code/config.yaml` and assert that the values in `docs/README.md` match the parsed YAML values exactly.

- [ ] T025 [P] [US3] Security hardening for data handling (PII scan implementation). **Verification**: Create `tests/unit/test_pii_scan.py` that runs a PII scan on `data/raw` and `data/processed` using Python's `re` module to search for common PII patterns (e.g., email, SSN patterns) and asserts `pii_scan_report.txt` is generated with no findings.

- [ ] T026a [US3] [Depends: T015, T016] Enforce N ≥ 30 constraint as a blocking gate before analysis. [UNRESOLVED-CLAIM: c_d453ce68 — status=not_enough_info] **Implementation Detail**: This task runs after T010 and T015/T016. It MUST read `data/processed/lzc_metrics.csv` (or `pe_metrics.csv` if LZC is missing) and count unique `participant_id` entries. If count < 30, it MUST exit with code 1 and log `validation_report.json` with message "Insufficient sample size: N < 30". This gate enforces SC-001 (Sample size N ≥ 30) measured against the [deferred] power requirement for effect size r=0.3. **Note**: The specific power calculation logic is deferred to the research phase, but this gate ensures the minimum N is met for that calculation. **Verification**:
 1. Create mock data at `tests/unit/data/mock_lzc_N29.csv` with exactly 29 unique participants.
 2. Run the validation script on this mock data.
 3. Assert the script exits with code 1.
 4. Assert the `validation_report.json` contains the message "Insufficient sample size: N < 30".
 5. Create mock data at `tests/unit/data/mock_lzc_N30.csv` with exactly 30 unique participants.
 6. Run the validation script on this mock data.
 7. Assert the script exits with code 0 (success).

- [ ] T027 [US3] [Depends: T011, T026a] Verify total pipeline memory usage ≤ 7 GB (SC-003, DC-001) using lightweight monitoring. **Implementation Detail**: This task runs AFTER T026a succeeds (N>=30). It MUST check the count of unique participants in `data/processed/lzc_metrics.csv` BEFORE running the pipeline. If N < 30, the test MUST SKIP, log a warning "Insufficient real data for memory profiling (N < 30)", and write `data/analysis/memory_report.json` with status "SKIPPED". If N ≥ 30, it MUST run the full pipeline (Download → Preprocess → Features → Analysis) on the full dataset WITHOUT the `memory_profiler` overhead. If the full dataset is not available, it MUST run on a representative subset (e.g., first N participants) defined by a fixed seed. It MUST use Python's built-in `resource` module (or equivalent system-level monitoring) to capture peak RSS (Resident Set Size) of the main process. It MUST write the result to `data/analysis/memory_report.json` with schema `{ "peak_memory_mb": float, "limit_mb": float, "status": "PASS/FAIL" }`. **Verification**:
 1. Assert `data/analysis/memory_report.json` exists.
 2. If N < 30 (based on pre-check), assert `status` is "SKIPPED".
 3. If N ≥ 30, assert `status` is "PASS" (peak memory < 7GB) or "FAIL" (peak memory ≥ 7GB).
 4. Verify the `peak_memory_mb` value is a valid float.

- [ ] T036 [US3] [Depends: T026a, T019, T020, T021, T022, T023, T027] Verify total pipeline runtime ≤ 6 hours (SC-002). **Implementation Detail**: Run the full pipeline (Download → Preprocess → Features → Analysis) on the full dataset (N=30) and measure wall-clock time. The script MUST write the result to `data/analysis/runtime_report.json` with schema `{ "total_runtime_hours": float, "unit": "hours" }`. **Verification**: Assert the total runtime recorded in `data/analysis/runtime_report.json` is ≤ 6 hours. **Dependency**: Depends on completion of all US1, US2, and US3 tasks, and T027 (Memory).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Validate `docs/quickstart.md` integration. **Dependency**: This task must run AFTER T029a (Research/Design phase) has generated `docs/quickstart.md`. **Verification**: Run the commands in `docs/quickstart.md` in a fresh environment and assert all steps complete successfully without errors.

**Note**: Tasks T045, T048, T049, T050 have been REMOVED. T045 and T048 logic was consolidated into T027. T049 and T050 were removed due to unauthorized scope creep (Attractor Topology Analysis not mandated by spec.md FR-003/FR-004). Phase 6 (T051-T054) has been REMOVED as it implemented unauthorized scope (Topological Refinement) not present in spec.md.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on cleaned data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on features from US2
- **Topological Refinement (Phase 6)**: REMOVED (unauthorized scope)

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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: All tasks must run on CPU‑only CI (limited cores, constrained RAM, no GPU)
- **Critical**: No synthetic/fake data allowed for integration tests; must use real datasets from verified sources. Synthetic data is permitted ONLY for unit tests where real data is unavailable.
- **Critical**: T010 implements the mandatory validation logic for paired pre/post fatigue ratings as defined in FR-001. It targets the specific PhysioNet dataset 'sleep-edf'.
- **Critical**: T011 specifies the 1–40 Hz bandpass filter and configurable notch filter as required by FR-002 and Constitution Principle VI.
- **Critical**: T019 implements the Pearson/Spearman correlation approach as defined in spec.md FR-004, with a cross-sectional fallback as described in plan.md Summary.
- **Critical**: T022, T023, T024, etc. respect the spec‑defined deliverables.
- **Critical**: T021 now explicitly defines the schema for the sensitivity analysis table to meet FR-006 (count of significant electrodes) and mandates ingestion by report.py.
- **Critical**: T026a added to enforce N≥30 as a blocking gate. [UNRESOLVED-CLAIM: c_86ecfede — status=not_enough_info]
- **Critical**: T027 (Memory) moved to Phase 5 to ensure it is part of the core validation flow, not 'Polish'. It now includes explicit N<30 skip logic.
- **Critical**: T029a has been moved to Phase 2 to resolve the circular dependency with `quickstart.md`.
- **Critical**: T011 verification now includes both synthetic unit tests and real-data integration tests to satisfy all spec requirements.
- **Critical**: T015 and T016 verification steps now explicitly distinguish between unit test (synthetic allowed for logic) and integration test (real data required) scenarios, with a skip condition for N<30.
- **Critical**: T027 verification now explicitly requires real data and skips if insufficient, prohibiting synthetic data for memory profiling.
- **Critical**: T010 logic updated to validate metadata before full download to satisfy FR-001 efficiency constraints.
- **Critical**: T011 verification now strictly enforces >20dB attenuation as per spec US-1 for both synthetic and real data.
- **Critical**: T036 added to explicitly verify SC-002 (Runtime ≤ 6h) with sequential execution.
- **Critical**: T043 and T044 have been REMOVED as they were unauthorized scope creep (Topological Complexity) not mandated by spec.md.
- **Critical**: T005 configuration now includes `artifact_threshold_uV` to clarify units.
- **Critical**: T019 and T020 now mandate Pearson/Spearman correlation as per spec.md FR-004, with cross-sectional fallback.
- **Critical**: T010 now outputs `data/processed/participant_exclusion_log.csv` and `data/raw/download_manifest.json`.
- **Critical**: T015 and T016 now explicitly state output must be a CSV with a header row.
- **Critical**: T027 now includes specific `memory_profiler` command invocation and wrapper script dependency (consolidated into T027).
- **Critical**: T045 and T048 have been REMOVED and their logic consolidated into T027.
- **Critical**: T019 dependency corrected to depend on T010 (metadata) rather than T026a (features).
- **Critical**: T026a dependency corrected to depend on T015 and T016 (feature extraction).
- **Critical**: T027 dependency corrected to depend on T011 and T026a, and is no longer marked as [P] (parallel) as it is a sequential verification step.
- **Critical**: T036 now explicitly specifies output file and schema for runtime report.
- **Critical**: T046 and T047 have been REMOVED as they were unauthorized scope creep (Topological Complexity) not present in spec.md.
- **Critical**: T019 now implements cross-sectional fallback if paired data is missing, as per plan.md Summary.
- **Critical**: T027 (Phase 5) now correctly depends on T011 and T026a, and is no longer marked as [P] (parallel) as it is a sequential verification step.
- **Critical**: Phase 6 (T051-T054) has been REMOVED as it implemented unauthorized scope (Topological Refinement) not present in spec.md.
- **Critical**: T010 now outputs `data/processed/participant_exclusion_log.csv` and `data/raw/download_manifest.json`.
- **Critical**: T015 and T016 verification logic has been atomized into separate tasks for implementation and testing.
- **Critical**: T022 verification no longer depends on report.py ingestion logic.
- **Critical**: T023 verification now includes mock data generation within the test setup.
- **Critical**: T045 now runs the full pipeline as a standalone process for accurate memory profiling (Logic moved to T027).
- **Critical**: T004 typo 'pyrly' corrected to 'pyRly'.
- **Critical**: T049 and T050 REMOVED due to scope creep. No replacement tasks exist as they are not mandated by spec.md.
- **Critical**: T015 and T016 verification logic now explicitly handles N<30 by skipping the test and logging a warning.
- **Critical**: T027 verification logic now explicitly checks N<30 before running the pipeline to avoid circular dependencies.
- **Critical**: T010 now includes the concrete Metadata URL 'https://physionet.org/files/sleep-edf/1.0.0/'.
- **Critical**: T011 now includes explicit dependency on T010 and file existence checks.
- **Critical**: T015 and T016 now include explicit dependency on T011 and file existence checks.
- **Critical**: T027 and T036 dependencies have been clarified to avoid logical loops.
- **Critical**: T029a has been moved to Phase 2 to clarify its dependency on Research/Design phase outputs. [UNRESOLVED-CLAIM: c_57f78402 — status=not_enough_info]