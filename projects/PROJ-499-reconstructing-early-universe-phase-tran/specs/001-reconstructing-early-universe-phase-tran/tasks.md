# Tasks: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

**Input**: Design documents from `/specs/001-reconstructing-early-universe-phase-tran/`
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

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-499-reconstructing-early-universe-phase-tran/`) with the following exact directories: `data/raw`, `data/derived`, `data/synthetic`, `code`, `tests/unit`, `tests/integration`, `tests/contract`, `docs`, `state`.
- [X] T002 Initialize a Python project with `requirements.txt` (pinning `healpy==1.16.5`, `dynesty==2.1.3`, `emcee==3.1.6`, `numpy==1.24.3`, `scipy==1.11.4`, `requests==2.31.0`, `pyyaml==6.0.1`, `astropy==5.3.4`, `astroquery==0.4.6`).
- [X] T003a [P] Create `.flake8` configuration file with `max-line-length=88`, `ignore=E203,W503`, and `exclude=venv,.git`.
- [X] T003b [P] Create `pyproject.toml` section for `black` with `line-length=88` and `target-version=['py311']`.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/` directory structure (`raw/`, `derived/`, `synthetic/`) and `.gitignore` for large files
- [X] T005 [P] Implement `code/utils.py` with the following exact function signatures:
 - `verify_checksum(file_path: str, expected_hash: str) -> bool`: Uses SHA-256 to verify file integrity.
 - `retry_download(url: str, max_retries: int = 3, base_delay: float = 1.0) -> bytes`: Implements exponential backoff logic.
 - **Constitution Check**: Ensure `verify_checksum` is used to satisfy Constitution Principle III (Data Hygiene).
- [X] T006 [P] Setup `code/` module structure with `__init__.py` and relative import configuration
- [X] T007 Create base configuration loader in `code/config.py` to handle `random.seed` pinning and CPU-only constraints, and to store verified dataset URLs (keys: `PLANCK_MAP_ID`, `BICEP_URL`).
- [X] T008 Setup `tests/` directory structure (`unit/`, `integration/`, `contract/`) with `pytest.ini`
- [ ] T020a [P] [US2] Implement `code/synthetic_data.py` function `generate_inflation_synthetic` to create synthetic B-mode maps with $r=0.01$. **Artifact**: `data/synthetic/ground_truth_inflation.json`, `data/synthetic/inflation_synthetic.fits`.
- [ ] T020c [P] [US2] Implement `code/synthetic_data.py` function `generate_pt_synthetic` to create synthetic B-mode maps with $E_{PT}=10^{15}$ GeV. **Artifact**: `data/synthetic/ground_truth_pt.json`, `data/synthetic/pt_synthetic.fits`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0.5: Synthetic Validation (GATED)

**Purpose**: Validate the pipeline against synthetic data BEFORE processing real data.
**GATE**: This phase MUST pass before Phase 2 (US1) begins.
**Note**: This phase now correctly depends on Phase 1 (Foundational) being complete.

### Tests for Synthetic Validation
- [X] T024 [P] [US2] Contract test for synthetic data generation in `tests/contract/test_synthetic_data.py`
- [X] T025 [P] [US2] Integration test for validation pipeline in `tests/integration/test_synthetic_validation.py`

### Implementation for Synthetic Validation

- [ ] T025a [US2] Implement `code/inference.py` function `run_inference_synthetic` to run dynesty on `data/synthetic/inflation_synthetic.fits`. **Artifact**: `data/synthetic/inference_results_inflation.json`.
- [ ] T025b [US2] Implement `code/validation.py` function `validate_inflation_synthetic` to verify posterior for $r$ covers true value within 95% CI and is centered within 10%. **Metric**: Check if true_value is within [percentile_2.5, percentile_97.5] and |(mean - true)|/true < 0.10 (SC-005). **Artifact**: `data/validation/validation_report_inflation.json`.

- [ ] T025c [US2] Implement `code/inference.py` function `run_inference_pt_synthetic` to run dynesty on `data/synthetic/pt_synthetic.fits`. **Artifact**: `data/synthetic/inference_results_pt.json`.
- [ ] T025d [US2] Implement `code/validation.py` function `validate_pt_synthetic` to verify posterior for $E_{PT}$ covers true value within 95% CI and is centered within 10%. **Metric**: Check if true_value is within [percentile_2.5, percentile_97.5] and |(mean - true)|/true < 0.10 (SC-005). **Artifact**: `data/validation/validation_report_pt.json`.

- [ ] T025g [US2] Implement `code/validation.py` function `validate_bayes_factor_synthetic` to verify Bayes factor correctly distinguishes between models ($K > 10$) in synthetic cases. **Artifact**: `data/validation/bayes_factor_validation.json`.

**Checkpoint**: Synthetic Validation complete. Pipeline is validated. Proceed to Phase 2 only if T025a-g pass.

---

## Phase 2: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, mask, and prepare Planck 2015 and BICEP/Keck B-mode polarization maps to compute clean angular power spectra.

**Independent Test**: The pipeline can be fully tested by running it on a subset of the sky (e.g., a single HEALPix patch) and verifying that the output power spectrum matches known theoretical expectations for lens-only B-modes in that region. **Note**: While this test is theoretically possible, the *execution* of this phase on real data is gated by the success of Phase 0.5.

### Tests for User Story 1 (TDD First) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data download integrity in `tests/contract/test_data_ingestion.py`
- [X] T011 [P] [US1] Integration test for masked map generation in `tests/integration/test_masking.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_ingestion.py` to download Planck SMICA B-mode maps and BICEP/Keck spectra. **Input**: Read `PLANCK_MAP_ID` and `BICEP_URL` from `code/config.py`. **Dependencies**: Call `retry_download` and `verify_checksum` from `code/utils.py` (T005). **Output**: Store downloaded files as `data/raw/planck_smica_bmode.fits` and `data/raw/bicep_spectrum.json`. **Artifact**: Write SHA-256 checksums to `data/hashes.json` with schema: `{"file_path": "sha256_hash"}`. Implement retry logic for corrupted downloads. **Requirement**: Explicitly satisfy FR-001 and Constitution Principle III.
- [ ] T015a [US1] Implement `code/data_ingestion.py` function `verify_planck_mask_coverage` to read the Planck 2015 Common Mask file and extract the official sky coverage percentage. **Output**: Write the verified coverage value to `data/derived/mask_coverage_verified.json`. **Requirement**: This task verifies the threshold used in T015 against the official mask metadata.
- [ ] T013 [US1] Implement `code/data_ingestion.py` function `apply_planck_mask` to apply Planck 2015 Common Mask to B-mode maps (FR-002). **Input**: `data/raw/planck_smica_bmode.fits`. **Output**: `data/derived/masked_bmode.fits`.
- [ ] T014 [US1] Implement `code/spectrum_computation.py` to compute $C_\ell^{BB}$ from masked maps using `pyHEALPix` (healpy) in CPU-only mode (FR-003). **Output**: `data/derived/cl_bb_spectrum.json`.
- [ ] T015 [US1] Implement `code/data_ingestion.py` function `verify_sky_coverage(masked_map: np.ndarray) -> float` to calculate sky coverage. **Behavior**: **Raise ValueError** if `coverage < 0.70` (verified in T015a). **Artifact**: Write coverage report to `data/derived/coverage_report.json`. **Requirement**: Explicitly satisfy FR-002, US1 Acceptance Scenario 1, and SC-001.
- [ ] T016 [US1] Add logging for data ingestion and masking operations with checksum verification status.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Theoretical Model Generation and Fitting (Priority: P2)

**Goal**: Generate theoretical B-mode power spectra for inflationary, phase transition, and null models, and fit them to observed data using CPU-tractable Nested Sampling.

**Independent Test**: The fitting routine can be tested independently by generating synthetic data from a known model (e.g., $r=0.01$ inflation) and verifying that the sampler recovers the input parameters within 1$\sigma$ confidence intervals.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for synthetic data generation in `tests/contract/test_model_generation.py`
- [X] T019 [P] [US2] Integration test for Nested Sampling convergence in `tests/integration/test_inference.py`

### Implementation for User Story 2

- [ ] T020b [US2] Implement `code/model_generation.py` function `generate_null_model` to generate the Null (lens-only) theoretical spectrum. **Input**: Standard lensing template. **Output**: JSON file with schema `{"model_type": "null", "params": {}, "l_values": list[int], "cl_values": list[float]}`. **Requirement**: Explicitly satisfy FR-004 (Null model).
- [X] T020 [P] [US2] Implement `code/model_generation.py` to generate theoretical spectra for Inflation and Phase Transition. **Input**: Grid of $r$ over a relevant small-range interval and $E_{PT} \in [10^{14}, 10^{16}]$ GeV (log scale). **Output**: JSON file with exact schema: `{"model_type": str, "params": dict, "l_values": list[int], "cl_values": list[float]}` (FR-004).
- [X] T021a [US2] Implement `code/inference.py` using `dynesty` (Nested Sampling) with limited live points (e.g., 50) for CPU feasibility to estimate posteriors for $r$ and $E_{PT}$ (Plan requirement, FR-005). **Note**: Overrides FR-005 in spec (emcee) per Plan Section: Technical Context (dynesty for CPU stability). **Artifact**: `data/derived/posterior_samples.json`.
- [X] T022 [US2] Implement `code/inference.py` to detect non-convergence (evidence estimate instability, `logz_change` or `eff` metrics) and log warnings or extend the run (Edge Case).
- [X] T023 [US2] Implement `code/inference.py` to clamp model predictions for $\ell < 2$ and flag extrapolated points (Edge Case).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Model Comparison and Statistical Validation (Priority: P3)

**Goal**: Compute Bayes factors using Nested Sampling and perform null tests using independent sky patches to distinguish between models.

**Independent Test**: The validation suite can be tested by splitting synthetic data into two halves, running the full analysis on each, and verifying that the Bayes factors and parameter estimates are consistent within statistical fluctuations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for Bayes factor precision in `tests/contract/test_model_comparison.py`
- [X] T027 [P] [US3] Integration test for sky patch consistency in `tests/integration/test_sky_split.py`

### Implementation for User Story 3

- [X] T028a [P] [US3] Implement `code/model_comparison.py` to compute Bayes factors via `dynesty` evidence calculation for Inflation vs. Phase Transition vs. Null (Plan requirement, FR-006). **Note**: Overrides FR-006 in spec (thermodynamic integration) per Plan Section: Technical Context (dynesty for stability).
- [X] T029 [US3] Implement `code/validation.py` to split sky into independent patches (Northern/Southern) and verify consistency of best-fit $r$ values (FR-007). **Requirement**: Verify coordinate invariance by ensuring $|r_{north} - r_{south}|$ is negligible. **Artifact**: `data/derived/patch_consistency_report.json`.
- [X] T030 [US3] Implement `code/model_comparison.py` to report Bayes factor $K$ with 2 decimal places precision and decision thresholds ($K > 10$) (US3 Acceptance 1).
- [X] T031 [US3] Add plotting functionality in `code/plotting.py` to visualize posteriors and Bayes factors for all models.
- [ ] T032 [US3] Implement `code/utils.py` to generate `data/derived/model_comparison_results.json` with exact schema from contracts/
- [ ] T049 [US3] Implement `code/validation.py` function `validate_bayes_factor_observed` to compute Bayes factors on **observed data** (after Phase 0.5 gate passes) and verify $K > 10$ for the correct model. **Artifact**: `data/validation/bayes_factor_observed.json`. **Requirement**: Must satisfy SC-002 and SC-003.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Research-Stage Review Resolution (Priority: P1)

**Goal**: Address the "albert-einstein-simulated" review regarding reference frame invariance and statistical observability by integrating checks into existing tasks and adding Phase 6 for rigorous validation.

### Implementation for Review Resolution

- [X] T029 [US3] (Enhanced) **Note**: This task now explicitly includes the verification of coordinate invariance via sky patch consistency (Northern/Southern), addressing the reviewer's concern about "reference frame invariance" without adding un-specified physics modeling tasks.
- [X] T049 [US2] (Enhanced) **Note**: This task explicitly validates statistical observability via Bayes factors on observed data, addressing the "statistically detectable signatures" concern without adding un-specified SNR thresholds.

**Checkpoint**: Review concerns addressed via integration into existing core tasks; no scope creep.

---

## Phase 6: Reference Frame Invariance & Statistical Observability Validation (Priority: P1)

**Goal**: Explicitly address the "albert-einstein-simulated" review concern: "What invariant quantity, under change of reference frame, distinguishes the signal from the noise?" by implementing rigorous coordinate transformations and statistical robustness checks.

**Independent Test**: The validation suite must demonstrate that the Bayes factor $K$ and parameter estimates ($r$, $E_{PT}$) remain statistically consistent when the sky map is rotated by arbitrary angles and when the coordinate system is transformed (e.g., Galactic to Ecliptic).

### Implementation for Review Resolution

- [ ] T045 [US3] Implement `code/validation.py` function `rotate_sky_map` to apply HEALPix rotation matrices using `healpy.rotator` to `data/derived/masked_bmode.fits` by random angles (0° to 180°) and re-compute $C_\ell^{BB}$ spectra. **Requirement**: Verify that the power spectrum $C_\ell^{BB}$ is rotationally invariant (within numerical precision) for the null (lens-only) model. **Artifact**: `data/validation/rotation_invariance_report.json`.
- [ ] T046 [US3] Implement `code/validation.py` function `transform_coordinate_system` to convert B-mode maps from Galactic to Ecliptic coordinates using `astropy.coordinates.SkyCoord` and re-run the full inference pipeline (T021a, T028a). **Requirement**: Verify that the Bayes factor $K$ and posterior distributions for $r$ and $E_{PT}$ remain unchanged (within 1$\sigma$ statistical fluctuations) across coordinate systems. **Artifact**: `data/validation/coordinate_invariance_report.json`.
- [ ] T047 [US3] Implement `code/validation.py` function `assess_statistical_observability` to compute the signal-to-noise ratio (SNR) of the phase transition signature relative to the inflationary null hypothesis across multiple random sky realizations. **Requirement**: Ensure that the "statistically detectable signature" claim is supported by a clear separation in the likelihood ratio distribution, not just a single-point estimate. **Artifact**: `data/validation/observability_assessment.json`.
- [ ] T048 [US3] Implement `code/plotting.py` to generate diagnostic plots showing the stability of $K$ and $r$ under coordinate transformations and random rotations. **Requirement**: Visualize the "invariant quantity" that distinguishes signal from noise as requested by the reviewer. **Artifact**: `docs/figures/invariance_stability_plots.pdf`.

**Checkpoint**: Reference frame invariance and statistical observability are rigorously validated. The project can now claim that detected signatures are physical and not artifacts of the coordinate system or statistical noise.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038a [P] Update `docs/quickstart.md` with new CLI flags and execution steps.
- [ ] T038b [P] Update `docs/data-model.md` with schema changes. **Specifics**: Update `dataset_schema` keys for `ground_truth_inflation`, `ground_truth_pt`, and `inference_results` to reflect Phase 0.5 and Phase 1-3 outcomes.
- [ ] T038c [P] Update `docs/research.md` with final results (Phase 0.5 and Phase 1-3 outcomes).
- [X] T039 [P] Code cleanup and refactoring for CPU efficiency: **Deliverable**: Refactor `code/inference.py` to ensure max cyclomatic complexity < 10 as measured by `radon`. **Artifact**: Generate `data/validation/cyclomatic_complexity_report.txt` using `radon` with max complexity threshold < 10.
- [ ] T040 [P] Performance optimization across all stories: **Deliverable**: Optimize `code/inference.py` to reduce runtime of 1000-step `dynesty` run on Nside=64 synthetic data to < 2 hours on CPU. **Artifact**: Generate `data/validation/performance_report.json` containing timing metrics.
- [ ] T041 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T042 Security hardening for data download URLs
- [ ] T043 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution within 6 hours. **Artifact**: Generate `data/validation/quickstart_execution_log.txt`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - can start immediately
- **Phase 1 (Foundational)**: Depends on Phase 0 completion - BLOCKS all user stories and Phase 0.5
- **Phase 0.5 (Synthetic Validation)**: Depends on Phase 1 completion. **GATE**: Must pass before Phase 2.
- **Phase 2 (US1)**: Depends on Phase 1 completion AND Phase 0.5 success (GATED).
- **Phase 3 (US2)**: Depends on Phase 1 completion (can use synthetic data for validation without real data)
- **Phase 4 (US3)**: Depends on Phase 3 completion
- **Phase 5 (Review Resolution)**: Integrated into Phase 2/3/4 tasks; no separate execution phase needed.
- **Phase 6 (Invariance Validation)**: Depends on Phase 4 completion. **GATE**: Must pass before final reporting.
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories, but execution on real data is gated by Phase 0.5.
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on US1 data ingestion for real data, but can use synthetic data for validation
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on US2 for model fitting results
- **Review Resolution (Phase 5)**: Integrated into existing tasks.
- **Invariance Validation (Phase 6)**: Depends on US3 results.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data download integrity in tests/contract/test_data_ingestion.py"
Task: "Integration test for masked map generation in tests/integration/test_masking.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download Planck 2015 SMICA B-mode maps"
Task: "Implement code/data_ingestion.py to apply Planck 2015 Common Mask"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup
2. Complete Phase 1: Foundational
3. Complete Phase 0.5: Synthetic Validation (GATED)
4. Complete Phase 2: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Review Resolution (Integrated) → Validate invariance and observability
6. Add Invariance Validation (Phase 6) → Rigorous coordinate and statistical checks
7. Each story adds value without breaking previous stories

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
- **Critical**: Phase 0.5 Synthetic Validation (T025a-g) MUST pass before any observational data is processed (Plan Gate).
- **Critical**: All tasks must run on CPU-only (2 cores, 7GB RAM) within 6 hours.
- **Critical**: No fake data; all synthetic data must be generated from known ground truth models.
- **Critical**: Primary inference engine is `dynesty` (Nested Sampling) as per Plan and updated Spec (FR-005, FR-006). **Note**: T021a and T028a explicitly override FR-005/FR-006 per Plan Section: Technical Context.
- **Critical**: Review concerns regarding invariance and observability are addressed by enhancing T029 and T049, and adding Phase 6 (T045-T048) for rigorous validation.
- **Critical**: T012 and T015 now explicitly define artifacts and hard gates to satisfy FR-001, FR-002, and Constitution Principle III. T015a verifies the threshold source.
- **Critical**: Phase 6 (T045-T048) is mandatory to address the "albert-einstein-simulated" review regarding reference frame invariance and statistical observability.
- **Critical**: T020a, T020b, T020c cover Inflation, Null, and Phase Transition models respectively, ensuring FR-004 is fully satisfied.