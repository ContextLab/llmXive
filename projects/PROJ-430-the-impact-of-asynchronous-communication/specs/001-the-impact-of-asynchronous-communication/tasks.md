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

- [ ] T001a [P] Create project root directories: Initialize `projects/PROJ-430-the-impact-of-asynchronous-communication/`. **Output**: Root directory.
- [ ] T001b [P] Create subdirectories: Create `code/`, `data/`, `tests/`, `docs/` inside the project root. **Output**: Directory tree.
- [ ] T001c [P] Create `requirements.txt`: Pin dependencies (pandas, scikit-learn, nltk, requests, matplotlib, seaborn, pyyaml, langdetect, networkx, pytest, ruff, black, statsmodels, pylmm). **Output**: `requirements.txt` file.
- [ ] T002a [P] Create Python 3.11 virtual environment: Run `python -m venv venv` in project root. **Output**: `venv/` directory.
- [ ] T002b [P] Install dependencies: Run `pip install -r requirements.txt` within the virtual environment. **Output**: Installed packages.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` with strict rules; run initial lint check.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `code/config.py` for paths, API keys, and deferred thresholds (sample_size, min_events)
- [ ] T005 [P] Implement `code/utils/hygiene.py` for SHA-256 hashing and state updates (Constitution Principle V)
- [ ] T006 [P] Setup `data/` directory structure (`raw/`, `derived/`, `validation/`, `logs/`) with `.gitignore` rules (exclude `*.csv`, `*.json` in raw, keep `.gitkeep` in validation)
- [ ] T007 Create base data models/entities in `code/models.py` (Project, Event, ContributorPair, Metric)
- [ ] T008 Configure logging infrastructure in `code/utils/logger.py` with JSON formatting for pipeline monitoring
- [ ] T009 Setup rate-limit handling wrapper in `code/utils/github_client.py` for GitHub API interactions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Derivation (Priority: P1) 🎯 MVP

**Goal**: Download GitHub event data and calculate response-time variance and mean delay per contributor pair.

**Independent Test**: Execute ingestion script against known repositories; verify output CSV contains `response_time_variance` and `mean_delay` with non-null, positive values; verify accuracy against a set of manually calculated pairs (tolerance ≤ 0.01).

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/data_ingestion.py` to fetch issues, PRs, and comments for a sample of projects (FR-001). **Entry Point**: `python code/data_ingestion.py --fetch`. **Output**: `data/raw/events.json`. **Logic**: Use `requests` with pagination; handle rate limits; filter out internal bot events (names ending in '[bot]' or IDs in GitHub Apps registry) as per FR-002.
- [ ] T011 [US1] Implement bot-exclusion logic in `code/data_ingestion.py` (filter names ending in '[bot]' or GitHub Apps) (FR-002). **Logic**: Explicitly check `user.login` and `user.type` before processing events; log excluded bot count per project.
- [ ] T012a [US1] Implement Contributor Pair identification and metric calculation in `code/metrics.py`: identify pairs as any two distinct authors who have exchanged at least one message (excluding self-replies and internal bot events), calculate inter-arrival times, `response_time_variance`, and `mean_delay` (FR-002)
- [ ] T014 [US1] Implement project-level filtering for insufficient data (< min_events) in `code/data_ingestion.py` (FR-001). **Logic**: Filter based on the *derived* pair metrics from T012a; exclude projects with fewer than `min_events` valid interactions. **Prerequisite**: T012a.
- [ ] T015 [US1] **SECONDARY ROBUSTNESS CHECK**: Aggregate pair-level variances to a project-level metric using the **median** of all pair variances (per FR-010 in spec.md) to ensure unit-of-analysis alignment. **Output**: `data/derived/project_metrics.csv`. **Logic**: Calculate median of `response_time_variance` for all pairs in a project; include `mean_delay` as well. This is the input for the Secondary Analysis (T026/T027).
- [ ] T015a [US1] Persist intermediate timestamp-derived features to `data/derived/timestamp_features.parquet` to enforce Constitution Principle VI (Modality Separation) (Const VI). **Schema**: Must include columns `project_id`, `pair_id`, `response_time_variance`, `mean_delay`, `pair_count`. **Prerequisite**: T012a. **Handoff to US2**. 👉 **Handoff to US2**
- [ ] T016 [US1] Add error handling for API rate limits and large datasets (chunking if >100k events) to prevent OOM (FR-001)
- [ ] T017 [US1] Unit test for metric derivation accuracy in `tests/unit/test_metrics.py` (compare against ground truth)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cohesion Proxy Calculation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and language detection to derive `cohesion_proxy_score` and validate against manual coding (or synthetic fallback per Plan).

**Independent Test**: Process a set of manually annotated comments; verify VADER scores correlate with manual trend; verify non-English text exclusion rate is logged **per project** (JSON format); verify existence and format of `data/validation/manual_ground_truth.csv` or synthetic fallback.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement language detection filter in `code/sentiment.py` using `langdetect` (confidence ≥ 0.95) (FR-011)
- [ ] T019 [US2] Implement VADER sentiment analysis for English-only text in `code/sentiment.py` (FR-003)
- [ ] T020 [US2] Implement project-level `cohesion_proxy_score` aggregation (weighted average of compound scores) in `code/sentiment.py` (FR-003)
- [ ] T021 [US2] Handle edge case: projects with no text content (assign 0 or flag "no_text_data") in `code/sentiment.py`
- [ ] T021b [US2] **CRITICAL DATA PREP**: Aggregate pair-level sentiment scores to generate `data/derived/pair_sentiment.parquet`. **Input**: `data/derived/timestamp_features.parquet` (for pair IDs) and raw event text. **Output**: `data/derived/pair_sentiment.parquet` with `pair_id`, `mean_sentiment`, `count`. **Logic**: Group comments by `pair_id` and calculate mean compound score. **Prerequisite**: T019. **Handoff to US3 (Primary)**.
- [ ] T022a [US2] Implement logic to select a representative sample of comments per project for manual coding and generate `data/validation/sampling_request.json` (schema and list) (FR-009). **Output**: JSON file with `project_id`, `comment_id`, `text_snippet`. **Logic**: This file serves as the request for human annotators.
- [ ] T022c [US2] **VALIDATION PROTOCOL & SYNTHETIC FALLBACK**: Check for `data/validation/manual_ground_truth.csv`. **Logic**: 
  1. If present: Load and validate schema.
  2. If missing: Generate `data/validation/synthetic_ground_truth.csv` by sampling synthetic scores based on the VADER distribution (Plan Task 4.5). Log `data/validation/synthetic_mode_active.log`. 
  3. Do NOT halt. Proceed with available data (real or synthetic). (FR-009, SC-005, Plan Phase 4). **Prerequisite**: T022a.
- [ ] T023a [US2] Implement multi-modal validation logic to align VADER scores with the manual/synthetic ground truth data (FR-009). **Output**: `data/validation/alignment_config.yaml` mapping VADER bins to manual scores. **Prerequisite**: T019, T022c.
- [ ] T023b [US2] Calculate Spearman correlation (ρ) between VADER scores and manual/synthetic scores. **Logic**: If real data used, **HALT** if ρ < 0.5 (SC-005). If synthetic mode active, flag as "UNVALIDATED" and proceed. **Output**: `data/validation/validation_report.json` with schema: `{ "correlation_coefficient": float, "threshold": 0.5, "passed": bool, "status": "PASS" | "FAIL" | "UNVALIDATED" }`. (SC-005). **Prerequisite**: T022c.
- [ ] T024 [US2] Calculate and log the exclusion rate for non-English text **per project** to `data/logs/exclusion_rate.json` (FR-011). **Output**: JSON file with list of objects: `{ "project_id": str, "total_comments": int, "excluded_count": int, "exclusion_rate": float }`. **Prerequisite**: T018.
- [ ] T025 [US2] Unit test for sentiment score correlation with manual annotations in `tests/unit/test_sentiment.py` (FR-009). **Prerequisite**: T018.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform **Primary Analysis** (Pair-level HLM) and **Secondary Analysis** (Project-level Regression), control for confounders, and generate visualization with 95% CI.

**Independent Test**: Run analysis on static CSV; verify output includes correlation coefficient, p-value, regression coefficients, and PNG scatter plot; **verify output contains stratified results per language/size tier in `data/derived/stratified_results.json`**.

### Implementation for User Story 3

- [ ] T026 [P] [US3] **SECONDARY ROBUSTNESS CHECK**: Implement Spearman rank correlation calculation in `code/analysis.py` using **project-level aggregated data** (median variance vs cohesion) as per FR-010. **Input**: `data/derived/project_metrics.csv` (T015) and `data/derived/cohesion_scores.csv` (T020). **Output**: `data/derived/secondary_correlation.json`. **Prerequisite**: T015, T020.
- [ ] T027 [US3] **SECONDARY ROBUSTNESS CHECK**: Implement linear regression model controlling for `team_size` and `project_age` in `code/analysis.py` using **project-level aggregated data**. **Input**: `data/derived/project_metrics.csv`. **Output**: `data/derived/secondary_regression.json`. **Prerequisite**: T015, T020.
- [ ] T028 [US3] Implement Variance Inflation Factor (VIF) check and halt-on-high-VIF logic in `code/analysis.py` (FR-008).
- [ ] T029 [US3] Implement Benjamini-Hochberg correction for secondary hypothesis tests: 1) Calculate stratified correlations by language (Python, JS, Go) and size tier (<10, ≥10). 2) Collect all p-values. 3) Sort p-values, calculate thresholds `p_i <= (i/m)*q`. 4) Identify significant results. **Output**: `data/derived/corrected_pvalues.json` (FR-007).
- [ ] T030 [US3] Implement scatter plot generation with regression line and 95% CI ribbon in `code/viz.py` (FR-006).
- [ ] T031 [US3] Generate separate correlation results and p-values for each stratum (language/size tier) and output a JSON file at `data/derived/stratified_results_temp.json` containing a list of objects with keys: `language`, `size_tier`, `spearman_r`, `p_value`. **Prerequisite**: T029. **Note**: This task outputs a temporary file to be merged by T031b.
- [ ] T031b [US3] **MERGE CORRECTIONS (SOLE PRODUCER)**: Read `data/derived/stratified_results_temp.json` (from T031) and `data/derived/corrected_pvalues.json` (from T029). Merge the corrected p-values into the stratified results. **Write the final, definitive artifact** to `data/derived/stratified_results.json`. **Output**: `data/derived/stratified_results.json`. **Prerequisite**: T029, T031. **Ownership**: This task is the **sole producer** of the final `stratified_results.json`. It must not modify existing files; it generates the final output from scratch using the inputs. **Note**: This resolves ambiguity about file ownership and ensures deterministic output.
- [ ] T031a [US3] Generate separate scatter plots with regression lines and 95% CI ribbons for each stratified subgroup (language/size tier) and save as PNGs (FR-007).
- [ ] T032 [US3] Ensure output formats (JSON/CSV) for statistical results include all required metrics (coefficients, p-values) (FR-004, FR-005).
- [ ] T033 [US3] Unit test for regression stability and VIF threshold enforcement in `tests/unit/test_analysis.py` (FR-008).
- [ ] T034 [US3] Integration test for full pipeline (Data → Sentiment → Analysis → Viz) in `tests/integration/test_pipeline.py`.
- [ ] T035 [US3] **PRIMARY ANALYSIS**: Implement Hierarchical Linear Model (HLM) in `code/analysis.py` using **pair-level data** (pair variance vs pair sentiment) with `project_id` as random effect. **Input**: `data/derived/pair_metrics.parquet` (T015a) and `data/derived/pair_sentiment.parquet` (T021b). **Output**: `data/derived/hlm_results.json`. **Note**: This is the Primary Analysis method per Plan Phase 3 Task 3.2.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `docs/`
- [ ] T036a [P] Implement streaming for sentiment analysis: Replace list accumulation in `code/sentiment.py` with `datasets.load_dataset(..., streaming=True)` and `itertools.islice` for batch processing. **Verification**: Add test to assert `peak_ram < 6.0 GB` during full run using `tracemalloc` or `memory_profiler`.
- [ ] T036b [P] Implement generator-based metrics calculation in `code/metrics.py` to avoid loading full event logs into memory.
- [ ] T036c [P] Implement memory mapping for large CSVs in `code/analysis.py` using `pandas.read_csv(..., chunksize=...)`.
- [ ] T037a [P] Profile ingestion module using `cProfile` to identify bottlenecks.
- [ ] T037b [P] Profile metrics module using `cProfile` to identify bottlenecks.
- [ ] T037c [P] Profile analysis module using `cProfile` to identify bottlenecks.
- [ ] T037d [P] Optimize identified bottlenecks to ensure runtime < 5.5 hours.
- [ ] T038 [P] Additional unit tests for edge cases (empty datasets, single contributor teams) in `tests/unit/`
- [ ] T039 Security hardening: ensure no API keys are logged and PII is filtered
- [ ] T040 Run `quickstart.md` validation and end-to-end execution check

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST depend on T015a completion** (Constitution Principle VI)
 - **T022a must be executed prior to T022c** (Sampling request needed before validation logic)
 - **T015a must be executed prior to T021b** (Pair IDs required for sentiment aggregation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2
 - **T015 must be executed prior to T026/T027** (Project-level aggregated data required for Secondary Analysis)
 - **T020 must be executed prior to T026/T027** (Cohesion scores required for analysis)
 - **T015a and T021b must be executed prior to T035** (Pair-level data required for Primary HLM)
 - **T029 must be executed prior to T031b** (Corrected p-values required for merge)
 - **T031 must be executed prior to T031b** (Intermediate results required for merge)

### Within Each User Story

- **T012a must be executed prior to T014 and T015** (Hard Prerequisite)
- **T018 must be executed prior to T024** (Language detection required for exclusion logging)
- **T024 must be executed prior to T025** (Logging required for test)
- **T031 must be executed prior to T031b** (Intermediate results required for merge)
- **T031b must be executed prior to T034** (Final stratified results required for integration test)
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
- **Critical Constraint**: Constitution Principle VI requires timestamp features to be persisted to `data/derived/timestamp_features.parquet` before sentiment analysis begins.
- **Critical Constraint**: Ground truth for validation must be ingested from external human annotation at `data/validation/manual_ground_truth.csv`. **IF MISSING, USE SYNTHETIC FALLBACK** per Plan Task 4.5.
- **Critical Constraint**: Stratified results must be output to `data/derived/stratified_results.json` and must contain Benjamini-Hochberg corrected p-values.
- **Critical Constraint**: Aggregation method for variance is **median** (per FR-010 in spec.md) for Secondary Analysis. T015 implements this. T035 implements HLM as the Primary Analysis.
- **Critical Constraint**: T023b must halt the pipeline if the validation threshold (ρ ≥ 0.5) is not met AND real data is used. If synthetic data is used, flag as UNVALIDATED.
- **Critical Constraint**: T031b is the **sole producer** of `data/derived/stratified_results.json`. T031 outputs to a temporary file `stratified_results_temp.json` to prevent race conditions. T031b reads the temporary file and the corrected p-values, merges them, and writes the final artifact from scratch.