# Tasks: llmXive follow-up: extending TriSplat for CPU-only edge robotics

**Input**: Design documents from `/specs/001-llmxive-trisplat-ext/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create project structure per `plan.md` in `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/`. **Deliverables**: Execute `mkdir -p code/{data,models,utils,experiments} tests/{unit,integration} data/{raw,processed} state/projects`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`. **Deliverables**: Create `code/.ruff.toml` (lint rules) and `code/pyproject.toml` (black config).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/cli.py` entry point with arguments: `--views`, `--timeout`, `--seed`, `--update-state`
- [X] T023 [P] Implement dynamic view count configuration in `code/cli.py` (FR-002) to support 2, 3, 4, 5 views as a prerequisite for batch orchestration
- [X] T005 [P] Create `code/data/loader.py` implementing RealEstate10K streaming via `datasets.load_dataset(..., streaming=True)` with explicit 320x240 downscaling logic (FR-003).
- [X] T006 [P] Implement `code/utils/mesh_utils.py` for mesh generation, validation (manifold check), and cleanup
- [X] T007 [P] Implement `code/utils/stats.py` for Shapiro-Wilk, paired t-test, and Wilcoxon signed-rank test logic (FR-005)
- [X] T008 [P] Create `code/models/trisplat_base.py` to load frozen TriSplat backbone weights in CPU-compatible mode
- [X] T009 [P] Create `code/models/geometry_only.py` stub (empty file) for the differentiable ray-surface intersection layer (FR-001)
- [X] T010 [P] Implement `code/data/metrics.py` for Chamfer Distance and PSNR calculation against ground truth
- [X] T011 [P] Setup `code/experiments/run_batch.py` orchestrator skeleton with N=20 scene limit. **Note**: Must define the *need* for a timeout mechanism (orchestration level).

### Timeout Mechanism Block (FR-006, FR-007)
- [X] T011a [P] Implement a configurable batch timeout mechanism in `code/experiments/run_batch.py`: Add a wrapper using `signal.alarm` (or `time.time()` loop) that triggers a graceful exit and logs "BATCH_TIMEOUT_EXCEEDED" if the process runs longer than a predefined duration. **Config**: Must expose a CLI argument `--batch-timeout` with a default value of `6 hours` (360 minutes). (FR-006)
- [X] T011b [P] Implement per-scene timeout mechanism in `code/experiments/run_batch.py`: Define a concrete per-scene timeout to enforce the wall-clock limit. **Config**: Must expose a CLI argument `--scene-timeout` with a default value of `4.5 minutes` (270 seconds). Log "SCENE_TIMEOUT_EXCEEDED" and skip the scene if exceeded. (FR-006)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Geometry-Only Reconstruction (Priority: P1) 🎯 MVP

**Goal**: Run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints, producing a valid mesh within 30 minutes.

**Independent Test**: Execute pipeline on a single RealEstate10K scene (320x240) on CPU-only runner; verify valid `.obj`/`.ply` output within 30 mins.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/models/geometry_only.py` differentiable ray-surface intersection layer using local triangle connectivity and depth gradients (FR-001). **STATUS**: Implemented.
- [X] T016 [US1] Implement convergence detection in `code/models/geometry_only.py` with a configurable hard limit on the maximum number of iterations. **Config**: Must expose a CLI argument `--max-iterations` with a default value set to a reasonable upper bound for typical convergence behavior. The failure condition for convergence is defined as: If p-value < 0.05 AND relative error increase > tolerance.
- [X] T017 [US1] Integrate `code/utils/mesh_utils.py` (from T006) into `code/experiments/run_batch.py` to produce valid `.obj`/`.ply` files (FR-004). **Note**: Consumes T006 logic, does not re-implement.
- [X] T018 [US1] Integrate `code/models/geometry_only.py` into `code/experiments/run_batch.py` to replace the learned refinement head
- [X] T019b [US1] **Handle monocular input gracefully**: In `code/cli.py` and `run_batch.py`, if input views < 2, log a WARNING "Monocular input detected. Skipping scene." and continue to the next scene (do NOT exit with code 1). (FR-002, US1). **Note**: Replaces T019 to satisfy graceful handling requirement.
- [X] T020 [US1] Implement corrupted/missing ground truth handling in `code/data/loader.py`: If ground truth is missing *after* a successful fetch, skip scene, log WARNING, and continue (Edge Case). **Note**: Distinguish from fetch errors (T049); this handles data integrity issues *after* a successful fetch.
- [X] T040 [US1] Implement low-texture/non-convergence detection in `code/models/geometry_only.py`: detect via gradient variance (L2 norm of gradient map), output a placeholder mesh, and log a distinct error flag "LOW_TEXTURE_CONVERGENCE_FAILED", including the `view_count` in the log message. **Threshold**: If variance < `0.01`. **Log Format (Canonical)**: `ERROR: Convergence failed. View Count: {view_count}. Reason: LOW_TEXTURE_CONVERGENCE_FAILED`.
- [X] T043 [US1] Implement general non-convergence handling in `code/models/geometry_only.py`: if the maximum iteration limit (defined by `--max-iterations` in T016) is hit for ANY reason (not just low-texture), generate a placeholder mesh and log an error flag "TIMEOUT_CONVERGENCE_FAILED" to satisfy FR-007. **Trigger**: Only if T040 (low-texture) did not trigger. **Log Format**: `ERROR: Convergence failed. View Count: {view_count}. Reason: TIMEOUT_CONVERGENCE_FAILED`. Must include the current `view_count` in the log entry to attribute failure to sparsity.

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for a bounded iteration limit in `code/models/geometry_only.py` (FR-007) in `tests/unit/test_geometry.py`. **Note**: Test function `test_iteration_limit_enforcement` must assert that the process raises a `TimeoutError` or sets a specific status flag when iterations > limit, and verify the log contains 'TIMEOUT_CONVERGENCE_FAILED'.
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
- [X] T026 [US2] **Implement Statistical Tests**: Explicitly perform ALL three tests (Shapiro-Wilk, paired t-test, Wilcoxon) in `code/utils/stats.py` regardless of normality results. **Logic**: 1. Run Shapiro-Wilk. 2. Run BOTH paired t-test AND Wilcoxon. 3. If Shapiro-Wilk p-value >= 0.05, use the t-test p-value for the final significance decision. 4. If Shapiro-Wilk p-value < 0.05, use the Wilcoxon p-value for the final significance decision. Log all three p-values. (FR-005).
- [X] T027 [US2] **Implement Shapiro-Wilk test**: Explicitly implement and log the Shapiro-Wilk normality test results in `code/utils/stats.py` as a distinct, verifiable unit of work to satisfy FR-005 requirement to perform all three tests.
- [X] T028 [US2] Integrate statistical results (T027, T026) into the final batch report JSON (FR-004)
- [X] T041 [US2] Implement threshold identification logic in `code/utils/stats.py`: Define a CLI argument `--tolerance` (configurable) for the tolerance threshold. **Default**: a predefined relative error increase limit. Calculate relative error increase as `(error_N - error_baseline) / error_baseline` where error_N is Chamfer Distance at view count N. Identify the specific view count where the relative error increase exceeds the `--tolerance` threshold. **Dependency**: Must consume the final significance results from T026/T027. Output result to `data/processed/threshold_result.json` (FR-005).
- [X] T055 [US2] Implement bootstrapping logic in `code/utils/stats.py` to calculate confidence intervals for the identified threshold, integrating it with the threshold determination logic in T041.

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for statistical significance logic (Shapiro-Wilk -> t-test/Wilcoxon) in `tests/unit/test_stats.py`. **Note**: Must include test functions `test_shapiro_wilk_normality`, `test_conditional_ttest_wilcoxon`, and `test_threshold_calculation`.
- [X] T022 [P] [US2] Integration test for batch processing with varying view counts in `tests/integration/test_sparsity_batch.py`

**Checkpoint**: User Story 2 is complete; sparsity threshold is identified and logged

---

## Phase 5: User Story 3 - Quantitative Fidelity and Latency Benchmarking (Priority: P3)

**Goal**: Compare inference latency and geometric fidelity of the geometry-only module against the baseline.

**Independent Test**: Run both methods on same hardware; compare latency and fidelity metrics.

### Implementation for User Story 3

- [X] T031 [US3] Implement baseline TriSplat execution logic in `code/experiments/run_batch.py`. **Enforce 2-core CPU affinity** using `os.sched_setaffinity` for both the baseline and the geometry-only module (T015/T018) to satisfy SC-001.
- [X] T030 [US3] Implement latency measurement wrapper in `code/experiments/run_batch.py` to record inference time per scene-config
- [X] T032 [US3] Implement comparative metric aggregation in `code/utils/stats.py` to calculate speedup ratio and PSNR delta (FR-004)
- [X] T033 [US3] Generate benchmark report CSV at `data/processed/benchmark_tradeoff.csv` with columns: `view_count,latency,chamfer_distance,psnr,baseline_latency,speedup_ratio,psnr_delta` (US-3 Acceptance 1). **Note**: Explicitly list these headers in the code.
- [X] T039 [US3] Generate visualization of trade-off curve: Create a plot (PNG/SVG) showing latency vs. Chamfer Distance for different view counts, saved to `data/processed/benchmark_tradeoff_plot.png` (US-3 Acceptance 3)

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for latency measurement wrapper in `tests/unit/test_latency.py`. **Note**: Test function `test_latency_measurement_wrapper` must assert that the wrapper uses `time.perf_counter()`, returns a float > 0, and correctly logs exceptions during the timed block.
- [X] T029 [P] [US3] Integration test for comparative benchmarking in `tests/integration/test_benchmark.py`

**Checkpoint**: User Story 3 is complete; benchmark results are generated

---

## Phase 6: Stretch Goal & Polish

**Purpose**: Handling N=50 scenes and final validation

- [X] T042 [P] Implement N=50 stretch goal logic in `code/experiments/run_batch.py`: If N=20 scenes complete within 70% of the batch timeout value defined in T011a, dynamically expand the scene list to 50 random scenes and continue processing (Plan: Stretch Goal). **Note**: Implement timeout using `signal.alarm` or `threading.Timer` to enforce the predefined wall-clock limit.
- [X] T035 [P] Add checksumming logic for downloaded dataset shards in `code/data/loader.py` (Plan: Data Hygiene)
- [X] T044 [P] Implement data flow for checksums: Ensure `code/data/loader.py` writes computed checksums to a temporary JSON file (`data/processed/checksums_temp.json`) that `code/cli.py --update-state` ingests to satisfy Constitution Principle III (Data Hygiene). **Note**: Explicitly defines the producer-consumer chain for checksums to state file.
- [X] T034 [P] Implement `code/cli.py --update-state` command to compute SHA-256 hashes and update `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` (Plan: Post-Execution State Update). **Note**: Read `checksums_temp.json` if present (from T044) instead of recomputing hashes. **DEPENDS ON: T044**.
- [X] T050 [P] **Artifact Hashing Logic**: In `code/cli.py --update-state`, implement the logic to recursively hash all files in `data/processed/` (including the `threshold_result.json` and `benchmark_tradeoff_plot.png`) and write the resulting map to `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` under key `artifact_hashes` to ensure the "Single Source of Truth" is updated. **Note**: Filter files by size < 100MB using `os.path.getsize` BEFORE hashing to avoid long runtimes on large mesh files.
- [X] T036 [P] Write comprehensive `README.md` and `quickstart.md` in `specs/001-llmxive-trisplat-ext/`. **Deliverables**: `specs/001-llmxive-trisplat-ext/README.md` (Installation, Usage, Data Source, Architecture) and `specs/001-llmxive-trisplat-ext/quickstart.md` (Quick start guide). **Mandatory Sections**: 'Installation', 'Usage', 'Data Source', 'Architecture'.
- [X] T037 [P] Validate all contracts (`contracts/*.schema.yaml`) against generated JSON outputs
- [X] T046 [P] Final CI validation: Run full batch (N=20) on simulated GitHub Actions free-tier environment and archive logs to `data/processed/ci_validation_logs/` to satisfy Reproducibility principle

---

## Phase 7: Data Integrity & Reproducibility Hardening (Revision)

**Purpose**: Addressing specific reviewer concerns regarding data source verification, deterministic sampling, and stream handling to prevent fabrication.

### Implementation for Data Integrity

- [X] T047 [US1] **Explicit Dataset Sampling Rule**: In `code/experiments/run_batch.py`, explicitly define the RealEstate10K validation split ID ('validation') and implement a deterministic sampling strategy using `itertools.islice` to select the *first* N=20 (or N=50) scenes from the streamed dataset using seed 42. Document the exact seed and slice logic in the code comments to satisfy the "Real data + real results" rule. **Note**: This task implements the sampling logic within T024.
- [X] T048 [US1] **Stream Verification**: In `code/data/loader.py`, add a pre-flight check that attempts to stream a small sample of frames from the dataset to verify connectivity and schema validity before starting the main batch. If this fails, raise a loud error (no fallback) to satisfy Constitution Principle III. **Note**: This task implements the verification logic within T005.
- [X] T049 [US1] **Real Data Source Lock-in**: Ensure `code/data/loader.py` uses `streaming=True` and never falls back to synthetic data (Constitution Principle III & IV).

---

## Phase 8: Analysis-Driven Revisions (Pending Review)

**Purpose**: Tasks to be added after `/speckit.analyze` identifies specific gaps or failures in the current plan.

- [ ] T051 [US1] **Pending Analysis**: Implement missing convergence metric calculation if `/speckit.analyze` reports that the current iteration limit logic does not capture the "rate of convergence" required by the research question. **Trigger**: If `analyze_report` flags "insufficient convergence diagnostics".
- [ ] T052 [US2] **Pending Analysis**: Add a bootstrapping confidence interval calculation to `data/processed/threshold_result.json` if `/speckit.analyze` indicates that the single-point threshold estimate lacks statistical robustness for N=20. **Trigger**: If `analyze_report` flags "low statistical power for threshold identification".
- [ ] T053 [US3] **Pending Analysis**: Implement a variance-stabilizing transformation for latency measurements if `/speckit.analyze` detects non-normal distribution in the latency logs that invalidates the t-test assumptions. **Trigger**: If `analyze_report` flags "violation of normality assumption in latency data".
- [ ] T054 [General] **Pending Analysis**: Add a dedicated "Data Source Validation" task if `/speckit.analyze` finds that the streaming verification (T048) does not cover all edge cases (e.g., corrupted shards, partial downloads). **Trigger**: If `analyze_report` flags "incomplete data integrity checks".

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
- **Data Integrity (Phase 7)**: Can be implemented in parallel with Phase 6, but MUST be completed before final CI validation (T046).
- **Analysis-Driven Revisions (Phase 8)**: Can ONLY be executed after `/speckit.analyze` is run and specific triggers are identified.

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

- All Setup tasks marked [P] can run in parallel (once T001/T003 are fixed)
- All Foundational tasks marked [P] (T004-T011) can run in parallel
- Once Foundational phase completes:
 - Developer A can work on US1 (P1) Implementation
 - Developer B can work on US2 (P2) logic (batch orchestration)
 - Developer C can work on US3 (P3) logic (benchmarking)
- All tests for a user story marked [P] can run in parallel (after implementation)
- Phase 6 tasks (T047-T050) can run in parallel with Phase 6 tasks.
- Phase 8 tasks (T051-T054) are blocked until analysis results are available.

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together (excluding dependent tasks):
Task: "Implement differentiable ray-surface layer in code/models/geometry_only.py"
Task: "Integrate mesh generation from code/utils/mesh_utils.py"
Task: "Implement low-texture detection in code/models/geometry_only.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for a bounded iteration limit in code/models/geometry_only.py"
Task: "Integration test for single scene in tests/integration/test_single_scene.py"
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (write tests after implementation skeleton exists)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure `code/data/loader.py` uses `streaming=True` and never falls back to synthetic data (Constitution Principle III).
- **Critical**: Ensure `code/models/geometry_only.py` runs on CPU only for the primary hypothesis (US-1).
- **Critical**: T042 ensures the N=50 spec requirement is met if runtime permits.
- **Critical**: T035 ensures checksums are recorded in the state file as per Constitution Principle III.
- **Critical**: Ensure `code/experiments/run_batch.py` explicitly defines the RealEstate10K validation split ID and uses `itertools.islice` for the first N=20 (or N=50) scenes to guarantee a deterministic, reproducible sample as per the "Real data + real results" rule (T047).
- **Critical**: Ensure `code/data/loader.py` raises a loud error on fetch failure and contains NO synthetic fallback logic (T049).
- **Critical**: Ensure `code/cli.py --update-state` correctly hashes all processed artifacts (excluding large files >100MB) to update the state file (T050).
- **Critical**: T011a and T011b implement the timeout mechanisms according to the plan and spec.
- **Critical**: T043 ensures placeholder mesh is generated for general 100-iteration timeouts.
- **Critical**: Ensure T019b explicitly handles monocular input with a warning and skip.
- **Critical**: Ensure T027 explicitly implements Shapiro-Wilk test as a distinct unit.
- **Critical**: Ensure T046 runs final CI validation.
- **Critical**: Ensure T044 is executed before T034.
- **Critical**: Phase 7 tasks (T047-T049) can run in parallel with Phase 6 tasks.
- **Critical**: Phase 8 tasks (T051-T054) are placeholders and must be activated only after `/speckit.analyze` returns specific findings.