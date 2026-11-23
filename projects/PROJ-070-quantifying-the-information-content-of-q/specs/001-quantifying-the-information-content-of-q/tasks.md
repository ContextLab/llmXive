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

- [ ] T001 Create project structure per implementation plan (folders: `code/`, `data/`, `tests/`, `docs/`)
- [X] T002 Initialize Python 3.11 project with dependencies (numpy, scipy, h5py, pandas, matplotlib, seaborn, scikit-learn, tenpy, pytest) in `requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base `QuantumState` entity class in `code/models/quantum_state.py` supporting sparse representation
- [X] T005a [P] Implement external dataset validation in `code/data_loader.py` per FR-009: At startup, check for Zenodo/HuggingFace datasets. If absent or malformed, **exit immediately with error code `E_DATASET_MISSING` and log the error**. Do NOT proceed to internal generation.
- [X] T005b [P] Implement internal data generation interface in `code/data_loader.py` for N=10-40; define the interface for ED/DMRG generators (T013/T014) to ensure consistent output format (HDF5/NumPy).
- [ ] T005c [P] Implement data generation orchestration in `code/main.py` to trigger internal generation (T013/T014) ONLY if the `--internal-only` flag is passed. If the flag is NOT passed, the system MUST rely on external datasets validated by T005a and exit with `E_DATASET_MISSING` if they are absent.
- [X] T006 [P] Setup sparse matrix utility functions in `code/utils/sparse_helpers.py` (CSR/CSC conversion, memory profiling)
- [X] T007 Create configuration manager for random seeds and system parameters in `code/config.py`
- [X] T008 Setup logging infrastructure to track numerical instabilities (NaN/Inf) and data exclusion in `code/logging_config.py`
- [X] T009 Implement data validation schema checks for generated wavefunctions in `code/validators/data_schema.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute and correlate entanglement entropy with complexity (Priority: P1) 🎯 MVP

**Goal**: Load 1D Heisenberg/Ising wavefunctions, compute bipartite entanglement entropy via sparse SVD, estimate complexity via NCD on reduced representations, and correlate them.

**Independent Test**: Run pipeline on 10 fixed configurations (N=10-20); verify output includes valid correlation coefficient (r), p-value, and scatter plot; ensure runtime < 6h and RAM < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for sparse SVD entanglement calculation in `tests/unit/test_metrics.py`
- [X] T011 [P] [US1] Unit test for quantization and NCD calculation in `tests/unit/test_metrics.py`
- [X] T012 [P] [US1] Integration test for full US1 pipeline on small N in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement Exact Diagonalization (ED) generator in `code/data_loader.py` for N <= 20 using `scipy.sparse.linalg.eigsh` (Output: raw wavefunction coefficients in HDF5). Depends on T005b.
- [X] T014 [US1] Implement DMRG generator in `code/data_loader.py` for N > 20 using `tenpy` with streaming/chunked processing to stay within RAM (Output: raw wavefunction coefficients in HDF5). Depends on T005b.
- [X] T015 [US1] Implement bipartite entanglement entropy calculation in `code/metrics.py` using sparse SVD (`scipy.sparse.linalg.svds` with ARPACK). **MUST convert reduced density matrix to CSR/CSC format before calling svds**. Input: T013/T014 output. Output: Entanglement entropy and entropy per spin written to `data/processed/entanglement_metrics.csv`.
- [ ] T016 [US1] Implement complexity estimation in `code/metrics.py`: 1) **Quantize input wavefunction coefficients to 16-bit signed integers** per FR-003a; 2) **Generate an internal size-matched random baseline** (random phases on product basis) locally; 3) **Quantize the internal baseline to 16-bit signed integers**; 4) **Calculate the raw compression ratio** (compressed_size / original_size) on **quantized reduced representations** (singular values of the reduced density matrix or subsystem vectors) and record it; 5) Calculate **Normalized Compression Distance (NCD)** using gzip/lzma/bzip2 on **quantized reduced representations** relative to the quantized baseline; 6) Output NCD, raw ratio, and quantized state hashes to `data/processed/complexity_metrics.csv`. **Self-contained: does not depend on T023**.
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

- [ ] T030 [US3] Implement bootstrap resampling engine with **exactly 1000 iterations** in `code/statistics.py` using the **partial correlation function (output artifact of T017)** and **stratified analysis** logic. **Output: Confidence interval for the correlation coefficient**.
- [ ] T031 [US3] Implement confidence interval calculation in `code/statistics.py`: Calculate skewness of the bootstrap distribution; if skewness > 0.5, use **bias-corrected percentile method**; otherwise, use **standard percentile method**.
- [ ] T031a [US3] Implement runtime verification for bootstrap in `tests/integration/test_us3_runtime.py`: Run 1000 iterations on a representative dataset and assert total runtime < 6 hours (SC-003).
- [ ] T032 [US3] Integrate bootstrap results into final correlation output structure in `code/statistics.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Review Revision - Grounding in Physics of Information (Priority: P1)

**Goal**: Address David Krakauer's review by implementing Matrix Product State (MPS) bond dimension as a computable surrogate for algorithmic complexity and comparing it against compression-based estimates.

**Independent Test**: Run pipeline on generated states; verify MPS bond dimension is computed; verify correlation exists between bond dimension and NCD; update research.md with Calabrese/Cardy and Brown/Susskind citations.

### Implementation for Research Review Revision

- [ ] T033 [P] [US1] Implement MPS bond dimension extraction in `code/metrics.py`. Use `tenpy` to convert wavefunctions (from T013/T014) to MPS form and extract the maximum bond dimension (χ) required to represent the state within a truncation error threshold (e.g., 1e-8). This serves as the "minimal bond dimension" surrogate.
- [ ] T034 [P] [US1] Implement correlation analysis between MPS bond dimension (χ) and compression-based NCD in `code/statistics.py`. Compare the strength of this correlation against the entanglement entropy vs. NCD correlation.
- [ ] T035 [P] [US1] Update `docs/research.md` to cite Calabrese & Cardy (2005) for entanglement entropy scaling and Brown & Susskind (2016) for circuit depth/complexity. Explicitly frame the MPS bond dimension as the tractable stand-in for algorithmic complexity proposed in the review.
- [ ] T036 [P] [US1] Add visualization in `code/viz.py` to plot MPS bond dimension (log scale) vs. Entanglement Entropy, and MPS bond dimension vs. NCD, to visually demonstrate the tripartite relationship.
- [ ] T037 [P] [US1] Add unit tests for MPS bond dimension extraction and correlation logic in `tests/unit/test_metrics.py` and `tests/unit/test_statistics.py`.

**Checkpoint**: Research methodology grounded in established physics literature; surrogate complexity metric validated.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Update `docs/quickstart.md` with CLI usage examples and data generation instructions
- [ ] T038b [P] Update `docs/data-model.md` with entity definitions and schema details
- [ ] T039 [P] Refactor T014 (DMRG generator) to use streaming iterators for wavefunction generation to ensure memory usage stays < 7GB on N=40.
- [ ] T040 [P] Add memory profiling to T015 (SVD calculation) and enforce a hard limit of < 6GB RAM on N=40; fail with E_MEMORY_EXCEEDED if exceeded.
- [ ] T041 [P] Additional unit tests for edge cases (N=40, numerical instabilities) in `tests/unit/`
- [ ] T042 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Research Review Revision (Phase 6)**: Depends on Foundational phase completion; can run in parallel with US1 implementation but requires US1 data structures.
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (Self-contained NCD baseline)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Generates baseline for comparative analysis (FR-010)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data structure
- **Research Review Revision (Phase 6)**: Depends on US1 data generation (T013/T014) to compute MPS metrics; depends on T016 for NCD comparison.
- **Polish (Phase 7)**: Depends on US1, US2, US3, and Phase 6 implementation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/DataLoaders before Metrics
- Metrics before Statistics
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3, and Phase 6 can start in parallel (if team capacity allows)
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
5. Add Research Review Revision (Phase 6) → Validate surrogate metrics → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Metrics) - Self-contained
 - Developer B: User Story 2 (Null Models) - Independent of A
 - Developer C: User Story 3 (Bootstrap)
 - Developer D: Research Review Revision (MPS Surrogate) - Depends on A's data generation
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: T005a enforces FR-009 by exiting with E_DATASET_MISSING if external data is missing. Internal generation is conditional on --internal-only flag.
- **Critical**: T016 implements NCD on **quantized reduced representations** (singular values/subsystem vectors) to satisfy the 7GB RAM constraint (SC-004) and Constitution Principle VI.
- **Critical**: T016 explicitly includes quantization of the input wavefunction coefficients to 16-bit integers and calculation of the raw compression ratio.
- **Critical**: T017, T030 implement partial correlation and stratified analysis to avoid confounding.
- **Critical**: Phase 6 (MPS analysis) has been added to address David Krakauer's review regarding the need for a computable surrogate (minimal bond dimension) for algorithmic complexity.
- **New**: T038a and T038b split documentation updates into specific file targets.
- **Note**: T030 explicitly specifies 1000 iterations to match Spec US-3.
- **New**: T033-T037 implement the MPS bond dimension surrogate and comparative analysis requested in the research review.
- **New**: T031a added to verify bootstrap runtime against the 6-hour constraint.
- **New**: T039 and T040 replaced vague cleanup tasks with specific refactoring and profiling actions.