# Tasks: DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards

**Input**: Design documents from `/specs/619-delta-discriminative-token-credit-assign/`
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

**Purpose**: Project initialization, constitution compliance, and basic structure

- [X] T000 [P] Create `constitution.md` file defining project principles and constraints to satisfy Spec Kit protocol (Plan Compliance)
- [X] T001a [P] Create project directories: `mkdir -p scripts external/dlbook_notation tests/unit tests/contract tests/integration`
- [X] T001b [P] Initialize Git repository and create `.gitmodules` file for `external/dlbook_notation`
- [X] T002 [P] Initialize Bash/LaTeX project configuration (`.gitignore`, `Makefile` stub)
- [X] T003 [P] Configure linting and formatting tools for shell scripts (e.g., `shellcheck` config)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Define specification for `scripts/validate-deps.sh` (dependency check logic)
- [X] T005 [P] Define specification for `scripts/setup-plan.sh` (submodule initialization logic)
- [X] T006 [P] Define error handling framework for missing dependencies (exit codes & messages)
- [X] T007 [P] Define base validation logic for submodule commit hash verification against `SubmoduleMetadata` schema
- [X] T008 [P] Configure resource monitoring (CPU/RAM) for build execution
- [X] T009 [P] Setup environment configuration for CI runner (ubuntu-latest)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Code Verification (Priority: P1) 🎯 MVP

**Goal**: Initialize the project environment, clone the vendored `dlbook_notation` submodule, and verify codebase structure matches the paper's description.

**Independent Test**: A researcher can run a single validation command to confirm the presence of all required files (`make.sh`, `notation.tex`, `README.md`) and that the git submodule points to the correct commit hash.

### Implementation for User Story 1

- [X] T012 [US1] Implement `scripts/setup-plan.sh` to clone `external/dlbook_notation` and verify `make.sh`, `notation.tex`, `venn.pdf` presence (FR-001)
- [X] T013 [US1] Implement submodule commit hash verification logic in `scripts/validate-submodule.sh` validating against `SubmoduleMetadata` schema (FR-001)
- [X] T014 [US1] Implement `scripts/validate-deps.sh` to check for `pdflatex`, `bibtex` and exit with specific error codes if missing (FR-005)
- [X] T015 [US1] Add error handling for "Submodule commit not found" scenario in `scripts/setup-plan.sh`
- [X] T016 [US1] Add logging for initialization steps in `scripts/setup-plan.sh`

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to verify scripts**

- [X] T010 [P] [US1] Integration test for `setup-plan.sh` submodule clone logic in `tests/integration/test_setup.sh`
- [X] T011 [P] [US1] Integration test for `validate-deps.sh` dependency check logic in `tests/integration/test_deps.sh`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - End-to-End Execution and Artifact Generation (Priority: P2)

**Goal**: Execute the primary entry point (`make.sh`) to generate paper's core artifacts (PDFs) on CPU-only infrastructure.

**Independent Test**: A researcher can run the build script and verify the existence of generated artifacts (`notation_example.pdf`, `venn.pdf`) within a defined directory structure.

### Implementation for User Story 2

- [X] T019 [US2] Implement `scripts/run-build.sh` wrapper to execute `./make.sh` in `external/dlbook_notation` with timeout (6h) and resource limits (FR-002)
- [X] T020 [US2] Implement logic to scan `external/dlbook_notation` (including .tex and .cfg files) for hardcoded GPU/CUDA device assignments (`device="cuda"`, `load_in_8bit`) and fail if found (FR-006)
- [X] T021 [US2] Implement artifact generation verification in `scripts/validate-build.sh` to check for `notation_example.pdf` and `venn.pdf` (FR-003)
- [X] T022 [US2] Add file size check (>50KB) for generated PDFs in `scripts/validate-build.sh` (FR-003, SC-002)
- [X] T023 [US2] Add error messaging for "Build failed" scenarios in `scripts/run-build.sh` (FR-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduction Report and Validation Summary (Priority: P3)

**Goal**: Generate a summary report mapping execution results to paper's claims, explicitly addressing "verifiable rewards" and external observability as per research review.

**Independent Test**: A researcher can inspect the generated `reproduction_report.md` and verify it contains a section confirming execution status and addressing the "verifiable rewards" claim based on code logic.

### Implementation for User Story 3

- [X] T026 [US3] Implement `scripts/generate-report.sh` to compile findings into `reproduction_report.md` (FR-004)
- [X] T027 [US3] Add logic to explicitly state "Status: Success/Partial/Failed" in `reproduction_report.md` (FR-004, SC-003)
- [X] T028 [US3] Scan codebase for "Discriminative Token Credit Assignment" logic; explicitly report "Not Found" in LaTeX source but confirm the build mechanism for benchmarks is defined in plan.md (US-3, FR-004)
- [X] T029 [US3] Scan `external/dlbook_notation` for text definitions of "verifiable rewards" and external observable states; explicitly report "Not Found" if absent (US-3)
- [X] T030 [US3] Add section in `reproduction_report.md` explicitly documenting the absence of dynamic reward signals in the static LaTeX code (US-3)
- [X] T031 [US3] Add note in `reproduction_report.md` that 7 benchmarks were not re-run, confirming the mechanism is defined in the plan but not implemented in the code (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Update `README.md` with project structure and usage instructions
- [X] T032b [P] Update `quickstart.md` with step-by-step build instructions
- [X] T032c [P] Update script documentation in `docs/` for `scripts/`
- [X] T033a [P] Refactor error handling into common `scripts/common.sh` functions
- [X] T033b [P] Extract common functions from shell scripts to reduce duplication
- [X] T034a [P] Optimize build scripts by parallelizing LaTeX compilation where possible
- [X] T034b [P] Optimize I/O operations in build scripts to reduce disk usage
- [X] T035a [P] Unit test for `setup-plan.sh` in `tests/unit/test_setup.sh`
- [X] T035b [P] Unit test for `validate-deps.sh` in `tests/unit/test_deps.sh`
- [X] T035c [P] Unit test for `run-build.sh` in `tests/unit/test_build.sh`
- [X] T036 [P] Security hardening for script execution (input validation, safe paths)
- [X] T037 [P] Run `quickstart.md` validation to ensure instructions are accurate

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

- Tests (if included) MUST be written AFTER implementation to verify scripts
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
# Launch all implementation tasks for User Story 1 together:
Task: "Implement scripts/setup-plan.sh to clone external/dlbook_notation"
Task: "Implement scripts/validate-deps.sh to check for pdflatex"

# Launch all integration tests for User Story 1 together (after implementation):
Task: "Integration test for scripts/setup-plan.sh in tests/integration/test_setup.sh"
Task: "Integration test for scripts/validate-deps.sh in tests/integration/test_deps.sh"
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
- Verify tests run after implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence