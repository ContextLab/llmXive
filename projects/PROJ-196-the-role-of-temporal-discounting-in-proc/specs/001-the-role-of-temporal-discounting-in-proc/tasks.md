# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

**Input**: Design documents from `/specs/001-temporal-discounting-in-procrastination/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan. **MUST execute**: `mkdir -p projects/PROJ-196-the-role-of-temporal-discounting-in-proc/{data/raw,data/processed,code,tests,docs,specifications}`.
- [X] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn` dependencies. **MUST create** `pyproject.toml` with `[project]` section containing `dependencies = ["pandas>=2.0", "numpy>=1.24", "scipy>=1.11", "statsmodels>=0.14", "scikit-learn>=1.3"]`. **MUST ALSO create** `requirements.txt` with pinned versions using `pip freeze` output to ensure reproducibility.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **MUST create** `.ruff.toml` with `target-version = "py311"` and `pyproject.toml` tool sections for `black` and `ruff` with `line-length = 88`, `select = ["E", "F", "W", "I"]`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a **[FR-001] [US1] STATE INITIALIZATION**: Create `state/projects/` directory and initialize `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with an empty `artifact_hashes` map (dict), a `last_updated` timestamp (ISO 8601 string), and a `completion_status` key (string, default "in_progress"). **MUST run before T009a.**
- [X] T004 Setup `data/raw/` and `data/processed/` directory structure. **MUST create** `.gitkeep` files in `data/raw/` and `data/processed/` to ensure directories are tracked in git.
- [X] T005 [P] **REMOVED**: Merged into T002.
- [X] T006 [P] Configure `pytest` framework and directory structure. **MUST create** `pytest.ini` with `[pytest] testpaths = tests` and `tests/conftest.py` containing fixtures for `random_seed` and `data_path`.
- [X] T007 Create `code/__init__.py` and base configuration loader.
- [X] T008 [P] Setup seed management: Create `code/config.py` to load `RANDOM_SEED` and provide `get_random_state()` helper; explicitly pass `random_state` to all stochastic functions in `numpy`, `pandas`, `scipy` (including `stats`), and `sklearn` to ensure reproducibility per Constitution I. **MUST NOT** include runtime validation steps; Reference-Validator Agent execution is a pre-requisite gate step.
- [X] T009a [P] **STATE INITIALIZATION (CHECKSUM MAP)**: Initialize the `artifact_hashes` map in `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` to an empty dictionary if it does not exist. **MUST run before T009b.**
- [X] T009b [P] **REMOVED**: Moved to Phase 3.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest, harmonize, and process raw data (or DGP) into a unified analysis-ready dataset with calculated discount rates.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output DataFrame contains the required columns (`discount_rate_k`, `procrastination_score`, `wm_accuracy`, `wm_rt`, `age`, `gender`, `education`) with zero null values in key predictor/outcome columns after imputation or filtering.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are written first (TDD) but listed here to reflect dependency on code structure created by T013-T018.

- [X] T010 [P] [US1] Unit test for DGP parameter generation in `tests/test_ingestion.py`. **MUST NAME** function `test_dgp_params_valid`.
- [X] T011 [P] [US1] Unit test for hyperbolic model fitting edge cases (failure cases) in `tests/test_modeling.py`. **MUST NAME** function `test_hyperbolic_fit_failure`.
- [X] T012 [P] [US1] Integration test for full data harmonization pipeline in `tests/test_integration.py`. **MUST NAME** function `test_harmonization_id_match`.

### Implementation for User Story 1

- [X] T013 [US1] **DATA GENERATION (DGP) & HARMONIZATION**: Implement Synthetic Data Generation and Harmonization in `code/ingestion.py`. **MUST GENERATE** **three distinct CSV files** simulating N=500 participants based on the **DEFINITIVE** parameters below.
 - **DEFINITIVE PARAMETERS** (Do not reference external files):
 ```json
 {
 "k_mean": 0.05, "k_sd": 0.02,
 "procrastination_mean": 3.5, "procrastination_sd": 0.8,
 "wm_accuracy_mean": 0.85, "wm_accuracy_sd": 0.1,
 "age_mean": 25, "age_sd": 5,
 "gender_distribution": {"male": 0.5, "female": 0.5, "other": 0.0},
 "education_mean": 16, "education_sd": 2
 }
 ```
 - **MUST GENERATE ITEM-LEVEL DATA**: `procrastination_item_1` through `procrastination_item_10` (for Cronbach's alpha) and `nback_trials` data (for WM accuracy/RT).
 - **MUST LOG** the specific parameter values used to `data/processed/dgp_params.log`.
 - **MUST VALIDATE** DGP parameters against a strict schema.
 - **MUST FLAG** this as "Methodological Validation" by writing `data/processed/data_source_flag.json` with schema: `{"source": "synthetic_dgp", "n": 500, "methodology": "Methodological Validation", "dgp_params_hash": "<sha256>"}`. Each file must contain distinct experimental paradigm data.
 - **STEP 1 (Generate)**: Create `discounting_raw.csv`, `procrastination_raw.csv`, `nback_raw.csv`.
 - **STEP 2 (Harmonize)**: Merge using `participant_id` via inner join. **MUST calculate ID mismatch rate as `1 - (len(merged_df) / len(initial_df))` **.
 - **IF** mismatch rate > 0.10 AND missing items are CORE CONSTRUCTS (discount_rate, procrastination, wm): **WRITE** `data/processed/halt_log.json` with reason "ID Mismatch > 10% for Core Constructs" **THEN** `Raise SystemExit(1)`.
 - **IF** mismatch rate > 0.10 AND missing items are COVARIATES (age, gender): **PROCEED** with reduced model (see Step 4).
 - **STEP 3 (Reliability Check)**: Calculate Cronbach's alpha for `procrastination_item_1` to `procrastination_item_10` and `nback_accuracy`/`nback_rt`. **IF** any alpha < 0.7, **raise `SystemExit(1)` with message "CRITICAL: Data reliability below threshold (alpha < 0.7) - DGP failure"**. Log seed values to `data/processed/construct_independence.log`.
 - **STEP 4 (Missing Data)**: Calculate row-wise missingness for covariates (`age`, `gender`) as: `count(missing in [age, gender] for row) / 2`.
 - **IF** row-wise missingness > 0.10 (i.e., > 10% of total rows have missing covariates), **flag for reduced model** by writing `data/processed/model_config.json` with schema `{"reduced_model": true, "excluded_covariates": ["age", "gender"], "imputation_method": "listwise_deletion"}`.
 - **ELSE** (if missing <= 10%), **MUST WRITE** `data/processed/model_config.json` with schema `{"reduced_model": false, "excluded_covariates": [], "imputation_method": "mean"}` and perform mean imputation.
 - **MUST LOG** the exact imputation values used for each imputed column to `data/processed/imputation_log.json`.
 - **STEP 5 (Model Fitting)**: Implement `fit_hyperbolic_model` in `code/modeling.py` using `scipy.optimize.curve_fit`. Calculate `discount_rate_k` for each participant. **MUST EXCLUDE** participants where fitting fails and **GENERATE A WARNING LOG** with the count of excluded participants.
 - **STEP 6 (Halt Check)**: Verify core constructs (`discount_rate_k`, `procrastination_score`, `wm_accuracy`) are present and non-null.
 - **IF** missing: **WRITE** `data/processed/halt_log.json` with reason "Core constructs missing" **THEN** `Raise SystemExit(1)`.
 - **STEP 7 (Write & Checksum)**: Write final harmonized dataset to `data/processed/harmonized_dataset.parquet`. **MUST generate checksum** for this file AND the following specific files: `model_config.json`, `data_source_flag.json`, `dgp_params.log`, `construct_independence.log`, `imputation_log.json`, `halt_log.json` (if created). **MUST UPDATE** `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with the new hashes. **IF** checksum update fails, **Raise `SystemExit(1)`**.
 - **Output**: Three source CSV files, `data/processed/data_source_flag.json`, `data/processed/model_config.json`, `data/processed/harmonized_dataset.parquet`, and all log files.

- [X] T013b [US1] **RELIABILITY CHECK**: This task is a validation step executed as part of T013 (Step 3). **NO CODE CHANGES REQUIRED** beyond ensuring T013 Step 3 runs. **MUST** verify that T013 Step 3 successfully calculated Cronbach's alpha and raised an error if < 0.7. **MUST** log the alpha values to `data/processed/reliability_log.json`.

- [X] T009b [US1] **CHECKSUM UPDATE**: After T013 completes, calculate SHA256 checksums for all artifacts in `data/processed/` and update `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml`. **MUST depend on T013**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Moderation Regression Analysis (Priority: P2)

**Goal**: Execute OLS regression to test the primary hypothesis (moderation effect) and calculate VIF.

**Independent Test**: The analysis can be fully tested by running the regression script and verifying that the output includes a coefficient and p-value for the interaction term (`log(k) * wm_metric`), and that model assumptions (VIF) are reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for interaction term creation and mean-centering in `tests/test_modeling.py`. **MUST NAME** function `test_interaction_term_creation`.
- [X] T020 [P] [US2] Unit test for VIF calculation and threshold flagging in `tests/test_modeling.py`. **MUST NAME** function `test_vif_calculation`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement log-transformation of discount rate (`log(k)`) and mean-centering of predictors in `code/modeling.py`. **MUST WRITE** centered data to `data/processed/centered_data.parquet`.
- [X] T022 [US2] Implement OLS regression model construction with interaction term in `code/modeling.py` (FR-004). **Depends on T013, T021**: Read `data/processed/model_config.json` and `data/processed/centered_data.parquet`.
 - **STEP 1 (Read Config)**: Load `data/processed/model_config.json`.
 - **STEP 2 (Construct Formula)**:
 - Base formula: `procrastination ~ log_k + wm_metric + log_k:wm_metric`.
 - **CRITICAL CHECK**:
 - **IF** `log_k` or `wm_metric` in `excluded_covariates`: **RAISE** `SystemExit(1)` with message "CRITICAL: Primary predictor 'log_k' or 'wm_metric' cannot be excluded per FR-004/FR-009".
 - **IF** `age` or `gender` in `excluded_covariates`: **REMOVE** them from the formula.
 - **MUST INCLUDE INLINE MONITORING**: Use `memory_profiler` and `time` module; if `max_memory_mb > 7168` or `elapsed_time` exceeds 50% of 6h limit, **Raise `SystemExit(1)`**.
 - **MUST** write the final formula used to a log file `data/processed/regression_formula.log`.
 - **STEP 3 (Log Formula)**: Log the final formula string to `data/processed/regression_formula.log`.
 - **STEP 4 (VIF & Centering Loop)**: Calculate VIF for all predictors.
 - **IF** any VIF > 5: **MUST** mean-center predictors (using data from T021) and **RE-RUN** VIF calculation.
 - **IF** VIF > 5 persists after centering: **Log a warning** "VIF > 5 persists after centering" but **PROCEED** with the model (centering is the mandated mitigation).
 - **MUST WRITE** results to `data/processed/vif_report.json`.
- [X] T023 [US2] **REMOVED**: Merged into T022 Step 4.
- [X] T024 [US2] Implement extraction of coefficients, p-values, and confidence intervals for the interaction term. **MUST WRITE** results to `data/processed/interaction_results.json`.
- [X] T025 [US2] Save regression results summary to `data/processed/regression_results.json`. **MUST WRITE** a JSON object with keys: `r_squared`, `adj_r_squared`, `aic`, `bic`, `coefficients` (dict of variable_name: value), `p_values` (dict of variable_name: value), `vif_scores` (dict of variable_name: value).
**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform bootstrapping and sensitivity analysis to verify stability of the interaction effect.

**Independent Test**: The robustness check can be independently tested by running the bootstrapping script and verifying that the confidence intervals for the interaction coefficient do not include zero (if the primary effect was significant) or that the stability metric is calculated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for bootstrap resampling logic (a sufficient number of resamples) in `tests/test_robustness.py`. **MUST NAME** function `test_bootstrap_resampling_generates_95ci`.
- [X] T027 [P] [US3] Unit test for sensitivity analysis threshold sweeps in `tests/test_robustness.py`. **MUST NAME** function `test_sensitivity_threshold_sweep`. **MUST assert** specific thresholds (median, median ± 0.05*SD, median ± 0.10*SD).

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement bootstrapping routine to generate a confidence interval for interaction coefficient in `code/robustness.py` (FR-006). **Depends on T022**.
 - **STEP 1 (Significance Check)**: Read `data/processed/interaction_results.json`. **IF** primary effect p-value >= 0.05: **SKIP** stability check, log "Primary effect not significant, skipping stability check", and write `data/processed/bootstrap_ci.json` with `stability_check: false`. **IF** p-value < 0.05: **PROCEED** to Step 2.
 - **STEP 2 (Bootstrap)**: Run bootstrapping with deterministic seed (`RANDOM_SEED + 1000`). **MUST WRITE** results to `data/processed/bootstrap_ci.json`. **MUST INCLUDE INLINE MONITORING**: Use `memory_profiler` and `time` module; if `max_memory_mb > 7168` or `elapsed_time` exceeds 50% of 6h limit, **Raise `SystemExit(1)`**.
- [X] T029 [US3] Implement sensitivity analysis for WM load threshold (median, ±0.05*SD, ±0.10*SD) AND discount rate (median, ±0.05*SD, ±0.10*SD) in `code/robustness.py` (FR-007). **MUST GENERATE EXACTLY 5 THRESHOLDS PER VARIABLE** (Total 10 sweeps). **MUST OUTPUT** a JSON list of objects containing `threshold_value`, `p_value`, `coefficient`, `ci_lower`, `ci_upper` to `data/processed/sensitivity_sweep_raw.json`. **MUST LOG** the exact threshold values used in the sweep to `data/processed/sweep_config.json` before execution.
- [X] T030 [US3] Implement logic to calculate `instability_ratio` = (count of thresholds where 95% CI crosses zero) / (total count of **10** defined threshold sweeps). **Flag instability if `instability_ratio > 0.5`** (SC-004). **MUST WRITE** result to `data/processed/instability_flag.json`.
- [X] T031 [US3] Aggregate all results (primary, bootstrap, sensitivity, instability_ratio) into a final `data/processed/final_analysis_report.json`. **MUST read** `data/processed/sensitivity_sweep_raw.json` (output of T029), `data/processed/instability_flag.json`, and `data/processed/bootstrap_ci.json`. **Depends on T028, T029, T030**. **MUST AGGREGATE** by **copying** `instability_ratio` from `instability_flag.json` and embedding the full list from `sensitivity_sweep_raw.json` under the key `sensitivity_sweep_raw` and embedding `bootstrap_ci.json` under `bootstrap_confidence_interval`. **MUST** structure `sensitivity_sweep_raw` as a list of objects with keys `threshold_value`, `p_value`, `coefficient`, `ci_lower`, `ci_upper`. **MUST WRITE** the `instability_ratio` flag and the raw threshold sweep data to this JSON file.
- [X] T032 [US3] **Final Verification**: Verify total runtime and memory usage stay within 6h/7GB limits on CPU (FR-010). Use `memory_profiler` and `time` module; assert `max_memory_mb < 7168` and `elapsed_time < 21600`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Update `README.md` with execution instructions and DGP explanation. **MUST ADD** "Usage" section with command: `python code/main.py --seed` and "DataSource" section explaining the synthetic data strategy.
- [X] T034 Code cleanup and refactoring for readability: **MUST** refactor `code/ingestion.py` and `code/modeling.py` to improve readability. **SPECIFIC ACTIONS**:
 - **Extract** complex conditional blocks (e.g., formula construction, missing data logic) into dedicated helper functions (e.g., `build_regression_formula`, `handle_missing_covariates`).
 - **Ensure** all public functions have clear Google-style docstrings (Args, Returns, Raises).
 - **Ensure** code is maintainable and free of `TODO` comments.
 - **DO NOT** attempt to meet a specific cyclomatic complexity threshold; focus on structural clarity.
- [X] T035 [P] Add docstrings to all public functions in `code/`. **MUST USE** Google style with Args, Returns, Raises sections.
- [X] T036a [P] Execute pipeline end-to-end: Run `python code/main.py` to generate all artifacts.
- [X] T036b [P] Verify pipeline output: Check that all expected files in `data/processed/` exist and are non-empty.
- [X] T037 [P] Update `state.yaml` with execution hashes and completion status. **MUST UPDATE** `artifact_hashes` map with hashes for all files in `data/processed/` and set `completion_status` to "success". **NOTE**: T009b updates state for US1 artifacts; T037 performs final consolidation for all artifacts.

- [X] T038 [US1] **REVISION: ENHANCED DATA LOADER FAIL-SAFE**: Refactor `code/ingestion.py` to implement a strict "Fail Loud" policy for data loading. **MUST REMOVE** any `try/except` blocks that silently fallback to synthetic data if a real source (if ever implemented) fails. **MUST** ensure that if `load_dataset` or file reading fails, the script raises a specific `FileNotFoundError` with the message: "Data source not found: {path}". **MUST** document this behavior in `docs/data_strategy.md` by creating the file and adding a section "Fail-Loud Policy" explaining the behavior.
- [ ] T039 [US1] **REVISION: EXPLICIT EXCLUSION LOGGING**: Enhance `code/modeling.py` (Step 5 of T013) to create a dedicated `data/processed/excluded_participants.csv`. **MUST** log every participant `participant_id` excluded due to hyperbolic model fitting failure, along with the specific reason code (e.g., "NO_SOLUTION", "CONVERGENCE_FAIL", "INVALID_RANGE"). **MUST** update `data/processed/halt_log.json` to include the count of these excluded participants and the file path to `excluded_participants.csv`.
- [ ] T040 [US1] **REVISION: DGP SEPARATION**: Split `code/ingestion.py` into two distinct modules: `code/data/generate_dgp.py` (pure data generation) and `code/data/harmonize.py` (merging and cleaning). **MUST** create `code/data/generate_dgp.py` with function `generate_synthetic_data(params)` returning a dict of DataFrames. **MUST** create `code/data/harmonize.py` with function `harmonize_datasets(data_dict)` returning the final DataFrame. **MUST** move the DGP parameter definition and generation logic to `generate_dgp.py`. **MUST** move the merging, ID mismatch check, and reliability check logic to `harmonize.py`. **MUST** update `code/main.py` to call these in sequence. **MUST** add unit tests in `tests/test_generate_dgp.py` and `tests/test_harmonize.py` to verify each module independently.
- [ ] T041 [US2] **REVISION: MODEL DIAGNOSTICS VISUALIZATION**: Add a task to generate diagnostic plots for the OLS regression. **MUST** create `code/visualizations/plot_diagnostics.py` using `matplotlib` to generate: 1) Residuals vs Fitted plot, 2) Q-Q plot for normality, 3) Scale-Location plot. **MUST** save these plots as PNG files in `data/processed/diagnostics/` with filenames `residuals.png`, `qq_plot.png`, `scale_location.png`. **MUST** include a summary of visual inspection results in `data/processed/model_diagnostics_report.json`.
- [ ] T042 [US3] **REVISION: BOOTSTRAP SEEDING CONSISTENCY**: Ensure the bootstrapping routine in `code/robustness.py` uses a deterministic seed derived from the global `RANDOM_SEED` plus an offset (e.g., `RANDOM_SEED + 1000`) to ensure the bootstrap samples are reproducible but distinct from the DGP generation. **MUST** log the specific seed used for bootstrapping in `data/processed/bootstrap_config.json` with schema: `{"seed": int, "offset": int}`. <!-- FAILED: unspecified -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US2

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for DGP parameter generation in tests/test_ingestion.py"
Task: "Unit test for hyperbolic model fitting edge cases in tests/test_modeling.py"

# Launch all models for User Story 1 together:
Task: "Implement Data Generating Process (DGP) generator in code/ingestion.py"
Task: "Implement hyperbolic model fitting function in code/modeling.py"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Regression)
 - Developer C: User Story 3 (Robustness)
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
- **CRITICAL**: T013 MUST generate item-level data and perform reliability check.
- **CRITICAL**: T013 MUST use the hardcoded parameters as the definitive source.
- **CRITICAL**: T013 MUST calculate missingness as row-wise (count/2) and use 10% threshold.
- **CRITICAL**: T013 MUST list exact files for checksumming.
- **CRITICAL**: T022 MUST NOT remove `wm_metric` or the interaction term.
- **CRITICAL**: T022 MUST split logic into Read, Construct, Log steps.
- **CRITICAL**: T034 MUST extract helpers and add docstrings (no complexity threshold).
- **CRITICAL**: T002a MUST precede T009a.
- **CRITICAL**: T013b is a validation step within T013, not a separate code task.

---

## Phase Revision: Data Integrity & Pipeline Robustness (Addressing Analysis Findings)

**Goal**: Address specific reviewer concerns regarding data loader failure modes, explicit logging of exclusion reasons, and the separation of DGP generation from harmonization logic to ensure reproducibility and auditability.

### Implementation for Revision

- [ ] T038 [US1] **REVISION: ENHANCED DATA LOADER FAIL-SAFE**: Refactor `code/ingestion.py` to implement a strict "Fail Loud" policy for data loading. **MUST REMOVE** any `try/except` blocks that silently fallback to synthetic data if a real source (if ever implemented) fails. **MUST** ensure that if `load_dataset` or file reading fails, the script raises a specific `FileNotFoundError` with the message: "Data source not found: {path}". **MUST** document this behavior in `docs/data_strategy.md` by creating the file and adding a section "Fail-Loud Policy" explaining the behavior.
- [ ] T039 [US1] **REVISION: EXPLICIT EXCLUSION LOGGING**: Enhance `code/modeling.py` (Step 5 of T013) to create a dedicated `data/processed/excluded_participants.csv`. **MUST** log every participant `participant_id` excluded due to hyperbolic model fitting failure, along with the specific reason code (e.g., "NO_SOLUTION", "CONVERGENCE_FAIL", "INVALID_RANGE"). **MUST** update `data/processed/halt_log.json` to include the count of these excluded participants and the file path to `excluded_participants.csv`.
- [ ] T040 [US1] **REVISION: DGP SEPARATION**: Split `code/ingestion.py` into two distinct modules: `code/data/generate_dgp.py` (pure data generation) and `code/data/harmonize.py` (merging and cleaning). **MUST** create `code/data/generate_dgp.py` with function `generate_synthetic_data(params)` returning a dict of DataFrames. **MUST** create `code/data/harmonize.py` with function `harmonize_datasets(data_dict)` returning the final DataFrame. **MUST** move the DGP parameter definition and generation logic to `generate_dgp.py`. **MUST** move the merging, ID mismatch check, and reliability check logic to `harmonize.py`. **MUST** update `code/main.py` to call these in sequence. **MUST** add unit tests in `tests/test_generate_dgp.py` and `tests/test_harmonize.py` to verify each module independently.
- [ ] T041 [US2] **REVISION: MODEL DIAGNOSTICS VISUALIZATION**: Add a task to generate diagnostic plots for the OLS regression. **MUST** create `code/visualizations/plot_diagnostics.py` using `matplotlib` to generate: 1) Residuals vs Fitted plot, 2) Q-Q plot for normality, 3) Scale-Location plot. **MUST** save these plots as PNG files in `data/processed/diagnostics/` with filenames `residuals.png`, `qq_plot.png`, `scale_location.png`. **MUST** include a summary of visual inspection results in `data/processed/model_diagnostics_report.json`.
- [ ] T042 [US3] **REVISION: BOOTSTRAP SEEDING CONSISTENCY**: Ensure the bootstrapping routine in `code/robustness.py` uses a deterministic seed derived from the global `RANDOM_SEED` plus an offset (e.g., `RANDOM_SEED + 1000`) to ensure the bootstrap samples are reproducible but distinct from the DGP generation. **MUST** log the specific seed used for bootstrapping in `data/processed/bootstrap_config.json` with schema: `{"seed": int, "offset": int}`.