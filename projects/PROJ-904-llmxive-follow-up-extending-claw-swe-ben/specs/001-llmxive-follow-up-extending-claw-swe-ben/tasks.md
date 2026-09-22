# Tasks: llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs

**Input**: Design documents from `/specs/001-context-fidelity-scaling-tradeoff/`
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

- [X] T001 [P] Create missing directory structure per implementation plan in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`: `data/`, `models/`, `experiments/`, `analysis/`, `tests/`, `utils/`. **Verification**: Run `ls -R projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` and verify the existence of exactly the directories listed above, plus `tests/unit/` and `tests/integration/`.
- [X] T002 [P] Create missing `__init__.py` files for all new directories in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`. **Verification**: Run `find projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/ -type d | wc -l` and verify the count matches the number of `__init__.py` files created (one per directory).
- [X] T003 [P] Initialize missing Python 3.11 project with `transformers`, `datasets`, `scikit-learn`, `statsmodels`, `networkx`, `pytest`, and `huggingface_hub` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt`.
- [X] T004 [P] Create missing `.ruff.toml` and `pyproject.toml` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` for linting and formatting. **Verification**: Verify `.ruff.toml` and `pyproject.toml` exist, then run `ruff check projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` and `black --check projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` to ensure no config errors.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004c [P] [US1, US2, US3] [Const-I] Create `config.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` with a hardcoded random seed variable (e.g., `RANDOM_SEED`). **Verification**: Verify `config.py` contains a `RANDOM_SEED` variable and is importable.
- [X] T004d [P] [US1] Update `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py` to import and use the seed from `config.py`. **Verification**: Verify `run_baseline.py` calls `random.seed(config.RANDOM_SEED)`.
- [X] T004e [P] [US2, US3] Update `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` and `run_7b_experiments.py` to import and use the seed from `config.py`. **Verification**: Verify both files call `random.seed(config.RANDOM_SEED)`.
- [X] T005 [P] Implement deterministic logging and error handling infrastructure in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/utils/logger.py`: implement `setup_logger()` and `log_error()` functions. **Verification**: `pytest tests/unit/test_logger.py::test_logger_initialization`.
- [X] T006a [P] [US1, US2, US3] Create base data model class `TaskInstance` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/task_instance.py`. **Verification**: `pytest tests/unit/test_models.py::test_task_instance_init`.
- [X] T006b [P] [US1, US2, US3] Create base data model class `ContextConfiguration` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/context_config.py`. **Verification**: `pytest tests/unit/test_models.py::test_context_config_init`.
- [X] T006c [P] [US1, US2, US3] Create base data model class `ExecutionResult` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/execution_result.py`. **Verification**: `pytest tests/unit/test_models.py::test_execution_result_init`.
- [X] T006d [P] [US1, US2, US3] Create entity schemas (YAML files) for `TaskInstance`, `ContextConfiguration`, `ExecutionResult` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/specs/001-context-fidelity-scaling-tradeoff/contracts/`: `task_instance.schema.yaml`, `context_config.schema.yaml`, `execution_result.schema.yaml`. **Verification**: Run `python -m jsonschema validate --schema contracts/task_instance.schema.yaml data/sample.json` (or equivalent) to verify schema validity.
- [X] T007 [P] Setup environment variable management for model paths and HF token in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py`.
- [X] T016b [P] [US1, US2, US3] Implement `BatchExecutor` class with `submit()` method in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py`. **Verification**: `pytest tests/unit/test_batch_executor.py::test_batch_submit`.
- [X] T016c [P] [US1, US2, US3] Implement `TimeoutGuard` decorator in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py`. **Verification**: `pytest tests/unit/test_batch_executor.py::test_timeout_guard`.
- [X] T026a [P] [US1, US2, US3] Implement `load_model_q4_k_m()` helper in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/quantization.py` to handle the specific loading logic for Q4_K_M quantization on CPU. **Verification**: Verify the 7B model loads successfully with Q4_K_M quantization and fits within 7GB RAM.
- [X] T026b [P] [US1, US2, US3] [FR-007] Implement memory pressure handling logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/quantization.py` using explicit memory checks (max memory within system constraints) and aggressive quantization fallbacks. **Verification**: Run a dry-run load of a 7B Q4_K_M model and verify it stays within 7GB RAM using `psutil` to log max RSS.
- [X] T026c [P] [US1, US2, US3] [FR-002, FR-004] Implement generic `ModelRunner` class in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/runner.py`. This class MUST support loading both Small-scale and large-scale models with Q4_K_M quantization on CPU, utilizing the logic from T026a/T026b. **Dependency**: This task MUST complete before T016 (US1), T023 (US2), and T027 (US3) to ensure execution tasks have a valid runner. **Verification**: Verify the 7B model loads successfully with Q4_K_M quantization and fits within 7GB RAM.
- [X] T008a [P] [US1, US2, US3] Implement `validate_schema()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py` to validate JSONL inputs against schemas. **Verification**: `pytest tests/unit/test_merge_results.py::test_validate_schema`.
- [X] T008b [P] [US1, US2, US3] Implement `aggregate_jsonl()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py` to merge JSONL files into a single CSV (Single Source of Truth). **Verification**: `pytest tests/unit/test_merge_results.py::test_aggregate_jsonl`.
- [X] T017a [P] [US1, US2, US3] [FR-008] Implement `classify_failure(log: str) -> str` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/failure_classifier.py` with explicit rule-based logic: flag "missing context" if log contains "file not found", "cannot locate", or references a file not in input context; flag "reasoning error" if file exists but logic fails. **Verification**: `pytest tests/unit/test_failure_classifier.py::test_detects_file_not_found`.
- [X] T042 [P] [Plan] [FR-006] Implement `QuantizationCalibration` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/quantization_calibration.py` to run a small pilot set (e.g., a limited number of instances) with both FP16 (if feasible) and Q4_K_M, calculating the performance drop; if >5%, set `Quantization_Penalty` flag (0/1) for the GLM model. **Dependency**: Must run before T029 (GLM) to provide the penalty covariate. **Verification**: Verify the script outputs a `quantization_penalty` boolean to a JSON file and logs the performance drop percentage.
- [X] T043 [P] [FR-007] Implement `GlobalTimeBudgetEnforcer` class in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py` that tracks the total wall-clock time of the entire experiment and terminates the batch if the time limit is exceeded. **Verification**: Create `test_batch_executor.py` and define `test_global_timeout` to verify the enforcer terminates the batch.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Context-Bound Task Filtering and Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Filter Claw-SWE-Bench for high-complexity instances (>500 lines) and execute a naive baseline with a CPU-runnable 1B model.

**Independent Test**: Run the filtering script on the raw dataset and verify the output contains only instances with >500 lines of relevant file history, then execute a single instance with the baseline model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: T010 is scaffolding.**

- [X] T010 [P] [US1] Unit test scaffolding for import graph traversal logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py`. **Note**: This is scaffolding; implementation logic follows in T012c. Scaffolding should create empty test file with import stubs for `ClawSweBenchLoader`.
- [X] T011 [P] [US1] Integration test for baseline execution timeout in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/integration/test_baseline_execution.py`.

### Implementation for User Story 1

- [ ] T012a [FR-001] [US1] Implement `ClawSweBenchLoader` streaming fetch in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: Use `datasets.load_dataset(..., streaming=True)` to fetch from Hugging Face. **Rule**: Fail loudly if fetch fails; do NOT generate synthetic data. **Output**: Stream data to a temporary buffer. **Verification**: Verify `streaming=True` is set and data can be iterated without loading all into RAM.
- [ ] T012b [FR-001] [US1] Implement **Hybrid IR-Seeding** in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: Parse `issue_description` for file paths; if none, use a **frozen generic CodeBERT-base** model (independent of experimental strategies) to embed the description and retrieve **top-5 files** via similarity. **Verification**: Verify the CodeBERT model is frozen and not the experimental strategy, and that top-5 files are retrieved.
- [ ] T012c [FR-001] [US1] Implement **Graph Traversal** in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: For each identified file, load and count lines; traverse import graph (via `networkx`) to include direct dependencies, summing lines. Filter for instances where sum > 500. Write filtered dataset to `data/filtered_swe_bench_v1.parquet`. **Verification**: Verify `data/filtered_swe_bench_v1.parquet` exists, contains only instances with >500 lines, and the derivation path is recorded in `state/...yaml`.
- [X] T040 [FR-001] [Plan] [P] Implement `RepresentativenessValidator` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/representativeness_validator.py` to perform a Kolmogorov-Smirnov (KS) test comparing the distribution of line counts and issue types in the filtered dataset vs. the full raw dataset. **Constraint**: If KS-test p-value < 0.05, the run MUST fail with "Insufficient Context-Bound Data" error. **Dependency**: Must run after T012c. **Verification**: Verify the script logs the KS statistic and p-value and fails the run if p < 0.05.
- [ ] T041 [FR-001] [Plan] [P] [FR-001-Step6] Implement `IndependenceCheck` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/construct_validity.py` to calculate the correlation between the generic retriever's scores (used for filtering) and the experimental strategies (TF-IDF, etc.). **Constraint**: If correlation >= 0.3, the run MUST fail with "Circularity Detected" error. **Dependency**: Must run after T012c. **Verification**: Verify the script logs the correlation coefficient and fails the run if >= 0.3.
- [X] T014 [P] [US1] Implement "first-N-lines" naive truncation strategy in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` (FR-002). **Note**: N=2048.
- [X] T015 [P] [US1] Configure `ModelRunner` (from T026c) for the B-parameter model (e.g., Llama-3-1B) with Q4_K_M quantization on CPU (FR-002). **Note**: This task configures the generic runner implemented in T026c; it does not re-implement the runner class.
- [ ] T016 [US1] Implement `run_baseline.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the filtered dataset with the 1B model and naive strategy. **Constraint**: Enforce a **fixed runtime budget of 60 minutes per instance** and a **total wall-clock duration of ≤72 hours** via `GlobalTimeBudgetEnforcer` (T043). Output `data/intermediate/baseline_run.jsonl` (US-1). **Dependency**: Requires T012c (Loader), T040, T041 (Validity Checks), T043 (Global Timer), T026c (ModelRunner). **Verification**: Verify `data/intermediate/baseline_run.jsonl` exists, contains >0 lines, all records validate against `execution_result.schema.yaml`, and `GlobalTimeBudgetEnforcer` was triggered and respected limits.
- [ ] T017b [US1] Apply `classify_failure()` from T017a to the baseline results (`data/intermediate/baseline_run.jsonl`) to annotate failure modes for US1 results. **Constraint**: If the classifier finds no matches, handle the "missing context" fallback scenario defined in the spec's Edge Cases. **Dependency**: Must run after T016 completes. **Verification**: Verify `data/intermediate/baseline_run.jsonl` is updated with failure mode annotations and fallback scenarios are logged.
- [X] T017c [US2] Apply `classify_failure()` from T017a to the high-fidelity results (`data/intermediate/hf_run_1b.jsonl`) to annotate failure modes for US2 results. **Dependency**: Must run after T023.
- [X] T017d [US3] Apply `classify_failure()` from T017a to the 7B results (`data/intermediate/hf_run_7b.jsonl`) to annotate failure modes for US3 results. **Dependency**: Must run after T027.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Fidelity Context Strategy Integration (Priority: P2)

**Goal**: Implement and integrate three context compression modules (TF-IDF, Heuristic Keyword-Proxy, Semantic Summarization) and execute them with the 1B model.

**Independent Test**: Run a single high-fidelity strategy (e.g., TF-IDF) on a subset and verify the context differs from baseline and produces a different output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for TF-IDF/BM25 retrieval logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`
- [X] T019 [P] [US2] Unit test for diff-aware sliding window logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement TF-IDF/BM25 relevance retrieval module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` using `scikit-learn` (FR-003). **Verification**: `pytest tests/unit/test_context_processors.py::test_tfidf_retrieval`.
- [X] T021 [P] [US2] Implement **Heuristic Keyword-Proxy** module (formerly Diff-Aware) in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py`. **Logic**: Identify lines in "relevant files" containing keywords ('fix', 'bug', 'error', 'TODO') and include a local window around them. **Verification**: `pytest tests/unit/test_context_processors.py::test_keyword_proxy_window`.
- [X] T022 [US2] [P] Implement rule-based semantic summarization module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py`. **Logic**: Extract the **first sentence of every paragraph** and the **last sentence of every function block** (defined by indentation or `def`/`function` keywords), concatenate with `...` separator, and truncate to context window. **Verification**: `pytest tests/unit/test_context_processors.py::test_semantic_summarization` verifies that logic blocks are preserved and the heuristic is implemented exactly as specified (first sentence/last sentence).
- [ ] T023 [US2] Implement `run_strategy()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` to execute the model against all three high-fidelity strategies (TF-IDF, Heuristic Keyword-Proxy, Summarization). **Constraint**: Enforce a **fixed runtime budget of 60 minutes per instance** and a **total wall-clock duration of ≤72 hours** via `GlobalTimeBudgetEnforcer` (T043) and use parallel batching. Output `data/intermediate/hf_run_1b.jsonl` (US-2). **Dependency**: Requires T026c (ModelRunner), T020-T022 (Context Processors), T043. **Verification**: Verify `data/intermediate/hf_run_1b.jsonl` exists, contains >0 lines, all records validate against `execution_result.schema.yaml`, and **all three strategies** were executed.
- [ ] T023b [US2] Implement `main()` entry point in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` to orchestrate `run_strategy()` and output files.
- [X] T024 [P] [US2] Implement `fallback_strategy()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` that returns `first_n_lines` if `retrieved_snippets` is empty, logging the event to `data/audit_logs/fallbacks.jsonl` (Edge Case Handling). **Verification**: `pytest tests/unit/test_context_processors.py::test_fallback_on_empty_result`.
- [X] T024a [P] [US2] [FR-008] Refactor `context_processors.py` to remove any `try/except` blocks that might silently fall back to synthetic/mock data if a retrieval module (TF-IDF/Diff) fails, ensuring the "Fail Loudly" rule is enforced and the run terminates with a clear error. **Verification**: Run `grep -r "generate_synthetic\|mock_" code/data/context_processors.py && exit 1` to ensure no synthetic calls exist.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Scaling Comparison and Interaction Analysis (Priority: P3)

**Goal**: Repeat experiments with a 7B model and perform GLM analysis to test for interaction effects.

**Independent Test**: Run the 7B model on baseline and high-fidelity configurations, compare Pass@1 curves, and verify the GLM analysis runs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Write test scaffolding for GLM interaction effect calculation in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_glm_analyzer.py`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `run_7b_experiments.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the large language model (7B) against all strategies (Baseline, TF-IDF, Heuristic Keyword-Proxy, Summarization). **Constraint**: Enforce a **fixed runtime budget of 60 minutes per instance** and a **total wall-clock duration of ≤72 hours** via `GlobalTimeBudgetEnforcer` (T043) and use parallel batching. **Execution**: MUST run on CPU with Q4_K_M quantization as per FR-007 and Plan Assumptions. No GPU offload. Output `data/intermediate/hf_run_7b.jsonl` (US-3). *Dependency: Must complete T026c, T026a, T026b, and T043 first.* **Verification**: Verify `data/intermediate/hf_run_7b.jsonl` exists, contains >0 lines, all records validate against `execution_result.schema.yaml`, and Q4_K_M quantization was applied (check model config logs) and **CPU-only** execution is confirmed.
- [ ] T028 [US3] Execute `merge_results.py` (T008a/T008b logic) to aggregate all JSONL files (`baseline_run.jsonl`, `hf_run_1b.jsonl`, `hf_run_7b.jsonl`) into a single `data/results.csv` (Single Source of Truth) (FR-005). *Note: Logic was implemented in Phase 2; this task executes the merge.* **Dependency**: Requires completion of T016, T023, T027. **Verification**: Verify `data/results.csv` exists and contains >0 rows.
- [ ] T029 [FR-006] [US3] Implement `run_glm(data: pd.DataFrame) -> statsmodels.GLMResults` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to perform a Generalized Linear Model (GLM) with binomial link to test for **interaction effects between "context strategy" and "model size"** (FR-006, US-3). **Formula**: `Pass ~ Model_Size + Context_Strategy + Model_Size:Context_Strategy + Task_Difficulty + Quantization_Penalty`. **Method**: Implement **Firth's penalized likelihood correction** as the primary method using `statsmodels` (if available) or fallback to `firth-logistic` (Python) or `logistf` via `rpy2`. If all fail, proceed with standard GLM and report "Separation Risk". **Verification**: Create `tests/unit/test_glm_analyzer.py` and define `test_interaction_p_value_exists` to verify the function signature, fallback logic, and interaction p-value calculation.
- [ ] T030a [US3] Implement `calculate_pairwise_diff()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the difference in Pass@1 rates between the 1B-model (high-fidelity) and 7B-model (baseline) for each strategy.
- [ ] T030b [US3] Implement `check_significance()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the margin and p-value; log values; do not enforce binary pass/fail in code (SC-004). **Verification**: Verify the function calculates margin and p-value correctly.
- [ ] T030c [US3] Generate the final comparison report in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/data/results/comparison_report.md` (or.json) by aggregating results from T030a and T030b. **Logic**: Programmatically calculate the margin and p-value for each strategy. If any strategy shows a margin ≥5% and p < 0.05 where 1B outperforms 7B, explicitly state this in the report. **If no strategy meets the criteria, explicitly state 'No strategy found where 1B outperforms 7B by ≥5% with p < 0.05'** to satisfy SC-004 and the 'Single Source of Truth' principle. **Verification**: Verify `data/results/comparison_report.md` exists, contains the specific calculated margin and p-value (or the explicit negative statement), and the logic explicitly enforces the SC-004 thresholds (margin ≥5% AND p < 0.05) as a hard constraint.
- [ ] T030d [P] [US3] [FR-006] Add a `power_analysis()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the statistical power of the experiment given the expected effect size and sample count, logging a warning if power < 0.8 to address the "Insufficient Context-Bound Data" assumption. **Verification**: Verify the function runs and logs a warning if the calculated power is below the threshold.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`. **Verification**: Verify `docs/quickstart.md` contains step 1-3 and `data-model.md` contains all entity definitions.
- [X] T036 [P] Code cleanup and refactoring of `context_processors.py`. **Verification**: Extract `load_model` function; (Wikipedia: Cyclomatic complexity, https://en.wikipedia.org/wiki/Cyclomatic_complexity).
- [X] T037 [P] Performance optimization: Fine-tune parallel batching parameters in `batch_executor.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to ensure robustness of the total wall-clock budget (FR-007).
- [X] T038 [P] Additional unit tests for edge cases (empty context, timeout) in `tests/unit/`. **Verification**: `pytest tests/unit/` passes with new tests for empty context and timeout.
- [ ] T039 [P] [FR-005, Const-III] Run checksum generation and recording for ALL data artifacts: `data/results.csv`, `data/intermediate/baseline_run.jsonl`, `data/intermediate/hf_run_*.jsonl`, and the filtered dataset. Record hashes in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml` (Constitution Principle III). **Verification**: Verify `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml` contains the expected keys and valid hashes for all listed artifacts.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on `context_processors.py` structure but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on `ModelRunner` updates (T026c), `merge_results.py` (T008a/T008b), and CPU-only execution logic.

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
Task: "Write test scaffolding for import graph traversal logic in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py"
Task: "Write test scaffolding for baseline execution timeout in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/integration/test_baseline_execution.py"

# Launch all models for User Story 1 together:
Task: "Implement ClawSweBenchLoader streaming fetch in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
Task: "Implement Hybrid IR-Seeding in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
Task: "Implement Graph Traversal in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012a -> T012b -> T012c -> T040 -> T041 -> T016)
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
 - Developer A: User Story 1 (T012a/b/c, T016)
 - Developer B: User Story 2 (T020-T023)
 - Developer C: User Story 3 (T027-T030)
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
- **Critical**: All model execution (including 7B) must run on CPU with Q4_K_M quantization as per FR-007. No GPU offload is permitted.
- **Critical**: T012a/b/c, T040, T041 must complete before T016 to ensure valid data. T042 must complete before T029. T043 must complete before T016/T023/T027.