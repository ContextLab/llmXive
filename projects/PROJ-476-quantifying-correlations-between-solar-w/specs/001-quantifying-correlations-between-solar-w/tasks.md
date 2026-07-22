# Tasks: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Input**: Design documents from `/specs/feature-001-geomagnetic-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED - explicitly requested in the feature specification (User Stories 1, 2, and 3 all define Independent Tests).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure for code directories using exact command: `mkdir -p code/data code/analysis code/viz code/tests artifacts/figures artifacts/reports state/`.
- [X] T002 [P] Initialize Python 3.11 project by creating `code/requirements.txt` with the exact command: `echo -e "pandas>=2.0\nnumpy>=1.24\nscipy>=1.11\nstatsmodels>=0.14\nmatplotlib>=3.8\nrequests>=2.31\npyyaml>=6.0\npytest>=7.4\ntqdm>=4.66\njsonschema>=4.0" > code/requirements.txt`.
- [X] T003 [P] Configure linting and formatting by creating `pyproject.toml` and `.ruff.toml` using exact commands:
 1. `cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 88
target-version = ['py311']
EOF`
 2. `cat >.ruff.toml << 'EOF'
target-version = "py311"
line-length = 88
[lint]
select = ["E", "F", "W", "I"]
EOF`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create `code/config.py` as a Python constants module. **MUST define** the following constants with exact values: `TRAIN_START=1998`, `TRAIN_END=2017`, `TEST_START=2018`, `TEST_END=2020`, `ACE_URL="ftp://spdf.gsfc.nasa.gov/pub/data/ace/"`, `NOAA_DST_URL="https://www.ngdc.noaa.gov/stp/space-weather/interactive/dst/1hr/dst_1hr.txt"`, `NOAA_KP_URL="https://www.ngdc.noaa.gov/stp/space-weather/interactive/kp/1hr/kp_1hr.txt"`, `ACE_VARS=['N_p', 'T_p', 'He2+_ratio']`, `NOAA_VARS=['Kp', 'Dst']`. **MUST explicitly document** that `TRAIN_START` to `TEST_END` covers the full multi-decadal span referenced in SC-001 for the "full 20-year lagged correlation analysis" performance benchmark, while `TRAIN_START` to `TRAIN_END` is the subset used for model fitting. All downstream tasks MUST import these constants from `code.config`.
- [X] T005 [P] Setup logging infrastructure in `code/__init__.py` by creating a logger named 'solar_wind' with level 'INFO' and a StreamHandler. **MUST use the following exact code snippet**:
 ```python
 import logging
 logger = logging.getLogger('solar_wind')
 logger.setLevel(logging.INFO)
 handler = logging.StreamHandler()
 formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
 handler.setFormatter(formatter)
 logger.addHandler(handler)
 ```
- [X] T006 [P] Create `contracts/dataset.schema.yaml` in Phase 2. **MUST define** the JSON Schema for the `synced.csv` output, including columns: `timestamp`, `proton_density`, `temperature`, `helium_abundance`, `Kp`, `Dst`, `gap_mask`. **MUST** ensure `gap_mask` is a boolean column.
- [X] T007 [P] Create `contracts/analysis_schema.yaml` in Phase 2. **MUST define** the JSON Schema for `correlations.csv`, including columns: `composition_parameter`, `geomagnetic_index`, `lag_hours`, `pearson_r`, `spearman_rho`, `p_raw`, `p_bonferroni`, `significance_flag`.
- [X] T008 [P] Create `contracts/threshold.schema.yaml` in Phase 2. **MUST define** the JSON Schema for `global_threshold.json`, including `neff_values` (object), `bonferroni_alpha_adj` (float), and `global_divisor` (int).
- [X] T009 [P] Create `contracts/visual_artifact.schema.yaml` in Phase 2. **MUST define** the JSON Schema for visual artifact metadata, including `file_size_bytes` (int, max 5242880), `dimensions`, and `format`.
- [X] T010 [P] Create base data validation logic in `code/data/validate.py` as a **stub file**. **MUST import** `ACE_VARS` and `NOAA_VARS` from `code.config`. **MUST define** a function `validate_columns(df: pd.DataFrame, required_cols: list) -> None` that raises `ValueError` with the exact message "Missing required variable: <name>" if any column in `required_cols` is missing. Do not implement the abort logic yet; this task creates the file structure and imports. **Note**: This is a scaffolding step; logic must be implemented in T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Real Data Fixture Generation (Schema & Test Data)

**Purpose**: Create real, reproducible fixtures for integration tests by fetching limited real data from verified sources.

- [ ] T007a [P] [US1] **Fetch Real Monthly Sample**. **MUST** create a script `scripts/fetch_real_sample.py` that downloads ACE and NOAA data for a 1-month window (e.g., 2000-01-01 to 2000-01-31) using the verified URLs from `code/config.py`. **MUST** use `numpy.random.seed(42)` ONLY for random sampling if needed, but the source data MUST be real. **MUST** save the output to `data/fixtures/monthly_sample.csv`. **MUST** ensure no NaNs are present (if gaps exist, handle via interpolation as per T013 logic, or select a gap-free month). **Purpose**: Provides a guaranteed real input for T010 (Integration Test) without requiring the full 20-year download.
- [ ] T007b [P] [US2] **Fetch Real Full Sample**. **MUST** create a script `scripts/fetch_real_sample.py` (or extend T007a) to download a representative 1-year subset (e.g., 2000-01-01 to 2000-12-31) of real ACE/NOAA data. **MUST** save to `data/fixtures/full_correlation_sample.csv`. **MUST** ensure no NaNs are present. **Purpose**: Provides a guaranteed real input for T019 (Integration Test) to verify autocorrelation logic on real data distributions. **EXECUTION ORDER: Must run after T007a**.

**Checkpoint**: Schemas defined and real fixtures generated - validation and integration tasks can now be executed.

---

## Phase 3: User Story 1 - Data Acquisition & Synchronisation (Priority: P1) 🎯 MVP

**Goal**: Download ACE/NOAA data, align to 1-hour UTC grid, handle missing values via linear interpolation.

**Independent Test**: Run the pipeline for a month-long window. Verify output CSV contains exactly five columns (timestamp, proton_density, temperature, helium_abundance, Kp, Dst) with no NaNs after imputation.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST (Test-First approach). They are written before implementation but **executed** only after T013 is complete.

- [X] T011 [P] [US1] Unit test for variable validation in `code/tests/test_validate.py`. **Function name**: `test_fetch_aborts_on_missing_he2plus`. **MUST use** `pytest.raises(ValueError, match="Missing required variable: He2+_ratio")` to verify abort on missing `He2+_ratio` in source file.
- [X] T012 [P] [US1] Unit test for interpolation logic in `code/tests/test_align.py`. **Function name**: `test_align_interpolates_small_gaps_warns_large`. Verify gap ≤ 6h fills, > 6h warns.
- [ ] T013 [US1] **Write and Execute** Integration test for full month download in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_monthly_sync`. **MUST use** the pre-fetched real fixture file `data/fixtures/monthly_sample.csv` (created by T007a) as input. **MUST verify** `data/processed/synced.csv` structure and schema conformance against `contracts/dataset.schema.yaml` (created by T006). **Note**: This task is for WRITING the test code. The test is **executed** only after T014 (align.py write) is complete.

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement logic in `code/data/fetch.py` (populating the existing stub) to download ACE Level data (SWEPAM/SWICS) and NOAA Dst. **MUST implement** `fetch_ace` and `fetch_dst` with `start_date`, `end_date` parameters. **MUST use verified URLs** defined in `code.config.py` (see T004a). **MUST raise** `ConnectionError` or `FileNotFoundError` if the real fetch fails, **NEVER** falling back to synthetic/mock data. **MUST use `stream=True` if file size > 4GB**.
- [X] T015 [P] [US1] Implement logic in `code/data/fetch.py` to download NOAA Kp. **MUST implement** `fetch_kp` with `start_date`, `end_date` parameters. **MUST use verified URL** defined in `code.config.py` (see T004a). **MUST raise** `ConnectionError` or `FileNotFoundError` if the real fetch fails, **NEVER** falling back to synthetic/mock data.
- [X] T016 [US1] Implement `code/data/validate.py` to abort with clear error if `N_p`, `T_p`, or `He2+_ratio` are missing (FR-006). **MUST explicitly check the actual headers of the downloaded file against the hardcoded list and abort if they don't match**. **MUST verify source file column names against ACE Level 2 names ('N_p', 'T_p', 'He2+_ratio') BEFORE mapping**. **MUST log the specific missing variable name** (e.g., "Missing variable: He2+_ratio") in the abort message to satisfy SC-002. **MUST raise** `ValueError` with the exact message format defined in T010.
- [X] T017 [US1] Implement `code/data/align.py` to handle the full alignment pipeline. **MUST** read from `data/raw/ace.csv`, `data/raw/dst.csv`, and `data/raw/kp.csv` (produced by T014 and T015). **MUST** resample all to a standard hourly UTC grid using `df.resample('1h').mean()`. **MUST** perform linear interpolation for gaps ≤ 6h and **log** each interpolated interval. **MUST** **MARK** any gaps > 6h by setting a `gap_mask` column to `True` and leaving data as `NaN` (do NOT drop rows). This ensures the data is available for visualization (FR-008) but excluded from correlation calculations. **MUST** explicitly rename columns from ACE raw names (`N_p` → `proton_density`, `T_p` → `temperature`, `He2+_ratio` → `helium_abundance`) and NOAA names (`Kp`, `Dst`) to match the schema in `contracts/dataset.schema.yaml`. **MUST** ensure the output has **no NaNs** in the data columns (except where `gap_mask` is True). **MUST** write to `data/processed/synced.csv`. **MUST** verify the output contains **no NaNs** in non-masked rows before writing. **MUST** ensure the file contains exactly the required columns: `timestamp, proton_density, temperature, helium_abundance, Kp, Dst, gap_mask`.
- [X] T018 [US1] Create `code/main.py` entry point to orchestrate US1 pipeline (download → validate → sync). **MUST** call T014, T015, T016, and T017 in sequence.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lagged Correlation & Significance Testing (Priority: P2)

**Goal**: Compute Pearson/Spearman correlations at lags 0,1,2,3,6h on the FULL dataset, adjust p-values for autocorrelation (Neff), and apply Bonferroni correction.

**Independent Test**: Execute correlation module on full dataset. Verify results table has a complete set of rows IF all variables are present, or N rows (N<30) if variables are missing. Each row must contain Pearson r, Spearman ρ, raw p (Neff adjusted), and Bonferroni p.

### Tests for User Story 2 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T019 [P] [US2] Unit test for Neff calculation in `code/tests/test_correlation.py`. **Function name**: `test_correlation_neff_formula`. **MUST use formula** $N_{eff} = N \frac{1-\rho_1}{1+\rho_1}$ with synthetic data (e.g., N=100, rho=0.9) and verify expected result. **MUST include code snippet for synthetic data generation**: `np.random.RandomState(42).randn(100)`. **MUST verify that the detrending step (`scipy.signal.detrend`) is applied before calculating rho_1**.
- [X] T020 [P] [US2] Unit test for Bonferroni correction in `code/tests/test_correlation.py`. **Function name**: `test_correlation_bonferroni_divisor`. Verify α_adj = 0.05/30 (fixed global divisor).
- [X] T021 [US2] Integration test for full correlation run in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_correlation_full_run`. **MUST use** the pre-fetched real fixture file `data/fixtures/full_correlation_sample.csv` (created by T007b) as input. **MUST verify** `artifacts/correlations.csv` has 30 rows if all vars present, or fewer if missing. **MUST verify** schema conformance against `contracts/analysis_schema.yaml` (created by T007).

### Implementation for User Story 2

- [X] T022a [US2] Implement `code/analysis/correlation.py` function `iterate_lagged_pairs(df: pd.DataFrame, lags: list) -> list`. **MUST** generate all pairs of (composition_param, geomagnetic_index, lag).
- [X] T022b [US2] Implement `code/analysis/correlation.py` function `compute_pearson(df, x_col, y_col, lag) -> float`. **MUST** apply lag shift to y_col before computing Pearson r.
- [X] T022c [US2] Implement `code/analysis/correlation.py` function `compute_spearman(df, x_col, y_col, lag) -> float`. **MUST** apply lag shift to y_col before computing Spearman ρ.
- [X] T022d [US2] Implement `code/analysis/correlation.py` function `write_correlation_results(results: list, output_path: str) -> None`. **MUST** write to `artifacts/correlations.csv`. **MUST** enforce output structure: **30 rows** (if data present) with columns `composition_parameter, geomagnetic_index, lag_hours, pearson_r, spearman_rho, p_raw, p_bonferroni, significance_flag`.
- [X] T023 [US2] Implement `code/analysis/neff.py` to calculate effective sample size ($N_{eff}$) using lag autocorrelation on the FULL continuous series (1998-2020). **MUST use the method of Pyper & Peterman (late 1990s)**: **Call `scipy.signal.detrend`** on the time series to remove linear trend before calculating lag-1 autocorrelation ($\rho_1$) of the residuals, then apply formula $N_{eff} = N \frac{1-\rho_1}{1+\rho_1}$. Do NOT use `scipy.stats.autocorr` directly on raw data. **MUST implement the detrending logic inline** to ensure the producer before consumer principle is met.
- [X] T024 [US2] Implement raw p-value calculation using $N_{eff}$ in `code/analysis/correlation.py`.
- [X] T025 [US2] Implement Bonferroni correction logic in `code/analysis/correlation.py` (FR-004). **MUST derive the divisor 30 dynamically** from configuration (params × 2 indices × 5 lags) to calculate $\alpha_{adj} = 0.05 / 30$, regardless of actual data availability, to control family-wise error rate.
- [X] T026 [US2] Add flagging logic for significant pairs (Bonferroni p < 0.05) in `code/analysis/correlation.py`.
- [X] T027 [US2] Integrate US2 logic into `code/main.py` to run after US1 completes. **MUST** calculate global Neff and Bonferroni threshold values.
- [X] T028 [US2] **Write** `artifacts/thresholds/global_threshold.json` containing global Neff values and $\alpha_{adj}$. **MUST** validate against `contracts/threshold.schema.yaml` (created by T008) before writing using `jsonschema`. **This task must complete before T032**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualisation, Reporting & Validation (Priority: P3)

**Goal**: Generate visualizations (time-series, heatmaps) and a validation report on the held-out 2018-2020 period.

**Independent Test**: Run validation on 2018-2020. Verify PNGs ≤ 5MB and Markdown report correctly flags pairs with |r| > 0.5 and significant Bonferroni p (computed globally for main, applied to test set).

### Tests for User Story 3 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T029 [P] [US3] Unit test for file size check in `code/tests/test_viz.py`. **Function name**: `test_viz_png_size_limit`. **MUST use** `assert os.path.getsize(filepath) <= 5*1024*1024` to verify PNG generation ≤ 5MB.
- [X] T030 [P] [US3] Unit test for report logic in `code/tests/test_report.py`. **Function name**: `test_report_threshold_detection`. Verify |r| > 0.5 threshold detection.
- [X] T031 [US3] Integration test for full validation run in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_validation_full_run`. Verify artifacts exist and schema conformance against `contracts/visual_artifact.schema.yaml` (created by T009) (if applicable) or file existence checks.

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/viz/plots.py` to generate time-series overlay plots per lag.
- [X] T033 [P] [US3] Implement `code/viz/plots.py` to generate correlation heatmap (parameters × lags).
- [X] T034 [US3] Implement `code/viz/report.py` to split data into Train (early period) and Test (2018-2020) using constants `TRAIN_START`, `TRAIN_END`, `TEST_START`, `TEST_END` from `code/config.py`.
- [X] T035 [US3] **Compute Test Set Correlations**. **MUST** load `data/processed/synced.csv` (filtered for 2018-2020). **MUST** compute Pearson/Spearman correlations for all pairs and lags using the same logic as T022a-T022c. **MUST** calculate p-values using the **global Neff values** (from T028) but applied to the test set sample size. **MUST** write results to `artifacts/test_correlations.csv`. **MUST NOT re-compute Neff on the test set**; use the global Neff method but on test data.
- [X] T036 [US3] Implement `code/viz/report.py` to **load the GLOBAL significance threshold** (from `artifacts/thresholds/global_threshold.json` produced in T028) and **evaluate** the test set correlations (from T035) against the held-out 2018-2020 period data. **DO NOT** re-compute Neff or Bonferroni on the test set. **MUST apply** the global Bonferroni divisor (30) to the test set p-values to determine significance. **MUST report** whether the composition-index pair exceeds |r| > 0.5 **AND** has the global Bonferroni-corrected p < 0.05 in the test set.
- [X] T037 [US3] Generate Markdown report stating if Helium-Dst exceeds |r| > 0.5 (US-3 Acceptance Scenario 1). **MUST output** to `artifacts/reports/validation_report.md`. **MUST explicitly state** "Helium abundance vs. Dst at a temporal lag: r = X (significant)" if threshold met, OR "No composition parameter achieved the pre-registered effect-size threshold" if not. **MUST include** the Bonferroni-corrected p-value.
- [X] T038 [US3] Integrate US3 logic into `code/main.py` to run after US2 completes.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039a [P] Documentation updates: Create `README.md` with setup instructions, usage examples, and data source URLs.
- [X] T039b [P] Documentation updates: Create `docs/usage.md` with detailed pipeline explanation and statistical method references (Pyper & Peterman).
- [X] T040a Code cleanup: Remove unused imports from all files in `code/`.
- [X] T040b [P] Code cleanup: Fix linting errors in `code/` to pass ruff. **MUST** run `ruff check code/` and fix all errors.
- [X] T041a [P] Additional unit tests for edge cases in `code/tests/`. **Function name**: `test_align_handles_empty_dataframe`.
- [X] T041b [P] Additional unit tests for edge cases in `code/tests/`. **Function name**: `test_align_warns_large_gaps`.
- [X] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility.
- [X] T048 [P] **Benchmark Memory Usage** in `code/tests/test_pipeline.py`. **MUST** add a test `test_memory_usage_within_limits` that runs the full US1 pipeline on `data/processed/synced.csv` (produced by T017) and asserts peak RAM usage is ≤ 7GB (SC-001) and ≤ 4GB for US1 specifically (SC-004). **MUST** use `tracemalloc` or `psutil` for measurement.
- [X] T049 [P] **Benchmark Runtime** in `code/tests/test_pipeline.py`. **MUST** add a test `test_correlation_runtime_within_limits` that runs the full US2 pipeline on `data/processed/synced.csv` (produced by T017) and `artifacts/thresholds/global_threshold.json` (produced by T028) and asserts total runtime is ≤ 6 hours (SC-001). **MUST** use `time` module or `pytest-timeout` plugin.

---

## Phase N+1: Data Source Verification & Robustness (Revision)

**Purpose**: Resolve Constitution Check failure regarding missing NOAA data sources and ensure robust data fetching.

- [X] T050 [P] [US1] **Update `code/config.py`** with verified NOAA Kp and Dst URLs. **MUST** replace empty strings for `NOAA_KP_URL` and `NOAA_DST_URL` with the official NOAA National Centers for Environmental Information (NCEI) or WDC URLs (e.g., `https://www.ngdc.noaa.gov/stp/space-weather/...` or specific FTP paths). **MUST** verify these URLs are accessible and return valid data before committing. **Reference**: Plan.md "Constitution Check" failure and "Risks & Mitigations" section. **NOTE**: This task is now completed in T004a (Phase 2) and is removed from Phase N+1.
- [X] T051 [P] [US1] **Implement robust data fetching with explicit error handling** in `code/data/fetch.py`. **MUST** ensure `fetch_kp` and `fetch_dst` handle 404/503 errors explicitly and raise `RuntimeError` with a message pointing to the specific URL that failed. **MUST NOT** implement any `try/except` block that falls back to synthetic data or placeholder values when the real fetch fails. **MUST** log the exact URL attempted on failure.
- [X] T052 [P] [US1] **Add Unit Test for Fetch Failure**. **MUST** create `code/tests/test_fetch.py` with function `test_fetch_raises_on_invalid_url`. **MUST** mock the network request to return a 404 and verify that the `fetch_*` functions raise the expected `RuntimeError` without attempting to generate synthetic data. This ensures the "fail loudly" principle is tested.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Contract Definitions (Phase 2.5)**: Depends on Setup - BLOCKS validation tasks
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Performance & Resource Compliance (Phase N)**: Must complete before final CI validation to ensure SC-001 and SC-004 are met.
- **Data Source Verification (Phase N+1)**: Must complete before any full-scale data fetch to prevent pipeline aborts due to missing configuration.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST wait for T017 (US1 completion)** to ensure `synced.csv` exists.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **MUST wait for T028 (US2 completion)** to ensure `correlation_results.csv` and `artifacts/thresholds/global_threshold.json` exist.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services
- Services before Main orchestration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Performance benchmarking tasks (T048, T049) can run in parallel after their respective user stories are complete.
- Data source verification tasks (T050-T052) can run in parallel with Setup/Foundational tasks.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (Written first):
Task: "Unit test for variable validation in code/tests/test_validate.py (test_fetch_aborts_on_missing_he2plus)"
Task: "Unit test for interpolation logic in code/tests/test_align.py (test_align_interpolates_small_gaps_warns_large)"

# Launch all implementation tasks for User Story 1 together (after tests fail):
Task: "Implement logic in code/data/fetch.py to download ACE/NOAA"
Task: "Implement code/data/validate.py to abort on missing variables"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Contract Definitions & Fixture Generation
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Sync)
 - Developer B: User Story 2 (Correlation Logic)
 - Developer C: User Story 3 (Viz & Report)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All statistical operations (Neff, Bonferroni) must run on the FULL continuous time series as per FR-010 for the primary analysis. The validation period (2018-2020) MUST use the GLOBAL threshold derived from the full series, and MUST NOT re-compute local Neff or Bonferroni p-values.
- **Critical Constraint**: ACE variable names MUST match `N_p`, `T_p`, `He2+_ratio` exactly or the pipeline aborts (SC-002). The error message MUST contain the exact missing variable name.
- **Dependency Note**: T014 depends on T004a (config). T015 depends on T004a (config). T016 depends on T014/T015 (fetch). T022 depends on T017 (US1 completion). T032 depends on T028 (US2 completion). T036 depends on T028 (global thresholds) and T035 (test correlations).
- **Revision Note**: Tasks T007a/T007b now fetch REAL data for fixtures, not synthetic. T017 now marks gaps > 6h with a `gap_mask` column instead of dropping rows. T014/T015 now handle Kp and Dst separately. T035 added to compute test-set correlations explicitly.
- **Schema Note**: T017 now explicitly enforces the column renaming from raw ACE names (N_p, T_p, He2+_ratio) to the output schema names (proton_density, temperature, helium_abundance) to prevent mismatch.
- **Performance Note**: T048 and T049 address SC-001 and SC-004 by ensuring explicit benchmarking of memory and runtime.
- **Data Integrity Note**: T014 and T015 ensure that large datasets are processed without exceeding RAM limits (via conditional streaming), preventing OOM errors on CI runners.
- **Streaming Note**: T014 and T015 explicitly mandate conditional `stream=True` for large file downloads to prevent memory exhaustion during the fetch phase.
- **Chunking Note**: T017 mandates conditional chunked resampling to handle datasets larger than available RAM, ensuring the pipeline remains robust for multi-year data spans.
- **Constitution Fix Note**: T004a now contains valid NOAA URLs, resolving the "Constitution Check: Verified Accuracy" failure. T050-T052 in Phase N+1 are now redundant but kept for reference; the fix is in Phase 2.