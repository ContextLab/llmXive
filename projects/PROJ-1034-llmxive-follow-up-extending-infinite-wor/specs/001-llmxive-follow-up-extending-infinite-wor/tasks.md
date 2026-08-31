# Tasks: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

- [ ] T001 Create project structure: directories `src/sim`, `src/analysis`, `src/data`, `src/cli`, `src/tests`, `data/raw`, `data/processed`, `docs`, `state`. (Dep: None)
- [X] T002 Initialize Python project with `requirements.txt` containing pinned versions: `numpy>=1.24`, `pandas>=2.0`, `scikit-learn>=1.3`, `statsmodels>=0.14`, `huggingface_hub>=0.19`, `torch==2.1.0+cpu`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`. (Dep: T001)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools with `pyproject.toml` settings. (Dep: T001)
- [X] T010b [P] Create skeleton file `src/analysis/novelty.py` with placeholder functions for semantic novelty quantification (Required for T035). (Dep: T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
**⚠️ ORDERING**: T007 (Data Models) MUST complete before T004, T005, and T006.

- [X] T007 Create base data models: `SimulationRun`, `MetricRecord`, `ParameterGrid` in `src/data_models.py`. (Dep: T001)
- [X] T004 [US1] Implement `src/sim/eco_director.py` with schema definition, update loop, and runtime parameter injection mechanism (CLI args + YAML loader) to satisfy FR-001's "without code recompilation" constraint. (Dep: T007)
- [X] T005 [P] [US1] Implement `src/sim/neural_baseline.py` (Throttled M Parameter Proxy) with CPU-only constraints. (Dep: T007)
- [X] T006 [P] [US1] Implement `src/sim/physics_oracle.py` (Stochastic Physics Sandbox) to validate external constraints (FR-008) and explicitly log specific physics constraint violations (e.g., mass/energy deviation values) into `MetricRecord`. (Dep: T007)
- [X] T006b [US1] Implement internal memory/time limit **detection and signal emission** within the CA engine/simulation loop in `src/sim/eco_director.py` to satisfy FR-003's strict enforcement requirement. This task MUST call the termination handler defined in T008b when limits are exceeded. (Dep: T004, T008b)
- [X] T008a [P] [US1] Create CLI entry point `src/cli/run_simulation.py` with argument parsing for `--config`, `--steps`, `--seed`. (Dep: T004, T005, T006)
- [X] T008b [P] [US1] Implement **Graceful Termination Handler** in `src/cli/run_simulation.py` (or `src/sim/termination_handler.py`) that performs the actual mid-simulation shutdown, saves partial state if applicable, logs the specific 'Out of Bounds' reason (e.g., 'Memory Explosion'), and exits cleanly without crashing the CI job. (Dep: T001)
- [X] T008c [P] [US1] Implement timeout enforcement logic in `src/cli/run_simulation.py` to handle time-bound baseline runs (Edge Case 2), outputting a structured JSON status log with a 'Time-Bound' flag. (Dep: T006b)
- [X] T009 [P] Configure deterministic random seeds in `src/config.py` and ensure reproducibility across runs. (Dep: T001)
- [X] T010 [P] Implement logging infrastructure: Create `src/logging_config.py` that configures a rotating file handler writing JSON to `logs/simulation.log`; verify log file contains `step_latency` key. (Dep: T001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-Constrained Simulation Baseline (Priority: P1) 🎯 MVP

**Goal**: Run the comparative simulation between the neural baseline and the CA Eco-Director on a standard GitHub Actions free-tier runner to establish performance bounds.

**Independent Test**: The system can be tested by running the simulation script for a fixed duration on the CI runner and verifying that the job completes without OOM errors or timeout, while logging latency per step. The test must also verify the 'Power-Limited' flag and fallback dataset behavior if the primary dataset is unavailable.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011a [P] [US1] Unit test for parameter schema validation in `src/sim/eco_director.py`. (Dep: T004)
- [X] T011b [P] [US1] Unit test for eco_director.py state transitions in `tests/unit/test_eco_director.py`. (Dep: T004)
- [X] T012 [P] [US1] Integration test for simulation pipeline memory limits in `tests/integration/test_simulation_pipeline.py`. (Dep: T008b)

### Implementation for User Story 1

- [X] T013 [US1] Implement throttling logic in `src/sim/neural_baseline.py` to ensure it runs within 6h CPU limits. (Dep: T005)
- [ ] T018 [US1] Implement strict dataset loader in `src/data/loader.py` that raises an explicit `DataUnavailableError` on fetch failure. **Do NOT implement synthetic fallback here**; the fallback is handled by T015b upon catching this error. (Dep: T008a)
- [X] T015b [US1] Implement logic to flag results as 'Power-Limited' and fallback to a smaller synthetic dataset. This task MUST catch `DataUnavailableError` from T018 and trigger `src/data/synthetic_fallback.py` to generate a dataset with [deferred] steps, flagging the run as 'Power-Limited' in the JSON status log. **Note**: This triggers on data unavailability regardless of timeout status. If T008c also flags 'Time-Bound', both flags may be present. (Dep: T018, T008c)
- [ ] T016 [US1] Execute a minimum of 10,000 time-steps: Run `src/cli/run_simulation.py --steps 10000 --config default.yaml`. **Verification Step**: If the step count is not reached by the 6-hour timeout, verify that `data/raw/baseline_partial.parquet` exists and the run is flagged as 'Time-Bound Baseline'. (Dep: T013, T018, T008c)
- [ ] T017 [US1] Implement validation script `src/analysis/validate_metrics.py` that scans `data/raw/*.parquet` for NaN values and exits with code 1 if found. (Dep: T016)

---

## Phase 4: User Story 2 - Sweep Algorithmic Parameters for Coherence Analysis (Priority: P2)

**Goal**: Systematically vary CA parameters to identify which algorithmic properties correlate with high coherence/diversity scores.

**Independent Test**: The system can be tested by running a single parameter sweep and verifying that the output dataset contains distinct entries for each configuration with corresponding metric scores. The test must also verify that the model adjustment/fallback strategy is triggered correctly if the lag-1 autocorrelation check fails.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US2] Unit test for parameter grid generation in `tests/unit/test_param_grid.py`. (Dep: T023)
- [ ] T019 [P] [US2] Integration test for LMM data preparation in `tests/integration/test_lmm_data_prep.py`. (Dep: T026)

### Implementation for User Story 2

- [ ] T021a [US2] Implement `src/analysis/acf_validator.py` to compute ACF and check lag-1 autocorrelation < 0.1 (FR-007). (Dep: T016)
- [ ] T021b [US2] Implement model adjustment logic in `src/analysis/lmm_runner.py` to **switch to robust standard errors** if lag-1 autocorrelation >= 0.1. This is a mandatory adjustment required by FR-007, not just a diagnostic flag. (Dep: T021a)
- [ ] T023 [US2] Implement parameter sweep orchestration in `src/cli/run_simulation.py` including grid generation, runner wrapper, and data aggregation. (Dep: T004, T005, T006)
- [ ] T026 [US2] Run [deferred] time-steps per configuration: Read `target_steps` from `config.yaml` (default 10000); Execute parameter sweep; record metrics to `data/processed/`. (Dep: T023)
- [ ] T025 [US2] Ensure `data/raw/` logs are saved for every parameter configuration: Add serialization logic to `src/sim/eco_director.py` to write state snapshots to `data/raw/{run_id}.parquet` during simulation loop. (Dep: T023)
- [ ] T020 [US2] Implement `src/analysis/lmm_runner.py` to perform Linear Mixed-Effects Model analysis (FR-004) using `statsmodels` with formula `coherence ~ param + (1|time_step)` to treat 'time-step' as a random effect. **Must use configuration adjusted by T032b if partial correlation fails.** (Dep: T026, T025, T032b, T021b)
- [ ] T022 [US2] Implement `src/analysis/rf_runner.py` for Random Forest feature importance analysis (FR-009). (Dep: T026)
- [ ] T024 [US2] Implement logic to exclude unstable configurations (state explosion) from statistical analysis (Edge Case 1). (Dep: T026)
- [ ] T027 [US2] Implement streaming data processing in `src/analysis/lmm_runner.py` to handle large simulation logs via chunked iteration, ensuring memory usage stays within 7GB limits for long-horizon runs. (Dep: T020)
- [ ] T032 [US2] Implement partial correlation analysis in `src/analysis/partial_corr.py`: Calculate partial correlation between 'memory depth' and 'diversity' (controlling for other factors). **Output**: A configuration update file for T032b. **Note**: This runs before T020 to allow configuration adjustment. (Dep: T026)
- [ ] T032b [US2] Implement logic to act on partial correlation results: If coefficient >= 0.05, update the LMM configuration (e.g., add random effects or flags) and flag the run as 'Invalid' in the final report generation (T033). **This task must complete before T020 runs.** (Dep: T032)

---

## Phase 5: User Story 3 - Validate Statistical Parity and Latency Trade-offs (Priority: P3)

**Goal**: Confirm if optimal CA configuration achieves statistical parity with neural baseline and meets ≥90% latency reduction target.

**Independent Test**: The system can be tested by comparing aggregate metrics and verifying the latency reduction calculation is explicitly reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T041 [P] [US3] Unit test for latency reduction calculation in `tests/unit/test_latency_calc.py`. (Dep: T031)
- [ ] T042 [P] [US3] Integration test for sensitivity analysis report in `tests/integration/test_sensitivity_report.py`. (Dep: T029)

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/sensitivity.py` to sweep coherence decision cutoffs at specific thresholds **{0.01, 0.05, 0.1}**, calculate inconsistency rates, and generate `src/analysis/reports/sensitivity_report.md`. **Note**: This task is independent of LMM success (T020) and runs on the raw metric distributions. (Dep: T026)
- [ ] T030 [US3] Implement statistical comparison logic to calculate p-values for coherence/diversity parity (SC-002). (Dep: T020)
- [ ] T031 [US3] Implement latency reduction calculator to verify ≥90% target (SC-001, FR-005). (Dep: T013, T016, T023)
- [ ] T033 [US3] Generate final report: Generate `docs/report.md` containing the comparison table, p-values from `data/processed/summary.csv`, and the 'Invalid' flag from T032b if applicable. (Dep: T030, T031, T032b)
- [ ] T034 [US3] Validate results against `physics_oracle.schema.yaml` to ensure non-tautological coherence (FR-008) and verify that specific physics constraint violation values (e.g., mass/energy deviation) are recorded in `MetricRecord` as per T006. (Dep: T033)
- [ ] T035 [US3] Implement semantic novelty quantification in `src/analysis/novelty.py` by comparing event entropy distributions between CA and Neural runs, ensuring the metric is not derived solely from the CA rules. (Dep: T010b)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `quickstart.md`. (Dep: T033)
- [ ] T037 Code cleanup and refactoring for modularity. (Dep: T033)
- [ ] T038 Performance optimization for simulation loop (vectorization where possible). (Dep: T016)
- [ ] T039 [P] Additional unit tests for edge cases in `tests/unit/`. (Dep: T033)
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility. (Dep: T036)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Ordering**: T007 (Data Models) MUST complete before T004, T005, and T006.
 - T004 must be completed before T006b.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `eco_director` and `physics_oracle` implementation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T005, T006, T008a, T008b, T008c, T009, T010 in Foundational can run in parallel (after T007 and T004/T006b sequence)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T020 (LMM) and T032 (Partial Correlation) are explicitly parallel in execution but T020 depends on T032b (the adjustment). T032 runs before T020.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for parameter schema validation in src/sim/eco_director.py"
Task: "Unit test for eco_director.py state transitions in tests/unit/test_eco_director.py"
Task: "Integration test for simulation pipeline memory limits in tests/integration/test_simulation_pipeline.py"

# Launch all implementation for User Story 1 together:
Task: "Implement throttling logic in src/sim/neural_baseline.py"
Task: "Implement memory monitoring in src/cli/run_simulation.py"
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
- **Unique IDs**: T018 (Phase 3) is Strict Loader; T043 (Phase 4) is Unit Test. T027 (Phase 4) is Streaming; T042 (Phase 5) is Sensitivity Test.
- **Critical Ordering Note**: T032 (Partial Correlation) runs before T020 (LMM). T032b (Adjustment) runs after T032 and before T020. T020 depends on T032b to ensure correct configuration.