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

- [X] T001c [P] **Validate Data Sources & ERA5 Citation**: Verify the canonical URL for the Copernicus Climate Data Store (CDS) API (`) for hourly near-surface temperature data. Implement logic in `code/validate_sources.py` to:
 1. Fetch ERA metadata (product_type, variable, grid_resolution) using the `cdsapi` library.
 2. Verify the Moral Machine dataset URL (`https://osf.io/...`) and required columns (`latitude`, `longitude`, `timestamp`, `response_time`, `country`, `dilemma_id`).
 3. Implement the specific 'Title-token-overlap' verification logic against the primary source as mandated by Constitution Principle II (Verified Accuracy): Calculate Jaccard similarity of title tokens between the cited source and the primary source; require score >= 0.7.
 4. Log all validation results to `results/logs/data_validation_log.txt`. **(FR‑014, Constitution Principle II)**.

- [ ] T001b [P] **Ingest & Validate ERA5 Sample**: Write `code/validate_era5.py` to fetch a **specific sample subset** (Jan 1 – Jan 7 2016) for London (51.5074, ‑0.1278) using the CDS API with `product_type='reanalysis'`, `variable='2m_temperature'`, and `grid_resolution='0.25 (Wikipedia: Atmospheric correction for interferometric synthetic aperture radar technique, https://en.wikipedia.org/wiki/Atmospheric_correction_for_interferometric_synthetic_aperture_radar_technique)'`. Save to `data/raw/era5_sample.h5` (HDF5 format with compression). Validate that the file contains hourly resolution, a floating-point data type, and temperature values within a physically plausible range. Log success/failure to `results/logs/data_validation_log.txt`. **(FR‑014, US‑1)**.

- [X] T002c [P] **Execute Full ERA5 Fetch**: Run `code/fetch_era_full.py` to download the full multi‑year ERA temperature dataset. The script:
 1. Reads `data/external/bounding_box.json` (schema: `{ "min_lat":..., "max_lat":..., "min_lon":..., "max_lon":... }`).
 2. Requests tiles of moderate spatial extent using `shapely.geometry.box`.
 3. Streams each tile to disk as Parquet chunks to stay within RAM limits.
 4. Implements exponential back‑off for CDS rate limits.
 5. Saves the combined result to `data/raw/era5_full.h5`.
 6. Verifies file existence, non‑zero size, and at least one row of data.
 **(FR‑001)**.
 *Note*: Unit‑test task T002b_test is optional and does **not** block this step.

- [ ] T002d [P] **Checksum Full ERA5 File**: Compute SHA‑256 checksum of `data/raw/era5_full.h5` and record it under `artifact_hashes.era5_full` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`. Also update the `updated_at` timestamp in the same YAML file. **(FR‑014, Principle V)**.

- [ ] T003 [P] **Checksum ERA5 Sample File**: Compute SHA‑256 checksum of `data/raw/era5_sample.h5` and record it under `artifact_hashes.era5_sample` in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`, updating `updated_at`. **(FR‑014, Principle V)**.

- [X] T004 [P] **Validate ERA5 Sample Integrity**: Programmatically confirm that `era5_sample.h5` meets hourly temporal resolution and grid size standards (fixed resolution). Log Pass/Fail to `results/logs/data_validation_log.txt`. **(FR‑014)**.

- [ ] T006 [P] **Pre‑Ingestion Validation Gate**: Aggregate results from T001c, T001b, T004, and verify that `data/raw/era5_full.h5` exists. If any validation fails, raise an exception to abort the pipeline. Log final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`. **Dependencies**: T001c, T001b, T004, T002c.

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
 4. `ANDERSON_DARLING_SAMPLE_FRACTION = 0.1` (see T013a)
 **(Executability Fix)**.

- [X] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`.

- [X] T012 [P] Implement checksum generation and verification utilities in `code/utils.py` for files under `data/raw/` and `data/processed/`.

- [X] T013 [P] Create data loading utilities in `code/loaders.py` using `pandas` with a `load_chunked_parquet(path, chunk_size)` generator to handle large Parquet files without exceeding memory.

- [X] T013a [P] **Define Anderson‑Darling Sample Size**: Set a sampling fraction in `code/config.py` and document the configuration in `docs/research.md`.

- [X] T014 [P] Setup pytest configuration for CPU‑only execution and stratified sampling.

- [ ] T028a [P] **Check and Fetch Demographic Covariates**: Retrieve age, gender, and urban/rural classification from the World Bank API (` for population, `PD.SEX.TOTL.ZS` for gender). Verify presence of `age` and `gender` fields. If the API returns country-level aggregates that cannot be merged with individual-level Moral Machine data, log the mismatch to `results/logs/covariate_status.json`, skip merging individual-level data, and proceed with available aggregate data or nulls. Save available covariates to `data/processed/covariates.csv`. **(FR‑004, Assumptions)**. **Dependencies**: T006.

- [X] T028b [P] **Derive Dilemma Choice**: From the filtered Moral Machine data (output of T017), create a categorical variable `dilemma_choice` (e.g., "save_many" vs. "save_few") ensuring no use of `response_time` in its computation. Save to `data/processed/dilemma_choices.csv`. **Dependencies**: T017.

- [X] T028c [P] **Derive Dilemma Complexity**: Compute a static complexity score based on lives at stake and dilemma type, independent of response time. Save to `data/processed/dilemma_complexity.csv`. **Dependencies**: T017.

- [X] T028d [P] **Derive Time‑of‑Day**: Extract hour of day from timestamps and categorize (e.g., "morning", "afternoon", "evening", "night"). Save to `data/processed/time_of_day.csv`. **Dependencies**: T017.

- [X] T028e [P] **Validate Covariate Integrity**: Ensure all derived covariate files are complete, have no missing rows, and match the participant set. Log any issues to `results/logs/covariate_validation.json`. **Dependencies**: T028a, T028b, T028c, T028d.

- [X] T028f [P] **Integrate Dilemma Choice for Modeling**: Merge `dilemma_choice` into the primary processing pipeline (used by modeling). **Dependencies**: T028b.

- [ ] T028g [P] **Verify Dilemma Choice Derivation**: Unit‑test that `dilemma_choice` creation does not reference `response_time` and that the resulting column is correctly merged as a fixed effect in the model specification (`code/modeling.py`). Log verification result to `results/logs/dilemma_choice_verification.json`. **Dependencies**: T028b, T019b.

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL)

- [X] T015 [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`.

- [ ] T016 [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`.

### Implementation for User Story 1

- [ ] T017 [US1] **Load, Filter & Count**: Implement `code/ingestion.py` to:
 1. Load Moral Machine CSV from `data/raw/moral_machine.csv.gz`. **Column Mapping**: `lat` -> `latitude`, `lon` -> `longitude`, `response_time_ms` -> `response_time`.
 2. **HARD FILTER**: Immediately filter out records with response times < 100 ms or > 10 000 ms. Log excluded records to `results/logs/exclusion_log.csv` with reason "invalid response time". **(FR‑002, Edge Cases)**.
 3. Count total records with non‑null latitude/longitude → `count_total_valid_location` (log to `results/logs/counts.json`).
 4. Filter out records with missing location data.
 5. Log post‑filter count as `count_filtered_for_analysis`.
 6. **(FR‑002)**. **Dependencies**: T010, T006.

- [ ] T017b [US1] **Validate Temperature Range**: Implement `code/ingestion.py` (or `code/preprocessing.py`) to:
 1. Filter out records with temperature values outside the range of extreme cold to extreme heat (e.g., < -50°C or > 60°C) as defined in `code/config.py`.
 2. Log excluded records to `results/logs/exclusion_log.csv` with reason "temperature out of range". **(FR‑002)**. **Dependencies**: T006.

- [ ] T019 [US1] **Geospatial Matching & Flagging**: Using `code/ingestion.py`, for each filtered Moral Machine record (output of T017):
 1. Find nearest ERA5 grid point.
 2. Log a pre‑exclusion match count `count_matched_pre_exclusion` (records with any grid match, regardless of distance) to `results/logs/counts.json`.
 3. If distance > `DISTANCE_THRESHOLD_KM`, set `match_quality = 'low'`, add entry to `results/logs/data_quality_log.json` with reason "distance > 100km".
 4. Do **not** yet exclude; just flag.
 **(FR‑009)**. **Dependencies**: T017, T002c.

- [X] T019a [US1] **Log Pre‑Exclusion Match Count**: Extract `count_matched_pre_exclusion` from T019 and write it to `results/logs/counts.json` (ensuring the key exists for downstream SC‑001 calculation). **Dependencies**: T019.

- [ ] T019c [US1] **Interpolate & Flag Gaps**: Implement `code/interpolation.py` to process the ERA5 data stream (or merged subset):
 1. Identify temperature gaps for each record.
 2. If gap ≤ 2 hours → linearly interpolate.
 3. If gap > 2 hours → **exclude** the record and log reason "temperature gap > 2 hours" to `results/logs/data_quality_log.json`.
 4. Flag records with unresolvable gaps.
 **(FR‑010)**. **Dependencies**: T002c.

- [ ] T019b [US1] **Final Merge of Valid Records**: After flagging (T019) and gap filtering (T019c), exclude records where `match_quality == 'low'` or where temperature interpolation failed. Merge the remaining Moral Machine records with ERA5 temperature data, producing `data/processed/merged_dataset.parquet`. **Dependencies**: T019, T019c, T028b‑f (derived covariates).

- [X] T022a [US1] **Calculate Match Success Rate**: Compute SC‑001 as
 `(count_matched_pre_exclusion / count_total_valid_location) * 100`
 using values from `results/logs/counts.json`. Write the percentage to `results/logs/match_success_rate.json`. **Dependencies**: T017, T019a.

---

## Phase 3: User Story 2 - Mixed‑Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p‑value for the fixed effect.

### Tests for User Story 2 (OPTIONAL)

- [ ] T023 [US2] Unit test for log‑transformation and outlier handling in `tests/test_modeling.py`.

- [ ] T024 [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`.

### Implementation for User Story 2

- [ ] T025 [US2] **Log‑Transformation & Fallback**: In `code/modeling.py`, log‑transform `response_time`. If optimizer fails (non‑zero exit code or > 10 iterations), automatically switch to a GLMM with a log‑link and Gamma family. **(FR‑003)**. **Dependencies**: T019b, T028a‑f.

- [X] T026 [US2] **Primary Mixed‑Effects Model**: Fit a linear mixed‑effects model (or GLMM from T025) with:
 - Dependent variable: `log(response_time)`
 - Fixed effects: `temperature_celsius`, `age` (if present), `gender` (if present), `dilemma_complexity`, `time_of_day`, `dilemma_choice`
 - Random intercepts: `participant_id`, `cultural_region`
 Save model object and summary to `results/stats/model_results.json`. **(FR‑003, FR‑004, FR‑011)**. **Dependencies**: T025, T028a‑f, T019b, T028g.

- [X] T027 [US2] **Likelihood‑Ratio Test**: Compare the full model (with temperature) to a null model (without temperature) and log test statistic and p‑value to `results/stats/lrt.json`. **(FR‑005, SC‑002)**. **Dependencies**: T026.

- [X] T028 [US2] **Diagnostic Plots**: Generate QQ‑plot and residual‑vs‑fitted plot for model residuals; save PNGs to `results/figures/`. **(FR‑007, SC‑005)**. **Dependencies**: T026.

- [X] T028b [US2] **Anderson‑Darling Test**: Sample [deferred] of residuals (per `ANDERSON_DARLING_SAMPLE_FRACTION`) and compute Anderson‑Darling statistic; log p‑value to `results/logs/ad_test.json`. **(SC‑005)**. **Dependencies**: T026.

- [X] T031 [US2] **Non‑Linearity Test (OR)**: Implement **either** a quadratic term (`temperature_celsius^2`) **or** a spline basis (using `patsy` or `scipy`). Compare AIC/BIC against the linear‑only model and log the result to `results/stats/nonlinearity_test.json`. **(FR‑013)**. **Dependencies**: T026.

- [X] T032 [US2] **Export Model Coefficients**: Write fixed‑effect coefficients, standard errors, and p‑values to `results/stats/model_coefficients.csv`. **Dependencies**: T026, T031.

---

## Phase 3: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL)

- [ ] T044 [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`.

- [ ] T045 [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`.

### Implementation for User Story 3

- [ ] T056 [US3] **Create Robustness Module**: Create `code/robustness.py` as a distinct module to house all sensitivity analysis logic (T033, T035b, T047). Ensure the plan's structural intent is met. **(Plan Structure Fix)**. **Dependencies**: T026.

- [ ] T033 [US3] **Indoor/Outdoor Confound Analysis**: Using urban/rural proxy from T028a (if available), stratify the merged dataset and re‑run the primary model within each stratum. If proxy unavailable, log limitation to `results/logs/indoor_outdoor_limitation.json` and **quantify potential noise impact via a bootstrap robustness check** (resample with replacement, re-run model, report variance in coefficient). **(FR‑012)**. **Dependencies**: T019b, T026, T056.

- [ ] T035b [US3] **Distance Sensitivity Analysis**: Re‑run the matching step with alternative distance thresholds (e.g., varying spatial radii) and record how the temperature coefficient changes. Log results to `results/stats/distance_sensitivity.csv`. **Dependencies**: T019, T019b, T056.

- [ ] T047 [US3] **Temperature Outlier Threshold Sensitivity**: Sweep the outlier exclusion threshold over a sensible range (e.g., one to several standard deviations) and for each threshold record the temperature coefficient and its p‑value. Write a summary table to `results/stats/sensitivity_analysis.csv` with columns `threshold_sd`, `coefficient`, `p_value`. **(FR‑006)**. **Dependencies**: T026, T056.

---

## Phase 4: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Document limitations, quantify noise, and provide a cohesive limitations section.

### Consolidated Limitation Task

- [ ] T054 [US3] **Document Limitations & Quantify Noise**: Perform the following steps in a single cohesive workflow:
 1. Extract variance component for the random intercept (Participant ID) from the fitted model (T026) and compute the Intraclass Correlation Coefficient (ICC); save to `results/stats/individual_variance.json`.
 2. Draft a concise limitations narrative in `results/logs/limitations.md` covering:
 - Absence of baseline reaction‑time measures.
 - Lack of physiological arousal proxies.
 - Potential indoor/outdoor confound (referencing T033 outcome).
 - Any missing demographic covariates (from T028a status log).
 3. Conduct a hypothetical sensitivity analysis assuming baseline‑adjusted correlations (r = 0.0, 0.1, 0.2, 0.3) to estimate possible bias: `bias = r * (std_temp / std_response)`. Record min/max bias in `results/stats/sensitivity_hypothetical.json`.
 4. **Generate a quantitative summary table** in `results/stats/sensitivity_summary_table.csv` comparing the primary model results (T026) with alternative specifications (T033, T035b, T047) to satisfy SC‑003.
 5. Ensure the final limitations document references all generated statistics and figures, providing a single source of truth.
 **(FR‑012, FR‑014, Constraint Preservation)**. **Dependencies**: T026, T047, T033, T057, T058.

- [ ] T062 [US3] **Export All Results**: Consolidate all generated artifacts (logs, figures, stats) from `results/` into a final zip archive or ensure they are all present and checksummed as per FR-008. Verify that `results/stats/`, `results/figures/`, and `results/logs/` are complete. **(FR‑008)**. **Dependencies**: T026, T027, T028, T032, T033, T035b, T047, T054.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T055 [P] **Create Preprocessing Wrapper**: Create `code/preprocessing.py` as a wrapper script that calls the necessary functions from `code/ingestion.py` to satisfy the quickstart run-book command `python code/preprocessing.py`. **(Executability Fix)**. **Dependencies**: T017, T019c.

- [ ] T056 [P] **Create Robustness Wrapper**: Create `code/robustness.py` as a wrapper script that calls the necessary functions from `code/robustness.py` (T033, T035b, T047) to satisfy the quickstart run-book command `python code/robustness.py`. **(Executability Fix)**. **Dependencies**: T026, T033, T035b, T047.

---

## Phase 5: Review Resolution - Baseline & Arousal Confounds (Priority: P3 - Revision)

**Goal**: Address the specific review concern regarding individual baseline reaction speeds and physiological arousal proxies to reduce measurement noise.

**Independent Test**: Verify that the baseline-adjusted model produces a different coefficient estimate than the unadjusted model and that the new covariates (if available) are included.

### Implementation for Review Resolution

- [ ] T057 [US2-REV] **Baseline Reaction Time Proxy**: Implement a strategy to approximate individual baseline reaction times. Since the Moral Machine dataset lacks a separate baseline task, derive a proxy by calculating the **median response time per participant** across all dilemmas where the decision was "obvious" (defined as stake imbalance > 3:1 OR dilemma complexity score < 0.2, derived from T028c) to isolate general processing speed from moral deliberation. Save this `baseline_rt_proxy` to `data/processed/baseline_rt_proxy.csv`. **Dependencies**: T028c, T019b.

- [ ] T058 [US2-REV] **Temperature-Adjusted Response Time**: Create a new derived variable `adjusted_rt` in the merged dataset, calculated as `response_time - baseline_rt_proxy` (or log-transformed difference). Update the modeling pipeline to use `adjusted_rt` as the primary dependent variable in the mixed-effects model as an alternative specification. Save results to `results/stats/model_results_baseline_adjusted.json`. **(Review Concern: Baseline Confound)**. **Dependencies**: T057, T026.

- [ ] T059 [US2-REV] **Physiological Arousal Proxy Analysis**: Implement a robustness check using "Time of Day" and "Ambient Temperature" interaction terms as a proxy for physiological arousal (assuming higher heat + peak activity hours = higher arousal). Test if the interaction term `temperature * time_of_day` significantly predicts response time. If significant, report this as evidence of the arousal mechanism in `results/logs/arousal_proxy_analysis.json`. **(Review Concern: Arousal Proxy)**. **Dependencies**: T028d, T026.

- [ ] T060 [US3-REV] **Comparative Model Analysis**: Generate a comparison table in `results/stats/baseline_comparison.csv` contrasting the primary model (raw RT), the baseline-adjusted model (T058), and the arousal-proxied model (T059). Report the change in the `temperature_celsius` coefficient and its p-value across these specifications to quantify the impact of the confound. **(Review Concern: Quantify Noise Impact)**. **Dependencies**: T026, T058, T059.

- [ ] T061 [US3-REV] **Update Limitations Document**: Update `results/logs/limitations.md` to explicitly discuss the absence of a true physiological baseline task, the methodology used for the proxy (T057), and the results of the comparative analysis (T060) regarding the potential bias introduced by individual processing speed differences. **(Review Concern: Documentation)**. **Dependencies**: T054, T060.

- [ ] T063 [US3-REV] **Document Methodological Adaptation**: Explicitly document the derivation of the `baseline_rt_proxy` (T057) as a methodological adaptation to the spec's 'Assumptions' section (which stated no baseline task exists). Record the justification for this adaptation and its potential impact on the correlational design in `results/logs/methodological_adaptation.json`. **(Constraint Preservation)**. **Dependencies**: T057.