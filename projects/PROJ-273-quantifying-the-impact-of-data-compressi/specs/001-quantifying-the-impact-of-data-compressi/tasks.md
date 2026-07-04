# Tasks: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

**Input**: Design documents from `/specs/001-compression-impact-gw-reconstruction/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (lalsuite, gwosc, numpy, scipy, scikit-learn, glymur, pandas, pyyaml, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`, `data/derived`) with initial directory creation scripts
- [ ] T004b [P] Create schema files: `contracts/gw-event.schema.yaml` and `contracts/compression-result.schema.yaml` with exact field definitions for strain, metadata, and compression metrics
- [ ] T004c [P] Implement `code/utils/checksum_utils.py` for generating and validating SHA-256 checksums for all derived files (Constitution Principle III)
- [ ] T005 Implement schema validation framework using `pyyaml` and `jsonschema` for `gw-event.schema.yaml` and `compression-result.schema.yaml` (Depends on T004b)
- [ ] T006 [P] Create base configuration manager for paths, seeds, and resource limits (CPU cores, RAM)
- [ ] T007 Implement `GWOSCEvent` entity class with validation for strain data and metadata completeness
- [ ] T008 Implement `CompressionArtifact` entity class for tracking method, level, and error metrics
- [ ] T009 Implement `ParameterPosterior` entity class for storing MCMC samples and KL divergence results
- [ ] T010 Implement `SimulatedInjection` entity class for ground-truth tracking

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Acquire and Validate GWOSC Data (Priority: P1) 🎯 MVP

**Goal**: Download and validate ≥15 GWOSC CBC events, retaining ≥12 with complete metadata.

**Independent Test**: Script downloads data, validates integrity, and outputs a `validated_events.json` with checksums and field completeness reports.

### Tests for User Story 1

- [ ] T011 [P] [US1] Contract test for GWOSC API response schema in `tests/contract/test_gwosc_schema.py`
- [ ] T012 [P] [US1] Integration test for data download and validation pipeline in `tests/integration/test_data_acquisition.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `01_data_acquisition.py` to fetch O3a/O3b events via `gwosc` API
- [ ] T014 [US1] Implement validation logic in `01_data_acquisition.py`: check for `strain_h_plus`, `strain_h_cross`, and metadata fields (mass, distance, spin)
- [ ] T015 [US1] Implement filtering logic to exclude events with <95% field completeness; log warnings for excluded events; **log metadata flag for systematic limitation of reduced spin parameters (chi_eff, chi_p) for ALL valid processed events** (FR-008)
- [ ] T016 [US1] Generate `data/raw/validated_events.json` with checksums (via T004c) and completeness report (FR-001)
- [ ] T017a [US1] Unit test: `tests/unit/test_data_acquisition.py::test_missing_spin`
- [ ] T017b [US1] Unit test: `tests/unit/test_data_acquisition.py::test_incomplete_timestamps`
- [ ] T017c [US1] Unit test: `tests/unit/test_data_acquisition.py::test_valid_event`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Validate Against Simulated Injections (Priority: P1)

**Goal**: Generate ≥10 simulated injections with known ground truth to measure bias (US-4).

**Independent Test**: Script generates synthetic signals, saves ground-truth parameters, and verifies they match the injected values within floating-point tolerance.

### Tests for User Story 4

- [ ] T018 [P] [US4] Contract test for injection schema in `tests/contract/test_injection_schema.py`
- [ ] T019 [P] [US4] Integration test for injection generation and ground-truth verification in `tests/integration/test_simulation.py`

### Implementation for User Story 4

- [ ] T020 [US4] Implement `03_simulation.py` using `lalsimulation` with O3b CBC population model
- [ ] T021 [US4] Generate **exactly 50 simulated injections** with known mass, distance, spin, and theoretical SNR using **random seed=42** and **O3b population model parameters** (FR-009, Plan Phase 1); **Output `data/raw/injections_ground_truth.csv`**
- [ ] T021b [US4] [CI Fallback] If T021 fails due to resource limits, generate a reduced set (≥10) and log a warning; **ensure T021 remains the primary target**
- [ ] T022 [US4] Save `data/raw/injections_ground_truth.csv` with all ground-truth parameters (FR-009)
- [ ] T023 [US4] Implement verification script to ensure injected signals match ground truth within tolerance
- [ ] T024 [US4] Add unit tests for injection parameter generation and SNR calculation

**Checkpoint**: At this point, User Stories 1 AND 4 should both work independently

---

## Phase 5: User Story 2 - Apply Compression and Measure Error (Priority: P2)

**Goal**: Apply lossless and lossy compression to waveforms and measure reconstruction error (SNR, MSE).

**Independent Test**: Compress a waveform, decompress, and verify bit-identical results for lossless; measure SNR degradation for lossy.

### Tests for User Story 2

- [ ] T025 [P] [US2] Contract test for compression result schema in `tests/contract/test_compression_schema.py`
- [ ] T026 [P] [US2] Integration test for compression pipeline on a single event in `tests/integration/test_compression_engine.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement `02_compression_engine.py` skeleton with lossless methods (gzip, LZ, bzip2) at levels 1-9
- [ ] T027b [US2] Implement execution logic in `02_compression_engine.py` to apply compression to validated events (Depends on T016, T022)
- [ ] T028 [P] [US2] Implement lossy quantization (16-bit, 8-bit, 4-bit) using `numpy` casting (FR-003)
- [ ] T029 [US2] Implement JPEG2000 compression: convert strain to spectrogram, compress with `glymur`, reconstruct, inverse transform; **explicitly record the 1D-to-2D domain deviation in `data/derived/compression_provenance.json`** (FR-003, Constitution Principle VI)
- [ ] T030 [US2] Implement bit-identical verification for lossless methods (MSE = 0) (FR-004, SC-001)
- [ ] T031 [US2] Implement SNR degradation calculation for lossy methods with precision ≥0.1 dB (FR-004, SC-002)
- [ ] T031b [US2] **Implement parameter bias calculation for real events**: Compare PE results of compressed vs. original data to compute MAE for mass, distance, spin (FR-004); **Save to `data/derived/real_event_bias.json`**
- [ ] T032 [US2] Save results to `data/processed/compressed_events/` with metadata, checksums (via T004c), and compression artifacts
- [ ] T033b [US2] **Implement SNR classification logic**: Read **theoretical SNR** from `data/raw/injections_ground_truth.csv` (Depends on T022) and compare against measured SNR of compressed injections; flag as "Acceptable" if ≤ 5% degradation, else "Unacceptable" (SC-002, SC-006); **Write to `data/derived/compression_flags.json`**
- [ ] T033 [US2] Add unit tests for quantization logic and JPEG2000 round-trip accuracy
- [ ] T034b [US2] Generate `data/derived/compression_provenance.json` recording exact algorithms, levels, and deviations (Constitution Principle VI)

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should all work independently

---

## Phase 6: User Story 3 - Run Parameter Estimation and Compare Posteriors (Priority: P3)

**Goal**: Run LALInference CPU-mode on original and compressed data, compute KL divergence and ANOVA.

**Independent Test**: Run PE on one event, compare posteriors, and compute KL divergence.

### Tests for User Story 3

- [ ] T034 [P] [US3] Contract test for posterior schema in `tests/contract/test_posterior_schema.py`
- [ ] T035 [P] [US3] Integration test for LALInference CPU wrapper in `tests/integration/test_parameter_estimation.py`

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement `04_parameter_estimation.py` wrapper skeleton for LALInference CPU mode (`--cpu` flag)
- [ ] T036b [US3] Implement PE execution logic in `04_parameter_estimation.py` to run on original and compressed datasets (Depends on T027b, T032)
- [ ] T037 [US3] Configure MCMC with 50k iterations, Gelman-Rubin convergence check (R-hat < 1.1), **using `code/config/lalinference_cpu.ini`** and **defined priors for mass, distance, spin** (FR-005)
- [ ] T038 [US3] Execute PE for original and compressed datasets of ≥12 real events (FR-005)
- [ ] T039a [US3] Execute PE for simulated injections (FR-010)
- [ ] T039b [US3] **Compute SNR degradation for injections**: Compare measured SNR from T039a against **theoretical SNR** in `data/raw/injections_ground_truth.csv`; calculate bias and save to `data/derived/injection_snr_metrics.json` (FR-010, SC-002, SC-006)
- [ ] T040 [US3] Implement KL divergence calculation between original and compressed posteriors for mass, distance, spin (FR-006, SC-003)
- [ ] T041 [US3] Implement MAE calculation for injections against ground truth (FR-011, SC-005)
- [ ] T042 [US3] Implement statistical testing: **Test MAE/KL values for normality using Shapiro-Wilk; if p < 0.05, execute Friedman test; else execute Repeated-measures ANOVA**; **Use Bonferroni correction if comparisons ≤ 5, else use FDR (Benjamini-Hochberg)** (FR-007, SC-004); **Save results to `data/derived/stats.json`**
- [ ] T043 [US3] Generate `data/derived/stats.json` with all metrics and significance tests
- [ ] T044 [US3] Add unit tests for statistical calculations (KL, ANOVA/Friedman, MAE)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Visualization & Reporting

**Goal**: Generate plots and final reports for the analysis.

- [ ] T045 [P] Implement `06_visualization.py` script skeleton for plotting posterior distributions, SNR degradation, and bias metrics
- [ ] T045b [US3] Execute `06_visualization.py` to generate plots (Depends on T043)
- [ ] T046 [US3] Generate classification report using `data/derived/compression_flags.json` (input) and outputting `data/derived/classification_report.json` with "status" field (SC-002, SC-006)
- [ ] T047 [US3] Create final summary report in `data/derived/report.md` with all findings, limitations, and confidence intervals

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048a [P] Update `README.md` with usage examples for `02_compression_engine.py`
- [ ] T048b [P] Update `docs/` with API documentation for `04_parameter_estimation.py`
- [ ] T048c [P] Update `code/` docstrings and inline comments
- [ ] T049 Code cleanup and refactoring for memory efficiency (ensure <6GB RAM usage)
- [ ] T050 Performance optimization for parallel compression application
- [ ] T051 [P] Additional unit tests in `tests/unit/` for edge cases (incomplete metadata, failed compression)
- [ ] T052 Run quickstart.md validation and end-to-end pipeline test on CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - T004b (Schema creation) must complete before T005 (Validation)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US1 (Phase 3) and US4 (Phase 4) can run in parallel** (logically), but in task list US4 follows US1 for sequential clarity.
  - **US2 (Phase 5) depends on US1 and US4 outputs** (validated events, injections)
  - **US3 (Phase 6) depends on US2 outputs** (compressed data)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (data) and US4 (injections) being complete to have data to compress
- **User Story 3 (P3)**: Depends on US2 (compressed data) and US1/US4 (original data) being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T005 which depends on T004b) can run in parallel
- Once Foundational phase completes, US1 and US4 can start in parallel
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

**Note on US2/US4 Dependency**: While US1 and US4 are logically parallel, specific US2 tasks that consume US4 artifacts (e.g., T033b which requires `injections_ground_truth.csv` from T022) must wait for US4 completion. The linear task list reflects this dependency to prevent "consumer-before-producer" errors.

---

## Parallel Example: User Story 1 & 4

```bash
# Launch US1 and US4 in parallel (both P1, independent):
Task: "Implement 01_data_acquisition.py to fetch O3a/O3b events via gwosc API"
Task: "Implement 03_simulation.py using lalsimulation with O3b CBC population model"

# Launch tests for both in parallel:
Task: "Contract test for GWOSC API response schema in tests/contract/test_gwosc_schema.py"
Task: "Contract test for injection schema in tests/contract/test_injection_schema.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Real Data)
4. Complete Phase 4: User Story 4 (Simulated Data) - **Generate exactly 50 injections**
5. **STOP and VALIDATE**: Ensure data acquisition and simulation are working with ground truth.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US4 → Test independently → Validate data integrity
3. Add US2 → Test compression pipeline → Validate error metrics
4. Add US3 → Test PE and analysis → Validate statistical results
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Real Data)
   - Developer B: User Story 4 (Simulated Data)
   - Developer C: User Story 2 (Compression) - *Can start once US1/US4 data is available*
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
- **Resource Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM. LALInference must be run with `--cpu` and sampled data if necessary to fit memory. **US4 is capped at 50 injections (primary) with fallback to 10 for CI.**
- **Data Integrity**: Never fabricate data. Use real GWOSC data and real simulated injections only.
- **Provenance**: All compression operations must record exact algorithms and levels in `compression_provenance.json`.