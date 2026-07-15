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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`
- [ ] T001b [P] Create source structure: `projects/PROJ-540-the-influence-of-social-media-doomscroll/` with `__init__.py` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (e.g., `pandas==2.0.3`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `pyyaml==6.0.1`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools
- [X] T004 [P] Implement environment configuration management for dataset URLs and random seeds (`code/config.py`)
- [ ] T004b [P] Implement random seed verification and logging in `code/config.py` (or `code/utils.py`) to ensure seeds are actively applied and logged at runtime, satisfying Constitution Principle I (Reproducibility). Log a warning if a seed is not set.
- [X] T005 [P] Setup error handling infrastructure for custom exceptions (`PowerLimitationError`, `MathematicalCouplingError`) in `code/exceptions.py`
- [X] T006 [P] Create base data models/entities (`SurveyResponse`, `RegressionModel`) in `code/models.py`
- [ ] T007 [P] Configure logging infrastructure to `outputs/analysis.log`
- [X] T019a [P] [Foundational] Implement construct validity check in `code/validity.py` to verify `baseline_anxiety` and `anxiety_score` are distinct constructs; MUST raise `MathematicalCouplingError` and HALT if coupling detected (Per Plan Phase 1.5). This function must be callable by US2 tasks.

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

- [X] T010 [US1] Implement data ingestion script `code/ingest.py` to download data from verified URL (e.g., GSS/Pew) and parse to `data/raw/`
- [X] T011 [US1] Implement schema validation in `code/ingest.py` to ensure columns `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender` exist
- [X] T012 [US1] Implement listwise deletion in `code/clean.py` for missing predictor/outcome values. **MUST enforce Spec FR-002**: HALT with `PowerLimitationError` if resulting N < 30. If 30 <= N < 100, log 'Low Power' warning and proceed. (Note: The Plan suggests N < 130 for higher power, but the Spec requires N < 30; implement Spec logic and log the Plan's stricter guideline as a comment).
- [ ] T013 [US1] Save cleaned dataset to `data/processed/analysis_data.csv`
- [~] T014 [US1] Add logging for row counts, missing value statistics, and power check results

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Estimation (Priority: P2)

**Goal**: Fit a multiple linear regression model, verify construct validity, and calculate correlations.

**Independent Test**: The model can be tested by running the regression on a synthetic dataset with known coefficients and verifying that the estimated coefficients match the expected values within a small tolerance.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test in `tests/test_model.py`: Define function `test_pearson_correlation_matches_manual_calculation` to verify correlation logic against hardcoded synthetic values.
- [X] T016 [P] [US2] Unit test in `tests/test_validity.py`: Define function `test_coupling_detection_raises_error_on_identical_variables` to verify the `validity.py` module raises `MathematicalCouplingError` when inputs are identical.

### Implementation for User Story 2

- [X] T017 [US2] Implement Pearson/Spearman correlation calculation in `code/model.py` (FR-004)
- [X] T018 [US2] Implement OLS regression fitting in `code/model.py` with formula `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`. Create a reusable function `fit_regression_model`.
- [X] T019 [US2] Implement assumption checks in `code/model.py`:
 1. **Invoke** the distinct construct validation function from `code/validity.py` (T019a) to ensure `baseline_anxiety` and `anxiety_score` are distinct.
 2. Implement Linearity, Homoscedasticity (Breusch-Pagan), Normality (Shapiro-Wilk), and VIF checks as separate functions.
 3. Output diagnostic metrics and pass/fail status.
- [~] T020 [US2] Implement proxy flagging logic for `general_anxiety` vs `anticipatory_anxiety` (FR-008)
- [ ] T021 [US2] Save regression results to `outputs/regression_results.json` (coefficients, p-values, diagnostics)
- [ ] T022 [US2] Save correlation results to `outputs/correlation_results.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Check and Visualization (Priority: P3)

**Goal**: Generate visualizations and perform conditional robustness check on high-engagement subset.

**Independent Test**: The visualization can be tested by generating a plot file and verifying the regression line passes through the centroid of the data points. The robustness check is tested by comparing the coefficient sign and significance between the full sample and the high-engagement subset.

### Tests for User Story 3

- [X] T023 [P] [US3] Unit test in `tests/test_robustness.py`: Define function `test_subset_selection_filters_top_25_percentile` to verify the filtering logic for the high-engagement subset.
- [X] T024 [P] [US3] Integration test in `tests/test_viz.py`: Define function `test_plot_file_exists_and_contains_regression_line` to verify the plot file exists and contains the expected regression line.

### Implementation for User Story 3

- [X] T025 [US3] Implement robustness check logic in `code/robustness.py`:
 1. Calculate correlation between `social_media_engagement` and `news_exposure_freq`.
 2. **IF** correlation > 0.3, select the top 25th percentile of `social_media_engagement` from `data/processed/analysis_data.csv`.
 3. **IF** correlation <= 0.3, skip the check and log a warning (Per Spec FR-006).
- [~] T026 [US3] Re-fit regression on the high-engagement subset defined in T025 by **calling** the `fit_regression_model` function created in T018 (do not duplicate code). Compare coefficients/significance with full model.
- [ ] T027 [US3] Save robustness results to `outputs/robustness_results.json`
- [X] T028 [US3] Implement scatter plot generation in `code/viz.py` with regression line and 95% CI (FR-005)
- [ ] T029 [US3] Save plot to `outputs/plot.png`
- [ ] T030 [US3] Generate `outputs/final_report.md` summarizing findings, limitations, and associational nature

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `README.md` and `docs/`
- [ ] T032 [P] Code cleanup and refactoring: Remove unused imports, extract helper functions
- [ ] T033 [P] Performance optimization: Vectorize pandas operations, use chunking for large files (ensure < 60s on 10k records)
- [ ] T034 [P] Add specific unit tests for `code/config.py` (seed verification) and `code/robustness.py` (conditional logic) to ensure coverage of new logic.
- [ ] T035 [P] Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 and validity check (T019a)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model results from US2

### Within Each User Story

- Tests (if included) MUST be written as scaffolding (empty files with TODOs) before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all scaffolding for User Story 1 together:
Task: "Unit test scaffolding in tests/test_ingest.py: Define class TestIngestion and function test_schema_validation_raises_error_on_missing_column"
Task: "Unit test scaffolding in tests/test_clean.py: Define class TestCleaning and function test_listwise_deletion_halts_on_low_power"

# Launch all implementation for User Story 1 together:
Task: "Implement data ingestion script code/ingest.py"
Task: "Implement schema validation in code/ingest.py"
Task: "Implement listwise deletion and power check in code/clean.py (Spec N < 30 hard stop)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Scaffolding first)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence