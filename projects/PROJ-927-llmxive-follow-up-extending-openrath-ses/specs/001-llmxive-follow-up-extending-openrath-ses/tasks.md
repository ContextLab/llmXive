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
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/`): Create directories `code/`, `code/generators/`, `code/executors/`, `code/simulators/`, `code/reconstructors/`, `code/analyzers/`, `tests/`, `data/raw/workflows/`, `data/processed/event_log/`, `data/processed/session_first/`, `data/processed/results/`, `state/`. Create empty `__init__.py` files in all `code/` subdirectories (`code/`, `code/generators/`, `code/executors/`, `code/simulators/`, `code/reconstructors/`, `code/analyzers/`).
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` at `projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/` pinning exact versions: `pytest==7.4.0`, `scipy==1.11.0`, `pandas==2.1.0`, `numpy==1.24.0`, `pyyaml==6.0.1`, `jsonschema==4.19.0`.
- [ ] T003 [P] Configure linting and formatting: Create `.ruff.toml` with `[lint]` rules and `pyproject.toml` with `[tool.black]` section.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to define specific keys: `SEED=42`, `CORRUPTION_RATE=0.1`, `WORKFLOW_COUNT=500`, `SWEEP_RATES=[, low, moderate]

The specific value to remove/generalize: 'low'

Rewritten passage:`, and directory paths for `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, `STATE_DIR`.
- [ ] T005 [P] Create directory structure for `data/raw/workflows`, `data/processed/event_log`, `data/processed/session_first`, `data/processed/results`.
- [ ] T006 Implement `code/generators/__init__.py` and base schema definitions for Workflow Definition and Ground Truth.
- [ ] T007 Implement `code/executors/__init__.py` and `code/simulators/__init__.py` base classes.
- [ ] T008 Implement `code/reconstructors/__init__.py` and `code/analyzers/__init__.py` base classes.
- [ ] T009 Create `code/main.py` orchestration skeleton with CLI arguments (`--seed`, `--count`, `--resume`), checkpoint file format (`state/checkpoint.json` containing `last_workflow_id` and `status`), and resume logic flow (load checkpoint, skip completed IDs, process remaining).
- [ ] T017 [P] Implement comprehensive data hygiene checksumming: Create `code/utils/checksum_manager.py` to calculate SHA256 for EVERY file under `data/` (both `data/raw/` and `data/processed/`) in a single unified pass and register/update entries in `state/artifact_hashes.json` to satisfy Constitution Principle III.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Workflow Generation and Ground-Truth Capture (Priority: P1) 🎯 MVP

**Goal**: Generate a reproducible set of synthetic multi-agent debugging workflows and capture their exact final states as immutable ground truth.

**Independent Test**: Run the generation script twice with the same seed; verify byte-for-byte identical output and valid JSON structure.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for deterministic generation in `tests/unit/test_generator.py` (verify seed consistency).
- [ ] T011 [P] [US1] Unit test for ground truth immutability in `tests/unit/test_generator.py` (verify read-only constraints).

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/generators/workflow_generator.py` to create deterministic multi-agent workflows with tool outputs and decision trees.
- [ ] T013 [US1] Implement ground truth serialization in `code/generators/workflow_generator.py`: Store to `data/raw/workflows/{workflow_id}_ground_truth.json` (one file per workflow) with SHA256 hash.
- [ ] T014 [US1] Add validation logic to ensure generated workflows contain all necessary variables (tool outputs, state snapshots) as per SC-005.
- [ ] T015 [US1] Implement checkpointing logic in `code/main.py` to resume workflow generation from the last completed ID on timeout.
- [ ] T016 [US1] Add logging for workflow generation steps and hash verification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Architecture Execution with Stress Injection (Priority: P2)

**Goal**: Execute workflows through Baseline Event-Log and Experimental Session-First architectures while injecting corruption and network jitter.

**Independent Test**: Run a single workflow through both architectures with a moderate level of corruption; verify log modifications and architecture-specific storage patterns.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for corruption injector in `tests/unit/test_corruption.py` (verify deletion/modification logic).
- [ ] T019 [P] [US2] Integration test for atomic writes in `tests/integration/test_session_first.py` (verify write-to-temp-then-rename).

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/executors/base_executor.py` abstract base class for architecture execution.
- [ ] T021 [US2] Implement `code/executors/event_log_executor.py` for asynchronous, fragmented storage (transcripts, snapshots, outputs as separate files).
- [ ] T022 [US2] Implement `code/executors/session_first_executor.py` for atomic, single-object state recording (write-to-temp-then-rename).
- [ ] T023 [US2] Implement `code/simulators/corruption_injector.py` to randomly select and modify/delete log entries based on configurable rate (default moderate).
- [ ] T024a [US2] Implement stochastic network delay (jitter) simulation in `code/executors/event_log_executor.py`: Inject `time.sleep(random.uniform(0, jitter_ms))` specifically inside the `tool_call()` method (FR-004).
- [ ] T024b [US2] Implement stochastic network delay (jitter) simulation in `code/executors/session_first_executor.py`: Inject `time.sleep(random.uniform(0, jitter_ms))` specifically inside the `tool_call()` method (FR-004).
- [ ] T025 [US2] Integrate corruption injection into the execution flow in `code/main.py` to ensure logs are corrupted *after* generation but *before* reconstruction.
- [ ] T026 [US2] Add logic to mark corrupted files with a "corruption flag" in metadata: Add `"corrupted": true` to the JSON root of the file or create a sidecar `.meta` file with this flag.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reconstruction and Fidelity Scoring (Priority: P3)

**Goal**: Reconstruct final states from corrupted logs, compare against ground truth, and calculate success rates and latency.

**Independent Test**: Feed a corrupted log set and ground truth into the engine; verify binary pass/fail status and latency timestamp.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for reconstruction logic in `tests/unit/test_reconstruction.py` (verify state restoration).
- [ ] T029 [P] [US3] Unit test for McNemar's test integration in `tests/unit/test_metrics.py` (verify statistical calculation).

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/reconstructors/reconstruction_engine.py` to parse corrupted logs and rebuild state/decision tree.
- [ ] T031 [US3] Implement "Unrecoverable" detection logic: Read `data/processed/corruption_log.json` and cross-reference with `decision_tree.nodes` to flag workflows where critical data was deleted (FR-007).
- [ ] T032 [US3] Implement state comparison logic to calculate binary "Reconstruction Success Rate" against ground truth (FR-005).
- [ ] T033 [US3] Implement "Replay Latency" measurement in `code/analyzers/metrics_calculator.py` (time from start of reconstruction to completion).
- [ ] T034a [US3] Implement primary statistical test in `code/analyzers/statistical_test.py`: Cochran's Q test on the 2x2x3 design (Architecture x Outcome x Corruption Rate) as defined in Plan T013.
- [ ] T034b [US3] Implement post-hoc statistical analysis in `code/analyzers/statistical_test.py`: McNemar's test with Holm-Bonferroni correction for pairwise comparisons as defined in Plan T014.
- [ ] T035 [US3] Implement sensitivity sweep logic in `code/main.py` to iterate over the `SWEEP_RATES` list defined in `code/config.py` (T004) and run the full pipeline for each rate in the concrete set `{0.05, 0.10, 0.20}` (SC-004).
- [ ] T036 [US3] Generate `reconstruction_result.json` for each workflow containing success status, reconstructed state, and latency.
- [ ] T037 [US3] Implement aggregation logic to calculate "Total Resilience Rate" (Success/Total Workflows) where Unrecoverable cases are explicitly counted as failures in the denominator (FR-005), and write to `data/processed/results/aggregated_metrics.json`.
- [ ] T037a [US3] Implement aggregation logic to calculate "Recoverable State Fidelity" (Success/Recoverable Workflows, explicitly excluding Unrecoverable cases as per FR-005/FR-007) and write to `data/processed/results/fidelity_metrics.json`.
- [ ] T038 [US3] Implement fallback logic for small N contingency in `code/analyzers/statistical_test.py`: Use Exact McNemar if N < 25, and Monte Carlo (many repetitions) for Cochran's Q if assumptions are violated.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `README.md` and `docs/`.
- [ ] T042 Code cleanup and refactoring.
- [ ] T043 Performance optimization for 500-workflow sweep: Profile `code/main.py` and refactor loops to ensure < 6h runtime and < 4GB RAM; add `tests/bench_sweep.py` to verify performance constraints.
- [ ] T044 [P] Additional unit tests in `tests/unit/`.
- [ ] T045 Run `quickstart.md` validation.

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
- **Data Integrity**: Ground truth files must be stored in a read-only directory to prevent accidental corruption.
- **Reproducibility**: All random number generators must be seeded explicitly in `config.py`.
- **Failure Handling**: If corruption deletes critical data, the system must flag the workflow as "Unrecoverable" and exclude it from fidelity calculations, not crash.
- **Statistical Rigor**: Primary metric is Total Resilience (Success/Total); Recoverable State Fidelity is secondary. Use Cochran's Q for primary test, McNemar with Holm-Bonferroni for post-hoc.
- **Concrete Sweep**: Corruption rates must be explicitly iterated over {0.05, 0.10, 0.20}.
- **Jitter Scope**: Jitter must be injected ONLY inside the `tool_call()` method of both architecture executors.