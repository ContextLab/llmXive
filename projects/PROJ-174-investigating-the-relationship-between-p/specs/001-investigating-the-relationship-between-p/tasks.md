# Tasks: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Input**: Design documents from `/specs/001-pupil-dilation-cognitive-load/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md` structure)
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

- [ ] T001a [P] Create project directories: `code/`, `tests/`, `data/raw/`, `data/processed/`, `outputs/`
- [ ] T001b [P] Create `.gitignore` to exclude `data/`, `__pycache__/`, `*.pyc`, and `outputs/`
- [ ] T001c [P] Verify directory structure matches plan.md layout

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T002a [P] Create `code/requirements.txt` with pinned versions: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `mne`, `pyyaml`, `tqdm`
- [ ] T002b [P] Setup Python 3.11 virtual environment in `code/` and install dependencies
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

### Configuration & Logging

- [ ] T004 [P] Setup configuration management (`config.yaml` with seeds, thresholds, paths)
- [ ] T005 [P] Initialize logging infrastructure to capture preprocessing exclusions to `code/logs/preprocess.log` (supplementary) AND generate `outputs/quality_report.csv` as the primary artifact for exclusion counts
- [ ] T006 Create base data models/entities (`code/data_model.py`) for Dataset and ModelResult
- [ ] T007 Setup provenance tracking utilities for raw data metadata (`data/raw/*_meta.json`)
- [ ] T008 Configure environment variables for data paths and OpenNeuro credentials
- [ ] T009 Create synthetic placeholder dataset generator for development (if real data unavailable)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Trial‑wise Pupil‑Load Correlations (Priority: P1) 🎯 MVP

**Goal**: Load raw eye-tracking data, preprocess signals, extract load proxies, and compute correlations.

**Independent Test**: Run the pipeline on a single dataset and verify output CSV contains required columns and Pearson-r values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for data loader validation in `tests/test_data_loader.py`
- [ ] T011 [P] [US1] Unit test for blink interpolation logic in `tests/test_preprocess.py`
- [ ] T012 [P] [US1] Integration test for full preprocessing pipeline in `tests/test_pipeline_us1.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data_loader.py` to ingest raw files (OpenNeuro ds004248) and convert to uniform CSV (`timestamp`, `x`, `y`, `pupil_diameter`)
- [ ] T014 [US1] Implement `code/preprocess.py` with blink interpolation and low-pass filter (≤4 Hz) handling missing samples (>30% exclusion)
- [ ] T015 [US1] Implement `code/features.py` to compute load proxies: search time, fixation count; **READ** target salience ONLY from stimulus metadata; if metadata is missing, **SKIP** the proxy and log `WARNING: Target salience missing; skipping proxy` (do NOT compute on-the-fly)
- [ ] T016 [US1] Implement `code/analysis.py` to calculate Pearson correlations (peak/mean/quantized vs. proxies) with Bonferroni correction
- [ ] T017 [US1] Implement quality report generation in `code/preprocess.py` writing exclusion counts to `outputs/quality_report.csv`
- [ ] T018 [US1] Create `code/main.py` orchestrator for US1 pipeline execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Linear Mixed‑Effects Model (Priority: P2)

**Goal**: Fit LME model predicting pupil metrics from load proxies with subject random intercepts.

**Independent Test**: Execute LME script and verify model summary includes coefficients, SEs, p-values, and likelihood-ratio test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/test_analysis.py`
- [ ] T020 [P] [US2] Unit test for LME model fitting with missing predictor handling in `tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T021 [US2] Extend `code/analysis.py` to fit LME model `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`; if target salience metadata is missing, **SKIP** that predictor entirely (do NOT fit a reduced model) and log a warning
- [ ] T022 [US2] Implement collinearity mitigation (VIF > 5 triggers Reduced Model for remaining predictors only) in `code/analysis.py`
- [ ] T023 [US2] Implement likelihood-ratio test logic comparing nested models
- [ ] T024 [US2] Add validation for sufficient trials per subject (<20 triggers RuntimeError unless aggregation config is enabled)
- [ ] T025 [US2] Output fixed-effect estimates, SEs, p-values to `outputs/lme_results.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulated Real‑Time Load Classification Prototype (Priority: P3)

**Goal**: Deploy sliding-window logistic regression classifier and evaluate on held-out data.

**Independent Test**: Run classifier on test set and verify confusion matrix, accuracy, and ROC-AUC are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for sliding window data slicing in `tests/test_classifier.py`
- [ ] T027 [P] [US3] Unit test for sensitivity analysis logic in `tests/test_classifier.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/classifier.py` with sliding-window logistic regression (200 ms updates, L2 regularization)
- [ ] T029 [US3] Implement ground-truth labeling logic: if independent measure absent, label by median split of search time, **remove** "predictive validity" claims from all outputs, and write an explicit limitation note to `outputs/limitations.md` stating "Ground truth is derived from search-time median split; predictive validity claims removed"
- [ ] T030 [US3] Implement `code/evaluate.py` to compute accuracy, precision, recall, ROC-AUC on held-out set
- [ ] T031 [US3] Implement sensitivity analysis sweeping thresholds across a range of small values, outputting full metric tables (accuracy, AUC) to `outputs/sensitivity_analysis.csv` with caveat if ground truth is derived from median split
- [ ] T032 [US3] Output continuous correlation between predicted probability and search time as auxiliary validation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Create `docs/pipeline.md` and update `README.md` with CLI usage and limitations
- [ ] T034a [P] Refactor `code/` to reduce cyclomatic complexity of `preprocess.py` and `analysis.py` to < 15 and remove unused imports
- [ ] T035a [P] Profile memory usage of `preprocess.py` and optimize to ensure peak RAM < 6GB
- [ ] T036 [P] Additional unit tests for edge cases (corrupted timestamps, missing metadata)
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for data loader validation in tests/test_data_loader.py"
Task: "Unit test for blink interpolation logic in tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement data_loader.py to ingest raw files"
Task: "Implement preprocess.py with blink interpolation"
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence