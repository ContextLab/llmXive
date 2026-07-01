# Tasks: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

**Input**: Design documents from `/specs/795-opid-reproduction/`
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

**Purpose**: Project initialization, environment hardening, and CPU-only configuration

- [X] T001 Create project structure per implementation plan (`src/opid/`, `tests/`, `output/`)
- [X] T002 [P] Initialize Python 3.10+ project with `requirements.txt` (torch CPU-only, transformers, alfworld, pandas, numpy, pyyaml)
- [X] T003 [P] Configure GitHub Actions CI workflow (CPU-only runner, extended timeout, constrained RAM limit)
- [X] T004 Create `src/opid/config.py` with CPU-only overrides (force `device="cpu"`, disable CUDA)
- [X] T016 [P] Patch `external/OPID` imports (or inject config) to enforce `device="cpu"` and batch size limits in the vendored code
- [X] T005 [P] Implement `tests/unit/test_cpu_smoke.py` to verify no CUDA imports or GPU device calls

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure for data handling, logging, and on-policy generation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
**Internal Order**: T009/T010 MUST precede T008. T021 MUST precede T008.

- [X] T006 Implement `src/opid/utils.py` with trajectory sampling and memory-safe logging helpers
- [X] T007 [P] Create `src/opid/data_loader.py` to fetch a subset of ALFWorld task instances from HuggingFace dataset 'alfworld/alfworld' and cache to `data/alfworld_cache`
- [X] T021 [P] Implement `src/opid/logging.py` to write `output/trajectory_logs.json` with required schema (step_id, skill_type, log_prob_shift)
- [X] T009 [P] Implement `src/opid/routing.py` with `critical_first_routing` logic and episode-level fallback
- [X] T010 [P] Implement `src/opid/advantage.py` with `dual_advantage_calculator` (outcome + distillation)
- [X] T008 Implement `src/opid/strict_on_policy_generator.py` (collects trajectories, computes gradients, **persists to output/trajectory_logs.json**, then discards immediately)
- [X] T011 [P] Create `tests/unit/test_routing_logic.py` to verify fallback logic triggers when critical_step_detector returns None
- [X] T012 [P] Create `tests/unit/test_advantage_calculator.py` to verify calculation logic returns expected values for given inputs (not variance)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Verify End-to-End Execution on CPU-Only CI (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored OPID codebase on CPU-only hardware without hardware errors.

**Independent Test**: Run `src/opid/quickstart.py --cpu-only` and verify logs show successful ALFWorld init and first optimization step.

### Tests for User Story 1

- [X] T013 [P] [US1] Integration test `tests/integration/test_cpu_smoke.py` to verify no CUDA errors and valid loss output
- [X] T036 [P] [US1] Contract test `tests/contract/test_env_init.py` to verify ALFWorld environment loads without GPU dependencies
- [X] T014 [P] [US1] Integration test `tests/integration/test_full_loop_gpu.py` to run a sufficient number of steps and verify NO ImportError/RuntimeError related to GPU (SC-004)

### Implementation for User Story 1

- [X] T015 [US1] Implement `src/opid/quickstart.py` (entry point for 100-step CPU training run)
- [X] T017 [US1] Add memory monitoring in `src/opid/training.py` to abort if usage > 6GB
- [X] T018 [US1] Add logging calls in `src/opid/training.py` to capture step-level metadata (requires T021)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Artifact Generation and Data Integrity (Priority: P2)

**Goal**: Confirm execution produces valid artifacts (logs, metrics) reflecting OPID mechanism.

**Independent Test**: Inspect `output/trajectory_logs.json` and `output/opid_metrics.csv` for non-empty data, valid schema, and variance.

### Tests for User Story 2

- [X] T019 [P] [US2] Contract test `tests/contract/test_schema_validation.py` to verify `step_id`, `skill_type`, `log_prob_shift` fields
- [X] T020 [P] [US2] Integration test `tests/integration/test_artifact_integrity.py` to verify variance > 0 in metrics
- [X] T025 [P] [US2] Validation test `tests/contract/test_sc005_fallback.py` to verify SC-005: Parse `output/trajectory_logs.json` and confirm fallback ratio >= 10% on the specific 5-task subset

### Implementation for User Story 2

- [X] T022 [US2] Implement `src/opid/metrics.py` to compute and write `output/opid_metrics.csv` (outcome advantage, distillation advantage)
- [X] T023 [US2] Integrate logging calls into `src/opid/training.py` to capture step-level metadata (requires T021)
- [X] T024 [US2] Add validation logic in `src/opid/utils.py` to ensure `log_prob_shift` variance > 0 when distillation-weight != 0 (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Baseline Performance Trends (Priority: P3)

**Goal**: Compare OPID performance against outcome-only baseline on 5 ALFWorld tasks.

**Independent Test**: Run evaluation script for OPID and baseline, compare success rates (trend consistency, not hard threshold).

**Dependencies**: T027 depends on T015 (training entry) and T021 (logging artifacts).

### Tests for User Story 3

- [X] T037 [P] [US3] Contract test `tests/contract/test_baseline_comparison.py` to verify OPID success rate shows non-degenerate behavior compared to baseline (no hard 10% threshold)
- [X] T026 [P] [US3] Integration test `tests/integration/test_trend_validation.py` to run both modes and log results

### Implementation for User Story 3

- [X] T027 [US3] Implement `src/opid/evaluation.py` with `--mode opid` and `--mode baseline` flags
- [X] T028 [US3] Implement `src/opid/baseline_runner.py` for "outcome-only" configuration (distillation weight = 0)
- [X] T029 [US3] Add result aggregation in `src/opid/evaluation.py` to compute success rates and compare
- [X] T030 [US3] Add fallback logic in `src/opid/evaluation.py` to handle task timeouts gracefully

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Create `docs/SETUP.md` with setup, CPU constraints, and artifact schema
- [X] T039 [P] Create `docs/ARTIFACT_SCHEMA.md` detailing JSON/CSV schemas
- [X] T040 [P] Refactor `src/opid/utils.py` for memory safety and clarity
- [X] T041 [P] Refactor `src/opid/training.py` for readability and modularity
- [X] T042 [P] Benchmark memory usage with batch_size=4 on CI runner
- [X] T043 [P] Tune batch_size to ensure memory usage stays < 5GB
- [X] T034 [P] Additional unit tests in `tests/unit/` for edge cases (OOM, timeout, routing failure)
- [X] T035 Run `quickstart.md` validation and verify 100 steps complete within 6h
- [X] T044 [P] Validate SC-005 explicitly on the chosen 5-task subset and document the difficulty distribution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **Internal Order**: T009, T010, T021 MUST complete before T008. T008 cannot run in parallel with these.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for execution flow
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for data and evaluation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] **EXCEPT T008** can run in parallel (T008 depends on T009, T010, T021)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Integration test 'tests/integration/test_cpu_smoke.py' to verify no CUDA errors and valid loss output"
Task: "Contract test 'tests/contract/test_env_init.py' to verify ALFWorld environment loads without GPU dependencies"
Task: "Integration test 'tests/integration/test_full_loop_gpu.py' to verify 100 steps run without GPU errors"

# Launch all models for User Story 1 together:
Task: "Implement 'src/opid/quickstart.py' (entry point for 100-step CPU training run)"
Task: "Add memory monitoring in 'src/opid/training.py' to abort if usage > 6GB"
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

1. Team completes Setup + Foundational together (respecting T008 dependencies)
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (unless explicitly noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks MUST run on CPU-only CI (2 cores, 7GB RAM, no GPU)
- **Constraint**: No fabrication of data; use real ALFWorld tasks from verified sources
- **Constraint**: Strict on-policy data lifecycle (no buffering old trajectories)
- **Constraint**: SC-005 ([deferred] fallback) is dependent on task difficulty; T044 validates this on the specific subset.