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

## Phase 0: Documentation & Research (Prerequisites)

**Purpose**: Create required Phase 0/1 artifacts as mandated by the plan.

- [ ] T001.0 [P] [Docs] **Create research.md**: Create `research.md` in `specs/001-compression-impact-gw-reconstruction/` as required by the plan. *Content*: Summary of research approach, synthetic injection strategy, and feasibility constraints.

## Phase 0.1: Spec & Constitution Amendments (Blocking Prerequisites)

**Purpose**: Formalize all necessary deviations from the original spec and constitution before implementation begins.
**⚠️ CRITICAL**: No implementation tasks (Phase 2+) can begin until this phase is complete. All Txx.0 tasks MUST update `spec.md` and `plan.md` with the exact amended text.

### Step 1: Provenance Creation & Definition (T001.x)

- [ ] T001.1 [P] [Constitution] **Create Deviation Record (Principle II)**: Create `code/provenance/deviation_constitution_principle_ii.md` to formally record the deviation from Constitution Principle II (Verified Accuracy) regarding the lack of public injection campaigns. *Content Requirements*: Must include (1) The original principle text, (2) The specific deviation (use of synthetic injections), (3) Justification referencing Plan Complexity Tracking, (4) Mitigation strategy (LALSimulation + known ground truth). *Action*: Create file and update `state/projects/PROJ-273-quantifying-the-impact-of-data-compressi.yaml`.
- [ ] T001.2 [P] [Plan] **Update Constitution Check (Plan)**: Update the `Constitution Check` table in `plan.md` to reflect the status of Principle II and VII. *Edit Instruction*: Locate the `Constitution Check` table. Change Principle II status to "Pass (Modified)" and add a note: "Deviation recorded in code/provenance/deviation_constitution_principle_ii.md". Change Principle VII to "Pass (Modified)" with note: "Bilby/Dynesty authorized for pilot phase".
- [ ] T001.3 [P] [Spec] **Define Amendment Text (FR-001)**: Define the exact text for the FR-001 amendment in a temporary file or comment block. *Text*: "FR-001: System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns. The system MUST iterate fetching noise segments and generating injections until ≥12 valid events with complete spin metadata are found, or a maximum of 20 attempts is reached. [UNRESOLVED-CLAIM: c_95dda9e2 — status=not_enough_info] If a sufficient number of valid events are not found after a reasonable number of attempts, the system MUST raise a RuntimeError and halt. "
- [ ] T001.4 [P] [Spec] **Define Amendment Text (FR-005)**: Define the exact text for the FR-005 amendment. *Text*: "FR-005: System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints."
- [ ] T001.5 [P] [Spec] **Define Amendment Text (JPEG2000)**: Define the exact text for the JPEG2000 deviation. *Text*: "FR-003: Wavelet-based image compression MUST be implemented via 1D-to-2D folding (Hilbert curve algorithm) to adapt 2D codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression'."
- [ ] T001.6 [P] [Spec] **Define Amendment Text (FR-007)**: Define the exact text for the FR-007 fallback. *Text*: "FR-007: System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100), the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. [UNRESOLVED-CLAIM: c_1025897c — status=not_enough_info] This deviation is authorized by Plan Complexity Tracking."
- [ ] T001.7 [P] [Spec] **Define Amendment Text (SC-003)**: Define the exact text for the SC-003 amendment. *Text*: "SC-003: Parameter estimation bias is measured against an external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value)."

### Step 2: Spec Amendment Execution (T002.x)

- [ ] T002.0 [P] [Spec] **Update Spec (FR-001)**: Update `spec.md` to formally amend FR-001. *Edit Instruction*: Locate the `Functional Requirements` section. Replace the text for FR-001 with the text defined in T001.3.
- [ ] T002.1 [P] [Spec] **Update Spec (FR-005)**: Update `spec.md` to formally amend FR-005. *Edit Instruction*: Locate the `Functional Requirements` section. Replace the text for FR-005 with the text defined in T001.4.
- [ ] T002.2 [P] [Spec] **Update Spec (JPEG2000)**: Update `spec.md` to formally record the JPEG2000 folding deviation. *Edit Instruction*: Locate the `Functional Requirements` section. Update FR-003 to include the text defined in T001.5. Create `code/provenance/deviation_JPEG2000_folding.md` with the algorithm details (Hilbert curve).
- [ ] T002.3 [P] [Spec] **Update Spec (FR-007)**: Update `spec.md` to formally amend FR-007. *Edit Instruction*: Locate the `Functional Requirements` section. Replace the text for FR-007 with the text defined in T001.6.
- [ ] T002.4 [P] [Spec] **Update Spec (SC-003)**: Update `spec.md` to formally amend SC-003. *Edit Instruction*: Locate the `Success Criteria` section. Replace the text for SC-003 with the text defined in T001.7.

---

## Phase 1: Setup & Documentation (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and required documentation artifacts.

- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T006 [P] Create `data/raw/`, `data/interim/`, `data/processed/`, `data/external/` directory structure
- [ ] T007 [P] Create `tests/` directory structure (`unit/`, `integration/`, `contract/`)
- [ ] T008 [P] Configure `pytest` with coverage thresholds and CI-compatible timeout settings (timeout=300s)
- [ ] T017.1 [P] [Docs] **Create quickstart.md**: Create `quickstart.md` in `specs/001-compression-impact-gw-reconstruction/` as required by the plan. *Content*: Step-by-step pipeline execution guide.
- [ ] T017.2 [P] [Docs] **Create contracts directory**: Create `specs/contracts/` directory and initialize with a placeholder `README.md` describing the contract testing strategy.
- [ ] T017.3 [P] [Docs] **Create data-model.md**: Create `data-model.md` in `specs/001-compression-impact-gw-reconstruction/` as required by the plan. *Content*: Schema definitions for GWOSCEvent, CompressionArtifact, ParameterPosterior.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 [P] Setup `src/utils/config.py` for random seed pinning and path management
- [X] T005 [P] Implement `src/utils/logging.py` with structured logging for pipeline steps

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

- [X] T012 [P] [US1] Implement `src/data/download.py` to fetch real GW noise segments from GWOSC API (e.g., O data) **only**. *Note: Operates under **Amended FR-001**. Fetches noise only; injection is handled in T013.*
- [ ] T013 [P] [US1] Implement `src/data/inject.py` using `LALSimulation` to generate CBC waveforms with **known true parameters** (Mass, Spin, Distance) injected into the fetched noise for **a set of target events**. *Note: Operates under **Amended FR-001**. Generates metadata with 'true_parameters', not posteriors.*
- [X] T014 [US1] Implement `src/data/validate.py` to check for: strain time series, detector names, event timestamps, **known true parameters** (ground truth), and **spin metadata (tilt angles)** (FR-008, FR-009). *Note: Validates 'known true parameters' from synthetic injections, not posteriors.*
- [ ] T019.0 [US1] **Validate Input**: Check that `data/raw/` contains noise segments generated by T012 before proceeding. *Note: Pre-condition for T019.1.*
- [ ] T019.1 [US1] **Implement Fetch Loop**: Implement the logic in `src/data/fetch_loop.py` to fetch additional noise segments in batches and inject/validate until **≥12 valid events** with complete spin metadata are found. *Note: Implements a loop to ensure the final analysis set meets FR-009. **MUST include max_attempts=20 and timeout=300s**. **Loop Condition:** `while valid_count < 12 and attempts < 20`. If max attempts reached and valid_count < 12, **raise RuntimeError('Failed to find 12 valid events after 20 attempts')**.*
- [ ] T020 [US1] Create `src/data/main.py` to orchestrate the **download-inject-validate** pipeline for **≥15 target events** (per **Amended FR-001**) and produce the validated dataset. *Note: Calls T019.1 logic.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4.5: Baseline Generation (Prerequisite for US3)

**Purpose**: Generate the `Bias_Original` baseline required for Delta_Bias calculation.
**⚠️ CRITICAL**: This phase is the bridge between US1 (Data) and US3 (PE). It cannot run until T020 completes.

- [ ] T040.1 [US3] **Select Representative Event**: Load the validated dataset from T020 and select the first event with complete spin metadata as the representative event for baseline generation. *Note: Output is the event ID.*
- [ ] T040.2a [US3] **Check Baseline Availability**: Check if `data/external/baseline_bias_original.json` exists and is valid. *Note: If valid, skip to T040.3. If not, proceed to T040.2b.*
- [ ] T040.2b [US3] **Fetch Versioned Baseline**: Attempt to fetch `Bias_Original` from a canonical, versioned source (e.g., Zenodo, GitHub Release) as defined in `code/config.py`. *Note: If fetch fails, proceed to T040.2c.*
- [ ] T040.2c [US3] **Generate Baseline via CI Script**: Run a high-iteration `Bilby`/`Dynesty` run on the selected event (T040.1) using the script `code/scripts/generate_baseline.py`. *Note: Operates under **Amended FR-005** and **Plan Complexity Tracking: External Baseline**. **MUST use a CI-run with a timeout (e.g., 4 hours)**. If the run fails to converge or times out, generate a 'seed' baseline using a pre-computed set of samples and log a warning about the limitation. **Output**: `data/external/baseline_bias_original.json`.*
- [ ] T040.3 [US3] **Save/Verify Baseline Artifact**: Save the posterior samples and calculated `Bias_Original` (Posterior Mean - True Value) to `data/external/baseline_bias_original.json`. *Note: Output schema must include keys: `event_id`, `true_parameters`, `posterior_mean`, `bias`, `covariance`. Verify checksum.*
- [ ] T028.1 [US3] **Load/Verify** external baseline `Bias_Original` from `data/external/baseline_bias_original.json`. *Note: Dependent on T040.3 completion. Validates schema and checksum.*

**Checkpoint**: Baseline ready - US3 can now proceed

---

## Phase 5: User Story 2 - Apply Compression Techniques and Measure Reconstruction Error (Priority: P2)

**Goal**: Apply lossless and lossy compression methods to waveform data and compute reconstruction error metrics (MSE, SNR degradation).

**Independent Test**: Can be fully tested by compressing a subset of waveform data with each method, decompressing, and computing MSE/SNR.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.
> **NOTE**: Test descriptions now include explicit assertions (e.g., `assert mse == 0`) for executability.

- [ ] T017 [P] [US2] **Write** unit test for lossless compression bitwise equality in `tests/unit/test_compression.py` (`assert mse == 0`)
- [ ] T018 [P] [US2] **Write** unit test for lossy compression SNR calculation in `tests/unit/test_metrics.py` (`assert snr_degradation > 0`)

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/compression/lossless.py` with wrappers for gzip, LZ4, bzip2 at levels 1, 5, 9
- [ ] T020.1 [P] [US2] Implement `src/compression/lossy.py` - **Quantization**: Implement quantized floating-point (variable bit-widths, e.g., 8-bit, 4-bit) and corresponding unfold step. *Note: Output paths: `data/interim/compressed/quantization/{level}/`.*
- [ ] T020.2 [P] [US2] Implement `src/compression/lossy.py` - **Wavelet**: Implement Wavelet Thresholding and corresponding unfold step. *Note: Output paths: `data/interim/compressed/wavelet/{level}/`.*
- [ ] T020.3 [P] [US2] Implement `src/compression/lossy.py` - **JPEG2000**: Implement JPEG2000 via **Hilbert curve 1D-to-2D folding** (using `pillow`; target dimensions **2048x1024**). **MUST use Hilbert curve algorithm exclusively as mandated by Amended FR-003**. *Note: Hilbert was chosen over row-major for better space-filling properties in 1D-to-2D folding, as per Plan Complexity Tracking.* **MUST implement** the corresponding **unfold** step to restore 1D data before computing reconstruction error (MSE/SNR). **MUST include** a validation step to ensure the "transformation artifact" does not invalidate the MSE/SNR comparison. *Note: Ensures SC-002 validity. Output paths: `data/interim/compressed/jpeg2000/{level}/`.*
- [ ] T021 [US2] Implement `src/compression/metrics.py` to compute MSE and SNR degradation (precision ≥ 0.1 dB)
- [ ] T022 [US2] Implement `src/compression/main.py` to apply all methods to the validated events from US1. *Dependency: Must wait for T020.1, T020.2, T020.3 completion.*
- [ ] T023 [US2] Add logic to flag compression levels with SNR degradation > 5% as 'unacceptable' (FR-002, FR-003, FR-004, SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Run Parameter Estimation and Compare Posterior Distributions (Priority: P3)

**Goal**: Run "Fast PE" (Bilby/Dynesty) on original and compressed datasets, compare posterior distributions, and compute bias metrics.

**Independent Test**: Can be fully tested by running Bilby on a single event's original vs. compressed data and computing credible interval overlap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **writing** the test code. Execution occurs after implementation.

- [ ] T024 [P] [US3] **Write** unit test for posterior comparison logic in `tests/unit/test_pe.py` (`assert overlap > 0.5`)
- [ ] T025 [US3] Integration test for PE run and bias calculation in `tests/integration/test_pe_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/pe/run_bilby.py` wrapper for Bilby/Dynesty with **reduced iterations** (`maxiter=5000`, `nlive=200`, `dlogz_init=0.5`) **specifically chosen to meet the h/event constraint**. *Note: Uses Bilby/Dynesty per **Amended FR-005** and **Constitution Principle VII (Modified)** due to CI constraints. **Depends on T002.x** (Amendment) and **T040.3** (Baseline).*
- [ ] T027 [US3] Implement `src/pe/compare_posteriors.py` to:
 - Compute `Bias_Compressed` (Posterior Mean - True Value)
 - Calculate credible interval overlap between original and compressed posteriors
 - **Attempt Hierarchical Bayesian Shift Test** first (FR-007). **If convergence fails** (defined as ESS < 100), fallback to Paired t-tests (alpha=0.05) **APPLYING THE BENJAMINI-HOCHBERG CORRECTION**.
 - **Implementation Detail**: This task MUST use the `statsmodels.stats.multitest.multipletests` function (method='fdr_bh') for the Benjamini-Hochberg correction. Do NOT implement the algorithm inline. Ensure `statsmodels` is installed.
 - **Dependency**: Depends on **T040.3** (Baseline) and **T026** (PE Run).
- [ ] T028 [US3] Implement logic to load `Bias_Original` from `data/external/baseline_bias_original.json` (verified by T028.1) and calculate `Delta_Bias`. *Note: Operates under **Amended SC-003**. Hard dependency on T040.3.*
- [ ] T030 [US3] Create `src/pe/main.py` to orchestrate PE runs for all compressed variants and generate final bias report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data, US2 compressed data, and Phase 4.5 Baseline (T040.3)

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
- Different user stories can be worked on in parallel by different team members

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
- **Spec/Plan Alignment**: Tasks reference Plan amendments where Spec requirements (FR-005, FR-007, FR-011) are executed via feasible deviations (Bilby, Hierarchical Fallback, Synthetic Ground Truth).
- **Data Volume**: All tasks target ≥15 events to satisfy Amended FR-001 and FR-009.
- **Validation**: T014 validates known true parameters from synthetic injections, not posteriors.
- **Compression**: T020.3 records JPEG2000 folding deviation in provenance per Constitution Principle VII (Modified).
- **PE Method**: T026 uses Bilby/Dynesty per Amended FR-005 and Constitution Principle VII (Modified).
- **Statistical Tests**: T027 attempts Hierarchical Bayesian tests; fallback to Paired t-tests is authorized by Plan Complexity Tracking.
- **Amendments**: T001.1-T002.4 are mandatory formal amendment tasks to update spec artifacts in Phase 0.1 before implementation.