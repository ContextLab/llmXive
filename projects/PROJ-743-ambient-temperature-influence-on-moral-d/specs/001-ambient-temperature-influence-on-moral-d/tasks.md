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

**Purpose**: Verify data sources, download, and validate resolution standards before any ingestion or modeling can proceed.

**⚠️ CRITICAL**: No other tasks can begin until Phase 0 is complete and the data gap is resolved.

- [ ] T001 [P] Verify the canonical URL for the Copernicus Climate Data Store (CDS) API for ERA hourly data and confirm accessibility (HTTP 200) using the `cdsapi` library configuration. Log the verification result (including API endpoint and status) to `results/logs/data_validation_log.txt`.
- [ ] T001a [P] **Validate Moral Machine Source**: Verify the canonical URL for the Moral Machine dataset against the "Verified Accuracy" principle. Confirm the dataset exists, is accessible, and contains the required columns: `latitude`, `longitude`, `timestamp`, `response_time`. Log the validation status (Pass/Fail) and column schema to `results/logs/data_validation_log.txt`. **(FR-014, US-1)**.
- [ ] T001b [P] **Ingest & Validate ERA5 Sample**: Write a Python script `code/validate_era5.py` to fetch a **specific sample subset** for validation: **Jan 1, 2016 to Jan 7, 2016** in **London (51.5N, -0.1W)**. Execute this script to fetch the sample to `data/raw/era_sample.h5`. Verify the sample contains hourly resolution and valid temperature values. Log success/fail to `results/logs/data_validation_log.txt`. **(FR-014, US-1)**.
- [ ] T002 [P] **Derive Bounding Box**: Write a script `code/derive_bbox.py` to load the Moral Machine dataset (or a sample thereof) and calculate the exact geographic bounding box (min/max lat/lon) required for the ERA5 fetch. Output the bounding box to `data/external/bounding_box.json`. **(Executability Fix)**.
- [ ] T004c [P] **Validate ERA5 Full Metadata**: Using the bounding box from `data/external/bounding_box.json` (T002), query the CDS API metadata for the 2014‑2018 period. Verify that the metadata confirms **hourly temporal resolution** and **geographic coverage** that fully encompasses the bounding box. Log Pass/Fail and relevant metadata details to `results/logs/data_validation_log.txt`. This validation must succeed before any full ERA5 download. **(FR‑014, Principle II)**.
- [ ] T004b [P] **Validate Full Source Standards**: Write and execute `code/validate_era_full.py`. **Logic**: 1. Read bounding box from `data/external/bounding_box.json` (T002). 2. Query CDS API metadata for the 2014‑2018 period within this bounding box. 3. Verify that the metadata confirms **hourly resolution** and **geographic coverage** meets FR‑014 standards. 4. Log the specific validation result (Pass/Fail) and metadata details to `results/logs/data_validation_log.txt`. **Dependencies**: T002, T001. **Gate**: If validation fails, abort and log "ERA5 Standards Not Met".
- [ ] T002b [P] **Fetch ERA5 Logic**: Write a Python script `code/fetch_era_full.py` to fetch the **full 2014‑2018 ERA5 2m temperature dataset** required for the primary analysis. The script MUST:
    1. Read the bounding box from `data/external/bounding_box.json` (T002).
    2. **Filter**: Only request tiles that overlap with this bounding box.
    3. Implement chunking by **10×10 degree tiles** to avoid single‑call timeout and memory overflow.
    4. Stream data to disk in chunks to stay within the available RAM limit.
    5. Include **retry logic** for CDS API rate limits (exponential backoff).
    **Parameters**: Variable `2t`, Time range `2014‑01‑01` to `2018‑12‑31`, Format `netcdf`, Grid resolution `0.25`.
    **Output**: Save to `data/raw/era5_full.h5`. **(FR‑001, Executability Fix)**.
    **Dependencies**: T002, T004c. (Note: Validation occurs in T004c before this fetch).
- [ ] T002b_test [P] **Unit Tests for Fetcher**: Write unit tests in `tests/test_ingestion.py` for `code/fetch_era_full.py` logic. **Specifics**: Test function `test_chunking_strategy` asserts `chunk_count == expected` where `expected = ceil((max_lat - min_lat)/10) * ceil((max_lon - min_lon)/10)`. Test `test_merge_logic` asserts `final_file.shape == expected_shape`. **(Executability Fix)**.
- [ ] T002c [P] **Execute Fetch**: Execute the script from T002b to fetch the full dataset. **Execution Logic**: Run `fetch_era_full.py` which must fetch by year and tile (2014‑2018), merge results, and save to `data/raw/era5_full.h5`. Log success/fail to `results/logs/data_validation_log.txt`. **Dependencies**: T002, T004c, T002b. **Validation**: Verify file existence and integrity before completion.
- [ ] T002d [P] **Checksum ERA5**: Compute and record the SHA‑256 checksum of the downloaded full ERA5 file (`data/raw/era5_full.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_full`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V. **(FR‑014, Principle V)**.
- [ ] T003 [P] **Checksum Sample**: Compute and record the SHA‑256 checksum of the downloaded ERA5 sample file (`data/raw/era5_sample.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_sample`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [ ] T004 [P] Programmatically validate that the downloaded ERA5 sample meets the hourly temporal resolution and geographic grid size standards defined in FR‑014. Log validation status (Pass/Fail) to `results/logs/data_validation_log.txt`.
- [ ] T005 [P] Verify the Moral Machine dataset source against the "Verified Accuracy" principle and log the validation status to `results/logs/data_validation_log.txt` using a standardized format: "Source: <name>, Status: <Pass/Fail>".
- [ ] T006 [P] **Pre‑Ingestion Validation Gate**: Implement a final check task that aggregates results from T001‑T005. **Mechanism**: Read JSON log files from T001a, T004, T005 and check file existence for T002c. If ANY source validation (ERA5 or Moral Machine) fails, this task MUST raise an exception and abort the pipeline. Log the final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`. **Dependencies**: T001‑T005.

**Checkpoint**: Data validation complete. If Pass, proceed to Phase 1. If Fail, project is blocked.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T007 Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`
- [ ] T008 Initialize a Python project with dependencies (pandas, numpy, statsmodels>=0.13, scikit-learn, requests, pyyaml, seaborn, matplotlib, geopandas, cdsapi, huggingface_hub) in requirements.txt
- [ ] T009 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** distance thresholds (default distance, with parameters for shorter and longer ranges in sensitivity analysis).
- [ ] T010b [P] **Calculate Temperature Thresholds**: Write a script `code/calc_thresholds.py` to load a sample of the Moral Machine dataset and calculate the 1st and 99th percentile of the `temperature` column (once merged with a sample of ERA5). **Output**: Store `TEMPERATURE_COLD_THRESHOLD` and `TEMPERATURE_HOT_THRESHOLD` in `code/config.py` as constants. **Dependencies**: T001b (Sample Data).
- [ ] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`
- [ ] T012 [P] Implement checksum generation and verification for `data/raw/` and `data/processed/` files in `code/utils.py`
- [ ] T013 Create data loading utilities in `code/loaders.py` using `pandas.read_parquet` with `chunksize` parameter for memory mapping. Implement function `load_chunked_parquet(path, chunk_size)` to handle large Parquet ingestion without memory overflow.
- [ ] T014 [P] Setup unit test framework (pytest) with configuration for CPU‑only execution and stratified sampling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [P] [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`
- [ ] T016 [P] [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`. **Specifics**: Use the Jan 2016 London sample from T001b and verify the exact schema of the merged output.

### Implementation for User Story 1

- [ ] T017a [US1] [P] **Count Valid Location Data (Pre‑Filter)**: Scan `data/raw/moral_machine.csv.gz` and count **all** records that have non‑null `latitude` and `longitude` fields *before* any other filtering. Output this count to `results/logs/ingestion_summary.log` as `count_valid_location`. **Dependencies**: None (Independent). **(SC‑001)**.
- [ ] T017 [US1] [P] **Load, Filter & Count**: Implement `code/ingestion.py` to:
    1. Load the Moral Machine dataset from `data/raw/moral_machine.csv.gz`.
    2. Filter records with missing location data (already counted in T017a).
    3. Filter records with impossible response times (<100 ms or >10 000 ms) **(FR‑010)**.
    4. Filter records with temperature values outside the configurable range defined in `code/config.py` (`TEMPERATURE_COLD_THRESHOLD`, `TEMPERATURE_HOT_THRESHOLD`) **(FR‑002)**.
    5. Log excluded records to `results/logs/exclusion_log.csv` in CSV format, including the reason for each exclusion.
    6. Log the number of records that pass all filters to `results/logs/ingestion_summary.log` as `count_filtered`.
    **Dependencies**: T010, T010b. **(FR‑002, FR‑010)**.
- [ ] T018 [US1] **Define Logic**: Implement the **logic** for ERA5 Reanalysis data fetching and merging in `code/ingestion.py` using the CDS API (`cdsapi`) for 2014‑2018 (FR‑001). This task defines the functions `fetch_era5_data` and `merge_with_moral_machine` but does **not** execute them. **Dependencies**: T002c, T002d.
- [ ] T018b [US1] **Load and Merge**: Load the pre‑fetched ERA5 data from `data/raw/era5_full.h5` (produced by T002c) and merge it with the Moral Machine data processed in T017 using a streaming approach (`pandas.read_parquet` with `chunksize=100000`). **Deliverables**: Save **raw merged dataset** to `data/processed/merged_dataset_raw.parquet`. **Verification**:
    1. Compute and verify the SHA‑256 checksum of `data/raw/era5_full.h5` against the entry recorded by T002d.
    2. Validate that the schema of `data/processed/merged_dataset_raw.parquet` matches the schema defined in `data-model.md`.
    3. Log success entry `{"merge_status": "success", "schema_valid": true, "records_merged": <int>}` to `results/logs/ingestion_summary.log`.
    **Dependencies**: T018, T002c, T017.
- [ ] T019 [US1] **Geospatial Matching**: In `code/ingestion.py`, link each Moral Machine record to the nearest ERA5 grid point using the **Haversine** distance (via `geopy`). For matches where the distance exceeds 100 km, set `match_quality` to `'low'` and **log** the record in `results/logs/data_quality_log.json` with fields:
    - `record_id`
    - `grid_point_identifier`
    - `timestamp`
    - `distance_km`
    - `exclusion_reason`: `"distance > 100km"`
    This satisfies FR‑009 and Constitution Principle VI (explicit station/grid identifier and timestamp). Records with `'low'` quality will later be excluded. **Dependencies**: T018b.
- [ ] T019b [US1] **Primary Exclusion Filter**: Exclude from the primary analysis any records where `match_quality == 'low'` (distance > 100 km) **or** where `temporal_gap > 2 h` (as logged by T020). Update `results/logs/exclusion_log.csv` with the appropriate `reason` field (`"primary_filter_distance_gt_100km"` or `"primary_filter_temporal_gap_gt_2h"`). **Dependencies**: T019, T020.
- [ ] T020 [US1] **Time‑based Interpolation**: Implement linear interpolation for missing ERA5 hourly values **only** when the gap is ≤ 2 h. If the gap exceeds 2 h, exclude the record and log the exclusion reason `"ERA5 coverage gap"` in `results/logs/data_quality_log.json`. **Dependencies**: T018b, T019.
- [ ] T019c [US1] **Create Data Quality Log**: Initialise `results/logs/data_quality_log.json` as a single source of truth for all data‑quality flags, exclusion reasons, and match‑quality metrics. Ensure that T019, T020, and T019b append entries in the prescribed JSON schema. **(Spec Compliance)**.
- [ ] T022 [US1] **Generate Final Filtered Dataset**: From `data/processed/merged_dataset_raw.parquet`, apply the primary exclusion filters (T019b, T020) and write the cleaned dataset to `data/processed/merged_dataset.parquet`. **Verification Criteria**:
    1. Read `count_valid_location` from T017a.
    2. Read `count_filtered` (records after all filters) from T017.
    3. Log a JSON object to `results/logs/ingestion_summary.log`:
       `{"count_total": <count_valid_location>, "count_matched": <count_filtered>, "success_rate": <float>}` where `success_rate = count_filtered / count_valid_location * 100`.
    The task is considered complete only if this log entry is generated successfully. **Dependencies**: T019b, T020, T018b.
- [ ] T022a [US1] **Calculate Match Success Rate**: Append to `results/logs/ingestion_summary.log` the field `{"match_success_rate": <float>}` where the numerator is `count_matched` from T022 and the denominator is `count_valid_location` from T017a (ensuring the denominator reflects *all* records with valid latitude/longitude, per SC‑001). **Dependencies**: T017a, T022.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p‑value for the fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for log‑transformation and outlier handling in `tests/test_modeling.py`
- [ ] T024 [P] [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement `code/modeling.py` to perform log‑transformation of response times and handle non‑convergence by switching to GLMM (FR‑003). **Dependencies**: T022.
- [ ] T028a [US2] **Check Availability of Demographic Covariates**: Inspect the merged dataset (`data/processed/merged_dataset.parquet`) for aggregate country‑level `age` and `gender` columns. If present, retain them for modeling. If absent, **log** the limitation in `results/logs/demographic_gap_log.txt` (e.g., “Aggregate age/gender not available; proceeding without these covariates”). **Do NOT fetch external data**; the task complies with FR‑004 by using only available aggregate covariates or documenting their absence. **Dependencies**: T022.
- [ ] T028c [US2] **Derivation of Dilemma Complexity**: Derive a static metric for dilemma complexity (independent of response time) using the formula: `(number of lives at stake) + (dilemma type ID weight)`. Ensure it is merged into the dataset. **Dependencies**: T022. **Note**: This score is a required covariate for T026.
- [ ] T028d [US2] [P] **Derivation of Time‑of‑Day Covariate**: Extract the hour (0‑23) from the `timestamp` column in the merged dataset (T022) and create a new column `time_of_day`. **Dependencies**: T022. **(FR‑004)**
- [ ] T028e [US2] **Verify Covariate Integrity**: Run a validation script to check that ALL required covariates (temperature, dilemma complexity, time‑of‑day, dilemma choice, and any available age/gender aggregates) are present in the dataset before modeling. If any are missing, raise an exception. **Dependencies**: T028a, T028c, T028d.
- [ ] T026 [US2] **Primary Model: Linear Mixed‑Effects (LMM)** in `code/modeling.py` with fixed effects: temperature, dilemma complexity, time‑of‑day, dilemma choice, and **interaction term between temperature and dilemma choice**, and random intercepts for participant ID and cultural region. **Fallback**: If LMM fails to converge, implement GLMM with log‑link function (FR‑003). **Output**: Save results to `results/stats/lmm_model_results.json` following `model_output.schema.yaml` (keys: `temperature_coef`, `temperature_se`, `temperature_p_value`, `random_intercept_variances`, `dilemma_complexity_coef`, `time_of_day_coef`, `dilemma_choice_coef`). **Dependencies**: T025, T028c, T028d, T028a, T028e, T022.
- [ ] T029 [US2] Implement likelihood‑ratio test in `code/modeling.py` comparing Full Model (temperature, dilemma complexity, time‑of‑day, choice, interaction) vs. Null Model (dilemma complexity, time‑of‑day, choice, without temperature) and record p‑value (FR‑005, SC‑002). **Dependencies**: T026.
- [ ] T030a [US2] Implement diagnostic plot generation (QQ‑plot, residual vs. fitted) to verify normality and homoscedasticity assumptions of the transformed data (FR‑007). Save plots to `results/figures/`. **Dependencies**: T026.
- [ ] T030b [US2] Implement Anderson‑Darling statistical test on a **stratified random sample (size = max(1000, of rows))** to verify residual normality (SC‑005). Record the Anderson‑Darling p‑value in `results/stats/model_results.json` under the key `anderson_darling_p_value`. **Dependencies**: T026.
- [ ] T031 [US2] **Non‑Linearity Test**: Fit a model with a quadratic term (`temperature^2`) and a spline basis for temperature. Compare model fit (AIC/BIC) against the linear‑only model (FR‑013). Save results to `results/stats/nonlinearity_test_results.json`. **Dependencies**: T026.
- [ ] T032 [US2] Export model coefficients, standard errors, p‑values, and random effect variances to `results/stats/model_results.json` in a format compliant with `model_output.schema.yaml` (FR‑008). **Dependencies**: T026, T031.
- [ ] T041 [US2] **Extract Random Intercept Variance**: Using the fitted LMM output (from T032), extract the variance component for the cultural‑region random intercept and record it in `results/stats/model_results.json` under the field `cluster_robust_variance`. **Dependencies**: T032.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`
- [ ] T034 [P] [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement `code/robustness.py` to calculate alternative temperature metrics (e.g., 3‑hour moving average) and re‑run modeling (FR‑006)
- [ ] T035b [P] [US3] **Distance Sensitivity Analysis**: Re‑run the primary model excluding records >25 km and >50 km (using config thresholds from T010). Report the variation in the temperature coefficient. **Dependencies**: T019b, T026.
- [ ] T036 [US3] Implement sensitivity analysis in `code/robustness.py` sweeping temperature outlier thresholds (e.g., varying standard‑deviation multipliers) and reporting coefficient variation (FR‑006, SC‑003)
- [ ] T037 [US3] **Indoor/Outdoor Confound Analysis**: Attempt to stratify data or apply a proxy adjustment using urban/rural classification. **Data Source**: Fetch urban/rural data from `datasets.load_dataset('jrc/ghsl-population')` and use the file `files/GHSL_POP_GLO_V1.0.zip`. Verify file existence before use. If metadata is unavailable, **log the limitation** in `results/logs/indoor_outdoor_limitation.md` and include a section “Quantified Noise Impact” (or “N/A” with reason). (FR‑012). **Dependencies**: T022.
- [ ] T038 [US3] Generate comparison table in `code/robustness.py` showing temperature coefficient and p‑value for primary vs. alternative models (US‑3)
- [ ] T039 [US3] Save all robustness figures (scatter plots, conditional effect plots) to `results/figures/` (FR‑008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Address the absence of baseline data and arousal proxies by documenting them as limitations, as required by the spec's assumptions, and quantifying the noise floor via observed variance.

**Independent Test**: Verify that the results log explicitly states the inability to control for baseline reaction time and physiological arousal, and includes the quantified variance of individual differences from the model.

### Implementation for Limitations

- [ ] T040 [P3] Draft and verify `results/logs/limitations.md` explicitly stating: (1) No individual baseline reaction time data exists in the dataset; (2) Arousal/micro‑climate effects are unmeasured noise; (3) These factors are not controlled for, only reported (FR‑012, Spec Assumptions). **Input**: Read `results/stats/model_results.json` (key `cluster_robust_variance`). **Output**: Append section "Quantification of Unmeasured Baseline Noise" to `results/logs/limitations.md`. **Dependencies**: T041, T026.
- [ ] T045b [P3] **Document Baseline Limitation Disclaimer**: Update `results/logs/limitations.md` to include a specific disclaimer: "The reported `cluster_robust_variance` is a descriptive measure of unexplained variability; it does **not** imply causal isolation of temperature effects." **Dependencies**: T041.

**Checkpoint**: Limitations documented; analysis complete within data constraints.

---

## Phase 7: Research-Stage Review Resolution (Priority: P3 - Revision)

**Goal**: Address the specific concern from the "daniel‑kahneman‑simulated" review regarding the confounding of temperature effects with individual baseline reaction speed and physiological arousal, by explicitly documenting the data gap and quantifying the theoretical impact via observed variance.

**Independent Test**: Verify that the `results/logs/limitations.md` contains a specific entry for the Kahneman review, acknowledging the lack of baseline/arousal data, and that the `results/logs/limitations.md` includes the quantified noise floor.

### Implementation for Review Resolution

- [ ] T043 [P3] Update `results/logs/limitations.md` and `docs/research.md` to add a specific section for the "daniel‑kahneman‑simulated" review (dated 2026‑06‑21), explicitly stating that the dataset lacks pre‑test baseline reaction times and physiological arousal proxies (e.g., skin conductance), making the "temperature‑adjusted RT" calculation impossible. **Dependencies**: T040, T045b.

**Checkpoint**: Review concerns acknowledged, theoretical impact quantified, and future work proposed.

---

## Phase 8: Review-Driven Confound Quantification (Priority: P3 - Revision)

**Goal**: Directly address the Kahneman review's specific suggestion to quantify the "noise" of individual differences by documenting the theoretical impact using the observed random effect variance, as stratified analysis is not feasible with the available data.

**Independent Test**: Verify that `results/logs/limitations.md` contains a dedicated section "Review: daniel‑kahneman‑simulated" with the specific quantification of the baseline confound using the random effect variance.

### Implementation for Review Resolution

- [ ] T045 [P3] **Document Baseline Limitation**: Update `results/logs/limitations.md` to include a new subsection "Quantification of Reviewer Concern (Kahneman)" that: (1) Reports the `cluster_robust_variance` value from T041 as the estimated variance in the temperature effect due to unmeasured individual differences; (2) Explains that without a true baseline, the main effect is an upper bound; (3) Explicitly states that the stratified analysis proposed in the review is not feasible due to data constraints (Spec Assumptions). **Dependencies**: T041, T040, T045b.

**Checkpoint**: Reviewer's specific concern about baseline confounding is now quantified and documented, allowing the project to proceed with a clear understanding of the noise floor.

---

## Phase 9: Review-Driven Methodological Constraint Documentation (Priority: P3 - Revision)

**Goal**: Explicitly document the inability to implement the reviewer's proposed "pre‑test baseline" and "physiological proxy" methods due to the fixed nature of the Moral Machine dataset, and formally state this as a hard limitation in the research output.

**Independent Test**: Verify that `results/logs/limitations.md` contains a specific section "Methodological Constraints: Reviewer Proposals" that explicitly lists the unimplementable suggestions (pre‑test baseline, skin conductance) and the reason (data source immutability).

### Implementation for Review Resolution

- [ ] T046 [P3] **Document Methodological Constraints**: Update `results/logs/limitations.md` to add a subsection "Methodological Constraints: Reviewer Proposals" that: (1) Explicitly lists the Kahneman review's suggestion for a "pre‑test neutral reaction‑time task" and "physiological proxy (skin conductance)"; (2) States that these cannot be implemented because the Moral Machine dataset is a static, historical archive with no such metadata; (3) Concludes that the analysis is strictly limited to the available variables (temperature, response time, dilemma attributes). **Dependencies**: T043, T045.

**Checkpoint**: All reviewer suggestions regarding data collection are formally documented as infeasible, closing the loop on the review.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `docs/` and `quickstart.md` including instructions for running with sampled data
- [ ] T049 Code cleanup and refactoring to ensure modularity
- [ ] T050 Performance optimization: Ensure dataset sampling logic in `code/ingestion.py` prevents memory overflow on runners with constrained RAM resources
- [ ] T051 [P] Additional unit tests for edge cases (e.g., all records excluded due to distance)
- [ ] T052 Run quickstart.md validation to ensure full pipeline completes within 4 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Validation)**: Must run FIRST. BLOCKS all other phases.
- **Phase 1 (Setup)**: Depends on Phase 0 completion.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion.
- **User Stories (Phase 3‑5)**: All depend on Foundational phase completion; can run in parallel thereafter.
- **Limitations (Phase 6)**: Depends on US3 completion.
- **Review Resolution (Phase 7‑9)**: Depends on US3 and Limitations completion.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational.
- **User Story 2 (P2)**: Starts after Foundational; requires merged data from US1.
- **User Story 3 (P3)**: Starts after Foundational; requires model output from US2.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel.
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- Phase 6‑9 can be executed in parallel once their dependencies (US2/US3) are met.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data validation.
2. Complete Phase 1 + Phase 2.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Phase 0 → Data validated
2. Complete Setup + Foundational → Foundation ready
3. Add User Story 1 (Ingestion) → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 (Modeling) → Test independently → Deploy/Demo
5. Add User Story 3 (Robustness) → Test independently → Deploy/Demo
6. Add Limitations (Phase 6) → Test independently → Deploy/Demo
7. Add Review Resolution (Phase 7) → Test independently → Deploy/Demo
8. Add Review‑Driven Confound Quantification (Phase 8) → Test independently → Deploy/Demo
9. Add Review‑Driven Methodological Constraint Documentation (Phase 9) → Test independently → Deploy/Demo
10. Each story adds value without breaking previous stories

### Parallel Team Strategy

- Phase 0 together.
- Phase 1 + 2 together.
- Then parallel developers:
  - Dev A: User Story 1
  - Dev B: User Story 2
  - Dev C: User Story 3
- Subsequent phases handled similarly.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **CPU Constraint**: All tasks must be designed to run on a limited number of CPU cores and moderate memory resources. Use stratified sampling if dataset is large.
- **NO GPU**: No CUDA‑dependent code.
- **Data Constraints**: Do NOT simulate missing data (baseline, arousal) as real data. Document limitations and perform theoretical reporting instead.
- **Critical Blocker**: Phase 0 MUST pass before any ingestion tasks (T017+) are attempted.
- **Review Resolution**: Phases 6‑9 are mandatory to address the “daniel‑kahneman‑simulated” review regarding baseline reaction‑time confounds, quantify the noise floor, and document inability to implement proposed data‑collection methods.
