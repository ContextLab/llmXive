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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python project with `requirements.txt` (pins `statsmodels`, `prophet`, `lightgbm`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest-json-report`, `ruff`, `pre-commit`, `jsonschema`). **Deliverable**: `requirements.txt`. **Verification**: Run `pip check` to ensure no conflicts and confirm file exists.
- [X] T003 [P] Configure linting and formatting tools: **Install** `ruff` and `pre-commit` via `pip install ruff pre-commit`. Create `.ruff.toml` (with rules: `E4`, `E7`, `E9`, `F`, `I`) and `.pre-commit-config.yaml` (with hooks: `black`, `ruff`). **Deliverables**: `.ruff.toml`, `.pre-commit-config.yaml`. **Verification**: Run `ruff check .` and `pre-commit run --all-files` to confirm configuration is valid and no errors occur.
- [X] T004 [P] Fetch M4 dataset: Download `M4-Dataset.zip` and `manifest.json` from the official GitHub repository (URL from `research.md`) to `data/raw/`. Validate SHA256 checksums against `manifest.json` and record results in `state/checksums.yaml`. **Deliverables**: `data/raw/M4-Dataset.zip`, `state/checksums.yaml`. **Verification**: Run `sha256sum` on downloaded file and compare with `state/checksums.yaml`.
- [X] T004b [P] Create Configuration: Create `config.yaml` in the **project root** (`.`) with keys: `learning_rate`, `step_size`, `initial_alpha`, `nominal_levels` (list: `[0.80, 0.95]` - **Resolved implementation of [deferred] spec placeholders**), `threshold` (float: `0.02`), `seed` (int `42`), and `sensitivity_thresholds` (list of floats: `[0.01, 0.02, 0.05, 0.10]`). **Deliverable**: `config.yaml`. **Verification**: Run `python -c "import yaml, os; c=yaml.safe_load(open(os.path.join(os.getcwd(), 'config.yaml'))); assert c['nominal_levels']==[0.80, 0.95]; assert c['threshold']==0.02; assert c['sensitivity_thresholds']==[0.01, 0.02, 0.05, 0.10]"` to confirm structure and values.
- [X] T005a [P] Implement ARIMA wrapper: Implement `code/models/arima_model.py` using `statsmodels.tsa.arima.model.ARIMA`. Use `order=(1,1,1)` as default. **Fallback Rule**: If convergence fails, attempt to derive order using `pmdarima.auto_arima` (if available) or log a warning and return `None`. Handle `ConvergenceWarning` by logging and returning `None`. **Verification**: Run `pytest tests/unit/test_models.py::test_arima_convergence` to confirm success.
- [X] T005b [P] Implement ETS wrapper: Implement `code/models/ets_model.py` using `statsmodels.tsa.exponential_smoothing.ETSModel`. Use `trend='add'`, `seasonal='add'`. **Verification**: Run `pytest tests/unit/test_models.py::test_ets_convergence`.
- [X] T005c [P] Implement Prophet wrapper: Implement `code/models/prophet_model.py` using `prophet.Prophet`. Use `seasonality_mode='multiplicative'`, `changepoint_prior_scale=0.05`. **Verification**: Run `pytest tests/unit/test_models.py::test_prophet_convergence`.
- [X] T005d [P] Implement LightGBM wrapper: Implement `code/models/lightgbm_quantile.py`. Use quantile regression objective. **CRITICAL**: Must support generating intervals for nominal levels defined in `config.yaml`. Input: `pd.Series` (train); Output: `dict` with `point_forecast`, `lower`, `upper`. Handle `ConvergenceWarning` by logging and returning `None`. Explicitly exclude R libraries. Add docstrings. **Verification**: Run `pytest tests/unit/test_models.py::test_lightgbm_quantile`.
- [X] T006 [P] Implement `code/metrics.py` for empirical coverage calculation, **width calculation** (average interval width), and basic helper functions. Add docstrings to all functions. **Deliverable**: Intermediate functions ready for T042 and T016. **Verification**: Run `ruff check code/metrics.py` to confirm linting passes and docstrings exist.
- [X] T006a [P] Implement Interval Score calculation function in `code/metrics.py`: Calculate Interval Score = Width + (2/alpha) * (Lower - y) if y < Lower, or (y - Upper) if y > Upper, else 0. **Deliverable**: Function `calculate_interval_score(lower, upper, y, alpha)`. **Verification**: Run unit tests with known values to confirm formula implementation. **Depends on**: T006.
- [X] T007 [P] Implement `code/stratify.py` for STL decomposition (training split ONLY) and trend strength derivation (variance ratio > 0.5). Explicitly enforce that decomposition uses only training data to prevent leakage. Add docstrings to all functions. **Verification**: Run `ruff check code/stratify.py` to confirm linting passes and docstrings exist.
- [X] T008 [P] Implement `code/recalibration.py` for Adaptive Conformal Prediction post-processing. Load parameters from `config.yaml` (created in T004b). Add docstrings to all functions. **Depends on T004b**.
- [X] T009 [P] Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for contract testing. **Schema Requirements**: `dataset.schema.yaml` must define JSON Schema (Draft 7) for M4 series (id, frequency, seasonality, values). `output.schema.yaml` must define JSON Schema (Draft 7) for coverage results (series_id, model, horizon, nominal_coverage, empirical_coverage, deviation). **Deliverables**: `contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`. **Verification**: Validate a sample JSON file against each schema using `jsonschema` library and assert files exist.
- [X] T010 [P] Setup `tests/unit/test_metrics.py` with synthetic ground-truth data to verify coverage calculation logic. **Depends on**: T006.
- [X] T013a [US1] Execute data loading and sampling logic in `code/download.py`. Select up to 1000 representative series (or the maximum available if <1000) using stratified sampling by 'frequency' and 'seasonality' (seed=42). **Algorithm**: Calculate the **frequency distribution of series counts** in the full M4 dataset (P) and the sample distribution (Q). Select a subset such that the KL divergence between the sample distribution and the full distribution is < 0.1. **KL Divergence Formula**: KL(P||Q) = sum(P(i) * log(P(i)/Q(i))) where P is sample distribution and Q is full distribution. **Metric**: Calculate KL divergence; **VERIFY** that KL divergence < 0.1 (representing >=90% similarity) AND that the sample count is >= 1000 (or max available). **Deliverable**: `data/processed/sample_indices.csv` containing the selected series IDs. **Verification**: Assert `data/processed/sample_indices.csv` exists, contains >= 1000 rows (or max available), and the KL divergence metric is < 0.1. **Note**: This is a **single, blocking task** for sample selection; do NOT mark as [P] or run multiple sampling tasks simultaneously. **Depends on**: T004.
- [X] T013c [P] Validate M4 metadata: Implement validation in `code/download.py` to check that 'seasonality' and 'frequency' fields exist in the M4 metadata before proceeding. **Error Handling**: If required fields are missing, raise `ValueError` with a descriptive message. **Logging**: Log skipped series to `state/skipped.csv` if any partial data exists. **Deliverable**: `state/metadata_validation.json` with status 'passed' or 'failed'. **Verification**: Run with a dataset missing 'seasonality' and confirm `ValueError` is raised and `state/metadata_validation.json` reflects 'failed'. **Depends on**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest M4, fit models, generate intervals, compute coverage, and output results for 1000 series within 6h CPU.

**Independent Test**: Run pipeline on a series of time series; verify `results/coverage.csv` contains observed coverage rates matching manual calculation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for `results/coverage.csv` schema in `tests/contract/test_coverage_schema.py`. **Depends on**: T009 (schema). **Verification**: Run test against a mock JSON file conforming to the schema (do not wait for T019 data generation). **Note**: This test validates the schema, not the data content.
- [X] T012 [P] [US1] Integration test for mini-pipeline (10 series) in `tests/integration/test_mini_pipeline.py`

### Implementation for User Story 1

- [X] T013b [US1] Execute full 1000-series pipeline: Select the high-volume subset from T013a output. **Criteria**: Select series with length > 50 to ensure sufficient data for training/test split. **Definition**: 'High-volume' is defined as the **top [deferred] of series by length (sorted descending), with ties broken by `series_id` ascending**. **Verification**: Assert `data/processed/sample_indices.csv` (from T013a) contains >= 1000 rows (or max available). **Deliverable**: `data/processed/sample_indices.csv` (re-validated). **Depends on**: T013a.
- [X] T013d [US1] Verification Sub-sample: Select a small subset from the 1000-series sample for manual verification of coverage logic. **Deliverable**: `data/processed/sample_indices_10.csv`. **Depends on**: T013b.
- [X] T014 [US1] Implement `code/run_pipeline.py` orchestration: select the 1000-series subset from T013b output; loop over series, handle short series (skip + log to `state/errors.log`), handle model convergence failures (catch + log to `state/errors.log`). **Input**: `data/processed/sample_indices.csv`. **Output**: Intermediate results for coverage calculation. **Verification**: Run pipeline on 10 series and confirm `state/errors.log` exists (even if empty). **Depends on**: T013b.
- [X] T015 [US1] Invoke models defined in T005a-d to generate prediction intervals for horizons h=1 to 12 at nominal levels defined in `config.yaml` (0.80, 0.95). **Input**: `data/processed/sample_indices.csv` (from T013b). **Verification**: Confirm intervals are generated for all series and horizons. **Depends on**: T005a-d, T013b.
- [X] T042 [US1] Implement Interval Score artifact generation: Create `results/interval_scores.csv` by **calling functions from `code/metrics.py` (T006a) directly on the T015 output (intervals and actuals)**. **Deliverable**: `results/interval_scores.csv` with columns `series_id`, `model`, `horizon`, `interval_score`, `width`. **Verification**: Assert `results/interval_scores.csv` exists, contains columns `series_id`, `model`, `horizon`, `interval_score`, `width`, and values are non-negative. **Depends on**: T006a, T015.
- [X] T016 [US1] Implement empirical coverage calculation (proportion of test points inside interval) in `code/metrics.py`. **Input**: Interval outputs from T015. **Output**: `results/coverage_intermediate.csv` with columns: `series_id`, `model`, `horizon`, `empirical_coverage`. **Verification**: Assert `results/coverage_intermediate.csv` exists and coverage is calculated for each series and model (FR-004). **Depends on**: T015.
- [X] T017 [US1] Implement Statistical Significance: Generate raw p-values for hypothesis testing (models × horizons) and apply Benjamini-Hochberg (BH) FDR correction using `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. **Scope**: Correction MUST be applied across all models × horizons combined. **Input**: List of deviations per model/horizon. **Output**: `pd.Series` of corrected p-values. **Deliverable**: `results/pvalues.json` with schema: `{ "model": "string", "horizon": "int", "p_raw": "float", "p_value_fdr": "float" }` AND `results/hypotheses_list.json` listing the specific set of hypotheses (models × horizons) tested. **Verification**: Assert `results/pvalues.json` and `results/hypotheses_list.json` exist, contain valid p-values, and **assert the count of hypotheses in `hypotheses_list.json` is exactly 48** (4 models × 12 horizons). **Depends on**: T016.
- [X] T018 [US1] Implement sensitivity analysis loop: Sweep the absolute deviation between empirical and nominal coverage across the values defined in `config.yaml` (`sensitivity_thresholds`: `[0.01, 0.02, 0.05, 0.10]` - **corresponding to 'small magnitudes' in FR-008**). **Logic**: For each threshold, count series where |deviation| <= threshold. **Deliverable**: `results/sensitivity_analysis.csv` with columns: `threshold`, `count_within_threshold`, `percentage`. **Depends on**: T016.
- [X] T019 [US1] Write final aggregated results to `results/coverage.csv` with columns: `series_id`, `model`, `horizon`, `nominal_coverage` (values read from `config.yaml`), `empirical_coverage`, `deviation`, `p_raw`, `p_value` (FDR-corrected from T017), **and `pass_fail` (boolean: True if |deviation| <= 0.02, False otherwise)**. The `p_value` column corresponds to the FDR-corrected p-value for the specific **(model, horizon)** pair. **Verify** column order and types match `contracts/output.schema.yaml`. **Depends on**: T016, T017, T042.
- [X] T020 [P] [US1] Add a GitHub Actions step to assert runtime < 6h (21600s) in workflow logs for the 1000-series subset. **YAML Snippet**:
```yaml
 - name: Check Runtime
   run: |
     # Simulate runtime check locally or in CI
     START=$(date +%s)
     # ... (pipeline execution) ...
     END=$(date +%s)
     ELAPSED=$((END-START))
     if [ $ELAPSED -gt 21600 ]; then
       echo "Runtime exceeded 6 hours"
       exit 1
     fi
     echo "Runtime: $ELAPSED seconds"
   env:
     MAX_RUNTIME_SECONDS: 21600
```
**Deliverable**: `.github/workflows/ci.yml`. **Verification**: Run **local shell script** `START=$(date +%s); sleep 1; END=$(date +%s); ELAPSED=$((END-START)); if [ $ELAPSED -gt 21600 ]; then exit 1; fi` to confirm logic works. **Depends on**: T020b.
- [X] T020b [P] [US1] Record pipeline runtime metric: Add logic to `code/main.py` or `code/run_pipeline.py` to capture the total execution time and write it to `state/runtime.log`. **Deliverable**: `state/runtime.log` containing the runtime in seconds. **Verification**: Assert `state/runtime.log` exists and contains a numeric value. **Depends on**: T019.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Stratified Analysis (Priority: P2)

**Goal**: Group calibration results by seasonality and trend strength to identify systematic patterns.

**Independent Test**: Run on a pre-labeled subset; verify output groups results correctly by metadata tags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for `results/stratified_coverage.csv` schema in `tests/contract/test_stratified_schema.py`

### Implementation for User Story 2

- [X] T023 [US2] Integrate `code/stratify.py` into `code/run_pipeline.py` to classify series as 'high/low' trend strength and 'yes/no' seasonality. **Depends on**: T013a (shared sample indices).
- [X] T024 [US2] Implement aggregation logic to compute average coverage deviation per subgroup (seasonality, trend strength). **Depends on**: T016, T023.
- [X] T025 [US2] Write stratified results to `results/stratified_coverage.csv` with columns: `subgroup_type`, `subgroup_value`, `model`, `horizon`, `avg_coverage_deviation`
- [X] T026b [US2] Validate STL decomposition scope: Implement a verification step in `code/stratify.py` or a separate script to confirm that trend strength derivation uses ONLY the training split. **Verification**: Assert that the STL decomposition function is called only on the training split data (**verify input data length matches training split length**). **Deliverable**: `state/stl_validation.json` with status 'passed' or 'failed'. **Depends on**: T007.
- [X] T026 [US2] Generate bar charts using `seaborn.barplot` showing avg deviation by subgroup, saved to `results/plots/stratified_bar.png`. **Depends on**: T025, T026b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Recalibration & Comparison (Priority: P3)

**Goal**: Apply adaptive conformal prediction to baseline forecasts and compare new coverage rates.

**Independent Test**: Apply recalibration to fixed baseline forecasts; verify coverage shifts toward nominal target.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for `results/recalibration.csv` schema in `tests/contract/test_recalibration_schema.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement adaptive conformal prediction logic in `code/recalibration.py` (post-processing step on baseline forecasts). Load ACI parameters from `config.yaml` (T004b): `threshold`, `nominal_levels`. **Algorithm**: Compute conformal scores, adjust quantiles based on empirical coverage error. **Deliverable**: `results/recalibration_params.json` with schema: `{model, horizon, adjusted_quantile, original_quantile}`. **Depends on**: T004b, T015.
- [X] T040 [US3] Report calibration status: Check if the *initial calibration assessment* (per-series deviation from T019 AND aggregated deviation from T024) exceeds the threshold value 0.02 (derived from SC-002). **Logic**: Calculate the **maximum absolute deviation across all model/horizon pairs in T019**. If max_deviation > 0.02, status is 'non-compliant'; otherwise 'compliant'. **Verification**: Assert `config.yaml` threshold == 0.02 before use. **Explicit Check**: Verify that the baseline deviation > 0.02 for at least one model/horizon pair if the status is 'non-compliant'. **Note**: Recalibration is triggered **ONLY** if status is 'non-compliant' per Constitution Principle VII. **Deliverable**: `results/baseline_compliance.json` (status: 'compliant' if max_dev <= 0.02, 'non-compliant' otherwise). **Depends on**: T019, T024.
- [X] T029 [US3] Integrate recalibration into `code/run_pipeline.py` to generate recalibrated intervals for all models. **Condition**: Run **ONLY** if T040 status is 'non-compliant'. **Depends on**: T028, T015, T040.
- [X] T030 [US3] Compute recalibrated coverage rates and calculate the **raw improvement** (difference) against baseline in `code/metrics.py`. **Condition**: Run **ONLY** if T040 status is 'non-compliant'. **Depends on**: T016, T029.
- [X] T039 [US3] Implement a paired bootstrap test with a sufficient number of resamples in `code/metrics.py` to verify recalibration improvement. **Input**: Baseline and recalibrated coverage arrays (from T030 and T019). **Method**: Non-parametric paired bootstrap test (bootstrap the **mean difference of paired coverage rates**). **Test Statistic**: Mean difference of coverage rates. **Output**: `results/bootstrap_pvalues.json` with schema: `{model, horizon, p_value, resamples}`. **Verification**: Assert `results/bootstrap_pvalues.json` exists, contains valid p-values, `resamples` == 10000, and includes a `provenance` field linking to the specific model/dataset version. **Condition**: Run **ONLY** if T040 status is 'non-compliant' per Constitution Principle VII. **Depends on**: T030, T019, T040.
- [X] T041 [US3] Apply Benjamini-Hochberg FDR correction to the recalibration improvement p-values generated in T039. **Input**: `results/bootstrap_pvalues.json`. **Output**: `results/recalibration_pvalues_fdr.json` with corrected p-values. **Verification**: Assert `results/recalibration_pvalues_fdr.json` exists and contains corrected p-values for all model/horizon pairs. **Depends on**: T039.
- [X] T031 [US3] Write recalibration results to `results/recalibration.csv` with columns: `series_id`, `model`, `horizon`, `baseline_coverage`, `recalibrated_coverage`, `improvement`, `p_value_improvement` (FDR-corrected from T041). **Depends on**: T041.
- [X] T032 [US3] Add logic to report improvement per model to allow comparison of recalibration efficacy

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033a [P] Create `README.md` with usage examples and parameter descriptions
- [X] T033b [P] Generate API docs for `code/` modules using `pydoc` or `sphinx` (requires all code to be complete)
- [X] T034a [P] Code cleanup and refactoring (ensure no GPU imports). **Verification**: Run `ruff check code/` and confirm no GPU imports.
- [X] T034b [P] Add memory profiling script using `tracemalloc` that logs peak usage to `results/memory.log`. **Deliverable**: `scripts/profile_memory.py`, `results/memory.log`. **Verification**: Run script and confirm log file exists with data.
- [X] T035a [P] Vectorize operations in `code/metrics.py` for coverage calculation. **Verification**: Run `pytest tests/unit/test_metrics.py` and confirm runtime reduced compared to baseline.
- [X] T035b [P] Optimize STL decomposition in `code/stratify.py` using `statsmodels` built-in vectorization. **Verification**: Run `pytest tests/unit/test_stratify.py` and confirm runtime reduced by a measurable margin.
- [X] T035c [P] Profile and optimize LightGBM training loop in `code/models.py`. **Verification**: Run `pytest tests/unit/test_models.py::test_lightgbm` and confirm runtime reduced.
- [X] T036 [P] Additional unit tests for edge cases (short series, model failures) in `tests/unit/`
- [X] T037 Security hardening (ensure no external data sources other than M4 repo)
- [X] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data loading (T013a) and metric calculation from US1. T023 depends on T013a, allowing parallel execution with US1's model fitting. T024 depends on T016, so US2 aggregation cannot run in parallel with US1 model fitting.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on baseline forecasts from US1 (T019) AND reporting logic (T040). T040 depends on T019 and T024.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 2 can start in parallel (if team capacity allows) - T023 depends on T013a (shared artifact), not T014 (US1 pipeline). **Note**: T024 depends on T016, so the aggregation step in US2 must wait for US1's T016 to complete; full parallelism is limited to the model fitting and stratification logic, not the final aggregation.
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
- **Recalibration Logic**: Per Constitution Principle VII, recalibration is triggered ONLY if deviation > 2%. Tasks T029, T030, T039, T040 enforce this conditional trigger.
- **Interval Score**: Task T042 implements the Interval Score metric required by Constitution Principle VI.
- **Sampling**: Task T013a ensures a representative sample with KL divergence < 0.1.
- **Schemas**: Task T009 ensures data hygiene via JSON Schema validation.
- **STL Validation**: Task T026b ensures no data leakage by verifying STL uses only training data.
- **ARIMA Order**: Task T005a uses `order=(1,1,1)` as a default; use `auto_arima` if specific orders are unknown.
- **High-Volume Subset**: Task T013b defines 'high-volume' as top [deferred] by length.
- **Bootstrap Test**: Task T039 uses mean difference of coverage rates as the test statistic.
- **Hypothesis Count**: Task T017 verifies exactly 48 hypotheses (4 models × 12 horizons).
- **Runtime Check**: Task T020 uses local shell commands for verification.
- **KL Divergence**: Task T013a uses frequency distribution of series counts.
- **Config Path**: Task T004b places `config.yaml` in the project root.
- **Linter Install**: Task T003 installs `ruff` and `pre-commit` before checking.