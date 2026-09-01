# Tasks: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

**Input**: Design documents from `/specs/001-cross-dataset-apf-consistency/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are REQUIRED - explicitly requested in the feature specification (User Stories & Independent Tests).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001a [P] Create directory structure: `code/`, `tests/`, `data/raw`, `data/derivatives`, `data/processed`, `state/`
- [ ] T001b [P] Create `code/config.py` with global settings, random seeds, and path definitions
- [ ] T001c [P] Create `requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `pybids`, `openneuro-py`, `matplotlib`, `seaborn`, `scipy`, `pytest`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Implement `code/validators.py` for BIDS compliance checks (sampling frequency, channel layout) and SHA256 checksum generation
- [ ] T003 [P] Implement `code/exceptions.py` with specific error types for "Data Integrity", "Missing Metadata", and "Pipeline Failure"
- [ ] T004 Create base data models/entities in `code/models/` (EEGDataset, APFResult, VarianceComponent) matching `contracts/` schemas
- [ ] T005 [P] Configure logging infrastructure to output structured logs to `state/` and console
- [ ] T006 [P] Setup environment configuration management for dataset IDs and processing parameters

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Dual-Pipeline Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically download multiple specific resting‑state EEG datasets from OpenNeuro and apply TWO distinct standardized preprocessing pipelines to all data.

**Independent Test**: The system can be tested by executing the download and preprocessing scripts on a single dataset and verifying that output files exist for **BOTH** pipelines in the expected BIDS‑compliant derivative format with **no NaN values** in the signal channels.

### Tests for User Story 1 (Write‑First / Pre‑requisite)

> **NOTE**: These are *pre‑requisite* test tasks that must be written **before** the corresponding implementation tasks. They can be executed in parallel with implementation setup, but the implementation must later satisfy them.

- [ ] T007 [P] [US1] **[Pre‑req]** Contract test for BIDS validation in `tests/contract/test_bids_validation.py`
- [ ] T008 [P] [US1] **[Pre‑req]** Integration test for OpenNeuro download in `tests/integration/test_download.py` (mock API, verify file structure)
- [ ] T009 [P] [US1] **[Pre‑req]** Unit test for Pipeline A filtering and ICA rejection in `tests/unit/test_preprocessing.py`
- [ ] T010 [P] [US1] **[Pre‑req]** Unit test for Pipeline B filtering and re‑referencing in `tests/unit/test_preprocessing.py`
- [ ] T011 [US1] **[Pre‑req]** Integration test for "Missing Metadata" edge case: Verify system halts and logs specific error in `tests/integration/test_edge_cases.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download.py` using `openneuro-py` to fetch datasets from the OpenNeuro repository. **Constraint**: Must fail loudly on API error (no synthetic fallback).
- [ ] T013 [US1] Implement BIDS validation logic in `code/download.py` to skip datasets with < 20 subjects or missing `sampling_frequency`, logging "Data Integrity" warnings.
- [ ] T014 [US1] Implement `code/preprocessing.py` **Pipeline A**: Bandpass 1‑45 Hz, Notch 50/60 Hz, Common Average Reference, ICA (remove EOG components > 0.8 correlation or > 15 % frontal variance).
- [ ] T015 [US1] Implement `code/preprocessing.py` **Pipeline B**: Bandpass 0.5‑40 Hz, Notch 50/60 Hz, **Mastoid Reference**, **NO ICA**.  
  **NOTE**: This deviates from Constitution Principle VII (which mandates 1‑45 Hz band‑pass and ICA for *all* data). The deviation is **explicitly permitted** by Spec FR‑002, which overrides the principle for the alternative pipeline. The implementation therefore references FR‑002 as the authoritative source for this exception.
- [ ] T016 [US1] Implement sequential processing logic in `code/main.py` to handle RAM constraints (process one dataset at a time, delete raw data after derivative generation).
- [ ] T017 [US1] Add logging for artifact rejection status ("None Detected" if no EOG components found) and write to metadata.
- [ ] T019 [US1] **Pre‑req to T016**: Implement explicit NaN verification step in `code/preprocessing.py` that scans each derivative file for NaN values **after** pipeline processing; if any NaNs are found, halt the pipeline and log a "NaN Detected" error, satisfying the independent test requirement.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Alpha Peak Frequency (APF) Estimation via Dual Methods (Priority: P2)

**Goal**: Calculate the Alpha Peak Frequency (APF) for every subject using two distinct methods (time‑domain autocorrelation and frequency‑domain PSD peak detection) and verify consistency.

**Independent Test**: The system can be tested by running the APF estimation on a synthetic EEG signal with a known, injected alpha peak (e.g., 10.0 Hz) and verifying that both methods return a value within ±0.5 Hz of the ground truth.

### Tests for User Story 2

- [ ] T018 [P] [US2] **[Pre‑req]** Contract test for APF schema in `tests/contract/test_apf_schema.py`
- [ ] T020 [US2] **[Pre‑req]** Integration test for synthetic ground truth calibration: Must explicitly execute the synthetic signal generator (T023) and verify the error is within ±0.5 Hz; do not mock.
- [ ] T021 [US2] Unit test for "Indeterminate" flag when no clear peak exists in `tests/unit/test_apf_estimator.py`
- [ ] T022 [US2] Unit test for "Out-of-Band" flag when peak is outside the lower-alpha frequency band in `tests/unit/test_apf_estimator.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/apf_estimator.py` using Welch's PSD to identify the maximum power in the 8‑13 Hz range.
- [ ] T024 [US2] Implement `code/apf_estimator.py` Time‑domain Method: Autocorrelation peak detection, convert lag to frequency.
- [ ] T025 [US2] Implement synthetic signal generator in `code/apf_estimator.py` to create a test signal with a known peak frequency for calibration.
- [ ] T026 [US2] Implement logic to flag results as "Indeterminate" if peak detection fails or "Out-of-Band" if peak is outside 8‑13 Hz.
- [ ] T027 [US2] Run APF estimation on all preprocessed data (Pipeline A & B) and save results to `data/processed/apf_estimates.csv`.
- [ ] T029 [US2] Implement sensitivity analysis loop in `code/apf_estimator.py`: Sweep alpha band bounds by ±0.5 Hz (e.g., 7.5‑12.5, 8.0‑13.0, 8.5‑13.5), **calculate the change in mean APF**, compare against the ≤ 0.2 Hz threshold, and output a Pass/Fail status as required by SC‑005.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Variance Decomposition and Reporting (Priority: P3)

**Goal**: Fit a mixed‑effects model to decompose variance in APF estimates into components attributable to "Dataset Source", "Preprocessing Pipeline", and "Estimation Method".

**Independent Test**: The system can be tested by running the analysis on a simulated dataset where variance components are known, verifying the model recovers them within a reasonable margin of error.

### Tests for User Story 3

- [ ] T030 [P] [US3] **[Pre‑req]** Contract test for Variance Component schema in `tests/contract/test_variance_schema.py`
- [ ] T031 [P] [US3] **[Pre‑req]** Integration test for Mixed‑Effects model recovery on simulated data in `tests/integration/test_model_recovery.py`
- [ ] T032 [US3] Unit test for Bootstrapping confidence interval calculation in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analysis.py` Mixed‑Effects Model: `APF ~ dataset_source + pipeline_type + estimation_method + (1|subject_id) + (1|subject_id:pipeline) + (estimation_method|subject_id)`.
- [ ] T034 [US3] Implement bootstrapping procedure in `code/analysis.py` with **1000 resamples** to generate 95 % confidence intervals for variance components.
- [ ] T035 [US3] Implement simulation‑based power analysis in `code/analysis.py`: Simulate 1000 datasets with known variances (dataset=0.4, pipeline=0.1, residual=0.5) to estimate achieved power.
- [ ] T036 [US3] Implement **minimum sample size estimation** in `code/analysis.py`: **Iteratively vary N from a small initial value to a large upper bound in steps of 5**, compute power for each N, stop when power ≥ 0.80, and **report the minimum N required** to detect the pipeline effect (fulfills FR‑006).
- [ ] T037 [US3] Implement `code/reporting.py` to generate Forest Plot (APF by dataset) and Variance Bar Chart (percentage of total variance).
- [ ] T038 [US3] Generate final report in `data/processed/final_report.md` including sensitivity table. **Logic**: Explicitly evaluate **R² ≥ 0.30** for dataset source (SC‑001), **|APF_psd − APF_autocorr| ≤ 0.5 Hz** (SC‑002), **power ≥ 0.80** (SC‑003), and **Δmean APF ≤ 0.2 Hz** from the sensitivity sweep (SC‑005); output a **binary Pass/Fail status** for each criterion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Update `README.md` with installation steps, usage examples, and environment setup instructions.
- [ ] T040 [P] Generate API docs for `code/preprocessing.py`, `code/apf_estimator.py`, and `code/analysis.py`.
- [ ] T041 Code cleanup and refactoring of `code/main.py` orchestration
- [ ] T042 Performance optimization: Ensure streaming logic handles large datasets without OOM
- [ ] T043 [P] Unit test for "Missing Metadata" edge case in `tests/unit/test_edge_cases.py`
- [ ] T044 [P] Unit test for "Out-of-Band" peak edge case in `tests/unit/test_edge_cases.py`
- [ ] T045 [P] Unit test for "No Alpha Peak" edge case in `tests/unit/test_edge_cases.py`
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
- **User Story 2 (P2)**: **Depends on US1** – requires pre‑processed data from both pipelines.
- **User Story 3 (P3)**: **Depends on US2** – requires APF estimates from both pipelines and both methods.

### Within Each User Story

- **Write‑First Tests** (`T007‑T011`, `T018`, `T020`, `T030‑T032`) are **pre‑requisite** tasks; they must exist and initially fail before the corresponding implementation tasks (`T012‑T017`, `T023‑T029`, `T033‑T038`) are completed.
- Tests and models marked `[P]` can run in parallel.
- Implementation tasks that produce data must complete **before** downstream tasks that consume that data (e.g., `T014/T015` → `T019` → `T027` → `T033`).

### Parallel Example: User Story 1

```bash
# Write‑First tests (can be authored in parallel)
Task: "Contract test for BIDS validation in tests/contract/test_bids_validation.py"   # T007
Task: "Integration test for OpenNeuro download in tests/integration/test_download.py" # T008

# Implementation (can run once tests are written)
Task: "Implement download.py"   # T012
Task: "Implement Pipeline A"    # T014
Task: "Implement Pipeline B"    # T015
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Download + Preprocess + NaN check)
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
- **Constitutional Exception**: Pipeline B (0.5‑40 Hz, No ICA) is a sanctioned deviation from Constitution Principle VII, explicitly allowed by Spec FR‑002. This is documented in T015.
- **Success Criteria**: All success criteria (SC‑001, SC‑002, SC‑003, SC‑005) are evaluated with binary Pass/Fail logic in the final report (T038).
