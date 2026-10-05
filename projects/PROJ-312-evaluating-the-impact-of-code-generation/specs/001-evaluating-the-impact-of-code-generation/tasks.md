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
- [ ] T002a [P] Create file `projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt` containing pinned versions (requests, pandas, scipy, matplotlib, pyyaml, tqdm, statsmodels). **Pinning Strategy**: Use exact `==` constraints (e.g., `pandas==2.0.3`) derived from the project's `pylock` or `pip freeze` output to ensure deterministic execution. (FR-001, Constitution Principle I)
- [ ] T002b [P] Verify environment: Run `pip install -r projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt` and confirm all imports succeed.
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

- [ ] T004a [P] Create local schema definition: `contracts/pull_request.schema.yaml` with exact content:
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
- [ ] T004b [P] Create local schema definition: `contracts/repo_metadata.schema.yaml` with exact content:
 ```yaml
 type: object
 properties:
 repo_name: {type: string}
 stars: {type: number}
 contributors: {type: number}
 required: [repo_name, stars]
 ```
- [ ] T004c [P] Create local schema definition: `contracts/statistical_result.schema.yaml` with exact content:
 ```yaml
 type: object
 properties:
 test_type: {type: string}
 u_statistic: {type: number}
 p_value: {type: number}
 effect_size: {type: number}
 sample_sizes: {object}
 required: [test_type, u_statistic, p_value]
 ```
- [X] T005 [P] Implement schema validation utility in `code/utils.py`: Function `validate_json_schema(data, schema_path)` that returns True/False and logs errors
- [X] T006a [P] [US1] Create file `logs/pipeline.log` (empty) to initialize logging infrastructure.
- [X] T006b [P] [US1] Implement logging function in `code/utils.py`: Function `log_api_headers(response)` that extracts `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and the `retry_count` from the response context and appends them to `logs/pipeline.log`.
- [X] T006c [!] [US1] Integrate logging: Ensure `log_api_headers` is called by every API request function in `code/fetch_data.py`. (FR-009, Constitution Principle VI). **Dependency**: This task depends on T005 (Validation utility) being complete; ensure T005 is finished before starting T006c. **NOT Parallel**: Must complete before T012a/T012b.
- [X] T007 [P] Implement exponential backoff utility in `code/utils.py`: Function `api_request_with_backoff(url, headers)` with **exact parameters**: `base_delay=1s`, `multiplier=2`, `max_delay=60s`, `max_retries=3`, and jitter strategy (random non-negative percentage of delay). (FR-009)
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
- [X] T011 [P] [US1] Contract test for `pull_request.schema.yaml` validation in `tests/contract/test_schema_validation.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Fetch a representative set of top Python and JavaScript repositories by star count using GitHub API endpoints: `search/repositories?q=language:Python+stars:>10000&sort=stars&order=desc` and `search/repositories?q=language:JavaScript+stars:>10000&sort=stars&order=desc`. **Target**: Top 20 Python and Top 20 JavaScript repositories. Save output to `data/raw/repos.json` as a list of objects with `name` and `stars` (FR-001)
- [ ] T012b [US1] For each repo from T012a, fetch PRs and iterate through commits. **Goal**: Fetch ALL PRs for each repo in the representative set. **Stop Condition**: Stop after fetching **50 pages** per repo OR a bounded execution time (a maximum duration of approximately half an hour). **MUST handle pagination via the GitHub API 'Link' header** to fetch as many PRs as possible within the stop condition, extracting commit messages for classification. **Partial Data Handling**: If the stop condition triggers, save partial data to `data/processed/pr_turnaround_partial.csv`, log the repository name to `data/processed/truncated_repos.txt`, and include a note in the final report that the dataset may be incomplete for these repos, acknowledging a potential limitation to FR-001. (FR-001, Plan Constraints, Executability)
- [X] T013 [US1] Implement logic in `code/fetch_data.py` to exclude PRs with missing `merged_at` timestamps and log exclusion counts (FR-010)
- [ ] T014 [US1] Implement logic in `code/fetch_data.py` to skip repos with fewer than **50** PRs after filtering and log warnings; **explicitly write the list of skipped repository names to `data/processed/excluded_repos.txt`** (Edge Case: Repo Size < 50). **Configurable**: The threshold MUST be read from the `MIN_PR_THRESHOLD` constant in `code/utils.py` (defined as 50 in this task), not hardcoded. (Edge Case, Executability)
- [X] T015 [US1] Implement classification logic in `code/fetch_data.py` to label PRs as AI-assisted or non-AI-labeled based on commit messages ("copilot", "ai-generated") and labels ("ai-generated", "copilot-assisted", "llm-code") (FR-002)
- [X] T016 [US1] Implement turnaround time calculation in `code/fetch_data.py` as total calendar hours (merged_at - created_at) (FR-003)
- [X] T017 [US1] Calculate and log median star count and median number of contributors for selected repositories; Save to `data/processed/repo_metadata.json` (FR-013)
- [X] T018a [US1] Save raw data to `data/raw/pr_data.json` with schema validation (FR-001)
- [X] T018b [US1] Save processed data to `data/processed/pr_turnaround.csv` with schema validation (FR-001)
- [X] T018c [US1] Calculate overall data quality success rate (processed/total PRs). If < 95%, log a warning, save a detailed error log to `data/processed/data_quality_warning.log`, and **save a quality status artifact to `data/processed/quality_status.json`** with `status: "warning"` and `rate: <value>`. **Do NOT halt the pipeline**; the final report will handle limitations via T035 (FR-012) based on false-negative rate, not quality rate. (SC-003, Edge Cases)
- [X] T019a [US1] Implement `code/validate_spot_check.py` to generate a CSV of non-AI-labeled PR IDs (stratified by repo and PR size) for manual review. Save to `data/spot_check/sample_list.csv` (FR-011)
- [ ] T019b [US1] Create Annotation Template: Implement `code/validate_spot_check.py` to generate a blank CSV template `data/spot_check/annotation_template.csv` with columns `pr_id`, `is_ai_assisted` (human label). **Include a header comment in the file with explicit instructions for the human annotator: "Open this file in a text editor. For each PR ID, manually review the PR on GitHub. If you see AI-generated code (e.g., Copilot suggestions), set is_ai_assisted to 1, otherwise 0. Save the file as annotations.csv."** **EXTERNAL PROCESS**: This task generates the template. The actual review is a manual human step not performed by the code. (FR-011)
- [ ] T019c [US1] Wait for Annotations: Implement `code/validate_spot_check.py` to check for the existence of `data/spot_check/annotations.csv`. **If missing**, log a warning and proceed to T019d. **If present**, validate the schema and proceed to T019e. This task does NOT generate the file; it only waits for the human-generated file. (FR-011, Constitution Principle I)
- [ ] T019d [US1] Handle Missing Real Data: If `data/spot_check/annotations.csv` is missing after the check in T019c, log a CRITICAL warning, flag the validation status as 'UNVALIDATED' in the final report, and **proceed with the analysis using the heuristic-only classification**. (FR-011, Constitution Principle I)
- [ ] T019e [US1] Ingest Real Annotations: If `data/spot_check/annotations.csv` exists (from T019c), ingest it, calculate the false-negative rate, and save to `data/spot_check/validation_report.csv`. **Strict Requirement**: If `annotations.csv` is missing or empty, the script MUST log a CRITICAL warning, set the validation status to 'UNVALIDATED', and proceed to T019d. **NO SYNTHETIC FALLBACK** is permitted. (FR-011, Constitution Principle I)
- [X] T020 [US1] Save spot-check results to `data/spot_check/validation_report.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Perform descriptive statistics, IQR outlier handling for visualization and primary test, and execute Mann-Whitney U test.

**Independent Test**: Can be tested by running the analysis on a sample dataset and verifying that the Mann-Whitney U test produces statistically valid results with appropriate p-values and effect size calculations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for IQR outlier calculation in `tests/unit/test_iqr.py`
- [X] T022 [P] [US2] Unit test for Mann-Whitney U test execution in `tests/unit/test_mwu.py`

### Implementation for User Story 2

- [ ] T023a [US2] Implement `code/analyze.py` to load and validate input data. **Input**: Must exclude data from repositories listed in `data/processed/excluded_repos.txt` (from T014). **Fallback**: If `excluded_repos.txt` is missing, assume no exclusions and log a warning. **Prerequisite**: Must consume `data/processed/pr_turnaround.csv` (T018b). (FR-004, SC-002, Edge Case).
- [~] T023b [US2] Implement `code/analyze.py` to calculate descriptive statistics (mean, median, SD, quartiles) for AI and non-AI groups using the loaded data from T023a. Save to `data/processed/descriptive_stats.json`. (FR-004, SC-002)
- [ ] T024 [US2] Implement IQR outlier calculation in `code/analyze.py` (Q1 - 1.5×IQR, Q3 + 1.5×IQR) calculated separately per group. **Requirement**: Create `data/processed/pr_turnaround_full.csv` (Full Dataset, for the **Primary Hypothesis Test** per Plan Phase 1) and `data/processed/pr_turnaround_cleaned.csv` (Outliers Removed, for **Visualization ONLY** per Spec FR-005). **Log**: Count and log the number of outliers identified and removed per group. **Clarification**: The cleaned file is for visualization ONLY; the primary test (T026a) must use the Full Dataset from T018b/T023a, NOT the cleaned file. (FR-005, SC-002, F001)
- [X] T027a [US2] Implement power check in `code/analyze.py`: if AI group count < 30, raise `SampleSizeError` with message "Sample size too small: AI group < 30" to abort pipeline (Plan Phase 1)
- [ ] T026a [US2] Execute **Standard Mann-Whitney U test** in `code/analyze.py`. **Input**: Use the **Full Dataset** (`data/processed/pr_turnaround.csv` from T018b) to comply with Plan Phase 1 robustness requirement. **Method**: Perform standard MWU test comparing AI vs non-AI groups. Return U statistic, p-value, and effect size (r). **Traceability**: This task implements Spec FR-006 exactly. **Status**: PRIMARY RESULT. **Dependency**: T023a, T023b. **NOT T024** (Full Dataset used directly). (FR-005, FR-006, SC-004, F001)
- [X] T026c [US2] Log the conclusion of the statistical test. **Logic**: If p < 0.05, log "Significant difference found". If p >= 0.05, log "No significant difference found (valid result)". Ensure the "No significant" case is recorded as a valid finding for the report. (SC-004)
- [X] T029 [US2] Save statistical results to `data/processed/statistical_results.json`, explicitly including keys: `u_statistic`, `p_value`, `effect_size`, `sample_sizes`, `median_stars`, `median_contributors`, `distribution_stats` (FR-013, FR-006, SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality boxplot and assemble final report with conditional limitation logic.

**Independent Test**: Can be tested by verifying that the script generates a clear, labeled boxplot showing both distributions and successfully saves it to the designated artifacts directory.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for boxplot generation parameters (DPI, labels) in `tests/unit/test_visualize.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/visualize.py` to generate boxplot comparing turnaround time distributions for AI and non-AI groups. **Use outlier-excluded data for whiskers only** (FR-007)
- [X] T032 [US3] Ensure boxplot axes are labeled (turnaround time in hours vs. PR type) and whiskers use IQR bounds (FR-007)
- [X] T033 [US3] Save visualization to `artifacts/boxplot.png` with ≥300 DPI resolution (FR-008, SC-005)
- [X] T036a [US3] Verify `artifacts/boxplot.png` exists and calculate the correct relative path for the report. If missing, raise an error.
- [X] T034 [US3] Implement `code/report.py` to assemble final report including boxplot image path, statistical test results, key descriptive statistics, and validation summary (FR-008, SC-003)
- [X] T034b [US3] Load spot-check results from `data/spot_check/validation_report.csv` (T020). Calculate `false_negative_rate = count(misclassified_AI) / total_sample_size` (FR-011, FR-012)
- [ ] T035 [US3] Implement conditional logic in `code/report.py`: **Prerequisite: T020 completion**. If `false_negative_rate` (from T034b) > 10%, inject limitation statement with text: "Limitation: False-negative rate exceeds 10% threshold, indicating potential misclassification in non-AI group." (FR-012)
- [ ] T036b [US3] Render the final report to `artifacts/final_report.md`. **Template**: Use the following Markdown structure exactly:
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
**Logic**: Replace placeholders with values from T029 and T023. **Explicitly load T017 output** (`data/processed/repo_metadata.json`) to populate median star/contributor values in the report. If `false_negative_rate` > 10%, set `{limitation_statement}` to the exact string from T035; otherwise set it to "No limitations detected." **Dependencies**: T029, T023, T033, T035, **T017** (Repo Metadata). (FR-008, SC-005, FR-012, FR-013)
- [X] T037 [US3] Update `state/projects/PROJ-312-.../state.yaml` with artifact hashes and `updated_at` timestamp (Constitution Principle V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Documentation updates in `projects/PROJ-312-evaluating-the-impact-of-code-generation/README.md`
- [X] T039 [P] Ensure code quality: Run `ruff --fix` and `black --check` to ensure zero linting and formatting errors.
- [X] T040a [P] Add unit tests for edge cases in `fetch_data.py` (e.g., empty response, rate limit) in `tests/unit/test_fetch_data_edge_cases.py`
- [X] T040b [P] Add unit tests for edge cases in `analyze.py` (e.g., empty group, NaN values) in `tests/unit/test_analyze_edge_cases.py`
- [X] T040c [P] Add unit tests for edge cases in `visualize.py` (e.g., zero variance) in `tests/unit/test_visualize_edge_cases.py`
- [X] T041 [P] Run quickstart.md validation: Execute all commands in `quickstart.md`, verify exit code 0 for each, and confirm expected output files exist
- [X] T042 [P] Verify all CSV/JSON outputs match schema contracts in `contracts/`
- [ ] T043 [P] [US1] Add integration test for GitHub API pagination logic in `tests/integration/test_github_pagination.py`. **Goal**: Verify that the `Link` header parsing correctly iterates through multiple pages of results for a repository with >100 PRs, ensuring no data is truncated before the stop condition is met. (Revision Concern: T012b Pagination)
- [ ] T045 [P] [US1] Add unit test for `validate_spot_check.py` missing annotation handling. **Goal**: Verify that T019d correctly logs a CRITICAL warning and sets the validation status to 'UNVALIDATED' when `annotations.csv` is missing, and that T019e correctly handles the file existence check without raising an error. (Revision Concern: T019c/d/e Flow)
- [ ] T046 [P] [US2] Add unit test for MWU power check. **Goal**: Verify that T027a correctly raises `SampleSizeError` when the AI group count is less than 30, ensuring the pipeline aborts before attempting the statistical test. (Revision Concern: T027a Robustness)
- [ ] T047 [P] [US3] Add integration test for report generation. **Goal**: Verify that T036b correctly injects the limitation statement from T035 into `artifacts/final_report.md` when the false-negative rate exceeds 10%, and correctly omits it otherwise. (Revision Concern: T035/T036b Logic)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and US1 data availability. Depends on `data/processed/pr_turnaround.csv` from T018b and `data/processed/excluded_repos.txt` from T014.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and US2 data availability. Depends on `data/processed/statistical_results.json` from T029 and `data/spot_check/validation_report.csv` from T020. **Explicitly depends on T020 completion.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetching (T012a, T012b) before classification (T015) and calculation (T016)
- Classification before saving processed data (T018)
- Spot-check (T019) can run in parallel with main analysis but results needed for Report (T035)
- **T012b** depends on T012a (Repo list) - **NOT Parallel**
- **T006** (Logging logic) must be implemented before T012a/T012b (API calls)
- **T006c** depends on T005 (Validation utility) - **NOT Parallel**
- **T023a** depends on T014 (excluded repos) and T018b (processed data). **NOT Parallel** with other Phase 4 tasks that rely on T023a.
- **T023b** depends on T023a.
- **T026a** depends on T023a, T023b. **NOT T024**.
- **T026c** depends on T026a results.
- **T019b** depends on T019a.
- **T019c** depends on T019b.
- **T019d** depends on T019c (timeout logic).
- **T019e** depends on T019c (file existence).
- **T034b** depends on T020.
- **T035** depends on T034b.
- **T036b** depends on T034, T035, T029, T033, **T017** - **NOT Parallel**.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T006c which must precede API calls
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
- **Methodology Note**: Per Plan Phase 1, the **Full Dataset** is used for the Primary Hypothesis Test (T026a). The **Cleaned Dataset** (outliers removed) is used only for Visualization (T031). This resolves the Spec vs Plan conflict.
- **Plan Alignment**: T026a implements the Spec-mandated Standard MWU (PRIMARY) on the Full Dataset. **T026b (Stratified MWU) has been removed** as the required covariates (`lines_changed`, `total_prs_by_author`) are not fetched in the data acquisition phase (FR-001 scope).
- **Spot Check Flow**: T019b creates a template with instructions for humans. T019c waits for the human-generated file. T019d handles missing data gracefully without fabrication. T019e ingests the real data if present; if missing, it logs a warning and proceeds.
- **Sensitivity Analysis**: REMOVED. The Spec and Plan do not mandate bias-correction or Monte Carlo sensitivity analysis. The spot-check (FR-011) is used solely for the limitation statement (FR-012).
- **Data Fetching**: T012b mandates fetching ALL PRs for the representative set (Top 20 repos) to strictly satisfy FR-001, with a safety stop condition (max 50 pages) to prevent timeouts. Truncated repos are logged and documented as a limitation.
- **Revision Concern**: T019e Synthetic Fallback Logic: REMOVED. The task now strictly requires real data or a graceful fallback (UNVALIDATED status).
- **Revision Concern**: T026b Stratified Test: **REMOVED** due to missing covariates in upstream data fetch.
- **Revision Concern**: T012b Pagination: Verify that the GitHub API pagination logic handles the `Link` header correctly for all repos. If a repo has >100 PRs, the current implementation must ensure all pages are fetched (up to the stop condition). Add a test task T043 if pagination logic is complex.
- **Revision Concern**: T044 Stratified Pre-check: **REMOVED** (T026b removed).
- **Revision Concern**: T045 Spot Check Robustness: Explicitly test the error handling for missing or empty annotation files to ensure the pipeline fails loudly or degrades gracefully without synthetic data.
- **Revision Concern**: T046 Power Check: Verify that the pipeline aborts correctly when sample size is insufficient, preventing invalid statistical tests.
- **Revision Concern**: T047 Report Logic: Verify that the limitation statement is correctly injected into the final report based on the false-negative rate threshold.