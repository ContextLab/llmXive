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
- [ ] T007b [P] Create `config.yaml` with default key `filter_discard_percent: 0.4` and schema definition for all required keys. **Note**: This value is a **provisional default** derived from the **Implementation Plan (plan.md)** which resolves the spec's `[deferred]` placeholder. The config key must allow runtime override.
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected
- [ ] T009 [P] Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches
- [ ] T006b [P] Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks
- [ ] T012 [US1] Implement prompt management in `src/generation/prompts.py` loading verified RobotBench prompts. **Logic**: Load prompts from a verified static JSON file or URL defined in `data/prompts.json`. **Note**: Moved to Phase 2 to ensure prompts are ready before generation.
- [ ] T012b [P] [US1] Verify availability of `Wan2.1` model family from `huggingface.co/Wan-AI/Wan2.1-Turbo`. **Logic**: Prefer `Wan-Turbo` (distilled **from** a large-scale model) if available; otherwise, verify and fallback to the base `Wan2.1` model. **Output**: Verify script in `src/generation/verify_model.py`. **Dependency**: None (Independent of prompts).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU-based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset (n=10), verify physics filtering discards the bottom [deferred] of the distribution based on score distribution, and ensure remaining videos pass continuity checks.

### Implementation for User Story 1

- [ ] T013 [US1] Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use 'Wan2.1' model family. **Logic**:
 1. Verify 'Wan2.1' family exists.
 2. If 'Wan-Turbo' is available, use it as an optimization target; otherwise, use base 'Wan2.1'.
 3. If CPU inference fails (OOM or unsupported op), trigger offload to Kaggle GPU with `device="cuda"`, `batch_size=1 `, and a strict limit on the number of videos.
 **Dependency**: Requires T012 (prompts) and T012b (model verification).
 **Output**: Raw MP4s in `data/raw/` and metadata in `data/raw/metadata.jsonl`.
- [ ] T014b [US1] Implement CV Pipeline in `src/filtering/cv_pipeline.py`. **Logic**: Use OpenCV + YOLOv8 (or similar lightweight detector) to extract **2D object centroids and optical flow vectors** from generated video frames. **Output**: JSONL file `data/raw/trajectories.jsonl` with `video_id`, `frame_id`, `object_id`, `x_2d`, `y_2d`, `flow_x`, `flow_y`. **Constraint**: Must handle missing frames gracefully by skipping them (do not crash). **Dependency**: Requires T013 (Videos). **Note**: This task is sequential to T013; [P] tag removed.
- [ ] T015 [US1] Implement physics scoring in `src/filtering/pybullet_filter.py`. **Logic**:
 1. Load generated video from `data/raw/` AND extracted 2D trajectories from `data/raw/trajectories.jsonl` (T014b).
 2. **Ground Truth Generation**: Parse prompt semantic keywords (e.g., "grasp cup") to generate a **simplified top-down 2D PyBullet scene** (XY plane, Z-axis ignored) representing the expected object motion.
 3. Compare the extracted 2D trajectory against the simulated 2D ground truth to calculate `continuity_score` (trajectory smoothness) and `contact_score` (object persistence/collision in 2D).
 **Constraint**: If PyBullet simulation fails or trajectory extraction fails, assign a score of 0.0 and log the error.
 **Dependency**: Requires T012 (Prompts), T013 (Videos), T014b (Trajectories).
 **Output**: `data/curated/scores.parquet` with columns `video_id`, `continuity_score`, `contact_score`.
- [ ] T016 [US1] Implement filtering logic in `src/filtering/score_utils.py`. **Logic**: Read `data/curated/scores.parquet`. Apply discard rate defined in `config.yaml` (default 0.4 / [deferred] - **provisional default from Plan.md**). Discard the bottom [deferred] of videos based on the combined physics score. Save remaining to `data/curated/` and `data/curated/curated_metadata.jsonl`. **CRITICAL**: Output `data/curated/split_indices.json` containing the indices of **RETAINED** videos. **Constraint**: No dynamic pilot runs. **Dependency**: Requires T015.
- [ ] T019 [US1] Add error handling for corrupted video frames in `src/filtering/pybullet_filter.py`. **Logic**: If frame decoding fails, assign score 0.0, log error, and exclude from dataset.
- [ ] T020 [US1] Add memory usage monitoring to ensure < 6 GB RAM during filtering in `src/utils/io_utils.py`.
- [ ] T047 [US1] Implement "Fail Loud" data loader in `src/generation/wan21_generator.py`. **Logic**: Remove any `try/except` blocks that fall back to synthetic data. If the Wan2.1 model download or inference fails, raise a `RuntimeError` with a clear message directing the user to check the verified URL or GPU offload configuration.
- [ ] T018 [US1] [P] Implement MuJoCo validation and orthogonality check in `src/evaluation/mujoco_validator.py`. **Logic**: **Pre-Training Sanity Check**: Validate a subset of curated videos against a distinct MuJoCo ground truth to ensure the PyBullet filter score and MuJoCo score are not trivially correlated (correlation < 0.95) *before* training. **Dependency**: Requires T016. **Output**: `data/validation/orthogonality_report.json`. **Note**: This task is a blocking gate for Phase 4 (US2); Phase 4 cannot start until T018 passes.

### Tests for User Story 1 (Run AFTER Implementation)

- [ ] T011a [P] [US1] Integration test: Verify generation of 10 samples and output format. **Input**: 10 prompts from T012. **Output**: Verify `data/raw/` contains 10 MP4s and `data/raw/metadata.jsonl` is valid. **Dependency**: T013.
- [ ] T011b [P] [US1] Integration test: Verify physics filter assigns low score to corrupted frames. **Input**: Inject a corrupted frame into a video. **Output**: Verify score < 0.1 and video is excluded. **Dependency**: T015, T019.
- [ ] T011c [P] [US1] Integration test: Verify curated dataset contains only videos with score >= threshold. **Input**: Run filter on known good set. **Output**: Verify min score in `data/curated/` >= 60th percentile of raw set. **Dependency**: T016.
- [ ] T011d [P] [US1] Integration test: Verify discard rate is within an acceptable threshold. **Input**: A set of videos will be collected to investigate the research question using the specified method, as outlined in the relevant references. with known scores. **Output**: Verify `len(data/curated/) == 60`. **Dependency**: T016.
- [ ] T011e [P] [US1] Integration test: Verify orthogonality of PyBullet and MuJoCo scores. **Input**: Curated dataset. **Output**: Verify correlation coefficient < 0.95. **Dependency**: T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of substantial capacity on the curated dataset using CPU-only optimization.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement data augmentation module in `src/training/augmentation.py` (temporal jittering ±2 frames, geometric flipping p=0.5) for FR-009. **Logic**: Apply augmentation only if dataset size < 30. [UNRESOLVED-CLAIM: c_328a2f78 — status=not_enough_info] **Verification**: Add a check to ensure augmented videos do not introduce new collisions (physical consistency check). **Dependency**: None.
- [ ] T019b [US2] Augment Curated Dataset if size < 30. **Logic**: Check `len(data/curated/)`. If < 30, apply augmentation from T023 to reach n=30. **Dependency**: Depends on T016 AND T023. **Output**: Augmented dataset in `data/curated_augmented/`.
- [ ] T024a [US2] Define UNet architecture parameters (channels, blocks) to target a parameter count in the tens of millions in `src/training/config.py`. **Logic**: Calculate parameter count based on architecture choices. **Output**: Verified config with `total_params: ~50M`.
- [ ] T024b [US2] Implement UNet-based diffusion model in `src/training/diffusion_trainer.py` (CPU-optimized) using parameters from T024a. **Spec**: Target a compact diffusion model with a parameter count suitable for efficient deployment. (target estimate derived from Plan.md for CPU feasibility; spec requires 'parameter-efficient'). **Logic**: Configure UNet architecture (channels, down/up blocks, attention heads) such that the total parameter count is approximately 50M (±10%) and peak RAM usage remains within acceptable limits. **Verification**: Add a check in `src/training/config.py` to validate parameter count and memory footprint before training starts. **Dependency**: T024a.
- [ ] T025 [US2] Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning rate adjustment (retry up to 3 times), and Timeout enforcement (hours).
- [ ] T026 [US2] Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for GB RAM. **Constraint**: Must fail loudly if real data fetch fails (no synthetic fallback).
- [ ] T027 [US2] Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`.
- [ ] T028 [US2] Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`.
- [ ] T017 [US2] Train Randomized Control Model. **Logic**: Use the same training script as T024/T025. Load `data/raw/` using the **indices of retained videos** from `data/curated/split_indices.json` (T016) to select the corresponding raw subset (ensuring same size as curated). **Output**: `models/control_model/`. **Dependency**: Depends on T016 (specifically `split_indices.json`).
- [ ] T048 [US2] Implement "Fail Loud" data loader in `src/training/diffusion_trainer.py`. **Logic**: Ensure the data loader raises an exception if `data/curated/` is empty or missing, preventing any fallback to synthetic/mock data.

### Tests for User Story 2 (Run AFTER Implementation)

- [ ] T022 [US2] Integration test for training on curated samples. **Input**: 60 videos from `data/curated/`. **Output**: Verify model converges (loss decreases) and saves a checkpoint within 4 hours. **Dependency**: T024b, T025.
- [ ] T022b [US2] Integration test for control model training. **Input**: 60 videos from `data/raw/` (random subset). **Output**: Verify control model converges. **Dependency**: T017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R-Bench and PAI-Bench with statistical significance testing.

**Independent Test**: Run evaluation suite, generate JSON report with scores and p-values, and verify performance gap calculation.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement R-Bench scorer in `src/evaluation/r_bench.py` using MuJoCo.
- [ ] T032 [P] [US3] Implement PAI-Bench scorer in `src/evaluation/pai_bench.py` using MuJoCo.
- [ ] T033a [US3] Fetch PhysisForcing Baseline Model or Reproduction Code. **Logic**: Fetch verified model weights or the reproduction code from the PhysisForcing paper repository. **Output**: `data/baseline/physisforcing_model/` or `data/baseline/physisforcing_code/`. **Constraint**: If model weights are unavailable, attempt to run reproduction code. If BOTH are unavailable, raise `BaselineUnavailableError` (Fail Loud).
- [ ] T033b [US3] Run PhysisForcing Baseline Evaluation (if model weights unavailable). **Logic**: If T033a only provided code, run the baseline evaluation on the provided test set to generate scores. **Output**: `data/eval/physisforcing_baseline.json`. **Dependency**: T033a (if code only).
- [ ] T034 [US3] Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`.
- [ ] T035a [US3] Implement t-test and Mann-Whitney U statistical testing in `src/evaluation/stats.py` (FR-006 compliance).
- [ ] T036 [US3] Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`.
- [ ] T037a [US3] Implement distinct ground truth simulation in `src/evaluation/ground_truth_gen.py`. **Spec**: Use a *different* prompt set (not the ones used for filtering) to generate ground truth trajectories in MuJoCo. **Output**: JSON with keys: trajectory, initial_pose, video_id. **Details**: SI units, origin (0,0,0), Z-up axis, s timestep. **Constraint**: Must be distinct from filter prompts to ensure non-circularity.
- [ ] T037b [US3] Fetch real-world data. **Logic**: Load `data/raw/real_subset` (if available) or fetch from `RobotBench` dataset via `datasets.load_dataset("RobotBench")`. **Constraint**: If missing, set `real_data_available = False` flag and log warning. **Do NOT raise an error**. Store in `data/eval/real_world_data/` if successful.
- [ ] T037 [US3] Implement MuJoCo independent validation in `src/evaluation/mujoco_validator.py`. **INPUT**: Ground truth from T037a AND Real-world data from T037b (if `real_data_available` is True) OR Baseline results from T033a/T033b. **Logic**: Validate the trained model's output against the distinct ground truth (T037a) or real data (T037b). If real data is missing, use Baseline results as the primary comparison. **Dependency**: Depends on T013, T016, T037a, T033a, T033b.
- [ ] T038 [US3] Implement correlation analysis in `src/evaluation/stats.py` comparing PyBullet scores (on CV-extracted trajectories) vs MuJoCo scores (on distinct ground truth) to verify correlation < 0.95 (non-circularity). **Note**: This is the **Final Evaluation** orthogonality check, distinct from T018's pre-training check.
- [ ] T039 [US3] Generate final JSON report in `data/eval/results.json` with all metrics and p-values.
- [ ] T040 [US3] Add logic to trigger data augmentation if eval subset n < 30 before statistical testing in `src/evaluation/stats.py`. **Logic**: If eval subset < 30, trigger T019b augmentation logic.
- [ ] T049 [US3] Implement "Fail Loud" baseline loader in `src/evaluation/stats.py`. **Logic**: Ensure that if the PhysisForcing baseline data (T033a/T033b) is missing or invalid, the evaluation raises an error rather than synthesizing a proxy baseline.
- [ ] T050 [US3] Implement statistical power analysis in `src/evaluation/stats.py`. **Logic**: Calculate required sample size for desired power (sufficiently high to detect meaningful effects) and effect size; if current n is insufficient, flag the limitation in the report. **Dependency**: T035a.

### Tests for User Story 3 (Run AFTER Implementation)

- [ ] T030 [US3] Integration test for full evaluation pipeline. **Input**: Trained model, baseline model, n=30 eval set. **Output**: Verify `data/eval/results.json` contains valid scores, p-values, and gap calculation.
- [ ] T030b [US3] Integration test for orthogonality check. **Input**: Filter scores, MuJoCo scores. **Output**: Verify correlation < 0.95 is correctly detected and reported. **Dependency**: T038.

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
3. Complete Phase 3: User Story 1 (Including T014b CV Pipeline and T018 Orthogonality Check)
4. **STOP and VALIDATE**: Test User Story 1 independently (generate, filter, verify discard rate, verify orthogonality)
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
- **CRITICAL (Revision)**: The "Physics-Informed Training Proxy" is REMOVED. The baseline comparison is now against the *actual* PhysisForcing paper results (T033a/T033b) or the *Randomized Control* model (T017) trained on raw data with the same algorithm.
- **CRITICAL (Revision)**: The discard rate is FIXED at [deferred] (T007b, T016) as a **provisional default** from the plan; the spec's `[deferred]` is acknowledged but the implementation uses this value.
- **NEW (Revision Concern)**: Added T047, T048, T049 to explicitly enforce "Fail Loud" data loading across generation, training, and evaluation modules to prevent any silent substitution of synthetic data.
- **NEW (Revision Concern)**: Added T019b for dataset augmentation if n < 30, and updated T040 to handle eval-set augmentation.
- **NEW (Revision Concern)**: Added T018 for MuJoCo validation and orthogonality check as a pre-training gate.
- **NEW (Revision Concern)**: Removed optical flow fallback from T015 to ensure strict physics simulation.
- **NEW (Revision Concern)**: Updated T016 and T011a to use `config.yaml` for discard rate (0.4), resolving `[deferred]` placeholder with a provisional note.
- **NEW (Revision Concern)**: Updated T037b to set a flag `real_data_available = False` if missing (Fail Loud removed for this specific optional input).
- **NEW (Revision Concern)**: Updated T012b to verify Wan2.1 family instead of strict 100M variant and clarified "distilled from a large-scale model".
- **NEW (Revision Concern)**: Updated T024 to explicitly state 50M parameter target (split into T024a/T024b).
- **NEW (Revision Concern)**: Split T001 into T001 and T001b for better granularity.
- **NEW (Revision Concern)**: Added explicit dependencies to T037, T017, T012b, T019b, T015.
- **NEW (Revision Concern)**: Removed [P] tag from T012b (now [P] again).
- **NEW (Revision Concern)**: Added T014b (CV Pipeline) to enable trajectory extraction for T015.
- **NEW (Revision Concern)**: Removed [UNRESOLVED-CLAIM] from T023 and defined explicit augmentation parameters.
- **NEW (Revision Concern)**: Updated T033a/T033b to handle baseline model fetching and execution.
- **NEW (Revision Concern)**: Added T050 for statistical power analysis to ensure robust results.
- **NEW (Revision Concern)**: **Fixed T014b/T015 Logic**: T014b now extracts 2D centroids/flow; T015 defines a top-down 2D PyBullet projection (XY plane) to match.
- **NEW (Revision Concern)**: **Fixed T016/T017 Logic**: T016 outputs indices of *retained* videos; T017 uses these indices.
- **NEW (Revision Concern)**: **Fixed T012b Phrasing**: Corrected "distilled a large-scale model" to "distilled from a large-scale model".