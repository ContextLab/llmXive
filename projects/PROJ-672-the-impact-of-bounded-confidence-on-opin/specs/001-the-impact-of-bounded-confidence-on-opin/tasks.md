# Tasks: The Impact of Bounded Confidence on Opinion Polarization Speed

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project structure per implementation plan: create directories `code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/contract/`
- [ ] T002 Initialize Python 3.11 project with dependencies (networkx, numpy, pandas, scikit-learn, scipy, matplotlib, pytest) in `projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/checksums.py` utility to generate SHA-256 hashes for data files and update `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` (Principle III & V)
- [ ] T005 [P] Implement `utils/metrics.py` to calculate structural metrics (assortativity, average path length, clustering coefficient) for NetworkX graphs
- [ ] T006 [P] Implement `utils/plotting.py` for generating log-log convergence plots and regression scatter plots
- [ ] T007 [P] Create base data schemas (JSON schemas) for `SimulationRun`, `ScalingResult`, and `RegressionResult` in `code/contracts/` (files: `code/contracts/simulation_run.json`, `code/contracts/scaling_result.json`, `code/contracts/regression_result.json`)
- [ ] T008 [P] Setup `pytest` configuration and contract testing framework in `tests/contract/` (framework setup only, does not run tests yet; schemas from T007 must exist)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Synthetic Network Ensembles (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible ensembles of Erdős-Rényi, Barabási-Albert, and Watts-Strogatz networks ($N=500$) with distinct topological features.

**Independent Test**: Generate one instance of each topology, compute metrics, and verify they match theoretical expectations within 5% tolerance.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009 [P] [US1] Unit test for Barabási-Albert power-law degree distribution in `tests/unit/test_network_gen.py`
- [ ] T010 [P] [US1] Unit test for Watts-Strogatz clustering coefficient vs. rewiring probability in `tests/unit/test_network_gen.py`
- [ ] T011 [P] [US1] Memory constraint test: Verify 50 networks of $N=500$ fit within 7GB RAM in `tests/unit/test_memory_limits.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/generate_networks.py` to generate multiple independent instances per topology type with fixed random seeds using `numpy.random` (FR-001)
- [ ] T013 [US1] Implement logic to calculate and store structural metrics (assortativity, path length) for each generated network instance; save as JSON to `data/raw/networks/metrics_{seed}.json`
- [ ] T014 [US1] Add serialization logic to save network instances and metrics to `data/raw/networks/` with checksums
- [ ] T015 [US1] Add validation to ensure generated networks are connected (or handle disconnected components explicitly)
- [ ] T016 [US1] Implement logic to explicitly compare and validate the divergence of $\gamma$ (scaling exponent) between scale-free (BA) and small-world (WS) topologies as a distinct verification step for Constitution Principle VI (output to `data/processed/topology_comparison.json`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Bounded Confidence Simulations (Priority: P2)

**Goal**: Execute discrete-time Hegselmann-Krause simulations on generated networks, sweeping $\epsilon$ across a range of confidence thresholds and measuring convergence time.

**Independent Test**: Run a single simulation on $N=50$ with fixed $\epsilon$ and verify convergence to stable state ($<10^{-4}$ change) within reasonable iterations.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for HK update rule convergence on a small static network in `tests/unit/test_hk_logic.py`
- [ ] T018 [P] [US2] Unit test for non-convergence handling (max iteration limit) in `tests/unit/test_hk_logic.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/simulate_hk.py` with vectorized NumPy updates for the discrete-time Hegselmann-Krause rule (FR-002, FR-003). **Dependency**: This task consumes network instances saved by T014.
- [ ] T020 [US2] Implement convergence detection logic: stop when max opinion change $< 10^{-4}$ or max iterations reached (FR-004, FR-007)
- [ ] T021 [US2] Implement batch execution engine to sweep $\epsilon$ across a range of $[0.05, 0.50]$ with step size $0.05$ and execute multiple independent simulation runs per configuration (FR-003)
- [ ] T022 [US2] Add logic to handle non-convergent runs: flag as "non-convergent" in the `status` column of the CSV output in `data/raw/simulations/`
- [ ] T023 [US2] Write raw simulation results (seed, epsilon, convergence_time, status) to `data/raw/simulations/` with checksums
- [ ] T024 [US2] Integration test for batch execution of multiple configurations (3 topologies × variable epsilons) verifying output format in `tests/integration/test_simulation_batch.py`
- [ ] T025 [US2] Implement performance optimization and runtime monitoring in `code/simulate_hk.py` (e.g., parallel processing with `multiprocessing`, progress tracking) to ensure the full simulation suite completes within 5 hours (SC-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Scaling Laws and Structural Correlations (Priority: P3)

**Goal**: Fit power-law models to convergence time data, extract $\gamma$, and regress against structural metrics.

**Independent Test**: Provide synthetic data, verify regression identifies known correlation and power-law fit $R^2 > 0.8$.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for power-law fitting with bootstrapping error estimation in `tests/unit/test_scaling_fit.py`
- [ ] T027 [P] [US3] Unit test for multiple linear regression with categorical topology variable in `tests/unit/test_regression.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analyze_scaling.py` with peak-finding algorithm to detect $\epsilon_c$ per topology and calculate the critical threshold explicitly (FR-005). **Output**: $\epsilon_c$ values for each topology.
- [ ] T029 [US3] Implement power-law fitting $T = A(\epsilon - \epsilon_c)^{-\gamma}$ restricted to critical regime $\epsilon \in [\epsilon_c + 0.05, 0.50]$. **Logic**: Must consume $\epsilon_c$ values from T028 to define the regime filter, then perform the fit (FR-005)
- [ ] T030 [US3] Implement multiple linear regression to correlate $\gamma$ with assortativity and path length, including topology as a categorical variable (FR-006)
- [ ] T031 [US3] Implement visualization module to generate: (1) $\gamma$ vs. assortativity scatter with regression line, (2) Convergence time vs. $\epsilon$ on log-log scale
- [ ] T032 [US3] Save processed results (ScalingResult, RegressionResult) to `data/processed/` with checksums

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis (FR-008)

**Goal**: Verify robustness of results to convergence threshold as mandated by FR-008.

**Independent Test**: Sweep convergence threshold $10^{-3}$ to $10^{-5}$ and verify $\gamma$ variation < 5%.

### Implementation for Sensitivity Analysis

- [ ] T033 [US3] Implement `code/sensitivity_analysis.py` to **re-run the simulation engine** (`simulate_hk.py`) with convergence thresholds $\delta \in [10^{-3}, 10^{-5}]$ (generating new raw data in `data/raw/simulations_sensitivity/`), then re-analyze to compare resulting $\gamma$ values (FR-008). **Dependency**: Depends on `simulate_hk.py` code from US2, not on US3 analysis completion.
- [ ] T034 [US3] Generate report comparing $\gamma$ variation across the sensitivity sweep; flag if variation > 5%

**Checkpoint**: Sensitivity and robustness checks complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` including explanation of the methodology and results
- [ ] T036 Code cleanup and refactoring of `simulate_hk.py` for performance (vectorization check)
- [ ] T037 [P] Run quickstart.md validation
- [ ] T038 Update `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` with final artifact hashes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Network Gen) must complete before US2 (Simulation) can run
  - US2 (Simulation) must complete before US3 (Analysis) can run
  - Sensitivity (Phase 6) depends on the *code* of US2 (to re-run simulations) and US3 (for analysis logic), but is a parallel branch that re-executes US2 logic.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Depends on US1 (needs networks to simulate)
- **User Story 3 (P3)**: Depends on US2 (needs simulation results)
- **Sensitivity (Phase 6)**: Depends on US2 code (to re-run) and US3 code (for analysis); re-executes US2 logic with new parameters.
- **Polish (Phase N)**: Depends on all prior phases

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, US1 can start immediately
- US2 can start as soon as US1 produces the first batch of networks (if pipelined)
- All tests for a user story marked [P] can run in parallel
- Phase 6 tasks (T033-T034) can run in parallel with US3 analysis if US2 code is ready.

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Network Generation)
4. Complete Phase 4: US2 (Simulation)
5. **STOP and VALIDATE**: Ensure raw data is generated and checksums are valid.
6. Proceed to Analysis (US3) and Sensitivity (Phase 6).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Validate network metrics
3. Add US2 → Test independently → Validate convergence times
4. Add US3 → Test independently → Validate scaling exponents
5. Add Sensitivity → Test independently → Validate robustness
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Network Gen)
   - Developer B: US2 (Simulation Engine) - *Note: Developer B can start with a mock network generator if US1 is delayed*
   - Developer C: US3 (Analysis) - *Can start with synthetic data*
3. Once baseline is established:
   - Developer D: Phase 6 (Sensitivity Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **Critical Constraint**: All tasks must run on CPU-only (limited cores, constrained RAM). No GPU, no 8-bit quantization, no large model loading.
- **Scope Note**: This project strictly implements the fixed Hegselmann-Krause model as defined in FR-001 to FR-008. The experimental Phase 7 tasks (adaptive thresholds, alternative rules) have been removed to adhere strictly to the spec.
- **Performance**: Task T025 explicitly addresses the 5-hour runtime constraint (SC-003).
- **Sensitivity**: Task T033 explicitly re-runs simulations to satisfy FR-008, ensuring valid sensitivity analysis.
- **Validation**: Task T016 explicitly validates Constitution Principle VI regarding topological divergence.