# Tasks: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Input**: Design documents from `/specs/001-predicting-cognitive-load-eeg/`
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
 Implemented independently
 - Tested independently
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Data Verification & Power Analysis

**Purpose**: Verify dataset integrity and statistical power before implementation begins.

- [ ] T000 [P] [US1] Implement `code/data/verify_dataset.py` to fetch `ds000246` (or `ds003465`) and verify the presence of `gaze.tsv`. **HALT** with `FileNotFoundError` and a clear message if gaze data is missing, flagging the spec for update. **Output**: `results/verification_report.json` containing `status`, `message`, and `n_channels` (derived from dataset metadata). (Plan Phase 0, Step 1).
- [ ] T001 [US1] Implement `code/data/power_analysis.py` to calculate minimum N required for R²=0.2 with `n_channels * 2` predictors **derived from `results/verification_report.json` (T000 output)**. **HALT** if actual_n < calculated_min_n, flagging study as underpowered. **Output**: `results/power_analysis_report.json`. **Must run after T000**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.** (Plan Phase 0, Step 2).
- [ ] T002 [US1] Implement `code/data/memory_check.py` to verify chunked loading logic with a subset, ensuring peak memory usage stays within acceptable operational limits. **Output**: `results/memory_check_report.json`. **Must run after T008** (Foundational Phase). (Plan Phase 0, Step 3).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T003 [P] Create project structure per implementation plan: `mkdir -p code/data code/features code/models tests/unit tests/integration data/raw data/processed results`.

- [X] T004 [P] Update `state/` YAML with checksums and `updated_at` timestamp for the new project structure. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T005 [P] Initialize Python 3.11 project with pinned dependencies (`mne`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `requests`) in `requirements.txt`

- [X] T006 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/config.py` to load `pipeline_config.yaml` and environment variables.

- [X] T008 [P] Implement `code/data/loader.py` with chunked loading logic (by `epoch_id`) to ensure memory safety (≤ 6.5 GB).

- [X] T009 [US1] Implement `code/data/generate_manifest.py` to produce `data/manifest.yaml` containing fields: `url`, `version`, `checksum_sha256` (computed via SHA-256 of the downloaded tarball). **Must run after T010**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T010 [P] Implement `code/data/download.py` with a strict verification gate: fetch the primary dataset, check for `gaze.tsv`; if missing, raise a `FileNotFoundError` with a clear message and flag spec for the fallback dataset. **Do NOT implement automatic fallback**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T011 [P] Create `pipeline_config.yaml` with default signal processing parameters (–45 Hz bandpass, Hz downsampling, ICA settings).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and prepare the OpenNeuro EEG dataset, ensuring artifact-free data aligned with behavioral logs within memory constraints.

**Independent Test**: Can be fully tested by executing the data loading and ICA artifact removal script on the target runner and verifying that the output contains clean epochs with matching behavioral timestamps, while monitoring memory usage to ensure it stays within acceptable system limits.

### Test-First Sub-Phase for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for chunked loading logic in `tests/unit/test_loader.py` (verify memory peak < 7GB)
- [X] T013 [P] [US1] Unit test for dataset verification gate in `tests/unit/test_download.py` (verify halt on missing gaze data)
- [X] T014 [P] [US1] Integration test for full preprocessing pipeline in `tests/integration/test_preprocess.py` (verify ICA removal and epoch retention > 70%)

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/preprocess_filter.py` to apply a Butterworth bandpass filter (high-pass at a low frequency, 45 Hz low-pass) and a notch filter at line frequency. **Read filter parameters from `pipeline_config.yaml`**. **Must run after T010**. (Plan Phase 1, Step 2).
- [X] T016 [US1] Implement `code/data/preprocess_ica.py` to apply ICA for eye-blink artifact removal and retain only clean components. **Must run after T015**. (Plan Phase 1, Step 3).
- [X] T017 [US1] Implement `code/data/preprocess_epoch.py` to segment data into epochs aligned with behavioral events, exclude subjects with > 50% rejected epochs, calculate epoch retention rate, and **HALT execution if < 70%**. **Must run after T016**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.** (Plan Phase 1, Step 5).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Label Generation (Priority: P2)

**Goal**: Compute spectral power features (theta/alpha) and generate continuous cognitive load labels from gaze variance.

**Independent Test**: Can be fully tested by running the feature extraction module on a subset of clean epochs and verifying that the resulting feature matrix contains valid theta/alpha power ratios and that the label distribution is non-trivial.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T018 [P] [US2] Unit test for Welch's PSD calculation in `tests/unit/test_extract.py` (verify band limits)
- [X] T019 [P] [US2] Unit test for gaze variance calculation in `tests/unit/test_labels.py` (verify min-max scaling)
- [X] T020 [P] [US2] Unit test for missing value flagging in `tests/unit/test_validity.py` (verify > 5% threshold)

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/features/extract.py` to compute PSD using Welch's method (FR-003) with built-in **chunked loading logic** to ensure memory safety during PSD computation on the full dataset (SC-002). The module must extract mean power for theta and alpha bands per channel, handle division-by-zero using `EPSILON = 1e-9` (Edge Case) when calculating ratios, and flag epochs with > 5% missing sensor data for exclusion. **Must run after T017**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T022 [US2] Implement `code/features/labels.py` to derive continuous cognitive load score from gaze variance per epoch (FR-004), normalize labels via min-max scaling per subject (FR-004), identify and exclude epochs with > 5% missing sensor data (FR-003), and explicitly measure and report the stability and non-zero nature of extracted power values across subjects (SC-005). **Must run after T017 and T021**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Training and Statistical Validation (Priority: P3)

**Goal**: Train a Ridge Regression model, validate performance against baseline, and apply statistical corrections.

**Independent Test**: Can be fully tested by running the training and evaluation script on the held-out test set and verifying that the reported R² and RMSE values are calculated correctly and that the model outperforms the baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T023 [P] [US3] Unit test for Ridge Regression CV in `tests/unit/test_train.py` (verify subject-wise split)
- [X] T024 [P] [US3] Unit test for permutation testing in `tests/unit/test_evaluate.py` (verify null distribution)
- [X] T025 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_evaluate.py` (verify Bonferroni)

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/models/split.py` to perform a subject-wise split of subjects into train/test sets ensuring no subject overlap, dynamically calculate the split size, and save a **split manifest file**. **Must run after T022**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T027 [US3] Implement `code/models/evaluate.py` to perform **Channel Importance Analysis**: (1) Compute Pearson correlation per channel/band, (2) Apply Bonferroni correction (FR-007), (3) Generate a unified `results/channel_importance.json` report. **Must run after T026**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T028 [US3] Implement `code/models/train.py` to train Ridge Regression model with subject-wise k-fold CV, tune alpha, and evaluate on held-out test set (FR-005, FR-006). **Must run after T026**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T029 [US3] Implement `code/models/sensitivity.py` to perform sensitivity analysis (FR-008): **Iterate through a defined list of gaze variance window sizes**, **re-calculate labels** for each window, **re-execute the full training pipeline (T028 logic)** for each iteration, and store comparative R² results in `results/sensitivity_report.csv`. **Must run after T028**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T030 [US3] Implement `code/main.py` to orchestrate the full pipeline: Data -> Features -> Model -> Report. **Must specify CLI arguments (`--data-dir`, `--output-dir`), expected output paths, and verify `main.py` runs end-to-end producing `results/model_metrics.json`.** **Must run after T029**. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] [Polish] Update `README.md` with installation steps and `quickstart.md` with the exact command `python code/main.py --data-dir data/processed --output-dir results`.
- [ ] T032 Code cleanup and refactoring of `code/` directory
- [ ] T033 Performance optimization for chunked loading and ICA processing
- [ ] T034 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T035 [P] [Polish] Implement `code/features/stimulus_control.py` to regress out stimulus complexity metrics (if available in metadata) or explicitly flag this as a limitation in the final report (Plan Phase 3).
- [ ] T036 [P] [Polish] Add a dedicated script `code/utils/verify_data_integrity.py` to run pre-flight checks on `data/raw` ensuring all required files (EEG, gaze.tsv) exist and match checksums in `manifest.yaml` before any heavy processing begins (Plan Phase 0).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on features from US2 and data from US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (if applicable)
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
Task: "Unit test for chunked loading logic in tests/unit/test_loader.py"
Task: "Unit test for dataset verification gate in tests/unit/test_download.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/preprocess_filter.py to apply 1–45 Hz bandpass filter"
Task: "Implement code/data/preprocess_ica.py to apply ICA"
Task: "Implement code/data/preprocess_epoch.py to segment data and check retention"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify ICA removal and memory limits)
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Features/Labels)
 - Developer C: User Story 3 (Modeling/Stats)
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
- **Critical**: Ensure `code/data/download.py` halts if `gaze.tsv` is missing (Spec Contradiction Check) or falls back to `ds003465`
- **Critical**: Ensure all data loading uses chunking to stay within available memory constraints.
- **Critical**: Ensure no GPU usage or deep learning models are introduced
- **Constitution Principle V**: State updates are now integrated into T001, T004, T009, T010, T015, T016, T017, T021, T022, T026, T027, T028, T029, T030. No separate end-task for state updates.
- **Revision Note**: T015, T016, T017 split from original T015 for granularity. T026, T027 merged for Channel Importance. T029 updated for explicit sensitivity loop. T000/T001 fixed for data flow.