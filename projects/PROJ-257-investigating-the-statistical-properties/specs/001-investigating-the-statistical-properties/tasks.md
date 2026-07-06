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

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `src/` directory at repository root with subdirectories: `data/`, `analysis/`, `viz/`, `utils/`
- [ ] T001b [P] Create `tests/` directory at repository root
- [ ] T001c [P] Create `data/` (raw, processed) and `output/` (results, figures) directories
- [ ] T002a [P] Create `requirements.txt` with pinned versions (numpy, scipy, pandas, matplotlib, requests, tqdm, pytest)
- [ ] T002b [P] Initialize Python 3.11 virtual environment and install dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/checksum.py` for SHA256 integrity verification of downloaded files
- [ ] T005 [P] Implement `src/utils/logger.py` with structured logging and log levels
- [ ] T006 [P] Create `src/config.py` defining paths, random seeds (42), and `alpha_thresholds=[0.04, 0.05, 0.06]` for sensitivity analysis. The configuration must default to this full list to support the required sweep logic in FR-009. **Note**: This specific set is the default mandated by FR-009, but the implementation MUST support extension via CLI arguments or a config file if the sweep range needs to be widened later without code changes.
- [ ] T007 Implement `src/data/schemas.py` with Pydantic models for GWTC_Catalog, Simulation_Dataset, Statistical_Test_Result
- [ ] T008 [P] Setup `tests/contract/test_schemas.py` to validate JSON/CSV data against defined schemas
- [ ] T009 Implement `src/main.py` as the pipeline entry point with argument parsing, orchestration logic, and integrated resource monitoring hooks. The pipeline MUST log peak memory/disk usage. If thresholds (time, RAM, Disk) are exceeded, the pipeline MUST log a `[RESOURCE_BREACH]` message with the specific metric and value, then **continue execution** to completion to ensure logs are generated. Verification of constraints is handled by a separate CI check. Exit with code 0 even on breach.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess GWTC Catalogs (Priority: P1) 🎯 MVP

**Goal**: Acquire observational data (GWTC-1/2) and prepare it for statistical comparison.

**Independent Test**: Verify `data/raw/gwtc_*.csv` exists with ≥100 valid events and correct checksums.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for checksum verification in `tests/unit/test_checksum.py`
- [ ] T011 [P] [US1] Unit test for NaN filtering logic in `tests/unit/test_preprocess.py`
- [ ] T012 [P] [US1] Integration test for download retry logic (simulate 404) in `tests/integration/test_download.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/data/download.py` function to fetch GWTC-1 (DOI 10.5281/zenodo.3966973) AND GWTC-2 (DOI 10.5281/zenodo.3966974) with unified retry/backoff logic
- [ ] T015 [US1] Implement `src/data/preprocess.py` to parse posterior samples, extract mass_ratio, effective_spin, component_mass, and filter NaNs
- [ ] T016 [US1] Implement validation in `src/data/preprocess.py` to ensure ≥100 valid events remain; fail with explicit error if not
- [ ] T017 [US1] Implement sampling from posterior distributions (FR-014) to create point-estimate datasets for KS tests, ensuring uncertainty is reflected

**Checkpoint**: User Story 1 complete - observational data is downloaded, validated, and preprocessed.

---

## Phase 4: User Story 1b - Download/Generate Simulation Population (Priority: P1) 🎯 MVP

**Goal**: Acquire or generate a simulation dataset with matching schema (mass_ratio, effective_spin).

**Independent Test**: Verify `data/raw/simulation_catalog.csv` exists with ≥100 valid events and matching schema.

### Tests for User Story 1b

- [ ] T018 [P] [US1b] Unit test for synthetic data generation distribution (power-law) in `tests/unit/test_synthetic_gen.py`
- [ ] T019 [P] [US1b] Unit test for schema validation of simulation data in `tests/unit/test_schemas.py`

### Implementation for User Story 1b

- [ ] T020 [P] [US1b] Implement `src/data/download.py` function to attempt fetching a dedicated BBH population synthesis catalog (e.g., from Zenodo/Community Repo)
- [ ] T021 [US1b] Implement fallback logic in `src/data/download.py` to generate synthetic catalog if external source fails
- [ ] T022 [US1b] Implement `src/data/generate_synthetic.py` to create a catalog based on a "Power-law spin distribution" hypothesis (cited from GWTC-3 literature)
- [ ] T023 [US1b] Ensure synthetic generator produces ≥100 events with `mass_ratio`, `effective_spin`, `component_mass_1`, `component_mass_2`
- [ ] T024 [US1b] Add validation in `src/data/preprocess.py` to confirm simulation data schema matches observational data schema

**Checkpoint**: User Story 1b complete - simulation data is available and schema-matched.

---

## Phase 5: User Story 2 - Statistical Analysis (KS Tests & Corrections) (Priority: P2)

**Goal**: Perform Kolmogoror-Smirnov tests with Bonferroni correction and sensitivity analysis.

**Independent Test**: Verify `output/results/ks_test_results.json` contains statistics, p-values, and corrected flags.

### Tests for User Story 2

- [ ] T025 [P] [US2] Unit test for KDE bandwidth selection (Scott's rule) in `tests/unit/test_kde.py`
- [ ] T026 [P] [US2] Unit test for Bonferroni correction logic in `tests/unit/test_ks_test.py`
- [ ] T027 [P] [US2] Unit test for sensitivity analysis sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 2

- [ ] T028 [P] [US2] Implement `src/analysis/kde.py` to compute 1D KDEs for mass_ratio and effective_spin using scipy.stats.gaussian_kde
- [ ] T029 [US2] Implement `src/analysis/ks_test.py` to perform KS tests on mass_ratio and effective_spin distributions
- [ ] T030 [US2] Implement Bonferroni correction in `src/analysis/ks_test.py` for multiple comparisons (FR-006)
- [ ] T031 [US2] Implement `src/analysis/sensitivity.py` to sweep α ∈ {0.04, 0.05, 0.06} and flag "borderline" results (FR-009). This task MUST implement the logic but does not generate the final artifact.
- [ ] T031b [US2] Generate `data/results/sensitivity_report.json` by executing the sensitivity sweep logic defined in T031. This task MUST consume the bootstrapped KS results and output the sweep report.
- [ ] T032 [US2] Implement selection bias handling in `src/analysis/ks_test.py` (FR-016): Attempt to load LVK selection files. If present, apply correction. If LVK files are missing, log the message "Selection bias correction unavailable: LVK files missing" at WARNING level and **MUST generate** `data/results/selection_bias_status.json` documenting the uncorrected state. DO NOT implement any fallback correction method (e.g., volume weighting) as this is scientifically invalid per plan.md.
- [ ] T033 [US2] Generate `output/results/ks_test_results.json` with all statistics, adjusted p-values, and significance flags

**Checkpoint**: User Story 2 complete - statistical comparisons are performed and corrected.

---

## Phase 6: User Story 2b & 2c - Power Analysis & Limitations (Priority: P2)

**Goal**: Assess statistical power, calculate MDES, and log limitations.

**Independent Test**: Verify `output/results/power_analysis.json` and limitations section in final report.

### Tests for User Story 2b/2c

- [ ] T034 [P] [US2c] Unit test for MDES calculation logic in `tests/unit/test_power.py`
- [ ] T035 [P] [US2c] Unit test for power limitation detection logic in `tests/unit/test_power.py`

### Implementation for User Story 2b/2c

- [ ] T036 [US2c] Implement `src/analysis/power.py` to calculate Minimum Detectable Effect Size (MDES) using simulation-based power analysis (bootstrapping KS statistics) with standard statistical confidence levels. This task MUST consume `output/results/ks_test_results.json` (from T033) and `data/results/sensitivity_report.json` (from T031b) as inputs.
- [ ] T037 [US2c] Implement logic in `src/analysis/power.py` to detect if simulation sample size < 50% of observational size
- [ ] T038 [US2c] Generate `output/results/power_analysis.json` containing MDES values (explicitly named "minimum_detectable_effect_size"), sample size ratios, and power estimates
- [ ] T039 [US2c] Update report generation to include "Limitations" section with power notes and MDES interpretation (FR-010, SC-011)

**Checkpoint**: User Story 2b/2c complete - power and limitations are quantified.

---

## Phase 7: User Story 3 - Visualization & Reporting (Priority: P3)

**Goal**: Generate plots and final report with divergence annotations.

**Independent Test**: Verify `output/figures/` contains ≥2 PNGs (300 DPI) with annotated divergence regions.

### Tests for User Story 3

- [ ] T040 [P] [US3] Unit test for plot generation and DPI settings in `tests/unit/test_plots.py`
- [ ] T041 [P] [US3] Integration test for full report generation in `tests/integration/test_report.py`

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement `src/viz/plots.py` to create 1D KDE plots for mass_ratio and effective_spin (overlaid distributions)
- [ ] T043 [US3] Implement annotation logic in `src/viz/plots.py` to highlight regions where p < 0.05 as statistically significant (FR-008)
- [ ] T044 [US3] Implement `src/viz/report.py` to assemble final markdown/JSON report including KS results, power analysis, and sensitivity sweep
- [ ] T045 [US3] Ensure all figures saved as PNG with ≥300 DPI resolution
- [ ] T046 [US3] Add "Borderline" warnings to report if sensitivity analysis shows significance flipping (FR-009)

**Checkpoint**: User Story 3 complete - visualizations and reports are generated.

---

## Phase 8: User Story 0 - CI/CD Constraints & Performance (Priority: P0)

**Goal**: Ensure pipeline runs within GitHub Actions free-tier limits (≤6h, ≤7GB RAM, ≤20GB Disk).

**Independent Test**: Run pipeline in CI environment and verify resource usage logs.

### Implementation for User Story 0

- [ ] T047 [P] [US0] Configure `.github/workflows/ci.yml` to run the pipeline with timeout-minutes=360 and resource constraints. Ensure this task depends on T009 (main.py) which contains the integrated monitoring logic.
- [ ] T048 [P] [US0] Optimize data loading in `src/data/preprocess.py` to stream/process in chunks if necessary (avoid loading full posterior samples into RAM)
- [ ] T049 [P] [US0] Add pre-commit hook to check for large file uploads or inefficient imports

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

- **Phase 1, 2, 8**: All setup tasks can run in parallel.
- **Phase 3 & 4**: US1 (Observational) and US1b (Simulation) can be developed in parallel.
- **Phase 5, 6, 7**: Once data is ready, KDE, KS, Power, and Viz modules can be developed in parallel (if data dependencies are mocked or data is ready).

---

## Implementation Strategy

### MVP First (User Stories 1, 1b, 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Download GWTC)
4. Complete Phase 4: US1b (Download/Gen Simulation)
5. Complete Phase 5: US2 (KS Tests)
6. **STOP and VALIDATE**: Ensure data flows and KS tests run correctly on free-tier.

### Incremental Delivery

1. Add Phase 6: US2b/2c (Power Analysis)
2. Add Phase 7: US3 (Visualization)
3. Add Phase 8: US0 (CI Constraints)

### Parallel Team Strategy

- **Dev A**: Focus on Data Pipeline (US1, US1b)
- **Dev B**: Focus on Analysis Core (US2, US2b/2c)
- **Dev C**: Focus on Viz, Reporting (US3)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **Critical Constraint**: All code must run on CPU-only, -core, limited RAM. No GPU, no large model loading.
- **Data Integrity**: All downloads must have checksum verification. No fake data allowed.
- **Scope Boundary**: This project is strictly limited to comparing existing GWTC data against the single synthetic baseline defined in US-1b and US-2. **Future projections, "Slow Takeoff" analysis, or alternative hypothesis testing regarding future data requirements are explicitly out of scope** and must not be implemented.
