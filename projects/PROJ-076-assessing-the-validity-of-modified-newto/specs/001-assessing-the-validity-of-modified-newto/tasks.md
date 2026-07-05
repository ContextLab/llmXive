# Tasks: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

**Input**: Design documents from `/specs/001-assessing-mond-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `results/`, `tests/`, `state/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scipy, numpy, pandas, requests, pyyaml, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement data schema validators in `tests/contract/test_schemas.py` matching `contracts/dataset.schema.yaml`
- [ ] T005 [P] Create base configuration loader for `data/metadata.yaml` in `code/__init__.py`
- [ ] T006 [P] Setup deterministic random seed utility in `code/utils.py` (global seed pinning)
- [~] T007 Implement error handling wrapper for HTTP requests in `code/download.py` (retry logic)
- [~] T008 Create logging infrastructure in `code/utils.py` to track pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download SPARC data, parse rotation curves, and filter for quality (inclination <10°, points ≥15)

**Independent Test**: Execute download and preprocessing scripts; verify output CSV has ≥15 points/galaxy and inclination uncertainty <10°.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T010 [P] [US1] Contract test for parsed galaxy schema in `tests/contract/test_dataset_schema.py`
- [~] T011 [P] [US1] Unit test for inclination filter logic in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement SPARC downloader with a configurable retry logic mechanism in `code/download.py` (FR-001)
- [~] T016 [US1] Implement validation in `code/download.py` to ensure no synthetic/fake data is used; verify real URLs (SPARC) immediately after download before any processing (FR-001, Data Hygiene)
- [~] T013 [US1] Implement rotation curve parser in `code/preprocess.py` to extract radial distance, velocity, uncertainty (FR-002)
- [~] T014 [US1] Implement quality filter in `code/preprocess.py` to exclude inclination uncertainty ≥10° and <15 points (FR-003)
- [ ] T015 [US1] Create `data/processed/filtered_galaxies.csv` and `data/metadata.yaml` with download timestamp/version

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Model Fitting and Goodness-of-Fit Computation (Priority: P2)

**Goal**: Fit MOND (simple) and NFW models to each galaxy; compute reduced χ², AIC, BIC; perform sensitivity analysis

**Independent Test**: Run fitting on a subset; verify metrics match analytical definitions and execute within 30s/galaxy.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for MOND 'simple' interpolating function in `tests/unit/test_mond.py`
- [ ] T019 [P] [US2] Unit test for NFW profile with Gaussian prior in `tests/unit/test_nfw.py`
- [ ] T020 [P] [US2] Integration test for fitting pipeline on sample galaxy in `tests/integration/test_fitting.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement MOND 'simple' model in `code/models/mond.py`: a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0) with a0=1.2e-10; include M/L (mass-to-light ratio) as a free parameter (FR-004, Plan Summary)
- [ ] T022 [P] [US2] Implement NFW model in `code/models/nfw.py` with concentration prior c ~ M_baryon^α, where α is a negative scaling exponent. (Plan Summary; Note: FR-005 spec typo flagged for correction) (FR-005)
- [ ] T023 [US2] Implement fitting engine in `code/fit.py` using `scipy.optimize.curve_fit` with velocity uncertainty weighting (FR-006)
- [ ] T024 [US2] Implement metric calculator in `code/metrics.py` for reduced χ², AIC, BIC (FR-007)
- [ ] T025 [US2] Generate `results/fit_summary.csv` with all metrics per galaxy-model
- [ ] T026 [US2] Implement sensitivity analysis in `code/sensitivity.py` sweeping χ² thresholds across the set of representative values and output `results/sensitivity_data.csv` (FR-012, SC-006)
- [ ] T035 [US2] Generate `results/sensitivity_report.md` with visualizations comparing pass rates for thresholds across a range of values and summary text (FR-012, SC-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Residual Analysis and Statistical Comparison (Priority: P3)

**Goal**: Analyze residuals, perform block-bootstrap permutation test, apply Holm-Bonferroni correction, and generate verdicts

**Independent Test**: Run residual analysis; verify block-bootstrap p-values and corrected p-values are produced and compared to alpha thresholds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for residual calculation in `tests/unit/test_residuals.py`
- [ ] T029 [P] [US3] Unit test for block-bootstrap logic in `tests/unit/test_bootstrap.py`
- [ ] T030 [P] [US3] Integration test for full statistical comparison in `tests/integration/test_statistics.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement residual calculator in `code/residuals.py` to compute (observed - predicted) distributions (FR-008)
- [ ] T032 [US3] Implement block-bootstrap permutation test in `code/residuals.py` resampling at galaxy level (FR-009, US3)
- [ ] T033 [US3] Implement Holm-Bonferroni correction in `code/residuals.py` for multiple hypothesis tests (FR-010)
- [ ] T034 [US3] Generate `results/residual_stats.csv` with mean, median, std, p-values per model
- [ ] T036 [US3] Generate `results/analysis_verdict.md` comparing calculated p-values against alpha=0.05 thresholds (SC-004, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (including the associational framing in paper text per FR-011)
- [ ] T038 Code cleanup and refactoring of `code/models/` and `code/residuals.py`
- [ ] T039 Performance optimization: ensure fitting loop <30s/galaxy (memory profiling)
- [ ] T040 [P] Additional unit tests in `tests/unit/` covering edge cases (malformed files, convergence failures)
- [ ] T041 Run `quickstart.md` validation and verify all checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires fit results from US2
- **Sensitivity Analysis (T035)**: Moved to Phase 4 as it depends on fit results (US2), not residuals (US3)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Fitting + Sensitivity)
 - Developer C: User Story 3 (Statistics + Verdict)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Correction**: Phase 6 removed to eliminate unapproved scope creep.
- **Correction**: Sensitivity analysis (T035) moved to Phase 4 to align with data dependencies.
- **Correction**: Task T027 removed to prevent data hygiene violation (no CSV disclaimers).
- **Correction**: Task T036 added to explicitly verify Success Criteria via alpha threshold comparison.
- **Correction**: Task T016 reordered to run before filtering to ensure data integrity.
- **Correction**: Removed T042-T045 (Rule Runner) to eliminate unapproved scope and synthetic data generation.
- **Correction**: Updated T026/T035 to explicitly enforce {1.0, 1.25, 1.5, 1.75} thresholds from SC-006.
- **Correction**: Updated T021 to include M/L parameter as per plan summary.
- **Flagged**: Spec FR-005 typo ($c \sim M_{baryon}^{()}$) vs Plan ($c \sim M_{baryon}^{\text{negative}}$); Task implements Plan.
- **Flagged**: Plan Complexity Tracking rejects permutation test vs Spec FR-009 mandates it; Task implements Spec.