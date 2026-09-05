# Tasks: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Input**: Design documents from `/specs/001-neural-correlates-of-predictive-error-si/`
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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Dataset Validation & Variable Fit (SC-004 Gate)

**Purpose**: Verify dataset metadata and determine analysis path (Error-Signal vs Stimulus-Driven).

- [X] T001 [P] [US1] Implement dataset metadata fetcher in `src/data/ingest.py` to search for "tactile", "somatosensory", "odd-ball" datasets (FR-001)
- [X] T002 [P] [US1] Implement variable check in `src/data/ingest.py` to verify presence of `stimulus_type` and `response_correctness` in metadata (FR-011, FR-012)
- [X] T003 [P] [US1] Generate `data/validation_report.json` with `analysis_mode` ("error_signal" or "stimulus_driven") based on variable availability (FR-011, FR-012). **Logic**:
 1. If `response_correctness` exists -> set `analysis_mode` to "error_signal".
 2. If only `stimulus_type` exists -> set `analysis_mode` to "stimulus_driven" and log fallback warning (Pipeline continues).
 3. If neither exists -> log error and skip dataset.
 **Verification**: Confirm file exists, contains valid JSON, and `analysis_mode` key is present with a valid value. (Merged T022 logic here).
- [X] T004 [P] [US1] Log warning and skip datasets with missing metadata rather than crashing (FR-011)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T005c [P] Initialize Git repository and configure `.gitignore`. **Commands**: `git init`, `git add.`, `git commit -m 'init'`. **Constraint**: Must also generate initial `state/projects/PROJ-500-neural-correlates-of-predictive-error-si.yaml` with content hashes for `requirements.txt` and `pyproject.toml` to satisfy Constitution Principle V. (Moved to start of Phase 1, removed [P] flag for logical flow).
- [X] T005a [P] Create project directory structure (`src/`, `tests/`, `contracts/`, `data/`, `analysis/`)
- [X] T005b [P] Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (dependencies: `mne`, `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `datasets`, `joblib`)
- [X] T006 [P] Configure linting (`ruff`) and formatting (`black`) tools (Create `ruff.toml` and `pyproject.toml` [tool.black] sections)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Dependency**: T009 must complete before T014/T015.

- [ ] T009a [P] Create base data schema `contracts/aligned_data.schema.yaml`. **Fields**: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, `analysis_mode`.
- [ ] T009b [P] Create base data schema `contracts/model_output.schema.yaml`. **Fields**: `coefficients`, `p_values`, `fdr_p_values`, `permutation_p_value`.
- [X] T010 [P] Setup environment variable validation and error handling infrastructure (Create `src/utils/env_validator.py` to check `DATA_DIR`, `SEED`, `RAM_LIMIT`)
- [X] T007 [P] Setup configuration management (`src/utils/config.py`) for paths, seeds, and parameters (Low-frequency to Hz filter, –250ms window)
- [X] T008 [P] Implement structured logging (`src/utils/logging.py`) with JSON output for pipeline traceability
- [X] T011 [P] Implement checksum utility (`src/utils/checksum.py`) for data hygiene (FR-009, Constitution III)
- [X] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_schemas.py`. **Dependency**: Requires T009a/b completion.
- [X] T013 [P] [US1] Integration test for full ingestion pipeline on a small OpenNeuro sample in `tests/integration/test_pipeline.py`. **Verification**: Ensure the test confirms that datasets/subjects flagged as "underpowered" (<20 subjects) are explicitly excluded from the primary GLMM input data. **Dependency**: Requires T009a/b completion.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw EEG data from OpenNeuro/HF, preprocess (filter, ICA, interpolate), and epoch data with ≥95% success rate for valid datasets.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample dataset and verifying the output contains correctly labeled epochs, filtered signals, and interpolated channels without manual intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_schemas.py`
- [X] T013 [P] [US1] Integration test for full ingestion pipeline on a small OpenNeuro sample in `tests/integration/test_pipeline.py`. **Verification**: Ensure the test confirms that datasets/subjects flagged as "underpowered" (<20 subjects) are explicitly excluded from the primary GLMM input data. **Dependency**: Requires T009a/b completion.

### Implementation for User Story 1

- [X] T014 [US1] Implement streaming data downloader in `src/data/ingest.py` (chunked buffering, delete raw files post-processing, FR-001, FR-009)
- [X] T015 [US1] Implement preprocessing module in `src/data/preprocess.py` (–40 Hz bandpass, ICA artifact removal, bad channel interpolation) (FR-002)
- [X] T016 [US1] Implement artifact rejection logic (trial count loss ≤ 5%) and underpowered dataset flagging (<20 subjects) in `src/data/preprocess.py`. **Deliverable**: Write excluded subject IDs to `data/excluded_subjects.csv` with columns: `subject_id`, `reason`. **Logic**: Explicitly filter `aligned_data.csv` generation (T026) to remove these subjects from the primary GLMM input (Constitution VII, Plan Phase 0.5). **Verification**: Confirm `excluded_subjects.csv` exists and `aligned_data.csv` (T026) contains none of these IDs.
- [X] T018 [US1] Implement epoching logic in `src/data/preprocess.py` (-200ms to 500ms, standard/deviant separation based on metadata) (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - MMN Amplitude and Behavioral Alignment (Priority: P2)

**Goal**: Compute MMN amplitude (early-latency window) at CP3, CP4, C3, C4, align with behavioral accuracy using Lagged Alignment, and handle missing logs via "Stimulus-Driven" fallback.

**Independent Test**: Can be fully tested by running the alignment module on a pre-processed dataset and verifying the output CSV contains a time-series of MMN amplitudes and corresponding accuracy percentages for each block, with no missing values for valid blocks.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for aligned_data schema in `tests/contract/test_schemas.py`
- [X] T020 [P] [US2] Integration test for lagged alignment logic in `tests/integration/test_alignment.py`. **Verification**: Must validate that `data/interim_lagged_mmns.csv` is generated with the exact schema: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, and that the lagged logic (50-trial source window -> subsequent accuracy block) is correctly applied.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement MMN amplitude calculator (Standard) in `src/data/align.py` (mean difference wave early-mid latency at CP3, CP4, C3, C4) (FR-004)
- [ ] T023 [US2] Implement behavioral binning logic in `src/data/align.py`. **Logic**: Calculate accuracy over **10-trial blocks** (t to t+10) as defined in Plan Phase 2 and Spec FR-005. **Output**: `data/accuracy_blocks.csv` (Schema: `subject_id`, `block_id`, `accuracy`, `trial_start`, `trial_end`). **Verification**: Confirm file exists and contains valid accuracy values for 10-trial windows. <!-- FAILED: unspecified -->
- [ ] T024 [US2] Implement **Lagged Alignment** logic in `src/data/align.py`: Calculate MMN over a preceding **50-trial window** (t-50 to t-10) and align to the **subsequent 10-trial accuracy block** (t to t+10) generated by T023. **Deliverable**: Write intermediate artifact to `data/interim_lagged_mmns.csv` with columns: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial` (Plan Methodological Correction). **Dependency**: Requires T023 output.
- [ ] T025 [US2] Implement exclusion logic for blocks with <10 valid trials and NaN handling for excessive artifact rejection. **Logic**: Filter `interim_lagged_mmns.csv` and `accuracy_blocks.csv` to remove invalid blocks. **Deliverable**: Produce filtered versions of these files for T026. **Verification**: Confirm no blocks with <10 trials exist in filtered files.
- [ ] T026 [US2] Finalize and Write Aligned Dataset: Merge filtered `data/interim_lagged_mmns.csv` (T025) with filtered `data/accuracy_blocks.csv` (T025), apply underpowered subject filter (from T016 `excluded_subjects.csv`), and generate final `data/aligned_data.csv` (FR-011, FR-012). **Verification**: Ensure `aligned_data.csv` contains no excluded subjects, matches the schema, and has no NaN values in critical columns.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Fit Gaussian LME (`MMN ~ Accuracy + (1|Subject)`), apply multiple-comparison correction, run permutation test (n=1000), and perform sensitivity analysis.

**Independent Test**: Can be fully tested by executing the analysis script on the aligned dataset and verifying the output includes the model coefficients, p-values (corrected), and a permutation test p-value, all generated within 6 hours on CPU-only hardware.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for model_output schema in `tests/contract/test_schemas.py`
- [X] T028 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_model.py`. **Verification**: Must verify that the permutation test includes a logic check for sufficiency (e.g., stability of p-value with increasing n) or dynamically adjusts n based on dataset size.

### Implementation for User Story 3

- [X] T029 [US3] Implement Gaussian LME fitting in `src/analysis/model.py` (`MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`) consuming `data/aligned_data.csv` (Plan Correction, Spec FR-006 Updated). **Note**: Assumes Spec v1.1 is the SSoT. **Dependency**: Requires `aligned_data.csv` from T026.
- [X] T030 [P] [US3] Implement multiple-comparison correction using **FDR (Benjamini-Hochberg)** for electrodes in `src/analysis/model.py` (FR-008). **Dependency**: Requires T029 output.
- [X] T031 [US3] Implement permutation test (n=1000 shuffles) in `src/analysis/model.py` to validate significance. **Verification**: Include logic to check if n=1000 is sufficient (e.g., by checking **coefficient variance < 5% across 3 runs** OR dynamically adjusting n) as per Spec FR-007. **Dependency**: Requires T029 output.
- [X] T032 [US3] Implement sensitivity analysis in `src/analysis/robustness.py` (sweep time window ±10ms: 140–240ms, 160–260ms) (FR-010)
- [X] T033 [US3] Implement exclusion logic for subjects with zero accuracy to avoid singularity
- [X] T034 [US3] Generate `analysis/results/model_output.json` with coefficients, p-values, and robustness metrics (SC-001, SC-002, SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md` including `quickstart.md`
- [X] T036a [P] Refactor `src/data/ingest.py` to use streaming buffers ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling and log peak usage < 7GB. (FR-009)
- [X] T036b [P] Refactor `src/analysis/model.py` to process subjects in batches ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling and log peak usage < 7GB. (FR-009)
- [ ] T037 [P] Performance optimization: Verify full pipeline runtime ≤6 hours on 2-core CPU (FR-009, SC-005)
- [ ] T038 [P] Additional unit tests for edge cases (missing metadata, zero accuracy) in `tests/unit/`
- [ ] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Dataset Validation)**: No dependencies - can start immediately
- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Setup completion - BLOCKS all user stories. **Critical**: T009a/b must complete before T014/T015.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (clean epochs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (aligned data)

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
Task: "Contract test for data schema validation in tests/contract/test_schemas.py"
Task: "Integration test for full ingestion pipeline on a small OpenNeuro sample in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset metadata fetcher in src/data/ingest.py"
Task: "Implement streaming data downloader in src/data/ingest.py"
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
 - Developer A: User Story 1 (Ingestion/Preprocessing)
 - Developer B: User Story 2 (Alignment)
 - Developer C: User Story 3 (Statistical Modeling)
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
- **Critical Constraint**: All tasks must be executable on a multi-core CPU, sufficient RAM, no GPU. No 8-bit/4-bit quantization or large model loading.
- **Spec Alignment**: Spec v1.1 is the Single Source of Truth (Gaussian LME, Lagged Alignment). No spec amendment tasks are required.
- **Data Integrity**: All data loading tasks must fail loudly on missing real data; synthetic fallbacks are strictly prohibited.
- **Resource Management**: Streaming and chunking must be used for all large dataset operations to adhere to 7GB RAM limits.
- **Missing Tasks**: T017 (Topographic Correlation) and T027a (Spec Amendment) have been removed as they were unapproved scope or governance violations.