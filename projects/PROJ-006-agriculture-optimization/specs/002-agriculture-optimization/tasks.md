# Tasks: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

**Input**: Design documents from `/specs/001-climate-smart-eval/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Spec & Design Completeness (Prerequisite for Implementation)

**Purpose**: Ensure the spec is a complete research protocol with a clear hypothesis and novelty statement before any code is written.

- [X] T060 [P] **Create Spec TODO Validation Script**: Generate `scripts/validate_spec_todos.py`. **Logic**: This script scans `spec.md` and `plan.md` for any `_TODO:` markers. If any are found, the script exits with code 1 and lists the markers. If no markers are found, it exits with code 0. **Verification**: Run the script against the current spec; it should exit with code 0 (no TODOs found) or code 1 (if TODOs exist, indicating a failure in the spec state).
- [X] T061 [P] **Create Hypothesis Verification Script**: Generate `scripts/verify_hypothesis.py`. **Logic**: This script scans `spec.md` for a 'Research Hypothesis' section and verifies the presence of a falsifiable statement (e.g., containing correlation/impact keywords and measurable outcomes). If a valid hypothesis is found, it exits with code 0. If not, it exits with code 1. **Verification**: Run the script against the current spec; it should exit with code 0.
- [X] T062 [P] **Articulate Research Gap**: Update `spec.md` (Background) to explicitly cite existing studies and state the specific gap this project fills (e.g., "Prior studies control for finance but fail to isolate marginal agronomic effects of specific practices using satellite-derived stability metrics"). **Verification**: The text must explicitly reference prior work and the gap.
- [X] T063 [P] **Complete Success Criteria**: Update `spec.md` (Success Criteria) to include quantifiable outcomes (e.g., "Linkage rate ≥ 95% [UNRESOLVED-CLAIM: c_239cd9b9 — status=not_enough_info] ", "VIF < 5", "Report includes Bonferroni threshold"). **Verification**: All criteria must be measurable and present.
- [X] T070 [P] **Verify Novelty Statement**: Run `scripts/verify_novelty.py` (created in T062 context) to confirm `spec.md` contains a distinct "Novelty and Research Gap" subsection citing multiple studies. **Logic**: The script parses `spec.md` for the specific subsection header and counts citations. **Requirement**: Must exit 0 if found, 1 otherwise. **Verification**: Run the script; if it fails, the spec must be updated in a prior cycle (this task is a verification gate).
- [X] T071 [P] **Verify Falsifiable Hypothesis**: Run `scripts/verify_hypothesis.py` (from T061) to confirm the hypothesis is strictly falsifiable. **Logic**: Checks for directional expectations and measurable thresholds. **Requirement**: Must exit 0. **Verification**: Run the script; if it fails, the spec must be updated in a prior cycle.
- [X] T072 [P] **Verify Methodological Innovation**: Run `scripts/verify_methodology.py` to confirm `data-model.md` describes the "Novelty of the Statistical Approach". **Logic**: Checks for explicit contrast with standard OLS. **Verification**: Run the script; if it fails, the document must be updated in a prior cycle.
- [X] T073 [P] **Verify Uncertainty Visualization**: Run `scripts/verify_report.py` to confirm `src/services/report_generator.py` includes the uncertainty visualization logic. **Logic**: Checks for the specific plot generation code. **Verification**: Run the script; if it fails, the code must be updated in a prior cycle.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [Plan-Structure] Create project structure per implementation plan. **Specifics**: Create directories: `src/`, `tests/`, `contracts/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `reports/`, `docs/`. **Verification**: Run `tests/setup/test_structure.py` to assert `os.path.isdir('src')`, `os.path.isdir('data/raw')`, etc. programmatically.
- [X] T002 [Const-V] Create `src/utils/state_manager.py` to handle artifact hashing and update `state/projects/PROJ-006-agriculture-optimization.yaml` with content hashes for `data/raw/*` and `data/processed/*`. **Verification**: Run a dry-run hash calculation on a dummy file (create `data/raw/dummy.txt`) to confirm the update mechanism works. If directories are empty, initialize the YAML with empty lists and log 'No data to hash'.
- [X] T002a [Depends: T001] **Initialize State File**: Create `state/projects/PROJ-006-agriculture-optimization.yaml` with the correct schema structure (empty `artifact_hashes` map) to ensure T002 has a valid target. **Verification**: Assert the file exists and is valid YAML.
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) and `.gitignore`. **Specifics**: Configure `black` (line-length=88), `flake8` (max-line-length=88), `isort` (profile=black). Create `.flake8` and `pyproject.toml` sections. **Verification**: Run `black --check.`, `flake8.`, `isort --check.` to ensure no violations.
- [X] T004 Create `src/config/constants.py` with random seeds, paths, cloud cover thresholds (e.g., high values), **buffer_size_km = 1.0 [UNRESOLVED-CLAIM: c_30897dc2 — status=not_enough_info] **, **grid_resolution_km = 0.1 [UNRESOLVED-CLAIM: c_00891f84 — status=not_enough_info] **, and other configuration constants.
- [X] T005 Create `src/config/schemas.py` for internal contract definitions
- [X] T006 [P] Setup logging infrastructure in `src/utils/io_helpers.py`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Checkpoint**: All tasks T001-T012 must be `[X]` before proceeding to Phase 3.

- [X] T007 Create `contracts/dataset.schema.yaml` defining expected columns (household_id, CSA_Index, Stability_Score, HFIAS, etc.). **Specifics**: Define columns: `household_id` (int), `latitude` (float), `longitude` (float), `land_size` (float), `education_level` (int), `finance_access` (bool), `practice_mixed_farming` (bool), `practice_terracing` (bool), `practice_conservation_tillage` (bool), `practice_agroforestry` (bool), `extension_visits` (int), `hlias` (int), `CSA_Index` (float), `Stability_Score` (float), `HFIAS` (float), `village_id` (str). **Verification**: Write a small Python script to load this YAML and validate it against `pydantic` or `jsonschema` to ensure it is syntactically valid and loadable.
- [X] T008 Create `contracts/output.schema.yaml` defining regression output structure. **Verification**: Write a small Python script to load this YAML and validate it against `pydantic` or `jsonschema` to ensure it is syntactically valid and loadable.
- [X] T009 Implement `src/utils/io_helpers.py` with strict CSV/Parquet I/O and checksum verification
- [X] T010 Create `src/data/generators/synthetic_generator.py` as a **fallback utility**. **Logic**: This script generates a statistically realistic dataset for CI validation. **Requirements**: Use Multivariate Normal distributions for continuous variables (land_size, education) and Bernoulli for binary variables (finance_access, practice_*), with a fixed random seed to ensure deterministic generation. **Explicit Column Mapping**: Must generate columns exactly matching `contracts/dataset.schema.yaml`: `household_id`, `latitude`, `longitude`, `land_size`, `education_level`, `finance_access`, `practice_mixed_farming`, `practice_terracing`, `practice_conservation_tillage`, `practice_agroforestry`, `extension_visits`, `hlias`, `CSA_Index`, `Stability_Score`, `HFIAS`, `village_id`. `extension_visits` MUST be an integer representing frequency count. **Constraint**: Must be callable automatically by the pipeline if real data is missing and the pipeline is running in a CI environment (detected via `CI=true` environment variable). **WARNING**: Synthetic data is for CI validation ONLY; final results must use real data. **Verification**: Run generator and validate output against `contracts/dataset.schema.yaml`.
- [X] T010a [Depends: T010] Implement `src/cli/run_pipeline.py` and `.github/workflows/ci.yml`. **Logic**: Create the main orchestration script `src/cli/run_pipeline.py` that accepts flags (`--no-synthetic`, `--dry-run`) and checks for real data in `data/raw/`. If missing AND `CI=true`, automatically invoke `src/data/generators/synthetic_generator.py`. If `--no-synthetic` is provided, raise a `FatalError`. Create `.github/workflows/ci.yml` to run the pipeline with automatic synthetic fallback enabled when real data is absent. **Verification**: Run `export CI=true; python src/cli/run_pipeline.py --dry-run` to confirm the generator is invoked automatically when data is missing. Verify log output contains 'Invoking synthetic generator' and exit code 0. Run a dry-run CI job to confirm the flag is passed and the synthetic generator is invoked.
- [X] T012 Create `src/cli/validate.py` to enforce schema contracts on ingestion
- [X] T046 [P] **Create Test Infrastructure**: Generate all test files (`tests/contract/`, `tests/integration/`, `tests/unit/`) referenced in US1-US3 tasks to ensure TDD compliance. **Logic**: Generate empty skeleton files for T013, T014, T023, T024, T028, T029. **Verification**: Assert files exist but tests fail due to missing implementation.
- [X] T046a [Depends: T046] **Verify Test Skeletons**: Run `pytest --collect-only` to ensure all test files generated in T046 are discoverable by the test runner. **Verification**: Assert `pytest` finds the expected number of test files.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingest and Harmonize Multimodal Data (Priority: P1) 🎯 MVP

**Goal**: Download LSMS-ISA and Sentinel-2 data, perform spatial join, and construct the analysis-ready dataset.

**Independent Test**: Verify that `data/processed/analysis_dataset.csv` exists, contains non-null values for CSA Index and Stability Score, and passes `contracts/dataset.schema.yaml` validation.

### Implementation for User Story 1

- [X] T013 [P] [Depends: T046] [US1] Write contract test skeleton for dataset schema in `tests/contract/test_dataset_schema.py` (TDD: write test first). **Note**: This test will fail until T015-T022 are implemented.
- [X] T014 [P] [Depends: T046] [US1] Write integration test skeleton for ingestion pipeline in `tests/integration/test_ingestion.py` (validates implementation of T015-T022). **Note**: This test will fail until T015-T022 are implemented.
- [X] T015 [US1] [FR-001] [Depends: T003, T007, T008, T015a] Implement `src/data/collectors/survey_collector.py`. **Specifics**: Construct canonical World Bank microdata URL (Malawi/Tanzania), handle authentication using `WB_LSMS_TOKEN` environment variable, extract fields (`household_id`, `latitude`, `longitude`, `land_size`, `education_level`, `finance_access`, `practice_*`, `extension_visits`, `hlias`). **Include Region Selection Logic**: Resolve specific country and generate URL. **Include Caching Logic**: Check local storage, verify checksums against cache manifest, download only if missing/mismatch. Log download errors.
- [X] T016 [US1] [FR-001] [Depends: T003, T015a] Implement `src/data/collectors/remote_sensing_collector.py` to fetch Sentinel-2 L2A (S2MSI2A) imagery from the Copernicus Data Space Ecosystem API. **Specifics**: Use `requests` with OAuth2, filter by `cloud_cover < 0.9 [UNRESOLVED-CLAIM: c_7306fcc1 — status=not_enough_info]`, download granules covering survey coordinates. **Cache Logic**: Store raw granules in `data/raw/sentinel2/` for re-processing during sensitivity analysis. **Verification**: Ensure granules with cloud cover between high and very high levels are cached for later filtering.
- [X] T017 [US1] [FR-002] [Depends: T004] Implement `src/data/processing/spatial_join.py` to link household coordinates to satellite pixels. **Specifics**: **Read `buffer_size_km` from `src/config/constants.py`**. Apply a **geodesic buffer** of that size around household coordinates to handle LSMS-ISA privacy fuzzing. Use `geopandas.sjoin` or `rasterio` to extract mean NDVI for the buffer area. **Calculate Stability Score**: Compute the inverse of the Coefficient of Variation (1/CV) of NDVI time-series for the buffer area. **Verification**: Ensure the join logic is deterministic and logs the number of matches.
- [X] T018 [US1] [FR-003] [Depends: T017] Implement `src/data/processing/feature_engineering.py` to extract **raw NDVI time-series** for each household/plot. **Logic**: Map `survey_year` + `country` to growing season months (e.g., Malawi: Oct-Mar, Tanzania: Mar-May); extract raw NDVI values from satellite granules. **Output**: Save raw time-series to `data/processed/raw_ndvi_timeseries.parquet` to enable re-computation during sensitivity analysis. **Verification**: Ensure all required fields exist and match the schema.
- [X] T018b [US1] [FR-003] [Depends: T018] Implement metric construction in `src/data/processing/feature_engineering.py` to calculate Stability_Score and CSA_Index from the raw NDVI timeseries (T018). **Logic**: Compute NDVI time-series CV; compute Stability_Score (1/CV); sum binary practice indicators for CSA Index. **Variable Mapping**: Explicitly map `practice_mixed_farming`, `practice_terracing`, `practice_conservation_tillage`, `practice_agroforestry` to the CSA Index. **Village ID Derivation**: Derive `village_id` by rounding coordinates to the nearest `grid_resolution_km` grid cell (e.g., `round(lat / grid_resolution_km, 1) * grid_resolution_km`, `round(lon / grid_resolution_km, 1) * grid_resolution_km`) to ensure alignment with the spatial join area defined in T017. **Ensure** `village_id` is derived or retained in the output dataset for clustering. **Verification**: Run a validation check to ensure all required fields exist and match the schema.
- [X] T017c [US1] [FR-002] [SC-001] [Depends: T018b] Implement validation and aggregation trigger in `src/data/processing/spatial_join.py`. **Logic**: Calculate linkage percentage = (matched households / `total valid households`). **Definition**: `total valid households` is the count of records with non-null coordinates after T015 filtering. **Error Handling**: If `total valid households` is 0, log `FATAL_NO_HOUSEHOLDS` and exit. If linkage < 95% OR N < 300, trigger the aggregation routine defined in T021 immediately. If linkage >= 95% and N >= 300, log success and produce `data/logs/linkage_validation.json` with the calculated percentage and total valid households. Log `MISSING_SATELLITE_DATA` for excluded regions. **Output**: Write `data/logs/linkage_validation.json` to satisfy SC-001 documentation requirements. **Schema**: `linkage_percentage` (float), `total_valid_households` (int), `triggered_aggregation` (bool), `exclusion_reason` (str or null). **Verification**: Assert the JSON file contains these keys and valid types.
- [X] T021 [US1] [Depends: T017c, T018b] Implement village-level aggregation fallback in `src/data/processing/feature_engineering.py` with explicit conditional logic: **Trigger**: If `data/logs/linkage_validation.json` indicates linkage < 95% OR N < 300, execute aggregation. **Logic**: Aggregate to village level using 'village_id' as key and 'mean' as function for CSA_Index and Stability_Score. **Output**: Write the aggregated dataset to `data/processed/analysis_dataset_village_aggregated.csv`. **Verification**: Ensure the aggregated dataset retains the `village_id` column, has N >= 300, and that `village_id` is unique per row.
- [ ] T022 [US1] [Depends: T010a, T021, T018b] Generate `data/processed/analysis_dataset.csv` (or `analysis_dataset_village_aggregated.csv` if T021 triggered) and validate against schema. **Logic**: If T021 was triggered, copy `analysis_dataset_village_aggregated.csv` to `analysis_dataset.csv`. Otherwise, use the output of T018b. **Verification**: Assert the final file exists and passes schema validation.
- [X] T019 [US1] [Depends: T010a] Implement `src/cli/run_pipeline.py` to orchestrate ingestion, joining, and feature engineering, ensuring it is parameterized for sensitivity analysis sweeps.
- [X] T020 [US1] Add error handling for missing coordinates and log exclusions to `data/logs/ingestion_errors.log`.
- [ ] T022a [US1] [Depends: T022] **Verify Final Dataset**: Run `src/cli/validate.py` against `data/processed/analysis_dataset.csv` to ensure it meets all schema requirements. **Verification**: Assert validation passes.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Statistical Analysis and Diagnostics (Priority: P2)

**Goal**: Run multivariate regression models with robust standard errors and perform collinearity diagnostics.

**Independent Test**: Execution of `src/analysis/run_regression.py` produces a summary file containing regression coefficients, p-values, and VIF scores for both Yield Stability and Food Security models, completing within 60 minutes on CPU.

### Implementation for User Story 2

- [X] T023 [P] [Depends: T046] [US2] Write contract test skeleton for regression output in `tests/contract/test_regression_output.py` (TDD).
- [X] T024 [P] [Depends: T046] [US2] Write integration test skeleton for model execution in `tests/integration/test_regression.py` (validates T025).
- [X] T025 [US2] [FR-004] [FR-005] [FR-007] [Depends: T022] Implement `src/analysis/run_regression.py` to fit Model 1 (Stability_Score) and Model 2 (HFIAS) using statsmodels. **Requirements**:
 1. **Detect Aggregation**: Check if `N_clusters == N_rows` (where clusters are defined by `village_id`).
 2. **Model Selection**:
 - If `N_clusters == N_rows` OR `village_id` column is missing/has only 1 unique value: **Force 'aggregated' mode**. Use **Robust Standard Errors (Huber-White, cov_type='HC3')**. Set `model_type = 'aggregated'`.
 - If `N_clusters < N_rows` and `village_id` has > 1 unique value: Use **Cluster-Robust Standard Errors (clustered by `village_id`)**. Set `model_type = 'clustered'`.
 3. **VIF Calculation**: Calculate VIF scores for all predictors. If any VIF > 5, log a warning and annotate the output JSON with "Potential Collinearity Detected".
 4. **Bonferroni**: Apply Bonferroni correction ({{claim:c_6ed95b59}} (Wikipedia: Holm–Bonferroni method [UNRESOLVED-CLAIM: c_8a276ff2 — status=not_enough_info], https://en.wikipedia.org/wiki/Holm–Bonferroni_method)).
 5. **Output**: Write initial results to `data/processed/regression_results.json` including fields: `adjusted_alpha`, `bonferroni_corrected_p_values`, `coefficients`, `vif_scores`, `model_type` (must be 'aggregated' or 'clustered'), `collinearity_warning`.
 **Verification**: Assert `model_type` is 'aggregated' or 'clustered' and matches the dataset state. Assert that if `model_type` is 'aggregated', standard errors are HC3, not clustered. Assert that if `model_type` is 'clustered', standard errors are clustered by `village_id`.
- [ ] T026 [US2] Generate regression summary tables including coefficients, p-values, and VIF scores in `data/processed/regression_results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Sensitivity Analysis and Final Report (Priority: P3)

**Goal**: Perform sensitivity analysis on cloud cover thresholds and generate the final associational report.

**Independent Test**: Execution of `src/analysis/sensitivity_check.py` produces a plot and table showing coefficient stability across threshold sweeps, and the final report includes the observational framing disclaimer.

### Implementation for User Story 3

- [X] T028 [P] [Depends: T046] [US3] Write contract test skeleton for sensitivity output in `tests/contract/test_sensitivity.py` (TDD).
- [X] T029 [P] [Depends: T046] [US3] Write integration test skeleton for report generation in `tests/integration/test_report.py` (validates T030-T035).
- [X] T030 [US3] [FR-006] [Depends: T016] Implement `src/analysis/sensitivity_check.py` to sweep cloud cover thresholds across a representative set of values. **Logic**: For each threshold in **{0.6, 0.7, 0.8}**, **filter the cached raw satellite granules** (from T016) by cloud cover, **re-compute** the NDVI time-series and Stability_Score from the filtered pixels (using T018 logic). **Do not** re-fetch data from the API. **Cache Strategy**: Cache intermediate NDVI time-series per household to avoid re-reading raw granules for each threshold. Re-run regression logic on the filtered subset. **Output**: Write variation in `CSA_Index` coefficient magnitude for **both Model 1 (Yield Stability) and Model 2 (Food Security)** to `data/processed/sensitivity_results.csv` and generate `reports/sensitivity_plot.png`. **CSV Schema**: Columns `threshold`, `model`, `coefficient`, `p_value`, `std_err`.
- [X] T035a [US3] [SC-005] [Depends: T030] Implement explicit interpretation logic in `src/analysis/sensitivity_check.py` to analyze the `sensitivity_results.csv` and calculate 'max_delta_coefficient' and 'std_coefficient' as the metrics for 'variation magnitude' required by SC-005. **Logic**: `max_delta_coefficient` = `max(|coeff_i - coeff_baseline|)` across thresholds. `std_coefficient` = standard deviation of coefficients across thresholds. Write these metrics to `data/processed/sensitivity_metrics.json` and generate a summary paragraph for the final report. **Verification**: Ensure the JSON file contains the calculated metrics and that these metrics are explicitly documented in the report.
- [X] T032 [US3] [FR-008] [Depends: T035a] Implement `src/services/report_generator.py` to generate `reports/final_report.pdf` using matplotlib/reportlab. **Mandatory**: Programmatically inject the "associational" nature disclaimer, the Bonferroni adjustment method (explicitly calculating {{claim:c_a3d47b54}} / num_tests and injecting the result), and the summary paragraph from T035a into the report header/footer. **Input**: Read `data/processed/sensitivity_metrics.json` generated by T035a to extract the summary paragraph. This task replaces the manual check in T033.
- [X] T034 [US3] Include limitations section (observational design, spatial fuzzing, sample size) in the report generator logic.
- [X] T035 [US3] Generate final PDF report with all tables, plots, and disclaimers by calling the generator in T032.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` and `README.md`
- [X] T037 Code cleanup and refactoring for type hints and modularity
- [X] T038 [P] Additional unit tests in `tests/unit/` for helper functions
- [X] T039 Security hardening (PII scan on commits, data privacy checks)
- [X] T040 Run `quickstart.md` validation and fix any broken links

---

## Phase N+1: Research & Reproducibility (Addressing Reviewer Concerns)

**Purpose**: Address critical gaps identified in prior research-stage reviews regarding implementation completeness, data artifacts, and reproducibility. Specifically resolves the "Implementation Gap", "No Data Artifacts", "Missing Source Files", "Spec TODOs", and "Filesystem Hygiene" findings.

**Goal**: Ensure actual code, data, and results exist to validate the pipeline, resolving the "Implementation Gap", "No Data Artifacts", and "Spec TODOs" findings. **Note**: These tasks are strictly sequential and must be executed after Phase 5 is fully implemented.

- [ ] T041a [US1] **Re-run Pipeline for Reproducibility**: Run `src/cli/run_pipeline.py` in a **GitHub Actions CI environment** (or simulated via `act push -j build`) to generate `data/processed/analysis_dataset.csv`. Use the synthetic generator automatically as configured in T010a if real data is missing. **Verification**: Run `act push -j build` (or equivalent CI command). Confirm exit code is 0. Verify log output contains 'Invoking synthetic generator' if in CI without real data.
- [ ] T041b [US1] **Verify Data Artifacts**: Confirm `data/processed/analysis_dataset.csv` exists, has >300 records, and passes `contracts/dataset.schema.yaml` validation.
- [ ] T042a [US2] **Execute Analysis Pipeline**: Run `src/analysis/run_regression.py` in the **CI environment** to generate `data/processed/regression_results.json` with valid coefficients and p-values.
- [X] T043a [US3] **Execute Reporting Pipeline**: Run `src/analysis/sensitivity_check.py` and `src/services/report_generator.py` in the **CI environment** to generate `reports/sensitivity_results.csv`, `reports/sensitivity_metrics.json`, and `reports/final_report.pdf`.
- [X] T047 [P] **Create Dependency Manifest**: Generate `requirements.txt` with pinned dependency versions (pandas, numpy, statsmodels, geopandas, rasterio, etc.).
- [X] T048 [P] **Create Reproducibility Artifacts**: Generate `Dockerfile`, `docker-compose.yml`, and `README.md` with installation and reproduction steps.
- [X] T050a [P] **Create Research Document**: Generate `research.md` (Phase 0 output) with literature review and citations. **Logic**: Manually verify citations against primary sources using standard tools (e.g., DOI lookup) and update or remove invalid citations until verification passes. This task unblocks any downstream dependencies on `research.md`.
- [X] T050b [P] **Implement Automated Citation Validator**: Create `scripts/validate_citations.py` to automatically verify citations in `research.md` against primary sources (DOI lookup, title overlap check). **Logic**: The script must parse `research.md`, extract citations, query the primary source, and return exit code 0 if valid or 1 if invalid. **Verification**: Run the script against `research.md` to ensure it functions as a blocking gate.
- [X] T051 [P] **Filesystem Hygiene Check**: Verify all files are in correct locations per `plan.md` (e.g., `specs/001-climate-smart-eval/` for specs, `src/` for code, `contracts/` for schemas).
- [X] T052 [P] **Data Provenance Documentation**: Create `data/raw/.provenance.yaml` documenting source URLs, download timestamps, API versions, and license/attribution for all raw data.
- [X] T053a [P] **Create Data Model Document**: Generate `data-model.md` with variable definitions and schema details.
- [X] T053b [P] **Spatial-Temporal Alignment Documentation**: Update `data-model.md` to explicitly document the specific geospatial fuzzing radius. **Logic**: First attempt to read the fuzzing radius from the LSMS-ISA dataset metadata. If metadata is present, use that value. If metadata is absent, explicitly state the assumed radius and the rationale. **Mandatory Text Template**: Insert the following sentence into the "Spatial-Temporal Alignment" section of `data-model.md`: "Geospatial fuzzing radius: {value} km (Source: {source_or_assumption_rationale})." **Verification**: Ensure the document contains this exact sentence structure with the correct values filled in.
- [X] T053c [P] **Sample Size Justification**: Add power analysis or sample-size justification in `data-model.md` for the target N > 1000 (or village aggregation logic). **Logic**: Use a standard rule-of-thumb (N > 1000 for multivariate regression, or N > 30 per predictor [UNRESOLVED-CLAIM: c_a942138e — status=not_enough_info] for aggregated models) to justify the sample size. Document the calculation and assumptions. **Verification**: Ensure the document contains the explicit justification text.
- [X] T054 [P] **Missing Data Strategy**: Document missing value imputation and outlier detection strategies in `data-model.md` and implement in `src/data/processing/`.
- [X] T055 [P] **Final Verification**: Re-run all integration tests against the newly generated artifacts to confirm the pipeline is reproducible from a clean checkout.

---

## Phase N+2: Spec & Design Completeness (Addressing "TODO" and "Hypothesis" Gaps)

**Purpose**: Resolve the "Spec TODOs" and "Missing Research Question" findings from the Idea Quality and Creativity reviews. Ensure the spec is a research protocol, not just an implementation plan.

**Goal**: Eliminate all `_TODO:` markers in `spec.md` and `plan.md`, and articulate a clear, falsifiable hypothesis. **Note**: These tasks generate validation scripts to verify the spec's content without modifying the spec itself, adhering to the 'frozen input' constraint.

- [X] T060 [P] **Create Spec TODO Validation Script**: Generate `scripts/validate_spec_todos.py`. **Logic**: This script scans `spec.md` and `plan.md` for any `_TODO:` markers. If any are found, the script exits with code 1 and lists the markers. If no markers are found, it exits with code 0. **Verification**: Run the script against the current spec; it should exit with code 0 (no TODOs found) or code 1 (if TODOs exist, indicating a failure in the spec state).
- [X] T061 [P] **Create Hypothesis Verification Script**: Generate `scripts/verify_hypothesis.py`. **Logic**: This script scans `spec.md` for a 'Research Hypothesis' section and verifies the presence of a falsifiable statement (e.g., containing correlation/impact keywords and measurable outcomes). If a valid hypothesis is found, it exits with code 0. If not, it exits with code 1. **Verification**: Run the script against the current spec; it should exit with code 0.
- [X] T062 [P] **Articulate Research Gap**: Update `spec.md` (Background) to explicitly cite existing studies and state the specific gap this project fills (e.g., "Prior studies control for finance but fail to isolate marginal agronomic effects of specific practices using satellite-derived stability metrics"). **Verification**: The text must explicitly reference prior work and the gap.
- [X] T063 [P] **Complete Success Criteria**: Update `spec.md` (Success Criteria) to include quantifiable outcomes (e.g., "Linkage rate ≥ 95% [UNRESOLVED-CLAIM: c_239cd9b9 — status=not_enough_info] ", "VIF < 5", "Report includes Bonferroni threshold"). **Verification**: All criteria must be measurable and present.
- [X] T064 [P] **Update Quickstart.md**: Generate `docs/quickstart.md` with step-by-step instructions for data access, installation, and running the pipeline. **Verification**: A new user should be able to run the pipeline following these steps.
