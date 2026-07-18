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

- [ ] T001a Create `src/` directory at repository root with subdirectories: `data/`, `analysis/`, `viz/`, `utils/`. **Verification**: Run `ls src/` and verify it returns `[data, analysis, viz, utils]`. Create `src/.gitkeep` to ensure the directory is tracked by git. Verify `src/.gitkeep` exists with `test -f src/.gitkeep`.
- [ ] T001b Create `tests/` directory at repository root. **Verification**: Run `ls tests/` and verify it returns `[unit, integration, contract]`. Create `tests/.gitkeep`. Verify `tests/.gitkeep` exists with `test -f tests/.gitkeep`.
- [ ] T001c Create `data/` (raw, processed) and `output/` (results, figures) directories. **Verification**: Run `ls data/` and `ls output/` and verify the subdirectories exist. Create `data/raw/.gitkeep`, `data/processed/.gitkeep`, `output/results/.gitkeep`, `output/figures/.gitkeep`. Verify each file exists with `stat`.
- [X] T002a Create `requirements.txt` with pinned versions (numpy, scipy, pandas, matplotlib, requests, tqdm, pytest, h5py, statsmodels).
- [ ] T002b Initialize Python virtual environment and install dependencies. **Verification**: Run `python -m venv.venv` and `source.venv/bin/activate`. Run `pip list` and verify all packages from `requirements.txt` are installed. Verify `.venv/bin/python --version` returns Python 3.11.x.
- [ ] T003 Configure linting (ruff) and formatting (black) tools. **Verification**: Run `ruff check.` and `black --check.` and verify they return exit code 0 (or show expected linting errors if code is not yet written). Verify `ruff` and `black` are in `.venv/bin/`.
- [ ] T004 [P] Implement `src/utils/checksum.py` for SHA256 integrity verification of downloaded files. **Output**: A function `verify_file(path: str, expected_hash: str) -> bool`.
- [ ] T005 [P] Implement `src/utils/logger.py` with structured logging and log levels. **Output**: A configured logger that writes to `stdout` and `logs/pipeline.log`.
- [ ] T047 [US0] Configure `.github/workflows/ci.yml`. **Content**: Must include `runs-on: ubuntu-latest`, `timeout-minutes: 360` (6 hours), and a step running `pytest` (e.g., `python -m pytest tests/ -v`). **Dependency**: Runs after T001a. **Verification**: Run `cat.github/workflows/ci.yml` and verify the presence of `runs-on`, `timeout-minutes`, and `pytest` command.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes selection bias handling and main pipeline entry.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Create `src/config.py` defining paths, random seeds, and `alpha_thresholds` defaults. The configuration MUST define `alpha_thresholds` as a list of significance levels that is **overridable via CLI arguments or environment variables**.
- [ ] T007 Implement `src/data/schemas.py` with Pydantic models for GWTC_Catalog, Simulation_Dataset, Statistical_Test_Result.
- [ ] T008 [P] Setup `tests/contract/test_schemas.py` to validate JSON/CSV data against defined schemas.
- [ ] T032 [P] [US2] Implement selection bias handling in `src/analysis/selection_bias.py` (FR-016): Attempt to load official LVK selection efficiency files (if available in `data/raw/`). **If files are missing**: DO NOT invent parameters. Log a `[SELECTION_BIAS_UNCORRECTED]` warning, proceed with uniform weighting, and record this limitation in `data/results/selection_bias_status.json`. **If files exist**: Apply Inverse Probability Weighting (IPW) and record the method used. **Dependency**: Must complete before T029 and T033.
- [ ] T009 Implement `src/main.py` as the pipeline entry point with argument parsing, orchestration logic, and integrated resource monitoring hooks. The pipeline MUST log peak memory/disk usage. If thresholds (time, RAM, Disk) are exceeded, the pipeline MUST log a `[RESOURCE_BREACH]` message with the specific metric and value, then **exit with code 1** to signal failure, ensuring hard constraints (FR-011) are enforced. **Dependency**: Requires T004, T005, T032.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess GWTC Catalogs (Priority: P1) 🎯 MVP

**Goal**: Acquire observational data (GWTC-1/2) and prepare it for statistical comparison.

**Independent Test**: Verify `data/processed/obs_catalog.csv` exists with ≥100 valid events and correct checksums.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for checksum verification in `tests/unit/test_checksum.py`.
- [ ] T011 [P] [US1] Unit test for NaN filtering logic in `tests/unit/test_preprocess.py`.
- [ ] T012 [P] [US1] Integration test for download retry logic (simulate 404) in `tests/integration/test_download.py`.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/data/download.py` function to fetch GWTC-1 (DOI 10.5281/zenodo.3966973) AND GWTC-2 (DOI 10.5281/zenodo.3966974) with unified retry/backoff logic. **Verification**: Downloaded files must exist in `data/raw/` with valid checksums.
- [ ] T015 [US1] Implement `src/data/preprocess.py` to parse posterior samples, extract mass_ratio, effective_spin, component_mass, and filter NaNs.
- [ ] T016 [US1] Implement validation in `src/data/preprocess.py` to ensure ≥100 valid events remain; fail with explicit error if not.
- [ ] T017 [US1] Implement **Event-Level Bootstrapping** in `src/data/preprocess.py` to create the primary observational artifact. **Specific Mechanism**: For each bootstrap iteration (N=1000), sample a **new median** for **every single event** from its respective posterior distribution. Compute the final point estimate as the **median of these bootstrapped medians** for each parameter. Compute uncertainty as the **standard deviation** of the bootstrapped medians. **Output**: Save to `data/processed/obs_catalog.csv` with columns: `event_id`, `mass_ratio_median`, `mass_ratio_std`, `effective_spin_median`, `effective_spin_std`, `component_mass_1_median`, `component_mass_1_std`, `component_mass_2_median`, `component_mass_2_std`. This satisfies FR-014 by encoding the bootstrapped uncertainty distribution into the single point-estimate CSV. **Dependency**: Requires T013, T015, T016.

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
- [ ] T022 [US1b] Implement `src/data/generate_synthetic.py` to create a catalog based on a "Power-law mass with independent spin" hypothesis. **Citation**: Must cite "Abbott et al. (2021), ApJL, 913, L7" (or similar LVC population paper). **Parameters**: Use `alpha=2.3` (mass power-law index), `m_min=5`, `m_max=100` for component masses, and a flat spin distribution for effective spin. **Output**: `data/processed/sim_catalog.csv` with ≥100 events.
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

- [ ] T028 [P] [US2] Implement `src/analysis/kde.py` to compute 1D KDEs for mass_ratio and effective_spin using scipy.stats.gaussian_kde. **Dependency**: Requires T017 (Observational Data) AND T032 (Selection Bias/Weights) to be complete.
- [ ] T029 [P] [US2] Implement `src/analysis/ks_test.py` to perform **Weighted** KS tests on mass_ratio and effective_spin distributions using the weights from T032. **Dependency**: Requires T017 (Observational Data) and T032 (Selection Bias) to be complete.
- [ ] T030 [US2] Implement Bonferroni correction in `src/analysis/ks_test.py` for multiple comparisons (FR-006).
- [ ] T031 [US2] Implement `src/analysis/sensitivity.py` to sweep α over the explicit set {0.04, 0.05, 0.06} and flag "borderline" results (FR-009). **Artifact Generation**: This task MUST generate `data/results/sensitivity_results.json` containing the p-values and significance flags for each α in the sweep set. **Dependency**: Requires T029 (KS Test) to be complete.
- [ ] T033 [US2] Generate `output/results/ks_test_results.json` with all statistics, adjusted p-values, and significance flags. **Dependency**: Requires T031 (Sensitivity Results) and T029 (KS Test) to ensure borderline flags are applied before finalizing the report.

**Checkpoint**: User Story 2 complete - statistical comparisons are performed and corrected.

---

## Phase 6: User Story 2b & 2c - Power Analysis & Limitations (Priority: P2)

**Goal**: Assess statistical power, calculate MDES, and log limitations.

**Independent Test**: Verify `output/results/power_analysis.json` and limitations section in final report.

### Tests for User Story 2b/2c

- [ ] T034 [P] [US2c] Unit test for MDES calculation logic in `tests/unit/test_power.py`.
- [ ] T035 [P] [US2c] Unit test for power limitation detection logic in `tests/unit/test_power.py`.

### Implementation for User Story 2b/2c

- [ ] T036 [US2c] Implement `src/analysis/power.py` to calculate Minimum Detectable Effect Size (MDES) (FR-010, FR-015). **Method**: Prefer an analytical calculation based on sample sizes and standard deviations. If analytical methods are insufficient, a simulation-based (bootstrapping) approach is allowed **only if** it completes within the CPU time budget. **Dependency**: This task MUST consume `output/results/ks_test_results.json` (from T033) and `data/results/sensitivity_results.json` (from T031) as inputs.
- [ ] T037 [US2c] Implement logic in `src/analysis/power.py` to detect if simulation sample size < 50% of observational size.
- [ ] T038 [US2c] Generate `output/results/power_analysis.json` containing MDES values (explicitly named "minimum_detectable_effect_size"), sample size ratios, and power estimates.
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
- [ ] T044 [US3] Implement `src/viz/report.py` to assemble final markdown/JSON report including KS results, power analysis, sensitivity sweep (consuming `sensitivity_results.json` from T031), and "Borderline" warnings (FR-009).
- [ ] T045 [US3] Ensure all figures saved as PNG with resolution **≥300 DPI** (explicitly set `dpi=300` in matplotlib). **Verification**: Check file properties of generated PNGs using `stat` or `identify` (ImageMagick) to confirm DPI.

**Checkpoint**: User Story 3 complete - visualizations and reports are generated.

---

## Phase 8: User Story 0 - CI/CD Constraints & Performance (Priority: P0)

**Goal**: Ensure pipeline runs within GitHub Actions free-tier limits (≤6h, ≤7GB RAM, ≤20GB Disk).

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

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Download/Preprocess before Analysis.
- Analysis before Visualization.
- Core implementation before integration.

### Parallel Opportunities

- **Phase 1, 2, 8**: All setup tasks can run in parallel (except T047 which depends on T001a).
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
- **Limitations**: The report must explicitly state any limitations regarding selection bias (if LVK files were missing) and sample size power, as generated in T039.