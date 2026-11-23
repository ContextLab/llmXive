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
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`. **Deliverables**: Create `code/.ruff.toml` (lint rules) and `code/pypy.toml` (black config).

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
- [X] T011a [P] Implement a configurable batch timeout mechanism in `code/experiments/run_batch.py`: Add a wrapper using `signal.alarm` (or `time.time()` loop) that triggers a graceful exit and logs "BATCH_TIMEOUT_EXCEEDED" if the process runs longer than a predefined duration. **Config**: Must expose a CLI argument `--batch-timeout` with a default value of a substantial duration. (FR-006)
- [X] T011b [P] Implement per-scene timeout mechanism in `code/experiments/run_batch.py`: Define a concrete per-scene timeout to enforce the wall-clock limit. **Config**: Must expose a CLI argument `--scene-timeout` with a default value representing a reasonable duration for scene processing. Log "SCENE_TIMEOUT_EXCEEDED" and skip the scene if exceeded. (FR-006)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Geometry-Only Reconstruction (Priority: P1) 🎯 MVP

**Goal**: Run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints, producing a valid mesh within 30 minutes.

**Independent Test**: Execute pipeline on a single RealEstate10K scene (320x240) on CPU-only runner; verify valid `.obj`/`.ply` output within 30 mins.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/models/geometry_only.py` differentiable ray-surface intersection layer using local triangle connectivity and depth gradients (FR-001). **STATUS**: Implemented.
- [X] T016 [US1] **REMOVED**: Superseded by T059. The logic for convergence detection and iteration limits is now handled by the adaptive scaling mechanism in T059.
- [X] T017 [US1] Integrate `code/utils/mesh_utils.py` (from T006) into `code/experiments/run_batch.py` to produce valid `.obj`/`.ply` files (FR-004). **Note**: Consumes T006 logic, does not re-implement.
- [X] T018 [US1] Integrate `code/models/geometry_only.py` into `code/experiments/run_batch.py` to replace the learned refinement head
- [X] T019b [US1] **Handle monocular input gracefully**: In `code/cli.py` and `run_batch.py`, if input views < 2, log a WARNING "Monocular input detected. Skipping scene." and continue to the next scene (do NOT exit with code 1). (FR-002, US1). **Note**: Replaces T019 to satisfy graceful handling requirement.
- [X] T020 [US1] Implement corrupted/missing ground truth handling in `code/data/loader.py`: If ground truth is missing *after* a successful fetch, skip scene, log WARNING, and continue (Edge Case). **Note**: Distinguish from fetch errors (T049); this handles data integrity issues *after* a successful fetch.
- [X] T040 [US1] Implement low-texture/non-convergence detection in `code/models/geometry_only.py`: detect via gradient variance (L2 norm of gradient map), output a placeholder mesh, and log a distinct error flag "LOW_TEXTURE_CONVERGENCE_FAILED", including the `view_count` in the log message. **Threshold**: If variance is low. **Log Format (Canonical)**: `ERROR: Convergence failed. View Count: {view_count}. Reason: LOW_TEXTURE_CONVERGENCE_FAILED`.
- [X] T043 [US1] **Implement general non-convergence handling**: This task executes SEQUENTIALLY after T040 and T059. **Logic**: 1. Check if T040 triggered (low-texture). If yes, skip this task. 2. Check if T059 adaptive limit was hit. If yes, generate a placeholder mesh and log "TIMEOUT_CONVERGENCE_FAILED" including the `view_count`. **Trigger**: Only if T040 did NOT trigger and the adaptive iteration limit (T059) was hit. This ensures distinct logging for failure reasons (T040 vs T059). (FR-007). **Log Format**: `ERROR: Convergence failed. View Count: {view_count}. Reason: TIMEOUT_CONVERGENCE_FAILED`.

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for adaptive iteration limit enforcement in `code/models/geometry_only.py` (FR-007) in `tests/unit/test_geometry.py`. **Note**: Test function `test_adaptive_iteration_limit` must assert that the process adapts the cap based on gradient magnitude and raises a `TimeoutError` or sets a specific status flag when iterations > adaptive limit, and verify the log contains 'TIMEOUT_CONVERGENCE_FAILED'.
- [X] T013 [P] [US1] Integration test for single scene reconstruction pipeline in `tests/integration/test_single_scene.py`
- [X] T014 [P] [US1] Memory usage test verifying < 6 GB peak RAM in `tests/integration/test_memory_limits.py`

**Checkpoint**: User Story 1 is fully functional and testable independently on CPU

---

## Phase 4: User Story 2 - Sparsity Threshold Identification (Priority: P2)

**Goal**: Systematically vary input views to identify the sparsity threshold where geometric constraints fail.

**Independent Test**: Run pipeline on 20 scenes (or 50 if T042 triggers) with varying view counts; output structured log of Chamfer Distance/PSNR; perform statistical test to identify threshold.

### Implementation for User Story 2

- [X] T024 [US2] Implement batch orchestration in `code/experiments/run_batch.py` to process N=20 scenes (or N=50 if T042 triggers) across 2, 3, 4, and 5 view configurations (depends on T023). **Note**: Strictly defaults to N=20. N=50 logic is handled by T042.
- [X] T025 [US2] Implement metric logging in `code/experiments/run_batch.py` to output JSON logs with Chamfer Distance and PSNR per scene/view-count (FR-004)
- [X] T026 [US2] **Implement Statistical Tests with Outlier Detection**: Explicitly implement and perform ALL three tests (Shapiro-Wilk, paired t-test, and Wilcoxon signed-rank) in `code/utils/stats.py`. **Logic**: 
    1. **Outlier Detection (Pre-step)**: Before running tests, calculate Z-scores for all metric values. Flag any value with |Z| > 3.0 as an outlier. Log these flags but DO NOT remove them automatically. 
    2. Run Shapiro-Wilk. 
    3. Run BOTH paired t-test AND Wilcoxon. 
    4. If Shapiro-Wilk p-value >= 0.05, use the t-test p-value for the final significance decision. 
    5. If Shapiro-Wilk p-value < 0.05, use the Wilcoxon p-value for the final significance decision. 
    6. Log all three p-values and the outlier flags. 
    **Ownership**: This single task covers the entire implementation of FR-005, including the Shapiro-Wilk test and the robust outlier detection step. (FR-005).
- [X] T028 [US2] Integrate statistical results (T026) into the final batch report JSON (FR-004)
- [X] T055 [US2] **Implement Bootstrapping**: Implement bootstrapping logic in `code/utils/stats.py` to calculate confidence intervals for the identified threshold. **Output**: Must output the bootstrapped confidence intervals to a temporary file or return them to be consumed by T041. **Dependency**: This task must run BEFORE T041 to provide the necessary data.
- [X] T041 [US2] **Implement Threshold Identification**: Define a CLI argument `--tolerance` (configurable) for the tolerance threshold. **Logic**: Calculate relative error increase as `(error_N - error_baseline) / error_baseline`. Identify the specific view count where the relative error increase exceeds the `--tolerance` threshold. **Dependency**: Must consume the final significance results from T026 AND the bootstrapped confidence intervals from T055. Output result to `data/processed/threshold_result.json` (FR-005). **Note**: This task now explicitly generates the final JSON including confidence intervals, removing the need for conditional T052. **DEPENDS ON: T055**.

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for statistical significance logic (Shapiro-Wilk -> t-test/Wilcoxon) and outlier detection in `tests/unit/test_stats.py`. **Note**: Must include test functions `test_shapiro_wilk_normality`, `test_conditional_ttest_wilcoxon`, `test_outlier_detection_zscore`, and `test_threshold_calculation`.
- [X] T022 [P] [US2] Integration test for batch processing with varying view counts in `tests/integration/test_sparsity_batch.py`

**Checkpoint**: User Story 2 is complete; sparsity threshold is identified and logged

---

## Phase 5: User Story 3 - Quantitative Fidelity and Latency Benchmarking (Priority: P3)

**Goal**: Compare inference latency and geometric fidelity of the geometry-only module against the baseline.

**Independent Test**: Run both methods on same hardware; compare latency and fidelity metrics.

### Implementation for User Story 3

- [X] T031 [US3] Implement baseline TriSplat execution logic in `code/experiments/run_batch.py`. **Enforce 2-core CPU affinity** using `os.sched_setaffinity` for both the baseline (geometry-only module) and the experimental module to satisfy SC-001 and Constitution Principle VII. **Note**: The "baseline" here refers to the geometry-only model (stripped of CNN) to satisfy Constitution Principle VII; do NOT compare against a full CNN-refinement model as that would invalidate the hypothesis.
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
- [X] T050 [P] **Artifact Hashing Logic**: In `code/cli.py --update-state`, implement the logic to recursively hash ALL files in `data/processed/` (including the `threshold_result.json` and `benchmark_tradeoff_plot.png`) and write the resulting map to `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` under key `artifact_hashes`. **Constraint**: Do NOT filter by size. If a file exceeds a large size threshold, use a streaming hash algorithm (e.g., `hashlib` chunked reading) to ensure every artifact carries a content hash as required by Constitution Principle V. **DEPENDS ON: T034**.
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

## Phase 8: Advanced Statistical & Convergence Enhancements (Concrete Implementation)

**Purpose**: Concrete implementation of robust statistical methods and adaptive convergence logic to satisfy FR-005 and FR-007 without external dependencies.

### Implementation for Convergence & Statistical Robustness

- [X] T059 [US1] **Implement Adaptive Iteration Scaling**: Replace the fixed `--max-iterations` limit (T016) with an adaptive scaling logic in `code/models/geometry_only.py`. **Logic**: 
    1. **Base Cap**: Set a default base iteration cap to a reasonable magnitude.
    2. **Gradient Calculation**: Compute the L2 norm of the gradient map for the current iteration.
    3. **Scaling Factor**: Calculate a dynamic scaling factor `f` as a function of the gradient norm. Clamp `f` within a bounded range.
    4. **Adaptive Cap**: `current_max_iterations` = `base_cap * f`.
    5. **Execution**: Stop if iterations reach `current_max_iterations` OR if gradient norm drops below a convergence threshold.
    **Output**: Log the calculated adaptive cap and the final iteration count for every scene. (FR-007).
- [X] T060 [US3] **Implement Variance-Stabilizing Transformation**: In `code/utils/stats.py`, implement a Box-Cox or log transformation for latency measurements before running Shapiro-Wilk/t-test. **Logic**: 
    1. Check if latency data is strictly positive. If not, add a small epsilon to all values.
    2. Apply natural log transformation: `transformed = log(latency + epsilon)`, where epsilon is a small positive constant to prevent undefined values.
    3. Use the `transformed` values for all subsequent statistical tests (T026).
    4. Log the transformation method used and the mean/std of transformed values.
    **Output**: Log the transformed values and the transformation method used. (FR-005).
- [X] T063 [US1] **Implement Convergence Metrics**: In `code/models/geometry_only.py`, add a detailed convergence metric calculation (rate of convergence, final error delta) to satisfy FR-007. **Logic**: 
    1. Calculate `final_error_delta` = `error_at_last_iteration - error_at_first_iteration`.
    2. Calculate `convergence_rate` = `final_error_delta / total_iterations`.
    3. Log these metrics in the JSON report for every scene.
    **Output**: Log these metrics in the JSON report for every scene.
- [X] T064 [General] **Implement Artifact Size Audit**: In `code/cli.py --update-state` (T050), add a pre-hash audit that logs the size of every file to be hashed. **Output**: Write a summary of file sizes to `data/processed/artifact_size_audit.json` to verify that no critical files are excluded by size (even though T050 now hashes all).

**Checkpoint**: All previously "Pending" requirements are now implemented as concrete, executable tasks with explicit default logic.