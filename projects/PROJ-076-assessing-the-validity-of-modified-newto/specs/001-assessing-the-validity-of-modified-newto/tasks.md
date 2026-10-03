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

- [ ] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/`, `state/`
- [ ] T001b [P] Create `code/models/`, `code/utils/`, `code/simulations/` subdirectories
- [X] T003a [P] Initialize `pyproject.toml` or `ruff.toml` with linting configuration (ruff/flake8)
- [X] T003b [P] Initialize `.black` or `pyproject.toml` formatting configuration (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Generate `contracts/dataset.schema.yaml` defining the schema for parsed galaxy data (FR-002, FR-003)
- [ ] T004b [P] Generate `contracts/fit_results.schema.yaml` defining the schema for model fit outputs (FR-007, FR-009)
- [ ] T004d Implement data schema validators in `tests/contract/test_schemas.py` matching the generated contracts (Depends on T004a AND T004b completion - removed [P] tag)
- [X] T005 [P] Create base configuration loader for `data/metadata.yaml` in `code/__init__.py`
- [X] T006 [P] Setup deterministic random seed utility in `code/utils.py` (global seed pinning)
- [X] T007 [P] Implement error handling wrapper for HTTP requests in `code/download.py` (retry logic)
- [X] T008 [P] Create logging infrastructure in `code/utils.py` to track pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download SPARC data, parse rotation curves, and filter for quality (inclination <10°, points ≥15)

**Independent Test**: Execute download and preprocessing scripts; verify output CSV has ≥15 points/galaxy and inclination uncertainty <10°.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for parsed galaxy schema in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Unit test for inclination filter logic in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

**⚠️ CRITICAL SEQUENCE**: T012 -> T016 -> T013 -> T014 -> T015. Do NOT run in parallel.

- [ ] T012 [US1] Implement SPARC downloader with a configurable retry logic mechanism (a limited number of attempts) in `code/download.py` (FR-001)
- [ ] T016 [US1] Implement checksum verification and metadata logging for downloaded SPARC data in `data/metadata.yaml` per Constitution Principle III (Data Hygiene). **Dependency**: T012 must complete first. (FR-001, Constitution Principle III)
- [ ] T013 [US1] Implement rotation curve parser in `code/preprocess.py` to extract radial distance, velocity, uncertainty. **Dependency**: T016 must complete first (requires verified data). (FR-002)
- [ ] T014 [US1] Implement quality filter in `code/preprocess.py` to exclude inclination uncertainty ≥10° and <15 points. **Dependency**: T013 must complete first. (FR-003)
- [ ] T015 [US1] Create `data/processed/filtered_galaxies.csv` and update `data/metadata.yaml` with download timestamp/version. **Dependency**: T014 must complete first.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Model Fitting and Goodness-of-Fit Computation (Priority: P2)

**Goal**: Fit MOND (simple) and NFW models to each galaxy; compute reduced χ², AIC, BIC; perform sensitivity analysis

**Independent Test**: Run fitting on a subset; verify metrics match analytical definitions and execute within 30s/galaxy.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for MOND 'simple' interpolating function in `tests/unit/test_mond.py`
- [X] T019 [P] [US2] Unit test for NFW profile with Gaussian prior in `tests/unit/test_nfw.py`
- [X] T020 [P] [US2] Integration test for fitting pipeline on sample galaxy in `tests/integration/test_fitting.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement MOND 'simple' model in `code/models/mond.py`: a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0) with a0=1.2e-10; include M/L (mass-to-light ratio) as a free parameter (FR-004, Plan Summary)
- [ ] T022 [P] [US2] Implement NFW model in `code/models/nfw.py` with concentration prior c ~ M_baryon^α (α=0.24, std=0.1 dex) and scale radius as free parameter. **Note**: Implements specific prior per FR-005 to ensure executability. (FR-005)
- [ ] T023 [US2] Implement fitting engine in `code/fit.py` using `scipy.optimize.curve_fit` with velocity uncertainty weighting. **Dependency**: T021 AND T022 must complete. (FR-006)
- [ ] T024 [US2] Implement metric calculator in `code/metrics.py` for reduced χ², AIC, BIC (FR-007)
- [ ] T025 [US2] Generate `results/fit_summary.csv` with all metrics per galaxy-model. **Dependency**: T023 and T024 must complete.
- [ ] T026 [US2] Implement sensitivity analysis in `code/sensitivity.py` sweeping χ² thresholds across a range of representative values and output `results/sensitivity_data.csv`. **Dependency**: T025 must complete. (FR-012, SC-006)
- [ ] T035 [US2] Generate `results/sensitivity_summary.txt` with a text-based summary of the sensitivity sweep results (pass rates per threshold) derived from `results/sensitivity_data.csv`. **Dependency**: T026 must complete. (FR-012, SC-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Residual Analysis and Statistical Comparison (Priority: P3)

**Goal**: Analyze residuals, perform block-bootstrap permutation test, apply Holm-Bonferroni correction, and generate verdicts

**Independent Test**: Run residual analysis; verify block-bootstrap p-values and corrected p-values are produced and compared to alpha thresholds.

**⚠️ PLAN CONFLICT NOTE**: The plan.md 'Complexity Tracking' section states 'permutation test [was] rejected', but spec.md FR-009 MANDATES 'block-bootstrap permutation test'. This task implements the SPEC requirement. The plan.md MUST be updated to reflect this decision in the next revision cycle.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for residual calculation in `tests/unit/test_residuals.py`
- [X] T029 [P] [US3] Unit test for block-bootstrap logic in `tests/unit/test_bootstrap.py`
- [X] T030 [P] [US3] Integration test for full statistical comparison in `tests/integration/test_statistics.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement residual calculator in `code/residuals.py` to compute (observed - predicted) distributions (FR-008)
- [ ] T032 [US3] Implement block-bootstrap permutation test in `code/residuals.py` resampling at galaxy level. **Note**: Implements spec FR-009 requirement despite plan.md rejection. (FR-009, US3)
- [ ] T033 [US3] Implement Holm-Bonferroni correction in `code/residuals.py` for multiple hypothesis tests. **Dependency**: T032 must complete. (FR-010)
- [ ] T034 [US3] Generate `results/residual_stats.csv` with mean, median, std, p-values per model. **Dependency**: T031, T032, T033 must complete.
- [ ] T036 [US3] Generate `results/analysis_verdict.md` by reading `results/residual_stats.csv` (T034 output) and applying the following logic: If p < 0.05, output "MOND preferred"; else if p > 0.95, output "NFW preferred"; else output "No significant difference". **Dependency**: T034 must complete. (SC-004, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Documentation updates in `docs/` (including the associational framing in paper text per FR-011)
- [ ] T050 Code cleanup and refactoring of `code/models/`, `code/residuals.py`
- [ ] T051 Performance optimization: ensure fitting loop <30s/galaxy (memory profiling)
- [ ] T052 [P] Additional unit tests in `tests/unit/` covering edge cases (malformed files, convergence failures)
- [ ] T053 Run `quickstart.md` validation and verify all checksums

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
- **Polish (Phase N)**: Depends on all desired user stories and revisions being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Specific Task Dependencies

- **T004d**: Depends on T004a AND T004b completion.
- **T012 -> T016 -> T013 -> T014 -> T015**: Strict sequential order in Phase 3.
- **T023**: Depends on T021 AND T022 completion.
- **T025**: Depends on T023 AND T024 completion.
- **T026**: Depends on T025 completion.
- **T035**: Depends on T026 completion.
- **T034, T036**: Depend on T031, T032, T033 completion.

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
3. Complete Phase 3: User Story 1 (Strictly sequential T012->T016->T013->T014->T015)
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
 - Developer A: User Story 1 (Data - Sequential)
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
- **Correction**: Phase 6 (Hypergraph Simulation) REMOVED due to unapproved scope creep (not in spec.md).
- **Correction**: T035 replaced (plot removed) with text summary to comply with SC-006.
- **Correction**: T016 updated to explicitly mandate checksums and metadata logging per Constitution Principle III (Data Hygiene) and placed BEFORE parsing.
- **Correction**: T004a, T004b split into two tasks for atomic execution.
- **Correction**: T013 updated to explicitly require verified data from T016 (removed [P] tag).
- **Correction**: T022 updated to specify α=0.24 and std=0.1 dex to satisfy FR-005 executability.
- **Correction**: T026 updated to specify exact threshold set {, 1.25, 1.5, 1.75} and removed [P] tag.
- **Correction**: T036 updated to explicitly name output file and input source, and removed [P] tag.
- **Correction**: T025 status changed to '[ ]' (not started) to resolve 'Pending' ambiguity.
- **Correction**: T032 updated to implement 'block-bootstrap permutation test' per spec FR-009, overriding plan.md.
- **Correction**: T004d [P] tag removed to reflect dependency on T004a/T004b.
- **Correction**: Phase 3 tasks reordered to enforce T012 -> T016 -> T013 -> T014 -> T015 sequence.