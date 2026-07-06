# Tasks: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

**Input**: Design documents from `/specs/001-quantization-impact-gw/`
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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory structure: `projects/PROJ-329-quantifying-the-impact-of-data-quantizat/code/` with `src/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/` and verify tree via `tree` command, saving output to `logs/setup_tree.txt` <!-- FAILED: unspecified -->
- [X] T001b [P] Create empty placeholder files: `src/__init__.py`, `tests/__init__.py`, `requirements.txt`
- [X] T001c [P] Verify directory tree matches plan.md 'Project Structure' section exactly

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pycbc, bilby, numpy, scipy, matplotlib, pandas, h5py, astropy)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/state_manager.py` to record artifact hashes (Constitution V) after each phase
- [ ] T005 [P] Implement data hygiene utilities: checksumming for `data/raw/` and `data/processed/`
- [ ] T006 [P] Setup `src/utils.py` with quantization logic (Fixed FSR) and SNR calculation helpers
- [ ] T007 Create base data schemas in `contracts/` (`waveform.schema.yaml`, `result.schema.yaml`)
- [ ] T008 Configure error handling for missing/corrupted noise files (fail gracefully)
- [ ] T009 [P] Setup environment configuration for random seeds and CI limits (2 CPU, 7 GB RAM) and calculate batch size constraints for N=1200 pilot
- [ ] T010 [P] Calculate and document batch sizes: Verify N=1200 (6 depths × 4 bins × 50) fits within 6-hour CI limit and 7 GB RAM (based on T009)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Quantize Simulated Gravitational Waveforms (Priority: P1) 🎯 MVP

**Goal**: Generate binary black hole merger waveforms, inject into LIGO O3 noise, and apply controlled quantization (including low bit-widths and standard precisions up to 16 bits) to create the dataset.

**Independent Test**: Generate a small batch (), apply 8-bit quantization, verify discrete levels match $2^8$ bins and SNR is within [8, 50].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test for quantization logic: verify 1-bit and 16-bit edge cases in `tests/unit/test_quantization.py`
- [~] T012 [P] [US1] Integration test for noise injection: verify SNR range [8, 50] in `tests/integration/test_injection.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `src/data_generation.py`: Generate BBH waveforms (IMRPhenomPv) with masses [10, 50] $M_\odot$ and distances [100, 1000] Mpc.
- [~] T013a [US1] Verify that the stratified bins (8-14, 14-20, 20-30, 30-50) collectively cover the full [8, 50] range, and that individual injected signals meet the ±0.5 SNR tolerance (US-1 Acceptance Scenario 1)
- [~] T014 [US1] Implement `src/data_generation.py`: Apply Fixed Full-Scale Range (FSR) quantization for all required bit depths:, 8, 10, 12, 14, and 16 bits (FR-002)
- [~] T015 [US1] [after T014] Implement `src/data_generation.py`: Generate parallel float64 baseline waveforms for every quantized signal (FR-007)
- [~] T016 [US1] [after T015] Save output dataset to `data/processed/waveforms_pilot_{seed}.h5` in HDF5 format, ensuring batch size fits 7 GB RAM limit; verify file size < 4GB and checksum recorded in `state.yaml`
- [~] T017 [US1] Add validation: verify quantized signals contain **no more than** $2^N$ unique levels (accounting for signal amplitude clipping) and SNR tolerance ±0.5

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Parameter Estimation on Quantized Signals (Priority: P2)

**Goal**: Run Bayesian parameter estimation (Uniform MCMC) on quantized waveforms to recover chirp mass, spin, and distance, and compute MSE against ground truth.

**Independent Test**: Run inference on a single low-SNR 8-bit signal.; verify convergence and physically plausible parameters.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for MSE calculation: verify bias < 10% for known injected values in `tests/unit/test_metrics.py`
- [~] T019 [P] [US2] Integration test for inference pipeline: verify convergence on SNR > 10 signal in `tests/integration/test_inference.py`

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement `src/inference_engine.py`: CPU-optimized Bilby/PyCBC-Inference wrapper with Uniform MCMC (fixed steps)
- [~] T021 [US2] Implement `src/inference_engine.py`: Stratified batch processing loop for bit depths (1, 8, 10, 12, 14, 16) × SNR bins (8-14, 14-20, 20-30, 30-50) × 50 signals = 1200 signals/run (full FR-002 set)
- [~] T022 [US2] Implement `src/inference_engine.py`: Parallel execution strategy to fit within 6-hour CI limit (2 cores)
- [~] T023 [US2] Compute MSE between injected ground-truth and recovered posterior means for chirp mass, spin, and distance
- [~] T024 [US2] Save inference results to `data/results/inference_pilot_{seed}.json` as JSON/CSV, including 90% credible intervals
- [~] T025 [US2] Handle edge cases: record "non-detections" for SNR < 8 or failed convergence instead of crashing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Identify Quantization-Dominance Thresholds (Priority: P3)

**Goal**: Analyze error vs. SNR curves to identify the SNR threshold where quantization noise adds >10% to instrumental error.

**Independent Test**: Plot error curves for a subset; verify divergence of 8-bit vs 16-bit at a specific SNR.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T026 [P] [US3] Unit test for threshold fitting: verify crossover detection logic in `tests/unit/test_analysis.py`
- [~] T027 [P] [US3] Integration test for reproducibility: verify std dev of crossover SNR < 0.5 across 10 runs in `tests/integration/test_reproducibility.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `src/analysis.py`: Calculate Instrumental Error (float64 baseline) and Quantization Error (quantized)
- [ ] T029 [US3] Implement `src/analysis.py`: Fit error-vs-SNR curves and identify crossover point where $\Delta > 0.1 \times E_{inst}$
- [ ] T030 [US3] Implement `src/analysis.py`: Generate diagnostic plots showing slope change >20% at the threshold
- [ ] T031 [US3] Execute **10 independent runs** (different seeds) of the **N=1200 pilot batch** (6 depths × 4 bins × 50 signals) to calculate standard deviation of identified crossover SNR; save results to `data/results/crossover_stats.csv` (SC-005)
- [ ] T032 [US3] Generate final report at `docs/report.md` stating a concrete **crossover point (threshold)** where 8-bit quantization is deemed insufficient (format: "SNR threshold = X ± Y")
- [ ] T033 [US3] Run `src/state_manager.py` to record final artifact hashes and update `research.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `quickstart.md` and `docs/`
- [ ] T035 Code cleanup and refactoring for CPU efficiency
- [ ] T036 Performance optimization: ensure memory usage < 4 GB during inference batches
- [ ] T037 [P] Additional unit tests for edge cases (1-bit quantization, missing noise file)
- [ ] T038 Security hardening: verify no external data sources other than verified GWOSC
- [ ] T039 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for quantization logic: verify 1-bit and 16-bit edge cases in tests/unit/test_quantization.py"
Task: "Integration test for noise injection: verify SNR range [8, 50] in tests/integration/test_injection.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data_generation.py: Generate BBH waveforms..."
Task: "Implement src/data_generation.py: Fetch LIGO O3 noise PSD..."
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
- **Pilot Scope**: This implementation uses a pilot of N=1200 signals (6 depths × 4 bins × 50) per run to fit within 6-hour CI limits. Full signal set and 6 bit depths are deferred to post-CI validation.