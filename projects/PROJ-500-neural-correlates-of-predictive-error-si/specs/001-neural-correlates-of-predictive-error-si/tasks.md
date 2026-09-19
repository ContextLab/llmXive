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
 **Exclusion Requirement**: Explicitly apply Constitution Principle VII: Minimum Statistical Power Requirements to **BOTH** "error_signal" and "stimulus_driven" modes before generating the report.
 **Verification**: Confirm file exists, contains valid JSON, `analysis_mode` key is present, and excluded subjects are logged.
- [X] T004 [P] [US1] Implement graceful degradation in `src/data/ingest.py`: Log warnings for missing metadata or failed fetches and skip affected datasets rather than crashing (FR-011). **Requirement**: If a real dataset fetch (OpenNeuro/HF) fails, log the error, skip the dataset, and continue processing other datasets. Do NOT terminate the pipeline.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T005c [P] Initialize Git repository at the **repository root** (not in `src/`). **Commands**: `git init` executed at the root level. **Constraint**: Must be executed before any other git operations.
- [X] T005d [US1] Generate initial `state/projects/PROJ-500-neural-correlates-of-predictive-error-si.yaml` with content hashes for `./requirements.txt` and `./pyproject.toml` to satisfy Constitution Principle V. **Dependency**: T005c (Git Init). **Implementation Detail**: Use **SHA-256** hashing algorithm. Hash the full content of `./requirements.txt` and `./pyproject.toml`. **Verification**: Confirm file exists, contains valid YAML, and includes `artifact_hashes` map with SHA-256 values for both files. **Note**: Sequential execution required to ensure directory structure is ready.
- [X] T005a [P] Create project directory structure (`src/`, `tests/`, `contracts/`, `data/`, `analysis/`)
- [X] T005b [P] Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (dependencies: `mne`, `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `datasets`, `joblib`)
- [X] T006 [P] Configure linting (`ruff`) and formatting (`black`) tools (Create `ruff.toml` and `pyproject.toml` [tool.black] sections)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Dependency**: T009 must complete before T014/T015.

- [X] T009a [P] Create base data schema `contracts/aligned_data.schema.yaml`. **Format**: YAML (JSON Schema Draft 7). **Library**: `jsonschema`. **Fields**: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, `analysis_mode`, `learning_phase`. **Deliverable**: Write the **complete, valid JSON Schema** content to `contracts/aligned_data.schema.yaml`. **Verification**: Validate the file against JSON Schema Draft 7 syntax and ensure all required fields are present.
- [X] T009b [P] Create base data schema `contracts/model_output.schema.yaml`. **Format**: YAML (JSON Schema Draft 7). **Library**: `jsonschema`. **Fields**: `coefficients`, `p_values`, `fdr_p_values`, `permutation_p_value`. **Deliverable**: Write the **complete, valid JSON Schema** content to `contracts/model_output.schema.yaml`. **Verification**: Validate the file against JSON Schema Draft 7 syntax and ensure all required fields are present.
- [X] T010 [P] Setup environment variable validation and error handling infrastructure (Create `src/utils/env_validator.py` to check `DATA_DIR`, `SEED`, `RAM_LIMIT`)
- [X] T007 [P] Setup configuration management (`src/utils/config.py`) for paths, seeds, and parameters (Low-frequency filter in the range of a few hertz to the upper limit of the low-frequency band., `EPOCH_WINDOW` (default -200 to 500ms), `ACCURACY_BLOCK_SIZE`)
- [X] T008 [P] Implement structured logging (`src/utils/logging.py`) with JSON output for pipeline traceability
- [X] T011 [P] Implement checksum utility (`src/utils/checksum.py`) for data hygiene (FR-009, Constitution III)
- [X] T012 [US1] Contract test for data schema validation in `tests/contract/test_schemas.py`. **Dependency**: Requires T009a/b completion. **Logic**: Load schemas from `contracts/` and validate sample data against them. **Note**: Sequential execution required after T009a/b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw EEG data from OpenNeuro/HF, preprocess (filter, ICA, interpolate), and epoch data with ≥95% success rate for valid datasets.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample dataset and verifying the output contains correctly labeled epochs, filtered signals, and interpolated channels without manual intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for underpowered exclusion in `tests/contract/test_schemas.py`. **Function Name**: `test_underpowered_exclusion`. **Dependency**: T009a/b (Schemas), T007 (Config). **Logic**: Load a mock dataset with <20 subjects or <500 trials/condition, run the exclusion logic (T016), and assert that the resulting schema-compliant output does not contain these subjects. **Mock Data Generation**: Create a DataFrame within the test using: `import pandas as pd; mock = pd.DataFrame({'subject_id': ['S1', 'S2'], 'trial_count': [100, 100]})`. **Verification**: Assert that `excluded_subjects.csv` is generated and contains the specific IDs. **Note**: This test validates the *schema and logic contract*, not the full pipeline execution.

### Implementation for User Story 1

- [X] T014 [US1] Implement streaming data downloader in `src/data/ingest.py` (chunked buffering, delete raw files post-processing, FR-001, FR-009)
- [X] T015 [US1] Implement preprocessing module in `src/data/preprocess.py` (Bandpass filter **1–40 Hz** as per Plan Phase 1, ICA artifact removal, bad channel interpolation) (FR-002, Constitution VI). **Note**: Explicitly use 1–40 Hz to resolve Spec ambiguity.
- [X] T016 [US1] Implement artifact rejection logic (trial count loss ≤ 5%) and underpowered dataset flagging in `src/data/preprocess.py`. **Logic**: Apply **static thresholds** (≥20 subjects, ≥500 trials/condition) as the **sole** exclusion criteria. Explicitly filter `aligned_data.csv` generation (T024) to remove these subjects from the primary GLMM input (Constitution VII, Plan Phase 0.5). **Deliverable**: Write excluded subject IDs to `data/excluded_subjects.csv` with columns: `subject_id`, `reason` (must explicitly state if excluded due to subject count <20 OR trial count <500). **Verification**: Confirm `excluded_subjects.csv` exists and contains entries for BOTH exclusion criteria (subject count AND trial count) where applicable. **Note**: Do NOT implement dynamic post-hoc exclusion logic.
- [X] T017 [US1] Implement epoching logic in `src/data/preprocess.py`. **Requirement**: Read `EPOCH_WINDOW` from `src/utils/config.py` (default: ms to 500ms) and apply it. **Note**: The default value is provisional pending spec confirmation; the code must support configuration changes without modification. (FR-003). **Verification**: Confirm epoching window matches the configured value in `config.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - MMN Amplitude and Behavioral Alignment (Priority: P2)

**Goal**: Compute MMN amplitude (early-latency window) at CP3, CP4, C3, C4, align with behavioral accuracy using Lagged Alignment, and handle missing logs via "Stimulus-Driven" fallback.

**Independent Test**: Can be fully tested by running the alignment module on a pre-processed dataset and verifying the output CSV contains a time-series of MMN amplitudes and corresponding accuracy percentages for each block, with no missing values for valid blocks.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for aligned_data schema in `tests/contract/test_schemas.py`. **Dependency**: T009a (Base Schema), T022b (Learning_Phase extension). **Logic**: Validate that the final `aligned_data.csv` contains all required fields including `learning_phase`.
- [ ] T019 [P] [US2] Integration test for lagged alignment logic in `tests/integration/test_alignment.py`. **Verification**: Must validate that `data/interim_lagged_mmns.csv` is generated with the exact schema: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, and that the lagged logic (-trial source window -> subsequent accuracy block) is correctly applied.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement MMN amplitude calculator in `src/data/align.py`. **Requirement**: Calculate mean difference wave (Deviant - Standard) **explicitly at electrodes CP3, CP4, C3, and C4** within the 150–250ms window (FR-004). **Deliverable**: Output must be a DataFrame with distinct columns/rows for each of the four electrodes. **Verification**: Verify output file contains columns/rows for CP3, CP4, C3, C4. Do NOT calculate a single global average.
- [ ] T021 [US2] Implement behavioral binning logic in `src/data/align.py`. **Logic**: Calculate accuracy over a **configurable multi-trial block** (t to t+n) defined in `src/utils/config.py` as `ACCURACY_BLOCK_SIZE` (FR-005, Plan Phase 2). **Output**: `data/accuracy_blocks.csv` (Schema: `subject_id`, `block_id`, `accuracy`, `trial_start`, `trial_end`). **Verification**: Confirm file exists and contains valid accuracy values for the configured window size.
- [ ] T022 [US2] Implement **Lagged Alignment** logic in `src/data/align.py`: Calculate MMN over a preceding fixed-length trial window (t-N to t-M) and align to the **subsequent accuracy block** (t to t+n) generated by T021. **Deliverable**: Write intermediate artifact to `data/interim_lagged_mmns.csv` with columns: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial` (Spec FR-005, Plan Phase 2). **Dependency**: Requires T021 output.
- [ ] T022b [US2] Implement **Learning_Phase** feature generation in `src/data/align.py`. **Logic**: Bin trial blocks into discrete phases (e.g., "Early", "Late") based on `block_id` or cumulative trial count to create the `Learning_Phase` predictor required for the LME model (FR-006). **Output**: Add `learning_phase` column to `data/interim_lagged_mmns.csv` or create `data/learning_phases.csv`. **Verification**: Confirm `learning_phase` column exists and contains valid categorical values. **Note**: Must complete before T027.
- [ ] T024 [US2] Finalize and Write Aligned Dataset: **Dependency**: Explicitly consume `excluded_subjects.csv` from T016, filtered data from T023 (removed), and `learning_phase` from T022b **BEFORE** merging. **Logic**: Merge filtered `data/interim_lagged_mmns.csv` with filtered `data/accuracy_blocks.csv`, apply underpowered subject filter (from T016), and **perform a final re-verification** that the merged dataset contains no subjects/blocks violating the trial count threshold (<500 trials/condition) before writing. **Deliverable**: Generate final `data/aligned_data.csv` (FR-011, FR-012). **Verification**: Ensure `aligned_data.csv` contains no excluded subjects, matches the schema, has no NaN values, and passes the final trial count re-verification. **Note**: Sequential execution required after T016 and T022b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Fit Gaussian LME (`MMN ~ Accuracy + (1|Subject)`), apply multiple-comparison correction, run permutation test (n=1000), and perform sensitivity analysis.

**Independent Test**: Can be fully tested by executing the analysis script on the aligned dataset and verifying the output includes the model coefficients, p-values (corrected), and a permutation test p-value, all generated within 6 hours on CPU-only hardware.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for model_output schema in `tests/contract/test_schemas.py`
- [X] T026 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_model.py`. **Verification**: Must verify that the permutation test runs exactly 1000 shuffles and reports the fixed p-value.

### Implementation for User Story 3

- [ ] T027 [US3] Implement Gaussian LME fitting in `src/analysis/model.py` (`MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`) consuming `data/aligned_data.csv` (Plan Correction, Spec FR-006 Updated). **Note**: Assumes Spec v1.1 is the SSoT. **Dependency**: Requires `aligned_data.csv` from T024 and `Learning_Phase` feature from T022b. <!-- FAILED: unspecified -->
- [X] T028 [P] [US3] Implement multiple-comparison correction using **FDR (Benjamini-Hochberg)** for electrodes in `src/analysis/model.py` (FR-008). **Dependency**: Requires T027 output.
- [X] T029 [US3] Implement permutation test in `src/analysis/model.py`. **Logic**: Run a **fixed** permutation test with **exactly n=1000 shuffles**. **Requirement**: Do NOT implement dynamic pilot logic or variance adjustment. The spec mandates n=1000. **Deliverable**: Write `analysis/results/permutation_stability_log.json` containing the final n used (1000) and the final p-value. **Verification**: Confirm log file exists and shows n=1000 was used.
- [X] T030 [US3] Implement sensitivity analysis in `src/analysis/robustness.py` (sweep time window ±10ms: 140–240ms, 160–260ms) (FR-010)
- [X] T031 [US3] Generate `analysis/results/model_output.json` with coefficients, p-values, and robustness metrics. **Traceability**: Output must be derived from and traceable to Functional Requirements FR-006, FR-007, and FR-010. **Verification**: Ensure JSON contains all required fields and matches the schema from T009b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Documentation updates in `docs/` and `README.md` including `quickstart.md`
- [X] T033a [P] Refactor `src/data/ingest.py` to use streaming buffers ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling using `memory_profiler` (command: `python -m memory_profiler src/main.py`) and log peak usage < 7GB. (FR-009)
- [X] T033b [P] Refactor `src/analysis/model.py` to process subjects in batches ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling using `memory_profiler` (command: `python -m memory_profiler src/main.py`) and log peak usage < 7GB. (FR-009)
- [X] T034 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility
- [X] T035 [P] Additional unit tests for edge cases (missing metadata, handling zero accuracy values to prevent division errors) in `tests/unit/`
- [X] T036 [P] Verify full pipeline runtime ≤6 hours on **GitHub Actions free-tier runner (2-core, 7GB RAM)**. **Verification**: Run full pipeline on sample dataset, log runtime to `analysis/runtime.log`, and confirm ≤6 hours. **Note**: This is a **Performance Goal** (per Plan); minor variations due to hardware are acceptable if reproducibility is maintained. (FR-009, SC-005)

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

- All Setup tasks marked [P] can run in parallel (except T005c)
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
- **Missing Tasks**: T017 (Topographic Correlation) has been removed as it was unapproved scope. T037 (Strict Real-Data Loader) removed to align with FR-011. T039 (Dynamic Power) removed to align with static thresholds. T023 (50% Artifact Filter) removed as unapproved scope.

---

## Phase 7: Execution Verification & Robustness (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data source verification, streaming integrity, and rigorous power analysis enforcement.

- [X] T037 [P] [US1] **DELETED**: Replaced by T004 (Graceful Degradation).
- [X] T038 [P] [US1] Implement **Streaming Chunk Verification** in `src/data/ingest.py`. **Logic**: When using `datasets.load_dataset(..., streaming=True)`, implement an iterator wrapper that logs the count of processed chunks and verifies the total row count matches the expected dataset size (or logs a specific sampling fraction if subsampling is intentional). **Deliverable**: Add `data/streaming_log.json` recording chunks processed and total rows seen.
- [X] T039 [P] [US1] **DELETED**: Replaced by T016 (Static Thresholds).
- [ ] T040 [P] [US2] Implement **Lagged Window Sanity Check** in `src/data/align.py`. **Logic**: Before writing `data/interim_lagged_mmns.csv`, assert that the "source window" (t-N to t-M) and "target block" (t to t+n) do not overlap and that the source window contains at least 10 valid trials. If not, drop the block and log a warning. **Verification**: Ensure no overlapping windows exist in the output CSV.
- [X] T041 [P] [US3] Implement **Permutation Test Stability Report** in `src/analysis/model.py`. **Requirement**: Extend T029 to output a detailed report of the exact n-value chosen (1000). **Verification**: Confirm `analysis/results/permutation_stability_log.json` contains `final_n` (1000) and `stability_reason` ("Fixed n=1000 as per Spec FR-007").
