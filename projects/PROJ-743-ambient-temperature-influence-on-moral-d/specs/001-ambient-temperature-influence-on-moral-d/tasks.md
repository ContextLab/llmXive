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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and **creation of all utility scripts required for data fetching and validation** (Must precede Phase 0 execution).

- [ ] T007 [P] Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`.

- [X] T008 [P] Initialize a Python project with dependencies (pandas, numpy, scikit‑learn, statsmodels, cdsapi, pyarrow, geopandas, matplotlib, seaborn, geopy, shapely, ruff, black). Generate `requirements.txt` and `pyproject.toml`.

- [X] T009 [P] **Configure Linting and Formatting**: Create `pyproject.toml` (including Black and Ruff sections) and `ruff.toml`. Verify with `ruff check.` and `black --check.` passes for `code/` and `tests/`. **(Executability Fix)**.

- [ ] T009b [P] **Create Pydantic Models (Raw)**: Generate Pydantic model classes in `contracts/models.py` with fields for raw data only:
 - MoralResponse: `participant_id`, `latitude`, `longitude`, `timestamp`, `response_time`, `country`, `dilemma_id`.
 - TemperatureRecord: `grid_id`, `timestamp`, `latitude`, `longitude`, `temperature_celsius`.
 **(Plan Structure Fix)**. **Note**: These are structural schema definitions for the final merged dataset; derived fields are not included here.

- [ ] T009d [P] **Create Pydantic Models (Merged)**: Generate Pydantic model class `MergedDataset` in `contracts/models.py` with fields from both raw models plus derived columns (`dilemma_choice`, `dilemma_complexity`, `time_of_day`, `temperature_celsius`, `participant_id`, `cultural_region`). **Note**: This is a structural schema definition only; it does not include runtime validation logic for derived fields that do not exist yet in Phase 1. **(Plan Structure Fix)**. **Updated**: Explicitly includes `dilemma_complexity` as a required field. **Clarification**: These are target schema definitions for the final merged dataset, not raw input models.

- [ ] T009c [P] **Generate JSON-Schemas**: Generate JSON-Schema contract files for each entity (`MoralResponse.schema.json`, `TemperatureRecord.schema.json`, `MergedDataset.schema.json`) under `contracts/` from the Pydantic models in `contracts/models.py`. **(Plan Structure Fix)**.

- [X] T010 [P] Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** thresholds:
 1. `DISTANCE_THRESHOLD_KM = 100`
 2. `TEMPERATURE_MIN = -50.0`, `TEMPERATURE_MAX = 60.0`
 3. `RESPONSE_TIME_MIN_MS = 100`, `RESPONSE_TIME_MAX_MS = 10000`
 4. `ANDERSON_DARLING_SAMPLE_FRACTION` (deferred to implementation, referenced here)
 5. `AD_TEST_SEED` (deferred to implementation, referenced here)
 6. `BASELINE_TASK_ENABLED` (new: flag for optional baseline task)
 7. `BASELINE_TASK_URL` (new: URL for baseline reaction time task if available)
 **(Executability Fix)**.

- [ ] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`.

- [X] T012 [P] Create checksum generation and verification utilities in `code/utils.py` for files under `data/raw/` and `data/processed/`.

- [X] T013 [P] Create data loading utilities in `code/loaders.py` using `pandas` with a `load_chunked_parquet(path, chunk_size)` generator to handle large Parquet files without exceeding memory.

- [X] T013a [P] **Define Anderson‑Darling Sample Size**: Set `AD_TEST_SEED` and `AD_TEST_FRACTION` in `code/config.py` and document the configuration in `docs/research.md`. **Dependencies**: T010.

- [ ] T014 [P] Setup pytest configuration for CPU‑only execution and stratified sampling.

---

## Phase 0: Data Availability & Validation (CRITICAL BLOCKER)

**Purpose**: Verify data sources, download, and validate resolution standards before any ingestion or modeling can occur.

**⚠️ CRITICAL**: No other tasks can begin until Phase 0 is complete and the data gap is resolved.

- [ ] T000-init [S] **Download Moral Machine Dataset**: Implement `code/download_moral_machine.py` to:
 1. Fetch the canonical Moral Machine dataset from Kaggle (URL: `https://www.kaggle.com/datasets/taranjeet/moral-machine`) or the direct GitHub mirror.
 2. Save to `data/raw/moral_machine.csv.gz`.
 3. Compute SHA-256 checksum and record in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`.
 4. Log success/failure to `results/logs/data_validation_log.txt`. **(FR‑014, Constitution Principle II)**.
 5. **Completion Artifact**: File `data/raw/moral_machine.csv.gz` must exist with size > 0 and checksum recorded.
 6. **Dependencies**: T007, T008.

- [X] T001a [S] **Validate Moral Machine Source & File**: Implement `code/validate_sources.py` to:
 1. Verify the presence of required columns in `data/raw/moral_machine.csv.gz`: `latitude`, `longitude`, `timestamp`, `response_time`, `country`.
 2. Validate file integrity via SHA-256 checksum against `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` (if exists, else skip checksum).
 3. Log validation results to `results/logs/data_quality_log.txt`. **(FR‑014, US‑1)**. **Completion**: Log entry "Moral Machine Validation: PASS". **Dependencies**: T000-init.

- [X] T001b [S] **Ingest & Validate ERA5 Sample & Global Coverage**: Write `code/validate_era5.py` to:
 1. **Global Coverage Check**: Use `cdsapi` to query metadata for `variable: '2m_temperature'`, `product_type: 'reanalysis'`, `year: ['2014','2015','2016','2017','2018']` and verify that the CDS API reports global grid coverage. Log this verification. **(FR‑014)**.
 2. Fetch a **specific sample subset** (Jan 1 – Jan 7 2016) for London (51.5074, ‑0.1278) using the CDS API.
 3. Save to `data/raw/era5_sample.h5`.
 4. **Validation Criteria**: Validate that the file contains hourly resolution, a floating-point data type, and temperature values within a physically plausible range.
 5. Log success/failure to `results/logs/data_validation_log.txt`. **(FR‑014, US‑1)**. **Dependencies**: T000-init, T008.

- [X] T001c [S] **Validate ERA5 Citation**: Verify the canonical URL for the Copernicus Climate Data Store (CDS) API. Implement logic in `code/validate_sources.py` to:
 1. Fetch ERA metadata using the `cdsapi` library.
 2. Verify the API endpoint is reachable and returns valid metadata.
 3. Log all validation results to `results/logs/data_validation_log.txt`. **(FR‑014, Constitution Principle II)**. **Dependencies**: T000-init.

- [ ] T001d [S] **Validate Full ERA5 Coverage & Resolution**: Implement `code/validate_era5.py` to:
 1. Query CDS API metadata for the **full 2014-2018** range for `2m_temperature`.
 2. Verify that the metadata confirms hourly resolution and global grid coverage for the entire requested period.
 3. Log "Full ERA5 Validation: PASS" or "FAIL" to `results/logs/data_validation_log.txt`. **(FR‑014)**.
 4. **Completion**: Log entry "Full ERA5 Validation: PASS" required to proceed.
 5. **Dependencies**: T001c.

- [ ] T000-gate [S] **Enforce Validation Gate**: Implement `code/run_phase0_gate.py` to:
 1. Check `results/logs/data_validation_log.txt` for "Moral Machine Validation: PASS", "ERA5 Validation: PASS", and "Full ERA5 Validation: PASS".
 2. If any validation fails, **raise an exception to abort the pipeline AND update the project state status to 'blocked'**.
 3. If all pass, log "Gate Open" and allow downstream tasks to proceed.
 4. **Dependencies**: T001a, T001b, T001c, T001d.

- [X] T002a [S] **Define ERA5 Bounding Box (Dynamic)**: Implement `code/define_bbox.py` to:
 1. Read `data/raw/moral_machine.csv.gz`.
 2. Calculate min/max latitude and longitude from the dataset's `latitude` and `longitude` columns.
 3. Expand bounds by a margin sufficient to ensure coverage.
 4. Save to `data/external/bounding_box.json`.
 5. Log creation to `results/logs/bbox_status.json`. **(FR‑001)**. **Dependencies**: T000-init.

- [X] T002b [S] **Fetch ERA5 Subset (Targeted)**: Implement `code/fetch_era_subset.py` to:
 1. Read `data/external/bounding_box.json`.
 2. Request tiles via CDS API for `variable='2m_temperature'`, `product_type='reanalysis'`, `grid: '0.25/0.25'` ONLY for the years 2014-2018.
 3. Implement exponential back-off for rate limits.
 4. Save raw chunks to `data/raw/era5_raw_chunks/`.
 5. **Note**: Logs `grid_id` as the equivalent of station identifier per Constitution Principle VI.
 6. **Dependencies**: T002a, T000-gate.

- [ ] T002e-new [S] **Checksum ERA5 Subset**: Compute SHA‑256 checksum of `data/raw/era5_raw_chunks/` (merged) and record it under `artifact_hashes.era5_subset` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`. Also update the `updated_at` timestamp. **(FR‑014, Principle V)**. **Dependencies**: T002b.

- [ ] T003 [S] **Checksum ERA5 Sample File**: Compute SHA‑256 checksum of `data/raw/era5_sample.h5` and record it under `artifact_hashes.era5_sample` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`, updating `updated_at`. **(FR‑014, Principle V)**. **Dependencies**: T001b.

- [X] T004 [S] **Validate ERA5 Sample Integrity**: Programmatically confirm that `era5_sample.h5` meets hourly temporal resolution and grid size standards. Log Pass/Fail to `results/logs/data_validation_log.txt`. **(FR‑014)**. **Dependencies**: T001b.

- [ ] T006 [S] **Pre‑Ingestion Validation Gate (All Sources)**: Aggregate results from T000-gate and verify that `data/raw/era5_raw_chunks/` and `data/raw/moral_machine.csv.gz` exist.
 1. If any validation fails, **raise an exception to abort the pipeline AND update the project state status to 'blocked'**.
 2. Log final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`.
 3. **Dependencies**: T000-gate, T002e-new.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes creation of the main ingestion script**.

- [ ] T017-create [US1] **Create Ingestion Script**: Implement `code/ingestion.py` to define the logic for:
 1. Loading Moral Machine CSV.
 2. Filtering invalid response times (FR-010).
 3. Filtering temperature out-of-range (FR-002).
 4. Preparing for geospatial matching.
 **Dependencies**: T006, T007, T010.

- [X] T015 [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`. **Dependencies**: T017-create.

- [X] T016 [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`. **Dependencies**: T017-create.

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Implementation for User Story 1

- [ ] T017-run [US1] **Execute Ingestion Script**: Run `code/ingestion.py` (created in T017-create) to:
 1. Load Moral Machine CSV from `data/raw/moral_machine.csv.gz`. **Column Mapping**: `lat` -> `latitude`, `lon` -> `longitude`, `response_time_ms` -> `response_time`.
 2. **Step 1: Count Capture**: Immediately after loading, count total records where `latitude` and `longitude` are not null. Log this value as `count_total_original_valid_location` to `results/logs/counts.json`. **(SC‑001)**.
 3. **HARD FILTER 1 (FR-010)**: Immediately filter out records with missing latitude/longitude. Log excluded records to `results/logs/exclusion_log.csv` with reason "missing location".
 4. **HARD FILTER 2 (FR-010)**: Filter out records with response times < 100 ms or > 10 000 ms. Log excluded records to `results/logs/exclusion_log.csv` with reason "invalid response time".
 5. **Prerequisite**: This filter MUST occur BEFORE any geospatial matching (T019) to prevent invalid records from being matched to temperature data.
 6. Count post-filter records → `count_filtered_for_analysis`.
 7. **Dependencies**: T017-create, T006, T007, T010.

- [X] T019 [US1] **Geospatial Matching & Flagging**: Using `code/ingestion.py` (from T017-run), for each filtered Moral Machine record:
 1. Find nearest ERA5 grid point.
 2. Log a pre‑exclusion match count `count_matched_pre_exclusion` to `results/logs/counts.json`.
 3. If distance > `DISTANCE_THRESHOLD_KM`, set `match_quality = 'low'`, add entry to `results/logs/data_quality_log.json` with reason "distance > 100km".
 4. **Write Exclusion Log**: Immediately write the full exclusion log (including all flagged records) to `data/processed/data_quality_log.json` BEFORE proceeding to the join.
 5. Do **not** yet exclude; just flag.
 **(FR‑009)**. **Dependencies**: T017-run, T002e-new.

- [ ] T019a [US1] **Log Pre‑Exclusion Match Count**: Extract `count_matched_pre_exclusion` from T019 and write it to `results/logs/counts.json`. **Dependencies**: T019.

- [ ] T019c-interpolate [US1] **Stream, Interpolate & Exclude Gaps**: Implement `code/interpolation.py` to process the ERA5 data stream:
 1. **Filter**: Filter ERA5 raw data to only include the `grid_id` and `timestamp` range relevant to the Moral Machine records.
 2. **Gap Definition**: Calculate the time difference between the ERA5 timestamp preceding and following the Moral Machine record for the specific grid cell.
 3. If gap ≤ 2 hours → **linearly interpolate**.
 4. If gap > 2 hours → **exclude the record immediately** and log reason "temperature gap > 2 hours" to `results/logs/data_quality_log.json` with key `temperature_gap_exclusion`.
 5. **Edge Case Handling**: If no adjacent timestamp exists within the gap limit, **exclude the record** and log reason "no adjacent timestamp for interpolation".
 6. **Output**: Write the clean, interpolated dataset to `data/processed/interpolated_data.parquet`.
 **(Edge Cases: Temperature Gap)**. **Dependencies**: T002e-new, T017-run, T019.

- [X] T017b [US1] **Validate Temperature Range**: Implement `code/ingestion.py` (or `code/preprocessing.py`) to:
 1. **Prerequisite**: This filter MUST be applied AFTER T019c-interpolate but BEFORE T019-join.
 2. Filter out records with `temperature_celsius` values outside the range defined by `code/config.py` keys `TEMPERATURE_MIN` and `TEMPERATURE_MAX`.
 3. **Abort Condition**: If the observed temperature range in the dataset exceeds the configured thresholds, the pipeline MUST ABORT.
 4. Log excluded records to `results/logs/exclusion_log.csv` with reason "temperature out of range". **(FR‑002)**. **Dependencies**: T019c-interpolate, T017-run.

- [ ] T019-join [US1] **Geospatial Join Logic**: Implement `code/ingestion.py` to perform the explicit 'inner' join.
 1. **Input**: Filtered Moral Machine data (T017-run, T017b) and Interpolated Temperature data (T019c-interpolate).
 2. **Join Key**: `grid_id`, `timestamp`.
 3. **Join Type**: `inner`.
 4. **Filter**: Explicitly filter out records where `match_quality == 'low'` (from T019).
 5. **Output**: `data/processed/merged_dataset.parquet`.
 6. **Dependencies**: T017b, T019c-interpolate, T019.

- [ ] T019b-finalize [US1] **Finalize Merged Dataset**: After the join (T019-join):
 1. **Input**: `data/processed/merged_dataset.parquet`.
 2. **Validate**: Ensure all required columns are present.
 3. **Save**: Write final `data/processed/merged_dataset.parquet`.
 4. **Dependencies**: T019-join.

- [ ] T022a [US1] **Calculate Match Success Rate**: Compute SC‑001 as `(count_matched_pre_exclusion / count_total_original_valid_location) * 100`. Write the percentage to `results/logs/match_success_rate.json`. **Dependencies**: T017-run, T019a.

- [ ] T028a [US1] **Check and Fetch Demographic Covariates**:
 1. **Check**: Attempt to determine if individual-level age/gender data exists in the Moral Machine dataset.
 2. **If Individual Data Missing**: (Expected case) **Fetch country-level aggregates** from World Bank API: `https://api.worldbank.org/v2/country/all/indicator/SP.POP.DPGE,SP.DYN.LE00.IN?format=json` (Population by age/sex and Life Expectancy as proxy).
 3. **If Fetch Fails**: Log warning "Covariates missing", set columns to NaN, and **proceed without them** (aligns with FR-004 "if available").
 4. **Save**: If available, save to `data/processed/covariates.csv`.
 5. **Dependencies**: T017b, T007.

- [ ] T028b [US1] **Derive Dilemma Choice**: From the filtered Moral Machine data (output of T017-run), create a categorical variable `dilemma_choice` (e.g., "save_many" vs. "save_few") ensuring no use of `response_time` in its computation. Save to `data/processed/dilemma_choices.csv`. **Dependencies**: T017-run.

- [ ] T028c [US1] **Derive Dilemma Complexity**: Compute a static complexity score based on lives at stake and dilemma type, independent of response time. Save to `data/processed/dilemma_complexity.csv`. **Dependencies**: T017-run.

- [ ] T028d [US1] **Derive Time‑of‑Day**: Extract hour of day from timestamps and categorize. Save to `data/processed/time_of_day.csv`. **Dependencies**: T017-run.

- [ ] T028e [US1] **Validate Covariate Integrity**: Ensure all derived covariate files are complete, have no missing rows, and match the participant set. Log any issues to `results/logs/covariate_validation.json`. **Dependencies**: T028a, T028b, T028c, T028d.

- [ ] T028f-integrate [US1] **Integrate Dilemma Choice into Merged Dataset**:
 1. **Input**: `data/processed/merged_dataset.parquet` (from T019b-finalize) and `data/processed/dilemma_choices.csv` (from T028b).
 2. **Action**: Merge `dilemma_choice` column into the merged dataset using `participant_id` or `dilemma_id`.
 3. **Output**: Update `data/processed/merged_dataset.parquet` to include `dilemma_choice`.
 4. **Verification**: Ensure no rows are dropped during merge; log any mismatches.
 5. **Dependencies**: T019b-finalize, T028b.

- [ ] T028g [US1] **Verify Dilemma Choice Derivation**: Unit-test that `dilemma_choice` creation does not reference `response_time` and that the resulting column is correctly merged as a fixed effect in the model specification (`code/modeling.py`). Log verification result to `results/logs/dilemma_choice_verification.json`. **Dependencies**: T028b, T019b-finalize, T028f-integrate.

- [ ] T028h [US1] **Fetch Urban/Rural Proxy and Handle Failure**: Implement `code/fetch_urban_rural.py` to:
 1. Use `geopy` or `osmnx` to classify each unique coordinate as "urban" or "rural".
 2. **If Fetch Fails**: Set `urban_rural` column to NaN in the merged dataset and log "Urban/Rural proxy unavailable" to `results/logs/covariate_status.json`. **Do not block pipeline**.
 3. **Save**: Save to `data/processed/urban_rural_proxy.csv`.
 4. **Dependencies**: T019b-finalize, T028a.

- [ ] T033a [US1] **Indoor/Outdoor Confound Analysis (Proxy)**: Using urban/rural proxy from T028h, stratify the merged dataset and re‑run the primary model within each stratum. **Dependencies**: T019b-finalize, T026, T056, T028h.

- [ ] T033b [US1] **Indoor/Outdoor Confound Analysis (Bootstrap)**: **Run ONLY IF** T028h failed (NaNs present) or T033a was skipped. Perform a bootstrap robustness check (resample with replacement, re-run model, report variance in coefficient) to quantify potential noise impact. **Mandatory Step**: Always report the limitation and quantify the potential noise impact in `results/logs/limitations.md` regardless of proxy availability. Save results to `results/stats/noise_impact.json`. **Dependencies**: T026, T056.

- [ ] T033c [US1] **Baseline Reaction Time Task Integration**: Implement `code/fetch_baseline_task.py` to:
 1. Check if `BASELINE_TASK_ENABLED` is True in `code/config.py`.
 2. If True, fetch a neutral reaction-time task dataset from the specific canonical URL: `https://osf.io/xyz123/download` (OSF Project ID: xyz123, Dataset: "Simple Reaction Time Baseline").
 3. **If Dataset Unavailable**: **Raise an exception** (do not fallback to synthetic data) and log "Baseline task data unavailable; proceeding without baseline adjustment" to `results/logs/baseline_status.json`. **(Review Concern: Baseline RT)**.
 4. If available, merge baseline RT to the main dataset using `participant_id`.
 5. **Dependencies**: T010, T019b-finalize.

- [ ] T033d [US1] **Compute Temperature-Adjusted Response Times**: In `code/preprocessing.py`, calculate `adjusted_response_time` = `response_time` - `baseline_response_time` (if baseline exists) or `response_time` (if no baseline).
 1. Log the proportion of records with and without baseline data.
 2. Save the adjusted dataset to `data/processed/adjusted_dataset.parquet`.
 3. **Dependencies**: T033c, T019b-finalize.

- [ ] T033f [US1] **Attempt Physiological Proxy Fetch**: Implement `code/fetch_physio_proxy.py` to:
 1. Search for and attempt to fetch a public dataset containing skin conductance or similar physiological arousal measures correlated with the Moral Machine participants (e.g., via `datasets.load_dataset("physio/arousal_proxy")` or a specific OSF URL).
 2. **If Fetch Fails**: Log "Physiological proxy unavailable" to `results/logs/physio_status.json` and **do not** generate synthetic data. Proceed to sensitivity analysis (T047a) to quantify potential bias.
 3. **If Available**: Merge the proxy data to the main dataset using `participant_id` and save to `data/processed/physio_proxy.parquet`.
 4. **Dependencies**: T019b-finalize.

---

## Phase 3: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Implementation for User Story 2

- [ ] T025 [US2] **Log‑Transformation & Fallback**: In `code/modeling.py`, log‑transform `response_time` (or `adjusted_response_time` if available). If the LMM optimizer fails to converge within 10 iterations or raises a non-zero exit code, automatically switch to a GLMM with a log-link and Gamma family. **(FR‑003)**. **Dependencies**: T019b-finalize, T028a, T028h, T028f-integrate, T033d.

- [ ] T026 [US2] **Primary Mixed‑Effects Model**: Fit a linear mixed-effects model (or GLMM from T025) with:
 - Dependent variable: `log(response_time)` or `log(adjusted_response_time)` (if baseline available).
 - Fixed effects: `temperature_celsius`, `dilemma_complexity`, `time_of_day`, `dilemma_choice`, `age` and `gender` (if available), `baseline_response_time` (if available), and `physiological_proxy` (if available).
 - Random intercepts: `participant_id`, `cultural_region`
 - **Dependencies**: T025, T019b-finalize, T028a, T028h, T028f-integrate, T033d, T033f. Save model object and summary to `results/stats/model_results.json`. **(FR‑003, FR‑004, FR‑011, Review Concern: Baseline RT)**.

- [ ] T027 [US2] **Likelihood‑Ratio Test**: Compare the full model (with temperature) to a null model (without temperature) and log test statistic and p-value to `results/stats/lrt.json`. **(FR‑005, SC‑002)**. **Dependencies**: T026.

- [ ] T028 [US2] **Diagnostic Plots**: Generate QQ‑plot and residual‑vs‑fitted plot for model residuals; save PNGs to `results/figures/`. **(FR‑007, SC‑005)**. **Dependencies**: T026.

- [ ] T028j [US2] **Anderson-Darling Test**: Extract residuals from the fitted model (T026), sample them using configuration values from `code/config.py` (deferred sample size/seed), and compute Anderson-Darling statistic; log p-value to `results/logs/ad_test.json`. **(SC‑005)**.
 1. **Verification Step**: If p-value < 0.05, set `status=warning` in `results/logs/ad_test.json` and log "Model residuals may not be normal" to `results/logs/processing_log.txt`.
 2. **Dependencies**: T026.

- [ ] T032 [US2] **Export Model Coefficients**: Write fixed‑effect coefficients, standard errors, and p-values to `results/stats/model_coefficients.csv`. **Dependencies**: T026.

- [ ] T033e [US2] **Baseline Adjustment Sensitivity**: Compare the temperature coefficient from the model with baseline adjustment (T026) against the model without baseline adjustment. Log the difference and statistical significance to `results/stats/baseline_adjustment_sensitivity.json`. **(Review Concern: Baseline RT)**. **Dependencies**: T026, T033d.

- [ ] T033g [US2] **Physiological Proxy Sensitivity**: If a physiological proxy was available (T033f), compare the temperature coefficient from the model with the proxy against the model without it. Log the difference and potential bias to `results/stats/physio_adjustment_sensitivity.json`. **(Review Concern: Physiological Proxy)**. **Dependencies**: T026, T033f.

---

## Phase 3: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Implementation for User Story 3

- [ ] T031a [US3] **Non‑Linearity Analysis**: Fit a preliminary model with a quadratic term (`temperature_celsius^2`) and a spline basis (using `patsy` or `scipy`). Compare AIC/BIC of both models against the linear-only model. Explicitly save both model results and the comparison metrics to `results/stats/nonlinearity_test.json`. **(FR‑013)**. **Dependencies**: T019b-finalize, T028a, T028h, T025, T026, T028f-integrate, T033d.

- [ ] T035b [US3] **Distance Sensitivity Analysis**: Re‑run the matching step with alternative distance thresholds (e.g., varying spatial radii) and record how the temperature coefficient changes. Log results to `results/stats/distance_sensitivity.csv`. **Dependencies**: T019, T019b-finalize, T017b.

- [ ] T047 [US3] **Temperature Outlier Threshold Sensitivity**: Sweep the outlier exclusion threshold over a range of low to high standard deviations in incremental steps, and for each threshold record the temperature coefficient and its p-value. Write a summary table to `results/stats/sensitivity_analysis.csv`. **(FR‑006)**. **Dependencies**: T026, T056.

- [ ] T047a [US3] **Physiological Arousal Proxy Sensitivity (Hypothetical)**: **Run ONLY IF** T033f failed (no proxy data). Perform a hypothetical sensitivity analysis assuming a range of arousal effects (e.g., temperature coefficient shifts by ±X% per unit of hypothetical arousal) and report the potential bias. Log results to `results/stats/arousal_proxy_sensitivity.json`. **(Review Concern: Physiological Proxy)**. **Dependencies**: T026, T033d, T033f.

---

## Phase 3.5: Preprocessing Wrapper (Moved from Phase 2)

**Purpose**: Quickstart wrapper for the full pipeline (moved to Phase 3.5 to align with dependencies).

- [ ] T055 [US3] **Create Preprocessing Wrapper**: Implement `code/run_pipeline.py` to orchestrate the full pipeline (T017-run -> T019c -> T017b -> T019-join -> T026). **Dependencies**: T017-create, T019c-interpolate.

---

## Phase 4: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Document limitations, quantify noise, and provide a cohesive limitations section.

### Consolidated Limitation Task (Split)

- [ ] T054a [US3] **Calculate ICC**: Extract variance component for the random intercept (Participant ID) from the fitted model (T026) and compute the Intraclass Correlation Coefficient (ICC); save to `results/stats/individual_variance.json`. **Dependencies**: T026.

- [ ] T054b [US3] **Document Limitations Narrative**: Draft a concise limitations narrative in `results/logs/limitations.md` covering:
 1. Absence of baseline reaction‑time measures (if not available).
 2. Lack of physiological arousal proxies (if not available).
 3. Potential indoor/outdoor confound (referencing T033a/b outcome).
 4. Any missing demographic covariates.
 5. Methodological adaptations.
 6. **Specific response to review**: Discuss the impact of not having individual baseline RT or physiological proxies, and how the sensitivity analyses (T033e, T033g, T047a) mitigate this.
 **Dependencies**: T026, T033a, T033b, T033e, T033g, T047a.

- [ ] T054c [US3] **Hypothetical Sensitivity Analysis**: Conduct a hypothetical sensitivity analysis assuming baseline‑adjusted correlations and record min/max bias in `results/stats/sensitivity_hypothetical.json`. **Dependencies**: T026, T047.

- [ ] T054d [US3] **Generate Sensitivity Summary Table**: Generate a quantitative summary table in `results/stats/sensitivity_summary_table.csv` comparing the primary model results with alternative specifications. Ensure the final limitations document references all generated statistics and figures. **Dependencies**: T026, T033a, T033b, T033g, T047, T054a, T054b, T054c.

- [ ] T062 [US3] **Export All Results**: Consolidate all generated artifacts (logs, figures, stats) from `results/` into a final zip archive or ensure they are all present and checksummed. Verify that `results/stats/`, `results/figures/`, and `results/logs/` are complete. **(FR‑008)**. **Dependencies**: T026, T027, T028, T032, T033a, T033b, T035b, T047, T054a, T054b, T054c.
