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
- [X] T001c-impl [P] **Implement Orchestration Script** in `code/main.py`:
 1. Create the entry point that imports `ingest`, `clean`, `model`, `viz`, and `config`.
 2. **MUST** execute the pipeline in order: `ingest` -> `clean` -> `model` -> `viz`.
 3. **MUST** handle exceptions from any module and log them to `outputs/analysis.log`.
 4. **MUST** return exit code 0 on success, non-zero on failure.
 5. **BLOCKED BY**: T001b-iv, T002.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story or data ingestion can begin.

**⚠️ CRITICAL**: No data ingestion or user story work can begin until this phase is complete.

- [X] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (e.g., `pandas>=2.0.3`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `requests>=2.31.0`, `pyyaml>=6.0.1`, `flake8>=6.1.0`, `black>=23.12.1`).
- [X] T003a [P] Configure linting: Create `.flake8` config file at repository root with `max-line-length = 88` and `exclude =.git,__pycache__,build,dist`. **BLOCKED BY**: T002. (Parallel with T003b relative to each other, but strictly sequential to T002).
- [X] T003b [P] Configure formatting: Create `pyproject.toml` at repository root with `[tool.black]` section setting `line-length = 88` and `target-version = ['py311']`. **BLOCKED BY**: T002. (Parallel with T003a relative to each other, but strictly sequential to T002).
- [X] T004 [P] **Implement environment configuration management** in `code/config.py`:
 1. Create function to load dataset URLs and random seeds.
 2. **MUST** verify `seed` variable is not None and raise `ValueError` if missing.
 3. **MUST** log the seed at runtime to satisfy Constitution Principle I (Reproducibility). Use format: `LOG: SEED={seed_value} (INFO)` or `LOG: SEED NOT SET (WARNING)`.
 4. **MUST** explicitly pass the seed to `np.random.seed(seed)` for any data shuffling/sampling operations. Note: OLS fitting in `statsmodels` is deterministic given the data; seed the underlying RNG for any stochastic preprocessing steps.
 5. **MUST** write the seed to `data/processed/metadata.json` with the exact key `random_seed` (e.g., `{"random_seed": 12345}`) to ensure persistence (Constitution Principle V).
- [X] T005 [P] Setup error handling infrastructure for custom exceptions (`PowerLimitationError`, `MathematicalCouplingError`, `DataAvailabilityError`, `DataIntegrityError`) in `code/exceptions.py`.
- [X] T006 [P] Create base data models/entities (`SurveyResponse`, `RegressionModel`) in `code/models.py`. **MUST** include fields `instrument_source` and `measurement_timepoint` in `SurveyResponse` to support T019a's schema validation and metadata checks.
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
- [X] T037c-1 [US1] **Implement Source Iterator** in `code/ingest.py`.
 1. Create function `get_fallback_sources()` returning the ordered list: `['NHANES_2017_2018', 'GSS', 'Pew', 'YouGov']`.
 2. **MUST** iterate through sources in order.
 3. **BLOCKED BY**: T037a, T037b.
- [X] T037c-2 [US1] **Implement Schema Validation Loop** in `code/ingest.py`.
 1. **MUST** iterate through sources provided by T037c-1.
 2. **MUST** attempt to stream the first chunk (via T037a) and validate schema (via T037b) for each source.
 3. **MUST** perform a 'quick count' (head N) on the streamed chunk to estimate sample size.
 4. **MUST** HALT with `PowerLimitationError` immediately if the estimated N < 30 for the current source, preventing full download of insufficient datasets.
 5. **MUST** HALT with `DataAvailabilityError` ONLY if ALL sources fail to provide the required schema OR if ALL sources fail the N < 30 check.
 6. **MUST** NOT fallback to synthetic data.
 7. **OUTPUT**: `data/processed/metadata.json` with verified schema, source URL, and variable mapping notes.
 8. **BLOCKED BY**: T037a, T037b, T037c-1.
- [X] T037c-3 [US1] **Write Metadata Output** in `code/ingest.py`.
 1. **MUST** write the final `metadata.json` containing `source_url`, `verified_columns`, and `random_seed`.
 2. **BLOCKED BY**: T037c-2.
- [X] T010a [US1] Implement data download in `code/ingest.py`: Create function `download_data(url, output_path)` that fetches data to `data/raw/` and raises an exception on 404/timeout. **MUST NOT** fallback to synthetic data. **MUST** implement strict loader logic: if fetch fails, raise `DataAvailabilityError` immediately. **MUST** be conditional on T037c success (check `metadata.json` for valid source). **BLOCKED BY**: T037c-3.
- [X] T010b [US1] Implement data parsing and schema validation in `code/ingest.py`: Create function `parse_and_validate(raw_path)` that reads the file, checks for columns `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, and `gender`, and raises `ValueError` if missing. Output to `data/raw/parsed_data.csv`. **BLOCKED BY**: T010a.
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
- [X] T016 [P] [US2] Unit test in `tests/test_validity.py`: Define function `test_coupling_detection_raises_error_on_identical_instruments` to verify the `validity.py` module raises `MathematicalCouplingError` when `baseline_anxiety` and `anxiety_score` are derived from the same instrument or time point. The test must mock metadata indicating identical sources to trigger the error.

### Implementation for User Story 2

- [X] T019a [US2] Implement construct validity check in `code/validity.py` to verify `baseline_anxiety` and `anxiety_score` are distinct constructs. **MUST** check variable metadata from `data/processed/metadata.json` (generated by T037c) and `research.md`. **IF metadata is ambiguous or they are derived from the same instrument/time point**: **DROP** `baseline_anxiety` from the model, **LOG** a warning with specific reason (e.g., "Coupling Detected: Same Instrument ID"), and **FLAG** the limitation in the output (do not HALT), per Spec Edge Cases. **MUST** output the final list of `formula_variables` to `data/processed/metadata.json` under the key `formula_variables` to be consumed by T018a. **BLOCKED BY**: T013, T037c-3.
- [X] T017 [US2] Implement Pearson/Spearman correlation calculation in `code/model.py` (FR-004). **BLOCKED BY**: T013.
- [X] T018a [US2] **Implement Formula Construction** in `code/model.py`.
 1. **MUST** read `data/processed/metadata.json` and extract the `formula_variables` list generated by T019a.
 2. **MUST** construct the regression formula string dynamically: `anxiety_score ~ { ' + '.join(formula_variables) }`.
 3. **MUST** NOT hardcode the formula; it must depend on T019a's output.
 4. **BLOCKED BY**: T013, T019a.
- [X] T018b [US2] **Implement OLS Regression Fitting** in `code/model.py`.
 1. Create a reusable function `fit_regression_model(formula_string, df)`.
 2. **MUST** use the formula string generated by T018a.
 3. **BLOCKED BY**: T018a.
- [X] T019b [US2] Implement assumption checks in `code/model.py`:
 1. **Invoke** the distinct construct validation function from `code/validity.py` (T019a) to ensure `baseline_anxiety` and `anxiety_score` are distinct.
 2. Implement Linearity, Homoscedasticity (Breusch-Pagan), Normality (Shapiro-Wilk) checks as separate functions.
 3. Output diagnostic metrics and pass/fail status. **BLOCKED BY**: T018b.
- [X] T047a [US2] **Implement VIF Flagging Logic** in `code/model.py`. **MUST** check VIF results from T019b. **IF any VIF > 10**:
 1. **FLAG** the model as unstable in `outputs/regression_results.json`.
 2. **SET** the `news_exposure_freq` coefficient to `null` in the output JSON.
 3. **DO NOT** remove variables or re-fit the model.
 4. **LOG** the specific variable(s) causing instability.
 **BLOCKED BY**: T019b.
- [X] T020 [US2] Implement proxy flagging logic in `code/model.py` for `general_anxiety` vs `anticipatory_anxiety` (FR-008). **MUST** explicitly flag the analysis results in the output JSON and final report if 'general_anxiety' was used as a proxy, noting the construct validity limitation. **BLOCKED BY**: T018b.
- [X] T021 [US2] Save regression results to `outputs/regression_results.json` (coefficients, p-values, diagnostics). **MUST** include the `flags` array aggregating all flags (VIF instability, Proxy Used, Coupling Detected) and VIF status. **MUST** ensure the `flags` array is populated before T039 runs. **BLOCKED BY**: T018b, T047a.
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

- [X] T025b-1 [US3] **Check Correlation Condition** in `code/robustness.py`.
 1. **Check for `social_media_engagement` variable**: If present, calculate correlation with `news_exposure_freq`.
 2. **If `r > 0.3`**: Proceed to T025b-2.
 3. **If `r <= 0.3` OR variable missing**: **SKIP** the robustness check entirely. **LOG** a warning: "Robustness check skipped: Correlation condition (r > 0.3) not met or variable missing per Spec FR-006".
 4. **MUST** explicitly flag in `outputs/robustness_results.json` that the check was skipped if applicable.
 5. **MUST** explicitly document in the output JSON that this is a strict adherence to Spec FR-006.
 6. **BLOCKED BY**: T013, T021.
- [X] T025b-2 [US3] **Run Subset Model** in `code/robustness.py` (only if T025b-1 passes).
 1. Select top 25th percentile of users based on `social_media_engagement`.
 2. Re-fit the model using the formula from T018a.
 3. Compare coefficients/significance with full model.
 4. **BLOCKED BY**: T025b-1.
- [X] T025b-3 [US3] **Generate Comparison Output** in `code/robustness.py`.
 1. Overwrite `outputs/robustness_results.json` with `status: "run"` (if run) or `status: "skipped"` (if skipped), including full results or reason.
 2. **MUST** compare the coefficient sign and significance between the full sample and the subset ONLY if the check was run.
 3. **BLOCKED BY**: T025b-1, T025b-2.
- [X] T028 [US3] Implement scatter plot generation in `code/viz.py` with regression line and 95% CI (FR-005). **BLOCKED BY**: T018b.
- [X] T029 [US3] Save plot to `outputs/plot.png`. **BLOCKED BY**: T028.
- [X] T030 [US3] **Generate Final Report** in `code/viz.py`. **MUST** include sections: Executive Summary, Methods, Results (including correlation, regression, and VIF flags), Robustness Check (reporting full results or skip reason), Limitations, and Conclusion. **MUST** cite specific JSON outputs (`regression_results.json`, `correlation_results.json`, `robustness_results.json`). **MUST** include Streaming Data Metadata (from T037c) and VIF Flagging Log (from T047a). **BLOCKED BY**: T021, T025b-3, T047a.
- [X] T029b [US3] Implement robustness visualization in `code/viz.py` to generate `outputs/robustness_comparison.png` (only if T025b-2 runs). **MUST** overlay the subset data points with a different color than the full sample and plot two distinct regression lines (one for full sample, one for subset) with a legend indicating which is which, ensuring visual traceability of the robustness check. **BLOCKED BY**: T025b-2.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T031 [P] **Documentation updates** in `README.md` and `docs/`. **MUST** include:
 1. A "Usage" section with the command `python code/main.py`.
 2. A "Data" section describing the expected schema and the verified dataset source (NHANES 2017-2018 or fallback).
 3. Generation of `quickstart.md` with step-by-step instructions for running the pipeline.
- [X] T032 [P] Code cleanup and refactoring: Remove unused imports, extract helper functions.
- [X] T033 [P] **Performance Benchmark (Real Data Only)**:
 1. Create a function `run_benchmark` in `code/main.py` that executes the full pipeline on a **real streamed sample** (first [deferred] rows of the verified NHANES dataset).
 2. **MUST NOT** use synthetic data.
 3. **MUST** measure total runtime.
 4. **MUST** write `benchmark.log` with the result.
 5. **MUST** verify `benchmark.log` contains "PASS: Runtime < 60s" and exit code 0.
 6. **BLOCKED BY**: T001c-impl, T038 (conceptually, but runs as a separate validation step).
- [X] T034 [P] Add specific unit tests for `code/config.py` (seed verification) and `code/robustness.py` (conditional logic) to ensure coverage of new logic.
- [X] T041-impl [P] **Implement Validation Script** in `code/validation.py`:
 1. Create a script that reads `outputs/success_criteria_validation.json`, `outputs/regression_results.json`, `outputs/robustness_results.json`, and `benchmark.log`.
 2. **MUST** implement logic to check SC-001 through SC-005.
 3. **MUST** output a JSON report with explicit PASS/FAIL status for each SC.
 4. **MUST** handle missing files gracefully by reporting FAIL for the corresponding SC.
 5. **BLOCKED BY**: T031.
- [X] T035 [P] **Run quickstart.md validation**: Execute the steps in `quickstart.md` (generated by T031) and verify that the pipeline runs successfully without manual intervention.

---

## Phase 6: Execution Verification & Final Audit (Blocking Completion)

**Purpose**: Ensure the pipeline runs end-to-end on real data and produces verifiable artifacts without fabrication.

**⚠️ CRITICAL**: This phase MUST be completed before marking the feature as "Done".

- [X] T038 [US1] **Execute Full Pipeline on NHANES**: Run `python code/main.py` against the verified NHANES 2017-2018 dataset (or fallback). **MUST** verify that:
 1. The dataset is successfully downloaded and streamed (no synthetic fallback).
 2. The schema validation passes or fails loudly (no silent errors).
 3. The regression model runs and produces `outputs/regression_results.json`.
 4. The robustness check runs (or skips) and produces `outputs/robustness_results.json`.
 5. All plots are generated in `outputs/`.
 6. The final report `outputs/final_report.md` is generated with all required sections.
 7. **BLOCKED BY**: T001c-impl, T021, T022, T025b-3.
- [X] T039 [US1] **Audit for Fabrication**: Inspect `outputs/regression_results.json`, `outputs/correlation_results.json`, and `outputs/robustness_results.json` to ensure no values are hardcoded, synthetic, or derived from `generate_synthetic_data`. **MUST** verify that the `flags` array correctly identifies the use of `general_anxiety` as a proxy (FR-008) and any other limitations. **Specific Check**: Verify `flags` array contains the string "Proxy Used: General Anxiety" if applicable. **Deterministic Heuristic**: Verify that no float values in the results match the hardcoded synthetic defaults defined in `code/config.py` (e.,g., 0.0, 1.0, 0.5) and check for zero variance in continuous result fields. **BLOCKED BY**: T038, T021, T022.
- [X] T040 [US1] **Verify Reproducibility**: Re-run the pipeline with the same seed and verify that the output files (`outputs/regression_results.json`, `outputs/correlation_results.json`, `outputs/robustness_results.json`) are bitwise identical (for text files) or within floating-point tolerance (`np.allclose` with `rtol=1e-5, atol=1e-8` for floats) to the previous run. **BLOCKED BY**: T039, T021, T022.

---

## Phase 7: Final Validation & Sign-off

**Purpose**: Final checks to ensure the project meets all success criteria and is ready for deployment.

- [ ] T041 [P] **Validate Success Criteria**: Run `code/validation.py` (generated by T041-impl) to programmatically check SC-001 through SC-005 against the generated JSON artifacts.
 1. **SC-001**: Verify `p-value` for `news_exposure_freq` is present and compared to 0.05.
 2. **SC-002**: Verify `R-squared` is present and reported.
 3. **SC-003**: Verify robustness check results (coefficient sign/significance) are compared and logged (or skip reason logged).
 4. **SC-004**: Verify assumption check results (Shapiro-Wilk p-value) are present and reported.
 5. **SC-005**: Verify `benchmark.log` (from T033) exists and shows runtime < 60s. **MUST** explicitly check if runtime > 60s and report "FAIL: Runtime Exceeded" or "PASS: Runtime OK".
 6. **MUST** generate `outputs/success_criteria_validation.json` with the exact schema: `{ 'SC-001': { 'status': 'PASS' | 'FAIL', 'value': <float> }, ... }`.
 7. **MUST** generate this file regardless of pass/fail status to unblock downstream tasks.
 8. **BLOCKED BY**: T038, T039, T040, T033, T041-impl.
- [X] T042 [P] **Final Code Review**: Perform a manual review of `code/main.py`, `code/ingest.py`, `code/model.py`, and `code/viz.py` to ensure no fabrication logic, synthetic fallbacks, or hardcoded values exist. **MUST** confirm all data flows from real sources.
- [X] T043 [P] **Generate Final Documentation**: Update `README.md` with final results summary, known limitations (e.g., proxy use), and instructions for reproducing the analysis. **MUST** read `outputs/success_criteria_validation.json` and `outputs/regression_results.json` to populate a "Results Summary" section. **MUST** generate `outputs/task_status_log.json` aggregating the status of T001-T044. **BLOCKED BY**: T041, T042.
- [X] T044 [P] **Archive Artifacts**: Create a zip archive of `data/processed/`, `outputs/`, and `code/` for long-term storage and reproducibility. **BLOCKED BY**: T043.
- [ ] T045 [P] **Sign-off**: Confirm all tasks are complete and the project meets the definition of done.
 1. **MUST** generate `outputs/sign_off_report.md` that lists:
 - Status of all prior tasks (T001-T044) by reading `outputs/task_status_log.json`.
 - **Final project state**: 'Success' if T041 reports all SCs as PASS, or 'Documented Failure' if any SC is FAIL.
 2. **MUST** determine 'Final project state' by reading `outputs/success_criteria_validation.json` and `outputs/task_status_log.json`.
 3. **BLOCKED BY**: T041, T043, T044.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies - MUST complete first.
- **Phase 2 (Data Ingestion)**: Depends on Phase 1 completion.
- **Phase 3 (Modeling)**: Depends on Phase 2 completion.
- **Phase 4 (Robustness)**: Depends on Phase 3 completion.
- **Phase 5 (Polish)**: Depends on all desired user stories being complete.
- **Phase 6 (Execution)**: Depends on all previous phases being complete.
- **Phase 7 (Final Validation)**: Depends on Phase 6 completion.

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
- **Critical**: T025b-1 implements strict Spec FR-006 compliance (skip if r <= 0.3).
- **Critical**: T019a handles coupling (DROP and FLAG) per Spec Edge Cases and outputs `formula_variables` for T018a.
- **Critical**: T033 (Benchmark) uses REAL streamed data (10,000 rows), no synthetic generation.
- **Critical**: T038, T039, T040 are mandatory execution verification tasks to ensure real data usage and reproducibility.
- **Correction**: T003a and T003b are sequential dependencies of T002 (not parallel) to ensure linting/formatter tools are installed before configuration.
- **New**: Phase 7 removed. Streaming logic merged into T037a/b/c.
- **New**: Phase 8 tasks (T046a, T046b, T046c, T047a) added to Phase 3 for Spec-compliant diagnostics and flagging. (Note: T046a/b/c removed, T047a retained).
- **New**: Phase 9 tasks (T030) merged into Phase 4 for final report generation.
- **New**: T001c-impl added to create `code/main.py`.
- **New**: T021 updated to mandate `flags` array aggregation.
- **New**: T033 updated to remove synthetic data generator and use real streamed data.
- **New**: T041 updated with explicit PASS/FAIL criteria for runtime and defined JSON schema.
- **New**: T025b updated to strictly follow Spec FR-006 (skip if r <= 0.3) and atomized into T025b-1, T025b-2, T025b-3.
- **New**: T019a updated to depend on T037c-3 and output `formula_variables`.
- **New**: T003a/b updated to clarify parallelism only relative to each other, not T002.
- **Removed**: T033a/b (synthetic data generator) to comply with Data Hygiene.
- **Removed**: T046a/b/c (gold-plating) to focus on core spec requirements.
- **New**: T037c split into T037c-1, T037c-2, T037c-3 for executability.
- **New**: T018 split into T018a (Formula Construction) and T018b (Fitting) to enforce pre-condition.
- **New**: T045 updated to define 'Final project state' logic based on T041.
- **New**: T041-impl added to implement `code/validation.py`.
- **New**: T043.1 added to generate `task_status_log.json`.