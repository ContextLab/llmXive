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

- [X] T001 Create project structure per implementation plan: create directories `code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/contract/`, and initialize `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml`
- [X] T002 Initialize Python 3.11 project with dependencies (networkx, numpy, pandas, scipy, matplotlib, pytest, statsmodels) in `projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `utils/checksums.py` utility to generate SHA-256 hashes for data files and update `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` (Principle III & V)
- [X] T005 [P] Implement `utils/metrics.py` to calculate structural metrics (assortativity, average path length, clustering coefficient) for NetworkX graphs
- [X] T006 [P] Implement `utils/plotting.py` for generating log-log convergence plots and regression scatter plots
- [X] T007 [P] Create base data schemas (JSON schemas) for `SimulationRun`, `ScalingResult`, and `RegressionResult` in `code/contracts/` (files: `code/contracts/simulation_run.json`, `code/contracts/scaling_result.json`, `code/contracts/regression_result.json`)
- [ ] T008 [P] Setup `pytest` configuration and contract testing framework in `tests/contract/` (framework setup only, does not run tests yet; schemas from T007 must exist)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Synthetic Network Ensembles (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible ensembles of Erdős-Rényi, Barabási-Albert, and Watts-Strogatz networks ($N=500$) with distinct topological features.

**Independent Test**: Generate one instance of each topology, compute metrics, and verify they match theoretical expectations within 5% tolerance.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Unit test for Barabási-Albert power-law degree distribution in `tests/unit/test_network_gen.py`
- [ ] T010 [P] [US1] Unit test for Watts-Strogatz clustering coefficient vs. rewiring probability in `tests/unit/test_network_gen.py`
- [ ] T011 [P] [US1] Memory constraint test: Verify 50 networks of $N=500$ fit within 7GB RAM in `tests/unit/test_memory_limits.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/generate_networks.py` to generate multiple independent instances per topology type with fixed random seeds using `numpy.random` explicitly wired to the global seed fixture defined in `tests/conftest.py` (FR-001)
- [ ] T013 [US1] Implement logic to calculate and store structural metrics (assortativity, path length) for each generated network instance; save as JSON to `data/raw/networks/metrics_{seed}.json`
- [ ] T014 [US1] Add serialization logic to save network instances and metrics to `data/raw/networks/` with checksums
- [ ] T015 [US1] Add validation to ensure generated networks are connected (or handle disconnected components explicitly)
- [ ] T016a [P] [US1] **Data Schema Prep**: Implement the data structure preparation for regression analysis in `code/contracts/regression_schema.py`. This task defines the schema for `regression_data.json` (mapping structural metrics to simulation IDs) but does NOT populate it with gamma values yet (FR-006, US-3 dependency).
- [ ] T016b [P] [US3] **Data Population**: (Depends on US3 completion) Implement logic to populate `data/processed/regression_data.json` by correlating the extracted scaling exponent $\gamma$ (from T029/T030) with structural metrics (from T013) and outputting the final dataset (FR-006, US-3).

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
- [ ] T021 [US2] Implement batch execution engine to sweep $\epsilon$ across a range of $[, 0.50]$ with step size $0.05$ and execute multiple independent simulation runs per configuration (FR-003)
- [ ] T022 [US2] Add logic to handle non-convergent runs: flag as "non-convergent" in the `status` column of the CSV output in `data/raw/simulations/`
- [ ] T023 [US2] Write raw simulation results to `data/raw/simulations/` with checksums. **CRITICAL CHANGE**: Output format MUST include the full temporal trace of opinion vectors (state at every iteration) for each run to support FR-008 sensitivity analysis, in addition to the final convergence time and status.
- [ ] T024 [US2] Integration test for batch execution of multiple configurations (multiple topologies × variable epsilons) verifying output format in `tests/integration/test_simulation_batch.py`
- [ ] T025 [US2] Implement performance optimization and runtime monitoring in `code/simulate_hk.py` (e.g., parallel processing with `multiprocessing`, progress tracking) to ensure the full simulation suite completes within 5 hours (SC-003). **Reproducibility Constraint**: Parallel workers MUST use a deterministic seed distribution strategy (e.g., `worker_seed = base_seed + worker_id`) to prevent race conditions and ensure floating-point reproducibility.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Scaling Laws and Structural Correlations (Priority: P3)

**Goal**: Fit power-law models to convergence time data, extract $\gamma$, and regress against structural metrics.

**Independent Test**: Provide synthetic data, verify regression identifies known correlation and power-law fit $R^2 > 0.8$.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for power-law fitting with bootstrapping error estimation in `tests/unit/test_scaling_fit.py`
- [ ] T027 [P] [US3] Unit test for multiple linear regression with categorical topology variable in `tests/unit/test_regression.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analyze_scaling.py` with peak-finding algorithm to detect $\epsilon_c$ for each of the network instances per topology and output a set of $\epsilon_c$ values to `data/processed/epsilon_c_values.json` (FR-005, Plan Clarification #1)
- [ ] T029 [US3] Implement power-law fitting $T = A(\epsilon - \epsilon_c)^{-\gamma}$ restricted to critical regime $\epsilon \in [\epsilon_c + \delta, 0.50]$, where $\delta$ represents a small positive offset defining the onset of the critical regime.. **Logic**: Must consume per-instance $\epsilon_c$ values from T028 to define the regime filter, then perform the fit (FR-005)
- [ ] T030 [US3] Implement Model A: Multiple linear regression to correlate $\gamma$ with Topology type (categorical variable only), excluding structural metrics to avoid multicollinearity (FR-006, Plan Clarification #3)
- [ ] T030b [US3] Implement Model B: Multiple linear regression to correlate $\gamma$ with Assortativity and PathLength *within* each topology group, excluding Topology as a variable (FR-006, Plan Clarification #3)
- [ ] T031 [US3] Implement visualization module to generate: (1) $\gamma$ vs. assortativity scatter with regression line, (2) Convergence time vs. $\epsilon$ on log-log scale
- [ ] T032 [US3] Save processed results (ScalingResult, RegressionResult) to `data/processed/` with checksums

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis (FR-008)

**Goal**: Verify robustness of results to convergence threshold as mandated by FR-008.

**Independent Test**: Sweep convergence threshold $10^{-3}$ to $10^{-5}$ and verify $\gamma$ variation < 5%.

### Implementation for Sensitivity Analysis

- [ ] T033 [US3] Implement `code/sensitivity_analysis.py` to **re-analyze existing simulation traces** (from `data/raw/simulations/` generated by T023) by applying convergence thresholds $\delta \in [10^{-3}, 10^{-5}]$ to the **full temporal traces** stored in the raw data and re-running the analysis logic to compare resulting $\gamma$ values (FR-008). **Dependency**: Depends on `simulate_hk.py` output (T023) containing full traces.
- [ ] T034 [US3] Generate report comparing $\gamma$ variation across the sensitivity sweep; flag if variation > 5%

**Checkpoint**: Sensitivity and robustness checks complete.

---

## Phase 7: Research Review Resolution (Addressing Prior Reviews)

**Goal**: Explicitly address concerns raised by Alan Turing (adaptive thresholds), David Krakauer (biological signal detection context), Stephen Wolfram (rule-space exploration), and Geoffrey West (scaling of $\epsilon$ with density) without violating the static HK constraint of the current spec.

**Independent Test**: Documentation and code comments clearly distinguish between the static baseline and the proposed adaptive variants; a "Rule Space Explorer" script runs variations of the HK update rule; a scaling analysis script tests $\epsilon$ vs. network density.

### Implementation for Research Review Resolution

- [ ] T035 [P] [Review] Implement `code/explorers/rule_space_explorer.py` to systematically enumerate and run alternative update rules (e.g., weighted averaging, median-based updates, non-linear transformations) within the bounded confidence framework, generating a "rule landscape" dataset (Response to Stephen Wolfram).
- [ ] T036 [P] [Review] Implement `code/explorers/adaptive_threshold_prototype.py` as a **non-executable research prototype** (or a separate optional branch) that simulates an agent adapting $\epsilon$ based on convergence history, strictly isolated from the main `simulate_hk.py` to maintain spec fidelity (Response to Alan Turing).
- [ ] T037 [P] [Review] Update `docs/methodology.md` to include a section "Biological Imperative and Signal Detection" discussing the evolutionary context of bounded confidence as a noise-filtering mechanism vs. error-calcifying mechanism (Response to David Krakauer).
- [ ] T038 [P] [Review] Update `docs/methodology.md` to include a section "Historical Lineage and Micro-Rules" explicitly contrasting Deffuant (convergence) vs. Hegselmann & Krause (fragmentation) outcomes based on the specific micro-rule implemented (Response to David Krakauer).
- [ ] T039 [P] [Review] Add a validation task in `tests/unit/test_review_alignment.py` to ensure the codebase explicitly distinguishes between "static cognitive limitation" (current model) and "adaptive learning" (future work) in all docstrings and comments (Response to Alan Turing).
- [ ] T040 [P] [Review] Generate a comparative plot in `code/visualizations/plot_rule_space.py` showing how different update rules affect the phase transition point (Response to Stephen Wolfram).
- [ ] T041 [P] [Review] Implement `code/explorers/epsilon_scaling_analysis.py` to test the hypothesis that $\epsilon$ scales with network density (average degree) by running a targeted sweep of $\epsilon$ values across networks of varying densities and plotting the resulting $\gamma$ vs. density relationship (Response to Geoffrey West).
- [ ] T042 [P] [Review] Update `docs/methodology.md` to include a section "Topological Constraints and Scaling" discussing the implications of degree heterogeneity (power-law vs. homogeneous) on the critical threshold and the potential for phase transitions at critical network sizes (Response to Geoffrey West).
- [ ] T043 [P] [Review] Run the Reference-Validator Agent on all new citations introduced in `docs/methodology.md` and `code/explorers/` (T035-T042) to satisfy Constitution Principle II before transitioning to `research_accepted`.

**Checkpoint**: All prior research-stage reviews are addressed with code prototypes or explicit documentation clarifications.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/` including explanation of the methodology and results
- [ ] T045 Code cleanup and refactoring of `simulate_hk.py` for performance (vectorization check)
- [ ] T046 [P] Run quickstart.md validation
- [ ] T047 [P] Update `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` with final artifact hashes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (Network Gen) must complete before US2 (Simulation) can run
 - US2 (Simulation) must complete before US3 (Analysis) can run
 - Sensitivity (Phase 6) depends on the *code* of US2 (to re-run simulations) and US3 (for analysis logic), but is a parallel branch that re-executes US2 logic.
 - Research Review (Phase 7) can run in parallel with US3/Phase 6 as it focuses on exploration and documentation.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Depends on US1 (needs networks to simulate)
- **User Story 3 (P3)**: Depends on US2 (needs simulation results)
- **Sensitivity (Phase 6)**: Depends on US2 code (to re-run) and US3 code (for analysis); re-executes US2 logic with new parameters.
- **Research Review (Phase 7)**: Can start after Foundational; depends on US2/US3 logic for comparison but is largely independent.
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
- Phase 7 tasks (T035-T043) can run in parallel with US3 and Phase 6.

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
6. Add Research Review → Test independently → Validate alignment with prior reviews
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: US1 (Network Gen)
 - Developer B: US2 (Simulation Engine) - *Note: Developer B can start with a mock network generator if US1 is delayed*
 - Developer C: US3 (Analysis) - *Can start with synthetic data*
 - Developer D: Phase 7 (Research Review Exploration) - *Can start immediately on rule-space logic and scaling analysis*
3. Once baseline is established:
 - Developer E: Phase 6 (Sensitivity Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **Critical Constraint**: All tasks must run on CPU-only (limited cores, constrained RAM). No GPU, no 8-bit quantization, no large model loading.
- **Scope Note**: This project strictly implements the fixed Hegselmann-Krause model as defined in FR-001 to FR-008. The experimental Phase 7 tasks (adaptive thresholds, alternative rules, scaling analysis) are **exploratory prototypes** or **documentation** and do not alter the core static model execution.
- **Performance**: Task T025 explicitly addresses the 5-hour runtime constraint (SC-003) with deterministic parallelization.
- **Sensitivity**: Task T033 explicitly re-analyzes existing traces (now containing full temporal data) to satisfy FR-008, ensuring valid sensitivity analysis within runtime limits.
- **Validation**: Task T016a/T016b explicitly validates Constitution Principle VI regarding topological divergence by preparing and populating data for regression.
- **Review Alignment**: Phase 7 tasks (T035-T043) directly address the specific concerns raised by Alan Turing (static vs. adaptive), David Krakauer (biological context), Stephen Wolfram (rule space exploration), and Geoffrey West (scaling of $\epsilon$ with density), including the mandatory Reference-Validator run (T043).