# Tasks: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Input**: Design documents from `/specs/001-lora-topology-scheduling/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `projects/PROJ-813-llmxive-follow-up-extending-mint-managed/` with `data/raw/`, `data/processed/`, `data/results/`, `code/`, `tests/`, `specs/`
- [ ] T001b [P] Create `requirements.txt` pinning simpy, numpy, scipy, scikit-learn, pandas, pytest
- [ ] T001c [P] Create `.gitignore` and `pytest.ini` with random seed pinning configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with seeds, memory limits, paths, and NUM_ADAPTERS (deferred)
- [ ] T005 [P] Setup `code/data_generation.py` skeleton with block-wise computation logic for sparse matrix generation
- [ ] T006 [P] Setup `code/simulation.py` skeleton with SimPy environment and resource monitor (peak RSS tracking)
- [ ] T007 Create `code/policies.py` skeleton with abstract base class for scheduling policies (FCFS, Greedy, Lookahead)
- [ ] T008 Setup `code/analysis.py` skeleton with statistical test wrappers (Shapiro-Wilk, t-test, Wilcoxon)
- [ ] T010 Implement timeout wrapper in `code/main.py` to enforce a maximum execution limit

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation & Topology Construction (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic LoRA adapters and compute pairwise parameter overlap to construct the LoRA Topology Graph.

**Independent Test**: Run `code/data_generation.py` on 2 vCPU runner; verify output `data/processed/topology_graph.parquet` is symmetric, contains no NaNs, and dimensions match [deferred] adapters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for sparse matrix generation in `tests/test_data_generation.py` (verify rank/sparsity patterns) | Depends on: T005
- [ ] T012 [P] [US1] Unit test for block-wise overlap computation in `tests/test_data_generation.py` (verify symmetry and memory bounds) | Depends on: T005
- [ ] T013 [P] [US1] Integration test for graph validity in `tests/test_data_generation.py` (verify no NaNs/Infs) | Depends on: T005

### Implementation for User Story 1

- [ ] T014 [US1] Implement synthetic adapter generation in `code/data_generation.py` (random ranks across a variable range, sparse patterns)
- [ ] T015 [US1] Implement block-wise pairwise parameter overlap calculation in `code/data_generation.py` using `scipy.sparse` to compute the **degree of shared weight updates** for edge weights; output `data/processed/topology_graph.parquet`; verify symmetry and no NaNs | Depends on: T005
- [ ] T016 [US1] Implement graph validation logic (symmetry check, NaN check) in `code/data_generation.py`
- [ ] T017 [US1] Implement serialization of adjacency matrix to `data/processed/topology_graph.parquet`
- [ ] T018 [US1] Add logging for data generation steps and memory usage tracking

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Discrete-Event Simulation of MinT Infrastructure (Priority: P2)

**Goal**: Implement the SimPy-based simulation engine modeling memory constraints, adapter loading, and request processing.

**Independent Test**: Run simulation with FCFS policy and static trace; verify deterministic log of wall-clock time and cache events matches memory constraints.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for eviction logic in `tests/test_simulation.py` (verify LRU/low-priority removal)
- [ ] T020 [P] [US2] Unit test for memory constraint enforcement in `tests/test_simulation.py` (verify OOM handling)
- [ ] T021 [P] [US2] Integration test for FCFS baseline in `tests/test_simulation.py` (verify deterministic output)

### Implementation for User Story 2

- [ ] T022 [US2] Implement SimPy environment setup with a memory resource (configurable limit) in `code/simulation.py` | Depends on: T006
- [ ] T023 [US2] Implement adapter loading mechanism in `code/simulation.py` with cost model parameters: I/O bandwidth (MB/s), memory copy time (ms), and **simulated network contention** (latency jitter); log latency events to `data/results/latency_events.csv` | Depends on: T022
- [ ] T024 [US2] Implement eviction logic (LRU or priority-based) in `code/simulation.py`
- [ ] T025 [US2] Implement request processing simulation with cost model (network contention, latency) in `code/simulation.py`
- [ ] T026 [US2] Implement event logging for wall-clock time, cache hits, and evictions to `data/results/`
- [ ] T027 [US2] Integrate timeout wrapper to terminate gracefully if 6-hour limit exceeded

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Greedy Frequency-Based Scheduling Policy (Priority: P2.5)

**Goal**: Implement and execute the Greedy frequency-based scheduling policy as a secondary baseline.

**Independent Test**: Run simulation with Greedy policy on same trace as US-2; verify eviction logic prioritizes least-frequently accessed adapters.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for frequency tracking in `tests/test_policies.py`
- [ ] T029 [P] [US3] Unit test for Greedy eviction selection in `tests/test_policies.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement frequency tracking mechanism in `code/policies.py` (history of request access) | Depends on: T022, T023, T024, T025, T026, T017
- [ ] T031 [US3] Implement Greedy policy logic (evict lowest frequency on memory full) in `code/policies.py` | Depends on: T030, T022, T023, T024, T025, T026
- [ ] T032 [US3] Integrate Greedy policy with simulation engine in `code/main.py`
- [ ] T033 [US3] Run Greedy policy simulation and write results to `data/results/greedy_results.csv`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Topological Lookahead Scheduling Policy Execution (Priority: P3)

**Goal**: Implement and execute the Topological Lookahead policy using the LoRA Topology Graph and Markov chain transitions.

**Independent Test**: Run simulation with Lookahead policy; statistically compare latency against FCFS/Greedy using Shapiro-Wilk and t-test/Wilcoxon.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US4] Unit test for Markov transition matrix construction in `tests/test_policies.py`
- [ ] T035 [P] [US4] Unit test for Topological Lookahead prefetch logic in `tests/test_policies.py`
- [ ] T036 [P] [US4] Unit test for statistical test selection logic (Shapiro-Wilk -> t-test/Wilcoxon) in `tests/test_analysis.py`

### Implementation for User Story 4

- [ ] T015a [US4] Generate synthetic request trace (with hotspots) and save to `data/processed/request_trace.parquet` | Depends on: T004
- [ ] T037 [US4] Implement Markov chain request transition analysis in `code/policies.py` using `data/processed/request_trace.parquet` and `data/processed/topology_graph.parquet`; output `data/processed/markov_matrix.npy` | Depends on: T015a, T017
- [ ] T038 [US4] Implement Topological Lookahead prefetch logic in `code/policies.py` consuming `data/processed/markov_matrix.npy` from T037 to cluster adapters and pre-fetch high-probability neighbors | Depends on: T037
- [ ] T039 [US4] Integrate Lookahead policy with simulation engine in `code/main.py`
- [ ] T040 [US4] Run Lookahead policy simulation and write results to `data/results/lookahead_results.csv`
- [ ] T041 [US4] Implement epoch-based aggregation for latency distributions in `code/analysis.py`
- [ ] T042 [US4] Implement Shapiro-Wilk normality test and conditional t-test/Wilcoxon selection in `code/analysis.py`
- [ ] T043 [US4] Generate statistical summary `data/results/statistical_summary.json` including fields: `p_latency` (median cold-start latency), `p_value`, `test_type`, `significance_flag` comparing Lookahead vs FCFS and Lookahead vs Greedy | Depends on: T040, T042
- [ ] T044 [US4] Implement logic to compute `significance_flag` (boolean) and `test_type` (string) in `code/analysis.py` based on p < 0.05 threshold and write them to `data/results/statistical_summary.json` | Depends on: T042

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` (explain simulation cost model and statistical methods)
- [ ] T046 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T047a [US1] Enforce sparse matrix representation (CSR/CSC) for all adapter data and overlap matrices in `code/data_generation.py` to ensure memory < 7168 MB
- [ ] T047b [US1] Implement block-wise overlap computation logic in `code/data_generation.py` to process 1000x1000 chunks, verifying peak RAM stays within limits
- [ ] T048 [P] Additional unit tests for edge cases (zero locality trace, sparse matrix fallback) in `tests/`
- [ ] T049 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T050 [P] Verify all results are checksummed and recorded in `state/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2.5)**: Can start after Foundational (Phase 2) - Depends on US1 graph and US2 simulation
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 graph, US2 simulation, and US3 baselines

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Services before endpoints/policies
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
Task: "Unit test for sparse matrix generation in tests/test_data_generation.py"
Task: "Unit test for block-wise overlap computation in tests/test_data_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic adapter generation in code/data_generation.py"
Task: "Implement block-wise pairwise parameter overlap calculation in code/data_generation.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3 & 4 (or split)
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
- **CRITICAL**: All data generation must use real synthetic data (random seeds) and never fake results; all metrics must be computed from actual simulation runs.
- **CRITICAL**: Ensure sparse matrix representations and block-wise computation are used to stay within 7168 MB RAM limit.
- **CRITICAL**: Simulation must handle edge cases (zero locality, timeout) gracefully without crashing.