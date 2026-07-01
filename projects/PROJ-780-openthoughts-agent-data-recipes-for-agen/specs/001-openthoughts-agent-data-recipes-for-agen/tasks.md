# Tasks: OpenThoughts-Agent Data Pipeline Validation & Reproduction

**Input**: Design documents from `/specs/780-openthoughts-agent-validation/`
**Prerequisites**: plan.md, spec.md, research.md (Phase 0 output), data-model.md (Phase 1 output), contracts/ (Phase 1 output)

**Tests**: Unit and integration tests included as requested in spec.md (US-1, US-2).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (docs, src, tests, results)
- [X] T002 Initialize Python 3.10+ project with dependencies: `open-thoughts-agent`, `requests`, `pydantic`, `pytest`, `pyyaml`
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/lib/api_client.py` with exponential backoff (max 3 retries, 5s initial) for API calls (FR-003)
- [X] T005 Implement `src/lib/submodule_checker.py` to detect missing submodules and fail fast with specific error (FR-005)
- [X] T006 Create `contracts/task_trajectory.schema.yaml` defining `input`, `thought_process`, `output` fields
- [X] T007 Create `contracts/dataset_manifest.schema.yaml` defining file metadata structure
- [X] T008 Setup environment configuration management for API keys (mockable) and `--task-limit` args
- [X] T009 Configure logging infrastructure to capture pipeline execution and retry warnings

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End-to-End Data Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the core data generation pipeline on CPU-only CI using mocks to verify code structure.

**Independent Test**: Run `src/data/generate_and_run_sbatch.py` with `--task-limit 10` and `--dry-run` or mock API; verify 5+ valid JSON files created in `src/data/generated/`.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for `src/lib/api_client.py` retry logic in `tests/unit/test_api_client.py`
- [X] T011 [P] [US1] Unit test for `src/lib/submodule_checker.py` failure paths in `tests/unit/test_submodule_checker.py`
- [X] T012 [P] [US1] Integration test for pipeline execution with mocked API in `tests/integration/test_pipeline_execution.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/data/generate_and_run_sbatch.py` entry point with `--task-limit` and `--local` flags (FR-001)
- [X] T014 [US1] Integrate `src/lib/api_client.py` into pipeline to handle task fetch with retry logic (FR-003)
- [X] T015 [US1] Implement logic to generate 10 sample task trajectories (mocked) into `src/data/generated/`
- [X] T016 [US1] Ensure NO GPU/CUDA operations are invoked during generation (FR-006)
- [X] T017 [US1] Add logging for task count and processing summary (US-1 acceptance)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Artifact Verification & Integrity Check (Priority: P2)

**Goal**: Verify generated artifacts match schema and are deserializable.

**Independent Test**: Run `src/data/bespoke/verify.py` against `src/data/generated/`; expect 0 schema violations and successful deserialization.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for schema validation logic in `tests/unit/test_schema_validation.py`
- [X] T019 [P] [US2] Integration test for empty dataset detection in `tests/integration/test_empty_dataset.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `src/data/bespoke/verify.py` to validate JSON against `contracts/task_trajectory.schema.yaml` (FR-002)
- [X] T021 [US2] Implement logic to detect empty datasets and raise specific "Empty Dataset" error (Edge Case)
- [X] T022 [US2] Implement deserialization check to ensure files load without `JSONDecodeError` (US-2 acceptance)
- [X] T023 [US2] Generate `src/data/generated/manifest.json` listing validated files and sizes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducibility Report Generation (Priority: P3)

**Goal**: Generate a human-readable report summarizing results and flagging blocked comparisons.

**Independent Test**: Verify `results/reproduction_report.md` exists, contains "Blocked" flags for API data, and lists artifact counts.

### Tests for User Story 3

- [X] T024 [P] [US3] Integration test for report generation logic in `tests/integration/test_report_generation.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement `src/data/generate_report.py` to compile execution status and artifact counts (FR-004)
- [X] T026 [US3] Add logic to explicitly flag "Blocked" status for paper comparisons (US-3 acceptance)
- [X] T027 [US3] Implement discrepancy detection logic (e.g., execution time vs paper claims) with "Needs Clarification" notes (US-3 acceptance)
- [X] T028 [US3] Generate `results/reproduction_report.md` with required sections (Execution Status, Artifact Counts, Discrepancy Analysis)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation and validation

- [X] T029 [P] Update `src/quickstart.md` with run instructions for `--task-limit` and `--dry-run`
- [X] T030 [P] Run full pipeline end-to-end with `--task-limit 10` to verify all phases
- [X] T031 [P] Validate `results/reproduction_report.md` content against SC-001 to SC-004
- [X] T032 [P] Clean up temporary files and ensure `src/data/generated/` is reproducible

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (generated files)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output (manifest and validation results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Libraries (`api_client`, `submodule_checker`) before pipeline scripts
- Pipeline scripts before report generation
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T008, T009) can run in parallel
- Once Foundational phase completes, US2 and US3 can start in parallel if data flow allows (US1 must finish first)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for api_client retry logic in tests/unit/test_api_client.py"
Task: "Unit test for submodule_checker failure paths in tests/unit/test_submodule_checker.py"

# Launch all models/libraries for User Story 1 together:
Task: "Implement api_client.py with exponential backoff"
Task: "Implement submodule_checker.py to detect missing submodules"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Pipeline Execution)
4. **STOP and VALIDATE**: Test pipeline execution with mocks
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Verification)
4. Add User Story 3 → Test independently → Deploy/Demo (Reporting)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Pipeline)
   - Developer B: User Story 2 (Verification) - *Note: Requires US1 output*
   - Developer C: User Story 3 (Reporting) - *Note: Requires US1 & US2 output*
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
- **CPU Constraint**: Ensure all tasks strictly avoid GPU/CUDA operations.
- **Mocking**: All external API calls in US1 must use mocks or `--dry-run` to ensure CI feasibility.
