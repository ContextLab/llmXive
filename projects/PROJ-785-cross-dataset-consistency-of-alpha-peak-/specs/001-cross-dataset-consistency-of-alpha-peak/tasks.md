# Tasks: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

**Input**: Design documents from `/specs/001-cross-dataset-apf-consistency/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are REQUIRED - explicitly requested in the feature specification (User Stories & Independent Tests).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ CONSTITUTIONAL OVERRIDE NOTICE**:
The project Spec (FR-002) and Plan originally requested "Two distinct preprocessing pipelines" (Standard vs Alternative).
However, **Constitution Principle VII** mandates a "strictly defined, versioned pipeline" (1-45 Hz, CAR, ICA) and forbids
in-place modification or alternative protocols. Per Constitution Rule I (Reproducibility) and Principle VII, the "Alternative"
Pipeline (Pipeline B) is **SUPERSERVED**. This project implements **ONLY** the Single Standard Pipeline.
All tasks related to Pipeline B (T015.x) have been removed. The `pipeline_type` variable in the mixed-effects model is
removed; the model now analyzes `dataset_source` and `estimation_method` only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

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

- [ ] T001a [P] Create directory structure: Run `mkdir -p code tests data/raw data/derivatives data/processed state` to establish the required filesystem hierarchy.
- [X] T001b [P] Create `code/config.py` with global settings, random seeds, and path definitions
- [X] T001c [P] Create `requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `pybids`, `openneuro-py`, `matplotlib`, `seaborn`, `scipy`, `pytest`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004.1 [P] Create Pydantic model `EEGDataset` in `code/models/dataset.py` implementing the schema defined in `contracts/dataset.schema.yaml`.
- [ ] T004.2 [P] Create Pydantic model `APFResult` in `code/models/apf_result.py` implementing the schema defined in `contracts/apf_result.schema.yaml`.
- [ ] T004.3 [P] Create Pydantic model `VarianceComponent` in `code/models/variance_component.py` implementing the schema defined in `contracts/variance_component.schema.yaml`.
- [ ] T002 [P] Implement `code/validators.py` for BIDS compliance checks (sampling frequency, channel layout) and SHA256 checksum generation
- [ ] T003 [P] Implement `code/exceptions.py` with specific error types for "Data Integrity", "Missing Metadata", and "Pipeline Failure"
- [ ] T005 [P] Configure logging infrastructure: Create `code/logging_config.py` to set up structured JSON logging that outputs to both `state/` (file) and `console` (stdout).
- [ ] T006 [P] Setup environment configuration management: Define and document variables in `code/config.py` including `DATASET_IDS` (list) and `ALPHA_BAND` (tuple) to satisfy environment configuration requirements. **Note**: `PREPROCESSING_MODE` is REMOVED to comply with Constitution Principle VII.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Standardized Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically download specific resting‑state EEG datasets from OpenNeuro and apply the SINGLE, STRICTLY DEFINED preprocessing pipeline mandated by Constitution Principle VII (1-45 Hz, CAR, ICA).

**Independent Test**: The system can be tested by executing the download and preprocessing scripts on a single dataset and verifying that output files exist in the expected BIDS‑compliant derivative format with **no NaN values** in the signal channels.

### Tests for User Story 1 (Write‑First / Pre‑requisite)

> **NOTE**: These are *pre‑requisite* test tasks that must be written **before** the corresponding implementation tasks. They can be executed in parallel with implementation setup, but the implementation must later satisfy them.

- [X] T007 [P] [US1] **[Pre‑req]** Contract test for BIDS validation in `tests/contract/test_bids_validation.py`: Implement `test_validate_sampling_frequency_raises` which asserts that a missing `sampling_frequency` in `dataset_description.json` raises `DataIntegrityError`.
- [X] T008 [P] [US1] **[Pre‑req]** Integration test for OpenNeuro download in `tests/integration/test_download.py`: Mock API for `ds003775`, verify file structure `sub-01/eeg/sub-01_task-rest_eeg.fif` exists, and assert file count matches expected subject count.
- [X] T009 [P] [US1] **[Pre‑req]** Unit test for Pipeline Bandpass filtering and ICA rejection in `tests/unit/test_preprocessing.py`: Test `apply_bandpass` and `reject_ica_components` functions with synthetic data using Constitution-mandated parameters (1-45Hz). [UNRESOLVED-CLAIM: c_a1b2af57 — status=not_enough_info]
- [X] T010 [P] [US1] **[Pre‑req]** Unit test for Common Average Reference in `tests/unit/test_preprocessing.py`: Test `apply_car` function with synthetic data.
- [X] T011 [US1] **[Pre‑req]** Integration test for "Missing Metadata" edge case in `tests/integration/test_edge_cases.py`: Verify system halts and logs `DataIntegrityError: Missing 'sampling_frequency'` when `dataset_description.json` lacks the field.

### Implementation for User Story 1

- [ ] T012.1 [US1] **[Pre‑req to T012.2]** Define the list of dataset IDs in `code/config.py` (variable `DATASET_IDS`). **Constraint**: {{claim:c_f270543f}} (Wikidata Q1828075, https://www.wikidata.org/wiki/Q1828075) **Note**: No validation logic is executed in this task.
- [ ] T013.1 [P] [US1] **[Pre‑req to T012.2]** Implement subject count validation logic in `code/validators.py`: Define `validate_subject_count(dataset_id)` function that counts subjects and enforces `>= 20` threshold; raise `DataIntegrityError` if violated.
- [ ] T012.2 [US1] **[Pre‑req to T014]** Validate the list of dataset IDs defined in T012.1 by calling `validate_subject_count` (T013.1) for each ID. Raise `ValueError` if any ID fails the subject count check.
- [ ] T012 [US1] Implement `code/download.py` using `openneuro-py` to fetch datasets from the OpenNeuro repository. **Constraint**: Must fail loudly on API error (no synthetic fallback).
- [ ] T014.1 [US1] **[Pre‑req to T014.4]** Implement Bandpass Filter in `code/preprocessing.py`: Define `apply_bandpass(signal, low=1.0, high=45.0)` function. [UNRESOLVED-CLAIM: c_37008958 — status=not_enough_info] **Validation**: Assert `low < high`. **Constraint**: Parameters are FIXED to Constitution Principle VII (1-45 Hz). **Note**: No `PREPROCESSING_MODE` flag; this is the only pipeline.
- [ ] T014.2 [P] [US1] **[Pre‑req to T014.4]** Implement Notch Filter in `code/preprocessing.py`: Define `apply_notch(signal, frequency)` function. **Logic**: Strictly validate `PowerLineFrequency` from BIDS metadata; if missing or ambiguous, raise `DataIntegrityError` (do NOT default).
- [ ] T014.3 [P] [US1] **[Pre‑req to T014.4]** Implement Common Average Reference in `code/preprocessing.py`: Define `apply_car(data)` function.
- [ ] T014.4 [P] [US1] **[Pre‑req to T019]** Implement ICA Artifact Rejection in `code/preprocessing.py`: Define `reject_ica_components(data, correlation_threshold=0.8, variance_threshold=0.15)` function. [UNRESOLVED-CLAIM: c_e8828c19 — status=not_enough_info] **Constraint**: ICA MUST be applied as per Constitution Principle VII.
- [X] T019 [US1] **[Pre‑req to T016]** Implement explicit NaN verification step in `code/preprocessing.py` that scans each derivative file for NaN values **after** pipeline processing; if any NaNs are found, halt the pipeline and log a "NaN Detected" error.
- [X] T016 [US1] **[Pre‑req to T027]** Implement OOM detection and sequential processing logic in `code/main.py`: Detect memory pressure, process one dataset at a time, and delete raw data after derivative generation to stay within RAM limits. (Merged T016.1 into this task).
- [ ] T017 [US1] Add logging for artifact rejection status ("None Detected" if no EOG components found) and write to `data/derivatives/rejection_log.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Alpha Peak Frequency (APF) Estimation via Dual Methods (Priority: P2)

**Goal**: Calculate the Alpha Peak Frequency (APF) for every subject using two distinct methods (time‑domain autocorrelation and frequency‑domain PSD peak detection) and verify consistency.

**Independent Test**: The system can be tested by running the APF estimation on a synthetic EEG signal with a known, injected alpha peak (e.g., 10.0 Hz) and verifying that both methods return a value within ±0.5 Hz of the ground truth.

### Tests for User Story 2

- [ ] T018 [P] [US2] **[Pre‑req]** Contract test for APF schema in `tests/contract/test_apf_schema.py`
- [ ] T020 [US2] **[Pre‑req]** Integration test for synthetic ground truth calibration: Write test that mocks the T023 implementation. Test must explicitly execute the synthetic signal generator (T023) with parameters (10.0 Hz sine wave, 256 Hz sampling rate) and verify the error is within ±0.5 Hz.
- [ ] T021 [US2] Unit test for "Indeterminate" flag in `tests/unit/test_apf_estimator.py`: Test that a flat spectrum (power < 1e-6 across 8-13 Hz) triggers the "Indeterminate" flag.
- [ ] T022 [US2] Unit test for "Out-of-Band" flag in `tests/unit/test_apf_estimator.py`: Test that a peak at a specific frequency triggers the "Out-of-Band" flag with expected string value.

### Implementation for User Story 2

- [ ] T023.1 [US2] **[Pre‑req to T023.2]** Implement Welch's PSD calculation in `code/apf_estimator.py`: Define `calculate_psd(signal, fs)` function.
- [ ] T023.2 [US2] **[Pre‑req to T027]** Implement peak detection logic in `code/apf_estimator.py`: Define `find_psd_peak(psd, freqs, low=8.0, high=13.0)` function.
- [ ] T024.1 [US2] **[Pre‑req to T024.2]** Implement autocorrelation calculation in `code/apf_estimator.py`: Define `calculate_autocorr(signal)` function.
- [ ] T024.2 [US2] **[Pre‑req to T027]** Implement peak-to-frequency conversion in `code/apf_estimator.py`: Define `autocorr_to_frequency(peak_lag, fs)` function.
- [ ] T025 [US2] Implement synthetic signal generator in `code/apf_estimator.py` to create a test signal with a known peak frequency for calibration.
- [ ] T026 [US2] Implement logic to flag results as "Indeterminate" if peak detection fails or "Out-of-Band" if peak is outside 8‑13 Hz.
- [ ] T027 [US2] Run APF estimation on all preprocessed data (Single Pipeline) and save results to `data/processed/apf_estimates.csv`.
- [ ] T027.1 [US2] **[Pre‑req to T038]** Implement consistency metric calculation for real data: Compute `|APF_psd - APF_autocorr|` for each subject and compare against a predefined frequency threshold.
- [ ] T029 [US2] Implement sensitivity analysis loop in `code/apf_estimator.py`: Sweep alpha band bounds by ±0.5 Hz (specifically: [7.5-12.5, 8.0-13.0, 8.5-13.5]), **calculate the change in mean APF**, and generate a CSV file `data/processed/sensitivity_analysis.csv` with columns: `lower_bound`, `upper_bound`, `mean_apf`, `delta_mean_apf`. **Deliverable**: The task must output this CSV file with numeric delta values.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Variance Decomposition and Reporting (Priority: P3)

**Goal**: Fit a mixed‑effects model to decompose variance in APF estimates into components attributable to "Dataset Source" and "Estimation Method". (Note: Pipeline variable removed per Constitution).

**Independent Test**: The system can be tested by running the analysis on a simulated dataset where variance components are known, verifying the model recovers them within a reasonable margin of error.

### Tests for User Story 3

- [ ] T030 [P] [US3] **[Pre‑req]** Contract test for Variance Component schema in `tests/contract/test_variance_schema.py`
- [ ] T031 [P] [US3] **[Pre‑req]** Integration test for Mixed‑Effects model recovery on simulated data in `tests/integration/test_model_recovery.py`: Simulate a dataset with known variance components (Dataset=0.40, Residual=0.50). [UNRESOLVED-CLAIM: c_bba81f72 — status=not_enough_info] Fit the model and assert that the recovered components are within ±0.05 of the true values.
- [ ] T032 [US3] Unit test for Bootstrapping confidence interval calculation in `tests/unit/test_analysis.py`: Test with input N=50, assert CI width and coverage probability. [UNRESOLVED-CLAIM: c_cb15db05 — status=not_enough_info]

### Implementation for User Story 3

- [ ] T033.1 [US3] **[Pre‑req to T033.2]** Define model formula in `code/analysis.py`: `APF ~ dataset_source + estimation_method + (1|subject)`. **Constraint**: Formula matches Spec FR-004 (modified for single pipeline) and Constitution Principle VI. **Note**: Removed `pipeline_type` and complex random slopes to prevent singularity.
- [ ] T033.2 [US3] **[Pre‑req to T033.3]** Fit model in `code/analysis.py`: Implement `fit_mixed_effects_model(data, formula)`.
- [ ] T033.3 [US3] **[Pre‑req to T034]** Extract variance components in `code/analysis.py`: Implement `extract_variance_components(model)`.
- [ ] T034.1 [US3] **[Pre‑req to T034.2]** Implement resampling logic in `code/analysis.py`: Define `bootstrap_resample(data, n_samples)`.
- [ ] T034.2 [US3] **[Pre‑req to T035]** Implement CI calculation in `code/analysis.py`: Define `calculate_confidence_intervals(resampled_stats, confidence=0.95)`.
- [ ] T035 [US3] **[Pre‑req to T035.2]** Implement simulation‑based power analysis in `code/analysis.py`: Simulate multiple datasets with known variance components (Dataset=0.40, Residual=0.50) and varying sample sizes. **Input Parameters**: `effect_size=0.15` (small effect for Dataset/Method), `alpha=0.05`. Fit the model and calculate the percentage of simulations where the dataset effect is significant (p < 0.05). **Output**: Generate `data/processed/minimum_sample_size_estimation.csv` identifying the minimum N required to achieve [deferred] power.
- [ ] T035.2 [US3] **[Pre‑req to T036.1]** **[Pre‑req to T038]** Calculate achieved power for real dataset in `code/analysis.py`: Compute power based on observed variance components and sample size of the real data. **Input Parameters**: `effect_size=0.15`, `alpha=0.05`. Write the calculated power value to `data/processed/power_analysis_results.json`.
- [ ] T036.1 [US3] **[Pre‑req to T038]** **CRITICAL**: Implement "Achieved Power" validation in `code/analysis.py`: Verify that the calculated achieved power (from T035.2) meets the SC-003 threshold (≥ 0.80) and generate a binary Pass/Fail flag for the current study's validity.
- [ ] T036 [US3] **[Pre‑req to T038]** Implement minimum sample size estimation in `code/analysis.py`: Iteratively vary N from a small initial value to a large upper bound in consistent steps., compute power for each N, stop when power ≥ 0.80, and report the minimum N required. **Note**: This task now estimates sample size for 'Dataset Source' and 'Estimation Method' variance only (Pipeline removed).
- [ ] T037.1 [US3] **[Pre‑req to T038]** Implement Forest Plot generation in `code/reporting.py`: Plot APF by dataset.
- [ ] T037.2 [US3] **[Pre‑req to T038]** Implement Variance Bar Chart generation in `code/reporting.py`: Plot percentage of total variance by factor (Dataset, Method, Subject).
- [ ] T038 [US3] Generate final report in `data/processed/final_report.md` including sensitivity table. **Logic**: Explicitly evaluate **R² ≥ 0.30** for dataset source (SC‑001), **|APF_psd − APF_autocorr| ≤ 0.5 Hz** (SC‑002), **achieved power ≥ 0.80** (SC‑003, using T035.2 and T036.1), and **Δmean APF ≤ 0.2 Hz** from the sensitivity sweep (SC‑005); **Output**: A binary Pass/Fail status for each criterion AND the **numeric delta mean APF values** from `sensitivity_analysis.csv` displayed in the report text to allow independent verification.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Update `README.md` with installation steps, usage examples, and environment setup instructions.
- [ ] T040 [P] Generate API docs for `code/preprocessing.py`, `code/apf_estimator.py`, and `code/analysis.py`.
- [ ] T041 Code cleanup and refactoring of `code/main.py` orchestration
- [ ] T042 Performance optimization: Ensure streaming logic handles large datasets without OOM
- [ ] T043 [P] Unit test for "Missing Metadata" edge case in `tests/unit/test_edge_cases.py`: Test `sampling_frequency` field with specific error message.
- [ ] T044 [P] Unit test for "Out-of-Band" peak edge case in `tests/unit/test_edge_cases.py`: Test 7.5 Hz peak with expected flag string.
- [ ] T045 [P] Unit test for "No Alpha Peak" edge case in `tests/unit/test_edge_cases.py`: Test white noise input with expected 'Indeterminate' flag value.
- [ ] T046 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility
- [ ] T047 Verify all SHA256 checksums in `state/` match `data/raw` artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories
- **User Stories (Phase 3‑5)**: All depend on Foundational phase completion
 - Once Foundational is done, the three user stories can proceed **in parallel** (if staffing permits) or sequentially by priority (P1 → P2 → P3)

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependencies on other stories.
- **User Story 2 (P2)**: **Depends on US1** – requires pre‑processed data from the standard pipeline.
- **User Story 3 (P3)**: **Depends on US2** – requires APF estimates from the standard pipeline.

### Within Each User Story

- **Write‑First Tests** (`T007‑T011`, `T018`, `T020`, `T030‑T032`) are **pre‑requisite** tasks; they must exist and initially fail before the corresponding implementation tasks (`T012‑T017`, `T023‑T029`, `T033‑T038`) are completed.
- Tests and models marked `[P]` can run in parallel.
- Implementation tasks that produce data must complete **before** downstream tasks that consume that data (e.g., `T014.1/T014.2/T014.3/T014.4` → `T019` → `T027` → `T033`).

### Parallel Example: User Story 1

```bash
# Write‑First tests (can be authored in parallel)
Task: "Contract test for BIDS validation in tests/contract/test_bids_validation.py" # T007
Task: "Integration test for OpenNeuro download in tests/integration/test_download.py" # T008

# Implementation (can run once tests are written)
Task: "Implement Bandpass Filter" # T014.1
Task: "Implement Notch Filter" # T014.2
Task: "Implement CAR" # T014.3
Task: "Implement ICA" # T014.4
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Download + Preprocess + NaN check)
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Download/Preprocess)
 - Developer B: User Story 2 (APF Estimation – can start once a small subset of preprocessed data is available)
 - Developer C: User Story 3 (Analysis – starts after APF estimates are generated)
3. Stories integrate independently and converge in Phase 6

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Integrity**: System MUST fail loudly if real data fetch fails; never use synthetic fallbacks.
- **Memory Management**: Use sequential processing for datasets to stay within available RAM limits.
- **Reproducibility**: All random seeds must be pinned in `code/config.py`.
- **Constitution Compliance**: The project implements a **SINGLE** pipeline (1-45Hz, CAR, ICA) as mandated by Constitution Principle VII. The "Alternative" pipeline (Pipeline B) is **REMOVED** to ensure compliance.
- **Success Criteria**: All success criteria (SC‑001, SC‑002, SC‑003, SC‑005) are evaluated with binary Pass/Fail logic in the final report (T038), **PLUS** the required numeric reporting of delta mean APF values for SC‑005 verification.
- **Achieved Power**: T035.2 and T036.1 are mandatory for SC-003 compliance, ensuring the *actual* dataset's statistical power is calculated and reported, not just theoretical simulations.
- **Power Analysis Inputs**: All power analysis tasks (T035, T035.2, T036) use `effect_size=0.15` (small effect for Dataset/Method) and `alpha=0.05` as fixed parameters. **Note**: Pipeline effect is no longer simulated.