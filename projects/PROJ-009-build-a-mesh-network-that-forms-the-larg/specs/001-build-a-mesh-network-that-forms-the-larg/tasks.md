# Tasks: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Input**: Design documents from `/specs/001-mesh-supercomputer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to satisfy the "Independent Test" acceptance criteria in the Spec.

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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/orchestrator`, `code/analysis`, `code/simulation`, `data/raw`, `data/processed`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `paramiko`, `scikit-learn`, `pandas`, `pygam`, `statsmodels`, `pytest`, `pyyaml`, `numpy`, `simpy`)
- [ ] T003 [P] Configure linting (ruff/black) and formatting tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base data models: `PhysicalNode`, `TaskChunk`, `ExecutionRun` in `code/orchestrator/models.py` with Pydantic validation
- [X] T005 [P] Implement configuration manager in `code/orchestrator/config.py` to load YAML configs for node lists, granularity settings, and network parameters
- [X] T006 [P] Setup logging infrastructure in `code/orchestrator/logger.py` to output structured JSON logs to `data/raw/` with run IDs
- [X] T007 Implement SSH connection pool manager in `code/orchestrator/node_manager.py` (using `paramiko`) with heartbeat logic and timeout handling
- [ ] T008 Create schema validation contracts in `contracts/` (YAML schemas for ExecutionRun and RegressionModel) and unit tests in `tests/contract/`
- [X] T009 Implement the "Hard Timeout" wrapper in `code/orchestrator/runner.py` to enforce the 6-hour CI limit (FR-007)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Physical Testbed Orchestration & Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Deploy a dynamic scheduler to a physical mesh, inject impairments, and collect raw execution logs (wall-clock, packets, CPU).

**Independent Test**: Launch a single benchmark job across multiple physical nodes with injected latency; verify distribution, log capture (`tcpdump`/`mpstat`), and CSV output matching `PhysicalNode`/`TaskChunk` schema.

### Tests for User Story 1 (MANDATORY)

- [X] T010 [P] [US1] Contract test for ExecutionRun schema validation in `tests/contract/test_execution_run.py`
- [X] T011 [P] [US1] Integration test for SSH heartbeat and failure detection in `tests/integration/test_node_manager.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement the Monte Carlo Integration benchmark worker script in `code/orchestrator/workers/monte_carlo.py` (must be runnable via CLI)
- [X] T013 [P] [US1] Implement the Instrumentor in `code/orchestrator/instrumentor.py` to remotely execute `tcpdump` (packet counts) and `mpstat` (CPU utilization) on target nodes via SSH
- [ ] T019 [P] [US1] Implement the Network Metrics Collector in `code/orchestrator/network_metrics.py` to measure bandwidth (using `iperf3`) and SNR (using `iwlist`/`iwgetid`) on target nodes via SSH. **Deliverable**: Write `data/raw/network_metrics.csv` with columns `node_id`, `bandwidth_Mbps`, `snr_db`. Verify file exists and contains non-null values. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement the Orchestrator logic in `code/orchestrator/scheduler.py` to distribute `TaskChunk`s to `PhysicalNode`s based on availability
- [X] T015 [US1] Implement network impairment injection in `code/orchestrator/network_impairments.py` (using `tc`/`netem` commands via SSH) for latency and packet loss
- [X] T024 [US1] [Depends: T013, T015] Implement the "Asynchronous Timeout" logic in `code/orchestrator/scheduler.py` (2x median task time) to handle stragglers without stalling the barrier
- [X] T043 [US1] [Depends: T013, T015] Implement the "Network Saturation" detector in `code/orchestrator/network_impairments.py` to analyze `tcpdump` output in real-time; if packet loss > 20%, abort the run and log `network_saturation` error code. **Verification**: Verify exit code 1 and log entry contains `network_saturation` (Edge Case handling).
- [X] T016 [US1] [Depends: T013, T019, T043] Implement the Data Aggregator in `code/orchestrator/data_aggregator.py` to parse raw logs from T013 and T019, and write `data/raw/execution_logs.csv` with columns: `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `status`, `hardware_spec` (JSON string), `current_latency`, `bandwidth_Mbps`, `snr_db`. Ensure T043 has passed before writing final logs.
- [X] T017 [US1] Implement the "Straggler & Dropout" handler in `code/orchestrator/scheduler.py` to detect heartbeat loss, re-assign tasks, and log re-assignment events with timestamps

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (requires physical hardware for full validation, mocked for CI)

---

## Phase 4: User Story 2 - Dynamic Scheduler & Granularity Parameter Sweep (Priority: P2)

**Goal**: Execute a parameter sweep varying chunk sizes, node counts, and network conditions to generate the dataset for identifying the "sweet spot".

**Independent Test**: Run three campaigns (fine/medium/coarse) on identical nodes; verify output contains distinct throughput measurements and coordination overhead ratios.

### Tests for User Story 2 (MANDATORY)

- [X] T018 [P] [US2] Contract test for Parameter Sweep configuration in `tests/contract/test_sweep_config.py`
- [X] T020 [P] [US2] Integration test for Granularity parameter variation in `tests/integration/test_sweep_runner.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement the Parameter Sweep Runner in `code/orchestrator/sweep_runner.py` to iterate over configurations (granularity: fine/medium/coarse, nodes: a small to moderate number, latency: low to high)
- [X] T022 [US2] Implement the Coordination Overhead Calculator in `code/analysis/overhead.py` to compute `handshake_time / total_time` for every task execution
- [ ] T023 [US2] Implement the "Straggler Effect" analyzer in `code/analysis/straggler.py` to calculate variance in completion times per granularity setting
- [ ] T048 [US2] [Depends: T021] Implement the Data Exporter in `code/orchestrator/exporter.py` to write aggregated results to `data/processed/sweep_results.json` containing `node_count`, `throughput_tasks_per_sec`, `coordination_overhead_ratio`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Theoretical Validation (Priority: P3)

**Goal**: Execute multiple linear regression/GAMs and ANOVA on physical data; validate against Ong & Motani (2007) theoretical bounds.

**Independent Test**: Feed physical logs into analysis module; verify output of regression model (R², p-values) and theoretical bound deviation metric.

### Tests for User Story 3 (MANDATORY)

- [ ] T025 [P] [US3] Contract test for RegressionModel schema in `tests/contract/test_regression_model.py`
- [ ] T026 [P] [US3] Unit test for Ong & Motani bound calculation in `tests/unit/test_theoretical_bound.py`

### Implementation for User Story 3

- [ ] T027 [US3] [Depends: T016, T023] Implement the Data Preprocessor in `code/analysis/preprocessor.py` to merge raw logs. **Logic**: If a critical variable is missing, flag the run as WARN and exclude from regression. If a non-critical variable is missing, proceed with reduced model complexity. Output `data/processed/valid_runs.csv` and update `state/valid_run_ids.json` (SC-006 compliance).
- [ ] T028 [US3] [Depends: T027] Implement the Multiple Linear Regression Module in `code/analysis/regression.py` using `statsmodels` (OLS) to model linear relationships. Output `data/processed/linear_model.json` (coefficients, p-values, R²) to satisfy FR-005.
- [ ] T046 [US3] [Depends: T027] Implement the GAM Regression Module in `code/analysis/gam_regression.py` using `pygam` to model non-linear interactions between heterogeneity and granularity. Output `data/processed/gam_model.json` (coefficients, p-values, R²).
- [ ] T029 [US3] [Depends: T027] Implement the ANOVA Module in `code/analysis/anova.py` using `statsmodels` to test significance of granularity differences (p < 0.05)
- [ ] T030 [US3] [Depends: T027, T019] Implement the Theoretical Bound Validator in `code/analysis/theoretical_bound.py` using Ong & Motani (2007) formula parameterized by measured bandwidth/SNR from T019 (consumed via T027); calculate deviation and flag if empirical > theoretical
- [ ] T045 [US3] [Depends: T019] Implement the Bandwidth/SNR Ingestion Validator in `code/analysis/ingestion.py` to explicitly verify that `data/raw/network_metrics.csv` from T019 is correctly consumed and mapped to the `valid_runs.csv` columns required for T030 (FR-006 coverage).
- [ ] T036 [US3] [Depends: T028, T029, T030, T046] Implement the Final Report Generator in `code/analysis/report.py` to aggregate all metrics into `data/processed/final_analysis.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Simulation & Validation (Constitution Principle VI)

**Goal**: Build and calibrate a Discrete-Event Simulation (DES) model against the physical "Golden Dataset". *Note: DES scope limited to 'embarrassingly parallel' event modeling to align with Assumptions; required by Constitution Principle VI.*

**Independent Test**: Run DES with calibrated parameters; verify output matches physical throughput curve within a defined tolerance.

### Implementation for Phase 6

- [ ] T047 [US3] [Constitution VI] Implement the Discrete-Event Simulation (DES) Framework in `code/simulation/des_model.py` as a mandatory research requirement derived from Constitution Principle VI. This task defines the core simulation engine.
- [ ] T031 [US3] [Depends: T021, T024] Implement the Golden Dataset Generation Script in `code/simulation/golden_dataset_runner.py` to execute a small-scale physical deployment (a limited number of nodes, medium granularity) and output `data/raw/golden_dataset.csv`.
- [ ] T032 [US3] [Depends: T047, T031] Implement the DES Event Definition in `code/simulation/des_model.py` using `simpy` (events: task arrival, compute, network transfer, handshake). *NOT parallel-safe: must align with finalized data schema.*
- [ ] T033 [US3] [Depends: T032] Implement the Parameter Tuning Script in `code/simulation/calibrator.py` to tune DES parameters (service rates, network delays) using `scipy.optimize` to minimize error against T031 Golden Dataset.
- [ ] T034 [US3] [Depends: T033] Implement the Validation Script in `code/simulation/validator.py` to compare DES output vs. Physical Golden Dataset and generate `data/processed/simulation_validation.json`.
- [ ] T035 [US3] [Depends: T034] Implement the Extrapolation Script in `code/simulation/extrapolator.py` to run DES on larger node counts using calibrated parameters.

**Checkpoint**: Simulation model validated against physical reality

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates: Write `quickstart.md` (physical testbed setup) and `README.md` (analysis pipeline) with specific sections for installation, usage, and data interpretation.
- [ ] T038 [P] Code cleanup and refactoring of `code/orchestrator` modules to reduce cyclomatic complexity.
- [ ] T039 [P] Performance optimization: Reduce SSH connection latency via connection pooling improvements.
- [ ] T040 [P] Additional unit tests for edge cases (e.g., network saturation, OOM signals) in `tests/unit/`.
- [ ] T041 [P] Security hardening: Ensure SSH keys are handled securely and no credentials are hardcoded.
- [ ] T042 [P] Run `quickstart.md` validation to ensure end-to-end feasibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be completed first to generate data for US3
 - US2 (P2) depends on US1 infrastructure (scheduler/instrumentor) but can run in parallel with US3 analysis scripts
 - US3 (P3) depends on data generation from US1/US2
- **Simulation (Phase 6)**: Depends on US3 (requires "Golden Dataset" from physical runs)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must complete before US3 analysis.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses US1 scheduler; generates the bulk dataset.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on output of US1/US2** (raw logs) to run regression.
- **Simulation (Phase 6)**: **Depends on US3** (requires validated physical data).

### Within Each User Story

- Tests (mandatory) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 (Orchestrator) and US3 (Analysis Scripts) can be developed in parallel by different team members (US3 can use mocked data initially)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for ExecutionRun schema validation in tests/contract/test_execution_run.py"
Task: "Integration test for SSH heartbeat and failure detection in tests/integration/test_node_manager.py"

# Launch all models/infrastructure for User Story 1 together:
Task: "Implement the Instrumentor in code/orchestrator/instrumentor.py"
Task: "Implement the Data Aggregator in code/orchestrator/data_aggregator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Orchestration + Data Collection)
4. **STOP and VALIDATE**: Run a small physical test (3-5 nodes) to verify `execution_logs.csv` generation.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (Physical Testbed) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (Parameter Sweep) → Deploy/Demo
4. Add User Story 3 → Test independently (Regression/Validation) → Deploy/Demo
5. Add Simulation (Phase 6) → Calibrate against Physical Data → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Orchestrator/SSH/Instrumentation)
 - Developer B: User Story 3 (Analysis/Regression/Validation - using mocked data initially)
3. Once US1 generates real data:
 - Developer B switches to real data for US3
 - Developer C starts User Story 2 (Sweep logic)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: Ensure all raw logs in `data/raw/` are never modified; derived stats go to `data/processed/`.
- **Compute Constraints**: Ensure analysis scripts (US3) are optimized for the 2-core, 7GB RAM CI limit (use streaming for large logs if needed).
- **Edge Case Handling**: Explicitly implemented in T043 (Network Saturation) and T017 (Straggler/Dropout) to prevent data corruption and ensure robust execution.
- **Missing Variable Handling**: Explicitly implemented in T027 to ensure runs with non-critical missing data are not discarded, adhering to SC-006.
- **Simulation Requirement**: Phase 6 tasks (T047, T031-T035) are mandatory per Constitution Principle VI, distinct from the Spec's FR list but required for the research project's validity.