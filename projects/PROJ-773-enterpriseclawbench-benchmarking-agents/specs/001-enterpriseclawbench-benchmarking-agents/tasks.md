# Tasks: EnterpriseClawBench Reproduction & Validation

**Input**: Design documents from `/specs/001-enterpriseclawbench-reproduction/`
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

- [X] T001a Create `src/` directory structure: `runners`, `validators`, `utils`
- [X] T001b Create `tests/` directory structure: `contract`, `integration`, `unit`
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` including `pyyaml`, `pytest`, `pandas`, `jsonschema`
- [X] T002a Define concrete fallback thresholds for SC-001 (100% smoke test success) and SC-005 (0 crashes on malformed input) to satisfy testability lens given `[deferred]` placeholders in spec.md
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Clone and verify integrity of `external/EnterpriseClawBench` git submodule
- [X] T005 [P] Install dependencies from `external/EnterpriseClawBench/requirements.txt`
- [X] T006 Verify existence of `raw_session_example` and `example_runs` directories in submodule
- [X] T007 Create `src/utils/retry_utils.py` implementing FR-007 (exponential backoff, max 3 retries, **mark as unscorable** on failure)
- [X] T007a Create `src/utils/yaml_parser.py` to implement FR-002: parse `smoke.yaml` and `public_session_full.yaml` for dynamic scope adjustment
- [X] T008 Create `src/validators/task_validator.py` to enforce SC-002 (5 required fields check)
- [X] T009 Create `src/validators/report_validator.py` to enforce SC-003 (report structure check)
- [X] T010 [P] Create `contracts/task.schema.yaml` and `contracts/report.schema.yaml` based on **spec.md:FR-003** and **FR-004** field lists

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Construction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute construction pipeline on minimal data to verify code integrity and basic functionality.

**Independent Test**: Run `python -m construction.enterprise_clawbench_construction.cli --config construction/configs/smoke.yaml` and verify exit code 0 and valid JSON output.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for task JSON schema validation in `tests/contract/test_task_schema.py`
- [X] T012 [P] [US1] Integration test for smoke pipeline execution in `tests/integration/test_smoke_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Create `src/runners/smoke_runner.py` to orchestrate construction pipeline with `smoke.yaml`
- [X] T014 [US1] Implement logic to invoke `external/EnterpriseClawBench/construction/cli.py` with sample config
- [X] T015 [US1] Add error handling in `smoke_runner.py` to log specific file paths on malformed input (US-1 Edge Case)
- [X] T016 [US1] Integrate `task_validator.py` to verify `prompt`, `role_class`, `skill_subclass`, `hard_rules`, `semantic_rubric` fields in `output/smoke/tasks/`
- [X] T016a Implement 'Pack Validate' and 'Export' stages in `smoke_runner.py` to ensure full FR-001 pipeline sequence coverage
- [X] T017 [US1] Create a synthetic malformed input file to test graceful error logging (FR-001, US-1)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Evaluation Protocol (Priority: P2)

**Goal**: Validate judge logic, scoring rubrics, and determinism using static artifacts.

**Independent Test**: Execute evaluation CLI on `example_runs` artifacts and verify `report.json` structure and determinism.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for report JSON schema in `tests/contract/test_report_schema.py`
- [X] T019 [P] [US2] Integration test for evaluation determinism in `tests/integration/test_eval_determinism.py`

### Implementation for User Story 2

- [X] T020 [US2] Create `src/runners/eval_runner.py` to orchestrate evaluation on `example_runs` (static) OR `output/smoke/tasks/` (generated); **Depends on T016a completion**
- [X] T021 [US2] Implement deterministic controls: check if provider supports `seed`; if yes, set `temperature=0` and `seed`; if no, trigger fallback logic
- [X] T021a Create `src/runners/scoring_logic.py` to implement FR-004: score artifacts on `artifact_delivery`, `visual_quality`, `cost`, `runtime`, `skill_transfer`
- [X] T022a [US2] Implement check: verify if LLM provider supports `seed` parameter; if not, flag for fallback
- [X] T022b [US2] Implement fallback logic: switch to **rule-based scoring mode ONLY for smoke test** if seed unsupported; ensure this mode preserves determinism (SC-003)
- [X] T023 [US2] Integrate `retry_utils.py` to handle LLM timeouts (FR-007) and mark tasks as `unscorable`
- [X] T024 [US2] Implement double-run check in `eval_runner.py` to verify `report.json` identity (SC-003); **Depends on T020 completion**
- [X] T025 [US2] Simulate LLM timeout in test data to verify 3-attempt retry and `unscorable` status (FR-007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Paper Statistics (Priority: P3)

**Goal**: Aggregate results and validate structural trends against paper metrics.

**Independent Test**: Generate role distribution histogram and compare relative proportions against paper figures.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for role distribution calculation logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T027 [US3] Create `src/runners/stats_runner.py` to aggregate task counts and role classes from `output/smoke/tasks/` and `output/reports/`; **Depends on T020 completion**
- [X] T028 [US3] Implement logic to generate role class distribution histogram (Pandas/Matplotlib)
- [X] T029a [US3] Implement comparison logic to verify relative proportions match paper trends (Plan.md Phase 3 limitation) using **KL-divergence < 0.1** against `data/paper_stats.json`
- [X] T029b [US3] Implement absolute count variance check (<5%) against `data/paper_stats.json`; **Explicitly skip this check if sample size N < 10** (Plan.md limitation)
- [X] T030 [US3] Generate `data/results/role_distribution.json` (schema: `{ "role": count,... }`) and `data/results/leaderboard.json` (schema: `{ "model": score,... }`); verify leaderboard consistency with paper's "high performance" claim (score > 0.85 or top [deferred] rank)
- [X] T031 [US3] Add logging for error handling robustness metrics (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Create `docs/execution_guide.md` with sections: prerequisites, smoke test command, expected output, and fallback thresholds
- [X] T033 Code cleanup and refactoring of `src/utils` and `src/runners`
- [X] T034 [P] Run `quickstart.md` validation if created
- [X] T035 Verify all tasks complete within 6 hours on CPU-only runner (Constraint Check)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on Task Pack generation (US1) for evaluation input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on Task Pack (US1) and Evaluation (US2) for aggregation

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
Task: "Contract test for task JSON schema validation in tests/contract/test_task_schema.py"
Task: "Integration test for smoke pipeline execution in tests/integration/test_smoke_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Create smoke_runner.py in src/runners/smoke_runner.py"
Task: "Create task_validator.py in src/validators/task_validator.py"
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