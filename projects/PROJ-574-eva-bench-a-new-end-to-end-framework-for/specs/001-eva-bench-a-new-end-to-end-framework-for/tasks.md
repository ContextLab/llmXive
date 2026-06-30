# Tasks: EVA-Bench Reproduction & Validation

**Input**: Design documents from `/specs/574-eva-bench-reproduction/`
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

- [X] T001a [P] Create directory `external/` in repository root
- [X] T001b [P] Create directory `scripts/` in repository root
- [X] T001c [P] Create directory `reports/` in repository root
- [X] T001d [P] Create directory `contracts/` in repository root
- [X] T001e [P] Create placeholder file `external/dlbook_notation/.gitkeep`
- [X] T001f [P] Create placeholder file `scripts/validate_build.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Bash/Python project environment (ensure `texlive-full`, `ghostscript` availability in CI)
- [X] T003 [P] Configure linting and formatting tools (shellcheck, black)
- [X] T004 Create `contracts/build_artifacts.schema.yaml` defining PDF size/content constraints
- [X] T005 Create `contracts/reproduction_report.schema.yaml` defining report structure
- [X] T006 [P] Create `.github/workflows/reproduction.yml` with a job that: checks out repo, installs `texlive-full` (pinned version), installs `fonts-noto` and `fonts-dejavu`, and runs `external/dlbook_notation/make.sh`
- [X] T007 Initialize `external/dlbook_notation` as a git submodule and verify checkout
- [X] T008 Create base validation helper script `scripts/validate_build.py` skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproduce Core Execution Flow (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored `dlbook_notation` codebase end-to-end on a standard CPU-only CI runner and confirm it produces expected output artifacts without GPU errors.

**Independent Test**: Run `./make.sh` on a fresh GitHub Actions runner; verify exit code 0 and existence of `notation_example.pdf` within 300s.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests must be defined before implementation (T012-T016). Once defined, T010 and T011 can run in parallel with each other, but logically precede the implementation tasks.

- [X] T010 [P] [US1] Contract test for build execution in `tests/contract/test_build_execution.py`
- [X] T011 [P] [US1] Integration test for script runtime in `tests/integration/test_script_runtime.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `scripts/run_build.sh` to invoke `external/dlbook_notation/make.sh` with timeout constraints
- [X] T013 [US1] Add logic to capture `stderr` and scan for "CUDA", "GPU", or hardware-specific dependency errors; write detected errors to `reports/build_errors.log`
- [X] T014 [US1] Implement logic to verify `notation_example.pdf` exists in `external/dlbook_notation/` after execution
- [X] T015 [US1] Add logging for build duration and exit codes to `reports/build_log.txt`
- [X] T016 [US1] Ensure `run_build.sh` exits with code 0 only if: exit code is 0, `notation_example.pdf` exists, `reports/build_log.txt` exists, and no GPU errors are found in stderr
- [X] T019a [US1] Verify existence and non-empty content of the required text log file artifact `reports/build_log.txt` as per FR-002

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Artifact Fidelity (Priority: P2)

**Goal**: Verify that the generated artifacts (PDFs/figures) match visual/structural descriptions in the EVA-Bench paper (content validity, not just existence).

**Independent Test**: Check generated PDF file size (>50KB, <10MB) and extract text to confirm presence of "EVA-A" and "EVA-X" metric definitions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for PDF content extraction in `tests/contract/test_pdf_content.py`
- [X] T025 [P] [US2] Integration test for artifact size validation in `tests/integration/test_artifact_fidelity.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `scripts/validate_artifacts.py` to check file size of `notation_example.pdf` (50KB < size < 10MB) AND use ghostscript (`gs`) to verify PDF renders without fatal errors (Note: depends on T012 completing)
- [X] T021 [US2] Implement text extraction logic (using `pdftotext` or `ghostscript`) from `external/dlbook_notation/notation_example.pdf`
- [X] T022 [US2] Add regex/pattern matching to verify "EVA-A" and "EVA-X" strings exist in extracted text
- [X] T023 [US2] Integrate validation results into `reports/build_log.txt` by appending a JSON block with validation status and metrics
- [X] T024 [US2] Ensure `validate_artifacts.py` returns non-zero exit code if FR-004 (content validity) fails

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Document Reproduction Constraints & Discrepancies (Priority: P3)

**Goal**: Generate a `reproduction_report.md` that logs deviations, warnings, and execution status for transparency.

**Independent Test**: Verify `reports/reproduction_report.md` exists and contains "Pass/Fail" status, warnings, and error logs if applicable.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for report generation in `tests/contract/test_report_generation.py`
- [X] T028 [P] [US3] Integration test for discrepancy logging in `tests/integration/test_discrepancy_logging.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `scripts/generate_report.py` to aggregate build logs, validation results, and error streams
- [X] T030 [US3] Format output into `reports/reproduction_report.md` following `contracts/reproduction_report.schema.yaml`, ensuring it includes listed warnings and constraints (e.g., TeX Live version) and at least one warning or constraint as per US3-Scenario 2
- [X] T031 [US3] Add logic to detect and list specific constraints (e.g., "Assumed TeX Live 2023", "No GPU available")
- [X] T032 [US3] Ensure report includes "Last 10 lines of error log" if a build failure occurs (FR-005)
- [X] T033 [US3] Integrate report generation as the final step of the CI workflow by adding a new job step in `.github/workflows/reproduction.yml` that runs `scripts/generate_report.py` after the validation job

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `docs/` (README, quickstart)
- [X] T035 Code cleanup and refactoring of validation scripts
- [X] T036 Performance optimization (ensure build < 300s target)
- [X] T037 [P] Additional unit tests for validation logic in `tests/unit/`
- [X] T038 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 producing artifacts
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 results to generate report

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
Task: "Contract test for build execution in tests/contract/test_build_execution.py"
Task: "Integration test for script runtime in tests/integration/test_script_runtime.py"

# Launch all models for User Story 1 together:
Task: "Implement scripts/run_build.sh"
Task: "Add logic to capture stderr and scan for CUDA errors"
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