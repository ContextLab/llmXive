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

- [ ] T000 [S] **Download Moral Machine Dataset**: Implement `code/download_moral_machine.py` to:
 1. Fetch the canonical Moral Machine dataset from the direct GitHub mirror: ` (or use `kaggle-cli` if the direct link is unavailable).
 2. Save to `data/raw/moral_machine.csv.gz`.
 3. Compute SHA-256 checksum and record in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`.
 4. Log success/failure to `results/logs/data_validation_log.txt`. **(FR‑014, Constitution Principle II)**.

- [ ] T001a [S] **Validate Moral Machine Source & File**: Implement `code/validate_sources.py` to:
 1. Verify the URL ` is reachable.
 2. Verify the presence of required columns in `data/raw/moral_machine.csv.gz`: `latitude`, `longitude`, `timestamp`, `response_time`, `country`, `dilemma_id`.
 3. Validate file integrity via SHA-256 checksum against `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`.
 4. Log validation results to `results/logs/data_validation_log.txt`. **(FR‑014, US‑1)**. **Dependencies**: T000.

- [ ] T001b [S] **Ingest & Validate ERA5 Sample**: Write `code/validate_era5.py` to fetch a **specific sample subset** (Jan 1 – Jan 7 2016) for London (51.5074, ‑0.1278) using the CDS API with `product_type='reanalysis'`, `variable='2m_temperature'`, and `grid_resolution='fine'`.
 1. **Credentials**: Read API key from `$CDS_API_KEY` environment variable or `.cdsrc` file.
 2. Save to `data/raw/era5_sample.h5` (HDF5 format with compression).
 3. Validate that the file contains hourly resolution, a floating-point data type, and temperature values within a physically plausible range.
 4. Log success/failure to `results/logs/data_validation_log.txt`. **(FR‑014, US‑1)**.

- [ ] T001c [S] **Validate ERA5 Citation**: Verify the canonical URL for the Copernicus Climate Data Store (CDS) API. Implement logic in `code/validate_sources.py` to:
 1. Fetch ERA metadata (product_type, variable, grid_resolution) using the `cdsapi` library.
 2. Verify the API endpoint is reachable and returns valid metadata.
 3. Log all validation results to `results/logs/data_validation_log.txt`. **(FR‑014, Constitution Principle II)**.

- [ ] T002a [S] **Define ERA5 Bounding Box**: Create `data/external/bounding_box.json` with the global extent required for Moral Machine data (approx. Lat: southern mid to high latitudes to 80, Lon: global longitudinal coverage) or a specific subset if known.
 1. Schema: `{ "min_lat": -60.0, "max_lat": 80.0, "min_lon": -180.0, "max_lon": 180.0 }`.
 2. Log creation to `results/logs/bbox_status.json`. **(FR‑001)**.

- [ ] T002c [S] **Fetch ERA5 Full Dataset**: Run `code/fetch_era_full.py` to initiate the download of the full multi‑year ERA temperature dataset (-2018).
 1. Reads `data/external/bounding_box.json` (schema: `{ "min_lat":..., "max_lat":..., "min_lon":..., "max_lon":... }`).
 2. **Tile Strategy**: Split the global extent into fixed-degree lat/lon boxes using `shapely.geometry.box` to create manageable tiles.
 3. Requests tiles of moderate spatial extent using the CDS API.
 4. **Credentials**: Read API key from `$CDS_API_KEY` environment variable or `.cdsrc` file.
 5. Implements exponential back‑off for CDS rate limits.
 6. Outputs a list of requested tiles and status to `results/logs/fetch_status.json`.
 7. Saves raw chunks to `data/raw/era5_raw_chunks/`.
 **(FR‑001)**. **Dependencies**: T002a.

- [ ] T002d [S] **Stream & Save ERA5 Chunks**: Run `code/stream_era5.py` to process the tiles from T002c.
 1. **Input**: Read the list of requested tiles and status from `results/logs/fetch_status.json` generated by T002c.
 2. Streams each tile from `data/raw/era5_raw_chunks/` to disk as Parquet chunks to stay within RAM limits.
 3. Concatenates chunks into `data/raw/era5_full.parquet`.
 4. **Missing Artifact Handling**: If `data/raw/era5_full.parquet` is missing, re-execute the fetch with deterministic seeds and parameters; do NOT raise an exception.
 5. Verifies file existence and non-zero size.
 **(FR‑001)**. **Dependencies**: T002c.

- [ ] T002e [S] **Checksum Full ERA5 File**: Compute SHA‑256 checksum of `data/raw/era5_full.parquet` and record it under `artifact_hashes.era5_full` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`. Also update the `updated_at` timestamp in the same YAML file. **(FR‑014, Principle V)**. **Dependencies**: T002d.

- [ ] T003 [S] **Checksum ERA5 Sample File**: Compute SHA‑256 checksum of `data/raw/era5_sample.h5` and record it under `artifact_hashes.era5_sample` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`, updating `updated_at`. **(FR‑014, Principle V)**. **Dependencies**: T001b.

- [ ] T004 [S] **Validate ERA5 Sample Integrity**: Programmatically confirm that `era5_sample.h5` meets hourly temporal resolution and grid size standards (fixed resolution). Log Pass/Fail to `results/logs/data_validation_log.txt`. **(FR‑014)**. **Dependencies**: T001b.

- [ ] T006 [S] **Pre‑Ingestion Validation Gate (All Sources)**: Aggregate results from T001a, T001b, T001c, T002c, T002d, T002e, T003, T004, and verify that `data/raw/era5_full.parquet` and `data/raw/moral_machine.csv.gz` exist. If any validation fails, raise an exception to abort the pipeline. Log final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`. **Dependencies**: T000, T001a, T001b, T001c, T002c, T002d, T002e, T003, T004.

**Checkpoint**: Data validation complete. If Pass, proceed to Phase 1. If Fail, project is blocked.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T007 [P] Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`.

- [X] T008 [P] Initialize a Python project with dependencies (pandas, numpy, scikit‑learn, statsmodels, cdsapi, pyarrow, matplotlib, seaborn, geopandas, shapely, ruff, black). Generate `requirements.txt` and `pyproject.toml`.

- [X] T009 [P] **Configure Linting and Formatting**: Create `pyproject.toml` (including Black and Ruff sections) and `ruff.toml`. Verify with `ruff check.` and `black --check.` passes for `code/` and `tests/`. **(Executability Fix)**.

- [X] T009b [P] **Create Pydantic Models**: Generate Pydantic model classes in `contracts/models.py` with fields:
 - MoralResponse: `participant_id`, `latitude`, `longitude`, `timestamp`, `response_time`, `country`, `dilemma_id`.
 - TemperatureRecord: `grid_id`, `timestamp`, `latitude`, `longitude`, `temperature_celsius`.
 - MergedDataset: all fields from both plus derived columns (`dilemma_choice`, `dilemma_complexity`, `time_of_day`, etc.). **(Plan Structure Fix)**.

- [X] T009c [P] **Generate JSON-Schemas**: Generate JSON-Schema contract files for each entity (`MoralResponse.schema.json`, `TemperatureRecord.schema.json`, `MergedDataset.schema.json`) under `contracts/` from the Pydantic models in `contracts/models.py`. **(Plan Structure Fix)**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T010 [P] Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** thresholds:
 1. `DISTANCE_THRESHOLD_KM = 100`
 2. `TEMPERATURE_MIN = -50.0`, `TEMPERATURE_MAX = 60.0`
 3. `RESPONSE_TIME_MIN_MS = 100`, `RESPONSE_TIME_MAX_MS = 10000`
 4. `ANDERSON_DARLING_SAMPLE_FRACTION = 0.1`
 5. `AD_TEST_SEED = 42`
 6. `AD_TEST_FRACTION = 0.1`
 **(Executability Fix)**.

- [X] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`.

- [X] T012 [P] Implement checksum generation and verification utilities in `code/utils.py` for files under `data/raw/` and `data/processed/`.

- [X] T013 [P] Create data loading utilities in `code/loaders.py` using `pandas` with a `load_chunked_parquet(path, chunk_size)` generator to handle large Parquet files without exceeding memory.

- [X] T013a [P] **Define Anderson‑Darian Sample Size**: Set `AD_TEST_SEED=42` and `AD_TEST_FRACTION=0.1` in `code/config.py` and document the configuration in `docs/research.md`. **Dependencies**: T010.

- [X] T014 [P] Setup pytest configuration for CPU‑only execution and stratified sampling.

- [ ] T055 [P] **Create Preprocessing Wrapper**: Create `code/preprocessing.py` as a wrapper script that calls the necessary functions from `code/ingestion.py` to satisfy the quickstart run-book command `python code/preprocessing.py`. **(Executability Fix)**. **Dependencies**: T017, T019c.

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL)

- [ ] T015 [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`.

- [ ] T016 [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`.

### Implementation for User Story 1

- [ ] T017 [US1] **Load, Filter & Count**: Implement `code/ingestion.py` to:
 1. Load Moral Machine CSV from `data/raw/moral_machine.csv.gz`. **Column Mapping**: `lat` -> `latitude`, `lon` -> `longitude`, `response_time_ms` -> `response_time`.
 2. **HARD FILTER 1**: Immediately filter out records with missing latitude/longitude. Log excluded records to `results/logs/exclusion_log.csv` with reason "missing location".
 3. **HARD FILTER 2**: Filter out records with response times < 100 ms or > 10 000 ms. Log excluded records to `results/logs/exclusion_log.csv` with reason "invalid response time". **(FR‑002, Edge Cases)**.
 4. Count post-filter records → `count_filtered_for_analysis`.
 5. **(FR‑002)**. **Dependencies**: T006.

- [ ] T017a [US1] **Capture Pre-Filter Count**: Implement `code/ingestion.py` to capture the count of records with valid latitude/longitude **BEFORE** T017's filtering.
 1. Count total records where `latitude` and `longitude` are not null.
 2. Log this value as `count_total_original_valid_location` to `results/logs/counts.json`.
 3. **(SC‑001)**. **Dependencies**: T006.

- [ ] T017b [US1] **Validate Temperature Range**: Implement `code/ingestion.py` (or `code/preprocessing.py`) to:
 1. Filter out records with `temperature_celsius` values outside the range defined by `code/config.py` keys `TEMPERATURE_MIN` and `TEMPERATURE_MAX`.
 2. Log excluded records to `results/logs/exclusion_log.csv` with reason "temperature out of range". **(FR‑002)**. **Dependencies**: T006.

- [ ] T019 [US1] **Geospatial Matching & Flagging**: Using `code/ingestion.py`, for each filtered Moral Machine record (output of T017):
 1. Find nearest ERA5 grid point.
 2. Log a pre‑exclusion match count `count_matched_pre_exclusion` (records with any grid match, regardless of distance) to `results/logs/counts.json`.
 3. If distance > `DISTANCE_THRESHOLD_KM` (from `code/config.py`), set `match_quality = 'low'`, add entry to `results/logs/data_quality_log.json` with reason "distance > 100km".
 4. Do **not** yet exclude; just flag.
 **(FR‑009)**. **Dependencies**: T017, T002d.

- [X] T019a [US1] **Log Pre‑Exclusion Match Count**: Extract `count_matched_pre_exclusion` from T019 and write it to `results/logs/counts.json` (ensuring the key exists for downstream SC‑001 calculation). **Dependencies**: T019.

- [ ] T019c [US1] **Interpolate & Flag Gaps**: Implement `code/interpolation.py` to process the ERA5 data stream (or merged subset):
 1. **Filter**: Filter the ERA5 raw data (from `data/raw/era5_full.parquet`) to only include the `grid_id` and `timestamp` range relevant to the Moral Machine records (from T017).
 2. **Gap Definition**: Calculate the time difference between the ERA5 timestamp preceding the Moral Machine record and the ERA5 timestamp following it for the specific grid cell.
 3. If gap ≤ 2 hours → linearly interpolate.
 4. If gap > 2 hours → **exclude** the record and log reason "temperature gap > 2 hours" to `results/logs/data_quality_log.json`.
 5. Flag records with unresolvable gaps.
 **(Edge Cases: Temperature Gap)**. **Dependencies**: T019, T002d.

- [ ] T019b [US1] **Final Merge of Valid Records**: After flagging (T019) and gap filtering (T019c), exclude records where `match_quality == 'low'` or where temperature interpolation failed. Merge the remaining Moral Machine records with ERA5 temperature data, producing `data/processed/merged_dataset.parquet`.
 1. **Merge Key**: `grid_id`, `timestamp`.
 2. **Join Type**: `inner`.
 3. **Filter**: Explicitly filter out records where `match_quality == 'low'`.
 4. **Fallback**: If covariate files (T028a-f) are missing, merge without them and log warning, but DO NOT fail the merge.
 **Dependencies**: T019, T019c, T028a-f (derived covariates).

- [X] T022a [US1] **Calculate Match Success Rate**: Compute SC‑001 as
 `(count_matched_pre_exclusion / count_total_original_valid_location) * 100`
 using values from `results/logs/counts.json` (T019a for numerator, T017a for denominator). Write the percentage to `results/logs/match_success_rate.json`. **Dependencies**: T017a, T019a.

- [ ] T028a [S] **Check and Fetch Demographic Covariates**: Retrieve age and gender proxies from the World Bank API using specific indicators (`SP.POP.TOTL` for total population, `SP.POP.TOTL.FE.ZS` for female population percentage).
 1. If country-level aggregates are available: Derive age/gender proxies (e.g., mean age, female % per country) and merge to the dataset using `country` code.
 2. If NO data is available for specific indicators: **Log the exclusion to `results/logs/covariate_status.json`** and **retain all records** for analysis, noting the missing covariate in `results/logs/model_specification.json`. Do not drop the variable from the model specification; drop the records only if the covariate is present but missing for a *specific row*, not the whole country.
 3. Save available covariates to `data/processed/covariates.csv`. **(FR‑004, Assumptions)**. **Dependencies**: T017, T007.

- [ ] T028b [S] **Derive Dilemma Choice**: From the filtered Moral Machine data (output of T017), create a categorical variable `dilemma_choice` (e.g., "save_many" vs. "save_few") ensuring no use of `response_time` in its computation. Save to `data/processed/dilemma_choices.csv`. **Dependencies**: T017.

- [ ] T028c [P] **Derive Dilemma Complexity**: Compute a static complexity score based on lives at stake and dilemma type, independent of response time. Save to `data/processed/dilemma_complexity.csv`. **Dependencies**: T017.

- [ ] T028d [P] **Derive Time‑of‑Day**: Extract hour of day from timestamps and categorize (e.g., "morning", "afternoon", "evening", "night"). Save to `data/processed/time_of_day.csv`. **Dependencies**: T017.

- [ ] T028e [P] **Validate Covariate Integrity**: Ensure all derived covariate files are complete, have no missing rows, and match the participant set. Log any issues to `results/logs/covariate_validation.json`. **Dependencies**: T028a, T028b, T028c, T028d.

- [ ] T028f [P] **Integrate Dilemma Choice for Modeling**: Merge `dilemma_choice` into the primary processing pipeline (used by modeling). **Dependencies**: T028b.

- [ ] T028g [P] **Verify Dilemma Choice Derivation**: Unit‑test that `dilemma_choice` creation does not reference `response_time` and that the resulting column is correctly merged as a fixed effect in the model specification (`code/modeling.py`). Log verification result to `results/logs/dilemma_choice_verification.json`. **Dependencies**: T028b, T019b.

---

## Phase 3: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Implementation for User Story 2

- [ ] T025 [US2] **Log‑Transformation & Fallback**: In `code/modeling.py`, log‑transform `response_time`. If optimizer fails (non-zero exit code or > 10 iterations), automatically switch to a GLMM with a log-link and Gamma family. **(FR‑003)**. **Dependencies**: T019b, T028a‑f.

- [ ] T026 [US2] **Primary Mixed‑Effects Model**: Fit a linear mixed-effects model (or GLMM from T025) with:
 - Dependent variable: `log(response_time)`
 - Fixed effects: `temperature_celsius`, `age` (if present), `gender` (if present), `dilemma_complexity`, `time_of_day`, `dilemma_choice`
 - Random intercepts: `participant_id`, `cultural_region`
 Save model object and summary to `results/stats/model_results.json`. **(FR‑003, FR‑004, FR‑011)**. **Dependencies**: T025, T028a‑f, T019b, T028g.

- [ ] T027 [US2] **Likelihood‑Ratio Test**: Compare the full model (with temperature) to a null model (without temperature) and log test statistic and p-value to `results/stats/lrt.json`. **(FR‑005, SC‑002)**. **Dependencies**: T026.

- [ ] T028 [US2] **Diagnostic Plots**: Generate QQ‑plot and residual‑vs‑fitted plot for model residuals; save PNGs to `results/figures/`. **(FR‑007, SC‑005)**. **Dependencies**: T026.

- [ ] T028b [US2] **Anderson‑Darling Test**: Extract residuals from the fitted model (T026), sample them using `AD_TEST_SEED=42` and `AD_TEST_FRACTION=0.1` (from T013a), and compute Anderson‑Darling statistic; log p-value to `results/logs/ad_test.json`. **(SC‑005)**. **Dependencies**: T026.

- [ ] T031 [US2] **Non‑Linearity Test (OR)**: Implement **either** a quadratic term (`temperature_celsius^2`) **or** a spline basis (using `patsy` or `scipy`). **Crucially, apply the quadratic/spline term to `temperature_celsius` BEFORE the log-transformation of the response time**. Compare AIC/BIC against the linear‑only model and log the result to `results/stats/nonlinearity_test.json`. **(FR‑013)**. **Dependencies**: T026.

- [ ] T032 [US2] **Export Model Coefficients**: Write fixed‑effect coefficients, standard errors, and p-values to `results/stats/model_coefficients.csv`. **Dependencies**: T026, T031.

### Tests for User Story 2 (OPTIONAL)

- [ ] T023 [US2] Unit test for log‑transformation and outlier handling in `tests/test_modeling.py`. **Dependencies**: T025.
- [ ] T024 [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`. **Dependencies**: T026.

---

## Phase 3: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL)

- [ ] T044 [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`.

- [ ] T045 [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`.

### Implementation for User Story 3

- [ ] T056 [S] **Create Robustness Module**: Create `code/robustness.py` as a distinct module to house all sensitivity analysis logic (T033, T035b, T047). Ensure the plan's structural intent is met. **(Plan Structure Fix)**. **Dependencies**: T026.

- [ ] T033a [US3] **Indoor/Outdoor Confound Analysis (Proxy)**: Using urban/rural proxy from T028a (if available), stratify the merged dataset and re‑run the primary model within each stratum. **Dependencies**: T019b, T026, T056.

- [ ] T033b [US3] **Indoor/Outdoor Confound Analysis (Bootstrap)**: If the urban/rural proxy is unavailable, perform a bootstrap robustness check (resample with replacement, re-run model, report variance in coefficient) to quantify potential noise impact. Save results to `results/stats/noise_impact.json`. **(FR‑012)**. **Dependencies**: T026, T056.

- [ ] T035b [US3] **Distance Sensitivity Analysis**: Re‑run the matching step with alternative distance thresholds (e.g., varying spatial radii) and record how the temperature coefficient changes. Log results to `results/stats/distance_sensitivity.csv`. **Dependencies**: T019, T019b, T056.

- [ ] T047 [US3] **Temperature Outlier Threshold Sensitivity**: Sweep the outlier exclusion threshold over a sensible range (e.g., one to several standard deviations) and for each threshold record the temperature coefficient and its p-value. Write a summary table to `results/stats/sensitivity_analysis.csv` with columns `threshold_sd`, `coefficient`, `p_value`. **(FR‑006)**. **Dependencies**: T026, T056.

---

## Phase 4: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Document limitations, quantify noise, and provide a cohesive limitations section.

### Consolidated Limitation Task (Split)

- [ ] T054a [US3] **Calculate ICC**: Extract variance component for the random intercept (Participant ID) from the fitted model (T026) and compute the Intraclass Correlation Coefficient (ICC); save to `results/stats/individual_variance.json`. **Dependencies**: T026.

- [ ] T054b [US3] **Document Limitations Narrative**: Draft a concise limitations narrative in `results/logs/limitations.md` covering:
 1. Absence of baseline reaction‑time measures.
 2. Lack of physiological arousal proxies.
 3. Potential indoor/outdoor confound (referencing T033a/b outcome).
 4. Any missing demographic covariates (from T028a status log).
 5. Methodological adaptations (referencing T057/T063 logic).
 **Dependencies**: T026, T033a, T033b, T028a.

- [ ] T054c [US3] **Hypothetical Sensitivity Analysis**: Conduct a hypothetical sensitivity analysis assuming baseline‑adjusted correlations (r = 0.0, 0.1, 0.2, 0.3) to estimate possible bias: `bias = r * (std_temp / std_response)`. Record min/max bias in `results/stats/sensitivity_hypothetical.json`. **Dependencies**: T026, T047.

- [ ] T054d [US3] **Generate Sensitivity Summary Table**: Generate a quantitative summary table in `results/stats/sensitivity_summary_table.csv` comparing the primary model results (T026) with alternative specifications (T033a, T033b, T035b, T047) to satisfy SC‑003. Ensure the final limitations document references all generated statistics and figures. **Dependencies**: T026, T047, T033a, T033b, T054a, T054b, T054c.

- [ ] T062 [US3] **Export All Results**: Consolidate all generated artifacts (logs, figures, stats) from `results/` into a final zip archive or ensure they are all present and checksummed as per FR-008. Verify that `results/stats/`, `results/figures/`, and `results/logs/` are complete. **(FR‑008)**. **Dependencies**: T026, T027, T028, T032, T033a, T033b, T035b, T047, T054a, T054b, T054c, T054d.

- [ ] T056b [P] **Create Robustness Wrapper**: Create `code/robustness_wrapper.py` as a wrapper script that calls the necessary functions from `code/robustness.py` (T033a, T033b, T035b, T047) to satisfy the quickstart run-book command `python code/robustness.py`. **(Executability Fix)**. **Dependencies**: T026, T033a, T033b, T035b, T047.

---

## Phase 5: Review Resolution - Baseline & Arousal Confounds (Priority: P3 - Revision)

**Goal**: Address the specific review concern regarding individual baseline reaction speeds and physiological arousal proxies to reduce measurement noise.

**Independent Test**: Verify that the baseline-adjusted model produces a different coefficient estimate than the unadjusted model and that the new covariates (if available) are included.

### Implementation for Review Resolution

- [ ] T057 [US2-REV] **Document Baseline & Arousal Limitations**: Explicitly document the absence of a true physiological baseline task and the decision to omit derived baseline metrics in `results/logs/limitations.md`.
 1. State that the Moral Machine dataset lacks a separate baseline task.
 2. Explain that deriving a `baseline_rt_proxy` was considered but **omitted** to adhere to Constraint Preservation (no unauthorized derived variables).
 3. Explain that while an interaction term `temperature * time_of_day` was considered, it was omitted to avoid creating unauthorized derived variables.
 4. Quantify the potential impact of these missing variables by referencing the sensitivity analysis results from T047, T033b, and T060.
 5. Reference the existing sensitivity analyses (T033a, T033b, T047) as the primary method for quantifying noise impact.
 **(Review Concern: Documentation, Constraint Preservation)**. **Dependencies**: T054b, T026.

- [ ] T060 [US3-REV] **Comparative Model Analysis**: Generate a comparison table in `results/stats/baseline_comparison.csv` contrasting the primary model (raw RT) and any alternative valid specifications (e.g., with/without specific covariates if data allowed).
 1. **Columns**: `model_name`, `temperature_coef`, `std_error`, `p_value`, `delta_coef`, `delta_p`.
 2. Report the change in the `temperature_celsius` coefficient and its p-value across these specifications to quantify the impact of the confound. **(Review Concern: Quantify Noise Impact)**. **Dependencies**: T026, T057.

- [ ] T061 [US3-REV] **Update Limitations Document**: Update `results/logs/limitations.md` to explicitly discuss the absence of a true physiological baseline task, the methodology used for the proxy (T057), and the results of the comparative analysis (T060) regarding the potential bias introduced by individual processing speed differences. **(Review Concern: Documentation)**. **Dependencies**: T054b, T060.

- [ ] T063 [US3-REV] **Document Methodological Adaptation**: Explicitly document the decision to omit derived baseline metrics (T057) as a methodological adaptation to the spec's 'Assumptions' section (which stated no baseline task exists). Record the justification for this adaptation and its potential impact on the correlational design in `results/logs/methodological_adaptation.json`. **(Constraint Preservation)**. **Dependencies**: T057.