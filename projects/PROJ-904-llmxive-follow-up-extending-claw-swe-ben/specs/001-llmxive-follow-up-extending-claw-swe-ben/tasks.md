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

- [X] T001 [P] Create missing directory structure per implementation plan in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`: `data/`, `models/`, `experiments/`, `analysis/`, `tests/`, `utils/`. **Verification**: Run `test -d projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data && test -d projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models && test -d projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments && test -d projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis && test -d projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests && test -d projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/utils` and verify all directories exist.
- [X] T002 [P] Create missing `__init__.py` files for all new directories in `projects/PROJ-llmxive-follow-up-extending-claw-swe-ben/code/`. **Verification**: Run `find projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/ -type d | wc -l` and verify the count matches the number of `__init__.py` files created (one per directory).
- [X] T003 [P] Initialize missing Python 3.11 project with `transformers`, `datasets`, `scikit-learn`, `statsmodels`, `networkx`, `pytest`, and `huggingface_hub` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt`. **Verification**: Verify file exists at `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt` and run `pip check` to ensure no dependency conflicts.
- [X] T004 [P] Create missing `.ruff.toml`, `pyproject.toml`, and `pypy.toml` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` for linting and formatting. **Verification**: Verify `.ruff.toml`, `pyproject.toml`, and `pypy.toml` exist. Run `ruff check projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` and `black --check projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` to ensure no config errors.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004c [P] [US1, US2, US3] [Const-I] Create `config.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` with a hardcoded random seed variable (e.g., `RANDOM_SEED`) and `BASELINE_N_LINES = 2048`. **Logic**: Set `BASELINE_N_LINES` to 2048 as a reasonable default for "substantial" lines per plan context, noting it can be adjusted if needed. **Verification**: Run `python -c "from config import RANDOM_SEED; print(RANDOM_SEED)"` to verify importability and value.
- [X] T004d [P] [US1] Update `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py` to import and use the seed from `config.py`. **Verification**: Verify `run_baseline.py` calls `random.seed(config.RANDOM_SEED)`.
- [X] T004e [P] [US2, US3] Update `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` and `run_7b_experiments.py` to import and use the seed from `config.py`. **Verification**: Verify both files call `random.seed(config.RANDOM_SEED)`.
- [X] T005 [P] Implement deterministic logging and error handling infrastructure in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/utils/logger.py`: implement `setup_logger()` and `log_error()` functions. **Verification**: `pytest tests/unit/test_logger.py::test_logger_initialization`.
- [X] T006a [P] [US1, US2, US3] Create base data model class `TaskInstance` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/task_instance.py`. **Verification**: `pytest tests/unit/test_models.py::test_task_instance_init`.
- [X] T006b [P] [US1, US2, US3] Create base data model class `ContextConfiguration` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/context_config.py`. **Verification**: `pytest tests/unit/test_models.py::test_context_config_init`.
- [X] T006c [P] [US1, US2, US3] Create base data model class `ExecutionResult` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/execution_result.py`. **Verification**: `pytest tests/unit/test_models.py::test_execution_result_init`.
- [X] T006d-1 [P] [US1, US2, US3] Create entity schemas (YAML files) for `TaskInstance`, `ContextConfiguration`, `ExecutionResult` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/specs/001-context-fidelity-scaling-tradeoff/contracts/`: `task_instance.schema.yaml`, `context_config.schema.yaml`, `execution_result.schema.yaml`. **Verification**: Verify files exist and are valid YAML.
- [X] T006d-2 [US1, US2, US3] Generate `data/sample.json` using the schemas created in T006d-1 to provide test data for validation. **Logic**: Generate a valid JSON file that conforms to the `task_instance.schema.yaml` structure. **Dependency**: This task MUST run after T006d-1 and before T006d-3. It cannot run in parallel with T006d-3. **Verification**: Verify `data/sample.json` exists and is valid JSON matching the schema structure.
- [X] T006d-3 [US1, US2, US3] Validate `data/sample.json` against the schemas in T006d-1. **Verification**: Run `python -m jsonschema validate --schema contracts/task_instance.schema.yaml data/sample.json` (or equivalent) to verify schema validity.
- [X] T007 [P] Setup environment variable management for model paths and HF token in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py`. **Verification**: Verify `config.py` contains `HF_TOKEN`, `MODEL_PATH`, and `RANDOM_SEED` variables and is importable.
- [X] T016b [P] [US1, US2, US3] Implement `BatchExecutor` class with `submit()` method in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py`. **Verification**: `pytest tests/unit/test_batch_executor.py::test_batch_submit`.
- [X] T016c [P] [US1, US2, US3] Implement `TimeoutGuard` decorator in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py`. **Verification**: `pytest tests/unit/test_batch_executor.py::test_timeout_guard`.
- [X] T026a [P] [US1, US2, US3] Implement `load_model_q4_k_m()` helper in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/quantization.py` to handle the specific loading logic for Q4_K_M quantization on CPU. **Logic**: Use `bitsandbytes` for 1B model and `GGUF` for 7B model. **Verification**: Verify the code explicitly sets `device='cpu'`, `load_in_8bit=True` or equivalent quantization flags, and uses `GGUF` or `bitsandbytes` as per plan. (Static check: `grep -r "device.*cpu" code/models/quantization.py`). **Verification**: Verify unit tests exist for `load_model_q4_k_m`.
- [X] T026b [P] [US1, US2, US3] [FR-007] Implement memory pressure handling logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/quantization.py` using explicit memory checks (max memory within system constraints) and aggressive quantization fallbacks. **Verification**: Verify the code includes `psutil` or `torch.cuda.mem_get_info` (if applicable) checks and fallback logic.
- [X] T026c [P] [US1, US2, US3] [FR-002, FR-004] Implement generic `ModelRunner` class in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/runner.py`. This class MUST support loading both Small-scale and large-scale models with Q4_K_M quantization on CPU, utilizing the logic from T026a/T026b. **Dependency**: This task MUST complete before T016 (US1), T023 (US2), and T027 (US3) to ensure execution tasks have a valid runner. **Verification**: Run a "smoke test" load of the 7B model on CPU to verify it fits within 7GB RAM (runtime check). **Verification**: Explicitly confirm `device='cpu'` is enforced in the model config.
- [X] T042 [P] [US3] [FR-007] Implement `QuantizationCalibration` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/calibration.py`. Run a pilot on instance. **Logic**: If OOM, write `state/quantization_penalty.json` with a penalty value indicating the fallback state due to out-of-memory conditions. If success, write `{"penalty": <calibrated_value>, "reason": "calibrated"}`. **Verification**: Verify `state/quantization_penalty.json` exists and contains the `penalty` key (float) and `reason` key (string).
- [X] T044 [P] [US1, US2, US3] Implement `RuntimeEstimator` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/runtime_estimator.py`. **Logic**: Read `state/quantization_penalty.json` (from T042) to calculate estimated total duration. If T042 output is missing, use default penalty 0.0. **Dependency**: Must run after T042 completes (success or failure). **Verification**: Verify the script reads the penalty file (or uses default) and outputs an estimated duration.
- [X] T043 [P] [US1, US2, US3] Implement `GlobalTimeBudgetEnforcer` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/time_budget.py`. **Logic**: Enforce a per-instance time limit and a 72h total duration. **Dependency**: Must run after T044 (Estimator) to validate feasibility before enforcement. **Verification**: Verify the script enforces the time limits.
- [X] T045 [P] [US1, US2, US3] [FR-001] Implement `DatasetThresholdValidator` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/threshold_validator.py` to count rows in `data/filtered_swe_bench_v1.parquet`. **Logic**: If rows < 50, raise "Insufficient Context-Bound Data" (exit 1). If 50 <= rows < 800, log "Exploratory Mode" (exit 0). If rows >= 800, log "Confirmatory Mode" (exit 0). **Note**: The 50-row threshold applies to the *filtered* dataset count. **Dependency**: Must run after T012c-3. **Verification**: Verify the script logs `\"Row count: {N}\"` and exits with code 1 if N < 50, code 0 otherwise.
- [X] T008a [P] [US1, US2, US3] Implement `validate_schema()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py` to validate JSONL inputs against schemas. **Verification**: `pytest tests/unit/test_merge_results.py::test_validate_schema`.
- [X] T008b [P] [US1, US2, US3] Implement `aggregate_jsonl()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py` to merge JSONL files into a single CSV (Single Source of Truth). **Verification**: `pytest tests/unit/test_merge_results.py::test_aggregate_jsonl`.
- [X] T017a [P] [US1, US2, US3] [FR-008] Implement `classify_failure(log: str) -> str` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/failure_classifier.py` with explicit rule-based logic: flag "missing context" if log contains "file not found", "cannot locate", or references a file not in input context; flag "reasoning error" if file exists but logic fails. **Verification**: `pytest tests/unit/test_failure_classifier.py::test_detects_file_not_found`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Context-Bound Task Filtering and Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Filter Claw-SWE-Bench for high-complexity instances (>500 lines) and execute a naive baseline with a CPU-runnable large-scale model.

**Independent Test**: Run the filtering script on the raw dataset and verify the output contains only instances with >500 lines of relevant file history, then execute a single instance with the baseline model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: T010 is scaffolding.**

- [X] T010 [P] [US1] Unit test scaffolding for import graph traversal logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py`. **Note**: This is scaffolding; implementation logic follows in T012c-1. Scaffolding should create empty test file with import stubs for `ClawSweBenchLoader`.
- [X] T011 [P] [US1] Integration test for baseline execution timeout in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/integration/test_baseline_execution.py`.

### Implementation for User Story 1

- [X] T012a [FR-001] [US1] Implement `ClawSweBenchLoader` streaming fetch in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: Use `datasets.load_dataset(..., streaming=True)` to fetch from Hugging Face. **Rule**: Fail loudly if fetch fails; do NOT generate synthetic data. **Output**: Stream data to a temporary buffer. **Verification**: Verify `streaming=True` is set and data can be iterated without loading all into RAM.
- [X] T012b [FR-001] [US1] Implement static analysis for file retrieval in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: Parse `issue_description` for file paths using regex (e.g., `.*\.[py|js|ts]`). **Hybrid IR-Seeding**: If no paths found, use frozen CodeBERT to retrieve top-k candidates. **Rule**: Final filtering metric (line count) MUST be purely static. **Verification**: Verify the logic uses regex and import graph traversal for file identification and retrieval.
- [X] T012c-1 [P] [FR-001] [US1] Implement Graph Traversal logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: For each identified file, load and count lines; traverse import graph (via `networkx`) to include direct dependencies, summing lines. **Verification**: Verify the graph traversal logic correctly sums lines.
- [X] T012c-2 [P] [FR-001] [US1] Implement Filtering logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: Filter for instances where sum > 500. **Verification**: Verify the filtering logic correctly applies the >500 threshold.
- [X] T012c-3 [P] [FR-001] [US1] Implement Parquet writing logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py`. **Logic**: Write filtered dataset to `data/filtered_swe_bench_v1.parquet` with schema: `instance_id` (str), `line_count` (int), `files_in_context` (list), `issue_description` (str), `repo_state` (str). **Verification**: Verify `data/filtered_swe_bench_v1.parquet` exists, contains only instances with >500 lines, and the derivation path is recorded in `state/...yaml`.
- [X] T014 [P] [US1] Implement "first-N-lines" naive truncation strategy in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` (FR-002). **Logic**: Use `N` from `config.py.BASELINE_N_LINES`. **Verification**: Verify the function uses the config value.
- [X] T015 [P] [US1] Configure `ModelRunner` (from T026c) for the B-parameter model (e.g., Llama-3-1B) with Q4_K_M quantization on CPU (FR-002). **Note**: This task configures the generic runner implemented in T026c; it does not re-implement the runner class.
- [X] T016 [US1] Implement `run_baseline.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the filtered dataset with the 1B model and naive strategy. **Constraint**: Enforce a **fixed runtime budget of 60 minutes per instance** and a **total wall-clock duration of ≤72 hours** via `GlobalTimeBudgetEnforcer` (T043). **Logic**: Calculate Pass@ as 1 if any of N attempts pass the unit tests (from `test_patch`), else 0. **Output**: Generate `data/intermediate/baseline_run.jsonl` (US-1). **Verification**: Verify `data/intermediate/baseline_run.jsonl` exists, contains >0 lines, all records validate against `execution_result.schema.yaml`, `Pass@1` was calculated correctly (1 if any of N attempts pass, else 0), the 'first-N-lines' strategy is recorded in the output, and `GlobalTimeBudgetEnforcer` was triggered and respected limits. **Dependency**: Must run after T045, T042, T044, T043.
- [X] T017b [US1] Apply `classify_failure()` from T017a to the baseline results (`data/intermediate/baseline_run.jsonl`) to annotate failure modes for US1 results. **Dependency**: Must run after T016. **Verification**: Verify `data/intermediate/baseline_run.jsonl` is updated with failure mode annotations.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Fidelity Context Strategy Integration (Priority: P2)

**Goal**: Implement and integrate three context compression modules (TF-IDF, Diff-Aware, Semantic Summarization) and execute them with the 1B model.

**Independent Test**: Run a single high-fidelity strategy (e.g., TF-IDF) on a subset and verify the context differs from baseline and produces a different output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for TF-IDF/BM25 retrieval logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`
- [X] T019 [P] [US2] Unit test for diff-aware sliding window logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`

### Implementation for User Story 2)

- [X] T020 [P] [US2] Implement TF-IDF/BM25 relevance retrieval module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` using `scikit-learn` (FR-003). **Verification**: `pytest tests/unit/test_context_processors.py::test_tfidf_retrieval`.
- [X] T021 [P] [US2] Implement **Heuristic Keyword-Proxy** (formerly Diff-Aware) module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py`. **Logic**: Search relevant files for keywords ('fix', 'bug', 'error', 'TODO'). Include a sliding window of a predefined size around each identified keyword match. **Do NOT use `difflib` on issue descriptions.** **Verification**: `pytest tests/unit/test_context_processors.py::test_keyword_proxy_window`. **Note**: Explicitly log that this is a construct validity limitation and a lower-bound proxy for "diff-aware" retrieval.
- [X] T022 [P] [US2] Implement rule-based semantic summarization module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py`. **Logic**: Extract the **first sentence of every paragraph** and the **last sentence of every function block** (defined by indentation or `def`/`function` keywords), concatenate with `...` separator, and truncate to context window. **Verification**: `pytest tests/unit/test_context_processors.py::test_semantic_summarization` verifies that logic blocks are preserved and the heuristic is implemented exactly as specified (first sentence/last sentence). **Verification**: Explicitly check that the output context is truncated to the defined context window.
- [X] T023 [US2] Implement `run_strategy()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` to execute the 1B model against **all four strategies**: Baseline, TF-IDF, Diff-Aware (Keyword-Proxy), and Summarization. **Constraint**: Enforce a **fixed runtime budget of 60 minutes per instance** and a **total wall-clock duration of ≤72 hours** via `GlobalTimeBudgetEnforcer` (T043) and use parallel batching. **Output**: Generate `data/intermediate/hf_run_1b.jsonl` (US-2). **Verification**: Verify `data/intermediate/hf_run_1b.jsonl` exists, contains >0 lines, all records validate against `execution_result.schema.yaml`, **all four strategies** are present in the output (check `strategy` field values), and `GlobalTimeBudgetEnforcer` was triggered and respected limits. **Dependency**: Must run after T045, T042, T044, T043.
- [X] T023b [US2] Implement `main()` entry point in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` to orchestrate `run_strategy()` and output files.
- [X] T024 [P] [US2] Implement `fallback_strategy()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` that returns `first_n_lines` if `retrieved_snippets` is empty, logging the event to `data/audit_logs/fallbacks.jsonl` (Edge Case Handling). **Verification**: `pytest tests/unit/test_context_processors.py::test_fallback_on_empty_result`.
- [X] T024a [P] [US2] [FR-008] Refactor `context_processors.py` to remove any `try/except` blocks that might silently fall back to synthetic/mock data if a retrieval module (TF-IDF/Diff) fails, ensuring the "Fail Loudly" rule is enforced and the run terminates with a clear error. **Verification**: Run `grep -r "generate_synthetic\|mock_" code/data/context_processors.py && exit 1` to ensure no synthetic calls exist.
- [X] T017c [US2] Apply `classify_failure()` from T017a to the high-fidelity results (`data/intermediate/hf_run_1b.jsonl`) to annotate failure modes for US2 results. **Dependency**: Must run after T023. **Verification**: Verify `data/intermediate/hf_run_1b.jsonl` is updated with failure mode annotations.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Scaling Comparison and Interaction Analysis (Priority: P3)

**Goal**: Repeat experiments with a 7B model and perform GLM analysis to test for interaction effects.

**Independent Test**: Run the 7B model on baseline and high-fidelity configurations, compare Pass@1 curves, and verify the GLM analysis runs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Write test scaffolding for GLM interaction effect calculation in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_glm_analyzer.py`.

### Implementation for User Story 3

- [X] T027 [US3] Implement `run_7b_experiments.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the 7B model against **all four strategies**: Baseline, TF-IDF, Diff-Aware (Keyword-Proxy), and Summarization. **Constraint**: Enforce a **fixed runtime budget of 60 minutes per instance** and a **total wall-clock duration of ≤72 hours** via `GlobalTimeBudgetEnforcer` (T043) and use parallel batching. **Execution**: MUST run on CPU with Q4_K_M quantization as per FR-007. No GPU offload. **Output**: Generate `data/intermediate/hf_run_7b.jsonl` (US-3). *Dependency: Must complete T026c, T026a, T026b, and T043.* **Verification**: Verify `data/intermediate/hf_run_7b.jsonl` exists, contains >0 lines, all records validate against `execution_result.schema.yaml`, Q4_K_M quantization was applied (check model config logs for 'q4_k_m'), `device=cpu` is confirmed in logs, `GlobalTimeBudgetEnforcer` was triggered and respected limits, and **all four strategies** are present. **Dependency**: Must run after T045, T042, T044, T043.
- [X] T028 [US3] Execute `merge_results.py` (T008a/T008b logic) to aggregate all JSONL files (`baseline_run.jsonl`, `hf_run_1b.jsonl`, `hf_run_7b.jsonl`) into a single `data/results.csv` (Single Source of Truth) (FR-005). **Logic**: This task invokes the aggregation logic implemented in T008a/T008b. **Dependency**: Requires completion of T016, T023, T027. **Verification**: Verify `data/results.csv` exists and contains >0 rows.
- [X] T029a [US3] Implement `run_glm_formula()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to perform a Generalized Linear Model (GLM) with binomial link. **Formula**: `Pass ~ Model_Size + Context_Strategy + Model_Size:Context_Strategy + Task_Difficulty + Quantization_Penalty`. **Verification**: Verify the function signature and formula construction.
- [X] T029b [FR-006] [US3] Implement Firth penalization fallback in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py`. **Logic**: Attempt Firth (statsmodels/rpy2). If fails, fallback to standard GLM and log "Separation Risk". **Clarification**: Firth is an implementation choice to satisfy FR-006's binomial link under sparse data; the fallback ensures spec compliance. **Verification**: Verify logs confirm Firth invocation or fallback, and interaction p-value is non-NaN.
- [X] T029c [P] [US3] [FR-006] Add a `power_analysis()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the statistical power of the experiment given the expected effect size and sample count. **Logic**: If N < 800, explicitly set the `study_type` flag to "Exploratory" and ensure the primary metric reported is the Odds Ratio with 95% CI, not just p-values. **Verification**: Verify the function runs and logs a warning if the calculated power is below the threshold, and sets the `study_type` flag correctly.
- [X] T030a [US3] Implement `calculate_pairwise_diff()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the difference in Pass@1 rates between the 1B-model (high-fidelity) and 7B-model (baseline) for each strategy.
- [X] T030b [US3] Implement `check_significance()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the margin and p-value; log values; do not enforce binary pass/fail in code (SC-004). **Verification**: Verify the function calculates margin and p-value correctly.
- [X] T030c [US3] Generate the final comparison report in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/data/results/comparison_report.md` (or.json) by aggregating results from T030a and T030b. **Logic**: Programmatically calculate the margin and p-value for each strategy from `data/results.csv`. **Write a boolean flag `strategy_found` (True/False), the specific `margin` (float, percentage difference), `p_value` (float, 4 decimal places), `odds_ratio` (float), `ci_lower` (float), `ci_upper` (float), and `study_type` (string) to `data/analysis_flags.json`** to ensure machine-readability and satisfy SC-004. **Output Schema**: The JSON file MUST contain exactly these keys with these types: `{"strategy_found": bool, "margin": float, "p_value": float, "odds_ratio": float, "ci_lower": float, "ci_upper": float, "study_type": "Exploratory" | "Confirmatory"}`. **If** any strategy shows a margin ≥5% and p < 0.05 where 1B outperforms 7B, explicitly state this in the report. **If no strategy meets the criteria**, explicitly state 'No strategy found where 1B outperforms 7B by ≥5% with p < 0.05'. **If N < 800**, ensure the report prioritizes Odds Ratio/CI. **Verification**: Verify `data/analysis_flags.json` contains the `strategy_found`, `margin`, `p_value`, `odds_ratio`, `ci_lower`, `ci_upper`, and `study_type` keys with correct types and formatting.
- [X] T017d [US3] Apply `classify_failure()` from T017a to the 7B results (`data/intermediate/hf_run_7b.jsonl`) to annotate failure modes for US3 results. **Dependency**: Must run after T027. **Verification**: Verify `data/intermediate/hf_run_7b.jsonl` is updated with failure mode annotations.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`. **Verification**: Verify `docs/quickstart.md` contains step 1-3 and `data-model.md` contains all entity definitions.
- [X] T036 [P] Code cleanup and refactoring of `context_processors.py`. **Verification**: Refactor `context_processors.py` to extract `load_model` into `models/runner.py` and reduce cyclomatic complexity of `context_processors.py` to <10.
- [X] T037 [P] Performance optimization: Fine-tune parallel batching parameters in `batch_executor.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to ensure robustness of the total wall-clock budget (FR-007).
- [X] T038 [P] Additional unit tests for edge cases (empty context, timeout) in `tests/unit/`. **Verification**: `pytest tests/unit/` passes with new tests for empty context and timeout.
- [X] T039 [P] [US1, US2, US3] [FR-005, Const-III] Run checksum generation and recording for ALL data artifacts: `data/results.csv`, `data/intermediate/baseline_run.jsonl`, `data/intermediate/hf_run_*.jsonl`, and the filtered dataset. Record hashes in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml` (Constitution Principle III). **Logic**: Generate a `derivation.json` file alongside the checksums to document the derivation path for every transformation. **Verification**: Verify `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml` contains keys `raw_parquet`, `filtered_parquet`, `results_csv` and valid hashes for all listed artifacts. **Verification**: Ensure a `derivation.json` file is generated alongside the checksums to document the derivation path for every transformation. **Dependency**: Must run after T028 (Results Aggregation).

---

## Revision Concerns (Mode B Resolutions)

**Purpose**: Address specific issues raised by `/speckit.analyze` regarding data integrity, execution feasibility, and specification alignment.

- [X] T054 [P] [US1, US2, US3] [FR-001, Const-III] Implement `RepresentativenessValidator` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/representativeness_validator.py`. **Logic**: Perform a Kolmogorov-Smirnov (KS) test comparing the distribution of `line_count` in `data/filtered_swe_bench_v1.parquet` against the raw dataset (streamed sample). **Output**: Log a warning if the KS statistic > 0.1, indicating the filtered set is not representative of the full population. **Verification**: Verify the script runs and logs the KS statistic and p-value, and logs a warning if KS > 0.1.
- [X] T055 [P] [US1, US2, US3] [FR-001, Const-III] Implement `ConstructValidityAudit` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/construct_validity_audit.py`. **Logic**: Calculate the correlation between the "Hybrid IR-Seeding" scores (used for filtering) and the "TF-IDF/BM25" scores (used for high-fidelity strategy). **Rule**: If correlation > 0.3, log a critical warning that the complexity metric is confounded with the strategy. **Verification**: Verify the script logs the correlation coefficient and the warning if threshold exceeded.
- [X] T056 [P] [US1, US2, US3] [FR-003] Refactor `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/strategies/summarization.py` to explicitly document the "first sentence of paragraph, last sentence of function" heuristic as a **construct validity limitation** and a **lower-bound proxy** for semantic summarization. **Verification**: Verify the code comments and docstrings explicitly state this limitation and the heuristic definition.
- [X] T057 [P] [US3] [FR-006] Implement `PowerAnalysisReporter` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to dynamically adjust the study conclusion based on the actual sample size `N`. **Logic**: If `N < 800`, explicitly set the `study_type` flag to "Exploratory" and ensure the primary metric reported is the Odds Ratio with 95% CI, not just p-values. **Verification**: Verify the output report includes the `study_type` flag and the correct primary metric emphasis.
- [X] T058 [P] [US1, US2, US3] [FR-007] Refactor `experiments/batch_executor.py` to implement a **dynamic back-off strategy** for the 72-hour wall-clock limit. **Logic**: If the estimated remaining time (based on current throughput) exceeds the budget, terminate the batch gracefully and log a "Timeout" status for remaining instances, rather than hanging or crashing. **Verification**: Verify the script logs "Timeout" and stops processing when the budget is exceeded.
- [X] T059 [P] [US1, US2, US3] [FR-001] Add a `StaticAnalysisSanityCheck` task in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py` to verify that the "Hybrid IR-Seeding" logic does not accidentally use the `test_patch` or any ground-truth data. **Verification**: Run the test and verify it fails if the loader attempts to read `test_patch` or `ground_truth` fields.
- [X] T060 [P] [US1, US2, US3] [FR-008] Implement `FailureModeAggregator` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/failure_classifier.py` to generate a summary report of failure modes (missing context vs. reasoning error) for each configuration. **Verification**: Verify the report correctly aggregates counts and percentages for each strategy/model combination.