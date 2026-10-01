# Tasks: Statistical Analysis of Publicly Available Climate Model Output Ensembles

**Input**: Design documents from `/specs/001-statistical-analysis-of-publicly-availab/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`, `artifacts`)
- [ ] T005 [P] Create `code/config.py` with paths, seeds, and hyperparameters
- [ ] T006 [P] Implement `code/update_state.py` to compute artifact hashes and update state YAML (Constitution Principle V)
- [ ] T007 Create base logging and error handling infrastructure
- [ ] T008 Setup contract schema validators (`tests/contract/test_schemas.py`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Functional Representation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw CMIP6 data, handle missing values via spline-based imputation, and transform discrete time-series into smooth B-spline functions.

**Independent Test**: Run the ingestion pipeline on a small, fixed subset of CMIP6 models and verify that B-spline coefficients are generated without error and reconstructed curves match original data within tolerance (MSE ≤ 0.01).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for spline-based imputation in `tests/unit/test_ingestion.py`
- [ ] T010 [P] [US1] Unit test for B-spline basis expansion in `tests/unit/test_basis.py`
- [ ] T011 [US1] Integration test for full ingestion pipeline on sample data in `tests/integration/test_ingestion_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/ingestion.py`: Download CMIP6 data from `sungduk/wip_cmip6` via `datasets` library (streaming if >7GB)
- [ ] T013 [P] [US1] Implement `code/ingestion.py`: Handle missing values via **spline-based imputation** to preserve derivative structure for fPCA (FR-002, Constitution Principle VII) and flag affected models/time steps in logs (FR-001)
- [ ] T014 [US1] Implement `code/ingestion.py`: Standardize ensemble members across spatial grids and time steps
- [ ] T015 [US1] Implement `code/basis.py`: Pilot GCV/AIC selection to determine global basis dimension $K$ (FR-002)
- [ ] T016 [US1] Implement `code/basis.py`: B-spline basis expansion for each ensemble member using determined $K$ (FR-002)
- [ ] T017 [US1] Implement `code/basis.py`: Reconstruct curves from coefficients and verify MSE ≤ 0.01 (US1-AC2)
- [ ] T018 [US1] Save processed B-spline coefficients to `data/processed/` and update state hash

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dominant Mode Extraction via fPCA (Priority: P2)

**Goal**: Perform Functional Principal Component Analysis (fPCA) to identify dominant spatiotemporal modes and cumulative variance.

**Independent Test**: Execute fPCA on prepared data and verify output includes sorted eigenvalues, eigenfunctions, and cumulative variance percentages.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for fPCA eigenvalue calculation in `tests/unit/test_fpca.py`
- [ ] T020 [P] [US2] Unit test for cumulative variance calculation in `tests/unit/test_fpca.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/fpca.py`: Load B-spline coefficients from `data/processed/`
- [ ] T022 [US2] Implement `code/fpca.py`: Execute fPCA using `scikit-fda` to extract dominant modes (FR-003)
- [ ] T023 [US2] Implement `code/fpca.py`: Calculate and report cumulative variance for a small set of initial components. (US2-AC2)
- [ ] T024 [US2] Save eigenvalues, eigenfunctions, and variance metrics to `data/processed/`
- [ ] T025 [US2] Implement `code/visualize.py`: Generate plots of dominant modes as spatiotemporal patterns (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Assessment via Bootstrap Resampling (Priority: P3)

**Goal**: Assess stability of dominant modes using **Bootstrap Resampling (≥ 100 iterations)** to test sensitivity to ensemble composition, as mandated by FR-004 and US3.

**Independent Test**: Run Bootstrap loop (≥ 100 iterations), calculate stability metrics (loading correlations), and report standard deviation of correlations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Bootstrap subsample generation in `tests/unit/test_robustness.py`
- [ ] T027 [P] [US3] Unit test for stability metric calculation in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/robustness.py`: Bootstrap Resampling loop (≥ 100 iterations) generating random subsamples of ensemble members (FR-004)
- [ ] T028a [US3] Validate that Bootstrap iteration count ≥ 100 regardless of ensemble size (FR-004 statistical power requirement)
- [ ] T029 [US3] Implement `code/robustness.py`: Align eigenfunctions using Procrustes analysis as a preprocessing step for stability comparison (US3-AC1)
- [ ] T029b [US3] Implement `code/robustness.py`: **Calculate and report stability metrics** (loading correlations and standard deviation) comparing each subsample's fPCA results to the full ensemble results (US3-AC1, FR-005)
- [ ] T030 [US3] Flag unstable modes and identify specific ensemble members or patterns causing instability (US3-AC3)
- [ ] T031 [US3] Generate histogram of stability metrics and uncertainty bands for visualizations (FR-006)
- [ ] T032 [US3] Save Bootstrap results and stability metrics to `artifacts/` and update state hash

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `specs/001-statistical-analysis-of-publicly-availab/` (update `research.md` with methodological justification for Bootstrap vs LOO)
- [ ] T034 Code cleanup and refactoring
- [ ] T035 [P] **Performance Instrumentation**: Implement runtime/memory logging in `code/main.py` and generate a compliance report against GitHub Actions limits (limited CPU, 7 GB RAM, 6h) to satisfy SC-003
- [ ] T036 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T037 Security hardening
- [ ] T038 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 fPCA results

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
Task: "Unit test for spline-based imputation in tests/unit/test_ingestion.py"
Task: "Unit test for B-spline basis expansion in tests/unit/test_basis.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py: Download CMIP6 data"
Task: "Implement code/ingestion.py: Handle missing values via spline-based imputation"
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
- **Methodology Note**: Bootstrap Resampling (≥ 100 iterations) is used for robustness (FR-004) to ensure sufficient statistical power, replacing LOO Jackknife as documented in `research.md` to align with spec requirements.
