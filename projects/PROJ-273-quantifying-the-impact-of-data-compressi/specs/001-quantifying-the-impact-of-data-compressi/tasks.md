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

---

## Phase 0.1: Spec & Constitution Amendments (BLOCKING PREREQUISITES)

**Purpose**: Formalize all necessary deviations from the original spec and constitution before implementation begins.
**⚠️ CRITICAL**: No implementation tasks (Phase 1+) can begin until this phase is complete. All Txx.0 tasks MUST update `spec.md` and `plan.md` with the exact amended text.

### Step 1: Provenance Creation & Definition (T001.0)

- [ ] T001.0 [P] [Constitution] **Create Provenance Records**: Create the following provenance files in `code/provenance/` to formally record deviations:
 1. `deviation_constitution_principle_ii.md`: Record deviation from Principle II (Verified Accuracy) for synthetic injections. *Content*: (1) Original principle text, (2) Deviation (synthetic injections), (3) Justification (Plan Complexity Tracking), (4) Mitigation (LALSimulation + known ground truth).
 2. `deviation_JPEG2000_folding.md`: Record deviation for 1D-to-2D folding. *Content*: Hilbert curve algorithm details, transformation parameters (2048x1024), validation strategy.
 3. `deviation_LALInference_Bilby.md`: Record deviation from Principle VII (Parameter-Estimation Integrity). *Content*: Original text, deviation (Bilby/Dynesty), justification (CI constraints).
 4. `deviation_Hierarchical_Fallback.md`: Record deviation for statistical testing fallback. *Content*: Original text, deviation (Paired t-tests), justification (Plan Complexity Tracking).
 *Action*: Create files and update `state/projects/PROJ-273-quantifying-the-impact-of-data-compression.yaml` with `artifact_hashes` for these files.

### Step 2: Draft Spec Amendments (T002.0)

- [ ] T002.0 [P] [Spec] **Draft Spec Amendments**: Create a draft document `specs/001-compression-impact-gw-reconstruction/amendment_draft.md` containing the exact text to be applied to `spec.md`. *Edit Instructions for Draft*:
 1. **FR-001**: Replace text with: "FR-001: System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns. The system MUST iterate fetching noise segments and generating injections until ≥12 valid events with complete spin metadata are found, or a maximum of 100 attempts is reached. If a sufficient number of valid events are not found after a predefined number of attempts, the system MUST fail with an error."
 2. **FR-003**: Update text to include: "For wavelet-based image compression standards, a D-to-D folding transformation (Hilbert curve) is applied to adapt multi-dimensional codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression' as recorded in `code/provenance/deviation_JPEG2000_folding.md`."
 3. **FR-005**: Replace text with: "FR-005: System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints."
 4. **FR-007**: Replace text with: "FR-007: System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100) or sample size N < 12, the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. This deviation is authorized by Plan Complexity Tracking."
 5. **FR-009**: Replace text with: "FR-009: System MUST exclude any event lacking complete spin metadata (specifically tilt angle posteriors) from the analysis set. The final analysis set must contain ≥ 12 events with complete spin metadata. [UNRESOLVED-CLAIM: c_6b5544e8 — status=not_enough_info] If a sufficient number of events are not found after a predefined threshold of attempts, the system MUST fail with an error."
 6. **SC-003**: Replace text with: "SC-003: Parameter estimation bias is measured against an external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value)."
 7. **US-1 Narrative**: Update to reflect "generate synthetic CBC injections into real GW noise segments" and "known true parameters".
 8. **US-1 Acceptance**: Update Scenario 2 to reflect "synthetic injections" and "known true parameters".
 9. **US-3 Narrative**: Update to reflect "`Bilby` with `Dynesty` (Fast PE)" and "fallback to Paired t-tests".
 10. **US-3 Acceptance**: Update Scenario 1 to reflect "Bilby/Dynesty" and "Fast PE".
 11. **US-2 Narrative**: Update to include "via 1D-to-2D folding (Hilbert curve)" for JPEG2000.
 12. **SC-005/SC-006**: Update to explicitly mention "measured against known ground truth of **synthetic injections**".
 *Note*: This task creates the draft document. It does NOT edit `spec.md` directly.

### Step 3: Validate Draft (T001.9)

- [ ] T001.9 [P] [Amendment] **Validate Draft Amendments**: Review `amendment_draft.md` to ensure all deviations are consistent with the Plan and Constitution. *Action*: Verify that the text in `amendment_draft.md` matches the requirements in `plan.md` and `spec.md`. *Dependency*: T002.0.

### Step 4: Approve and Apply Spec Amendments (T002.1)

- [ ] T002.1 [P] [Spec] **Approve and Apply Spec Amendments**: Update `spec.md` and `plan.md` with the exact text from `amendment_draft.md`. *Edit Instructions*:
 1. Locate the `Functional Requirements` section in `spec.md` and replace FR-001, FR-003, FR-005, FR-007, FR-009 with the text from `amendment_draft.md`.
 2. Locate the `Success Criteria` section in `spec.md` and replace SC-003, SC-005, SC-006.
 3. Locate the `User Scenarios` section in `spec.md` and update US-1, US-2, US-3 narratives and acceptance scenarios.
 4. Update `plan.md` Constitution Check table: Change Principle II status to "Pass (Modified)" with note: "Deviation recorded in code/provenance/deviation_constitution_principle_ii.md". Change Principle VII to "Pass (Modified)" with note: "Bilby/Dynesty authorized for pilot phase".
 *Dependency*: Must be completed before T013, T020, T026. *Prerequisite*: T001.9 (Draft Validation).

### Step 5: Smoke Test (T001.8)

- [ ] T001.8 [P] [Amendment] **Run Code Structure Smoke Test**: **Blocked until T002.1 complete**. Run a minimal smoke test to verify that the amended approach (Synthetic Injections + Bilby/Dynesty) is viable before full implementation. *Action*: Execute a single synthetic injection using a **minimal sine wave** (numpy array of 1000 points, frequency 50Hz) and a single Bilby/Dynesty run with **reduced iterations** (`maxiter=100`, `nlive=20`) using a **real minimal config** (dict: `{'maxiter': 100, 'nlive': 20, 'likelihood': 'Gaussian'}`). Log success/failure. Expected log message: "SMOKE TEST PASSED". This task is a prerequisite for T013 and T020 **only for code structure**, not semantic validity. *Note: This task uses a minimal valid waveform to avoid circular dependency on T013/T026.*

---

## Phase 1: Setup & Documentation (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and required documentation artifacts.

- [ ] T003.1 [P] **Configure Linting**: Create `pyproject.toml` at repository root. Add `[tool.ruff]` section with `select = ["E", "W", "F"]` and `target-version = "py311"`.
- [ ] T003.2 [P] **Configure Formatting**: Add `[tool.black]` section to `pyproject.toml` with `line-length = 88` and `target-version = ["py311"]`.
- [ ] T006.1 [P] **Create Data Directories**: Create `data/raw/`, `data/interim/`, `data/processed/`, `data/external/` directories.
- [ ] T007.1 [P] **Create Test Directories**: Create `tests/unit/`, `tests/integration/`, `tests/contract/` directories.
- [ ] T008.1 [P] **Configure Pytest**: Create `pytest.ini` at repository root. Set `timeout = 300` and `addopts = "-v --cov=src --cov-report=term-missing"`.
- [ ] T017.1 [P] [Docs] **Create quickstart.md**: Create `quickstart.md` in `specs/001-compression-impact-gw-reconstruction/` as required by the plan. *Content*: Step-by-step pipeline execution guide. *Note*: This is a documentation artifact, not a test.
- [ ] T017.2 [P] [Docs] **Create contracts directory**: Create `specs/contracts/` directory and initialize with a placeholder `README.md` describing the contract testing strategy. *Note*: This is a documentation artifact, not a test.
- [ ] T017.3 [P] [Docs] **Create data-model.md**: Create `data-model.md` in `specs/001-compression-impact-gw-reconstruction/` as required by the plan. *Content*: Schema definitions for GWOSCEvent, CompressionArtifact, ParameterPosterior. *Note*: This is a documentation artifact, not a test.

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
- [X] T013 [P] [US1] **Blocked until T002.1 and T001.8 complete**. Implement `src/data/inject.py` using `LALSimulation` to generate CBC waveforms with **known true parameters** (Mass, Spin, Distance) injected into the fetched noise for **a set of target events**. *Note: Operates under **Amended FR-001**. Generates metadata with 'true_parameters', not posteriors.*
- [X] T014 [US1] Implement `src/data/validate.py` to check for: strain time series, detector names, event timestamps, **known true parameters** (ground truth), and **spin metadata (tilt angles)** (FR-008, FR-009). *Note: Validates 'known true parameters' from synthetic injections, not posteriors. Operates under Amended FR-008/009.*
- [X] T019.1 [US1] **Implement Fetch Loop**: Implement the logic in `src/data/fetch_loop.py` to fetch noise segments **one by one** (`batch_size=1`) and inject/validate until **≥12 valid events** with complete spin metadata are found or `max_attempts=100` is reached. *Note: Implements a loop to ensure the final analysis set meets Amended FR-009. **MUST include max_attempts=100 and timeout=300s**. **Loop Condition:** `while valid_count < 12 and attempts < 100`. **Batch Size:** `batch_size=1` (fetch one segment per attempt). **Attempt Counting:** Increment `attempts` on every API call (success or failure). **Post-Loop Validation:** After loop, filter for valid events. If `valid_count < 12`, **raise a RuntimeError** with message "Insufficient valid events found after 100 attempts". Do NOT proceed with reduced power. **Dependency**: T013 (inject logic).*
- [ ] T020 [US1] **Blocked until T002.1 and T001.8 complete**. Create `src/data/main.py` to orchestrate the **download-inject-validate** pipeline for **≥15 target events** (per **Amended FR-001**) and produce the validated dataset. *Note: Calls T019.1 logic. **Dependency**: T019.1 must be implemented and tested.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4.5: Baseline Generation (Prerequisite for US3)

**Purpose**: Generate the `Bias_Original` baseline required for Delta_Bias calculation.
**⚠️ CRITICAL**: This phase is the bridge between US1 (Data) and US3 (PE). It cannot run until T020 completes.

- [ ] T040.1 [US3] **Select Representative Event**: Load the validated dataset from T020 and select the first event with complete spin metadata as the representative event for baseline generation. *Note: Output is the event ID.*
- [ ] T040.2b [US3] **Generate Local Convergence Baseline**: **Generate the 'Bias_Original' baseline locally** using `Bilby` with `Dynesty` on the representative event (T040.1) with **high iterations** (`maxiter=50000`, `nlive=500`) to approximate a 'pre-converged' state. *Note: Must generate `posterior_mean` and `covariance` for the specific event. Log a warning about the limitation.* *Dependency: T020 (Dataset Finalization).*
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

- [X] T017 [P] [US2] **Write** unit test for lossless compression bitwise equality in `tests/unit/test_compression.py` (`assert mse == 0`)
- [X] T018 [P] [US2] **Write** unit test for lossy compression SNR calculation in `tests/unit/test_metrics.py` (`assert snr_degradation > 0`)

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/compression/lossless.py` with wrappers for gzip, LZ4, bzip2 at varied levels including 5 and 9
- [ ] T020.1 [P] [US2] Implement `src/compression/lossy.py` - **Quantization**: Implement quantized floating-point (variable bit-widths, e.g., low-bit). and corresponding unfold step. *Note: Output paths: `data/interim/compressed/quantization/{level}/`.*
- [ ] T020.2 [P] [US2] Implement `src/compression/lossy.py` - **Wavelet**: Implement Wavelet Thresholding and corresponding unfold step. *Note: Output paths: `data/interim/compressed/wavelet/{level}/`.*
- [ ] T020.4 [P] [US2] **Define JPEG2000 Validation Metric**: Create `src/compression/validation_jpeg2000.py` containing a function `validate_transformation_artifact(original, folded, compressed)` that compares the MSE of `original` vs `unfolded(compressed)` against the theoretical MSE of the folding transformation alone. *Action*: This metric isolates compression error from folding artifacts. **Formula**: Calculate `folding_error = MSE(original, unfold(fold(original)))`. The metric returns `True` if `MSE(original, unfold(compressed)) - folding_error` is within acceptable tolerance. *Note: This task MUST be completed before T020.3. **Dependency**: T002.1 (Apply Amendments).*
- [ ] T020.3 [P] [US2] Implement `src/compression/lossy.py` - **JPEG2000**: Implement JPEG2000 via **Hilbert curve 1D-to-2D folding** (using `hilbert_curve` package, function `points2keys`; target dimensions **2048x1024**). **MUST use Hilbert curve algorithm exclusively as mandated by Amended FR-003**. *Note: Hilbert was chosen over row-major for better space-filling properties in 1D-to-2D folding, as per Plan Complexity Tracking.* **MUST implement** the corresponding **unfold** step to restore 1D data before computing reconstruction error (MSE/SNR). **MUST use the validation metric defined in T020.4** to ensure the "transformation artifact" does not invalidate the MSE/SNR comparison. *Note: Ensures SC-002 validity. Output paths: `data/interim/compressed/jpeg2000/{level}/`.*
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

- [X] T024 [P] [US3] **Write** unit test for posterior comparison logic in `tests/unit/test_pe.py` (`assert overlap > 0.5`)
- [ ] T025 [US3] Integration test for PE run and bias calculation in `tests/integration/test_pe_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/pe/run_bilby.py` wrapper for Bilby/Dynesty with **reduced iterations** (`maxiter=5000`, `nlive=200`, `dlogz_init=0.5`) **specifically chosen to meet the h/event constraint**. *Note: Uses Bilby/Dynesty per **Amended FR-005** and **Constitution Principle VII (Modified)** due to CI constraints. **Depends on T002.1** (Amendment) and **T040.3** (Baseline).*
- [ ] T027.1 [US3] **Define Failure Detection Logic**: Create `src/pe/failure_detection.py` to explicitly define how Hierarchical Bayesian test failure is detected. *Action*: Implement function `check_hierarchical_convergence(ess_value)` that returns True if `ess_value < 100`. **Input Source**: The `ess_value` must be extracted from the Bilby/Dynesty output JSON (key: `effective_sample_size`) after the PE run. *Note: This task MUST be completed before T027.*
- [ ] T027 [US3] Implement `src/pe/compare_posteriors.py` to:
 - Compute `Bias_Compressed` (Posterior Mean - True Value)
 - Calculate credible interval overlap between original and compressed posteriors
 - **Attempt Hierarchical Bayesian Shift Test** first (FR-007). **Check sample size N**: If `N < 12`, immediately fallback to Paired t-tests. **If convergence fails** (defined as ESS < 100, **detected by calling `src/pe/failure_detection.py` with the ESS value from the Bilby output JSON**), fallback to Paired t-tests (alpha=0.05) **APPLYING THE BENJAMINI-HOCHBERG CORRECTION**.
 - **Implementation Detail**: This task MUST use the `statsmodels.stats.multitest.multipletests` function (method='fdr_bh') for the Benjamini-Hochberg correction. Do NOT implement the algorithm inline. Ensure `statsmodels` is installed.
 - **Model Structure**: For the Hierarchical test (only if N ≥ 12), use a **Gaussian Mixture Model** for the population of biases. Use `bilby.hierarchical` module if available, or adapt `dynesty` for hierarchical inference.
 - **Input Vector**: Apply the correction to the p-values of the 'Mass', 'Distance', and 'Spin' parameters.
 - **Output Artifact**: Save the adjusted p-values to `data/processed/statistical_test_results.json`.
 - **Dependency**: Depends on **T040.3** (Baseline), **T026** (PE Run), and **T027.1** (Failure Detection).
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
- **Spec Amendments (Phase 0.1)**: No dependencies - MUST complete before Phase 1/2
- **Foundational (Phase 2)**: Depends on Phase 0.1 and Setup - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion and Phase 0.1 completion (for T013, T020, T026)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except T013/T020 blocked by T002.1 and T001.8)
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
- **Amendments**: T001.0-T002.1 are mandatory formal amendment tasks to update spec artifacts in Phase 0.1 before implementation.
- **Blocking Status**: T013, T020, T026 are blocked until Phase 0.1 (T002.1 and T001.8) is complete.
- **CI Constraints**: T040.2b explicitly forbids CI execution for full PE; requires local high-iteration baseline generation.