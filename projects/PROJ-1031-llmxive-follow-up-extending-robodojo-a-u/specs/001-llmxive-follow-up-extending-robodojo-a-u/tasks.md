# Tasks: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

**Input**: Design documents from `/specs/001-symbolic-dojo-extend/`
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

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `code/src/__init__.py`
- [X] T001b Create `code/tests/__init__.py`
- [ ] T001c Create `code/data/raw/`, `code/data/interim/`, `code/data/processed/`, `code/data/final/` directories
- [X] T001d Initialize Python 3.11 virtual environment and create `code/requirements.txt` (torch-cpu, scikit-learn, networkx, pandas, datasets, opencv-python, pyyaml)
- [ ] T001e Create `code/src/config.py` with paths, seeds, and RoboDojo dataset commit hash `v.1`
- [X] T001f Create `code/src/data_loader.py`
- [X] T001g Create `code/src/vision_encoder.py`
- [X] T001h Create `code/src/state_mapper.py`
- [X] T001i Create `code/src/planner.py`
- [X] T001j Create `code/src/controller_adapter.py`
- [X] T001k Create `code/src/oracle_executor.py`
- [X] T001l Create `code/src/metrics_logger.py`
- [X] T001m Create `code/src/stats_analysis.py`
- [X] T001n Create `code/src/executor.py`
- [ ] T001o Create `code/tests/` directory structure
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement `code/src/data_loader.py` to stream RoboDojo parquet files from HuggingFace without loading full dataset into RAM
 - **Implementation**: Use `datasets.load_dataset(..., streaming=True)` to iterate over the RoboDojo dataset shards. Do NOT load the full dataset into memory. Accumulate statistics online or process frame-by-frame. Explicitly raise an error if the stream fails to open a verified real source; do NOT fall back to synthetic data. Use dataset ID `RoboDojo/RoboDojo-v1` and commit `v.1`.
- [ ] T004 [P] Implement `code/src/metrics_logger.py` to record CPU cycles, RAM usage, and wall-clock time for every task
- [ ] T005 Create base entity schemas in `specs/001-symbolic-dojo-extend/contracts/` (SymbolicState, ExecutionOutcome, ComputeMetric)
- [ ] T006 [P] Setup contract validation tests in `code/tests/contract/` using `pyyaml` and `jsonschema`
- [ ] T046 [P] [Foundational] Define `replan_support` boolean flag in `SymbolicState` schema in `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml` to enable deterministic replanning logic in T025.
 - **Implementation**: Add `replan_support: boolean` field to the `SymbolicState` schema. Update `code/src/state_mapper.py` to populate this flag based on task metadata.
- [ ] T007 Implement `code/src/main.py` orchestration script to chain data loading, planning, and logging

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Baseline Re-Execution (Priority: P0)

**Goal**: Generate paired baseline data for statistical validity.
**Dependencies**: Depends on Phase 2 (Foundational) completion. Specifically depends on T003 for data access.

- [ ] T000 [P] Execute the original GPU-based RoboDojo Neural Policy on a comprehensive suite of tasks in a high-fidelity simulated environment to generate `data/interim/baseline_results.parquet` labeled as 'Sim-Baseline'.
 - **Implementation**: Load the original RoboDojo Neural Policy weights from HuggingFace dataset `RoboDojo/RoboDojo-v1`, commit `v.1`, file `weights/baseline_policy.pt`. Run the baseline model on each task in the high-fidelity simulated environment. **Run this task on a dedicated GPU instance (e.g., Kaggle GPU or separate CI job)** as the original policy is GPU-based. Record `ExecutionOutcome` (Success/Failure) for each task. **Contingency**: If the real-world robot is unavailable, log the result as 'Sim-Baseline' (this is a valid logged state, not synthetic data generation). **Do NOT fallback to synthetic data generation.** If the simulation environment fails to initialize (physics engine crash), the task MUST raise a `SimulationFailureError` and abort. **Dependencies**: This task depends on T003 for data ingestion infrastructure.
 - **Dependencies**: Depends on T003.

---

## Phase 2.7: Adapter Construction (Sim-to-Real) (Priority: P0.5)

**Goal**: Train the low-level controller adapter without overfitting to the test set, then retrain on all data for final evaluation.
**Dependencies**: This phase depends on Phase 2 (Foundational) completion.

- [ ] T010 [P] Implement `code/src/controller_adapter.py` to define the "Linear Probe" architecture and execute the following atomic flow: 1. Split the tasks from `RoboDojo/RoboDojo-v1` (split="train", seed=42) into a training set and a hold-out validation set. 2. Train the probe on the training tasks. 3. Save intermediate weights to `data/processed/adapter_weights_interim.pt`. 4. Validate on the hold-out tasks. 5. **IF** validation metrics pass threshold, **THEN** retrain on all tasks and save final weights to `data/processed/adapter_weights.pt`. **IF** validation fails, raise `ValidationFailedError` and abort; do NOT produce final weights.
 - **Implementation**: Use a fixed seed 42 for the split. Ensure the 'Retrain on ALL 18 tasks' step is mandatory and only executed if validation passes. The final artifact `adapter_weights.pt` must be the result of this retraining step. This task is atomic and sequential; [P] tag removed to reflect strict ordering.

**Checkpoint**: Adapter ready for integration with US2

---

## Phase 3: User Story 1 - CPU-Tractable Symbolic Planner Execution (Priority: P1) 🎯 MVP

**Goal**: Generate valid action sequences for long-horizon tasks using a CPU-only symbolic planner.

**Independent Test**: The system is tested by feeding a RoboDojo task specification into the planner and verifying that a discrete action sequence is output within 60 seconds on a 2-core CPU.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T008 [P] [US1] Unit test for `state_mapper.py` deterministic thresholding in `code/tests/unit/test_state_mapper.py`
- [ ] T009 [P] [US1] Integration test for A* planner generating valid sequences in `code/tests/integration/test_planner.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/src/vision_encoder.py` using frozen MobileViT (CPU-only) to generate `SemanticEmbedding` from video frames
- [ ] T014 [P] [US1] Implement `code/src/state_mapper.py` to map embeddings to discrete `SymbolicState` predicates (affordances, connectivity) explicitly excluding continuous physics dynamics (friction, mass).
 - **Implementation**: Ensure the mapping logic explicitly filters out continuous physics variables. **Depends on T046**.
- [ ] T015 [US1] Implement `code/src/planner.py` with A* algorithm to generate `ActionSequence` of sub-goals
- [ ] T016 [US1] Add validation in `code/src/planner.py` to ensure generated sequences respect object affordances defined in the input graph
- [ ] T017 [US1] Add logging in `code/src/planner.py` to record planning time and verify ≤ 60s constraint per task
- [ ] T022 [US1] Implement memory-efficient streaming in `code/src/metrics_logger.py` to ensure total RAM usage remains ≤ 6 GB during planning. If RAM approaches 6 GB, **raise `ResourceLimitExceeded` error and abort**. Do NOT downsample or skip logging.
 - **Implementation**: Monitor RAM. If > 6 GB, raise `ResourceLimitExceeded`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Real-World Execution Validation (Priority: P2)

**Goal**: Execute generated symbolic action sequences on a real-world robot and measure task completion rates.

**Independent Test**: The system is tested by running the symbolic planner output on the physical robot and recording binary pass/fail outcomes with explicit failure mode labels.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for `ExecutionOutcome` schema in `code/tests/contract/test_execution_outcome.py`
- [ ] T020 [P] [US2] Integration test for failure mode logging in `code/tests/integration/test_failure_logging.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/src/executor.py` to run `ActionSequence` on the physical robot using the adapted controller (from T010).
 - **Implementation**: Use ROS topic `/robot/cmd_pose` and `rosbridge_library` for connection. If connection fails, raise `ConnectionError` and abort.
- [ ] T023 [US2] Implement logic in `code/src/executor.py` to detect task completion (pose deviation ≤ 5cm, orientation ≤ 15°) and record `ExecutionOutcome`.
- [ ] T024 [US2] Implement failure detection in `code/src/executor.py` to label failures as "Planner Infeasibility" or "Controller Execution Failure" and explicitly append this label and the outcome to `data/interim/execution_logs.parquet`.
 - **Implementation**: Ensure `failure_mode` column is written to the parquet file.
- [ ] T025 [US2] Implement conditional check in `code/src/executor.py` to attempt to replan from the last known valid state ONLY IF the `replan_support` flag in `SymbolicState` is true (per T046). If false, record as a hard failure. **Do not implement a new replanning algorithm.**
 - **Implementation**: Check `replan_support` flag from `SymbolicState`. If true, attempt replan. If false, log hard failure.
- [ ] T026 [US2] Log all execution metrics (time, success/failure, failure mode) to `data/interim/execution_logs.parquet`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Statistically compare success rates and compute overhead of the symbolic approach against the original RoboDojo baseline.

**Independent Test**: The system is tested by running the statistical analysis module on collected data, verifying the output includes the Wilcoxon signed-rank test statistic and p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `code/tests/unit/test_stats.py`
- [ ] T031 [P] [US3] Integration test for full statistical report generation in `code/tests/integration/test_report.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `code/src/stats_analysis.py` to load baseline results from `data/interim/baseline_results.parquet` (from T000) and symbolic results from `data/interim/execution_logs.parquet`.
- [ ] T033 [US3] Implement Wilcoxon signed-rank test in `code/src/stats_analysis.py` (null hypothesis: median difference = 0).
- [ ] T033b [US3] Calculate rank-biserial correlation effect size in `code/src/stats_analysis.py`.
- [ ] T033c [US3] Generate power analysis report text (including N=18 limitation) and write it to `data/final/statistical_report.txt`.
 - **Implementation**: Explicitly include the text "Power Analysis: N=18" in the final report.
- [ ] T034 [US3] Calculate percentage reduction in compute overhead (CPU cycles, memory) in `code/src/stats_analysis.py`. **Depends on T032 and T000 completion.**
- [ ] T035 [US3] Generate report in `code/src/stats_analysis.py` explicitly stating whether the null hypothesis is rejected at α = 0.05.
- [ ] T036 [US3] Implement calculation of catastrophic failure rate (defined as "complete task abandonment due to unmodeled dynamics"), compare the calculated rate against the explicit threshold of ≤ 5% defined in SC-005, and flag the result as Pass/Fail in the final report. **Do NOT check for Hardware Error or Timeout.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Physics Fidelity Isolation Control (Priority: P4)

**Goal**: Run a control experiment using a "Perfect Low-Level Executor" to isolate the impact of the symbolic abstraction.

**Independent Test**: The system is tested by running the symbolic planner against a simulated oracle and comparing the success rate to the real-world execution rate.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US4] Unit test for Oracle executor logic in `code/tests/unit/test_oracle.py`
- [ ] T040 [P] [US4] Integration test for Physics Fidelity Gap calculation in `code/tests/integration/test_gap_analysis.py`

### Implementation for User Story 4

- [ ] T037 [P] [US4] Implement `code/src/oracle_executor.py` as a simulated "Perfect Low-Level Executor" with ground-truth physics using MuJoCo physics engine, scene file `scene/robodojo_oracle.xml`, and ground-truth data source `ground_truth_poses.parquet`. **This is a diagnostic-only control experiment (Constitution Principle VI). It must not be used for primary metrics.**
- [ ] T038 [US4] Execute `ActionSequence` (from T015) against the Oracle in `code/src/oracle_executor.py` and record success rate, generating `data/interim/oracle_results.json`.
 - **Implementation**: Run the full loop of symbolic plans against the Oracle and persist results to JSON.
- [ ] T041 [US4] Calculate "Physics Fidelity Gap" (Oracle success rate - Real-World success rate) in `code/src/stats_analysis.py` using data from T038 and T026, and write the result to `data/interim/oracle_results.json` as a distinct diagnostic output.
 - **Implementation**: Calculate gap in `stats_analysis.py` and save to `oracle_results.json`. **Depends on T038 and T026.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Ablation Study & Final Reporting (Priority: P5)

**Goal**: Vary state representation detail and generate final research report.

**Independent Test**: The system is tested by comparing success rates and compute overhead across different state representation levels.

### Implementation for Ablation Study

- [ ] T042 [P] [US3] Implement "Full Affordance Graph" mode in `code/src/state_mapper.py`
- [ ] T043 [P] [US3] Implement "Simplified Connectivity Graph" mode in `code/src/state_mapper.py`
- [ ] T044a [US3] Orchestrate the comparative execution of both graph modes (Full vs Simplified) using the pipeline from US1 and US2. **Depends on T042, T043, and US1/US2 completion.**
 - **Implementation**: Run US1 & US2 with Full Graph, then with Simplified Graph.
- [ ] T044b [US3] Perform statistical comparison of the results (success rates, compute overhead) between the two modes and **generate `data/interim/ablation_results.parquet`** with the comparative metrics as the primary deliverable.
 - **Implementation**: Calculate and save comparative metrics to `ablation_results.parquet`.
- [ ] T045 [US3] Generate final statistical report in `data/final/statistical_report.txt` including limitations (N=18).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046a Update README.md with installation instructions, usage examples, and project structure overview
- [ ] T046b Add API documentation for planner.py and state_mapper.py in `docs/`
- [ ] T046c Add coding standards section and PR template instructions to CONTRIBUTING.md
- [ ] T047 Code cleanup and refactoring in `code/src/`
- [ ] T048 Performance optimization for streaming data loader in `code/src/data_loader.py`
- [ ] T049 [P] Additional unit tests for edge cases (ambiguous embeddings, mid-sequence failures) in `code/tests/unit/`
- [ ] T050 Run `quickstart.md` validation and ensure all scripts execute on CPU

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - can start immediately.
- **Phase 2 (Foundational)**: Depends on Setup completion - BLOCKS all user stories.
- **Phase 2.5 (Baseline)**: Depends on Phase 2 (Foundational) completion.
- **Phase 2.7 (Adapter)**: Depends on Phase 2 (Foundational) completion.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (ActionSequence) and Phase 2.7 output (adapter_weights.pt).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1, US2, and Phase 2.5 outputs.
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1 output (ActionSequence).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: US4 (Oracle) depends on US1 (Planner) completion, not US2.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for state_mapper.py deterministic thresholding in code/tests/unit/test_state_mapper.py"
Task: "Integration test for A* planner generating valid sequences in code/tests/integration/test_planner.py"

# Launch all models for User Story 1 together:
Task: "Implement code/src/vision_encoder.py using frozen MobileViT"
Task: "Implement code/src/state_mapper.py to map embeddings to discrete SymbolicState"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup
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
 - Developer C: User Story 3
 - Developer D: User Story 4 (depends on A's completion)
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