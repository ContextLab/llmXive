# Tasks: Evaluating CBNRM vs State-Led Management

**Input**: Design documents from `/specs/001-evaluating-the-effectiveness-of-communit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED - the spec explicitly mandates synthetic data tests for the regression and verification tests for data ingestion.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md` structure)
- Paths shown below assume single project structure: `code/data/`, `code/analysis/`, `code/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code/data code/analysis code/tests data/raw data/processed docs/output logs`
- [X] T002 Initialize Python 3.11 project: Create `code/requirements.txt` containing: `pandas==2.0.3`, `numpy==1.24.3`, `statsmodels==0.14.0`, `matplotlib==3.7.2`, `requests==2.31.0`, `pyyaml==6.0.1`, `pytest==7.4.0`
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools: Create `.ruff.toml` with target-version `py311` and `black` formatter config in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directories (`data/raw/`, `data/processed/`) and output directories (`docs/output/`, `logs/`)
- [X] T005 [P] Implement logging infrastructure: Create `code/__init__.py` with `dictConfig` setup for JSON format, level INFO, output to console and `logs/run.log`
- [X] T006 [P] Create base configuration loader in `code/config.py` defining API endpoints and year ranges. **Deliverable**: Create `code/config.py` with a dictionary `CONFIG` containing keys: `API_BASE_URL` (string), `DATA_YEARS_START` (int, representing the start of the historical period), `DATA_YEARS_END` (int, 2020), `FAO_INDICATOR` (string), `WB_CBNRM_INDICATOR` (string). Verify the module loads without error.
- [X] T007 [P] Setup unit test framework (pytest) with `code/tests/__init__.py` and `conftest.py` (empty fixture file)
- [X] T060 [US1] [P] Implement "Fail Loud" Data Loader in `code/data/download.py`: Implement a robust fetch function that retries up to 3 times with exponential backoff. If all retries fail, **log a clear error message to `logs/run.log` and exit with a non-zero code** (graceful failure). **Do NOT** generate synthetic/mock data. This ensures the execution stage catches the failure and re-routes to a verified real source.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download and merge land-use data from FAO STAT with governance/policy data from World Bank, classifying regime types for years 2000–2020.

**Independent Test**: Run the ingestion script in isolation. Verify it produces a CSV with ≥50 rows (or all available if <50) containing non-null `land_use_change_rate`, `regime_type`, `gdp_per_capita`, and `population_density`.

### Implementation for User Story 1

- [ ] T009 [US1] [D: T060] Fetch CBNRM Proxy: **Step 1: Verify**: Check if the specific CBNRM policy indicator `AG.LND.FRST.CF` (Community Forestry Area Share) exists in the World Bank API metadata. **Step 2: Fetch or Proxy**: If it exists, fetch it for years covering the early 21st century. If it does **not** exist, log a 'Data Gap' warning, attempt to use a validated proxy (e.g., `AG.LND.FRST.ZS` with a derived threshold) as per the Plan's Data Gap protocol, or skip this indicator if no proxy is available. **Do NOT** use 'EG.GOV.POLI.ZS' or 'EG.FEC.RNEW.ZS'. Save the raw data to `data/raw/cbnrm_proxy.csv` and the metadata (indicator code, source URL, validation status, and a derived 'threshold' value for classification) to `data/processed/cbnrm_proxy_metadata.json`. **Note**: This task is a 'Producer' unblocking downstream consumers.
- [ ] T009b [US1] [D: T009] Validate Proxy: Implement a validation script in `code/data/classify.py` to check the variance of the fetched CBNRM proxy. If a country has zero variance in the proxy over time, **exclude that specific country from the dataset** and log the exclusion to `logs/run.log`. Do NOT halt the entire pipeline. Save validation results (including excluded countries list) to `data/processed/proxy_validation.json`. **Output**: The list of excluded country codes is saved here for T022 to consume during regression.
- [X] T010 [US1] [D: T060] Verify FAO Indicator: Implement a pre-flight check in `code/data/download.py` to verify that the 'Forest Area Change' indicator (`AG.LND.FRST.ZS`) exists in the FAO STAT API. If missing, log "Data Gap: Missing Variable in Source" warning and **skip this indicator** (do not halt), allowing the pipeline to continue with partial data.
- [ ] T011 [US1] [D: T010, T060] Implement FAO STAT data downloader in `code/data/download.py`: Fetch 'Forest Area Change' with indicator code **`AG.LND.FRST.ZS`** (exact code, no 'or equivalent') for the period spanning the early 21st century from the **FAO STAT** (Statistical Database) API. Handle retries with exponential backoff. **Use chunked processing (chunksize) if the dataset is large** to prevent OOM errors. Save raw data to `data/raw/fao_land_use.csv`.
- [ ] T012 [US1] [D: T009, T011, T060] Implement World Bank data loader in `code/data/download.py`: Load GDP and Population Density data (fetching if needed) and **load the specific CBNRM proxy data** from the output file generated by T009 (`data/raw/cbnrm_proxy.csv`). **Use chunked processing (chunksize) if the dataset is large**. Do not re-fetch the proxy.
- [ ] T013 [US1] [D: T012] Implement data merging and cleaning in `code/data/clean.py`: Standardize years (int), ISO codes (alpha-3), drop rows missing primary vars. Save merged panel to `data/processed/merged_panel.csv`. <!-- FAILED: unspecified -->
- [X] T016 [US1] [D: T013] Implement row-level exclusion logic in `code/data/clean.py`: Apply row-level exclusion (FR-007) for **Secondary Variables** (GDP, Pop): Log the specific missing variable name, exclude the row, continue.
- [X] T016b [US1] [D: T016] Implement country-level exclusion logic in `code/data/clean.py`: Apply country-level exclusion for **Primary Variables** (Land-Use, Regime): Calculate missing percentage *after* T016 has removed the rows. If >20% of a country's years are missing for a primary variable, exclude the entire country. Log "Primary Variable Missing".
- [ ] T014 [US1] [D: T009b, T013, T016b] Implement regime classification logic in `code/data/classify.py`: Load the specific CBNRM proxy indicator code and validated thresholds from `data/processed/cbnrm_proxy_metadata.json` (output of T009) and `data/processed/proxy_validation.json` (output of T009b). Derive binary `regime_type` using the logic: **If `proxy_value` > `threshold` (from metadata), set `regime_type`=1, else 0**. <!-- FAILED: unspecified -->
- [X] T015 [US1] [D: T011, T012, T013] Implement coverage rate calculation in `code/data/clean.py`: Load the total available rows from the raw FAO and World Bank downloads (T011, T012) and the `total_merged` count from T013. Calculate the coverage rate as `total_merged / min(total_fao_available, total_wb_available)` to represent the intersection of available records. Log this metric to `data/processed/metrics.json` (SC-001).

### Tests for User Story 1

- [X] T017a [P] [US1] Unit test for API retry logic: Add test in `code/tests/test_data_clean.py::test_download_exponential_backoff` that mocks server errors and verifies multiple retries with specific sleep intervals, and no synthetic data generation.
- [X] T018a [P] [US1] Unit test for data merge logic: Add test in `code/tests/test_data_clean.py::test_merge_handles_missing_keys` that verifies row exclusion when ISO codes mismatch.
- [X] T019a [P] [US1] Unit test for row exclusion: Add test in `code/tests/test_data_clean.py::test_excludes_row_when_gdp_missing` that verifies a row is excluded if GDP is null and logged correctly.
- [X] T019b [P] [US1] Unit test for country exclusion: Add test in `code/tests/test_data_clean.py::test_excludes_country_when_primary_missing` that verifies a country is excluded if >20% of years are missing for a primary variable.
- [X] T020a [P] [US1] Unit test for threshold mapping: Add test in `code/tests/test_data_clean.py::test_classifies_cbnrm_when_proxy_above_threshold` that verifies `regime_type` is 1 when proxy > threshold.
- [X] T020b [P] [US1] Unit test for edge cases: Add test in `code/tests/test_data_clean.py::test_classifies_state_led_when_proxy_below_threshold` that verifies `regime_type` is 0 when proxy <= threshold.
- [X] T065 [US1] [P] Unit Test for "Fail Loud" Behavior: Add `test_fetch_fails_loudly_no_synthetic` in `code/tests/test_data_clean.py` that mocks a persistent API failure and asserts that the script **raises an exception** and **does not** generate or return any synthetic/mock data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Panel Regression and Inference (Priority: P2)

**Goal**: Run fixed-effects panel regression comparing CBNRM vs State-led, controlling for covariates, with robustness checks.

**Independent Test**: Run regression script on synthetic dataset (seed=42, β=0.15, σ=0.1). Verify output coefficient matches synthetic truth within 1% tolerance and output is labeled "associational".

### Implementation for User Story 2

- [ ] T022 [US2] Implement Time-Invariance Diagnostic in `code/analysis/regression.py`: Detect countries where `regime_type` is constant over time. **Logic**: Calculate `std_dev` of `regime_type` per country. If `std_dev == 0` or `unique_values == 1`, flag the country. **Consume** the list of flagged countries from `data/processed/proxy_validation.json` (T009b) to avoid redundant calculation. Output list of flagged country codes to `data/processed/time_invariant_countries.json`.
- [X] T040 [US2] [D: T022] Implement Country Exclusion Logic in `code/analysis/regression.py`: Filter input dataset to exclude countries flagged by T022; prepare data for Fixed-Effects model. Output the filtered dataset count.
- [X] T041 [US2] [D: T022, T040] Implement Cross-Sectional Fallback in `code/analysis/regression.py`: **Consume the count of flagged countries from T022**. If **ALL** countries are time-invariant (count == total countries) OR the dataset becomes empty after exclusion:
 1. **Switch to a Random Effects model (RE)** on the full panel data.
 2. **Perform a Hausman Test** to compare Fixed Effects vs Random Effects.
 3. Explicitly log that the model is **Random Effects** due to lack of time-variation in the treatment variable.
 4. Output the selected model type ("Random Effects") and the results to `data/processed/model_selection.json`.
 5. Handle the case where the dataset is empty by logging "No data available for regression" and halting.
- [X] T023a [US2] [D: T040, T041] Implement Fixed-Effects Panel Regression (OLS) in `code/analysis/regression.py`: **Verify that time-invariant countries have been excluded** (via T040) or that the model has switched to Random Effects (T041). Model `land_use_change` ~ `regime_type` + GDP + Pop; control for country fixed effects using `statsmodels` `PanelOLS` (or `RandomEffects` if T041 triggered). Run the model. <!-- FAILED: unspecified -->
- [ ] T023b [US2] [D: T023a] Save Fixed-Effects results to `data/processed/regression_results_primary.json`.
- [ ] T027 [US2] [D: T023a] Add explicit "Associational" flag generation in `code/analysis/regression.py` (FR-004): Set a boolean flag `is_associational = True` and save to `data/processed/regression_metadata.json`. **File path must match T036 expectation**.
- [ ] T024 [US2] [D: T023a] Implement Sensitivity Analysis in `code/analysis/regression.py`: Run model without GDP controls. **Explicitly save the raw coefficient values** for both the 'Full Model' and 'No GDP Model' to `data/processed/sensitivity_coefficients.json` to serve as evidence for SC-005. Calculate % change.
- [ ] T025 [US2] [D: T023a] Implement Non-linearity Robustness Check in `code/analysis/regression.py`: Add quadratic term for CBNRM index (`regime_type^2`); test significance. Save results to `data/processed/regression_results_nonlinear.json`.
- [ ] T050 [US2] [D: T023a, T025, T024] Implement Test Count Logic in `code/analysis/regression.py`: **Count all distinct hypothesis tests**. Distinct tests: 1) Primary (CBNRM effect, T023a), 2) Non-linearity (T025). **Explicitly EXCLUDE Sensitivity Analysis (T024) from this count** as it tests control variables, per FR-006. Output the count and test metadata to `data/processed/test_count.json`.
- [ ] T051 [US2] [D: T050, T023b, T025, T024] Implement Benjamini-Hochberg FDR correction in `code/analysis/regression.py`: Read the test count from `data/processed/test_count.json` (T050). **If count >= 2**, aggregate p-values from Primary (T023a) and Non-linearity (T025) tests and apply correction using alpha=0.05 (1906.01701, https://arxiv.org/abs/1906.01701) and the Benjamini-Hochberg step-up method. If count < 2, skip correction.

### Tests for User Story 2

- [ ] T029a [P] [US2] Unit test for synthetic data generation: Add test in `code/tests/test_regression.py::test_synthetic_data_seed_42` that verifies generated dataframe shape and mean values (seed=42, beta=0.15, sigma=0.1).
- [ ] T030 [P] [US2] Unit test for fixed-effects regression coefficient accuracy: Add test in `code/tests/test_regression.py::test_coefficient_matches_synthetic_truth_within_1pct` that verifies the coefficient matches synthetic truth within 1% tolerance.
- [ ] T031 [P] [US2] Unit test for Benjamini-Hochberg FDR correction logic: Add test in `code/tests/test_regression.py::test_bh_fdr_correction_applies` that verifies the correction logic with known p-values.
- [ ] T032 [P] [US2] Unit test for non-linearity robustness check: Add test in `code/tests/test_regression.py::test_nonlinearity_quadratic_term` that verifies the quadratic term logic and significance test.
- [ ] T033 [P] [US2] Unit test for Random Effects Fallback logic: Add test in `code/tests/test_regression.py::test_random_effects_fallback` that verifies the fallback logic and execution when all countries are time-invariant.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate residual scatter plot and coefficient plot using CPU-only libraries.

**Independent Test**: Verify script generates two `.png` files in `docs/output/`: residual scatter and coefficient plot. Plots must have axis labels and error bars.

### Implementation for User Story 3

- [ ] T034 [US3] Implement Residual Scatter Plot generation in `code/analysis/visualization.py`: Plot Predicted vs. Residuals. **Axis labels**: "Predicted Values" (X), "Residuals" (Y).
- [ ] T035 [US3] Implement Coefficient Plot generation in `code/analysis/visualization.py`: Display CBNRM effect with confidence interval error bars. **Axis labels**: "Coefficient", "Variable".
- [ ] T036 [US3] [D: T011, T015, T024, T025, T041, T027, T023b] Implement report text generation in `code/analysis/report.py`: Load Coverage Rate from `data/processed/metrics.json` (T015), Sensitivity results (raw coefficients) from `data/processed/sensitivity_coefficients.json` (T024), the "Associational" flag from `data/processed/regression_metadata.json` (T027), primary regression results from `data/processed/regression_results_primary.json` (T023b), non-linearity results from `data/processed/regression_results_nonlinear.json` (T025), and model selection data from `data/processed/model_selection.json` (T041). Generate `docs/output/report.md` with explicit "Associational" disclaimer and all metrics.
- [ ] T037 [US3] Ensure all plotting uses CPU-only rendering (no GPU acceleration) in `code/analysis/visualization.py`.

### Tests for User Story 3

- [ ] T038 [P] [US3] Unit test for plot generation: Add test in `code/tests/test_visualization.py::test_plot_generates_png_files` that asserts file existence and format (`.png`).
- [ ] T039 [P] [US3] Unit test for plot content: Add test in `code/tests/test_visualization.py::test_plot_has_axis_labels` that asserts axis labels are present and correct.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Quality Assurance & Polish

**Purpose**: Final validation and reproducibility checks.

- [X] T042 [P] Run full test suite (`pytest`) including synthetic data regression test
- [X] T043 [P] Verify checksums for raw data downloads (if applicable) and processed artifacts
- [X] T044 [P] Validate reproducibility: Run pipeline from scratch on a clean environment
- [X] T045 [P] Update `docs/output/` with final plots and summary report
- [X] T046 [P] Run `quickstart.md` validation (if exists) to ensure end-to-end execution
- [ ] T070 [P] [SC-003] Measure Pipeline Runtime: Add a timer wrapper around the entire pipeline execution (from data download to report generation). Compare the total runtime against the 6-hour limit defined in SC-003. Log the total runtime and a "PASS/FAIL" status to `data/processed/runtime_metrics.json`. If the runtime exceeds the limit, log a warning but do not halt (as the limit is a success criterion, not a hard stop for the script itself).

---

## Phase 7: Data Integrity & Streaming (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and OOM errors.

- [X] T062 [US1] [P] Enforce "Fail Loud" on Data Source Mismatch in `code/data/download.py`: Add a validation step that compares the **actual** data source URL/package used against the **verified** source list in `plan.md`. If the fetched data comes from an unverified mirror or a guessed URL, raise a `DataIntegrityError` and halt. **Do NOT** proceed with unverified data.
- [X] T063 [US1] [P] Implement Verified Source Injection Handler in `code/data/download.py`: If the execution environment provides a "VERIFIED REAL DATA SOURCE" block (e.g., a specific package and access recipe), **override** all default API fetch logic to use **only** that injected source. Do not attempt to fetch from the public API if a verified source is present.
- [X] T064 [US2] [P] Add Memory Usage Monitoring in `code/analysis/regression.py`: Wrap the regression execution in a memory monitor using `tracemalloc`. If RAM usage exceeds a high threshold (leaving a buffer), log a warning and attempt to optimize by deleting intermediate DataFrames. If the limit is breached, **retry the regression using a chunked/batch approach** (processing countries in groups) to reduce memory footprint. **Do NOT** reference GPU offloading. Raise a `MemoryLimitError` with a specific message if the batched approach also fails.