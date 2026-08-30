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

- [X] T001 [P] **Verify Data Sources**: Verify the canonical URL for the Copernicus Climate Data Store (CDS) API for ERA hourly data and confirm accessibility (HTTP 200) using the `cdsapi` library configuration. **AND** Verify the canonical URL for the Moral Machine dataset: `https://osf.io/...` (OSF). Confirm the dataset exists, is accessible, and contains the required columns: `latitude` (float), `longitude` (float), `timestamp` (datetime), `response_time` (float), `country` (string), `dilemma_id` (string). Log the validation status (Pass/Fail) and column schema to `results/logs/data_validation_log.txt`. **(FR-014, Constitution Principle II)**.
- [X] T001c [P] **Validate ERA5 Citation (Verified Accuracy)**: Implement logic in `code/validate_sources.py` to verify the ERA5 data source against Constitution Principle II. **Action**: Use `cdsapi` to fetch the primary source metadata for ERA5 (product name, temporal coverage, spatial resolution) and log the specific metadata fields (e.g., `product_type`, `variable`, `grid_resolution`) to verify they match the claims in `plan.md`. Compute a "metadata match score" (Pass/Fail) based on exact string matching of key attributes (e.g., "2m temperature", "0.25 deg"). Log the score and validation status (Pass/Fail) to `results/logs/data_validation_log.txt`. **(Constitution Principle II, FR-014)**.
- [ ] T001b [P] **Ingest & Validate ERA5 Sample**: Write a Python script `code/validate_era5.py` to fetch a **specific sample subset** for validation: **Jan 1, 2016 to Jan 7, 2016** in **London (51.5074, -0.1278)**. Execute this script to fetch the sample to `data/raw/era_sample.h5`. Verify the sample contains hourly resolution and valid temperature values. Log success/fail to `results/logs/data_validation_log.txt`. **(FR-014, US-1)**.
- [X] T002 [P] **Derive Bounding Box**: Write a script `code/derive_bbox.py` to load the Moral Machine dataset (or a sample thereof) and calculate the exact geographic bounding box (min/max lat/lon) required for the ERA5 fetch. Output the bounding box to `data/external/bounding_box.json`. **(Executability Fix)**.
- [X] T002b [P] **Fetch ERA5 Logic**: Write a Python script `code/fetch_era_full.py` to fetch the **full multi-year ERA5 2m temperature dataset** required for the primary analysis. The script MUST:
 1. Read the bounding box from `data/external/bounding_box.json` (T002).
 2. **Filter**: Only request tiles that overlap with this bounding box using `shapely.geometry.box`.
 3. **Parameters**: Variable `2t` (2m temperature), Time range `2014-01-01` to `2018-12-31`, Product type `reanalysis`, Grid resolution `0.25` (approx 25km).
 4. **Chunking**: Implement chunking by **10x10 degree tiles** (latitude/longitude ranges) to avoid single-call timeout and memory overflow.
 5. Stream data to disk in chunks to stay within the available RAM limit.
 6. Include **retry logic with exponential backoff** for CDS API rate limits.
 **Output**: Save to `data/raw/era5_full.h5`. **Verification**: After execution, verify `data/raw/era5_full.h5` exists, has file size > 0, and contains at least one row of data. **(FR-001)**.
- [ ] T002b_test [P] **Unit Tests for Fetcher**: Write unit tests in `tests/test_ingestion.py` for `code/fetch_era_full.py` logic. **Specifics**: Test function `test_chunking_strategy` asserts `chunk_count == expected` where `expected = ceil((max_lat - min_lat) / 10) * ceil((max_lon - min_lon) / 10)`. Test `test_merge_logic` asserts `final_file.shape == expected_shape`. **(Executability Fix)**.
- [ ] T002c [P] **Execute Fetch**: Execute the script from T002b to fetch the full dataset. **Execution Logic**: Run `fetch_era_full.py` which must fetch by year and tile (2014‑2018), merge results, and save to `data/raw/era5_full.h5`. Log success/fail to `results/logs/data_validation_log.txt`. **Dependencies**: T002, T002b, T002b_test. **Verification**: If T002b_test is skipped, verify `data/raw/era5_full.h5` exists, size > 0, and row count > 0.
- [ ] T002d [P] **Checksum ERA5**: Compute and record the SHA-256 checksum of the downloaded full ERA5 file (`data/raw/era5_full.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_full`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V. **(FR-014, Principle V)**.
- [ ] T003 [P] **Checksum Sample**: Compute and record the SHA-256 checksum of the downloaded ERA5 sample file (`data/raw/era5_sample.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_sample`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [X] T004 [P] **Validate ERA5 Sample**: Programmatically validate that the downloaded ERA5 sample meets the hourly temporal resolution and geographic grid size standards defined in FR-014. Log validation status (Pass/Fail) to `results/logs/data_validation_log.txt`.
- [X] T006 [P] **Pre-Ingestion Validation Gate**: Implement a final check task that aggregates results from T001, T001c, T004. **Mechanism**: Read JSON log files and check file existence for T002c. If ANY source validation (ERA5 or Moral Machine) fails, this task MUST raise an exception and abort the pipeline. Log the final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`. **Dependencies**: T001, T001c, T004, T002c.

**Checkpoint**: Data validation complete. If Pass, proceed to Phase 1. If Fail, project is blocked.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T007 [P] Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`
- [X] T008 [P] Initialize a Python project with dependencies (pandas, numpy, scikit-learn, statsmodels, cdsapi, pyarrow, matplotlib, seaborn, geopandas, huggingface_hub, shapely).
- [ ] T009 [P] **Configure Linting and Formatting**: Create standard configuration files: `pyproject.toml` (for Black and Ruff configuration sections) and `ruff.toml` (if separate config is preferred). **Verification**: Run `ruff check .` and `black --check .` successfully without errors. **(Executability Fix)**.
- [ ] T009b [P] **Generate Data Model Contracts**: Create the `contracts/` directory and generate contract definitions for the data models (Moral Response, Temperature Record, Merged Dataset) and API interfaces. **(Plan Structure Fix)**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T010 [P] Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** thresholds:
 1. `DISTANCE_THRESHOLD_KM` (default 100).
 2. `TEMPERATURE_MIN` (e.g., -50.0) and `TEMPERATURE_MAX` (e.g., 60.0) for FR-002 filtering.
 3. `RESPONSE_TIME_MIN_MS` (100) and `RESPONSE_TIME_MAX_MS` (10000) for FR-010 filtering.
 **(Executability Fix)**.
- [ ] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`
- [ ] T012 [P] Implement checksum generation and verification for `data/raw/` and `data/processed/` files in `code/utils.py`
- [ ] T013 [P] Create data loading utilities in `code/loaders.py` using `polars` or `pandas` with `chunksize` parameter for memory mapping. Implement function `load_chunked_parquet(path, chunk_size)` to handle large Parquet ingestion without memory overflow.
- [ ] T013a [P] **Define Anderson-Darling Sample Size**: Explicitly define the sampling fraction for the Anderson-Darling test in `code/config.py` as **0.1**. Document the specific sampling fraction in `docs/research.md`.
- [ ] T014 [P] Setup unit test framework (pytest) with configuration for CPU-only execution and stratified sampling
- [ ] T028a [P] **Check and Fetch Covariates**: Fetch external demographic and urban/rural data from **World Bank API** for the countries in the dataset. **Verification**: Explicitly verify the presence of 'age' and 'gender' fields in the API response schema. **Logic**: If fields exist, merge to dataset by 'country_code' and save to `data/processed/covariates.csv`. If fields are missing, log the specific missing fields to `results/logs/covariate_status.json` and proceed to T033 (Limitations) without blocking. **(FR-004, Assumptions)**. **Dependencies**: T007.
- [ ] T028b [P] **Derivation of Dilemma Choice**: Implement logic to derive the dilemma choice variable from the raw data. Save to `data/processed/dilemma_choices.csv`. **Dependencies**: T022 (merged into T018b).
- [ ] T028c [P] **Derivation of Dilemma Complexity**: Implement logic to derive the dilemma complexity score. Save to `data/processed/dilemma_complexity.csv`. **Dependencies**: T022 (merged into T018b).
- [ ] T028d [P] **Derivation of Time-of-Day**: Implement logic to derive time-of-day from timestamps. Save to `data/processed/time_of_day.csv`. **Dependencies**: T022 (merged into T018b).
- [ ] T028e [P] **Verify Covariate Integrity**: Validate all derived and fetched covariates for completeness and correctness. **Dependencies**: T028a, T028b, T028c, T028d.
- [ ] T028f [P] **Derive Dilemma Choice for Model**: Ensure 'dilemma_choice' is derived and available as a fixed effect. **Action**: Merge 'dilemma_choice' (from T028b) into the main processing pipeline. **Dependencies**: T022 (merged into T018b).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`
- [ ] T016 [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`.

### Implementation for User Story 1

- [ ] T017 [US1] **Load, Filter & Count**: Implement `code/ingestion.py` to:
 1. Define numeric thresholds in `code/config.py`.
 2. Load the Moral Machine dataset from `data/raw/moral_machine.csv.gz`.
 3. **Count 1**: Count the total number of records with valid latitude and longitude. Log this as `count_total_valid_location` to `results/logs/counts.json`.
 4. **Filter 1**: Filter out records with missing location data.
 5. **Filter 2**: Filter out records with impossible response times (<100ms or >10,000ms).
 6. **Filter 3**: Filter out records with temperature values outside the range defined in `code/config.py` (TEMPERATURE_MIN/MAX from T010).
 7. **Count 2**: Count the number of records remaining after all filters. Log this as `count_filtered_for_analysis` to `results/logs/counts.json`.
 8. Log excluded records to `results/logs/exclusion_log.csv` in CSV format. **(FR-002)**. **Dependencies**: T010.
- [ ] T018b [US1] **Load and Merge** the full dataset. **Action**: Load the pre-fetched ERA5 data from `data/raw/era5_full.h5` (produced by T002c) and merge it with Moral Machine data (from T017). **Verification**: Verify the merged file `data/processed/merged_dataset.parquet` exists, size > 0, and row count > 0. **Output**: Save merged dataset to `data/processed/merged_dataset.parquet`. **Dependencies**: T002c, T017.
- [ ] T019 [US1] **Geospatial Matching & Exclusion**: Implement geospatial matching logic in `code/ingestion.py` to link Moral Machine records to nearest ERA5 grid within 100km threshold. Explicitly flag records >100km by setting `match_quality` to 'low' and logging the reason "distance > 100km" to `results/logs/data_quality_log.json` before exclusion (FR-009). **Output**: Add a column `era5_grid_id` to the dataset and exclude low-quality matches. **Dependencies**: T018b.
- [ ] T020 [US1] **Time-based Interpolation**: Implement time-based interpolation for missing ERA5 hourly values (linear interpolation only if gap ≤ 2 hours). Flag records with larger gaps without exclusion. **Dependencies**: T019.
- [ ] T022a [US1] **Calculate Match Success Rate**: Compute the percentage of Moral Machine records successfully matched with ERA5 temperature data (SC-001). Input: Read `count_total_valid_location` and `count_matched_pre_exclusion` from `results/logs/counts.json` (generated by T017/T018b). **Dependencies**: T018b.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [US2] Unit test for log‑transformation and outlier handling in `tests/test_modeling.py`
- [ ] T024 [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `code/modeling.py` to perform log-transformation of response times. **Fallback Logic**: If optimization fails after a limited number of iterations or convergence code != 0, switch to GLMM with **log-link function and Gamma family**. **(FR-003)**. **Dependencies**: T018b, T028a, T028b, T028c, T028d, T028f.
- [ ] T026 [US2] **Primary Model**: Fit a linear mixed-effects model (or GLMM from T025) with log-transformed response time, temperature as fixed effect, random intercepts for participant ID and cultural region. **Fixed Effects**: Temperature, Age (if available), Gender (if available), Dilemma Complexity, Time-of-Day, **Dilemma Choice** (from T028f). **Dependencies**: T025, T028a, T028b, T028c, T028d, T028f, T018b.
- [ ] T027 [US2] **Primary Likelihood-Ratio Test**: Implement likelihood-ratio test to assess statistical significance (FR-005) for the **primary model**. Log results to `results/stats/model_results.json`. **(SC-002)**. **Dependencies**: T026.
- [ ] T028 [US2] **Primary Diagnostic Plots**: Generate diagnostic plots for model residuals (QQ-plot, residual vs fitted) to verify normality and homoscedasticity assumptions (FR-007). Save to `results/figures/`. **(SC-005)**. **Dependencies**: T026.
- [ ] T028b [US2] **Execute Anderson-Darling Test**: Run the Anderson-Darling test on a random [deferred] sample (from T013a) of model residuals. Log the p-value to `results/logs/ad_test.json`. **(SC-005)**. **Dependencies**: T026.
- [ ] T031 [US2] **Non-Linearity Test**: Test for non-linearity by implementing **BOTH** a quadratic term (temperature^2) **AND** a spline basis (using `patsy` or `scipy`). Compare model fit (AIC/BIC) against the linear-only model. **(FR-013)**. **Dependencies**: T026.
- [ ] T032 [US2] **Export model coefficients**: Save model results to `results/stats/model_results.json`. **Dependencies**: T026, T031.

**Checkpoint**: User Story 2 should be fully functional and testable independently

---

## Phase 3: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [ ] T044 [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`
- [ ] T045 [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T033 [US3] **Indoor/Outdoor Confound Analysis**: Implement confound analysis for indoor/outdoor effects by stratifying data using **urban/rural classification** proxy (from T028a). If metadata unavailable, **report the limitation** and quantify the potential noise impact via robustness checks. **(FR-012)**. **Dependencies**: T018b, T026.
- [ ] T035b [US3] **Distance Sensitivity Analysis**: Test varying distance thresholds (e.g., short, medium, and long ranges). **Dependencies**: T019, T026.
- [ ] T047 [US3] **Sensitivity Analysis**: Run sensitivity analysis on temperature outlier thresholds by sweeping the threshold from **1.0 to 4.0 standard deviations** and reporting the variation in the temperature coefficient. **(FR-006)**. **Dependencies**: T026.

**Checkpoint**: User Story 3 should be fully functional and testable independently

---

## Phase 4: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Address the absence of baseline data and arousal proxies by documenting them as limitations, as required by the spec's assumptions, and quantifying the noise floor via observed variance.

**Independent Test**: Verify that the results log explicitly states the inability to control for baseline reaction time and physiological arousal, and includes the quantified variance of individual differences from the model.

### Implementation for Limitations

- [ ] T054 [US3] **Quantify Individual Difference Noise**: Extract the variance component for the random intercept (Participant ID) from the primary model (T026). Calculate the Intraclass Correlation Coefficient (ICC) to quantify the proportion of variance in response time attributable to individual differences in baseline speed. Log this value to `results/stats/individual_variance.json`. **(Review Concern: Baseline Confound)**. **Dependencies**: T026.
- [ ] T048 [US3] **Draft Limitations**: Draft the limitations section in `results/logs/limitations.md`. **Dependencies**: T026, T054.
- [ ] T041 [US3] **Extract random intercept variance**: Quantify noise floor by extracting random intercept variance from T026. **Dependencies**: T026.
- [ ] T043 [US3] **Document Methodological Constraints**: Document constraints regarding the lack of pre-test baselines and physiological proxies as a hard limitation. **Dependencies**: T048, T054.
- [ ] T046 [US3] **Document Baseline Limitation Disclaimer**: Add specific disclaimer regarding the inability to measure physiological arousal or baseline reaction speed in the existing Moral Machine dataset. **Dependencies**: T054, T048.
- [ ] T049 [US3] **Generate Feasibility Report**: Generate final report. **Dependencies**: T043, T046.
- [ ] T050 [US3] **Documentation updates**: Update all documentation. **Dependencies**: T049.
- [ ] T051 [US3] **Code cleanup**: Clean up code. **Dependencies**: T050.
- [ ] T052 [US3] **Performance optimization**: Optimize performance. **Dependencies**: T051.
- [ ] T053 [US3] **Additional unit tests**: Add additional tests. **Dependencies**: T051.

**Checkpoint**: All reviewer suggestions regarding data collection are formally documented as infeasible, closing the loop on the review.

---

## Phase 11: Review Resolution - Baseline Confound Mitigation (Priority: P3 - Revision)

**Goal**: Address the specific concern from the Daniel Kahneman simulated review regarding the lack of individual baseline reaction speed and physiological arousal controls. Since the dataset does not contain this data, we must quantify the resulting noise and document it as a hard limitation.

- [ ] T055 [US3] **Document Baseline Limitation**: Explicitly write a section in `results/logs/limitations.md` stating that the Moral Machine dataset lacks a pre-test neutral reaction-time task. Explain that the observed temperature effect is therefore confounded by unmeasured individual baseline speed. **(Review Concern: Baseline Confound)**. **Dependencies**: T054, T048.
- [ ] T056 [US3] **Document Arousal Proxy Limitation**: Explicitly write a section in `results/logs/limitations.md` stating that no physiological proxy (e.g., skin conductance) or self-reported arousal measure was collected. Explain that the mechanism (System 1 arousal vs. direct temperature effect) cannot be disentangled. **(Review Concern: Arousal Proxy)**. **Dependencies**: T054, T048.
- [ ] T057 [US3] **Simulated Sensitivity Analysis (Hypothetical)**: Perform a theoretical sensitivity analysis in `code/robustness.py` to estimate the impact of a hypothetical baseline correction. **Action**: Assume a range of plausible correlations between temperature and baseline speed (r = 0.0, 0.1, 0.2, 0.3). For each r, calculate `bias = r * (std_temp / std_response)`. Report the min and max bias values as the "Potential Bias Range" in `results/stats/sensitivity_hypothetical.json`. **(Review Concern: Baseline Confound)**. **Dependencies**: T054, T048.
- [ ] T058 [US3] **Final Limitations Review**: Review the `limitations.md` file to ensure it comprehensively addresses the Kahneman review points (baseline, arousal, noise floor) and includes the quantitative variance estimates from T054 and T057. **(Review Concern: Baseline Confound)**. **Dependencies**: T055, T056, T057.

**Checkpoint**: All reviewer concerns regarding missing baseline and arousal data are formally addressed through quantitative noise estimation and explicit documentation of limitations.