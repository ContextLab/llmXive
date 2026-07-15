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

- [X] T001a [P] Create project directory structure (`code/`, `data/`, `tests/`, `docs/`) per `projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/`
- [X] T001b [P] Create `.gitignore` for large files and Python artifacts
- [X] T002a [P] Create `code/requirements.txt` with pinned versions (torch-cpu, onnxruntime, scikit-learn, opencv-python, pandas, numpy, pyyaml, tqdm, matplotlib, seaborn, bayesian_changepoint_detection, statsmodels, open3d)
- [X] T002b [P] Initialize Python 3.11 virtualenv and install dependencies
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `results/`, `interim/`)
- [ ] T005 [P] Implement `code/lib/alignment.py` for coordinate transform logic (UTM/Geographic)
- [ ] T006 [P] Implement `code/lib/degradation.py` for synthetic mask generation and downscaling logic
- [X] T007a [P] Create `code/lib/models.py` class `DegradedScene`
- [X] T007b [P] Create `code/lib/models.py` class `ReconstructedScene`
- [X] T007c [P] Create `code/lib/models.py` class `GroundTruthLiDAR`
- [ ] T007d [P] Create `code/lib/models.py` class `FidelityMetrics`
- [ ] T008 [P] Configure logging infrastructure to `data/results/execution.log` with structured JSON output
- [~] T009 [P] Setup environment configuration management (loaders for `city_list.txt`, random seeds)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Degradation & Ground Truth Alignment (Priority: P1) 🎯 MVP

**Goal**: Download a representative set of urban Sentinel-2 tiles, align with OpenTopography LiDAR, extract patches of varying sizes, and apply reproducible synthetic degradation (low-res, clouds, temporal shifts) with NNF variance.

**Independent Test**: A script generates paired samples where alignment error is < 2 meters, and degradation parameters (resolution, cloud coverage, NNF) are verified against the ground truth.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011a [P] [US1] Unit test for alignment error calculation in `tests/unit/test_alignment.py` (verify < 2m residual)
- [X] T011b [P] [US1] Unit test for degradation parameters in `tests/unit/test_degradation.py` (verify coarse spatial resolution and partial cloud coverage; **verify implementation of Kolmogorov-Smirnov (KS) test for mask distribution comparison**)
- [X] T011c [P] [US1] Unit test for cloud mask validation logic in `tests/unit/test_mask_validation.py` (verify KS-test implementation)

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/01_data_curation.py` to download Sentinel-2 (Microsoft Planetary Computer) and LiDAR (USGS 3DEP/NYC) for urban regions; **implement a `while count < 500` retry loop** that repeatedly downloads and aligns new batches until a sufficient number of valid samples (alignment error < 2m) are secured; save raw assets to `data/raw/` and generate `data/processed/raw_manifest.csv` listing all downloaded IDs; output the final filtered dataset to `data/processed/aligned_pairs.csv` and `data/processed/alignment_report.csv`
- [~] T013 [US1] Implement `code/01_patch_extraction.py` to **extract 100m² patches ** from the downloaded 1km² aligned tiles (output of T012); output to `data/processed/patches_100m2/`; ensure this step occurs BEFORE degradation to satisfy compute budget constraints (SC-003, FR-003); generate `data/processed/patch_manifest.csv`
- [~] T015 [US1] Acquire reference real cloud masks for a small subset of selected regions from Sentinel-2 Cloud Probability dataset (e.g., `S2MSK` products) and save to `data/raw/real_cloud_masks_subset/`; **define the statistical comparison method (Kolmogorov-Smirnov test)** to compare the distribution of synthetic masks against these real masks; **DO NOT** switch the data source to real masks, use only for tuning
- [~] T016 [US1] Implement `code/02b_validate_masks.py` to **perform the Kolmogorov-Smirnov test** between synthetic mask stats and `data/raw/real_cloud_masks_subset/`; output `data/results/mask_similarity_score.json`; if similarity < 0.8, **tune the degradation pipeline parameters** (T014a) to improve similarity, ensuring the experiment remains synthetic-only
- [X] T014a [US1] Implement `code/02_degradation_pipeline.py` to apply **downscale to coarse spatial resolution

The research question and method remain unchanged as per the original planning document, with the specific empirical value generalized to a qualitative descriptor.** and **procedural cloud masks** (tuned per T016) to the 100m² patches from T013; output intermediate degraded scenes to `data/processed/degraded_base/`; ensure the resolution is explicitly set to 30m/pixel ± 1%
- [~] T014b [US1] Implement `code/02_degradation_pipeline.py` to apply **temporal shifts** (simulating stale imagery via temporal interpolation or selection from adjacent dates) and **systematically vary NNF** (Normalized Noise Fraction) by sweeping degradation intensity across the sample set; output the final NNF-varied dataset to `data/processed/nnf_varied_scenes/` and `data/processed/degraded_manifest.json`
- [ ] T017 [US1] Save aligned pairs, patches, and degraded scenes to `data/processed/` with checksums in `data/manifest.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized Generative Restoration (Priority: P2)

**Goal**: Run 3D Gaussian Splatting (3DGS) and CPU-optimized inpainting (ONNX Runtime) on degraded scenes within 45 mins/scene and < 6.5 GB RAM, measuring performance metrics.

**Independent Test**: A single degraded patch is processed end-to-end on a multi-core CPU, producing a valid `.ply` file without CUDA errors, with logged RAM/time metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for ONNX Runtime initialization in `tests/unit/test_cpu_3dgs.py` (verify no GPU device calls)
- [~] T019 [P] [US2] Integration test for memory usage in `tests/integration/test_memory_limits.py` (verify < 6.5 GB peak RAM)

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/lib/cpu_3dgs_wrapper.py` to load CPU-quantized diffusion prior (low-bit/LCM) via ONNX Runtime; explicitly assert `torch.cuda.is_available()` is False and force `execution_provider=['CPUExecutionProvider']`
- [ ] T021 [US2] Implement `code/03_3dgs_baseline.py` to generate baseline 3DGS `.ply` scenes from the **degraded inputs in `data/processed/nnf_varied_scenes/` (from T014b)**; output to `data/processed/reconstructed/baseline/`; ensure completion < 30 mins per scene; **wrap execution with `memory_profiler` to log per-sample `peak_ram_mb` and `wall_clock_time` to a temporary buffer**
- [ ] T022 [US2] Implement `code/03_render_interface.py` to load the baseline `.ply` files from T021 and render 512x512 RGB and Depth maps using fixed camera intrinsics (f=1024, c=256) and fixed poses; output to `data/processed/reconstructed/rendered_interface/`; **this is the mandatory data interface for the inpainting module**
- [ ] T023 [US2] Implement `code/03_inpainting_restoration.py` to consume the **rendered maps from T022**, apply the CPU-optimized inpainting module, and generate Inpainted `.ply` files; output to `data/processed/reconstructed/inpainted/`; **wrap execution with `memory_profiler` to log per-sample `peak_ram_mb` and `wall_clock_time` to the same temporary buffer**
- [ ] T024 [US2] Implement `code/03_performance_logger.py` to **finalize the per-sample performance logs** from the temporary buffer (generated by T021/T023), ensuring `peak_ram_mb`, `wall_clock_time`, and `status` (success/ERR_OOM_CPU) are written for every sample to a staging file; handle `MemoryError` by logging `ERR_OOM_CPU`
- [ ] T027 [US2] Implement `code/03_ply_validator.py` to validate output `.ply` files for format compatibility and size < 500 MB; **ensure the staging performance logs from T024 are persisted** before aggregation
- [ ] T026 [US2] Implement `code/03_performance_aggregator.py` to **read the staging performance logs from T024/T027**, **verify that the total sample execution time fits within the GitHub Actions time window**, and **write per-sample rows** (including `sample_id`, `peak_ram_mb`, `wall_clock_time`, `status`) to `data/results/performance_log.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity Quantification & Threshold Analysis (Priority: P3)

**Goal**: Compute P-PSNR, P-SSIM, Chamfer Distance, and Geometric Divergence Score (GDS) against LiDAR, perform statistical significance testing using Wilcoxon and LMM, and identify the critical NNF threshold using the NNF-varied dataset from T014.

**Independent Test**: A script processes the NNF-varied dataset, outputs a metrics CSV including GDS, and generates a plot showing the performance drop-off curve with a identified NNF threshold (p > 0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026a [P] [US3] Unit test for Chamfer Distance calculation in `tests/unit/test_metrics.py` (verify normalized scale)
- [ ] T026b [P] [US3] Unit test for statistical significance (Wilcoxon/LMM) in `tests/unit/test_analysis.py` (verify p-value logic)

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/lib/metrics.py` to compute P-PSNR and P-SSIM between reconstructed and LiDAR scenes
- [ ] T029 [US3] Implement `code/lib/metrics.py` to compute Chamfer Distance on a normalized scale (meters)
- [ ] T029b [US3] Implement `code/lib/metrics.py` to compute **Geometric Divergence Score (GDS)** comparing Baseline vs Inpainted geometry to distinguish recovery from hallucination
- [ ] T030 [US3] Implement `code/04_metrics_evaluation.py` to run metrics (P-PSNR, P-SSIM, Chamfer Distance, **GDS**) on all samples from `data/processed/nnf_varied_scenes/` and save `data/results/metrics.csv`
- [ ] T031 [US3] Implement `code/05_threshold_analysis.py` to perform **Wilcoxon signed-rank test** on improvement (Inpainted - Baseline) and **Linear Mixed-Effects (LMM)** model with `scene_complexity` as random effect; log significance (p-value)
- [ ] T032 [US3] Implement `code/05_threshold_analysis.py` to sweep NNF thresholds using the dataset from T014, **calculate the p-value at each step using the Wilcoxon signed-rank test AND the Linear Mixed-Effects (LMM) model**, identify the critical failure point where **p > 0.05**, and extract the scalar value
- [ ] T033 [US3] Generate plots (performance drop-off curve, Recovery vs. Hallucination) in `data/results/` and save the critical NNF threshold scalar to `data/results/critical_threshold.json`

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Explicitly depends on T026 (US2 output)**

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
Task: "Unit test for cloud mask validation logic in tests/unit/test_mask_validation.py"

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