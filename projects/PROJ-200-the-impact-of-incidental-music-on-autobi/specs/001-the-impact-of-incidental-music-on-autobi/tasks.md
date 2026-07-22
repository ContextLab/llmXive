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
- [X] T023 [US1] Implement `code/data_ingestion.py` function `check_fallback_trigger` for FR-008 (Global Exposure metric) check. **ORDERING**: This task is a **PRE-CHECK** only. It MUST calculate the percentage of missing birth years from the **raw ingested data** (output of T013, before any filtering). **CRITICAL**: This task MUST NOT depend on T013a or T015. It must run on the raw dataset to satisfy EC-001. **LOGIC**:
 1. Calculate `missing_pct = count(missing_birth_year) / count(total_raw_records)`.
 2. If `missing_pct > 0.5`:
    - **CHECK SPEC**: Verify if a valid 'aggregate population data' source is defined in `spec.md` or `plan.md`.
    - **IF NO SOURCE DEFINED**: Raise a **FATAL EXCEPTION** stating: "FR-008 Fallback Triggered (>50% missing birth years) but no valid 'aggregate population data' source is defined in the specification. Pipeline cannot proceed. Please define a verified data source in spec.md."
    - **IF SOURCE DEFINED**: Proceed to implement the fallback logic (not implemented in this scope as no source exists).
 3. If `missing_pct <= 0.5`: Proceed normally.
 **DEPENDS ON**: T013 (raw ingestion). **DO NOT** depend on T013a or T015. **NOTE**: T023 runs BEFORE T013a to prevent false triggers (EC-001).
- [X] T013a [US1] Implement `code/data_ingestion.py` function `filter_cohort` to filter MSD logs for `birth_year` presence and calculate adolescent window (birth_year + early adolescence to late adolescence). **DEPENDS ON**: T013, T023. **MUST run after T023** to ensure the fallback check is performed on the raw dataset first (EC-001).
- [X] T012a [US1] Implement `code/data_ingestion.py` function `audit_amt_source` to verify AMT data integrity. **REQUIREMENT**: Invoke the function `validate_source` in `code/utils.py` with the AMT source URL as input. **FAIL LOGIC**: If the agent is unavailable or verification fails (timeout > 30s), **raise a fatal exception** to stop the pipeline. Do NOT proceed with unverified data. Do NOT substitute with local heuristics.
- [X] T015 [US1] Implement `code/data_ingestion.py` function `apply_frequency_threshold` to filter tracks with < 10 total listens. **DEPENDS ON**: T023, T013a. **MUST run after T013a** to prevent false fallback triggers (EC-001). Relies on the state set by T013a, not a re-run of ingestion.
- [X] T013b [US1] Implement `code/data_ingestion.py` function `fetch_popularity_scores` to retrieve `overall_popularity_score` for each track from MSD metadata. **DEPENDS ON**: T013.
- [X] T014 [US1] Implement `code/data_ingestion.py` function `calculate_ratio_score` to compute `adolescent_exposure_score` (adolescent listens / total valid listens) per track
- [X] T016 [US1] Implement `code/data_ingestion.py` function `calculate_residualized_score` to compute `residualized_exposure_score` by running OLS regression of `adolescent_exposure_score` ~ `overall_popularity_score` and **extracting the residuals** as the output variable. **CRITICAL**: This task MUST explicitly join the `overall_popularity_score` (fetched in T013b) with the cohort data before running the regression. Formula: `residuals = observed - predicted`. **DEPENDS ON**: T014, T013b.
- [X] T028 [US1] Implement `code/main.py` orchestration to enforce the specific order: Fallback Check (T023) -> Filter Cohort (T013a) -> Frequency Filter (T015) -> Popularity Fetch (T013b) -> Ratio Score (T014) -> Residualized Score (T016). **DEPENDS ON**: T013, T013a, T023, T015, T013b, T014, T016. **NOTE**: T028 must explicitly orchestrate the sequential execution of these steps.
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
- [X] T025 [US2] Implement `code/aggregation.py` function `join_exposure_data` to join matched cues with exposure data (Track-level exposure joined to User-Track pairs). **DEPENDS ON**: T018 (ingested_cohort.parquet). **NOTE**: T018 must be generated before this task runs.
- [X] T026 [US2] Implement `code/aggregation.py` function `aggregate_to_user_track` to aggregate data to **User-Track Pair** level (mean vividness, mean valence) as per spec FR-004 and FR-005.
- [X] T027 [US2] Implement `code/aggregation.py` function `filter_zero_variance` to filter out tracks with **zero associated User-Track pairs** in the aggregated dataset (high exposure, zero memory cues) to avoid singularities in the design matrix. **CRITICAL**: This filter applies to the aggregated **User-Track Pair** dataset, removing tracks that have no rows in the pair-level table.
- [X] T036 [US2] Implement `code/aggregation.py` function `enforce_match_rate` to verify SC-004 (Match Rate ≥ `config.MATCH_RATE_THRESHOLD`); **LOG WARNING** and proceed if threshold is missed, do NOT raise exception. **LOGIC**:
 1. Read `config.MATCH_RATE_THRESHOLD`.
 2. If the value is the string `[deferred]`, **default the threshold to 0.8 (80%)**. Do NOT skip the check.
 3. Perform the numeric `>=` check using the threshold (default 0.8 or config value).
 4. If the rate is below the threshold, log a warning and proceed.
 **DEPENDS ON**: T026. **MUST read threshold from `config.py`**, which must default to `[deferred]` as per SC-004. **MUST NOT hardcode the value** (except for the fallback logic defined above).
- [X] T029 [US2] Generate `data/processed/user_track_pairs.parquet` with checksum and update `state.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

**Goal**: Fit linear mixed-effects models on User-Track pairs, run sensitivity analysis, and perform permutation tests.

**Independent Test**: Run analysis on the aggregated dataset; verify regression summary includes p-values, sensitivity table shows stability across thresholds, and permutation test confirms significance.

### Tests for User Story 3

- [X] T030 [US3] Unit test for model formula construction in `tests/unit/test_modeling.py`
- [X] T031 [US3] Unit test for sensitivity analysis loop (thresholds ranging from low to high values) in `tests/unit/test_modeling.py`
- [X] T032 [US3] Unit test for permutation test logic (block-permutation) in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/modeling.py` function `fit_mixed_model` to fit `statsmodels` MixedLM: `mean_vividness ~ residualized_exposure + popularity + (1|user_id)` on **User-Track pairs**
- [X] T035 [US3] Implement `code/modeling.py` function `check_collinearity` to calculate Variance Inflation Factor (VIF) and check for multicollinearity (VIF > 5)
- [X] T044a [US3] Implement `code/modeling.py` helper function `run_match_with_threshold` to re-run normalization and matching with a parameterized Levenshtein threshold. **DEPENDS ON**: Code existence of T022, T047. **NOTE**: This is a helper for T044c, not a standalone execution.
- [X] T044b [US3] Implement `code/modeling.py` helper function `run_aggregate_with_threshold` to re-aggregate matched data to User-Track pairs and filter zero variance tracks using a parameterized threshold. **DEPENDS ON**: Code existence of T026, T027. **NOTE**: This is a helper for T044c, not a standalone execution.
- [X] T044 [US3] Implement `code/modeling.py` function `run_sensitivity_analysis` to orchestrate the sensitivity loop. **CRITICAL ORCHESTRATION**: This function MUST implement a **loop** over a range of threshold values. For **each** threshold:
 1. **Load Data**: Load `data/processed/ingested_cohort.parquet` (T018) to get the base track list.
 2. **Filter Tracks**: Apply the current frequency filter logic to the track list.
 3. **Re-Fetch Popularity**: **Re-fetch** `overall_popularity_score` for the current filtered track set (re-run T013b logic on the filtered tracks) to ensure metadata is current.
 4. **Re-Calculate Exposure**: **Re-calculate** `adolescent_exposure_score` (T014 logic) and **Re-run OLS Regression** (T016 logic) on the **filtered track set** to generate a **new** `residualized_exposure_score` valid for this specific subset.
 5. **Re-Match**: Call `run_match_with_threshold` (T044a) with the current threshold.
 6. **Re-Aggregate**: Call `run_aggregate_with_threshold` (T044b) to generate a **temporary** artifact `data/processed/user_track_pairs_threshold_X.parquet` for this iteration.
 7. **Re-Model**: Fit the model on the temporary aggregated data.
 8. **Store Results**: Append results to a list.
 9. **Cleanup**: Delete temporary artifacts after the loop.
 **DEPENDS ON**: T018, T013b, T014, T016, Code existence of T044a, T044b. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially.
- [X] T045a [US3] Implement `code/modeling.py` helper function `run_permutation_shuffle` to perform the **block-permutation** shuffle logic on the **User-Track Pair** dataset. **Procedure**:
 1. **Pin the random seed** (from config.py).
 2. **Construct Shuffle Pool**: **Aggregate** the `residualized_exposure_score` to the **track level** first (one score per unique `track_id`).
 3. **Shuffle**: Randomly shuffle this vector of **track-level scores** (not the row IDs).
 4. **Re-assign**: Create a temporary DataFrame mapping `track_id` to `shuffled_score`. Drop the original `residualized_exposure_score` column from the User-Track pair dataset. **Merge** the shuffled scores back to the original User-Track pairs using `track_id` as the key. This ensures the number of pairs per track (block structure) is preserved exactly while the predictor values are randomized.
 **CONSTRAINT**: This preserves the number of pairs per track (block structure) while shuffling the predictor values.
 **DEPENDS ON**: T029.
- [X] T045b [US3] Implement `code/modeling.py` helper function `run_permutation_loop` to re-fit the model and record the **t-statistic for the `residualized_exposure` coefficient** for a given shuffled dataset. **Procedure**:
 1. **Re-fit**: Re-fit the model on the shuffled data.
 2. **Record**: Record the t-statistic.
 3. **Repeat**: Repeat for **a sufficient number of iterations to ensure convergence**.
 **DEPENDS ON**: T033, T045a.
- [X] T045c [US3] Implement `code/modeling.py` function `run_permutation_test` to orchestrate the permutation test. **Procedure**:
 1. **Call** `run_permutation_shuffle` (T045a) to generate shuffled datasets.
 2. **Call** `run_permutation_loop` (T045b) to generate statistics for each iteration.
 3. **Calculate P-Value**: Compute the p-value by comparing the observed statistic against the null distribution.
 4. **Atomic Write**: **Collect all iteration statistics and the final p-value in memory**. Write to a **temporary file** (e.g., `data/final/permutation_results.csv.tmp`), then use **`os.replace()`** to **atomically rename** the temp file to the final path `data/final/permutation_results.csv`. This ensures no race conditions or partial writes.
 **OUTPUT**: `data/final/permutation_results.csv` with columns: `iteration, statistic` and a final row `metric='p_value', value=<p>`. **DEPENDS ON**: T033, T045a, T045b. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially.
- [X] T038 [US3] Generate `data/final/regression_summary.csv` containing coefficients, SEs, p-values, and VIFs
- [X] T039a [US3] Generate `data/final/sensitivity_analysis.csv` from the aggregated results of T044. **DEPENDS ON**: T044.
- [X] T040 [US3] Generate diagnostic plots (residual checks, QQ plots) and save to `data/final/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `README.md` and `code/` docstrings
- [X] T042 Code cleanup and refactoring of `code/main.py` orchestration script
- [X] T043 Performance optimization: ensure chunking is used if memory > 5GB during ingestion
- [X] T051 [P] Add integration test in `tests/integration/test_pipeline.py` to run full flow on synthetic data and verify sensitivity analysis logic (DEPENDS ON T044).
- [X] T046 [P] Run `quickstart.md` validation to ensure pipeline runs end-to-end within 6 hours (SC-005). **DEPENDS ON: T052**.
- [X] T050 [P] **Verify Artifacts**: Check existence and checksums of `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`, `data/final/regression_summary.csv`, `data/final/sensitivity_analysis.csv`, `data/final/permutation_results.csv` against `state.yaml`. **DEPENDS ON: T029, T038, T039a, T045c** (Must wait for all final artifacts).

**Note**: Tasks T053 (Effect Size), T054 (Assumption Validation), T055, T056, T060, T061, T049, T023b, T057, T058, T059, and T034 (fit_valence_model) have been removed as they represent unauthorized scope creep, conflict with the spec/constitution, or reference undefined data sources. Task T057 and T058 were specifically removed as they are not supported by any Functional Requirement in spec.md. T059 was removed as it is speculative gold-plating.

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

- **T023 -> T013a -> T015**: Fallback check (T023) MUST run on RAW data before any filtering. T013a (filter_cohort) and T015 (frequency filter) must depend on T023 to satisfy EC-001.
- **T036 -> T033/T034**: Match Rate Check (T036) MUST complete before Modeling (T033, T034). T036 is NOT parallel-safe with modeling tasks.
- **T044 Internal**: T044 must NOT re-run T023/T015. It must load pre-computed data, but **MUST re-calculate exposure scores** (T014, T016) and **re-fetch popularity** (T013b) for the filtered track set. **T044 is NOT PARALLEL SAFE**.
- **T045 Internal**: T045 (T045a, T045b, T045c) must run sequentially after T033. **T045 is NOT PARALLEL SAFE**.
- **T050 -> T029, T038, T039a, T045c**: T050 (Verify Artifacts) **MUST wait for T029, T038, T039a, and T045c** to complete before execution to avoid race conditions.
- **T044 Dependencies**: T044 depends on the **code existence** of T044a/T044b, and the **execution** of T013b, T014, T016 within the loop.
- **T045 Atomicity**: T045c must perform an atomic write for the output file (including p-value summary) using `os.replace()`.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for birth year filtering logic in tests/unit/test_ingestion.py"
Task: "Unit test for exposure score calculation in tests/unit/test_ingestion.py"
Task: "Unit test for fallback 'global exposure' trigger in tests/unit/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py function download_datasets"
Task: "Implement code/data_ingestion.py function check_fallback_trigger"
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
- **Dependency Note**: T050 (Verify Artifacts) depends on T029 (Generate `user_track_pairs.parquet`), T038 (Generate `regression_summary.csv`), T039a (Generate `sensitivity_analysis.csv`), and T045c (Generate `permutation_results.csv`).
- **Removed Tasks**: T053 (Effect Size), T054 (Assumption Validation), T060, T061, T049, T055, T056, T034, T023b, T057, T058, T059 have been removed as they are not required by the spec or represent scope creep, or reference undefined data sources. T057 and T058 were specifically removed as they are not supported by any Functional Requirement in spec.md. T059 was removed as it is speculative gold-plating.
- **Removed Tasks**: T055 and T056 have been removed as standalone tasks; their requirements are integrated into T013.
- **Removed Tasks**: T045b has been removed; its logic is merged into T045c to ensure atomic writes via `os.replace()`.
- **Removed Tasks**: T023b has been removed as it references a non-existent data source.
- **Updated Tasks**: T036 updated to strictly follow SC-004 (warn and proceed if deferred, no 0.8 default, but enforce check with default 0.8 if config is [deferred]).
- **Updated Tasks**: T012a updated to raise a fatal error on verification failure.
- **Updated Tasks**: T013a updated to explicitly depend on T013 and T023.
- **Updated Tasks**: T023 updated to run on raw data (no T013a dependency) and raise a FATAL EXCEPTION if fallback is needed but no source is defined.
- **Updated Tasks**: T044 updated to re-calculate exposure scores and re-fetch popularity within the sensitivity loop.
- **Updated Tasks**: T045a updated to explicitly describe the re-join step to preserve block structure.
- **Split Tasks**: T045 split into T045a, T045b, T045c for atomicity.