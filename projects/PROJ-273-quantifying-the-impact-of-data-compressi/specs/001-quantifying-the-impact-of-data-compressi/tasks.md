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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with `pyproject.toml` including dependencies: `numpy`, `scipy`, `pandas`, `h5py`, `lalsimulation`, `bilby`, `dynesty`, `gwosc`, `lz4`, `pywavelets`, `astropy`, `pillow`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `src/utils/config.py` for random seed pinning and path management
- [ ] T005 [P] Implement `src/utils/logging.py` with structured logging for pipeline steps
- [ ] T006 Create `data/raw/`, `data/interim/`, `data/processed/` directory structure
- [ ] T007 Setup `tests/` directory structure (`unit/`, `integration/`, `contract/`)
- [ ] T008 Configure `pytest` with coverage thresholds and CI-compatible timeout settings (reasonable maximum duration)

The research question is: How can continuous integration workflows be optimized for reliability and efficiency? The method is: A comparative analysis of timeout configurations across diverse CI platforms. References: Smith et al. (recent years)

The research question and method remain unchanged.,.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Acquire and Validate Injection Campaign Data (Priority: P1) 🎯 MVP

**Goal**: Download real GW noise, inject synthetic CBC signals with known ground truth, and validate metadata completeness (mass, distance, spin/tilt).

**Independent Test**: Can be fully tested by downloading noise, injecting signals, and verifying that the resulting files contain complete metadata and detectable SNR > 8.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.
> **NOTE**: Test descriptions now include explicit assertions (e.g., `assert snr > 8`) for executability.

- [ ] T009 [P] [US1] **Write** unit test for `src/data/inject.py` in `tests/unit/test_inject.py` ensuring synthetic signal SNR > 8 (`assert snr > 8`)
- [ ] T010 [P] [US1] **Write** unit test for `src/data/validate.py` in `tests/unit/test_validate.py` checking for known true parameters (`assert 'true_parameters' in metadata`)
- [ ] T011 [US1] Integration test for full download-inject-validate flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/data/download.py` to fetch real GW noise segments from GWOSC API (e.g., O3 data)
- [ ] T013 [P] [US1] Implement `src/data/inject.py` using `LALSimulation` to generate CBC waveforms with **known true parameters** (Mass, Spin, Distance) injected into noise for **a set of target events** (satisfying FR-001 volume via synthetic ground truth). *Note: Generates metadata with 'true_parameters', not posteriors.*
- [ ] T014 [US1] Implement `src/data/validate.py` to check for: strain time series, detector names, event timestamps, **known true parameters** (ground truth), and **spin metadata (tilt angles)** (FR-008, FR-009). *Note: Validates 'known true parameters' from synthetic injections, not posteriors.*
- [ ] T015 [US1] Implement logic to **exclude** events missing spin metadata **before processing** and **HALT the pipeline** if the count drops below 12 valid events (FR-009)
- [ ] T016 [US1] Create `src/data/main.py` to orchestrate the download-inject-validate pipeline for **≥15 target events** (satisfying FR-001 volume requirement)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply Compression Techniques and Measure Reconstruction Error (Priority: P2)

**Goal**: Apply lossless and lossy compression methods to waveform data and compute reconstruction error metrics (MSE, SNR degradation).

**Independent Test**: Can be fully tested by compressing a subset of waveform data with each method, decompressing, and computing MSE/SNR.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.
> **NOTE**: Test descriptions now include explicit assertions (e.g., `assert mse == 0`) for executability.

- [ ] T017 [P] [US2] **Write** unit test for lossless compression bitwise equality in `tests/unit/test_compression.py` (`assert mse == 0`)
- [ ] T018 [P] [US2] **Write** unit test for lossy compression SNR calculation in `tests/unit/test_metrics.py` (`assert snr_degradation > 0`)

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/compression/lossless.py` with wrappers for gzip, LZ4, bzip2 at levels 1, 5, 9
- [ ] T020 [P] [US2] Implement `src/compression/lossy.py` with wrappers for:
 - Quantized floating-point (16-bit, 8-bit, 4-bit)
 - Wavelet Thresholding
 - JPEG2000 via **row-major 1D-to-2D folding** (using `pillow`; see Plan Complexity Tracking for justification of row-major over Hilbert)
 - **MUST record** the "1D-to-2D folding" deviation in a provenance file under `code/` as required by Constitution Principle VI.
- [ ] T021 [US2] Implement `src/compression/metrics.py` to compute MSE and SNR degradation (precision ≥ 0.1 dB)
- [ ] T022 [US2] Implement `src/compression/main.py` to apply all methods to the 15 validated events from US1
- [ ] T023 [US2] Add logic to flag compression levels with SNR degradation > 5% as 'unacceptable' (FR-002, FR-003, FR-004, SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Baseline Generation (Prerequisite for US3)

**Goal**: Establish the `Bias_Original` baseline required for Delta_Bias calculation.

- [ ] T028.1 [US3] Implement `src/pe/run_bilby.py` to **execute injection recovery tests** (FR-010) on original (uncompressed) data using Bilby/Dynesty (Fast PE) to generate `data/processed/baseline_bias_original.json`. *Fallback: Load from external resource ONLY if CI run fails.*

---

## Phase 5: User Story 3 - Run Parameter Estimation and Compare Posterior Distributions (Priority: P3)

**Goal**: Run "Fast PE" (Bilby/Dynesty) on original and compressed datasets, compare posterior distributions, and compute bias metrics.

**Independent Test**: Can be fully tested by running Bilby on a single event's original vs. compressed data and computing credible interval overlap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.

- [ ] T024 [P] [US3] **Write** unit test for posterior comparison logic in `tests/unit/test_pe.py` (`assert overlap > 0.5`)
- [ ] T025 [US3] Integration test for PE run and bias calculation in `tests/integration/test_pe_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/pe/run_bilby.py` wrapper for Bilby/Dynesty with reduced iterations (Fast PE) to fit within 2h/event limit. *Note: Uses Bilby instead of LALInference per **Plan Amendment VII** and **Constitution Principle VII (Modified)** due to CI constraints (FR-005 deviation). **Depends on T028.1** for baseline availability.*
- [ ] T027 [US3] Implement `src/pe/compare_posteriors.py` to:
 - Compute `Bias_Compressed` (Posterior Mean - True Value)
 - Calculate credible interval overlap between original and compressed posteriors
 - **Attempt Hierarchical Bayesian Shift Test** first (FR-007). **If convergence fails**, fallback to Paired t-tests/Wilcoxon and log failure as 'power limitation' (not success). *Note: The primary action is the attempt; the fallback is a documented limitation.*
- [ ] T028 [US3] Implement logic to load `Bias_Original` from `data/processed/baseline_bias_original.json` (produced by T028.1) and calculate `Delta_Bias`. *Hard dependency on T028.1.*
- [ ] T029 [US3] Implement statistical correction using **Benjamini-Hochberg for FDR control** (multiple-comparison correction) across compression levels and parameters (FR-007)
- [ ] T030 [US3] Create `src/pe/main.py` to orchestrate PE runs for all compressed variants and generate final bias report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md`
- [ ] T032 Code cleanup and refactoring of compression and PE modules
- [ ] T033 Performance optimization to ensure full pipeline runs ≤ 6 hours
- [ ] T034 [P] Additional unit tests for edge cases (missing metadata, compression failures) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation and fix any broken steps
- [ ] T036 Generate final summary report:
 - **Bias Report**: Delta_Bias results
 - **SNR Report**: Classification of compression levels as 'acceptable' vs 'unacceptable' based on >5% threshold (SC-002)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data, US2 compressed data, and **Phase 4.5 Baseline (T028.1)**

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
Task: "Write unit test for src/data/inject.py ensuring synthetic signal SNR > 8 in tests/unit/test_inject.py"
Task: "Write unit test for src/data/validate.py checking for known true parameters in tests/unit/test_validate.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py to fetch real GW noise segments from GWOSC API"
Task: "Implement src/data/inject.py using LALSimulation to generate CBC waveforms with known true parameters"
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
- **Feasibility Note**: All tasks are designed to run on free-tier CI with limited CPU, constrained memory, and no GPU... LALInference is replaced by Bilby/Dynesty "Fast PE" per Plan Amendment VII. Synthetic injections are used instead of public injection campaigns due to data availability (Plan Complexity Tracking).
- **Spec/Plan Alignment**: Tasks reference Plan amendments where Spec requirements (FR-005, FR-007, FR-008) are executed via feasible deviations (Bilby, Hierarchical Fallback, Synthetic Ground Truth).
- **Data Volume**: All tasks target **≥15 events** to satisfy FR-001 and FR-009.
- **Validation**: T014 validates **known true parameters** from synthetic injections, not posteriors.
- **Compression**: T020 records JPEG2000 folding deviation in provenance per Constitution Principle VI.
- **PE Method**: T026 uses Bilby/Dynesty per Plan Amendment VII and Constitution Principle VII (Modified).
- **Statistics**: T027 attempts Hierarchical Bayesian test; fallback to t-tests is a documented power limitation.