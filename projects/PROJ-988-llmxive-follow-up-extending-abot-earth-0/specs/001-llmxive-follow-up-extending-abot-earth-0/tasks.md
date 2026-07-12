# Tasks: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

**Input**: Design documents from `/specs/001-generative-3d-earth-fidelity/`
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

- [ ] T001a [P] Create project directory structure (`code/`, `data/`, `tests/`, `docs/`) per `projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/`
- [ ] T001b [P] Create `.gitignore` for large files and Python artifacts
- [ ] T002a [P] Create `code/requirements.txt` with pinned versions (torch-cpu, onnxruntime, scikit-learn, opencv-python, pandas, numpy, pyyaml, tqdm, matplotlib, seaborn, bayesian_changepoint_detection)
- [ ] T002b [P] Initialize Python 3.11 virtualenv and install dependencies
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `results/`, `interim/`)
- [ ] T005 [P] Implement `code/lib/alignment.py` for coordinate transform logic (UTM/Geographic)
- [ ] T006 [P] Implement `code/lib/degradation.py` for synthetic mask generation and downscaling logic
- [ ] T007a [P] Create `code/lib/models.py` class `DegradedScene`
- [ ] T007b [P] Create `code/lib/models.py` class `ReconstructedScene`
- [ ] T007c [P] Create `code/lib/models.py` class `GroundTruthLiDAR`
- [ ] T007d [P] Create `code/lib/models.py` class `FidelityMetrics`
- [ ] T008 [P] Configure logging infrastructure to `data/results/execution.log` with structured JSON output
- [ ] T009 [P] Setup environment configuration management (loaders for `city_list.txt`, random seeds)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Degradation & Ground Truth Alignment (Priority: P1) 🎯 MVP

**Goal**: Download a representative set of urban Sentinel-2 tiles, align with OpenTopography LiDAR, and apply reproducible synthetic degradation (low-res, clouds, temporal shifts) with NNF variance.

**Independent Test**: A script generates 500 paired samples where alignment error is < 2 meters, and degradation parameters (resolution, cloud coverage, NNF) are verified against the ground truth.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for alignment error calculation in `tests/unit/test_alignment.py` (verify < 2m residual)
- [ ] T011 [P] [US1] Unit test for degradation parameters in `tests/unit/test_degradation.py` (verify moderate spatial resolution and partial cloud coverage)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_data_curation.py` to download Sentinel-2 (Microsoft Planetary Computer) and LiDAR (USGS 3DEP/NYC) for 500 urban regions; save raw assets to `data/raw/` and generate `data/processed/raw_manifest.csv` listing all downloaded IDs
- [ ] T013 [US1] Implement `code/01_data_curation.py` to register LiDAR to image coordinates using `code/lib/alignment.py`, calculate spatial alignment error for each pair, and **automatically exclude** samples with > 2m error; output the final filtered dataset to `data/processed/aligned_pairs.csv` and `data/processed/alignment_report.csv` (pass/fail flags)
- [ ] T013b [US1] Verify and log that the final filtered dataset in `data/processed/aligned_pairs.csv` contains a sufficient number of valid samples (or fail if count < 500)
- [ ] T011b [US1] Acquire reference real cloud masks for the selected regions from Sentinel-2 Cloud Probability dataset and save to `data/raw/real_cloud_masks_subset/`; **IF** synthetic mask similarity check (to be run in T016) fails (< 0.8), configure the degradation pipeline (T014) to use these real masks instead of procedural generation
- [ ] T016 [US1] Implement `code/02b_validate_masks.py` to compare synthetic mask stats against `data/raw/real_cloud_masks_subset/` and output `data/results/mask_similarity_score.json`; if similarity < 0.8, **explicitly configure** the degradation pipeline to switch to real masks and log the fallback decision
- [ ] T014a [US1] Implement `code/02_degradation_pipeline.py` to apply **downscale** (to 30m/pixel) and **procedural/real cloud masks** (based on T016) to the aligned pairs; output intermediate degraded scenes to `data/processed/degraded_base/`
- [ ] T014b [US1] Implement `code/02_degradation_pipeline.py` to apply **temporal shifts** (simulating stale imagery via temporal interpolation or selection from adjacent dates) and **systematically vary NNF** (Normalized Noise Fraction) by sweeping degradation intensity across the sample set; output the final NNF-varied dataset to `data/processed/nnf_varied_scenes/` and `data/processed/degraded_manifest.json`
- [ ] T017 [US1] Save aligned pairs and degraded scenes to `data/processed/` with checksums in `data/manifest.json` (Note: T017 now depends on T014 completing the NNF-varied generation)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized Generative Restoration (Priority: P2)

**Goal**: Run 3D Gaussian Splatting (3DGS) and CPU-optimized inpainting (ONNX Runtime) on degraded scenes within 45 mins/scene and < 6.5 GB RAM, measuring performance metrics.

**Independent Test**: A single degraded patch is processed end-to-end on a multi-core CPU, producing a valid `.ply` file without CUDA errors, with logged RAM/time metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for ONNX Runtime initialization in `tests/unit/test_cpu_3dgs.py` (verify no GPU device calls)
- [ ] T019 [P] [US2] Integration test for memory usage in `tests/integration/test_memory_limits.py` (verify < 6.5 GB peak RAM)

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/lib/cpu_3dgs_wrapper.py` to load CPU-quantized diffusion prior (low-bit/LCM) via ONNX Runtime; explicitly assert `torch.cuda.is_available()` is False and force `execution_provider=['CPUExecutionProvider']`
- [ ] T021 [US2] Implement `code/03_3dgs_cpu_inference.py` to **orchestrate the full end-to-end pipeline**: load degraded input from T014 -> generate baseline 3DGS scene -> apply inpainting module for recovery -> save paired baseline/inpainted `.ply` files to `data/processed/reconstructed/`; **explicitly instrument and log peak RAM usage and wall-clock time per scene to `data/results/performance_log.csv`**; ensure completion < 45 mins per scene; implement graceful OOM handling (`ERR_OOM_CPU`)
- [ ] T024 [US2] Validate output `.ply` files for format compatibility and size < 500 MB in `code/03_3dgs_cpu_inference.py`
- [ ] T025 [US2] Save reconstructed scenes to `data/processed/reconstructed/` with metadata

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity Quantification & Threshold Analysis (Priority: P3)

**Goal**: Compute P-PSNR, P-SSIM, and Chamfer Distance against LiDAR, perform statistical significance testing, and identify the critical NNF threshold using the NNF-varied dataset from T014.

**Independent Test**: A script processes the NNF-varied dataset, outputs a metrics CSV, and generates a plot showing the performance drop-off curve with a identified NNF threshold (p > 0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Chamfer Distance calculation in `tests/unit/test_metrics.py` (verify normalized scale)
- [ ] T027 [P] [US3] Unit test for statistical significance (t-test) in `tests/unit/test_analysis.py` (verify p-value logic)

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/lib/metrics.py` to compute P-PSNR and P-SSIM between reconstructed and LiDAR scenes
- [ ] T029 [US3] Implement `code/lib/metrics.py` to compute Chamfer Distance on a normalized scale (meters)
- [ ] T030 [US3] Implement `code/04_metrics_evaluation.py` to run metrics on all samples from `data/processed/nnf_varied_scenes/` and save `data/results/metrics.csv`
- [ ] T031 [US3] Implement `code/05_threshold_analysis.py` to perform paired t-test (baseline vs. inpainted) and log significance
- [ ] T032 [US3] Implement `code/05_threshold_analysis.py` to sweep NNF thresholds using the dataset from T014, identify the critical failure point (p > 0.05), and extract the scalar value
- [ ] T033 [US3] Generate plots (performance drop-off curve) in `data/results/` and save the critical NNF threshold scalar to `data/results/critical_threshold.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` and `README.md`
- [ ] T035 Code cleanup and refactoring of `code/lib/` modules
- [ ] T036 Performance optimization for batch processing (if applicable)
- [ ] T037 [P] Additional unit tests in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Explicitly depends on T017 (US1 data completion)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Explicitly depends on T025 (US2 output)**

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
Task: "Unit test for alignment error calculation in tests/unit/test_alignment.py"
Task: "Unit test for degradation parameters in tests/unit/test_degradation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/lib/alignment.py"
Task: "Implement code/lib/degradation.py"
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