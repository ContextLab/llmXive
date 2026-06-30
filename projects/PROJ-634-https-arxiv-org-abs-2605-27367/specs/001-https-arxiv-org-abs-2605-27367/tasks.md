# Tasks: Reproduce & Validate SpatialBench

**Input**: Design documents from `/specs/634-reproduce-spatialbench/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY - they are required by the implementation plan to ensure validation.

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

## Phase 0: Research & Feasibility

**Purpose**: Verify data availability, baseline sources, and CPU feasibility BEFORE implementation begins.
**⚠️ CRITICAL**: This phase produces `research.md` which determines the validation strategy (external vs. internal consistency).

- [X] T000 [P] [Research] Verify existence of `load_dtu.py` and `load_scannet.py` in `external/SpatialBench`; if missing, document manual download URLs in `research.md`.
- [X] T001 [P] [Research] Implement SHA-256 hash computation script for dataset archives; compare against paper's documented hashes; abort with `EXIT_CODE_DATA_MISSING` if mismatched.
- [X] T002 [P] [Research] Check for per-scene baseline metric files (`reference_results/*.json`); document presence/absence in `research.md`.
- [X] T003 [P] [Research] Document CPU-FP vs GPU-FP numerical drift estimation (cite literature); adopt a strict tolerance for external consistency and a tighter tolerance for internal consistency.
- [X] T004 [P] [Research] Design stratified sampling strategy: DTU scenes (low/medium depth), ScanNet scenes (indoor/outdoor), and a mixed-density scene.
- [X] T005 [P] [Research] Perform dry-run import of `external/SpatialBench` with `torch.set_default_device('cpu')`; confirm no CUDA import errors.
- [X] T006 [Research] Generate `specs/634-reproduce-spatialbench/research.md` containing dataset strategy, feasibility report, and baseline justification.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T007 Create project structure per implementation plan: `src/spatialbench_runner/`, `tests/`, `specs/634-reproduce-spatialbench/`
- [X] T008 Initialize Python 3.10+ project with `requirements.txt` (include `torch` with CPU-only wheel command: `pip install torch --index-url, plus numpy, pandas, matplotlib, seaborn, scikit-learn, pyyaml, psutil)
- [X] T009 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data models, contracts, and critical error handling logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 [P] Create `specs/634-reproduce-spatialbench/data-model.md` documenting `BenchmarkResults` and `MemoryLog` schemas; explicitly document that `delta3` is optional and that constraints reflect SC-002 (at least 3 models, 2 domains).
- [X] T011 [P] Create contract files: `specs/634-reproduce-spatialbench/contracts/benchmark_results.schema.yaml` and `memory_log.schema.yaml`.
- [X] T012 [P] Implement `src/spatialbench_runner/config.py` defining `MAX_RAM_MB = 6144`, CPU-only flags, and `EXIT_CODE_DATA_MISSING` constant.
- [X] T013 Implement `src/spatialbench_runner/runner.py` skeleton with `torch.set_default_device('cpu')` and memory watchdog logic.
- [X] T014 Implement `src/spatialbench_runner/metrics.py` skeleton for Abs Rel, δ1, δ2 calculation.
- [X] T015 Implement `src/spatialbench_runner/visualizer.py` skeleton for PNG/HTML generation.
- [X] T016 Write `src/spatialbench_runner/__init__.py` to expose public API.
- [X] T017 Draft `specs/634-reproduce-spatialbench/quickstart.md` with CPU-only install commands and usage examples.
- [X] T018 [P] Implement data loader verification logic in `src/spatialbench_runner/runner.py` (check for `load_dtu.py`, `load_scannet.py`; raise `DataLoaderMissingError` and exit with `EXIT_CODE_DATA_MISSING` if missing).
- [X] T019 [P] Implement internal consistency fallback logic in `src/spatialbench_runner/metrics.py` (trigger: if baseline file missing; run twice; check ≤0.1% variance; emit `EXIT_CODE_INTERNAL_VALIDATION` if active).
- [X] T020 [P] Implement timing guard in `src/spatialbench_runner/runner.py` to abort if wall-clock > 60 minutes (emit `EXIT_CODE_TIMEOUT`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate End-to-End Execution on CPU (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored `SpatialBench` benchmark on CPU-only CI, ensuring no crashes, valid artifacts, and strict memory adherence.

**Independent Test**: Run the benchmark entry point with `--device cpu` and `--num-scenes 1`. Verify exit code 0, non-empty `results_minimal.json`, and memory usage <7GB.

### Tests for User Story 1 (MANDATORY)

- [X] T021 [P] [US1] Contract test for output schema in `tests/contract/test_results_schema.py`
- [X] T022 [P] [US1] Integration test for CPU execution flow in `tests/integration/test_cpu_execution.py`

### Implementation for User Story 1

- [X] T023 [US1] Implement memory monitoring loop in `src/spatialbench_runner/runner.py` using `psutil` to abort if `ram_mb > MAX_RAM_MB`.
- [X] T024 [US1] Implement graceful GPU fallback in `src/spatialbench_runner/runner.py` (detect CUDA requirement; if missing, raise `EXIT_CODE_GPU_REQUIRED` or skip with clear log; ensure clean exit).
- [X] T025 [US1] Implement `--num-scenes` subset logic in `src/spatialbench_runner/config.py` and `runner.py`.
- [X] T026 [US1] Add logging for memory usage and skip events in `src/spatialbench_runner/runner.py`.
- [X] T027 [US1] Create `results_minimal.json` output generator in `src/spatialbench_runner/runner.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reproduce Key Quantitative Findings (Priority: P2)

**Goal**: Run benchmark on multiple scenes across 2 domains (DTU, ScanNet) and validate metrics against paper baselines (≤5% tolerance) or internal consistency.

**Independent Test**: Execute benchmark on 5 stratified scenes. Verify `metrics.py` calculates Abs Rel within 5% of paper baseline (or ≤0.1% variance if baseline missing).

### Tests for User Story 2 (MANDATORY)

- [X] T028 [P] [US2] Unit test for metric calculation accuracy in `tests/unit/test_metrics.py`
- [X] T029 [P] [US2] Integration test for baseline comparison logic in `tests/integration/test_baseline_validation.py`

### Implementation for User Story 2

- [X] T030 [P] [US2] Implement stratified scene sampling logic in `src/spatialbench_runner/config.py` (Multiple DTU, Multiple ScanNet, 1 mixed).
- [X] T031 [US2] Implement `metrics.py` Abs Rel, δ1, δ2 calculation logic with float32 precision enforcement.
- [X] T032 [US2] Implement baseline comparison logic in `src/spatialbench_runner/metrics.py` (conditional: if baseline file exists, load reference JSON, calculate relative error, enforce a predefined tolerance threshold; else, delegate to internal consistency logic).
- [X] T033 [US2] Integrate scene iteration loop in `src/spatialbench_runner/runner.py` to process scenes sequentially with `gc.collect()`.
- [X] T034 [US2] Run full integration test suite and verify all acceptance criteria (SC-001 to SC-005).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Validation Report & Visualization (Priority: P3)

**Goal**: Automatically generate `overview.png`, `memory_curve.png`, and an HTML report summarizing results.

**Independent Test**: Run `visualize_benchmark_web.py` on `results.json`. Verify 2 PNGs and 1 HTML report are generated with correct axes/labels.

### Tests for User Story 3 (MANDATORY)

- [X] T035 [P] [US3] Contract test for visualization file existence in `tests/contract/test_visualization_outputs.py`

### Implementation for User Story 3

- [X] T036 [P] [US3] Implement `memory_curve.png` generation in `src/spatialbench_runner/visualizer.py` (Memory vs. Scene Index for multiple scenes).
- [X] T037 [P] [US3] Implement `overview.png` generation (domain performance heatmap/table) in `src/spatialbench_runner/visualizer.py`.
- [X] T038 [US3] Implement HTML report generation in `src/spatialbench_runner/visualizer.py` (include run params, metrics summary).
- [X] T039 [US3] Integrate visualization trigger in `src/spatialbench_runner/runner.py` (run after all scenes processed).
- [X] T040 [US3] Add validation logic in `src/spatialbench_runner/visualizer.py` to ensure output files are non-empty and valid images.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Update `quickstart.md` with final CPU-only install commands and usage examples (if not done in Phase 2).
- [X] T042 Code cleanup and refactoring in `src/spatialbench_runner/`.
- [X] T043 Run `visualize_benchmark_web.py` validation to confirm artifact quality.
- [X] T044 Final review of `research.md` to ensure all limitations (subset size, tolerance justification) are documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion (feasibility confirmed)
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

- Tests (MANDATORY) MUST be written and FAIL before implementation
- Models/Config before logic
- Logic before integration
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
# Launch all tests for User Story 1 together (MANDATORY):
Task: "Contract test for output schema in tests/contract/test_results_schema.py"
Task: "Integration test for CPU execution flow in tests/integration/test_cpu_execution.py"

# Launch all logic tasks for User Story 1 together:
Task: "Implement memory monitoring loop in src/spatialbench_runner/runner.py"
Task: "Implement graceful GPU fallback in src/spatialbench_runner/runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (CPU run, no OOM, valid JSON)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Research + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Metrics validation)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualizations)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Research + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Execution & Memory)
 - Developer B: User Story 2 (Metrics & Baselines)
 - Developer C: User Story 3 (Visualizations)
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
- **Critical Constraint**: All tasks MUST run on CPU-only CI (low vCPU count, ~7GB RAM). No GPU, no 8-bit/4-bit quantization.
- **Mandatory Error Codes**: `EXIT_CODE_DATA_MISSING`, `EXIT_CODE_GPU_REQUIRED`, `EXIT_CODE_INTERNAL_VALIDATION`, `EXIT_CODE_TIMEOUT`, `EXIT_CODE_MEMORY_LIMIT`.