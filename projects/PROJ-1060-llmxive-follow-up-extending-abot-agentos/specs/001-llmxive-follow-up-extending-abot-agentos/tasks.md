# Tasks: llmXive follow-up: extending "ABot-AgentOS" with Symbolic Memory

**Input**: Design documents from `/specs/001-symbolic-memory-edge-robotics/`
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

- [X] T001 Create project structure per implementation plan: Create the following directories: `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/001-symbolic-memory-edge-robotics/contracts/`. Create empty `__init__.py` files in `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/001-symbolic-memory-edge-robotics/contracts/`.
- [X] T002 Create `code/requirements.txt` containing pinned versions for: `networkx==3.2.1`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `statsmodels==0.14.1`, `datasets==2.16.1`, `transformers==4.37.2`, `pytest==7.4.3`, `ruff==0.1.11`, `black==23.12.1`, `tracemalloc` (stdlib).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`: Create `code/.ruff.toml` with `line-length = 88` and `select = ["E", "F", "I"]`. Create `code/pyproject.toml` with `[tool.black] line-length = 88`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with canonical seeds and hyperparameters: `RANDOM_SEED = 42`, `GRANULARITY = "coarse"`, `PREDICATE_SET = "spatial"`, `MODEL_ID = "google/vit-base-patch16-224"`, `MAX_TRACES = 500`.
- [X] T005 [P] Implement `code/data_loader.py` to stream ALFWorld traces via `datasets.load_dataset("alfworld/alfworld", streaming=True)` with checksum verification.
- [X] T006 [P] Implement fallback mechanism in `code/data_loader.py` to load versioned artifacts from `data/raw/` if remote download fails (FAIL LOUDLY if neither works).
- [X] T007 Create `code/metrics.py` defining class `MetricsLogger` with methods: `log_success(bool)`, `log_latency(float)`, `log_memory(float)`, `save_report(str)`; output format JSON/CSV.
- [X] T008 [P] Setup `pytest` configuration and contract test scaffolding in `tests/`: Create `tests/conftest.py` with `pythonpath = ["code"]` and `addopts = "-v"`.
- [X] T009 [P] Define ALFWorld ground-truth schema mapping in `data/schemas/ground_truth_mapping.json` with keys: `nodes` (list of token strings), `edges` (list of `{source: string, target: string, predicate: string}`), `predicates` (allowed list).
- [X] T009b [P] Depends on T009: Implement `code/validator.py` to calculate reconstruction error: compare constructed graph nodes/edges against `ground_truth_mapping.json`, compute error rate, and log result to `data/results/reconstruction_error.json`.
- [X] T027a Acquire, install, or containerize the ABot-AgentOS baseline version. If acquisition fails (private repo/complex deps), DO NOT implement a mock baseline. The task must fail and the project must transition to `human_input_needed` to preserve the validity of SC-001/SC-002 against a real neural system.
- [X] T027 Depends on T027a: Implement `code/baseline_runner.py` to execute the neural baseline (ABot-AgentOS v1.0) via `subprocess.run` or import, accepting task traces and returning success/latency metrics.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Symbolic Graph Construction from Task Traces (Priority: P1) 🎯 MVP

**Goal**: Ingest raw task traces from ALFWorld and convert them into a deterministic DAG of semantic tokens and logical predicates without GPU inference.

**Independent Test**: The system can be tested by running the construction pipeline on a subset of task traces and verifying the output graph structure (nodes, edges, predicates) against ground-truth annotations from ALFWorld via a manual audit of a random sample of traces. Success is defined by a graph reconstruction error rate < 1% against ground truth.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for graph schema in `tests/contract/test_graph_schema.py`
- [X] T011 [P] [US1] Unit test for token mapping accuracy in `tests/unit/test_token_mapping.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Depends on T002, T009: Implement `code/tokenizer.py` function `discretize_trace(trace: dict) -> list[str]` using frozen VLM `code/config.py` MODEL_ID (`google/vit-base-patch-224`) to map raw visual observations to fixed taxonomy.
- [X] T013 [P] [US1] Depends on T012, T009: Implement `code/graph_builder.py` logic to construct a Directed Acyclic Graph (DAG) where nodes are semantic tokens and edges are predicates (`on_top_of`, `near`, `before`).
- [X] T014 [P] [US1] Depends on T012: Implement `code/graph_builder.py` logic to actively detect and flag logical inconsistencies (contradictory spatial info) for review, and EXCLUDE flagged edges from the final DAG.
- [X] T015 [US1] Depends on T012: Implement logic in `code/graph_builder.py` to handle missing VLM matches by assigning "unknown_object" token and logging the event.
- [X] T016 [US1] Depends on T013: Implement and EXECUTE parametric sweeps in `code/experiment_runner.py`: Run all combinations of `granularity=["coarse", "fine"]` and `expressiveness=["spatial", "spatial+temporal"]`; aggregate results into `data/results/sweep_metrics.csv` with columns: `granularity`, `expressiveness`, `success_rate`, `latency_ms`, `memory_mb` (FR-008, FR-009).
- [X] T017 [US1] Add validation in `code/graph_builder.py` to ensure memory footprint of constructed graph ≤ 2 GB for 500 traces.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Deterministic Symbolic Query Execution (Priority: P2)

**Goal**: Execute memory queries using a depth-first traversal algorithm on the symbolic graph to retrieve relevant context for navigation decisions, ensuring zero GPU dependency.

**Independent Test**: The system can be tested by issuing a series of standard navigation queries against the constructed graph and verifying the returned path/context matches the ground truth in the source logs within a defined latency budget.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for query output schema in `tests/contract/test_query_output.py`
- [X] T019 [P] [US2] Integration test for multi-hop predicate chaining in `tests/integration/test_query_chaining.py`

### Implementation for User Story 2

- [X] T020 [US2] Depends on T013, T014, T015: Implement `code/query_engine.py` function `query_graph(graph: networkx.DiGraph, query: str) -> list[Node]` using a deterministic depth-first traversal algorithm operating entirely on CPU. Define `Node` as a dataclass with fields `id`, `token`, `predicates`.
- [X] T021 [US2] Depends on T020: Extend `code/query_engine.py` to handle complex queries requiring chaining multiple predicates (e.g., "Find X near Y which is before Z").
- [X] T022 [US2] Depends on T020: Extend `code/query_engine.py` to return "not found" (null) status when no path exists, without hallucinating a path.
- [X] T023 [US2] Depends on T020: Implement `code/latency_guard.py` decorator `@latency_guard(100)` to measure query latency; if limit exceeded, log violation to `data/results/latency_violations.json` (schema: `[{\"query_id\": str, \"latency_ms\": float, \"timestamp\": str}]`) and continue (do NOT fail the run).
- [X] T024 [US2] Depends on T020: Add validation in `tests/integration/test_gpu_free.py` to confirm zero GPU resource utilization during execution by checking `torch.cuda.is_available()` and running `nvidia-smi` via subprocess; assert both return no active processes or false.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Performance & Success Rate Analysis (Priority: P3)

**Goal**: Run a comparative experiment executing the same set of logic-heavy navigation tasks using both the new symbolic memory system and the baseline neural memory system (ABot-AgentOS v1.0), recording success rates, latency, and memory usage.

**Independent Test**: The system can be tested by running the simulation on a fixed subset of tasks, collecting the metrics, and generating a report that compares the symbolic baseline against the neural baseline. Success is defined by the system outputting the correct statistical metrics (p-value, t-statistic/McNemar statistic) and error categorization.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for statistical report schema in `tests/contract/test_stats_report.py`
- [X] T026 [P] [US3] Integration test for full comparative pipeline in `tests/integration/test_comparative_pipeline.py`

### Implementation for User Story 3

- [X] T028 [US3] Depends on T016, T027: Implement `code/experiment_runner.py` to orchestrate the comparative study across a representative set of tasks, recording success rate, peak RAM, and query latency for both systems.
- [X] T029 [US3] Depends on T028: Implement `code/metrics.py` function `run_mcnemar_test(success_symbolic: list[bool], success_neural: list[bool]) -> (float, float)` to compute p-value and statistic from a contingency table.
- [X] T030 [US3] Depends on T028: Implement `code/error_analysis.py` to categorize symbolic system failures into "discretization ambiguity" or "logical inference limitations".
- [X] T030a [P] [US3] Depends on T028: Implement `code/error_analysis.py` to capture and log the total count of failures before categorization begins.
- [X] T030b [US3] Depends on T030, T030a: Implement `code/error_analysis.py` to calculate error analysis coverage percentage (`categorized_failures / total_failures * 100`) and report to `data/results/error_coverage.json` (schema: `{\"total_failures\": int, \"categorized_failures\": int, \"coverage_pct\": float}`).
- [X] T031 [US3] Depends on T016: Implement `code/metrics.py` logic to aggregate sweep results and measure impact of granularity/predicate expressiveness on performance.
- [X] T032a [US3] Depends on T028, T029: Implement `code/metrics.py` to calculate specific deltas: `success_rate_delta = symbolic_rate - neural_rate` and `memory_reduction_pct = (1 - symbolic_mem / neural_mem) * 100`; write to `data/results/deltas.json` (schema: `{\"success_rate_delta\": float, \"memory_reduction_pct\": float}`).
- [X] T032 [US3] Depends on T028, T029, T032a: Generate final report in `data/results/final_report.md` (Markdown format) containing p-values, test statistics, error counts, and the calculated deltas (success rate difference, memory reduction), evaluating if targets (≤5%, ≥80%) are met. Sections: `p-value`, `test_statistic`, `error_counts`, `deltas`, `target_met`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `specs/001-symbolic-memory-edge-robotics/`: Update `README.md`, `specs/001-symbolic-memory-edge-robotics/quickstart.md`, and `code/CONTRIBUTING.md` with execution instructions and schema references.
- [X] T034 Code cleanup and refactoring: Remove unused imports, enforce line length < 88, simplify nested conditionals in `code/`.
- [X] T035 Performance optimization across all stories: Optimize `query_engine.py` for latency (target ≤100ms) and `graph_builder.py` for peak RAM (target ≤2GB).
- [X] T036 [P] Additional unit tests in `tests/unit/`: Add `tests/unit/test_edge_cases.py::test_contradictory_spatial` and `tests/unit/test_token_mapping.py::test_unknown_object`.
- [X] T037 Run `quickstart.md` validation: Execute `python code/main.py --validate` and verify exit code 0.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable. **Note**: Query engine (US2) logically requires the graph artifact from US1.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable. **Note**: Comparative analysis (US3) logically requires outputs from US1 and US2.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
 - US1 (Graph Construction) can start immediately.
 - US2 (Query Engine) can start only AFTER US1 produces the symbolic graph artifact (or can be developed in parallel if mocking the graph structure, but integration requires US1 completion).
 - US3 (Comparative Analysis) can start only AFTER US1 and US2 are functional.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for graph schema in tests/contract/test_graph_schema.py"
Task: "Unit test for token mapping accuracy in tests/unit/test_token_mapping.py"

# Launch all models for User Story 1 together (distinct files):
Task: "Implement code/tokenizer.py offline discretization module"
Task: "Implement code/graph_builder.py logic to construct a Directed Acyclic Graph (DAG)"
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
 - Developer A: User Story 1 (Graph Construction)
 - Developer B: User Story 2 (Query Engine) - *Can develop logic, but integration waits for US1*
 - Developer C: User Story 3 (Comparative Analysis) - *Can develop logic, but integration waits for US1/US2*
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