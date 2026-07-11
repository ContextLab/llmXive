# Tasks: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Input**: Design documents from `/specs/001-lrmxive-follow-up-extending-mint-managed/`
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

- [ ] T001 Create project structure per implementation plan by running `mkdir -p code/data code/simulation code/analysis tests code/utils data/raw data/processed data/logs docs` <!-- FAILED: unspecified -->
- [ ] T002 Initialize Python 3.11 project with dependencies: `simpy`, `numpy`, `scipy`, `networkx`, `pandas`, `pytest`, `hypothesis` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/main.py` entry point and CLI argument parser
- [X] T005 [P] Implement logging infrastructure and configuration management in `code/utils/config.py` (Define `MEMORY_LIMIT_BYTES` constant here)
- [X] T006 [P] Define base exception classes (e.g., `MemoryLimitExceeded`) in `code/utils/exceptions.py`
- [~] T007 Create data schema definitions and validation utilities in `code/data/schema.py`
- [~] T008 Setup deterministic random seed management for reproducibility in `code/utils/seeds.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Workload Generation & Topology Construction (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of LoRA adapters with injected correlations, compute pairwise parameter overlap, and construct the LoRA Topology Graph.

**Independent Test**: Run `generate_adapters.py` and `compute_overlap.py` to verify the existence of `data/raw/adapters.parquet` (or CSV), `data/processed/overlap_matrix.csv`, and `data/processed/topology_graph.json` with correct dimensionality and value ranges.

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data/generate_adapters.py` to create synthetic LoRA adapters (ranks 1-256, clustered base weights) and save to `data/raw/adapters.parquet`
- [~] T014 [US1] Implement `code/data/generate_trace.py` to create request traces using a Clustered Markov Chain model and save to `data/processed/trace.csv`
- [~] T015 [US1] Implement `code/data/compute_overlap.py` to calculate pairwise cosine similarity, normalize to a bounded interval, and save the adjacency matrix to `data/processed/overlap_matrix.csv`
- [~] T016 [US1] Implement graph construction logic in `code/data/compute_overlap.py` to build an undirected `networkx` graph from the overlap matrix and save to `data/processed/topology_graph.json`
- [ ] T017 [US1] Add validation logic to ensure injected correlations result in non-trivial graph variance; if the graph is too sparse to support the Topological Lookahead policy, implement a graceful degradation strategy (e.g., fallback to frequency-based) rather than raising a hard error; script exits with code 0 only if a valid strategy is confirmed.
- [ ] T018 [US1] Add logging for data generation steps and checksums to `data/state.log`

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to ensure imports work**

- [ ] T019 [P] [US1] Unit test `tests/unit/test_data_gen.py::test_generate_adapters_creates_clustered_weights` (rank distribution, sparsity)
- [ ] T020 [P] [US1] Unit test `tests/unit/test_graph.py::test_overlap_matrix_normalization` (cosine similarity normalization)
- [ ] T021 [P] [US1] Contract test `tests/contract/test_schema_validation.py::test_output_schema_artifacts` verifying output schema of generated artifacts

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Data & Graph ready)

---

## Phase 4: User Story 2 - Discrete-Event Simulation of MinT Infrastructure (Priority: P1)

**Goal**: Implement the SimPy-based discrete-event simulation engine modeling memory constraints, adapter loading with jitter, and cache eviction.

**Independent Test**: Run simulation with "No-Op" and "FCFS" policies on a small trace to verify memory usage remains within acceptable system limits. and request order is preserved.

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/simulation/engine.py` core SimPy environment, memory manager, and event definitions (RequestArrival, LoadStart, LoadEnd, Evict)
- [ ] T023 [US2] Implement `code/simulation/policies.py` with the **FCFS** (First-Come-First-Served) scheduling logic
- [ ] T024 [US2] Implement `code/simulation/policies.py` with the **Greedy Frequency** scheduling logic (track access counts)
- [ ] T025 [US2] Implement `code/simulation/policies.py` with the **Topological Lookahead** logic: consume `topology_graph.json` (T016) to identify the set of adapters with high parameter overlap to the currently requested adapter; select the next adapter to load from this set if it is predicted to be needed soon (based on trace frequency or simple lookahead window), WITHOUT constructing a Markov transition matrix from the trace for the scheduling decision; produce a function signature `def lookahead_decision(current_adapter, trace_window, topology_graph) -> next_candidate`.
- [ ] T026 [US2] Implement `code/simulation/engine.py` logic for adapter loading with size-proportional time and ±10% stochastic jitter
- [ ] T027 [US2] Implement `code/simulation/engine.py` cache eviction logic (LRU or policy-specific) when a memory limit is reached.
- [ ] T028 [US2] Implement `code/simulation/run_simulation.py` to execute a single trace with a specified policy and seed, outputting logs to `data/logs/`
- [ ] T029 [US2] Add validation to ensure no memory overflow occurs (assert `current_memory <= config.MEMORY_LIMIT_BYTES`)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US2] Unit test `tests/unit/test_simulation_engine.py::test_memory_limit_exceeded_event_triggering`
- [ ] T031 [P] [US2] Integration test `tests/integration/test_simulation_flow.py::test_fcfs_policy_execution_flow`

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently (Simulation Engine ready)

---

## Phase 5: User Story 3 - Policy Comparison & Statistical Validation (Priority: P2)

**Goal**: Execute multiple replications of the simulation for all three policies and perform statistical comparison (block-bootstrapping or paired t-test).

**Independent Test**: Run analysis on pre-generated logs to verify p-value calculation and boolean PASS/FAIL output for the 15% latency reduction threshold.

**⚠️ DEPENDENCY**: This phase depends on the completion of Phase 4 (US2).

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/simulation/run_experiment.py` to orchestrate exactly 30 independent replications for FCFS, Greedy, and Topological policies with different seeds
- [ ] T033 [US3] Implement `code/analysis/stats.py` to parse simulation logs and aggregate metrics (latency, evictions, hit rates) per policy
- [ ] T034 [US3] Implement `code/analysis/stats.py` to compute the *delta* of eviction counts between Topological and FCFS policies, and verify if the Topological policy reduces evictions (log result as PASS/FAIL).
- [ ] T035 [US3] Implement `code/analysis/stats.py` to perform block-bootstrapping on the 30 replication means comparing Topological vs. FCFS to determine statistical significance (p-value < 0.05).
- [ ] T036 [US3] Implement `code/analysis/stats.py` to evaluate the latency reduction threshold and output `PASS`/`FAIL`
- [ ] T037 [US3] Implement `code/analysis/visualize.py` to generate plots of latency distributions and convergence (if applicable)
- [ ] T038 [US3] Implement `code/analysis/report.py` to generate a summary report (JSON/Markdown) containing p-values, confidence intervals, and the final verdict
- [ ] T039 [US3] Add logging for statistical test parameters and results to `data/logs/analysis_report.log`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 [P] [US3] Unit test `tests/unit/test_stats.py::test_statistical_significance_calculation` (block-bootstrap)
- [ ] T041 [P] [US3] Integration test `tests/integration/test_experiment_run.py::test_full_experiment_orchestration`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `README.md` and `docs/`
- [ ] T043 Code cleanup and refactoring for efficiency (e.g., sparse matrix optimization for large overlap matrices)
- [ ] T044 Performance optimization to ensure full experiment runs < 6 hours on GitHub Actions free-tier
- [ ] T045 [P] Additional unit tests coverage verification in `tests/unit/`
- [ ] T046 Run `quickstart.md` validation and ensure all paths are correct
- [ ] T047 Verify `requirements.txt` pins exact versions for reproducibility

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (Produces data for US2/US3)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 data (Topology Graph) to implement Topological Lookahead policy
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 (Simulation Engine) to run replications
 - *Note*: While US2 and US3 are P1/P2, US3 logically requires US2 to be functional to run the experiment.

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation to ensure imports work
- Models/Schema before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 (Data Gen) and US2 (Engine Core/FCFS) can start in parallel.
- US2 (Topological Policy) must wait for US1 completion.
- US3 must wait for US2 completion.
- All tests for a user story marked [P] can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for adapter generation logic in tests/unit/test_data_gen.py"
Task: "Unit test for overlap matrix calculation in tests/unit/test_graph.py"

# Launch data generation tasks (if logic is separated):
Task: "Implement generate_adapters.py"
Task: "Implement generate_trace.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data & Graph)
4. **STOP and VALIDATE**: Verify synthetic data and topology graph are generated correctly and meet "non-trivial variance" criteria.
5. Deploy/demo if ready (Data pipeline validated).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Data) → Test independently → Data ready
3. Add User Story 2 (Simulation) → Test independently (FCFS/Greedy first, then Topological) → Simulation ready
4. Add User Story 3 (Analysis) → Test independently → Full experiment ready
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation & Graph)
 - Developer B: User Story 2 (Simulation Engine & FCFS/Greedy Policies)
3. Developer B implements Topological Policy once Developer A finishes US1.
4. Developer C: User Story 3 (Analysis & Stats) starts once US2 is functional.
5. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (or write after implementation to ensure imports work)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All simulation tasks must run on CPU-only (vCPU, limited RAM). No GPU libraries.
- **Constraint**: Synthetic data generation must use real mathematical operations (cosine similarity), not random fabrication of final metrics.
- **Constraint**: Simulation must complete within 6 hours; if not, reduce trace size or replication count in `run_experiment.py`.