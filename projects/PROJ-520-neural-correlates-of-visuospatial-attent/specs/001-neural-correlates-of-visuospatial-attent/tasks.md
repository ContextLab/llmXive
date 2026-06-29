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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T005 is a hard gate**: Downstream tasks (T010+) cannot proceed if T005 fails, even if marked [P]. **T005 is NOT parallel-safe in execution; it must complete before any data-dependent tasks begin.**

- [X] T004 [P] Setup data directories structure (`data/raw`, `data/processed`) to ensure T005 can write logs and verify artifacts.
- [X] T005 [US1] Implement dataset verification script to validate OpenNeuro BIDS compliance and event markers [UNRESOLVED-CLAIM: c_b9870d78 — status=not_enough_info] in `code/verify_dataset.py`
 *Note: T004 must complete before T005 to ensure target directories exist.*
- [X] T006 [P] Setup configuration management for random seeds and file paths in `code/config.py`
- [X] T007 Create base data model entities (Epoch, Feature, ClassifierResult) in `code/models.py`
- [X] T008 Configure error handling and logging infrastructure for pipeline stages
- [X] T009 Setup environment configuration management for CI limits (CPU/RAM)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - EEG Data Pipeline and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess OpenNeuro EEG datasets, including bandpass filtering, artifact removal, and epoch segmentation around attention shift events.

**Independent Test**: Verify that the pipeline outputs a preprocessed data file containing ≥100 epochs labeled by condition (active/passive) with valid time-frequency features, and that the preprocessing runs successfully within the allocated CI time budget.

### Implementation for User Story 1

- [X] T010 [US1] Implement dataset download and BIDS validation in `code/preprocessing.py` (verifies FR-001)
 *Checkpoint: Download Complete - T011-T017 depend on T010 output.*
- [ ] T011 [US1] Implement bandpass filter (low-frequency cutoff) and notch filter (50/60 Hz) in `code/preprocessing.py` (addresses FR-002)
- [ ] T012a [US1] Implement automatic ICA artifact rejection using `ica.find_bads_eog` and `ica.find_bads_ecg` in `code/preprocessing.py` (addresses FR-003 auto-part)
- [ ] T012b [US1] Implement manual review capability: generate detailed log file of rejected components and visual inspection hints in `code/preprocessing.py` (addresses FR-003 manual-part)
- [ ] T013 [US1] Implement epoch segmentation (2-second windows) centered on attention shift events in `code/preprocessing.py` (addresses FR-004)
- [ ] T014 [US1] Implement sample size validation: halt if <50 epochs/condition; flag as underpowered if <100 epochs/condition [UNRESOLVED-CLAIM: c_207e5343 — status=not_enough_info] (addresses SC-005)
- [ ] T015 [US1] Implement fallback logic for missing event markers (use landmark timestamps) and document substitution in 'assumptions' section of `data/processed/metadata.json` with key `event_source: landmark_fallback` (addresses Edge Cases)
- [ ] T016 [US1] Handle missing electrode data: skip affected electrodes and log skipped electrodes in `data/processed/metadata.json` with key `skipped_electrodes` (addresses Edge Cases)
- [ ] T017 [US1] Save preprocessed epochs to `data/processed/epochs_cleaned.fif`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Time-Frequency Feature Extraction (Priority: P2)

**Goal**: Extract mean power values from alpha and beta bands over specific electrodes using Morlet wavelet decomposition.

**Independent Test**: Verify that feature extraction produces a matrix with dimensions (epochs × features) where features include alpha power from parietal electrodes and beta power from frontal electrodes, and that values fall within physiologically plausible ranges.

### Implementation for User Story 2

- [ ] T018 [US2] Implement Morlet wavelet time-frequency decomposition (low-frequency band) consuming `data/processed/epochs_cleaned.fif` in `code/feature_extraction.py` (addresses FR-005)
- [ ] T019 [US2] Implement baseline normalization (pre-stimulus interval to stimulus onset) for dB conversion. in `code/feature_extraction.py`
- [ ] T020 [US2] Extract mean alpha power for P, Pz, P4 electrodes from the normalized output of T019 in `code/feature_extraction.py` (addresses FR-006)
- [ ] T021 [US2] Extract mean beta power (beta frequency band) for F3, Fz, F4 electrodes from the normalized output of T019 in `code/feature_extraction.py` (addresses FR-006)
- [ ] T022 [US2] Implement feature validation: {{claim:c_c24bc9cf}} and log failures
- [ ] T023 [US2] Save feature matrix to `data/processed/features_matrix.csv` with dimensions (epochs × multiple) [UNRESOLVED-CLAIM: c_2585e127 — status=refuted]
- [ ] T024 [US2] Document electrode collinearity and correlation structure in `data/processed/feature_metadata.json`

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Classification and Statistical Validation (Priority: P3)

**Goal**: Train LDA classifier, validate with cross-validation and permutation testing, and perform sensitivity analysis.

**Independent Test**: Verify that classification pipeline reports accuracy, precision, and recall metrics alongside a permutation p-value < 0.05 or a clear statement of non-significance.

### Implementation for User Story 3

- [ ] T025 [US3] Implement LDA classifier training with k-fold cross-validation consuming `data/processed/features_matrix.csv` in `code/classification.py` (addresses FR-007)
- [ ] T026 [US3] Report accuracy, precision, recall with standard deviation across folds [UNRESOLVED-CLAIM: c_be0b3f2a — status=not_enough_info] in `code/classification.py`
- [ ] T027 [US3] Implement permutation testing with a sufficient number of iterations to establish statistical significance [UNRESOLVED-CLAIM: c_b65c8a62 — status=not_enough_info] in `code/classification.py` (addresses FR-008)
- [ ] T028 [US3] Report classifier p-value and null hypothesis rejection decision (α = 0.05) [UNRESOLVED-CLAIM: c_d0d8655e —status=not_enough_info] in `results.json`
- [ ] T028a [US3] Run univariate t-tests on features and save results to `data/processed/t_test_results.json` (producer for T029)
- [ ] T029 [US3] Implement {{claim:c_147c0918}} (Wikidata Q858572, https://www.wikidata.org/wiki/Q858572) for univariate t-tests on alpha (low-frequency range) at P3/Pz/P4 and beta (13-30 Hz) at F3/Fz/F4; append `fwe_corrected_p_values` to `data/processed/feature_metadata.json` (addresses FR-009, clarifies scope)
- [ ] T030 [US3] Implement sensitivity analysis: sweep classification threshold and report FP/FN variation [UNRESOLVED-CLAIM: c_26579e32 — status=not_enough_info] in `code/classification.py` (addresses FR-010)
- [ ] T031 [US3] Generate comprehensive `results.json` containing `participant_count`, `epoch_count`, `classification_results`, `statistical_corrections`, and `sensitivity_analysis`
- [ ] T032 [US3] Validate success criteria: perform pass/fail gating check against benchmark (value deferred) and report `benchmark_status: deferred` in `results.json`; compare metrics against SC-001 through SC-006 thresholds (addresses SC-002, SC-005)
- [ ] T033 [US3] Handle underpowered scenarios: halt if <50 epochs/condition; flag results as underpowered if <100 epochs/condition and adjust interpretation (aligns with SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `README.md` and `quickstart.md` with execution instructions and dependency details
- [ ] T034b [P] Update spec docs in `specs/001-neural-correlates-of-visuospatial-attent/` with final implementation notes
- [ ] T035a Refactor `code/preprocessing.py` to extract distinct functions for filtering and ICA to improve modularity
- [ ] T036a Profile memory usage in `code/preprocessing.py` and optimize epoch loading to ensure pipeline runs within 6 hours on 2 CPU cores
- [ ] T037 [P] Additional unit tests for preprocessing edge cases in `tests/unit/`
- [ ] T038 Run quickstart.md validation to ensure reproducible execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T004 must complete before T005** to ensure directory structure exists.
 - **T005 is a sequential hard gate**: Must complete before any data-dependent tasks (T010+) begin.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
 - **T035a (Refactor) must precede T034b (Update docs)** to ensure documentation reflects final code state.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **EXCEPT T005 which is a sequential hard gate** and **T004 which must precede T005**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement bandpass filter (1-40 Hz) and notch filter (50/60 Hz) in code/preprocessing.py"
Task: "Implement automatic ICA artifact rejection using ica.find_bads_eog in code/preprocessing.py"
Task: "Implement sample size validation: halt if <50 epochs/condition, warn if <100 epochs/condition"
```

**Note on Single-File Parallelism**: Tasks T011, T012a, T012b, T013, T014, T015, T016, T017 all target `code/preprocessing.py`. While marked [P] for parallel *development* (if using feature branches or flags), they must be implemented sequentially within the file or via strict modularization to avoid merge conflicts.

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

- [P] tasks = different files, no dependencies (with exception of T005 hard gate and T004/T005 ordering)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, limited RAM, NO GPU. [UNRESOLVED-CLAIM: c_b609d98d — status=not_enough_info] No 8-bit/4-bit quantization or CUDA-dependent libraries.
- **Manual Review**: T012b ensures FR-003 compliance by providing a log-based manual review path.
- **Deferred Benchmarks**: T032 handles '[deferred]' SC-002 values by reporting status while enforcing the pass/fail gating mechanism.
- **FWE Scope**: T029 explicitly limits FWE correction to univariate tests on specific electrodes/bands (P3/Pz/P4 alpha, F3/Fz/F4 beta).
- **Ordering Constraints**: T004 must precede T005; T010 must complete before T011-T017.