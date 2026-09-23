# Tasks: Statistical Properties of Simulated Black Hole Mergers

**Input**: Design documents from `/specs/001-statistical-properties-black-hole-mergers/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure, including core utilities required for data integrity and logging.

- [ ] T001 [P] Initialize Project Directory Structure. **Content**: Create `src/`, `tests/`, `data/raw/`, `data/processed/`, `output/results/`, `output/figures/`, `logs/`, `src/data/`, `src/analysis/`, `src/viz/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`. **Verification**: Run `test -d src` AND `test -d tests` AND `test -d data/raw` AND `test -d data/processed` AND `test -d output/results` AND `test -d output/figures` AND `test -d logs` AND `test -d src/data` AND `test -d src/analysis` AND `test -d src/viz` AND `test -d src/utils` AND `test -d tests/unit` AND `test -d tests/integration` AND `test -d tests/contract`.
- [X] T002 [P] Create `requirements.txt` with pinned versions (numpy, scipy, pandas, matplotlib, requests, tqdm, pytest, h5py, statsmodels).
- [X] T003 [P] Initialize Python virtual environment and install dependencies. **Verification**: Run `python -m venv.venv` and `source.venv/bin/activate`. Run `pip list` and verify all packages from `requirements.txt` are installed. Verify `.venv/bin/python --version` returns a compatible Python 3.x version.
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools. **Verification**: Run `ruff check.` and `black --check.` and verify they return exit code 0 (or show expected linting errors if code is not yet written). Verify `ruff` and `black` are in `.venv/bin/`.
- [X] T005 [P] Implement `src/utils/checksum.py` for SHA256 integrity verification of downloaded files. **Output**: A function `verify_file(path: str, expected_hash: str) -> bool`.
- [ ] T006 [P] Implement `src/utils/logger.py` with structured logging and log levels. **Output**: A configured logger that writes to `stdout` and `logs/pipeline.log`.
- [ ] T047 [US0] Configure `.github/workflows/ci.yml`. **Content**: Must include `runs-on: ubuntu-latest`, `timeout-minutes: 360` (6 hours), and a step running `pytest` (e.g., `python -m pytest tests/ -v`). **Dependency**: Runs after T003. **Verification**: Run `cat.github/workflows/ci.yml` and verify the presence of `runs-on`, `timeout-minutes`, and `pytest` command.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes selection bias handling and main pipeline entry.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Create `src/config.py` defining paths, random seeds, and `alpha_thresholds` defaults. The configuration MUST define `alpha_thresholds` as a list of significance levels that is **overridable via CLI arguments or environment variables**.
- [ ] T008 [P] Implement `src/data/schemas.py` with Pydantic models for GWTC_Catalog, Simulation_Dataset, Statistical_Test_Result.
- [ ] T009 [P] Setup `tests/contract/test_schemas.py` to validate JSON/CSV data against defined schemas.
- [ ] T010 [P] Implement `src/main.py` as the pipeline entry point with argument parsing, orchestration logic, and integrated resource monitoring hooks. The pipeline MUST log peak memory/disk usage. If thresholds (time, RAM, Disk) are exceeded, the pipeline MUST log a `[RESOURCE_BREACH]` message with the specific metric and value, then **exit with code 1** to signal failure, ensuring hard constraints (FR-011) are enforced. **Dependency**: Requires T005, T006. (Note: T032 is now in Phase 5 and handled within the orchestration flow after data is loaded).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess GWTC Catalogs (Priority: P1) 🎯 MVP

**Goal**: Acquire observational data (GWTC-1/2) and prepare it for statistical comparison.

**Independent Test**: Verify `data/processed/obs_catalog.csv` exists with ≥100 valid events and correct checksums. [UNRESOLVED-CLAIM: c_3e601a42 — status=not_enough_info]

### Tests for User Story 1

- [ ] T011 [P] [US1] Unit test for checksum verification in `tests/unit/test_checksum.py`.
- [ ] T012 [P] [US1] Unit test for NaN filtering logic in `tests/unit/test_preprocess.py`.
- [ ] T013 [P] [US1] Integration test for download retry logic (simulate 404) in `tests/integration/test_download.py`.

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/data/download.py` function to fetch GWTC-1 (DOI) AND GWTC-2 (DOI 10.5281/zenodo.3966974) with unified retry/backoff logic. **Verification**: Downloaded files must exist in `data/raw/` with valid checksums. [UNRESOLVED-CLAIM: c_6a10bfcb — status=not_enough_info]
- [ ] T015 [US1] Implement `src/data/preprocess.py` to parse posterior samples, extract mass_ratio, effective_spin, component_mass, and filter NaNs.
- [ ] T016 [US1] Implement validation in `src/data/preprocess.py` to ensure ≥100 valid events remain; fail with explicit error if not.
- [ ] T017 [US1] Implement **Event-Level Bootstrapping** in `src/data/preprocess.py` to create the primary observational artifact. **Specific Mechanism**: For each bootstrap iteration (N=1000), sample a **new median** for **every single event** from its respective posterior distribution.
 1. **Output A**: Save the aggregated summary to `data/processed/obs_catalog.csv` with columns: `event_id`, `mass_ratio_median`, `mass_ratio_std`, `effective_spin_median`, `effective_spin_std`, `component_mass_1_median`, `component_mass_1_std`, `component_mass_2_median`, `component_mass_2_std`.
 2. **Output B (CRITICAL)**: Save the full bootstrapped dataset to `data/processed/bootstrapped_obs_samples.h5` (HDF5 format) containing the array of sampled medians for every event and every iteration. This file is required for T028 and T029 to perform the KS test on the distribution, satisfying FR-014 and the i.i.d. assumption handling.
 **Constraint**: MUST implement chunked writing/streaming to ensure memory usage stays within acceptable limits and disk usage under 20GB. **Verification**: Run `du -sh data/processed/bootstrapped_obs_samples.h5` to confirm size < 20GB. **AND** Run a Python snippet: `import h5py; f=h5py.File('data/processed/bootstrapped_obs_samples.h5','r'); assert f['data'].shape[0] >= 100 and f['data'].shape[1] == 1000; assert f['data'].dtype.kind in 'fc'; f.close()`. **Dependency**: Requires T014, T015, T016.

**Checkpoint**: User Story 1 complete - observational data is downloaded, validated, and preprocessed.

---

## Phase 4: User Story 1b - Download/Generate Simulation Population (Priority: P1) 🎯 MVP

**Goal**: Acquire or generate a simulation dataset with matching schema (mass_ratio, effective_spin).

**Independent Test**: Verify `data/processed/sim_catalog.csv` exists with ≥100 valid events and matching schema. [UNRESOLVED-CLAIM: c_dc6c4f6c — status=not_enough_info]

### Tests for User Story 1b

- [ ] T018 [P] [US1b] Unit test for synthetic data generation distribution (power-law) in `tests/unit/test_synthetic_gen.py`.
- [ ] T019 [P] [US1b] Unit test for schema validation of simulation data in `tests/unit/test_schemas.py`.

### Implementation for User Story 1b

- [ ] T020 [P] [US1b] Implement `src/data/download.py` function to attempt fetching a dedicated BBH population synthesis catalog (e.g., from Zenodo/Community Repo).
- [ ] T021 [US1b] Implement fallback logic in `src/data/download.py` to generate synthetic catalog if external source fails.
- [ ] T022 [US1b] Implement `src/data/generate_synthetic.py` to create a catalog based on a "Power-law mass with independent spin" hypothesis. **Citation**: Must cite "Abbott et al. (), ApJL, 913, L7 " (or similar LVC population paper). **Parameters**: **Output**: `data/processed/sim_catalog.csv` with ≥100 events.
- [ ] T023 [US1b] Ensure synthetic generator produces ≥100 events with `mass_ratio`, `effective_spin`, `component_mass_1`, `component_mass_2`.
- [ ] T024 [US1b] Add validation in `src/data/preprocess.py` to confirm simulation data schema matches observational data schema.

**Checkpoint**: User Story 1b complete - simulation data is available and schema-matched.

---

## Phase 5: User Story 2 - Statistical Analysis (KS Tests & Corrections) (Priority: P2)

**Goal**: Perform Kolmogorov-Smirnov tests with Bonferroni correction and sensitivity analysis.

**Independent Test**: Verify `output/results/ks_test_results.json` contains statistics, p-values, and corrected flags.

### Tests for User Story 2

- [ ] T025 [P] [US2] Unit test for KDE bandwidth selection (Scott's rule) in `tests/unit/test_kde.py`.
- [ ] T026 [P] [US2] Unit test for Bonferroni correction logic in `tests/unit/test_ks_test.py`.
- [ ] T027 [P] [US2] Unit test for sensitivity analysis sweep logic in `tests/unit/test_sensitivity.py`.

### Implementation for User Story 2

- [ ] T032 [US2] Implement selection bias handling in `src/analysis/selection_bias.py` (FR-016): Attempt to load official LVK selection efficiency files (if available in `data/raw/`).
 - **If files exist**: Apply Inverse Probability Weighting (IPW) and record the method used in `data/results/selection_bias_status.json`.
 - **If files are missing**: **HALT EXECUTION**. Log a critical `[SELECTION_BIAS_MISSING]` error with the message "Cannot proceed without selection bias correction data (FR-016). Pipeline terminated." The pipeline MUST NOT generate results or proceed to T028/T029.
 **Verification**: Run `python -c "import json; d=json.load(open('data/results/selection_bias_status.json')); assert d['method'] == 'ipw'; print(d['method'])"` (only if files exist). **Dependency**: Requires `data/processed/bootstrapped_obs_samples.h5` (from T017) to calculate weights. **Execution Order**: MUST run BEFORE T028 and T029.
- [ ] T028 [US2] Implement `src/analysis/kde.py` to compute 1D KDEs for mass_ratio and effective_spin using scipy.stats.gaussian_kde. **Dependency**: Requires `data/processed/bootstrapped_obs_samples.h5` (from T017) AND `data/results/selection_bias_status.json` (from T032) to ensure weights are applied. **3D Structure Handling**: Iterate over the 'Iteration' axis (shape [Events, Iterations, Parameters]) of the HDF5 file. For each iteration `j`, sample one median per event from the `j-th` slice, compute the KDE, and aggregate the results across all iterations.
- [ ] T029 [US2] Implement `src/analysis/ks_test.py` to perform **Weighted** KS tests on mass_ratio and effective_spin distributions using the weights from T032. **Dependency**: Requires `data/processed/bootstrapped_obs_samples.h5` (from T017) and `data/results/selection_bias_status.json` (from T032). **3D Structure Handling**: Iterate over the 'Iteration' axis (shape [Events, Iterations, Parameters]) of the HDF5 file. For each iteration `j`, sample one median per event from the `j-th` slice, compute the KS statistic with weights, and aggregate the resulting KS statistics to form the final distribution. **Bonferroni Correction**: Apply Bonferroni correction for multiple comparisons (multiple tests) as a sub-step of this task.
- [ ] T031 [US2] Implement `src/analysis/sensitivity.py` to sweep α over a **dynamic range** (e.g., 0.01 to 0.10 in steps of 0.01) and flag "borderline" results (FR-009). **Artifact Generation**: This task MUST generate `data/results/sensitivity_report.json` containing the p-values and significance flags for each α in the sweep set. **Dependency**: Requires T029 (KS Test) to be complete.
- [ ] T033 [US2] Generate `output/results/ks_test_results.json` with all statistics, adjusted p-values, and significance flags. **Dependency**: Requires T031 (Sensitivity Results) and T029 (KS Test) to ensure borderline flags are applied before finalizing the report.

**Checkpoint**: User Story 2 complete - statistical comparisons are performed and corrected.

---

## Phase 6: User Story 2b & 2c - Power Analysis & Limitations (Priority: P2)

**Goal**: Assess statistical power, calculate MDES, and log limitations.

**Independent Test**: Verify `data/results/power_analysis.json` and limitations section in final report.

### Tests for User Story 2b/2c

- [ ] T034 [P] [US2c] Unit test for MDES calculation logic in `tests/unit/test_power.py`.
- [ ] T035 [P] [US2c] Unit test for power limitation detection logic in `tests/unit/test_power.py`.

### Implementation for User Story 2b/2c

- [ ] T036 [US2c] Implement `src/analysis/power.py` to calculate Minimum Detectable Effect Size (MDES) (FR-010, FR-015). **Method**: Prefer an analytical calculation based on sample sizes and standard deviations. If analytical methods are insufficient, a simulation-based (bootstrapping) approach is allowed **only if** it completes within the CPU time budget. **Dependency**: This task MUST consume `output/results/ks_test_results.json` (from T033) and `data/results/sensitivity_report.json` (from T031) as inputs.
- [ ] T037 [US2c] Implement logic in `src/analysis/power.py` to detect if simulation sample size < 50% of observational size.
- [ ] T038 [US2c] Generate `data/results/power_analysis.json` containing MDES values (explicitly named "minimum_detectable_effect_size"), sample size ratios, and power estimates. **Path Correction**: Matches `plan.md` T021.
- [ ] T039 [US2c] Update report generation to include "Limitations" section with power notes, MDES interpretation (FR-010, SC-011), and explicit notes on any selection bias limitations (from T032).

**Checkpoint**: User Story 2b/2c complete - power and limitations are quantified.

---

## Phase 7: User Story 3 - Visualization & Reporting (Priority: P3)

**Goal**: Generate plots and final report with divergence annotations.

**Independent Test**: Verify `output/figures/` contains ≥2 PNGs (300 DPI) with annotated divergence regions. [UNRESOLVED-CLAIM: c_fa3fdc55 — status=not_enough_info]

### Tests for User Story 3

- [ ] T040 [P] [US3] Unit test for plot generation and DPI settings in `tests/unit/test_plots.py`.
- [ ] T041 [P] [US3] Integration test for full report generation in `tests/integration/test_report.py`.

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement `src/viz/plots.py` to create 1D KDE plots for mass_ratio and effective_spin (overlaid distributions).
- [ ] T043 [US3] Implement annotation logic in `src/viz/plots.py` to highlight regions where p < 0.05 as statistically significant (FR-008).
- [ ] T044 [US3] Implement `src/viz/report.py` to assemble final markdown/JSON report including KS results, power analysis, sensitivity sweep (consuming `sensitivity_report.json` from T031), and "Borderline" warnings (FR-009).
- [ ] T045 [US3] Ensure all figures saved as PNG with resolution **≥300 DPI** (explicitly set `dpi=300` in matplotlib). **Verification**: Check file properties of generated PNGs using `stat` or `identify` (ImageMagick) to confirm DPI.

**Checkpoint**: User Story 3 complete - visualizations and reports are generated.

---

## Phase 8: Future Data Projection & Review Response (Priority: P2)

**Goal**: Address Freeman-Dyson-simulated review concern regarding the "gap between theory and nature" and the "slow takeoff" of statistical significance with future data volumes.

**Independent Test**: Verify `output/reports/slow_takeoff_projection.md` exists and contains a quantitative projection of required sample sizes to distinguish formation channels.

### Implementation for Review Response

- [ ] T046 [P] [US2c] Acquire Future Detector Sensitivity Data. **Content**: Download or define the "projected rates for 3rd generation detectors" (e.,g., LIGO A+, Cosmic Explorer, Einstein Telescope) and "LIGO A+ sensitivity curves". **Source**: Use verified sources such as the "LIGO Scientific Collaboration" public data releases or the "Einstein Telescope Design Document". **Output**: Save to `data/raw/future_detector_projections.yaml`. **Dependency**: None (Independent data acquisition).
- [ ] T050 [FR-017] [US2c] Implement `src/analysis/slow_takeoff.py` to perform a **Future-Data Projection** analysis.
 1. **Input**: Current sample sizes (N_obs, N_sim) and the observed effect sizes (differences in distribution moments or KS statistics) from T033. **Future Data**: Load `data/raw/future_detector_projections.yaml` from T046.
 2. **Mechanism**: Use the **power analysis** results from T036 (specifically the MDES) to extrapolate the number of events required to achieve statistical power for detecting the *observed* effect size (or a specific theoretical divergence) if the current trend holds.
 3. **Method**: Calculate the "Event Count to Significance" for a range of future detector sensitivities (e.g., LIGO A+, Cosmic Explorer, Einstein Telescope) assuming standard merger rate evolution models.
 4. **Output**: Generate `output/reports/slow_takeoff_projection.md` containing:
 - A table of "Events Required" to distinguish between the current null hypothesis and the observed alternative at a standard confidence level.
 - A qualitative assessment of whether the current catalog is in a "pre-significance" regime (where distributions look similar) or a "divergence" regime.
 - A "Back-of-the-Envelope" estimate of the timeline (years) to reach this event count based on current detector run rates (O4, O5) and projected rates for 3rd generation detectors.
 5. **Citation**: Must reference LVC O run rates and projected rates for 3rd generation detectors (e.,g., "Abbott et al. 2021, ApJL, 913, L7 " or "Sathyaprakash et al. 2019 ").
 **Dependency**: Requires T036 (Power Analysis), T033 (KS Results), and T046 (Future Data) to be complete.

- [ ] T051 [FR-017] [US3] Update the main final report generator (`src/viz/report.py`) to include a dedicated section "Future Outlook: The Slow Takeoff of Significance" that summarizes the findings from T050.
 **Dependency**: Requires T050 to be complete.

**Checkpoint**: Review response complete - project now addresses the "gap between theory and nature" and future scalability.

---

## Phase 9: User Story 0 - CI/CD Constraints & Performance (Priority: P0)

**Goal**: Ensure pipeline runs within GitHub Actions free-tier limits (pipeline runs within GitHub Actions free-tier limits (≤6h, ≤7GB RAM, ≤20GB Disk).).

**Independent Test**: Run pipeline in CI environment and verify resource usage logs.

### Implementation for User Story 0

- [ ] T048 [P] [US0] Optimize data loading in `src/data/preprocess.py` to stream/process in chunks if necessary (avoid loading full posterior samples into RAM).
- [ ] T049 [P] [US0] Add pre-commit hook to check for large file uploads or inefficient imports.

**Checkpoint**: User Story 0 complete - pipeline is optimized for CI constraints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)** and **US1b (P1)** can run in parallel once Foundational is done.
 - **US2 (P2)** depends on US1 and US1b (data must be ready).
 - **US2b/2c (P2)** depends on US2 (results must be ready).
 - **US3 (P3)** depends on US2 and US2b/2c (results and power analysis must be ready).
 - **US0 (P0)** is cross-cutting but must be validated before final CI run.
 - **Phase 8 (Review Response)**: Depends on US2 and US2b/2c (requires power analysis and KS results to project future significance) AND T046 (Future Data).
 - **Phase 9 (CI/CD)**: Cross-cutting.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Download/Preprocess before Analysis.
- Analysis before Visualization.
- Core implementation before integration.

### Parallel Opportunities

- **Phase 1, 2, 9**: All setup tasks can run in parallel (except T047 which depends on T003).
- **Phase 3 & 4**: US1 (Observational) and US1b (Simulation) can be developed in parallel.
- **Phase 5, 6, 7**: Once data is ready, KDE, KS, Power, and Viz modules can be developed in parallel (if data dependencies are mocked or data is ready).

---

## Notes

- [P] tasks = different files, no dependencies (relative to each other within the phase)
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **Critical Constraint**: All code must run on CPU-only, -core, limited RAM. No GPU, no large model loading.
- **Data Integrity**: All downloads must have checksum verification. No fake data allowed.
- **Scope Boundary**: This project is strictly limited to comparing existing GWTC data against the single synthetic baseline defined in US-1b and US-2. No additional Monte Carlo extrapolations or "Slow Takeoff" analyses are included **except** for the specific projection analysis in Phase 8 which addresses the reviewer's request for a "back-of-the-envelope" estimate of future data needs (FR-017).
- **Limitations**: The report must explicitly state any limitations regarding selection bias (if LVK files were missing - which is now handled by halting execution per T032) and sample size power, as generated in T039.
- **Selection Bias**: Per FR-016, if LVK selection files are missing, the pipeline MUST halt with a critical error (T032), ensuring the 'Limitations' section (T039) can be generated with the correct error context.
- **Reviewer Response**: The "Slow Takeoff" analysis (T050) is a direct response to the Freeman-Dyson-simulated review, addressing the concern that current catalogs may be insufficient to claim knowledge of the cosmic population shape.