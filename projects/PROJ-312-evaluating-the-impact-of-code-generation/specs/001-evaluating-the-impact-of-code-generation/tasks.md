# Tasks: Evaluating the Impact of Code Generation on Code Review Turnaround Time

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-code-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

- [ ] T001a [P] Create directory structure: `projects/PROJ-312-evaluating-the-impact-of-code-generation/`, `code/`, `data/`, `tests/`, `contracts/`, `artifacts/`, `state/`
- [ ] T001b [P] Create initial files: `README.md`, `code/__init__.py`
- [ ] T002 [P] Initialize Python 3.11 project: Create file `projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt` containing pinned versions (requests, pandas, scipy, matplotlib, pyyaml, tqdm, statsmodels), then run `pip install -r projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt`
- [ ] T003 [P] Configure linting and formatting: Create file `projects/PROJ-312-evaluating-the-impact-of-code-generation/pyproject.toml` containing:
 ```toml
 [tool.ruff]
 max-line-length = 88
 select = ["E", "F", "W"]

 [tool.black]
 line-length = 88
 ```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create local schema definitions in `contracts/` with exact content:
 - `pull_request.schema.yaml`:
 ```yaml
 type: object
 properties:
 pr_id: {type: string}
 repo_name: {type: string}
 created_at: {type: string}
 merged_at: {type: string}
 labels: {type: array}
 commit_messages: {type: array}
 turnaround_hours: {type: number}
 required: [pr_id, repo_name, turnaround_hours]
 ```
 - `repo_metadata.schema.yaml`:
 ```yaml
 type: object
 properties:
 repo_name: {type: string}
 stars: {type: number}
 contributors: {type: number}
 required: [repo_name, stars]
 ```
 - `statistical_result.schema.yaml`:
 ```yaml
 type: object
 properties:
 test_type: {type: string}
 u_statistic: {type: number}
 p_value: {type: number}
 effect_size: {type: number}
 sample_sizes: {type: object}
 required: [test_type, u_statistic, p_value]
 ```
- [X] T005 [P] Implement schema validation utility in `code/utils.py`: Function `validate_json_schema(data, schema_path)` that returns True/False and logs errors
- [~] T006 [P] Setup logging infrastructure: Create file `logs/pipeline.log` with JSON formatting. Capture rate-limit headers `X-RateLimit-Remaining` and `X-RateLimit-Reset` on every API call.
- [X] T007 [P] Implement exponential backoff utility in `code/utils.py`: Function `api_request_with_backoff(url, headers)` with base delay s, multiplier 2.0, max delay 60s, jitter strategy (random 0-50% of delay), a limited number of retries.
- [~] T008 [P] Create directory structure: `data/raw/`, `data/processed/`, `data/spot_check/`, `artifacts/`, `tests/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Fetch PR metadata, classify AI contributions, calculate turnaround times, and validate data quality.

**Independent Test**: Can be fully tested by verifying that the script successfully fetches data from the GitHub API, correctly identifies AI vs. human contributions via commit messages and specific labels, and outputs a CSV file with calculated turnaround times.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for classification logic (keywords/labels) in `tests/unit/test_classifier.py`
- [~] T010 [P] [US1] Unit test for turnaround time calculation (wall-clock hours) in `tests/unit/test_time_calc.py`
- [~] T011 [P] [US1] Contract test for `pull_request.schema.yaml` validation in `tests/contract/test_schema_validation.py`

### Implementation for User Story 1

- [ ] T012a [US1] Fetch a representative set of top Python and JavaScript repositories by star count using GitHub API endpoint: `search/repositories?q=language:Python+stars:>10000&sort=stars&order=desc` (and JS equivalent). Save output to `data/raw/repos.json` as a list of objects with `name` and `stars` (FR-001)
- [~] T012b [US1] For each repo from T012a, fetch all PRs and iterate through the list of commits for *each* PR to extract commit messages for classification (FR-001, Edge Case)
- [X] T013 [US1] Implement logic in `code/fetch_data.py` to exclude PRs with missing `merged_at` timestamps and log exclusion counts (FR-010)
- [X] T014 [US1] Implement logic in `code/fetch_data.py` to skip repos with < 50 PRs after filtering and log warnings; ensure these repos are tracked for exclusion from final analysis (Edge Case)
- [X] T015 [US1] Implement classification logic in `code/fetch_data.py` to label PRs as AI-assisted or non-AI-labeled based on commit messages ("copilot", "ai-generated") and labels ("ai-generated", "copilot-assisted", "llm-code") (FR-002)
- [X] T016 [US1] Implement turnaround time calculation in `code/fetch_data.py` as total calendar hours (merged_at - created_at) (FR-003)
- [~] T017 [US1] Calculate and log median star count and median number of contributors for selected repositories (FR-013)
- [~] T018 [US1] Save raw data to `data/raw/` and processed data to `data/processed/` with schema validation (FR-001)
- [~] T018b [US1] Calculate overall data quality success rate (processed/total PRs). If < 95%, raise `DataQualityError` with message "Data quality threshold not met: X%" and halt pipeline. Otherwise, log success (SC-003)
- [X] T019 [US1] Implement `code/validate_spot_check.py` to perform manual spot-check of a *stratified random sample* (n=50) of non-AI-labeled PRs. Stratification must be based on repository and PR size (number of files changed). Estimate false-negative rate (FR-011)
- [ ] T020 [US1] Save spot-check results to `data/spot_check/validation_report.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Perform descriptive statistics, IQR outlier handling for visualization, and execute Mann-Whitney U test.

**Independent Test**: Can be tested by running the analysis on a sample dataset and verifying that the Mann-Whitney U test produces statistically valid results with appropriate p-values and effect size calculations, and that outliers are removed per group for visualization.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for IQR outlier calculation in `tests/unit/test_iqr.py`
- [ ] T022 [P] [US2] Unit test for Mann-Whitney U test execution in `tests/unit/test_mwu.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/analyze.py` to calculate descriptive statistics (mean, median, SD, quartiles) for AI and non-AI groups. **Input**: Must exclude data from repositories skipped in T014 (FR-004, Edge Case)
- [ ] T023b [US2] Calculate and log distribution characteristics (skewness, kurtosis) for both groups to validate against SC-002 (distribution characteristics)
- [ ] T023c [US2] Calculate and log Shapiro-Wilk test p-value for normality check for both groups to validate distribution shape (SC-002)
- [ ] T024 [US2] Implement IQR outlier calculation in `code/analyze.py` (Q1 - 1.5×IQR, Q3 + 1.5×IQR) calculated separately per group. **Note**: Outliers are excluded ONLY for visualization (T031) and sensitivity analysis (T028), NOT for the primary hypothesis test (Plan Phase 1)
- [ ] T024b [US2] Save outlier indices for visualization and sensitivity analysis. **Do NOT exclude outliers from the primary dataset used in T026** (FR-005, Plan Phase 1)
- [ ] T025 [US2] Log the count of outliers identified per group (FR-005)
- [ ] T026 [US2] Execute **Stratified** Mann-Whitney U test in `code/analyze.py` comparing AI vs. non-AI groups using the **FULL dataset** (from T018, not cleaned). Stratify by PR size and author activity (Plan Phase 1, FR-006). Return U statistic, p-value, and effect size (r)
- [ ] T026b [US2] Compare the calculated p-value against the α=0.05 threshold. Log conclusion: "Significant difference found" if p < 0.05, else "No significant difference". If p >= 0.05 and power check fails, raise `SignificanceError` (SC-004)
- [ ] T027a [US2] Implement power check in `code/analyze.py`: if AI group count < 30, flag for abort (Plan Phase 1)
- [ ] T027b [US2] If T027a condition is met, define `class SampleSizeError(Exception): pass` and raise `SampleSizeError` with message "Sample size too small: AI group < 30" to halt pipeline execution (Plan Phase 1)
- [ ] T028 [US2] Implement sensitivity analysis in `code/analyze.py` to apply bias-correction using spot-check error rates from T020. **Load false_negative_rate from data/spot_check/validation_report.csv**. Formula: `adjusted_p_value = p_value * (1 + false_negative_rate)`. This is a planned sensitivity check per Plan Phase 1 (FR-006, Plan Phase 1)
- [ ] T029 [US2] Save statistical results to `data/processed/statistical_results.json`, explicitly including median star count, median contributors, U statistic, p-value, effect size, and sample sizes (FR-013, FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality boxplot and assemble final report with conditional limitation logic.

**Independent Test**: Can be tested by verifying that the script generates a clear, labeled boxplot showing both distributions and successfully saves it to the designated artifacts directory.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for boxplot generation parameters (DPI, labels) in `tests/unit/test_visualize.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/visualize.py` to generate boxplot comparing turnaround time distributions for AI and non-AI groups. **Use outlier-excluded data for whiskers only** (FR-007)
- [ ] T032 [US3] Ensure boxplot axes are labeled (turnaround time in hours vs. PR type) and whiskers use IQR bounds (FR-007)
- [ ] T033 [US3] Save visualization to `artifacts/boxplot.png` with ≥300 DPI resolution (FR-008, SC-005)
- [ ] T034 [US3] Implement `code/report.py` to assemble final report including boxplot, statistical test results, key descriptive statistics, and validation summary (FR-008, SC-003)
- [ ] T034b [US3] Load spot-check results from `data/spot_check/validation_report.csv` (T020). Calculate `false_negative_rate = count(misclassified_AI) / total_sample_size` (FR-011, FR-012)
- [ ] T035 [US3] Implement conditional logic in `code/report.py`: **Prerequisite: T020 completion**. If `false_negative_rate` (from T034b) > 10%, inject limitation statement with text: "Limitation: False-negative rate exceeds 10% threshold, indicating potential misclassification in non-AI group." (FR-012)
- [ ] T036 [US3] Save final report to `artifacts/final_report.md`
- [ ] T037 [US3] Update `state/projects/PROJ-312-.../state.yaml` with artifact hashes and `updated_at` timestamp (Constitution Principle V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `projects/PROJ-312-evaluating-the-impact-of-code-generation/README.md`
- [ ] T039a Run ruff --fix to ensure zero linting errors
- [ ] T039b Run black --check to ensure zero formatting errors
- [ ] T040a [P] Add unit tests for edge cases in `fetch_data.py` (e.g., empty response, rate limit) in `tests/unit/test_fetch_data_edge_cases.py`
- [ ] T040b [P] Add unit tests for edge cases in `analyze.py` (e.g., empty group, NaN values) in `tests/unit/test_analyze_edge_cases.py`
- [ ] T040c [P] Add unit tests for edge cases in `visualize.py` (e.g., zero variance) in `tests/unit/test_visualize_edge_cases.py`
- [ ] T041 Run quickstart.md validation: Execute all commands in `quickstart.md`, verify exit code 0 for each, and confirm expected output files exist
- [ ] T042 Verify all CSV/JSON outputs match schema contracts in `contracts/`

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Produces `data/processed/` required by US2/US3.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and US1 data availability. Depends on `data/processed/` from T018.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and US2 data availability. Depends on `data/processed/statistical_results.json` from T029 and `data/spot_check/validation_report.csv` from T020. **Explicitly depends on T020 completion.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetching (T012a, T012b) before classification (T015) and calculation (T016)
- Classification before saving processed data (T018)
- Spot-check (T019) can run in parallel with main analysis but results needed for Report (T035)

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for classification logic (keywords/labels) in tests/unit/test_classifier.py"
Task: "Unit test for turnaround time calculation (wall-clock hours) in tests/unit/test_time_calc.py"

# Launch data fetching and spot check in parallel (once foundation is ready):
Task: "Implement code/fetch_data.py to fetch top 10 Python/JS repos..."
Task: "Implement code/validate_spot_check.py to perform manual spot-check..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Acquisition & Spot Check)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data quality, classification accuracy, schema compliance)
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
 - Developer A: User Story 1 (Data Fetch & Spot Check)
 - Developer B: User Story 2 (Statistical Analysis) - *Note: Depends on US1 data*
 - Developer C: User Story 3 (Visualization & Reporting) - *Note: Depends on US1 & US2 data*
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
- **Critical Constraint**: All data acquisition must use real GitHub API data; no synthetic data generation.
- **Critical Constraint**: All statistical tests must run on CPU-only free-tier runners; no GPU dependencies.
- **Methodology Note**: Per Plan Phase 1, the primary Mann-Whitney U test uses the FULL dataset. Outlier removal (IQR) is applied only for visualization (boxplot whiskers) and sensitivity analysis, not the primary hypothesis test.