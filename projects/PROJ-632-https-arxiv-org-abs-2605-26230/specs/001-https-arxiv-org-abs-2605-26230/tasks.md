# Tasks: Reproduce & Validate Geometry-Aware Representation Denoising (GARD)

**Input**: Design documents from `/specs/001-reproduce-gard/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-632-https-arxiv-org-abs-2605-26230/`)
- [X] T002 Initialize Python 3.10 project with CPU-only PyTorch, Open3D, Pillow, NumPy, scikit-image, and lpips dependencies in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `src/config.py` to load environment variables and enforce `device='cpu'`
- [X] T005 [P] Implement pre-flight GPU/CUDA detector in `src/validators.py` to abort execution if CUDA is requested (FR-001, SC-004)
- [X] T006 Create `src/run_gard.py` entry point wrapper that handles timeouts and OOM diagnostics (FR-004, SC-005)
- [X] T007 Define `data/gard_input.schema.yaml` to validate input dataset structure before processing
- [X] T008 [US1] Define `data/gard_input.schema.yaml` schema content and validation rules (FR-003)
- [X] T009 Setup `outputs/geometry/` and `outputs/images/` directory creation logic in the entry point

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute GARD Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored GARD code on a CPU-only runner with a sample degraded dataset to generate 3D geometry and restored images.

**Independent Test**: The CI job runs `src/run_gard.py` with `data/da3_sample`; exits with code 0 and produces `.ply` and `.png` files in `outputs/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for GPU detector in `tests/unit/test_gpu_abort.py`
- [X] T011 [P] [US1] Unit test for missing data error message in `tests/unit/test_missing_data.py`
- [X] T012 [P] [US1] Integration test for full pipeline execution in `tests/integration/test_integration_real_call.py`

### Implementation for User Story 1

- [X] T013 [US1] Vendor and verify `external/GARD` code is read-only and compatible with CPU (check for hardcoded CUDA); generate `external/GARD/compatibility_report.md` listing any hardcoded CUDA calls found (FR-001)
- [X] T017 [US1] Create sample `data/da3_sample` dataset using REAL degraded images from the DA3 benchmark (NO mocks) conforming to `gard_input.schema.yaml` for CI testing (FR-003, SC-001)
- [X] T014 [US1] Implement loader logic in `src/data_loader.py` to fetch or validate `data/da3_sample` multi-view images against `data/gard_input.schema.yaml` (Depends on: T008, T017)
- [X] T015 [US1] Implement `src/run_gard.py` wrapper to invoke GARD inference with CPU device override
- [X] T016 [US1] Implement `src/run_gard.py::process_batch()` to handle memory limits (<7GB) via chunking by view, returning a list of partial results; this is a wrapper-level strategy, no model modification (FR-004, SC-005)
- [X] T019 [US1] Implement the timeout watchdog logic in `src/run_gard.py` to enforce a predefined wall-clock time limit and trigger a graceful exit with diagnostics (FR-004)
- [X] T018 [US1] Verify pipeline produces `outputs/geometry/*.ply` and `outputs/images/*.png`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Output Artifacts Against Paper Claims (Priority: P2)

**Goal**: Validate that generated artifacts are loadable, non-empty, and perceptually superior to a Gaussian Blur baseline.

**Independent Test**: Automated script confirms `.ply` loads in Open3D, images load in PIL, and NIQE/LPIPS metrics beat the blur baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for geometry loadability in `tests/unit/test_loadability.py`
- [X] T021 [P] [US2] Unit test for blind metric calculation (NIQE/LPIPS) in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `src/validators.py` function to load `.ply` with Open3D and `.png` with PIL (FR-005, SC-002) (Depends on: T018)
- [X] T023 [US2] Implement `src/validators.py` function to generate a Gaussian Blur baseline from input images (Depends on: T018)
- [X] T024 [US2] Implement `src/validators.py::compute_metrics(input_path, output_path)` to compute NIQE and LPIPS comparing Output vs. Blur AND Output vs. Input, returning a dict `{niqe: float, lpips: float, structural_diff: bool}` (US-2, SC-002) (Depends on: T018)
- [X] T025 [US2] Implement `src/validators.py::evaluate_success(metrics)` to determine "Success" if `NIQE(Output) < NIQE(Blur)` and LPIPS indicates structural difference, returning a boolean and a reason string (US-2) (Depends on: T018)
- [X] T026 [P] [US2] Create `tests/unit/test_blur_baseline.py` to verify baseline generation logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Document Reproduction Fidelity (Priority: P3)

**Goal**: Generate `reproduction_report.md` summarizing execution status, artifacts, and fidelity to the paper.

**Independent Test**: `reproduction_report.md` exists in root, contains "Success"/"Partial Success", and cites specific artifacts and paper figures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for report generation logic in `tests/unit/test_report.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `src/report_generator.py` to aggregate metrics, file paths, and execution logs
- [X] T029 [US3] Implement logic in `src/report_generator.py` to read `data/paper_claims.yaml`, compare results against paper claims (arXiv:2605.26230), and append a "Fidelity Score" section citing specific figure numbers (SC-003)
- [X] T030 [US3] Implement logic to parse `data/paper_claims.yaml` for figure numbers and generate the citation section in `reproduction_report.md` (SC-003)
- [X] T031 [US3] Integrate report generation into `src/run_gard.py` to run automatically after successful validation
- [X] T032 [P] [US3] Verify `reproduction_report.md` content matches acceptance criteria (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `README.md` with explicit CPU-only execution instructions
- [X] T034 Code cleanup and refactoring of `src/run_gard.py`
- [X] T035 Performance optimization for memory usage in `src/data_loader.py`
- [X] T036 [P] Additional unit tests for edge cases (empty images, corrupted PLY) in `tests/unit/`
- [X] T037 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 outputs (artifacts) for validation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 for data to report

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
Task: "Unit test for GPU detector in tests/unit/test_gpu_abort.py"
Task: "Unit test for missing data error message in tests/unit/test_missing_data.py"
Task: "Integration test for full pipeline execution in tests/integration/test_integration_real_call.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data_loader.py to fetch or validate data/da3_sample multi-view images"
Task: "Create sample data/da3_sample dataset (or mock data) conforming to gard_input.schema.yaml for CI testing"
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