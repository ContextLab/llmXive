# Tasks: Testing the Equivalence Principle with Satellite Laser Ranging

**Input**: Design documents from `/specs/001-testing-the-equivalence-principle-with-s/`
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

- [X] T001 Create project structure per implementation plan: `mkdir -p code/data code/models code/analysis code/utils code/tests contracts data/raw data/processed data/results docs`
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (copy list from plan.md Technical Context)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `config.py` to load paths, hyperparams, and `verified_dataset_urls` keys
- [X] T005 [P] Create `contracts/normal_point.schema.yaml` defining the SLR observation schema
- [X] T006 [P] Create `contracts/orbit_solution.schema.yaml` defining the fit results schema
- [ ] T007 [P] Create `contracts/eotvos_result.schema.yaml` defining the final metric schema
- [ ] T008 Implement `utils/logging.py` for standardized error handling and progress logging
- [ ] T009 Implement `data/ingestion.py` skeleton with `DataUnavailableError` check (trigger if `config.verified_dataset_urls` is empty). **Note**: The verified ILRS URLs for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette are hardcoded as pre-requisites in this task (e.g., `) to satisfy the 'Verified Accuracy' gate before implementation.
- [ ] T010 Setup `pytest` framework: create `tests/conftest.py`, `pytest.ini`, and `requirements-dev.txt`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Orbit Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download and clean SLR normal-point series for LAGEOS, Etalon, and Starlette.

**Independent Test**: Execute ingestion pipeline and verify output CSV contains ≥ 95% of available points with no NaN values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for URL validation and backoff retry logic in `tests/test_ingestion.py`
- [X] T012 [P] [US1] Unit test for quality filtering (>2cm residual exclusion) in `tests/test_preprocessing.py`
- [X] T013 [P] [US1] Integration test: Verify end-to-end download and CSV generation for LAGEOS-1 in `tests/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `data/ingestion.py` function `fetch_single_satellite(satellite_id: str, url: str) -> pd.DataFrame` to fetch data from ILRS (using `requests` with exponential backoff) for a single satellite ID.
- [ ] T014.1 [US1] Implement `data/ingestion.py` function `fetch_all_satellites(satellite_ids: list[str]) -> pd.DataFrame` to orchestrate the loop over all relevant satellites (LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette) and aggregate results into a single DataFrame.
- [ ] T015 [US1] Implement `data/ingestion.py` to parse raw SLR files into `NormalPoint` objects
- [ ] T016 [US1] Implement `data/preprocessing.py` to filter residuals > 2cm and handle sparse satellites
- [ ] T017 [US1] Implement time-alignment logic in `data/preprocessing.py` to merge multi-satellite datasets
- [~] T018 [US1] Add error handling for 403 errors and "Insufficient Data" (<500 points) warnings
- [ ] T019 [US1] Write output to `data/processed/cleaned_slr_data.csv` with checksum verification; record checksum in `data/processed/.checksums.json` in JSON format `{ "file": "cleaned_slr_data.csv", "sha256": "..." }` and ensure raw data is preserved unchanged

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Differential Acceleration Parameter Estimation (Priority: P2)

**Goal**: Run **joint** weighted least-squares orbit determination to estimate $a_c$ and $\eta$.

**Independent Test**: Verify **joint** solver convergence (residuals < 1e-5m) and correct calculation of $\eta$ with 95% CI.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for dynamical model components (geopotential, drag, SRP) in `tests/test_dynamics.py`
- [X] T021 [US2] Unit test for **joint** least-squares solver convergence in `tests/test_estimator.py` (TDD-first: depends on interface definition in T024)
- [X] T022 [US2] Unit test for $\eta$ calculation and covariance propagation in `tests/test_eotvos.py` (TDD-first: depends on interface definition in T024)

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `models/dynamics.py` with GGM05C geopotential, Jacchia drag, and SRP models; input: state vector, output: acceleration vector (ITRS coordinates, using `astropy.coordinates`)
- [ ] T024 [US2] Implement `models/estimator.py` for **joint** weighted least-squares fitting (stack residuals of both satellites into single vector, estimate shared $a_c$); output: joint solution object
- [~] T025 [US2] Implement function `extract_joint_parameters(solution: OrbitSolution) -> dict` to **extract** differential acceleration $a_c$ and local gravity $g$ **directly from the joint solution vector** and joint covariance matrix, returning a dictionary with keys `{'ac': float, 'g': float, 'covariance': np.array}`.
- [~] T026 [US2] Implement `analysis/eotvos.py` to compute $\eta = |a_c| / g$ and 95% CI from the joint covariance matrix
- [~] T027 [US2] Implement fallback logic for non-convergence (relax tolerance, log warning, output best-fit) as authorized by plan robustness requirements
- [ ] T028 [US2] Save `OrbitSolution` and `EotvosResult` to `data/results/orbit_solutions.json` and `data/results/eotvos_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Robustness Analysis (Priority: P3)

**Goal**: Perform F-test/BIC comparison and geopotential sensitivity analysis.

**Independent Test**: Verify sensitivity plot generation and correct application of multiple-comparison corrections.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for F-test and BIC calculation logic in `tests/test_validation.py`
- [X] T030 [P] [US3] Unit test for Bonferroni/Holm-Bonferroni correction logic in `tests/test_validation.py`
- [X] T031 [P] [US3] Integration test: Verify sensitivity sweep across 3 geopotential models in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `analysis/validation.py` for F-test and BIC model comparison (Null vs Alternative)
- [ ] T033 [US3] Implement `analysis/validation.py` to sweep GGM, EGM, and GOCO geopotential models. and record **Z-scores and p-values**
- [ ] T034 [US3] Implement `analysis/validation.py` function `apply_correction(p_values: list[float], method: str) -> list[float]` to support Bonferroni, Holm-Bonferroni, and Benjamini-Hochberg methods, returning corrected p-values.
- [ ] T035 [US3] Implement logic to flag "Unreliable" if Z-score variation > 20% across models
- [ ] T036 [US3] Generate sensitivity plot and save to `data/results/sensitivity_analysis.png`
- [ ] T037 [US3] Implement `analysis/report.py` to generate diagnostic report (chi2, eta limit, **p-value**, residuals CSV)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Compute Feasibility & Resource Validation (Priority: P4)

**Goal**: Validate pipeline execution within GitHub Actions free-tier constraints (time limits, CPU, and RAM).

**Independent Test**: Run full pipeline on subset and verify completion time < 6 hours.

### Implementation for User Story 4

- [ ] T038 [P] [US4] Implement `main.py` entry point with CLI arguments, runtime monitoring (check time periodically), and exit code behavior on timeout
- [ ] T039 [US4] Implement memory profiling hooks in `main.py` to warn if RAM > 6GB
- [ ] T040 [US4] Create `tests/test_feasibility.py` to run pipeline on 1-year subset and assert time < 6h
- [ ] T041 [US4] Document performance benchmarks and resource usage in `docs/performance.md`

**Checkpoint**: Feasibility validated for CI environment

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `docs/` (README, API reference)
- [ ] T043 Code cleanup and refactoring of `models/dynamics.py` for readability
- [ ] T044 Performance optimization: Vectorize `data/preprocessing.py` operations using NumPy
- [ ] T045 [P] Add unit tests for edge cases (missing data, empty results) in `tests/unit/`
- [ ] T046 Run `quickstart.md` validation to ensure reproducibility
- [ ] T047 Verify all artifacts have content hashes and versioning discipline applied

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T017, T019)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1, US2, US3 integration

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
Task: "Unit test for URL validation and backoff retry logic in tests/test_ingestion.py"
Task: "Unit test for quality filtering (>2cm residual exclusion) in tests/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement data/ingestion.py to fetch data from ILRS"
Task: "Implement data/preprocessing.py to filter residuals > 2cm"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Estimation)
 - Developer C: User Story 3 (Validation)
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
- **CRITICAL**: Ensure all data download tasks use verified, reachable URLs (ILRS/UCI) and never synthesize fake data.
- **CRITICAL**: All models must run on CPU-only (limited core count and memory) without GPU dependencies.
- **CRITICAL**: T024 depends on T017/T019 (data cleaning) - do not mark as [P] relative to Phase 3.
- **CRITICAL**: T021/T022 depend on T024 interface definition - do not mark as [P] relative to Phase 4 implementation.
- **CRITICAL**: T024 and T025 must implement **joint** estimation, not separate fits, to align with the plan's methodology and the updated spec.md (FR-003, FR-004).
- **CRITICAL**: Spec.md has been updated to reflect the 'joint' methodology; no tasks exist to modify the spec.