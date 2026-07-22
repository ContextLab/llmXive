# Tasks: llmXive follow-up: extending PhysisForcing (Physics Filter)

**Input**: Design documents from `/specs/001-llmxive-physs-filter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/` matching the exact directory tree in `plan.md`: `data/raw`, `data/curated`, `data/eval`, `src/generation`, `src/filtering`, `src/training`, `src/evaluation`, `src/utils`, `tests/unit`, `tests/integration`.
- [ ] T002 Initialize Python 3.11 project with CPU-only `torch`, `pybullet`, `mujoco`, `diffusers`, `transformers`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `sam2`, `zoe_depth`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Create `requirements.txt` with pinned versions and verify `pip install` on CPU-only runner

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup data directory structure: `data/raw`, `data/curated`, `data/eval` with checksumming utilities in `src/utils/io_utils.py`. **Include**: Create `assets/library.json` defining the mapping schema for prompt-to-scene translation (keyword -> .urdf asset, initial pose).
- [ ] T006 [P] Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics
- [ ] T007 Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU-only flags
- [ ] T007b [P] Create `config.yaml` with default key `filter_discard_percent: 0.4` and schema definition for all required keys
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected
- [ ] T009 [P] Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches
- [ ] T006b [P] Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks
- [ ] T012 [US1] Implement prompt management in `src/generation/prompts.py` loading verified RobotBench prompts. **Logic**: Load prompts from a verified static JSON file or URL defined in `assets/prompts.json`. **Note**: Moved to Phase 2 to ensure prompts are ready before generation.
- [ ] T012b [US1] Define and verify Wan2.1 CPU-compatible subset. **Logic**: Confirm availability of `Wan-Turbo (distilled 100M)` from `huggingface.co/Wan-AI/Wan2.1-Turbo`. If not available, raise error. **Output**: Verify script in `src/generation/verify_model.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU-based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset (n=10), verify physics filtering discards the bottom portion of the distribution based on score distribution, and ensure remaining videos pass continuity checks.

### Implementation for User Story 1

- [ ] T013 [US1] Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use 'Wan-Turbo (distilled 100M)' from `huggingface.co/Wan-AI/Wan2.1-Turbo`. **Logic**: If CPU inference fails (OOM or unsupported op), trigger offload to Kaggle GPU with `device="cuda"`, `batch_size=1`, and strict limit of 50 videos. **Dependency**: Requires T012 (prompts) and T012b (model verification). **Output**: Raw MP4s in `data/raw/`.
- [ ] T014 [US1] Implement prompt-to-scene translation in `src/filtering/prompt_to_scene.py`. **Logic**: Load `assets/library.json` (from T005) to map prompt keywords to specific PyBullet `.urdf` assets and initial poses (e.g., "grasp cup" -> `assets/cup.urdf`, pose (0,0,0)).
- [ ] T015 [US1] Implement canonical simulation in `src/filtering/pybullet_filter.py` (DEPENDS ON T014) to generate ground truth trajectories using PyBullet headless mode. **Logic**: Use the prompt-derived scene to run a deterministic simulation and output the "intended" trajectory for scoring.
- [ ] T016 [P] [US1] Implement CV pipeline in `src/filtering/cv_pipeline.py` using SAM2 and ZoeDepth for 3D trajectory extraction with Kalman filtering. **Constraint**: Must run in headless mode, processing frames in chunks to stay < 6GB RAM.
- [ ] T017a [US1] Implement metric calculation in `src/filtering/score_utils.py` to calculate trajectory continuity and contact conservation scores using ground truth from T015. **Output**: Continuous score (0-1) based on trajectory deviation and contact loss.
- [ ] T017 [US1] Orchestrate and aggregate scores in `src/filtering/pybullet_filter.py` (Requires: T015, T016, T017a output) to call T017a functions and generate raw scores for all videos.
- [ ] T018a [US1] Implement Pilot Run logic in `src/filtering/score_utils.py`. **Logic**: Generate a pilot set (n=50), calculate scores, determine the 60th percentile threshold, and **write this value to `config.yaml` key `filter_discard_percent`** (default 0.4 if pilot fails).
- [ ] T018 [US1] Implement filtering logic in `src/filtering/score_utils.py` to read `filter_discard_percent` from `config.yaml` (updated by T018a), discard a substantial portion of videos, and save curated dataset to `data/curated/`.
- [ ] T019 [US1] Add error handling for corrupted video frames in `src/filtering/pybullet_filter.py`. **Logic**: If frame decoding fails, assign score 0.0, log error, and exclude from dataset.
- [ ] T020 [US1] Add memory usage monitoring to ensure < 6 GB RAM during filtering in `src/utils/io_utils.py`.

### Tests for User Story 1 (Run AFTER Implementation)

- [ ] T011a [US1] Integration test: Verify generation of 10 samples and discard rate is within 5% of [deferred]. **Input**: 10 prompts from T012. **Output**: Verify `data/curated/` contains exactly 6 videos.
- [ ] T011b [US1] Integration test: Verify physics filter assigns low score to corrupted frames. **Input**: Inject a corrupted frame into a video. **Output**: Verify score < 0.1 and video is excluded.
- [ ] T011c [US1] Integration test: Verify curated dataset contains only videos with score >= threshold. **Input**: Run filter on known good set. **Output**: Verify min score in `data/curated/` >= 60th percentile of raw set.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of substantial capacity on the curated dataset using CPU-only optimization.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement data augmentation module in `src/training/augmentation.py` (temporal jittering, geometric flipping) for FR-009. **Logic**: Apply augmentation only if dataset size < 30.
- [ ] T024 [US2] Implement UNet-based diffusion model in `src/training/diffusion_trainer.py` (CPU-optimized). **Spec**: Target a reduced parameter count using reduced channels (64) and fewer blocks (4).. **Verify**: `abs(count_parameters - 50000000) / 50000000 <= 0.10`.
- [ ] T025 [US2] Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning rate adjustment (retry up to 3 times), and Timeout enforcement (hours).
- [ ] T026 [US2] Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for 7GB RAM. **Constraint**: Must fail loudly if real data fetch fails (no synthetic fallback).
- [ ] T027 [US2] Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`.
- [ ] T028 [US2] Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`.

### Tests for User Story 2 (Run AFTER Implementation)

- [ ] T022 [US2] Integration test for training on curated samples. **Input**: 60 videos from `data/curated/`. **Output**: Verify model converges (loss decreases) and saves a checkpoint within 4 hours.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R-Bench and PAI-Bench with statistical significance testing.

**Independent Test**: Run evaluation suite, generate JSON report with scores and p-values, and verify performance gap calculation.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement R-Bench scorer in `src/evaluation/r_bench.py`.
- [ ] T032 [P] [US3] Implement PAI-Bench scorer in `src/evaluation/pai_bench.py`.
- [ ] T033a [US3] Implement physics-informed loss function in `src/training/losses.py`. **Spec**: `L_phys = L2_norm(extracted_trajectory, canonical_trajectory)`. This is a differentiable loss term added to standard diffusion loss.
- [ ] T033b [US3] Implement baseline training loop in `src/training/baseline_trainer.py` (Requires: US2 completion, T033a, T024, T025). **Logic**: Train using `L_phys` + standard loss on the *raw* dataset.
- [ ] T033d [US3] Execute baseline training run on `data/raw` dataset (unfiltered) using the 'Physics-Informed Training Proxy' loss from T033a to generate baseline model artifacts. **Logic**: Use the *same random seed and split indices* as the filtered model's training set to ensure fair comparison.
- [ ] T033c [US3] Implement baseline artifact management in `src/evaluation/baseline_proxy.py` to load and manage the trained proxy model (Requires: T033d).
- [ ] T034 [US3] Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`.
- [ ] T035a [US3] Implement t-test and Mann-Whitney U statistical testing in `src/evaluation/stats.py` (FR-006 compliance).
- [ ] T035b [US3] Implement Linear Mixed Model (LMM) testing in `src/evaluation/stats.py`. **Logic**: Use LMM if batch effects are detected; otherwise use t-test on residuals.
- [ ] T036 [US3] Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`.
- [ ] T037a [US3] Generate distinct ground truth simulation files in `src/evaluation/ground_truth_gen.py`. **Spec**: Use T014 logic (prompt-to-scene) to generate ground truth from *prompts*, not video extraction. **Output**: JSON with keys: trajectory, initial_pose, video_id. **Details**: SI units, origin (0,0,0), Z-up axis, s timestep.
- [ ] T037b [US3] Fetch real-world data. **Logic**: Try to load `data/raw/real_subset` (if available). **Constraint**: If missing, raise `FileNotFoundError` (do NOT generate synthetic fallback for the source). Store in `data/eval/real_world_data/`.
- [ ] T037 [US3] Implement MuJoCo independent validation in `src/evaluation/mujoco_validator.py`. **INPUT**: Ground truth from T037a OR T037b (if real data exists). **Logic**: If T037b fails (no real data), use T037a only and log "Real data unavailable, using synthetic fallback". Requires: T037a AND T037b (or fallback) AND US1 output.
- [ ] T038 [US3] Implement correlation analysis in `src/evaluation/stats.py` comparing PyBullet scores (on CV-extracted trajectories) vs MuJoCo scores (on distinct ground truth) to verify correlation < 0.95 (non-circularity).
- [ ] T039 [US3] Generate final JSON report in `data/eval/results.json` with all metrics and p-values.
- [ ] T040 [US3] Add logic to trigger data augmentation if n < 30 before statistical testing in `src/evaluation/stats.py`.

### Tests for User Story 3 (Run AFTER Implementation)

- [ ] T030 [US3] Integration test for full evaluation pipeline. **Input**: Trained model, baseline model, n=30 eval set. **Output**: Verify `data/eval/results.json` contains valid scores, p-values, and gap calculation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T042 Code cleanup and refactoring for memory efficiency across all modules to reduce peak RAM to < 5.5 GB (verified by `src/utils/profile_memory.py`)
- [ ] T043 Performance optimization for CV pipeline (SAM2/ZoeDepth) to reduce processing time per video to < 2 minutes
- [ ] T044 [P] Additional unit tests for edge cases (corrupted frames, NaN loss, small dataset) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure all phases execute correctly on CPU-only runner
- [ ] T046 Verify all artifacts have content hashes recorded in `state/projects/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (curated dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (trained model) and US1 output (baseline data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately; US2 and US3 can start in parallel if US1 output is available
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for prompt-to-scene translation logic in tests/unit/test_prompt_to_scene.py"
Task: "Integration test: Verify generation of 10 samples and discard rate is within 5% of target"

# Launch all models for User Story 1 together:
Task: "Implement prompt-to-scene translation in src/filtering/prompt_to_scene.py"
Task: "Implement CV pipeline in src/filtering/cv_pipeline.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate, filter, verify discard rate)
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
 - Developer A: User Story 1 (Data Generation & Filtering)
 - Developer B: User Story 2 (Model Training) - *Wait for US1 output*
 - Developer C: User Story 3 (Evaluation) - *Wait for US1 & US2 output*
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
- **CRITICAL**: All tasks MUST run on CPU-only (limited cores, constrained RAM). No CUDA, no large model training, no GPU-specific libraries.
- **CRITICAL**: All data must be real. No fabricated datasets. Use verified URLs for RobotBench prompts and Wan2.1 weights.
- **CRITICAL**: MuJoCo validation (T037) MUST NOT use CV-extracted trajectories from T016; it must use distinct ground truth (T037a) or real-world data (T037b) to ensure non-circularity.
- **CRITICAL (Revision)**: Wan2.1 generation (T013) must explicitly handle CPU fallback or distilled CPU-compatible weights; if GPU is required for generation, the task MUST specify offloading to Kaggle GPU with `device="cuda"` and a strict sample size limit (e.g., 50 videos) to fit the 9h kernel, never fabricating a CPU-only generation step for a GPU-bound model.
- **CRITICAL (Revision)**: Data loading tasks (T012, T026) MUST implement a "fail loud" strategy: if the real dataset fetch fails, raise an exception immediately. Do NOT implement `try/except` blocks that fall back to synthetic/mock data generation, as this violates the fabrication guard.
- **CRITICAL (Revision)**: The "Physics-Informed Training Proxy" (T033a/T033b) must be implemented as a distinct training run on the *same* raw dataset (pre-filtering) to ensure a fair comparison against the filtered model, explicitly documenting the loss function difference (standard vs. physics-informed) to satisfy the hypothesis test.