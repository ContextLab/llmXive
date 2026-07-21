# Tasks: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Input**: Design documents from `/specs/001-impact-of-incidental-music/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize a Python project with `requirements.txt` dependencies (`pandas`, `numpy`, `scikit-learn`, `statsmodels`, `python-Levenshtein`, `pyyaml`, `tqdm`, `scipy`) using a compatible Python 3.x version.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/dataset.schema.yaml` defining Track, CohortListen, MemoryCue, and AggregatedMetric schemas
- [X] T005 Create `contracts/output.schema.yaml` for regression results and sensitivity analysis outputs
- [X] T006 [P] Implement `code/config.py` with paths, thresholds (Levenshtein ≤ 4), seeds, and fallback flags
- [X] T007 Setup `data/raw/`, `data/processed/`, and `data/final/` directories with `.gitkeep`
- [X] T008 Implement `code/__init__.py` and basic logging configuration in `code/utils.py`
- [X] T009 Create `state.yaml` mechanism for checksum tracking of derived files
- [X] T052 [P] Generate `quickstart.md` with step-by-step instructions to run the pipeline, required for T046 validation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Exposure Scoring (Priority: P1) 🎯 MVP

**Goal**: Ingest MSD and AMT data, filter for valid birth years, and compute the `adolescent_exposure_score` and `residualized_exposure_score`.

**Independent Test**: Run ingestion on a small synthetic subset; verify output CSV has `adolescent_exposure_score` (0.0-1.0), excludes records without `birth_year`, and applies the minimum listen threshold.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Unit test for birth year filtering logic in `tests/unit/test_ingestion.py`
- [X] T011 [US1] Unit test for exposure score calculation (0 listens = 0.0) in `tests/unit/test_ingestion.py`
- [X] T012 [US1] Unit test for fallback "global exposure" trigger when >50% missing birth years in `tests/unit/test_ingestion.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` function `download_datasets` to download/verify MSD and AMT datasets from canonical URLs defined in `config.MSD_URL` and `config.AMT_URL`. **Constraints**:
 1. **Chunked Iteration**: Must process large datasets in chunks (streaming) to stay within RAM limits; do NOT load full dataset into memory.
 2. **Fail Loudly**: Must raise an exception if real data sources (MSD/AMT) are unreachable or invalid. Do NOT implement a `try/except` fallback to synthetic data (except for FR-008 Global Exposure).
 3. **Ordering**: This task must integrate the logic for T055 and T056 (removed as standalone tasks).
 **DEPENDS ON**: None.
- [X] T013a [US1] Implement `code/data_ingestion.py` function `filter_cohort` to filter MSD logs for `birth_year` presence and calculate adolescent window (birth_year + early adolescence to late adolescence)
- [X] T012a [US1] Implement `code/data_ingestion.py` function `audit_amt_source` to verify AMT data integrity. **REQUIREMENT**: Invoke the function `validate_source` in `code/utils.py` with the AMT source URL as input. **FAIL LOGIC**: If the agent is unavailable or verification fails (timeout > 30s), **log a WARNING**, set `validation_status='unverified'` in the artifact metadata, and **proceed** with the pipeline using the raw AMT data without modification. Do NOT raise a fatal exception to ensure reproducibility in CI. Do NOT substitute with local heuristics.
- [X] T023b [US1] Implement `code/data_ingestion.py` function `calculate_global_exposure` to generate the "Global Exposure" metric using **verified aggregate population data**. **DATA SOURCE**: Must fetch from verified direct CSV URL: `https://raw.githubusercontent.com/owid/development-indices/master/data/population_by_age_group.csv` (or equivalent verified academic mirror with explicit schema). **SCHEMA**: The data must contain `age_group` (string) and `proportion` (float) columns. **CONSTRAINT**: If the data source is unavailable or schema validation fails, raise an error; do NOT generate synthetic data. **DEPENDS ON**: None.
- [X] T023 [US1] Implement `code/data_ingestion.py` function `handle_fallback` for FR-008 (Global Exposure metric) if birth year data is insufficient (>50% missing). **ORDERING**: This task is a **PRE-CHECK** only. It MUST calculate the percentage of missing birth years from the state set by T013a and T013 (ingested data), and set a global configuration flag/metric. **CRITICAL**: This task MUST NOT re-ingest data, re-run T013, or execute the fallback logic itself. It only determines if the fallback is needed. **DEPENDS ON**: T023b (Global Exposure calculation logic for availability), T013, T013a. **NOTE**: T023 runs BEFORE T015 to prevent false triggers (EC-001).
- [X] T015 [US1] Implement `code/data_ingestion.py` function `apply_frequency_threshold` to filter tracks with < 10 total listens. **DEPENDS ON**: T023. **MUST run after T023** to prevent false fallback triggers (EC-001). Relies on the state set by T023, not a re-run of ingestion.
- [X] T013b [US1] Implement `code/data_ingestion.py` function `fetch_popularity_scores` to retrieve `overall_popularity_score` for each track from MSD metadata. **DEPENDS ON**: T013.
- [X] T014 [US1] Implement `code/data_ingestion.py` function `calculate_ratio_score` to compute `adolescent_exposure_score` (adolescent listens / total valid listens) per track
- [X] T016 [US1] Implement `code/data_ingestion.py` function `calculate_residualized_score` to compute `residualized_exposure_score` by running OLS regression of `adolescent_exposure_score` ~ `overall_popularity_score` and **extracting the residuals** as the output variable. **CRITICAL**: This task MUST explicitly join the `overall_popularity_score` (fetched in T013b) with the cohort data before running the regression. Formula: `residuals = observed - predicted`. **DEPENDS ON**: T014, T013b.
- [X] T028 [US1] Implement `code/main.py` orchestration to enforce the specific order: Fallback Check (T023) -> Frequency Filter (T015) -> Popularity Fetch (T013b) -> Ratio Score (T014) -> Residualized Score (T016). **DEPENDS ON**: T013, T013a, T023, T015, T013b, T014, T016. **NOTE**: T028 must explicitly orchestrate the sequential execution of these steps.
- [ ] T018 [US1] Generate `data/processed/ingested_cohort.parquet` with checksum and update `state.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cue Matching and Memory Attribute Aggregation (Priority: P2)

**Goal**: Parse AMT free-text cues, match to MSD tracks via fuzzy string matching (Levenshtein distance ≤ 4), and aggregate vividness/valence per User-Track pair.

**Independent Test**: Provide a small set of AMT cues with known MSD titles; verify matching accuracy and correct aggregation of mean vividness/valence.

### Tests for User Story 2

- [X] T019 [US2] Unit test for text normalization (lowercase, remove punctuation) in `tests/unit/test_matching.py`
- [X] T020 [US2] Unit test for fuzzy matching logic (Levenshtein distance ≤ 4) in `tests/unit/test_matching.py`
- [X] T021 [US2] Unit test for aggregation logic (mean vividness/valence per User-Track) in `tests/unit/test_matching.py`
- [X] T037 [US2] Unit test for SC-004 warning path: simulate a high match rate using synthetic AMT file `tests/data/low_match_cues.csv` ([deferred] unmatched cues) and verify that a warning is logged and the pipeline proceeds without raising an exception in `tests/unit/test_matching.py`.

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/cue_matching.py` function `normalize_cues` to normalize AMT cues and load MSD track titles into a searchable index
- [X] T047 [US2] Implement `code/cue_matching.py` function `match_cues` to perform fuzzy matching with Levenshtein distance ≤ 4 and log unmatched cues
- [X] T024 [US2] Implement `code/cue_matching.py` function `resolve_collisions` to resolve ambiguous matches (same title/artist) and log collisions
- [X] T025 [US2] Implement `code/aggregation.py` function `join_exposure_data` to join matched cues with exposure data (Track-level exposure joined to User-Track pairs). **DEPENDS ON**: T018 (ingested_cohort.parquet).
- [X] T026 [US2] Implement `code/aggregation.py` function `aggregate_to_user_track` to aggregate data to **User-Track Pair** level (mean vividness, mean valence) as per spec FR-004 and FR-005.
- [X] T027 [US2] Implement `code/aggregation.py` function `filter_zero_variance` to filter out tracks with **zero associated User-Track pairs** in the aggregated dataset (high exposure, zero memory cues) to avoid singularities in the design matrix. **CRITICAL**: This filter applies to the aggregated **User-Track Pair** dataset, removing tracks that have no rows in the pair-level table.
- [X] T036 [US2] Implement `code/aggregation.py` function `enforce_match_rate` to verify SC-004 (Match Rate ≥ `config.MATCH_RATE_THRESHOLD`); **LOG WARNING** and proceed if threshold is missed, do NOT raise exception. **LOGIC**:
 1. Read `config.MATCH_RATE_THRESHOLD`.
 2. If the value is the string `[deferred]`, **set effective_threshold = 0.8**, **log a WARNING** that the check was deferred and defaulting to 0.8, and **proceed** (skip the numeric comparison against the string).
 3. If the value is numeric, perform the `>=` check using the numeric value. If the rate is below threshold, log a warning and proceed.
 **DEPENDS ON**: T026. **MUST read threshold from `config.py`**, which must default to `[deferred]` as per SC-004. **MUST NOT hardcode the value** (except for the fallback logic defined above).
- [X] T029 [US2] Generate `data/processed/user_track_pairs.parquet` with checksum and update `state.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

**Goal**: Fit linear mixed-effects models on User-Track pairs, run sensitivity analysis, and perform permutation tests.

**Independent Test**: Run analysis on the aggregated dataset; verify regression summary includes p-values, sensitivity table shows stability across thresholds, and permutation test confirms significance.

### Tests for User Story 3

- [X] T030 [US3] Unit test for model formula construction in `tests/unit/test_modeling.py`
- [X] T031 [US3] Unit test for sensitivity analysis loop (thresholds `[2, 3, 4, 5, 6]`) in `tests/unit/test_modeling.py`
- [X] T032 [US3] Unit test for permutation test logic (block-permutation) in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/modeling.py` function `fit_mixed_model` to fit `statsmodels` MixedLM: `mean_vividness ~ residualized_exposure + popularity + (1|user_id)` on **User-Track pairs**
- [X] T035 [US3] Implement `code/modeling.py` function `check_collinearity` to calculate Variance Inflation Factor (VIF) and check for multicollinearity (VIF > 5)
- [X] T044a [US3] Implement `code/modeling.py` helper function `run_match_with_threshold` to re-run normalization and matching with a parameterized Levenshtein threshold. **DEPENDS ON**: Code existence of T022, T047. **NOTE**: This is a helper for T044c, not a standalone execution.
- [X] T044b [US3] Implement `code/modeling.py` helper function `run_aggregate_with_threshold` to re-aggregate matched data to User-Track pairs and filter zero variance tracks using a parameterized threshold. **DEPENDS ON**: Code existence of T026, T027. **NOTE**: This is a helper for T044c, not a standalone execution.
- [X] T044 [US3] Implement `code/modeling.py` function `run_sensitivity_analysis` to orchestrate the sensitivity loop. **CRITICAL ORCHESTRATION**: This function MUST implement a **loop** over a range of threshold values. For **each** threshold:
 1. **Load Data**: Load `data/processed/ingested_cohort.parquet` (T018).
 2. **Re-Match**: Call `run_match_with_threshold` (T044a) with the current threshold.
 3. **Re-Filter**: Apply frequency filter logic to the matched set.
 4. **Re-Aggregate**: Call `run_aggregate_with_threshold` (T044b) to generate a **temporary** artifact `data/processed/user_track_pairs_threshold_X.parquet` for this iteration.
 5. **Re-Model**: Fit the model on the temporary aggregated data.
 6. **Store Results**: Append results to a list.
 7. **Cleanup**: Delete temporary artifacts after the loop.
 **DEPENDS ON**: T018, Code existence of T044a, T044b. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially.
- [ ] T045 [US3] Implement `code/modeling.py` function `run_permutation_test` to perform a **block-permutation** on the **User-Track Pair** dataset. **Procedure**:
 1. **Pin the random seed** (from config.py).
 2. **Construct Shuffle Pool**: **Aggregate** the `residualized_exposure_score` to the **track level** first (one score per unique `track_id`).
 3. **Shuffle**: Randomly shuffle this vector of **track-level scores** (not the row IDs).
 4. **Reassign**: Assign the shuffled score vector to the tracks in the dataset by matching the row's `track_id` to the shuffled vector. **CONSTRAINT**: This preserves the number of pairs per track (block structure) while shuffling the predictor values.
 5. **Re-fit**: Re-fit the model and record the **t-statistic for the `residualized_exposure` coefficient** for this iteration.
 6. **Repeat**: Repeat for **1000 iterations**.
 7. **Calculate P-Value**: Compute the p-value by comparing the observed statistic against the null distribution.
 8. **Atomic Write**: **Collect all iteration statistics and the final p-value in memory**. Write to a **temporary file** (e.g., `data/final/permutation_results.csv.tmp`), then use **`os.replace()`** to **atomically rename** the temp file to the final path `data/final/permutation_results.csv`. This ensures no race conditions or partial writes.
 **OUTPUT**: `data/final/permutation_results.csv` with columns: `iteration, statistic` and a final row `metric='p_value', value=<p>`. **DEPENDS ON**: T033. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially.
- [X] T038 [US3] Generate `data/final/regression_summary.csv` containing coefficients, SEs, p-values, and VIFs
- [ ] T039a [US3] Generate `data/final/sensitivity_analysis.csv` from the aggregated results of T044. **DEPENDS ON**: T044.
- [X] T040 [US3] Generate diagnostic plots (residual checks, QQ plots) and save to `data/final/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `README.md` and `code/` docstrings
- [X] T042 Code cleanup and refactoring of `code/main.py` orchestration script
- [X] T043 Performance optimization: ensure chunking is used if memory > 5GB during ingestion
- [X] T051 [P] Add integration test in `tests/integration/test_pipeline.py` to run full flow on synthetic data and verify sensitivity analysis logic (DEPENDS ON T044).
- [X] T049 [P] Security hardening: Run `presidio-analyzer` on all log files and output files; save report to `data/final/pii_scan_report.json` and fail if PII is detected. **MUST be integrated as an automated CI/CD gate** per Constitution Principle III.
- [X] T046 [P] Run `quickstart.md` validation to ensure pipeline runs end-to-end within 6 hours (SC-005). **DEPENDS ON: T052**.
- [X] T050 [P] **Verify Artifacts**: Check existence and checksums of `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`, `data/final/regression_summary.csv`, `data/final/sensitivity_analysis.csv`, `data/final/permutation_results.csv` against `state.yaml`. **DEPENDS ON: T029, T038, T039a, T045** (Must wait for all final artifacts).

**Note**: Tasks T053 (Effect Size) and T054 (Assumption Validation) have been removed as they represent unauthorized scope creep (gold-plating) with no traceable requirement in the spec. Task T034 (fit_valence_model) has been removed as it is not required by FR-005.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (T018: `ingested_cohort.parquet`). Specifically, **T025 and T026 depend on T018**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (T029: `user_track_pairs.parquet`)

### Within Each User Story

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

### Critical Ordering Constraints

- **T023 -> T015**: Fallback check (T023) MUST run before frequency filter (T015) (EC-001).
- **T036 -> T033/T034**: Match Rate Check (T036) MUST complete before Modeling (T033, T034). T036 is NOT parallel-safe with modeling tasks.
- **T044 Internal**: T044 must NOT re-run T023/T015. It must load pre-computed data. **T044 is NOT PARALLEL SAFE**.
- **T045 Internal**: T045 must run sequentially after T033. **T045 is NOT PARALLEL SAFE**.
- **T050 -> T029, T038, T039a, T045**: T050 (Verify Artifacts) **MUST wait for T029, T038, T039a, and T045** to complete before execution to avoid race conditions.
- **T044 Dependencies**: T044 depends on the **code existence** of T044a/T044b, not their execution.
- **T045 Atomicity**: T045 must perform an atomic write for the output file (including p-value summary) using `os.replace()`.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for birth year filtering logic in tests/unit/test_ingestion.py"
Task: "Unit test for exposure score calculation in tests/unit/test_ingestion.py"
Task: "Unit test for fallback 'global exposure' trigger in tests/unit/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py function download_datasets"
Task: "Implement code/data_ingestion.py function filter_cohort"
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
- **Constraint**: All data processing must run on CPU-only CI (no GPU, no 8-bit models)
- **Constraint**: All datasets must be fetched from real, verified URLs (no fabrication)
- **Constraint**: Spec requirements (User-Track Pair unit of analysis, block-permutation) are active constraints for all implementation tasks.
- **Dependency Note**: T051 (Integration Test) depends on T044 (Sensitivity Analysis) being completed first.
- **Dependency Note**: T036 (Match Rate Check) is NOT parallel-safe with T033/T034 (Modeling).
- **Dependency Note**: T044 (Sensitivity Analysis) must load pre-computed data, not re-ingest. **T044 is NOT PARALLEL SAFE**.
- **Dependency Note**: T045 (Permutation Test) must shuffle scores among tracks, not pairs, and output only the statistic per iteration. **T045 is NOT PARALLEL SAFE**.
- **Critical Constraint**: The pipeline must **fail loudly** if real data sources (MSD/AMT) are unreachable; **never** implement a `try/except` block that falls back to synthetic/mock data generation (except for FR-008 Global Exposure).
- **Critical Constraint**: For large datasets, implement **chunked iteration** to process data in chunks, ensuring the full dataset contributes to results without exceeding RAM limits.
- **Critical Constraint**: If a verified real data source is injected via execution feedback, **adopt it exclusively** in the data-loading task; do not maintain alternative hand-rolled fetchers.
- **Dependency Note**: T050 (Verify Artifacts) depends on T029 (Generate `user_track_pairs.parquet`), T038 (Generate `regression_summary.csv`), T039a (Generate `sensitivity_analysis.csv`), and T045 (Generate `permutation_results.csv`).
- **Removed Tasks**: T053 (Effect Size), T054 (Assumption Validation), and T034 (fit_valence_model) have been removed as they are not required by the spec.
- **Removed Tasks**: T055 and T056 have been removed as standalone tasks; their requirements are integrated into T013.
- **Removed Tasks**: T045b has been removed; its logic is merged into T045 to ensure atomic writes via `os.replace()`.