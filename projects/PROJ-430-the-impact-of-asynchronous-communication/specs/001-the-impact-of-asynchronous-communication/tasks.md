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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-430-the-impact-of-asynchronous-communication/`)
- [ ] T002 Initialize Python 3.11 project with dependencies in `requirements.txt` (pandas, scikit-learn, nltk, requests, matplotlib, seaborn, pyyaml, langdetect, networkx)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/config.py` for paths, API keys, and deferred thresholds (sample_size, min_events)
- [ ] T005 [P] Implement `code/utils/hygiene.py` for SHA-256 hashing and state updates (Constitution Principle V)
- [ ] T006 [P] Setup `data/` directory structure (`raw/`, `derived/`, `validation/`) with `.gitignore` rules
- [~] T007 Create base data models/entities in `code/models.py` (Project, Event, ContributorPair, Metric)
- [~] T008 Configure logging infrastructure in `code/utils/logger.py` with JSON formatting for pipeline monitoring
- [~] T009 Setup rate-limit handling wrapper in `code/utils/github_client.py` for GitHub API interactions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Derivation (Priority: P1) 🎯 MVP

**Goal**: Download GitHub event data and calculate response-time variance and mean delay per contributor pair.

**Independent Test**: Execute ingestion script against known repositories; verify output CSV contains `response_time_variance` and `mean_delay` with non-null, positive values; verify accuracy against a set of manually calculated pairs (tolerance ≤ 0.01).

### Implementation for User Story 1

- [~] T010 [US1] Implement `code/data_ingestion.py` to fetch issues, PRs, and comments for a sample of projects (FR-001)
- [~] T011 [US1] Implement bot-exclusion logic in `code/data_ingestion.py` (filter names ending in '[bot]' or GitHub Apps) (FR-002)
- [~] T012a [US1] Implement Contributor Pair identification and metric calculation in `code/metrics.py`: identify pairs as any two distinct authors who have exchanged at least one message (excluding self-replies and internal bot events), calculate inter-arrival times, `response_time_variance`, and `mean_delay` (FR-002)
- [~] T014 [US1] Implement project-level filtering for insufficient data (< min_events) in `code/data_ingestion.py` (FR-001)
- [~] T015 [US1] Aggregate pair-level variances to a project-level metric using the **weighted mean** (per plan.md Complexity Tracking) to address statistical instability (FR-010)
- [~] T015a [US1] Persist intermediate timestamp-derived features to `data/derived/timestamp_features.parquet` to enforce Constitution Principle VI (Modality Separation) (FR-002, Const VI) 👉 **Handoff to US2**
- [~] T016 [US1] Add error handling for API rate limits and large datasets (chunking if >100k events) to prevent OOM (FR-001)
- [ ] T017 [US1] Unit test for metric derivation accuracy in `tests/unit/test_metrics.py` (compare against ground truth)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cohesion Proxy Calculation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and language detection to derive `cohesion_proxy_score` and validate against manual coding.

**Independent Test**: Process a set of manually annotated comments; verify VADER scores correlate with manual trend; verify non-English text exclusion rate is logged **per project** (JSON format); verify existence and format of `data/validation/manual_ground_truth.csv`.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement language detection filter in `code/sentiment.py` using `langdetect` (confidence ≥ 0.95) (FR-011)
- [ ] T019 [US2] Implement VADER sentiment analysis for English-only text in `code/sentiment.py` (FR-003)
- [ ] T020 [US2] Implement project-level `cohesion_proxy_score` aggregation (weighted average of compound scores) in `code/sentiment.py` (FR-003)
- [ ] T021 [US2] Handle edge case: projects with no text content (assign 0 or flag "no_text_data") in `code/sentiment.py`
- [ ] T022 [US2] Implement logic to select a representative sample of comments per project for manual coding and prepare the request file (schema and sampling list) for external human annotation (FR-009)
- [ ] T022b [US2] Implement ingestion of the external human-annotated CSV at `data/validation/manual_ground_truth.csv` (columns: `project_id`, `comment_id`, `manual_cohesion_score`) (FR-009)
- [ ] T023 [US2] Implement multi-modal validation logic (preparation) to align VADER scores with the manual ground truth data (FR-009)
- [ ] T023a [US2] Calculate Spearman correlation (ρ) between VADER scores and manual scores; output pass/fail against threshold ρ ≥ 0.5 (SC-005)
- [ ] T024 [US2] Calculate and log the exclusion rate for non-English text **per project** in `code/utils/logger.py` (FR-011); Log a JSON line for each project with fields: `project_id`, `total_comments`, `excluded_count`, `exclusion_rate`
- [ ] T025 [US2] Unit test for sentiment score correlation with manual annotations in `tests/unit/test_sentiment.py` (FR-009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform Spearman correlation, controlled linear regression, and generate visualization with 95% CI.

**Independent Test**: Run analysis on static CSV; verify output includes correlation coefficient, p-value, regression coefficients, and PNG scatter plot; **verify output contains stratified results per language/size tier in `data/derived/stratified_results.json`**.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement Spearman rank correlation calculation in `code/analysis.py` (FR-004)
- [ ] T027 [US3] Implement linear regression model controlling for `team_size` and `project_age` in `code/analysis.py` (FR-005)
- [ ] T028 [US3] Implement Variance Inflation Factor (VIF) check and halt-on-high-VIF logic in `code/analysis.py` (FR-008)
- [ ] T029 [US3] Implement Benjamini-Hochberg correction for secondary hypothesis tests: First calculate stratified correlations by language and size tier, then apply the correction to the resulting set of p-values (FR-007)
- [ ] T030 [US3] Implement scatter plot generation with regression line and 95% CI ribbon in `code/viz.py` (FR-006)
- [ ] T031 [US3] Generate separate correlation results and p-values for each stratum (language/size tier) and output a JSON file at `data/derived/stratified_results.json` containing a list of objects with keys: `language`, `size_tier`, `spearman_r`, `p_value` (FR-007)
- [ ] T031a [US3] Generate separate scatter plots with regression lines and 95% CI ribbons for each stratified subgroup (language/size tier) and save as PNGs (FR-007)
- [ ] T032 [US3] Ensure output formats (JSON/CSV) for statistical results include all required metrics (coefficients, p-values) (FR-004, FR-005)
- [ ] T033 [US3] Unit test for regression stability and VIF threshold enforcement in `tests/unit/test_analysis.py` (FR-008)
- [ ] T034 [US3] Integration test for full pipeline (Data → Sentiment → Analysis → Viz) in `tests/integration/test_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `README.md` and `docs/`
- [ ] T036 [P] Code cleanup and refactoring for memory efficiency (ensure RAM < 6.0 GB)
- [ ] T036a [P] Implement streaming or chunked processing for sentiment analysis and correlation steps: Process in batches of [deferred] events and discard from memory after aggregation to ensure RAM < 6.0 GB (SC-004)
- [ ] T037 Performance optimization for large event logs (ensure runtime < 5.5 hours)
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
 - **T022b must be executed prior to T023a** (Ground truth required for validation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2

### Within Each User Story

- **T012a must be executed prior to T014 and T015** (Hard Prerequisite)
- **T024 must be executed prior to T025** (Logging required for test)
- **T031/T031a must be executed prior to T034** (Stratified results required for integration test)
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
- **Critical Constraint**: No GPU required; use CPU-only libraries (scikit-learn, pandas, nltk).
- **Critical Constraint**: Constitution Principle VI requires timestamp features to be persisted to `data/derived/timestamp_features.parquet` before sentiment analysis begins.
- **Critical Constraint**: Ground truth for validation must be ingested from external human annotation at `data/validation/manual_ground_truth.csv` (T022b); do not simulate.
- **Critical Constraint**: Stratified results must be output to `data/derived/stratified_results.json` and visualized (T031a).
- **Critical Constraint**: Aggregation method for variance is **weighted mean** (per plan.md), not median.