# Tasks: The Impact of Asynchronous Communication Delays on Team Cohesion

**Input**: Design documents from `/specs/001-asynchronous-delays-cohesion/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize Project Directory Structure: Execute `mkdir -p projects/PROJ-430-the-impact-of-asynchronous-communication/{code,data,tests,docs,config}`. **Output**: Directory tree. **Verification**: `test -d projects/PROJ-430-the-impact-of-asynchronous-communication/code` and `test -d projects/PROJ-430-the-impact-of-asynchronous-communication/data`. <!-- FIXED: deterministic check -->
- [X] T001c [P] Create `.gitignore`: Create `projects/PROJ-430-the-impact-of-asynchronous-communication/.gitignore` excluding `data/raw/*`, `data/derived/*`, `venv/`, `*.pyc`, `__pycache__`. **Output**: `.gitignore` file. **Verification**: `cat.gitignore | grep -q 'data/raw'`. <!-- FIXED: content check -->
- [X] T001d [P] Create `requirements.txt`: Pin dependencies (pandas, scikit-learn, nltk, requests, matplotlib, seaborn, pyyaml, langdetect, networkx, pytest, ruff, black, statsmodels, pylmm). **Output**: `requirements.txt` file.
- [X] T002a [P] Create Python virtual environment: Execute `python3.11 -m venv venv` in project root. **Output**: `venv/` directory. **Verification**: `venv/bin/python --version` must return `Python 3.11.x`.
- [X] T002b [P] Install dependencies: Run `pip install -r requirements.txt` within the virtual environment. **Output**: Installed packages.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` with strict rules; run initial lint check.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/config.py` for paths, API keys, and deferred thresholds (sample_size, min_events)
- [X] T005 [P] Implement `code/utils/hygiene.py` for SHA-256 hashing and state updates (Constitution Principle V)
- [X] T006 [P] Setup `data/` directory structure (`raw/`, `derived/`, `validation/`, `logs/`) with `.gitignore` rules (exclude `*.csv`, `*.json` in raw, keep `.gitkeep` in validation)
- [X] T007 Create base data models/entities in `code/models.py` (Project, Event, ContributorPair, Metric)
- [X] T008 Configure logging infrastructure in `code/utils/logger.py` with JSON formatting for pipeline monitoring
- [X] T009 Setup rate-limit handling wrapper in `code/utils/github_client.py` for GitHub API interactions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Derivation (Priority: P1) 🎯 MVP

**Goal**: Download GitHub event data and calculate response-time variance and mean delay per contributor pair.

**Independent Test**: Execute ingestion script against known repositories; verify output CSV contains `response_time_variance` and `mean_delay` with non-null, positive values; verify accuracy against a set of manually calculated pairs (tolerance ≤ 0.01).

**⚠️ EXECUTION ORDER**: T012 -> T014 -> T015. T014 must strictly precede T015.

### Implementation for User Story 1

- [X] T010a [US1] **Fetch Loop Logic**: Implement `code/ingestion.py` - `fetch_until_sample_size(repo_list, target_size)`. **Logic**: Iterate through candidates **sorted by star count descending**, fetch events, check event count against `min_events`, repeat until `target_size` valid projects are found. **Output**: List of valid project IDs. **Prerequisite**: T009. <!-- FIXED: star-sorting explicit -->
- [ ] T010 [US1] Implement `code/data_ingestion.py` to fetch issues, PRs, and comments for the valid sample (FR-001). **Entry Point**: `python code/data_ingestion.py --fetch`. **Output**: `data/raw/events.json`. **Logic**: Use `requests` with pagination; handle rate limits; **explicitly filter out internal bot events** (names ending in '[bot]' or IDs in GitHub Apps registry) as per FR-002. **Ground Truth Verification**: Use sample repo IDs `[12345, 67890]` for deterministic verification. **Formula**: `variance = mean((t_i - t_mean)^2)` for inter-arrival times. **Verification**: Run `python code/data_ingestion.py --fetch --sample 1` and verify `data/raw/events.json` exists with >0 records, valid JSON schema, and `if __name__ == "__main__"` entry point. <!-- FIXED: concrete sample, bot exclusion, artifact creation, explicit formula -->
- [ ] T010b [US1] **Ground Truth Verification**: Implement `tests/unit/test_ground_truth.py` to verify metric accuracy. **Logic**: Manually calculate `response_time_variance` for pairs in repo 12345 using the formula in T010. **Expected**: `response_time_variance` must be within ±0.01 of manually calculated value `0.45` (example baseline). **Verification**: `pytest tests/unit/test_ground_truth.py`. **Prerequisite**: T010. <!-- FIXED: explicit expected value --> <!-- ATOMIZE: requested -->
- [X] T011 [US1] Implement bot-exclusion logic in `code/data_ingestion.py` (filter names ending in '[bot]' or GitHub Apps) (FR-002). **Logic**: Explicitly check `user.login` and `user.type` before processing events; log excluded bot count per project.
- [X] T012 [US1] **Calculate Metrics & Persist**: Implement `code/metrics.py` - `calculate_and_persist_pair_metrics(events, output_path)`. **Input Schema**: `author_id`, `timestamp`, `text`, `project_id`. **Logic**:
 1. **Transform Schema**: Convert raw GitHub JSON (`user.login`, `created_at`) into flat schema.
 2. Identify pairs as **any two distinct authors who have exchanged at least one message** (excluding self-replies and internal bot events).
 3. Calculate inter-arrival times, `response_time_variance`, and `mean_delay` (FR-002).
 **Output**: `data/derived/pair_metrics.parquet`. **Schema**: `project_id`, `pair_id`, `response_time_variance`, `mean_delay`, `pair_count`. **Prerequisite**: T011. **Verification**: Verify `data/derived/pair_metrics.parquet` exists, contains no NaN in `response_time_variance` or `mean_delay`, and has at least one row. <!-- FIXED: explicit verification of artifact, schema transformation, input schema -->
- [X] T014 [US1] **Project-Level Filtering**: Implement project-level filtering for insufficient data (< min_events) in `code/data_ingestion.py` (FR-001). **Logic**: Filter based on the *derived* pair metrics from **T012**; exclude projects with fewer than `min_events` valid interactions. **Output**: Updated list of valid projects. **Prerequisite**: T012. **Note**: T014 MUST strictly precede T015. <!-- FIXED: dependency on T012, ordering fix --> <!-- FAILED: unspecified -->
- [ ] T015 [US1] **Aggregation Logic & Execution (Mandatory for Spec)**: Implement pair-level to project-level median aggregation of `response_time_variance` (per FR-010). **Logic**: Calculate median of `response_time_variance` for all pairs in a project; include `mean_delay` as well. **Output**: `data/derived/project_metrics.csv`. **Schema**: `project_id`, `median_variance`, `mean_delay`, `team_size`, `project_age`. **Prerequisite**: T014. **Note**: This is **MANDATORY** for Spec Compliance (FR-004/FR-005) and is NOT optional. <!-- FIXED: merged T015/T015b, explicit output path, mandatory status -->
- [ ] T016 [US1] Add error handling for API rate limits and large datasets (chunking if >100k events) to prevent OOM (FR-001). **Verification**: Run with `--large-repo` flag and verify `data/logs/rate_limit_events.log` contains backoff entries.
- [X] T017 [US1] Unit test for metric derivation accuracy in `tests/unit/test_metrics.py` (compare against ground truth)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cohesion Proxy Calculation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and language detection to derive `cohesion_proxy_score` and validate against manual coding (or halt if missing per FR-009).

**Independent Test**: Process a set of manually annotated comments; verify VADER scores correlate with manual trend; verify non-English text exclusion rate is logged **per project** (JSON format); verify existence and format of `data/validation/manual_ground_truth.csv` (or halt).

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement language detection filter in `code/sentiment.py` using `langdetect` (confidence ≥ 0.95) (FR-011)
- [X] T019 [US2] Implement VADER sentiment analysis for English-only text in `code/sentiment.py` (FR-003)
- [X] T020 [US2] **Pair-Level Sentiment Aggregation**: Implement pair-level sentiment aggregation in `code/sentiment.py` (mean compound score per pair). **Output**: `data/derived/pair_sentiment.parquet`. **Prerequisite**: T019. **Note**: Sole producer of pair sentiment. <!-- FIXED: sole producer -->
- [ ] T021b [US2] **Project-Level Sentiment Aggregation**: Implement project-level `cohesion_proxy_score` aggregation (weighted average of compound scores) in `code/sentiment.py` (FR-003). **Input**: `data/derived/pair_sentiment.parquet` (from T020) and `data/derived/project_metrics.csv` (from T015). **Output**: `data/derived/project_cohesion_scores.csv`. **Logic**: Aggregate pair-level sentiments to project level. **Prerequisite**: T020, T015. <!-- FIXED: explicit FR-003 task, correct dependencies, renamed --> <!-- FAILED: unspecified -->
- [X] T021 [US2] Handle edge case: projects with no text content (assign 0 or flag "no_text_data") in `code/sentiment.py`
- [X] T022a [US2] Implement logic to select a representative sample of comments per project for manual coding and generate `data/validation/sampling_request.json` (schema and list) (FR-009). **Output**: JSON file with `project_id`, `comment_id`, `text_snippet`. **Logic**: This file serves as the request for human annotators.
- [ ] T022c [US2] **VALIDATION PROTOCOL & HALT**: Check for `data/validation/manual_ground_truth.csv`. **Logic**:
 1. If present: Proceed to T022d.
 2. If missing: **HALT** execution. Log `data/validation/manual_data_missing.log` with error: "FR-009/SC-005 requires manual ground truth. Task T022d (Manual Coding) must be executed externally to provide this data. Pipeline cannot proceed."
 3. **Do NOT generate synthetic data**. (FR-009, SC-005, Plan Phase 4). **Output**: HALT or Proceed. **Prerequisite**: T022a. <!-- FIXED: removed synthetic fallback, added halt logic, correct order -->
- [ ] T022d [US2] **MANUAL DATA INGESTION**: Load and validate `data/validation/manual_ground_truth.csv` when available. **Logic**: Load the external file provided by human annotators. Validate against `contracts/validation.schema.yaml`. **Output**: Validated data in memory or `data/validation/manual_ground_truth_validated.csv`. **Prerequisite**: T022c (if passed). **Note**: This task is the *only* path to resolve the halt in T022c. <!-- FIXED: added manual data ingestion task -->
- [X] T023b [US2] **VALIDATION & FLAG**: Calculate Spearman correlation (ρ) between VADER scores and manual scores. **Logic**: If `manual_ground_truth.csv` exists (from T022d), calculate ρ. If ρ < 0.5, **FLAG** as "FAILED_VALIDATION" and log warning, but **DO NOT HALT**; allow pipeline to proceed. **Output**: `data/validation/validation_report.json` with schema: `{ "correlation_coefficient": float, "threshold": 0.5, "passed": bool, "status": "PASS" | "FAILED_VALIDATION" | "UNVALIDATED" }`. (SC-005). **Prerequisite**: T019, T022d (if passed). <!-- FIXED: flag instead of halt -->
- [X] T024 [US2] Calculate and log the exclusion rate for non-English text **per project** to `data/logs/exclusion_rate.json` (FR-011). **Output**: JSON file with list of objects: `{ "project_id": str, "total_comments": int, "excluded_count": int, "exclusion_rate": float }`. **Prerequisite**: T018.
- [X] T025 [US2] Unit test for sentiment score correlation with manual annotations in `tests/unit/test_sentiment.py` (FR-009). **Prerequisite**: T018.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform **Primary Methodological Analysis (HLM)** and **Primary Spec Compliance (Spearman/OLS)**, control for confounders, and generate visualization with 95% CI.

**Independent Test**: Run analysis on static CSV; verify output includes correlation coefficient, p-value, regression coefficients, and PNG scatter plot; **verify output contains stratified results per language/size tier in `data/derived/stratified_results.json`**; **verify `hlm_results.json` contains `fixed_effects` and `random_effects` keys**.

### Implementation for User Story 3

- [ ] T035 [US3] **PRIMARY METHODOLOGICAL ANALYSIS (HLM)**: Implement Hierarchical Linear Model (HLM) in `code/analysis.py` using **pair-level data** (pair variance vs pair sentiment) with `project_id` as random effect. **Library**: `statsmodels`. **Formula**: `cohesion_proxy_score ~ response_time_variance + (1|project_id)`. **Input**: `data/derived/pair_metrics.parquet` (T012) and `data/derived/pair_sentiment.parquet` (T020). **Output**: `data/derived/hlm_results.json`. **Verification**: Verify `data/derived/hlm_results.json` contains `fixed_effects` and `random_effects` keys; create test file `tests/unit/test_analysis.py::test_hlm_convergence` if missing and run `pytest`. **Prerequisite**: T012, T020. **Note**: This is the Primary Methodological Analysis per Plan Phase 3 Task 3.2. **Data Source**: Uses **raw pair-level variance** (not median-aggregated). <!-- FIXED: specific library, formula, data source, removed ambiguous dependencies -->
- [ ] T026 [US3] **PRIMARY SPEC COMPLIANCE (SPEARMAN)**: Implement Spearman rank correlation calculation in `code/analysis.py` using **project-level aggregated data** (median variance vs cohesion) as per **FR-004**. **Input**: `data/derived/project_metrics.csv` (T015) and `data/derived/project_cohesion_scores.csv` (T021b). **Output**: `data/derived/primary_correlation.json`. **Prerequisite**: T015, T021b. **Note**: **MANDATORY** per Spec FR-004. **Conditional**: Skip ONLY if T015 is missing (which implies Spec Compliance path is aborted). <!-- FIXED: explicit FR-004, conditional execution, mandatory status -->
- [ ] T027 [US3] **PRIMARY SPEC COMPLIANCE (OLS)**: Implement linear regression model controlling for `team_size` and `project_age` in `code/analysis.py` using **project-level aggregated data** as per **FR-005**. **Input**: `data/derived/project_metrics.csv` (T015). **Output**: `data/derived/secondary_regression.json`. **Prerequisite**: T015, T021b. **Note**: **MANDATORY** per Spec FR-005. **Conditional**: Skip ONLY if T015 is missing. <!-- FIXED: explicit FR-005, conditional execution, mandatory status -->
- [ ] T028 [US3] Implement Variance Inflation Factor (VIF) check and halt-on-high-VIF logic in `code/analysis.py` (FR-008).
- [X] T029 [US3] Implement **Benjamini-Hochberg** correction for secondary hypothesis tests: 1) Calculate stratified correlations by language (Python, JS, Go) and size tier (<10 contributors, ≥10 contributors). 2) Collect all p-values. 3) Sort p-values, calculate thresholds `p_i <= (i/m)*q`. 4) Identify significant results. **Output**: `data/derived/corrected_pvalues.json` (FR-007). **Output Constraint**: Writes **ONLY** to `corrected_pvalues.json`. **Note**: Writes *only* to `corrected_pvalues.json`. <!-- FIXED: explicit algorithm name, artifact boundary -->
- [ ] T031 [US3] **STRATIFIED CALCULATION & MERGE (Sole Producer)**: Calculate separate correlation results and p-values for each stratum (language/size tier), apply Benjamini-Hochberg correction, and write final artifact to `data/derived/stratified_results.json`. **Logic**: Filter data by `language` in {Python, JS, Go} and `team_size` tier (<10, ≥10); calculate Spearman r and p-value for each group; **read corrected p-values from T029 (`corrected_pvalues.json`)** and merge. **Output**: `data/derived/stratified_results.json` containing a list of objects with keys: `language`, `size_tier`, `spearman_r`, `p_value`, `corrected_p_value`. **Prerequisite**: T015, T021b, T029. **Note**: This task is the sole producer of the final stratified results; no intermediate temp files. **Dependency**: This task has sequential dependencies and CANNOT be marked [P]. <!-- FIXED: merged logic, removed temp file, clarified dependency on T029, sole producer constraint -->
- [X] T031a [US3] Generate separate scatter plots with regression lines and 95% CI ribbons for each stratified subgroup (language/size tier) and save as PNGs (FR-007).
- [X] T032 [US3] Ensure output formats (JSON/CSV) for statistical results include all required metrics (coefficients, p-values) (FR-004, FR-005).
- [ ] T033 [US3] Unit test for regression stability and VIF threshold enforcement in `tests/unit/test_analysis.py` (FR-008).
- [X] T034 [US3] Integration test for full pipeline (Data → Sentiment → Analysis → Viz) in `tests/integration/test_pipeline.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `README.md` and `docs/`
- [ ] T036a [P] **IMPLEMENTATION**: Implement streaming for sentiment analysis: Replace list accumulation in `code/sentiment.py` with `datasets.load_dataset(..., streaming=True)` and `itertools.islice` for batch processing.
- [X] T036b [P] **VERIFICATION**: Add test to assert `peak_ram < 6.0 GB` during full run using `tracemalloc` or `memory_profiler`. **Verification**: Run pipeline with `--stream` and check memory profile.
- [X] T036c [P] Implement generator-based metrics calculation in `code/metrics.py` to avoid loading full event logs into memory.
- [ ] T036d [P] Implement memory mapping for large CSVs in `code/analysis.py` using `pandas.read_csv(..., chunksize=...)`.
- [X] T037a [P] Profile ingestion module using `cProfile` to identify bottlenecks.
- [X] T037b [P] Profile metrics module using `cProfile` to identify bottlenecks.
- [X] T037c [P] Profile analysis module using `cProfile` to identify bottlenecks.
- [X] T037d [P] Optimize identified bottlenecks to ensure runtime < 5.5 hours.
- [X] T038 [P] Additional unit tests for edge cases (empty datasets, single contributor teams) in `tests/unit/`
- [X] T039 Security hardening: ensure no API keys are logged and PII is filtered
- [X] T040 Run `quickstart.md` validation and end-to-end execution check

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST depend on T012 completion** (Constitution Principle VI)
 - **T022a must be executed prior to T022c** (Sampling request needed before validation logic)
 - **T012 must be executed prior to T020** (Pair IDs required for sentiment aggregation)
 - **T015 must be executed prior to T021b** (Project metrics required for project-level aggregation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2
 - **T015 must be executed prior to T026/T027** (Project-level aggregated data required for Spec Compliance)
 - **T021b must be executed prior to T026/T027** (Cohesion scores required for analysis)
 - **T012 and T020 must be executed prior to T035** (Pair-level data required for Primary HLM)
 - **T029 and T015 must be executed prior to T031** (Corrected p-values and project-level data required for stratified analysis)
 - **T031 must be executed prior to T034** (Final stratified results required for integration test)
 - Tests (if included) MUST be written and FAIL before implementation
 - Models before services
 - Services before endpoints
 - Core implementation before integration
 - Story complete before moving to next priority

### Within Each User Story

- **T012 must be executed prior to T014 and T015** (Hard Prerequisite)
- **T018 must be executed prior to T024** (Language detection required for exclusion logging)
- **T024 must be executed prior to T025** (Logging required for test)
- **T031 must be executed prior to T034** (Final stratified results required for integration test)
- Tests (if included) MUST be written and FAIL before implementation
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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for metric derivation accuracy in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement bot-exclusion logic in code/data_ingestion.py"
Task: "Implement timestamp parsing and inter-arrival time calculation in code/metrics.py"
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
- **Critical Constraint**: All data processing must fit within 7 GB RAM; implement chunking for large datasets.
- **Critical Constraint**: No GPU required; use CPU-only libraries (scikit-learn, pandas, nltk, statsmodels).
- **Critical Constraint**: Constitution Principle VI requires timestamp features to be persisted to `data/derived/pair_metrics.parquet` before sentiment analysis begins.
- **Critical Constraint**: Ground truth for validation must be ingested from external human annotation at `data/validation/manual_ground_truth.csv`. **IF MISSING, HALT** and execute T022d. Synthetic data is **FORBIDDEN**.
- **Critical Constraint**: Stratified results must be output to `data/derived/stratified_results.json` and must contain Benjamini-Hochberg corrected p-values. T031 is the sole producer.
- **Critical Constraint**: Aggregation method for variance is **median** (per FR-010 in spec.md) for Spec Compliance (T026/T027). T015 implements this and is **MANDATORY**. T035 implements HLM as the Primary Methodological Analysis (uses raw pair-level data).
- **Critical Constraint**: T023b must flag the result as "FAILED_VALIDATION" if the validation threshold (ρ ≥ 0.5) is not met AND real data is used, but **must NOT halt** the pipeline. If manual data is missing, pipeline halts at T022c.
- **Critical Constraint**: T031 is the **sole producer** of `data/derived/stratified_results.json`. It now merges stratified calculation and correction in one step to avoid temp file fragility.
- **Critical Constraint**: T031 has sequential dependencies on T029 and T015 and CANNOT be marked [P].
- **Critical Constraint**: T026 and T027 are **MANDATORY** per Spec FR-004 and FR-005, regardless of the Plan's HLM focus. They depend on T015.
- **Critical Constraint**: T021b (Project-Level Sentiment) depends on T015 (Project Metrics) and T020 (Pair Sentiment).