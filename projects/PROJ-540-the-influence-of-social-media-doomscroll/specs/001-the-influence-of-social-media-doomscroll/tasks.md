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

## Phase 0: Data Availability & Methodology Ratification (Blocking Prerequisites)

**Purpose**: Verify data existence and ratify methodology overrides before any implementation begins.

**⚠️ CRITICAL**: No implementation tasks (Phase 3+) can begin until this phase is complete.

- [ ] T036 [P] [Review] **Create Amendment Document**: Create `specs/001-doomscrolling-anxiety/amendment.md` to formally ratify the following methodology overrides. **MUST** follow this exact template:
 1. **Header**: `# Methodology Amendment`
 2. **Override 1 (Power)**: Override Spec FR-002 (N < 30) to Plan Phase 1 (N < 130). Include scientific justification.
 3. **Override 2 (Robustness)**: Override Spec FR-006 (conditional check) to Plan Phase 2.3 (unconditional check). Include justification.
 4. **Traceability Matrix**: Explicitly list `Spec FR-ID` -> `Plan Override` -> `Justification` for each.
 5. **Validation**: Confirm that T012 and T025b will implement these overrides.
 6. **Verification**: The implementer MUST explicitly verify that the amendment document correctly cites the specific line items in the spec being overridden and that the code logic (T012, T025b) matches the ratified text.
 **MUST** be completed and marked [X] before T037, T012, or T025 can be executed.

- [ ] T037 [US1] **Data Source Verification & Streaming**: Implement a specific, verified data ingestion task in `code/ingest.py` targeting a list of verified public datasets (GSS, Pew, YouGov). **MUST** use `datasets.load_dataset(..., streaming=True)` if estimated size > 1GB. **MUST** include a pre-flight check fetching the schema/head to confirm presence of `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, and `gender` for *each* candidate dataset in the list until one matches. If *all* candidates fail schema validation or are unreachable, raise `DataAvailabilityError` and HALT. **MUST NOT** fallback to synthetic data. If streaming, process in chunks to calculate online statistics for power check. **BLOCKED BY T036**.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory structure: `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`. **MUST** create `.gitkeep` files in each directory to ensure deterministic deliverables.
- [ ] T001b [P] Create source structure: Create directory `projects/PROJ-540-the-influence-of-social-media-doomscroll/` and create `__init__.py` files in the root and every immediate subdirectory (code/, tests/, data/, data/raw/, data/processed/, outputs/).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (e.g., `pandas==2.0.3`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `pyyaml==6.0.1`)
- [ ] T003a [P] Configure linting: Create `.flake8` config file at repository root with `max-line-length = 88` and `exclude =.git,__pycache__,build,dist`.
- [X] T003b [P] Configure formatting: Create `pyproject.toml` at repository root with `[tool.black]` section setting `line-length = 88` and `target-version = ['py311']`.
- [X] T004 [P] **Implement environment configuration management** in `code/config.py`:
 1. Create function to load dataset URLs and random seeds.
 2. **MUST** verify `seed` variable is not None and raise `ValueError` if missing.
 3. **MUST** log the seed at runtime to satisfy Constitution Principle I (Reproducibility). Use format: `LOG: SEED={seed_value} (INFO)` or `LOG: SEED NOT SET (WARNING)`.
- [X] T005 [P] Setup error handling infrastructure for custom exceptions (`PowerLimitationError`, `MathematicalCouplingError`) in `code/exceptions.py`
- [X] T006 [P] Create base data models/entities (`SurveyResponse`, `RegressionModel`) in `code/models.py`
- [X] T007 [P] Configure logging infrastructure to `outputs/analysis.log`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Extraction (Priority: P1) 🎯 MVP

**Goal**: Download a public survey dataset, validate schema, and extract required variables.

**Independent Test**: The pipeline can be tested by verifying that the output CSV/JSON contains the exact columns defined in the schema with no null values for the primary predictor and outcome variables after cleaning.

### Tests for User Story 1

> **NOTE: Write these tests FIRST (Scaffolding only), ensure they FAIL before implementation**

- [X] T008 [P] [US1] Unit test scaffolding in `tests/test_ingest.py`: Define class `TestIngestion` and function `test_schema_validation_raises_error_on_missing_column` with `pytest.skip("Implementation pending")` and assert structure. Do not import implementation logic yet.
- [X] T009 [P] [US1] Unit test scaffolding in `tests/test_clean.py`: Define class `TestCleaning` and function `test_listwise_deletion_halts_on_low_power` with `pytest.skip("Implementation pending")` and assert structure. Do not import implementation logic yet.

### Implementation for User Story 1

- [X] T010a [US1] Implement data download in `code/ingest.py`: Create function `download_data(url, output_path)` that fetches data to `data/raw/` and raises an exception on 404/timeout. **MUST NOT** fallback to synthetic data. **BLOCKED BY T037**.
- [X] T010b [US1] **Implement data parsing and schema validation** in `code/ingest.py`: Create function `parse_and_validate(raw_path)` that reads the file, checks for columns `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, and `gender`, and raises `ValueError` if missing. Output to `data/raw/parsed_data.csv`. **BLOCKED BY T037**.
- [X] T012 [US1] **Implement listwise deletion and power check** in `code/clean.py` for missing predictor/outcome values. **MUST enforce N < 130 hard stop (per ratified amendment T036)**: HALT with `PowerLimitationError` if resulting N < 130. If 130 <= N < 200, log 'Low Power' warning and proceed. **MUST** explicitly state logic: `if n < 130: raise PowerLimitationError("N < 130")`. **MUST** log Spec baseline as: `INFO: Spec baseline N < 30 (Legacy) - Plan override N < 130 active`. **BLOCKED BY T036**.
- [X] T013 [US1] Save cleaned dataset to `data/processed/analysis_data.csv`
- [X] T014 [US1] Add logging for row counts, missing value statistics, and power check results. **MUST** log exact messages using `logging.info()` and `logging.warning()`: `INFO: Rows dropped: {count}`, `INFO: Final N: {n}`, `ERROR: Power limitation. N < 130` (if N < 130), or `WARNING: Low Power (130 <= N < 200)` (if 130 <= N < 200).
- [X] T014b [US1] Implement strict dataset loader in `code/ingest.py` that raises an explicit exception on fetch failure (e.g., 404, timeout) and **DOES NOT** fallback to synthetic/mock data, ensuring "fail loud" behavior per Constitution Principle III (Data Hygiene) and Reproducibility.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Estimation (Priority: P2)

**Goal**: Fit a multiple linear regression model, verify construct validity, and calculate correlations.

**Independent Test**: The model can be tested by running the regression on a synthetic dataset with known coefficients and verifying that the estimated coefficients match the the expected values within a small tolerance.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test in `tests/test_model.py`: Define function `test_pearson_correlation_matches_manual_calculation` to verify correlation logic against hardcoded synthetic values.
- [X] T016 [P] [US2] Unit test in `tests/test_validity.py`: Define function `test_coupling_detection_raises_error_on_identical_instruments` to verify the `validity.py` module raises `MathematicalCouplingError` when `baseline_anxiety` and `anxiety_score` are derived from the **same instrument or time point**. The test must mock metadata indicating identical sources to trigger the error.

### Implementation for User Story 2

- [X] T017 [US2] Implement Pearson/Spearman correlation calculation in `code/model.py` (FR-004)
- [X] T018 [US2] Implement OLS regression fitting in `code/model.py` with formula `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`. Create a reusable function `fit_regression_model`.
- [X] T019a [US2] Implement construct validity check in `code/validity.py` to verify `baseline_anxiety` and `anxiety_score` are distinct constructs. **MUST** check variable metadata, descriptions, or documentation to confirm they were measured via distinct instruments or at distinct time points. MUST raise `MathematicalCouplingError` and HALT if they are derived from the same instrument or time point. If metadata is missing/ambiguous, log WARNING and proceed (do not halt).
- [X] T019b [US2] Implement assumption checks in `code/model.py`:
 1. **Invoke** the distinct construct validation function from `code/validity.py` (T019a) to ensure `baseline_anxiety` and `anxiety_score` are distinct.
 2. Implement Linearity, Homoscedasticity (Breusch-Pagan), Normality (Shapiro-Wilk) checks as separate functions.
 3. Output diagnostic metrics and pass/fail status.
- [X] T019c [US2] Implement Variance Inflation Factor (VIF) detection in `code/model.py`. **MUST** calculate VIF for all predictors and flag the model as unstable if any VIF > 10 (do not halt), as required by Spec Edge Cases.
- [X] T020 [US2] Implement proxy flagging logic in `code/model.py` for `general_anxiety` vs `anticipatory_anxiety` (FR-008). **MUST** explicitly flag the analysis results in the output JSON and final report if 'general_anxiety' was used as a proxy, noting the construct validity limitation.
- [X] T021 [US2] Save regression results to `outputs/regression_results.json` (coefficients, p-values, diagnostics)
- [X] T022 [US2] Save correlation results to `outputs/correlation_results.json`
- [X] T022b [US2] Implement diagnostic plot generation in `code/model.py` to output `outputs/diagnostics_residuals.png` (Residuals vs Fitted) and `outputs/diagnostics_qq.png` (Q-Q Plot). **MUST** include the Breusch-Pagan and Shapiro-Wilk test statistics in the plot titles or legends.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Check and Visualization (Priority: P3)

**Goal**: Generate visualizations and perform unconditional robustness check on high-engagement subset.

**Independent Test**: The visualization can be tested by generating a plot file and verifying the regression line passes through the centroid of the data points. The robustness check is tested by comparing the coefficient sign and significance between the full sample and the high-engagement subset.

### Tests for User Story 3

- [X] T023 [P] [US3] Unit test in `tests/test_robustness.py`: Define function `test_subset_selection_filters_top_25_percentile` to verify the filtering logic for the high-engagement subset.
- [X] T024 [P] [US3] Integration test in `tests/test_viz.py`: Define function `test_plot_file_exists_and_contains_regression_line` to verify the plot file exists and contains the expected regression line.

### Implementation for User Story 3

- [X] T025b [US3] **Implement Plan-compliant unconditional robustness check** in `code/robustness.py`:
 1. **ALWAYS** select the top 25th percentile of `social_media_engagement` (ignore correlation threshold).
 2. Re-fit regression model on this subset.
 3. Compare coefficients/significance with full model.
 4. Log the correlation between engagement and news as a descriptive statistic only.
 5. Overwrite `outputs/robustness_results.json` with `status: "unconditional_run", plan_override: true`, including full results.
 6. **MUST** explicitly state logic: "Always run check regardless of correlation value." **BLOCKED BY T036**.
- [X] T028 [US3] Implement scatter plot generation in `code/viz.py` with regression line and 95% CI (FR-005)
- [X] T029 [US3] Save plot to `outputs/plot.png`
- [X] T030 [US3] Generate `outputs/final_report.md` (Markdown format) summarizing findings, limitations, and associational nature. **MUST** include sections: Executive Summary, Methods, Results (including correlation, regression, and VIF), Robustness Check (reporting full results), Limitations, and Conclusion. **MUST** cite specific JSON outputs (`regression_results.json`, `correlation_results.json`, `robustness_results.json`).
- [X] T029b [US3] Implement robustness visualization in `code/viz.py` to generate `outputs/robustness_comparison.png`. **MUST** overlay the high-engagement subset data points with a different color than the full sample and plot two distinct regression lines (one for full sample, one for subset) with a legend indicating which is which, ensuring visual traceability of the robustness check.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] **Documentation updates** in `README.md` and `docs/`. **MUST** include:
 1. A "Usage" section with the command `python code/main.py`.
 2. A "Data" section describing the expected schema and the verified dataset source (generic schema validation).
 3. Generation of `quickstart.md` with step-by-step instructions for running the pipeline.
- [ ] T032 [P] Code cleanup and refactoring: Remove unused imports, extract helper functions
- [ ] T033a [P] **Create Benchmark Data Generator**: Create `code/benchmark_utils.py` with a function `generate_synthetic_data(n=10000, seed=42)` that produces a DataFrame with the required schema for testing.
- [ ] T033 [P] Performance optimization: Vectorize pandas operations, use chunking for large files. **MUST** ensure the pipeline completes on 10k records (generated via `code/benchmark_utils.py` with seed 42) in < 60 seconds. **MUST** produce a `benchmark.log` file showing the runtime.
- [X] T034 [P] Add specific unit tests for `code/config.py` (seed verification) and `code/robustness.py` (unconditional logic) to ensure coverage of new logic.
- [X] T035 [P] **Run quickstart.md validation**: Execute the steps in `quickstart.md` (generated by T031) and verify that the pipeline runs successfully without manual intervention.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data & Amendments)**: No dependencies - MUST complete first.
- **Setup (Phase 1)**: No dependencies - can start immediately (after Phase 0).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 and validity check (T019a).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model results from US2.

### Within Each User Story

- Tests (if included) MUST be written as scaffolding (empty files with TODOs) before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
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
Task: "Implement listwise deletion and power check in code/clean.py (N < 130 hard stop per T036)"
Task: "Implement strict dataset loader in code/ingest.py with no synthetic fallback"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Availability & Amendments.
2. Complete Phase 1: Setup.
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
4. Complete Phase 3: User Story 1 (including T037 Data Verification).
5. **STOP and VALIDATE**: Test User Story 1 independently.
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!).
3. Add User Story 2 → Test independently → Deploy/Demo.
4. Add User Story 3 → Test independently → Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Amendments) and Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: T036 (Amendment) MUST be completed before T012, T025b, or T037.
- **Critical**: T037 uses generic schema validation loop over candidate datasets (GSS, Pew, YouGov) per ratified amendment T036.
- **Critical**: T012 implements N < 130 hard stop per ratified amendment T036.
- **Critical**: T025b implements Plan unconditional logic.
- **Critical**: T019a handles coupling (hard stop); T019b handles multicollinearity (flag).
- **Critical**: T033a generates benchmark data; T033 runs pipeline on generated data.