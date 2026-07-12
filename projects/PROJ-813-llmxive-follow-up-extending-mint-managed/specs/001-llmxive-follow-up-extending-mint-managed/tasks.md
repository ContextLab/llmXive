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
- [ ] T001b [P] Create `requirements.txt` pinning simpy, numpy, scipy, scikit-learn, pandas, pytest, statsmodels, psutil, pyyaml
- [ ] T001c [P] Create `.gitignore` and `pytest.ini` with random seed pinning configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Implement `code/config.py` with seeds, memory limits, paths, NUM_ADAPTERS=10000, and cost model parameters (I/O bandwidth, copy time)
- [ ] T004b [P] Implement cost model calibration in `code/config.py` or `code/utils/calibration.py` against standard published CPU I/O bandwidth values (e.g., NVMe and DDR4) and record the source citation; update config with calibrated values | Depends on: T004a
- [ ] T005 [P] Setup `code/data/generator.py` skeleton with block-wise computation logic for sparse matrix generation
- [ ] T006 [P] Setup `code/simulation/environment.py` skeleton with SimPy environment and resource monitor (peak RSS tracking)
- [ ] T007 Create `code/simulation/policies.py` skeleton with abstract base class for scheduling policies (FCFS, Greedy, Lookahead)
- [ ] T008 Setup `code/analysis/statistics.py` skeleton with statistical test wrappers (Shapiro-Wilk, t-test, Wilcoxon)
- [ ] T009 Setup `code/analysis/metrics.py` skeleton for latency, eviction, and graph density calculation
- [ ] T010 Implement timeout wrapper in `code/simulation/runner.py` to enforce a maximum execution limit and graceful termination

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation & Topology Construction (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic LoRA adapters and compute pairwise parameter overlap to construct the LoRA Topology Graph.

**Independent Test**: Run `code/data/generator.py` on 2 vCPU runner; verify output `data/processed/topology_graph.npz` is symmetric, contains no NaNs, and dimensions match requested N.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for sparse matrix generation in `tests/unit/test_data_generation.py` (verify rank/sparsity patterns) | Depends on: T005
- [ ] T012 [P] [US1] Unit test for block-wise overlap computation in `tests/unit/test_data_generation.py` (verify symmetry and memory bounds) | Depends on: T005
- [ ] T013 [P] [US1] Integration test for graph validity in `tests/integration/test_data_generation.py` (verify no NaNs/Infs) | Depends on: T005

### Implementation for User Story 1

- [ ] T014 [US1] Implement synthetic adapter generation in `code/data/generator.py` (random ranks across a variable range, sparse patterns)
- [ ] T015 [US1] Implement block-wise pairwise parameter overlap calculation in `code/data/generator.py` using `scipy.sparse` to compute the **degree of shared weight updates** for edge weights; output `data/processed/topology_graph.npz`; verify symmetry and no NaNs | Depends on: T005
- [ ] T016 [US1] Implement graph validation logic (symmetry check, NaN check) in `code/data/generator.py`
- [ ] T017 [US1] Implement serialization of adjacency matrix to `data/processed/topology_graph.npz` (CSR format)
- [ ] T018 [US1] Add logging for data generation steps and memory usage tracking
- [ ] T019 [US1] Implement sensitivity analysis logic to generate adapters with varying sparsity levels (Low=0.1, Medium=0.5, High=0.9) for FR-008 | Depends on: T014

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Discrete-Event Simulation of MinT Infrastructure (Priority: P2)

**Goal**: Implement the SimPy-based simulation engine modeling memory constraints, adapter loading, and request processing.

**Independent Test**: Run simulation with FCFS policy and static trace; verify deterministic log of wall-clock time and cache events matches memory constraints.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for eviction logic in `tests/unit/test_simulation.py` (verify LRU/low-priority removal)
- [ ] T021 [P] [US2] Unit test for memory constraint enforcement in `tests/unit/test_simulation.py` (verify OOM handling)
- [ ] T022 [P] [US2] Integration test for FCFS baseline in `tests/integration/test_simulation.py` (verify deterministic output)

### Implementation for User Story 2

- [ ] T023 [US2] Implement SimPy environment setup with a memory resource (configurable limit) in `code/simulation/environment.py` | Depends on: T006
- [ ] T024 [US2] Implement adapter loading mechanism in `code/simulation/environment.py` with cost model parameters: I/O bandwidth (MB/s) and memory copy time (ms); log latency events to `data/results/latency_events.csv` | Depends on: T023, T004b
- [ ] T025 [US2] Implement eviction logic (LRU or priority-based) in `code/simulation/environment.py`
- [ ] T026 [US2] Implement request processing simulation with cost model (I/O bandwidth, memory copy time) in `code/simulation/environment.py`
- [ ] T027 [US2] Implement event logging for wall-clock time, cache hits, and evictions to `data/results/`
- [ ] T028 [US2] Integrate timeout wrapper to terminate gracefully if the predefined time limit is exceeded. | Depends on: T010
- [ ] T029 [US2] Implement memory pressure detection and fallback to chunked processing in `code/utils/memory_monitor.py` | Depends on: T006

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Greedy Frequency-Based Scheduling Policy (Priority: P2.5)

**Goal**: Implement and execute the Greedy frequency-based scheduling policy as a secondary baseline.

**Independent Test**: Run simulation with Greedy policy on same trace as US-2; verify eviction logic prioritizes least-frequently accessed adapters.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for frequency tracking in `tests/unit/test_policies.py`
- [ ] T031 [P] [US3] Unit test for Greedy eviction selection in `tests/unit/test_policies.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement frequency tracking mechanism in `code/simulation/policies.py` (history of request access) | Depends on: T023, T024, T025, T026
- [ ] T033 [US3] Implement Greedy policy logic (evict lowest frequency on memory full) in `code/simulation/policies.py` | Depends on: T032
- [ ] T034 [US3] Integrate Greedy policy with simulation engine in `code/simulation/runner.py`
- [ ] T035 [US3] Run Greedy policy simulation and write results to `data/results/greedy_results.csv` | Depends on: T034

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Topological Lookahead Scheduling Policy Execution (Priority: P3)

**Goal**: Implement and execute the Topological Lookahead policy using the LoRA Topology Graph and Markov chain transitions.

**Independent Test**: Run simulation with Lookahead policy; statistically compare latency against FCFS/Greedy using Shapiro-Wilk and t-test/Wilcoxon.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [P] [US4] Unit test for Markov transition matrix construction in `tests/unit/test_policies.py`
- [ ] T037 [P] [US4] Unit test for Topological Lookahead prefetch logic in `tests/unit/test_policies.py`
- [ ] T038 [P] [US4] Unit test for statistical test selection logic (Shapiro-Wilk -> t-test/Wilcoxon) in `tests/unit/test_analysis.py`

### Implementation for User Story 4

- [ ] T039 [US4] Implement synthetic request trace generation with topological bias (FR-011) using correlation mechanism P(Request B | Request A) = base_rate + k * Overlap(A,B) in `code/data/generator.py`; save to `data/processed/request_trace.parquet` | Depends on: T004, T017
- [ ] T040 [US4] Implement Markov chain request transition analysis in `code/simulation/policies.py` using `data/processed/request_trace.parquet` and `data/processed/topology_graph.npz`; output `data/processed/markov_matrix.npy` | Depends on: T039, T017
- [ ] T041 [US4] Implement Topological Lookahead prefetch logic in `code/simulation/policies.py` consuming `data/processed/markov_matrix.npy` to cluster adapters and pre-fetch high-probability neighbors | Depends on: T040
- [ ] T042 [US4] Integrate Lookahead policy with simulation engine in `code/simulation/runner.py`
- [ ] T043 [US4] Run Lookahead policy simulation and write results to `data/results/lookahead_results.csv` | Depends on: T042
- [ ] T044 [US4] Implement epoch-based aggregation for latency distributions in `code/analysis/metrics.py` | Depends on: T009
- [ ] T045 [US4] Implement Shapiro-Wilk normality test and conditional t-test/Wilcoxon selection in `code/analysis/statistics.py` | Depends on: T008
- [ ] T046 [US4] Generate statistical summary `data/results/statistical_summary.json` including fields: `p_latency` (median cold-start latency), `p_value`, `test_type`, `significance_flag`, `eviction_reduction_pct` (percentage reduction in total cache evictions), and `eviction_ci` (confidence interval) comparing Lookahead vs FCFS and Lookahead vs Greedy | Depends on: T043, T045
- [ ] T047 [US4] Implement logic to compute `significance_flag` (boolean) and `test_type` (string) in `code/analysis/statistics.py` based on p < 0.05 threshold | Depends on: T045
- [ ] T048 [US4] Implement "Zero Locality" trace generation (alpha=0.0) and verify Topological policy degrades to FCFS behavior | Depends on: T039
- [ ] T049 [US4] Implement "Noisy" trace generation (alpha=0.15 + 20% noise) to validate robustness | Depends on: T039
- [ ] T057 [US4] Implement the 'Fixed Topology, Regenerated Trace' replication loop: For each of 10 seeds: (1) Generate and freeze a unique Topology Graph (adapters + overlap); (2) Generate 10 distinct request traces for that frozen graph using T039 logic; (3) Run FCFS, Greedy, and Lookahead policies on all 10 traces; (4) Aggregate results for statistical testing in T046. Ensure full dataset regeneration (adapters + topology + trace) per seed. | Depends on: T017, T039, T042

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates in `docs/` (explain simulation cost model and statistical methods)
- [ ] T051 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T052a [US1] Enforce sparse matrix representation (CSR/CSC) for all adapter data and overlap matrices in `code/data/generator.py` to ensure memory < 7168 MB; Add assertion: `assert peak_rss < 7168` | Depends on: T015
- [ ] T052b [US1] Implement block-wise overlap computation logic in `code/data/generator.py` to process 1000x1000 chunks, verifying peak RAM stays within limits | Depends on: T052a
- [ ] T053 [P] Additional unit tests for edge cases (zero locality trace, sparse matrix fallback, timeout) in `tests/`
- [ ] T054 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T055 [P] Verify all results are checksummed and recorded in `state/`
- [ ] T056 [P] Implement warm-up verification script for N=1,000 adapters to validate feasibility before full scale run (FR-010)
- [ ] T058 [US4] Execute Sensitivity Analysis: Run the full T057 replication loop (10 seeds x 10 traces) for three sparsity levels (Low=0.1, Medium=0.5, High=0.9); generate comparative report `data/results/sensitivity_report.json` showing Topological Lookahead performance across sparsity levels | Depends on: T057, T019

**Checkpoint**: All user stories should now be independently functional

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
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 graph, US2 simulation, and US3 baselines; **T057** is the critical path for statistical validity.

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
Task: "Unit test for sparse matrix generation in tests/unit/test_data_generation.py"
Task: "Unit test for block-wise overlap computation in tests/unit/test_data_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic adapter generation in code/data/generator.py"
Task: "Implement block-wise pairwise parameter overlap calculation in code/data/generator.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo (Requires T057 loop)
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
- **CRITICAL**: Trace generation MUST follow the "Fixed Topology, Regenerated Trace" design for statistical validity (Plan.md). T057 is the enforcement task.
- **CRITICAL**: Cost model must be calibrated against published values (T004b) and strictly model I/O bandwidth and memory copy time (no network contention).
- **CRITICAL**: Sparsity levels for sensitivity analysis are fixed at 0.1, 0.5, 0.9 (T019, T058).