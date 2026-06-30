# Tasks: $π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows

**Input**: Design documents from `/specs/001-bench-evaluating-proactive-personal-assi/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `src/`, `tests/`, `external/`
- [X] T002 Initialize Python 3 project with `requirements.txt` (torch-cpu, scikit-learn, pyyaml, pytest, scipy, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup mock environment wrapper in `src/mocks/environment.py` to simulate Gmail/Amazon APIs with deterministic responses
- [X] T005 [P] Implement CPU-only enforcement logic in `src/runners/cpu_runner.py` (force `device="cpu"`, no CUDA checks)
- [X] T006 [P] Setup resource monitoring hooks (memory/time) in `src/utils/logger.py` to track against GB/6h limits
- [X] T007 Create base data models for `Task`, `Trajectory`, and `Persona` in `src/data_models.py`
- [X] T008 Configure error handling infrastructure to log "Environment Failure" vs "Agent Failure" in `src/utils/error_handler.py`
- [X] T009 Setup configuration management for personas and model YAMLs in `src/config/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Successfully run the vendored `Pi-Bench` codebase on CPU-only CI without crashing, generating valid JSON results for at least one persona.

**Independent Test**: Trigger the `quickstart` runbook. The CI job must finish with exit code 0 and produce `results/` directory containing JSON artifacts for the `Financier` persona.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for JSON output schema in `tests/contract/test_output_schema.py`
- [X] T011 [P] [US1] Integration test for CPU-only execution in `tests/integration/test_cpu_run.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `src/runners/evaluator.py` to wrap `Pi-Bench` `main.py` with CPU constraints
- [X] T013 [US1] Integrate mock environment in `src/mocks/environment.py` to handle `task.yaml` and `profile.yaml` loading
- [X] T014 [US1] Implement task execution loop in `src/runners/evaluator.py` to process multiple tasks without OOM
- [X] T015 [US1] Add logic to handle model loading fallback to CPU if CUDA is detected in `src/runners/cpu_runner.py`
- [X] T016 [US1] Add error handling to log "Environment Failure" and exclude from metrics in `src/utils/error_handler.py`
- [X] T017 [US1] Add logging for task completion and latency in `src/utils/logger.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Proactivity Metrics and Distinguish from Retrieval (Priority: P2)

**Goal**: Compute `proactivity_score` and implement Sequence Novelty Index (SNI) to distinguish planning from complex retrieval, addressing the Turing-simulated reviewer's concern.

**Independent Test**: Analyze generated `results/` JSON files. The output must contain `proactivity_score`, `task_completion_rate`, and `novelty_index`. Verify that high-entropy retrieval paths are penalized.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for metric fields in `tests/contract/test_metric_schema.py`
- [X] T019 [P] [US2] Unit test for SNI calculation logic in `tests/unit/test_sni_logic.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/utils/metrics.py` with `proactivity_score` calculation (baseline comparison)
- [X] T021 [US2] Implement **Sequence Novelty Index (SNI)** in `src/utils/metrics.py` using n-gram deviation from template library
- [X] T022 [US2] Implement logic to penalize high-entropy retrieval paths lacking causal structure in `src/utils/metrics.py`
- [X] T023 [US2] Add logic to flag "Ambiguous Intent" tasks in results based on `task.yaml` analysis
- [X] T024 [US2] Integrate SNI and Proactivity scoring into the evaluation loop in `src/runners/evaluator.py`
- [X] T025 [US2] Add logic to calculate `action_entropy` and `novelty_index` for each trajectory in `src/utils/metrics.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Comparative Baseline Results (Priority: P3)

**Goal**: Reproduce comparative analysis between different LLM backends (MiniMax, Claude, DeepSeek) and generate a summary report with bootstrapping.

**Independent Test**: Run evaluation with at least two distinct model configurations and generate a comparative report showing statistically distinguishable differences (or lack thereof).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for comparative report schema in `tests/contract/test_report_schema.py`
- [X] T027 [P] [US3] Integration test for multi-model comparison in `tests/integration/test_model_comparison.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement model configuration loader for multiple backends in `src/config/models/`
- [X] T029 [US3] Implement aggregation logic in `src/runners/evaluator.py` to run tasks across multiple models
- [X] T030 [US3] Implement bootstrapping strategy for low-N comparisons in `src/utils/metrics.py`
- [X] T031 [US3] Generate comparative table (JSON/CSV) showing `proactivity_score` and `completion_rate` per model in `src/utils/reporter.py`
- [X] T032 [US3] Add logic to distinguish "hidden intent" vs "explicit instruction" performance gaps in `src/utils/reporter.py`
- [X] T033 [US3] Implement stability check (variance within ±0.05) for repeated runs in `src/utils/metrics.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `docs/` and `README.md`
- [X] T035 Code cleanup and refactoring of `src/utils/metrics.py` for clarity
- [X] T036 Performance optimization to ensure full task run fits in 6 hours
- [X] T037 [P] Additional unit tests for edge cases (timeout, API failure) in `tests/unit/`
- [X] T038 Security hardening for mock environment inputs
- [X] T039 Run `quickstart.md` validation to confirm end-to-end success

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for JSON output schema in tests/contract/test_output_schema.py"
Task: "Integration test for CPU-only execution in tests/integration/test_cpu_run.py"

# Launch all models for User Story 1 together:
Task: "Implement src/runners/evaluator.py to wrap Pi-Bench main.py with CPU constraints"
Task: "Integrate mock environment in src/mocks/environment.py to handle task.yaml and profile.yaml loading"
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
- **Specific Reviewer Concern Addressed**: Task T021-T023 explicitly implement the "Sequence Novelty Index" and "causal structure penalty" requested by the Alan Turing-simulated reviewer to distinguish planning from complex retrieval.
