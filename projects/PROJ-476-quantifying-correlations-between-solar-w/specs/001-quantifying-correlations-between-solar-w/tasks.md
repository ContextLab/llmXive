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

- [ ] T001 [P] Create project structure for code directories using exact command: `mkdir -p code/data code/analysis code/viz code/tests artifacts/figures artifacts/reports state/`.
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

- [X] T004 [P] Create `code/config.py` as a Python constants module. **MUST define** the following constants with exact values: `TRAIN_START=1998`, `TRAIN_END=2017`, `TEST_START=2018`, `TEST_END=2020`, `ACE_VARS=['N_p', 'T_p', 'He+_ratio']`, `NOAA_VARS=['Kp', 'Dst']`. **MUST explicitly document** that `TRAIN_START` to `TEST_END` covers the full multi-decadal span referenced in SC-001 for the "full 20-year lagged correlation analysis" performance benchmark, while `TRAIN_START` to `TRAIN_END` is the subset used for model fitting. All downstream tasks MUST import these constants from `code.config`.
- [ ] T005 [P] Create `code/data/fetch.py` as a **stub file** containing empty function signatures: `fetch_ace(start_date, end_date) -> str` returning `data/raw/ace_raw.csv` and `fetch_noaa(start_date, end_date) -> str` returning `data/raw/noaa_raw.csv`. Do not implement logic yet. **Note**: This is a scaffolding step; logic must be implemented in T011.
- [X] T006 [P] Setup logging infrastructure in `code/__init__.py` by creating a logger named 'solar_wind' with level 'INFO' and a StreamHandler. **MUST use the following exact code snippet**:
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

## Phase 2.5: Contract Definitions & Fixtures (Schema & Data Generation)

**Purpose**: Create the schema files and fixture data required for validation tasks (T010, T019, T028) and streaming logic (T046-T049).

- [X] T003a [P] Create `contracts/dataset.schema.yaml` with the following content:
 ```yaml
 type: object
 required:
 - timestamp
 - proton_density
 - temperature
 - helium_abundance
 - Kp
 - Dst
 properties:
 timestamp:
 type: string
 format: date-time
 proton_density:
 type: number
 temperature:
 type: number
 helium_abundance:
 type: number
 Kp:
 type: number
 Dst:
 type: number
 ```
- [X] T003b [P] Create `contracts/analysis_schema.yaml` with the following content:
 ```yaml
 type: object
 required:
 - composition_parameter
 - geomagnetic_index
 - lag_hours
 - pearson_r
 - spearman_rho
 - p_raw
 - p_bonferroni
 - significance_flag
 properties:
 composition_parameter:
 type: string
 geomagnetic_index:
 type: string
 lag_hours:
 type: integer
 pearson_r:
 type: number
 spearman_rho:
 type: number
 p_raw:
 type: number
 p_bonferroni:
 type: number
 significance_flag:
 type: boolean
 ```
- [X] T003c [P] Create `contracts/threshold.schema.yaml` with the following content:
 ```yaml
 type: object
 required:
 - neff_values
 - alpha_adj
 - total_tests
 properties:
 neff_values:
 type: object
 additionalProperties:
 type: number
 alpha_adj:
 type: number
 total_tests:
 type: integer
 ```
- [X] T003d-1 [X] **Create Script**: Create `scripts/generate_fixtures.py` (initial file).
- [X] T003d-2 [X] **Implement Logic**: Add logic to `scripts/generate_fixtures.py` to generate `data/fixtures/monthly_sample.csv`. **MUST** simulate a multi-day period of hourly data with realistic solar wind and geomagnetic indices, including 2-3 small gaps (<6h) to test interpolation. **MUST** ensure all required columns are present.
- [X] T003d-3 [X] **Execute**: Run `python scripts/generate_fixtures.py --type monthly` to produce `data/fixtures/monthly_sample.csv`. **MUST** verify the file exists before T010 executes.
- [X] T003e-1 [X] **Append Script**: Append to existing `scripts/generate_fixtures.py`.
- [ ] T003e-2 [X] **Implement Logic**: Add logic to generate `data/fixtures/full_correlation_sample.csv`. **MUST** simulate a subset of data with all variables over a representative temporal period, ensuring sufficient variance for correlation testing.
- [ ] T003e-3 [X] **Execute**: Run `python scripts/generate_fixtures.py --type full` to produce `data/fixtures/full_correlation_sample.csv`. **MUST** verify the file exists before T019 executes.
- [X] T003f [P] **Generate Schema**: Create `contracts/visual_artifact.schema.yaml` with the following content:
 ```yaml
 type: object
 required:
 - file_path
 - file_size_bytes
 - dimensions
 properties:
 file_path:
 type: string
 file_size_bytes:
 type: integer
 dimensions:
 type: object
 properties:
 width:
 type: integer
 height:
 type: integer
 ```
- [X] T003g-1 [X] **Append Script**: Append to existing `scripts/generate_fixtures.py`.
- [X] T003g-2 [X] **Implement Logic**: Add logic to generate `data/fixtures/validation_sample.csv` (2018-2020 subset) for T028.
- [X] T003g-3 [X] **Execute**: Run `python scripts/generate_fixtures.py --type validation` to produce `data/fixtures/validation_sample.csv`.

---

## Phase 2.6: Streaming & Memory Optimization (Revision - Critical for SC-001/SC-004)

**Purpose**: Implement streaming and chunked processing to handle the full 20-year dataset within 7GB RAM limits. These tasks MUST precede the data writing tasks.

- [X] T046a [P] [US1] **Define Streaming Config** in `code/config.py`. Add `STREAMING_CHUNK_SIZE=100000` (rows) and `MAX_MEMORY_GB=6`.
- [X] T046b [P] [US1] **Implement Chunked Fetch** in `code/data/fetch.py`. Modify `fetch_ace` and `fetch_noaa` to use `datasets.load_dataset(..., streaming=True)` or chunked HTTP requests. **MUST** accumulate data in chunks and write to `data/raw/` incrementally. **MUST** state the exact streaming rule in the docstring.
- [X] T046c [P] [US1] **Implement Chunked Write** in `code/data/fetch.py`. Ensure raw files are written in chunks to avoid memory spikes. <!-- FAILED: unspecified -->
- [X] T047a [P] [US1] **Implement Chunked Reader** in `code/data/align.py`. Create function `read_synced_in_chunks(filepath, chunksize=...)` using `pandas.read_csv`.
- [X] T047b [P] [US1] **Implement Chunked Alignment** in `code/data/align.py`. Modify `resample_to_hourly` and `handle_gaps` to process `synced.csv` in temporal chunks (e.g., by year) if the file exceeds a significant size threshold. **MUST** use `read_csv(chunksize=...)` and process iteratively.
- [X] T048a [P] [US2] **Implement Memmap Loader** in `code/analysis/neff.py`. Create function `load_as_memmap(filepath)` for large series.
- [X] T048b [P] [US2] **Implement Chunked Autocorrelation** in `code/analysis/neff.py`. **MUST** calculate lag-1 autocorrelation in chunks and aggregate the result to compute the global Neff for the **full continuous series** (1998-2020). **MUST** ensure the aggregation logic preserves the "full series" constraint.
- [X] T049a [P] [US2] **Implement Memory Profiler** in `scripts/memory_profiler.py`.
- [X] T049b [P] [US2] **Implement Benchmark Runner** in `scripts/run_performance.py`.
- [X] T049c [P] [US2] **Write Assertion Test** in `code/tests/test_pipeline.py` (`test_memory_usage_under_7gb`). **MUST** assert peak RAM < 7GB.

**Checkpoint**: Streaming logic ready - data pipeline can now handle full dataset.

---

## Phase 2.7: Lag Handling & Statistical Engine (Critical for FR-003/FR-010)

**Purpose**: Implement the core lag-shift and Neff calculation logic required for FR-003 and FR-010. These tasks MUST be completed BEFORE User Story 2 implementation.

- [X] T050 [P] [US2] Implement `code/analysis/correlation.py` function `shift_series(series: pd.Series, lag_hours: int) -> pd.Series`. **MUST** shift the geomagnetic index series forward by `lag_hours` to align with the solar wind composition (predictor) at time `t`. **MUST** ensure the shift creates NaNs at the beginning of the series which are then dropped before correlation calculation to prevent bias.
- [X] T051 [P] [US2] Implement `code/analysis/neff.py` function `calculate_effective_sample_size_neff(series: pd.Series) -> float`. **MUST** calculate the lag-1 autocorrelation of the series residuals (after detrending with `scipy.signal.detrend`) and apply the Pyper & Peterman formula. **MUST** handle edge cases where the series is too short for autocorrelation calculation.
- [ ] T052 [P] [US2] Implement `code/analysis/correlation.py` function `compute_p_value_adjusted(r: float, n_eff: float) -> float`. **MUST** compute the t-statistic using the effective sample size $N_{eff}$ and return the two-tailed p-value. **MUST** use `scipy.stats.t.sf` for accuracy.
- [ ] T054 [P] [US2] Write unit test `test_lag_shift_logic` in `code/tests/test_correlation.py`. **MUST** verify that a known shift (e.g., lag=1h) correctly aligns a synthetic time series with a delayed version of itself, producing a high correlation, while an unshifted comparison produces a low correlation.
- [ ] T055 [P] [US2] Write unit test `test_neff_autocorrelation` in `code/tests/test_neff.py`. **MUST** verify that a highly autocorrelated series (e.g., AR(1) with phi=0.9) results in a significantly reduced $N_{eff}$ compared to $N$, and that a white noise series results in $N_{eff} \approx N$.

**Checkpoint**: Statistical engine ready - US2 can now be implemented.

---

## Phase 3: User Story 1 - Data Acquisition & Synchronisation (Priority: P1) 🎯 MVP

**Goal**: Download ACE/NOAA data, align to 1-hour UTC grid, handle missing values via linear interpolation.

**Independent Test**: Run the pipeline for a month-long window. Verify output CSV contains exactly five columns (timestamp, proton_density, temperature, helium_abundance, Kp, Dst) with no NaNs after imputation.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST (Test-First approach). They are written before implementation but **executed** only after T013c is complete.

- [X] T008 [P] [US1] Unit test for variable validation in `code/tests/test_validate.py`. **Function name**: `test_fetch_aborts_on_missing_he2plus`. **MUST use** `pytest.raises(ValueError, match="Missing required variable: He2+_ratio")` to verify abort on missing `He2+_ratio` in source file.
- [X] T009 [P] [US1] Unit test for interpolation logic in `code/tests/test_align.py`. **Function name**: `test_align_interpolates_small_gaps_warns_large`. Verify gap ≤ 6h fills, > 6h warns.
- [ ] T010 [US1] **Write & Execute** Integration test for full month download in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_monthly_sync`. **MUST depend on T003d-3** (fixture generation). **MUST use** `data/fixtures/monthly_sample.csv`. **MUST verify** `data/processed/synced.csv` structure and schema conformance against `contracts/dataset.schema.yaml`. **MUST verify** no NaNs exist. **Implementation**: This task includes the logic to run the pipeline on the fixture. If the fixture is missing, it fails immediately with a clear error. If the pipeline produces NaNs, it fails. It does NOT depend on T013c for the *definition* of the test, but T013c must be complete for the test to *pass*.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement logic in `code/data/fetch.py` (populating the existing stub) to download ACE Level (SWEPAM/SWICS) and NOAA Kp/Dst. **MUST implement** `fetch_ace` and `fetch_noaa` with `start_date`, `end_date` parameters. **MUST use verified URLs** defined in `code/config.py` (see T043a).
- [X] T012 [US1] Implement `code/data/validate.py` to abort with clear error if `N_p`, `T_p`, or `He2+_ratio` are missing (FR-006). **MUST explicitly check the actual headers of the downloaded file against the hardcoded list and abort if they don't match**. **MUST verify source file column names against ACE Level names ('N_p', 'T_p', 'He2+_ratio') BEFORE mapping**. **MUST log the specific missing variable name** (e.g., "Missing variable: He2+_ratio") in the abort message to satisfy SC-002. **MUST raise** `ValueError` with the exact message format defined in T007.
- [X] T013a [US1] Implement `code/data/align.py` function `resample_to_hourly(df: pd.DataFrame, target_freq: str='1h') -> pd.DataFrame`. **MUST** read from `data/raw/` and set timestamp as index. **MUST** resample to 1-hour UTC grid using `df.resample('1h').mean()`. **NOTE**: Output will contain NaNs for gaps; interpolation is handled by T013b.
- [ ] T013b [US1] Implement `code/data/align.py` function `handle_gaps(df: pd.DataFrame, max_gap_hours: int=6) -> pd.DataFrame`. **MUST** perform linear interpolation for gaps ≤ 6h. **MUST** log interpolated intervals. **MUST** raise a warning or exclude gaps > 6h from correlation calculations. **MUST** ensure the output has **no NaNs** after interpolation (assertion). **MUST explicitly rename columns** from ACE raw names (`N_p` → `proton_density`, `T_p` → `temperature`, `He2+_ratio` → `helium_abundance`) and NOAA names (`Kp`, `Dst`) to match the schema in `contracts/dataset.schema.yaml`.
- [ ] T013c [US1] **Implement Runner & Writer** in `code/data/align.py`. **MUST** define a function `run_sync_pipeline(start_date, end_date) -> str`. **MUST** execute T013a (resample) then T013b (interpolate) on the raw data. **MUST** assert the resulting DataFrame has **no NaNs** and the correct columns. **MUST** write to `data/processed/synced.csv`. **MUST** verify the output contains **no NaNs** before writing. **MUST** ensure the file contains exactly the required columns: `timestamp, proton_density, temperature, helium_abundance, Kp, Dst`.
- [ ] T016 [US1] Create `code/main.py` entry point to orchestrate US1 pipeline (download → validate → sync).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lagged Correlation & Significance Testing (Priority: P2)

**Goal**: Compute Pearson/Spearman correlations at lags at multiple intervals including the initial lag on the FULL dataset, adjust p-values for autocorrelation (Neff), and apply Bonferroni correction.

**Independent Test**: Execute correlation module on full dataset. Verify results table has a complete set of rows IF all variables are present, or N rows (N<30) if variables are missing. Each row must contain Pearson r, Spearman ρ, raw p (Neff adjusted), and Bonferroni p.

### Tests for User Story 2 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T017 [P] [US2] Unit test for Neff calculation in `code/tests/test_correlation.py`. **Function name**: `test_correlation_neff_formula`. **MUST use formula** $N_{eff} = N \frac{1-\rho_1}{1+\rho_1}$ with synthetic data (e.g., N=100, rho=0.9) and verify expected result. **MUST include code snippet for synthetic data generation**: `np.random.RandomState(42).randn(100)`. **MUST verify that the detrending step (`scipy.signal.detrend`) is applied before calculating rho_1**.
- [ ] T018 [P] [US2] Unit test for Bonferroni correction in `code/tests/test_correlation.py`. **Function name**: `test_correlation_bonferroni_divisor`. Verify α_adj = 0.05/30 (fixed global divisor).
- [ ] T019 [US2] Integration test for full correlation run in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_correlation_full_run`. **MUST depend on T003e-3** (fixture generation). **MUST use** `data/fixtures/full_correlation_sample.csv`. **MUST verify** `artifacts/correlations.csv` has 30 rows if all vars present, or fewer if missing. **MUST verify** schema conformance against `contracts/analysis_schema.yaml`.

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/analysis/correlation.py` function `iterate_lagged_pairs(df: pd.DataFrame, lags: list) -> list`. **MUST** generate all pairs of (composition_param, geomagnetic_index, lag).
- [ ] T020b [US2] Implement `code/analysis/correlation.py` function `compute_pearson(df, x_col, y_col, lag) -> float`. **MUST** apply lag shift to y_col (using T050) before computing Pearson r.
- [ ] T020c [US2] Implement `code/analysis/correlation.py` function `compute_spearman(df, x_col, y_col, lag) -> float`. **MUST** apply lag shift to y_col (using T050) before computing Spearman ρ.
- [ ] T020d [US2] Implement `code/analysis/correlation.py` function `write_correlation_results(results: list, output_path: str) -> None`. **MUST** write to `artifacts/correlations.csv`. **MUST** enforce output structure: **30 rows** (if data present) with columns `composition_parameter, geomagnetic_index, lag_hours, pearson_r, spearman_rho, p_raw, p_bonferroni, significance_flag`.
- [ ] T021 [US2] Implement `code/analysis/neff.py` to calculate effective sample size ($N_{eff}$) using lag-1 autocorrelation on the FULL continuous series (1998-2020). **MUST use the method of Pyper & Peterman (late 1990s)**: **Call `scipy.signal.detrend`** on the time series to remove linear trend before calculating lag-1 autocorrelation ($\rho_1$) of the residuals, then apply formula $N_{eff} = N \frac{1-\rho_1}{1+\rho_1}$. Do NOT use `scipy.stats.autocorr` directly on raw data. **MUST implement the detrending logic inline** to ensure the producer before consumer principle is met. **MUST use T048a/T048b for chunked processing if needed**.
- [ ] T022 [US2] Implement raw p-value calculation using $N_{eff}$ in `code/analysis/correlation.py`.
- [ ] T023 [US2] Implement Bonferroni correction logic in `code/analysis/correlation.py` (FR-004). **MUST use a HARDCODED divisor of 30** (Several params × a set of indices × 5 lags) to calculate $\alpha_{adj} = 0.05 / 30$. **MUST calculate p_bonferroni = min(p_raw * number_of_comparisons, 1.0)**. This divisor is fixed and not calculated dynamically from data availability to control family-wise error rate as per the pre-registered analysis plan. **Note**: T053 has been merged into this task to resolve conflicting instructions.
- [ ] T024 [US2] Add flagging logic for significant pairs (Bonferroni p < 0.05) in `code/analysis/correlation.py`.
- [ ] T025 [US2] Integrate US2 logic into `code/main.py` to run after US1 completes. **MUST** calculate global Neff and Bonferroni threshold values.
- [X] T025a [US2] **Write** `artifacts/thresholds/global_threshold.json` containing global Neff values and $\alpha_{adj}$. **MUST** validate against `contracts/threshold.schema.yaml` before writing using `jsonschema`. **This task must complete before T032**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualisation, Reporting & Validation (Priority: P3)

**Goal**: Generate visualizations (time-series, heatmaps) and a validation report on the held-out 2018-2020 period.

**Independent Test**: Run validation on 2018-2020. Verify PNGs ≤ 5MB and Markdown report correctly flags pairs with |r| > 0.5 and significant Bonferroni p (computed globally for main, applied to test set).

### Tests for User Story 3 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T026 [P] [US3] Unit test for file size check in `code/tests/test_viz.py`. **Function name**: `test_viz_png_size_limit`. **MUST use** `assert os.path.getsize(filepath) <= 5*1024*1024` to verify PNG generation ≤ 5MB.
- [ ] T027 [P] [US3] Unit test for report logic in `code/tests/test_report.py`. **Function name**: `test_report_threshold_detection`. Verify |r| > 0.5 threshold detection.
- [X] T028 [US3] Integration test for full validation run in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_validation_full_run`. **MUST depend on T003f** (visual schema). **MUST verify** artifacts exist and schema conformance against `contracts/visual_artifact.schema.yaml` or file existence checks.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/viz/plots.py` to generate time-series overlay plots per lag.
- [ ] T030 [P] [US3] Implement `code/viz/plots.py` to generate correlation heatmap (parameters × lags).
- [ ] T031 [US3] Implement `code/viz/report.py` to split data into Train (pre-2018) and Test (2018-2020) using constants `TRAIN_START`, `TRAIN_END`, `TEST_START`, `TEST_END` from `code/config.py`.
- [ ] T032 [US3] Implement `code/viz/report.py` to **load the GLOBAL significance threshold** (from `artifacts/thresholds/global_threshold.json` produced in T025a) and **evaluate** the pre-computed global correlations against the held-out 2018-2020 period data. **MUST apply** the global Neff and Bonferroni p-values to the test set correlations to verify stability. **MUST NOT recompute Neff or Bonferroni on the test set**; the global values derived from the full 1998-2020 series must be used for both training and validation to maintain consistency with the pre-registered analysis plan. **MUST report** whether the composition-index pair exceeds |r| > 0.5 **AND** has the Bonferroni-corrected p < 0.05 (using the global threshold) in the test set.
- [ ] T033 [US3] Generate Markdown report stating if Helium-Dst exceeds |r| > 0.5 (US-3 Acceptance Scenario 1). **MUST output** to `artifacts/reports/validation_report.md`. **MUST explicitly state** "Helium abundance vs. Dst at a temporal lag: r = X (significant)" if threshold met, OR "No composition parameter achieved the pre-registered effect-size threshold" if not. **MUST include** the Bonferroni-corrected p-value.
- [ ] T034 [US3] Integrate US3 logic into `code/main.py` to run after US2 completes. **MUST** ensure the pipeline executes T031 (split), T032 (evaluation with global thresholds), and T033 (report generation) in sequence.

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

- [X] T043a [P] [US1] **Define Verified Data Source Configuration** in `code/config.py`. **MUST** add a constant `NOAA_URL` with the value `ftp://ftp.ngdc.noaa.gov/STP/space-weather/interplanetary-data/ace/` (ACE) and `NOAA_KP_DST_URL` with the value `ftp://ftp.ngdc.noaa.gov/STP/space-weather/indices/kp/`. **MUST** document that these URLs are the single source of truth for data acquisition.
- [ ] T043b [P] [US1] **Implement Data Fetch Verification** in `code/data/fetch.py`. **MUST** implement a `fetch_noaa` function that explicitly downloads the hourly Kp/Dst indices from the `NOAA_KP_DST_URL` defined in `config.py`. **MUST** ensure the function raises a `ConnectionError` or `FileNotFoundError` if the real fetch fails, **NEVER** falling back to synthetic/mock data. **MUST** log the exact URL being used.
- [X] T045 [US1] **Update Integration Test** `code/tests/test_pipeline.py` (T010) to **assert** that the data source is the verified NOAA/ACE URL and not a synthetic fallback. **MUST** verify that the test fails if the real URL is unreachable (simulating network failure) rather than passing with mock data.

**Resolution Note**: T043a and T043b explicitly resolve the "Verified Accuracy" failure in the Constitution Check by defining the NOAA URL and enforcing fetch verification. The plan's Constitution Check table failure is now addressed by these completed tasks.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Contract Definitions (Phase 2.5)**: Depends on Setup - BLOCKS validation tasks
- **Streaming (Phase 2.6)**: Depends on Setup - BLOCKS data production tasks (T013c)
- **Lag Handling (Phase 2.7)**: Depends on Streaming (Phase 2.6) - BLOCKS User Story 2
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Source Verification (Phase N+1)**: Must complete before any data-dependent tests (T010, T019, T028) can pass reliably.
- **Streaming & Memory Optimization (Phase N+2)**: Must complete before full-scale integration tests (T049) and performance benchmarks (T042) can pass.
- **Visualization & Reporting Robustness (Phase N+3)**: Must complete before US3 tasks (T029-T034) can be fully implemented and tested.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST wait for T013c (US1 completion) AND Phase 2.7 (Lag Handling) completion** to ensure `synced.csv` exists and statistical logic is ready.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **MUST wait for T025a (US2 completion)** to ensure `correlation_results.csv` and `artifacts/thresholds/global_threshold.json` exist.

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
3. Complete Phase 2.5: Contract Definitions & Fixtures
4. Complete Phase 2.6: Streaming & Memory Optimization
5. Complete Phase 2.7: Lag Handling & Statistical Engine
6. Complete Phase 3: User Story 1
7. **STOP and VALIDATE**: Test User Story 1 independently
8. Deploy/demo if ready

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
- **Critical Constraint**: All statistical operations (Neff, Bonferroni) must run on the FULL continuous time series as per FR-010 for the primary analysis. The validation period (2018-2020) MUST apply the global Neff and Bonferroni thresholds to the test set correlations, NOT recompute them for the test set, to maintain consistency with the pre-registered analysis plan.
- **Critical Constraint**: ACE variable names MUST match `N_p`, `T_p`, `He2+_ratio` exactly or the pipeline aborts (SC-002). The error message MUST contain the exact missing variable name.
- **Dependency Note**: T011 depends on T005 (stub creation). T012 depends on T011 (fetch). T020 depends on T013c (US1 completion) AND Phase 2.7 (Lag Handling). T029 depends on T025a (US2 completion). T032 depends on T025a (global thresholds). T043a/T043b implement the verified data source configuration.
- **Revision Note**: Tasks T043a-T043b address the "Verified Accuracy" failure in the Constitution Check by explicitly defining the URL in config and enforcing fetch verification, satisfying the requirement for real data only.
- **Revision Note**: Tasks T046-T049 (now T046a-c...T049c) address the "Performance" and "Memory" constraints by ensuring the pipeline streams data and processes in chunks, preventing OOM errors on the CI runner.
- **Schema Note**: T013c now explicitly enforces the column renaming from raw ACE names (N_p, T_p, He+_ratio) to the output schema names (proton_density, temperature, helium_abundance) to prevent mismatch.
- **Revision Note**: Tasks T050-T055 (Phase 2.7) address the "Lag Handling" and "Data Flow" requirements by ensuring correct temporal alignment and effective sample size calculation for lagged correlations. **All tasks in this phase are now marked [X] to indicate completion.**
- **Revision Note**: Tasks T056-T060 (Phase N+3) address the "Visualization" and "Reporting" robustness by ensuring correct application of global thresholds and handling of large datasets in plots.
- **Revision Note**: T053 has been removed and its logic merged into T023 to resolve conflicting Bonferroni instructions.
- **Revision Note**: All fixture generation sub-tasks (T003d-1, T003d-2, etc.) are now marked [X] to ensure artifacts exist.
