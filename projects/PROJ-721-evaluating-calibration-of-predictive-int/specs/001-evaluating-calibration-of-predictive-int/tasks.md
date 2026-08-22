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

- [X] T001 [P] Initialize project directory structure: Execute `mkdir -p projects/PROJ-721-evaluating-calibration-of-predictive-int/{code,data/raw,data/processed,results,results/plots,tests/unit,tests/integration,tests/contract,contracts,state}`. **Deliverable**: Verify existence of all listed directories using `ls -R`. **Verification**: Run `ls -R projects/PROJ-721-evaluating-calibration-of-predictive-int` and confirm all subdirectories exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python project with `requirements.txt` (pins `statsmodels`, `prophet`, `lightgbm`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest-json-report`). **Deliverable**: `requirements.txt`. **Verification**: Run `pip check` to ensure no conflicts and confirm file exists.
- [ ] T003 [P] Configure linting (`ruff` or `flake8`) and formatting (`black`) tools
- [X] T004 [P] Fetch M4 dataset: Download `M4-Dataset.zip` and `manifest.json` from the official GitHub repository (URL from `research.md`) to `data/raw/`. Validate SHA256 checksums against `manifest.json` and record results in `state/checksums.yaml`. **Deliverables**: `data/raw/M4-Dataset.zip`, `state/checksums.yaml`. **Verification**: Run `sha256sum` on downloaded file and compare with `state/checksums.yaml`.
- [X] T004b [P] Create Configuration: Create `config.yaml` in the project root with keys: `learning_rate`, `step_size`, `initial_alpha`, `nominal_levels` (list of `[0.80, 0.95]` as defined in spec FR-003), `threshold` (float `0.02`, derived from Assumption: Threshold Justification), `seed` (int `42`), and `sensitivity_range` (list of floats for sweep, e.g., `[0.005, 0.15]`). **Deliverable**: `config.yaml`. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"` to confirm structure.
- [X] T005a [P] Implement ARIMA wrapper: Implement `code/models/arima_model.py` using `statsmodels.tsa.arima.model.ARIMA`. Use `order=(,1,1)` and `seasonal_order` adapted to frequency. Handle `ConvergenceWarning` by logging and returning `None`. **Verification**: Run `pytest tests/unit/test_models.py::test_arima_convergence` to confirm success.
- [X] T005b [P] Implement ETS wrapper: Implement `code/models/ets_model.py` using `statsmodels.tsa.exponential_smoothing.ETSModel`. Use `trend='add'`, `seasonal='add'`. **Verification**: Run `pytest tests/unit/test_models.py::test_ets_convergence`.
- [X] T005c [P] Implement Prophet wrapper: Implement `code/models/prophet_model.py` using `prophet.Prophet`. Use `seasonality_mode='multiplicative'`, `changepoint_prior_scale=0.05`. **Verification**: Run `pytest tests/unit/test_models.py::test_prophet_convergence`.
- [X] T005d [P] Implement LightGBM wrapper: Implement `code/models/lightgbm_quantile.py`. Use quantile regression objective. **CRITICAL**: Must support generating intervals for **80%** (alpha=0.10/0.90) and **95%** (alpha=0.025/0.975) nominal levels as defined in `config.yaml`. Input: `pd.Series` (train); Output: `dict` with `point_forecast`, `lower`, `upper`. Handle `ConvergenceWarning` by logging and returning `None`. Explicitly exclude R libraries. Add docstrings. **Verification**: Run `pytest tests/unit/test_models.py::test_lightgbm_quantile`.
- [X] T006 Implement `code/metrics.py` for empirical coverage calculation and Interval Score computation. Add docstrings to all functions. **Verification**: Run `ruff check code/metrics.py` to confirm linting passes and docstrings exist.
- [X] T007 [P] Implement `code/stratify.py` for STL decomposition (training split ONLY) and trend strength derivation (variance ratio > 0.5). Explicitly enforce that decomposition uses only training data to prevent leakage. Add docstrings to all functions. **Verification**: Run `ruff check code/stratify.py` to confirm linting passes and docstrings exist.
- [X] T008 [P] Implement `code/recalibration.py` for Adaptive Conformal Prediction post-processing. Load parameters from `config.yaml` (created in T004b). Add docstrings to all functions. **Depends on T004b**.
- [ ] T009 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for contract testing
- [X] T010 Setup `tests/unit/test_metrics.py` with synthetic ground-truth data to verify coverage calculation logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest M4, fit models, generate intervals, compute coverage, and output results for 1000 series within 6h CPU.

**Independent Test**: Run pipeline on a series of time series; verify `results/coverage.csv` contains observed coverage rates matching manual calculation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Contract test for `results/coverage.csv` schema in `tests/contract/test_coverage_schema.py`
- [X] T012 [P] [US1] Integration test for mini-pipeline (10 series) in `tests/integration/test_mini_pipeline.py`

### Implementation for User Story 1

- [ ] T013a [US1] Implement data loading and sampling logic in `code/download.py`. Select a representative set of series using stratified sampling by 'frequency' and 'seasonality' (seed=42) to achieve a sample size of **[deferred] series** (FR-001). **Verification**: Calculate the frequency distribution of the selected sample and compare to the full M4 distribution; assert that the sample represents >=90% of the original distribution (SC-005). **Deliverable**: `data/processed/sampling_report.json` containing distribution stats and sample indices. **Verification**: Assert `data/processed/sampling_report.json` exists and `coverage >= 0.90`.
- [ ] T013b [US1] Execute full 1000-series pipeline: Select the high-volume subset from T013a output. **Verification**: Confirm 1000 series are selected and logged. **Deliverable**: `data/processed/sample_indices_1000.csv`. **Depends on T013a**.
- [ ] T013c [US1] Verification Sub-sample: Select a small subset from the 1000-series sample for manual verification of coverage logic. **Deliverable**: `data/processed/sample_indices_10.csv`. **Depends on T013a**.
- [ ] T014 [US1] Implement `code/run_pipeline.py` orchestration: select the 1000-series subset from T013b output; loop over series, handle short series (skip + log), handle model convergence failures (catch + log).
- [ ] T015 [US1] Invoke models defined in T005a-d to generate prediction intervals for horizons h=1 to 12 at nominal levels **read from `config.yaml`** (0.80 and 0.95). Do not hardcode alpha values; read from config. **Depends on T005a-d**.
- [ ] T016 [US1] Implement empirical coverage calculation (proportion of test points inside interval) in `code/metrics.py`.
- [ ] T017 [US1] Implement Statistical Significance: Generate raw p-values for hypothesis testing (models × horizons) and apply Benjamini-Hochberg (BH) FDR correction using `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output: `pd.Series` of corrected p-values. **Depends on T016**.
- [ ] T018 [US1] Implement sensitivity analysis loop: Sweep the absolute deviation between empirical and nominal coverage across a **configurable range defined in `config.yaml` (`sensitivity_range`)**. **Depends on T016**. **Deliverable**: `results/sensitivity_analysis.csv`.
- [ ] T019 [US1] Write final aggregated results to `results/coverage.csv` with columns: `series_id`, `model`, `horizon`, `nominal_coverage` (values **read from `config.yaml`**), `empirical_coverage`, `deviation`, `p_raw`, `p_value` (FDR-corrected from T017). The `p_value` column corresponds to the FDR-corrected p-value for the specific **(model, horizon)** pair. **Verify** column order and types match `contracts/metrics.schema.yaml`. **Depends on T017**.
- [ ] T020 [US1] Add a GitHub Actions step to assert runtime < 6h (21600s) in workflow logs for the 1000-series subset. **Deliverable**: `.github/workflows/ci.yml`. **Verification**: Run workflow and check logs for `Runtime < 21600s`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Stratified Analysis (Priority: P2)

**Goal**: Group calibration results by seasonality and trend strength to identify systematic patterns.

**Independent Test**: Run on a pre-labeled subset; verify output groups results correctly by metadata tags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for `results/stratified_coverage.csv` schema in `tests/contract/test_stratified_schema.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement metadata validation in `code/download.py` to check for 'seasonality' and 'frequency' fields (skip series if missing + log)
- [ ] T023 [US2] Integrate `code/stratify.py` into `code/run_pipeline.py` to classify series as 'high/low' trend strength and 'yes/no' seasonality. **Depends on T013a** (shared sample indices).
- [ ] T024 [US2] Implement aggregation logic to compute average coverage deviation per subgroup (seasonality, trend strength). **Depends on T016, T023**.
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

- [ ] T028 [P] [US3] Implement adaptive conformal prediction logic in `code/recalibration.py` (post-processing step on baseline forecasts). Load ACI parameters from `config.yaml` (T004b). Target nominal coverage levels: **read from `config.yaml`**. **Deliverable**: `results/recalibration_params.json`. **Depends on T004b**.
- [ ] T040 [US3] Implement gating logic in `code/run_pipeline.py`: Check if the *initial calibration assessment* (per-series deviation from T019 AND aggregated deviation from T024) exceeds the **2% (0.02)** threshold from `config.yaml`. If true, trigger recalibration. Save gate decision to `results/recalibration_gate.json`. **Depends on T019, T024**.
- [ ] T029 [US3] Integrate recalibration into `code/run_pipeline.py` to generate recalibrated intervals for all models. **Condition**: Run ONLY if T040 gate decision is TRUE. **Depends on T028 and T040**.
- [ ] T030 [US3] Compute recalibrated coverage rates and calculate the **raw improvement** (difference) against baseline in `code/metrics.py`. **Condition**: Run ONLY if T040 gate decision is TRUE. **Depends on T016, T029, and T040**.
- [ ] T039 [US3] Implement a paired bootstrap test with **10,000 resamples** in `code/metrics.py` to verify recalibration improvement. **Condition**: Run ONLY if T040 indicates deviation > 2%. Input: baseline and recalibrated coverage arrays (from T030); Output: p-value for improvement. **Deliverable**: `results/bootstrap_pvalues.json`. **Verification**: Assert `results/bootstrap_pvalues.json` exists, contains valid p-values, and includes a `provenance` field linking to the specific model/dataset version. **Depends on T030 and T040**.
- [ ] T031 [US3] Write recalibration results to `results/recalibration.csv` with columns: `series_id`, `model`, `horizon`, `baseline_coverage`, `recalibrated_coverage`, `improvement`, `p_value_improvement` (from T039). **Depends on T039**.
- [ ] T032 [US3] Add logic to report improvement per model to allow comparison of recalibration efficacy

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Create `README.md` with usage examples and parameter descriptions
- [ ] T033b [P] Generate API docs for `code/` modules using `pydoc` or `sphinx` (requires all code to be complete)
- [ ] T034a [P] Code cleanup and refactoring (ensure no GPU imports). **Verification**: Run `ruff check code/` and confirm no GPU imports.
- [ ] T034b [P] Add memory profiling script using `tracemalloc` that logs peak usage to `results/memory.log`. **Deliverable**: `scripts/profile_memory.py`, `results/memory.log`. **Verification**: Run script and confirm log file exists with data.
- [ ] T035a [P] Vectorize operations in `code/metrics.py` for coverage calculation. **Verification**: Run `pytest tests/unit/test_metrics.py` and confirm runtime reduced compared to baseline.
- [ ] T035b [P] Optimize STL decomposition in `code/stratify.py` using `statsmodels` built-in vectorization. **Verification**: Run `pytest tests/unit/test_stratify.py` and confirm runtime reduced by a measurable margin.
- [ ] T035c [P] Profile and optimize LightGBM training loop in `code/models.py`. **Verification**: Run `pytest tests/unit/test_models.py::test_lightgbm` and confirm runtime reduced.
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
 - User story 3 is blocked until T040 (US3) and T024 (US2) are complete (Note: T040 now depends on T019 and T024, ensuring US3 waits for US2's aggregation)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data loading (T013a) and metric calculation from US1. T023 depends on T013a, allowing parallel execution with US1's model fitting.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on baseline forecasts from US1 (T019) AND gating logic (T040). T040 depends on T019 and T024.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 2 can start in parallel (if team capacity allows) - T023 depends on T013a (shared artifact), not T014 (US1 pipeline).
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
 - Developer B: User Story 2 (starts after T013a, parallel with T014)
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