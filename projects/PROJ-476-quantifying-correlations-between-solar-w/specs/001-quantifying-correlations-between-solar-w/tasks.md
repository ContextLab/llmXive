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

- [X] T004 [P] Create `code/config.py` as a Python constants module. **MUST define** the following constants with exact values: `TRAIN_START=1998`, `TRAIN_END=2017`, `TEST_START=2018`, `TEST_END=2020`, `{{claim:c_f896f13e}} `, `NOAA_VARS=['Kp', 'Dst'] [UNRESOLVED-CLAIM: c_0c965cac — status=not_enough_info] `. **MUST explicitly document** that `TRAIN_START` to `TEST_END` covers the full multi-decade span referenced in SC-001 for the "full 20-year lagged correlation analysis" performance benchmark, while `TRAIN_START` to `TRAIN_END` is the subset used for model fitting. All downstream tasks MUST import these constants from `code.config`.
- [X] T005 [P] Create `code/data/fetch.py` as a **stub file** containing empty function signatures: `fetch_ace(start_date, end_date) -> str` returning `data/raw/ace_raw.csv` and `fetch_noaa(start_date, end_date) -> str` returning `data/raw/noaa_raw.csv`. Do not implement logic yet. **Note**: This is a scaffolding step; logic must be implemented in T011.
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
- [X] T007 [P] Create base data validation logic in `code/data/validate.py` as a **stub file**. **MUST import** `ACE_VARS` and `NOAA_VARS` from `code.config`. **MUST define** a function `validate_columns(df: pd.DataFrame, required_cols: list) -> None` that raises `ValueError` with the exact message "Missing required variable: <name>" if any column in `required_cols` is missing. Do not implement the abort logic yet; this task creates the file structure and imports. **Note**: This is a scaffolding step; logic must be implemented in T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Contract Definitions (Schema Generation)

**Purpose**: Create the schema files required for validation tasks (T010, T019, T028, T025a).

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

**Checkpoint**: Schemas defined - validation tasks can now be executed.

---

## Phase 3: User Story 1 - Data Acquisition & Synchronisation (Priority: P1) 🎯 MVP

**Goal**: Download ACE/NOAA data, align to 1-hour UTC grid, handle missing values via linear interpolation.

**Independent Test**: Run the pipeline for a month-long window. Verify output CSV contains exactly five columns (timestamp, proton_density, temperature, helium_abundance, Kp, Dst) with no NaNs after imputation.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST (Test-First approach). They are written before implementation but **executed** only after T013/T013c is complete.

- [X] T008 [P] [US1] Unit test for variable validation in `code/tests/test_validate.py`. **Function name**: `test_fetch_aborts_on_missing_he2plus`. **MUST use** `pytest.raises(ValueError, match="Missing required variable: He2+_ratio")` to verify abort on missing `He2+_ratio` in source file.
- [X] T009 [P] [US1] Unit test for interpolation logic in `code/tests/test_align.py`. **Function name**: `test_align_interpolates_small_gaps_warns_large`. Verify gap ≤ 6h fills, > 6h warns.
- [ ] T010 [US1] **Write** Integration test for full month download in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_monthly_sync`. **MUST use a pre-seeded fixture file** `data/fixtures/monthly_sample.csv` (created by a separate setup step or assumed present) representing a valid month of ACE/NOAA data. **MUST verify** `data/processed/synced.csv` structure and schema conformance against `contracts/dataset.schema.yaml`. **Note**: This task is for WRITING the test code. The test is **executed** only after T013c (align.py write) is complete. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement logic in `code/data/fetch.py` (populating the existing stub) to download ACE Level 2 (SWEPAM/SWICS) and NOAA Kp/Dst. **MUST implement** `fetch_ace` and `fetch_noaa` with `start_date`, `end_date` parameters. **MUST use verified URLs** defined in `code/config.py` (see T043a).
- [X] T012 [US1] Implement `code/data/validate.py` to abort with clear error if `N_p`, `T_p`, or `He2+_ratio` are missing (FR-006). **MUST explicitly check the actual headers of the downloaded file against the hardcoded list and abort if they don't match**. **MUST verify source file column names against ACE Level 2 names ('N_p', 'T_p', 'He2+_ratio') BEFORE mapping**. **MUST log the specific missing variable name** (e.g., "Missing variable: He2+_ratio") in the abort message to satisfy SC-002. **MUST raise** `ValueError` with the exact message format defined in T007.
- [X] T013a [US1] Implement `code/data/align.py` function `resample_to_hourly(df: pd.DataFrame, target_freq: str='1h') -> pd.DataFrame`. **MUST** read from `data/raw/` and set timestamp as index. **MUST** resample to 1-hour UTC grid using `df.resample('1h').mean()`.
- [X] T013b [US1] Implement `code/data/align.py` function `handle_gaps(df: pd.DataFrame, max_gap_hours: int=6) -> pd.DataFrame`. **MUST** perform linear interpolation for gaps ≤ 6h. **MUST** log interpolated intervals. **MUST** raise a warning or exclude gaps > 6h from correlation calculations. **MUST** ensure the output has **no NaNs** after interpolation (assertion). **MUST explicitly rename columns** from ACE raw names (`N_p` → `proton_density`, `T_p` → `temperature`, `He2+_ratio` → `helium_abundance`) and NOAA names (`Kp`, `Dst`) to match the schema in `contracts/dataset.schema.yaml`.
- [ ] T013c [US1] Implement `code/data/align.py` function `write_synced_csv(df: pd.DataFrame, output_path: str) -> None`. **MUST** read the DataFrame from the previous step (after T013b). **MUST explicitly rename columns** to match the output schema: `N_p` → `proton_density`, `T_p` → `temperature`, `He2+_ratio` → `helium_abundance`. **MUST assert** that the DataFrame keys are exactly `['timestamp', 'proton_density', 'temperature', 'helium_abundance', 'Kp', 'Dst']` before writing. **MUST** write to `data/processed/synced.csv`. **MUST** verify the output contains **no NaNs** before writing. **MUST** ensure the file contains exactly the required columns: `timestamp, proton_density, temperature, helium_abundance, Kp, Dst`.
- [X] T016 [US1] Create `code/main.py` entry point to orchestrate US1 pipeline (download → validate → sync).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lagged Correlation & Significance Testing (Priority: P2)

**Goal**: Compute Pearson/Spearman correlations at lags 0,1,2,3,6h on the FULL dataset, adjust p-values for autocorrelation (Neff), and apply Bonferroni correction.

**Independent Test**: Execute correlation module on full dataset. Verify results table has a complete set of rows IF all variables are present, or N rows (N<30) if variables are missing. Each row must contain Pearson r, Spearman ρ, raw p (Neff adjusted), and Bonferroni p.

### Tests for User Story 2 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T017 [P] [US2] Unit test for Neff calculation in `code/tests/test_correlation.py`. **Function name**: `test_correlation_neff_formula`. **MUST use formula** $N_{eff} = N \frac{1-\rho_1}{1+\rho_1}$ with synthetic data (e.g., N=100, rho=0.9) and verify expected result. **MUST include code snippet for synthetic data generation**: `np.random.RandomState(42).randn(100)`. **MUST verify that the detrending step (`scipy.signal.detrend`) is applied before calculating rho_1**.
- [X] T018 [P] [US2] Unit test for Bonferroni correction in `code/tests/test_correlation.py`. **Function name**: `test_correlation_bonferroni_divisor`. Verify α_adj = 0.05/30 (fixed global divisor).
- [X] T019 [US2] Integration test for full correlation run in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_correlation_full_run`. **MUST use a pre-seeded fixture file** `data/fixtures/full_correlation_sample.csv` representing a valid full dataset with all variables present. **MUST verify** `artifacts/correlations.csv` has 30 rows if all vars present, or fewer if missing. **MUST verify** schema conformance against `contracts/analysis_schema.yaml`.

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/analysis/correlation.py` function `iterate_lagged_pairs(df: pd.DataFrame, lags: list) -> list`. **MUST** generate all pairs of (composition_param, geomagnetic_index, lag).
- [X] T020b [US2] Implement `code/analysis/correlation.py` function `compute_pearson(df, x_col, y_col, lag) -> float`. **MUST** apply lag shift to y_col before computing Pearson r.
- [X] T020c [US2] Implement `code/analysis/correlation.py` function `compute_spearman(df, x_col, y_col, lag) -> float`. **MUST** apply lag shift to y_col before computing Spearman ρ.
- [X] T020d [US2] Implement `code/analysis/correlation.py` function `write_correlation_results(results: list, output_path: str) -> None`. **MUST** write to `artifacts/correlations.csv`. **MUST** enforce output structure: **30 rows** (if data present) with columns `composition_parameter, geomagnetic_index, lag_hours, pearson_r, spearman_rho, p_raw, p_bonferroni, significance_flag`.
- [X] T021 [US2] Implement `code/analysis/neff.py` to calculate effective sample size ($N_{eff}$) using lag-1 autocorrelation on the FULL continuous series (1998-2020). **MUST use the method of Pyper & Peterman (late 1990s)**: **Call `scipy.signal.detrend`** on the time series to remove linear trend before calculating lag-1 autocorrelation ($\rho_1$) of the residuals, then apply formula $N_{eff} = N \frac{1-\rho_1}{1+\rho_1}$. Do NOT use `scipy.stats.autocorr` directly on raw data. **MUST implement the detrending logic inline** to ensure the producer before consumer principle is met.
- [X] T022 [US2] Implement raw p-value calculation using $N_{eff}$ in `code/analysis/correlation.py`.
- [X] T023 [US2] Implement Bonferroni correction logic in `code/analysis/correlation.py` (FR-004). **MUST derive the divisor 30 dynamically** from configuration (params × 2 indices × 5 lags) to calculate $\alpha_{adj} = 0.05 / 30$, regardless of actual data availability, to control family-wise error rate.
- [X] T024 [US2] Add flagging logic for significant pairs (Bonferroni p < 0.05) in `code/analysis/correlation.py`.
- [X] T025 [US2] Integrate US2 logic into `code/main.py` to run after US1 completes. **MUST** calculate global Neff and Bonferroni threshold values.
- [X] T025a [US2] **Write** `artifacts/thresholds/global_threshold.json` containing global Neff values and $\alpha_{adj}$. **MUST** validate against `contracts/threshold.schema.yaml` before writing using `jsonschema`. **This task must complete before T032**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualisation, Reporting & Validation (Priority: P3)

**Goal**: Generate visualizations (time-series, heatmaps) and a validation report on the held-out 2018-2020 period.

**Independent Test**: Run validation on 2018-2020. Verify PNGs ≤ 5MB and Markdown report correctly flags pairs with |r| > 0.5 and significant Bonferroni p (computed globally for main, applied to test set).

### Tests for User Story 3 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T026 [P] [US3] Unit test for file size check in `code/tests/test_viz.py`. **Function name**: `test_viz_png_size_limit`. **MUST use** `assert os.path.getsize(filepath) <= 5*1024*1024` to verify PNG generation ≤ 5MB.
- [X] T027 [P] [US3] Unit test for report logic in `code/tests/test_report.py`. **Function name**: `test_report_threshold_detection`. Verify |r| > 0.5 threshold detection.
- [X] T028 [US3] Integration test for full validation run in `code/tests/test_pipeline.py`. **Function name**: `test_pipeline_validation_full_run`. Verify artifacts exist and schema conformance against `contracts/visual_artifact.schema.yaml` (if applicable) or file existence checks.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/viz/plots.py` to generate time-series overlay plots per lag.
- [X] T030 [P] [US3] Implement `code/viz/plots.py` to generate correlation heatmap (parameters × lags).
- [X] T031 [US3] Implement `code/viz/report.py` to split data into Train (1998-2017) and Test (2018-2020) using constants `TRAIN_START`, `TRAIN_END`, `TEST_START`, `TEST_END` from `code/config.py`.
- [X] T032 [US3] Implement `code/viz/report.py` to **load the GLOBAL significance threshold** (from `artifacts/thresholds/global_threshold.json` produced in T025a) and **evaluate** the pre-computed global correlations against the held-out 2018-2020 period data. **DO NOT** re-compute Neff or Bonferroni on the test set. **MUST apply** the global Neff and Bonferroni p-values to the test set correlations to verify stability. **MUST report** whether the composition-index pair exceeds |r| > 0.5 **AND** has the global Bonferroni-corrected p < 0.05 in the test set.
- [X] T033 [US3] Generate Markdown report stating if Helium-Dst exceeds |r| > 0.5 (US-3 Acceptance Scenario 1). **MUST output** to `artifacts/reports/validation_report.md`. **MUST explicitly state** "Helium abundance vs. Dst at a temporal lag: r = X (significant)" if threshold met, OR "No composition parameter achieved the pre-registered effect-size threshold" if not. **MUST include** the Bonferroni-corrected p-value.
- [X] T034 [US3] Integrate US3 logic into `code/main.py` to run after US2 completes. <!-- ATOMIZE: requested -->

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039a [P] Documentation updates: Create `README.md` with setup instructions, usage examples, and data source URLs.
- [X] T039b [P] Documentation updates: Create `docs/usage.md` with detailed pipeline explanation and statistical method references (Pyper & Peterman).
- [X] T040a Code cleanup: Remove unused imports from all files in `code/`.
- [X] T040b Code cleanup: Fix linting errors in `code/` to pass ruff.
- [X] T041a [P] Additional unit tests for edge cases in `code/tests/`. **Function name**: `test_align_handles_empty_dataframe`.
- [X] T041b [P] Additional unit tests for edge cases in `code/tests/`. **Function name**: `test_align_warns_large_gaps`.
- [X] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility.

---

## Phase N+1: Data Source Verification & Robustness (Revision)

**Purpose**: Resolve Constitution Check failure regarding missing NOAA URL and ensure robust data loading without synthetic fallbacks.

- [X] T043a [P] [US1] **Define Verified Data Source Configuration** in `code/config.py`. **MUST** add a constant `NOAA_URL` with the value ` (or the specific verified FTP path if available and confirmed). **MUST** add a constant `ACE_URL` with the value `ftp://spdf.gsfc.nasa.gov/pub/data/ace/`. **MUST** document that these URLs are the single source of truth for data acquisition.
- [X] T043b [P] [US1] **Implement Data Fetch Verification** in `code/data/fetch.py`. **MUST** implement a `fetch_noaa` function that explicitly downloads the hourly Kp/Dst indices from the `NOAA_URL` defined in `config.py`. **MUST** ensure the function raises a `ConnectionError` or `FileNotFoundError` if the real fetch fails, **NEVER** falling back to synthetic/mock data. **MUST** log the exact URL being used.
- [X] T045 [US1] **Update Integration Test** `code/tests/test_pipeline.py` (T010) to **assert** that the data source is the verified NOAA/ACE URL and not a synthetic fallback. **MUST** verify that the test fails if the real URL is unreachable (simulating network failure) rather than passing with mock data.

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
- **Data Source Verification (Phase N+1)**: Must complete before any data-dependent tests (T010, T019, T028) can pass reliably.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST wait for T013c (US1 completion)** to ensure `synced.csv` exists.
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
3. Complete Phase 2.5: Contract Definitions
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
- **Dependency Note**: T011 depends on T005 (stub creation). T012 depends on T011 (fetch). T020 depends on T013c (US1 completion). T029 depends on T025a (US2 completion). T032 depends on T025a (global thresholds). T043a/T043b implement the verified data source configuration.
- **Revision Note**: Tasks T043a-T043b address the "Verified Accuracy" failure in the Constitution Check by explicitly defining the URL in config and enforcing fetch verification, satisfying the requirement for real data only.
- **Schema Note**: T013c now explicitly enforces the column renaming from raw ACE names (N_p, T_p, He2+_ratio) to the output schema names (proton_density, temperature, helium_abundance) to prevent mismatch.
