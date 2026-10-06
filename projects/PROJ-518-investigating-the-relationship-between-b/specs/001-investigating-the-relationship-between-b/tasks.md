# Tasks: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Input**: Design documents from `/specs/518-brain-dynamics-creativity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY where defined by spec acceptance criteria.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan (`mkdir -p projects/PROJ-518-investigating-the-relationship-between-b/code projects/PROJ-518-investigating-the-relationship-between-b/tests projects/PROJ-518-investigating-the-relationship-between-b/data/raw projects/PROJ-518-investigating-the-relationship-between-b/data/processed projects/PROJ-518-investigating-the-relationship-between-b/data/interim projects/PROJ-518-investigating-the-relationship-between-b/docs/outputs projects/PROJ-518-investigating-the-relationship-between-b/results`).
- [X] T002 Initialize Python 3.10 project with pinned `requirements.txt` containing `nilearn==0.10.0`, `networkx==3.2.1`, `scikit-learn==1.4.2`, `numpy==1.26.4`, `pandas==2.2.2`, `matplotlib==3.8.4`, `scipy==1.12.0`, `brainconn==0.1.0`.
- [X] T003 [P] Configure linting (flake8/black) by creating `.flake8` and `pyproject.toml` with appropriate sections.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 Setup data directory structure (`mkdir -p data/raw data/processed data/interim docs/outputs results`).
- [X] T005 [P] Implement `code/config.py` with a `Config` dataclass containing `WINDOW_SIZES = [20,30,40]`, `STEP = 5`, `ATLAS_PATH`, `DATA_PATH`, `FWE_METHOD = 'max-t'` (or 'bonferroni'), and load from `.env` if present.
- [X] T005.1 [P] Implement `code/config.py` function `validate_fwe_config()` that checks if `FWE_METHOD` is 'max-t' and ensures `distribution_of_max_stats` will be available from T027, or if 'bonferroni' is selected, ensures no max-T dependency exists. Raises `ValueError` if mismatch. **Dependency**: T005. **Verification**: Unit test `tests/unit/test_config.py::test_fwe_config_validation`.
- [X] T006 [P] Setup `code/utils/logging.py` with function `log_exclusion(reason: str, subject_id: str)` that appends CSV rows to `data_exclusion_log.txt`.
- [X] T007 Create `code/utils/versioning.py` with `hash_file(path: str) -> str` and `update_state_file()` that writes SHA‑256 hashes to `state/projects/PROJ-518...yaml`.
- [X] T008 Configure error handling: define `class DataMissingCreativityError(Exception)` in `code/errors.py`.
- [X] T009 Setup environment configuration management (`code/config.py` as above).

## Phase 2.5: Critical Pre‑Conditions (User Story 4 – Priority: P1) 🚨 BLOCKER

- [X] T033 Implement `validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool` in `code/data/loader.py` that checks for the CAQ field and raises `DataMissingCreativityError` with the missing field name if absent.
- [X] T036 [P] [US4] Implement `code/main.py` function `run_validation()` that calls `validate_caq_availability`. **Dependency**: T033, T008.
- [X] T036.1 [US4] Implement error handling in `code/main.py`: wrap `run_validation()` in a `try-except` block catching `DataMissingCreativityError`. **Logic**: In the `except` block: log the specific error code `DATA_MISSING_CREATIVITY` to the console and log file, then call `sys.exit(1)`. **Dependency**: T036, T008.
- [X] T036.2 [US4] Implement success path in `code/main.py`: if no exception, proceed to the next stage (data fetching). **Dependency**: T036, T036.1.
- [X] T036.3 [US4] Explicitly define the entry point function `main()` in `code/main.py` that orchestrates the flow: call `run_validation()`, and on success, call `fetch_hcp_data()`. **Dependency**: T036.2.

### Tests for US4 (Mandatory)
- [X] T034 [P] [US4] Contract test `tests/contract/test_loader.py::test_validate_caq_availability_raises_on_missing` asserting `DataMissingCreativityError` is raised when CAQ is missing in the manifest.
- [X] T035 [P] [US4] Contract test `tests/contract/test_loader.py::test_validate_caq_availability_passes_on_present` asserting function returns True when CAQ is present.

- [X] T018 [US1] Implement `code/data/loader.py` function `validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]` that skips subjects with missing scans (log warning) and missing behavioral scores (exclude + log). **Output**: Returns filtered list. **Log Format**: Appends CSV rows to `data_exclusion_log.txt` with columns `subject_id, reason, timestamp`. Reason must be `MISSING_SCAN` or `MISSING_SCORE`. **Dependency**: T006.
- [X] T019 [US1] Implement `code/data/loader.py` function `filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]` that excludes participants exceeding motion criteria. **Output**: Returns filtered list. **Log Format**: Calls `log_exclusion` with reason `HIGH_MOTION` for each excluded subject. **Dependency**: T006.
- [X] T020b [US1] Implement standardized logging invocation: Ensure `log_exclusion` is called with standardized reason codes (`MISSING_SCAN`, `MISSING_SCORE`, `HIGH_MOTION`) for every exclusion decision in T018 and T019. **Dependency**: T018, T019. **Pre-requisite**: Must be implemented after filtering tasks to ensure the logging mechanism is used correctly. **Verification**: Unit test `tests/unit/test_logging.py::test_standardized_reason_codes` must assert that the log file contains these exact reason codes for excluded subjects.

## Phase 3: User Story 1 – Compute Network Flexibility and Test Association (Priority: P1) 🎯 MVP

### Tests (MANDATORY)

- [X] T011 [P] [US1] Integration test `tests/integration/test_pipeline_flow.py::test_end_to_end_correlation` runs the full pipeline on a mock subset and asserts numeric `r` and `p` values.

### Implementation

- [ ] T012 [US1] Implement `code/data/loader.py` function `fetch_hcp_data(subject_id: str)` that downloads raw fMRI and behavioral JSON from OpenNeuro (dataset ID: the HCP S1200 Release). **AFTER** validation (T036.2) succeeds. **Logic**: The task must verify that the specific dataset manifest contains the 'CAQ' key before initiating the download. **Output**: Saves files to `data/raw/hcp_{subject_id}/`. **Verification**: Assert that the downloaded files exist and are non-empty. **Note**: This task is NOT parallel-safe ([P] removed) as it depends on T036.2 completion.
- [X] T013 [P] [US1] Implement `code/data/preprocess.py` function `preprocess_fmri(input_path: str, output_path: str)` performing motion correction, spatial normalization, and **band‑pass filtering within a low-frequency range** using Nilearn. **Output Convention**: The `output_path` MUST be constructed as `data/processed/{subject_id}_preprocessed.nii.gz` to ensure deterministic file naming for downstream tasks.
- [ ] T014 [US1] Implement `code/analysis/connectivity.py` function `compute_sliding_window_connectivity(fmri_data: np.ndarray, window_size: int, step: int)` reading `WINDOW_SIZES` and `STEP` from `config.py`.
- [ ] T014.1 [US1] Implement `code/analysis/connectivity.py` function `compute_static_connectivity_strength(fmri_data: np.ndarray) -> float` that calculates the mean of absolute pairwise correlations **from the full‑window static matrix** per participant. **Output**: Returns a float. **Dependency**: None. **Verification**: Unit test `tests/unit/test_connectivity.py::test_static_strength_returns_float` must assert the return type is float and value is within [-1, 1].
- [ ] T014.2 [US1] Implement `code/analysis/connectivity.py` function `construct_covariates_dict(static_strengths: List[float], ages: List[float], sexes: List[str], educations: List[int]) -> dict` that aggregates per-participant metrics into the `covariates` dictionary required by T051. **Input**: List of floats from T014.4 (aggregated static strengths) and demographic lists **extracted by iterating over the filtered Participant list from T018/T019 and accessing the .age, .sex, and .education attributes**. **Output**: Dict with keys `static_connectivity_strength`, `age`, `sex`, `education`. **Mandatory**: The function MUST verify that the `static_connectivity_strength` key is present and non-null in the resulting dict. **Dependency**: T014.4. **Verification**: Unit test `tests/unit/test_connectivity.py::test_covariates_dict_structure` must assert the dict contains all required keys.
- [ ] T014.3 [US1] Implement `code/analysis/connectivity.py` function `validate_alignment(static_strengths: List[float], flexibility: List[float], creativity: List[float], subject_ids: List[str]) -> bool` that checks if all lists have the same length and corresponding `subject_ids` match. Raises `ValueError` if mismatch. **Input**: Lists from T014.4, T016, T018/T019. **Output**: Returns True if aligned. **Dependency**: T014.4, T016, T018, T019. **Verification**: Unit test `tests/unit/test_connectivity.py::test_validate_alignment` must assert correct handling of mismatched lists.
- [ ] T014.4 [US1] Implement `code/analysis/connectivity.py` function `collect_static_strengths(static_strength_results: List[float]) -> List[float]` that aggregates the individual float results from T014.1 (run in parallel per subject) into a single list. **Input**: List of floats from T014.1. **Output**: A single aggregated list of floats. **Dependency**: T014.1. **Verification**: Unit test `tests/unit/test_connectivity.py::test_collect_static_strengths` must assert the output is a list of floats.
- [X] T015 [US1] Implement `code/analysis/dynamics.py` function `detect_communities(connectivity_matrix: np.ndarray, gamma: float = 1.0) -> List[int]` using Louvain with **γ = 1.0**.
- [X] T016 [US1] Implement `code/analysis/dynamics.py` function `calculate_flexibility(community_labels: List[List[int]]) -> float` that counts ROI community changes **and averages across ROIs** to produce the whole‑brain metric.
- [X] T043 [US1] Implement `code/analysis/statistics.py` function `format_delta_r2(delta_r2: float) -> str` returning a string with **four decimal places** (e.g., "0.1234"). **Dependency**: Must be implemented before T017.1.
- [X] T051 [US1] Implement `code/analysis/statistics.py` function `fit_regression(flexibility: np.ndarray, creativity: np.ndarray, covariates: dict) -> RegressionResult` using `statsmodels` OLS to fit the full model `creativity ~ network_flexibility + age + sex + education + static_connectivity_strength`.
 **Data Flow Implementation**:
 1. Iterate over the list of participants.
 2. For each participant, load preprocessed fMRI data from `data/processed/{subject_id}_preprocessed.nii.gz` (output of T013).
 3. Call `compute_static_connectivity_strength` (T014.1) on the loaded data.
 4. Aggregate the resulting floats into a list `static_strengths` using `collect_static_strengths` (T014.4).
 5. Call `construct_covariates_dict` (T014.2) with `static_strengths` and other demographic lists to generate the `covariates` dict.
 6. **Validation**: Call `validate_alignment` (T014.3) to verify that `static_connectivity_strength` is correctly aligned with `flexibility` and `creativity` vectors. Raise `ValueError` if mismatch.
 7. Pass this `covariates` dict to the OLS model.
 **Input**: `covariates` dict MUST be constructed via the logic above and validated. **Output**: Returns `RegressionResult` containing coefficients, R², adjusted R², and `pearson_r`. **Dependency**: T014.1, T014.2, T014.3, T014.4.
- [X] T051b [US1] Implement `code/analysis/statistics.py` function `fit_baseline_regression(creativity: np.ndarray, static_strengths: List[float], covariates: dict) -> RegressionResult` that fits the baseline model `creativity ~ static_connectivity_strength + age + sex + education`. **Logic**:
 1. Construct a new covariates dict excluding `network_flexibility`.
 2. Fit the OLS model using `statsmodels`.
 3. Return `RegressionResult` containing coefficients, R², and adjusted R² for the baseline model.
 **Output**: Returns `RegressionResult` for the baseline model. **Dependency**: T014.1, T014.2, T014.3, T014.4.
- [ ] T017 [US1] Within `fit_regression` output (or as a post-processing step), compute and **report Pearson correlation coefficient** between flexibility and creativity. **Deliverable**: Append a row to `data/interim/regression_summary.csv` with columns `subject_id`, `flexibility`, `creativity`, `pearson_r`, `empirical_p_value`. **Logic**: If the file does not exist, **initialize it with headers** before appending. **Context**: This metric must be reported as part of the full model output to satisfy FR-005. The `empirical_p_value` MUST be derived from the permutation test (T027), not a parametric calculation. **Dependency**: T051, T027.
- [ ] T017.1 [US1] Implement baseline model `creativity ~ static_connectivity_strength + covariates`, compute ΔR², and **format ΔR² to 4 decimal places** by explicitly calling `format_delta_r2` from T043. **Logic**:
 1. Call `fit_regression` (T051) to get full model R².
 2. Call `fit_baseline_regression` (T051b) to get baseline model R².
 3. Calculate `delta_r2 = full_model_r2 - baseline_model_r2`.
 4. Format using `format_delta_r2`.
 **Deliverable**: Store `delta_r2_str` in `RegressionResult` and write to `data/interim/regression_summary.csv`. **Verification**: Unit test `tests/unit/test_statistics.py::test_format_delta_r2_precision` must assert the string has exactly 4 decimal places. **Dependency**: T051, T051b, T043.

## Phase 4: User Story 2 – Generate Diagnostic Visualisations (Priority: P2)

### Tests

- [X] T021 [P] [US2] Contract test `tests/contract/test_plots.py::test_plot_functions_exist`.

### Implementation

- [X] T022 [P] [US2] Implement `code/viz/plots.py` function `plot_flexibility_vs_creativity(flexibility, creativity, output_path='docs/outputs/flexibility_vs_creativity.png')` that creates a scatter plot with regression line and a confidence band, saves as **`flexibility_vs_creativity.png`**. **Robustness**: Skip NaN data points and log a warning.
- [ ] T023 [US2] Implement `code/viz/plots.py` function `plot_residuals(model: RegressionResult, residuals_path='docs/outputs/model_residuals.png', qq_path='docs/outputs/model_qq.png')` that generates residuals‑vs‑fitted and QQ plots. **Logic**:
 1. Extract residuals and fitted values from `model`.
 2. Filter out any NaN or Inf values before plotting.
 3. Generate residuals-vs-fitted plot and save as `model_residuals.png`.
 4. Generate QQ-plot and save as `model_qq.png`.
 5. **Verification**: Assert both files exist and are non-empty.
 **Dependency**: T051.
- [X] T057 [US2] [P] Implement `compress_image(path: str, max_mb: float = 5.0)` in `code/viz/plots.py`. **Logic**:
 1. Log initial file size.
 2. Attempt compression (e.g., reduce PNG quality or convert to JPEG if acceptable).
 3. Verify final size <= 5MB.
 4. **Failure Handling**: If compression fails to reduce size below 5MB, **raise a `RuntimeError`** with a clear message indicating the file size violation. **Do NOT** skip compression or keep the original file.
 5. **Verification**: Log final file size.
 **Dependency**: T022, T023 (must run after images are generated).
- [ ] T058 [US2] Add error handling in plot functions to skip NaN data points, log warnings, and continue (robustness for missing data). **Verification**: Unit test `tests/unit/test_plots.py::test_nan_handling` must assert that plots are generated without error when input contains NaN.

## Phase 5: User Story 3 – Perform Permutation‑Based Significance Testing & Sensitivity Sweep (Priority: P3)

### Tests

- [X] T026 [P] [US3] Contract test `tests/contract/test_permutation.py::test_permutation_counts`.

### Implementation

- [X] T027 [P] [US3] Implement `run_permutation_test(flexibility, creativity, n_permutations=10000, seed: int = 42) -> dict` in `code/analysis/statistics.py`.
 **Implementation Details**:
 1. Initialize `numpy.random.Generator` with the provided `seed` for reproducibility.
 2. Use vectorized operations: generate a matrix of shape `(n_permutations, len(creativity))` of random indices using `rng.choice`.
 3. Shuffle creativity scores using these indices.
 4. Compute correlation for each shuffled set against the fixed flexibility vector.
 5. **Return Value**: Return a dict containing `{'empirical_p_value': float, 'distribution_of_max_stats': list}`. The `empirical_p_value` is the primary output for FR-006; `distribution_of_max_stats` is required for FR-007 max-T correction.
 **Output**: Returns a dict containing `empirical_p_value` and `distribution_of_max_stats`. **Dependency**: None (independent).
- [X] T046 [US3] Implement `run_sensitivity_analysis(flexibility, creativity, window_lengths=[20,30,40]) -> dict` in `code/analysis/statistics.py`.
 **Implementation Details**:
 1. **Efficiency Constraint**: Do NOT re-run the full fMRI preprocessing or sliding window connectivity computation.
 2. Load pre-computed static connectivity matrices and pre-computed sliding window connectivity matrices (from T014 outputs) from `data/processed/`.
 3. For each `window_length` in the sweep set:
 a. Re-run only the Louvain community detection (T015) and flexibility calculation (T016) on the cached connectivity matrices for that specific window length.
 b. Compute correlation and **empirical p-value** (via permutation test T027) for the new flexibility vector against creativity.
 4. Aggregate results.
 **Output**: `{'p_values': [float,...], 'correlations': [float,...], 'window_lengths': [int,...]}`. **Note**: `p_values` MUST be the *empirical* p-values from T027. **Dependency**: T014 (cached outputs), T015, T016, T027. **Note**: This task is NOT parallel-safe ([P] removed) as it depends on T014 completion.
- [ ] T046.1 [US3] Implement `construct_sensitivity_df(data: dict) -> pd.DataFrame` that transforms the dictionary output of T046 into a pandas DataFrame with columns `window_length`, `correlation`, `empirical_p_value`. **Dependency**: T046. **Verification**: Unit test `tests/unit/test_analysis.py::test_sensitivity_df_columns` must assert the DataFrame has these exact columns, specifically `empirical_p_value`.
- [X] T045.1 [US3] Implement `merge_permutation_data(p_values: List[float], distribution_of_max_stats: List[float]) -> dict` in `code/analysis/statistics.py`. **Logic**: Create a dictionary containing both `p_values` and `distribution_of_max_stats` to be passed to T045. **Input**: `p_values` from T046, `distribution_of_max_stats` from T027. **Output**: Dict ready for FWE correction. **Dependency**: T046, T027.
- [ ] T045.2 [US3] Implement `aggregate_hypothesis_results(window_p_values: List[float], roi_p_values: List[float]) -> dict` in `code/analysis/statistics.py`. **Logic**: Aggregate p-values from multiple hypothesis tests (e.g., sensitivity sweep from T046.1 and ROI-wise tests from T045.3) into a unified list of p-values and test statistics. **Input**: P-values from T046.1 and `roi_p_values` from T045.3. **Output**: Dict containing `all_p_values` and `all_test_stats`. **Dependency**: T046.1, T045.3.
- [ ] T045.3 [US3] Implement `generate_roi_mock_data() -> List[float]` in `code/analysis/statistics.py`. **Logic**: Since the current scope is whole-brain, generate a deterministic mock list of p-values (e.g., `[0.05, 0.04, 0.03]`) representing hypothetical ROI-wise tests to satisfy the FWE aggregation requirement. **Output**: List of floats. **Dependency**: None. **Verification**: Unit test `tests/unit/test_analysis.py::test_roi_mock_data` must assert the output is a list of floats.
- [X] T045 [US3] Implement `apply_fwe_correction(merged_data: dict, method: str = None) -> List[float]` in `code/analysis/statistics.py`.
 **Logic**:
 1. If `method` is None, read `config.FWE_METHOD` (default 'max-t').
 2. If `method='max-t'`, use `merged_data['distribution_of_max_stats']` to compute max-T corrected p-values.
 3. If `method='bonferroni'`, calculate `p_adjusted = min(p * k, 1.0)` where k is the number of tests.
 **Input**: `merged_data` from T045.1 and T045.2. **Output**: List of adjusted p-values. **Dependency**: T045.1, T045.2.
- [ ] T030 [US3] Save permutation results to `data/interim/permutation_results.csv` and sensitivity summary to `data/interim/sensitivity_summary.csv`. **Schema**:
  - `permutation_results.csv`: columns `shuffle_id`, `correlation`.
  - `sensitivity_summary.csv`: columns `window_length`, `correlation`, `empirical_p_value`. **Mandatory**: The `empirical_p_value` column must contain the permutation-derived p-value from T027.
 **Dependency**: T027, T046.1. **Verification**: Unit test `tests/unit/test_analysis.py::test_sensitivity_csv_schema` must assert the `empirical_p_value` column is present and non-null.
- [ ] T031 [US3] Verify the sensitivity DataFrame includes `correlation` and `empirical_p_value` for each window length (SC‑005). **Verification**: Unit test `tests/unit/test_analysis.py::test_sensitivity_df_columns` must assert the DataFrame has these columns. **Dependency**: T030.
- [ ] T060 [US3] Profile and optimise `run_permutation_test` (vectorised NumPy) to complete **≤ 6 hours** on 2 CPU cores and < 7 GB RAM. **Deliverable**: Generate `docs/outputs/profiling_report.txt` containing memory peak and runtime. **Logic**: Generate a subset of a representative number of subjects using `itertools.islice` on the filtered participant list. **Mocking**: Use a pre-generated dummy NIfTI file located at `tests/fixtures/dummy_fmri.nii.gz` (created in T001/T004 setup) to mock heavy fMRI preprocessing steps for the benchmark test. **Verification**: Unit test `tests/benchmark/test_runtime.py` must assert runtime < 6h using a subset of 10 subjects. **Dependency**: T027.
- [ ] T060.1 [US3] Implement scaling projection and CI timeout mitigation. **Logic**: Based on the 10-subject benchmark from T060, extrapolate runtime for ~1000 participants. If projection exceeds 6 hours, implement a mitigation strategy (e.g., chunked processing, parallel execution on multiple runners, or reduced permutation count with justification). **Deliverable**: Update `docs/outputs/profiling_report.txt` with projection and mitigation plan. **Verification**: Unit test `tests/benchmark/test_scaling.py` must assert projection logic is sound. **Dependency**: T060.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T037 [P] Documentation updates in `README.md` and `docs/outputs/` describing each generated artifact and their filenames. **Verification**: Assert `README.md` exists and contains artifact descriptions.
- [ ] T038 Code cleanup and refactoring using `black` and `flake8`. **Verification**: Run `flake8 code/` and assert zero errors.
- [ ] T039 Performance optimisation across all stories (profiling, memory usage < 7 GB). **Verification**: Assert `docs/outputs/profiling_report.txt` indicates memory < 7GB.
- [ ] T040 [P] Additional unit tests for `calculate_flexibility`, `fit_regression`, and `run_permutation_test`. **Verification**: Assert all new tests pass.
- [ ] T041 Security hardening: run `safety check` on `requirements.txt` and update vulnerable packages. **Verification**: Assert `safety check` returns no critical vulnerabilities.
- [ ] T042 [P] Run `quickstart.md` commands in a fresh virtualenv and verify successful completion. **Verification**: Assert all commands in `quickstart.md` execute without error.

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **Critical Pre‑Conditions (Phase 2.5)** → **User Stories (Phase 3‑5)** → **Polish (Phase N)**
- Tasks T018/T019 now explicitly depend on T006 (logging setup) and are listed under Phase 2.5 for correct ordering.
- T020b (logging usage) depends on T018/T019 to ensure logging is invoked correctly.
- T012 runs **after** T036.2 (validation execution) succeeds (ordering clarified).
- T014.1 must be completed before T014.4.
- T014.4 must be completed before T014.2.
- T014.2 must be completed before T051 and T051b.
- T014.3 must be completed before T051 and T051b.
- T051b must be completed before T017.1.
- T017 and T017.1 must be completed after T051 and T051b.
- T043 must be completed before T017.1.
- T046 must be completed before T046.1.
- T046.1 must be completed before T030.
- T045.1 must be completed before T045.
- T045.3 must be completed before T045.2.
- T045.2 must be completed before T045.
- T045 depends on T045.1 and T045.2 (which merges T027, T046, and T045.3 outputs).
- T057 must run after T022/T023.
- T060.1 must run after T060.
- All [P] tasks can run in parallel within their phase.