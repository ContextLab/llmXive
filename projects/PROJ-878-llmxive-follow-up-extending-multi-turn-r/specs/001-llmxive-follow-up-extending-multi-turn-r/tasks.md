# Tasks: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

**Input**: Design documents from `/specs/001-llmxive-topological-limits/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run after previous task)
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

- [X] T001 Create project directories matching `plan.md` structure: `data/raw/`, `data/processed/`, `code/`, `code/utils/`, `tests/`, `results/paper_figures/`. **Verification**: Run `ls` to confirm existence of all directories.
- [X] T002 Create `__init__.py` files in `code/`, `code/utils/`, and `tests/` directories. **Verification**: Run `find . -name __init__.py` to confirm.
- [X] T003 Create `code/requirements.txt` with Python dependencies (torch, transformers, datasets, networkx, lifelines, scikit-learn, pandas, numpy, pytest) with **explicit version pinning** (e.g., `torch==2.1.0`) for reproducibility. **Verification**: Run `pip install -r code/requirements.txt` and verify success.
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` with black-compatible rules (line-length=88) and ruff linting rules. **Verification**: Run `ruff check --output-format=concise` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `code/utils/logging_utils.py` for standardized experiment logging and checksum generation. **Deliverable**: Implement functions `log_experiment(config: dict) -> str` (returns log file path) and `generate_checksum(file_path: str) -> str` (returns SHA-256 hex). **Verification**: Run `python -c "from code.utils.logging_utils import log_experiment, generate_checksum; print('OK')"`.
- [ ] T006 [P] [US1] Implement `code/utils/graph_utils.py` containing DAG validation (acyclic check), `nesting_depth` (longest path), `branching_factor` (mean in-degree), and **longest_path** calculators. **Deliverable**: Implement `is_acyclic(graph: nx.DiGraph) -> bool`, `calculate_nesting_depth(graph: nx.DiGraph) -> int`, `calculate_branching_factor(graph: nx.DiGraph) -> float`, `get_longest_path(graph: nx.DiGraph) -> list`. **Verification**: Run `pytest tests/test_graph_utils.py::test_graph_metrics` to verify functions exist and return correct types.
- [ ] T007 [P] [US1] **Consolidated Test**: Unit test for `code/utils/graph_utils.py` covering DAG validation (acyclic check) AND metric calculation (nesting_depth, branching_factor, longest_path) in `tests/test_graph_utils.py`. **Verification**: Ensure all metric functions are tested against known graph structures.
- [ ] T008 [P] Create `code/.env` file with `SEED=42`, `MODEL_PATH=<verified_repo_id>`. **Verification**: Run `cat code/.env` to confirm variables.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation with Controlled Topology (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of logical puzzles where `nesting_depth` and `branching_factor` are explicitly controlled, verified as acyclic, and recorded in metadata.

**Independent Test**: The generation script can be executed in isolation to produce a JSONL file. A validation script can parse this file and verify that the distribution of `nesting_depth` and `branching_factor` matches the requested ranges, and that the ground-truth solution is derivable from the graph structure.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `code/graph_generator.py` output schema in `tests/test_graph_generator.py` (validate against `LogicalPuzzle` entity in `data-model.md`)
- [X] T010 [P] [US1] Integration test for stratified orthogonalization (depth vs branching correlation < 0.2) in `tests/test_graph_generator.py` (Input: N=500, depth 3-6, branching 1-5; Assertion: |r| < 0.2)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/graph_generator.py` using `networkx` to generate Directed Acyclic Graphs (DAGs) with target `nesting_depth` and `branching_factor`. **Algorithm**: Use rejection sampling. Generate candidate graph. If `is_acyclic` is false or `abs(corr(depth, branch)) >= 0.2`, reject. **Output Schema**: JSONL with `instance_id`, `text`, `ground_truth_path`, `nesting_depth`, `branching_factor`, `graph_structure`. **Verification**: Run `python code/graph_generator.py --test-mode` to verify output schema.
- [ ] T013 [US1] Implement **Stratified Orthogonalization** logic: Rejection sampling loop (generate N candidates, calculate r, if |r|>=0.2 reject, else accept) to ensure |r| < 0.2 between depth and branching factors; **Verify and log final correlation coefficient** to stdout and write to `data/validation_metrics.json`. **JSON Schema**: `{"correlation_coefficient": float, "samples_generated": int, "samples_rejected": int}`. **Verification**: Run `python -c "import json; d=json.load(open('data/validation_metrics.json')); assert abs(d['correlation_coefficient']) < 0.2"`.
- [ ] T014 [US1] Implement **Deterministic Template Engine** in `code/graph_generator.py` to map DAG structure to logical text prompts (no LLM involved). **Verification**: Ensure text output is deterministic for same graph input.
- [ ] T015 [US1] Implement **Randomized Path Perturbation** (FR-007) to select a valid ground-truth path different from the longest path; **Calculate the cycle rate** (count of cyclic graphs / total generated) internally. **Output**: Write the string `"[deferred]"` to `data/validation_metrics.json` under key `cycle_rate` to satisfy SC-005. **Verification**: Run `python -c "import json; d=json.load(open('data/validation_metrics.json')); assert d['cycle_rate'] == '[deferred]'"`.
- [ ] T016 [US1] Write generated instances to `data/raw/logical_puzzles.jsonl` with metadata (`instance_id`, `text`, `ground_truth_path`, `nesting_depth`, `branching_factor`, `graph_structure`). **Verification**: Run `wc -l data/raw/logical_puzzles.jsonl` to confirm N=500.
- [ ] T017 [US1] Implement checksum generation for `data/raw/logical_puzzles.jsonl` using SHA-256 and record in `data/checksums.txt` in format `<hash> <filename>`. **Verification**: Run `sha256sum -c data/checksums.txt`.

**Checkpoint**: User Story 1 complete. T016 and T017 MUST be completed before any US2 tasks (T024+) can start.

---

## Phase 4: User Story 2 - CPU-Feasible Baseline Execution (Priority: P2)

**Goal**: Execute the Reflective Masking (RM) loop on the generated dataset using a pre-trained Mask Diffusion Model on CPU, recording turns to convergence or failure.

**Independent Test**: The execution script can be run on a standard CPU environment. It must complete within the CI limit for the full dataset. The output must be a log file containing `instance_id`, `turns_to_converge` (or `failure`), and `final_accuracy`.

**⚠️ DEPENDENCY**: This phase requires `data/raw/logical_puzzles.jsonl` from T016 to be present.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for `code/rm_executor.py` input/output schema in `tests/test_rm_executor.py`. **Input Schema**: `puzzle_text: str`, `model: torch.nn.Module`. **Output Schema**: `dict` with keys `instance_id`, `turns_to_converge` (int or None), `convergence_status` (str), `path_coverage` (float). **Verification**: Run `pytest tests/test_rm_executor.py::test_schema_validation`.
- [ ] T019 [P] [US2] Integration test for Independent Logical Validator (ILV) verifying path coverage in `tests/test_rm_executor.py`
- [ ] T020 [P] [US2] Unit test for hard turn limit enforcement (50 turns) and censored data flagging in `tests/test_rm_executor.py`. **Verification**: Run `pytest tests/test_rm_executor.py::test_turn_limit_enforcement` which asserts `convergence_status` is 'failure' at turn 51.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/rm_executor.py` to load pre-trained Mask Diffusion Model. **Parameters**: Load with `device="cpu"`, `torch_dtype=torch.float32`. **Model Path**: Read from `code/.env` `MODEL_PATH`. **Verification**: Run `python -c "from code.rm_executor import load_model; load_model()"` to verify load.
- [ ] T022 [US2] Implement **Reflective Masking Loop**: Token-level masking, prediction, unmasking, and convergence check. **Function Signature**: `run_rm_loop(puzzle_text: str, model: torch.nn.Module, max_turns: int) -> dict`. **Verification**: Unit test for convergence check logic.
- [ ] T023 [US2] Implement **Independent Logical Validator (ILV)** in `code/utils/graph_utils.py`: Function `calculate_path_coverage(model_output: str, original_dag: nx.DiGraph) -> float`. **Logic**: Parse model output, compare edges with DAG. **Output**: Float between 0.0 and 1.0. **Verification**: Run `pytest tests/test_rm_executor.py::test_ilv_logic`.
- [ ] T024 [S] [US2] **Implement hard turn limit for primary run**: Enforce a maximum of 50 turns. If the limit is exceeded, set `convergence_status` to **'failure'** (not 'timeout') to distinguish budget exhaustion from reasoning failure. **Variable**: `MAX_TURNS = 50`. **Verification**: Verify that instances with >50 turns are marked with status 'failure'.
- [ ] T025 [S] [US2] Implement batch processing logic (batch size=4) to ensure memory constraints and streaming if necessary. **Function**: `process_batch(puzzles: list) -> list`. **Verification**: Verify memory usage remains within acceptable limits and log total execution time (must be < 6 hours).
- [ ] T026 [S] [US2] **Write execution results to `data/processed/execution_log.csv`**. **Depends on**: T021-T025. **Columns**: `instance_id`, `turns_to_converge`, `convergence_status` (values: 'success' or 'failure'), `path_coverage`. **Logic**: Read `ground_truth_path` from `data/raw/logical_puzzles.jsonl`. Calculate `path_coverage` using ILV. Write to CSV. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/execution_log.csv'); assert list(df.columns) == ['instance_id', 'turns_to_converge', 'convergence_status', 'path_coverage']"`.
- [ ] T027 [S] [US2] **Verify divergence metric**. **Depends on**: T026. **Script**: `code/verify_divergence.py`. **Logic**: Read `data/processed/execution_log.csv`. **Assertion**: All `path_coverage` values must be >= 0.0 and <= 1.0. No nulls allowed. **Exit Code**: 0 on success, 1 on failure. **Verification**: Run `python code/verify_divergence.py`.
- [ ] T028 [S] [US2] **Implement Extended Budget Validation Run** (FR-008). **Depends on**: T026. **Filter**: Select rows where `convergence_status='failure'`. **Action**: Re-run these instances with an extended turn limit. **Output**: Write results to `data/processed/extended_budget_log.csv`. **Verification**: Ensure `extended_budget_log.csv` row count matches filtered input count.
- [ ] T029 [S] [US2] **Generate checksums for `data/processed/execution_log.csv` and `data/processed/extended_budget_log.csv` using SHA-256**. **Format**: `<hash>  <filename>` (two spaces). **Script**: `code/generate_checksums.py`. **Verification**: Run `sha256sum -c data/checksums.txt` and ensure exit code 0.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation & Threshold Analysis (Priority: P3)

**Goal**: Perform Survival Analysis (Cox PH) and Segmented Regression to correlate topological metrics with convergence, and execute sensitivity analysis on thresholds.

**Independent Test**: The analysis script can be run on the results log. It must produce a report containing correlation coefficients, p-values, and a plot/table showing how convergence rates change when the success threshold is varied.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T030 [P] [US3] Define the expected interface for `code/analyzer.py` and write the contract test in `tests/test_analyzer.py` (validate output report schema). **Expected Output Schema**: `dict` with keys `spearman_coeff`, `spearman_p_value`, `tipping_point_depth`, `sensitivity_table` (dict of cutoff->failure_rate). **Verification**: Run `pytest tests/test_analyzer.py::test_analyzer_schema`.
- [ ] T031 [P] [US3] Unit test for Cox Proportional Hazards model handling of censored data in `tests/test_analyzer.py`
- [ ] T032 [P] [US3] **Unit test for Segmented Regression tipping point detection** in `tests/test_analyzer.py`. **Input**: Synthetic data with known tipping point at depth X. **Assertion**: Model detects tipping point within tolerance.

### Implementation for User Story 3

- [ ] T033 [US3] **FR-004 Compliance**: Implement **Survival Analysis (Cox PH)** in `code/analyzer.py` (Primary) using `lifelines.CoxPHFitter` AND **Spearman rank correlation analysis** (Descriptive only) between `nesting_depth` and `turns_to_converge`; **Output Spearman coefficient and p-value explicitly** to satisfy FR-004 and SC-001 as descriptive statistics only.
- [ ] T034 [US3] Implement **Segmented Regression** (piecewise linear) to identify the specific `nesting_depth` "tipping point" where degradation rate changes; **Explicitly calculate and report failure rates at adjacent depths (depth-1, depth, depth+1) to satisfy SC-002**
- [ ] T035 [US3] Implement **Sensitivity Analysis**: Re-evaluate failure rates at **three specific cutoffs (40, 50, and 60 turns)** to verify the stability of the identified "tipping point" (FR-005). **Output**: Table showing failure rates for each cutoff.
- [ ] T036 [S] [US3] **Implement Extended Budget Analysis**. **Depends on**: T028. **Input**: Read `data/processed/extended_budget_log.csv` and `data/processed/execution_log.csv`. **Logic**: Calculate rate of budget exhaustion: `(count of instances in extended_log with convergence_status='success' AND turns_to_converge <= 1000) / (count of instances in primary_log with convergence_status='failure') * 100`. **Output**: Generate `results/extended_budget_analysis.md` containing this percentage. **Verification**: Ensure `data/processed/extended_budget_log.csv` exists and contains rows before analysis.
- [ ] T037 [US3] Apply Bonferroni correction for multiple comparisons (number of comparisons = 2). **Output**: Corrected p-values.
- [ ] T038 [US3] Generate `results/paper_figures/` plots (hazard function, tipping point) and `results/statistical_report.md` with all metrics, p-values, and tipping point values. **Verification**: Check file existence and content.
- [ ] T039 [US3] **Update README.md** with usage examples and setup instructions. **Verification**: Check for required sections.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] **Update `docs/api.md`** with function signatures for `code/` modules. **Verification**: Check for all public functions.
- [ ] T041 [P] Code cleanup and refactoring of `code/utils/` modules. **Criteria**: Remove dead code (unused imports/functions), ensure consistent naming (snake_case). **Verification**: Run `ruff check code/`.
- [ ] T044 [P] Additional unit tests coverage validation in `tests/`. **Threshold**: >80% coverage. **Tool**: `pytest-cov`. **Verification**: Run `pytest --cov=code --cov-report=term-missing` and verify coverage > 80%.
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility. **Verification**: Run `quickstart.md` steps and verify success.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires `data/raw/logical_puzzles.jsonl` from US1 (T016)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires `data/processed/execution_log.csv` from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utilities (graph_utils) before Generators/Executors
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for graph_generator.py output schema in tests/test_graph_generator.py"
Task: "Integration test for stratified orthogonalization in tests/test_graph_generator.py"

# Launch all models for User Story 1 together:
Task: "Implement graph_generator.py using networkx"
Task: "Implement Deterministic Template Engine in code/graph_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify topology control)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Execution loop)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical insights)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Gen)
 - Developer B: User Story 2 (Execution)
 - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, must wait for previous task
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All data generation must be real (synthetic but controlled) and execution must be CPU-only. No synthetic fallbacks for data loading.