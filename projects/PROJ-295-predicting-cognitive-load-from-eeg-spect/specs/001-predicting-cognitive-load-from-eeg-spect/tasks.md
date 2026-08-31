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

- [ ] T000 [P] [US1] Implement `code/data/verify_dataset.py` to fetch `ds000246` (or `ds003465`) and verify the presence of `gaze.tsv`. **HALT** with `FileNotFoundError` and a clear message if gaze data is missing, flagging the spec for update. Output: `results/verification_report.json`. (Plan Phase 0, Step 1).
- [ ] T001 [P] [US1] Implement `code/data/power_analysis.py` to calculate minimum N required for R²=0.2 with ~128 predictors dynamically; **HALT** if actual_n < calculated_min_n, flagging study as underpowered. Output: `results/power_analysis_report.json`. (Plan Phase 0, Step 2).
- [ ] T002 [P] [US1] Implement `code/data/memory_check.py` to verify chunked loading logic with a subset, ensuring peak memory usage stays within acceptable operational limits. Output: `results/memory_check_report.json`. (Plan Phase 0, Step 3).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure per implementation plan: `mkdir -p code/data code/features code/models tests/unit tests/integration data/raw data/processed results`.

- [X] T001b [P] Update `state/` YAML with checksums and `updated_at` timestamp for the new project structure. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T004 Initialize Python 3.11 project with pinned dependencies (`mne`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `requests`) in `requirements.txt`
- [X] T005 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`
- [X] T006 Create `pipeline_config.yaml` with default signal processing parameters (1–45 Hz bandpass, 250 Hz downsampling, ICA settings)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/config.py` to load `pipeline_config.yaml` and environment variables
- [X] T006 Implement `code/data/loader.py` with chunked loading logic (by `epoch_id`) to ensure memory safety (≤ 6.5 GB)
- [X] T007 [P] Generate and save `data/manifest.yaml` containing fields: `url`, `version`, `checksum` to satisfy Constitution Principle VI. The task must produce the actual file, not just a generator script. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**
- [X] T008 [P] Implement `code/data/download.py` with a strict verification gate: fetch the primary dataset, check for `gaze.tsv`; if missing, raise a `FileNotFoundError` with a clear message and flag spec for the fallback dataset. **Do NOT implement automatic fallback.** **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

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

- [X] T014 [US1] Implement `code/data/preprocess.py` with full module logic: (1) Apply a Butterworth bandpass filter (1 Hz high-pass, 45 Hz low-pass, order=4) to remove DC offset and drift, (2) Apply a notch filter at line frequency to remove line noise (FR-001), (3) Downsample to Hz (FR-001), (4) Apply ICA for eye-blink artifact removal (FR-002), (5) Segment data into epochs aligned with behavioral events (FR-002), (6) Explicitly exclude subjects with > 50% rejected epochs to prevent bias (Edge Case), (7) Calculate and log epoch retention rate; halt if < 70% (SC-004), and (8) Log the final exclusion count. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Label Generation (Priority: P2)

**Goal**: Compute spectral power features (theta/alpha) and generate continuous cognitive load labels from gaze variance.

**Independent Test**: Can be fully tested by running the feature extraction module on a subset of clean epochs and verifying that the resulting feature matrix contains valid theta/alpha power ratios and that the label distribution is non-trivial.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T016 [P] [US2] Unit test for Welch's PSD calculation in `tests/unit/test_extract.py` (verify band limits)
- [X] T017 [P] [US2] Unit test for gaze variance calculation in `tests/unit/test_labels.py` (verify min-max scaling)
- [X] T018 [P] [US2] Unit test for missing value flagging in `tests/unit/test_validity.py` (verify > 5% threshold)

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/features/extract.py` to compute PSD using Welch's method (FR-003) with built-in **chunked loading logic** to ensure memory safety during PSD computation on the full dataset (SC-002). The module must extract mean power for theta and alpha bands per channel., handle division-by-zero using `EPSILON = 1e-9` (Edge Case) when calculating ratios, and flag epochs with > 5% missing sensor data for exclusion. **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

- [X] T026 [US2] Implement `code/features/labels.py` to derive continuous cognitive load score from gaze variance per epoch (FR-004), normalize labels via min-max scaling per subject (FR-004), identify and exclude epochs with > 5% missing sensor data (FR-003), and explicitly measure and report the stability and non-zero nature of extracted power values across subjects (SC-005). **Must run only after `data/processed/clean_epochs` artifact is produced and after T023.** **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Training and Statistical Validation (Priority: P3)

**Goal**: Train a Ridge Regression model, validate performance against baseline, and apply statistical corrections.

**Independent Test**: Can be fully tested by running the training and evaluation script on the held-out test set and verifying that the reported R² and RMSE values are calculated correctly and that the model outperforms the baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T025 [P] [US3] Unit test for Ridge Regression CV in `tests/unit/test_train.py` (verify subject-wise split)
- [X] T026 [P] [US3] Unit test for permutation testing in `tests/unit/test_evaluate.py` (verify null distribution)
- [X] T027 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_evaluate.py` (verify Bonferroni)

### Implementation for User Story 3

- [X] T036 [US3] Implement `code/models/train.py` to calculate the dynamic subject split size honoring the constraint (use a standard training/testing split) before training. **Must run before T035.**
- [X] T035 [US3] Implement `code/models/train.py` to perform a subject-wise split of subjects into train/test sets ensuring no subject overlap and create a distinct, non-overlapping held-out test set (FR-005, FR-006). **Must run after T036 and T026.** **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**
- [X] T037 [US3] Implement `code/models/evaluate.py` to compute Pearson correlation and RMSE on held-out test set (FR-006)
- [X] T038 [US3] Implement `code/models/evaluate.py` to compare model performance against a mean-baseline predictor (FR-006)
- [X] T039 [US3] Implement `code/models/evaluate.py` to apply Bonferroni correction to channel-wise correlations (FR-007)
- [X] T040 [US3] Implement `code/models/evaluate.py` to perform permutation testing for global significance: Perform a sufficient number of permutations to ensure statistical robustness, shuffle labels, and output p-value in `results/model_metrics.json`. (Plan Phase 4). **Must run after T035.**
- [X] T041 [US3] Implement `code/models/sensitivity.py` to vary gaze variance calculation windows (configured in `pipeline_config.yaml`), re-evaluate R², and store results in `results/sensitivity_report.csv` (FR-008). **Must run after T035.**
- [X] T044 [US3] Implement `code/main.py` to orchestrate the full pipeline: Data -> Features -> Model -> Report. **Must specify CLI arguments (`--data-dir`, `--output-dir`), expected output paths, and verify `main.py` runs end-to-end producing `results/model_metrics.json`.** **After completion, update `state/` YAML with checksums and `updated_at` timestamp.**

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] [Polish] Update `README.md` with installation steps and `quickstart.md` with the exact command `python code/main.py --data-dir data/processed --output-dir results`.
- [ ] T046 Code cleanup and refactoring of `code/` directory
- [ ] T047 Performance optimization for chunked loading and ICA processing
- [ ] T048 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T049 [P] [Polish] Add explicit power analysis documentation in `research.md` calculating minimum N for R²=0.2 with current predictor count, and implement the logic to halt if N < 120 (Plan Phase 0).
- [ ] T050 [P] [Polish] Implement `code/features/stimulus_control.py` to regress out stimulus complexity metrics (if available in metadata) or explicitly flag this as a limitation in the final report (Plan Phase 3).
- [ ] T051 [P] [Polish] Add a dedicated script `code/utils/verify_data_integrity.py` to run pre-flight checks on `data/raw` ensuring all required files (EEG, gaze.tsv) exist and match checksums in `manifest.yaml` before any heavy processing begins (Plan Phase 0).

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
Task: "Implement code/data/preprocess.py to apply 1–45 Hz bandpass filter, ICA, and exclusion logic"
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
- **Constitution Principle V**: State updates are now integrated into T001b, T007, T008, T014, T023, T026, T035, T044. No separate end-task for state updates.
- **Revision Note**: T049, T050, and T051 added to address Plan Phase 0 blocking checks (Power Analysis, Stimulus Control, and Pre-flight Integrity) which were identified as critical prerequisites for the research validity.
