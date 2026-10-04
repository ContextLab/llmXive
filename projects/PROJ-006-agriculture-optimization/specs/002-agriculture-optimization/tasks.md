# Tasks: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

**Input**: Design documents from `/specs/001-climate-smart-eval/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Recovery, Reset & Spec Completeness (Prerequisite for Implementation)

**Purpose**: Ensure the project state is consistent, resolve missing artifacts, and verify the spec is a complete research protocol before any code is written. This phase replaces the previous "T085" meta-task with active logic.

- [X] T050a [P] **Create Research Document**: Generate `research.md` (Phase 0 output) with literature review and placeholder citations. **Logic**: Generate `research.md` using the exact "Research Hypothesis" and "Novelty and Research Gap" text provided in the `spec.md` Background section. **Required Sections**: Must include a "Research Hypothesis" section with falsifiable statements and a "Novelty and Research Gap" section citing multiple studies. **Verification**: Ensure `research.md` exists and contains these sections.
- [X] T050b [Depends: T050a] [P] **Implement Automated Citation Validator**: Create `src/cli/validate_citations.py` to automatically verify citations in `research.md` against primary sources. **Logic**: The script must parse `research.md`, extract citations, query the primary source via Crossref API (DOI lookup), and check title overlap (threshold > 0.7). Return exit code 0 if valid or 1 if invalid. **Integration**: This script MUST be invoked by `src/cli/run_pipeline.py` (T010a) as a blocking gate at the start of execution. **Verification**: Run the script against `research.md` to ensure it functions as a blocking gate.
- [X] T000 [P] **Recovery & Reset**: Execute `scripts/recovery_reset.py`. **Logic**: This script scans `data/`, `src/`, and `tests/` for missing artifacts (e.g., `data/processed/analysis_dataset.csv`, `src/data/collectors/survey_collector.py`). If critical source files are missing, it automatically unmarks (resets) all dependent tasks in `tasks.md` (specifically T015-T035) to `[ ]`. It also verifies `research.md` exists. **Verification**: Script exits 0 if reset is complete; exits 1 if `research.md` is missing.
- [X] T085 [P] **Initialize Re-implementation State**: Reset task markers for T015-T035 to `[ ]` to ensure a clean slate for re-implementation and verification. **Logic**: This task MUST run immediately after T000. It scans the `tasks.md` file and explicitly unmarks any tasks in the range T015-T035 that are marked as `[X]`. **Verification**: Assert that T015-T035 are all marked `[ ]` after execution. **Note**: This resolves the contradiction where the pipeline runs on "complete" tasks that are actually being patched.
- [X] T060 [P] **Verify Spec Completeness**: Create and run `scripts/validate_spec_completeness.py`. **Logic**: This script scans `spec.md` and `plan.md` for `_TODO:` markers, verifies the presence of a 'Research Hypothesis' section with falsifiable statements, and checks for quantifiable success criteria (e.g., "≥ 95% linkage"). **Verification**: Script exits 0 if all checks pass; exits 1 if any TODOs or missing criteria are found, blocking further implementation.
- [X] T061 [Depends: T050a] [P] **Verify Novelty & Hypothesis**: Create and run `scripts/verify_novelty_hypothesis.py`. **Logic**: Parses `research.md` (not spec.md) for a "Novelty and Research Gap" subsection citing multiple studies and validates the hypothesis contains directional expectations and measurable thresholds. **Verification**: Script exits 0 if valid; exits 1 if missing or insufficient.
- [X] T062 [Depends: T050a] [P] **Verify Methodology & Reporting**: Create and run `scripts/verify_methodology_report.py`. **Logic**: Checks `data-model.md` for explicit contrast with standard OLS and `plan.md` for the uncertainty visualization logic and report disclaimer requirements. **Verification**: Script exits 0 if all required sections and logic descriptions are present.
- [X] T050d [Depends: T050a, T050b] [P] **Verify Research Artifacts**: Create and run `scripts/verify_research_artifacts.py`. **Logic**: This script explicitly checks that `research.md` exists, contains the required sections, and that `src/cli/validate_citations.py` returns exit code 0. **Verification**: Script exits 0 only if all checks pass. This task ensures the 'complete' status of Phase 0 is truthful.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [Plan-Structure] Create project structure per implementation plan. **Specifics**: Create directories: `src/`, `tests/`, `contracts/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `reports/`, `docs/`. **Verification**: Run `tests/setup/test_structure.py` to assert `os.path.isdir('src')`, `os.path.isdir('data/raw')`, etc. programmatically.
- [X] T002a [P] **Initialize State File**: Create `state/projects/PROJ-006-agriculture-optimization.yaml` with the correct schema structure (empty `artifact_hashes` map) to ensure T002b has a valid target. **Verification**: Assert the file exists and is valid YAML.
- [X] T002b [Depends: T002a] [P] **Create State Manager**: Create `src/utils/state_manager.py` to handle artifact hashing and update `state/projects/PROJ-006-agriculture-optimization.yaml` with content hashes for `data/raw/*` and `data/processed/*`. **Verification**: Run a dry-run hash calculation on a dummy file (create `data/raw/dummy.txt`) to confirm the update mechanism works. If directories are empty, initialize the YAML with empty lists and log 'No data to hash'.
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) and `.gitignore`. **Specifics**: Configure `black` (line-length=88), `flake8` (max-line-length=88), `isort` (profile=black). Create `.flake8` and `pyproject.toml` sections. **Verification**: Run `black --check.`, `flake8.`, `isort --check.` to ensure no violations.
- [X] T004 [P] Create `src/config/constants.py` with random seeds, paths, cloud cover thresholds (e.g., high values), **buffer_size_km = 1.0 **, **grid_resolution_km = 0.1 **, and other configuration constants.
- [X] T006 [P] Setup logging infrastructure in `src/utils/io_helpers.py`
- [X] T007 [P] **Create Dataset Schema**: Create `contracts/dataset.schema.yaml` defining expected columns. **Specifics**: Define columns: `household_id` (int), `latitude` (float), `longitude` (float), `land_size` (float), `education_level` (int), `finance_access` (bool), `practice_mixed_farming` (bool), `practice_terracing` (bool), `practice_conservation_tillage` (bool), `practice_agroforestry` (bool), `extension_visits` (int), `hlias` (int), `CSA_Index` (float), `Stability_Score` (float), `HFIAS` (float), `village_id` (str). **Verification**: Write a small Python script to load this YAML and validate it against `pydantic` or `jsonschema` to ensure it is syntactically valid and loadable.
- [X] T008 [P] **Create Output Schema**: Create `contracts/output.schema.yaml` defining regression output structure. **Specifics**: Define keys: `coefficients` (dict), `p_values` (dict), `vif_scores` (dict), `model_type` (str), `collinearity_warning` (bool). **Verification**: Write a small Python script to load this YAML and validate it against `pydantic` or `jsonschema` to ensure it is syntactically valid and loadable.
- [X] T053a [P] **Create Data Model Document**: Generate `data-model.md` with variable definitions and schema details.
- [X] T053b [Depends: T053a] [P] **Spatial-Temporal Alignment Documentation**: Update `data-model.md` to explicitly document the specific geospatial fuzzing radius. **Logic**: Read the fuzzing radius from `src/config/constants.py`. **Correction**: Since LSMS-ISA is not available, use the default value from `src/config/constants.py` (1.0km) and explicitly document the assumption that the fuzzing is synthetic/project-defined. **Mandatory Text Template**: Insert the following sentence into the "Spatial-Temporal Alignment" section of `data-model.md`: "Geospatial fuzzing radius: {value} km (Source: Assumption - Synthetic Data Mode)." **Verification**: Ensure the document contains this exact sentence structure with the correct values filled in.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Checkpoint**: All tasks T001-T012 must be `[X]` before proceeding to Phase 3.

- [X] T009 Implement `src/utils/io_helpers.py` with strict CSV/Parquet I/O and checksum verification
- [X] T010 [P] **Create Structural Validation Generator**: Create `src/data/generators/structural_validation_generator.py`. **Logic**: This script generates a dataset for **Structural Validation Mode** when real data is unavailable. **Requirements**: Use Multivariate Normal distributions for continuous variables (mean=0, covariance=Identity scaled by) and Bernoulli for binary variables (p=0.5). **Explicit Column Mapping**: Generates raw fields AND derived metrics (`CSA_Index`, `Stability_Score`) to ensure the pipeline is executable. **Constraint**: Must be strictly decoupled from analysis logic (fixed seed, independent RNG). **Verification**: Run generator and validate output against `contracts/dataset.schema.yaml` including derived columns. **Output**: `data/raw/structural_validation_data.csv`.
- [X] T010a [Depends: T010, T050b] [P] **Implement CLI Orchestrator**: Create `src/cli/run_pipeline.py`. **Logic**: The script MUST accept flags (`--dry-run`). It MUST check for real data in `data/raw/`. If missing AND `CI=true`, automatically invoke `src/data/generators/structural_validation_generator.py` (T010) and then invoke `src/data/processing/feature_engineering.py` to derive metrics. If `CI=false` and real data is missing, log a warning and proceed with synthetic data for local testing. **CRITICAL GATE**: At the start of execution, the script MUST invoke `src/cli/validate_citations.py` on `research.md`. **Logic**: This check is independent of data availability. If `validate_citations.py` returns non-zero (citation failure in `research.md`), the pipeline MUST abort immediately with a clear error message, even if synthetic data is used. This ensures structural validation (citations/schema) is never bypassed, resolving the contradiction between data fallback and citation gating. **Verification**: Run `export CI=true; python src/cli/run_pipeline.py --dry-run` to confirm the generator is invoked automatically when data is missing. Verify log output contains 'Invoking structural validation generator' and exit code 0. Run a dry-run CI job to confirm the flag is passed and the generator is invoked. **Verification**: Ensure `validate_citations.py` blocks the pipeline if citations are invalid.
- [X] T010b [Depends: T010a] [P] **Configure CI Workflow**: Create `.github/workflows/ci.yml`. **Logic**: Configure the workflow to run `python src/cli/run_pipeline.py --dry-run` with `CI=true` environment variable. **Verification**: Run `act push -j build` (or equivalent) to confirm the workflow triggers the pipeline with synthetic fallback enabled.
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
- [ ] T015b [US1] [FR-001] [Depends: T003, T007, T008] **Generate Synthetic Survey Data (Structural Validation Mode)**: Implement `src/data/collectors/survey_collector.py`. **Specifics**: **Primary Source**: Real data (LSMS-ISA) is **Blocked** per plan. **Fallback**: Use `src/data/generators/structural_validation_generator.py` to generate synthetic household data. **Explicit Schema Mapping**: Generate fields: `household_id`, `latitude` (clustering around multiple centroids with a A radius of moderate scale.), `longitude`, `land_size`, `education_level`, `finance_access`, `practice_mixed_farming`, `practice_terracing`, `practice_conservation_tillage`, `practice_agroforestry`, `extension_visits`, `hlias`. **Include Caching Logic**: Check local storage, verify checksums. **Output**: Save mapped data to `data/raw/survey_raw.csv` and filtered data to `data/raw/filtered_survey.csv` (removing records with missing coordinates). **Verification**: Assert file exists and passes schema validation.
- [ ] T015c [US1] [FR-001] [Depends: T003] **Download and Map Real Survey Data (Real Path)**: Implement `src/data/collectors/survey_collector.py` logic for real LSMS-ISA data. **Specifics**: **Primary Source**: LSMS-ISA dataset for Malawi/Tanzania. **Logic**: Check if `data/raw/lsms_isa.csv` exists. If yes, load and validate schema. If no, skip this task and rely on T015b. **Verification**: Assert file exists if real data is present; assert task is skipped if not.
- [ ] T016b [US1] [FR-001] [Depends: T003] **Generate Synthetic Sentinel-2 Granules (Structural Validation Mode)**: Implement `src/data/collectors/remote_sensing_collector.py`. **Specifics**: **Primary Source**: Real data (Sentinel-2) is **Blocked** per plan. **Fallback**: Generate synthetic NDVI time-series consistent with survey data. **Logic**: Use a sinusoidal function with **stochastic noise** (standard deviation within a moderate range) to simulate NDVI time-series, ensuring a valid Coefficient of Variation (CV) can be calculated. **Metadata**: Embed `cloud_cover` metadata (ranging 0.0 to 0.9) in the generated.tif files or a sidecar JSON to enable sensitivity analysis. **Output**: `data/raw/sentinel2/synthetic_granules.tif`. **Verification**: Ensure granules with cloud cover between high and very high levels are cached. <!-- FAILED: unspecified -->
- [ ] T017b [US1] [FR-002] [Depends: T004, T015b, T015c, T016b] **Perform Spatial Join and Linkage Validation**: Implement `src/data/processing/spatial_join.py` to link household coordinates to satellite pixels. **Specifics**: **Read `buffer_size_km` from `src/config/constants.py`**. Apply a **geodesic buffer** of that size around household coordinates to handle LSMS-ISA privacy fuzzing. **Intermediate Artifact**: Generate `data/processed/buffered_coordinates.geojson`. **Verification**: Assert the buffer was applied correctly. Use `geopandas.sjoin` or `rasterio` to extract mean NDVI for the buffer area. **Output**: `data/processed/spatial_joined_data.csv`. **Mandatory Output**: Generate `data/logs/linkage_validation.json` with the schema: `linkage_percentage` (float), `total_valid_households` (int), `triggered_aggregation` (bool), `exclusion_reason` (str), `data_source_type` (str: 'Real' or 'Synthetic'). **Logic**: Calculate linkage percentage from actual data results (Real or Synthetic). If linkage < 95% or N < 300, set `triggered_aggregation` to true. Log `data_source_type` as 'Synthetic' if T015b was used, 'Real' if T015c was used. **Handle Missing Data**: If `total_valid_households` is 0, log `FATAL_NO_HOUSEHOLDS` and exit immediately. Log `MISSING_SATELLITE_DATA` for excluded regions.
- [ ] T018b [US1] [FR-003] [Depends: T017b] **Extract Raw NDVI Time-Series**: Implement `src/data/processing/feature_engineering.py` to extract **raw NDVI time-series** for each household/plot. **Logic**: Map `survey_year` + `country` to growing season months; extract raw NDVI values from satellite granules. **Synthetic Path**: If real granules are missing, generate synthetic NDVI time-series using a sinusoidal function with **stochastic noise** (std 0.1). **Output**: Save raw time-series to `data/processed/raw_ndvi_timeseries.parquet`. **Verification**: Assert file exists and contains columns `household_id`, `timestamp`, `ndvi_value`.
- [ ] T018c [US1] [FR-003] [Depends: T018b] **Calculate CSA Index and Stability Score**: Implement metric construction in `src/data/processing/feature_engineering.py`. **Logic**: Sum binary practice indicators (`practice_mixed_farming`, etc.) and `extension_visits` to create `CSA_Index`. Read `data/processed/raw_ndvi_timeseries.parquet`, compute NDVI time-series CV, and compute `Stability_Score` (1/CV). **Verification**: Assert `CSA_Index` and `Stability_Score` are calculated correctly and non-null.
- [ ] T018d [US1] [FR-003] [Depends: T018c] **Derive Village ID**: Implement village ID derivation. **Logic**: Derive `village_id` by rounding coordinates to the nearest `grid_resolution_km` grid cell using the formula: `village_id = f'{int(lat / grid_resolution_km)}_{int(lon / grid_resolution_km)}'`. **Output**: Ensure `village_id` is derived or retained in the output dataset for clustering.
- [ ] T017e [US1] [FR-002] [Constitution VII] [Depends: T018d, T017b] **Perform Final Dataset Validation and Assembly**: **Logic**: Read `data/logs/linkage_validation.json`. If `triggered_aggregation` is true, read `data/processed/feature_engineered_data.csv` (output of T018c), aggregate to village level (mean CSA_Index, mean Stability_Score), and write to `data/processed/analysis_dataset_village_aggregated.csv`. Otherwise, use `data/processed/feature_engineered_data.csv` directly. Copy the final dataset to `data/processed/analysis_dataset.csv`. **Verification**: Assert the final file exists, passes schema validation, and contains >300 records. **Mandatory Text**: Write "Geospatial fuzzing radius: {value} km (Source: Assumption - Synthetic Data Mode)" to `data/logs/linkage_validation.json` if `data_source_type` is 'Synthetic'.
- [ ] T022 [US1] [Depends: T017e, T010a] **Verify Final Dataset**: Run `src/cli/validate.py` against `data/processed/analysis_dataset.csv` to ensure it meets all schema requirements. **Verification**: Assert validation passes.
- [ ] T065 [US1] [Depends: T010a] **Unified Data Access and Execution**: Create `src/cli/verify_data_access.py`. **Logic**: Check for existence of `data/raw/` and valid credentials (environment variables) for LSMS-ISA and Sentinel-2. If real data is missing, log 'Structural Validation Mode' and proceed. If `--no-synthetic` flag is passed and real data is missing, exit with error. **Verification**: Assert the script exits 0 and logs the appropriate status.
- [ ] T090a [US1] [Depends: T065, T022] **Execute Data Pipeline**: Run `python src/cli/run_pipeline.py --ci` (or `--dry-run` for local). **Logic**: This task executes the full pipeline, triggering the structural validation generator if real data is missing. **Verification**: Assert `data/processed/analysis_dataset.csv` is generated and contains >300 records.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Statistical Analysis and Diagnostics (Priority: P2)

**Goal**: Run multivariate regression models with robust standard errors and perform collinearity diagnostics.

**Independent Test**: Execution of `src/analysis/run_regression.py` produces a summary file containing regression coefficients, p-values, and VIF scores for both Yield Stability and Food Security models, completing within 60 minutes on CPU.

### Implementation for User Story 2

- [ ] T023 [P] [Depends: T046] [US2] Write contract test skeleton for regression output in `tests/contract/test_regression_output.py` (TDD).
- [ ] T024 [P] [Depends: T046] [US2] Write integration test skeleton for model execution in `tests/integration/test_regression.py` (validates T025a).
- [ ] T025a [US2] [FR-004] [FR-005] [FR-007] [Depends: T022] **Implement Regression Logic**: Create `src/analysis/run_regression.py`. **Specifics**: Implement Model 1 (`Stability_Score ~ CSA_Index + Access_to_Finance + Controls`) and Model 2 (`HFIAS ~ CSA_Index + Access_to_Finance + Controls`). Use `statsmodels` with robust standard errors (HC3). **Verification**: Script runs without error on `analysis_dataset.csv`.
- [ ] T025b [US2] [FR-004] [FR-005] [FR-007] [Depends: T025a] **Implement Model Selection Logic**: Detect aggregation state (N_clusters == N_rows). If aggregated, use HC3 or Cluster-Robust SE; if clustered, use Cluster-Robust SE. Log appropriate warnings. **Verification**: Assert model type is correctly detected.
- [ ] T025c [US2] [FR-004] [FR-005] [FR-007] [Depends: T025b] **Implement VIF Calculation**: Calculate VIF for ALL predictors in BOTH models regardless of aggregation state. If any VIF > 5, log warning and annotate output. **Verification**: Assert VIF scores are calculated and logged.
- [ ] T025d [US2] [FR-004] [FR-005] [FR-007] [Depends: T025c] **Implement Bonferroni Correction and Write Output**: Apply standard Bonferroni correction for **3 tests** (Yield Stability, Food Security, Interaction): `adjusted_alpha = 0.05 / 3`. Write final structured results to `data/processed/regression_results.json` including fields: `adjusted_alpha`, `bonferroni_corrected_p_values`, `coefficients`, `vif_scores`, `model_type`, `collinearity_warning`, `aggregation_warning`. **Verification**: Assert `model_type` is 'aggregated' or 'clustered'. Assert that `vif_scores` are present. **Assert adjusted_alpha == 0.0167**.
- [ ] T081d [US2] [Depends: T025a] **Implement unit tests for run_regression.py**: Implement unit tests for `src/analysis/run_regression.py` (VIF calculation, model selection logic). **Specifics**: Test VIF calculation with known collinear data; test model selection logic with aggregated vs clustered data. **Verification**: Run `pytest tests/unit/` and assert all tests pass.
- [ ] T066 [US2] [Depends: T090a, T025d] **Execute Regression Analysis**: Run `src/analysis/run_regression.py` against `data/processed/analysis_dataset.csv` to produce `data/processed/regression_results.json`. **Verification**: Assert `data/processed/regression_results.json` exists, contains `coefficients`, `p_values`, `vif_scores`, and `model_type`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Sensitivity Analysis and Final Report (Priority: P3)

**Goal**: Perform sensitivity analysis on cloud cover thresholds and generate the final associational report.

**Independent Test**: Execution of `src/analysis/sensitivity_check.py` produces a plot and table showing coefficient stability across threshold sweeps, and the final report includes the observational framing disclaimer.

### Implementation for User Story 3

- [ ] T028 [P] [Depends: T046] [US3] Write contract test skeleton for sensitivity output in `tests/contract/test_sensitivity.py` (TDD).
- [ ] T029 [P] [Depends: T046] [US3] Write integration test skeleton for report generation in `tests/integration/test_report.py` (validates T087-T088).
- [ ] T087 [US3] [FR-006] [Depends: T016b, T018b] **Sensitivity Sweep and Metrics Calculation**: Implement cloud cover threshold sweep. **Sweep Range**: [0.0, 0.6, 0.7, 0.8, 0.9]. **Logic**: For each threshold, filter cached raw satellite granules (T016b) by cloud cover. Re-compute NDVI time-series and Stability_Score for each filtered subset. Re-run regression logic on the filtered subset. **Output**: Write variation in `CSA_Index` coefficient magnitude for **both Model 1 and Model 2** to `data/processed/sensitivity_results.csv` and generate `reports/sensitivity_plot.png`. **Metrics**: Calculate `max_delta_coefficient` = `max(|coeff_i - coeff_baseline|)` and `std_coefficient` = standard deviation of coefficients across thresholds. Write these metrics to `data/processed/sensitivity_metrics.json`. **Verification**: Ensure the JSON file contains the calculated metrics.
- [ ] T088 [US3] [FR-008] [Depends: T087] **Implement Report Logic**: Create `src/services/report_generator.py`. **Specifics**: Generate `reports/final_report.pdf` using reportlab. **Mandatory**: Programmatically inject the "associational" nature disclaimer, the Bonferroni adjustment method (explicitly calculating 0.05 / 3 and injecting the result), and the summary paragraph from T087 into the report footer. **Input**: Read `data/processed/sensitivity_metrics.json` generated by T087. **Text**: "Results are associational. Bonferroni-adjusted alpha = 0.0167. [UNRESOLVED-CLAIM: c_1c3d4cda — status=not_enough_info] Structural Validation Only: No scientific claims regarding the hypothesis are made due to lack of verified real-world data."
- [ ] T032 [US3] [FR-008] [Depends: T088] **Generate Final Report**: Call `src/services/report_generator.py` to generate `reports/final_report.pdf`. **Mandatory**: Programmatically inject the "associational" nature disclaimer, the Bonferroni adjustment method, and the summary paragraph. **Verification**: Assert the PDF exists and contains the required disclaimers.
- [ ] T034 [US3] Include limitations section (observational design, spatial fuzzing, sample size) in the report generator logic.
- [ ] T081e [US3] [Depends: T087] **Implement unit tests for sensitivity_check.py**: Implement unit tests for `src/analysis/sensitivity_check.py` (threshold filtering logic). **Specifics**: Test threshold filtering with known cloud cover values; test coefficient variation calculation. **Verification**: Run `pytest tests/unit/` and assert all tests pass.
- [ ] T067 [US3] [Depends: T066, T087] **Execute Sensitivity & Report Generation**: Run `src/analysis/sensitivity_check.py` and `src/services/report_generator.py` to produce `reports/sensitivity_results.csv`, `reports/sensitivity_metrics.json`, and `reports/final_report.pdf`. **Verification**: Assert all three output files exist and contain valid data/content.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `README.md`
- [ ] T037 Code cleanup and refactoring for type hints and modularity
- [ ] T038 [P] Additional unit tests in `tests/unit/` for helper functions
- [ ] T039 Security hardening (PII scan on commits, data privacy checks)
- [ ] T040 Run `quickstart.md` validation and fix any broken links

---

## Phase N+1: Research & Reproducibility (Addressing Reviewer Concerns)

**Purpose**: Address critical gaps identified in prior research-stage reviews regarding implementation completeness, data artifacts, and reproducibility. Specifically resolves the "Implementation Gap", "No Data Artifacts", "Missing Source Files", "Spec TODOs", and "Filesystem Hygiene" findings.

**Goal**: Ensure actual code, data, and results exist to validate the pipeline, resolving the "Implementation Gap", "No Data Artifacts", and "Spec TODOs" findings. **Note**: These tasks are strictly sequential and must be executed after Phase 5 is fully implemented.

- [ ] T047 [P] **Create Dependency Manifest**: Generate `requirements.txt` with pinned dependency versions (pandas, numpy, statsmodels, geopandas, rasterio, etc.).
- [ ] T048 [P] **Create Reproducibility Artifacts**: Generate `Dockerfile`, `docker-compose.yml`, and `README.md` with installation and reproduction steps.
- [ ] T051 [P] **Filesystem Hygiene Check**: Verify all files are in correct locations per `plan.md` (e.g., `specs/001-climate-smart-eval/` for specs, `src/` for code, `contracts/` for schemas).
- [ ] T052 [P] **Data Provenance Documentation**: Create `data/raw/.provenance.yaml` documenting source URLs, download timestamps, API versions, and license/attribution for all raw data.
- [ ] T054 [P] **Missing Data Strategy**: Document missing value imputation and outlier detection strategies in `data-model.md` and implement in `src/data/processing/`.
- [ ] T055 [P] **Final Verification**: Re-run all integration tests against the newly generated artifacts to confirm the pipeline is reproducible from a clean checkout.

---

## Phase N+3: Implementation Completeness & Artifact Generation (Addressing "No Data" and "Missing Code" Reviews)

**Purpose**: Directly address the critical "No Data Artifacts", "Missing Source Files", and "Implementation Gap" findings from the research reviews. These tasks mandate the actual execution of the pipeline to generate the required data and results, ensuring the project is not just a design document.

**Goal**: Generate the `data/processed/analysis_dataset.csv`, `data/processed/regression_results.json`, and `reports/final_report.pdf` artifacts in a reproducible CI environment, and verify the existence of all source files listed in the plan.

- [ ] T068 [P] **Verify Source Code Completeness**: Run a script `scripts/verify_source_structure.py` that checks for the existence of all files listed in `plan.md` (e.g., `src/data/collectors/survey_collector.py`, `src/analysis/run_regression.py`, `tests/contract/`, etc.). **Verification**: Script exits 0 only if all required files exist and are non-empty.
- [ ] T069 [P] **Verify Test Execution**: Run `pytest` to ensure all generated test skeletons (T013-T029) have corresponding implementations that pass. **Verification**: `pytest` returns exit code 0.
- [ ] T074 [P] **Address "No Data" Review**: Create `data/raw/.provenance.yaml` with actual download timestamps, source URLs, and checksums for the data used in T090a. **Logic**: If real data (LSMS-ISA) was used, record its URL and checksum. If synthetic data (Structural Validation Mode) was used, record the generator script ID, seed, and a clear label "Synthetic Data - Structural Validation". **Verification**: File exists and contains valid YAML with required fields and appropriate source labeling.
- [ ] T075 [P] **Verify Contract Compliance**: Run `src/cli/validate.py` against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` to ensure they are valid and match the generated data. **Verification**: Validation passes against existing contracts (no re-generation).
- [ ] T076 [P] **Address "Missing Docker" Review**: Create `Dockerfile` and `docker-compose.yml` as specified in T055 (now re-verified) and verify `docker build` succeeds. **Verification**: Docker image builds successfully.
- [ ] T077 [P] **Address "Missing README" Review**: Update `README.md` with installation, data access, and execution instructions, ensuring it references the newly generated artifacts. **Verification**: README.md exists and contains all required sections.

---

## Phase N+4: Critical Review Remediation (Addressing "Implementation Gap" and "No Data Artifacts")

**Purpose**: Directly address the severe implementation gaps identified in the research reviews (specifically `research_reviewer__2026-04-30__research.md`, `research_reviewer_code_quality_research__2026-04-30__research.md`, and `research_reviewer_implementation_completeness__2026-04-30__research.md`). These tasks are mandatory to resolve the "Full Revision" verdicts by ensuring the codebase matches the design.

**Goal**: Verify and patch the existing source code, test files, and data artifacts that were previously missing despite being marked as complete in the tasks list. **Note**: This phase does NOT re-implement T015-T035; it verifies and patches them.

- [ ] T081a [P] **Implement Contract Tests**: Implement `tests/contract/test_dataset_schema.py`, `tests/contract/test_regression_output.py`, and `tests/contract/test_sensitivity.py`. **Specifics**: Assert columns/keys exist and have correct types/values. **Verification**: Run `pytest tests/contract/` and assert tests pass with valid data.
- [ ] T081b [P] **Implement Integration Tests**: Implement `tests/integration/test_ingestion.py`, `tests/integration/test_regression.py`, and `tests/integration/test_report.py`. **Specifics**: Assert end-to-end flow generates correct artifacts. **Verification**: Run `pytest tests/integration/` and assert tests pass with valid data.
- [ ] T081c [P] **Implement Unit Tests**: Implement `tests/unit/test_feature_engineering.py`, `tests/unit/test_run_regression.py`, and `tests/unit/test_sensitivity_check.py`. **Specifics**: Test specific logic (CSA Index, VIF, Threshold filtering). **Verification**: Run `pytest tests/unit/` and assert all tests pass.
- [ ] T090a [P] **Execute Data Pipeline**: Run `python src/cli/run_pipeline.py --ci`. **Verification**: Assert exit code is 0.
- [ ] T091 [P] **Verify Artifacts**: Verify `data/processed/analysis_dataset.csv`, `data/processed/regression_results.json`, and `reports/final_report.pdf` are generated and valid. **Verification**: Assert all three files exist, contain valid data (non-empty, schema-compliant), and have >300 records for the dataset.
- [ ] T092 [P] **Verify Final Report**: Run `src/cli/validate.py` against `reports/final_report.pdf`. **Verification**: Assert exit code 0 and file contains required disclaimers and sensitivity analysis results.
- [ ] T093 [P] **Resolve Spec TODOs**: Scan `spec.md` and `plan.md` for any remaining `_TODO:` markers and resolve them. **Logic**:
 - If a TODO is found, update the document with the required content (e.g., "measurable outcomes", "Functional Requirements").
 - Run `scripts/validate_spec_todos.py` to confirm no TODOs remain.
 **Verification**: Script exits with code 0.
- [ ] T094 [P] **Verify Filesystem Hygiene**: Ensure all files are in the correct locations as per `plan.md`. **Specifics**:
 - Move `spec.md`, `plan.md`, `tasks.md` to `specs/001-climate-smart-eval/` if currently in root.
 - Ensure `contracts/` is at project root.
 - Ensure `src/`, `tests/`, `data/`, `reports/` are at project root.
 **Verification**: Run `scripts/verify_filesystem_hygiene.py` to confirm structure.
- [ ] T095 [P] **Verify Test Execution**: Run `pytest` to ensure all tests pass. **Verification**: `pytest` returns exit code 0.
- [ ] T096 [P] **Verify Docker Build**: Run `docker build` to ensure the image builds successfully. **Verification**: Docker image builds successfully.
- [ ] T097 [P] **Verify README Completeness**: Check `README.md` for installation, data access, and execution instructions. **Verification**: README.md exists and contains all required sections.

---

## Phase N+5: Final Verification & Gate Compliance (Addressing "No Data" and "Missing Code" Reviews)

**Purpose**: Ensure all critical reviewer concerns regarding missing data, missing code, and missing tests are definitively resolved before closing the revision cycle.

**Goal**: Verify that the project now contains all required artifacts, code, and tests, and that the pipeline executes successfully with real or synthetic data as appropriate.

- [ ] T090b [P] **Verify Data Artifact Generation**: Run `src/cli/validate.py` against `data/processed/analysis_dataset.csv`. **Verification**: Assert exit code 0 and file contains >300 records.
- [ ] T091 [P] **Verify Regression Results Generation**: Run `src/cli/validate.py` against `data/processed/regression_results.json`. **Verification**: Assert exit code 0 and file contains `coefficients`, `p_values`, `vif_scores`, and `model_type`.
- [ ] T092 [P] **Verify Final Report Generation**: Run `src/cli/validate.py` against `reports/final_report.pdf`. **Verification**: Assert exit code 0 and file contains required disclaimers and sensitivity analysis results.
- [ ] T099 [P] **Verify Final System Integrity**: Run `scripts/verify_task_completion.py` to perform a comprehensive check of all source files, tests, hygiene, and artifacts. **Logic**: This task consolidates T093-T099 from the original plan. It verifies: (1) All source files exist (T093), (2) All tests pass (T095), (3) Filesystem hygiene (T094), (4) Spec TODOs resolved (T093), (5) Docker build success (T096), (6) README completeness (T097), (7) Gate compliance (T090b-T092). **Verification**: Script exits with code 0 only if all checks pass.