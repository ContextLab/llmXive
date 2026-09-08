# Tasks: Leveraging Large Language Models for Automated Code Refactoring

**Input**: Design documents from `/specs/001-leveraging-llm-refactoring/`
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

- [ ] T001 Initialize project directory structure: Create the full nested directory tree at `projects/PROJ-043-leveraging-large-language-models-for-aut/` including `code/`, `data/`, `tests/`, `paper/`, and `contracts/`. **Specifics**: Must create `code/data/`, `code/llm/`, `code/models/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/cache/`, `data/results/`. **Verification**: Run `test -d projects/PROJ-043-leveraging-large-language-models-for-aut/code/data && test -d projects/PROJ-043-leveraging-large-language-models-for-aut/code/llm` and assert exit code 0.
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/requirements.txt`. **Content**: Must include `datasets==2.18.0`, `transformers==4.38.0`, `radon==6.0.1`, `pylint==3.0.3`, `scikit-learn==1.4.0`, `statsmodels==0.14.1`, `pandas==2.2.0`, `numpy==1.26.4`, `requests==2.31.0`, `pydantic==2.6.1`, `pytest==7.4.4`. **Verification**: Run `pip install -r requirements.txt` and assert success.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools: Create `pyproject.toml` and `.ruff.toml` enabling rules E, F, W, I in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/`. **Verification**: Run `ruff check --output-format=json.` and assert exit code 0 (or expected warnings).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [US1] Implement configuration management in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/config.py`: Define variables `HF_API_KEY` (str), `RANDOM_SEED` (int), `MAX_ATTEMPTS` (int, default 400), `MIN_VALID_FUNCTIONS` (int, default 100), `TARGET_VALID_FUNCTIONS` (int, default 200), `BATCH_SIZE` (int, default 10), and `BASELINE_TOLERANCE` (float, default 0.01) with default values and type validation.
- [ ] T005a [P] Create schema files: Create `projects/PROJ-043-leveraging-large-language-models-for-aut/contracts/config.schema.yaml` and `projects/PROJ-043-leveraging-large-language-models-for-aut/contracts/output.schema.yaml` defining the required JSON structures for configuration and output artifacts. **Note**: This task must run before T005.
- [ ] T005 [P] Setup schema validation using `pydantic` in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/utils/validation.py`: Implement validation logic for `contracts/config.schema.yaml` and `contracts/output.schema.yaml`. **Dependency**: Depends on T001 and T005a. **Verification**: Create dummy payload and run `pydantic validate` asserting success.
- [ ] T006 [P] Implement robust logging and error handling infrastructure in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/utils/logging.py`
- [ ] T007 [US1] Create base data models in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/models/entities.py`: Define `FunctionSample` (fields: `code: str`, `metrics: dict`, `hash: str`) and `MetricDelta` (fields: `complexity_delta: float`, `pylint_delta: float`, `maintainability_delta: float`). **Constitution Compliance**: Implement logic to use `hash` for checksumming raw data files in `data/` as required by Constitution Principle III. **Dependency**: Depends on T005 if models are generated from schemas, otherwise parallel.
- [ ] T008 [US1] Implement caching mechanism in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/utils/cache.py` (disk-based, keyed by function hash)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Structural Analysis (Priority: P1) 🎯 MVP

**Goal**: Download Python functions from BigCode, compute structural metrics (LOC, nesting, PEP Violation Count, PEP-8 Adherence Score, Maintainability Index, Docstring Presence), and filter for valid code.

**Independent Test**: Run `projects/PROJ-043-leveraging-large-language-models-for-aut/code/data/download.py` and `projects/PROJ-043-leveraging-large-language-models-for-aut/code/data/static_analysis.py` on a local subset (10 functions) to verify a JSON file is produced with original code and multiple metrics, with no LLM API calls.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Only include if tests are explicitly requested.**

- [ ] T009 [P] [US1] Unit test for metric calculation in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/unit/test_static_analysis.py`: Implement `test_metric_calculation_returns_valid_float()` asserting that `radon` and `pylint` calls return numeric values for valid code (e.g., mock AST node with `loc=5`) and raise `SyntaxError` or `ValueError` for invalid code. **(OPTIONAL)**
- [ ] T010 [P] [US1] Unit test for dataset sampling logic in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/unit/test_download.py`: Implement `test_sampling_stops_at_limit()` asserting that the sampler stops after a configurable maximum number of attempts (400) or a target number of valid samples (200).
- [ ] T011 [P] [US1] Integration test for full data pipeline (fetch -> analyze -> save) in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/integration/test_data_pipeline.py`: Implement `test_full_pipeline_produces_json()` asserting that `data/processed/raw_metrics.json` exists and contains the required keys.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/data/download.py`: Fetch `bigcode/the-stack-dedup` via `datasets.load_dataset`. **Strict Constraints**: Loop **up to 400 attempts**; stop immediately if **200 valid samples** are found. **Error Handling**: If an insufficient number of valid samples are found (<100), halt with a clear error. If between 100 and 199 valid samples are found, **log a warning and proceed** with the available data (as per Spec US-1 Scenario 4). Handle rate limits with exponential backoff. **FAIL LOUDLY** if the canonical dataset is inaccessible.
- [ ] T013 [US1] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/data/static_analysis.py`: Parse Python AST to compute LOC, max nesting depth, parameter count, **PEP-8 Adherence Score** (normalized 0-1), and **docstring presence** (boolean); use `radon` for cyclomatic complexity; use `pylint` to compute **PEP-8 Violation Count** (integer count of style violations) and **Maintainability Index** (using `pylint`'s maintainability score or a custom calculation based on complexity and lines). Flag unparseable functions. **Distinction**: Compute these metrics strictly on the *original* code to serve as predictors.
- [ ] T014 [US1] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/data/processor.py`: Orchestrate download (T012) and analysis (T013). **Dependency**: Must wait for T007, T012, and T013 to complete. Filter out unparseable functions, **validate that count >= 100** (log warning if a low count of events, halt if <100), and save `projects/PROJ-043-leveraging-large-language-models-for-aut/data/processed/raw_metrics.json` with original code and structural predictors. **Schema**: Validate output against `contracts/output.schema.yaml` (required keys: `code`, `hash`, `loc`, `nesting_depth`, `param_count`, `pep8_violations`, `pep8_adherence_score`, `maintainability_index`, `docstring_present`). **Efficiency**: Log **functions per second**, **total execution time**, and **time vs. limit ratio** to satisfy SC-003. **Verification**: Assert `data/processed/raw_metrics.json` exists and contains the required keys.
- [ ] T014a [US1] Verify Artifact Existence: Check that `data/processed/raw_metrics.json` and `contracts/output.schema.yaml` exist before marking Phase 3 complete. **Dependency**: T014. **Verification**: Assert file existence.
- [ ] T014b [US1] Implement efficiency reporting: Calculate the **sampling success rate** (valid functions / total attempts) and compare against the 6-hour budget in a final report entry in `data/results/efficiency_report.json`. **Verification**: Assert `data/results/efficiency_report.json` contains `success_rate` and `time_elapsed`.
- [ ] T014c [US1] Validate Data Flow: Ensure T012 and T013 have successfully produced the specific JSON structure required by T014 before T014c validates the count. **Dependency**: T012, T013 (execution).
- [ ] T015 [US1] Implement caching for static metrics: Extend `projects/PROJ-043-leveraging-large-language-models-for-aut/code/utils/cache.py` to cache the *static analysis metrics* (raw metrics) keyed by function hash to prevent redundant computation if the pipeline is interrupted. **Verification**: Simulate pipeline restart and assert metrics are loaded from cache.
- [ ] T015a [US1] Explicitly Cache Static Metrics: Create a dedicated task to cache the *static analysis metrics* (raw metrics) to `data/cache/static_metrics.json` keyed by function hash, satisfying FR-007. **Dependency**: T013. **Verification**: Assert cache file exists after T013.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Zero-Shot Refactoring, Null Baseline, and Quality Measurement (Priority: P2)

**Goal**: Invoke WizardCoder API for refactoring and identity baseline, compute quality deltas (ΔComplexity, ΔPylint, ΔMaintainability).

**Independent Test**: Process multiple functions, verify API returns refactored code, identity baseline is generated, and quality metrics are calculated for original/refactored/baseline with non-null deltas.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for API retry logic and timeout handling in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/unit/test_llm_client.py`: Implement `test_retry_logic_exponential_backoff()` asserting that retries occur with increasing delays and timeout is enforced.
- [ ] T017 [P] [US2] Unit test for null baseline generation in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/unit/test_baseline.py`: Implement `test_baseline_returns_identity()` asserting that the baseline code string matches the input code string exactly.
- [ ] T018 [P] [US2] Integration test for refactoring batch processing in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/integration/test_refactoring_pipeline.py`: Implement `test_batch_processing_handles_errors()` asserting that a single failed refactoring does not crash the batch and is marked as "Refactoring Failed".

### Implementation for User Story 2

- [ ] T019 [US2] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/llm/refactoring.py`: Invoke HuggingFace Inference API for `WizardCoder-Python-13B` with zero-shot prompts; implement batching (≤10), retry logic (limited number of attempts), **timeout=60** seconds per attempt, and **integrate caching** using `projects/PROJ-043-leveraging-large-language-models-for-aut/code/utils/cache.py` with `function_hash` as the cache key (ensure cache check occurs before API call).
- [ ] T020 [US2] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/llm/baseline.py`: Generate null baseline (identity transformation) for each valid function.
- [ ] T021 [US2] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/llm/quality.py`: Calculate cyclomatic complexity, pylint scores, and **maintainability index** for original, refactored, and baseline code; compute deltas (Δ) for each. **Validation**: Calculate the delta between original and identity baseline. If `|delta| >= config.BASELINE_TOLERANCE`, **log a warning** (do not raise an error) indicating the baseline is not perfectly zero, but proceed with the calculation. **Note**: `BASELINE_TOLERANCE` is a configurable parameter representing a small, application-specific threshold.
- [ ] T022 [US2] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/llm/pipeline.py`: Orchestrate refactoring (T019), baseline (T020), and quality (T021) steps. Handle syntax errors in LLM output (mark as "Refactoring Failed") and save `projects/PROJ-043-leveraging-large-language-models-for-aut/data/processed/refactoring_results.json` with deltas. **Efficiency**: Log **total execution time**, **success rate percentage** (successful functions / total attempts) to verify SC-005 (>=95%), and **time vs. limit ratio**. **Verification**: Assert `data/processed/refactoring_results.json` exists and contains keys: `code`, `hash`, `delta_complexity`, `delta_pylint`, `delta_maintainability`.
- [ ] T022a [US2] Verify Artifact Existence: Check that `data/processed/refactoring_results.json` exists before marking Phase 4 complete. **Dependency**: T022. **Verification**: Assert file existence.
- [ ] T023 [US2] Implement caching for baseline results: Extend `projects/PROJ-043-leveraging-large-language-models-for-aut/code/utils/cache.py` to cache the *null baseline generation results* keyed by function hash to prevent redundant computation if the pipeline is interrupted. **Verification**: Simulate pipeline restart and assert baselines are loaded from cache.
- [ ] T023a [US2] Explicitly Cache Null Baseline: Create a dedicated task to cache the *null baseline generation results* to `data/cache/baseline_results.json` keyed by function hash, satisfying FR-007. **Dependency**: T020. **Verification**: Assert cache file exists after T020.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Statistical Validation (Priority: P3)

**Goal**: Fit Multiple Linear Regression (OLS), Ridge Regression, and GLM models using k-fold cross-validation; perform One-Sample T-Test (per Plan correction) on deltas; validate significance.

**Independent Test**: Feed `projects/PROJ-043-leveraging-large-language-models-for-aut/data/processed/refactoring_results.json` to `projects/PROJ-043-leveraging-large-language-models-for-aut/code/models/regression.py` and verify output of coefficients, adjusted R², and t-test p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for VIF calculation and predictor filtering in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/unit/test_regression.py`: Implement `test_vif_filters_highly_correlated_predictors()` asserting that predictors with VIF > 5 are removed.
- [ ] T025 [P] [US3] Unit test for t-test implementation in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/unit/test_stats.py`: Implement `test_ttest_returns_correct_statistic()` asserting that the t-statistic and p-value match expected values for a known dataset.
- [ ] T026 [P] [US3] Integration test for full modeling pipeline in `projects/PROJ-043-leveraging-large-language-models-for-aut/tests/integration/test_modeling_pipeline.py`: Implement `test_full_modeling_produces_summary()` asserting that `data/results/model_summary.json` contains all required fields.

### Implementation for User Story 3

- [ ] T030 [US3] Implement VIF Filtering: In `projects/PROJ-043-leveraging-large-language-models-for-aut/code/models/regression.py`, calculate Variance Inflation Factors (VIF) for all predictors; **iteratively drop the predictor with the highest VIF and re-fit the model** until all remaining predictors have VIF ≤ 5. Output the filtered predictor set to `data/processed/vif_filtered_predictors.json`. **Verification**: Assert `data/processed/vif_filtered_predictors.json` exists and contains the list of retained predictors. **Note**: This must run before OLS fitting.
- [ ] T031a [US3] [P] Implement Ridge Regression: In `projects/PROJ-043-leveraging-large-language-models-for-aut/code/models/regression.py`, implement a **k-fold cross-validation loop** that fits a Ridge Regression model on each fold using the VIF-filtered predictors. Output the coefficients from each fold. **Constraint**: The model fitting logic itself MUST utilize k-fold cross-validation as per FR-004.
- [ ] T031b [US3] [P] Implement GLM: In `projects/PROJ-043-leveraging-large-language-models-for-aut/code/models/regression.py`, implement a **k-fold cross-validation loop** that fits a Generalized Linear Model (GLM) on each fold using the VIF-filtered predictors. Output the coefficients from each fold. **Constraint**: The model fitting logic itself MUST utilize k-fold cross-validation as per FR-004.
- [ ] T031c [US3] [P] Implement OLS with CV: In `projects/PROJ-043-leveraging-large-language-models-for-aut/code/models/regression.py`, implement a **k-fold cross-validation loop** that fits the OLS model on each fold using the VIF-filtered predictors. Output the coefficients from each fold. **Constraint**: The model fitting logic itself MUST utilize k-fold cross-validation as per FR-004.
- [ ] T031d [US3] [P] Justify OLS Inclusion: Add a documented note in `code/models/regression.py` justifying the inclusion of OLS alongside Ridge/GLM as a baseline for comparison, satisfying the Plan's design while adding value. **Dependency**: T031a, T031b, T031c.
- [ ] T032a [US3] [P] Spec-Compliance Check: Implement a conditional check in `code/main.py` to verify the 'paired t-test' requirement of FR-005 against the implemented 'one-sample t-test'. If the deviation is not formally reconciled in the spec (via a 'Methodological Correction' flag), the pipeline MUST halt with a clear error. **Dependency**: T032. **Verification**: Assert that the check passes or halts correctly.
- [ ] T032 [US3] [P] Implement T-Test (Plan-Correction): Perform a **One-Sample T-Test** on the delta distribution (testing against zero). **Note**: While FR-005 specifies a "paired t-test", the Plan's "Methodological Correction" explicitly overrides this with a one-sample test for identity baselines. This task implements the Plan's correction to ensure statistical validity, referencing the Plan's deviation to resolve the traceability gap. **Verification**: Assert the test statistic and p-value are calculated correctly. **Dependency**: T032a.
- [ ] T033 [US3] Implement `projects/PROJ-043-leveraging-large-language-models-for-aut/code/main.py` (Modeling Orchestrator):
 1. Load processed data.
 2. Run VIF filtering (T030).
 3. **Validate Methodological Deviation**: Check the Plan's "Methodological Correction" flag before executing T032.
 4. Execute Ridge (T031a), GLM (T031b), and OLS (T031c) fitting.
 5. **Execute T-Test** (T032) on the delta distribution unconditionally.
 6. **Aggregate Results**: Calculate the **mean coefficients** from the k-fold results for each model type. **Train final model** on the full dataset using the mean coefficients (or report the mean coefficients directly as the final result, as per FR-008).
 7. Validate output against `contracts/output.schema.yaml`. **Failure Behavior**: If validation fails, the pipeline MUST **halt** with a clear error.
 8. Generate `projects/PROJ-043-leveraging-large-language-models-for-aut/data/results/model_summary.json` including the **mean coefficients from folds**, adjusted R² (from CV), and the T-Test result (t-statistic, p-value). **References FR-004, FR-005, FR-008, FR-010**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Generate draft paper in `projects/PROJ-043-leveraging-large-language-models-for-aut/paper/draft.md` from `data/results/model_summary.json` using the template in `specs/001-leveraging-llm-refactoring/research.md`. **Content**: Include sections on Data Acquisition, Refactoring Results, Statistical Significance, and Limitations. **Mapping**: Extract `mean_coefficients` to "Results", `p_value` to "Discussion", `success_rate` to "Data Acquisition". **Specifics**: Populate "Data Acquisition" with `success_rate`, "Refactoring Results" with `mean_coefficients`, "Statistical Significance" with `p_value` and `t_statistic`.
- [ ] T035 [P] Update `README.md` with project status, dependencies, and run instructions. **Verification**: Ensure `README.md` contains a "Usage" section with `python code/main.py` command and a "Dependencies" section.
- [ ] T036 [P] Security hardening: Implement API key masking in logs using a logging filter. **Specifics**: Register the filter on the root logger in `config.py` that redacts values matching `API_KEY=.*` or environment variable names containing `KEY`. **Verification**: Run `grep -r "API_KEY" code/` and ensure no plaintext keys are found; verify `config.py` uses `os.environ.get` with a default of `None`.
- [ ] T037 [P] Run validation: Execute `python code/main.py --validate` and verify exit code 0. **Note**: Assumes `--validate` flag is implemented in `main.py`.
- [ ] T038 [P] Profile API latency in `projects/PROJ-043-leveraging-large-language-models-for-aut/code/llm/refactoring.py` to ensure batch processing meets <60s per attempt constraint. **Verification**: Add a log entry with `time.time()` deltas and assert the average is <60s in the test suite.
- [ ] T039 [P] Ensure code passes `ruff check` and `black --check`. **Verification**: Run `ruff check.` and `black --check.` in CI and ensure exit code 0.
- [ ] T075 [P] Add `--dry-run` flag to `main.py` that executes the pipeline up to the API call stage (without making real calls) to verify data flow and schema validation before consuming API credits.
- [ ] T076 [P] Add `--sample-size` argument to `main.py` to allow overriding the default a sufficient number of attempts for testing purposes, without modifying the code.
- [ ] T077 [P] Add `--output-dir` argument to `main.py` to allow specifying a custom output directory for results, useful for running multiple experiments in parallel.
- [ ] T078 [P] Add `--seed` argument to `main.py` to allow setting a specific random seed for reproducibility of the sampling process, overriding the default in `config.py`.
- [ ] T079 [P] Add `--verbose` flag to `main.py` that enables detailed logging of every metric calculation and API response, useful for debugging specific function failures.
- [ ] T080 [P] Ensure `code/models/stats.py` handles the case where the delta distribution has zero variance (all deltas are identical) by returning a p-value at the upper bound of the scale and a warning, rather than crashing.
- [ ] T081 [P] Verify that `paper/draft.md` generation script explicitly cites the specific version of the BigCode dataset and the WizardCoder model used, ensuring the paper is reproducible.
- [ ] T082 [P] Ensure `code/data/download.py` uses `streaming=True` if the dataset is large, to prevent memory overflow on the GitHub Actions runner, and accumulates results in chunks.
- [ ] T083 [P] Ensure `code/llm/baseline.py` script explicitly copies the original code string without any modification, and verifies the hash matches before saving, to guarantee the null baseline is truly null.
- [ ] T084 [P] Ensure `code/models/regression.py` script handles the case where all predictors are dropped due to VIF > 5 by returning a warning and a model with no predictors, rather than crashing.
- [ ] T085 [P] Ensure `code/utils/cache.py` script implements a TTL (Time-To-Live) for cached API responses to prevent stale data from being used indefinitely, defaulting to a configurable duration.
- [ ] T086 [P] Ensure `code/data/static_analysis.py` script handles non-UTF-8 encoded files by skipping them and logging a warning, rather than crashing the entire pipeline.
- [ ] T087 [P] Ensure `code/llm/refactoring.py` script logs the API response time for each request, to help identify performance bottlenecks or rate limiting issues.
- [ ] T088 [P] Verify that `code/models/stats.py` script uses the correct degrees of freedom for the t-test (based on sample size) and reports the confidence interval alongside the p-value.
- [ ] T089 [P] Ensure `code/llm/refactoring.py` script implements a `max_retries` limit per function (default configurable) and logs the final failure reason if all retries are exhausted, preventing infinite loops.
- [ ] T090 [P] Ensure `code/llm/refactoring.py` script correctly detects non-Python output (e.g., markdown explanations) using a regex or AST parse check before attempting to calculate metrics, ensuring "Refactoring Failed" status is assigned correctly.
- [ ] T091 [P] Ensure `code/models/stats.py` script handles the case where the delta distribution has zero variance (all deltas are 0) by returning a p-value indicative of no statistical significance and a warning, rather than crashing.
- [ ] T092 [P] Verify that `code/models/regression.py` script handles the case where all predictors are dropped due to VIF > 5 by returning a warning and a model with no predictors, rather than crashing.
- [ ] T093 [P] Ensure `code/utils/cache.py` script implements a TTL (Time-To-Live) for cached API responses to prevent stale data from being used indefinitely, defaulting to a configurable duration.
- [ ] T094 [P] Ensure `code/data/static_analysis.py` script handles non-UTF-8 encoded files by skipping them and logging a warning, rather than crashing the entire pipeline.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (raw metrics)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data (deltas)
 - *Note: While US2 and US3 can be coded in parallel, US3 cannot run until US2 produces `refactoring_results.json`.*

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
Task: "Unit test for metric calculation in tests/unit/test_static_analysis.py"
Task: "Unit test for dataset sampling logic in tests/unit/test_download.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py"
Task: "Implement static_analysis.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `raw_metrics.json` with 5 predictors).
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Verify deltas)
4. Add User Story 3 → Test independently → Deploy/Demo (Verify statistical significance)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Metrics)
 - Developer B: User Story 2 (LLM & Deltas)
 - Developer C: User Story 3 (Modeling & Stats)
3. Stories complete and integrate independently (US3 depends on US2 output).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Data Constraint**: The pipeline MUST fail loudly if the BigCode dataset is inaccessible; no synthetic fallbacks allowed.
- **Critical API Constraint**: No silent fallback to smaller models; if WizardCoder API fails, the run halts.
- **Statistical Constraint**: Use **One-Sample T-Test** (Plan correction) as the **sole** validation method on the *delta* distribution (mathematically equivalent to paired t-test against zero), subject to T032a compliance check.
- **Model Constraint**: Implement **Multiple Linear Regression (OLS)**, **Ridge Regression**, and **GLM** as per Plan Summary.
- **Cross-Validation Requirement**: T031a, T031b, T031c MUST implement k-fold cross-validation and report **mean coefficients from folds** as the final result.
- **Error Handling**: Proceed with warning if 100-199 valid functions; halt if <100.
- **Baseline Constraint**: Use configurable `BASELINE_TOLERANCE` (default 0.01) for identity baseline delta warning; do not halt.
- **Review Resolution**: Added T075-T094 to address specific reviewer comments on caching, data hygiene, and robustness.
- **Review Resolution**: Added T031a and T031b to ensure Ridge and GLM models are implemented as per Plan Summary.
- **Review Resolution**: Corrected all file paths to match the Plan's nested project structure.
- **Review Resolution**: Unmarked T014 and T022 as complete until artifacts are generated.
- **Review Resolution**: Added T005a to create schema files before validation.
- **Review Resolution**: Added T015a and T023a to explicitly cache non-API artifacts.
- **Review Resolution**: Added T014b to calculate sampling efficiency.
- **Review Resolution**: Added T033 validation step to check Plan deviation before executing T032.
- **Review Resolution**: Added T032a to reconcile the 'paired t-test' vs 'one-sample t-test' deviation.
- **Review Resolution**: Added T031d to justify OLS inclusion alongside Ridge/GLM.
- **Review Resolution**: Renumbered T040-T060 to T075-T094 for sequential ID continuity.