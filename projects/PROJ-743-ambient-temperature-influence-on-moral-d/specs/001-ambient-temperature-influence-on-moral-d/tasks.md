# Tasks: Ambient Temperature Influence on Moral Decision Speed

**Input**: Design documents from `/specs/001-ambient-temp-moral-speed/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Data Availability & Validation (CRITICAL BLOCKER)

**Purpose**: Verify data sources, download, and validate resolution standards before any ingestion or modeling can occur.

**⚠️ CRITICAL**: No other tasks can begin until Phase 0 is complete and the data gap is resolved.

- [X] T001 [P] Verify the canonical URL for the Copernicus Climate Data Store (CDS) API for ERA hourly data and confirm accessibility (HTTP 200) using the `cdsapi` library configuration. Log the verification result (including API endpoint and status) to `results/logs/data_quality_log.txt`.
- [X] T001a [P] **Validate Moral Machine Source**: Verify the canonical URL for the Moral Machine dataset against the "Verified Accuracy" principle. Confirm the dataset exists, is accessible, and contains the required columns: `latitude` (float), `longitude` (float), `timestamp` (datetime), `response_time` (float), `country` (string), `dilemma_id` (string). **URL**: `. Log the validation status (Pass/Fail) and column schema to `results/logs/data_validation_log.txt`. **(FR-014, Constitution Principle II)**.
- [ ] T001b **Ingest & Validate ERA5 Sample**: Write a Python script `code/validate_era5.py` to fetch a **specific sample subset** for validation: **Jan, 2016 to Jan 7, 2016** in **London (N, -0.1W)**. Execute this script to fetch the sample to `data/raw/era_sample.h5`. Verify the sample contains hourly resolution and valid temperature values. Log success/fail to `results/logs/data_validation_log.txt`. **(FR-014, US-1)**.
- [X] T001c [P] **Validate ERA5 Citation (Verified Accuracy)**: Implement logic in `code/validate_sources.py` to verify the ERA5 data source against Constitution Principle II. **Action**: Use `cdsapi` to fetch the primary source metadata for ERA5 (product name, temporal coverage, spatial resolution) and log the specific metadata fields (e.g., `product_type`, `variable`, `grid_resolution`) to verify they match the claims in `plan.md`. Compute a "metadata match score" (Pass/Fail) based on exact string matching of key attributes (e.g., "2m temperature", "0.25 deg"). Log the score and validation status (Pass/Fail) to `results/logs/data_validation_log.txt`. **(Constitution Principle II, FR-014)**.
- [ ] T002 [P] **Derive Bounding Box**: Write a script `code/derive_bbox.py` to load the Moral Machine dataset (or a sample thereof) and calculate the exact geographic bounding box (min/max lat/lon) required for the ERA5 fetch. Output the bounding box to `data/external/bounding_box.json`. **(Executability Fix)**.
- [ ] T002b **Fetch ERA5 Logic**: Write a Python script `code/fetch_era_full.py` to fetch the **full -2018 ERA5 2m temperature dataset** required for the primary analysis. The script MUST:
 1. Read the bounding box from `data/external/bounding_box.json` (T002).
 2. **Filter**: Only request tiles that overlap with this bounding box.
 3. **Parameters**: Variable `2t` (2m temperature), Time range `2014-01-01` to `2018-12-31`, Product type `reanalysis`, Grid resolution `0.25` (approx 25km).
 4. **Chunking**: Implement chunking by **10x10 degree tiles** (latitude/longitude ranges) to avoid single-call timeout and memory overflow.
 5. Stream data to disk in chunks to stay within the available RAM limit.
 6. Include **retry logic** for CDS API rate limits (exponential backoff).
 **Output**: Save to `data/raw/era5_full.h5`. **(FR-001)**.
- [ ] T002b_test **Unit Tests for Fetcher**: Write unit tests in `tests/test_ingestion.py` for `code/fetch_era_full.py` logic. **Specifics**: Test function `test_chunking_strategy` asserts `chunk_count == expected` where `expected` is calculated based on the spatial resolution of the grid, determined by dividing the latitude and longitude ranges by a configurable cell size parameter. **Assumption**: Bounding box coordinates are in degrees and tile size is fixed at a constant value. Test `test_merge_logic` asserts `final_file.shape == expected_shape`. **(Executability Fix)**.
- [ ] T002c **Execute Fetch**: Execute the script from T002b to fetch the full dataset. **Execution Logic**: Run `fetch_era_full.py` which must fetch by year and tile (2014‑2018), merge results, and save to `data/raw/era5_full.h5`. Log success/fail to `results/logs/data_validation_log.txt`. **Dependencies**: T002, T002b, T002b_test.
- [ ] T002d **Checksum ERA5**: Compute and record the SHA-256 checksum of the downloaded full ERA5 file (`data/raw/era5_full.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_full`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V. **(FR-014, Principle V)**.
- [ ] T003 **Checksum Sample**: Compute and record the SHA-256 checksum of the downloaded ERA5 sample file (`data/raw/era5_sample.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_sample`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [ ] T004 **Validate ERA5 Sample**: Programmatically validate that the downloaded ERA5 sample meets the hourly temporal resolution and geographic grid size standards defined in FR-014. Log validation status (Pass/Fail) to `results/logs/data_validation_log.txt`.
- [ ] T005 **Verify Moral Machine Source**: Verify the Moral Machine dataset source against the "Verified Accuracy" principle and log the validation status to `results/logs/data_validation_log.txt` using a standardized format: "Source: <name>, Status: <Pass/Fail>".
- [ ] T006 **Pre-Ingestion Validation Gate**: Implement a final check task that aggregates results from T001-T005. **Mechanism**: Read JSON log files from T001a, T001c, T004, T005 and check file existence for T002c. If ANY source validation (ERA5 or Moral Machine) fails, this task MUST raise an exception and abort the pipeline. Log the final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`. **Dependencies**: T001-T005.

**Checkpoint**: Data validation complete. If Pass, proceed to Phase 1. If Fail, project is blocked.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T007 Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`
- [X] T008 Initialize a Python project with dependencies (pandas, numpy, scikit-learn, statsmodels, cdsapi, pyarrow, matplotlib, seaborn, geopandas, huggingface_hub).
- [ ] T009 Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T010 Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** distance thresholds (default distance, with parameters for shorter and longer ranges in sensitivity analysis).
- [ ] T010b **Calculate Temperature Thresholds**: Write a script `code/calc_thresholds.py` to load a sample of the Moral Machine dataset and calculate the 1st and 99th percentile of the `temperature` column (once merged with a sample of ERA5). Output the calculated thresholds to `config.py`.
- [ ] T011 Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`
- [ ] T012 Implement checksum generation and verification for `data/raw/` and `data/processed/` files in `code/utils.py`
- [ ] T013 Create data loading utilities in `code/loaders.py` using `polars` or `pandas` with `chunksize` parameter for memory mapping. Implement function `load_chunked_parquet(path, chunk_size)` to handle large Parquet ingestion without memory overflow.
- [ ] T013a **Define Anderson-Darling Sample Size**: Explicitly define the sampling fraction for the Anderson-Darling test in `code/config.py` (e.g., 0.1). Document the specific sampling fraction in `docs/research.md`.
- [ ] T014 Setup unit test framework (pytest) with configuration for CPU-only execution and stratified sampling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 Unit test for location validation and exclusion logic in `tests/test_ingestion.py`
- [ ] T016 Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`.

### Implementation for User Story 1

- [ ] T017 [US1] **Load, Filter & Count**: Implement `code/ingestion.py` to:
 1. Define numeric thresholds in `code/config.py`.
 2. Load the Moral Machine dataset from `data/raw/moral_machine.csv.gz`.
 3. **Count 1**: Count the total number of records with valid latitude and longitude. Log this as `count_total_valid_location`.
 4. **Filter 1**: Filter out records with missing location data.
 5. **Filter 2**: Filter out records with impossible response times (<100ms or >10,000ms).
 6. **Filter 3**: Filter out records with temperature values outside the range defined in `code/config.py`.
 7. **Count 2**: Count the number of records remaining after all filters. Log this as `count_filtered_for_analysis`.
 8. Log excluded records to `results/logs/exclusion_log.csv` in CSV format. **(FR-002)**.
- [ ] T018 [US1] **Define Logic**: Implement the **logic** for ERA5 Reanalysis data fetching, geospatial matching, and merging in `code/ingestion.py` using the CDS API. This task defines the functions but does NOT execute them. **Dependencies**: T002, T001, T001a, T001c.
- [ ] T018b [US1] **Load and Merge** the full dataset. **Action**: Load the pre-fetched ERA5 data from `data/raw/era5_full.h5` (produced by T002c) and merge it with Moral Machine data (from T017). **Output**: Save merged dataset to `data/processed/merged_dataset.parquet`. **Dependencies**: T018, T002d, T017, T028a.
- [ ] T019 [US1] **Geospatial Matching**: Implement geospatial matching logic in `code/ingestion.py` to link Moral Machine records to nearest ERA5 grid within 100km threshold. Explicitly flag records >100km by setting `match_quality` to 'low' and logging the reason "distance > 100km" to `results/logs/data_quality_log.json` before exclusion (FR-009). **Output**: Add a column `era5_grid_id` to the dataset. **Dependencies**: T018b, T018.
- [ ] T019b [US1] **Primary Exclusion Filter**: Implement in `code/ingestion.py`. Exclude records where `match_quality` == 'low' or where time gaps exceed limits. Log exclusions. **Dependencies**: T019, T020.
- [ ] T019c [US1] **Create Data Quality Log**: Initialize and structure `results/logs/data_quality_log.json`. Dependencies: T019, T020, T019b.
- [ ] T020 [US1] **Time-based Interpolation**: Implement time-based interpolation for missing ERA5 hourly values (linear interpolation only if gap ≤ 2 hours). Flag records with larger gaps without exclusion.. Dependencies: T018b, T019.
- [ ] T022 [US1] **Generate and verify output** to save merged dataset to `data/processed/merged_dataset.parquet`. Dependencies: T019b, T020, T018b.
- [ ] T022a [US1] **Calculate Match Success Rate**: Compute the percentage of Moral Machine records successfully matched with ERA5 temperature data (SC-001). Input: Read `count_total_valid_location` from T017 and `count_matched_pre_exclusion` from T018b.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [US2] Unit test for log‑transformation and outlier handling in `tests/test_modeling.py`
- [ ] T024 [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `code/modeling.py` to perform log-transformation of response times and handle non-convergence by switching to GLMM (FR-003). Dependencies: T022.
- [ ] T026 [US2] **Primary Model**: Fit a linear mixed-effects model with log-transformed response time, temperature as fixed effect, random intercepts for participant ID and cultural region.. Dependencies: T025, T028b, T028c, T028d, T028a, T028e, T022.
- [ ] T027 [US2] Implement likelihood-ratio test to assess statistical significance (FR-005). Dependencies: T026.
- [ ] T028 [US2] Generate diagnostic plots for model residuals to verify normality and homoscedasticity assumptions (FR-007). Dependencies: T026.

**Checkpoint**: User Story 2 should be fully functional and testable independently

---

## Phase 3: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [ ] T029 Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`
- [ ] T030 Integration test for robustness summary table generation in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/robustness.py` to calculate alternative temperature metrics and re-run modeling (FR-006)
- [ ] T032 [US3] Perform sensitivity analysis on temperature thresholds (FR-006).
- [ ] T033 [US3] Implement confound analysis for indoor/outdoor effects. Dependencies: T028e.

**Checkpoint**: User Story 3 should be fully functional and testable independently

---

## Phase 4: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Address the absence of baseline data and arousal proxies by documenting them as limitations, as required by the spec's assumptions, and quantifying the noise floor via observed variance.

**Independent Test**: Verify that the results log explicitly states the inability to control for baseline reaction time and physiological arousal, and includes the quantified variance of individual differences from the model.

### Implementation for Limitations

- [ ] T034 Draft limitations section in `results/logs/limitations.md`.
- [ ] T035 Extract random intercept variance to quantify noise floor. Dependencies: T028e, T034.

**Checkpoint**: Review concerns acknowledged, theoretical impact quantified, and future work proposed.

---

## Phase 5: Review-Driven Methodological Constraint Documentation (Priority: P3 - Revision)

**Goal**: Explicitly document the inability to implement the reviewer's proposed "pre‑test baseline" and "physiological proxy" methods due to the fixed nature of the Moral Machine dataset, and formally state this as a hard limitation in the research output.

### Implementation for Review Resolution
- [ ] T036 Document methodological constraints in `results/logs/limitations.md`. Dependencies: T035.

**Checkpoint**: All reviewer suggestions regarding data collection are formally documented as infeasible, closing the loop on the review.

---

## Phase 6: Review-Driven Feasibility Report (Priority: P3 - Revision)
**Goal**: Produce a final, consolidated feasibility report that synthesizes the data constraints, the quantified noise floor, and the explicit rejection of proposed data-collection methods, ensuring the project's conclusions are scientifically sound given the limitations.

### Implementation for Feasibility Report
- [ ] T037 Generate feasibility report based on previous steps. Dependencies: T036.

**Checkpoint**: Feasibility report complete, providing a clear, documented basis for the project's conclusions and limitations.

---

## Phase 7: Covariate Preparation (Priority: P2 - Pre-Merge)

**Goal**: Fetch and prepare external covariates (World Bank, Urban/Rural) before the final merge.

- [ ] T028a [US2] **Check and Fetch Covariates**: Fetch external demographic and urban/rural data from verified sources (e.g., World Bank API) for the countries in the dataset. **Dependencies**: T007.
- [ ] T028b [US2] **Derivation of Dilemma Choice**: Implement logic to derive the dilemma choice variable from the raw data. **Dependencies**: T022.
- [ ] T028c [US2] **Derivation of Dilemma Complexity**: Implement logic to derive the dilemma complexity score. **Dependencies**: T022.
- [ ] T028d [US2] **Derivation of Time-of-Day**: Implement logic to derive time-of-day from timestamps. **Dependencies**: T022.
- [ ] T028e [US2] **Verify Covariate Integrity**: Validate all derived and fetched covariates for completeness and correctness. **Dependencies**: T028a, T028b, T028c, T028d.

---

## Phase 8: Advanced Modeling & Diagnostics (Priority: P2)

**Goal**: Perform non-linearity tests and export results.

- [ ] T029 [US2] **Likelihood-ratio test**: Compare full model vs null model. **Dependencies**: T026.
- [ ] T030a [US2] **Diagnostic plot generation**: Generate QQ-plots and residual vs fitted plots. **Dependencies**: T026.
- [ ] T031 [US2] **Non-Linearity Test**: Test for quadratic effects or splines. **Dependencies**: T026.
- [ ] T032 [US2] **Export model coefficients**: Save model results to `results/stats/model_results.json`. **Dependencies**: T026, T031.

---

## Phase 9: Robustness & Sensitivity (Priority: P3)

**Goal**: Execute sensitivity analyses and robustness checks.

- [ ] T033 [US3] **Unit test for sensitivity analysis**: Test threshold sweeping logic. **Dependencies**: T035.
- [ ] T034 [US3] **Integration test for robustness**: Test robustness summary table generation. **Dependencies**: T035.
- [ ] T035 [US3] **Implement robustness**: Implement robustness scripts. **Dependencies**: T022.
- [ ] T035b [US3] **Distance Sensitivity Analysis**: Test varying distance thresholds. **Dependencies**: T019b, T026.
- [ ] T036 [US3] **Sensitivity analysis**: Run sensitivity analysis on thresholds. **Dependencies**: T035.
- [ ] T037 [US3] **Indoor/Outdoor Confound Analysis**: Analyze urban/rural stratification. **Dependencies**: T022.

---

## Phase 10: Limitations & Reporting (Priority: P3)

**Goal**: Document limitations, quantify noise, and generate final reports.

- [ ] T040 [US3] **Draft Limitations**: Draft the limitations section. **Dependencies**: T026, T041.
- [ ] T041 [US3] **Extract random intercept variance**: Quantify noise floor. **Dependencies**: T032.
- [ ] T043 [US3] **Update Limitations for Review**: Update limitations with review feedback. **Dependencies**: T040, T041.
- [ ] T045 [US3] **Document Baseline Limitation & Quantify Noise**: Finalize baseline limitation and noise quantification. **Dependencies**: T041, T040.
- [ ] T045b [US3] **Document Baseline Limitation Disclaimer**: Add specific disclaimer. **Dependencies**: T041.
- [ ] T046 [US3] **Document Methodological Constraints**: Document constraints. **Dependencies**: T043, T045.
- [ ] T047 [US3] **Generate Feasibility Report**: Generate final report. **Dependencies**: T043, T045, T046.
- [ ] T048 [US3] **Documentation updates**: Update all documentation. **Dependencies**: T047.
- [ ] T049 [US3] **Code cleanup**: Clean up code. **Dependencies**: T048.
- [ ] T050 [US3] **Performance optimization**: Optimize performance. **Dependencies**: T049.
- [ ] T051 [US3] **Additional unit tests**: Add additional tests. **Dependencies**: T049.