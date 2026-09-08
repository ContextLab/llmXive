# Tasks: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-robodojo-a-u/`
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
 - **Implementation**: Run `mkdir -p code/data/{raw,interim,processed,final}`. Verify creation with `ls code/data`.
- [X] T001d Initialize Python 3.11 virtual environment and create `code/requirements.txt` (torch-cpu, scikit-learn, networkx, pandas, datasets, opencv-python, pyyaml)
- [X] T001e Create `code/src/config.py` with paths, seeds, and RoboDojo dataset commit hash `v.1`
 - **Implementation**: Create `code/src/config.py` with the following exact content:
 ```python
 # code/src/config.py
 import os

 BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 DATASET_ID = "RoboDojo/RoboDojo-v1"
 DATASET_COMMIT = "v.1"
 REAL_WORLD_SPLIT = "real_world"
 SEED = 42
 RAM_LIMIT_GB = 6
 PLANNING_TIMEOUT_S = 60
 POSE_DEV_TOLERANCE_CM = 5.0
 ORIENT_DEV_TOLERANCE_DEG = 15.0
 ```
- [X] T001f Create `code/src/data_loader.py`
- [X] T001g Create `code/src/vision_encoder.py`
- [X] T001h Create `code/src/state_mapper.py`
- [X] T001i Create `code/src/planner.py`
- [X] T001j Create `code/src/controller_adapter.py`
- [X] T001k Create `code/src/oracle_executor.py`
- [X] T001l Create `code/src/metrics_logger.py`
- [X] T001m Create `code/src/stats_analysis.py`
- [X] T001n Create `code/src/executor.py`
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools in `code/`
 - **Implementation**: Create `code/pyproject.toml` with the following content:
 ```toml
 [tool.black]
 line-length = 88
 target-version = ['py311']

 [tool.ruff]
 select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
 ignore = []
 target-version = "py311"

 [tool.ruff.per-file-ignores]
 "__init__.py" = ["F401"]
 ```
 Create `code/.ruff.toml` with:
 ```toml
 extend = "pyproject.toml"
 ```

---

## Phase 1: Foundational (Blocking Prerequisites & Schema Definitions)

**Purpose**: Core infrastructure and schema definitions that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a [P] [Foundational] Create `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml` defining `SymbolicState` with fields: `state_id`, `predicates` (list of strings), `affordances` (dict), `connectivity` (list), `replan_support` (boolean).
 - **Implementation**: Create the YAML file with the specified schema structure. Ensure `replan_support` is a boolean field.
- [ ] T005b [P] [Foundational] Create `specs/001-symbolic-dojo-extend/contracts/execution_outcome.schema.yaml` defining `ExecutionOutcome` with fields: `task_id`, `success` (boolean), `failure_mode` (string: "Planner Infeasibility" | "Controller Execution Failure" | "Hardware Error" | "Timeout"), `timestamp`.
 - **Implementation**: Create the YAML file with the specified schema structure.
- [ ] T005c [P] [Foundational] Create `specs/001-symbolic-dojo-extend/contracts/compute_metric.schema.yaml` defining `ComputeMetric` with fields: `task_id`, `cpu_cycles` (int), `ram_mb` (float), `wall_clock_s` (float).
 - **Implementation**: Create the YAML file with the specified schema structure.
- [ ] T005d [P] [Foundational] Create `specs/001-symbolic-dojo-extend/contracts/ablation_result.schema.yaml` defining `AblationResult` with fields: `graph_type` (string), `success_rate` (float), `compute_overhead` (float).
 - **Implementation**: Create the YAML file with the specified schema structure.
- [X] T046 [P] [Foundational] Update `code/src/state_mapper.py` to populate the `replan_support` boolean flag in `SymbolicState` based on task metadata.
 - **Implementation**: Add logic to `code/src/state_mapper.py` to set `replan_support` based on the `task_metadata` input. Ensure the schema file `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml` is updated to reflect this new field.
- [ ] T006a [P] [Foundational] Create `code/tests/contract/test_symbolic_state.py` using `jsonschema` to validate `SymbolicState` against `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml`.
 - **Implementation**: Use `jsonschema.validate` to test against the YAML schema.
- [ ] T006b [P] [Foundational] Create `code/tests/contract/test_execution_outcome.py` using `jsonschema` to validate `ExecutionOutcome` against `specs/001-symbolic-dojo-extend/contracts/execution_outcome.schema.yaml`.
 - **Implementation**: Use `jsonschema.validate` to test against the YAML schema.
- [ ] T006c [P] [Foundational] Create `code/tests/contract/test_compute_metric.py` using `jsonschema` to validate `ComputeMetric` against `specs/001-symbolic-dojo-extend/contracts/compute_metric.schema.yaml`.
 - **Implementation**: Use `jsonschema.validate` to test against the YAML schema.
- [ ] T006d [P] [Foundational] Create `code/tests/contract/test_ablation_result.py` using `jsonschema` to validate `AblationResult` against `specs/001-symbolic-dojo-extend/contracts/ablation_result.schema.yaml`.
 - **Implementation**: Use `jsonschema.validate` to test against the YAML schema.
- [X] T003 [P] Implement `code/src/data_loader.py` to stream RoboDojo parquet files from HuggingFace without loading full dataset into RAM
 - **Implementation**: Use `datasets.load_dataset(..., streaming=True)` to iterate over the RoboDojo dataset shards. Do NOT load the full dataset into memory. Accumulate statistics online or process frame-by-frame. Explicitly raise an error if the stream fails to open a verified real source; do NOT fall back to synthetic data. Use dataset ID `RoboDojo/RoboDojo-v1` and commit `v.1`.
- [ ] T000 [US2] Execute the original RoboDojo Neural Policy on all real-world RoboDojo tasks to generate `data/interim/baseline_results.parquet` labeled as 'Real-Baseline'. <!-- FAILED: unspecified -->
 - **Implementation**: Load the original RoboDojo Neural Policy weights from HuggingFace dataset `RoboDojo/RoboDojo-v1`, commit `v.1`, file `weights/baseline_policy.pt`. Run the baseline model on each of the real-world tasks. **MUST execute on real-world robot hardware**. If real-world hardware is unavailable, the process MUST raise a `HardwareUnavailableError` and abort immediately. Do NOT substitute simulation or generate a 'Sim-Baseline' result. Log the source ('Real') along with the results. **Dependencies**: Depends on T003 (data ingestion) and T005 (schema definitions).
- [X] T004 [P] Implement `code/src/metrics_logger.py` to record CPU cycles, RAM usage, and wall-clock time for every task
- [ ] T007 Implement `code/src/main.py` orchestration script to chain data loading, planning, and logging

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.7: Adapter Construction (Sim-to-Real) (Priority: P0.5)

**Goal**: Train the low-level controller adapter without overfitting to the test set.
**Dependencies**: This phase depends on Phase 1 (Foundational) completion.

- [ ] T010 [US2] Implement `code/src/controller_adapter.py` to define the "Linear Probe" architecture and execute the following atomic flow: 1. Split the *real-world video subset* of tasks from `RoboDojo/RoboDojo-v1` (split="real_world", seed=42) into a training set and a hold-out validation set. 2. Train the probe on the training set. 3. Save intermediate weights to `data/processed/adapter_weights_interim.pt`. 4. Validate on the hold-out set. 5. **IF** validation metrics pass threshold, **THEN** save the validated weights to `data/processed/adapter_weights.pt`. **IF** validation fails, raise `ValidationFailedError` and abort. **Do NOT** retrain on the full dataset.

---

## Phase 3: User Story 1 - CPU-Tractable Symbolic Planner Execution (Priority: P1) 🎯 MVP

**Goal**: Generate valid action sequences for long-horizon tasks using a CPU-only symbolic planner.

**Independent Test**: The system is tested by feeding a RoboDojo task specification into the planner and verifying that a discrete action sequence is output within 60 seconds on a 2-core CPU.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Unit test for `state_mapper.py` deterministic thresholding in `code/tests/unit/test_state_mapper.py`
- [X] T009 [P] [US1] Integration test for A* planner generating valid sequences in `code/tests/integration/test_planner.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/src/vision_encoder.py` using frozen MobileViT (CPU-only) to generate `SemanticEmbedding` from video frames
- [X] T014 [P] [US1] Implement `code/src/state_mapper.py` to map embeddings to discrete `SymbolicState` predicates (affordances, connectivity) explicitly excluding continuous physics dynamics (friction, mass).
 - **Implementation**: Ensure the mapping logic explicitly filters out continuous physics variables. **Depends on T046**.
- [X] T015 [US1] Implement `code/src/planner.py` with A* algorithm to generate `ActionSequence` of sub-goals
- [ ] T016 [US1] Add validation in `code/src/planner.py` to ensure generated sequences respect object affordances defined in the input graph
- [ ] T017 [US1] Add logging in `code/src/planner.py` to record planning time and verify ≤ 60s constraint per task
- [ ] T022 [US1] Implement memory-efficient streaming in `code/src/metrics_logger.py` to ensure total RAM usage remains ≤ 6 GB during planning. If RAM exceeds 6 GB, **raise `ResourceLimitExceeded` error and halt the entire process immediately.**
 - **Implementation**: Monitor RAM. If > 6 GB, raise error and halt execution. Do NOT continue to the next task.
- [ ] T022 [US1] Add logging in `code/src/planner.py` to record planning time and verify ≤ 60s constraint per task

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

- [ ] T032 [US3] Implement `code/src/stats_analysis.py` to load baseline results from `data/interim/baseline_results.parquet` (from T000) and symbolic results from `data/interim/execution_logs.parquet`.
 - **Implementation**: Load data from T000 and T026.
- [ ] T033 [US3] Implement Wilcoxon signed-rank test in `code/src/stats_analysis.py` (null hypothesis: median difference = 0).
- [ ] T033b [US3] Calculate rank-biserial correlation effect size in `code/src/stats_analysis.py`.
- [ ] T033c [US3] Generate power analysis report text (including N=18) and write it to `data/final/statistical_report.txt`.
 - **Implementation**: Explicitly include the text "Power Analysis: N=18" in the final report.
- [ ] T034 [US3] Calculate percentage reduction in compute overhead (CPU cycles, memory) in `code/src/stats_analysis.py`.
- [ ] T035 [US3] Generate report in `code/src/stats_analysis.py` explicitly stating whether the null hypothesis is rejected at α = 0.05.
- [ ] T036 [US3] Implement calculation of catastrophic failure rate (defined strictly as "complete task abandonment due to unmodeled dynamics", **specifically "Hardware Error" or "Timeout"**), compare the calculated rate against the predefined threshold of ≤ 5% defined in SC-005, and flag the result as Pass/Fail in the final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Physics Fidelity Isolation Control (Priority: P4)

**Goal**: Run a control experiment using a "Perfect Low-Level Executor" to isolate the impact of the symbolic abstraction.

**Independent Test**: The system is tested by running the symbolic planner against a simulated oracle and comparing the success rate to the real-world execution rate.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US4] Unit test for Oracle executor logic in `code/tests/unit/test_oracle.py`
- [ ] T040 [P] [US4] Integration test for Physics Fidelity Gap calculation in `code/tests/integration/test_gap_analysis.py`

### Implementation for User Story 4

- [ ] T037 [US4] Implement `code/src/oracle_executor.py` as a simulated "Perfect Low-Level Executor" using a simulated kinematic model (no physics engine) and explicitly **avoiding** the use of real-world recordings.
 - **Implementation**: Use the simulated kinematic model to generate perfect poses. Do not use real-world recordings.
- [ ] T038 [US4] Execute `ActionSequence` (from T015) against the Oracle in `code/src/oracle_executor.py` and record success rate, generating `data/interim/oracle_results.json`.
 - **Implementation**: Run the full loop of symbolic plans against the Oracle and persist results to JSON.
- [ ] T041 [US4] Calculate "Physics Fidelity Gap" (Oracle success rate - Real-World success rate) in `code/src/stats_analysis.py` using data from T038 and T026, and write the result to `data/interim/oracle_results.json` as a distinct diagnostic output.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 7: Ablation Study & Final Reporting (Priority: P5)

**Goal**: Vary state representation detail and generate final research report.

**Independent Test**: The system is tested by comparing success rates and compute overhead across different state representation levels.

### Implementation for Ablation Study

- [ ] T042 [P] [US3] Implement "Full Affordance Graph" mode in `code/src/state_mapper.py`
- [ ] T043 [P] [US3] Implement "Simplified Connectivity Graph" mode in `code/src/state_mapper.py`
- [ ] T044a [US3] Orchestrate the comparative execution of both graph modes (Full vs Simplified) using the pipeline from US1 and US2.
- [ ] T044b [US3] Perform statistical comparison of the results (success rates, compute overhead) between the two modes and **generate `data/interim/ablation_results.parquet`** with the comparative metrics as the primary deliverable.
- [ ] T045 [US3] Generate final statistical report in `data/final/statistical_report.txt` including limitations (N=18).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046a [P] Update `README.md` with installation instructions, usage examples, and project structure overview.
 - **Implementation**: Add sections: "Installation", "Usage Example", "Project Structure".
- [ ] T046b [P] Add API documentation for `planner.py` and `state_mapper.py` in `docs/` using Sphinx autodoc from docstrings in `planner.py` and `state_mapper.py`.
 - **Implementation**: Generate docs using Sphinx autodoc from docstrings in `planner.py` and `state_mapper.py`.
- [ ] T046c [P] Add coding standards section and PR template instructions to `CONTRIBUTING.md`.
 - **Implementation**: Add sections: "Coding Standards", "PR Template Guidelines".
- [ ] T047 [P] Code cleanup and refactoring in `code/src/`.
 - **Implementation**: Remove unused imports, rename variables for clarity, extract duplicate code into helper functions.
- [ ] T048 [P] Performance optimization for streaming data loader in `code/src/data_loader.py`.
 - **Implementation**: Target: reduce latency in `data_loader.py` streaming logic via batching and chunk optimization.
- [ ] T049 [P] Additional unit tests for edge cases (ambiguous embeddings, mid-sequence failures) in `code/tests/unit/`.
 - **Implementation**: Create `test_ambiguous_embeddings.py` and `test_mid_sequence_failure.py` with specific assertions for each edge case.
- [ ] T050 [P] Run `quickstart.md` validation and ensure all scripts execute on CPU.
 - **Implementation**: Run `python -m code.main --validate-quickstart`. Verify output matches expected format and all scripts execute successfully on CPU.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence