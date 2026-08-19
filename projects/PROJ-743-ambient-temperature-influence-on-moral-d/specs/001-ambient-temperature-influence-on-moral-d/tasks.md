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

- [X] T001 [P] Verify the canonical URL for the Copernicus Climate Data Store (CDS) API for ERA hourly data and confirm accessibility (HTTP 200) using the `cdsapi` library configuration. Log the verification result (including API endpoint and status) to `results/logs/data_validation_log.txt`.
- [ ] T002 [P] Write a Python script `code/fetch_era_sample.py` to fetch a **specific sample subset** for validation: **Jan 1, 2016 to Jan 7, 2016** in **London (51.5N, -0.1W)**. Execute this script to fetch the sample to `data/raw/era_sample.h5`. Log success/fail to `results/logs/data_validation_log.txt`.
- [ ] T002b [P] Write a Python script `code/fetch_era_full.py` to fetch the **full 2014-2018 ERA5 2m temperature dataset** required for the primary analysis. The script MUST implement chunking by **10x10 degree tiles** to avoid single-call timeout and memory overflow. **Parameters**: Variable `2t`, Time range `2014-01-01` to `2018-12-31`, Area `Global` (-90 to 90, -180 to 180). The script MUST include **retry logic** for CDS API rate limits (exponential backoff) and stream data to disk in chunks to stay within the available RAM limit.
- [ ] T002b_test [P] Write unit tests in `tests/test_ingestion.py` for `code/fetch_era_full.py` logic. **Specifics**: Test function `test_chunking_strategy` asserts `chunk_count == expected` and `test_merge_logic` asserts `final_file.shape == expected_shape`. Test that the chunking strategy (10x10 tiles) produces the expected number of files, that the merge logic handles missing chunks gracefully, and that the final file size is within expected bounds.
- [ ] T002c [P] Execute the script from T002b to fetch the full dataset. **Execution Logic**: Run `fetch_era_full.py` which must fetch by year and tile (2014-2018), merge results, and save to `data/raw/era5_full.h5`. Log success/fail to `results/logs/data_validation_log.txt`.
- [ ] T002d [P] Compute and record the SHA-256 checksum of the downloaded full ERA5 file (`data/raw/era5_full.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_full`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [ ] T003 [P] Compute and record the SHA-256 checksum of the downloaded ERA5 sample file (`data/raw/era5_sample.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_sample`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [X] T004 [P] Programmatically validate that the downloaded ERA5 sample meets the hourly temporal resolution and geographic grid size standards defined in FR-014. Log validation status (Pass/Fail) to `results/logs/data_validation_log.txt`.
- [X] T005 [P] Verify the Moral Machine dataset source against the "Verified Accuracy" principle and log the validation status to `results/logs/data_validation_log.txt` using a standardized format: "Source: <name>, Status: <Pass/Fail>".
- [ ] T006 [P] **Pre-Ingestion Validation Gate**: Implement a final check task that aggregates results from T001-T005. If ANY source validation (ERA5 or Moral Machine) fails, this task MUST raise an exception and abort the pipeline. Log the final gate status (Pass/Fail) to `results/logs/data_validation_log.txt`. **Dependencies**: T001-T005.

**Checkpoint**: Data validation complete. If Pass, proceed to Phase 1. If Fail, project is blocked.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T007 Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`
- [X] T008 Initialize a Python project with dependencies (pandas, numpy, statsmodels>=0.13, scikit-learn, requests, pyyaml, seaborn, matplotlib, geopandas, cdsapi, huggingface_hub) in requirements.txt
- [ ] T009 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** distance thresholds (default distance, with parameters for shorter and longer ranges in sensitivity analysis) and **temperature thresholds** for extreme cold/heat.
- [ ] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`
- [X] T012 [P] Implement checksum generation and verification for `data/raw/` and `data/processed/` files in `code/utils.py`
- [X] T013 Create data loading utilities in `code/loaders.py` using `pandas.read_parquet` with `chunksize` parameter for memory mapping. Implement function `load_chunked_parquet(path, chunk_size)` to handle large Parquet ingestion without memory overflow.
- [ ] T014 [P] Setup unit test framework (pytest) with configuration for CPU-only execution and stratified sampling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests are optional for the MVP. However, if the 'Independent Test' scenario is to be automated, these specific test files must be implemented and verified.
> The 'Independent Test' scenario (running the script on a subset) is MANDATORY for verification of the data pipeline.

- [X] T015 [P] [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`
- [X] T016 [P] [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`. **Specifics**: Use the Jan 2016 London sample from T002 and verify the exact schema of the merged output.

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement `code/ingestion.py` to load Moral Machine dataset and filter records with missing location data or impossible response times (<100ms or >10,000ms), logging excluded records to `results/logs/exclusion_log.csv` in CSV format (FR-002, FR-010). **Dependencies**: T017c.
- [ ] T017b [US1] [P] Implement `code/ingestion.py` to define numeric thresholds for 'extreme cold' and 'extreme heat' (read from `code/config.py`) and filter records with temperature values outside this range. Log excluded records to `results/logs/exclusion_log.csv` with reason "temperature_out_of_range" (FR-002). **Dependencies**: T010.
- [ ] T017c [US1] [P] **Define Numeric Thresholds**: Write specific numeric thresholds for 'extreme cold' (e.g., -40C) and 'extreme heat' (e.g., 50C) into `code/config.py` under keys `TEMPERATURE_COLD_THRESHOLD` and `TEMPERATURE_HOT_THRESHOLD`. This task ensures T017b and T017 read the correct values. **Dependencies**: T010.
- [ ] T018 [US1] [P] Implement the **logic** for ERA5 Reanalysis data fetching and merging in `code/ingestion.py` using the CDS API (`cdsapi`) for 2014-2018 (FR-001). This task defines the functions `fetch_era5_data` and `merge_with_moral_machine` but does NOT execute them. **Dependencies**: T002c, T002d.
- [ ] T018b [US1] **Load and Merge** the full dataset. **Action**: Load the pre-fetched ERA5 data from `data/raw/era5_full.h5` (produced by T002c) and merge it with Moral Machine data using streaming logic to avoid memory overflow. **Deliverables**: Save merged dataset to `data/processed/merged_dataset.parquet`. **Verification**: 1) Compute and verify SHA-256 checksum of `data/raw/era5_full.h5` against `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`. 2) Verify the schema of `data/processed/merged_dataset.parquet` matches the expected output schema (response_id, participant_id, latitude, longitude, timestamp, dilemma_id, choice, country, mean_log_rt, temperature_celsius, match_quality, station_identifier). 3) Log the specific success entry `{"merge_status": "success", "schema_valid": true, "records_merged": <int>}` to `results/logs/ingestion_summary.log`. **Note**: This task MUST use a streaming approach to merge data to avoid memory overflow. **Dependencies**: T018, T002d.
- [X] T019 [US1] Implement geospatial matching logic in `code/ingestion.py` to link Moral Machine records to nearest ERA5 grid within 100km threshold. Explicitly flag records >100km by setting `match_quality` to 'low' and logging the exact reason "distance > 100km" to `results/logs/exclusion_log.csv` before exclusion (FR-009). **Note**: This task depends on T018b and T002d (Data Ready). **Logging**: Log the `grid_id` as the `station_identifier` in a dedicated column named `station_identifier` in the exclusion log and merged dataset to satisfy Constitution Principle VI.
- [ ] T020 [US1] [P] Implement time-based interpolation for missing ERA5 hourly values in `code/ingestion.py`: apply linear interpolation ONLY if the gap is ≤2 hours; EXCLUDE the record if the gap >2 hours. Log all excluded records with reasons (e.g., "ERA5 coverage gap", "Low confidence match", "temporal_gap > 2h") to `results/logs/exclusion_log.csv` in CSV format (Edge Case: Missing Temp, FR-002). **Note**: This task depends on T019 and T002d.
- [ ] T019b [US1] [P] Implement **Primary Exclusion Filter** in `code/ingestion.py`: Explicitly exclude all records where `match_quality` == 'low' (distance > 100km) OR where `temporal_gap > 2h` (logged in T020) from the primary dataset used for modeling. Log the count of excluded records to `results/logs/exclusion_log.csv` with reason "primary_filter_distance_gt_100km" or "primary_filter_temporal_gap_gt_2h". **Dependencies**: T019, T020.
- [ ] T022 [US1] **Generate and verify output** to save merged dataset to `data/processed/merged_dataset.parquet`. **Verification Criteria**: Log the success rate to `results/logs/ingestion_summary.log` with the exact JSON schema: `{"count_total": <int>, "count_matched": <int>, "success_rate": <float>}`. The task is considered complete ONLY if `success_rate` > 0.90. **Dependencies**: T019b, T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre-processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for log-transformation and outlier handling in `tests/test_modeling.py`
- [X] T024 [P] [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement `code/modeling.py` to perform log-transformation of response times and handle non-convergence by switching to GLMM (FR-003). **Dependencies**: T022.
- [ ] T028a [US2] Implement **Check and Fetch Covariates**. **Step 1**: Check if individual-level `age` and `gender` columns exist in the Moral Machine dataset. **Step 2**: If absent, fetch aggregate country-level data from the World Bank API (Endpoint: `https://api.worldbank.org/v2/country/{id}/indicator/SP.DYN.LE00.IN` for life expectancy as age proxy; `SP.POP.TOTL` for population). **Years**: 2014-2018. **Log**: Explicitly document the absence of individual-level data and the use of proxies. **Dependencies**: T022.
- [ ] T028b [US2] Implement **Merge and Log Limitation**. Merge the country-level covariates to the participant-aggregated rows **using 'country_code' as the join key (left join)**. **Critical**: Log the specific reduction in statistical power and explicitly state in `results/logs/demographic_gap_log.txt` that "This approach uses country-level aggregates as a proxy due to data unavailability; individual-level data is not present." (FR-004). **Dependencies**: T028a.
- [ ] T028c [US2] Implement **Derivation of Dilemma Complexity**. Derive a static metric for dilemma complexity (independent of response time) and ensure it is merged into the dataset. **Dependencies**: T022. **Note**: This score is a required covariate for T026 and T026b.
- [ ] T026 [US2] Implement **Primary Model: Linear Mixed-Effects (LMM)** in `code/modeling.py` with fixed effects: temperature, dilemma complexity, time-of-day, dilemma choice, and **interaction term between temperature and dilemma choice**, and random intercepts for participant ID and cultural region. **Fallback**: If LMM fails to converge, implement GLMM with log-link function (FR-003). **Output**: Save results to `results/stats/lmm_model_results.json` following `model_output.schema.yaml` (keys: `temperature_coef`, `temperature_se`, `temperature_p_value`, `random_intercept_variances`, `dilemma_complexity_coef`, `time_of_day_coef`, `dilemma_choice_coef`). **Dependencies**: T025, T028c, T022.
- [ ] T026b [US2] Implement **GLMM Fallback**. If T026 (LMM) fails convergence, implement the GLMM with log-link function as the primary model. **Dependencies**: T025, T028c, T022.
- [ ] T026c [US2] Implement **Interaction Term**. Explicitly implement and verify the interaction term between temperature and dilemma choice as a fixed effect in the LMM/GLMM model (FR-011). **Dependencies**: T026, T026b.
- [ ] T029 [US2] Implement likelihood-ratio test in `code/modeling.py` comparing Full Model (temperature, dilemma complexity, time-of-day, choice, interaction) vs. Null Model (dilemma complexity, time-of-day, choice, without temperature) and record p-value (FR-005, SC-002). **Dependencies**: T026, T026c.
- [ ] T030a [US2] Implement diagnostic plot generation (QQ-plot, residual vs. fitted) to verify normality and homoscedasticity assumptions of the transformed data (FR-007). Save plots to `results/figures/`. **Dependencies**: T026.
- [ ] T030b [US2] Implement Anderson-Darling statistical test on a **stratified random sample (sample size defined in `code/config.py` as a 'deferred' parameter)** to verify residual normality (SC-005). Record the Anderson-Darling p-value in `results/stats/model_results.json` under the key `anderson_darling_p_value`. **Dependencies**: T026.
- [ ] T031 [US2] Implement **Non-Linearity Test**. Fit a model with a quadratic term (temperature^2) and a spline basis for temperature. Compare model fit (AIC/BIC) against the linear-only model (FR-013). Save results to `results/stats/nonlinearity_test_results.json`. **Dependencies**: T026.
- [ ] T032 [US2] Export model coefficients, standard errors, p-values, and random effect variances to `results/stats/model_results.json` in a format compliant with `model_output.schema.yaml` (FR-008). **Dependencies**: T026, T026c, T031.
- [ ] T041 [US2] Extract the **random intercept variance** for the cultural region from the primary model output (output of T032) to quantify the baseline "individual difference" noise floor observed in the data. **Method**: Use `statsmodels>=0.13` and access `results.random_effects_variance`. Record this value in `results/stats/model_results.json` under the field `cluster_robust_variance`. **Note**: This task depends on T032 completing. (Note: This aligns with the LMM strategy which produces random effect variances).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`
- [ ] T034 [P] [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement `code/robustness.py` to calculate alternative temperature metrics (e.g., 3-hour moving average) and re-run modeling (FR-006)
- [ ] T035b [P] [US3] Implement **Distance Sensitivity Analysis** in `code/robustness.py`. Re-run the primary model excluding records >25km and >50km (using config from T010) and report the variation in the temperature coefficient. **Note**: This task tests sensitivity against thresholds *after* the primary exclusion logic (T019b) has removed >100km records. **Dependencies**: T019b, T026.
- [ ] T036 [US3] Implement sensitivity analysis in `code/robustness.py` sweeping temperature outlier thresholds (e.g., varying standard deviation multipliers) and reporting coefficient variation (FR-006, SC-003)
- [ ] T037 [US3] Implement indoor/outdoor confound analysis in `code/robustness.py` by FIRST attempting to stratify data or apply proxy adjustment using urban/rural classification. **Data Source**: Fetch urban/rural data from `datasets.load_dataset('jrc/ghsl-population')` and use the file `files/GHSL_POP_GLO_2020V1.0.zip`. **Check**: Verify file existence before use. If metadata is unavailable, THEN report the limitation and quantify noise impact by writing to `results/logs/indoor_outdoor_limitation.md` with a specific section "Quantified Noise Impact" (or 'N/A' with reason). (FR-012). **Dependencies**: T022.
- [ ] T038 [US3] Generate comparison table in `code/robustness.py` showing temperature coefficient and p-value for primary vs. alternative models (US-3)
- [ ] T039 [US3] Save all robustness figures (scatter plots, conditional effect plots) to `results/figures/` (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Address the absence of baseline data and arousal proxies by documenting them as limitations, as required by the spec's assumptions, and quantifying the noise floor via observed cluster-robust variances.

**Independent Test**: Verify that the results log explicitly states the inability to control for baseline speed and arousal due to data absence, and includes the quantified variance of individual differences from the model.

### Implementation for Limitations

- [ ] T040 [P3] Draft and verify `results/logs/limitations.md` explicitly stating: (1) No individual baseline reaction time data exists in the dataset; (2) Arousal/micro-climate effects are unmeasured noise; (3) These factors are not controlled for, only reported (FR-012, Spec Assumptions). **Input**: Read `results/stats/model_results.json` (key `cluster_robust_variance`). **Output**: Append section "Quantification of Unmeasured Baseline Noise" to `results/logs/limitations.md`. **Dependencies**: T041, T026 (executable).

**Checkpoint**: Limitations documented; analysis complete within data constraints.

---

## Phase 7: Research-Stage Review Resolution (Priority: P3 - Revision)

**Goal**: Address the specific concern from the "daniel-kahneman-simulated" review regarding the confounding of temperature effects with individual baseline reaction speed and physiological arousal, by explicitly documenting the data gap and quantifying the theoretical impact via observed variance.

**Independent Test**: Verify that the `results/logs/limitations.md` contains a specific entry for the Kahneman review, acknowledging the lack of baseline/arousal data, and that the `results/logs/limitations.md` includes the quantified noise floor.

### Implementation for Review Resolution

- [ ] T043 [P3] Update `results/logs/limitations.md` and `docs/research.md` to add a specific section for the "daniel-kahneman-simulated" review (dated -06-21), explicitly stating that the dataset lacks pre-test baseline reaction times and physiological arousal proxies (skin conductance), making the "temperature-adjusted RT" calculation impossible. This documents the known constraint per the Spec's Assumptions. **Dependencies**: T040.

**Checkpoint**: Review concerns acknowledged, theoretical impact quantified, and future work proposed.

---

## Phase 8: Review-Driven Confound Quantification (Priority: P3 - Revision)

**Goal**: Directly address the Kahneman review's specific suggestion to quantify the "noise" of individual differences by implementing a stratified analysis that isolates the temperature effect within homogeneous response-time groups, and to report the theoretical impact of the missing baseline.

**Independent Test**: Verify that `results/stats/model_results.json` includes a new metric `kahneman_review_noise_floor` derived from the stratified analysis, and that `results/logs/limitations.md` contains a dedicated section "Review: daniel-kahneman-simulated" with the specific quantification of the baseline confound.

### Implementation for Review Resolution

- [ ] T045 [US3] [P3] Implement a stratified analysis in `code/robustness.py` that bins participants into quartiles based on their **country-level median response time** (serving as an external proxy for baseline speed, avoiding circularity). **Fallback**: If a country has <30 responses, **exclude that country** from the analysis. **Re-run the primary temperature model** (T026 logic) within each quartile to observe if the temperature coefficient varies by baseline speed. Save the coefficients per quartile to `results/robustness/baseline_stratification.json`. **CRITICAL DISCLAIMER**: This task DOES NOT resolve the individual baseline confound (per Spec Assumptions). The goal is strictly to **quantify the upper bound of noise** introduced by unmeasured individual differences. The output must be framed as a "Noise Floor Estimate" and explicitly state that without true baseline data, the main effect is an upper bound. This analysis quantifies the variance in coefficients as a proxy for the unmeasured confound's impact (FR-012, SC-003). **Dependencies**: T022, T026.
- [ ] T046 [P3] Calculate the **variance of the temperature coefficients** across the baseline quartiles (from T045). This variance serves as a proxy for the unmeasured "individual difference" noise floor identified by the review. Record this value as `kahneman_review_noise_floor` in `results/stats/model_results.json`.
- [ ] T047 [P3] Update `results/logs/limitations.md` to include a new subsection "Quantification of Reviewer Concern (Kahneman)" that: (1) Reports the `kahneman_review_noise_floor` value from T046; (2) Explains that this value represents the estimated variance in the temperature effect due to unmeasured baseline speed differences; (3) States that without a true baseline, the main effect is an upper bound.

**Checkpoint**: Reviewer's specific concern about baseline confounding is now quantified and documented, allowing the project to proceed with a clear understanding of the noise floor.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `docs/` and `quickstart.md` including instructions for running with sampled data
- [ ] T049 Code cleanup and refactoring to ensure modularity
- [ ] T050 Performance optimization: Ensure dataset sampling logic in `code/ingestion.py` prevents memory overflow on runners with constrained RAM resources
- [ ] T051 [P] Additional unit tests for edge cases (e.g., all records excluded due to distance)
- [ ] T052 Run quickstart.md validation to ensure full pipeline completes within 4 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Validation)**: No dependencies - must run FIRST. BLOCKS all other phases.
- **Phase 1 (Setup)**: Depends on Phase 0 completion - can start immediately after validation passes.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories.
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Limitations (Phase 6)**: Depends on US3 completion (to summarize findings)
- **Review Resolution (Phase 7)**: Depends on US3 and Limitations (Phase 6) completion to fully contextualize the data gaps.
- **Review-Driven Confound Quantification (Phase 8)**: Depends on US2 (model output T026) and US3 (robustness framework) to perform the stratified analysis.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires merged data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model output from US2
- **Limitations (Phase 6)**: Requires US3 implementation to summarize findings
- **Review Resolution (Phase 7)**: Requires US3 and Limitations (Phase 6) to fully address the review.
- **Review-Driven Confound Quantification (Phase 8)**: Requires US2 (for baseline proxy T026) and US3 (for robustness framework).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion (US1) before Modeling (US2)
- Modeling (US2) before Robustness (US3)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 6, 7, and 8 can be executed in parallel once their dependencies (US2/US3) are met.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for location validation and exclusion logic in tests/test_ingestion.py"
Task: "Integration test for ERA5 data fetching and merging with sample Moral Machine data in tests/test_ingestion.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/ingestion.py to load Moral Machine dataset..."
Task: "Implement ERA5 Reanalysis data fetching logic in code/ingestion.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Validation (CRITICAL - must pass)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Data validated
2. Complete Setup + Foundational → Foundation ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Add Limitations (Phase 6) → Test independently → Deploy/Demo
7. Add Review Resolution (Phase 7) → Test independently → Deploy/Demo
8. Add Review-Driven Confound Quantification (Phase 8) → Test independently → Deploy/Demo
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Data Validation) together
2. Once Phase 0 passes:
 - Team completes Setup + Foundational together
3. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Robustness)
4. Stories complete and integrate independently
5. Developer D (or A/B/C rotation): Limitations (Phase 6), Review Resolution (Phase 7), and Review-Driven Confound Quantification (Phase 8) to document constraints, quantify noise, and address the specific Kahneman review concerns.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must be designed to run on a limited number of CPU cores and moderate memory resources. Use stratified sampling if dataset size exceeds memory.
- **NO GPU**: No -bit/4-bit quantization, no CUDA dependencies. Use standard precision models.
- **Data Constraints**: Do NOT attempt to simulate missing data (baseline, arousal) as real data. Document limitations and perform theoretical reporting instead.
- **Critical Blocker**: Phase 0 MUST pass before any ingestion tasks (T017+) are attempted.
- **Review Resolution**: Phases 6, 7, and 8 are mandatory to address the "daniel-kahneman-simulated" review regarding baseline reaction time confounds and to quantify the theoretical impact of the missing data.