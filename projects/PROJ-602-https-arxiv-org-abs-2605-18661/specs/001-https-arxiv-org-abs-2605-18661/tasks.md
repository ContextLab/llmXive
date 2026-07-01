# Tasks: AI for Auto-Research: Roadmap & User Guide Reproduction

**Input**: Design documents from `/specs/602-reproduce-auto-research/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `src/`, `tests/`, `external/`, `output/`, `logs/` and `__init__.py` files in each.
- [X] T002 Initialize Python 3.11 project with pytest, pyyaml, requests, matplotlib, pandas, sentence-transformers, tenacity, and torch (CPU-only) dependencies
- [X] T003 [P] Generate `research.md` (Phase 0/1 output) documenting the reproduction study's initial hypotheses and methodology.
- [X] T004 [P] Generate `quickstart.md` (Phase 1 output) with execution instructions for Mock Mode and Real Mode.
- [X] T005 [P] Generate `data-model.md` (Phase 1 output) defining the schema for Reproduction Run, Generated Artifact, and Validation Report.
- [X] T006 [P] Generate `contracts/` directory (Phase 1 output) containing API interface definitions or OpenAPI specs for internal modules.
- [X] T007 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T008 [P] Implement `src/models/entities.py` to define the `Reproduction Run` entity schema (run ID, start time, artifact set) matching `data-model.md`.
- [X] T009 [P] Initialize `external/awesome-ai-auto-research` git submodule (URL: `) and verify entry point `main.py` accessibility.
- [X] T010 [P] Setup environment configuration management (loading API keys, mock mode flags) in `src/utils/config.py`
- [X] T011 [P] Implement `src/utils/cuda_patcher.py` to force `torch.set_device('cpu')` and mock `torch.cuda.is_available()` to return `False`. **Crucial**: If vendor code crashes despite patching, log error and exit with 'GPU Required' code (no silent failure).
- [X] T012 [P] Setup logging infrastructure in `src/utils/logging.py` to capture API interactions and resource usage to `logs/api_usage.json`
- [X] T013 [P] Create base data structures for `Generated Artifact` and `Validation Report` entities in `src/models/entities.py` (matching `data-model.md` schema).
- [X] T014 [P] Implement retry mechanism with exponential backoff (using `tenacity`) for external calls in `src/utils/retry.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Run the vendored pipeline on CPU-only CI, ensuring it exits 0 and produces 3 distinct artifact types (text, figure, data) without GPU errors.

**Independent Test**: The CI job executes the entry script, completes within 6 hours, and the output directory contains at least one `.md`, one `.png`, and one `.csv` (or equivalent) file.

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `src/mocks/llm_mock.py` to generate deterministic, short text blocks if the vendor code requires LLM inference (CPU-safe fallback). **Note**: This is a Structural Mock; Real Mode validation is deferred to the report.
- [X] T016 [US1] Implement `src/reproduction/pipeline_runner.py` to execute the vendor entry point, inject the CUDA patcher (T011), and apply retry logic. **Crucial**: If vendor code fundamentally relies on GPU kernels, fail gracefully with 'GPU Required' error (no silent mock).
- [X] T017 [US1] Implement logic in `pipeline_runner.py` to detect and handle "Mock Mode" vs "Real Mode" based on environment variables.
- [X] T018 [US1] Add validation in `pipeline_runner.py` to ensure the output directory contains at least 3 distinct artifact types (`.md`, `.png`, `.csv`) with size > 0 bytes AND no placeholder content (e.g., "TODO", "Lorem Ipsum").
- [X] T019 [US1] Implement error handling in `pipeline_runner.py` to fail gracefully with clear messages if required environment variables are missing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests are written BEFORE implementation but executed AFTER.

- [X] T020 [P] [US1] Unit test for `cuda_patcher.py` verifying `torch.cuda.is_available()` returns `False` in `tests/unit/test_cuda_patcher.py`.
- [X] T021 [P] [US1] Unit test for `retry.py` verifying exponential backoff logic in `tests/unit/test_retry.py`.
- [X] T022 [P] [US1] Unit test for retry mechanism with simulated rate limit (Mock Mode) in `tests/unit/test_retry_mock.py` to verify retry logic triggers even without real API calls.
- [X] T023 [P] [US1] Integration test for pipeline execution in `tests/integration/test_pipeline_e2e.py` (mocked API calls, asserts exit code 0 and artifact existence).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Artifact Integrity Against Paper Claims (Priority: P2)

**Goal**: Compare generated artifacts against paper claims (cost, fabrication, novelty) and report pass/fail status.

**Independent Test**: A validation script parses artifacts, calculates cost from logs, checks for fabrication markers, and outputs a structured validation report.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement `src/models/entities.py` to define the `Validation Report` entity schema (score, rate, flags) matching `data-model.md`.
- [X] T025 [P] [US2] Implement `src/reproduction/cost_estimator.py` to parse `logs/api_usage.json` and calculate total cost (or "N/A" if mock mode). **Depends on T016 output: logs/api_usage.json**.
- [X] T026 [P] [US2] Implement `src/reproduction/validation.py` with structural checks (empty strings, "TODO" markers, placeholder detection) for fabrication detection.
- [X] T027 [US2] Implement logic to compute a `fabrication_score` [0.0, 1.0] using formula: `score = 0.6 * heuristic_score + 0.4 * semantic_score` (if semantic available, else `heuristic_score`). Flag scores > 0.8 as "Fabrication Detected".
- [X] T028 [US2] Implement image validation in `validation.py` to check file headers of generated figures for validity.
- [X] T029 [US2] Implement logic to report a `fabrication_rate` (percentage of checked items flagged) alongside the score.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US2] Unit test for `cost_estimator.py` verifying cost calculation from sample API logs in `tests/unit/test_cost_estimator.py`.
- [X] T031 [P] [US2] Unit test for `validation.py` verifying fabrication detection heuristics in `tests/unit/test_validation.py`.
- [X] T032 [P] [US2] Integration test for validation pipeline in `tests/integration/test_validation_e2e.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Document Methodological Limitations and Failure Modes (Priority: P3)

**Goal**: Generate `REPRODUCTION_REPORT.md` with structured summary of deviations, failure modes, and limitations.

**Independent Test**: The report generation script produces a markdown file containing a "Limitations" section with at least two explicit deviations.

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement `src/reproduction/report_generator.py` to aggregate logs, validation results, and environment info. **Depends on T024 (Validation Report entity), T025 (Cost Estimator), T027 (Fabrication Score)**.
- [X] T034 [US3] Implement logic in `report_generator.py` to explicitly state "No GPU detected" and detail CPU adaptation/failure modes.
- [X] T035 [US3] Implement logic to detect and list hallucinated citations or content degradation using regex for citation patterns and string matching against known hallucination sets.
- [X] T036 [US3] Implement "Methodological Deviation" section generation, listing at least one constraint imposed by the free-tier CI environment.
- [X] T037 [US3] Ensure report explicitly marks "Cost" and "True Novelty" claims as "Unverifiable" if Mock Mode was active.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T038 [P] [US3] Unit test for `report_generator.py` verifying report structure generation in `tests/unit/test_report_generator.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `README.md` with execution instructions for Mock Mode and Real Mode.
- [X] T040 [P] Run `quickstart.md` validation: Execute `python -m src.main --validate` and assert exit code 0.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on artifacts generated by US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on validation results from US2

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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