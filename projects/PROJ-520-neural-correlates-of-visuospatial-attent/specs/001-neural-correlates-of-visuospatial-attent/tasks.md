# Tasks: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

**Input**: Design documents from `/specs/001-neural-attention-navigation/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. Required before any code-based verification can run.

- [X] T001 Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `logs/`, `tests/unit/`, `tests/integration/`. Verify directories exist via `ls`.
- [X] T002 Create placeholder files: `code/preprocessing.py`, `code/feature_extraction.py`, `code/classification.py`, `code/config.py`, `code/entities.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`.
- [X] T003 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (MNE-Python, numpy, scipy, scikit-learn, pandas)
- [X] T004 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story or dataset verification can begin.

**⚠️ CRITICAL**: No user story or data download work can begin until this phase is complete

- [X] T005 [P] Setup random seed management in `code/config.py` with key `random_seed` set to value `42` and configuration loading logic.
- [X] T006 [P] Setup logging infrastructure to `logs/preprocessing.log` and `logs/analysis.log` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 4, column 68:
... omprehensive logging module that:
 ^) -->
- [X] T007 [P] Create base data entity definitions (Epoch, Feature, PermutationResult) in `code/entities.py`

**Checkpoint**: Foundation ready - dataset verification and user story implementation can now begin

---

## Phase 3: Dataset Verification & Acquisition (Blocking Prerequisite)

**Purpose**: Verify dataset availability, content, and download the data before any preprocessing begins. Addresses FR-001 and SC-005.
**Dependencies**: Requires Phase 1 (Setup) for directories. Requires Phase 2 (Foundational) for entity definitions.

- [X] T008 [P] [US1] Implement dataset verification utility in `code/verify_dataset.py` to check BIDS compliance, navigation task conditions, and presence of required electrodes (P3, Pz, P4, F3, Fz, F4). **Input**: Downloaded dataset from T011.
- [X] T009 [P] [US1] Implement electrode presence check in `code/verify_dataset.py` to generate `data/electrode_metadata.json` documenting any skipped electrodes per Edge Cases. **Input**: Downloaded dataset from T011.
- [X] T010 [P] [US1] Implement epoch count pre-check in `code/verify_dataset.py` to estimate available epochs and flag power limitations before preprocessing starts. **Input**: Downloaded dataset from T011.
- [X] T010a [P] [US1] Implement pre-download source verification in `code/verify_dataset.py` to scan `research.md` for a verified dataset source. If no verified source is found in the `# Verified datasets` block, halt execution with error code 1 and log "No verified dataset found in research.md". This task executes before T011.
- [X] T011 [P] [US1] Implement dataset search and downloader in `code/download_data.py`. **Logic**:
 1. Query OpenNeuro API for datasets containing 'navigation' AND 'landmark' keywords.
 2. Verify metadata contains 'active' or 'passive' task conditions.
 3. **Constraint**: Do NOT hardcode any dataset ID (e.g., ds0001171).
 4. If a valid dataset is found, download it to `data/raw/`.
 5. If no valid dataset is found, halt with error code 1 and log "No verified navigation dataset found via OpenNeuro API".
 6. **Execution Order**: This task must run after T010a and before T008-T010.

---

## Phase 4: User Story 1 - EEG Data Pipeline and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess OpenNeuro EEG datasets for navigation tasks, including filtering, artifact removal, and epoch segmentation.

**Independent Test**: Verify the pipeline outputs a preprocessed data file containing ≥100 epochs labeled by condition (active/passive) with valid time-frequency features, running within the 6-hour CI budget.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Create test file `tests/unit/test_preprocessing.py` with function `test_epoch_count_validation` to verify epoch count logic.
- [X] T013 [P] [US1] Create test file `tests/integration/test_pipeline.py` with function `test_full_pipeline_execution` using mock data.

### Implementation for User Story 1

- [X] T014 [US1] Implement raw data loader in `code/preprocessing.py` using MNE-Python BIDS reader.
- [X] T015 [US1] Implement bandpass filter (1-40 Hz) and notch filter (50/60 Hz) in `code/preprocessing.py` per FR-002. **Constraint**: Apply bandpass first, then notch, to resolve conflict between Spec and Plan; verify residual line noise is <5%.
- [X] T016 [US1] Implement ICA-based artifact rejection with automatic component classification in `code/preprocessing.py` per FR-003. **Constraint**: Use CPU-only ICA algorithms; limit component estimation to prevent memory overflow.
- [X] T017 [US1] Implement epoch segmentation (2s, centered on attention shift) in `code/preprocessing.py` per FR-004.
- [X] T018 [US1] Add logic to handle missing electrodes (skip and log) and insufficient epoch counts: If <100 epochs per condition, exit with code 1 and log "W001: Insufficient epochs (<100) for power requirement". Do NOT proceed with 'underpowered' flag. Log message format: "Epoch Count: {count} - Status: {status}".
- [X] T019 [US1] Implement epoch rejection rate logging to `logs/rejection_report.json` with schema: `{ "total_epochs": int, "rejected_epochs": int, "rejection_rate": float, "timestamp": string }`.
- [X] T020 [US1] Implement data sampling strategy: If raw dataset size exceeds 6GB (approx. 70% of CI RAM limit), implement chunked loading or subject-subset selection to ensure processing completes within 7GB RAM and 6-hour time budget. **Constraint**: Selection strategy MUST be deterministic: 'Sort subjects by total epoch count descending, then select the top N subjects until the cumulative epoch count meets the minimum threshold'.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Time-Frequency Feature Extraction (Priority: P2)

**Goal**: Extract mean power values from alpha and beta bands over specific electrodes using Morlet wavelets.

**Independent Test**: Verify feature extraction produces an (epochs × features) matrix with alpha power (parietal) and beta power (frontal) within physiological ranges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for wavelet decomposition dimensions in `tests/unit/test_feature_extraction.py`.
- [X] T022 [P] [US2] Integration test for feature matrix generation in `tests/integration/test_features.py`.

### Implementation for User Story 2

- [ ] T023 [US2] Implement Morlet wavelet time-frequency decomposition (8-30 Hz) in `code/feature_extraction.py` per FR-005. Input: Preprocessed epochs from T014-T020. **Constraint**: Use low-complexity Morlet parameters (n_cycles=3, reference methodology sources for justification); generate frequency vector linearly spaced 8-30 Hz; ensure CPU feasibility. Remove [P] tag as this depends on US1 completion.
- [ ] T024 [US2] Implement baseline normalization (pre-stimulus interval -200ms to 0ms) for dB conversion in `code/feature_extraction.py`.
- [ ] T025 [US2] Extract mean power for alpha (8-12 Hz) @ P3, Pz, P4 in `code/feature_extraction.py` per FR-006.
- [ ] T026 [US2] Extract mean power for beta (13-30 Hz) @ F3, Fz, F4 in `code/feature_extraction.py` per FR-006.
- [ ] T027 [US2] Add validation to ensure ≥80% epochs have non-NaN values. Output validation result to `data/processed/validation_status.json` with schema: `{ "valid_epochs": int, "total_epochs": int, "status": string, "error_message": string }`.
- [ ] T028 [US2] Save feature matrix to `data/processed/features.csv` with explicit column headers.
- [ ] T029 [US2] Generate SHA-256 checksum for `data/processed/features.csv` and update `state/projects/PROJ-520-neural-correlates-of-visuospatial-attent.yaml` with the new artifact hash and derivation timestamp.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Classification and Statistical Validation (Priority: P3)

**Goal**: Train LDA classifier, validate with cross-validation and permutation testing, and apply statistical corrections.

**Independent Test**: Run classification pipeline and verify accuracy, precision, recall metrics, and a permutation p-value < 0.05 (or non-significance statement).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for permutation test logic in `tests/unit/test_classification.py`.
- [ ] T031 [P] [US3] Integration test for full classification and stats pipeline in `tests/integration/test_validation.py`.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement LDA classifier with 5-fold cross-validation in `code/classification.py` per FR-007.
- [ ] T033 [US3] Implement 1000-iteration permutation testing in `code/classification.py` per FR-008. **Constraint**: Use parallel processing (multiprocessing) to speed up permutation test on 2 CPU cores; ensure memory footprint remains < 7GB. Remove [P] tag as this depends on T032 completion.
- [ ] T034 [US3] Implement family-wise error correction (FDR/Bonferroni) for electrode-band t-tests ONLY. **Scope**: Correct for the multiple comparisons (6 electrodes x 2 bands) as defined in Plan Phase 3 Step 3. Do NOT apply to multivariate LDA accuracy. Per FR-009.
- [ ] T035 [US3] Implement sensitivity analysis (threshold sweep) to report FP/FN variation. Sweep range: LDA probability decision threshold across a broad spectrum from the baseline to high-confidence levels in incremental steps. Output format: JSON list of `{ "threshold": float, "accuracy": float, "fp_rate": float, "fn_rate": float }`. Per FR-010.
- [ ] T036 [US3] Generate `results.json` with exact schema: `{ "participant_count": int, "epoch_count": int, "classification_results": { "accuracy": float, "precision": float, "recall": float, "std_dev": float }, "statistical_corrections": { "fwe_p_values": [float], "permutation_p_value": float }, "sensitivity_analysis": [ { "threshold": float, "accuracy": float, "fp_rate": float, "fn_rate": float } ] }`. Aggregate outputs from T033, T034, and T035.
- [ ] T037 [US3] Implement success criteria validation logic (SC-001 to SC-006) including the Constitution Principle VII benchmark (accuracy >= 0.65) as a mandatory pass/fail target. Report status in `code/main.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates: Update `specs/001-neural-attention-navigation/quickstart.md` with new CLI flags and `README.md` with execution instructions.
- [ ] T039 Code cleanup and refactoring: Remove unused imports, enforce line length < 88, and verify no unused variables.
- [ ] T040 Performance optimization: Target memory usage < 5GB using `memory_profiler` to profile and optimize `code/preprocessing.py` and `code/feature_extraction.py`.
- [ ] T041 [P] Run `quickstart.md` validation: Execute `bash scripts/run_quickstart.sh`, verify exit code 0, and verify output string "Pipeline completed successfully".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all downstream work
- **Dataset Verification (Phase 3)**: Depends on Foundational (Phase 2) and Setup (Phase 1)
 - T010a must run before T011.
 - T011 must run before T008-T010.
- **User Stories (Phase 4+)**: All depend on Dataset Verification (Phase 3) and Foundational (Phase 2)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Dataset Verification (Phase 3) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Dataset Verification (Phase 3) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Dataset Verification (Phase 3) - Depends on US2 feature output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational and Dataset Verification phases complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Create test file tests/unit/test_preprocessing.py with function test_epoch_count_validation"
Task: "Create test file tests/integration/test_pipeline.py with function test_full_pipeline_execution"

# Launch all models for User Story 1 together:
Task: "Implement raw data loader in code/preprocessing.py"
Task: "Implement bandpass filter and notch filter in code/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: Dataset Verification (Download + Verify)
4. Complete Phase 4: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Dataset Verification → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Dataset Verification together
2. Once Foundation is done:
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
- **Compute Feasibility**: All tasks are designed for CPU-only execution (cores, 7GB RAM). No GPU-dependent libraries or quantization methods are used.