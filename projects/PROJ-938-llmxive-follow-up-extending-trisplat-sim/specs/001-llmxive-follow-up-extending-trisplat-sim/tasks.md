# Tasks: llmXive follow-up: extending TriSplat for CPU-only edge robotics

**Input**: Design documents from `/specs/001-llmxive-trisplat-ext/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure per `plan.md` - `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/`

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

- [ ] T001 Create project structure per `plan.md` in `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/`
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` including `torch`, `numpy`, `scipy`, `trimesh`, `pygltflib`, `datasets`, `scikit-learn`, `tqdm`, `pandas`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/cli.py` entry point with arguments: `--views`, `--timeout`, `--seed`, `--update-state`
- [X] T023 [P] Implement dynamic view count configuration in `code/cli.py` (FR-002) to support 2, 3, 4, 5 views as a prerequisite for batch orchestration
- [X] T005 [P] Create `code/data/loader.py` implementing RealEstate10K streaming via `datasets.load_dataset(..., streaming=True)` with explicit 320x240 downscaling logic (FR-003)
- [X] T006 [P] Implement `code/utils/mesh_utils.py` for mesh generation, validation (manifold check), and cleanup
- [X] T007 [P] Implement `code/utils/stats.py` for Shapiro-Wilk, paired t-test, and Wilcoxon signed-rank test logic (FR-005)
- [X] T008 [P] Create `code/models/trisplat_base.py` to load frozen TriSplat backbone weights in CPU-compatible mode
- [X] T009 [P] Create `code/models/geometry_only.py` stub (empty file) for the differentiable ray-surface intersection layer (FR-001)
- [X] T010 [P] Implement `code/data/metrics.py` for Chamfer Distance and PSNR calculation against ground truth
- [X] T011 [P] Setup `code/experiments/run_batch.py` orchestrator skeleton with N=20 scene limit and 6-hour timeout enforcement (FR-006). Note: T042 will handle N=50 stretch goal.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Geometry-Only Reconstruction (Priority: P1) 🎯 MVP

**Goal**: Run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints, producing a valid mesh within 30 minutes.

**Independent Test**: Execute pipeline on a single RealEstate10K scene (320x240) on CPU-only runner; verify valid `.obj`/`.ply` output within 30 mins.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/models/geometry_only.py` differentiable ray-surface intersection layer using local triangle connectivity and depth gradients (FR-001)
- [X] T016 [US1] Implement convergence detection in `code/models/geometry_only.py` with a configurable hard limit on the maximum number of iterations. and non-convergence logging (FR-007). **Note**: This task depends on T015 completion; [P] tag removed.
- [X] T017 [US1] Integrate `code/utils/mesh_utils.py` (from T006) into `code/experiments/run_batch.py` to produce valid `.obj`/`.ply` files (FR-004). **Note**: Consumes T006 logic, does not re-implement.
- [X] T018 [US1] Integrate `code/models/geometry_only.py` into `code/experiments/run_batch.py` to replace the learned refinement head
- [X] T019 [US1] **Reject monocular input (1 view)**: Implement strict rejection in `code/cli.py` and `run_batch.py`. If input views < 2, log **ERROR** with message "Monocular input not supported. Minimum 2 views required." and exit with code 1. (FR-002, US1). **Note**: Explicitly enforces 2-view minimum; no warning-only fallback.
- [X] T020 [US1] Implement corrupted/missing ground truth handling in `code/data/loader.py`: skip scene, log WARNING, and continue (Edge Case)
- [X] T040 [US1] Implement low-texture/non-convergence detection in `code/models/geometry_only.py`: detect via gradient variance, output a placeholder mesh, and log a distinct error flag "LOW_TEXTURE_CONVERGENCE_FAILED" (Edge Case)
- [X] T043 [US1] Implement general non-convergence handling in `code/models/geometry_only.py`: if the 100-iteration limit (T016) is hit for ANY reason (not just low-texture), generate a placeholder mesh and log an error flag "TIMEOUT_CONVERGENCE_FAILED" to satisfy FR-007 (Edge Case)

### Tests for User Story 1

> **NOTE**: Write these tests AFTER implementation to ensure they pass

- [X] T012 [P] [US1] Unit test for a bounded iteration limit in `code/models/geometry_only.py` (FR-007) in `tests/unit/test_geometry.py`
- [X] T013 [P] [US1] Integration test for single scene reconstruction pipeline in `tests/integration/test_single_scene.py`
- [X] T014 [P] [US1] Memory usage test verifying < 6 GB peak RAM in `tests/integration/test_memory_limits.py`

**Checkpoint**: User Story 1 is fully functional and testable independently on CPU

---

## Phase 4: User Story 2 - Sparsity Threshold Identification (Priority: P2)

**Goal**: Systematically vary input views (2, 3, 4, 5) to identify the sparsity threshold where geometric constraints fail.

**Independent Test**: Run pipeline on 20 scenes (or 50 if T042 triggers) with varying view counts; output structured log of Chamfer Distance/PSNR; perform statistical test to identify threshold.

### Implementation for User Story 2

- [X] T024 [US2] Implement batch orchestration in `code/experiments/run_batch.py` to process N=20 scenes (or N=50 if T042 triggers) across 2, 3, 4, and 5 view configurations (depends on T023)
- [X] T025 [US2] Implement metric logging in `code/experiments/run_batch.py` to output JSON logs with Chamfer Distance and PSNR per scene/view-count (FR-004)
- [X] T026 [US2] Implement statistical test logic in `code/utils/stats.py`: orchestrate normality check (T027) and conditional selection of t-test/Wilcoxon (FR-005)
- [X] T027 [US2] **Implement Shapiro-Wilk test**: Explicitly implement and log the Shapiro-Wilk normality test results in `code/utils/stats.py` as a distinct, verifiable unit of work to satisfy FR-005 requirement to perform all three tests.
- [X] T028 [US2] Integrate statistical results (T027, T026) into the final batch report JSON (FR-004)
- [X] T041 [US2] Implement threshold identification logic in `code/utils/stats.py`: Define a hard-coded constant `TOLERANCE_THRESHOLD = 0.15` (or CLI arg); calculate relative error increase against 5-view mean for each view count; identify the specific view count where this exceeds 15% tolerance; output result to `data/processed/threshold_result.json` (FR-005)

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for statistical significance logic (Shapiro-Wilk -> t-test/Wilcoxon) in `tests/unit/test_stats.py`
- [X] T022 [P] [US2] Integration test for batch processing with varying view counts in `tests/integration/test_sparsity_batch.py`

**Checkpoint**: User Story 2 is complete; sparsity threshold is identified and logged

---

## Phase 5: User Story 3 - Quantitative Fidelity and Latency Benchmarking (Priority: P3)

**Goal**: Compare inference latency and geometric fidelity of the geometry-only module against the baseline.

**Independent Test**: Run both methods on same hardware; compare latency and fidelity metrics.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement latency measurement wrapper in `code/experiments/run_batch.py` to record inference time per scene-config
- [X] T031 [US3] Implement baseline TriSplat execution logic in `code/experiments/run_batch.py`: **Explicitly enforce** 2-core CPU affinity (e.g., via `os.sched_setaffinity` or `taskset`) for **both** the baseline and the geometry-only module (T015/T018) to strictly match SC-001 requirements. Attempt execution on 2-core CPU. If it fails (CUDA error or timeout), log a JSON entry with `status: skipped`, `reason: baseline_cpu_unsupported`, and proceed. If it succeeds, record metrics (US-3 Acceptance 1)
- [X] T031b [US3] **Implement CPU affinity enforcement for geometry-only module**: Explicitly implement `os.sched_setaffinity` or `taskset` logic in `code/experiments/run_batch.py` to enforce 2-core CPU affinity for the geometry-only module (T015/T018) as required by SC-001, ensuring the primary hypothesis runs under strict CPU constraints.
- [X] T032 [US3] Implement comparative metric aggregation in `code/utils/stats.py` to calculate speedup ratio and PSNR delta (FR-004)
- [X] T033 [US3] Generate benchmark report CSV at `data/processed/benchmark_tradeoff.csv` with columns: `view_count`, `latency`, `chamfer_distance`, `psnr`, `baseline_latency` (if available)
- [X] T039 [US3] Generate visualization of trade-off curve: Create a plot (PNG/SVG) showing latency vs. Chamfer Distance for different view counts, saved to `data/processed/benchmark_tradeoff_plot.png` (US-3 Acceptance 3)

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for latency measurement wrapper in `tests/unit/test_latency.py`
- [X] T029 [P] [US3] Integration test for comparative benchmarking in `tests/integration/test_benchmark.py`

**Checkpoint**: All user stories are independently functional and benchmarked

---

## Phase 6: Stretch Goal & Polish

**Purpose**: Handling N=50 scenes and final validation

- [X] T042 [P] Implement N=50 stretch goal logic in `code/experiments/run_batch.py`: If N=20 scenes complete within 70% of the time budget, dynamically expand the scene list to 50 random scenes and continue processing (Plan: Stretch Goal)
- [X] T035 [P] Add checksumming logic for downloaded dataset shards in `code/data/loader.py` (Plan: Data Hygiene)
- [X] T044 [P] Implement data flow for checksums: Ensure `code/data/loader.py` (T035) writes computed checksums to a temporary JSON file (`data/processed/checksums_temp.json`) that `code/cli.py --update-state` (T034) ingests to satisfy Constitution Principle III (Plan: Data Hygiene). **Note**: Explicitly defines the producer-consumer chain for checksums to state file.
- [X] T034 [P] Implement `code/cli.py --update-state` command to compute SHA-256 hashes and update `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` (Plan: Post-Execution State Update). **Note**: Explicitly defines output path for state file.
- [X] T036 [P] Write comprehensive `README.md` and `quickstart.md` in `specs/001-llmxive-trisplat-ext/`
- [X] T037 [P] Validate all contracts (`contracts/*.schema.yaml`) against generated JSON outputs
- [X] T046 [P] Final CI validation: Run full batch (N=20) on simulated GitHub Actions free-tier environment and archive logs to `data/processed/ci_validation_logs/` to satisfy Reproducibility principle

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be completed first to validate feasibility
 - US2 (P2) depends on US1's geometry layer implementation
 - US3 (P3) depends on US1 and US2 for comparative data
- **Stretch Goal & Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core feasibility. Must pass before US2/US3 are meaningful.
- **User Story 2 (P2)**: Requires US1's geometry-only implementation to run the batch.
- **User Story 3 (P3)**: Requires US1 and US2 to generate comparative metrics.

### Within Each User Story

- Implementation MUST be completed before Tests for that story can run (Producer -> Consumer flow)
- Models/Utils before Orchestrators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004-T011) can run in parallel
- Once Foundational phase completes:
 - Developer A can work on US1 (P1) Implementation
 - Developer B can work on US2 (P2) logic (batch orchestration)
 - Developer C can work on US3 (P3) logic (benchmarking)
- All tests for a user story marked [P] can run in parallel (after implementation)

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together (excluding dependent tasks):
Task: "Implement differentiable ray-surface layer in code/models/geometry_only.py"
Task: "Integrate mesh generation from code/utils/mesh_utils.py"
Task: "Implement low-texture detection in code/models/geometry_only.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for a configurable maximum iteration limit in code/models/geometry_only.py"
Task: "Integration test for single scene in tests/integration/test_single_scene.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Geometry-only pipeline on CPU)
4. **STOP and VALIDATE**: Test US1 on a single scene. If it fails to produce a mesh or OOMs, the project is blocked.
5. Deploy/demo if ready (MVP: CPU-feasible geometry-only reconstruction)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Run batch of 20 scenes → Identify threshold → Deploy/Demo
4. Add User Story 3 → Run benchmark comparison → Generate trade-off curve → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Geometry Layer)
 - Developer B: User Story 2 (Batch Orchestrator & Stats)
 - Developer C: User Story 3 (Benchmarking & Latency)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (write tests after implementation skeleton exists)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure `code/data/loader.py` uses `streaming=True` and never falls back to synthetic data (Constitution Principle III & IV).
- **Critical**: Ensure `code/models/geometry_only.py` runs on CPU only for the primary hypothesis (US-1).
- **Critical**: T042 ensures the N=50 spec requirement is met if runtime permits.
- **Critical**: T044 ensures checksums are recorded in the state file as per Constitution Principle III.
- **Critical**: T031 and T031b enforce 2-core CPU affinity for both baseline and geometry-only modules to satisfy SC-001.
- **Critical**: T043 ensures placeholder mesh is generated for general 100-iteration timeouts.
- **Critical**: T041 enforces the 15% tolerance constant.
- **Critical**: T019 explicitly rejects monocular input (1 view) with a hard error exit.
- **Critical**: T027 explicitly implements Shapiro-Wilk test as a distinct unit.
- **Critical**: T046 ensures final CI validation logs are archived.
- **Critical**: Ensure `code/experiments/run_batch.py` explicitly defines the RealEstate10K validation split ID and uses `itertools.islice` for the first N=20 (or N=50) scenes to guarantee a deterministic, reproducible sample as per the "Real data + real results" rule.