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

**Goal**: Ingest MSD and AMT data, filter for valid birth years, and compute the `adolescent_exposure_ratio` (raw) and handle fallbacks.

**Independent Test**: Run ingestion on a small synthetic subset; verify output CSV has `adolescent_exposure_ratio` (0.0-1.0), excludes records without `birth_year` (unless fallback), and applies the minimum listen threshold.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Unit test for birth year filtering logic in `tests/unit/test_ingestion.py`
- [X] T011 [US1] Unit test for exposure score calculation (0 listens = 0.0) in `tests/unit/test_ingestion.py`
- [X] T012 [US1] Unit test for fallback "global exposure" trigger when >50% missing birth years in `tests/unit/test_ingestion.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` function `download_datasets` to download/verify MSD and AMT datasets from canonical URLs defined in `config.MSD_URL` and `config.AMT_URL`. **Constraints**:
 1. **Chunked Iteration**: Must process large datasets in chunks (streaming) to stay within RAM limits; do NOT load full dataset into memory.
 2. **Fail Loudly**: Must raise an exception if real data sources (MSD/AMT) are unreachable or invalid. Do NOT implement a `try/except` fallback to synthetic data (except for FR-008 Global Exposure).
 3. **Ordering**: This task MUST NOT perform any filtering. It is strictly for download and verification.
 4. **Data Integrity**: Must validate the structure and checksums of downloaded files. **DEPENDS ON**: None.
- [X] T023 [US1] Implement `code/data_ingestion.py` function `check_fallback_trigger` for FR-008 (Global Exposure metric) check. **ORDERING**: This task is a **PRE-CHECK** only. It MUST calculate the percentage of missing birth years from the **raw ingested data** (output of T013, before any filtering). **CRITICAL**: This task MUST NOT depend on T013a or T015. It must run on the raw dataset to satisfy EC-001. **LOGIC**:
 1. Calculate `missing_pct = count(missing_birth_year) / count(total_raw_records)`.
 2. If `missing_pct > 0.5`:
 - **CALCULATE METRIC**: Compute the 'Global Exposure' metric: **Calculate `adolescent_exposure_ratio` ONLY for the subset of records with valid birth years** from the **Million Song Dataset** (population-level) for the user's birth decade (e.g., 1980-1999 for 1990 birth). This mean serves as the population-level proxy. **Store** this value in the cohort data for descriptive analysis.
 - **EXCLUSION NOTE**: Log a **WARNING**: "FR-008 Fallback Triggered (>50% missing birth years). Global Exposure metric calculated from MSD population as population proxy. Per Plan decision, users with missing birth years are excluded from the primary causal inference model to avoid ecological fallacy."
 - **SET FLAG**: Set a global configuration flag `global_exposure_mode = True` (for descriptive logging only).
 - **OUTPUT**: Update `state.yaml` with `global_exposure_mode` flag. Log fallback metrics to `data/processed/fallback_log.csv`.
 3. If `missing_pct <= 0.5`: Proceed normally (set `global_exposure_mode = False`).
 **DEPENDS ON**: T013 (raw ingestion). **DO NOT** depend on T013a or T015. **NOTE**: T023 runs BEFORE T013a to prevent false triggers (EC-001).
- [X] T013a [US1] Implement `code/data_ingestion.py` function `filter_cohort` to filter MSD logs for `birth_year` presence and calculate adolescent window (birth_year to birth_year +). **DEPENDS ON**: T013, T023. **MUST run after T023** to ensure the fallback check is performed on the raw dataset first (EC-001). **NOTE**: If `global_exposure_mode` is True, this function should skip birth-year filtering for the global calculation but exclude these users from the primary model dataset.
- [X] T015 [US1] Implement `code/data_ingestion.py` function `apply_frequency_threshold` to filter user-track pairs where `total_listens` < 3. **DEPENDS ON**: T023, T013a. **MUST run after T013a** to prevent false fallback triggers (EC-001). Relies on the state set by T013a, not a re-run of ingestion. **NOTE**: This threshold matches FR-009 exactly.
- [X] T013b [US1] Implement `code/data_ingestion.py` function `fetch_popularity_scores` to retrieve `overall_popularity_score` for each track from MSD metadata. **DEPENDS ON**: T013.
- [X] T014 [US1] Implement `code/data_ingestion.py` function `calculate_ratio_score` to compute the raw `adolescent_exposure_ratio` (adolescent listens / total valid listens) per track. **DEPENDS ON**: T013a, T015. **CRITICAL**: This task outputs the **raw ratio** as defined in FR-001. Do NOT residualize against popularity here. **NOTE**: If `global_exposure_mode` is True, calculate the global metric (mean ratio for birth decade) and store it, but do not use it as a predictor in the primary model.
- [X] T028 [US1] Implement `code/main.py` orchestration to enforce the specific order: Fallback Check (T023) -> Filter Cohort (T013a) -> Frequency Filter (T015) -> Popularity Fetch (T013b) -> Ratio Score (T014). **DEPENDS ON**: T013, T013a, T023, T015, T013b, T014. **NOTE**: T028 must explicitly orchestrate the sequential execution of these steps.
- [ ] T018 [US1] Generate `data/processed/ingested_cohort.parquet` with checksum and update `state.yaml`. **DEPENDS ON**: T028. **NOTE**: This is a Write/Save task dependent on the output of T028.

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
- [X] T025 [US2] Implement `code/aggregation.py` function `join_exposure_data` to join matched cues with exposure data (Track-level exposure joined to User-Track pairs). **DEPENDS ON**: T018 (ingested_cohort.parquet). **NOTE**: T018 must be generated before this task runs. <!-- ATOMIZE: requested -->
- [X] T026 [US2] Implement `code/aggregation.py` function `aggregate_to_user_track` to aggregate data to **User-Track Pair** level (mean vividness, mean valence) as per spec FR-004 and FR-005.
- [X] T027 [US2] Implement `code/aggregation.py` function `filter_zero_variance` to filter out tracks with **zero associated User-Track pairs** in the aggregated dataset (high exposure, zero memory cues) to avoid singularities in the design matrix. **CRITICAL**: This filter applies to the aggregated **User-Track Pair** dataset, removing tracks that have no rows in the pair-level table.
- [X] T036 [US2] Implement `code/aggregation.py` function `enforce_match_rate` to verify SC-004 (Match Rate ≥ `config.MATCH_RATE_THRESHOLD`); **LOG WARNING** and proceed if threshold is missed, do NOT raise exception. **LOGIC**:
 1. Read `config.MATCH_RATE_THRESHOLD`.
 2. **IF the value is the string '[deferred]'**: **LOG WARNING**: "Match rate threshold is [deferred]. Proceeding with analysis. Warning logged if rate is below undefined threshold." **DO NOT enforce a numeric check.**
 3. **IF the value is numeric**: Perform the numeric `>=` check. If the rate is below the threshold, log a warning and proceed.
 **DEPENDS ON**: T026. **MUST read threshold from `config.py`**, which must default to `[deferred]` as per SC-004. **MUST NOT hardcode the value** (except for the fallback logic defined above).
- [ ] T029 [US2] Generate `data/processed/user_track_pairs.parquet` with checksum and update `state.yaml`. **DEPENDS ON**: T036. **NOTE**: This is a Write/Save task dependent on the output of T036.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

**Goal**: Fit linear mixed-effects models on User-Track pairs, run sensitivity analysis, and perform Parametric Bootstrap (replacing block-permutation per Plan).

**Independent Test**: Run analysis on the aggregated dataset; verify regression summary includes p-values, sensitivity table shows stability across thresholds, and bootstrap confirms significance.

### Tests for User Story 3

- [X] T030 [US3] Unit test for model formula construction in `tests/unit/test_modeling.py`
- [X] T031 [US3] Unit test for sensitivity analysis loop (thresholds ranging from low to high values) in `tests/unit/test_modeling.py`
- [X] T032 [US3] Unit test for parametric bootstrap logic (resampling residuals) in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/modeling.py` function `fit_mixed_model` to fit `statsmodels` MixedLM: `mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)` on **User-Track pairs**. **CRITICAL**: Use the **raw** `adolescent_exposure_ratio` (from T014) and `popularity` as **separate** covariates. Do NOT use a residualized score.
- [X] T035 [US3] Implement `code/modeling.py` function `check_collinearity` to calculate Variance Inflation Factor (VIF) and check for multicollinearity (VIF > 5 (2605.22529, https://arxiv.org/abs/2605.22529))
- [X] T044a [US3] Implement `code/modeling.py` function `run_sensitivity_loop_setup` to prepare the sensitivity analysis loop. **LOGIC**:
 1. Define the range of Levenshtein thresholds to test.
 2. Load `data/processed/ingested_cohort.parquet` (T018) to get the base track list.
 3. **DEPENDS ON**: **Code existence** of T013b, T014 (functions to be called within the loop), **Execution** of T018 (data availability).
 **NOTE**: This task sets up the loop but does not execute the full iteration logic.
- [X] T044b-1 [US3] Implement `code/modeling.py` function `re_calculate_exposure` for sensitivity iteration. **LOGIC**:
 1. **Filter Tracks**: Apply the current frequency filter logic to the track list **loaded from `ingested_cohort.parquet`**.
 2. **Re-Calculate Popularity**: **Filter** the pre-computed popularity scores from `ingested_cohort.parquet` for the current **filtered** track set. **Do NOT re-fetch from source.**
 3. **Re-Calculate Exposure**: **Re-calculate** `adolescent_exposure_ratio` (T014 logic) on the **filtered track set** using data from `ingested_cohort.parquet` to generate a **new** `adolescent_exposure_ratio` valid for this specific subset. **Pass the filtered track set explicitly**.
 **DEPENDS ON**: T018 (data), Code existence of T013b, T014.
- [X] T044b-2 [US3] Implement `code/modeling.py` function `re_match_cues` for sensitivity iteration. **LOGIC**:
 1. **Re-Match**: Call `match_cues` function (from T047 module) with the current threshold.
 **DEPENDS ON**: T044b-1, Code existence of T047.
- [X] T044b-3 [US3] Implement `code/modeling.py` function `re_aggregate` for sensitivity iteration. **LOGIC**:
 1. **Re-Aggregate**: Call `aggregate_to_user_track` (T026) to generate a **temporary** artifact `data/processed/user_track_pairs_threshold_X.parquet` for this iteration.
 2. **Re-Model**: Fit the model on the temporary aggregated data.
 3. **Store Results**: Append results to a list.
 4. **Cleanup**: Delete temporary artifacts after the loop.
 **DEPENDS ON**: T044b-2, Code existence of T026.
- [X] T044c [US3] Implement `code/modeling.py` function `run_sensitivity_analysis` to orchestrate the sensitivity loop. **LOGIC**:
 1. Call `run_sensitivity_loop_setup` (T044a).
 2. Loop over thresholds, calling `re_calculate_exposure` (T044b-1), `re_match_cues` (T044b-2), and `re_aggregate` (T044b-3) for each.
 3. Aggregate all results into `data/final/sensitivity_analysis.csv`.
 **DEPENDS ON**: T044a, T044b-1, T044b-2, T044b-3. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially.
- [X] T045a [US3] Implement `code/modeling.py` helper function `run_bootstrap_setup` to prepare the Parametric Bootstrap. **LOGIC**:
 1. **Pin the random seed** (from config.py).
 2. **Fit Null Model**: Fit the model under the null hypothesis (e.g., `mean_vividness ~ popularity + (1|user_id)`) to get residuals.
 3. **Extract Residuals**: Store the residuals for resampling.
 **DEPENDS ON**: T033.
- [X] T045b [US3] Implement `code/modeling.py` helper function `run_bootstrap_iteration` to generate a bootstrap sample and re-fit the model. **LOGIC**:
 1. **Resample Residuals**: Randomly resample the residuals with replacement (parametric bootstrap).
 2. **Generate New Outcome**: Create a new `mean_vividness` vector: `predicted_values_from_null + resampled_residuals`.
 3. **Re-Fit**: Fit the full model (`mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)`) using the new outcome vector.
 4. **Record**: Record the t-statistic for the `adolescent_exposure_ratio` coefficient.
 5. **Repeat**: Repeat for a sufficient number of iterations to ensure convergence and robustness of the results.
 **DEPENDS ON**: T033, T045a.
- [X] T045c-1 [US3] Implement `code/modeling.py` function `run_bootstrap_test` to orchestrate the bootstrap test. **Procedure**:
 1. **Call** `run_bootstrap_setup` (T045a) to prepare residuals.
 2. **Call** `run_bootstrap_iteration` (T045b) to generate statistics for each iteration (1000 iterations).
 3. **Calculate P-Value**: Compute the p-value by comparing the observed statistic (from T033) against the null distribution of bootstrap statistics.
 **DEPENDS ON**: T033, T045a, T045b. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially.
- [X] T045c-2 [US3] Implement `code/modeling.py` function `write_bootstrap_results` to perform atomic write. **Procedure**:
 1. **Collect** all iteration statistics and the final p-value in memory.
 2. **Write** to a **temporary file** (e.g., `data/final/bootstrap_results.csv.tmp`).
 3. **Use `os.replace()`** to **atomically rename** the temp file to the final path `data/final/bootstrap_results.csv`.
 **OUTPUT**: `data/final/bootstrap_results.csv` with columns: `iteration, statistic` and a final row `metric='p_value', value=<p>`. **DEPENDS ON**: T045c-1. **NOTE**: This task is **NOT PARALLEL SAFE** and must run sequentially. **NOTE**: This implements the Parametric Bootstrap as the validated replacement for the block-permutation test (FR-007), pending spec amendment (see T066).
- [ ] T038 [US3] Generate `data/final/regression_summary.csv` containing coefficients, SEs, p-values, and VIFs. **DEPENDS ON**: T033, T035. **NOTE**: This is a Write/Save task dependent on the output of T033/T035.
- [ ] T039a [US3] Generate `data/final/sensitivity_analysis.csv` from the aggregated results of T044c. **DEPENDS ON**: T044c. **NOTE**: This is a Write/Save task dependent on the output of T044c.
- [X] T040 [US3] Generate diagnostic plots (residual checks, QQ plots) and save to `data/final/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `README.md` and `code/` docstrings
- [X] T042 Code cleanup and refactoring of `code/main.py` orchestration script
- [X] T043 Performance optimization: ensure chunking is used if memory > 5GB during ingestion
- [X] T051 [P] Add integration test in `tests/integration/test_pipeline.py` to run full flow on synthetic data and verify sensitivity analysis logic (DEPENDS ON T044c).
- [X] T046 [P] Run `quickstart.md` validation to ensure pipeline runs end-to-end within 6 hours (SC-005). **DEPENDS ON: T052**.
- [ ] T050 [P] **Verify Artifacts**: Check existence and checksums of `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`, `data/final/regression_summary.csv`, `data/final/sensitivity_analysis.csv`, `data/final/bootstrap_results.csv` against `state.yaml`. **DEPENDS ON: T029, T038, T039a, T045c-2** (Must wait for all final artifacts). **CRITERIA**: 
 1. **Existence**: Verify all files exist. If missing, **Raise RuntimeError** and Exit 1.
 2. **Checksums**: Compute SHA-256 of each file and compare against `state.yaml`. If mismatch, **Raise RuntimeError** and Exit 1.
 3. **Schema**: Validate each file against `contracts/` schemas. If invalid, **Raise RuntimeError** and Exit 1.
 **ACTION**: **Exit 0 if all checks pass; Exit 1 if any file is missing, checksum mismatches, or schema validation fails.** If any check fails, the script must **Raise RuntimeError** to halt execution immediately. **DEPENDS ON**: T029, T038, T039a, T045c-2.

**Note**: Tasks T053 (Effect Size), T054 (Assumption Validation), T055, T056, T060, T061, T049, T023b, T057, T058, T059, and T034 (fit_valence_model) have been removed as they represent unauthorized scope creep, conflict with the spec/constitution, or reference undefined data sources. Task T057 and T058 were specifically removed as they are not supported by any Functional Requirement in spec.md. T059 was removed as it is speculative gold-plating. Task T016 (residualization) was removed to align with FR-001/FR-005. Task T073 (Heckman Correction) has been removed as it contradicts the plan's exclusion strategy for missing birth years, despite being listed in Complexity Tracking as a potential violation; the plan explicitly states exclusion is the chosen method to avoid ecological fallacy. T055 and T056 were removed as their logic is fully integrated into T013 (download/verification) and T013a (filtering), ensuring no gap in the pipeline.

---

## Phase 7: Revision & Verification (Addressing Review Concerns)

**Purpose**: Tasks added to resolve specific analysis findings regarding data integrity, ordering, and fallback logic.

### Implementation for Revision Concerns

- [X] T062 [US1] **Verify Data Source URLs**: Update `code/config.py` to explicitly define the canonical, verified URLs for MSD and AMT datasets. **Constraint**: If the execution environment injects a specific verified source, this task must update the config to use **only** that injected source and remove any other fallback URLs for the *primary* data sources. **CRITICAL**: This task must **NOT** remove or disable the FR-008 fallback mechanism (Global Exposure) which is independent of the primary data source URLs. The fallback mechanism must remain active and functional. **Specifics**: Set `MSD_URL = "hf://brian/MSD"` and `AMT_URL = "hf://[validated-AMT-source]"`. **[FR-001, FR-008, SC-004]**
- [X] T063 [US1] **Verify Streaming Implementation**: Refactor `code/data_ingestion.py` (T013) to ensure `datasets.load_dataset(..., streaming=True)` is used for all large dataset fetches. **Constraint**: The code must iterate via a generator and accumulate statistics on-the-fly; it must NOT call `.to_pandas()` or `.list()` on the full dataset before processing.
- [X] T064 [US1] **Verify Fallback Logic Isolation**: Add a unit test in `tests/unit/test_ingestion.py` specifically for `check_fallback_trigger` (T023) that asserts it sets `global_exposure_mode=True`, calculates the Global Exposure metric (from valid cohort), and logs a WARNING when the fallback source is missing (if applicable), ensuring no silent synthetic fallback occurs and the pipeline proceeds gracefully.
- [X] T065 [US3] **Verify Bootstrap Logic**: Add a unit test in `tests/unit/test_modeling.py` for `run_bootstrap_iteration` (T045b) that asserts the new outcome vector is generated by adding resampled residuals to the null model predictions, preserving the random intercept structure.
- [X] T066 [US3] **Update Spec for FR-007 and Artifacts**: Update `spec.md` to:
 1. Amend **FR-007** to replace "block-permutation test" with "**Parametric Bootstrap**" and update the description to match T045c.
 2. Update **Output Artifacts** section to replace `data/final/permutation_results.csv` with `data/final/bootstrap_results.csv`.
 3. Add a note in FR-007 stating: "Block-permutation was replaced by Parametric Bootstrap to preserve random intercept structure."
 **DEPENDS ON**: None. **NOTE**: This task aligns the spec with the implementation plan.
- [X] T068 [US1] **Create 02_preprocess.py**: Create `code/02_preprocess.py` as a wrapper script that imports and orchestrates functions from `code/data_ingestion.py` (T013, T015, T013a). **LOGIC**:
 1. Import `download_datasets`, `check_fallback_trigger`, `filter_cohort`, `apply_frequency_threshold`.
 2. Execute the pipeline in the correct order (T023 -> T013a -> T015).
 3. Output `data/processed/ingested_cohort.parquet`.
 **DEPENDS ON**: T013, T013a, T015, T023.
- [X] T070 [US1] **Create 04_exposure.py**: Create `code/04_exposure.py` as a wrapper script that imports and orchestrates functions from `code/data_ingestion.py` (T013b, T014). **LOGIC**:
 1. Import `fetch_popularity_scores`, `calculate_ratio_score`.
 2. Execute the pipeline in the correct order (T013b -> T014).
 3. Output `data/processed/ingested_cohort.parquet` with exposure scores.
 **DEPENDS ON**: T013b, T014.
- [X] T071 [US3] **Create 05_model.py**: Create `code/05_model.py` as a wrapper script that imports and orchestrates functions from `code/modeling.py` (T033, T035, T045c). **LOGIC**:
 1. Import `fit_mixed_model`, `check_collinearity`, `run_bootstrap_test`, `write_bootstrap_results`.
 2. Execute the pipeline in the correct order (T033 -> T035 -> T045c-1 -> T045c-2).
 3. Output `data/final/regression_summary.csv` and `data/final/bootstrap_results.csv`.
 **DEPENDS ON**: T033, T035, T045c-1, T045c-2.
- [X] T072 [US3] **Create 06_sensitivity.py**: Create `code/06_sensitivity.py` as a wrapper script that imports and orchestrates functions from `code/modeling.py` (T044a, T044b-1, T044b-2, T044b-3, T044c). **LOGIC**:
 1. Import `run_sensitivity_loop_setup`, `re_calculate_exposure`, `re_match_cues`, `re_aggregate`, `run_sensitivity_analysis`.
 2. Execute the sensitivity analysis loop.
 3. Output `data/final/sensitivity_analysis.csv`.
 **DEPENDS ON**: T044a, T044b-1, T044b-2, T044b-3, T044c.
- [X] T074 [US3] **Create 08_visualize.py**: Create `code/08_visualize.py` as a wrapper script that imports and orchestrates functions from `code/modeling.py` (T040). **LOGIC**:
 1. Import `generate_plots`.
 2. Execute the plotting logic.
 3. Output `data/final/plots/`.
 **DEPENDS ON**: T040.
- [X] T099 [US3] **Update Spec for FR-007**: Edit `spec.md` to replace "block-permutation test" with "parametric bootstrap" in FR-007 and update Output Artifacts to list `bootstrap_results.csv`. **DEPENDS ON**: None. **NOTE**: This task ensures the spec is updated before code execution, resolving the methodology contradiction.

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
- **T044 Internal**: T044 must NOT re-run T023/T015. It must load pre-computed data, but **MUST re-calculate exposure scores** (T014) and **re-fetch popularity** (T013b) for the filtered track set. **T044 is NOT PARALLEL SAFE**.
- **T045 Internal**: T045 (T045a, T045b, T045c-1, T045c-2) must run sequentially after T033. **T045 is NOT PARALLEL SAFE**.
- **T050 -> T029, T038, T039a, T045c-2**: T050 (Verify Artifacts) **MUST wait for T029, T038, T039a, and T045c-2** to complete before execution to avoid race conditions.
- **T044 Dependencies**: T044 depends on the **code existence** of T044a/T044b-1/2/3, and the **execution** of T013b, T014 within the loop.
- **T045 Atomicity**: T045c-2 must perform an atomic write for the output file (including p-value summary) using `os.replace()`.

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
- **Constraint**: All data processing must run on CPU-only CI (no GPU, no low-precision models)
- **Constraint**: All datasets must be fetched from real, verified URLs (no fabrication)
- **Constraint**: Spec requirements (User-Track Pair unit of analysis, Parametric Bootstrap) are active constraints for all implementation tasks.
- **Dependency Note**: T051 (Integration Test) depends on T044c (Sensitivity Analysis) being completed first.
- **Dependency Note**: T036 (Match Rate Check) is NOT parallel-safe with T033/T034 (Modeling).
- **Dependency Note**: T044 (Sensitivity Analysis) must load pre-computed data, not re-ingest. **T044 is NOT PARALLEL SAFE**.
- **Dependency Note**: T045 (Parametric Bootstrap) must resample residuals and output only the statistic per iteration. **T045 is NOT PARALLEL SAFE**.
- **Critical Constraint**: The pipeline must **fail loudly** if real data sources (MSD/AMT) are unreachable; **never** implement a `try/except` block that falls back to synthetic/mock data generation (except for FR-008 Global Exposure).
- **Critical Constraint**: For large datasets, implement **chunked iteration** to process data in chunks, ensuring the full dataset contributes to results without exceeding RAM limits.
- **Critical Constraint**: If a verified real data source is injected via execution feedback, **adopt it exclusively** in the data-loading task; do not maintain alternative hand-rolled fetchers.
- **Dependency Note**: T050 (Verify Artifacts) depends on T029 (Generate `user_track_pairs.parquet`), T038 (Generate `regression_summary.csv`), T039a (Generate `sensitivity_analysis.csv`), and T045c-2 (Generate `bootstrap_results.csv`).
- **Removed Tasks**: T053 (Effect Size), T054 (Assumption Validation), T060, T061, T049, T055, T056, T034, T023b, T057, T058, T059, T073 (Heckman Correction) have been removed as they are not required by the spec or represent scope creep, or reference undefined data sources. T057 and T058 were specifically removed as they are not supported by any Functional Requirement in spec.md. T059 was removed as it is speculative gold-plating. T016 (residualization) was removed to align with FR-001/FR-005. T073 was removed as it contradicts the plan's exclusion strategy.
- **Removed Tasks**: T055 and T056 have been removed as standalone tasks; their requirements are integrated into T013.
- **Removed Tasks**: T045b has been retained as a distinct function task to support T045c-1.
- **Removed Tasks**: T023b has been removed as it references a non-existent data source.
- **Removed Tasks**: T012a has been removed; its logic is integrated into T013.
- **Updated Tasks**: T036 updated to strictly follow SC-004 (log warning if [deferred], do NOT enforce 0.80 default).
- **Updated Tasks**: T023 updated to run on raw data (no T013a dependency) and enable fallback mode if no source is defined, instead of raising a FATAL EXCEPTION. It now calculates the Global Exposure metric from the MSD population.
- **Updated Tasks**: T044 split into T044a, T044b-1, T044b-2, T044b-3, T044c for clarity and testability.
- **Updated Tasks**: T044 updated to re-calculate exposure scores and re-fetch popularity within the sensitivity loop (from cached data).
- **Updated Tasks**: T045 split into T045a, T045b, T045c-1, T045c-2 to implement Parametric Bootstrap (resampling residuals) instead of block-permutation, aligning with the Plan.
- **Updated Tasks**: T066 updated to use existing research URLs or fail, and to preserve FR-008 fallback logic. Added traceability tags.
- **Updated Tasks**: T013 updated to include data integrity checks and emphasize NO filtering.
- **Updated Tasks**: T015 updated to filter at 3 listens (FR-009).
- **Updated Tasks**: T014 updated to output raw ratio.
- **Updated Tasks**: T033 updated to use raw ratio and popularity as separate covariates.
- **Added Tasks**: T066 added to update spec.md for FR-007 and Output Artifacts.
- **Added Tasks**: T068, T070, T071, T072, T074 added to create wrapper scripts for the plan's file structure.
- **Added Tasks**: T099 added to update spec.md FR-007 to mandate Parametric Bootstrap.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T067 Reconcile run-book vs implementation for `code/01_download_data.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/01_download_data.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T069 Reconcile run-book vs implementation for `code/03_aggregate.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/03_aggregate.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T074 Reconcile run-book vs implementation for `code/08_visualize.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/08_visualize.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.