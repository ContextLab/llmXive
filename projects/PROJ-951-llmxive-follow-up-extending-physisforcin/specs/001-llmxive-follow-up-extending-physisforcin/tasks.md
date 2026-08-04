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

- [ ] T001 Create project root directories under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`.
- [ ] T001b [P] Create `src/`, `tests/`, `data/` subdirectories and specific module directories (`data/raw`, `data/curated`, `data/eval`, `data/validation`, `src/generation`, `src/filtering`, `src/training`, `src/evaluation`, `src/utils`, `tests/unit`, `tests/integration`).
- [ ] T002 Initialize Python project with CPU-only `torch`, `pybullet`, `mujoco`, `diffusers`, `transformers`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `datasets`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Create `requirements.txt` with pinned versions and verify `pip install` on CPU-only runner

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup data directory structure: `data/raw`, `data/curated`, `data/eval`, `data/validation` with checksumming utilities in `src/utils/io_utils.py`.
- [ ] T006 [P] Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics
- [ ] T007 Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU-only flags
- [ ] T007b [P] Create `config.yaml` with default key `filter_discard_percent: 0.4` and schema definition for all required keys
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected
- [ ] T009 [P] Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches
- [ ] T006b [P] Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks
- [ ] T012 [US1] Implement prompt management in `src/generation/prompts.py` loading verified RobotBench prompts. **Logic**: Load prompts from a verified static JSON file or URL defined in `data/prompts.json`. **Note**: Moved to Phase 2 to ensure prompts are ready before generation.
- [ ] T012b [US1] {{claim:c_bdc111ab}} (Wikipedia: Alibaba Group, https://en.wikipedia.org/wiki/Alibaba_Group). **Logic**: Verify availability of `Wan2.1` model family from `huggingface.co/Wan-AI/Wan2.1-Turbo`. Prefer `Wan-Turbo (distilled a large-scale model)` if available; otherwise, verify any compatible Wan2.1 variant. **Output**: Verify script in `src/generation/verify_model.py`. **Dependency**: Depends on T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU-based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset (n=10), verify physics filtering discards the bottom [deferred] of the distribution based on score distribution, and ensure remaining videos pass continuity checks.

### Implementation for User Story 1

- [ ] T013 [US1] Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use 'Wan-Turbo (distilled 100M)' from `huggingface.co/Wan-AI/Wan2.1-Turbo`. **Logic**: If CPU inference fails (OOM or unsupported op), trigger offload to Kaggle GPU with `device="cuda"`, `batch_size=1 `, and a strict limit on the number of videos. **Dependency**: Requires T012 (prompts) and T012b (model verification). **Output**: Raw MP4s in `data/raw/` and metadata in `data/raw/metadata.jsonl`.
- [ ] T015 [US1] Implement physics scoring in `src/filtering/pybullet_filter.py`. **Logic**: Load generated video from `data/raw/`. Simulate the scene using PyBullet headless mode to extract ground truth trajectory (if prompt allows) OR score the video's extracted trajectory (via simple optical flow or frame differencing if full 3D extraction is too heavy, but preferred: direct simulation comparison if prompt-to-scene is skipped). **Correction**: Per plan, score the *generated video* against physics. Use `pybullet` to simulate the expected motion based on the prompt's semantic description (e.g., "grasp cup" -> simulate grasp) and compare with video content. **Constraint**: DO NOT use optical flow as a fallback. If PyBullet simulation fails, assign a score of 0.0 and log the error. **Output**: `data/curated/scores.parquet` with columns `video_id`, `continuity_score`, `contact_score`.
- [ ] T016 [US1] Implement filtering logic in `src/filtering/score_utils.py`. **Logic**: Read `data/curated/scores.parquet`. Apply discard rate defined in `config.yaml` (default a moderate threshold). Discard a substantial portion of the lowest-quality videos. Save remaining to `data/curated/` and `data/curated/curated_metadata.jsonl`. **Constraint**: No dynamic pilot runs.
- [ ] T019 [US1] Add error handling for corrupted video frames in `src/filtering/pybullet_filter.py`. **Logic**: If frame decoding fails, assign score 0.0, log error, and exclude from dataset.
- [ ] T020 [US1] Add memory usage monitoring to ensure < 6 GB RAM during filtering in `src/utils/io_utils.py`.
- [ ] T047 [US1] Implement "Fail Loud" data loader in `src/generation/wan21_generator.py`. **Logic**: Remove any `try/except` blocks that fall back to synthetic data. If the Wan2.1 model download or inference fails, raise a `RuntimeError` with a clear message directing the user to check the verified URL or GPU offload configuration.

### Tests for User Story 1 (Run AFTER Implementation)

- [ ] T011a [US1] Integration test: Verify generation of 10 samples and discard rate is within 5% of `config.yaml` value (A threshold will be established during the implementation phase.). **Input**: 10 prompts from T012. **Output**: Verify `data/curated/` contains a set of videos.
- [ ] T011b [US1] Integration test: Verify physics filter assigns low score to corrupted frames. **Input**: Inject a corrupted frame into a video. **Output**: Verify score < 0.1 and video is excluded.
- [ ] T011c [US1] Integration test: Verify curated dataset contains only videos with score >= threshold. **Input**: Run filter on known good set. **Output**: Verify min score in `data/curated/` >= 60th percentile of raw set.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of substantial capacity on the curated dataset using CPU-only optimization.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement data augmentation module in `src/training/augmentation.py` (temporal jittering, geometric flipping) for FR-009. **Logic**: Apply augmentation only if dataset size < 30. [UNRESOLVED-CLAIM: c_36f7b156 — status=not_enough_info]
- [ ] T019b [US2] Augment Curated Dataset if size < 30. **Logic**: Check `len(data/curated/)`. If < 30, apply augmentation from T023 to reach n=30. **Dependency**: Depends on T016. **Output**: Augmented dataset in `data/curated_augmented/`.
- [ ] T024 [US2] Implement UNet-based diffusion model in `src/training/diffusion_trainer.py` (CPU-optimized). **Spec**: Target a compact diffusion model (target a large-scale parameter count). **Logic**: Configure UNet architecture (channels, down/up blocks, attention heads) such that the total parameter count is approximately 50M (±10%) and peak RAM usage remains within acceptable limits. **Verification**: Add a check in `src/training/config.py` to validate parameter count and memory footprint before training starts. **Note**: Architecture details (e.g., 64 channels, 4 blocks) are implementation choices to meet the ~50M target, not rigid constraints.
- [ ] T025 [US2] Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning rate adjustment (retry up to 3 times), and Timeout enforcement (hours).
- [ ] T026 [US2] Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for GB RAM. **Constraint**: Must fail loudly if real data fetch fails (no synthetic fallback).
- [ ] T027 [US2] Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`.
- [ ] T028 [US2] Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`.
- [ ] T017 [US2] Train Randomized Control Model. **Logic**: Use the same training script as T024/T025. Load `data/raw/` using the *same split indices* as T016 (Curated) but on the raw dataset (random subset of same size). **Output**: `models/control_model/`. **Dependency**: Depends on T016.
- [ ] T048 [US2] Implement "Fail Loud" data loader in `src/training/diffusion_trainer.py`. **Logic**: Ensure the data loader raises an exception if `data/curated/` is empty or missing, preventing any fallback to synthetic/mock data.

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
- [ ] T033a [US3] Load PhysisForcing Baseline Results. **Logic**: Fetch verified results from the PhysisForcing paper (or a pre-computed artifact if available in `data/baseline/`). **Output**: `data/eval/physisforing_baseline.json` with `r_bench_score`, `pai_bench_score`. **Constraint**: If not found, raise `FileNotFoundError` (no synthetic fallback).
- [ ] T034 [US3] Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`.
- [ ] T035a [US3] Implement t-test and Mann-Whitney U statistical testing in `src/evaluation/stats.py` (FR-006 compliance).
- [ ] T036 [US3] Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`.
- [ ] T037a [US3] Implement distinct ground truth simulation in `src/evaluation/ground_truth_gen.py`. **Spec**: Use T015 logic (prompt-to-scene simulation) to generate ground truth from *prompts*, not video extraction. **Output**: JSON with keys: trajectory, initial_pose, video_id. **Details**: SI units, origin (0,0,0), Z-up axis, s timestep.
- [ ] T037b [US3] Fetch real-world data. **Logic**: Load `data/raw/real_subset` (if available) or fetch from `RobotBench` dataset via `datasets.load_dataset("RobotBench")`. **Constraint**: If missing, log a warning and proceed without real-world data (do NOT generate synthetic fallback for the source). Store in `data/eval/real_world_data/`.
- [ ] T037 [US3] Implement MuJoCo independent validation in `src/evaluation/mujoco_validator.py`. **INPUT**: Ground truth from T037a AND Real-world data from T037b (if available) OR Baseline results from T033a. **Logic**: If T037b fails (no real data), use T037a and T033a only and log "Real data unavailable, using synthetic baseline". Requires: T037a AND T037b (optional) AND T013, T016 (US1 output). **Dependency**: Depends on T013, T016, T037a, T037b (optional).
- [ ] T038 [US3] Implement correlation analysis in `src/evaluation/stats.py` comparing PyBullet scores (on CV-extracted trajectories) vs MuJoCo scores (on distinct ground truth) to verify correlation < 0.95 (non-circularity).
- [ ] T039 [US3] Generate final JSON report in `data/eval/results.json` with all metrics and p-values.
- [ ] T040 [US3] Add logic to trigger data augmentation if eval subset n < 30 before statistical testing in `src/evaluation/stats.py`. **Logic**: If eval subset < 30, trigger T019b augmentation logic.
- [ ] T049 [US3] Implement "Fail Loud" baseline loader in `src/evaluation/stats.py`. **Logic**: Ensure that if the PhysisForcing baseline data (T033a) is missing or invalid, the evaluation raises an error rather than synthesizing a proxy baseline.

### Tests for User Story 3 (Run AFTER Implementation)

- [ ] T030 [US3] Integration test for full evaluation pipeline. **Input**: Trained model, baseline model, n=30 eval set. **Output**: Verify `data/eval/results.json` contains valid scores, p-values, and gap calculation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T042 Code cleanup and refactoring for memory efficiency across all modules to reduce peak RAM to < 5.5 GB (verified by `src/utils/profile_memory.py`)
- [ ] T043 Performance optimization for CV pipeline (if used) to reduce processing time per video to < 2 minutes
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
- Commit after each logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All tasks MUST run on CPU-only (limited cores, constrained RAM). No CUDA, no large model training, no GPU-specific libraries.
- **CRITICAL**: All data must be real. No fabricated datasets. Use verified URLs for RobotBench prompts and Wan2.1 weights.
- **CRITICAL**: MuJoCo validation (T037) MUST NOT use CV-extracted trajectories from T016; it must use distinct ground truth (T037a) or real-world data (T037b) to ensure non-circularity.
- **CRITICAL (Revision)**: Wan2.1 generation (T013) must explicitly handle CPU fallback or distilled CPU-compatible weights; if GPU is required for generation, the task MUST specify offloading to Kaggle GPU with `device="cuda"` and a strict sample size limit (e.g., a manageable cohort) to fit the 9h kernel, never fabricating a CPU-only generation step for a GPU-bound model.
- **CRITICAL (Revision)**: Data loading tasks (T012, T026) MUST implement a "fail loud" strategy: if the real dataset fetch fails, raise an exception immediately. Do NOT implement `try/except` blocks that fall back to synthetic/mock data generation, as this violates the fabrication guard.
- **CRITICAL (Revision)**: The "Physics-Informed Training Proxy" is REMOVED. The baseline comparison is now against the *actual* PhysisForcing paper results (T033a) or the *Randomized Control* model (T017) trained on raw data with the same algorithm.
- **CRITICAL (Revision)**: The discard rate is FIXED at a predetermined level. (T018/T016). No pilot runs or dynamic thresholds.
- **NEW (Revision Concern)**: Added T047, T048, T049 to explicitly enforce "Fail Loud" data loading across generation, training, and evaluation modules to prevent any silent substitution of synthetic data.
- **NEW (Revision Concern)**: Added T019b for dataset augmentation if n < 30, and updated T040 to handle eval-set augmentation.
- **NEW (Revision Concern)**: Added T018 for MuJoCo validation and orthogonality check as a pre-training gate.
- **NEW (Revision Concern)**: Removed optical flow fallback from T015 to ensure strict physics simulation.
- **NEW (Revision Concern)**: Updated T016 and T011a to use `config.yaml` for discard rate, resolving `[deferred]` placeholder.
- **NEW (Revision Concern)**: Updated T037b to log warning instead of raising error if real data is missing.
- **NEW (Revision Concern)**: Updated T012b to verify Wan2.1 family instead of strict 100M variant.
- **NEW (Revision Concern)**: Updated T024 to explicitly state 50M parameter target.
- **NEW (Revision Concern)**: Split T001 into T001 and T001b for better granularity.
- **NEW (Revision Concern)**: Added explicit dependencies to T037, T017, T012b.
- **NEW (Revision Concern)**: Removed [P] tag from T012b.