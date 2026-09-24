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

- [X] T001 Create project structure per implementation plan: `mkdir -p code/data code/analysis code/tests data/raw data/processed docs/output`
- [X] T002 Initialize Python 3.11 project [UNRESOLVED-CLAIM: c_26c7e156 — status=not_enough_info]: Create `code/requirements.txt` containing: `pandas==2.0.3 [UNRESOLVED-CLAIM: c_00adfbc3 — status=not_enough_info]`, `numpy==1.24.3 [UNRESOLVED-CLAIM: c_580d9244 — status=not_enough_info]`, `statsmodels==0.14.0 [UNRESOLVED-CLAIM: c_6868a05c — status=not_enough_info]`, `matplotlib==3.7.2 [UNRESOLVED-CLAIM: c_97fba1b4 — status=not_enough_info]`, `requests==2.31.0 [UNRESOLVED-CLAIM: c_44497478 — status=not_enough_info]`, `pyyaml==6.0.1 [UNRESOLVED-CLAIM: c_848e5152 — status=not_enough_info]`, `pytest==7.4.0 [UNRESOLVED-CLAIM: c_096e188f — status=not_enough_info]`
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools: Create `.ruff.toml` with target-version `py311` and `black` formatter config in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directories (`data/raw/`, `data/processed/`) and output directories (`docs/output/`)
- [X] T005 [P] Implement logging infrastructure: Create `code/__init__.py` with `dictConfig` setup for JSON format, level INFO, output to console and `logs/run.log`
- [X] T006 [P] Create base configuration loader in `code/config.py` defining API endpoints and year ranges. **Deliverable**: Create `code/config.py` with a dictionary `CONFIG` containing keys: `API_BASE_URL` (string), `DATA_YEARS_START` (int, representing the start of the historical period), `DATA_YEARS_END` (int, 2020), `FAO_INDICATOR` (string), `WB_CBNRM_INDICATOR` (string). Verify the module loads without error.
- [X] T007 [P] Setup unit test framework (pytest) with `code/tests/__init__.py` and `conftest.py` (empty fixture file)
- [X] T060 [US1] [P] Implement "Fail Loud" Data Loader in `code/data/download.py`: Implement a robust fetch function that retries up to 3 times with exponential backoff. If all retries fail, **log a clear error message to `logs/run.log` and exit with a non-zero code** (graceful failure). **Do NOT** generate synthetic/mock data. This ensures the execution stage catches the failure and re-routes to a verified real source.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download and merge land-use data from FAO STAT with governance/policy data from World Bank, classifying regime types for years 2000–2020 [UNRESOLVED-CLAIM: c_a197d269 — status=not_enough_info].

**Independent Test**: Run the ingestion script in isolation. Verify it produces a CSV with ≥50 rows (or all available if <50) containing non-null `land_use_change_rate`, `regime_type`, `gdp_per_capita`, and `population_density`.

### Implementation for User Story 1

- [ ] T008a [US1] [D: T060] Count FAO Rows: Stream the FAO STAT dataset for 'Forest Area Change' (`AG.LND.FRST.ZS`) for a multi-decadal period. **Count rows as they arrive** to establish the `total_fao_available` count. Save this count to `data/processed/counts_fao.json`. **Do NOT** attempt to load the full dataset.
- [ ] T008b [US1] [D: T060] Count World Bank Rows: Stream the World Bank dataset for the CBNRM proxy (indicator `EG.GOV.POLI.ZS` per research.md) and GDP/Pop data for years 2000–2020 [UNRESOLVED-CLAIM: c_a197d269 — status=not_enough_info]. **Count rows as they arrive** to establish the `total_wb_available` count. Save this count to `data/processed/counts_wb.json`.
- [ ] T008c [US1] [D: T008a, T008b, T060] Merge and Count Merged: Load the FAO and World Bank data (using chunked processing if necessary) and perform the merge on `iso_code` and `year`. Count the resulting rows as `total_merged`. Save `total_merged` to `data/processed/counts_merged.json`.
- [X] T009 [US1] [D: T060] Fetch CBNRM Proxy: Query the World Bank API for the **specific CBNRM policy indicator** `EG.GOV.POLI.ZS` (Political Stability, used as a validated proxy per research.md) for years covering the early 21st century. **DO NOT** use 'EG.FEC.RNEW.ZS' (Renewable Energy) as a fallback. If the specific indicator is not found, log a 'Data Gap' error and halt. Save the raw data to `data/raw/cbnrm_proxy.csv` and the metadata (indicator code, source URL, validation status) to `data/processed/cbnrm_proxy_metadata.json`. **Note**: This task is a 'Producer' unblocking downstream consumers.
- [ ] T009b [US1] [D: T009] Validate Proxy: Implement a validation script in `code/data/classify.py` to check the variance of the fetched CBNRM proxy. If a country has zero variance in the proxy over time, **exclude that specific country from the dataset** and log the exclusion to `logs/run.log`. Do NOT halt the entire pipeline. Save validation results (including excluded countries list) to `data/processed/proxy_validation.json`.
- [X] T010 [US1] [D: T060] Verify FAO Indicator: Implement a pre-flight check in `code/data/download.py` to verify that the 'Forest Area Change' indicator (`AG.LND.FRST.ZS`) exists in the FAO STAT API. If missing, log "Data Gap: Missing Variable in Source" and **halt execution** (Plan Phase 0 protocol).
- [ ] T011 [US1] [D: T010, T060] Implement FAO STAT data downloader in `code/data/download.py`: Fetch 'Forest Area Change' with indicator code **`AG.LND.FRST.ZS`** (exact code, no 'or equivalent') for the period spanning the early 21st century from the **FAO STAT** (Statistical Database) API. Handle retries with exponential backoff. Save raw data to `data/raw/fao_land_use.csv`.
- [X] T012 [US1] [D: T009, T011, T060] Implement World Bank data loader in `code/data/download.py`: Load GDP and Population Density data (fetching if needed) and **load the specific CBNRM proxy data** from the output file generated by T009 (`data/raw/cbnrm_proxy.csv`). Do not re-fetch the proxy.
- [X] T013 [US1] [D: T012] Implement data merging and cleaning in `code/data/clean.py`: Standardize years (int), ISO codes (alpha-3), drop rows missing primary vars. Save merged panel to `data/processed/merged_panel.csv`.
- [X] T016 [US1] [D: T013] Implement row-level exclusion logic in `code/data/clean.py`: Apply row-level exclusion (FR-007) for **Secondary Variables** (GDP, Pop): Log the specific missing variable name, exclude the row, continue.
- [X] T016b [US1] [D: T016] Implement country-level exclusion logic in `code/data/clean.py`: Apply country-level exclusion for **Primary Variables** (Land-Use, Regime): Calculate missing percentage *after* T016 has removed the rows. If >20% of a country's years are missing for a primary variable, exclude the entire country. Log "Primary Variable Missing".
- [X] T014 [US1] [D: T009b, T013, T016b] Implement regime classification logic in `code/data/classify.py`: Load the specific CBNRM proxy indicator code and validated thresholds from `data/processed/cbnrm_proxy_metadata.json` (output of T009) and `data/processed/proxy_validation.json` (output of T009b). Derive binary `regime_type` using the logic: **If `proxy_value` > `threshold` (from metadata), set `regime_type`=1, else 0**.
- [ ] T015 [US1] [D: T008a, T008b, T008c] Implement coverage rate calculation in `code/data/clean.py`: Load the `total_fao_available` (from T008a), `total_wb_available` (from T008b), and `total_merged` (from T008c). Calculate the coverage rate as `total_merged / min(total_fao_available, total_wb_available)` to represent the intersection of available records. Log this metric to `data/processed/metrics.json` (SC-001).

### Tests for User Story 1

- [X] T017a [P] [US1] Unit test for API retry logic: Add test in `code/tests/test_data_clean.py::test_download_exponential_backoff` that mocks server errors and verifies multiple retries with specific sleep intervals, and no synthetic data generation.
- [X] T018a [P] [US1] Unit test for data merge logic: Add test in `code/tests/test_data_clean.py::test_merge_handles_missing_keys` that verifies row exclusion when ISO codes mismatch.
- [ ] T019a [P] [US1] Unit test for row exclusion: Add test in `code/tests/test_data_clean.py::test_excludes_row_when_gdp_missing` that verifies a row is excluded if GDP is null and logged correctly.
- [ ] T019b [P] [US1] Unit test for country exclusion: Add test in `code/tests/test_data_clean.py::test_excludes_country_when_primary_missing` that verifies a country is excluded if >20% of years are missing for a primary variable.
- [ ] T020a [P] [US1] Unit test for threshold mapping: Add test in `code/tests/test_data_clean.py::test_classifies_cbnrm_when_proxy_above_threshold` that verifies `regime_type` is 1 when proxy > threshold.
- [ ] T020b [P] [US1] Unit test for edge cases: Add test in `code/tests/test_data_clean.py::test_classifies_state_led_when_proxy_below_threshold` that verifies `regime_type` is 0 when proxy <= threshold.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Panel Regression and Inference (Priority: P2)

**Goal**: Run fixed-effects panel regression comparing CBNRM vs State-led, controlling for covariates, with robustness checks.

**Independent Test**: Run regression script on synthetic dataset (seed=42, β=0.15, σ=0.1). Verify output coefficient matches synthetic truth within 1% tolerance [UNRESOLVED-CLAIM: c_79158512 — status=not_enough_info] and output is labeled "associational".

### Implementation for User Story 2

- [ ] T022 [US2] Implement Time-Invariance Diagnostic in `code/analysis/regression.py`: Detect countries where `regime_type` is constant over time. **Logic**: Calculate `std_dev` of `regime_type` per country. If `std_dev == 0` or `unique_values == 1`, flag the country. Output list of flagged country codes to `data/processed/time_invariant_countries.json`.
- [X] T040 [US2] [D: T022] Implement Country Exclusion Logic in `code/analysis/regression.py`: Filter input dataset to exclude countries flagged by T022; prepare data for Fixed-Effects model. Output the filtered dataset count.
- [ ] T041 [US2] [D: T022, T040] Implement Cross-Sectional Fallback in `code/analysis/regression.py`: **Consume the count of flagged countries from T022**. If **ALL** countries are time-invariant (count == total countries) OR the dataset becomes empty after exclusion:
 1. **Switch to a Cross-Sectional OLS model** (Pooled OLS) on the **mean values** of the variables across the 2000-2020 period (or the latest available year if means are not feasible).
 2. Explicitly log that the model is **Cross-Sectional** due to lack of time-variation in the treatment variable.
 3. Output the selected model type ("Cross-Sectional OLS") and the results to `data/processed/model_selection.json`.
 4. Handle the case where the dataset is empty by logging "No data available for regression" and halting.
- [ ] T023a [US2] [D: T040, T041] Implement Fixed-Effects Panel Regression (OLS) in `code/analysis/regression.py`: **Verify that time-invariant countries have been excluded** (via T040). Model `land_use_change` ~ `regime_type` + GDP + Pop; control for country fixed effects using `statsmodels` `PanelOLS`. Run the model.
- [ ] T023b [US2] [D: T023a] Save Fixed-Effects results to `data/processed/regression_results_primary.json`.
- [ ] T027 [US2] [D: T023a] Add explicit "Associational" flag generation in `code/analysis/regression.py` (FR-004): Set a boolean flag `is_associational = True` and save to `data/processed/regression_metadata.json`. **File path must match T036 expectation**.
- [ ] T024 [US2] [D: T023a] Implement Sensitivity Analysis in `code/analysis/regression.py`: Run model without GDP controls. **Explicitly save the raw coefficient values** for both the 'Full Model' and 'No GDP Model' to `data/processed/sensitivity_coefficients.json` to serve as evidence for SC-005. Calculate % change.
- [ ] T025 [US2] [D: T023a] Implement Non-linearity Robustness Check in `code/analysis/regression.py`: Add quadratic term for CBNRM index (`regime_type^2`); test significance. Save results to `data/processed/regression_results_nonlinear.json`.
- [ ] T028a [US2] [D: T023a] Implement Interaction Term Generation in `code/analysis/regression.py`: Generate interaction terms (`regime_type * gdp_per_capita`, `regime_type * population_density`) and save to `data/processed/interaction_terms.csv`.
- [ ] T028 [US2] [D: T028a] Implement F-test for Joint Significance in `code/analysis/regression.py`: Perform an F-test specifically for the **joint significance of the governance interaction terms** (generated in T028a) as required by FR-003. Save results to `data/processed/regression_results_interactions.json`.
- [ ] T050 [US2] [D: T023b, T025, T028] Implement Test Count Logic in `code/analysis/regression.py`: **Count only Primary Hypothesis Tests**. Distinct tests: 1) Primary (CBNRM effect, T023a), 2) Interaction F-test (T028), 3) Non-linearity (T025). **Explicitly EXCLUDE Sensitivity Analysis (T024)** as it is a robustness check, not a distinct hypothesis test. Output the count and test metadata to `data/processed/test_count.json`.
- [ ] T051 [US2] [D: T050, T023b, T025, T028] Implement Benjamini-Hochberg FDR correction in `code/analysis/regression.py`: Read the test count from `data/processed/test_count.json` (T050). **If count >= 2**, aggregate p-values from Primary (T023a), Interaction (T028), and Non-linearity (T025) tests and apply correction using alpha=0.05 (2602.11610, https://arxiv.org/abs/2602.11610) [UNRESOLVED-CLAIM: c_68743b82 — status=not_enough_info] and the Benjamini-Hochberg step-up method. If count < 2, skip correction.

### Tests for User Story 2

- [ ] T029a [P] [US2] Unit test for synthetic data generation: Add test in `code/tests/test_regression.py::test_synthetic_data_seed_42` that verifies generated dataframe shape and mean values (seed=42, beta=0.15, sigma=0.1).
- [ ] T030 [P] [US2] Unit test for fixed-effects regression coefficient accuracy: Add test in `code/tests/test_regression.py::test_coefficient_matches_synthetic_truth_within_1pct` that verifies the coefficient matches synthetic truth within 1% tolerance.
- [ ] T031 [P] [US2] Unit test for Benjamini-Hochberg FDR correction logic: Add test in `code/tests/test_regression.py::test_bh_fdr_correction_applies` that verifies the correction logic with known p-values.
- [ ] T032 [P] [US2] Unit test for non-linearity robustness check: Add test in `code/tests/test_regression.py::test_nonlinearity_quadratic_term` that verifies the quadratic term logic and significance test.
- [ ] T033 [P] [US2] Unit test for Cross-Sectional Fallback logic: Add test in `code/tests/test_regression.py::test_cross_sectional_fallback` that verifies the fallback logic and execution when all countries are time-invariant.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate residual scatter plot and coefficient plot using CPU-only libraries.

**Independent Test**: Verify script generates two `.png` files in `docs/output/`: residual scatter and coefficient plot. Plots must have axis labels and error bars.

### Implementation for User Story 3

- [ ] T034 [US3] Implement Residual Scatter Plot generation in `code/analysis/visualization.py`: Plot Predicted vs. Residuals. **Axis labels**: "Predicted Values" (X), "Residuals" (Y).
- [ ] T035 [US3] Implement Coefficient Plot generation in `code/analysis/visualization.py`: Display CBNRM effect with confidence interval error bars. **Axis labels**: "Coefficient", "Variable".
- [ ] T036 [US3] [D: T011, T015, T024, T025, T028, T041, T027, T023b] Implement report text generation in `code/analysis/report.py`: Load Coverage Rate from `data/processed/metrics.json` (T015), Sensitivity results (raw coefficients) from `data/processed/sensitivity_coefficients.json` (T024), the "Associational" flag from `data/processed/regression_metadata.json` (T027), primary regression results from `data/processed/regression_results_primary.json` (T023b), non-linearity results from `data/processed/regression_results_nonlinear.json` (T025), interaction results from `data/processed/regression_results_interactions.json` (T028), and model selection data from `data/processed/model_selection.json` (T041). Generate `docs/output/report.md` with explicit "Associational" disclaimer and all metrics.
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

---

## Phase 7: Data Integrity & Streaming (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and OOM errors.

- [ ] T061a [US1] [P] Implement Chunked Data Processing for Large Datasets in `code/data/download.py`: If the FAO or World Bank API returns a dataset that exceeds a substantial size threshold (detected via `Content-Length` or row count estimate), switch to **chunked mode**. Use `pandas.read_csv(..., chunksize=10000)` or chunked HTTP requests to iterate row-by-row, accumulating statistics (sum, count) without loading the full dataset into RAM. **Do NOT** fallback to a synthetic subset unless the full stream is impossible; if a sample is used, log the exact sampling rule (e.g., "First [deferred] rows of stream"). **Use only `pandas` (no `datasets` library)**.
- [ ] T062 [US1] [P] Enforce "Fail Loud" on Data Source Mismatch in `code/data/download.py`: Add a validation step that compares the **actual** data source URL/package used against the **verified** source list in `plan.md`. If the fetched data comes from an unverified mirror or a guessed URL, raise a `DataIntegrityError` and halt. **Do NOT** proceed with unverified data.
- [ ] T063 [US1] [P] Implement Verified Source Injection Handler in `code/data/download.py`: If the execution environment provides a "VERIFIED REAL DATA SOURCE" block (e.g., a specific package and access recipe), **override** all default API fetch logic to use **only** that injected source. Do not attempt to fetch from the public API if a verified source is present.
- [ ] T064 [US2] [P] Add Memory Usage Monitoring in `code/analysis/regression.py`: Wrap the regression execution in a memory monitor using `tracemalloc`. If RAM usage exceeds a high threshold (leaving a buffer), log a warning and attempt to optimize by deleting intermediate DataFrames. If the limit is breached, **retry the regression using a chunked/batch approach** (processing countries in groups) to reduce memory footprint. **Do NOT** reference GPU offloading. Raise a `MemoryLimitError` with a specific message if the batched approach also fails.
- [ ] T065 [US1] [P] Unit Test for "Fail Loud" Behavior: Add `test_fetch_fails_loudly_no_synthetic` in `code/tests/test_data_clean.py` that mocks a persistent API failure and asserts that the script **raises an exception** and **does not** generate or return any synthetic/mock data.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (merged CSV)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 regression results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data downloaders before cleaners
- Cleaners before classifiers
- Classifiers before regression
- Regression before visualization
- Commit after each task or logical group

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a specific story (e.g., T017-T020) can run in parallel
- Visualization plots (T034, T035) can be generated in parallel once results are ready
- Robustness tests (T065-T067) can run in parallel with US1 implementation tests

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion)
4. **STOP and VALIDATE**: Test US1 independently (verify CSV output)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Analysis ready)
4. Add User Story 3 → Test independently → Deploy/Demo (Visuals ready)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data) + Phase 7 (Robustness)
 - Developer B: User Story 2 (Regression) - *Note: Requires US1 output, so sequential or mock data for dev*
 - Developer C: User Story 3 (Visualization) - *Note: Requires US2 output*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (limited CPU, limited RAM). No GPU, no quantized models, no heavy DL.
- **Data Integrity**: No synthetic/fake input data allowed for final runs. Real API data required. T060 enforces this by failing gracefully on fetch errors.
- **Data Flow Enforcement**: Tasks T008a/b/c (Data Verification) MUST complete before T012/T014 (Data Loading/Classification) to ensure the CBNRM proxy is validated before use. T015 (Coverage Rate) depends on T008a, T008b, T008c (Total Counts) and T013 (Merge). T023a (Regression) depends on T040 (Exclusion) which depends on T022 (Diagnostic). T051 (FDR) depends on T050 (Test Count) and all result files (T023a, T025, T028). T036 (Report) depends on T015, T024, T041, T027, T023b, T011, T025, T028.
- **Revision Concerns**: Phase 7 tasks (T061a-T065) specifically address the requirement to "fail loud" on data fetch errors (no synthetic fallback), validate the CBNRM proxy at runtime, handle large datasets via chunked `pandas` processing (not `datasets` library) to prevent OOM errors, and enforce verified source injection. T008a/b/c fixes the streaming logic flaw. T041 fixes the invalid Random Effects fallback. T050 fixes the FDR test count. T064 fixes the GPU reference.