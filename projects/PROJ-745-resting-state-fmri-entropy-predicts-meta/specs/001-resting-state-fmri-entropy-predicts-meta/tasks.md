# Tasks: Resting-State fMRI Entropy Predicts Metacognitive Accuracy

**Input**: Design documents from `/specs/001-gene-regulation/`
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

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project directories: `projects/PROJ-745-resting-state-fmri-entropy-predicts-meta/`, `data/`, `code/`, `tests/`
- [ ] T002 [P] Create `.gitignore` rules for `data/`, `__pycache__/`, and virtual environments
- [ ] T003 [P] Create empty `__init__.py` files in `code/` and `tests/` directories
- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement data ingestion metadata fetcher in `code/download.py` (HCP metadata validation)
- [ ] T006 [P] Implement NIfTI download logic in `code/download.py` (fetch raw fMRI data to `data/raw/`)
- [X] T007 [P] Implement behavioral data download logic in `code/download.py` (fetch CSV/Parquet to `data/raw/`)
- [X] T008 [P] Implement motion scrubbing skeleton in `code/preprocess.py` (FD calculation logic)
- [X] T009 [P] Implement nuisance regression skeleton in `code/preprocess.py` (motion, CSF, WM regression)
- [X] T010 [P] Implement band-pass filtering skeleton in `code/preprocess.py` <!-- ATOMIZE: requested -->
- [~] T011 [P] Define data schema in `code/models.py` (Pydantic schemas or CSV headers for Subject, TimeSeries, EntropyMetric, MetacognitiveEfficiency)
- [ ] T012 [P] Configure error handling and logging infrastructure in `code/utils/logging.py` <!-- SKIPPED: non-mapping output -->
- [~] T013 [P] Configure environment configuration management (`.env` for HCP credentials, random seeds)
- [X] T014 [P] Implement automated state file update logic in `code/utils/state_manager.py` to update `updated_at` timestamp upon artifact changes (Constitution Principle V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, preprocess, and parcellate HCP resting-state fMRI data to derive clean, comparable time series.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a subset of HCP subjects and verifying that the output consists of time series per subject matching the Schaefer atlas with no NaN values and a valid mean framewise displacement metric.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T015 [P] [US1] Unit test for data download logic in `tests/unit/test_download.py`
- [X] T016 [P] [US1] Integration test for preprocessing output schema in `tests/integration/test_preprocess.py`

### Implementation for User Story 1

- [X] T017 [US1] Implement HCP data fetcher in `code/download.py` (handles raw NIfTI and behavioral CSVs)
- [X] T018 [US1] Implement motion scrubbing (FD > 0.5mm flagging) in `code/preprocess.py`: MUST flag and continue processing high-motion subjects per US-1 Acceptance Scenario 2
- [X] T019 [US1] Implement nuisance regression (motion, CSF, WM) and band-pass filtering in `code/preprocess.py` <!-- ATOMIZE: requested -->
- [X] T020 [US1] Implement Schaefer 400-region parcellation logic in `code/preprocess.py`
- [ ] T021 [US1] Add validation: check for zero-variance time series and exclude subjects in `code/preprocess.py`
- [ ] T022 [US1] Add logging for subject exclusion reasons (corrupted data, high motion, missing behavior)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entropy and Metacognitive Metric Computation (Priority: P2)

**Goal**: Compute multiscale sample entropy for each parcel and calculate metacognitive efficiency (meta-d′/d′) from behavioral data.

**Independent Test**: The computation module can be tested by feeding synthetic time series with known entropy properties and synthetic behavioral data with known meta-d′ values, verifying that the output matches theoretical expectations within an acceptable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for MSE calculation with synthetic data in `tests/unit/test_metrics_entropy.py`
- [ ] T024 [P] [US2] Unit test for meta-d′ calculation with synthetic behavior in `tests/unit/test_metrics_meta.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement multiscale sample entropy calculation using `nolds` in `code/metrics.py`: use scales τ=1–5, m=2, **configurable r parameter (default 0.15)** per spec.md US-2 and FR-006
- [ ] T026 [US2] Implement whole-brain aggregation (arithmetic mean across parcels) in `code/metrics.py`
- [ ] T027 [US2] Implement Type 2 SDT logic for meta-d′, d′, and efficiency ratio in `code/metrics.py`
- [ ] T028 [US2] Implement bootstrapping for bias correction of meta-d′/d′ in `code/metrics.py`
- [ ] T029 [US2] Add validation: check confidence rating completeness (>10% missing threshold) and exclude subjects
- [ ] T030 [US2] Add logging for metric validation failures and exclusion reasons

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Association and Sensitivity Analysis (Priority: P3)

**Goal**: Run linear regression to test association between entropy and metacognition, including sensitivity analysis on entropy tolerance parameter `r`.

**Independent Test**: The analysis module can be tested by running it on a small, pre-defined dataset where the correlation coefficient is known, verifying that the p-value is <0.05 and that the sensitivity sweep produces the expected trend.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for regression model with known coefficients in `tests/unit/test_analysis.py`
- [ ] T032 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T033 [US3] **Power Check**: Verify N ≥ 194 (per plan.md Statistical Rigor: r=0.2, power=0.8); **if N < 194, halt execution and report "Power Insufficient" error** (spec.md US-3 Acceptance Scenario 3)
- [ ] T034 [P] [US3] Implement linear regression model `meta_efficiency ~ entropy + age + sex + FD` in `code/analysis.py`
- [ ] T035 [US3] Implement Bonferroni correction for p-values and report regression coefficients in `code/analysis.py`
- [ ] T036 [US3] Implement sensitivity analysis: sweep `r` values across a low-magnitude range and report beta/p-value variation table
- [ ] T037 [US3] Implement consistency check: verify direction of association (sign of beta) remains constant across `r`
- [ ] T038 [US3] Add error handling for "Power Insufficient" halt and report limitation in final output

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T040 Code cleanup and refactoring of `code/metrics.py` for CPU efficiency
- [ ] T041 Performance optimization: ensure memory usage stays < 7 GB during full cohort processing
- [ ] T042 [P] Run full pipeline validation on a representative subset
- [ ] T043 Run quickstart.md validation script

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data outputs
- **Reviewer Revision (P4)**: Removed - Scope creep addressed by deletion.

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
Task: "Unit test for data download logic in tests/unit/test_download.py"
Task: "Integration test for preprocessing output schema in tests/integration/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement HCP data fetcher in code/download.py"
Task: "Implement motion scrubbing skeleton in code/preprocess.py"
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
- **CRITICAL**: All data ingestion must use verified URLs from HCP; no synthetic/fake data generation for final results.
- **CRITICAL**: All entropy calculations must use `nolds` on CPU; no GPU/quantization.
- **CRITICAL**: Power check (T033) MUST halt execution if N < 194; it does NOT proceed.
- **CRITICAL**: No mechanistic claims of causality; the study is purely statistical.
- **CRITICAL**: Entropy parameter `r` is configurable (default 0.15) to support sensitivity analysis.