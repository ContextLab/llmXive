# Tasks: llmXive follow-up: extending "Latent Spatial Memory for Video World Models"

**Input**: Design documents from `/specs/001-gene-regulation/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure (`projects/PROJ-843-llmxive-follow-up-extending-latent-spati/`, `code/`, `data/`, `tests/`)
- [X] T001b [P] Initialize Python 3.11 project with `requirements.txt` (opencv-python, scikit-learn, scipy, pandas, numpy, torch-cpu, datasets, imageio, pytest, memory_profiler, scikit-image for FID)
- [X] T002 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement `code/utils/seeds.py` to pin all random seeds for reproducibility
- [X] T004 [P] Create `code/config.py` defining paths (`data/raw`, `data/stratified`, `data/results`), thresholds, and memory limits
- [ ] T005 [P] Implement `code/utils/memory_monitor.py` to log peak RAM and wall-clock time via `memory_profiler`
- [ ] T006 Create base data schemas and directory structure (`data/raw`, `data/processed`, `data/stratified`, `data/features`, `data/results`) <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stratified Dataset Preparation and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest RealEstate10K, stratify into 4 subsets (Static/Slow/Fast x High/Low texture), and extract sparse SIFT/ORB descriptors without dense depth.

**Independent Test**: Run `code/data/stratify.py` and `code/data/extract_features.py` on a small subset; verify 4 folders exist with N=50 sequences each, and `.npy` files contain valid coordinate/descriptor pairs.

### Implementation for User Story 1

- [X] T007 [P] [US1] Implement `code/data/download.py` to fetch RealEstate10K using `datasets.load_dataset` with specific revision and validate URL accessibility
- [X] T008 [US1] Implement `code/data/stratify.py` to:
 - Calculate motion magnitude (optical flow) and texture entropy for sequences
 - **ABORT execution** with error code 1 if any stratum has fewer than 50 sequences in the source pool (strict n≥50 enforcement)
 - Select a fixed number of sequences per stratum if >50 available (random selection with seed)
 - Stratify into 4 subsets (Static-High, Static-Low, Fast-High, Fast-Low)
 - Save metadata and move sequences to `data/stratified/`
- [X] T009 [US1] Implement `code/data/extract_features.py` to:
 - Iterate over `data/stratified/` keyframes
 - Extract sparse SIFT/ORB descriptors and 2D coordinates
 - **Explicitly skip** dense depth map generation
 - **Implement batch processing mode**: trigger sequential frame processing if RAM usage > 6GB to prevent OOM
 - **Detect low feature density** in "Fast" sequences and mark frames invalid per spec edge cases
 - Save results as `.npy` in `data/features/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sparse Epipolar Solver and Latent Warping Execution (Priority: P2)

**Goal**: Implement RANSAC-optimized sparse fundamental matrix solver and CPU-based RBF latent warping for occlusion filling.

**Independent Test**: Run solver on a "Static-High" sequence; verify valid fundamental matrix, 3D points (up to scale), and smooth RBF interpolation without NaNs or GPU usage.

### Implementation for User Story 2

- [X] T010 [P] [US2] Implement `code/geometry/solver.py` to:
 - Load sparse correspondences from `data/features/`
 - Compute Fundamental Matrix using RANSAC
 - Project to 3D (up to scale)
 - **Flag sequences as "Unsolvable"** if RANSAC fails to find sufficient inliers (low texture)
 - **Log "Unsolvable" sequences** to `data/results/unsolvable_sequences.json` and **exclude** them from statistical analysis
 - **Implement batch processing mode**: trigger sequential processing if RAM usage > 6GB to prevent OOM
 - Validate via re-projection error and enforce CPU-only execution
- [X] T011 [US2] Implement `code/geometry/warp.py` to:
 - Perform latent-space warping using sparse 3D points
 - Implement CPU-based Radial Basis Function (RBF) interpolation for occluded regions
 - Ensure geometric smoothness and no NaN artifacts
 - Implement batch processing mode to trigger sequential processing if CPU memory approaches limits (preventing OOM)
- [X] T012 [US2] Aggregate warped frames:
 - Consume outputs from T011
 - Compile all warped frames into a single artifact `data/results/sparse_warped_frames.npy`
 - Validate shape and data types

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Metrics and Statistical Validation (Priority: P3)

**Goal**: Compute WorldScore (dense) and Sparse-Consistency Score (sparse), run Two-Way ANOVA, and generate sensitivity reports.

**Independent Test**: Run evaluation script on pre-computed results; verify ANOVA table (p-value for interaction), sensitivity sweep table, and metrics JSON.

### Implementation for User Story 3

- [X] T016b [US3] Download dense baseline results: <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Strictly download** the pre-computed dense baseline from external source (e.g., HuggingFace `realestate10k/dense_baseline_v1` or official URL)
 - **DO NOT generate** or infer the baseline; if unavailable, **ABORT** with error
 - Validate checksum and save to `data/raw/dense_baseline_frames.npy`
- [ ] T017 [US3] Implement `code/eval/metrics.py` to:
 - **Compute WorldScore** for the dense baseline by reading `data/raw/dense_baseline_frames.npy` and applying the topological fidelity metric defined in spec.md
 - **Compute Sparse-Consistency Score** for the sparse method using the re-projection error defined in spec.md, reading `data/results/sparse_warped_frames.npy`
 - **Calculate Fréchet Inception Distance (FID)** by comparing the **distribution** of sparse warped frames against the **distribution** of dense baseline frames (using Inception-v3) to quantify the relative pixel-level reconstruction quality trade-off (SC-002)
 - Calculate Unified Geometric Error (Photometric Consistency) on held-out frames for internal validation
 - Output results in a structured format for ANOVA
- [X] T018 [US3] Implement `code/eval/anova.py` to:
 - Perform Two-Way ANOVA on metrics vs. (Scene Dynamics, Texture Level)
 - Output p-value for interaction effects (significance threshold p < 0.05)
- [X] T019 [US3] Implement `code/eval/sensitivity.py` to sweep RANSAC thresholds across a range of values and report variation specifically in **WorldScore and Sparse-Consistency Score**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Integration & Aggregation (Priority: P3)

**Purpose**: Chain the pipeline and synthesize final reports

- [ ] T020 [US3] Implement `code/main.py` orchestrator to:
 - **Consume completed artifacts** from phases T007-T019 (do not re-execute logic)
 - **Parse raw `memory_profiler` logs** from T005 and **aggregate them** into the final `data/results/metrics.json` following the `MetricReport` schema (FR-007)
 - Aggregate results from both sparse and dense paths
 - Record wall-clock time and peak RAM for both sparse and dense approaches
 - Write final results to `data/results/metrics.json`
- [X] T021 [US3] Implement `code/eval/report.py` to:
 - Read `data/results/metrics.json`
 - Calculate the percentage reduction in inference time (Sparse vs Dense)
 - **Compare against the 40% threshold** to produce a `pass` or `fail` boolean for SC-003
 - Write the final verification report to `data/results/hypothesis_verification.md` including:
 - WorldScore vs. Sparse-Consistency comparison
 - ANOVA interaction effects
 - Sensitivity analysis stability
 - Inference time reduction status (Pass/Fail)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T022 [P] Documentation updates in `README.md` and `quickstart.md`
- [X] T023 Code cleanup and refactoring for CPU efficiency <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T024 Run quickstart.md validation to ensure end-to-end reproducibility on CPU-only environment <!-- ATOMIZE: requested -->
- [X] T025 [P] Additional unit tests in `tests/unit/` for feature extraction, solver, and ANOVA logic <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Integration (Phase 6)**: Depends on US1, US2, and US3 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 results (and T016b for dense baseline)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tasks T007, T010, T018, T019 are marked [P] and can run in parallel once their specific prerequisites are met
- Different user stories can be worked on in parallel by different team members

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
- **Constraint**: All tasks must run on CPU-only CI (a minimal core count, sufficient RAM, no GPU). No 8-bit/4-bit quantization or large model training.
