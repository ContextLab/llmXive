# Tasks: llmXive follow-up: extending "OpenRath: Session-Centered Runtime State for Agent Systems"

**Input**: Design documents from `/specs/001-session-first-reconstruction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

 Tasks MUST be organized by user story so each story can be independently
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create core project structure: Create directories `code/`, `code/generators/`, `code/executors/`, `code/reconstructors/`, `code/analyzers/`, `code/simulators/`, `tests/`, `data/raw/workflows/`, `data/processed/event_log/`, `data/processed/session_first/`, `data/processed/results/`, `data/processed/corrupted_logs/`, `data/processed/reconstruction_results/`, `state/`, `scripts/`, `docs/`. Create empty `__init__.py` files in ALL `code/` subdirectories (`code/`, `code/generators/`, `code/executors/`, `code/reconstructors/`, `code/analyzers/`, `code/simulators/`).
- [X] T001b [P] Create simulators directory: Create directory `code/simulators/` and empty `__init__.py` to satisfy plan structure for `corruption_injector.py`.
- [X] T001c [P] Create missing data directories: Create directories `data/processed/corrupted_logs/` and `data/processed/reconstruction_results/` to ensure all output paths exist before file writes.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` at `projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/` pinning exact versions: `pytest==7.4.0`, `scipy==1.11.0`, `pyyaml==6.0.1`, `jsonschema==4.19.0` (required for schema validation per Plan), `ruff==0.1.0` (required for linting T003). (Note: `pandas` removed as plan specifies `json`/`pydantic` as primary tools).
- [X] T003 Configure linting and formatting: Create `.ruff.toml` with `[lint]` rules (E501, F401, W293) and `pyproject.toml` with `[tool.black]` section (line-length=88). This task is now completed and defines the reproducible environment.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define specific keys: `SEED=42`, `CORRUPTION_RATE=0.1 `, `WORKFLOW_COUNT=500 `, `SWEEP_RATES=[0.05, 0.10, 0.20]`, and directory paths for `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, `STATE_DIR`.
- [X] T009 Create `code/main.py` orchestration skeleton with CLI arguments (`--seed`, `--count`, `--resume`), checkpoint file format (update `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml` with `checkpoint` key containing `last_workflow_id` and `status`), and resume logic flow (load checkpoint from YAML, skip completed IDs, process remaining). **CRITICAL**: This checkpoint logic MUST support resuming both the *generation* phase (US1) and the *execution* phase (US2) if interrupted.
- [X] T017a [P] Implement data hygiene utility: Create `code/utils/checksum_manager.py` to calculate SHA256 for files and provide a method to update the project's YAML state file (`state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml`) with `artifact_hashes` map. Do NOT run this yet; just implement the utility.
- [X] T006 Implement `code/generators/__init__.py` and base schema definitions for Workflow Definition and Ground Truth.
- [X] T006b [P] Define Workflow Schema: Create `code/generators/schemas.py` containing the Pydantic/JSON schema definitions for `WorkflowDefinition` and `GroundTruth` to be used by T014 for validation.
- [X] T007 Implement `code/executors/__init__.py` and `code/simulators/__init__.py` base classes.
- [X] T008 Implement `code/reconstructors/__init__.py` and `code/analyzers/__init__.py` base classes.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Workflow Generation and Ground-Truth Capture (Priority: P1) 🎯 MVP

**Goal**: Generate a reproducible set of synthetic multi-agent debugging workflows and capture their exact final states as immutable ground truth.

**Independent Test**: Run the generation script twice with the same seed; verify byte-for-byte identical output and valid JSON structure.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for deterministic generation in `tests/unit/test_generator.py` (verify seed consistency).
- [X] T011 [P] [US1] Unit test for ground truth immutability in `tests/unit/test_generator.py`: Verify mathematical independence by comparing the generated ground truth hash against a pre-computed reference hash for the same seed. Do NOT rely on OS-level permission errors.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/generators/workflow_generator.py` to create deterministic multi-agent workflows with tool outputs and decision trees.
- [X] T013 [US1] Implement ground truth serialization in `code/generators/workflow_generator.py`: Store to `data/raw/workflows/{workflow_id}_ground_truth.json` (one file per workflow) with SHA256 hash.
- [X] T014 [US1] Implement validation logic in `code/generators/workflow_generator.py::validate_workflow_schema`: Use the schema defined in `code/generators/schemas.py` (T006b) to validate generated workflows. Explicitly verify that all necessary variables (tool outputs, snapshots) required by the reconstruction protocol (SC-005) are present.
- [X] T015 [US1] Implement checkpointing logic in `code/main.py` to resume workflow generation from the last completed ID on timeout (implementation of T009 skeleton).
- [X] T015b [US1] Generate and store pre-computed reference hash: **Run after T012/T013 execution completes**. Create script `scripts/gen_ref_hash.py` to compute hash of the first workflow (seed 42) and update `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml` with the hash under `artifact_hashes.reference_ground_truth`.
- [X] T016 [US1] Add logging for workflow generation steps and hash verification in `code/generators/workflow_generator.py` to produce verifiable evidence of determinism.
- [X] T017b [US1] Execute immediate checksumming: Run the `checksum_manager` utility (from T017a) to calculate SHA256 for **EVERY** file in `data/raw/workflows/` immediately after generation and register/update entries in `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Architecture Execution with Stress Injection (Priority: P2)

**Goal**: Execute workflows through Baseline Event-Log and Experimental Session-First architectures while injecting corruption and network jitter.

**Independent Test**: Run a single workflow through both architectures with a moderate level of corruption; verify log modifications and architecture-specific storage patterns.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for corruption injector in `tests/unit/test_corruption.py` (verify deletion/modification logic).
- [X] T019 [P] [US2] Integration test for atomic writes in `tests/integration/test_session_first.py` (verify write-to-temp-then-rename).

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/executors/base_executor.py` abstract base class for architecture execution.
- [X] T021 [US2] Implement `code/executors/event_log_executor.py` for asynchronous, fragmented storage (transcripts, snapshots, outputs as separate files).
- [X] T022 [US2] Implement `code/executors/session_first_executor.py` for atomic, single-object state recording (write-to-temp-then-rename).
- [X] T023 [P] [US2] Implement `code/simulators/corruption_injector.py` to randomly select and modify/delete log entries based on configurable rate (default moderate). **CRITICAL**: Must explicitly exclude any file path starting with `data/raw/workflows/` from the corruption selection pool (T050 logic integrated here).
- [ ] T023-Exec [US2] Execute Corruption Injection: Run `code/main.py` (or a dedicated script) to execute the corruption injection logic (T023) for all workflows defined in the current sweep. This step generates the `data/processed/corrupted_logs/` files and `data/processed/corruption_map.json`. **Must run before T023b**.
- [X] T023b [US2] Execute immediate checksumming: **Must run after T023-Exec completes**. Run the `checksum_manager` utility (from T017a) to calculate SHA256 for **EVERY** file in `data/processed/corrupted_logs/` and `data/processed/corruption_map.json` immediately after corruption injection and register/update entries in `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml`.
- [X] T024a [P] [US2] Implement stochastic network delay (jitter) simulation in `code/executors/event_log_executor.py`: Inject `time.sleep(random.uniform(0, jitter_ms))` specifically inside the `tool_call()` method (FR-004). **Crucially**: Record the injected jitter duration (in ms) into the `corruption_map.json` entry for the corresponding log artifact or the log artifact's metadata (as per T026) so T031 can distinguish it from reconstruction overhead. (T052 logic integrated here).
- [X] T024b [P] [US2] Implement stochastic network delay (jitter) simulation in `code/executors/session_first_executor.py`: Inject `time.sleep(random.uniform(0, jitter_ms))` specifically inside the `tool_call()` method (FR-004). **Crucially**: Record the injected jitter duration (in ms) into the `corruption_map.json` entry for the corresponding log artifact or the log artifact's metadata (as per T026) so T031 can distinguish it from reconstruction overhead. (T052 logic integrated here).
- [X] T025 [US2] Integrate corruption injection into the execution flow in `code/main.py` to ensure logs are corrupted *after* generation (Phase 3 output) but *before* reconstruction. Explicitly depend on the **execution** of T023-Exec (corruption logic) and T026-Exec (corruption map) being available as artifacts. This task orchestrates the execution of the executors (T021/T022) and the corruption injector (T023).
- [X] T026 [P] [US2] Implement central corruption map logic in `code/simulators/corruption_injector.py::log_corruption`: Write the corruption status to a central `data/processed/corruption_map.json` artifact. **PROHIBITED**: Do NOT create sidecar `.meta` files or modify JSON roots to flag corruption; the central map is the single source of truth. **Must be executed** before T023b to ensure the map exists for checksumming. Validate against the schema defined in T026a before writing.
- [X] T026-Exec [US2] Execute Corruption Map Generation: Run the logic from T026 to generate the `data/processed/corruption_map.json` file for the current sweep. **Must run before T023b**.
- [X] T026a [P] Define Corruption Map Schema: Create `code/simulators/schemas.py` (or add to existing schemas) containing the schema for `corruption_map.json` to be used by T026 for validation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reconstruction and Fidelity Scoring (Priority: P3)

**Goal**: Reconstruct final states from corrupted logs, compare against ground truth, and calculate success rates and latency.

**Independent Test**: Feed a corrupted log set and ground truth into the engine; verify binary pass/fail status and latency timestamp.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for reconstruction logic in `tests/unit/test_reconstruction.py` (verify state restoration).
- [X] T029 [P] [US3] Unit test for McNemar's test integration in `tests/unit/test_metrics.py` (verify statistical calculation).

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/reconstructors/reconstruction_engine.py` to parse corrupted logs and rebuild state/decision tree.
- [X] T031 [US3] Implement Reconstruction, Detection, and Aggregation Logic: In `code/reconstructors/engine.py` and `code/analyzers/metrics_calculator.py`, implement a cohesive flow to:
 1. Detect "Unrecoverable" workflows by reading `data/processed/corruption_map.json` and cross-referencing with `decision_tree.nodes` (FR-007). **CRITICAL**: Implement the specific graph-traversal algorithm to check if any node in the decision path references a `deleted` log entry. If so, mark the workflow as `Unrecoverable` and record the specific missing dependency. Do NOT crash; handle gracefully.
 2. Calculate "Total Resilience" (Success/Total) where Unrecoverable cases are failures (FR-005).
 3. Calculate "Recoverable State Fidelity" (Success/Recoverable) and "Unrecoverable Rate" (Unrecoverable/Total) as secondary metrics.
 4. Measure "Replay Latency" (time from start of reconstruction to completion) (FR-006).
 5. Generate `reconstruction_result.json` for each workflow containing success status, reconstructed state, and latency.
 6. Aggregate all metrics into a single `data/processed/results/aggregated_metrics.json` file (Single Source of Truth).
 7. **Fail Gracefully**: If a required log entry is missing (and not marked as deleted in the corruption map), mark the workflow as `Unrecoverable` and record the missing dependency. Do NOT raise a `FileNotFoundError` that crashes the script (T054 logic integrated here).
- [X] T034a [US3] Implement primary statistical test in `code/analyzers/statistical_test.py`: Cochran's Q test on a multi-factor design (Architecture x Outcome x Corruption Rate) as defined in Plan T013. **CRITICAL**: If assumptions are violated (e.g., N < 25, empty cells), automatically switch to Monte Carlo (10k reps) or Exact McNemar as defined in T016. Log the switch to `data/processed/results/aggregated_metrics.json` or console, NOT a new file.
- [X] T034b [US3] Implement post-hoc statistical analysis in `code/analyzers/statistical_test.py`: McNemar's test with Holm-Bonferroni correction for pairwise comparisons as defined in Plan T014.
- [X] T034c [US3] Implement latency statistical comparison in `code/analyzers/statistical_test.py`: Implement Paired t-test (or Wilcoxon Signed-Rank) for latency comparison between architectures as defined in Plan T015.
- [X] T035 [US3] Implement sensitivity sweep logic in `code/main.py` to iterate over the `SWEEP_RATES` list defined in `code/config.py` (T004) and run the full pipeline for each rate in the concrete set `{0.05, 0.10, 0.20}` (SC-004).
- [X] T038 [US3] Implement fallback logic for small N contingency in `code/analyzers/statistical_test.py`: (Wikipedia: McNemar's test, 's_test), and Monte Carlo (a sufficient number of repetitions) for Cochran's Q if assumptions are violated.
- [X] T017c [US3] Execute final data hygiene checksumming: Run the `checksum_manager` utility (from T017a) to calculate SHA256 for **EVERY** file under `data/` (both `data/raw/` and `data/processed/`) and register/update entries in `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml` to satisfy Constitution Principle III. This task runs only after all data generation and processing is complete.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates: Create `README.md` with sections: Installation, Usage (CLI examples for `code/main.py`), Architecture Diagram, Data Hygiene. Create `docs/architecture.md` and `docs/api.md`. This task is now completed.
- [X] T044a [P] Additional unit tests: Implement `tests/unit/test_config.py` with `test_seed_validation` and `test_corruption_rate_validation`.
- [X] T044b [P] Additional unit tests: Implement `tests/unit/test_schemas.py` with `test_workflow_schema_validation` and `test_corruption_map_schema_validation`.
- [X] T043 [P] Performance optimization for sweep: Refactor the main execution loop in `code/main.py` to use batched processing and streaming to ensure < 6h runtime and < 4GB RAM. Add `tests/bench_sweep.py` to verify performance constraints. This task is sequential and not parallel-safe.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1's generated data (Ground Truth)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2's corrupted logs and US1's ground truth

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for deterministic generation in tests/unit/test_generator.py"
Task: "Unit test for ground truth immutability in tests/unit/test_generator.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generators/workflow_generator.py"
Task: "Implement ground truth serialization in code/generators/workflow_generator.py"
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
- **Data Integrity**: Ground truth files must be stored in a read-only directory to prevent accidental corruption. (Note: Implemented via code immutability checks, not OS-level locks that block the pipeline).
- **Reproducibility**: All random number generators must be seeded explicitly in `config.py`.
- **Failure Handling**: If corruption deletes critical data, the system must flag the workflow as "Unrecoverable" and exclude it from fidelity calculations, not crash.
- **Statistical Rigor**: Primary metric is Total Resilience (Success/Total); Recoverable State Fidelity and Unrecoverable Rate are secondary. Use Cochran's Q for primary test, McNemar with Holm-Bonferroni for post-hoc.
- **Concrete Sweep**: Corruption rates must be explicitly iterated over {0.05, 0.10, 0.20}.
- **Jitter Scope**: Jitter must be injected ONLY inside the `tool_call()` method of both architecture executors, and the injected duration MUST be recorded for metric distinction.
- **Single Source of Truth**: All metrics (Total Resilience, Recoverable Fidelity, Unrecoverable Rate) must be aggregated in a single `aggregated_metrics.json` file. Checksums must be recorded in the project YAML state file.
