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
- [X] T001b [P] Create initial files: `README.md`, `code/__init__.py`
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
- [X] T006 [P] Setup logging infrastructure: Create file `logs/pipeline.log`. **CRITICAL**: Implement the logging logic in `code/utils.py` (function `log_api_headers(response)`) that extracts `X-RateLimit-Remaining` and `X-RateLimit-Reset` from the response headers and appends them to `logs/pipeline.log`. This logic MUST be called by every API request function in `code/fetch_data.py`. (FR-009, Constitution Principle VI)
- [X] T007 [P] Implement exponential backoff utility in `code/utils.py`: Function `api_request_with_backoff(url, headers)` with base delay s, multiplier 2.0, max delay 60s, jitter strategy (random 0-50% of delay), a limited number of retries.
- [ ] T008 [P] Create directory structure: `data/raw/`, `data/processed/`, `data/spot_check/`, `artifacts/`, `tests/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Fetch PR metadata, classify AI contributions, calculate turnaround times, and validate data quality.

**Independent Test**: Can be fully tested by verifying that the script successfully fetches data from the GitHub API, correctly identifies AI vs. human contributions via commit messages and specific labels, and outputs a CSV file with calculated turnaround times.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for classification logic (keywords/labels) in `tests/unit/test_classifier.py`
- [X] T010 [P] [US1] Unit test for turnaround time calculation (wall-clock hours) in `tests/unit/test_time_calc.py`
- [ ] T011 [P] [US1] Contract test for `pull_request.schema.yaml` validation in `tests/contract/test_schema_validation.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Fetch a representative set of top Python and JavaScript repositories by star count using GitHub API endpoint: `search/repositories?q=language:Python+stars:>10000&sort=stars&order=desc` (and JS equivalent). Save output to `data/raw/repos.json` as a list of objects with `name` and `stars` (FR-001)
- [ ] T012b [US1] For each repo from T012a, fetch ALL PRs and iterate through the FULL list of commits for *each* PR. **MUST handle pagination via the GitHub API 'Link' header to ensure ALL commits are fetched**, extracting all commit messages for classification. Do NOT limit to 10 commits (FR-001).
- [X] T013 [US1] Implement logic in `code/fetch_data.py` to exclude PRs with missing `merged_at` timestamps and log exclusion counts (FR-010)
- [X] T014 [US1] Implement logic in `code/fetch_data.py` to skip repos with < 50 PRs after filtering and log warnings; **explicitly write the list of skipped repository names to `data/processed/excluded_repos.txt`** (Edge Case: Repo Size < 50)
- [X] T015 [US1] Implement classification logic in `code/fetch_data.py` to label PRs as AI-assisted or non-AI-labeled based on commit messages ("copilot", "ai-generated") and labels ("ai-generated", "copilot-assisted", "llm-code") (FR-002)
- [X] T016 [US1] Implement turnaround time calculation in `code/fetch_data.py` as total calendar hours (merged_at - created_at) (FR-003)
- [ ] T017 [US1] Calculate and log median star count and median number of contributors for selected repositories; Save to `data/processed/repo_metadata.json` (FR-013)
- [ ] T018a [US1] Save raw data to `data/raw/pr_data.json` with schema validation (FR-001)
- [ ] T018b [US1] Save processed data to `data/processed/pr_turnaround.csv` with schema validation (FR-001)
- [ ] T018c [US1] Calculate overall data quality success rate (processed/total PRs). If < 95%, raise `DataQualityError` with message "Data quality threshold not met: X%" and halt pipeline. Otherwise, log success (SC-003)
- [ ] T019a [US1] Implement `code/validate_spot_check.py` to generate a CSV of non-AI-labeled PR IDs (stratified by repo and PR size) for manual review. Save to `data/spot_check/sample_list.csv` (FR-011)
- [ ] T019b [US1] **Manual Step**: Human annotator reviews the sample from T019a and fills in `data/spot_check/annotations.csv` with the true AI/human classification. **Pipeline HALTS here until `data/spot_check/annotations.csv` is manually uploaded to the repository.** (FR-011)
- [ ] T019c [US1] Implement `code/validate_spot_check.py` to ingest `data/spot_check/annotations.csv` (produced by T019b), calculate the false-negative rate, and save to `data/spot_check/validation_report.csv`. **Pipeline RESUMES here.** (FR-011)
- [X] T020 [US1] Save spot-check results to `data/spot_check/validation_report.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Perform descriptive statistics, IQR outlier handling for visualization, and execute Stratified Mann-Whitney U test.

**Independent Test**: Can be tested by running the analysis on a sample dataset and verifying that the Stratified Mann-Whitney U test produces statistically valid results with appropriate p-values and effect size calculations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for IQR outlier calculation in `tests/unit/test_iqr.py`
- [X] T022 [P] [US2] Unit test for Stratified Mann-Whitney U test execution in `tests/unit/test_mwu.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/analyze.py` to calculate descriptive statistics (mean, median, SD, quartiles) for AI and non-AI groups. **Input**: Must exclude data from repositories listed in `data/processed/excluded_repos.txt` (from T014). **Prerequisite**: Must consume `data/processed/excluded_repos.txt` (FR-004, Edge Case).
- [ ] T023b [US2] Implement `code/analyze.py` to calculate distribution characteristics: skewness, kurtosis, and Shapiro-Wilk p-values for both AI and non-AI groups. Save to `data/processed/distribution_stats.json` (SC-002, Plan Phase 1)
- [X] T024 [US2] Implement IQR outlier calculation in `code/analyze.py` (Q1 - 1.5×IQR, Q3 + 1.5×IQR) calculated separately per group. **Note**: Outliers are excluded ONLY for visualization (T031) and sensitivity analysis (T028), NOT for the primary hypothesis test (Plan Phase 1)
- [X] T024c [US2] Implement logic to create a *copy* of the dataset with outliers removed for visualization purposes only. Save to `data/processed/pr_turnaround_cleaned.csv`. **CRITICAL**: This file is NOT to be used for the primary test in T026 (FR-005)
- [X] T025 [US2] Log the count of outliers identified per group and the count of outliers removed in T024c (FR-005)
- [X] T027a [US2] Implement power check in `code/analyze.py`: if AI group count < 30, raise `SampleSizeError` with message "Sample size too small: AI group < 30" to abort pipeline (Plan Phase 1)
- [X] T026 [US2] Execute **Stratified Mann-Whitney U test** in `code/analyze.py`. **Input**: Use the **full dataset** from `data/processed/pr_turnaround.csv` (NOT the cleaned file). **Method**: Stratify by binning `lines_changed` (additions + deletions) into quartiles and `total_prs_by_author` into tertiles. Calculate MWU within each stratum and aggregate p-values using **Fisher's method**. Return U statistic, p-value, and effect size (r) (FR-006, Plan Phase 1)
- [ ] T026b [US2] Compare the calculated p-value against the α=0.05 threshold. Log conclusion: "Significant difference found" if p < 0.05, else "No significant difference" (SC-004)
- [X] T028 [US2] Implement sensitivity analysis in `code/analyze.py`. **Algorithm**: Perform a Monte Carlo simulation: randomly flip X% of non-AI labels to AI (where X = false_negative_rate from T020) using a fixed seed. Re-calculate the MWU test on the simulated dataset. Repeat the simulation multiple times and report the distribution of p-values. (mean, median, 95% CI). This addresses FR-006 and Plan Phase 1 sensitivity goals (FR-006, Plan Phase 1)
- [ ] T029 [US2] Save statistical results to `data/processed/statistical_results.json`, explicitly including keys: `u_statistic`, `p_value`, `effect_size`, `sample_sizes`, `median_stars`, `median_contributors`, `distribution_stats` (FR-013, FR-006, SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality boxplot and assemble final report with conditional limitation logic.

**Independent Test**: Can be tested by verifying that the script generates a clear, labeled boxplot showing both distributions and successfully saves it to the designated artifacts directory.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for boxplot generation parameters (DPI, labels) in `tests/unit/test_visualize.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/visualize.py` to generate boxplot comparing turnaround time distributions for AI and non-AI groups. **Use outlier-excluded data for whiskers only** (FR-007)
- [ ] T032 [US3] Ensure boxplot axes are labeled (turnaround time in hours vs. PR type) and whiskers use IQR bounds (FR-007)
- [ ] T033 [US3] Save visualization to `artifacts/boxplot.png` with ≥300 DPI resolution (FR-008, SC-005)
- [ ] T036a [US3] Verify `artifacts/boxplot.png` exists and calculate the correct relative path for the report. If missing, raise an error.
- [X] T034 [US3] Implement `code/report.py` to assemble final report including boxplot image path, statistical test results, key descriptive statistics, and validation summary (FR-008, SC-003)
- [X] T034b [US3] Load spot-check results from `data/spot_check/validation_report.csv` (T020). Calculate `false_negative_rate = count(misclassified_AI) / total_sample_size` (FR-011, FR-012)
- [X] T035 [US3] Implement conditional logic in `code/report.py`: **Prerequisite: T020 completion**. If `false_negative_rate` (from T034b) > 10%, inject limitation statement with text: "Limitation: False-negative rate exceeds 10% threshold, indicating potential misclassification in non-AI group." (FR-012)
- [~] T036b [US3] Render the final report to `artifacts/final_report.md`. **Template**: Use the following Markdown structure exactly:
```markdown
# Code Generation Impact Report

## Statistical Results
- U Statistic: {u_stat}
- P-Value: {p_value}
- Effect Size (r): {effect_size}
- Sample Sizes: AI={n_ai}, Non-AI={n_non_ai}

## Visualization
![Boxplot](artifacts/boxplot.png)

## Descriptive Statistics
{descriptive_stats_text}

## Validation Summary
{validation_summary_text}

{limitation_statement}
```
**Logic**: Replace placeholders with values from T029 and T023. If `false_negative_rate` > 10%, set `{limitation_statement}` to the exact string from T035; otherwise set it to "No limitations detected." (FR-008, SC-005, FR-012)
- [~] T037 [US3] Update `state/projects/PROJ-312-.../state.yaml` with artifact hashes and `updated_at` timestamp (Constitution Principle V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T038 [P] Documentation updates in `projects/PROJ-312-evaluating-the-impact-of-code-generation/README.md`
- [~] T039a Run ruff --fix to ensure zero linting errors
- [~] T039b Run black --check to ensure zero formatting errors
- [X] T040a [P] Add unit tests for edge cases in `fetch_data.py` (e.g., empty response, rate limit) in `tests/unit/test_fetch_data_edge_cases.py`
- [X] T040b [P] Add unit tests for edge cases in `analyze.py` (e.g., empty group, NaN values) in `tests/unit/test_analyze_edge_cases.py`
- [X] T040c [P] Add unit tests for edge cases in `visualize.py` (e.g., zero variance) in `tests/unit/test_visualize_edge_cases.py`
- [~] T041 Run quickstart.md validation: Execute all commands in `quickstart.md`, verify exit code 0 for each, and confirm expected output files exist
- [~] T042 Verify all CSV/JSON outputs match schema contracts in `contracts/`

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
- **T012b** depends on T012a (Repo list) - **NOT Parallel**
- **T006** (Logging logic) must be implemented before T012a/T012b (API calls)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T006 which must precede API calls
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
- **Methodology Note**: Per Spec FR-005, outliers are excluded from the *visualization* dataset but the primary test (T026) uses the **full dataset** for robustness.
- **Plan Alignment**: T026 implements the Stratified Mann-Whitney U Test as mandated by the Plan, controlling for PR size and author activity.
- **Spot Check Flow**: The pipeline halts at T019b for human input. T019c resumes the pipeline after the file is uploaded.
- **Sensitivity Analysis**: T028 uses a Monte Carlo simulation to adjust for false-negative rates, replacing the invalid formula.