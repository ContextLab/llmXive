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

- [X] T007 [P] Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`.

- [X] T008 [P] Initialize a Python project with dependencies (pandas, numpy, scikit‑learn, statsmodels, cdsapi, pyarrow, geopandas, matplotlib, seaborn, geopy, shapely, ruff, black). Generate `requirements.txt` and `pyproject.toml`.

- [X] T009 [P] **Configure Linting and Formatting**: Create `pyproject.toml` (including Black and Ruff sections) and `ruff.toml`. Verify with `ruff check.` and `black --check.` passes for `code/` and `tests/`. **(Executability Fix)**.

- [X] T009b [P] **Create Pydantic Models (Raw and Merged)**: Generate Pydantic model classes in `contracts/models.py` covering both:
 1. **Raw Models**: `MoralResponse` (`participant_id`, `latitude`, `longitude`, `timestamp`, `response_time`, `country`, `dilemma_id`) and `TemperatureRecord` (`grid_id`, `timestamp`, `latitude`, `longitude`, `temperature_celsius`).
 2. **Merged Model**: `MergedDataset` with fields from both raw models plus derived columns (`dilemma_choice`, `dilemma_complexity`, `time_of_day`, `temperature_celsius`, `participant_id`, `cultural_region`).
 **(Plan Structure Fix)**. **Dependencies**: T008.

- [X] T009c [P] **Generate JSON-Schemas**: Generate JSON-Schema contract files for each entity (`MoralResponse.schema.json`, `TemperatureRecord.schema.json`, `MergedDataset.schema.json`) under `contracts/` from the Pydantic models in `contracts/models.py` using the command: `python -c "from contracts.models import *; import json, pydantic; [json.dump(m.model_json_schema(), open(f'{m.__name__}.schema.json', 'w'), indent=2)) for m in [MoralResponse, TemperatureRecord, MergedDataset]]"`. **(Executability Fix)**. **Dependencies**: T009b.

- [X] T010 [P] Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** thresholds:
 1. `DISTANCE_THRESHOLD_KM = 100`
 2. `TEMPERATURE_MIN = -50.0`, `TEMPERATURE_MAX = 60.0`
 3. `RESPONSE_TIME_MIN_MS = 100`, `RESPONSE_TIME_MAX_MS = 10000`
 4. `ANDERSON_DARLING_SAMPLE_FRACTION` (deferred to implementation, referenced here)
 5. `AD_TEST_SEED` (deferred to implementation, referenced here)
 6. `BASELINE_TASK_ENABLED` (new: flag for optional baseline task)
 7. `BASELINE_TASK_URL` (new: URL for baseline reaction time task if available)
 8. `PHYSIO_PROXY_ENABLED` (new: flag for physiological proxy task)
 9. `PHYSIO_PROXY_URL` (new: URL for physiological proxy dataset if available)
 **(Executability Fix)**.

- [X] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`.

- [X] T012 [P] Create checksum generation and verification utilities in `code/utils.py` for files under `data/raw/` and `data/processed/`.

- [X] T013 [P] Create data loading utilities in `code/loaders.py` using `pandas` with a `load_chunked_parquet(path, chunk_size)` generator to handle large Parquet files without exceeding memory.

- [X] T013a [P] **Define Anderson‑Darling Sample Size**: Set `AD_TEST_SEED` and `AD_TEST_FRACTION` in `code/config.py` and document the configuration in `docs/research.md`. **Dependencies**: T010.

- [X] T014 [P] Setup pytest configuration for CPU‑only execution and stratified sampling.

---

## Phase 0: Data Availability & Validation (CRITICAL BLOCKER)

**Purpose**: Verify data sources, download, and validate resolution standards before any ingestion or modeling can occur.

**⚠️ CRITICAL**: No other tasks can begin until Phase 0 is complete and the data gap is resolved.

- [X] T000-init [S] **Download Moral Machine Dataset**: Implement `code/download_moral_machine.py` to:
 1. Fetch the canonical Moral Machine dataset from the specific GitHub mirror: `.
 2. Save to `data/raw/moral_machine.csv.gz`.
 3. Compute SHA-256 checksum and record in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`.
 4. **Verify Checksum**: Immediately verify the computed checksum against the `state` file. If mismatch, raise an exception and abort. **(Constitution Principle III)**.
 5. Log success/failure to `results/logs/data_validation_log.txt`. **(FR‑014, Constitution Principle II)**.
 6. **Completion Artifact**: File `data/raw/moral_machine.csv.gz` must exist with size > 0 and checksum verified.
 7. **Dependencies**: T007, T008.

- [X] T000b-init [S] **Download and Verify ERA5 Subset Checksum**: Implement `code/download_era_subset.py` (or extend T002b) to:
 1. Fetch the ERA5 data subset for 2014-2018 as defined in T002b.
 2. **Compute Checksum**: Compute the SHA-256 checksum of the *entire* fetched ERA5 subset (merged or all chunks).
 3. **Record Checksum**: Record the checksum in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under `artifact_hashes.era5_full_subset`.
 4. **Verify**: Verify the checksum against a known good value if available, or log the computed value for reproducibility.
 5. **Abort Condition**: If the checksum cannot be computed (e.g., empty file, missing data), raise an exception and abort.
 6. **Completion Artifact**: Checksum recorded in state file; `data/raw/era5_raw_chunks/` populated.
 7. **Dependencies**: T002a, T001-Validate-All-Sources.

- [X] T001-Validate-All-Sources [S] **Consolidated Data Validation**: Implement `code/validate_sources.py` to:
 1. Verify presence of required columns in `data/raw/moral_machine.csv.gz` (lat, lon, timestamp, response_time, country).
 2. Verify file integrity via SHA-256 checksum.
 3. Query CDS API metadata for `variable: '2m_temperature'`, `product_type: 'reanalysis'`, `year: ['2014','2015','2016','2017','2018']` and verify global grid coverage.
 4. Fetch a sample subset (Jan 1-7 2016, London) and validate hourly resolution and physical range.
 5. Log all results to `results/logs/data_validation_log.txt`.
 6. **Completion**: Log entry "All Sources Validated: PASS".
 7. **Dependencies**: T000-init, T000b-init, T008.

- [X] T003 [S] **Checksum ERA5 Sample File**: Compute SHA‑256 checksum of `data/raw/era5_sample.h5` and record it under `artifact_hashes.era5_sample` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`, updating `updated_at`. **(FR‑014, Principle V)**. **Dependencies**: T001-Validate-All-Sources.

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
 6. **Dependencies**: T002a, T001-Validate-All-Sources.

- [X] T002e-new [S] **Checksum ERA5 Subset**: Compute SHA‑256 checksum of `data/raw/era5_raw_chunks/` (merged) and record it under `artifact_hashes.era5_subset` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`. Also update the `updated_at` timestamp. **(FR‑014, Principle V)**. **Dependencies**: T002b.

- [X] T006 [S] **Pre‑Ingestion Validation Gate (All Sources)**: Aggregate results from T001-Validate-All-Sources, T000-init, and T000b-init.
 1. Verify `data/raw/moral_machine.csv.gz` exists and checksum matches.
 2. Verify `data/raw/era5_raw_chunks/` exists, is non-empty, and checksum matches `artifact_hashes.era5_full_subset`.
 3. **Explicit Check**: Verify that the checksum file for ERA5 exists and is not empty. If missing, raise an exception.
 4. If any validation fails, **raise an exception to abort the pipeline AND update the project state status to 'blocked'**.
 5. Log final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`.
 6. **Dependencies**: T001-Validate-All-Sources, T000-init, T000b-init.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes creation of the main ingestion script and data fetchers**.

- [X] T017-create [US1] **Create Ingestion Script**: Implement `code/ingestion.py` to define the logic for:
 1. Loading Moral Machine CSV.
 2. Filtering invalid response times (FR-010).
 3. Filtering temperature out-of-range (FR-002).
 4. Preparing for geospatial matching.
 **Output Artifact**: `data/processed/filtered_moral_machine.parquet`.
 **Dependencies**: T006, T007, T010.

- [X] T015 [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`. **Dependencies**: T017-create.

- [X] T016 [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`. **Dependencies**: T017-create.

- [X] T063-fix [US1] **Regenerate Baseline RT Fetcher**: Implement `code/download_baseline_rt.py` to:
 1. Check `code/config.py` for `BASELINE_TASK_URL`.
 2. If URL is invalid (empty, malformed), **log a warning** and set `baseline_available=False`. Proceed without data.
 3. If URL is valid, attempt to download the baseline reaction time dataset to `data/raw/baseline_rt.csv`.
 4. **Retry Logic**: On transient failure (timeout, 5xx), retry up to 3 times with exponential back-off.
 5. **Final State**: If the source is unavailable after retries, **log a warning** to `results/logs/baseline_fetch_log.txt` and set `baseline_available=False`. **DO NOT** raise an exception. Proceed without the data.
 6. **Dependencies**: T010, T000-init.

- [X] T064-fix [US1] **Regenerate Physiological Proxy Fetcher**: Implement `code/download_physio_proxy.py` to:
 1. Check `code/config.py` for `PHYSIO_PROXY_URL` or dataset ID.
 2. If URL is invalid (empty, malformed), **log a warning** and set `physio_available=False`. Proceed without data.
 3. If URL is valid, fetch the physiological arousal dataset to `data/raw/physio_proxy.csv`.
 4. **Retry Logic**: On transient failure (timeout, 5xx), retry up to 3 times with exponential back-off.
 5. **Final State**: If the source is unavailable after retries, **log a warning** to `results/logs/physio_fetch_log.txt` and set `physio_available=False`. **DO NOT** raise an exception. Proceed without the data.
 6. **Dependencies**: T010, T000-init.

- [X] T065 [US2] **Integrate Baseline RT into Model**: Update `code/modeling.py` to:
 1. Check for existence of `data/raw/baseline_rt.csv` and the `baseline_available` flag.
 2. If present, merge it into the main dataset.
 3. Include `baseline_response_time` as a fixed effect in the primary model.
 4. If absent, log a warning to `results/logs/limitations.md` but proceed with the standard model.
 5. **Dependencies**: T026, T063-fix.

- [X] T066 [US2] **Integrate Physiological Proxy into Model**: Update `code/modeling.py` to:
 1. Check for existence of `data/raw/physio_proxy.csv` and the `physio_available` flag.
 2. If present, merge it into the main dataset.
 3. Include `physiological_proxy` as a fixed effect in the primary model.
 4. If absent, log a warning to `results/logs/limitations.md` but proceed with the standard model.
 5. **Dependencies**: T026, T064-fix.

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Implementation for User Story 1

- [X] T017-run [US1] **Execute Ingestion Script (Location Filter)**: Run `code/ingestion.py` (created in T017-create) to:
 1. Load Moral Machine CSV from `data/raw/moral_machine.csv.gz`. **Column Mapping**: `lat` -> `latitude`, `lon` -> `longitude`, `response_time_ms` -> `response_time`.
 2. **Step 1: Count Capture**: Immediately after loading, count total records where `latitude` and `longitude` are not null. Log this value as `count_total_original_valid_location` to `results/logs/counts.json`. **(SC‑001)**.
 3. **HARD FILTER 1 (FR-010)**: Filter out records with missing latitude/longitude. **Log excluded records** to `results/logs/exclusion_log.csv` with reason "missing location". **Note**: This is distinct from distance filtering.
 4. **HARD FILTER 2 (FR-010)**: Filter out records with response times < 100 ms or > 10 000 ms. Log excluded records to `results/logs/exclusion_log.csv` with reason "invalid response time".
 5. **Prerequisite**: This filter MUST occur BEFORE any geospatial matching (T019) to prevent invalid records from being matched to temperature data.
 6. Count post-filter records → `count_filtered_for_analysis`.
 7. **Dependencies**: T017-create, T006, T007, T010.

- [X] T019 [US1] **Geospatial Matching & Exclusion**: Using `code/ingestion.py` (from T017-run), for each filtered Moral Machine record (with valid lat/lon):
 1. Find nearest ERA5 grid point.
 2. Log a pre‑exclusion match count `count_matched_pre_exclusion` to `results/logs/counts.json`.
 3. Calculate distance to nearest grid point.
 4. If distance > `DISTANCE_THRESHOLD_KM` (100km):
 a. **Exclude Immediately**: Do not include in the join.
 b. Set `match_quality = 'low'`, add entry to `results/logs/data_quality_log.json` with reason "distance > 100km".
 5. **Write Exclusion Log**: Immediately write the full exclusion log (including all flagged records) to `data/processed/data_quality_log.json`.
 6. **(FR‑009)**. **Dependencies**: T017-run, T002e-new.

- [X] T019a [US1] **Log Pre‑Exclusion Match Count**: Extract `count_matched_pre_exclusion` from T019 and write it to `results/logs/counts.json`. **Dependencies**: T019.

- [X] T019c-filter [US1] **Filter ERA5 Stream**: Implement `code/interpolation.py` to process the ERA5 data stream:
 1. **Filter**: Filter ERA5 raw data to only include the `grid_id` and `timestamp` range relevant to the Moral Machine records.
 2. **Output**: Write filtered stream to `data/processed/era5_filtered.parquet`.
 **(Edge Cases: Temperature Gap)**. **Dependencies**: T002e-new, T017-run, T019.

- [X] T019c-gap [US1] **Calculate Gaps**: Using `code/interpolation.py`, calculate the time difference between the ERA5 timestamp preceding and following the Moral Machine record for the specific grid cell.
 1. If gap > 2 hours → **exclude the record immediately** and log reason "temperature gap > 2 hours" to `results/logs/data_quality_log.json`.
 2. If no adjacent timestamp exists → **exclude** and log reason "no adjacent timestamp".
 3. **Output**: Write records with valid gaps to `data/processed/era5_valid_gaps.parquet`.
 **(Edge Cases: Temperature Gap)**. **Dependencies**: T019c-filter, T017-run.

- [X] T019c-interpolate [US1] **Interpolate Gaps**: Using `code/interpolation.py`, linearly interpolate missing values for gaps ≤ 2 hours using `pandas.DataFrame.interpolate(method='linear')`.
 1. **Output**: Write the clean, interpolated dataset to `data/processed/interpolated_data.parquet`.
 **(Edge Cases: Temperature Gap)**. **Dependencies**: T019c-gap, T017-run.

- [X] T017b [US1] **Validate Temperature Range**: Implement `code/ingestion.py` (or `code/preprocessing.py`) to:
 1. **Prerequisite**: This filter MUST be applied AFTER T019c-interpolate but BEFORE T019-join.
 2. Filter out records with `temperature_celsius` values outside the range defined by `code/config.py` keys `TEMPERATURE_MIN` and `TEMPERATURE_MAX` **from the interpolated stream**.
 3. **Abort Condition**: If the observed temperature range in the dataset exceeds the configured thresholds, the pipeline MUST ABORT.
 4. Log excluded records to `results/logs/exclusion_log.csv` with reason "temperature out of range". **(FR‑002)**. **Dependencies**: T019c-interpolate, T017-run.

- [X] T019-join [US1] **Geospatial Join Logic**: Implement `code/ingestion.py` to perform the explicit 'inner' join.
 1. **Input**: Filtered Moral Machine data (T017-run, T017b) and Interpolated Temperature data (T019c-interpolate).
 2. **Join Key**: `grid_id`, `timestamp`.
 3. **Join Type**: `inner`.
 4. **Filter**: Explicitly filter out records where `match_quality == 'low'` (from T019).
 5. **Output**: `data/processed/merged_dataset.parquet`.
 6. **Dependencies**: T017b, T019c-interpolate, T019.

- [X] T019b-finalize [US1] **Finalize Merged Dataset**: After the join (T019-join):
 1. **Input**: `data/processed/merged_dataset.parquet`.
 2. **Validate**: Ensure all required columns are present.
 3. **Save**: Write final `data/processed/merged_dataset.parquet`.
 4. **Dependencies**: T019-join.

- [X] T022a-retry [US1] **Regenerate Match Success Rate**: Compute SC‑001 as `(count_matched_pre_exclusion / count_total_original_valid_location) * 100`. Write the percentage to `results/logs/match_success_rate.json`. **Dependencies**: T017-run, T019a.

- [X] T028a [US1] **Fetch Demographic Covariates**:
 1. **Check**: Attempt to determine if individual-level age/gender data exists in the Moral Machine dataset.
 2. **If Individual Data Missing**: (Expected case) **Derive Country Key**: If the 'country' field is missing, use `geopy` (reverse geocoding) on `latitude`/`longitude` to derive the ISO-3 country code.
 3. **Fetch**: Fetch country-level aggregates from World Bank API: `https://api.worldbank.org/v2/country/all/indicator/SP.POP.DPGE,SP.DYN.LE00.IN?format=json`.
 4. **Parsing Logic**: Parse the JSON response to extract `age` and `gender` proxies (e.g., median age, population distribution) and map them to the `country` column in the merged dataset.
 5. **Handle Failure**: If API fails or country not found, **set columns to NaN**, log warning "Covariates missing for specific countries", and **proceed without them** (aligns with FR-004 "if available"). **Explicitly state**: T026 must handle NaN values by dropping or ignoring these covariates, not crashing.
 6. **Save**: If available, save to `data/processed/covariates.csv`.
 7. **Dependencies**: T017-run, T007.

- [X] T028a-retry [US1] **Regenerate Demographic Covariates**: Re-run T028a logic to ensure `data/processed/covariates.csv` is generated. **Dependencies**: T028a.

- [X] T028b [US1] **Derive Dilemma Choice**: From the filtered Moral Machine data (output of T017-run), create a categorical variable `dilemma_choice` (e.g., "save_many" vs "save_few") ensuring no use of `response_time` in its computation. Save to `data/processed/dilemma_choices.csv`. **Dependencies**: T017-run.

- [X] T028b-retry [US1] **Regenerate Dilemma Choice**: Re-run T028b logic to ensure `data/processed/dilemma_choices.csv` is generated. **Dependencies**: T028b.

- [X] T028c [US1] **Derive Dilemma Complexity**: Compute a static complexity score based on lives at stake and dilemma type, independent of response time. Save to `data/processed/dilemma_complexity.csv`. **Dependencies**: T017-run.

- [X] T028d [US1] **Derive Time‑of‑Day**: Extract hour of day from timestamps and categorize. Save to `data/processed/time_of_day.csv`. **Dependencies**: T017-run.

- [X] T028e [US1] **Validate Covariate Integrity**: Ensure all derived covariate files are complete, have no missing rows, and match the participant set. Log any issues to `results/logs/covariate_validation.json`. **Dependencies**: T028a, T028b, T028c, T028d.

- [X] T028f-integrate [US1] **Integrate Dilemma Choice into Merged Dataset**:
 1. **Input**: `data/processed/merged_dataset.parquet` (from T019b-finalize) and `data/processed/dilemma_choices.csv` (from T028b).
 2. **Action**: Merge `dilemma_choice` column into the merged dataset using `participant_id` or `dilemma_id`.
 3. **Output**: Write a **NEW** file `data/processed/merged_dataset_with_covariates.parquet`.
 4. **Verification**: Ensure no rows are dropped during merge; log any mismatches.
 5. **Generate Artifact**: Write a **preliminary** verification log to `results/logs/dilemma_choice_preliminary.json` confirming the merge was successful.
 6. **Generate Verification Log**: Explicitly generate `results/logs/dilemma_choice_verification.json` containing unit test results to confirm the merge and independence from response time.
 7. **Dependencies**: T019b-finalize, T028b.

- [X] T028g [US1] **Verify Dilemma Choice Derivation**:
 1. **Input**: `results/logs/dilemma_choice_verification.json` (from T028f-integrate).
 2. **Action**: Run a unit test to verify `dilemma_choice` creation does not reference `response_time` and that the resulting column is correctly merged as a fixed effect in the model specification (`code/modeling.py`).
 3. **Output**: Generate the final authoritative log `results/logs/dilemma_choice_verification.json` containing the unit test results.
 4. **Dependencies**: T028b, T019b-finalize, T028f-integrate.

- [X] T028h [US1] **Fetch Urban/Rural Proxy and Handle Failure**: Implement `code/fetch_urban_rural.py` to:
 1. Use `geopy` or `osmnx` to classify each unique coordinate as "urban" or "rural".
 2. **If Fetch Fails**: Set `urban_rural` column to NaN in the merged dataset, log "Urban/Rural proxy unavailable" to `results/logs/covariate_status.json`, and **write a status file** `results/logs/urban_rural_status.json` with `{"status": "unavailable"}`.
 3. **If Fetch Succeeds**: Save to `data/processed/urban_rural_proxy.csv` and write `results/logs/urban_rural_status.json` with `{"status": "available"}`.
 4. **Mandatory Trigger**: **IF** status file indicates "unavailable", **T033b MUST run** to quantify noise impact as required by FR-012.
 5. **Dependencies**: T019b-finalize, T028a, T033b.

- [X] T033a-setup [US3] **Implement CLI Stratify Argument**: Modify `code/modeling.py` to accept a `--stratify` argument.
 1. If `--stratify` is provided (e.g., `urban_rural`), split the dataframe by the specified column, run the model logic on each subset independently, and aggregate results.
 2. **Dependencies**: T026 (logic).

- [X] T033a [US1] **Indoor/Outdoor Confound Analysis (Proxy)**:
 1. **Input**: `data/processed/merged_dataset_with_covariates.parquet` (from T028f-integrate) and `data/processed/urban_rural_proxy.csv` (from T028h).
 2. **Action**: Stratify the merged dataset by `urban_rural` and **re-run the primary model logic** using the command `python code/modeling.py --stratify urban_rural` within each stratum independently. **Do not depend on T026 output**; execute the modeling step directly using the same data file as T026.
 3. **Fallback**: If T028h failed (NaNs present), log "Urban/Rural proxy unavailable" to `results/logs/limitations.md` and proceed to T033b (Bootstrap) without blocking.
 4. **Output**: Save results to `results/stats/indoor_outdoor_strata.json`.
 5. **Dependencies**: T019b-finalize, T028h, T028f-integrate, T033a-setup.

- [X] T033b [US1] **Indoor/Outdoor Confound Analysis (Bootstrap)**: **Run ONLY IF** `results/logs/urban_rural_status.json` indicates "unavailable" (i.e., T028h failed). Perform a bootstrap robustness check (resample with replacement, re-run model, report variance in coefficient) to quantify potential noise impact. **Mandatory Step**: Always report the limitation and quantify the potential noise impact in `results/logs/limitations.md` regardless of proxy availability. Save results to `results/stats/noise_impact.json`. **Dependencies**: T026, T056, T028h.

- [X] T033c [US1] **Baseline Reaction Time Task Integration**:
 1. **Check**: Check if `BASELINE_TASK_ENABLED` is True in `code/config.py`.
 2. **Verify Source**: Verify the canonical URL exists (e.g., `https://osf.io/...` - OSF Project: "Reaction-Time-Baseline" or similar verified source).
 3. **If Dataset Unavailable**: **Log a warning** (do not raise exception) and log "Baseline task data unavailable; proceeding without baseline adjustment" to `results/logs/baseline_status.json`. **(Review Concern: Baseline RT)**.
 4. **If Available**: Fetch the dataset and merge baseline RT to the main dataset using `participant_id`.
 5. **Dependencies**: T010, T019b-finalize.

- [X] T033d [US1] **Compute Temperature-Adjusted Response Times**: In `code/preprocessing.py`, calculate `adjusted_response_time` = `response_time` - `baseline_response_time` (if baseline exists) or `response_time` (if no baseline).
 1. **Order of Operations**: Explicitly subtract the baseline from the **raw** response time first. The log transformation (T025) will be applied to this `adjusted_response_time`.
 2. Log the proportion of records with and without baseline data.
 3. Save the adjusted dataset to `data/processed/adjusted_dataset.parquet`.
 4. **Dependencies**: T033c, T019b-finalize.

- [X] T033f [US1] **Attempt Physiological Proxy Fetch**:
 1. **Search**: Attempt to fetch a public dataset containing skin conductance or similar physiological arousal measures (e., via `datasets.load_dataset("physionet/EDA-Task")` or a specific OSF URL).
 2. **If Fetch Fails**: Log "Physiological proxy unavailable" to `results/logs/physio_status.json` and **do not** generate synthetic data. Proceed to sensitivity analysis (T047a) to quantify potential bias.
 3. **If Available**: Merge the proxy data to the main dataset using `participant_id` and save to `data/processed/physio_proxy.parquet`.
 4. **Dependencies**: T019b-finalize.

---

## Phase 3: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Implementation for User Story 2

- [X] T025 [US2] **Log‑Transformation & Fallback**: In `code/modeling.py`, log‑transform `response_time` (or `adjusted_response_time` if available). **Check**: Explicitly check for the existence of `adjusted_response_time` **before** applying the log transform. If T033d failed or was skipped, use `response_time`. If the LMM optimizer fails to converge within 10 iterations or raises a non-zero exit code, automatically switch to a GLMM with a log-link and Gamma family. **(FR‑003)**. **Dependencies**: T019b-finalize, T028a, T028h, T028f-integrate, T033d. **Note**: If T033d fails, this task proceeds with raw `response_time` without blocking.

- [X] T026 [US2] **Primary Mixed‑Effects Model**: Fit a linear mixed-effects model (or GLMM from T025) with:
 - Dependent variable: `log(response_time)` or `log(adjusted_response_time)` (if baseline available).
 - Fixed effects: `temperature_celsius`, `dilemma_complexity`, `time_of_day`, `dilemma_choice`, `age` and `gender` (if available, **handle NaNs by dropping rows or imputing**), `baseline_response_time` (if available), and `physiological_proxy` (if available). **Note**: `urban_rural` is **NOT** included as a fixed effect in the primary model (handled in T033a).
 - Random intercepts: `participant_id`, `cultural_region`
 - **Dependencies**: T025, T028f-integrate, T028a, T028b, T028c, T028d, T028h, T028f-integrate, T033d, T033f, T065, T066. Save model object and summary to `results/stats/model_results.json`. **(FR‑003, FR‑004, FR‑011, Review Concern: Baseline RT)**.

- [X] T027 [US2] **Likelihood‑Ratio Test**: Compare the full model (with temperature) to a null model (without temperature) and log test statistic and p-value to `results/stats/lrt.json`. **(FR‑005, SC‑002)**. **Dependencies**: T026.

- [X] T028 [US2] **Diagnostic Plots**: Generate QQ‑plot and residual‑vs‑fitted plot for model residuals; save PNGs to `results/figures/`. **(FR‑007, SC‑005)**. **Dependencies**: T026.

- [X] T028j [US2] **Anderson-Darling Test**: Extract residuals from the fitted model (T026), sample them using configuration values from `code/config.py` (deferred sample size/seed), and compute Anderson-Darling statistic; log p-value to `results/logs/ad_test.json`. **(SC‑005)**.
 1. **Verification Step**: If p-value < 0.05, set `status=warning` in `results/logs/ad_test.json` and log "Model residuals may not be normal" to `results/logs/processing_log.txt`.
 2. **Dependencies**: T026.

- [X] T032 [US2] **Export Model Coefficients**: Write fixed‑effect coefficients, standard errors, and p-values to `results/stats/model_coefficients.csv`. **Dependencies**: T026.

- [X] T033e [US2] **Baseline Adjustment Sensitivity**: Compare the temperature coefficient from the model with baseline adjustment (T026) against the model without baseline adjustment. Log the difference and statistical significance to `results/stats/baseline_adjustment_sensitivity.json`. **(Review Concern: Baseline RT)**. **Dependencies**: T026, T033d.

- [X] T033g [US2] **Physiological Proxy Sensitivity**: If a physiological proxy was available (T033f), compare the temperature coefficient from the model with the proxy against the model without it. Log the difference and potential bias to `results/stats/physio_adjustment_sensitivity.json`. **(Review Concern: Physiological Proxy)**. **Dependencies**: T026, T033f.

---

## Phase 3: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Implementation for User Story 3

- [X] T031a [US3] **Non‑Linearity Analysis**: Fit a preliminary model with a quadratic term (`temperature_celsius^2`) and a spline basis (using `patsy` or `scipy`). Compare AIC/BIC of both models against the linear-only model. Explicitly save both model results and the comparison metrics to `results/stats/nonlinearity_test.json`. **(FR‑013)**. **Dependencies**: T019b-finalize, T028a, T028h, T025, T026, T028f-integrate, T033d.

- [X] T035b [US3] **Distance Sensitivity Analysis**: Re‑run the matching step with alternative distance thresholds (e.g., varying spatial radii) and record how the temperature coefficient changes. Log results to `results/stats/distance_sensitivity.csv`. **Dependencies**: T019, T019b-finalize, T017b.

- [X] T047 [US3] **Temperature Outlier Threshold Sensitivity**: Sweep the outlier exclusion threshold over a range of low to high standard deviations in incremental steps. For each threshold, record the temperature coefficient and its p-value. Write a summary table to `results/stats/sensitivity_analysis.csv`. **(FR‑006)**. **Dependencies**: T026.

- [X] T047a [US3] **Physiological Arousal Proxy Sensitivity (Hypothetical)**: **Run ONLY IF** T033f failed (no proxy data). Perform a hypothetical sensitivity analysis assuming a range of arousal effects (e.g., temperature coefficient shifts by ±X% per unit of hypothetical arousal) and report the potential bias. Log results to `results/stats/arousal_proxy_sensitivity.json`. **(Review Concern: Physiological Proxy)**. **Dependencies**: T026, T033d, T033f.

---

## Phase 3.5: Preprocessing Wrapper (Moved from Phase 2)

**Purpose**: Quickstart wrapper for the full pipeline (moved to Phase 3.5 to align with dependencies).

- [X] T055 [US3] **Create Preprocessing Wrapper**: Implement `code/run_pipeline.py` to orchestrate the full pipeline (T017-run -> T019c -> T017b -> T019-join -> T026). **Dependencies**: T017-create, T019c-interpolate.

---

## Phase 4: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Document limitations, quantify noise, and provide a cohesive limitations section.

### Consolidated Limitation Task (Split)

- [X] T054a [US3] **Calculate ICC**: Extract variance component for the random intercept (Participant ID) from the fitted model (T026) and compute the Intraclass Correlation Coefficient (ICC); save to `results/stats/individual_variance.json`. **Dependencies**: T026.

- [X] T054b [US3] **Document Limitations Narrative**: Draft a concise limitations narrative in `results/logs/limitations.md` covering:
 1. Absence of baseline reaction‑time measures (if not available).
 2. Lack of physiological arousal proxies (if not available).
 3. Potential indoor/outdoor confound (referencing T033a/b outcome).
 4. Any missing demographic covariates.
 5. Methodological adaptations.
 6. **Specific response to review**: Discuss the impact of not having individual baseline RT or physiological proxies, and how the sensitivity analyses (T033e, T033g, T047a) mitigate this.
 **Dependencies**: T026, T033a, T033b, T033e, T033g, T047a.

- [X] T054b-retry [US3] **Regenerate Limitations Narrative**: Re-run T054b logic to ensure `results/logs/limitations.md` is generated. **Dependencies**: T054b.

- [X] T054c [US3] **Hypothetical Sensitivity Analysis**: Conduct a hypothetical sensitivity analysis assuming baseline‑adjusted correlations and record min/max bias in `results/stats/sensitivity_hypothetical.json`. **Dependencies**: T026, T047.

- [X] T054d [US3] **Generate Sensitivity Summary Table**: Generate a quantitative summary table in `results/stats/sensitivity_summary_table.csv` comparing the primary model results with alternative specifications. Ensure the final limitations document references all generated statistics and figures. **Dependencies**: T026, T033a, T033b, T033g, T047, T054a, T054b, T054c.

- [X] T062 [US3] **Export All Results**: Consolidate all generated artifacts (logs, figures, stats) from `results/` into a final zip archive or ensure they are all present and checksummed. Verify that `results/stats/`, `results/figures/`, and `results/logs/` are complete. **(FR‑008)**. **Dependencies**: T026, T027, T028, T032, T033a, T033b, T035b, T047, T054a, T054b, T054c.

---

## Phase 5: Review Resolution - Baseline & Physiological Confounds (Priority: P3 - Revision)

**Goal**: Address specific reviewer concerns regarding individual baseline reaction speed and physiological arousal proxies (Daniel Kahneman Simulated Review).

### Implementation for Review Resolution

- [X] T067 [US3] **Run Comparative Analysis with Baseline**: Execute a comparative analysis (T033e) specifically isolating the impact of adding `baseline_response_time` to the model. Report the change in the `temperature_celsius` coefficient and its significance. Save to `results/stats/baseline_impact_analysis.json`. **Dependencies**: T026, T065.

- [X] T068 [US3] **Run Comparative Analysis with Physiological Proxy**: Execute a comparative analysis (T033g) specifically isolating the impact of adding `physiological_proxy` to the model. Report the change in the `temperature_celsius` coefficient and its significance. Save to `results/stats/physio_impact_analysis.json`. **Dependencies**: T026, T066.

- [X] T069 [US3] **Synthesize Confound Mitigation Report**: Update `results/logs/limitations.md` to explicitly discuss:
 1. Whether baseline RT and physiological proxies were available.
 2. How their inclusion (or absence) affects the interpretation of the temperature coefficient.
 3. The results of T067 and T068.
 4. A final conclusion on the robustness of the temperature effect against these specific confounds.
 **Dependencies**: T067, T068, T054b.

---

## Phase 6: Review Resolution - Individual Baseline Noise (Priority: P3 - Revision)

**Goal**: Address the specific concern that individual differences in processing speed (System 1 vs System 2) confound the temperature effect, as highlighted in the Kahneman review.

### Implementation for Review Resolution

- [X] T070 [US3] **Implement Individual Baseline Noise Quantification**: In `code/modeling.py`, calculate the **residual variance** attributable to the random intercept (`participant_id`) from the primary model (T026). Compare this to the residual variance of a model where `baseline_response_time` (if available) is added. If baseline data is missing, **implement a simulation-based sensitivity analysis** (T071) to estimate how much individual noise could inflate the temperature coefficient. **Dependencies**: T026, T067, T068.

- [X] T071 [US3] **Simulate Individual Noise Impact (If Baseline Missing)**: **Run ONLY IF** T063-fix failed (no baseline data). Implement a Monte Carlo simulation in `code/simulations.py`:
 1. **Artifact Creation**: **If `code/simulations.py` does not exist**, create it and implement the simulation logic.
 2. **Assumption**: Assume a range of plausible standard deviations for individual baseline reaction times (e.g., small to large magnitudes).
 3. **Simulation**: For each assumed SD, generate synthetic "baseline" noise and add it to the observed response times.
 4. **Re-fit**: Re-fit the primary model for each simulation.
 5. **Record**: Record the shift in the `temperature_celsius` coefficient.
 6. **Reproducibility**: Use `AD_TEST_SEED` from `code/config.py` as the random seed for all iterations (1000 iterations).
 7. **Output**: Save the distribution of coefficient shifts to `results/stats/individual_noise_simulation.json`.
 8. **Explicitly state** in `results/logs/limitations.md` that the observed temperature effect is a "lower bound" if individual noise is positive. **Dependencies**: T026, T067.

- [X] T072 [US3] **Update Review Response in Limitations**: Update `results/logs/limitations.md` to include a dedicated section: **"Response to Kahneman Review: Individual Baseline Noise"**.
 1. Summarize the findings from T070 (actual residual variance) or T071 (simulated noise impact).
 2. Explicitly state whether the temperature effect remains significant after accounting for individual processing speed differences.
 3. If baseline data was unavailable, clearly articulate the magnitude of potential bias as quantified in T071.
 4. Conclude on the robustness of the findings against this specific confound.
 **Dependencies**: T070, T071, T054b, T069.

---

## Phase 7: Review Resolution - Physiological Arousal Mechanism (Priority: P3 - Revision)

**Goal**: Address the reviewer's specific suggestion to measure or proxy physiological arousal to disentangle direct temperature effects from general alertness modulation.

### Implementation for Review Resolution

- [X] T073 [US3] **Implement Physiological Arousal Proxy Simulation**: **Run ONLY IF** T064-fix failed (no physiological proxy data available). Implement a simulation in `code/simulations.py` (shared with T071) to model the impact of unmeasured physiological arousal.
 1. **Artifact Creation**: **If `code/simulations.py` does not exist**, create it and implement the simulation logic.
 2. **Assumption**: Define a plausible correlation range (e.g., 0.2 to 0.6) between ambient temperature and a latent physiological arousal variable.
 3. **Mechanism**: Assume this arousal variable has a linear effect on response time (faster RT with higher arousal).
 4. **Simulation**: For each correlation value in the range, generate a synthetic arousal variable, fit the primary model including this synthetic variable, and record the shift in the `temperature_celsius` coefficient.
 5. **Output**: Save the distribution of coefficient shifts to `results/stats/arousal_mechanism_simulation.json`.
 6. **Reproducibility**: Use `AD_TEST_SEED` from `code/config.py` as the random seed.
 7. **Dependencies**: T026, T033f.

- [X] T074 [US3] **Synthesize Physiological Mechanism Analysis**: Update `results/logs/limitations.md` to include a dedicated section: **"Response to Kahneman Review: Physiological Arousal Mechanism"**.
 1. Summarize the findings from T033f (actual proxy data if available) or T073 (simulated impact).
 2. Discuss whether the observed temperature effect is likely driven by direct thermal discomfort or mediated by general arousal/alertness.
 3. Quantify the potential bias if the arousal mechanism is ignored.
 4. Conclude on the robustness of the findings against this specific confound.
 **Dependencies**: T033f, T073, T069.

---

## Phase 8: Final Review Synthesis (Priority: P3 - Revision)

**Goal**: Consolidate all review responses into a single, coherent document.

### Implementation for Review Resolution

- [X] T075 [US3] **Finalize Limitations Document**: Merge all sections from T054b, T069, T072, and T074 into a single, comprehensive `results/logs/limitations.md`. Ensure all references to simulations, sensitivity analyses, and confound quantifications are consistent and cross-referenced. **Dependencies**: T054b, T069, T072, T074.

- [X] T076 [US3] **Generate Final Review Response Report**: Create a standalone report `results/logs/review_response_kahneman.md` that directly addresses the points raised in the `daniel-kahneman-simulated__2026-06-21__research.md` review. Structure the report to:
 1. Acknowledge the specific concerns (Baseline RT, Physiological Proxy).
 2. Detail the actions taken (Data fetching attempts, Simulation designs).
 3. Present the quantitative results (Coefficient shifts, Bias estimates).
 4. Provide the final conclusion on the validity of the temperature effect after accounting for these confounds.
 **Dependencies**: T075, T069, T072, T074.

- [X] T077 [US3] **Update Research Documentation**: Update `docs/research.md` to reflect the final methodology, including the simulation-based approaches for missing confounds and the specific limitations identified. **Dependencies**: T076.