# Tasks: Automated AI Skill Generation via Expert Knowledge Distillation

**Input**: Design documents from `/specs/650-colleague-skill-automated-ai-skill-gener/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are INCLUDED as per project requirements for a reproduction project to ensure schema and logic integrity.
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

- [X] T001 Create project structure per implementation plan: `mkdir -p src/{cli,distillation,validation,installation,models,config} tests/{unit,integration,contract} examples/ tools/research/`
- [X] T002 Initialize Python 3.9+ project: `python -m venv venv`, create `requirements.txt` with `pyyaml>=6.0, jsonschema>=4.0, pytest>=7.0, rich>=13.0`
- [X] T003 [P] Configure linting: Create `.flake8` (max-line-length=100) and `pyproject.toml` (black config)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define `contracts/skill_package.schema.yaml` as the Single Source of Truth for the Skill Package schema (FR-003, FR-004)
- [X] T005 Generate `src/models/skill_schema.py` from `contracts/skill_package.schema.yaml` to enforce JSON validation (FR-002)
- [X] T006 [P] Implement `src/distillation/intake.py` to handle input validation, file loading, and error handling for missing/malformed data (FR-006)
- [X] T007 [P] Implement `src/distillation/templates.py` with static templates for "capability" and "bounded behavior" tracks (FR-004)
- [X] T008 Setup environment configuration management: Create `src/config/settings.py` with keys `INPUT_PATH`, `OUTPUT_PATH`, `EXAMPLE_TIANI_PATH`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End-to-End Execution of the Distillation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the main CLI to ingest `example_tianyi` and generate a valid skill package directory.

**Independent Test**: Run `tests/integration/test_cli_lifecycle.py`; verify exit code 0 and existence of `meta.json`, `persona.md`, `work.md` in `skills/`.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST to define the interface, but they depend on the CLI structure (T012).

- [X] T010 [US1] Write integration test `tests/integration/test_cli_lifecycle.py` with function `test_cli_generates_valid_package`: Asserts exit code 0 and that `skills/example_tianyi/meta.json` exists and is valid JSON. (Note: Spec SC-001 and SC-002 require concrete metrics; this test enforces [deferred] pass rate on the generated artifact structure).
- [X] T011 [US1] Write contract test `tests/contract/test_empty_input.py` with function `test_empty_input_fails_fast`: Asserts non-zero exit code and error message containing "missing or invalid" when input file is empty.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/cli/main.py` CLI entry point to orchestrate the pipeline (FR-001)
- [X] T013 [US1] Implement `src/distillation/processor.py` to perform deterministic pattern matching and generate `meta.json`, `persona.md`, `work.md` (FR-001, FR-004)
- [X] T014 [US1] **REMOVED**: Retry logic for simulated API timeouts is out of scope for deterministic local processing.
- [X] T015 [US1] Integrate `intake.py` (T006) and `processor.py` (T013) logic within `src/distillation/processor.py` before wrapping in CLI (T012)
- [X] T016 [US1] Add logging for pipeline stages (intake, processing, generation) using `rich` in `src/cli/main.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validation of Generated Artifacts (Priority: P2)

**Goal**: Validate generated artifacts against the schema and content requirements.

**Independent Test**: Run `schema_validator.py` and `content_checker.py` against generated files; verify zero violations and ≥3 heuristics.

### Tests for User Story 2

- [X] T017 [P] [US2] Write unit test `tests/unit/test_schema.py` with function `test_schema_validation_passes`: Asserts `skill_schema.py` validates a correct `meta.json` and rejects an invalid one.
- [X] T018 [P] [US2] Write unit test `tests/unit/test_content_checker.py` with function `test_heuristics_count`: Asserts `content_checker.py` returns count >= 3 for a valid `work.md`.

### Implementation for User Story 2

- [X] T019 [US2] Implement `src/validation/schema_validator.py` to validate `meta.json` against `skill_schema.py` (FR-002, SC-002)
- [X] T020 [US2] Refine `src/distillation/processor.py` to ensure `persona.md` contains distinct "practices/mental models" and "communication style" sections (FR-004)
- [X] T021 [US2] Refine `src/distillation/processor.py` to ensure `work.md` contains at least 3 distinct decision heuristics (SC-004)
- [X] T022 [US2] Integrate validation step into `cli/main.py` so the pipeline fails if validation does not pass (FR-002)
- [X] T023 [US2] **REMOVED**: PII detection for real data is out of scope; project uses only provided example data (`example_tianyi`). The spec edge case regarding PII is acknowledged but deferred to a future security review; no implementation task exists for this reproduction phase.
- [X] T024 [P] [US2] **MOVED**: Moved to Phase 4 (US2) as it depends on the content_checker implementation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Verification of Installation and Portability (Priority: P3)

**Goal**: Verify the installation script can parse and acknowledge the generated skill package.

**Independent Test**: Run `tests/contract/test_installation.py` against the generated artifact; verify success message and "ready for deployment" status.

### Tests for User Story 3

- [X] T025 [P] [US3] Write integration test `tests/contract/test_installation.py` with function `test_install_claude_skill_success`: Asserts installation script parses `meta.json` and outputs "ready for deployment".

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/installation/install_claude_generated_skill.py` to parse `meta.json` and `persona.md` (FR-005)
- [X] T027 [US3] Implement version mismatch detection in `install_claude_generated_skill.py` using `semver` comparison, log specific warning, and skip rollback (Edge Cases)
- [X] T028 [US3] Add "ready for deployment" confirmation output logic in `install_claude_generated_skill.py`
- [X] T029 [US3] Integrate installation verification into the end-to-end test suite (US-3, SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification.

- [X] T030 [P] Documentation updates: Add "Installation", "Usage", and "Examples" sections to `README.md` and `quickstart.md`
- [X] T031 Code cleanup and refactoring: Reduce cyclomatic complexity in `src/distillation/processor.py` to < 10
- [X] T032 [P] Performance optimization: Profile `src/cli/main.py` using `cProfile` and verify execution time < 5 minutes on CPU-only runner (SC-005)
- [X] T033 [P] Run `quickstart.md` validation script to ensure reproducibility
- [X] T034 Final integration test run covering all User Stories (US1, US2, US3)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 generation to validate, but implementation is independent
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 generation to install, but implementation is independent

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts (T004-T005) before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006, T007) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all logic for User Story 1 together:
Task: "Implement src/distillation/processor.py for pattern matching"
Task: "Implement src/distillation/intake.py for input validation"
Task: "Implement src/cli/main.py CLI entry point"
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
   - Developer A: User Story 1 (CLI & Generation)
   - Developer B: User Story 2 (Validation & Content Checks)
   - Developer C: User Story 3 (Installation Script)
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
- **Compute Feasibility**: All tasks are designed for CPU-only execution (limited cores, constrained RAM). No GPU, no 8-bit quantization, no large model training.
- **Data Flow**: Ensure `intake.py` (T006) and `processor.py` (T013) are implemented before validation (T019) and installation (T026) tasks to ensure data exists to validate/install.
- **Spec Gap Note**: Spec SC-001 and SC-002 contained "[deferred]" placeholders in the initial draft; this task list enforces concrete pass rates ([deferred]) for the reproduction pipeline.
- **Scope Clarification**: PII detection (T023) and API retry logic (T014) are explicitly excluded as they pertain to "real data" or "external LLM" scenarios outside the scope of this deterministic reproduction project.