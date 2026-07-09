# Tasks: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Input**: Design documents from `/specs/001-narrative-archaeology/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies (nilearn, scikit-learn, transformers, pandas, numpy, openneuro-cli)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/config.py` with pinned random seeds, CPU-only constraints, and path definitions
- [ ] T005 [P] Create `code/utils/stats.py` for permutation testing and FDR correction logic
- [X] T006 [P] Create `code/utils/viz.py` for plotting RSA matrices and decoding accuracy
- [ ] T007-SKELETON [P] [US1] Create `code/data/download.py` file skeleton with checksum verification interface (Utility Skeleton)
- [ ] T008-SKELETON [P] Create `code/data/preprocess.py` file skeleton for nilearn/niworkflows wrapper
- [ ] T008-SEQ [P] Implement sequential execution wrapper logic in `code/data/preprocess.py`: Run fMRIPrep on individual subjects with flags `--output-spaces MNI`, `--fs-no-reconall`, `--omp-num-threads 2`, `--nthreads 2` to satisfy 7GB RAM constraints (Plan override of Spec FR-001)
- [ ] T009 [P] Implement error handling infrastructure (skip subject on motion artifacts, log errors)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, preprocess, and segment the Natural Stories fMRI dataset into event-aligned timecourses.

**Independent Test**: Verify that a small subject subset produces preprocessed NIfTI files, a valid event CSV with timestamps, and correctly aligned ROI masks within the CI limit.

### Implementation for User Story 1

- [ ] T013-RUN [US1] Orchestrate download of a subject subset of an OpenNeuro dataset (dsXXXXX). using `code/data/download.py` (T007) with checksum validation
- [ ] T014-RUN [US1] Configure and run nilearn pipeline for ds000234 (specific flags, HRF convolution) using `code/data/preprocess.py` (T008-SEQ)
- [ ] T015 [US1] Implement `code/data/segment.py` to align story events (plot, character, theme) with BOLD signal using HRF convolution
- [ ] T016 [US1] Create `code/data/roi_masker.py` to extract timecourses for hippocampus, mPFC, PCC, and lateral temporal cortex for **both Early and Late event phases separately**
- [ ] T017 [US1] Add robust error handling: skip subjects with motion artifacts (threshold defined in `code/config.py`) and log to `data/errors.log` with JSON format: `{"timestamp": "...", "subject_id": "...", "error_code": "...", "motion_mm": 0.0}`
- [ ] T018 [US1] Implement data hygiene: checksum raw data, ensure no in-place modifications, enforce PII scanning

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for OpenNeuro downloader in `tests/unit/test_download.py`
- [ ] T011 [P] [US1] Integration test for preprocessing pipeline on a small cohort of subjects in `tests/integration/test_preprocess.py`
- [ ] T012 [P] [US1] Verify event segmentation output matches annotation file (≤5% missing timepoints) in `tests/integration/test_segmentation.py`

**Checkpoint**: User Story 1 is fully functional; clean, event-aligned dataset is ready for analysis.

---

## Phase 4: User Story 2 - Early vs. Late Event Pattern Comparison (Priority: P2)

**Goal**: Compare neural patterns between Early and Late events (Adapted from Encoding vs. Recognition) using RSA to identify reconfiguration in hippocampus and mPFC.

**Independent Test**: Compute RSA matrices and verify that Early-Late dissimilarity is significantly higher than Early-Early (p < 0.05).

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/models/rsa.py` to compute dissimilarity matrices for **Early Event vs. Late Event** phases (Adapted per Spec FR-003/004 fallback)
- [ ] T022 [US2] Implement permutation testing logic in `code/utils/stats.py` with a sufficient number of iterations to ensure convergence.
- [ ] T023 [US2] Apply FDR correction (q < 0.05) across ROIs and report statistical significance
- [ ] T024 [US2] Visualize top differing ROIs (mPFC, hippocampus) in `code/utils/viz.py`
- [ ] T025-IMPLEMENT [US2] Implement "Early vs. Late Event Stability" RSA analysis in `code/models/rsa.py` (Primary Deliverable per Spec FR-003/004)
- [ ] T025-DOC [US2] Update `docs/narrative_archaeology.md` to reflect the "Early vs. Late" adaptation as the primary analysis strategy

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for RSA dissimilarity matrix calculation in `tests/unit/test_rsa.py`
- [ ] T020 [P] [US2] Integration test for permutation test convergence and FDR correction in `tests/integration/test_stats.py`

**Checkpoint**: Pattern reconfiguration analysis is complete; statistical significance established.

---

## Phase 5: User Story 3 - Narrative Element Reconstruction (Priority: P3)

**Goal**: Train linear classifiers to predict narrative elements (plot, character, theme) from recognition patterns and evaluate accuracy against chance.

**Independent Test**: Verify that decoder accuracy exceeds chance (1/N) for at least one category and significantly outperforms a null shuffled-label model (p < 0.01).

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/models/semantic.py` to extract semantic features using pre-trained **BERT-base-uncased** (CPU-only, inference only). **NOTE**: Features are used ONLY for RSA (T021) or as covariates, NOT as primary predictors for the decoder (T030), per Plan methodology.
- [ ] T030-PRIMARY [US3] Implement `code/models/decoder.py` with Ridge Regression for **N unique labels** (derived from data). **Logic**: If a category has <5 samples, aggregate into "Miscellaneous". **Metric**: Calculate chance baseline as `1/N_actual` where `N_actual` is the count of unique labels in the test fold *after* aggregation. Report `N_actual` and `adjusted_chance` in results.
- [ ] T031 [US3] Implement K-fold cross-validation and accuracy reporting against chance baseline (1/N_actual)
- [ ] T032 [US3] Apply multiple-comparison correction (FDR) across narrative categories and ROIs
- [ ] T033-LIM [US3] **Document Limitation**: Explicitly record the absence of "told vs. experienced" control condition in dataset; describe "label shuffling" as the simulation method used for null models in `docs/limitations.md`
- [ ] T030-REPORT [US3] Implement deviation reporting in `code/models/decoder.py`: When aggregation is used, report accuracy against chance level 1/M (where M is aggregated count) and explicitly document the deviation from SC-003 (static N) in the results JSON with schema: `{'actual_N': int, 'adjusted_chance': float, 'original_N': int}`.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for semantic feature extraction (BERT CPU inference) in `tests/unit/test_semantic.py`
- [ ] T027 [P] [US3] Unit test for Ridge Regression/SVM training and K-fold cross-validation in `tests/unit/test_decoder.py`
- [ ] T028 [P] [US3] Integration test for null model comparison (shuffled labels) in `tests/integration/test_decoder.py`

**Checkpoint**: Narrative element reconstruction is complete; accuracy and statistical validity confirmed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reviewers (Phase 6-7)**: **REMOVED**. These tasks were unapproved scope creep.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires preprocessed data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires preprocessed data and semantic features from US1/US2

### Within Each User Story

- Implementation tasks (Phase 3, 4, 5) MUST be completed before Test tasks for that story to validate them.
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
# Launch all implementation for User Story 1 together:
Task: "Orchestrate download of 10-subject subset of ds000234 using code/data/download.py"
Task: "Configure and run nilearn pipeline for ds000234 using code/data/preprocess.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for OpenNeuro downloader in tests/unit/test_download.py"
Task: "Integration test for preprocessing pipeline on 2 subjects in tests/integration/test_preprocess.py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Implementation first, then Tests)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on GitHub Actions free-tier (limited vCPU and RAM, no GPU). No 8-bit quantization, no CUDA, no large model training.
- **Data Integrity**: All data must be real (OpenNeuro ds000234). No synthetic data or hard-coded placeholders allowed.
- **Adaptation Note**: The "Encoding vs. Recognition" comparison (FR-004) is implemented as "Early vs. Late Event Stability" per the fallback authorization in FR-003 and FR-004.
- **Scope Boundary**: **Phase 6 and Phase 7 (tempo, affect, consolidation metrics) have been REMOVED.** These tasks were identified as unapproved scope creep absent from spec.md and plan.md, violating Constitution Principle IV (Single Source of Truth). The project strictly adheres to encoding/early-late pattern comparison and linear decoding.
- **Metric Definition**: SC-003 (1/N) is implemented using `N_actual` (observed unique labels after aggregation) to ensure calculability. The report documents the aggregation logic.
- **Deviation Authorization**: The fMRIPrep -> nilearn swap and sequential execution override are implemented in T008-SEQ per the Plan's explicit override. No local deviation doc task exists; the Plan serves as the authorization.
- **Semantic Features**: Task T029 uses BERT-base-uncased ONLY for RSA (T021) or as covariates. The decoder (T030) uses Neural Patterns -> Labels, avoiding circularity as per Plan methodology.
- **Reviewer Concerns Addressed**: Tasks related to "tempo", "affect", "consolidation" were removed as they were not authorized by the spec/plan.