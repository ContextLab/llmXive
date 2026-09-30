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

- [ ] T001 [P] Initialize Project Directory Structure. **Content**: Create `src/`, `tests/`, `data/raw/`, `data/processed/`, `output/results/`, `output/figures/`, `logs/`, `src/data/`, `src/analysis/`, `src/viz/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`. **Verification**: Generate `project_structure_manifest.json` containing a JSON object with keys for each directory and a list of its subdirectories. **Artifact**: `project_structure_manifest.json`.
- [X] T002 [P] Create `requirements.txt` with pinned versions (numpy, scipy, pandas, matplotlib, requests, tqdm, pytest, h5py, statsmodels).
- [X] T003 [P] Initialize Python virtual environment and install dependencies. **Verification**: Run `python -m venv.venv` and `source.venv/bin/activate`. Run `pip list` and verify all packages from `requirements.txt` are installed. Verify `.venv/bin/python --version` returns a compatible Python 3.x version.
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools. **Verification**: Run `ruff check.` and `black --check.` and verify they return exit code 0 (or show expected linting errors if code is not yet written). Verify `ruff` and `black` are in `.venv/bin/`.
- [X] T005 [P] Implement `src/utils/checksum.py` for SHA256 integrity verification of downloaded files. **Output**: A function `verify_file(path: str, expected_hash: str) -> bool`.
- [ ] T006 [P] Implement `src/utils/logger.py` with structured logging and log levels. **Output**: A configured logger that writes to `stdout` and `logs/pipeline.log`.
- [ ] T047 [US0] Configure `.github/workflows/ci.yml`. **Content**: Must include `runs-on: ubuntu-latest`, `timeout-minutes: 360` (6 hours), and a step running `pytest` (e.g., `python -m pytest tests/ -v`). **Dependency**: Runs after T001. **Verification**: Run `cat.github/workflows/ci.yml` and verify the presence of `runs-on`, `timeout-minutes`, and `pytest` command.
- [ ] T048 [P] [US0] Optimize data loading in `src/data/preprocess.py` to stream/process in chunks if necessary (avoid loading full posterior samples into RAM). **Dependency**: None (Setup task).
- [ ] T049 [P] [US0] Add pre-commit hook to check for large file uploads or inefficient imports. **Dependency**: None (Setup task).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes selection bias handling and main pipeline entry.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Create `src/config.py` defining paths, random seeds, and `alpha_thresholds` defaults. The configuration MUST define `alpha_thresholds` as a list of significance levels that is **overridable via CLI arguments or environment variables**.
- [ ] T008 [P] Implement `src/data/schemas.py` with Pydantic models for GWTC_Catalog, Simulation_Dataset, Statistical_Test_Result.
- [ ] T009 [P] Setup `tests/contract/test_schemas.py` to validate JSON/CSV data against defined schemas.
- [ ] T032 [P] [US2] Implement selection bias handling in `src/analysis/selection_bias.py` (FR-016): Attempt to load official LVK selection efficiency files from `data/raw/lvk_selection_efficiency.h5` (GWTC-1) and `data/raw/lvk_selection_efficiency_GWTC2.h5` (GWTC-2).
 - **If files exist**: Apply Inverse Probability Weighting (IPW) and record the method used as `ipw` in `data/results/selection_bias_status.json`.
 - **If files are missing**: **DO NOT HALT**. Log a warning `[SELECTION_BIAS_MISSING]`, proceed with **uniform weighting**, and record the method as `uniform_approximation` in `data/results/selection_bias_status.json`. The pipeline MUST continue to T028/T029. **CRITICAL**: This fallback MUST trigger a log entry explicitly classified as a 'Limitation' to preserve the mandatory nature of FR-016.
 **Verification**: Run `python -c "import json; d=json.load(open('data/results/selection_bias_status.json')); assert d['method'] in ['ipw', 'uniform_approximation']; print(d['method'])"`. **Dependency**: Requires `data/processed/bootstrapped_obs_samples.h5` (from T017) to calculate weights. **Execution Order**: MUST run BEFORE T028 and T029.
- [ ] T010 [P] Implement `src/main.py` as the pipeline entry point with argument parsing, orchestration logic, and integrated resource monitoring hooks. The pipeline MUST log peak memory/disk usage. [UNRESOLVED-CLAIM: c_b5aaf415 — status=not_enough_info] If thresholds (time, RAM, Disk) are exceeded, the pipeline MUST log a `[RESOURCE_BREACH]` message with the specific metric and value, then **exit with code 1** to signal failure, ensuring hard constraints (FR-011) are enforced. **Dependency**: Requires T005, T006, T032. (Note: T032 is now in Phase 2 and handled within the orchestration flow after data is loaded).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess GWTC Catalogs (Priority: P1) 🎯 MVP

**Goal**: Acquire observational data (GWTC-1/2) and prepare it for statistical comparison.

**Independent Test**: Verify `data/processed/obs_catalog.csv` exists with ≥100 valid events and correct checksums.

### Tests for User Story 1

- [ ] T011 [P] [US1] Unit test for checksum verification in `tests/unit/test_checksum.py`.
- [ ] T012 [P] [US1] Unit test for NaN filtering logic in `tests/unit/test_preprocess.py`.
- [ ] T013 [P] [US1] Integration test for download retry logic (simulate 404) in `tests/integration/test_download.py`.

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/data/download.py` function to fetch GWTC-1 (DOI) AND GWTC-2 (DOI 10.5281/zenodo.3966974) with unified retry/backoff logic. **Verification**: Downloaded files must exist in `data/raw/` with valid checksums.
- [ ] T015 [US1] Implement `src/data/preprocess.py` to parse posterior samples, extract mass_ratio, effective_spin, component_mass, and filter NaNs.
- [ ] T016 [US1] Implement validation in `src/data/preprocess.py` to ensure ≥100 valid events remain; fail with explicit error if not.
- [ ] T017 [US1] Implement **Event-Level Bootstrapping** in `src/data/preprocess.py` to create the primary observational artifact. **Specific Mechanism**:
 1. **Algorithm**: Iterate over events in **batches of 100**. For each batch:
 a. For each event in the batch, sample 1000 medians from its respective posterior distribution. [UNRESOLVED-CLAIM: c_4a957a82 — status=not_enough_info]
 b. Stack these samples into a temporary 3D array segment of shape `[100, 1000, 4]`.
 c. Append this segment to the HDF5 file `data/processed/bootstrapped_obs_samples.h5` using chunked writing.
 2. **Output A**: Save the aggregated summary to `data/processed/obs_catalog.csv` with columns: `event_id`, `mass_ratio_median`, `mass_ratio_std`, `effective_spin_median`, `effective_spin_std`, `component_mass_1_median`, `component_mass_1_std`, `component_mass_2_median`, `component_mass_2_std`.
 3. **Output B (CRITICAL)**: Save the full bootstrapped dataset to `data/processed/bootstrapped_obs_samples.h5` (HDF5 format). **Schema**: The file MUST contain a dataset named `samples` with shape `[N_events, 1000, 4]` (Events, Iterations, Parameters: mass_ratio, effective_spin, m1, m2) and dtype float64.
 **Constraint**: MUST implement chunked writing/streaming (batches of 100) to ensure memory usage stays within acceptable limits and disk usage under 20GB. **Verification**: Run `du -sh data/processed/bootstrapped_obs_samples.h5` to confirm size < 20GB. **AND** Run a Python snippet: `import h5py; f=h5py.File('data/processed/bootstrapped_obs_samples.h5','r'); assert f['samples'].shape[0] >= 100 and f['samples'].shape[1] == 1000 and f['samples'].shape[2] == 4 [UNRESOLVED-CLAIM: c_84a7a305 — status=not_enough_info]; assert f['samples'].dtype == 'float64'; f.close()`. **Dependency**: Requires T014, T015, T016.

**Checkpoint**: User Story 1 complete - observational data is downloaded, validated, and preprocessed.

---

## Phase 4: User Story 1b - Download/Generate Simulation Population (Priority: P1) 🎯 MVP

**Goal**: Acquire or generate a simulation dataset with matching schema (mass_ratio, effective_spin).

**Independent Test**: Verify `data/processed/sim_catalog.csv` exists with ≥100 valid events and matching schema.

### Tests for User Story 1b

- [ ] T018 [P] [US1b] Unit test for synthetic data generation distribution (power-law) in `tests/unit/test_synthetic_gen.py`.
- [ ] T019 [P] [US1b] Unit test for schema validation of simulation data in `tests/unit/test_schemas.py`.

### Implementation for User Story 1b

- [ ] T020 [P] [US1b] Implement `src/data/download.py` function to attempt fetching a dedicated BBH population synthesis catalog (e.g., from Zenodo/Community Repo).
- [ ] T021 [US1b] Implement fallback logic in `src/data/download.py` to generate synthetic catalog if external source fails.
- [ ] T022 [US1b] Implement `src/data/generate_synthetic.py` to create a catalog based on a "Power-law mass with independent spin" hypothesis. **Citation**: Must cite "Abbott et al. (), ApJL, L7 " (or similar LVC population paper). **Parameters**: **Output**: `data/processed/sim_catalog.csv` with ≥100 events.
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

- [ ] T028 [US2] Implement `src/analysis/kde.py` to compute 1D KDEs for mass_ratio and effective_spin using scipy.stats.gaussian_kde. **Dependency**: Requires `data/processed/bootstrapped_obs_samples.h5` (from T017) AND `data/results/selection_bias_status.json` (from T032) to ensure weights are applied. **3D Structure Handling**: Iterate over the 'Iteration' axis (shape [Events, Iterations, Parameters]) of the HDF5 file. For each iteration `j`, sample one median per event from the `j-th` slice, compute the KDE, and aggregate the results across all iterations.
- [ ] T029 [US2] Implement `src/analysis/ks_test.py` to perform **Weighted** KS tests on mass_ratio and effective_spin distributions using the weights from T032. **Dependency**: Requires `data/processed/bootstrapped_obs_samples.h5` (from T017) and `data/results/selection_bias_status.json` (from T032). **3D Structure Handling**: Iterate over the 'Iteration' axis (shape [Events, Iterations, Parameters]) of the HDF5 file. For each iteration `j`, sample one median per event from the `j-th` slice, compute the KS statistic with weights, and aggregate the resulting KS statistics to form the final distribution. **Bonferroni Correction**: Apply Bonferroni correction for multiple comparisons (multiple tests) as a sub-step of this task.
- [ ] T031 [US2] Implement `src/analysis/sensitivity.py` to sweep α over the **fixed discrete set {0.05, 0.06}** as mandated by FR-009. **Algorithm**: For each α in {0.05, 0.06}, evaluate significance. **Borderline Logic**: If the significance status (significant/not significant) flips between α=0.05 and α=0.06, flag the result as "borderline". **Artifact Generation**: This task MUST generate `data/results/sensitivity_report.json` containing the p-values and significance flags for each α in the sweep set. **Dependency**: Requires T029 (KS Test) to be complete.
- [ ] T033 [US2] Generate `output/results/ks_test_results.json` with all statistics, adjusted p-values, and significance flags. **Dependency**: Requires T031 (Sensitivity Results) and T029 (KS Test) to ensure borderline flags are applied before finalizing the report. **Specific Artifact**: Must include a dedicated entry `sc002_effective_spin_nominal` with the p-value and pass/fail status for α=0.05.

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

**Independent Test**: Verify `output/figures/` contains ≥2 PNGs (300 DPI) with annotated divergence regions.

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

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Download/Preprocess before Analysis.
- Analysis before Visualization.
- Core implementation before integration.

### Parallel Opportunities

- **Phase 1, 2**: All setup tasks can run in parallel (except T047 which depends on T001).
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
- **Scope Boundary**: This project is strictly limited to comparing existing GWTC data against the single synthetic baseline defined in US-1b and US-2. No additional Monte Carlo extrapolations or "Slow Takeoff" analyses are included.
- **Limitations**: The report must explicitly state any limitations regarding selection bias (if LVK files were missing - which is now handled by proceeding with uniform weighting per T032) and sample size power, as generated in T039.
- **Selection Bias**: Per FR-016, if LVK selection files are missing, the pipeline proceeds with uniform weighting and logs a limitation (T032), ensuring the 'Limitations' section (T039) can be generated with the correct error context.