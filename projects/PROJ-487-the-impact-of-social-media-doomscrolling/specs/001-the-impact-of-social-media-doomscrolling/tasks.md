# Tasks: The Impact of Social Media "Doomscrolling" on Anticipatory Anxiety

**Input**: Design documents from `/specs/001-doomscrolling-anxiety/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **MANDATORY** based on the "Independent Test" sections in the User Stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw/`, `data/processed/`, `output/reports/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, statsmodels, requests, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Implement data schema validation logic for `raw_news.schema.yaml` (GDELT) in `code/` using the following inline schema definition: `{"type": "object", "required": ["date", "value", "source"], "properties": {"date": {"type": "string", "format": "date"}, "value": {"type": "number"}, "source": {"type": "string"}}}`
- [ ] T004b [P] Implement data schema validation logic for `raw_trends.schema.yaml` (Trends) in `code/` using the following inline schema definition: `{"type": "object", "required": ["date", "value", "source"], "properties": {"date": {"type": "string", "format": "date"}, "value": {"type": "number"}, "source": {"type": "string"}}}`
- [X] T005 [P] Create base configuration manager for environment variables (API keys, date ranges, imputation thresholds) in `code/config.py`
- [~] T006 [P] Setup logging infrastructure to `output/logs/` with error tracking
- [~] T007 Implement deterministic random seed pinning in `code/__init__.py` for reproducibility
- [~] T008 Create sample CSV placeholders in `data/raw/samples/` for CI fallback testing (GDELT and Trends formats)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Retrieve historical time-series data for negative news sentiment (GDELT AVGTONE) and anxiety search trends (Google Trends) from external APIs.

**Independent Test**: Execute the fetch script and verify the output CSV files in `data/raw/` contain non-empty rows for the target date range (-01-01 to 2023-12-31).

### Implementation for User Story 1

- [~] T013 [US1] Implement GDELT fetcher in `code/fetch_data.py` using the `api.gdeltproject.org/api/v2/events` endpoint with query parameters `AVGTONE` metric (range -100 to +100), `EventDateTime` filter for target range, and `geo=US` if applicable; implement retry logic (a limited number of attempts) with exponential backoff and rate-limit handling (wait a brief interval on 429)
- [~] T014 [US1] Implement Google Trends fetcher in `code/fetch_data.py` using the `pytrends` library for keywords ("anticipatory anxiety", "worry about future") with exact parameters: geo=US, hl=en-US, category=0, timeframe=daily; handle API errors gracefully
- [~] T015 [US1] Implement data saving logic to write daily CSVs to `data/raw/gdelt_sentiment.csv` and `data/raw/trends_anxiety.csv`
- [~] T016 [US1] Add validation to ensure date ranges are ISO8601 formatted and values are floats
- [ ] T017 [US1] Add logging for fetch successes, failures, and data completeness warnings

### Tests for User Story 1 (MANDATORY)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation.

- [ ] T009 [P] [US1] Unit test for API retry logic (max 3 attempts) in `tests/unit/test_fetch_retry.py`
- [ ] T010 [P] [US1] Unit test for schema validation of fetched data in `tests/unit/test_fetch_schema.py`
- [ ] T011 [US1] Integration test verifying non-empty CSV generation for GDELT in `tests/integration/test_fetch_gdelt.py`
- [ ] T012 [US1] Integration test verifying non-empty CSV generation for Google Trends in `tests/integration/test_fetch_trends.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Preprocessing (Priority: P2)

**Goal**: Clean, normalize, and align retrieved time-series data to a consistent daily temporal resolution.

**Independent Test**: Run the preprocessing script on raw CSVs and verify the output in `data/processed/` contains no missing values, aligned daily timestamps, and z-scored values.

### Implementation for User Story 2 (Data Prep)

- [ ] T024 [US2] Implement Augmented Dickey-Fuller (ADF) test in `code/preprocess.py` to check stationarity (using `statsmodels.tsa.stattools.adfuller`)
- [ ] T025 [US2] Implement first-order differencing in `code/preprocess.py` if ADF p-value > 0.05
- [ ] T022 [US2] Implement timestamp alignment in `code/preprocess.py` to keep only dates present in both GDELT and Trends series (intersection)
- [ ] T023 [US2] Implement forward-fill imputation in `code/preprocess.py` for gaps; read the `imputation_threshold` from `code/config.py`; exit with error "Gap exceeds imputation threshold: Imputation failed" if gaps exceed the threshold; ensure dataset has no nulls after imputation
- [ ] T027 [US2] Save final aligned dataset to `data/processed/aligned_timeseries.csv`
- [ ] T028 [US2] Add validation to ensure SC-001 (≥95% data completeness) is met; log warning if not

### Tests for User Story 2 (MANDATORY)

> **NOTE**: While tests are written first (TDD), the integration tests (T021, T029a) require the implementation logic (T024, T025) to exist to execute successfully. The list order below reflects the logical dependency of the *test execution* on the *implementation*.

- [ ] T021 [US2] Integration test verifying ADF stationarity check execution in `tests/integration/test_preprocess_stationarity.py`
- [ ] T018 [P] [US2] Unit test for timestamp alignment (intersection logic) in `tests/unit/test_preprocess_align.py`
- [ ] T019 [P] [US2] Unit test for forward-fill imputation (max gap handling) in `tests/unit/test_preprocess_fill.py`
- [ ] T020 [P] [US2] Unit test for z-score normalization (mean=0, std=1) in `tests/unit/test_preprocess_norm.py`
- [ ] T029a [US2] Integration test verifying N < 20 check exits with error "Insufficient data for Granger causality (minimum N < 20)" in `tests/integration/test_preprocess_length.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute correlation coefficients, perform Granger causality tests, and generate visualizations/reports.

**Independent Test**: Execute the analysis script and verify output reports contain correlation values, p-values, Granger results for lags -3, and plot images.

### Tests for User Story 3 (MANDATORY)

- [ ] T029 [P] [US3] Unit test for Pearson/Spearman correlation calculation in `tests/unit/test_analysis_corr.py`
- [ ] T030 [P] [US3] Unit test for Granger causality test logic (multiple lags) in `tests/unit/test_analysis_granger.py`
- [ ] T031 [P] [US3] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_analysis_correction.py`
- [ ] T032 [P] [US3] Integration test verifying report generation (PDF/HTML) in `tests/integration/test_analysis_report.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement Pearson and Spearman correlation calculation with p-values in `code/analysis.py`
- [ ] T034 [US3] Implement Granger causality test for multiple lags (bivariate) in `code/analysis.py`; ensure output explicitly frames results as "associational predictive relationships" using the exact string template: "The analysis indicates an associational predictive relationship..." and verify this framing in the report generation step
- [ ] T035 [US3] Implement sensitivity analysis sweeping lag window ∈ {,, 3} and calculating significance rates in `code/analysis.py`
- [ ] T035a [US3] Generate `output/reports/sensitivity_summary.json` containing a list of objects `{lag: int, p_value: float, is_significant: bool}` (using Holm-Bonferroni adjusted p-values) and the calculated significance rate (count/percentage) for each lag
- [ ] T036 [US3] Apply Holm-Bonferroni correction to Granger p-values to control family-wise error rate, ensuring the adjusted p-values satisfy the effective threshold requirement of SC-002 (p < 0.0167) in `code/analysis.py`; note that Holm-Bonferroni is more powerful than standard Bonferroni and satisfies the spec's intent
- [ ] T038 [US3] Generate visualization plots (lag plots, correlation heatmaps) in `output/reports/` using matplotlib/seaborn
- [ ] T039 [US3] Generate final HTML report `output/reports/final_report.html` containing: table of Granger p-values, methodology, limitations, and significance rate summary
- [ ] T040 [US3] Ensure all analysis runs within CPU-only constraints (no GPU/CUDA) and logs runtime to verify SC-003

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T042 Code cleanup and refactoring in `code/`
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [ ] T044 [P] Additional unit tests for edge cases (e.g., insufficient data for Granger) in `tests/unit/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data being available (fetch)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data being available (preprocess)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Helpers before Services
- Services before Endpoints/Reports
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
# Launch all tests for User Story 1 together:
Task: "Unit test for API retry logic (configurable maximum attempts) in tests/unit/test_fetch_retry.py"
Task: "Unit test for schema validation of fetched data in tests/unit/test_fetch_schema.py"
Task: "Integration test verifying non-empty CSV generation for GDELT in tests/integration/test_fetch_gdelt.py"
Task: "Integration test verifying non-empty CSV generation for Google Trends in tests/integration/test_fetch_trends.py"
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure all data fetch tasks use real APIs or provided sample CSVs; do not fabricate data.
- **Critical**: Ensure all statistical tests use CPU-only libraries (statsmodels, scipy) and respect the -hour CI limit.
- **Note on TDD vs Execution**: While test tasks (e.g., T021, T029a) are listed after implementation tasks to reflect execution feasibility, the *authoring* of these tests should occur before the implementation to ensure TDD principles are followed.
- **Note on Event Dummies**: The Spec defines an observational study with no causal claims. Tasks related to confounder control via event dummies (T026a, T026b, T037) have been removed to strictly align with the Spec's scope.