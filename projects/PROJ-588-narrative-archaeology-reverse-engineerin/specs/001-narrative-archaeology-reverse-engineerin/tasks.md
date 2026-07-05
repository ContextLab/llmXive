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
- [ ] T006 [P] Create `code/utils/viz.py` for plotting RSA matrices and decoding accuracy
- [ ] T007-SKELETON [P] [US1] Create `code/data/download.py` file skeleton with checksum verification interface (Utility Skeleton)
- [ ] T008-SKELETON [P] Create `code/data/preprocess.py` file skeleton for nilearn/niworkflows wrapper
- [ ] T008-LOGIC [P] Implement nilearn/niworkflows wrapper logic in `code/data/preprocess.py` (CPU-optimized)
- [ ] T008-DEV [P] Document Deviation Authorization: Explicitly record fMRIPrep -> nilearn swap in `docs/deviations.md` as required adaptation to FR-001 (2 vCPU constraint)
- [ ] T009 [P] Implement error handling infrastructure (skip subject on motion artifacts, log errors)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2-REV: Spec Revision (Required Adaptations)

**Purpose**: Formalize necessary deviations from the original spec to ensure task feasibility and alignment with the Plan.

- [ ] T002-REV-EXEC [P] [Spec] Execute update to `spec.md`: Update FR-004 and US-2 to explicitly authorize "Early vs. Late Event Stability" RSA analysis as a replacement for "Encoding vs. Recognition" due to dataset constraints (The dataset lacks a recognition phase.). This task MUST complete before Phase 4.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, preprocess, and segment the Natural Stories fMRI dataset into event-aligned timecourses.

**Independent Test**: Verify that a small subject subset produces preprocessed NIfTI files, a valid event CSV with timestamps, and correctly aligned ROI masks within the 6-hour CI limit.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for OpenNeuro downloader in `tests/unit/test_download.py`
- [ ] T011 [P] [US1] Integration test for preprocessing pipeline on 2 subjects in `tests/integration/test_preprocess.py`
- [ ] T012 [P] [US1] Verify event segmentation output matches annotation file (≤5% missing timepoints) in `tests/integration/test_segmentation.py`

### Implementation for User Story 1

- [ ] T013-RUN [US1] Orchestrate download of a subject subset of ds000234 using `code/data/download.py` (T007) with checksum validation
- [ ] T014-RUN [US1] Configure and run nilearn pipeline for ds000234 (specific flags, HRF convolution) using `code/data/preprocess.py` (T008)
- [ ] T015 [US1] Implement `code/data/segment.py` to align story events (plot, character, theme) with BOLD signal using HRF convolution
- [ ] T016 [US1] Create `code/data/roi_masker.py` to extract timecourses for hippocampus, mPFC, PCC, and lateral temporal cortex for **both Early and Late event phases separately**
- [ ] T017 [US1] Add robust error handling: skip subjects with motion artifacts (threshold defined in `code/config.py`) and log to `data/errors.log` with specific format
- [ ] T018 [US1] Implement data hygiene: checksum raw data, ensure no in-place modifications, enforce PII scanning

**Checkpoint**: User Story 1 is fully functional; clean, event-aligned dataset is ready for analysis.

---

## Phase 4: User Story 2 - Early vs. Late Event Pattern Comparison (Priority: P2)

**Goal**: Compare neural patterns between Early and Late events (Adapted from Encoding vs. Recognition) using RSA to identify reconfiguration in hippocampus and mPFC.

**Independent Test**: Compute RSA matrices and verify that Early-Late dissimilarity is significantly higher than Early-Early (p < 0.05).

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for RSA dissimilarity matrix calculation in `tests/unit/test_rsa.py`
- [ ] T020 [P] [US2] Integration test for permutation test convergence and FDR correction in `tests/integration/test_stats.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/models/rsa.py` to compute dissimilarity matrices for **Early Event vs. Late Event** phases (Adapted per Spec Rev T002-REV-EXEC)
- [ ] T022 [US2] Implement permutation testing logic in `code/utils/stats.py` with **1000 iterations** for convergence
- [ ] T023 [US2] Apply FDR correction (q < 0.05) across ROIs and report statistical significance
- [ ] T024 [US2] Visualize top differing ROIs (mPFC, hippocampus) in `code/utils/viz.py`
- [ ] T025-IMPLEMENT [US2] Implement "Early vs. Late Event Stability" RSA analysis in `code/models/rsa.py` (Primary Deliverable per Spec Rev T002-REV-EXEC)
- [ ] T025-DOC [US2] Update `docs/narrative_archaeology.md` to reflect the "Early vs. Late" adaptation as the primary analysis strategy

**Checkpoint**: Pattern reconfiguration analysis is complete; statistical significance established.

---

## Phase 5: User Story 3 - Narrative Element Reconstruction (Priority: P3)

**Goal**: Train linear classifiers to predict narrative elements (plot, character, theme) from recognition patterns and evaluate accuracy against chance.

**Independent Test**: Verify that decoder accuracy exceeds chance (1/N) for at least one category and significantly outperforms a null shuffled-label model (p < 0.01).

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for semantic feature extraction (BERT/CLIP CPU inference) in `tests/unit/test_semantic.py`
- [ ] T027 [P] [US3] Unit test for Ridge Regression/SVM training and K-fold cross-validation in `tests/unit/test_decoder.py`
- [ ] T028 [P] [US3] Integration test for null model comparison (shuffled labels) in `tests/integration/test_decoder.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/models/semantic.py` to extract semantic features using pre-trained BERT/CLIP (CPU-only, inference only)
- [ ] T030-PRIMARY [US3] Implement `code/models/decoder.py` with Ridge Regression/SVM for **N=20 plot points / N=10 characters** (Primary SC-003 Target)
- [ ] T030-FALLBACK [US3] Implement hierarchical aggregation in `code/models/decoder.py`: **Merge categories with N < 5 into "Miscellaneous" bin** if T030-PRIMARY fails power threshold. **Report accuracy against chance level 1/M (where M is aggregated count) and document deviation from SC-003 N=20/10 in results.**
- [ ] T031 [US3] Implement K-fold cross-validation and accuracy reporting against chance baseline (1/N)
- [ ] T032 [US3] Apply multiple-comparison correction (FDR) across narrative categories and ROIs
- [ ] T033-LIM [US3] **Document Limitation**: Explicitly record the absence of "told vs. experienced" control condition in dataset; describe "label shuffling" as the simulation method used for null models in `docs/limitations.md`

**Checkpoint**: Narrative element reconstruction is complete; accuracy and statistical validity confirmed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address specific reviewer feedback.

- [ ] T036 [P] Update documentation in `docs/` to reflect CPU-only constraints and adaptation strategies
- [ ] T037 Code cleanup: Refactor preprocessing to ensure strict memory limits (≤7GB RAM)
- [ ] T038 Performance optimization: Parallelize subject processing where possible within 2 vCPU limit
- [ ] T039 [P] Add comprehensive unit tests for all statistical utilities in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Spec Revision (Phase 2-REV)**: Must be completed before Phase 4 (US2) to authorize adaptations
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires preprocessed data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires preprocessed data and semantic features from US1/US2

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
Task: "Unit test for OpenNeuro downloader in tests/unit/test_download.py"
Task: "Integration test for preprocessing pipeline on 2 subjects in tests/integration/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Orchestrate download of 10-subject subset of ds000234 using code/data/download.py"
Task: "Configure and run nilearn pipeline for ds000234 using code/data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2-REV: Spec Revision (Authorizes adaptations)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Spec Revision together
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on GitHub Actions free-tier (limited vCPU and RAM, no GPU). No 8-bit quantization, no CUDA, no large model training.
- **Data Integrity**: All data must be real (OpenNeuro ds000234). No synthetic data or hard-coded placeholders allowed.
- **Adaptation Note**: The "Encoding vs. Recognition" comparison (FR-004) has been formally adapted to "Early vs. Late Event Stability" via Spec Revision T002-REV-EXEC due to dataset constraints.
- **Scope Boundary**: Tasks T033-T035 (control condition, emotional contours, transient traces) were removed as out of scope. Limitations are documented in T033-LIM. **Task T040 (tempo and rhythm analysis) was removed as out of scope.**
- **Metric Definition**: SC-003 (N=20/10) is the primary target; T030-FALLBACK (Aggregation) is conditional on power failure and includes explicit reporting of adjusted chance level.
- **Deviation Authorization**: The fMRIPrep -> nilearn swap is documented in T008-DEV.