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

- [ ] T001 [P] Create missing directory structure per implementation plan in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`: `data/`, `models/`, `experiments/`, `analysis/`, `tests/`, `utils/`. **Verification**: Run `find. -name __init__.py` and verify 5 files exist.
- [ ] T002 [P] Create missing `__init__.py` files for all new directories in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`.
- [ ] T003 [P] Initialize missing Python 3.11 project with `transformers`, `datasets`, `scikit-learn`, `statsmodels`, `networkx`, `pytest`, and `huggingface_hub` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt`.
- [ ] T004 [P] Create missing `.ruff.toml` and `pyproject.toml` with black settings in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` for linting and formatting.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004b [P] [US1, US2, US3] [Const-I] Configure random seeds to be hardcoded in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py` (Constitution Principle I).
- [X] T004c [P] [US1, US2, US3] [Const-I] Implement explicit random seed pinning in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py` and `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` (Constitution Principle I) to ensure reproducibility even if config is decoupled.
- [ ] T005 [P] Implement deterministic logging and error handling infrastructure in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/utils/logger.py`: implement `setup_logger()` and `log_error()` functions. **Verification**: `pytest tests/unit/test_logger.py::test_logger_initialization`.
- [X] T006a [P] [US1, US2, US3] Create base data model class `TaskInstance` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/task_instance.py`. **Verification**: `pytest tests/unit/test_models.py::test_task_instance_init`.
- [X] T006b [P] [US1, US2, US3] Create base data model class `ContextConfiguration` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/context_config.py`. **Verification**: `pytest tests/unit/test_models.py::test_context_config_init`.
- [X] T006c [P] [US1, US2, US3] Create base data model class `ExecutionResult` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/execution_result.py`. **Verification**: `pytest tests/unit/test_models.py::test_execution_result_init`.
- [ ] T006d [P] [US1, US2, US3] Create entity schemas (YAML files) for `TaskInstance`, `ContextConfiguration`, `ExecutionResult` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/specs/001-context-fidelity-scaling-tradeoff/contracts/`: `task_instance.schema.yaml`, `context_config.schema.yaml`, `execution_result.schema.yaml`. **Verification**: Validate against JSON schema.
- [X] T007 [P] Setup environment variable management for model paths and HF token in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py`.
- [X] T016b [P] [US1, US2, US3] Implement `BatchExecutor` class with `submit()` method in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py`. **Verification**: `pytest tests/unit/test_batch_executor.py::test_batch_submit`.
- [X] T016c [P] [US1, US2, US3] Implement `TimeoutGuard` decorator in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/batch_executor.py`. **Verification**: `pytest tests/unit/test_batch_executor.py::test_timeout_guard`.
- [ ] T026 [P] [US1, US2, US3] [FR-002, FR-004] Implement generic `ModelRunner` class in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/runner.py`. This class MUST support loading both 1B and 7B models with Q4_K_M quantization on CPU, handling memory pressure via aggressive quantization or termination flags. **Dependency**: This task MUST complete before T016 (US1), T023 (US2), and T027 (US3) to ensure execution tasks have a valid runner.
- [ ] T008a [P] [US1, US2, US3] Implement `validate_schema()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py` to validate JSONL inputs against schemas. **Verification**: `pytest tests/unit/test_merge_results.py::test_validate_schema`.
- [ ] T008b [P] [US1, US2, US3] Implement `aggregate_jsonl()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py` to merge JSONL files into a single CSV (Single Source of Truth). **Verification**: `pytest tests/unit/test_merge_results.py::test_aggregate_jsonl`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Context-Bound Task Filtering and Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Filter Claw-SWE-Bench for high-complexity instances (>500 lines) and execute a naive baseline with a CPU-runnable 1B model.

**Independent Test**: Run the filtering script on the raw dataset and verify the output contains only instances with >500 lines of relevant file history, then execute a single instance with the baseline model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: T010 is scaffolding.**

- [ ] T010 [P] [US1] Unit test scaffolding for import graph traversal logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py`. **Note**: This is scaffolding; implementation logic follows in T013.
- [ ] T011 [P] [US1] Integration test for baseline execution timeout in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/integration/test_baseline_execution.py`.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `ClawSweBenchLoader` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` using `datasets.load_dataset(..., streaming=True)` to fetch from Hugging Face. **Rule**: Fail loudly if fetch fails; do NOT generate synthetic data. This task MUST implement the streaming logic required for large datasets (integrated from Phase O T040).
- [ ] T012a [P] [US1] [FR-001] Refactor `ClawSweBenchLoader` to use `datasets.load_dataset(..., streaming=True)` explicitly for the initial fetch, ensuring the full real dataset is streamed in chunks rather than loaded into RAM, addressing the "Large real datasets" constraint (FR-001). **Verification**: Verify `streaming=True` is set and no `.load()` call is made on the full dataset object.
- [ ] T012b [P] [US1] Implement `filter_dataset()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` to filter for instances where the total lines in the traversed graph exceed a substantial threshold (FR-001).
- [ ] T012d [P] [US1] Implement `validate_filtered_count()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` to check if the filtered count is >= a configurable threshold (default 50); log the actual count and raise `InsufficientContextError` if below threshold (Edge Case 1). **Verification**: `pytest tests/unit/test_loader.py::test_validate_filtered_count`.
- [ ] T012c [P] [US1] Implement `write_parquet_and_checksum()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` to write the *filtered* dataset (instances >500 lines) to a versioned file (e.g., `data/filtered_swe_bench_v1.parquet`) and record its checksum in `state/` (Constitution Principle III).
- [ ] T013 [P] [US1] Implement static analysis logic `calculate_relevant_lines(issue: dict) -> int` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` to calculate "relevant file history" lines: 1) Parse Python imports to build a dependency graph using `networkx`, 2) Perform BFS/DFS traversal from the issue target files, 3) Filter for instances where the total lines in the traversed graph exceed a substantial threshold. (FR-001). **Verification**: `pytest tests/unit/test_loader.py::test_graph_traversal_logic_correct`.
- [ ] T014 [P] [US1] Implement "first-N-lines" naive truncation strategy in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` (FR-002).
- [ ] T015 [P] [US1] Configure `ModelRunner` (from T026) for the 1B-parameter model (e.g., Llama-3-1B) with Q4_K_M quantization on CPU (FR-002). **Note**: This task configures the generic runner implemented in T026; it does not re-implement the runner class.
- [ ] T016 [US1] Implement `run_baseline.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the filtered dataset with the 1B model and naive strategy. **Constraint**: Enforce a fixed runtime budget per instance via `batch_executor.py`. Output `data/intermediate/baseline_run.jsonl` (US-1). **Dependency**: Requires T026 (ModelRunner) and T012 (Loader).
- [ ] T017a [P] [US1, US2, US3] Implement `classify_failure(log: str) -> str` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/failure_classifier.py` with explicit rule-based logic: flag "missing context" if log contains "file not found", "cannot locate", or references a file not in input context; flag "reasoning error" if file exists but logic fails (FR-008). **Verification**: `pytest tests/unit/test_failure_classifier.py::test_detects_file_not_found`.
- [ ] T017b [US1] Apply `classify_failure()` from T017a to the baseline results (`data/intermediate/baseline_run.jsonl`) to annotate failure modes for US1 results. **Dependency**: Must run after T016.
- [ ] T017c [US2] Apply `classify_failure()` from T017a to the high-fidelity results (`data/intermediate/hf_run_1b.jsonl`) to annotate failure modes for US2 results. **Dependency**: Must run after T023.
- [ ] T017d [US3] Apply `classify_failure()` from T017a to the 7B results (`data/intermediate/hf_run_7b.jsonl`) to annotate failure modes for US3 results. **Dependency**: Must run after T027.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Fidelity Context Strategy Integration (Priority: P2)

**Goal**: Implement and integrate three context compression modules (TF-IDF, Diff-Aware, Semantic Summarization) and execute them with the 1B model.

**Independent Test**: Run a single high-fidelity strategy (e.g., TF-IDF) on a subset and verify the context differs from baseline and produces a different output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for TF-IDF/BM25 retrieval logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`
- [ ] T019 [P] [US2] Unit test for diff-aware sliding window logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement TF-IDF/BM25 relevance retrieval module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` using `scikit-learn` (FR-003).
- [ ] T021 [P] [US2] Implement diff-aware sliding window module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` using standard diff libraries (FR-003).
- [ ] T022 [P] [US2] Implement rule-based semantic summarization module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` as defined in FR-003 (rule-based extraction of relevant code blocks/paragraphs).
- [ ] T023 [US2] Implement `run_strategy()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` to execute the model against all three high-fidelity strategies. **Constraint**: Enforce a fixed runtime budget per instance and use parallel batching. Output `data/intermediate/hf_run_1b.jsonl` (US-2). **Dependency**: Requires T026 (ModelRunner) and T020-T022 (Context Processors).
- [ ] T023b [US2] Implement `main()` entry point in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` to orchestrate `run_strategy()` and output files.
- [ ] T024 [P] [US2] Implement `fallback_strategy()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` that returns `first_n_lines` if `retrieved_snippets` is empty, logging the event to `data/audit_logs/fallbacks.jsonl` (Edge Case Handling). **Verification**: `pytest tests/unit/test_context_processors.py::test_fallback_on_empty_result`.
- [ ] T024a [P] [US2] [FR-008] Refactor `context_processors.py` to remove any `try/except` blocks that might silently fall back to synthetic/mock data if a retrieval module (TF-IDF/Diff) fails, ensuring the "Fail Loudly" rule is enforced and the run terminates with a clear error. **Verification**: Verify no `generate_synthetic_*` or `mock_*` calls exist in the fallback logic.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Scaling Comparison and Interaction Analysis (Priority: P3)

**Goal**: Repeat experiments with a 7B model and perform GLM analysis to test for interaction effects.

**Independent Test**: Run the 7B model on baseline and high-fidelity configurations, compare Pass@1 curves, and verify the GLM analysis runs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Write test scaffolding for GLM interaction effect calculation in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_glm_analyzer.py`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `run_7b_experiments.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the large language model against all strategies (Baseline, TF-IDF, Diff-Aware, Summarization). **Constraint**: Enforce a bounded runtime budget per instance and use parallel batching. Output `data/intermediate/hf_run_7b.jsonl` (US-3). *Dependency: Must complete T026 first.*
- [ ] T028 [US3] Execute `merge_results.py` (T008a/T008b logic) to aggregate all JSONL files (`baseline_run.jsonl`, `hf_run_1b.jsonl`, `hf_run_7b.jsonl`) into a single `data/results.csv` (Single Source of Truth) (FR-005). *Note: Logic was implemented in Phase 2; this task executes the merge.*
- [ ] T029 [US3] Implement `run_glm(data: pd.DataFrame) -> statsmodels.GLMResults` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to perform a Generalized Linear Model (GLM) with binomial link to test for interaction effects between "context strategy" and "model size" (FR-006, US-3). This task MUST implement Firth's penalized likelihood correction as the primary method to handle sparse binary data (integrated from Phase O T042). **Verification**: `pytest tests/unit/test_glm_analyzer.py::test_interaction_p_value_exists`.
- [ ] T029a [P] [US3] [FR-006] Update `glm_analyzer.py` to implement standard GLM as a fallback if Firth's method fails, or vice-versa, ensuring robust convergence (Complexity Tracking). **Verification**: Verify the `firth=True` or equivalent penalization argument is passed to the GLM constructor if convergence fails.
- [ ] T030a [US3] Implement `calculate_pairwise_diff()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the difference in Pass@1 rates between the 1B-model (high-fidelity) and 7B-model (baseline) for each strategy.
- [ ] T030b [US3] Implement `check_significance()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the margin and p-value; log values; do not enforce binary pass/fail in code (SC-004).
- [ ] T030c [US3] Generate the final comparison report in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/data/results/comparison_report.md` (or.json) by aggregating results from T030a and T030b, explicitly identifying the strategy where 1B outperforms 7B (SC-004).
- [ ] T030d [P] [US3] [FR-006] Add a `power_analysis()` function in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py` to calculate the statistical power of the experiment given the expected effect size and sample count, logging a warning if power < 0.8 to address the "Insufficient Context-Bound Data" assumption. **Verification**: Verify the function runs and logs a warning if the calculated power is below the threshold.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`. **Verification**: Verify `docs/quickstart.md` contains step 1-3 and `data-model.md` contains all entity definitions.
- [ ] T036 [P] Code cleanup and refactoring of `context_processors.py`. **Verification**: Extract `load_model` function; verify cyclomatic complexity < 10.
- [ ] T037 [P] Performance optimization: Fine-tune parallel batching parameters in `batch_executor.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to ensure robustness of the total wall-clock budget (FR-007).
- [ ] T038 [P] Additional unit tests for edge cases (empty context, timeout) in `tests/unit/`. **Verification**: `pytest tests/unit/` passes with new tests for empty context and timeout.
- [ ] T039 [P] Run checksum generation and recording for ALL data artifacts: `data/results.csv`, `data/intermediate/baseline_run.jsonl`, `data/intermediate/hf_run_*.jsonl`, and the filtered dataset. Record hashes in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml` (Constitution Principle III).

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on `ModelRunner` updates (T026) and `merge_results.py` (T008a/T008b) but independently testable

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
Task: "Implement ClawSweBenchLoader in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
Task: "Implement issue description parsing logic in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
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