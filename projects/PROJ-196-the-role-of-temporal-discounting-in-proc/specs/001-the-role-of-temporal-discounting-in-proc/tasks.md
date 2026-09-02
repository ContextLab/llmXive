# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

**Input**: Design documents from `/specs/001-temporal-discounting-procrastination/`
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

- [X] T001 Create project structure per implementation plan. **MUST execute**: `mkdir -p projects/PROJ-196-the-role-of-temporal-discounting-in-proc/{data/raw,data/processed,code,tests,docs,specifications}`.
- [X] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn` dependencies. **MUST create** `pyproject.toml` with `[project]` section containing `dependencies = ["pandas>=2.0", "numpy>=1.24", "scipy>=1.11", "statsmodels>=0.14", "scikit-learn>=1.3"]`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **MUST create** `.ruff.toml` with `target-version = "py311"` and `pyproject.toml` tool sections for `black` and `ruff` with `line-length = 88`, `select = ["E", "F", "W", "I"]`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/raw/` and `data/processed/` directory structure. **MUST create** `.gitkeep` files in `data/raw/` and `data/processed/` to ensure directories are tracked in git.
- [X] T005 [P] Implement `requirements.txt` with pinned versions for reproducibility.
- [X] T006 [P] Configure `pytest` framework and directory structure. **MUST create** `pytest.ini` with `[pytest] testpaths = tests` and `tests/conftest.py` containing fixtures for `random_seed` and `data_path`.
- [X] T007 Create `code/__init__.py` and base configuration loader.
- [X] T008 [P] Setup seed management: Create `code/config.py` to load `RANDOM_SEED` and provide `get_random_state()` helper; explicitly pass `random_state` to all stochastic functions in `numpy`, `pandas`, `scipy` (including `stats`), and `sklearn` to ensure reproducibility per Constitution I. **MUST ALSO** run the Reference-Validator Agent against DGP parameters in `research.md` to verify literature citations before data generation.
- [X] T002a **STATE INITIALIZATION**: Create `state/projects/` directory and initialize `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with an empty `artifact_hashes` map. **MUST run before T009.**
- [X] T009 [P] Implement data checksum verification utility in `code/utils/checksum.py` AND integrate it to write/update the `artifact_hashes` map in `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` for every raw/processed artifact, ensuring Single Source of Truth traceability per Constitution Principle III and V.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest, harmonize, and process raw data (or DGP) into a unified analysis-ready dataset with calculated discount rates.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output DataFrame contains the required columns (`discount_rate_k`, `procrastination_score`, `wm_accuracy`, `wm_rt`, `age`, `gender`, `education`) with zero null values in key predictor/outcome columns after imputation or filtering.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are written first (TDD) but listed here to reflect dependency on code structure created by T013-T018.

- [X] T010 [P] [US1] Unit test for DGP parameter generation in `tests/test_ingestion.py`
- [X] T011 [P] [US1] Unit test for hyperbolic model fitting edge cases (failure cases) in `tests/test_modeling.py`
- [X] T012 [P] [US1] Integration test for full data harmonization pipeline in `tests/test_integration.py`

### Implementation for User Story 1

- [X] T013 [US1] **PRE-CHECK**: Implement DGP Configuration Validator in `code/ingestion.py`. This task validates the DGP parameters (schema definition, expected columns, reliability targets) *before* data generation. It must verify that the configuration matches the spec's requirements (e.g., Cronbach's alpha targets) and raise `SystemExit(1)` if the DGP config is invalid.
- [ ] T014 [US1] **DATA GENERATION / INGESTION**: Implement Data Ingestion in `code/ingestion.py`. **MUST FIRST check for existence of real data files** (`data/raw/delay_discounting.csv`, `data/raw/procrastination.csv`, `data/raw/nback.csv`).
 - **IF REAL DATA EXISTS**: Load the three CSV files. Validate schema (FR-001). If core constructs (`discount_rate_k`, `procrastination_score`, `wm_accuracy`) are missing, **raise `SystemExit(1)` with message "CRITICAL: Real data missing core construct: {col}"** (FR-008).
 - **IF REAL DATA MISSING**: Generate **three distinct CSV files** simulating N=500 participants based on literature parameters using `get_random_state()` (T008). **MUST FLAG** this as "Methodological Validation" in a `data/processed/data_source_flag.json` file. Each file must contain distinct experimental paradigm data.
 - **Output**: Ensure three source files exist for harmonization.
- [X] T014b [US1] **RELIABILITY CHECK**: Implement Reliability Verification in `code/ingestion.py`. This task MUST calculate Cronbach's alpha for each of the generated/loaded datasets. If any alpha < 0.7 (for synthetic) or if real data reliability cannot be verified, **raise `SystemExit(1)`** with message "CRITICAL: Data reliability below threshold (alpha < 0.7)". **MUST REFERENCE** FR-001 and Constitution Principle II. This task runs after T014 and before T015a.
- [X] T015a [US1] **HARMONIZATION**: Implement data harmonization and merging logic in `code/ingestion.py`. This task reads the three distinct source files generated/loaded by T014, merges them using `participant_id` via inner join. **MUST calculate ID mismatch rate as `1 - (len(merged_df) / len(initial_df))`**. If mismatch rate > 0.10, **raise `SystemExit(1)` with message "CRITICAL: ID mismatch > 10%"** (FR-009).
- [X] T015c [US1] **MODEL FITTING**: Implement hyperbolic model fitting function `fit_hyperbolic_model` in `code/modeling.py` using `scipy.optimize.curve_fit` (uses `get_random_state()`). This task calculates `discount_rate_k` for each participant in the harmonized dataset. **MUST EXCLUDE** participants where fitting fails and **GENERATE A WARNING LOG** with the count of excluded participants (per spec Edge Cases).
- [X] T015b [US1] **CRITICAL HALT (Data)**: Implement validation logic to check for missing core constructs (`discount_rate_k`, `procrastination_score`, `wm_accuracy`) in the *generated and harmonized* data. **MUST run AFTER T015c**. If any are missing or contain NaNs, **Raise `SystemExit(1)`** with message "CRITICAL: Missing core construct: {col}". This task MUST execute after T015c and before T016.
- [ ] T016 [US1] **MISSING DATA HANDLING**: Implement missing data handling logic in `code/ingestion.py`. If missing covariates (age, gender) >10%, **flag for reduced model** by writing `data/processed/model_config.json` with `reduced_model: true` and excluding those covariates; otherwise perform listwise deletion or mean imputation. This task MUST run *before* T022 and write the config file so downstream tasks can read it.
- [ ] T018 [US1] **WRITE DATASET**: Write the final harmonized dataset to `data/processed/harmonized_dataset.parquet`. **MUST ALSO** generate checksum for this file and update `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with the new hash.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Moderation Regression Analysis (Priority: P2)

**Goal**: Execute OLS regression to test the primary hypothesis (moderation effect) and calculate VIF.

**Independent Test**: The analysis can be fully tested by running the regression script and verifying that the output includes a coefficient and p-value for the interaction term (`log(k) * wm_metric`), and that model assumptions (VIF) are reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for interaction term creation and mean-centering in `tests/test_modeling.py`
- [X] T020 [P] [US2] Unit test for VIF calculation and threshold flagging in `tests/test_modeling.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement log-transformation of discount rate (`log(k)`) and mean-centering of predictors in `code/modeling.py`
- [ ] T022 [US2] Implement OLS regression model construction with interaction term in `code/modeling.py` (FR-004). **Depends on T016**: Read `data/processed/model_config.json`. If `reduced_model` is true, **MUST ADJUST** the regression formula to exclude flagged covariates. **MUST INCLUDE INLINE MONITORING**: Use `memory_profiler` and `time` module; if `max_memory_mb > 7168` or `elapsed_time` exceeds 50% of 6h limit, **Raise `SystemExit(1)`**.
- [X] T023 [US2] Implement VIF calculation and reporting logic (flag if > 5) in `code/modeling.py` (FR-005). **MUST WRITE** results to `data/processed/vif_report.json`.
- [X] T024 [US2] Implement extraction of coefficients, p-values, and confidence intervals for the interaction term. **MUST WRITE** results to `data/processed/interaction_results.json`.
- [ ] T025 [US2] Save regression results summary to `data/processed/regression_results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform bootstrapping and sensitivity analysis to verify stability of the interaction effect.

**Independent Test**: The robustness check can be independently tested by running the bootstrapping script and verifying that the confidence intervals for the interaction coefficient do not include zero (if the primary effect was significant) or that the stability metric is calculated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for bootstrap resampling logic (a sufficient number of resamples) in `tests/test_robustness.py`. **MUST NAME** function `test_bootstrap_resampling_generates_95ci`.
- [X] T027 [P] [US3] Unit test for sensitivity analysis threshold sweeps in `tests/test_robustness.py`. **MUST NAME** function and assert specific thresholds (median, median ± 0.05*SD, median ± 0.10*SD).

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement bootstrapping routine to generate a confidence interval for interaction coefficient in `code/robustness.py` (FR-006). **MUST WRITE** results to `data/processed/bootstrap_ci.json`. **MUST INCLUDE INLINE MONITORING**: Use `memory_profiler` and `time` module; if `max_memory_mb > 7168` or `elapsed_time` exceeds 50% of 6h limit, **Raise `SystemExit(1)`**.
- [X] T029 [US3] Implement sensitivity analysis for WM load threshold (median, ±0.05*SD, ±0.10*SD) AND discount rate (median, ±0.05*SD, ±0.10*SD) in `code/robustness.py` (FR-007). **MUST GENERATE FULL CROSS-COMBINATION SWEEP** of WM x Discount thresholds. **MUST OUTPUT** a JSON list of objects containing `threshold_value`, `p_value`, `coefficient`, `ci_lower`, `ci_upper` to `data/processed/sensitivity_sweep_raw.json`.
- [X] T030 [US3] Implement logic to calculate `instability_ratio` = (count of thresholds where 95% CI crosses zero) / (total thresholds). **Flag instability if `instability_ratio > 0.5`** (SC-004). **MUST WRITE** result to `data/processed/instability_flag.json`.
- [ ] T031 [US3] Aggregate all results (primary, bootstrap, sensitivity, instability_ratio) into a final `data/processed/final_analysis_report.json`. **MUST read** `data/processed/sensitivity_sweep_raw.json` (output of T029) and embed its content into the final report. Explicitly mandate writing the `instability_ratio` flag and the raw threshold sweep data to this JSON file.
- [X] T032 [US3] **Final Verification**: Verify total runtime and memory usage stay within 6h/7GB limits on CPU (FR-010). Use `memory_profiler` and `time` module; assert `max_memory_mb < 7168` and `elapsed_time < 21600`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Update `README.md` with execution instructions and DGP explanation. **MUST ADD** "Usage" section with command: `python code/main.py --seed` and "Data Source" section explaining the synthetic data strategy.
- [X] T034 Code cleanup and refactoring for readability: Refactor `code/ingestion.py` and `code/modeling.py` to reduce cyclomatic complexity < 10 as measured by `radon` **AND** remove all `TODO` comments. **MUST SPECIFY** functions to refactor: `fit_hyperbolic_model`, `harmonize_data`.
- [X] T035 [P] Add docstrings to all public functions in `code/`. **MUST USE** Google style with Args, Returns, Raises sections.
- [X] T036a [P] Execute pipeline end-to-end: Run `python code/main.py` to generate all artifacts.
- [X] T036b [P] Verify pipeline output: Check that all expected files in `data/processed/` exist and are non-empty.
- [X] T037 [P] Update `state.yaml` with execution hashes and completion status. **MUST UPDATE** `artifact_hashes` map with hashes for all files in `data/processed/` and set `completion_status` to "success".

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
- **CRITICAL**: T015b MUST raise SystemExit(1) on missing core constructs (including NaNs).
- **CRITICAL**: T016 MUST write `data/processed/model_config.json` to signal reduced model path.
- **CRITICAL**: T008 MUST ensure seeds are passed to ALL stochastic functions AND run Reference-Validator.
- **CRITICAL**: T022 and T028 MUST include inline resource monitoring (no separate T032b).
- **CRITICAL**: T014 MUST check for real data first, then generate synthetic if missing, and FLAG synthetic data.
- **CRITICAL**: T014b MUST halt if Cronbach's alpha < 0.7.
- **CRITICAL**: T002a MUST create state directory before T009.
- **CRITICAL**: T015a MUST calculate ID mismatch rate explicitly and halt if > 10%.
- **CRITICAL**: T029 MUST output `data/processed/sensitivity_sweep_raw.json` with full cross-combination sweep.
- **CRITICAL**: T031 MUST read `data/processed/sensitivity_sweep_raw.json`.
- **CRITICAL**: T015b MUST run AFTER T015c.
- **CRITICAL**: T022 MUST depend on T016.
- **CRITICAL**: T015c MUST handle fit failures by excluding participants and logging.
- **CRITICAL**: T018 MUST write parquet AND update state checksums.
- **CRITICAL**: T023, T024, T025 MUST write specific JSON artifacts.
- **CRITICAL**: T026, T027 MUST have specific test function names.
- **CRITICAL**: T028 MUST write bootstrap results to specific JSON.
- **CRITICAL**: T030 MUST write instability flag to specific JSON.
- **CRITICAL**: T033, T034, T035 MUST have specific content requirements.
- **CRITICAL**: T036 split into execution and verification.
- **CRITICAL**: T037 MUST update specific state keys.
