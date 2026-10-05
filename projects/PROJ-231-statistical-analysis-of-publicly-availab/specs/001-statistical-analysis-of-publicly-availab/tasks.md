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

- [ ] T001a [P] Create `projects/PROJ-231-statistical-analysis-of-publicly-availab/` root directory
- [ ] T001b [P] Create `projects/PROJ-231-statistical-analysis-of-publicly-availab/code/__init__.py`
- [ ] T001c [P] Create `projects/PROJ-231-statistical-analysis-of-publicly-availab/data/raw/.gitkeep` and `data/processed/.gitkeep`
- [ ] T001d [P] Create `projects/PROJ-231-statistical-analysis-of-publicly-availab/tests/unit/.gitkeep` and `tests/contract/.gitkeep`
- [ ] T001e [P] Create `projects/PROJ-231-statistical-analysis-of-publicly-availab/.gitignore` and `requirements.txt` stub

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] [P] Create `code/config.py` with paths, seeds, and hyperparameters
- [ ] T006 [P] [P] Implement `code/update_state.py` to compute artifact hashes and update state YAML (Constitution Principle V)
- [ ] T007 [P] Create `code/logging_config.py` with JSON format logging at INFO, DEBUG, and ERROR levels
- [ ] T008 [P] Setup contract schema validators (`tests/contract/test_schemas.py`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Functional Representation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw CMIP6 data, handle missing values via spline-based imputation (per updated FR-001), and transform discrete time-series into smooth B-spline functions.

**Independent Test**: Run the ingestion pipeline on a small, fixed subset of CMIP6 models and verify that B-spline coefficients are generated without error and reconstructed curves match original data within tolerance (MSE ≤ 0.01).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for spline-based imputation in `tests/unit/test_ingestion.py`
- [ ] T010 [P] [US1] Unit test for B-spline basis expansion in `tests/unit/test_basis.py`
- [ ] T011 [US1] Integration test for full ingestion pipeline on sample data in `tests/integration/test_ingestion_pipeline.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement `code/ingestion.py`: Download CMIP6 data from `sungduk/wip_cmip6` via `datasets` library (implement download logic)
- [ ] T012b [P] [US1] Implement `code/ingestion.py`: Implement streaming fallback for datasets >7GB using `datasets.load_dataset(..., streaming=True)`
- [ ] T013 [US1] Implement `code/ingestion.py`: Handle missing values via **spline-based imputation** using `scipy.interpolate.CubicSpline`. **Requirement**: Sort data by time axis before interpolation; handle multi-dimensional data via explicit `axis` parameter; if CubicSpline raises a convergence error or produces NaNs, fallback to `scipy.interpolate.interp1d` with kind='linear'; flag affected models/time steps in logs (FR-001-AMENDED)
- [ ] T014 [US1] Implement `code/ingestion.py`: Standardize ensemble members across spatial grids and time steps (target: at a one-degree spatial resolution via bilinear interpolation); Write output as parquet files to `data/processed/standardized_{model}.parquet`
- [ ] T015 [US1] Implement `code/basis.py`: Pilot GCV/AIC selection to determine global basis dimension $K$ (FR-002)
- [ ] T016 [US1] Implement `code/basis.py`: B-spline basis expansion for each ensemble member using determined $K$ (FR-002)
- [ ] T017 [US1] Implement `code/basis.py`: Reconstruct curves from coefficients and verify MSE ≤ 0.01 (US1-AC2)
- [ ] T018 [US1] Save processed B-spline coefficients to `data/processed/` and update state hash

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

### Requirement Amendment Tasks for US1

- [ ] T013-AMEND [P] Update `spec.md` FR-001 text to replace "linear interpolation" with "spline-based imputation (CubicSpline) with linear fallback" to match T013 implementation. Verify spec text matches task.

---

## Phase 4: User Story 2 - Dominant Mode Extraction via fPCA (Priority: P2)

**Goal**: Perform Functional Principal Component Analysis (fPCA) to identify dominant spatiotemporal modes and cumulative variance.

**Independent Test**: Execute fPCA on prepared data and verify output includes sorted eigenvalues, eigenfunctions, and cumulative variance percentages.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for fPCA eigenvalue calculation in `tests/unit/test_fpca.py`
- [ ] T020 [P] [US2] Unit test for cumulative variance calculation in `tests/unit/test_fpca.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/fpca.py`: Load B-spline coefficients from `data/processed/` (Depends on T018)
- [ ] T022 [US2] Implement `code/fpca.py`: Execute fPCA using `scikit-fda` to extract dominant modes (FR-003)
- [ ] T023 [US2] Implement `code/fpca.py`: Calculate and report cumulative variance for top components. **Requirement**: Implement sensitivity analysis loop across a range of thresholds; if cumulative variance >= threshold, stop early. Write JSON file to `data/processed/variance_metrics.json` with keys: components, cumulative_variance, stopped_early, threshold_used (US2-AC2)
- [ ] T024 [US2] Save eigenvalues, eigenfunctions, and variance metrics to `data/processed/` (Depends on T023)
- [ ] T025 [US2] Implement `code/visualize.py`: Generate plots of dominant modes as spatiotemporal patterns (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Assessment via Leave-One-Out (LOO) Jackknife (Priority: P3)

**Goal**: Assess stability of dominant modes using **Leave-One-Out (LOO) Jackknife** (N iterations, where N is ensemble size) to test sensitivity to specific model families, as mandated by FR-004 (AMENDED) and Constitution Principle VI.

**Independent Test**: Run LOO loop (N iterations), calculate stability metrics (loading correlations), and report standard deviation of correlations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for LOO subsample generation in `tests/unit/test_robustness.py`
- [ ] T027 [P] [US3] Unit test for stability metric calculation in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [ ] T028-BASE [US3] Implement `code/robustness.py`: Compute **Full Ensemble Baseline** fPCA results (eigenvalues, eigenfunctions) required for comparison. This must be completed before T028-LOOP.
- [ ] T028-LOOP [P] [US3] Implement `code/robustness.py`: **Leave-One-Out (LOO) Jackknife** loop. **Requirement**: Accept `model_to_remove` parameter per worker; iterate N times (N = ensemble size); remove one model at a time to generate subsamples; compute fPCA for each subsample (FR-004-AMENDED). **Dependency**: Requires immutable baseline from T028-BASE.
- [ ] T028a [US3] [SC-002-AMENDED] Validate that the number of LOO iterations equals the ensemble size (N), ensuring full coverage of model removal (FR-004 statistical power requirement)
- [ ] T029 [US3] Implement `code/robustness.py`: Align eigenfunctions using Procrustes analysis as a preprocessing step for stability comparison (US3-AC1)
- [ ] T029b [US3] Implement `code/robustness.py`: **Calculate and report stability metrics** (loading correlations and standard deviation) comparing each LOO subsample's fPCA results to the full ensemble results (US3-AC1, FR-005)
- [ ] T030 [US3] Flag unstable modes (correlation < 0.95) and identify specific ensemble members causing instability. Write a JSON list of model IDs and correlation scores to `artifacts/unstable_modes.json` with schema: `[ { "model_id": str, "correlation_score": float } ]` (US3-AC3)
- [ ] T031 [US3] Generate histogram of stability metrics and uncertainty bands for visualizations (FR-006-AMENDED)
- [ ] T032 [US3] Save LOO results and stability metrics to `artifacts/` and update state hash

**Checkpoint**: All user stories should now be independently functional

### Requirement Amendment Tasks for US3

- [ ] T028-AMEND [P] Update `spec.md` FR-004 text to replace "bootstrap resampling (≥ 100 iterations)" with "Leave-One-Out (LOO) Jackknife (N iterations, where N is ensemble size)" to match T028 implementation. Verify spec text matches task.
- [ ] T031-AMEND [P] Update `spec.md` FR-006 text to replace "uncertainty bands derived from bootstrap resampling" with "uncertainty bands derived from LOO Jackknife" to match T031 implementation. Verify spec text matches task.
- [ ] T032-AMEND [P] Update `spec.md` SC-002 text to replace "correlation of eigenfunction loadings across 100 bootstrap iterations" with "correlation of eigenfunction loadings across N iterations (where N is ensemble size)" to match T032 implementation. Verify spec text matches task.
- [ ] T030-AMEND [P] Update `Constitution Principle VI` text to explicitly define the stability threshold of 0.95 for "stable against subsampling" to match T030 implementation. Verify constitution text matches task.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `specs/001-statistical-analysis-of-publicly-availab/` (update `research.md` with methodological justification for LOO Jackknife protocol and its effectiveness)
- [ ] T034 Code cleanup and refactoring
- [ ] T035 [P] **Performance Instrumentation**: Implement runtime/memory logging in `code/main.py`. Generate a compliance report at `artifacts/performance_compliance_report.md` containing a table with columns [Metric, Value, Limit, Status] verifying runtime < 6h and memory < 7GB to satisfy SC-003.
- [ ] T036 [P] Additional unit tests (if requested) in `tests/unit/` <!-- ATOMIZE: requested -->
- [ ] T037 Security hardening
- [ ] T038 [P] Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T018 -> T021)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 fPCA results (T024 -> T028-BASE)

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
- T028-LOOP tasks can run in parallel across different `model_to_remove` values

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
- **Methodology Note**: Leave-One-Out (LOO) Jackknife (N iterations) is used for robustness (FR-004-AMENDED) to test sensitivity to specific model families, as mandated by Constitution Principle VI and the approved plan.md.
- **Spec Alignment**: Tasks T013-AMEND, T028-AMEND, T031-AMEND, T032-AMEND, and T030-AMEND are required to ensure `spec.md` and `Constitution.md` reflect the actual implementation methodology.