# Tasks: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Input**: Design documents from `/specs/001-doomscrolling-anxiety/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Project Initialization (Setup)

**Purpose**: Basic project structure and dependencies.

- [X] T001b-i [P] Create root directory: `projects/PROJ-540-the-influence-of-social-media-doomscroll/`.
- [X] T001b-ii [P] Create subdirectories: `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `outputs/`.
- [X] T001b-iii [P] Create `__init__.py` in the root directory `projects/PROJ-540-the-influence-of-social-media-doomscroll/`.
- [X] T001b-iv [P] Create `__init__.py` in every immediate subdirectory (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `outputs/`).

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story or data ingestion can begin.

**⚠️ CRITICAL**: No data ingestion or user story work can begin until this phase is complete.

- [X] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (e.g., `pandas==2.0.3`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `flake8==6.1.0`, `black==23.12.1`).
- [X] T003a [P] Configure linting: Create `.flake8` config file at repository root with `max-line-length = 88` and `exclude =.git,__pycache__,build,dist`. **BLOCKED BY**: T002.
- [X] T003b [P] Configure formatting: Create `pyproject.toml` at repository root with `[tool.black]` section setting `line-length = 88` and `target-version = ['py311']`. **BLOCKED BY**: T002.
- [X] T004 [P] **Implement environment configuration management** in `code/config.py`:
 1. Create function to load dataset URLs and random seeds.
 2. **MUST** verify `seed` variable is not None and raise `ValueError` if missing.
 3. **MUST** log the seed at runtime to satisfy Constitution Principle I (Reproducibility). Use format: `LOG: SEED={seed_value} (INFO)` or `LOG: SEED NOT SET (WARNING)`.
 4. **MUST** explicitly pass the seed to `np.random.seed(seed)` for any data shuffling/sampling operations. Note: OLS fitting in `statsmodels` is deterministic given the data; seed the underlying RNG for any stochastic preprocessing steps.
 5. **MUST** write the seed to `data/processed/metadata.json` to ensure persistence (Constitution Principle V).
- [X] T005 [P] Setup error handling infrastructure for custom exceptions (`PowerLimitationError`, `MathematicalCouplingError`, `DataAvailabilityError`, `DataIntegrityError`) in `code/exceptions.py`.
- [X] T006 [P] Create base data models/entities (`SurveyResponse`, `RegressionModel`) in `code/models.py`. **MUST** include fields `instrument_source` and `measurement_timepoint` in `SurveyResponse` to support T037b's schema validation and T019a's metadata checks.
- [X] T007 [P] Configure logging infrastructure to `outputs/analysis.log`.

**Checkpoint**: Foundation ready - data ingestion and user story implementation can now begin.

---

## Phase 2: Data Ingestion & Verification (US1)

**Purpose**: Download a public survey dataset, validate schema, and extract required variables. This phase replaces the old "Phase 0" to ensure dependencies (T002, T006) are met.

**Goal**: Implement T037 (Data Source Verification) and US1 ingestion tasks.

**Independent Test**: The pipeline can be tested by verifying that the output CSV/JSON contains the exact columns defined in the schema with no null values for the primary predictor and outcome variables after cleaning.

### Implementation for Data Ingestion (T037 & US1)

- [X] T037a [US1] **Implement Streaming Data Loader** in `code/ingest.py`.
 1. Create function `stream_data_source(url)` using `datasets.load_dataset(..., streaming=True)`.
 2. **MUST** yield the first chunk of data (e.g., first 100 rows) for schema inspection without downloading the full dataset.
 3. **MUST** handle connection errors by raising `DataAvailabilityError`.
 4. **BLOCKED BY**: T002, T006.
- [X] T037b [US1] **Implement Schema Validator** in `code/ingest.py`.
 1. Create function `validate_schema(chunk_df, required_columns)` that checks if `required_columns` are present in the chunk.
 2. **REQUIRED COLUMNS**: `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`.
 3. **MAPPING RULES**:
    - **NHANES**: Check for `DMQ010` (Media Consumption) OR any column mapping to `news_exposure_freq`.
    - **GSS**: Check for `NEWS` or `NEWSFREQ` columns.
    - **Pew**: Check for `news_freq` or `social_media_news`.
    - **YouGov**: Check for `news_consumption` or `media_freq`.
 4. **MUST** return a boolean and a list of missing columns.
 5. **BLOCKED BY**: T037a.
- [X] T037c [US1] **Implement Fallback Mapper** in `code/ingest.py`.
 1. Create function `get_fallback_sources()` returning the ordered list: `['NHANES_2017_2018', 'GSS', 'Pew', 'YouGov']`.
 2. **MUST** iterate through sources in order.
 3. **MUST** attempt to download and validate schema for each source using T037a and T037b.
 4. **MUST** HALT with `DataAvailabilityError` ONLY if ALL sources fail to provide the required schema.
 5. **MUST NOT** fallback to synthetic data.
 6. **OUTPUT**: `data/processed/metadata.json` with verified schema, source URL, and variable mapping notes.
 7. **BLOCKED BY**: T037a, T037b.
- [X] T010a [US1] Implement data download in `code/ingest.py`: Create function `download_data(url, output_path)` that fetches data to `data/raw/` and raises an exception on 404/timeout. **MUST NOT** fallback to synthetic data. **MUST** implement strict loader logic: if fetch fails, raise `DataAvailabilityError` immediately. **BLOCKED BY**: T037a.
- [X] T010b [US1] **Implement data parsing and schema validation** in `code/ingest.py`: Create function `parse_and_validate(raw_path)` that reads the file, checks for columns `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, and `gender`, and raises `ValueError` if missing. Output to `data/raw/parsed_data.csv`. **BLOCKED BY**: T010a.
- [X] T012 [US1] **Implement listwise deletion and power check** in `code/clean.py` for missing predictor/outcome values. **MUST enforce N < 30 hard stop (per Spec FR-002)**: HALT with `PowerLimitationError` if resulting N < 30. If 30 <= N < 100, log 'Low Power' warning and proceed. **MUST** explicitly state logic: `if n < 30: raise PowerLimitationError("N < 30")`. **MUST** log Spec baseline as: `INFO: Spec baseline N < 30 active`. **BLOCKED BY**: T010b.
- [X] T013 [US1] Save cleaned dataset to `data/processed/analysis_data.csv`. **BLOCKED BY**: T012.
- [X] T014 [US1] Add logging for row counts, missing value statistics, and power check results. **MUST** log exact messages using `logging.info()` and `logging.warning()`: `INFO: Rows dropped: {count}`, `INFO: Final N: {n}`, `ERROR: Power limitation. N < 30` (if N < 30), or `WARNING: Low Power (30 <= N < 100)` (if 30 <= N < 100). **BLOCKED BY**: T012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 3: Statistical Modeling (US2)

**Goal**: Fit a multiple linear regression model, verify construct validity, and calculate correlations.

**Independent Test**: The model can be tested by running the regression on a synthetic dataset with known coefficients and verifying that the estimated coefficients match the expected values within a small tolerance.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test in `tests/test_model.py`: Define function `test_pearson_correlation_matches_manual_calculation` to verify correlation logic against hardcoded synthetic values.
- [X] T016 [P] [US2] Unit test in `tests/test_validity.py`: Define function `test_coupling_detection_raises_error_on_identical_instruments` to verify the `validity.py` module raises `MathematicalCouplingError` when `baseline_anxiety` and `anxiety_score` are derived from the **same instrument or time point**. The test must mock metadata indicating identical sources to trigger the error.

### Implementation for User Story 2

- [X] T019a [US2] Implement construct validity check in `code/validity.py` to verify `baseline_anxiety` and `anxiety_score` are distinct constructs. **MUST** check variable metadata from `data/processed/metadata.json` (generated by T037c) and `research.md`. **IF metadata is ambiguous or they are derived from the same instrument/time point**: **DROP** `baseline_anxiety` from the model, **LOG** a warning with specific reason (e.g., "Coupling Detected: Same Instrument ID"), and **FLAG** the limitation in the output (do not HALT), per Spec Edge Cases. **BLOCKED BY**: T013, T037c.
- [X] T017 [US2] Implement Pearson/Spearman correlation calculation in `code/model.py` (FR-004). **BLOCKED BY**: T013.
- [X] T018 [US2] Implement OLS regression fitting in `code/model.py` with formula `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`. Create a reusable function `fit_regression_model`. **MUST** use the formula determined by T019a (i.e., if `baseline_anxiety` was dropped, the formula must not include it). **BLOCKED BY**: T013, T019a.
- [X] T019b [US2] Implement assumption checks in `code/model.py`:
 1. **Invoke** the distinct construct validation function from `code/validity.py` (T019a) to ensure `baseline_anxiety` and `anxiety_score` are distinct.
 2. Implement Linearity, Homoscedasticity (Breusch-Pagan), Normality (Shapiro-Wilk) checks as separate functions.
 3. Output diagnostic metrics and pass/fail status. **BLOCKED BY**: T018.
- [X] T019c [US2] Implement Variance Inflation Factor (VIF) detection in `code/model.py`. **MUST** calculate VIF for all predictors and flag the model as unstable if any VIF > 10 (do not halt), as required by Spec Edge Cases. **BLOCKED BY**: T018.
- [X] T046a [US2] **Enhance Assumption Checks (Cook's Distance)** in `code/model.py`: Implement Cook's Distance calculation to identify influential observations. Flag if any exceed threshold (4/n). **BLOCKED BY**: T019b.
- [X] T046b [US2] **Enhance Assumption Checks (Durbin-Watson)** in `code/model.py`: Implement Durbin-Watson test for autocorrelation. **BLOCKED BY**: T019b.
- [X] T046c [US2] **Enhance Assumption Checks (VIF per Variable)** in `code/model.py`: Output individual VIF scores for each predictor. **BLOCKED BY**: T019c.
- [X] T047a [US2] **Implement VIF Flagging Logic** in `code/model.py`. **MUST** check VIF results from T046c. **IF any VIF > 10**:
 1. **FLAG** the model as unstable in `outputs/regression_results.json`.
 2. **SET** the `news_exposure_freq` coefficient to `null` in the output JSON.
 3. **DO NOT** remove variables or re-fit the model.
 4. **LOG** the specific variable(s) causing instability.
 **BLOCKED BY**: T046c.
- [X] T020 [US2] Implement proxy flagging logic in `code/model.py` for `general_anxiety` vs `anticipatory_anxiety` (FR-008). **MUST** explicitly flag the analysis results in the output JSON and final report if 'general_anxiety' was used as a proxy, noting the construct validity limitation. **BLOCKED BY**: T018.
- [X] T021 [US2] Save regression results to `outputs/regression_results.json` (coefficients, p-values, diagnostics). **MUST** include the `flags` array and VIF status. **BLOCKED BY**: T018, T047a.
- [X] T022 [US2] Save correlation results to `outputs/correlation_results.json`. **BLOCKED BY**: T017.
- [X] T022b [US2] Implement diagnostic plot generation in `code/model.py` to output `outputs/diagnostics_residuals.png` (Residuals vs Fitted) and `outputs/diagnostics_qq.png` (Q-Q Plot). **MUST** include the Breusch-Pagan and Shapiro-Wilk test statistics in the plot titles or legends. **BLOCKED BY**: T019b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 4: Robustness Check & Visualization (US3)

**Goal**: Generate visualizations and perform robustness check on high-engagement subset.

**Independent Test**: The visualization can be tested by generating a plot file and verifying the regression line passes through the centroid of the data points. The robustness check is tested by comparing the coefficient sign and significance between the full sample and the subset.

### Tests for User Story 3

- [X] T023 [P] [US3] Unit test in `tests/test_robustness.py`: Define function `test_subset_selection_filters_top_25_percentile` to verify the filtering logic for the high-engagement subset.
- [X] T024 [P] [US3] Integration test in `tests/test_viz.py`: Define function `test_plot_file_exists_and_contains_regression_line` to verify the plot file exists and contains the expected regression line.

### Implementation for User Story 3

- [X] T025b [US3] **Implement robustness check per Spec FR-006 & Plan Amendments**:
 1. **Check for `social_media_engagement` variable**: If present, calculate correlation with `news_exposure_freq`.
 2. **If `r > 0.3`**: Select top 25th percentile and re-fit model. Compare coefficients/significance with full model.
 3. **If `r <= 0.3` OR variable missing**: **SWITCH** to the **Education Level** subgroup (High vs Low) as mandated by the Plan's "Task Dependencies & Amendments" section.
 4. **Education Level Fallback Logic**:
    - Select top 25th percentile of `education_level` (or equivalent).
    - Re-fit model on this subgroup.
    - **MUST** verify subgroup sample size is sufficient (N >= 30). If N < 30, log warning and skip robustness check.
 5. **MUST** explicitly flag in `outputs/robustness_results.json` which subgroup was used (Engagement or Education Level) and the reason.
 6. **MUST** compare the coefficient sign and significance between the full sample and the subgroup.
 7. Overwrite `outputs/robustness_results.json` with `status: "run"`, including full results.
 8. **BLOCKED BY**: T018, T021.
- [X] T028 [US3] Implement scatter plot generation in `code/viz.py` with regression line and 95% CI (FR-005). **BLOCKED BY**: T018.
- [X] T029 [US3] Save plot to `outputs/plot.png`. **BLOCKED BY**: T028.
- [X] T030 [US3] **Generate Final Report** in `code/viz.py`. **MUST** include sections: Executive Summary, Methods, Results (including correlation, regression, and VIF flags), Robustness Check (reporting full results and subgroup used), Limitations, and Conclusion. **MUST** cite specific JSON outputs (`regression_results.json`, `correlation_results.json`, `robustness_results.json`). **MUST** include Streaming Data Metadata (from T037c) and VIF Flagging Log (from T047a). **BLOCKED BY**: T021, T025b, T047a, T046a, T046b, T046c.
- [X] T029b [US3] Implement robustness visualization in `code/viz.py` to generate `outputs/robustness_comparison.png` (only if T025b runs). **MUST** overlay the subset data points with a different color than the full sample and plot two distinct regression lines (one for full sample, one for subset) with a legend indicating which is which, ensuring visual traceability of the robustness check. **BLOCKED BY**: T025b.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T031 [P] **Documentation updates** in `README.md` and `docs/`. **MUST** include:
 1. A "Usage" section with the command `python code/main.py`.
 2. A "Data" section describing the expected schema and the verified dataset source (NHANES 2017-2018 or fallback).
 3. Generation of `quickstart.md` with step-by-step instructions for running the pipeline.
- [X] T032 [P] Code cleanup and refactoring: Remove unused imports, extract helper functions.
- [X] T033a [P] **Create Benchmark Data Generator**: Create `code/benchmark_utils.py` with a function `generate_synthetic_data(n=10000, seed=42)` that produces a DataFrame with the required schema for testing. **MUST** write "PASS: Runtime < 60s" to the log if the condition is met. **MUST** store generated data in `data/benchmark/` directory ONLY, explicitly isolating it from `data/processed/` to prevent leakage into the main analysis pipeline. **BLOCKED BY**: T033b.
- [X] T033b [P] **Create Runtime Check in main.py**: Implement a check in `code/main.py` that verifies the input data path is NOT in `data/benchmark/` before running the main analysis pipeline. **MUST** raise `DataIntegrityError` with message "DataIntegrityError: Synthetic data detected in main analysis path." if synthetic data is detected. **BLOCKED BY**: T033a.
- [X] T033 [P] Performance optimization: Vectorize pandas operations, use chunking for large files. **MUST** ensure the pipeline completes on **real data** (or a real streamed sample of up to 100k rows) in < 60 seconds. **MUST** produce a `benchmark.log` file showing the runtime. **MUST** verify `benchmark.log` contains "PASS: Runtime < 60s" and exit code 0. **BLOCKED BY**: T033a, T033b.
- [X] T034 [P] Add specific unit tests for `code/config.py` (seed verification) and `code/robustness.py` (conditional logic) to ensure coverage of new logic.
- [X] T035 [P] **Run quickstart.md validation**: Execute the steps in `quickstart.md` (generated by T031) and verify that the pipeline runs successfully without manual intervention.

---

## Phase 6: Execution Verification & Final Audit (Blocking Completion)

**Purpose**: Ensure the pipeline runs end-to-end on real data and produces verifiable artifacts without fabrication.

**⚠️ CRITICAL**: This phase MUST be completed before marking the feature as "Done".

- [ ] T038 [US1] **Execute Full Pipeline on NHANES**: Run `python code/main.py` against the verified NHANES 2017-2018 dataset (or fallback). **MUST** verify that:
 1. The dataset is successfully downloaded and streamed (no synthetic fallback).
 2. The schema validation passes or fails loudly (no silent errors).
 3. The regression model runs and produces `outputs/regression_results.json`.
 4. The robustness check runs (or switches to Education Level) and produces `outputs/robustness_results.json`.
 5. All plots are generated in `outputs/`.
 6. The final report `outputs/final_report.md` is generated with all required sections.
- [ ] T039 [US1] **Audit for Fabrication**: Inspect `outputs/regression_results.json`, `outputs/correlation_results.json`, and `outputs/robustness_results.json` to ensure no values are hardcoded, synthetic, or derived from `generate_synthetic_data`. **MUST** verify that the `flags` array in the results correctly identifies the use of `general_anxiety` as a proxy (FR-008) and any other limitations. **Specific Check**: Verify `flags` array contains the string "Proxy Used: General Anxiety" if applicable. **BLOCKED BY**: T038.
- [ ] T040 [US1] **Verify Reproducibility**: Re-run the pipeline with the same seed and verify that the output files (`outputs/regression_results.json`, `outputs/correlation_results.json`, `outputs/robustness_results.json`) are bitwise identical (for text files) or within floating-point tolerance (`np.allclose` with `rtol=1e-5, atol=1e-8` for floats) to the previous run. **BLOCKED BY**: T039.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies - MUST complete first.
- **Phase 2 (Data Ingestion)**: Depends on Phase 1 completion.
- **Phase 3 (Modeling)**: Depends on Phase 2 completion.
- **Phase 4 (Robustness)**: Depends on Phase 3 completion.
- **Phase 5 (Polish)**: Depends on all desired user stories being complete.
- **Phase 6 (Execution)**: Depends on all previous phases being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 completion.
- **User Story 2 (P2)**: Can start after Phase 2 completion (depends on clean data).
- **User Story 3 (P3)**: Can start after Phase 3 completion (depends on model results).

### Within Each User Story

- Tests (if included) MUST be written as scaffolding (empty files with TODOs) before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (within Phase 1).
- All Foundational tasks marked [P] can run in parallel (within Phase 1, excluding T003a/003b which depend on T002).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all scaffolding for User Story 1 together:
Task: "Unit test scaffolding in tests/test_ingest.py: Define class TestIngestion and function test_schema_validation_raises_error_on_missing_column"
Task: "Unit test scaffolding in tests/test_clean.py: Define class TestCleaning and function test_listwise_deletion_halts_on_low_power"

# Launch all implementation for User Story 1 together:
Task: "Implement data download in code/ingest.py"
Task: "Implement data parsing and schema validation in code/ingest.py"
Task: "Implement listwise deletion and power check in code/clean.py (N < 30 hard stop per Spec FR-002)"
Task: "Implement streaming data loader in code/ingest.py (T037a)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational.
2. Complete Phase 2: Data Ingestion (including T037 Data Verification).
3. **STOP and VALIDATE**: Test User Story 1 independently.
4. Deploy/demo if ready.

### Incremental Delivery

1. Complete Phase 1 -> Foundation ready.
2. Add Phase 2 -> Test independently -> Deploy/Demo (MVP!).
3. Add Phase 3 -> Test independently -> Deploy/Demo.
4. Add Phase 4 -> Test independently -> Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 (Foundational) together.
2. Once Phase 1 is done:
 - Developer A: Phase 2 (Data Ingestion)
 - Developer B: Phase 3 (Modeling)
 - Developer C: Phase 4 (Robustness)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing (Scaffolding first).
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Critical**: Ensure all data loading tasks strictly fail on missing real data and never fall back to synthetic generation.
- **Critical**: T037a/b/c use NHANES 2017-2018 as the primary source, with explicit fallback to GSS/Pew/YouGov if schema fails.
- **Critical**: T012 implements N < 30 hard stop per Spec FR-002.
- **Critical**: T025b implements conditional robustness check (r > 0.3) OR Education Level fallback per Plan Amendments.
- **Critical**: T019a handles coupling (DROP and FLAG) per Spec Edge Cases.
- **Critical**: T033a/b generate benchmark data and runtime check, isolating synthetic data from main pipeline.
- **Critical**: T038, T039, T040 are mandatory execution verification tasks to ensure real data usage and reproducibility.
- **Correction**: T003a and T003b are sequential dependencies of T002 (not parallel) to ensure linting/formatter tools are installed before configuration.
- **New**: Phase 7 removed. Streaming logic merged into T037a/b/c.
- **New**: Phase 8 tasks (T046a, T046b, T046c, T047a) added to Phase 3 for Spec-compliant diagnostics and flagging.
- **New**: Phase 9 tasks (T030) merged into Phase 4 for final report generation.
- **New**: T040 updated with specific reproducibility tolerance.
- **New**: T033a/b updated with specific error message and check location.
- **Note**: T038, T039, T040 are sequential, not parallel.