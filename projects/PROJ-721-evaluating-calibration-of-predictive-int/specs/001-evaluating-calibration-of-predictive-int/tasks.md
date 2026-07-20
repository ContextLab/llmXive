# Tasks: Evaluating Calibration of Predictive Intervals in Time Series Forecasting

**Input**: Design documents from `/specs/001-calibration-evaluation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-721-evaluating-calibration-of-predictive-int/` with `code/`, `data/`, `results/`, `tests/`, `contracts/` subdirectories and all necessary `__init__.py` files <!-- ATOMIZE: requested -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pins `statsmodels`, `prophet`, `lightgbm`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest-json-report`)
- [ ] T003 [P] Configure linting (`ruff` or `flake8`) and formatting (`black`) tools
- [ ] T004 fetch M4 dataset (M4-Dataset.zip and manifest.json) from official GitHub repo [UNRESOLVED-CLAIM: c_f41c15b3 — status=not_enough_info] (`) and validate SHA256 checksums against manifest
- [X] T005 [P] Implement `code/models.py` with Python-only wrappers for ARIMA (`statsmodels`), ETS (`statsmodels`), Prophet (`facebookprophet`), and LightGBM.
 - **ARIMA**: Use `order=(1,1,1)` and `seasonal_order=(1,1,1,12)` (or adapt to frequency).
 - **ETS**: Use `trend='add'`, `seasonal='add'`.
 - **Prophet**: Use `seasonality_mode='multiplicative'`, `changepoint_prior_scale=0.05`.
 - **LightGBM**: Use quantile regression objective with `alpha=0.1` (for 80% intervals: 0.10/0.90 quantiles) and `alpha=0.05` (for 90% intervals: 0.05/0.95 quantiles).
 - Input: `pd.Series` (train); Output: `dict` with `point_forecast`, `lower`, `upper`. Handle `ConvergenceWarning` by logging and returning `None`. Explicitly exclude R libraries (forecast package) [UNRESOLVED-CLAIM: c_2740aa67 — status=not_enough_info]. Add docstrings to all functions.
- [X] T006 Implement `code/metrics.py` for empirical coverage calculation and Interval Score computation. Add docstrings to all functions.
- [X] T007 [P] Implement `code/stratify.py` for STL decomposition (training split ONLY) and trend strength derivation (variance ratio > 0.5). Explicitly enforce that decomposition uses only training data to prevent leakage. Add docstrings to all functions.
- [ ] T008 Implement `code/recalibration.py` for Adaptive Conformal Prediction post-processing. Load parameters from `config.yaml` which MUST contain keys: `learning_rate`, `step_size`, `initial_alpha`, `nominal_levels` (list of [0.8, 0.9]). Add docstrings to all functions.
- [ ] T009 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for contract testing
- [ ] T010 Setup `tests/unit/test_metrics.py` with synthetic ground-truth data to verify coverage calculation logic
- [ ] T040 [P] Implement gating logic in `code/run_pipeline.py` to check if the *initial calibration assessment* (aggregate or per-series) deviation exceeds the **2% (0.02)** threshold from Constitution Principle VII. The threshold value MUST be read from `config.yaml` (key `threshold`) or default to 0.02. If true, trigger recalibration. Save gate decision to `results/recalibration_gate.json`. This task is a prerequisite for US3.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest M4, fit models, generate intervals, compute coverage, and output results for 100 series within 6h CPU.

**Independent Test**: Run pipeline on a series of time series; verify `results/coverage.csv` contains observed coverage rates matching manual calculation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Contract test for `results/coverage.csv` schema in `tests/contract/test_coverage_schema.py`
- [ ] T012 [P] [US1] Integration test for mini-pipeline (10 series) in `tests/integration/test_mini_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement data loading and sampling logic in `code/download.py` to select a representative set of series for full analysis using stratified sampling by both 'frequency' and 'seasonality' (seed=42)
- [ ] T014 [US1] Implement `code/run_pipeline.py` orchestration: select a 100-series subset from T013 output for MVP verification; loop over series, handle short series (skip + log), handle model convergence failures (catch + log)
- [ ] T015 [US1] Invoke models defined in T005 to generate prediction intervals for horizons h=1 to 12 at nominal **[deferred] and [deferred]** levels in `code/models.py`. Do not re-implement model logic.
- [ ] T016 [US1] Implement empirical coverage calculation (proportion of test points inside interval) in `code/metrics.py`
- [ ] T016b [P] [US1] Implement raw p-value generation for hypothesis testing (models × horizons) in `code/metrics.py`. Output: `pd.Series` of raw p-values.
- [ ] T017 [US1] Implement Benjamini-Hochberg (BH) FDR correction for p-values across the full set of hypotheses (**models × horizons**). Input: `pd.Series` of raw p-values (from T016b); Output: `pd.Series` of corrected p-values using `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. (Note: Spec FR-007 explicitly mandates BH; BY is only for sensitivity analysis). **Depends on T016b**.
- [ ] T018 [US1] Implement sensitivity analysis loop for absolute deviation thresholds specifically at 0.01, 0.05, and 0.1 in `code/run_pipeline.py`
- [ ] T019 [US1] Write final aggregated results to `results/coverage.csv` with columns: `series_id`, `model`, `horizon`, `nominal_coverage` (values **0.80 and 0.90**), `empirical_coverage`, `deviation`, `p_raw`, `p_value` (FDR-corrected from T017). The `p_value` column corresponds to the FDR-corrected p-value for the specific **(model, horizon)** pair associated with that row. Consume FDR-corrected p-values from T017. **Depends on T017**.
- [ ] T020 [US1] Add a GitHub Actions step to assert runtime < 6h (21600s) in workflow logs for the 100-series subset

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Stratified Analysis (Priority: P2)

**Goal**: Group calibration results by seasonality and trend strength to identify systematic patterns.

**Independent Test**: Run on a pre-labeled subset; verify output groups results correctly by metadata tags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for `results/stratified_coverage.csv` schema in `tests/contract/test_stratified_schema.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement metadata validation in `code/download.py` to check for 'seasonality' and 'frequency' fields (skip series if missing + log)
- [ ] T023 [US2] Integrate `code/stratify.py` into `code/run_pipeline.py` to classify series as 'high/low' trend strength and 'yes/no' seasonality
- [ ] T024 [US2] Implement aggregation logic to compute average coverage deviation per subgroup (seasonality, trend strength)
- [ ] T025 [US2] Write stratified results to `results/stratified_coverage.csv` with columns: `subgroup_type`, `subgroup_value`, `model`, `horizon`, `avg_coverage_deviation`
- [ ] T026 [US2] Generate bar charts using `seaborn.barplot` showing avg deviation by subgroup, saved to `results/plots/stratified_bar.png`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Recalibration & Comparison (Priority: P3)

**Goal**: Apply adaptive conformal prediction to baseline forecasts and compare new coverage rates.

**Independent Test**: Apply recalibration to fixed baseline forecasts; verify coverage shifts toward nominal target.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for `results/recalibration.csv` schema in `tests/contract/test_recalibration_schema.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement adaptive conformal prediction logic in `code/recalibration.py` (post-processing step on baseline forecasts). Load ACI parameters (learning rate, step size) from `config.yaml`. Target nominal coverage levels: **[deferred] and [deferred]**.
- [ ] T029 [US3] Integrate recalibration into `code/run_pipeline.py` to generate recalibrated intervals for all models. Depends on T040 (gating logic from Phase 2).
- [ ] T030 [US3] Compute recalibrated coverage rates and compare against baseline using p-values from T039 in `code/metrics.py`. **Depends on T028 and T016**.
- [ ] T039 [US3] Implement a paired bootstrap test with exactly 10,000 resamples [UNRESOLVED-CLAIM: c_ecb55a71 — status=not_enough_info] in `code/metrics.py` to verify recalibration improvement. Input: baseline and recalibrated coverage arrays (from T030); Output: p-value for improvement. **Depends on T030**.
- [ ] T031 [US3] Write recalibration results to `results/recalibration.csv` with columns: `series_id`, `model`, `horizon`, `baseline_coverage`, `recalibrated_coverage`, `improvement`, `p_value_improvement` (from T039).
- [ ] T032 [US3] Add logic to report improvement per model to allow comparison of recalibration efficacy

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Create `README.md` with usage examples and parameter descriptions
- [ ] T033b [P] Generate API docs for `code/` modules using `pydoc` or `sphinx` (requires all code to be complete)
- [ ] T034 Code cleanup and refactoring (ensure no GPU imports). Add memory profiling script using `tracemalloc` that logs peak usage to `results/memory.log`
- [ ] T035a [P] Vectorize operations in `code/metrics.py` for coverage calculation
- [ ] T035b [P] Optimize STL decomposition in `code/stratify.py` using `statsmodels` built-in vectorization
- [ ] T035c [P] Profile and optimize LightGBM training loop in `code/models.py`
- [ ] T036 [P] Additional unit tests for edge cases (short series, model failures) in `tests/unit/`
- [ ] T037 Security hardening (ensure no external data sources other than M4 repo)
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories 1 and 2 can then proceed in parallel (if staffed)
 - User story 3 is blocked until T040 (Foundational) and T024 (US2) are complete (Note: T029 now depends on T040, T030 depends on T028/T016)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data loading and metric calculation from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on baseline forecasts from US1 AND gating logic (T040)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (except US3 which waits for T040)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for coverage.csv schema in tests/contract/test_coverage_schema.py"
Task: "Integration test for mini-pipeline (10 series) in tests/integration/test_mini_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement data loading and sampling logic in code/download.py"
Task: "Invoke models defined in T005 to generate prediction intervals in code/models.py"
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
 - Developer C: User Story 3 (after T040 is done)
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
- **Spec Note**: The `spec.md` file currently contains "[deferred]" placeholders for the [deferred]/90% levels. This is a spec-level error. The tasks above have been corrected to use **[deferred] and [deferred]** as mandated by **FR-002**. A kickback to the spec author is required to resolve the "[deferred]" placeholders in `spec.md`.