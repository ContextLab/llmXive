# Tasks: Validate Express.js Submodule Execution

**Input**: Design documents from `/specs/001-validate-express-submodule/`
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

- [X] T001 Create directory structure: `src/`, `tests/`, `scripts/`, `logs/`, `data/`
- [X] T002 Generate `quickstart.md` with setup instructions and validation workflow content for the project
- [X] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Verify `external/express` submodule integrity: check `git status` is clean, `package.json` exists, and file count > 100 in `external/express`
- [X] T005 Install Node.js dependencies for `external/express` submodule without errors (FR-001) (Depends on T004)
- [X] T006 [P] Verify `node_modules` directory exists and contains express core
- [X] T007 Create `scripts/validate-express.js` orchestration script structure
- [X] T008 Configure error handling for missing dependencies (Edge Case: `node_modules` missing)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate Core HTTP Functionality (Priority: P1) 🎯 MVP

**Goal**: Confirm that the vendored `express` submodule is a functional, runnable Node.js web framework capable of handling standard HTTP requests.

**Independent Test**: Start the `hello-world` example server and successfully send a `curl` request to the root path, receiving a valid HTTP 200 response with "Hello World" text.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Write contract test for root endpoint in `tests/contract/test_hello_world.js`
- [X] T010 [P] [US1] Write integration test for 404 handling in `tests/integration/test_404_handling.js`

### Implementation for User Story 1

- [X] T011 [US1] Start `hello-world` example server: run `node external/express/examples/hello-world/index.js` on port 3000; verify port is open via `lsof -i:3000` or `netstat` (FR-002)
- [X] T011b [US1] Wait for server readiness: poll ` with `curl` until a successful HTTP status code is received or timeout after 10s (Depends on T011; Pre-requisite for T012-T014)
- [X] T012 [US1] Verify HTTP GET `/` returns 200 status and "Hello World" body using `curl -s -o /dev/null -w '%{http_code}' (FR-003, SC-002) (Depends on T011b)
- [X] T013 [US1] Verify HTTP GET `/nonexistent` returns 404 status (FR-007, US-1 Acceptance Scenario 2) (Depends on T011b)
- [X] T014 [P] [US1] Verify HTTP GET `/json` (if available) returns `Content-Type: application/json` (US-1 Acceptance Scenario 3) (Depends on T011b)
- [X] T015 [US1] Handle EADDRINUSE error gracefully if port 3000 is busy (Edge Case)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Built-in Test Suite (Priority: P2)

**Goal**: Verify the internal consistency and regression status of the vendored code by running the project's own test suite.

**Independent Test**: Execute `npm test` in `external/express` and observe a pass/fail summary where the total number of failing tests is zero.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Write contract test for test suite execution in `tests/contract/test_suite_execution.js`

### Implementation for User Story 2

- [X] T017 [US2] Execute `npm test` in `external/express` directory; capture output to `logs/test-results.log` and grep for failure count (FR-004)
- [X] T018 [US2] Parse `logs/test-results.log` to report the exact failure rate (e.g., "X failing, Y passing") as required by FR-004 (SC-001 analysis)
- [X] T019 [P] [US2] If `test/acceptance/ejs.js` exists, execute it; otherwise skip and log "Test file not found" (US-2 Scenario 2)
- [X] T020 [US2] Verify process exit code is 0 upon completion (US-2 Scenario 3)
- [X] T021 [US2] Validate total execution time < 60 seconds (SC-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Middleware and View Rendering (Priority: P3)

**Goal**: Confirm that the submodule supports advanced features (middleware chains, templating engines like EJS) required for complex agent interactions.

**Independent Test**: Run the `ejs` example, request the page, and verify the rendered HTML contains the expected dynamic data.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Write contract test for EJS rendering in `tests/contract/test_ejs_rendering.js`
- [X] T023 [P] [US3] Write integration test for session state in `tests/integration/test_auth_session.js`

### Implementation for User Story 3

- [X] T024a [P] [US3] Verify `external/express/examples/ejs` directory exists
- [X] T024 [P] [US3] Start `ejs` example server: run `node external/express/examples/ejs/app.js` on port 3001 (FR-005)
- [X] T025 [US3] Verify rendered HTML contains "Hello EJS" or equivalent dynamic content using `curl` (SC-003) (Depends on T024)
- [X] T026a [P] [US3] Verify `external/express/examples/auth` directory exists
- [X] T026 [P] [US3] Start `auth` example server: run `node external/express/examples/auth/index.js` on port 3002 (FR-006)
- [X] T027 [US3] Submit valid login credentials via POST and verify `Set-Cookie` header is present (SC-004, US-3 Acceptance Scenario 2) (Depends on T026)
- [X] T028 [US3] Verify redirect to protected resource after login (US-3 Acceptance Scenario 2) (Depends on T027)
- [X] T029a [P] [US3] Verify `external/express/examples/mvc` directory exists
- [X] T029 [P] [US3] Start `mvc` example server: run `node external/express/examples/mvc/app.js` on port 3003 and verify `/users` renders HTML list (US-3 Acceptance Scenario 1)
- [X] T030a [P] [US3] Verify `external/express/examples/error-pages` directory exists
- [X] T030 [P] [US3] Start `error-pages` example: run `node external/express/examples/error-pages/app.js` on port 3004; trigger error via `/error` route and verify custom 500 page renders (US-3 Acceptance Scenario 3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Update `specs/001-validate-express-submodule/research.md`: Add "Validation Results" section with test log summary and "Known Issues" section with skipped tests (e.g., missing examples)
- [X] T032 Code cleanup and refactoring of `scripts/validate-express.js`
- [X] T033 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T034 Run `quickstart.md` validation to ensure all paths are correct and commands work as documented (Depends on T002)
- [X] T035 Generate final validation report summarizing FR-001 through FR-007 compliance

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
Task: "Write contract test for root endpoint in tests/contract/test_hello_world.js"
Task: "Write integration test for 404 handling in tests/integration/test_404_handling.js"

# Launch all models for User Story 1 together:
Task: "Start hello-world example server from external/express/examples/hello-world"
Task: "Verify HTTP GET / returns 200 status and Hello World body"
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