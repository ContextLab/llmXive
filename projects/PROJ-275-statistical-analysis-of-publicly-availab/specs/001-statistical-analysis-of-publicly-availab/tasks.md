# Tasks: Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

**Input**: Design documents from `/specs/001-sentiment-revenue-lag-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `results/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with **exact version pinning** (e.g., `pandas==2.0.3`) in `code/requirements.txt` (pandas, numpy, scikit-learn, nltk, scipy, statsmodels, fuzzywuzzy, pytest) to satisfy Constitution Principle I
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `Reference-Validator` script in `code/reference_validator.py` to verify dataset URLs against `research.md` and halt on mismatch (Constitution Principle II); if any URL fails, halt pipeline and log specific failure to `data/logs/validation_error.log`
- [ ] T005 Create schema contracts in `specs/001-sentiment-revenue-lag-analysis/contracts/`: `dataset.schema.yaml` and `analysis_results.schema.yaml`
- [ ] T006 Implement schema validation utilities in `code/tests/test_dataset_schema.py` and `code/tests/test_analysis_results_schema.py`
- [X] T007 Create base data entities and configuration loader in `code/config.py` and `code/entities.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Preprocessing & Sentiment (Priority: P1) 🎯 MVP

**Goal**: Download, merge, filter, and score the TMDB 5000 and IMDb datasets to create a unified, time-aligned dataset with ≥500 valid movies and weekly sentiment scores. **Revenue remains a static anchor.**

**Independent Test**: The pipeline can be tested by executing the data ingestion script and verifying that the output CSV contains at least 500 movies with non-null values for `opening_weekend_revenue` and `sentiment_score` columns, along with valid `release_date` and `review_timestamp` fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Contract test for merged dataset schema in `code/tests/test_dataset_schema.py`

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `download_datasets()` in `code/data_ingestion.py` to fetch TMDB 5000 and IMDb Reviews from verified public URLs defined in `research.md#verified-datasets` using `wget`
- [X] T010 [US1] Implement `merge_datasets()` in `code/data_ingestion.py` to join on movie title/year using `pandas` with fuzzy matching fallback
- [~] T011 [US1] Implement `filter_valid_movies()` in `code/data_ingestion.py` to exclude movies with missing revenue or <3 months of review history; **must** log the count of excluded movies and the final count to `data/logs/ingestion_log.txt`, and **raise an error** if final count < 500
- [X] T012 [US1] Implement `align_timestamps()` in `code/data_ingestion.py` to create a weekly **sentiment** time-series structure aligned to `release_date`; **explicitly treat `opening_weekend_revenue` as a static anchor** (broadcast to all weeks) and **enforce** the 3-month minimum history check defined in FR-002 during this step
- [X] T015 [US1] Implement `compute_vader_sentiment()` in `code/sentiment_analysis.py` using `nltk.vader` (CPU-only) to score weekly review text and merge scores into the time-series structure
- [ ] T013 [US1] Save intermediate `data/processed/merged_clean.parquet` and log row counts to `data/logs/ingestion_log.txt`; **must verify** output contains columns `title`, `release_date`, `opening_weekend_revenue` (static), `sentiment_score`, `genre` and `row_count >= 500`; **fail** if not

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (includes sentiment scores and static revenue anchors)

---

## Phase 4: User Story 2 - Temporal Lag and Correlation Analysis (Priority: P2)

**Goal**: Compute the **Lagged Correlation Profile** (aggregate analysis) to identify the optimal time lag between sentiment trends and static revenue, aggregated by genre.

**⚠️ DEPENDENCY**: This phase strictly depends on the completion of Phase 3 (US1). US2 cannot start until the sentiment-scored dataset (with static revenue anchors) is available.

**Independent Test**: The analysis module can be tested by running it on a synthetic dataset with known aggregate lag patterns (e.g., sentiment leads revenue by a defined temporal interval) including realistic noise structures and verifying the computed lag matches the ground truth within a tolerance of ±1 week.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T014 [P] [US2] Unit test for aggregate lag calculation with synthetic ground-truth data in `code/tests/test_lag_logic.py`

### Implementation for User Story 2

- [ ] T016a [US2] Implement `differencing_sentiment()` in `code/lag_decay_analysis.py` to apply first-order differencing to the weekly **sentiment** time-series for stationarity
- [ ] T016b [US2] Implement `compute_sentiment_trend_relative_to_revenue()` in `code/lag_decay_analysis.py` to compute the correlation between the **aggregate** sentiment trend (averaged per genre) and the **static** `opening_weekend_revenue` anchor, treating revenue as a constant for the correlation calculation (as required by the Plan's 'Lagged Correlation Profile' methodology)
- [ ] T017 [US2] Implement `calculate_genre_lag_profile()` in `code/lag_decay_analysis.py` using `scipy.signal.correlate` on **aggregate** sentiment series to find the max absolute correlation lag **by genre** (not per-movie), then store the optimal lag for each genre
- [ ] T018 [US2] Implement `bootstrap_lag_aggregation()` in `code/lag_decay_analysis.py` to compute median lag and Confidence interval per genre using bootstrap resampling of movies
- [ ] T019 [US2] Save `results/lag_analysis_by_genre.csv` and generate preliminary `results/plot_lag_distribution.png`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Decay Rate Estimation and Reporting (Priority: P3)

**Goal**: Calculate the decay rate of the **aggregate** sentiment-revenue correlation over the theatrical run and generate final report artifacts.

**Independent Test**: The reporting module can be tested by verifying that the generated plots correctly show a decreasing correlation trend over weeks for a subset of movies using the aggregate profile.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US3] Unit test for Fisher Z-transformation and decay slope calculation in `code/tests/test_decay_logic.py`

### Implementation for User Story 3

- [ ] T021 [P] [US3] Implement `fisher_z_transform()` in `code/lag_decay_analysis.py` to normalize correlation coefficients
- [ ] T022 [US3] Implement `calculate_decay_rate()` in `code/lag_decay_analysis.py` using linear regression on Z-transformed **aggregate** correlations over the 12-week window to determine the decay slope per genre
- [ ] T023 [US3] Implement `generate_summary_tables()` in `code/reporting.py` to output mean decay rate, p-value (calculated via **Mann-Whitney U test** against the null hypothesis that "median lag difference between genre pairs is zero"), and N per genre
- [ ] T024 [US3] Implement `generate_lag_decay_plots()` in `code/reporting.py` to create final visualizations
- [ ] T025 [US3] Compile `results/final_report.md` including tables from T023, plots from T024, and a conclusion section summarizing genre-specific lag patterns as per US-3 acceptance criteria
- [ ] T026 [US3] Validate final output against `contracts/analysis_results.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Documentation updates in `specs/001-sentiment-revenue-lag-analysis/quickstart.md`
- [ ] T028 Code cleanup and refactoring in `code/`
- [ ] T029 [P] Performance optimization: Ensure pipeline runs within the fixed runtime limit defined in the Plan's Performance Goals (< 4 hours) on a CPU-only runner
- [ ] T031 [P] Run `pytest` on all unit and contract tests to verify schema compliance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Produces the sentiment-scored dataset with static revenue anchors
- **User Story 2 (Phase 4)**: **Strictly depends** on Phase 3 completion (cannot run in parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Phase 4 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Must wait** for User Story 1 to produce the sentiment-scored dataset with static revenue
- **User Story 3 (P3)**: Must wait for User Story 2 to produce lag results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/reporting
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- **Note**: User Stories 2 and 3 are strictly sequential and cannot run in parallel with US1 or each other due to data dependencies.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for merged dataset schema in code/tests/test_dataset_schema.py"

# Launch all data ingestion tasks for User Story 1 together:
Task: "Implement download_datasets() in code/data_ingestion.py"
Task: "Implement merge_datasets() in code/data_ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (includes sentiment scoring and static revenue anchors)
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
 - Developer B: Prepare Unit Tests for US2/US3
3. Once US1 completes:
 - Developer A: User Story 2
 - Developer B: User Story 3 (preparation)
4. Stories complete and integrate sequentially.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All dataset downloads MUST use verified public URLs (HuggingFace/Kaggle mirrors) as defined in `research.md`. No synthetic/fake data generation for input.
- **CRITICAL**: Revenue data is **static** (`opening_weekend_revenue`). Tasks MUST NOT attempt to construct a weekly revenue time-series. Analysis must use the 'Lagged Correlation Profile' (aggregate) method treating revenue as a constant anchor.
- **CRITICAL**: Statistical tests (T023) must explicitly define the null hypothesis and test method (e.g., Mann-Whitney U) to satisfy SC-003.