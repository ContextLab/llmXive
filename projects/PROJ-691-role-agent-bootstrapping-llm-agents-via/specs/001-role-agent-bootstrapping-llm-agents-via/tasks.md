# Tasks: Reproduce & validate: Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution

**Input**: Design documents from `/specs/001-role-agent-bootstrapping-llm-agents-via/`
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

- [X] T001 Create `src/reproduction/` directory
- [X] T002 Create `src/config/` directory
- [X] T003 Create `src/tests/` directory
- [X] T004 Initialize Python project with CPU-only dependencies: `ray`, `torch` (cpu), `transformers`, `alfworld`, `pytest` in `requirements.txt`
- [X] T005 [P] Configure linting (flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Setup `src/reproduction/__init__.py` to expose core modules without triggering imports
- [X] T007 Implement `src/reproduction/error_handlers.py` with `handle_gpu_error()` (raise `SystemExit(1)` if GPU detected per FR-005) and `handle_memory_pressure()` (raise error if RAM > 6GB)
- [X] T008 Setup environment configuration loader in `src/reproduction/config_loader.py` to inject CPU constraints into the vendored `external/roleagent`
- [X] T009 Create `src/config/alfworld_sample_config.yaml` defining a small episode subset and CPU-tractable model path (e.g., `google/flan-t5-small` or local mock)
- [X] T010 [P] Create `data/` directory for artifact storage

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Setup and Sanity Verification (Priority: P1) 🎯 MVP

**Goal**: Initialize the vendored `roleagent` repository, install dependencies, and run a minimal sanity check to confirm the environment is functional on CPU.

**Independent Test**: Execute `python tests/test_sanity.py` which imports `role_agent.wia_utils` and `role_agent.aiw_curriculum` and exits with code 0 and "All sanity checks passed".

### Implementation for User Story 1

- [X] T011 [US1] Implement `src/reproduction/sanity_check.py` script to initialize Ray (single-node) and verify `roleagent` imports
- [X] T012 [US1] Create `tests/test_sanity.py` integration script that runs the sanity check and asserts exit code 0
- [X] T013 [US1] Add logic to `src/reproduction/sanity_check.py` to detect and block execution if GPU memory is detected (FR-005) - *Delegates to error_handlers.py*
- [X] T014 [US1] Unit test for sanity check in `tests/unit/test_sanity.py`: Verify `torch.cuda.is_available()` returns False and no CUDA import errors occur. If mock GPU is present, verify `SystemExit(1)` is raised.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - World-In-Agent (WIA) Execution (Priority: P1)

**Goal**: Execute the WIA component on a sampled subset of ALFWorld on CPU., producing `wia_results.json` with state predictions.

**Independent Test**: Run `python src/reproduction/wia_runner.py --config src/config/alfworld_sample_config.yaml` and verify `wia_results.json` contains entries with `predicted_state` and `actual_state`.

### Implementation for User Story 2

- [X] T015 [US2] Implement `src/reproduction/wia_runner.py` to wrap `external/roleagent/wia_utils.py`, injecting CPU-only config and episode limit
- [X] T016 [US2] Implement memory monitoring in `wia_runner.py` using `psutil` to check RSS against a predefined storage threshold and call `error_handlers.handle_memory_pressure()`
- [X] T017 [US2] Create `src/reproduction/wia_logger.py` to serialize WIA output into `data/wia_results.json` (FR-002), ensuring `alignment_score` is calculated and included as per 'WIA_Log' entity definition
- [X] T018 [US2] Add model fallback logic to `wia_runner.py`: if `google/flan-t5-small` fails RAM checks, switch to a local mock or smaller model (Edge Case)
- [X] T019 [US2] Ensure `src/reproduction/wia_runner.py` explicitly sets `device="cpu"` for all PyTorch operations to prevent CUDA errors

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Agent-In-World (AIW) and Reproduction Report (Priority: P2)

**Goal**: Execute the AIW component to analyze `wia_results.json`, retrieve failure patterns, and generate `aiw_analysis_report.md`.

**Independent Test**: Run `python src/reproduction/aiw_analyzer.py --input data/wia_results.json` and verify `data/aiw_analysis_report.md` exists with a "Reproduction Summary" section.

### Implementation for User Story 3

- [X] T020 [US3] Implement `src/reproduction/aiw_analyzer.py` to wrap `external/roleagent/aiw_curriculum.py`, consuming `wia_results.json`
- [X] T021 [US3] Create `src/reproduction/report_generator.py` to format the AIW output into `aiw_analysis_report.md` (FR-004)
- [X] T022 [US3] [SC-003] Ensure `report_generator.py` explicitly states in the first sentence of the "Reproduction Summary" section: "The dual-role mechanism is present and operational in the pipeline" (dynamically based on execution results, not hardcoded success)
- [X] T023 [US3] [FR-004] Add logic to `report_generator.py` to list sample size, failure patterns, and explicitly document the limitation of sample size and inability to statistically validate quantitative claims (US-3 Acceptance 2)
- [X] T024 [US3] Unit test for report generation in `tests/unit/test_report.py`: Verify the report contains the required sections and the specific string for SC-003
- [X] T025 [P] Run `tests/validate_entities.py` against `data/wia_results.json` and `data/aiw_analysis_report.md` to validate against spec entities (WIA_Log, AIW_Report)

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T026 [P] Documentation updates: Add `README.md` with instructions to run the full pipeline (Setup → WIA → AIW)
- [X] T027 Code cleanup: Remove hardcoded paths, ensure all config is injected via `alfworld_sample_config.yaml`
- [X] T028 [P] Run full pipeline end-to-end in CI to verify total time < 2 hours (SC-004)

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires `wai_runner` to be functional
- **User Story 3 (P2)**: **Depends on US2 completion** - Requires `wia_results.json` to exist before execution

### Within Each User Story

- Implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- US3 must wait for US2 output artifacts

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
3. Developer C: User Story 3 (waits for US2 artifact)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks MUST run on free-tier CPU-only CI (limited CPU, GB RAM). No GPU, no 8-bit/4-bit quantization requiring CUDA.