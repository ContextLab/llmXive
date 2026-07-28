# Tasks: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

**Input**: Design documents from `/specs/001-quantifying-the-information-content-of-entanglement/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies (numpy, scipy, h5py, pandas, matplotlib, seaborn, scikit-learn, tenpy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base `QuantumState` entity class in `code/models/quantum_state.py` supporting sparse representation
- [X] T005a [P] Implement external dataset validation in `code/data_loader.py` per FR-009: Check for Zenodo/HuggingFace datasets at startup. If absent or malformed, raise `E_DATASET_MISSING` and **exit immediately**. **NO internal generation fallback is permitted here**; internal generation is a separate feature (T013/T014) and not a recovery path for missing external data.
- [X] T005b [P] Implement internal data generation interface in `code/data_loader.py` for N=10-40; define the interface for ED/DMRG generators (T013/T014) to ensure consistent output format (HDF5/NumPy).
- [X] T006 [P] Setup sparse matrix utility functions in `code/utils/sparse_helpers.py` (CSR/CSC conversion, memory profiling)
- [X] T007 Create configuration manager for random seeds and system parameters in `code/config.py`
- [X] T008 Setup logging infrastructure to track numerical instabilities (NaN/Inf) and data exclusion in `code/logging_config.py`
- [ ] T009 Implement data validation schema checks for generated wavefunctions in `code/validators/data_schema.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute and correlate entanglement entropy with complexity (Priority: P1) 🎯 MVP

**Goal**: Load 1D Heisenberg/Ising wavefunctions, compute bipartite entanglement entropy via sparse SVD, estimate complexity via NCD, and correlate them.

**Independent Test**: Run pipeline on 10 fixed configurations (N=10-20); verify output includes valid correlation coefficient (r), p-value, and scatter plot; ensure runtime < 6h and RAM < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for sparse SVD entanglement calculation in `tests/unit/test_metrics.py`
- [X] T011 [P] [US1] Unit test for quantization and NCD calculation in `tests/unit/test_metrics.py`
- [X] T012 [P] [US1] Integration test for full US1 pipeline on small N in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement Exact Diagonalization (ED) generator in `code/data_loader.py` for N <= 20 using `scipy.sparse.linalg.eigsh` (Output: raw wavefunction coefficients in HDF5). Depends on T005b.
- [ ] T014 [US1] Implement DMRG generator in `code/data_loader.py` for N > 20 using `tenpy` with streaming/chunked processing to stay within RAM (Output: raw wavefunction coefficients in HDF5). Depends on T005b.
- [ ] T015 [US1] Implement bipartite entanglement entropy calculation in `code/metrics.py` using sparse SVD (`scipy.sparse.linalg.svds` with ARPACK). **MUST convert reduced density matrix to CSR/CSC format before calling svds**. Input: T013/T014 output. Output: Entanglement entropy and entropy per spin written to `data/processed/entanglement_metrics.csv`.
- [ ] T016 [US1] Implement complexity estimation in `code/metrics.py`: 1) **Quantize raw wavefunction coefficients to fixed-point signed integers** (16-bit) per FR-003a; 2) **Generate an internal size-matched random baseline** (random phases on product basis) locally for the NCD calculation; 3) Calculate **Normalized Compression Distance (NCD)** using gzip/lzma/bzip2 on the **quantized full wavefunction coefficients** relative to the internal baseline; 4) Output NCD as the primary complexity metric. **Self-contained: does not depend on T023**.
- [ ] T017 [US1] Implement correlation analysis in `code/statistics.py` using **partial correlation controlling for system size N** and **stratified analysis** (entropy per spin) to decouple system size from entanglement structure.
- [ ] T018 [US1] Implement scatter plot generation with regression line and annotations in `code/viz.py`
- [ ] T019 [US1] Add numerical stability checks (NaN/Inf exclusion) and fail-fast logic (E_DATA_INSUFFICIENT) in `code/metrics.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate and validate null models (Priority: P2)

**Goal**: Generate random product states and Haar-random ensembles (maximally mixed approx) as baselines; compute their metrics; compare against physical states to validate distinctness.

**Independent Test**: Generate a set of random product states and a set of Haar states.; verify product states have near-zero entropy/high complexity; verify Haar states have maximal entropy; confirm statistical distinction (t-test p < 0.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for random product state generation in `tests/unit/test_null_models.py`
- [ ] T021 [P] [US2] Unit test for Haar-random ensemble generation in `tests/unit/test_null_models.py`
- [ ] T022 [P] [US2] Integration test for null model comparison statistics in `tests/integration/test_us2_null_models.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement random product state generator in `code/null_models.py` (random phases on product basis). **Generates the full set of random product states for comparative analysis (FR-010), distinct from the internal baseline used in T016**.
- [ ] T024 [US2] Implement Haar-random pure state ensemble generator in `code/null_models.py` (a sample set of states) to approximate maximally mixed states.
- [ ] T025 [US2] Implement metric calculation for null models in `code/metrics.py` (reusing US1 logic for Entanglement and NCD)
- [ ] T026 [US2] Implement statistical comparison (Welch's t-test/ANOVA) between physical states and null models in `code/statistics.py`
- [ ] T027 [US2] Add visualization logic to plot null model clusters alongside physical states in `code/viz.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bootstrap resampling for confidence intervals (Priority: P3)

**Goal**: Perform bootstrap resampling on the dataset to generate confidence intervals for correlation coefficients.

**Independent Test**: Run bootstrap on multiple configurations; verify % CI output; ensure runtime < 2h for this step.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for bootstrap resampling logic in `tests/unit/test_statistics.py`
- [ ] T029 [P] [US3] Unit test for bias-corrected percentile method selection in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement bootstrap resampling engine with a sufficient number of iterations in `code/statistics.py` using **partial correlation controlling for system size N** and **stratified analysis** logic from T017. **Output: 95% confidence interval for the correlation coefficient**.
- [ ] T031 [US3] Implement confidence interval calculation (standard vs. bias-corrected based on skewness) in `code/statistics.py`.
- [ ] T032 [US3] Integrate bootstrap results into final correlation output structure in `code/statistics.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**Note**: Tasks T033-T037 (MPS analysis) were removed as they implemented unapproved scope not present in the spec.

- [ ] T033 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T034 Code cleanup and refactoring for memory efficiency
- [ ] T035 Performance optimization for DMRG streaming and sparse SVD
- [ ] T036 [P] Additional unit tests for edge cases (N=40, numerical instabilities) in `tests/unit/`
- [ ] T037 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (Self-contained NCD baseline)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Generates baseline for comparative analysis (FR-010)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data structure
- **Polish (Phase 6)**: Depends on US1, US2, US3 implementation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/DataLoaders before Metrics
- Metrics before Statistics
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for sparse SVD entanglement calculation in tests/unit/test_metrics.py"
Task: "Unit test for quantization and NCD calculation in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement Exact Diagonalization (ED) generator in code/data_loader.py"
Task: "Implement DMRG generator in code/data_loader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Self-contained, no US2 dependency)
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
 - Developer A: User Story 1 (Core Metrics) - Self-contained
 - Developer B: User Story 2 (Null Models) - Independent of A
 - Developer C: User Story 3 (Bootstrap)
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
- **Critical**: T005a implements the mandatory external dataset validation (FR-009) with strict exit behavior.
- **Critical**: T015 and T016 implement NCD and 16-bit quantization on full wavefunction coefficients as primary metrics per Spec FR-003/FR-003a, with internal baseline generation to ensure US1 independence.
- **Critical**: T017, T030 implement partial correlation and stratified analysis to avoid confounding.
- **Critical**: Phase 6 (MPS analysis) has been removed as it was unapproved scope.
- **Note**: T005a follows Spec FR-009 (exit on missing). The Plan's assumption that "No external datasets exist" contradicts this requirement; if the Plan is correct, FR-009 must be updated to make internal generation the primary source.