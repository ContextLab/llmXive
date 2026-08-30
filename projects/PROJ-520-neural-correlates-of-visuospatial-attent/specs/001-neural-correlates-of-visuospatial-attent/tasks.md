# Tasks: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

**Input**: Design documents from `/specs/001-neural-correlates-of-visuospatial-attent/`
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

- [X] T001a Create project directories: `data/raw`, `data/processed`, `code`, `tests/unit`
- [X] T001b Initialize `code/` with `requirements.txt`, `config.py`, `models.py`, `preprocessing.py`, `feature_extraction.py`, `classification.py`, `main.py`
- [X] T001c Initialize `tests/` with `__init__.py` and `conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes critical data integrity safeguards.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T005 is a hard gate**: Downstream tasks (T010+) cannot proceed if T005 fails. **T039 must complete before T010** to ensure the 'Fail Loudly' logic is in place before any data download attempts.

- [X] T004 Setup data directories structure (`data/raw`, `data/processed`) to ensure T005 can write logs and verify artifacts.
 *Note: T004 must complete before T005 to ensure target directories exist.*
- [X] T005 [US1] Implement dataset verification script to validate OpenNeuro BIDS compliance and event markers in `code/verify_dataset.py`
- [X] T006 [P] Setup configuration management for random seeds and file paths in `code/config.py`
- [X] T007 Create base data model entities (Epoch, Feature, ClassifierResult) in `code/models.py`
- [X] T008 Configure error handling and logging infrastructure for pipeline stages
- [X] T009 Setup environment configuration management for CI limits (CPU/RAM)
- [X] T039 [US1] Refactor dataset loader in `code/preprocessing.py` to REMOVE any `try/except` blocks or fallback logic that generates synthetic/mock data on download failure; implement a strict `raise RuntimeError` on fetch failure to ensure "Fail Loudly" behavior. **CRITICAL**: This task preserves the valid fallback to landmark interaction timestamps as defined in spec Edge Cases, but strictly forbids synthetic data generation (addresses "Loader must fail loudly" rule and distinguishes valid fallback from fabrication).
 *Note: T039 must complete before T010 to prevent synthetic data generation during download.*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - EEG Data Pipeline and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess OpenNeuro EEG datasets, including bandpass filtering, artifact removal, and epoch segmentation around attention shift events.

**Independent Test**: Verify that the pipeline outputs a preprocessed data file containing ≥100 epochs labeled by condition (active/passive) with valid time-frequency features, and that the preprocessing runs successfully within the allocated CI time budget.

**⚠️ BLOCKING GATE**: T010 must complete before T011-T017 can begin. T010 is NOT parallel-safe with downstream tasks. These tasks are sequential within the single file `code/preprocessing.py`.

### Implementation for User Story 1

- [X] T010 [US1] Implement dataset download and BIDS validation in `code/preprocessing.py` (verifies FR-001)
 *Checkpoint: Download Complete - T011-T017 depend on T010 output.*
- [X] T011 [US1] Implement bandpass filter (1-40 Hz) and notch filter (50/60 Hz) in `code/preprocessing.py` (addresses FR-002)
 *Note: Depends on T010.*
- [X] T012a [US1] Implement automatic ICA artifact rejection using `ica.find_bads_eog` and `ica.find_bads_ecg` in `code/preprocessing.py` (addresses FR-003 auto-part)
 *Note: Depends on T011.*
- [X] T012b [US1] Implement manual review capability: generate detailed log file of rejected components and visual inspection hints in `code/preprocessing.py` (addresses FR-003 manual-part)
 *Note: Depends on T012a.*
- [X] T013 [US1] Implement epoch segmentation (short-duration windows) centered on attention shift events in `code/preprocessing.py` (addresses FR-004). **Explicitly uses 2-second windows as defined in Constitution Principle VI (overriding the typo in spec.md FR-004 which reads '-second epochs')**.
 *Note: Depends on T012b.*
- [X] T014 [US1] Implement sample size validation: **HALT immediately if <100 epochs/condition** (raise `SampleSizeError`); do NOT continue processing if threshold is not met (addresses SC-005)
 *Note: Depends on T013. Strict halt required by Independent Test.*
- [X] T015 [US1] Implement fallback logic for missing event markers (use landmark timestamps) and document substitution in 'assumptions' section of `data/processed/metadata.json` with key `event_source: landmark_fallback` (addresses Edge Cases)
 *Note: Depends on T014. This is a valid data-source fallback, distinct from synthetic data generation.*
- [X] T016 [US1] Handle missing electrode data: skip affected electrodes and log skipped electrodes in `data/processed/metadata.json` with key `skipped_electrodes` (addresses Edge Cases)
 *Note: Depends on T015.*
- [X] T017 [US1] Save preprocessed epochs to `data/processed/epochs_cleaned.fif`; Verify file exists and contains >0 epochs using `mne.io.read_raw_fif` (addresses FR-004)
 *Note: Depends on T016.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Time-Frequency Feature Extraction (Priority: P2)

**Goal**: Extract mean power values from alpha and beta bands over specific electrodes using Morlet wavelet decomposition.

**Independent Test**: Verify that feature extraction produces a matrix with dimensions (epochs × features) where features include alpha power from parietal electrodes and beta power from frontal electrodes, and that values fall within physiologically plausible ranges.

### Implementation for User Story 2

- [X] T018 [US2] Implement Morlet wavelet time-frequency decomposition (within the beta frequency range) consuming `data/processed/epochs_cleaned.fif` in `code/feature_extraction.py`; Save time-frequency power array to `data/processed/tf_power.npy`; Verify shape matches (n_epochs, n_channels, n_freqs) (addresses FR-005)
 *Note: Strictly 8-30 Hz (alpha/beta). No gamma bands.*
- [X] T019 [US2] Implement baseline normalization (pre-stimulus interval to stimulus onset) for dB conversion. in `code/feature_extraction.py`
 *Note: Depends on T018.*
- [X] T020 [US2] Extract mean alpha power for P3, Pz, P4 electrodes from the normalized output of T019 in `code/feature_extraction.py` (addresses FR-006)
 *Note: Depends on T019.*
- [X] T021 [US2] Extract mean beta power (-30 Hz) for F3, Fz, F4 electrodes from the normalized output of T019 in `code/feature_extraction.py` (addresses FR-006)
 *Note: Depends on T019.*
- [X] T022 [US2] Implement feature validation: verify ≥80% epochs have non-NaN values for all target electrodes; Write validation report to `data/processed/feature_validation.json`; Raise `FeatureValidationFailed` if <80% (addresses FR-006)
 *Note: Depends on T020, T021.*
- [X] T023 [US2] Save feature matrix to `data/processed/features_matrix.csv` with dimensions (epochs × features); **Schema: 'epoch_id', 'condition', 'P3_alpha', 'Pz_alpha', 'P4_alpha', 'F3_beta', 'Fz_beta', 'F4_beta'**. Verify file exists and has dimensions (epochs × number of features) (addresses FR-006)
 *Note: Depends on T022. T025 depends on this file.*
- [X] T024a [US2] Calculate Pearson correlation matrix for target electrodes (P3, Pz, P4, F3, Fz, F4) and save as `correlation_matrix` key in `data/processed/feature_metadata.json` (addresses executability-27e00795)
 *Note: Depends on T023.*
- [X] T024b [US2] Document electrode collinearity findings and interpretation in `data/processed/feature_metadata.json` under key `collinearity_report` (addresses executability-27e00795)
 *Note: Depends on T024a.*

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Classification and Statistical Validation (Priority: P3)

**Goal**: Train LDA classifier, validate with cross-validation and permutation testing, and perform sensitivity analysis.

**Independent Test**: Verify that classification pipeline reports accuracy, precision, and recall metrics alongside a permutation p-value < 0.05 or a clear statement of non-significance. **Additionally, verify that statistical corrections (FWE) are applied specifically to the alpha/beta electrode subsets defined in FR-006.**

### Implementation for User Story 3

- [X] T025 [US3] Implement LDA classifier training with 5-fold cross-validation consuming `data/processed/features_matrix.csv` in `code/classification.py` (addresses FR-007)
 *Note: Must complete before T026-T032. Depends on T023.*
- [X] T026 [US3] Report accuracy, precision, recall with standard deviation across folds in `code/classification.py`
- [X] T027 [US3] Implement permutation testing with ≥1000 iterations to establish statistical significance in `code/classification.py` (addresses FR-008)
- [X] T028 [US3] Report classifier p-value and null hypothesis rejection decision (α = 0.05) in `results.json`; Verify `results.json` contains key `permutation_p_value` with a float value < 0.05 or null (addresses FR-008)
- [X] T028a [US3] Run univariate t-tests on features and save results to `data/processed/t_test_results.json`; Verify file contains keys for each electrode-band pair with `p_value` and `t_statistic` (producer for T029)
- [X] T029 [US3] Implement Family-Wise Error (FWE) correction (Bonferroni or FDR) for univariate t-tests **specifically on alpha (8-12 Hz) at P3/Pz/P4 and beta (13-30 Hz) at F3/Fz/F4**; Append a list of objects to `data/processed/feature_metadata.json` under key `fwe_corrected_p_values`. **JSON Schema for objects: {'electrode': str, 'band': str, 'uncorrected_p': float, 'corrected_p': float, 'method': str}** (addresses FR-009)
 *Note: Depends on T028a and T024a/T024b (for target file).*
- [X] T030 [US3] Implement sensitivity analysis: sweep classification threshold and report FP/FN variation; Save sensitivity curve data to `data/processed/sensitivity_analysis.csv`; Verify file exists and contains columns `threshold`, `fp_rate`, `fn_rate` (addresses FR-010)
- [X] T031 [US3] Generate comprehensive `results.json` containing `participant_count`, `epoch_count`, `classification_results`, `statistical_corrections`, and `sensitivity_analysis`; Verify `results.json` exists and contains all listed keys with non-null values (addresses SC-002, SC-006)
- [X] T032 [US3] Validate success criteria: **Logic: Report `benchmark_status: deferred` in `results.json` if benchmark value is missing (SC-002); HALT if sample size < 100 (SC-005)**; compare metrics against SC-001 through SC-006 thresholds; Verify `results.json` contains `benchmark_status` key (addresses SC-002, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Update `README.md` with execution instructions; Verify instructions are clear and reproducible
- [X] T034b [P] Update `quickstart.md` with dependency details; Verify dependencies match `requirements.txt`
- [X] T035a [P] Refactor `code/preprocessing.py` to extract distinct filtering functions; Verify `filter_data` function exists and is unit-tested
- [X] T035b [P] Refactor `code/preprocessing.py` to extract distinct ICA functions; Verify `run_ica` function exists and is unit-tested
- [X] T036a [P] Profile memory usage of `code/preprocessing.py` and generate report; Verify report exists and identifies bottlenecks
- [X] T036b [P] Optimize epoch loading in `code/preprocessing.py` to meet the temporal constraint.; Verify pipeline runs within 6 hours on 2 CPU cores
- [X] T037 [P] Additional unit tests for preprocessing edge cases in `tests/unit/`
- [X] T038 Run quickstart.md validation to ensure reproducible execution

---

## Phase 7: Data Integrity & Compute Feasibility (Revision Concerns)

**Goal**: Ensure strict adherence to "Real Data Only" and "CPU-First" compute constraints, preventing fabrication and ensuring execution feasibility.

### Implementation for Data Integrity

- [X] T040 [P] [US1] Implement explicit dataset streaming logic using `datasets.load_dataset(..., streaming=True)` or chunked file reading for large OpenNeuro datasets to ensure memory footprint stays within available RAM limits without fabricating a toy subset (addresses "Large real datasets: STREAM" rule). **Verification: Ensure full dataset is processed (chunked) and not silently truncated.** (addresses "Large real datasets: STREAM" rule)
- [X] T041 [P] [US1] Add a pre-flight check in `code/verify_dataset.py` to explicitly validate that the target OpenNeuro dataset contains the required `events.tsv` markers or documented landmark timestamps before any download begins, preventing wasted CI time on invalid sources (addresses FR-001 verification)
- [X] T042 [P] [US2] Verify that `code/feature_extraction.py` uses `mne.time_frequency.tfr_morlet` with default float64 precision on CPU; explicitly document that no GPU acceleration or quantization is used to maintain CPU-tractability (addresses "Compute feasibility - CPU-first" rule)
- [X] T043 [P] [US3] Ensure `code/classification.py` uses `scikit-learn` permutation tests with a fixed random seed for reproducibility on CPU, avoiding any GPU-dependent deep learning libraries (addresses "Compute feasibility - CPU-first" rule)
- [X] T044 [P] [US1] Add a metadata field in `data/processed/metadata.json` explicitly stating the `data_source_url` and `fetch_method` (e.g., `mne.datasets.openneuro.fetch`) to satisfy "Verified Real Data Source" traceability (addresses "If a verified real data source is injected" rule)

**Checkpoint**: Data integrity and compute constraints are verified; no fabrication or GPU dependencies exist.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T004 must complete before T005** to ensure directory structure exists.
 - **T039 must complete before T010** to ensure 'Fail Loudly' logic is in place.
 - **T005 is a sequential hard gate**: Must complete before any data-dependent tasks (T010+) begin.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
 - **T035a (Refactor) must precede T034b (Update docs)** to ensure documentation reflects final code state.
- **Data Integrity (Phase 7)**: Must be completed before any data download or processing tasks (T010, T018, T025) to ensure strict adherence to real-data and CPU constraints.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`data/processed/epochs_cleaned.fif`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`data/processed/features_matrix.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **EXCEPT T005 which is a sequential hard gate**, **T004 which must precede T005**, and **T039 which must precede T010**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 7 tasks (T040-T044) can be implemented in parallel as they target distinct files or specific logic blocks.

---

## Sequential Example: User Story 1 (Data Pipeline)

```bash
# Launch tasks sequentially to respect single-file dependency and data flow:
# 1. Download & Validate
Task: "Implement dataset download and BIDS validation in code/preprocessing.py"
# 2. Filter
Task: "Implement bandpass filter (low-frequency cutoff) and notch filter (50/60 Hz) in code/preprocessing.py"
# 3. ICA
Task: "Implement automatic ICA artifact rejection using ica.find_bads_eog in code/preprocessing.py"
# 4. Epoch & Validate
Task: "Implement epoch segmentation (2-second windows) and sample size validation (HALT if <100 epochs/condition)"
```

**Note on Single-File Parallelism**: Tasks T010, T011, T012a, T012b, T013, T014, T015, T016, T017 all target `code/preprocessing.py`. They represent a sequential data pipeline (download → filter → ICA → epoch → validate) that **must be implemented sequentially** or via strict modularization to avoid merge conflicts. The [P] tag has been removed from these tasks to enforce this order.

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
 - Developer D: Phase 7 (Data Integrity & Compute Feasibility)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (with exception of T005 hard gate, T004/T005 ordering, and T039/T010 ordering)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, limited RAM, NO GPU. No 8-bit/4-bit quantization or CUDA-dependent libraries.
- **Manual Review**: T012b ensures FR-003 compliance by providing a log-based manual review path.
- **Deferred Benchmarks**: T032 handles '[deferred]' SC-002 values by reporting status while enforcing the pass/fail gating mechanism.
- **FWE Scope**: T029 explicitly limits FWE correction to univariate tests on specific electrodes/bands (P3/Pz/P4 alpha, F3/Fz/F4 beta).
- **Ordering Constraints**: T004 must precede T005; T039 must precede T010; T010 must complete before T011-T017; T018 must precede T023; T023 must precede T025.
- **Epoch Count Logic**: T014 enforces a strict halt if <100 epochs/condition to satisfy the Independent Test requirement of ≥100 epochs.
- **Real Data Only**: T039, T040, T041, T044 enforce strict "Real Data" and "Fail Loudly" policies to prevent fabrication.
- **CPU-First**: T042, T043 ensure all analysis remains CPU-tractable without GPU dependencies.
- **Single-File Sequentialism**: T010-T017 are now sequential (no [P] tag) to prevent merge conflicts in `code/preprocessing.py`.
- **Schema Definitions**: T023 and T029 now include explicit schema definitions for their output artifacts to ensure executability.
- **Task Splitting**: T024 has been split into T024a (calculation) and T024b (documentation) to ensure atomicity.