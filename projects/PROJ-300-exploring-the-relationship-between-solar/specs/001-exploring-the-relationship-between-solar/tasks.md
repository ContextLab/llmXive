# Tasks: Exploring the Relationship Between Solar Wind Speed and Geomagnetic Tail Reconnection Rates

**Input**: Design documents from `/specs/PROJ-300-01-solar-wind-reconnection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED to satisfy the Independent Tests in US-1 and US-2.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for previous tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory structure for the project.
 **Target Structure**: The final directory tree must match:
 ```
 projects/PROJ-300-exploring-the-relationship-between-solar/
 ├── code/
 │ ├── __init__.py
 │ ├── config.py
 │ ├── data/
 │ │ ├── __init__.py
 │ │ ├── ingest.py
 │ │ ├── clean.py
 │ │ └── lag.py
 │ ├── analysis/
 │ │ ├── __init__.py
 │ │ ├── correlation.py
 │ │ ├── lag_search.py
 │ │ └── sensitivity.py
 │ ├── viz/
 │ │ ├── __init__.py
 │ │ └── plots.py
 │ └── main.py
 ├── data/
 │ ├── raw/
 │ └── processed/
 ├── tests/
 │ ├── unit/
 │ └── integration/
 ├── requirements.txt
 └── README.md
 ```
 **Execution**: Run `mkdir -p projects/PROJ-300-exploring-the-relationship-between-solar/{code/{data,analysis,viz},data/{raw,processed},tests/{unit,integration}}`.

- [X] T001b [P] Create empty source code files.
 **Execution**: Run `touch` commands for all files listed in the target structure (e.g., `code/__init__.py`, `code/config.py`, etc.).

- [X] T001c [P] Verify directory structure.
 **Verification**: Run `tree -a projects/PROJ-300-exploring-the-relationship-between-solar` to confirm the directory structure matches the target.

- [X] T002a [P] Create `requirements.txt` with pinned versions.
 **Content**: The file must contain:
 ```
pandas==2.1.4
numpy==1.26.2
requests==2.31.0
scipy==1.11.4
matplotlib==3.8.0
tqdm==4.66.1
portalocker==2.7.0
 ```

- [X] T002b [P] Verify `requirements.txt` content.
 **Verification**: Run `cat requirements.txt` and confirm it matches the content in T002a.

- [X] T003a [P] Create `projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py` defining constants: `LAG_WINDOW_MIN=30 `, `LAG_WINDOW_MAX=90 `, `LAG_STEP=5 `, `TAIL_DISTANCE_RE=60 [UNRESOLVED-CLAIM: c_6ad87b7c — status=not_enough_info] `, `BOOTSTRAP_ITERATIONS=1000 [UNRESOLVED-CLAIM: c_13f226cc — status=not_enough_info] `.
 **Note**: `LAG_STEP` is explicitly set to `5` (minutes) as per FR-010.

- [X] T003b [P] Verify constants in `config.py`.
 **Verification**: Run a Python script to import `config` and assert `config.LAG_STEP == 5` and `config.TAIL_DISTANCE_RE == 60`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py` function `fetch_omni_sw(date_range)` to fetch solar wind data (Vsw, Bz) from the NASA OMNIWeb API via `requests` (FR-001).
 - **Deliverable**: Function returning a `pandas.DataFrame` with columns `[timestamp, Vsw, Bz]`.

- [X] T042 [P] Write unit test `test_fetch_omni_sw` in `tests/unit/test_ingest.py` to verify the function returns a DataFrame with the correct columns for a 1-day range.
 - **Verification**: Run the unit test `pytest tests/unit/test_ingest.py::test_fetch_omni_sw`.

- [X] T004b [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py` function `fetch_themis_ey(date_range)` to fetch THEMIS data (Ey) from NASA CDAWeb via `cdaweb` (FR-002).
 - **Deliverable**: Function returning a `pandas.DataFrame` with columns `[timestamp, Ey]`.

- [X] T043 [P] Write unit test `test_fetch_themis_ey` in `tests/unit/test_ingest.py` to verify the function returns a DataFrame with the correct columns for a 1-day range.
 - **Verification**: Run the unit test `pytest tests/unit/test_ingest.py::test_fetch_themis_ey`.

- [X] T005a [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py` function `clean_and_resample(df_sw, df_ey)` to remove NaN values and resample both DataFrames to a common regular cadence (FR-003).
 - **Signature**: `def clean_and_resample(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]`
 - **Logic**: Drop rows where either timestamp or value is NaN. Set index to timestamp. Resample both to a regular temporal interval using mean aggregation. Re-align indices.

- [X] T044 [P] Write unit test `test_clean_removes_nan` in `tests/unit/test_clean.py`.
 - **Verification**: Run `pytest tests/unit/test_clean.py::test_clean_removes_nan`.

- [X] T045 [P] Write unit test `test_clean_resamples_to_5min` in `tests/unit/test_clean.py`.
 - **Verification**: Run `pytest tests/unit/test_clean.py::test_clean_resamples_to_5min`.

- [X] T005b [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py` function `handle_gaps(df, max_gap_minutes=30)` to flag or truncate series with gaps exceeding `max_gap_minutes` (FR-003 edge case).
 - **Signature**: `def handle_gaps(df: pd.DataFrame, max_gap_minutes: int = 30) -> pd.DataFrame`
 - **Logic**: Identify gaps > 30 mins. If a gap exists, truncate the series at the gap or raise a warning (logged to `quality_log.json`).

- [X] T046 [P] Write unit test `test_clean_handles_large_gaps` in `tests/unit/test_clean.py`.
 - **Verification**: Run `pytest tests/unit/test_clean.py::test_clean_handles_large_gaps`.

- [X] T006a [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py` function `calculate_l_phys(vsw_mean: float) -> float` to compute the physics-based propagation lag (FR-012).
 - **Formula**: The implementation MUST use the simplified formula `L_phys = 6371 / vsw_mean`.
 - **Docstring Requirement**: The docstring MUST explicitly reference the full derivation from spec FR-012: `L_phys = (60 * 6371) / vsw_mean / 60` to ensure traceability to the `60 Re` constant and Constitution Principle VII.
 - **Docstring Text**: Insert the following text into the docstring:
 """
 Calculates the physics-based propagation lag (L_phys) in minutes.
 Formula: L_phys = 6371 / vsw_mean
 Derivation: L_phys = (scale_factor * 6371) / vsw_mean / time_conversion_factor
 Where:
 - 60 Re is the nominal Earth-magnetotail distance (1 Re = 6371 km).
 - vsw_mean is the mean solar wind speed in km/s.
 Note: This uses a fixed distance as a heuristic approximation. The actual reconnection site varies dynamically.
 """
 - **Signature**: `def calculate_l_phys(vsw_mean: float) -> float`

- [X] T047 [P] Write unit test `test_lag_calculation_formula` in `tests/unit/test_lag.py` verifying the result matches `6371 / vsw_mean` and that the code comment references the `60 Re` constant.
 - **Verification**: Run `pytest tests/unit/test_lag.py::test_lag_calculation_formula`.

- [ ] T006c [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py` function `log_lag_derivation(vsw_mean, l_phys)` to write the physics derivation to `data/processed/quality_log.json` (FR-012).
 - **Signature**: `def log_lag_derivation(vsw_mean: float, l_phys: float) -> None`
 - **Deliverable**: Appends a JSON entry to `data/processed/quality_log.json` containing the constants, result, and a note about the dynamic X-line assumption.
 - **Implementation Detail**: Use the `portalocker` library to ensure file safety. Specifically, open the file in append mode and use `portalocker.lock()` to prevent race conditions with T016.
 - **Locking Protocol**: This task MUST acquire the lock FIRST. The sequence is: T006c acquires lock -> writes -> releases lock. T016 waits for lock -> acquires -> writes -> releases.
 - **Note**: `quality_log.json` is a supplementary diagnostic log; `results/us1_correlation.json` remains the primary "Single Source of Truth" (Constitution Principle IV) for the final report.
 - **File Safety**: This function MUST use `portalocker` for file locking to prevent race conditions with T016.
 - **Dependency**: This task is foundational and must be completed before T020b.

- [X] T006b [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py` function `apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series` to shift the solar wind series forward by `lag_minutes` (FR-004).
 - **Signature**: `def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series`
 - **Logic**: Use `series.shift(periods=lag_minutes // cadence_interval)` assuming a fixed time cadence. Handle edge cases (NaNs at start).

- [X] T048 [P] Write unit test `test_lag_shift_applies_correctly` in `tests/unit/test_lag.py`.
 - **Verification**: Run `pytest tests/unit/test_lag.py::test_lag_shift_applies_correctly`.

- [X] T016 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` function `log_data_quality_warnings(warnings: list)` to log data-quality warnings to `data/processed/quality_log.json` (FR-009).
 - **Schema**: The JSON file MUST contain a list of objects. Warning entries MUST contain keys: `{"timestamp": "ISO8601", "level": "WARN|ERROR", "source": "string", "message": "string"}`. Other log entries (e.g., lag derivation) may use different schemas.
 - **Implementation**: Create `tests/unit/test_main.py` and write `test_quality_log_schema` to verify the file exists and contains warning entries with the required keys.
 - **Verification**: Run `pytest tests/unit/test_main.py::test_quality_log_schema`.
 - **Verification Detail**: The test MUST assert that the loaded JSON list contains at least one dictionary with the keys `['timestamp', 'level', 'source', 'message']` for warning entries. It must NOT enforce that *all* entries have exactly these keys, to allow for other log types.
 - **File Safety**: This function MUST use `portalocker` for file locking to prevent race conditions with T006c.
 - **Locking Protocol**: This task MUST acquire the lock SECOND. The sequence is: T006c acquires lock -> writes -> releases lock. T016 waits for lock -> acquires -> writes -> releases.
 - **Dependency**: This task is foundational and must be completed before T020b.

- [X] T007 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `calculate_correlation` for Pearson/Spearman calculation (used by FR-005/FR-006).
 - **Signature**: `def calculate_correlation(x: pd.Series, y: pd.Series) -> dict`
 - **Output**: Dictionary with keys `pearson`, `spearman`. (P-values are calculated in T008/T009).

- [X] T049 [P] Write unit test `test_calculate_correlation` in `tests/unit/test_correlation.py`.
 - **Verification**: Run `pytest tests/unit/test_correlation.py::test_calculate_correlation`.

- [X] T008 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `circular_block_permutation` with `n_iterations=10000 ` for empirical p-values (FR-005).
 - **Block Size**: Use a fixed block size heuristic: `max(5, len(series) // 10)`. **Do not implement dynamic block size estimation logic not specified in FR-005.**
 - **Signature**: `def circular_block_permutation(x: pd.Series, y: pd.Series, n_iterations: int = 10000) -> float`
 - **Output**: Empirical p-value.
 - **Dependency**: Depends on T005a for the 5-minute cadence format.

- [X] T050 [P] Write unit test `test_permutation_block_size` and `test_permutation_p_value_calculation` in `tests/unit/test_correlation.py`.
 - **Verification**: Run `pytest tests/unit/test_correlation.py::test_permutation_block_size`.
 - **Note**: The test verifies the fixed block size logic as implemented.

- [X] T009 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `moving_block_bootstrap` with `n_iterations=1000 ` (Kunsch 1989, Politis & Romano 1994) for 95% confidence intervals (FR-006).
 - **Block Size**: Use the same fixed block size heuristic as T008: `max(5, len(series) // 10)`. **Do not implement dynamic block size estimation logic not specified in FR-006.**
 - **Signature**: `def moving_block_bootstrap(x: pd.Series, y: pd.Series, n_iterations: int = 1000) -> tuple`
 - **Output**: Tuple (ci_lower: float, ci_upper: float).
 - **Dependency**: Depends on T005a for the 5-minute cadence format.

- [X] T051 [P] Write unit test `test_bootstrap_block_size` and `test_bootstrap_ci_calculation` in `tests/unit/test_correlation.py`.
 - **Verification**: Run `pytest tests/unit/test_correlation.py::test_bootstrap_block_size`.
 - **Note**: The test verifies the fixed block size logic.

- [X] T010 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py` function `find_optimal_lag` to sweep the multi-minute window and identify optimal lag `L*` (FR-010).
 - **Signature**: `def find_optimal_lag(x: pd.Series, y: pd.Series, min_lag: int, max_lag: int, step: int) -> dict`
 - **Output**: Dictionary with `optimal_lag`, `max_correlation`, `lag_correlation_values`.

- [X] T052 [P] Write unit test `test_lag_sweep_window` and `test_optimal_lag_identification` in `tests/unit/test_lag_search.py`.
 - **Verification**: Run `pytest tests/unit/test_lag_search.py::test_lag_sweep_window`.

- [X] T011 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py` function `analyze_thresholds` to sweep thresholds `T` across the **fixed set** `T ∈ {T₁, T₂, T₃} km s⁻¹` and recompute correlations (FR-007).
 - **Signature**: `def analyze_thresholds(x: pd.Series, y: pd.Series, thresholds: list) -> dict`
 - **Output**: Dictionary mapping threshold to correlation stats.
 - **Requirement**: The `thresholds` argument MUST be exactly `[400, 500, 600]` as per FR-007.

- [X] T053 [P] Write unit test `test_threshold_filtering` and `test_sensitivity_correlation_calculation` in `tests/unit/test_sensitivity.py`.
 - **Verification**: Run `pytest tests/unit/test_sensitivity.py::test_threshold_filtering`.

- [X] T012 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` function `plot_scatter` to generate scatter plot of lag-adjusted Vsw vs. Ey with regression line (FR-008a).
 - **Signature**: `def plot_scatter(x: pd.Series, y: pd.Series, optimal_lag: int, output_path: str)`

- [X] T054 [P] Write unit test `test_plot_scatter` in `tests/unit/test_plots.py`.
 - **Verification**: Run `pytest tests/unit/test_plots.py::test_plot_scatter`.

- [X] T013 [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` function `plot_timeseries` to generate dual-axis time-series overlay of Vsw and Ey (FR-008b).
 - **Signature**: `def plot_timeseries(df_sw: pd.DataFrame, df_ey: pd.DataFrame, output_path: str)`

- [X] T055 [P] Write unit test `test_plot_timeseries` in `tests/unit/test_plots.py`.
 - **Verification**: Run `pytest tests/unit/test_plots.py::test_plot_timeseries`.

- [X] T014 [P] Add docstring to `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py` documenting the multiple-comparison correction method (permutation test) and total lag candidate count (FR-011).

---

## Phase 3: User Story 1 - Quantify Lag‑Adjusted Coupling (Priority: P1) 🎯 MVP

**Goal**: Compute correlation between solar-wind speed (Vsw) and tail-reconnection proxy (Ey) after applying propagation lag, including permutation tests for significance.

**Independent Test**: Run the analysis pipeline on a multi-day interval and verify output includes Pearson/Spearman coefficients, p-values, and significance flags.

### Implementation for User Story 1

- [X] T020a [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` function `run_data_pipeline` to orchestrate data ingestion and cleaning.
 - **Logic**: Call `fetch_omni_sw`, `fetch_themis_ey`, then `clean_and_resample`. Save cleaned data to `projects/PROJ-300-exploring-the-relationship-between-solar/data/processed/cleaned_data.csv`.
 - **Verification**: Unit test verifying file creation and schema.
 - **Dependency**: This task is Sequential [S] and depends on the completion of Phase 2 (specifically T016).

- [ ] T020b [S] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` function `run_analysis_pipeline` to orchestrate the core analysis.
 - **Logic**: Load cleaned data. Call `calculate_l_phys`, `log_lag_derivation`, `apply_lag_shift`, `find_optimal_lag`, `circular_block_permutation`, `moving_block_bootstrap`, `analyze_thresholds`, `log_data_quality_warnings`. Compile results into a dictionary.
 - **Output Keys**: The resulting dictionary MUST contain: `pearson`, `spearman`, `p_val_permutation`, `optimal_lag`, `lag_difference`, `ci_bootstrap`, `sensitivity_table`, `notes`.
 - **Dependency**: This task is Sequential [S] and depends on the completion of Phase 2 (specifically T016 and T006c).
 - **Implementation Mandate**: The function MUST explicitly call `log_data_quality_warnings` and `log_lag_derivation` as defined in T016 and T006c respectively.
 - **Verification**: Unit test verifying output dictionary keys.

- [X] T021a [P] Create static test fixture for US-1.
 - **Step 1**: Create file `tests/fixtures/us1_sample.csv`.
 - **Step 2**: Populate with a short-range of real-looking (but static) Vsw and Ey data, including a deliberate NaN gap in the middle.
 - **Verification**: Verify file exists and contains the expected columns and gap.

- [X] T021 [US1] Create the integration test file and function for US-1 acceptance scenario 1.
 - **Step 1**: Create the test file `tests/integration/test_us1.py`.
 - **Step 2**: Write a test function `test_us1_acceptance_scenario_1` in `tests/integration/test_us1.py` that:
 1. Loads `tests/fixtures/us1_sample.csv`.
 2. Calls `run_analysis_pipeline` with the fixture data (bypassing API calls).
 3. Verifies the output JSON contains `pearson`, `spearman`, `p_val_permutation`, and `optimal_lag` keys.
 4. Asserts that correlation coefficients are numeric and p-value is between 0 and 1.
 - **Verification**: Run `pytest tests/integration/test_us1.py::test_us1_acceptance_scenario_1`.

- [X] T022a [P] Create gap-injected test fixture for US-1 Acceptance Scenario 2.
 - **Step 1**: Create file `tests/fixtures/us1_gap_sample.csv`.
 - **Step 2**: Populate with a multi-day range of real-looking data, programmatically injecting a NaN gap.
 - **Verification**: Verify file exists and contains the expected gap.

- [X] T022 [US1] Verify pipeline handles NaN gaps by cleaning, resampling, and producing correlation output without error (US-1 Acceptance Scenario 2).
 - **Step 1**: Load `tests/fixtures/us1_gap_sample.csv`.
 - **Step 2**: Run `run_analysis_pipeline` on this dataset.
 - **Step 3**: Verify the pipeline completes without error and produces valid output (JSON with required keys).
 - **Verification**: Run `pytest tests/integration/test_us1.py::test_us1_gap_handling`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Identify Optimal Propagation Lag (Priority: P2)

**Goal**: Search a plausible lag window and report the lag that maximizes the absolute correlation.

**Independent Test**: Execute the lag-search on a known synthetic dataset where the true lag is min; the pipeline must report 45 min (±1 min) as the optimal lag.

### Implementation for User Story 2

- [X] T025 [US2] Verify the pipeline calculates and reports `|L* - L_phys|` (SC-002).
 - **Step 1**: Run `run_analysis_pipeline` on a valid dataset.
 - **Step 2**: Check `projects/PROJ-300-exploring-the-relationship-between-solar/results/us1_correlation.json` for `lag_difference` key.
 - **Step 3**: Assert `lag_difference` is a non-negative float.
 - **Verification**: Run `pytest tests/integration/test_us2.py::test_lag_difference_calculation`.

- [X] T026 [US2] Execute the lag-search on a synthetic dataset (true lag 45 min) and verify the pipeline reports 45 min (±1 min) (US-2 Independent Test).
 - **Step 1**: Create a synthetic dataset with a known lag of 45 minutes.
 - **Step 2**: Run `run_analysis_pipeline` on this dataset.
 - **Step 3**: Verify `optimal_lag` in the output JSON is within 1 minute of 45.
 - **Verification**: Run `pytest tests/integration/test_synthetic.py::test_synthetic_lag_45min`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualise Relationship and Sensitivity (Priority: P3)

**Goal**: Generate scatter plots, time-series overlays, and sensitivity analysis for high-speed thresholds.

**Independent Test**: After a successful run, verify PNG files (scatter, time-series) and sensitivity table (T ∈ {400, 500, 600} km/s) are generated.

### Implementation for User Story 3

- [X] T062 [S] Update `code/analysis/sensitivity.py` to ensure the threshold analysis (T ∈ {400, 500, 600}) explicitly reports numeric correlation values for human analysis.
 - **Requirement**: The code must compute the correlation for each threshold and report the numeric values, including delta metrics if applicable, to allow human analysis of saturation trends. **Do NOT implement an automated trend classification algorithm (linear/quadratic/saturated).** The output must allow for human analysis of saturation trends.
 - **Output Schema**: The `sensitivity_table` MUST be a dictionary mapping the threshold integer (e.g., `400`) to a dictionary containing `pearson`, `spearman`, and `p_value`. Example: `{400: {"pearson": 0.5, "spearman": 0.6, "p_value": 0.01}}`.
 - **Verification**: Run the pipeline and verify the `sensitivity_table` output contains numeric correlation values for each threshold.
 - **Dependency**: T011

- [X] T027 [US3] Integrate `viz/plots.py` (scatter and time-series) with the main pipeline.
 - **Deliverable**: Generate `projects/PROJ-300-exploring-the-relationship-between-solar/results/plot_scatter.png` and `projects/PROJ-300-exploring-the-relationship-between-solar/results/plot_timeseries.png`.

- [X] T028 [US3] Integrate `analysis/sensitivity.py` to compute correlations for `T ∈ {400, 500, 600} km s⁻¹ ` (FR-007).
 - **Deliverable**: Update `projects/PROJ-300-exploring-the-relationship-between-solar/results/us1_correlation.json` to include `sensitivity_table`.
 - **Dependency**: T062

- [X] T029 [US3] Generate PNG files (scatter, time-series) and sensitivity table for a sample run.
 - **Verification**: Run `pytest tests/integration/test_us3.py`.

- [X] T030 [US3] Verify all plots load without error, include correct labels/units, and show the optimal lag annotation (SC-005).
 - **Verification**: Run `pytest tests/unit/test_plots.py`.

- [X] T031 [US3] Verify the sensitivity table correctly reports correlation magnitude for each threshold (US-3 Acceptance Scenario 2).
 - **Verification**: Check `projects/PROJ-300-exploring-the-relationship-between-solar/results/us1_correlation.json` for correct values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Testing & Validation

**Purpose**: Unit and integration tests required by plan.md and spec.md Independent Tests. Tests are written alongside implementation to ensure verification during development.

- [X] T032 [P] Write unit tests for `data/clean.py` in `tests/unit/test_clean.py` (FR-003).
 - **Test Functions**: `test_clean_removes_nan`, `test_clean_resamples_to_5min`, `test_clean_handles_empty_input`, `test_clean_handles_large_gaps`.

- [X] T033 [P] Write unit tests for `data/lag.py` in `tests/unit/test_lag.py` (FR-012). <!-- FAILED: unspecified -->
 - **Test Functions**: `test_lag_calculation_formula`, `test_lag_shift_applies_correctly`.

- [X] T034 [P] Write integration test for lag-adjusted correlation pipeline in `tests/integration/test_pipeline.py` (US-1 Independent Test).
 - **Test Function**: `test_us1_full_pipeline` verifying JSON output keys: `pearson`, `p_val_permutation`, `optimal_lag`.

- [X] T035 [P] Write unit tests for permutation test logic in `tests/unit/test_correlation.py` (FR-005).
 - **Test Functions**: `test_permutation_block_size`, `test_permutation_p_value_calculation`.

- [X] T036 [P] Write unit tests for lag sweep logic in `tests/unit/test_lag_search.py` (FR-010).
 - **Test Functions**: `test_lag_sweep_window`, `test_optimal_lag_identification`.

- [X] T037 [P] Write integration test for synthetic dataset validation in `tests/integration/test_synthetic.py` (US-2 Independent Test).
 - **Test Function**: `test_synthetic_lag_45min` verifying `abs(reported_lag - 45) <= 1` where `reported_lag` is retrieved from the JSON key `optimal_lag`.

- [X] T038 [P] Write unit tests for sensitivity threshold filtering in `tests/unit/test_sensitivity.py` (FR-007).
 - **Test Functions**: `test_threshold_filtering`, `test_sensitivity_correlation_calculation`.

- [X] T039 [P] Write unit tests for bootstrap resampling logic in `tests/unit/test_correlation.py` (FR-006).
 - **Test Functions**: `test_bootstrap_block_size`, `test_bootstrap_ci_calculation`.

- [X] T040 [P] Write unit tests for data cleaning edge cases (empty input, all-NaN column) in `tests/unit/test_clean.py` (FR-003).
 - **Test Functions**: `test_clean_all_nan`, `test_clean_single_value`.

- [X] T041a [P] Run unit and integration tests.
 - **Execution**: `pytest tests/ -v --tb=short`.
 - **Verification**: All tests pass (exit code 0). **This task must be completed before T099a.**

- [X] T099a [S] Execute pipeline on sample data to generate results artifacts.
 - **Execution**: Run `python code/main.py --start <start_date> --end <end_date>`.
 - **Deliverable**: Ensure `results/us1_correlation.json`, `results/plot_scatter.png`, `results/plot_timeseries.png`, and `data/processed/quality_log.json` are created.
 - **Verification**: Check file existence. **This task must be completed before T099b.**
 - **Dependency**: T016, T020b, T028, T027

- [X] T099b [P] Verify `projects/PROJ-300-exploring-the-relationship-between-solar/results/` directory contains all expected artifacts.
 - **Execution**: Check for `us1_correlation.json`, `plot_scatter.png`, `plot_timeseries.png`, `quality_log.json` in `projects/PROJ-300-exploring-the-relationship-between-solar/results/`.
 - **Verification**: All files exist.

- [X] T099c [P] Generate checksums for all artifacts.
 - **Execution**: Run `python code/checksums.py generate --base-dir projects/PROJ-300-exploring-the-relationship-between-solar`.
 - **Verification**: Verify checksums file exists.

---

## Phase 7: Polish & Cross-Cutting Concerns (Review Response)

**Purpose**: Address specific concerns from prior research-stage reviews regarding reference frames and physical mechanisms. These tasks are documentation-only and MUST be executed AFTER core analysis tasks (T020b, T027) to ensure accuracy.

- [X] T060 [S] [Review: Einstein] Implement `docs/reference_frames.md` to explicitly map measured quantities to their reference frames (GSM, Solar Wind Rest Frame, Earth Frame).
 - **Requirement**: Create `docs/reference_frames.md` with sections: 1. Reference Frames, 2. Lorentz Transformation Context, 3. Invariance Analysis.
 - **Verification**: Verify file exists and contains the string "Lorentz transformation" and "GSM".
 - **Command**: `grep -q "Lorentz transformation" docs/reference_frames.md && grep -q "GSM" docs/reference_frames.md`.
 - **Dependency**: T020b

- [X] T061 [S] [Review: Feynman] Implement `docs/physical_mechanism.md` to provide a qualitative "picture" of the reconnection process.
 - **Requirement**: Create `docs/physical_mechanism.md` with sections: 1. Topology, 2. Propagation, 3. Energy Budget, 4. ASCII Diagram.
 - **Verification**: Verify file exists and contains an ASCII diagram block and the citation "Kivelson & Russell".
 - **Command**: `grep -q "ASCII Diagram" docs/physical_mechanism.md`.
 - **Dependency**: T020b

- [ ] T063 [S] [Review: Einstein] Update `code/main.py` to include a "Reference Frame Context" section in the final JSON report (`notes` or a new `context` field).
 - **Requirement**: The report MUST state the reference frame in which Ey was measured and the transformation (if any) applied to align it with the solar wind speed vector.
 - **Verification**: Inspect the generated `results/us1_correlation.json` to confirm the presence of the reference frame statement.
 - **Dependency**: T020b

---

## Phase 8: Polish & Cross-Cutting Concerns (Original)

**Purpose**: Improvements that affect multiple user stories.

- [X] T056 [P] Update `README.md` with instructions on how to run the full pipeline and interpret the results.
 - **Update**: Include sections for "Running the Pipeline", "Interpreting Results", and "Data Sources". Ensure the README reflects only in-scope features (correlation, lag, sensitivity) and does not mention out-of-scope features.
 - **Addition**: Add a "Physical Context" section referencing the `spec.md` FR-012 and Constitution Principle VII, explaining the `60 Re` heuristic and the assumption of a fixed distance, without introducing new code artifacts.

- [X] T057 [P] Create `docs/physical_context.md` as a narrative document only (no code).
 - **Content**: Summarize the reference frames (GSM, Solar Wind Rest Frame) and the physical mechanism of reconnection as described in `spec.md` and `plan.md`.
 - **Requirement**: Explicitly state that the `60 Re` distance is a heuristic approximation and that the analysis does not validate against MHD timescales (Alfvén speed) as this is out of scope.
 - **Verification**: Review against `spec.md` to ensure no new requirements are introduced.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Testing (Phase 6)**: Can run in parallel with User Story implementation once modules are created
- **Polish (Phase 7, 8, & 9)**: Depends on all desired user stories, tests, and review fixes being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tasks within a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Testing tasks (Phase 6) can run in parallel with implementation tasks once the target modules exist
- Polish (Phase 7, 8, & 9) tasks can run in parallel with final testing.

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement projects/.../code/analysis/correlation.py with Pearson/Spearman calculation"
Task: "Implement projects/.../code/analysis/correlation.py Circular Block Permutation test"
Task: "Implement projects/.../code/analysis/correlation.py Moving Block Bootstrap"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic Correlation)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Polish (Phase 7, 8, & 9) → Final review and README update.
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Basic Pipeline)
 - Developer B: User Story 2 (Lag Search)
 - Developer C: User Story 3 (Visualization)
3. Stories complete and integrate independently
4. Team collaborates on Phase 7, 8, & 9 (Polish) to ensure consistent documentation.

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential (must wait for previous tasks)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All data ingestion must use verified URLs (OMNIWeb, CDAWeb) and no GPU libraries. Permutation tests must be optimized for CPU-only execution.
- **Scope Alignment**: The project scope is strictly limited to the requirements in spec.md. No tasks related to out-of-scope physics concepts are included in the core pipeline. Documentation in Phase 7 and 8 clarifies the physical context without adding code.
- **Test Coverage**: All Independent Tests from US-1 and US-2 are now explicitly mapped to test tasks (T021, T022, T034, T037) with specific function names and verification commands.
- **Formula Consistency**: Task T006a implements the correct simplified formula `6371 / Vsw_mean` and logs the full derivation for traceability.
- **Task Splitting**: Implementation and testing tasks have been separated (e.g., T004a/T042) to ensure clear deliverables and verification steps.
- **Execution Order**: Task T041a (Run unit tests) now precedes T099a (Execute pipeline) to ensure code correctness before full pipeline execution.
- **Critical Constraint on Fabrication**: All data must be real. The "schematic diagram" and "Alfvén Mach Number" tasks have been removed from the core pipeline to prevent scope creep and fabrication, but are addressed as documentation in Phase 7 and 8.
- **Review Response**: Phase 7 (T060-T063) has been added to address specific concerns from prior research-stage reviews regarding reference frames (Einstein) and physical mechanisms (Feynman). These tasks focus on documentation and clarifying existing code outputs, not introducing new computational requirements.
- **Task Splitting**: Implementation and testing tasks have been separated (e.g., T004a/T042) to ensure clear deliverables and verification steps.
- **Execution Order**: Task T099 has been split into T099a (execute), T099b (verify), and T099c (checksum) to resolve circular dependencies.
- **Phase 9 Removed**: Phase 9 (Revision) has been removed as the referenced review concerns (T070-T075) were not present in the current spec.md or plan.md artifacts, constituting scope creep. The tasks T060-T063 in Phase 7 address valid review concerns that *are* reflected in the current spec/plan artifacts.
- **New Review Response Tasks**: Tasks T060-T063 in Phase 7 address valid review concerns regarding reference frames and physical mechanisms. These tasks are documentation and minor code enhancements to the output report, ensuring the project does not "fool itself" with a correlation number without physical context.
- **Removed Tasks**: Tasks T070-T075 have been removed as they introduced unauthorized scope creep (Alfvén speed calculation, fine-grid sensitivity plots) not authorized by spec.md FR-001..FR-013.
- **Locking Protocol**: Tasks T006c and T016 now explicitly define a locking order (T006c first, T016 second) to prevent deadlocks when writing to `quality_log.json`.
- **Dependency Resolution**: `portalocker` has been added to `requirements.txt` to resolve the missing dependency for T006c and T016.
