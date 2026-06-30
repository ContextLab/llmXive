# Tasks: AutoResearchClaw Reproduction & Validation

**Input**: Design documents from `/specs/001-autoresearchclaw-repro/`
**Prerequisites**: plan.md, spec.md
**Tests**: Included to ensure CPU-only feasibility and mechanism validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

## Phase 0: Constitution & Setup (Shared Infrastructure)

**Purpose**: Project initialization, Constitution creation, and basic structure

- [X] T000 Create `constitution.md` with project SSoT principles (FR-030) to resolve "BLOCKING GAP" in plan.md
- [X] T001a Create project directory structure: `mkdir -p src/{core,validation,data,config} tests/{contract,integration,unit} config logs`
- [X] T001b Create empty `__init__.py` files in all new Python directories: `touch src/core/__init__.py src/validation/__init__.py src/data/__init__.py src/config/__init__.py tests/contract/__init__.py tests/integration/__init__.py tests/unit/__init__.py`
- [X] T002a Create `requirements.txt` with exact versions: `pandas==2.0.3`, `numpy==1.24.3`, `psutil==5.9.5`, `pyyaml==6.0.1`, `requests==2.31.0`, `pytest==7.4.0`
- [X] T002b Initialize virtual environment: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/config/topics.yaml` with minimal synthetic topic manifest. Schema: `[{id: str, name: str, description: str, data_source: str}]`. Example: `[{id: "B01", name: "Synthetic Biology", description: "Test topic", data_source: "synthetic"}]`
- [X] T005 [P] Implement `src/config/hitl_config.yaml` defining intervention points. Schema: `{intervention_points: [str], timeout_seconds: int, input_file: str}`. Allowed points: `["hypothesis", "experimental_design"]`
- [X] T006 Create base `src/core/checkpoint.py` to serialize/deserialize `ResearchCycle` state. Model: `{topic_id: str, hypothesis: str, experiment_code: str, results: dict, status: str}`. Format: JSON.
- [X] T007 [US1] Create base `src/core/memory_guard.py` using `psutil`. Logic: Monitor RAM usage (reactive) AND estimate next allocation via dataset size estimation (anticipatory: rows * cols * type_size * safety_factor). If estimated > 6GB OR current > 7GB, trigger data sampling (reduce dataset size by [deferred]).
- [X] T007a [US3] Define `src/logs/evolution_log.json` schema and utilities. Schema: `[{timestamp: str, error_type: str, lesson_learned: str, safeguards: [str], run_id: str}]`. Implement `append_entry()` and `read_safeguards()`. **NOT [P]** - must complete before T008.
- [X] T008 [US3] Setup `src/logs/evolution_log.json` initialization using schema from T007a. Implement `write/append` schema for cross-run history and `read/apply` logic for safeguards. **Depends on T007a completion**.
- [X] T009 Configure `pytest` environment with `conftest.py` for CPU-only resource constraints mocking

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End-to-End Execution on CPU (Priority: P1) 🎯 MVP

**Goal**: Execute the research loop on CPU to generate a valid artifact (JSON/PNG) within 6 hours.

**Independent Test**: Run `evaluate.py` with a synthetic topic and verify a non-empty output file exists.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for output schema in `tests/contract/test_artifact_schema.py`. Function: `test_artifact_schema_validates_json`. Validates against `src/contracts/artifact_schema.json`.
- [X] T011 [US1] Integration test for full CPU loop in `tests/integration/test_full_cpu_loop.py`. **Depends on T012-T017 completion**. (Note: T011 is NOT [P] as it depends on implementation).

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `src/data/synthetic_generators.py` to create small, CPU-tractable datasets. Format: CSV. Columns: `["id", "feature1", "feature2", "label"]`. Rows:. Distribution: Normal.
- [X] T013 [US1] Implement `src/core/runner.py` skeleton main loop wrapper. Steps: Hypothesis -> Experiment -> Analysis -> Report. Interfaces: `run(topic_id: str) -> Artifact`. Error handling: Catch-all.
- [X] T013b [US1] Implement `src/core/runner.py` self-healing logic for LLM errors. Detect code execution errors (Exception types). Invoke Pivot/Refine loop: Retry with modified code or skip. Log fix attempt.
- [X] T013c [US1] Implement `src/core/runner.py` Pivot/Refine loop for *code execution* errors. Logic: Catch SyntaxError/ImportError/ValueError, generate fix prompt, update code string, retry execution up to 3 times.
- [X] T014 [US1] Integrate `src/core/memory_guard.py` into `runner.py` to enforce 7GB RAM cap via sampling.
- [X] T015 [US1] Implement `src/validation/artifact_validator.py` to check for non-empty, valid outputs.
- [X] T016 [US1] Add retry logic with exponential backoff for LLM API calls in `runner.py`. Params: `initial_delay=1s`, `max_retries=3`, `multiplier=2.0`. Switch: Check ENV var `USE_MOCK_LLM`. If set, use `MockLLMProvider` mimicking real latency/failure modes (not bypass).
- [X] T017 [US1] Add checkpointing triggers in `runner.py` to save state every N minutes for timeout recovery.
- [X] T017b [US1] Implement 6-hour timeout monitoring in `runner.py`. Logic: Track elapsed time; if > 5.5h, trigger graceful abort and save partial report.
- [X] T017c [US1] Implement 6-hour timeout monitor in `runner.py` to measure execution time against budget and trigger graceful abort/partial report if limit approached (Edge Case requirement).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human-in-the-Loop (HITL) Intervention Mode (Priority: P2)

**Goal**: Simulate human intervention at specific points and verify plan modification.

**Independent Test**: Inject a JSON feedback payload at a trigger point and verify the next cycle reflects the change.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for HITL feedback schema in `tests/contract/test_hitl_feedback.py`
- [X] T019 [P] [US2] Integration test for HITL pause/resume in `tests/integration/test_hitl_intervention.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/validation/hitl_controller.py` to pause execution and wait for `hitl_input.json`. Protocol: Poll file at regular intervals; timeout s. Schema: `{intervention_point: str, feedback: dict}`.
- [X] T021 [US2] Implement logic in `src/core/runner.py` to parse HITL feedback and modify the `ResearchCycle` plan.
- [X] T022 [US2] Add logging in `src/core/runner.py` to record `InterventionEvent` details (trigger, payload, result).
- [X] T023 [US2] Create a mock HITL input generator in `tests/fixtures/hitl_mock.py` for automated testing
- [X] T023b [US2] Implement quality score calculation and comparison logic in `src/validation/metrics.py`. Logic: Score run with intervention vs run without; target >= 10% improvement.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Run Evolution & Error Memory (Priority: P3)

**Goal**: Demonstrate the system avoids previously logged errors in subsequent runs.

**Independent Test**: Run a task that triggers a known error, then run a similar task and verify the error is avoided.

### Tests for User Story 3

- [X] T024 [P] [US3] Contract test for `EvolutionLog` schema in `tests/contract/test_evolution_log.py`
- [X] T029a [US3] Create a cross-run error persistence test fixture in `tests/fixtures/error_trigger.py`. Scenario: Run A triggers error -> writes to EvolutionLog. Run B reads log -> avoids error. Validates T026/T027. **Must precede T025**.
- [X] T025 [US3] Integration test for error avoidance in `tests/integration/test_error_evolution.py`. **Depends on T029a completion**.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `src/validation/error_healer.py` to detect errors and generate "lessons learned". Logic: Parse exception -> generate lesson string -> format safeguards list.
- [X] T027 [US3] Implement `src/core/runner.py` logic to read `EvolutionLog` at startup and apply safeguards.
- [X] T028 [US3] Add logic in `src/validation/error_healer.py` to inject "avoidance strategies" into the plan based on logs.
- [X] T028b [US3] Implement recurrence rate calculation in `src/validation/metrics.py`. Logic: Query log for resolved errors -> count recurrence in subsequent runs -> report rate.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Documentation updates in `docs/` including `quickstart.md` for CPU-only setup
- [X] T031 Code cleanup and refactoring of `runner.py` error handling paths
- [X] T032a Performance optimization: Refactor `src/data/synthetic_generators.py` (T012) to use chunked writing for CSV generation to stay under 100MB RAM.
- [X] T032b Performance verification: Verify via `psutil` monitoring that T032a keeps RAM < 100MB.
- [X] T033 [P] Additional unit tests in `tests/unit/` for `memory_guard.py` and `checkpoint.py`
- [X] T034 Security hardening: sanitize inputs in `hitl_controller.py` and `error_healer.py`
- [X] T035 Run `quickstart.md` validation to ensure all steps execute on GitHub Actions free tier

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
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
Task: "Contract test for output schema in tests/contract/test_artifact_schema.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic_generators.py in src/data/synthetic_generators.py"
Task: "Implement artifact_validator.py in src/validation/artifact_validator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Constitution & Setup
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