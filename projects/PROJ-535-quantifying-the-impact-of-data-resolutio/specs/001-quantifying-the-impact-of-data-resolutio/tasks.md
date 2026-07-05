# Tasks: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

**Input**: Design documents from `/specs/001-quantify-resolution-impact/`
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

- [ ] T001 Create project structure by executing `mkdir -p projects/PROJ-535-quantifying-the-impact-of-data-resolutio/{code,data/raw,data/processed,tests/unit,tests/integration,specs/001-quantify-resolution-impact/contracts}`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, h5py, pandas, matplotlib, seaborn, scikit-learn, tqdm, pytest)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup configuration management in `code/config.py` (random seeds, paths, memory limits)
- [ ] T005 [P] Implement memory profiling utility in `code/utils/memory_monitor.py` (wraps `/proc/self/status` RSS checks)
- [ ] T006 [P] Create base data schemas: `velocity_field.schema.yaml` and `statistical_metrics.schema.yaml` in `specs/001-quantify-resolution-impact/contracts/`
- [ ] T007 Implement chunked HDF5 I/O utility in `code/utils/h5_io.py` to ensure RAM usage stays < 7GB
- [ ] T008 Setup environment configuration management (`.env` handling for JHTDB credentials)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Acquisition and Synthetic Downsampling (Priority: P1) 🎯 MVP

**Goal**: Download high-resolution isotropic turbulence snapshots from JHTDB and generate lower-resolution synthetic datasets via Fourier-mode truncation.

**Independent Test**: Verify that a single 1024³ snapshot can be downloaded, chunked, and downsampled to 256³ with zero high-wavenumber modes, while keeping RSS < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for Fourier truncation logic in `tests/unit/test_downsample.py` (verify k > Nyquist is zero)
- [ ] T010 [P] [US1] Unit test for memory profiling in `tests/unit/test_memory_monitor.py` (verify RSS check logic)
- [ ] T011 [P] [US1] Integration test for download pipeline in `tests/integration/test_download.py` (mock JHTDB, verify chunking)

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `TurbulenceSnapshot` and `ResolutionVariant` data classes in `code/models/data_models.py` to structure inputs/outputs for download and downsample tasks
- [ ] T017 [P] [US1] Implement metadata recording mechanism in `code/utils/metadata_io.py` to write/read `data/metadata.json` (checksums, dimensions, timestamps)
- [ ] T012 [P] [US1] Implement JHTDB fetcher in `code/download.py` with chunked reading, checksum verification, and calls to `metadata_io` (T017)
- [ ] T013 [US1] Implement Fourier-mode truncation in `code/downsample.py` (2/3 anti-aliasing rule, support factors, 4, 8, 16) using `data_models` (T014)
- [ ] T015 [US1] Add validation for grid dimensions and Reynolds number in `code/download.py` (add assertions to T012)
- [ ] T016 [US1] Add memory usage assertions in `code/download.py` and `code/downsample.py` (abort if > 7GB) (add assertions to T012/T013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Computation and Bias Quantification (Priority: P2)

**Goal**: Compute 3D energy spectra E(k) and structure functions S_p(r), then calculate relative bias against ground truth.

**Independent Test**: Verify that E(k) matches the Kolmogorov spectral slope. on a synthetic test case and bias is calculated correctly between two arrays.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Energy Spectrum calculation in `tests/unit/test_stats.py` (verify binning and FFT)
- [ ] T019 [P] [US2] Unit test for Structure Function calculation in `tests/unit/test_stats.py` (verify lag handling)
- [ ] T020 [P] [US2] Integration test for bias calculation in `tests/integration/test_bias.py` (verify relative error formula)

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement Energy Spectrum E(k) computation in `code/stats.py` (FFT-based, CPU-optimized) producing `data/processed/spectrum_{id}.npy`
- [ ] T022 [US2] Implement Longitudinal Velocity Structure Functions S_p(r) for p=2,3 in `code/stats.py` producing `data/processed/structure_fn_{id}.npy`
- [ ] T023 [US2] Implement Relative Bias calculation in `code/analysis.py` (signed percent error vs ground truth) consuming outputs from T021/T022
- [ ] T024 [US2] Implement bias aggregation logic to produce summary curves in `code/analysis.py`
- [ ] T025 [US2] Add handling for "Inertial Subrange Not Resolved" edge case in `code/stats.py`
- [ ] T026 [US2] Generate initial bias plots in `code/plot.py` (Bias vs Wavenumber)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Scaling Exponent Deviation and Confidence Interval Estimation (Priority: P3)

**Goal**: Fit power-law scaling exponents, perform conditional bootstrap resampling (if N ≥ 3), and estimate confidence intervals.

**Independent Test**: Verify that power-law fitting recovers the expected theoretical slope on synthetic data. and bootstrap CIs are calculated correctly if N ≥ 3.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Power-Law Fitting in `tests/unit/test_analysis.py` (verify R² and exponent extraction)
- [ ] T028 [P] [US3] Unit test for Bootstrap Resampling in `tests/unit/test_analysis.py` (verify CI bounds on synthetic noise)
- [ ] T029 [P] [US3] Integration test for Conditional Bootstrap logic in `tests/integration/test_bootstrap.py` (N=3 vs N<2 paths)

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement Power-Law Fitting (log-log regression) in `code/analysis.py` (extract exponents, R²) producing `data/processed/exponents.json`
- [ ] T031 [US3] Implement Conditional Bootstrap Logic in `code/analysis.py`: 
  - If N ≥ 3: Execute a sufficient number of iterations to ensure convergence and statistical stability. and prepare distribution for T031.1.
  - If N < 3: Generate `data/results/deterministic_report.json` with point estimates and "Deterministic Mode" flag.
- [ ] T031.1 [US3] Execute Bootstrap and Verify: Run the 1000 iterations (if N≥3) and log results to `data/results/bootstrap_summary.json` (including CI width) to verify SC-003.
- [ ] T032 [US3] Implement 95% Confidence Interval calculation for bias metrics in `code/analysis.py` (consumes T031.1 output)
- [ ] T033 [US3] Generate final summary tables and plots in `code/plot.py` (Exponents vs Resolution, Bias with CI)
- [ ] T034 [US3] Add "Deterministic Mode" flagging in `code/main.py` if N < 3 (consumes T031 output)
- [ ] T035 [US3] Implement runtime measurement and logging in `code/main.py` producing `data/results/runtime_summary.json` (verify ≤ 6h constraint, pass/fail status)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Cleanup (Polish)

**Purpose**: Ensure reproducibility, pass constitution gates, and finalize documentation.

- [ ] T036 [P] Run full pipeline stress test on the defined load profile (Multiple cases of 1024³ grids, 4 resolution levels each) and log results to `data/results/stress_test_results.json` (verify memory < 7GB and time < 6h)
- [ ] T036.1 [P] Verify Runtime Threshold: Read `data/results/runtime_summary.json` and `data/results/stress_test_results.json`, assert total time ≤ 6h, and write `data/results/runtime_verification.json` (pass/fail). Fail build if false.
- [ ] T036.2 [P] Verify Memory Threshold: Read `data/results/stress_test_results.json`, assert peak RSS ≤ 7GB, and write `data/results/memory_verification.json` (pass/fail). Fail build if false.
- [ ] T037 [P] Verify all artifacts are checksummed and hashes recorded in `state/` files
- [ ] T038 [P] Update `quickstart.md` with execution instructions and environment setup
- [ ] T039 [P] Run `pytest` suite and ensure [deferred] pass rate
- [ ] T040 [P] Update `research.md` with final data availability findings (N count, Reynolds numbers)
- [ ] T041 [P] Final Constitution Gate check (Reproducibility, Data Hygiene, Versioning)

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 statistics output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
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
Task: "Unit test for Fourier truncation logic in tests/unit/test_downsample.py"
Task: "Unit test for memory profiling in tests/unit/test_memory_monitor.py"

# Launch all models for User Story 1 together:
Task: "Implement JHTDB fetcher in code/download.py"
Task: "Implement Fourier-mode truncation in code/downsample.py"
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
- **CRITICAL**: All data downloads MUST use real JHTDB URLs or verified HuggingFace mirrors; no synthetic/fake data generation allowed for input.
- **CRITICAL**: All statistical results must be derived from real computed metrics; no hardcoded values or simulated results.
- **Verification**: Tasks T036.1 and T036.2 explicitly enforce the 6-hour runtime and 7GB memory limits defined in FR-007 and SC-004/005.
- **Bootstrap**: Task T031.1 ensures the 1000-iteration requirement is executed and logged; T031 handles the N<3 exception by generating a deterministic report.