# Tasks: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Input**: Design documents from `/specs/001-narrative-archaeology/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on previous task output)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

## Phase 1: Setup & Infrastructure

**Purpose**: Project initialization and environment configuration

- [ ] T001-SETUP [P] **CRITICAL**: Initialize project directory structure, `requirements.txt`, `pyproject.toml` (with black/flake8 config), and `.flake8` files. **Output**: `projects/PROJ-588-narrative-archaeology-reverse-engineerin/code/` structure.
- [ ] T002-CONFIG [P] Implement `code/config.py` with pinned random seeds, CPU-only constraints, motion thresholds (3mm), and path definitions. **Output**: `code/config.py`.
- [ ] T003-UTILS-STATS [P] Create `code/utils/stats.py` for permutation testing (1000 iterations), FDR correction (q < 0.05), and Fisher's Z aggregation logic. **Output**: `code/utils/stats.py`.
- [ ] T004-UTILS-VIZ [P] Create `code/utils/viz.py` for plotting RSA matrices and decoding accuracy with specific schema outputs. **Output**: `code/utils/viz.py`.
- [ ] T005-UTILS-LOGGING [P] Implement `code/utils/logging.py` for error handling: detect motion artifacts, skip subjects, and write JSON entries to `data/errors.log` with fields: `{timestamp, subject_id, error_code, motion_mm}`. **Output**: `code/utils/logging.py`.
- [ ] T006-UTILS-HYGIENE [P] Implement `code/utils/hygiene.py` for PII scanning and checksum verification. **Output**: `code/utils/hygiene.py`.
- [ ] T007-DATA-DOWNLOAD [P] Implement `code/data/download.py` with full checksum verification logic (md5/sha256) and OpenNeuro fetcher interface. **Output**: `code/data/download.py`, `data/raw/checksums.json`.
- [ ] T008-MODEL-SEMANTIC [P] Implement `code/models/semantic.py` to extract semantic features using pre-trained **BERT-base-uncased** (CPU-only, inference only). **Output**: `code/models/semantic.py`, `data/features/bert_embeddings.npy`. **Usage**: Features used for RSA (T021) or as covariates.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009-IMPLEMENT [S] [US1] Implement `code/data/preprocess.py` wrapper for fMRIPrep (v23.x). **Flags**: `--output-spaces MNI`, `--fs-no-reconall`, `--omp-num-threads 2`, `--nthreads 2`. **Output**: `code/data/preprocess.py`. **Constraint**: Must complete within 6 hours for 5 subjects on 2 vCPU/7GB RAM.
- [ ] T010-MOTION [S] [US1] Implement motion artifact detection logic in `code/data/preprocess.py` (threshold >3mm). Skip subjects exceeding threshold, log to `data/errors.log` (JSON), proceeding with the remaining subjects. **Output**: `code/data/preprocess.py` (updated).
- [ ] T011-EXEC [S] [US1] Implement sequential execution wrapper logic in `code/data/preprocess.py` to process 5 subjects (first 5 alphabetically) on the free-tier runner. **Output**: `code/data/preprocess.py` (updated). **Constraint**: Must complete within 6 hours.
- [ ] T012-SEGMENT [S] [US1] Implement `code/data/segment.py` to align story events (plot, character, theme) with BOLD signal using HRF convolution (double-gamma). **Output**: `data/processed/events_aligned.csv` with `≤ 5%` missing timepoints. **Dependency**: Must complete after T011.
- [ ] T013-ROI-MASKER [S] [US1] Create `code/data/roi_masker.py` to extract timecourses for hippocampus, mPFC, PCC, and lateral temporal cortex for **both Early and Late event phases separately**. **Output**: `data/processed/roi_timecourses.h5`. **Dependency**: Must complete after T012.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, preprocess, and segment the Natural Stories fMRI dataset into event-aligned timecourses.

**Independent Test**: Verify that a 5-subject subset produces preprocessed NIfTI files, a valid event CSV with timestamps, and correctly aligned ROI masks within the CI limit.

### Implementation for User Story 1

- [ ] T014-RUN [S] [US1] Orchestrate download of a **5-subject subset** (first 5 alphabetically) of ds000234 using `code/data/download.py` (T007) with checksum validation. **Output**: `data/raw/ds000234/`. **Dependency**: Must complete before T009.
- [ ] T015-RUN [S] [US1] Configure and run preprocessing pipeline for the 5-subject subset using `code/data/preprocess.py` (T009, T010, T011). **Output**: `data/processed/`. **Dependency**: Must complete after T014.
- [ ] T016-VERIFY-SEGMENT [P] [US1] Verify event segmentation output: Assert `missing_timepoints_ratio <= 0.05` in `tests/integration/test_segmentation.py`.
- [ ] T017-VERIFY-HYGIENE [P] [US1] Implement data hygiene: Verify checksums in `data/raw/`, ensure no in-place modifications, and enforce PII scanning. **Output**: `data/hygiene.log`.

**Checkpoint**: User Story 1 is fully functional; clean, event-aligned dataset is ready for analysis.

---

## Phase 4: User Story 2 - Early vs. Late Event Pattern Comparison (Priority: P2)

**Goal**: Compare neural patterns between Early and Late events (Adapted from Encoding vs. Recognition) using RSA to identify reconfiguration in hippocampus and mPFC.

**Independent Test**: Compute RSA matrices and verify that Early-Late dissimilarity is significantly higher than Early-Early (p < 0.05).

### Implementation for User Story 2

- [ ] T021 [S] [US2] Implement `code/models/rsa.py` to compute dissimilarity matrices for **Early Event vs. Late Event** phases. **Formula**: `RDM[i,j] = 1 - corr(timecourse_i, timecourse_j)`. **Output**: `results/rsa_matrices.json` (schema: `{roi: {early_late: float, early_early: float}}`). **Dependency**: Requires T013 (ROI timecourses) and T008 (Semantic features for covariates). <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [ ] T022 [S] [US2] Implement permutation testing logic in `code/utils/stats.py` with 1000 iterations and FDR correction (q < 0.05). **Output**: `results/permutation_pvalues.json`.
- [X] T023 [S] [US2] Implement Fisher's Z aggregation across subjects: `Z = 0.5 * ln((1+r)/(1-r))`. **Output**: `results/group_rsa_stats.json`.
- [ ] T024 [P] [US2] Visualize top differing ROIs (mPFC, hippocampus) in `code/utils/viz.py`. **Output**: `results/rsa_heatmaps.png`.
- [ ] T025-IMPLEMENT [S] [US2] Implement "Early vs. Late Event Stability" RSA analysis. **Metric**: `Stability = 1 - (Dissimilarity_Late - Dissimilarity_Early)`. **Output**: `results/stability_metrics.json`. **Dependency**: Requires T021.
- [ ] T025-DOC-GENERAL [S] [US2] Update `docs/methodology.md` to reflect the "Early vs. Late" adaptation as the primary analysis strategy and document the "Stability" metric formula: `Stability = 1 - (Dissimilarity_Late - Dissimilarity_Early)`. **Verification**: Verify the section exists via a grep check or specific string assertion in `tests/docs/test_methodology.py`. **Dependency**: Requires T025-IMPLEMENT.

### Tests for User Story 2

- [X] T019 [P] [US2] Unit test for RSA dissimilarity matrix calculation in `tests/unit/test_rsa.py`.
- [X] T020 [P] [US2] Integration test for permutation test convergence and FDR correction in `tests/integration/test_stats.py`.

**Checkpoint**: Pattern reconfiguration analysis is complete; statistical significance established.

---

## Phase 5: User Story 3 - Narrative Element Reconstruction (Priority: P3)

**Goal**: Train linear classifiers to predict narrative elements (plot, character, theme) from encoding patterns and evaluate accuracy against chance.

**Independent Test**: Verify that decoder accuracy exceeds chance (1/N) for at least one category and significantly outperforms a null shuffled-label model (p < 0.01).

### Implementation for User Story 3

- [ ] T030-PRIMARY [S] [US3] Implement `code/models/decoder.py` with Ridge Regression. **Logic**:
 1. **Aggregation**: If a category has <5 samples, aggregate into "Miscellaneous".
 2. **Validation (FR-011)**: Implement validation against a **held-out text set** (not the training set) to prevent circularity. **Action**: Record `validation_p_value` and `validation_accuracy` in `results/decoder_metrics.json`. Do not raise an error if validation fails; log the result and proceed.
 3. **Metric**: Calculate chance baseline as `1 / N_actual` (where N_actual is the count of unique labels after aggregation).
 4. **Output**: `results/decoder_metrics.json` with schema: `{'actual_N': int, 'adjusted_chance': float, 'original_N': int, 'accuracy': float, 'deviation_log': str, 'validation_p_value': float, 'validation_accuracy': float}`.
- [ ] T031 [S] [US3] Implement K-fold cross-validation (K=5) and accuracy reporting against chance baseline.
- [ ] T032 [S] [US3] Apply multiple-comparison correction (FDR) across narrative categories and ROIs.
- [ ] T033-LIM [P] [US3] **Document Limitation**: Explicitly record the absence of "told vs. experienced" control condition; describe "label shuffling" as the simulation method. **Output**: `docs/limitations.md`.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for semantic feature extraction (BERT CPU inference) in `tests/unit/test_semantic.py`.
- [X] T027 [P] [US3] Unit test for Ridge Regression/SVM training and K-fold cross-validation in `tests/unit/test_decoder.py`.
- [X] T028 [P] [US3] Integration test for null model comparison (shuffled labels) and FR-011 validation logging in `tests/integration/test_decoder.py`.

**Checkpoint**: Narrative element reconstruction is complete; accuracy and statistical validity confirmed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **CRITICAL**: US2 and US3 implementation can ONLY begin **after T008 (Semantic Feature Extraction)** and **T013 (ROI Timecourses)** complete.
 - US1 can proceed immediately after T014.
- **Phase 6 (Narrative Structure)**: Removed as out of scope.
- **Phase 7 (Biological Grounding)**: Removed as out of scope.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - **Requires T008 (Semantic Features) and T013 (ROI Timecourses)**.
- **User Story 3 (P3)**: Can start after Foundational - **Requires T008 (Semantic Features) and T013 (ROI Timecourses)**.
- **Phase 6 (Narrative Structure)**: Removed as out of scope.
- **Phase 7 (Biological Grounding)**: Removed as out of scope.

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks for that story to validate them.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel **EXCEPT T009-IMPLEMENT, T010-MOTION, T011-EXEC, T012-SEGMENT, T013-ROI-MASKER (Sequential)**.
- Once Foundational phase completes (specifically T008 and T013), US2 and US3 can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **ONLY AFTER T008 and T013 complete**.

---

## Parallel Example: User Story 1

```bash
# Launch implementation for User Story 1 (Sequential):
Task: "Orchestrate download of 5-subject subset of ds000234 using code/data/download.py" (T014-RUN)
Task: "Configure and run preprocessing pipeline for 5-subject subset using code/data/preprocess.py" (T015-RUN) -> MUST wait for T014

# Launch tests for User Story 1 (Parallel after implementation):
Task: "Unit test for OpenNeuro downloader in tests/unit/test_download.py"
Task: "Integration test for preprocessing pipeline on 5 subjects in tests/integration/test_preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (5 subjects)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Finalize Documentation (T025-DOC-GENERAL, T033-LIM)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done (specifically T008 and T013):
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Sequential (must wait for previous output)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Implementation first, then Tests)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on GitHub Actions free-tier (limited vCPU and RAM, no GPU) for a small subject subset. The spec (FR-001, SC-005) requires this. If the small-subject analysis exceeds the 6-hour limit, the spec/plan must be revised (plan kickback).
- **Data Integrity**: No synthetic data or hard-coded placeholders allowed.
- **Adaptation Note**: The "Encoding vs. Recognition" comparison (FR-004) is implemented as "Early vs. Late Event Stability" per the fallback authorization in FR-003 and FR-004.
- **Metric Definition**: SC-003 (1/N) is implemented using `N_actual` (observed unique labels after aggregation) to ensure calculability. The report documents the aggregation logic.
- **Semantic Features**: Task T008 uses BERT-base-uncased ONLY for RSA (T021) or as covariates. The decoder (T030) uses Neural Patterns -> Labels, avoiding circularity as per Plan methodology.
- **Validation Logic**: T030-PRIMARY now correctly implements FR-011 (held-out text set validation) by recording `validation_p_value` and proceeding, rather than halting the pipeline.
- **Removed Scope**: Phase 6 and 7 (T040-T049) have been removed as they contained unapproved scope creep (simulated reviewer feedback) and violated the "Verified Accuracy" principle by implementing features not in the ratified spec.