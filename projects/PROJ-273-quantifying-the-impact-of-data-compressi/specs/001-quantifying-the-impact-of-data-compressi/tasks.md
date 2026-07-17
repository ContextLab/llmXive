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

## Phase 0.1: Spec Amendments (Blocking Prerequisites)

**Purpose**: Formalize all necessary deviations from the original spec before implementation begins.
**⚠️ CRITICAL**: No implementation tasks (Phase 2+) can begin until this phase is complete. All Txx.0 tasks MUST update `spec.md` with the exact amended text.

- [ ] T004.0 [P] [Spec] **Formal Amendment Task**: Update `spec.md` to formally amend FR-005 and Constitution Principle VII to authorize `Bilby/Dynesty` as the Parameter Estimation engine for this project. *Exact Text to Insert:* "FR-005: System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints. Constitution Principle VII is amended to allow this deviation for the pilot phase." *Note: Must write the exact amended text into spec.md.*
- [ ] T012.0 [P] [Spec] **Formal Amendment Task**: Update `spec.md` to formally amend FR-001 to replace "download ≥15 injection campaigns" with "generate ≥15 synthetic injections into real GW noise" due to lack of public injection campaigns. *Exact Text to Insert:* "FR-001: System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns." *Note: Must write the exact amended text into spec.md.*
- [ ] T020.0 [P] [Spec] **Formal Amendment Task**: Create `code/provenance/deviation_JPEG2000_folding.md` and update `spec.md` to formally record the "1D-to-2D folding" deviation required for JPEG2000 implementation. *Exact Text to Insert:* "FR-003: JPEG2000 compression MUST be implemented via 1D-to-2D folding (Hilbert curve algorithm) to adapt 2D codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression'." *Note: Must write the exact amended text into spec.md.*
- [ ] T027.0 [P] [Spec] **Formal Amendment Task**: Update `spec.md` to formally amend FR-007 to authorize "Paired t-tests/Wilcoxon" as a valid fallback if Hierarchical Bayesian Shift Test convergence fails. *Exact Text to Insert:* "FR-007: System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100), the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. This deviation is authorized by Plan Complexity Tracking." *Note: Must write the exact amended text into spec.md.*
- [ ] T028.0 [P] [Spec] **Formal Amendment Task**: Update `spec.md` to formally amend SC-003 and FR-010 to measure `Delta_Bias` against an external baseline rather than absolute bias. *Exact Text to Insert:* "FR-010: System MUST execute injection recovery tests with known true parameters to establish an independent baseline for bias detection. SC-003: Parameter estimation bias is measured against this external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value)." *Note: Must write the exact amended text into spec.md.*

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p src/data src/compression src/pe src/utils tests/unit tests/integration tests/contract data/raw data/interim data/processed reports code/provenance data/external`
- [X] T002 Initialize a Python project with `pyproject.toml` including dependencies: `numpy`, `scipy`, `pandas`, `h5py`, `lalsimulation`, `bilby`, `dynesty`, `gwosc`, `lz4`, `pywavelets`, `astropy`, `pillow`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/config.py` for random seed pinning and path management
- [X] T005 [P] Implement `src/utils/logging.py` with structured logging for pipeline steps
- [ ] T006 Create `data/raw/`, `data/interim/`, `data/processed/`, `data/external/` directory structure
- [ ] T007 Setup `tests/` directory structure (`unit/`, `integration/`, `contract/`)
- [ ] T008 Configure `pytest` with coverage thresholds and CI-compatible timeout settings (timeout=300s)
- [ ] T028.1 [US3] **Load/Verify** external baseline `Bias_Original` from `data/external/baseline_bias_original.json` (produced by T040.3). *Note: Dependent on T040.3 completion.*
- [ ] T028.2 [US3] Create `code/provenance/deviation_PE_method.md` to **record the deviation** from Spec FR-005 (LALInference) to Bilby/Dynesty (Fast PE) as required by Constitution Principle VII and Plan Complexity Tracking.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Acquire and Validate Injection Campaign Data (Priority: P1) 🎯 MVP

**Goal**: Download real GW noise, inject synthetic CBC signals with known ground truth, and validate metadata completeness (mass, distance, spin/tilt).

**Independent Test**: Can be fully tested by downloading real GW noise from GWOSC, injecting synthetic CBC signals using `LALSimulation` with known ground truth parameters, and verifying that the resulting files contain complete metadata and detectable SNR > 8.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.
> **NOTE**: Test descriptions now include explicit assertions (e.g., `assert snr > 8`) for executability.

- [X] T009 [P] [US1] **Write** unit test for `src/data/inject.py` in `tests/unit/test_inject.py` ensuring synthetic signal SNR > 8 (`assert snr > 8`)
- [X] T010 [P] [US1] **Write** unit test for `src/data/validate.py` in `tests/unit/test_validate.py` checking for known true parameters (`assert 'true_parameters' in metadata`)
- [X] T011 [US1] Integration test for full download-inject-validate flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/data/download.py` to fetch real GW noise segments from GWOSC API (e.g., O data) **only**. *Note: Operates under **Amended FR-001**. Fetches noise only; injection is handled in T013. **Depends on T012.0**.*
- [ ] T013 [P] [US1] Implement `src/data/inject.py` using `LALSimulation` to generate CBC waveforms with **known true parameters** (Mass, Spin, Distance) injected into the fetched noise for **a set of target events**. *Note: Operates under **Amended FR-001**. Generates metadata with 'true_parameters', not posteriors.*
- [X] T014 [US1] Implement `src/data/validate.py` to check for: strain time series, detector names, event timestamps, **known true parameters** (ground truth), and **spin metadata (tilt angles)** (FR-008, FR-009). *Note: Validates 'known true parameters' from synthetic injections, not posteriors.*
- [ ] T015 [US1] Implement logic to **fetch additional noise segments in batches** and inject/validate until **≥15 valid events** with complete spin metadata are found. *Note: Implements a loop to ensure the final analysis set meets FR-009. **MUST include max_attempts=20 and timeout=300s**. **Loop Condition:** `while valid_count < 15 and attempts < 20`. **Depends on T012.0**.*
- [ ] T015.1 [US1] **Handle Failure Mode**: Implement logic to **halt the pipeline and log a critical error** if `max_attempts` is reached and <15 valid events are found. *Note: Ensures deterministic failure behavior and prevents silent violation of FR-009.*
- [ ] T016 [US1] Create `src/data/main.py` to orchestrate the **download-inject-validate** pipeline for **≥15 target events** (per **Amended FR-001**) and produce the validated dataset. *Note: Calls T015 logic. **Depends on T012.0**.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4.5: Baseline Generation (Prerequisite for US3)

**Purpose**: Generate the `Bias_Original` baseline required for Delta_Bias calculation.
**⚠️ CRITICAL**: This phase is the bridge between US1 (Data) and US3 (PE). It cannot run until T016 completes.

- [ ] T040.1 [US3] **Select Representative Event**: Load the validated dataset from T016 and select the first event with complete spin metadata as the representative event for baseline generation. *Note: Output is the event ID.*
- [ ] T040.2 [US3] **Execute Baseline Run**: Run `Bilby` with `Dynesty` on the representative event (selected in T040.1) using **exact configuration**: `max_iter=50000`, `nlive=200`, `seed=42`. *Note: Operates under **Amended FR-005** and **Plan Complexity Tracking: External Baseline**. This run establishes the converged baseline.*
- [ ] T040.3 [US3] **Save Baseline Artifact**: Save the posterior samples and calculated `Bias_Original` (Posterior Mean - True Value) to `data/external/baseline_bias_original.json`. *Note: Output schema must include keys: `event_id`, `true_parameters`, `posterior_mean`, `bias`, `covariance`.*

---

## Phase 4: User Story 2 - Apply Compression Techniques and Measure Reconstruction Error (Priority: P2)

**Goal**: Apply lossless and lossy compression methods to waveform data and compute reconstruction error metrics (MSE, SNR degradation).

**Independent Test**: Can be fully tested by compressing a subset of waveform data with each method, decompressing, and computing MSE/SNR.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.
> **NOTE**: Test descriptions now include explicit assertions (e.g., `assert mse == 0`) for executability.

- [X] T017 [P] [US2] **Write** unit test for lossless compression bitwise equality in `tests/unit/test_compression.py` (`assert mse == 0`)
- [ ] T018 [P] [US2] **Write** unit test for lossy compression SNR calculation in `tests/unit/test_metrics.py` (`assert snr_degradation > 0`)

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/compression/lossless.py` with wrappers for gzip, LZ, bzip2 at levels 1, 5, 9
- [ ] T020 [P] [US2] Implement `src/compression/lossy.py` with wrappers for:
 - Quantized floating-point (16-bit, 8-bit, 4-bit)
 - Wavelet Thresholding
 - JPEG2000 via **Hilbert curve 1D-to-2D folding** (using `pillow`; target dimensions 2048x1024). **MUST use Hilbert curve algorithm exclusively as mandated by Amended FR-003 (T020.0)**. *Note: Hilbert was chosen over row-major for better space-filling properties in 1D-to-2D folding, as per Plan Complexity Tracking.*
 - **MUST implement** the corresponding **unfold** step to restore 1D data before computing reconstruction error (MSE/SNR).
 - **MUST include** a validation step to ensure the "transformation artifact" does not invalidate the MSE/SNR comparison (e.g., by comparing the unfolded original to the folded-unfolded original). *Note: Ensures SC-002 validity.*
 - **Output Paths**: Save compressed artifacts to `data/interim/compressed/{method}/{level}/`.
- [ ] T021 [US2] Implement `src/compression/metrics.py` to compute MSE and SNR degradation (precision ≥ 0.1 dB)
- [ ] T022 [US2] Implement `src/compression/main.py` to apply all methods to the validated events from US1. *Dependency: Must wait for T016 completion.*
- [ ] T023 [US2] Add logic to flag compression levels with SNR degradation > 5% as 'unacceptable' (FR-002, FR-003, FR-004, SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Run Parameter Estimation and Compare Posterior Distributions (Priority: P3)

**Goal**: Run "Fast PE" (Bilby/Dynesty) on original and compressed datasets, compare posterior distributions, and compute bias metrics.

**Independent Test**: Can be fully tested by running Bilby on a single event's original vs. compressed data and computing credible interval overlap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.

- [ ] T024 [P] [US3] **Write** unit test for posterior comparison logic in `tests/unit/test_pe.py` (`assert overlap > 0.5`)
- [ ] T025 [US3] Integration test for PE run and bias calculation in `tests/integration/test_pe_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/pe/run_bilby.py` wrapper for Bilby/Dynesty with **reduced iterations** (`max_iter=5000`, `stop when ESS > 200`) **specifically chosen to meet the h/event constraint**. *Note: Uses Bilby/Dynesty per **Amended FR-005** and **Constitution Principle VII (Modified)** due to CI constraints. **Depends on T004.0** (Amendment) and **T028.1** (Baseline).* **Fallback**: If runtime exceeds a predefined threshold, reduce `max_iter` by [deferred] and log a warning.
- [ ] T026.1 [US3] Update `code/provenance/deviation_PE_method.md` (created in T028.2) to include the specific Bilby/Dynesty configuration used, ensuring the deviation is fully documented per Constitution Principle VII.
- [ ] T027 [US3] Implement `src/pe/compare_posteriors.py` to:
 - Compute `Bias_Compressed` (Posterior Mean - True Value)
 - Calculate credible interval overlap between original and compressed posteriors
 - **Attempt Hierarchical Bayesian Shift Test** first (FR-007). **If convergence fails** (defined as ESS < 100), fallback to Paired t-tests (alpha=0.05) **APPLYING THE BENJAMINI-HOCHBERG CORRECTION**.
 - **Implementation Detail**: This task MUST include the **full inline implementation** of the Benjamini-Hochberg correction logic (calculating adjusted p-values for multiple comparisons across compression levels and parameters). Do not rely on a separate task or external library for the core logic; implement the sorting and thresholding steps directly to ensure self-containment.
 - **Dependency**: Depends on **T027.0** (Spec Amendment) for authorization of the fallback method, but implements the logic internally. *Note: Merged definition and application to prevent execution gaps. **Depends on T027.0** for authorization.*
- [ ] T028 [US3] Implement logic to load `Bias_Original` from `data/external/baseline_bias_original.json` (verified by T028.1) and calculate `Delta_Bias`. *Note: Operates under **Amended SC-003**. Hard dependency on T040.3.*
- [ ] T030 [US3] Create `src/pe/main.py` to orchestrate PE runs for all compressed variants and generate final bias report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates:
 - Update `README.md` with installation, usage, and data schema.
 - Update `docs/quickstart.md` with step-by-step pipeline execution.
 - Update `docs/api.md` with function signatures for `src/data`, `src/compression`, and `src/pe` modules.
- [ ] T032 Code cleanup and refactoring of compression and PE modules
- [ ] T033 Performance optimization to ensure full pipeline execution ≤ 6 hours (CI constraint)
- [ ] T034 [P] Additional unit tests for edge cases (missing metadata, compression failures) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation and fix any broken steps
- [ ] T036 Generate final summary report:
 - **Bias Report**: Delta_Bias results
 - **SNR Report**: Classification of compression levels as 'acceptable' vs 'unacceptable' based on >5% threshold (SC-002)
 - **Output file**: `reports/final_summary.md` (Markdown format) containing the above sections.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Spec Amendments (Phase 0.1)**: No dependencies - MUST complete before Phase 2
- **Foundational (Phase 2)**: Depends on Phase 0.1 and Setup - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data, US2 compressed data, and **Phase 4.5 Baseline (T040.3)**

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

1. Complete Phase 0.1: Spec Amendments
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0.1 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0.1 + Setup + Foundational together
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
- **Data Volume**: All tasks target **≥15 events** to satisfy **Amended FR-001** and FR-009.
- **Validation**: T014 validates **known true parameters** from synthetic injections, not posteriors.
- **Compression**: T020 records JPEG2000 folding deviation in provenance per Constitution Principle VII (Modified) and includes artifact validation.
- **PE Method**: T026 uses Bilby/Dynesty per **Amended FR-005** and Constitution Principle VII (Modified).
- **Statistics**: T027 attempts Hierarchical Bayesian test; fallback to t-tests is authorized by **Amended FR-007** and MUST apply Benjamini-Hochberg correction **inline** (merged definition and application).
- **Amendments**: T004.0, T012.0, T020.0, T027.0, T028.0 are mandatory formal amendment tasks to update spec artifacts in Phase 0.1 before implementation.
- **Baseline**: T040.1/040.2/040.3 generates the external baseline artifact required by T028.1.
- **Failure Handling**: T015.1 ensures deterministic failure if <15 events are found.