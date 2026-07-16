# Tasks: Quantifying the Impact of Data Gaps on Reconstructed CMB Maps

**Input**: Design documents from `/specs/001-cmb-gap-bias-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per `plan.md` by executing: `mkdir -p code/simulation code/gap_filling code/analysis code/pipeline data/raw data/derived data/metadata data/results tests/contract tests/unit tests/integration`.
- [X] T002 Initialize Python version project by creating `code/requirements.txt` containing pinned versions: `healpy>=1.15.0`, `camb`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `astropy`, `pytest`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/config.py` with global constants, random seeds, and path definitions (Constitution I).
- [X] T005 [P] Create `contracts/simulation.schema.yaml` and `contracts/analysis.schema.yaml` defining CMBMap, GapConfig, PowerSpectrum, ParameterPosterior, and SensitivityAnalysis entities (Plan Task 1.2).
- [X] T006 [P] Implement `code/data_io.py` for loading/saving HEALPix `.fits` and JSON metadata with checksums (Constitution III, V).
- [ ] T007 [P] Create `code/pipeline/pilot_runner.py` to execute a fixed minimal subset (1 realization, 1 algorithm, 1 gap fraction) for runtime estimation. Verify the pilot completes successfully and records the execution time in `data/results/pilot_log.json` for budget calculation. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T008 Setup CI workflow (`.github/workflows/ci.yml`) to install dependencies and verify package availability (healpy>=1.15.0) before analysis (Assumption: CI).
- [X] T033 [P] Implement `code/pipeline/budget_check.py` (Dynamic Budget Check logic per FR-006):
 - Run pilot (T007) to estimate runtime.
 - Calculate max N.
 - **Explicit Reduction Logic**: If N < 30, reduce N_fractions first, then N_algos, then N_realizations (down to 30 minimum if budget allows, else halt).
 - Log specific configuration changes (original vs. final N_fractions, N_algos, N_realizations) to `data/results/run_log.yaml`.
 - Output the final configuration (N_realizations, N_fractions, N_algos) for downstream tasks.
- [X] T034 [P] Integrate `generate_maps.py` with `pilot_runner.py` and `budget_check.py` via a wrapper script `code/pipeline/integration_hook.py` that orchestrates the budget check and triggers the main analysis with the determined configuration.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Simulated CMB Maps with Controlled Gap Patterns (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth CMB maps with systematically varied gap characteristics to establish baselines for bias quantification.

**Independent Test**: Generate multiple simulation realizations with known gap parameters; verify each map contains the specified gap fraction (±0.5%) and morphology type.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test in `tests/contract/test_simulation_schema.py`: Function `test_validate_cmmap_schema` must assert that `CMBMap` schema validates a map with `Nside=512` and `gap_fraction` within tolerance.
- [X] T010 [P] [US1] Unit test in `tests/unit/test_mask_generation.py`: Function `test_gap_fraction_tolerance` must assert that generated mask pixel count matches target fraction ±0.5%.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/simulation/generate_maps.py` using `camb` to create ground-truth temperature/polarization maps with Nside=512. **Note**: Ground truth parameters are defined in `code/config.py` and recorded in metadata, not derived from external Planck data.
- [X] T012 [US1] Implement `code/simulation/utils.py` to generate gap masks with configurable fraction, spatial distribution (random, clustered), and morphology (point-source, Galactic plane). **Define gap fractions explicitly as a range of discrete thresholds (e.g., 5%, 10%, 15%, [deferred]) to evaluate model sensitivity across varying levels of data sparsity.** to ensure measurable success criteria.
- [ ] T013 [US1] Implement logic to write ground-truth parameters to `data/metadata/{realization_id}.json`. Read ground-truth values from `code/config.py` or CAMB generation log. Schema MUST include keys: `realization_id`, `H0`, `Omega_m`, `n_s`, `tau`, `seed`, `camb_version`.
- [ ] T014a1 [US1] Implement function `generate_random_mask` to create random gap masks for standard realizations.
- [ ] T014a2 [US1] Implement function `generate_clustered_mask` to create clustered gap masks.
- [ ] T014a3 [US1] Implement function `generate_morphology_masks` to create point-source and Galactic plane masks.
- [ ] T014b1 [US1] Implement function `generate_null_model` to generate Null Model realizations (random gaps uncorrelated with signal).
- [ ] T014b2 [US1] Implement verification logic to ensure Null Model baseline is correctly established and output to `data/derived/null_model/`.
- [ ] T015 [US1] Add error handling for corrupted files: log error, skip realization, and continue (Edge Case: corrupted files).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply Gap-Filling Algorithms and Compute Power Spectra (Priority: P2)

**Goal**: Apply multiple gap-filling algorithms to masked maps and compute angular power spectra (Cℓ) using HEALPix Nside=512.

**Independent Test**: Apply each algorithm to a masked map; verify recovered Cℓ values differ from known baseline by <5% for ℓ=100-1000 and no NaN values exist.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test in `tests/contract/test_analysis_schema.py`: Function `test_validate_powerspectrum_schema` must assert `PowerSpectrum` schema validates `Cℓ` values with no NaNs.
- [X] T018 [P] [US2] Unit test in `tests/unit/test_timing.py`: Function `test_execution_time_limit` must assert that each algorithm completes in ≤30 minutes.

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/gap_filling/harmonic_interp.py` (Harmonic Interpolation) ensuring no NaNs in output.
- [X] T020 [P] [US2] Implement `code/gap_filling/wiener_filter.py` (Wiener Filtering) ensuring no NaNs in output.
- [X] T021 [P] [US2] Implement `code/gap_filling/iterative_synthesis.py` (Iterative Harmonic Synthesis) ensuring no NaNs in output.
- [X] T022 [US2] Implement `code/analysis/power_spectra.py` using `healpy.anafast` to compute Cℓ for ℓ ≤ 2000.
- [ ] T023 [US2] Implement logic to record algorithm name, version, and execution time in `data/metadata/{realization_id}_algo_{name}.json`. Schema MUST include keys: `algo_name`, `algo_version`, `exec_time_sec`, `timestamp`.
- [ ] T024 [US2] Add convergence failure handling: log failure, record gap config, exclude from analysis (FR-008).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Estimate Cosmological Parameters and Quantify Bias (Priority: P3)

**Goal**: Estimate cosmological parameters from recovered power spectra and compute bias magnitude relative to ground-truth values.

**Independent Test**: Compare recovered parameters against ground-truth; verify bias calculation and statistical significance (p < 0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test in `tests/contract/test_analysis_schema.py`: Function `test_validate_parameter_posterior` must assert `ParameterPosterior` schema includes `median`, `ci_68`, `ci_95`, `ground_truth`.
- [ ] T026 [P] [US3] Integration test in `tests/integration/test_bias_pipeline.py`: Function `test_full_bias_pipeline` must assert that running the full pipeline produces `data/results/bias_summary.csv` with valid rows.

### Implementation for User Story 3

- [X] T027a [US3] Implement `code/analysis/custom_likelihood.py` to provide a custom likelihood correction path (alternative to mode-coupling) per FR-009.
- [X] T027 [US3] Implement `code/analysis/mode_coupling.py` to calculate the Mode-Coupling (Leakage) Matrix from the gap mask (FR-009). Output to `data/derived/leakage_matrix_{realization_id}.npy`.
- [X] T028c [US3] **Prerequisite**: Implement `code/analysis/generate_grid.py` to generate a **Pre-computed CAMB Likelihood Grid**. This task MUST use the CAMB/CosmoMC pipeline (Constitution VII) to generate a grid of likelihoods for a range of parameters (H₀, Ωₘ, nₛ, τ) and save it to `data/derived/camb_grid.pkl`. This grid will serve as the fast estimator for the main analysis (satisfying Spec FR-004 runtime).
- [X] T028a [US3] Implement `code/analysis/parameter_est.py` Step 1: Load leakage matrix from T027.
- [X] T028b [US3] Implement `code/analysis/parameter_est.py` Step 2: Apply leakage matrix to theoretical spectrum to correct the input, then estimate parameters (H₀, Ωₘ, nₛ, τ) by querying the **Pre-computed CAMB Likelihood Grid** (from T028c). Record ground-truth vs. recovered. **Note**: CosmoMC is reserved for spot-checking ≤ 5 realizations as per FR-004. <!-- FAILED: unspecified -->
- [~] T029a [US3] Implement `code/analysis/bias_analysis.py` Step 1: Calculate `bias_magnitude` = |recovered - ground_truth|. Output to `data/results/bias_summary.csv`.
- [~] T031 [US3] Implement comparison of observed bias trends against the **Null Model** baseline (from T014b1/T014b2, Data Ready) to ensure independence. (Depends on T029a and T014b).
- [ ] T029b1 [US3] Define the **Linear Regression Model** with interaction terms (Fraction × Algorithm × Morphology) and quadratic terms for gap fraction (implementation of FR-005 ANOVA/linear regression).
- [ ] T029b2 [US3] Implement Linear Regression fitting using `statsmodels.formula.api.ols` with the defined formula.
- [ ] T029b3 [US3] Save Regression results (coefficients, p-values, R-squared) to `data/results/regression_results.csv`.
- [~] T029c [US3] Apply Bonferroni or Benjamini-Hochberg multiple-comparison correction (FR-005) to Regression results.
- [ ] T030 [US3] Implement sensitivity analysis sweep (α ∈ {low, medium, high} and tolerance ∈ {low, medium, high}) and store results in `data/results/sensitivity_sweep.json` with fields: `alpha`, `tolerance`, `bias_variance`, `significance_change`.
- [~] T032 [US3] Implement final aggregation logic to ensure minimum 30 valid realizations are retained.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T035 [P] Documentation updates in `quickstart.md` with environment setup and pilot run instructions.
- [ ] T036 Code cleanup and refactoring of `code/pipeline/run_analysis.py` to use a generator pattern for memory safety, ensuring peak RAM < 7GB.
- [~] T037 Performance optimization: ensure float32 usage where precision allows to fit within 7GB RAM.
- [~] T038 [P] Additional unit tests for `mode_coupling.py` and `parameter_est.py` in `tests/unit/`.
- [ ] T039 Run full pipeline on a small subset to verify memory and time constraints (Task 3.2).
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (masked maps)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (power spectra)

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

### Specific Task Dependencies (Phase 5)

- **T027a (Custom Likelihood)**: No dependencies within Phase 5.
- **T027 (Mode-Coupling)**: No dependencies within Phase 5.
- **T028c (Grid Generation)**: No dependencies within Phase 5. (Must run before T028b).
- **T028a (Load Leakage)**: Depends on T027.
- **T028b (Parameter Est)**: Depends on T028a AND T028c (Grid).
- **T029a (Bias Calc)**: Depends on T028b.
- **T031 (Null Model)**: Depends on T029a AND T014b (Null Model Data).
- **T029b1 (Define Regression)**: Depends on T031 (or T029a if Regression is independent of Null comparison, but logically follows bias calc).
- **T029b2 (Fit Regression)**: Depends on T029b1.
- **T029b3 (Save Regression)**: Depends on T029b2.
- **T029c (Correction)**: Depends on T029b3.
- **T030 (Sensitivity)**: Depends on T029c.
- **T032 (Aggregation)**: Depends on T030.
- **T033 (Budget Check)**: Depends on T007 (Pilot) and T011 (Simulation).
- **T034 (Integration)**: Depends on T007, T011, and T033.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence