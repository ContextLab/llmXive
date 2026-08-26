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
- [X] T008 [US1, US2, US3] **Setup pytest configuration and contract testing framework**:
 1. Create `tests/conftest.py` with a global `seed` fixture that enforces a random seed for all tests.
 2. Update `pytest.ini` to include `[pytest]` section with `addopts = --strict-markers` and `markers = seed`.
 3. Create `tests/contract/__init__.py` and `tests/contract/test_schema_validation.py` to validate JSON data against schemas in `code/contracts/`.
 4. Implement an assertion in `conftest.py` that fails the test suite if a random seed is not explicitly set or if non-deterministic operations are detected.
 **Deliverable**: A runnable `pytest tests/contract/` that validates JSON data against the schemas in `code/contracts/`. (NOT [P] due to T007 dependency).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Synthetic Network Ensembles (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible ensembles of Erdős-Rényi, Barabási-Albert, and Watts-Strogatz networks ($N=500$) with distinct topological features.

**Independent Test**: Generate one instance of each topology, compute metrics, and verify they match theoretical expectations within 5% tolerance.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Unit test for Barabási-Albert power-law degree distribution in `tests/unit/test_network_gen.py`
- [X] T010 [P] [US1] Unit test for Watts-Strogatz clustering coefficient vs. rewiring probability in `tests/unit/test_network_gen.py`
- [X] T011 [P] [US1] Memory constraint test: Verify 50 networks of $N=500$ fit within 7GB RAM in `tests/unit/test_memory_limits.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/generate_networks.py` to generate multiple independent instances per topology type with fixed random seeds using `numpy.random` explicitly wired to the global seed fixture defined in `tests/conftest.py` (FR-001)
- [X] T013 [US1] **Calculate and store structural metrics**: Implement function `calculate_metrics(graph)` in `code/generate_networks.py` to compute assortativity, average path length, and clustering coefficient for each generated network. Save results to `data/raw/networks/metrics_{topology}_{seed}.json` with the following schema: `{"topology": str, "seed": int, "assortativity": float, "avg_path_length": float, "clustering_coeff": float, "node_count": int, "edge_count": int}`. (FR-001, US-1)
- [X] T014 [US1] **Serialization and Checksums**: Implement function `save_network(graph, path)` in `code/generate_networks.py` to save network instances (as edge lists or pickled graphs) and the metrics JSON files to `data/raw/networks/`. Generate SHA-256 checksums for all files and update `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml`. (FR-001)
- [X] T015 [US1] **Connectivity Validation**: Implement function `validate_connectivity(graph)` in `code/generate_networks.py` to verify if generated networks are connected. If disconnected, either re-generate with a different seed or explicitly flag the instance in the JSON metadata with `is_connected: false` and `largest_component_size: int`. (FR-001)
- [X] T016a [P] [US3] **Data Schema Prep**: Implement the data structure preparation for regression analysis in `code/contracts/regression_schema.py`. This task defines the schema for `data/processed/regression_data.json` (mapping structural metrics to simulation IDs) but does NOT populate it with gamma values yet (FR-006, US-3 dependency).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Bounded Confidence Simulations (Priority: P2)

**Goal**: Execute discrete-time Hegselmann-Krause simulations on generated networks, sweeping $\epsilon$ across a range of confidence thresholds and measuring convergence time.

**Independent Test**: Run a single simulation on $N=50$ with fixed $\epsilon$ and verify convergence to stable state ($<10^{-4}$ change) within reasonable iterations.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for HK update rule convergence on a small static network in `tests/unit/test_hk_logic.py`
- [X] T018 [P] [US2] Unit test for non-convergence handling (max iteration limit) in `tests/unit/test_hk_logic.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/simulate_hk.py` with vectorized NumPy updates for the discrete-time Hegselmann-Krause rule (FR-002, FR-003). **Dependency**: This task consumes network instances saved by T014.
- [X] T020 [US2] Implement convergence detection logic: stop when max opinion change $< 10^{-4}$ or max iterations reached (FR-004, FR-007)
- [X] T021 [US2] **Batch Execution Engine**: Implement logic to sweep $\epsilon$ across a representative range with a fixed step size and execute a sufficient number of independent seeds per configuration. Output results to `data/raw/simulations/` with a CSV or HDF5 format. (FR-003, SC-003)
- [X] T022 [US2] Add logic to handle non-convergent runs: flag as "non-convergent" in the `status` column of the CSV output in `data/raw/simulations/`
- [X] T023 [US2] **Write Raw Simulation Results**: Save raw simulation results to `data/raw/simulations/run_{topology}_{epsilon}_{seed}.h5`. **Format**: Use HDF5 format with a dataset `opinions` of shape `(n_iterations, n_agents)` storing the full temporal trace of opinion vectors, and a dataset `metadata` containing `epsilon`, `seed`, `topology`, `convergence_time`, and `status`. (FR-004, FR-008, FR-003)
- [X] T024 [US2] Integration test for batch execution of multiple configurations (multiple topologies × variable epsilons) verifying output format in `tests/integration/test_simulation_batch.py`
- [X] T025 [US2] Implement performance optimization and runtime monitoring in `code/simulate_hk.py` (e.g., parallel processing with `multiprocessing`, progress tracking) to Ensure the full simulation suite completes within 5 hours (SC-003). **Reproducibility Constraint**: Parallel workers MUST use a deterministic seed distribution strategy (e.g., `worker_seed = base_seed + worker_id`) to prevent race conditions and ensure floating-point reproducibility.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Scaling Laws and Structural Correlations (Priority: P3)

**Goal**: Fit power-law models to convergence time data, extract $\gamma$, and regress against structural metrics.

**Independent Test**: Provide synthetic data, verify regression identifies known correlation and power-law fit $R^2 > 0.8$.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for power-law fitting with bootstrapping error estimation in `tests/unit/test_scaling_fit.py`
- [X] T027 [P] [US3] Unit test for multiple linear regression with categorical topology variable in `tests/unit/test_regression.py`

### Implementation for User Story 3

- [X] T028 [US3] **Detect $\epsilon_c$**: Implement `code/analyze_scaling.py` with a grid-search algorithm to detect $\epsilon_c$ for each network instance. Test candidates in a low-to-moderate range with fine-grained steps. Select the $\epsilon_c$ that minimizes the Residual Sum of Squares (RSS) for the power-law fit. Output results to `data/processed/epsilon_c_values.json`. (FR-005, Plan Clarification #1)
- [X] T029 [US3] **Power-Law Fitting**: Implement power-law fitting $T = A(\epsilon - \epsilon_c)^{-\gamma}$ restricted to the critical regime $\epsilon \in [\epsilon_c + 0.05, 0.50]$. Use `delta = 0.05` as the offset. Extract $\gamma$ and $R^2$. Enforce $R^ \ge \text{a high threshold}$ as a pass/fail condition. (FR-005)
- [X] T030 [US3] Implement Model A: Multiple linear regression to correlate $\gamma$ with Topology type (categorical variable only), excluding structural metrics to avoid multicollinearity (FR-006, Plan Clarification #3)
- [X] T030b [US3] Implement Model B: Multiple linear regression to correlate $\gamma$ with Assortativity and PathLength *within* each topology group, excluding Topology as a variable (FR-006, Plan Clarification #3)
- [X] T031 [US3] Implement visualization module to generate: (1) $\gamma$ vs. assortativity scatter with regression line, (2) Convergence time vs. $\epsilon$ on log-log scale
- [X] T032 [US3] Save processed results (ScalingResult, RegressionResult) to `data/processed/` with checksums
- [X] T032b [US3] **Data Population for Regression**: Populate `data/processed/regression_data.json` by joining the extracted $\gamma$ values (from T029), $\epsilon_c$ values (from T028), and structural metrics (from T013). **Schema**: `{"topology": str, "seed": int, "gamma": float, "epsilon_c": float, "assortativity": float, "path_length": float, "clustering_coeff": float}`. (FR-006, US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis (FR-008)

**Goal**: Verify robustness of results to convergence threshold as mandated by FR-008.

**Independent Test**: Sweep convergence threshold $10^{-3}$ to $10^{-5}$ and verify $\gamma$ variation < 5%.

### Implementation for Sensitivity Analysis

- [X] T033 [US3] **Re-run Simulations for Sensitivity**: Implement `code/sensitivity_analysis.py` to re-run `simulate_hk.py` (from T019) with convergence thresholds $\delta \in [10^{-3}, 10^{-5}]$ for a subset of configurations (e.g., 5 seeds per topology). **Must re-execute the simulation loop** to measure the variation in convergence time (iteration count) for each threshold. Output a CSV report `data/processed/sensitivity_report.csv` with columns `threshold, gamma_mean, gamma_std`. (FR-008)
- [X] T034 [US3] Generate report comparing $\gamma$ variation across the sensitivity sweep; flag if variation > 5%

**Checkpoint**: Sensitivity and robustness checks complete.

---

## Phase 7: Research Review Resolution (Addressing Prior Reviews)

**Goal**: Explicitly address concerns raised by Alan Turing (adaptive thresholds), David Krakauer (biological signal detection context), Stephen Wolfram (rule-space exploration), and Geoffrey West (scaling of $\epsilon$ with density) without violating the static HK constraint of the current spec.

**Independent Test**: Documentation and code comments clearly distinguish between the static baseline and the proposed adaptive variants; a "Rule Space Explorer" script runs variations of the HK update rule; a scaling analysis script tests $\epsilon$ vs. network density.

### Implementation for Research Review Resolution

- [X] T035 [P] [Review] **Rule Space Explorer (Documentation)**: Update `docs/methodology.md` to include a section "Rule Space Exploration" discussing the theoretical implications of alternative update rules (e.g., weighted averaging, median-based updates) and contrasting them with the static HK model. **Note**: This is a documentation task only; no code implementation is required. (Response to Stephen Wolfram)
- [X] T036 [P] [Review] **Adaptive Threshold Prototype (Documentation)**: Update `docs/methodology.md` to include a section "Adaptive Thresholds: Future Work" discussing the theoretical basis for adaptive $\epsilon$ and contrasting it with the static constraint of the current spec. **Note**: This is a documentation task only; no code implementation is required. (Response to Alan Turing)
- [X] T037 [P] [Review] Update `docs/methodology.md` to include a section "Biological Imperative and Signal Detection" discussing the evolutionary context of bounded confidence as a noise-filtering mechanism vs. error-calcifying mechanism (Response to David Krakauer)
- [X] T038 [P] [Review] Update `docs/methodology.md` to include a section "Historical Lineage and Micro-Rules" explicitly contrasting Deffuant (convergence) vs. Hegselmann & Krause (fragmentation) outcomes based on the specific micro-rule implemented (Response to David Krakauer)
- [X] T039 [P] [Review] Add a validation task in `tests/unit/test_review_alignment.py` to ensure the codebase explicitly distinguishes between "static cognitive limitation" (current model) and "adaptive learning" (future work) in all docstrings and comments (Response to Alan Turing)
- [X] T040 [P] [Review] **Rule Space Plot (Documentation)**: Update `docs/methodology.md` to include a conceptual figure description or reference to literature showing how different update rules affect the phase transition point. **Note**: This is a documentation task only. (Response to Stephen Wolfram)
- [X] T041 [P] [Review] Update `docs/methodology.md` to include a section "Scaling of $\epsilon$ with Density" discussing the hypothesis that $\epsilon$ scales with network density and the potential for phase transitions at critical network sizes (Response to Geoffrey West)
- [X] T042 [P] [Review] Update `docs/methodology.md` to include a section "Topological Constraints and Scaling" discussing the implications of degree heterogeneity (power-law vs. homogeneous) on the critical threshold and the potential for phase transitions at critical network sizes (Response to Geoffrey West)
- [X] T043 [Review] Run the Reference-Validator Agent on all new citations introduced in `docs/methodology.md` and `code/explorers/` (T035-T042) to satisfy Constitution Principle II before transitioning to `research_accepted`. **Dependency**: Must follow T035-T042 completion. **NOT [P]**. <!-- ATOMIZE: requested -->

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
- All Foundational tasks marked [P] can run in parallel (except T008 which depends on T007)
- Once Foundational phase completes, US1 can start immediately
- US2 can start as soon as US1 produces the first batch of networks (if pipelined)
- All tests for a user story marked [P] can run in parallel
- Phase 6 tasks (T033-T034) can run in parallel with US3 analysis if US2 code is ready.
- Phase 7 tasks (T035-T042) can run in parallel with US3 and Phase 6. T043 must follow T035-T042.

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
- **Sensitivity**: Task T033 explicitly re-runs simulations with varied thresholds to satisfy FR-008, ensuring valid sensitivity analysis within runtime limits.
- **Validation**: Task T016a/T032b explicitly validates Constitution Principle VI regarding topological divergence by preparing and populating data for regression.
- **Review Alignment**: Phase 7 tasks (T035-T043) directly address the specific concerns raised by Alan Turing (static vs. adaptive), David Krakauer (biological context), Stephen Wolfram (rule space exploration), and Geoffrey West (scaling of $\epsilon$ with density), including the mandatory Reference-Validator run (T043).