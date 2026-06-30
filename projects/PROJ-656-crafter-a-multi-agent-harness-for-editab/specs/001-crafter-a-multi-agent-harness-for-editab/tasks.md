# Tasks: Crafter Multi-Agent Harness Validation

**Input**: Design documents from `/specs/656-crafter-validation/`
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

- [X] T001 Create project directory structure: `external/Crafter`, `output/`, `logs/`, `tests/`
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (cpu-only torch, scikit-learn, requests, lxml, pyyaml)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management (load `OPENAI_API_KEY`, `CRAFTER_MODE` env vars; fail fast if missing in non-mock mode)
- [X] T005 Implement logging infrastructure to write structured agent interactions to `logs/agent_trace.log` (FR-005)
- [X] T006 Create base error handling utilities for API rate limiting (HTTP 429 backoff) and OOM detection
- [X] T007 [P] Verify `external/Crafter` submodule is cloned and accessible
- [X] T008 Validate `craftbench/manifest.json` exists and is parseable
- [X] T017 [P] Implement global timeout enforcement utility in `src/utils/timeout.py` to enforce 6-hour timeout specifically for Full-Run mode (SC-003)
- [X] T018 [P] Implement log role validator in `src/utils/log_validator.py` to enforce presence of ≥3 distinct agent roles and fail the build if SC-004 is not met (SC-004)
- [X] T031 [P] Create logging utility in `src/utils/logger.py` to inject '[MOCK]' or '[REAL]' tags into agent trace entries (PRINCIPLE IV)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End-to-End Reproduction (Priority: P1) 🎯 MVP

**Goal**: Validate the `Crafter` harness can ingest a paper excerpt and generate a figure (or mock equivalent) without runtime errors.

**Independent Test**: Execute `inference.py` with sample input; verify output file exists and `agent_trace.log` is populated.

### Implementation for User Story 1

- [X] T011 [US1] Scaffold `inference.py` entry point to handle `CRAFTER_MODE=mock` vs `full` execution paths
- [X] T009 [P] [US1] Contract test for `inference.py` exit codes in `tests/integration/test_inference.py`
- [X] T010 [P] [US1] Integration test for mock mode execution in `tests/integration/test_mock_mode.py`
- [X] T012 [US1] Implement input chunking logic for large papers (>50 pages) to prevent OOM (Edge Case: Memory Constraints)
- [X] T013 [US1] Integrate rate-limit backoff logic (configurable wait time, a configurable number of retries) for external API calls
- [X] T014 [US1] Ensure `inference.py` logs distinct agent roles (Planner, Drawer, Critic) to `logs/agent_trace.log` (FR-005, SC-004)
- [X] T015 [US1] Implement output validation logic for `output_figure.png`: verify file size > 1KB, PNG magic bytes (0x89504E47), and dimensions > 0 (FR-001, US-1 Acceptance 2)
- [X] T016 [US1] Add "Fail Fast" check for missing API keys (exit non-zero within 30s) (FR-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validation of Editable SVG Conversion (Priority: P2)

**Goal**: Confirm `CraftEditor` converts raster images to editable SVGs preserving semantic structure.

**Independent Test**: Run `convert.py` on a raster image; inspect SVG for valid XML and editable text nodes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for SVG XML validity in `tests/contract/test_svg_schema.py`
- [X] T018 [P] [US2] Integration test for text element extraction in `tests/integration/test_svg_conversion.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement `convert.py` wrapper to handle raster-to-SVG conversion and create mock raster input generator for CI validation (US-2, Independent Test)
- [X] T020 [US2] Add XML parsing error handling to log specific line numbers on malformed SVG (Edge Case: SVG Parsing Failures)
- [X] T021 [US2] Create function `validate_svg_text_elements(svg_path: str) -> bool` in `src/utils/svg_validator.py` to guarantee presence of `<text>` or `<tspan>` elements (FR-002)
- [X] T022 [US2] Implement logic to verify presence of `<path>`, `<rect>`, or `<line>` elements (FR-002)
- [X] T023 [US2] Create a "Mock SVG" generator in `src/utils/mock_svg.py` that produces SVGs with text elements to satisfy FR-002 structural requirements in CI (NOTE: This satisfies pipeline integrity (PI-002) but does NOT satisfy SC-002 quality metrics)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Benchmark Evaluation Execution (Priority: P3)

**Goal**: Execute `CraftBench` to reproduce quantitative metrics and verify evaluation infrastructure.

**Independent Test**: Run evaluation script; verify JSON report with `success_rate`, `quality_score`, and `editability_score`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for evaluation report JSON schema in `tests/contract/test_eval_report.py`
- [X] T025 [P] [US3] Integration test for partial failure handling in `tests/integration/test_eval_robustness.py`

### Implementation for User Story 3

- [X] T032 [US3] Update evaluation report schema in `contracts/evaluation_report.schema.yaml` to include `design_origin` field clarifying that the harness executes instructions, not generates scientific hypotheses (PRINCIPLE IV)
- [X] T026 [US3] Implement wrapper for `python -m craftbench.evaluation.run_eval`
- [X] T027 [US3] Implement error handling to log failures and continue (not crash) on individual sample timeouts (US-3, Acceptance 3)
- [X] T028 [US3] Implement success rate calculation in `src/utils/report_generator.py` and add assertion in `tests/contract/test_eval_report.py` to enforce ≥90% threshold (fail the build if not met) (SC-001, FR-003)
- [X] T029 [US3] Calculate quality_score and editability_score ONLY in Full-Run mode. In Dry-Run, set these to N/A to prevent false validation (SC-002, US-3 Acceptance 2)
- [X] T030 [US3] Create `src/utils/seo_metric.py` to implement Structural Element Overlap (SEO) comparison logic against ground truth for SC-002 validation (SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior reviews

- [X] T033 [P] Add a `CONTRIBUTING.md` or `README` section clarifying the "Loom vs. Flower" analogy for future researchers (Addressing Reviewer Concern)
- [X] T034 [US2] Ensure SVG generation tasks log the source of the "design" (e.g., "Data derived from input prompt") to maintain transparency (PRINCIPLE IV)
- [X] T035 [P] Documentation updates in `quickstart.md` regarding `CRAFTER_MODE` usage
- [X] T038 [P] Additional unit tests for edge cases (API 429, OOM) in `tests/unit/`
- [X] T039 Run `quickstart.md` validation to ensure all entry points work as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 generating the raster image (or mock equivalent)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for data generation if running full evaluation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for inference.py exit codes in tests/integration/test_inference.py"
Task: "Integration test for mock mode execution in tests/integration/test_mock_mode.py"

# Launch all models for User Story 1 together:
Task: "Implement input chunking logic for large papers in src/utils/chunker.py"
Task: "Implement rate-limit backoff logic in src/utils/api_client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Mock Mode)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Polish (Phase 6) → Clarify "Loom vs. Flower" distinction
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Inference)
   - Developer B: User Story 2 (SVG Conversion)
   - Developer C: User Story 3 (Evaluation)
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
- **Feasibility Check**: All tasks assume CPU-only execution; no GPU-dependent model loading is permitted. Large models are replaced with mock logic or CPU-tractable alternatives.