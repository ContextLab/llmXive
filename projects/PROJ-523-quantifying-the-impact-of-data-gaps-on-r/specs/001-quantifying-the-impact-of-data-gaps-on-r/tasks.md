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
- [X] T007 [P] Create `code/pipeline/pilot_runner.py` to execute a fixed minimal subset (one realization, one algorithm, one gap fraction) for runtime estimation. **MUST verify the pilot completes successfully and records the execution time in `data/results/pilot_log.json`. If the file is not written, the script MUST exit with code 1. This artifact is a hard dependency for T033.**
- [X] T008 Setup CI workflow (`.github/workflows/ci.yml`) to install dependencies and verify package availability (healpy>=1.15.0) before analysis (Assumption: CI).
- [X] T042 [P] [Foundational] Implement a pre-flight validation step in `code/pipeline/run_analysis.py` that verifies `data/results/pilot_log.json` contains a valid, non-zero `avg_time_sec` before proceeding to budget calculation. **Depends on T007 (Pilot).**
- [X] T033 [P] Implement `code/pipeline/budget_check.py` (Dynamic Budget Check logic per FR-006):
 - **Pre-flight Check**: Verify `data/results/pilot_log.json` exists. **FAIL IMMEDIATELY** with error if missing. Read execution time from this file.
 - **Dynamic Arguments**: Accept `gap_fractions` list and `algo_list` as explicit arguments from config (T012a) rather than hardcoding defaults.
 - Calculate max N based on the actual number of fractions and algorithms.
 - **Explicit Reduction Logic**: If N < 30, reduce N_fractions first, then N_algos, then N_realizations (down to a practical minimum if budget allows, else halt).
 - Log specific configuration changes (original vs. final N_fractions, N_algos, N_realizations) to `data/results/run_log.yaml`.
 - Output the final configuration (N_realizations, N_fractions, N_algos) for downstream tasks.
 - **Dependency Correction**: This task depends ONLY on T007 (Pilot) and T012a (Gap Fractions Config). It must run BEFORE the main T011 simulation loop.
- [X] T034 [P] Integrate `generate_maps.py` with `pilot_runner.py` and `budget_check.py` via a wrapper script `code/pipeline/integration_hook.py` that orchestrates the budget check and triggers the main analysis with the determined configuration. **MUST enforce strict sequential execution per realization ID: Generate Mask -> Save Mask -> Apply Gap Fill -> Compute Spectrum -> Estimate Parameters.** This satisfies the data flow ordering requirement previously flagged in T047. **Depends on T033 and T007. Does NOT depend on T011.**

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

- [X] T011 [US1] Implement `code/simulation/generate_maps.py` using `camb` to create ground-truth temperature/polarization maps with Nside=512. **Note**: Ground truth parameters are defined in `code/config.py` and recorded in metadata, not derived from external Planck data.
- [X] T012a [US1] Create `code/config/gap_fractions.yaml` to define the list of gap fractions (e.g., a sequence of increasing values spanning the low to moderate range). **MUST include a comment block documenting the rationale for these specific values.** This file is the **Source of Truth** for the budget calculation (T033) and simulation loop (T011).
- [X] T012c [US1] Consolidate documentation update: Ensure `research_decisions.md` or `spec.md` is updated to reflect the chosen gap fractions and rationale defined in `code/config/gap_fractions.yaml`. **Replaces removed T012b.**
- [X] T014 [US1] Implement `code/simulation/utils.py` to generate gap masks with configurable fraction, spatial distribution (random, clustered), and morphology (point-source, Galactic plane). **Consolidates T014a1-a3 and T014b1-b2.**
 - Implement `generate_random_mask` for standard realizations.
 - Implement `generate_clustered_mask` for clustered gaps.
 - Implement `generate_morphology_masks` for point-source and Galactic plane.
 - Implement `generate_null_model` for Null Model realizations (random gaps uncorrelated with signal).
 - Implement verification logic to ensure Null Model baseline is correctly established and output to `data/derived/null_model/`.
- [X] T013 [US1] Implement logic to write ground-truth parameters to `data/metadata/{realization_id}.json`. Read ground-truth values from `code/config.py` or CAMB generation log. Schema MUST include keys: `realization_id`, `H0`, `Omega_m`, `n_s`, `tau`, `seed`, `camb_version`.
- [X] T015 [US1] Add error handling for corrupted files: log error, skip realization, and continue (Edge Case: corrupted files).

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
- [X] T023 [US2] Implement logic to record algorithm name, version, and execution time in `data/metadata/{realization_id}_algo_{name}.json`. Schema MUST include keys: `algo_name`, `algo_version`, `exec_time_sec`, `timestamp`, `gap_config`.
- [X] T023-TEST [P] [US2] Contract test in `tests/contract/test_metadata_schema.py`: Function `test_validate_algo_metadata` must assert that generated metadata files contain all required keys (`algo_name`, `algo_version`, `gap_config`).
- [X] T024 [US2] Add convergence failure handling: log failure, record gap config, exclude from analysis (FR-008). **MUST log every exclusion to `data/results/excluded_realizations.log` and validate that the count of valid realizations remains ≥ 40 of 50 for corrupted file scenarios, or ≥ 30 for general failures.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Estimate Cosmological Parameters and Quantify Bias (Priority: P3)

**Goal**: Estimate cosmological parameters from recovered power spectra and compute bias magnitude relative to ground-truth values.

**Independent Test**: Compare recovered parameters against ground-truth; verify bias calculation and statistical significance (p < 0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test in `tests/contract/test_analysis_schema.py`: Function `test_validate_parameter_posterior` must assert `ParameterPosterior` schema includes `median`, `ci_68`, `ci_95`, `ground_truth`.
- [X] T026 [P] [US3] Integration test in `tests/integration/test_bias_pipeline.py`: Function `test_full_bias_pipeline` must assert that running the full pipeline produces `data/results/bias_summary.csv` with valid rows.

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/analysis/mode_coupling.py` to calculate the Mode-Coupling (Leakage) Matrix from the gap mask (FR-009). Output to `data/derived/leakage_matrix_{realization_id}.npy`. **This is the sole implementation path selected to satisfy the 'custom likelihood correction OR mode-coupling matrix adjustment' requirement of FR-009. Depends on T012/T014 (Mask Generation) for the specific realization mask.**
- [X] T028d-pre [US3] **Pre-flight**: Generate and verify the pre-computed likelihood grid (fallback for T028b) using CAMB/CosmoMC on a representative subset. Store in `data/derived/likelihood_grid.pkl`. **MUST verify grid existence and integrity (checksum) before the main analysis run begins.** If grid generation fails, the pipeline MUST halt with a clear error. **This task resolves the single point of failure identified in the analysis report.**
- [X] T028a [US3] Implement `code/analysis/parameter_est.py` Step 1: Load leakage matrix from T027.
- [X] T028b [US3] Implement `code/analysis/parameter_est.py` Step 2: Apply leakage matrix to theoretical spectrum to correct the input, then estimate parameters (H₀, Ωₘ, nₛ, τ) using **Fisher Matrix Approximation (on-the-fly)**. **MUST include a fallback mechanism:** If the on-the-fly Fisher Matrix fails to converge, switch to using the pre-computed likelihood grid (generated in T028d-pre). If the grid is missing or also fails, exclude the realization and log the specific error. Record ground-truth vs. recovered. **Depends on T028d-pre.**
- [X] T028d-post [US3] Implement CosmoMC spot-checking for ≤ 5 realizations as required by FR-004. Run full MCMC on a subset of realizations to verify Fisher Matrix results. Store results in `data/results/cosmomc_spot_check.json`. **Depends on T028b.**
- [X] T029a [US3] Implement `code/analysis/bias_analysis.py` Step 1: Calculate `bias_magnitude` = |recovered - ground_truth|. Output to `data/results/bias_summary.csv`.
- [X] T029b [US3] Implement Linear Regression (FR-005) to fit bias vs. gap characteristics (Fraction × Algorithm × Morphology with interaction terms). **MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) and save the CORRECTED regression results to `data/results/regression_results.csv`. Depends on T029a AND T014b (Null Model Data) for baseline comparison.**
- [X] T029c-TEST [P] [US3] Contract test in `tests/contract/test_correction_schema.py`: Function `test_validate_corrected_pvalues` must assert that `data/results/corrected_p_values.csv` exists and contains valid statistical adjustments.
- [X] T030 [US3] Implement sensitivity analysis sweep (α ∈ {low, 0.05, 0.1} and tolerance ∈ {low, moderate, high}) and store results in `data/results/sensitivity_sweep.json` with fields: `alpha`, `tolerance`, `bias_variance`, `significance_change`. **MUST record the variance in bias rates AND the change in statistical significance across the sweep.**
- [X] T031 [US3] Implement comparison of observed bias trends against the **Null Model** baseline (from T014b, Data Ready) to ensure independence. **MUST perform an F-test to compare the variance of the Null Model bias distribution against the Gap-Filled bias distribution. FAIL if Null Model variance is significantly higher (p < 0.05).** **Depends on T029b (Regression Results) AND T014b (Null Model Data).**
- [X] T032 [US3] Implement final aggregation logic to ensure minimum 30 valid realizations are retained. **MUST** count valid realizations from `data/results/excluded_realizations.log` **AFTER** regression fitting (T029b). **MUST** raise a custom `StatisticalPowerError` with the message "Insufficient valid realizations: {count} < 30 required" and halt the pipeline if count < 30. **For corrupted file edge cases, enforce minimum 40 of 50.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `quickstart.md` with environment setup and pilot run instructions.
- [X] T036 Code cleanup and refactoring of `code/pipeline/run_analysis.py` to use a generator pattern for memory safety, ensuring peak RAM < 7GB.
- [X] T037 [P] Performance optimization: ensure float32 usage where precision allows to fit within 7GB RAM. **MUST run a memory benchmark and log results to `data/results/memory_benchmark.log`. PASS/FAIL**: The benchmark MUST log 'PASS' only if peak RAM < 7GB; otherwise, it MUST raise an error and halt the pipeline.
- [X] T038 [P] Additional unit tests for `mode_coupling.py` and `parameter_est.py` in `tests/unit/`.
- [X] T039 Run full pipeline on a small subset to verify memory and time constraints (Task 3.2).
- [X] T040 Run `quickstart.md` validation to ensure reproducibility.

---

## Phase 7: Verification & Final Validation

**Goal**: Ensure all reviewer concerns regarding data integrity, statistical rigor, and execution safety are resolved before final run.

- [X] T041 [US3] Implement `code/analysis/robustness_checks.py` to explicitly validate that the Fisher Matrix Hessian is positive-definite before inversion; **MUST** raise an error and exclude the realization if non-positive, logging the specific eigenvalue failure to `data/results/robustness_failures.log**. This check is ACTIVE and mandatory.**
- [X] T043 [US2] Implement a "NaN Propagation" guard in `code/gap_filling/*.py` that scans the output map immediately after gap-filling; if any NaNs are detected, the task MUST raise an exception and trigger the exclusion logic in T024**. This check is ACTIVE and mandatory.**
- [X] T044 [US1] Add a "Ground Truth Integrity" check in `code/simulation/generate_maps.py` that verifies the generated CMB map power spectrum matches the theoretical CAMB spectrum within 1% before saving the map; if mismatch > 1%, **FAIL** the generation task.
- [X] T045 [US3] Implement a "Bias Floor" validation in `code/analysis/bias_analysis.py` that compares the calculated bias against the statistical noise floor (sqrt(N) scaling); if bias < noise floor, flag the result as "Indistinguishable from Noise" in `data/results/bias_summary.csv`. This check is ACTIVE and mandatory.
- [X] T046 [US3] Create `data/results/final_validation_report.md` that aggregates all exclusion logs, budget reduction logs, and robustness failure logs to confirm the final dataset meets the "Minimum 30 Valid Realizations" requirement with full transparency.

---

## Phase 8: Final Integration & Execution Safety (RESOLVED)

**Goal**: Address critical execution safety concerns regarding data flow ordering, budget calculation dependencies, and final aggregation logic.
*Note: Tasks T047-T050 from the previous iteration have been merged into their respective implementation tasks (T034, T033, T032, T031) and are marked resolved below.*

- [X] T047 [US1/US2] **Data Flow Ordering**: Logic implemented in T034 (Pipeline Orchestrator) to enforce sequential execution per realization ID. **RESOLVED**.
- [X] T048 [Foundational] **Budget Calculation Dependency**: Logic merged into T033 to accept dynamic arguments. **RESOLVED**.
- [X] T049 [US3] **Aggregation Logic**: Logic merged into T032 to perform check after regression. **RESOLVED**.
- [X] T050 [US3] **Null Model Validation**: Logic merged into T031 to include F-test variance comparison. **RESOLVED**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 7)**: Depends on completion of all User Stories and Polish tasks
- **Final Integration (Phase 8)**: RESOLVED - logic merged into earlier phases

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

### Specific Task Dependencies (Phase 5, 7 & 8)

- **T027 (Mode-Coupling)**: Depends on T012/T014 (Mask Generation).
- **T028d-pre (Grid Generation)**: Independent, but MUST complete before T028b.
- **T028a (Load Leakage)**: Depends on T027.
- **T028b (Parameter Est)**: Depends on T028a AND T028d-pre.
- **T028d-post (CosmoMC Spot-check)**: Independent, but must be ready before T028b.
- **T028c (CosmoMC Spot-check)**: Depends on T028b.
- **T029a (Bias Calc)**: Depends on T028b.
- **T029b (Regression)**: Depends on T029a AND T014b (Null Model Data).
- **T029c-TEST (Correction Test)**: Depends on T029b.
- **T031 (Null Model)**: Depends on T029b (Regression Results) AND T014b (Null Model Data).
- **T030 (Sensitivity)**: Depends on T029b.
- **T032 (Aggregation)**: Depends on T030 AND T029b.
- **T033 (Budget Check)**: Depends on T007 (Pilot) AND T012a (Gap Fractions Config). **DOES NOT depend on T011.**
- **T034 (Integration)**: Depends on T033 and T007. **DOES NOT depend on T011.**
- **T041 (Robustness)**: Depends on T028b (Parameter Est).
- **T043 (NaN Guard)**: Depends on T019, T020, T021 (Gap Filling).
- **T044 (Ground Truth)**: Depends on T011 (Simulation).
- **T045 (Bias Floor)**: Depends on T029a (Bias Calc).
- **T046 (Final Report)**: Depends on T024, T032, T041, T043, T044, T045.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Phase 8 tasks (T047-T050) have been resolved by merging their requirements into T034, T033, T032, and T031 respectively.**
- **T028d-pre ensures the pre-computed grid fallback is generated and verified before the main loop, resolving the single point of failure.**
- **T032 explicitly defines the `StatisticalPowerError` mechanism, resolving the executability concern.**