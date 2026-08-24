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

- [ ] T001a [P] Create project root directory `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`. **Output**: Empty directory. **Dependency**: None.
- [ ] T001b [P] Create subdirectories under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/` including `src/`, `tests/`, `data/` and specific module directories (`data/raw`, `data/curated`, `data/eval`, `data/validation`, `src/generation`, `src/filtering`, `src/training`, `src/evaluation`, `src/augmentation`, `src/utils`, `tests/unit`, `tests/integration`). **Output**: Directory structure. **Dependency**: T001a.
- [ ] T002a [P] Create `requirements.txt` with pinned versions for CPU-only `torch`, `pybullet`, `mujoco`, `diffusers`, `transformers`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `datasets`. **Output**: `requirements.txt`. **Dependency**: None.
- [ ] T002b [P] Install dependencies from `requirements.txt` in a virtualenv and verify `pip install` on CPU-only runner. **Output**: Installed environment. **Dependency**: T002a.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools. **Output**: `pyproject.toml` or config files. **Dependency**: T002b.
- [X] T004 [P] Verify `requirements.txt` installation on CPU-only runner. **Dependency**: T002b.
- [ ] T007 [P] Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU-only flags. **Output**: `src/training/config.py`. **Dependency**: T002b.
- [ ] T007b [P] Create `config.yaml` with schema definition and a **configurable parameter** `discard_percentile` (default 40) representing the percentage of videos to discard from the bottom of the distribution. **Output**: `config.yaml`. **Dependency**: None (Phase 1). **Note**: This task defines the experimental parameter for the percentile-based filter. **Constraint**: The value represents the bottom percentage to discard (e.g., 40 means discard the bottom [deferred]). **Justification**: This value is derived from the hypothesis that discarding the bottom portion yields high-quality data. **Fallback**: The implementation MUST dynamically calculate the score threshold corresponding to this percentile from the batch distribution (e.g., if discard_percentile=40, threshold = 40th percentile score).
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected. **Output**: `src/utils/verify_env.py`. **Dependency**: T002b.
- [ ] T009 [P] Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches. **Output**: `src/utils/seeding.py`. **Dependency**: T002b.
- [ ] T006b [P] Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks. **Output**: `src/utils/profile_memory.py`. **Dependency**: T002b.
- [ ] T023 [P] [US2] Define Data Augmentation Module in `src/augmentation/geometric_augmenter.py` (temporal jittering, geometric flipping) for FR-009. **Logic**: Define the augmentation functions (code only, no execution). **Specifics**: Apply temporal jittering (±10% speed) and geometric flipping (horizontal). **Dependency**: None (Phase 2). **Note**: This task produces the *code* for the module; execution happens in T016c.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a [P] Create data directory structure: `data/raw`, `data/curated`, `data/eval`, `data/validation`. **Output**: Directories. **Dependency**: T001b.
- [ ] T005b [P] Implement checksumming utilities in `src/utils/io_utils.py`. **Output**: `src/utils/io_utils.py`. **Dependency**: T005a.
- [ ] T006 [P] Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics. **Output**: `src/utils/logging.py`. **Dependency**: T002b.
- [ ] T012 [P] Load Verified Prompts. **Logic**: Generate `data/prompts.jsonl` by writing a hardcoded list of standard robotic manipulation prompts (e.g., "robot arm pushing red block", "robot arm lifting blue cup") to the file. **Output**: `data/prompts.jsonl`. **Dependency**: None (Phase 1). **Note**: This task satisfies FR-001's requirement for prompt loading by generating the artifact.
- [ ] T033a-1 [P] [US3] Fetch PhysisForcing Baseline Results. **Logic**: Attempt to fetch verified results from the PhysisForcing paper (e.g., from a canonical HuggingFace dataset or GitHub repo). **Constraint**: If fetch fails, write `fetch_status: failed` to `state/baseline_fetch.json` and do NOT abort immediately; proceed to T033a-2 to check for local cache. If both fail, raise `RuntimeError`. **Output**: `data/eval/physisforcing_baseline.json` OR `state/baseline_fetch.json` with failure flag. **Dependency**: None.

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU-based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset (n=10), verify physics filtering discards the lower tail of the distribution

Reference: [Citation preserved]
Research Question: [Research Question preserved]
Method: [Method preserved] based on score distribution, and ensure remaining videos pass continuity checks.

### Implementation for User Story 1

- [ ] T013a [P] [US1] Check Kaggle Offload Availability. **Logic**: Verify if Kaggle credentials and environment are configured (e.g., `KAGGLE_KEY` env var exists). **Output**: Boolean flag `kaggle_available`. **Dependency**: None. **Note**: This task ensures T013 can abort gracefully if offload is not configured.
- [ ] T013 [US1] Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use 'Wan-AI/Wan-Turbo' from `huggingface.co/Wan-AI/Wan2.1-Turbo`. **Logic**: Attempt CPU inference by setting `torch.set_device('cpu')` and `device_map="cpu"`. If CPU inference fails (OOM or unsupported op), check `kaggle_available` (from T013a). If true, offload to Kaggle GPU. If false, raise a `RuntimeError` with a clear message indicating the specific CPU limitation and abort. **NO** silent fallback. **Dependency**: T012 (prompts), T013a. **Output**: Raw MP4s in `data/raw/` and metadata in `data/raw/metadata.jsonl`.
- [ ] T015b [US1] Create Direct Frame Extraction for Simulation. **Logic**: Create `src/filtering/reconstruction.py` to convert video frames (MP4) into PyBullet state vectors (position, velocity, contact points) using **lightweight, deterministic methods**: `opencv-python` for frame differencing to detect motion and simple color thresholding to identify object bounding boxes. **Constraint**: MUST NOT use optical flow, pose estimation, or complex object detection. Must handle corrupted frames gracefully (log error, assign default state). **Output**: `data/raw/reconstructed_states.parquet` with columns `video_id`, `frame_states`. **Dependency**: T013. **Note**: This task enables T015 to score actual video content without heavy CV models.
- [ ] T015a [P] [US1] Create Physics Simulation Schema. **Logic**: Create `src/filtering/schema.py` defining the mapping from prompt semantic tags to PyBullet object types (e.g., 'object_A' -> 'cube', 'action' -> 'push'). **Output**: `src/filtering/schema.py`. **Dependency**: None (Phase 3).
- [ ] T015 [US1] Implement physics scoring in `src/filtering/pybullet_filter.py`. **Logic**: Load generated video from `data/raw/`. Load reconstructed states from `data/raw/reconstructed_states.parquet` (T015b). Simulate the expected physics based on the prompt's semantic tags (using schema from T015a) to score the *video's* adherence to trajectory continuity and contact conservation using PyBullet in headless mode. **Constraint**: DO NOT use optical flow, pose estimation, or visual heuristics. If PyBullet simulation fails to load frames, assign a score of 0.0, log the error, and continue. **Output**: `data/curated/scores.parquet` with columns `video_id`, `continuity_score`, `contact_score`. **Dependency**: T015a, T015b.
- [ ] T016 [US1] Implement dynamic percentile-based filtering logic in `src/filtering/score_utils.py`. **Logic**: Read `data/curated/scores.parquet`. **Dynamic Threshold**: Read `discard_percentile` from `config.yaml` (default 40). Calculate the score threshold corresponding to this percentile of the current batch distribution (e.g., if discard_percentile=40, calculate the 40th percentile of scores; videos with scores >= this value pass). **Filter**: Discard videos where `combined_score < calculated_threshold`. **Constraint**: MUST use dynamic percentile calculation; NO hardcoded absolute score thresholds. **Conditional**: If resulting dataset size is < 30, set `needs_augmentation: true` in output metadata. **Crucial**: Always write `data/curated/curated_metadata.jsonl` with `N_curated` (final count), `calculated_threshold`, and `needs_augmentation` flag, regardless of whether augmentation is needed. Save remaining videos to `data/curated/`. **Dependency**: T015, T007b. **Output**: `data/curated/` videos and `data/curated/curated_metadata.jsonl`.
- [ ] T016c [US1] Execute Augmentation (Conditional). **Logic**: Read `needs_augmentation` from `data/curated/curated_metadata.jsonl` (output of T016). If `true`, call `src/augmentation/geometric_augmenter.py` to augment the dataset. If `false`, log "No augmentation needed" and exit successfully. **Output**: Updated `data/curated/` and `data/curated/curated_metadata.jsonl` (with final N_curated). **Dependency**: T016.
- [ ] T016d [US1] Re-score Augmented Samples. **Logic**: If T016c executed augmentation, re-run the physics filter (T015) on the *augmented* samples to ensure they meet the 'score >= calculated_threshold' acceptance criteria. If any augmented sample fails, exclude it from the curated set. **Output**: Updated `data/curated/scores.parquet` and `data/curated/curated_metadata.jsonl` (with final valid N_curated). **Dependency**: T016c, T015.
- [ ] T016b [US1] Verify and Log Discard Rate. **Logic**: Calculate the actual discard rate from T016d output. Log the result and verify it matches the target (based on the threshold distribution). **Output**: Log entry in `logs/discard_rate.log`. **Dependency**: T016d.
- [ ] T015c [US1] Generate Randomized Control Indices. **Logic**: Set `random.seed(config.seed)`. Read `N_curated` from `data/curated/curated_metadata.jsonl` (output of T016d). Generate a stratified random subset of indices from `data/raw/` (NOT augmented data) matching the *actual* curated set size (N_curated) using `random.sample`. Stratification criteria: prompt diversity and video length. Save to `data/control/indices.json`. **Dependency**: T016d. **Output**: `data/control/indices.json` (MUST EXIST).
- [ ] T018b [US1] Implement MuJoCo Reconstruction. **Logic**: Create `src/filters/mujoco_validator.py` to convert video frames (MP4) into MuJoCo state vectors (position, velocity, contact points) using **lightweight, deterministic methods**: `opencv-python` for frame differencing and simple color thresholding. **Constraint**: Must handle corrupted frames gracefully (log error, assign default state). **Output**: `data/validation/mujoco_reconstructed_states.parquet` with columns `video_id`, `frame_states`. **Dependency**: T013. **Note**: This task enables T018 to score actual video content independently.
- [ ] T018 [US1] Run MuJoCo Validation & Orthogonality Check (Sanity Gate). **Input**: `data/curated/` videos (subset). **Logic**: Load reconstructed states from `data/validation/mujoco_reconstructed_states.parquet` (T018b). Compute MuJoCo scores for each video. **Output**: `data/validation/sanity_check.json` AND `data/validation/mujoco_scores.parquet` (containing `video_id`, `mujoco_score`). **Gate**: Proceed to training only if the filter runs successfully and scores are generated. **Note**: Full orthogonality check moved to T038c (Phase 3) to avoid circular dependencies. **Dependency**: T018b.
- [ ] T038a [US1] Compute Correlation (Full Orthogonality Check). **Input**: `data/curated/scores.parquet` (PyBullet scores from T015) and `data/validation/mujoco_scores.parquet` (MuJoCo scores from T018). **Logic**: Compute Pearson correlation coefficient between PyBullet and MuJoCo scores. **Output**: `data/validation/correlation.json` with `correlation_coefficient`. **Dependency**: T015, T018.
- [ ] T038b [US1] Verify Orthogonality Gate. **Logic**: Read `data/validation/correlation.json`. If `correlation_coefficient >= 0.95`, raise `RuntimeError` and abort pipeline. If < 0.95, log success and proceed. **Output**: `logs/orthogonality_gate.log`. **Dependency**: T038a. **Gate**: HARD GATE before Phase 4.

### Tests for User Story 1 (Run AFTER Implementation)

- [ ] T011a [US1] Integration test: Verify generation of a representative set of samples. and discard rate is within 5% of `config.yaml` value (0.4). **Input**: 10 prompts from T012. **Output**: Verify `data/curated/` contains a set of videos.
- [ ] T011b [US1] Integration test: Verify physics filter assigns low score to corrupted frames. **Input**: Inject a corrupted frame into a video. **Output**: Verify score < 0.1 and video is excluded.
- [ ] T011c [US1] Integration test: Verify curated dataset contains only videos with score >= threshold. **Input**: Run filter on known good set. **Output**: Verify min score in `data/curated/` >= threshold.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of moderate capacity on the curated dataset using CPU-only optimization, ensuring feasibility within 4 hours.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Implementation for User Story 2

- [ ] T024a [P] [US2] Define UNet Architecture Config. **Logic**: Create `src/training/model_config.py` with parameters for a 50M parameter model (e.g., 64 base channels, 3 down blocks, 3 up blocks, 8 attention heads). **Output**: `src/training/model_config.py`. **Dependency**: None.
- [ ] T024b [P] [US2] Implement UNet-based diffusion model class in `src/training/unet_diffusion.py` (CPU-optimized). **Spec**: Target a compact diffusion model with a parameter count suitable for efficient deployment on CPU. **Logic**: Implement the model class using the config from T024a. **Dependency**: T024a.
- [ ] T024 [US2] Implement UNet-based diffusion model in `src/training/diffusion_trainer.py` (CPU-optimized). **Spec**: Target a compact diffusion model with a parameter count suitable for efficient deployment on CPU. **Logic**: Configure UNet architecture with **50M parameters (approx)** (e.g., 64 base channels, 3 down blocks, 3 up blocks, 8 attention heads) to ensure training completes within 4 hours on CPU. **Verification**: Create `src/training/verify_model_size.py` that loads the config, builds the model, asserts parameter count is within 50M (±10%), and exits 0/1. **Note**: Architecture details are fixed to ensure deterministic implementation and CPU feasibility. **Dependency**: T038b (Gate passed), T024a, T024b.
- [ ] T024c [US2] Verify Model Size. **Logic**: Run `src/training/verify_model_size.py` to build the model defined in T024 and assert parameter count is within 50M (±10%). **Output**: `logs/model_size_verification.log`. **Dependency**: T024.
- [ ] T025 [US2] Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning rate adjustment (retry up to 3 times), and **Wall-Clock Timeout** (max a limited duration of several hours). **Logic**: Train until convergence or time limit. **Instrument**: Log wall-clock training time to `data/eval/training_metrics.json` for SC-005 verification. **Dependency**: T024, T024c.
- [ ] T026 [US2] Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for GB RAM. **Constraint**: Must fail loudly if real data fetch fails (no synthetic fallback). **Dependency**: T024, T024c.
- [ ] T027 [US2] Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`. **Dependency**: T025.
- [ ] T028 [US2] Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`. **Dependency**: T025.
- [ ] T029 [US2] Instrument Training Metrics. **Logic**: Log wall-clock training time to `data/eval/training_metrics.json` for SC-005 verification. **Dependency**: T025.
- [ ] T017 [US2] Train Unfiltered Baseline Model. **Logic**: Use the same training script (T024/T025) to train a control model. Load `data/raw/` using the *pre-computed split indices* from `data/control/indices.json` (T015c). **Output**: `models/control_model/`. **Dependency**: T015c, T024 (implementation), T025 (implementation). **Note**: This task satisfies the "Unfiltered Baseline" requirement of FR-005.
- [ ] T048 [US2] Implement "Fail Loud" data loader in `src/training/diffusion_trainer.py`. **Logic**: Ensure the data loader raises an exception if `data/curated/` is empty or missing, preventing any fallback to synthetic/mock data. **Dependency**: T026.

### Tests for User Story 2 (Run AFTER Implementation)

- [ ] T022 [US2] Integration test for training on curated samples. **Input**: 60 videos from `data/curated/`. **Output**: Verify model converges (loss decreases) and saves a checkpoint within 4 hours. **Dependency**: T024, T025.
- [ ] T022b [US2] Integration test for control model training. **Input**: 60 videos from `data/raw/` (random subset). **Output**: Verify control model converges. **Dependency**: T017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R-Bench and PAI-Bench with statistical significance testing.

**Independent Test**: Run evaluation suite, generate JSON report with scores and p-values, and verify performance gap calculation.

### Implementation for User Story 3

- [ ] T033a-2 [P] [US3] Create Fallback Baseline Results. **Logic**: Generate a synthetic baseline result set (or load a local cached version if available) representing the PhysisForcing baseline performance. **Output**: `data/eval/physisforcing_baseline_fallback.json`. **Dependency**: None.
- [ ] T033a [US3] Load PhysisForcing Baseline Results. **Logic**: Load results from `data/eval/physisforcing_baseline.json` (output of T033a-1). **Constraint**: If T033a-1 failed (check `state/baseline_fetch.json`), load `data/eval/physisforcing_baseline_fallback.json` (T033a-2) instead. If both fail, raise `RuntimeError`. **Output**: `data/eval/physisforcing_baseline.json`. **Dependency**: T033a-1, T033a-2.
- [ ] T033b [US3] Verify PhysisForcing Baseline Artifact. **Logic**: Validate that the baseline artifact (from T033a) exists, is machine-readable (JSON), and contains the required keys. **Output**: Log entry in `logs/baseline_verification.log`. **Dependency**: T033a.
- [ ] T031 [P] [US3] Implement R-Bench scorer in `src/evaluation/r_bench.py`. **Dependency**: T024, T025.
- [ ] T032 [P] [US3] Implement PAI-Bench scorer in `src/evaluation/pai_bench.py`. **Dependency**: T024, T025.
- [ ] T034 [US3] Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`. **Logic**: Sample from the *augmented* curated dataset (if T016c augmented) or the raw curated set. **Constraint**: If the natural curated set is < 30, sample from the augmented set to ensure n >= 30. **Note**: If the eval set is augmented, the statistical test (T035a) MUST use non-parametric bootstrap methods or explicitly note the augmented nature in the report to satisfy FR-009. **Output**: `data/eval/eval_set.parquet` with metadata `eval_source: natural` or `eval_source: augmented`. **Dependency**: T016c.
- [ ] T035a [US3] Implement t-test and Mann-Whitney U statistical testing in `src/evaluation/stats.py` (FR-006 compliance). **Dependency**: T034, T031, T032.
- [ ] T036 [US3] Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`. **Dependency**: T034, T031, T032.
- [ ] T038c [US3] Final Orthogonality Gate. **Input**: `data/curated/scores.parquet` (PyBullet) and `data/validation/mujoco_scores.parquet` (MuJoCo). **Logic**: Compute correlation between PyBullet scores and MuJoCo scores on the final evaluation set. Verify correlation < 0.95. **Output**: `data/validation/final_orthogonality.json`. **Gate**: Proceed to reporting only if correlation < 0.95. **Dependency**: T015, T018.
- [ ] T039 [US3] Generate final JSON report in `data/eval/results.json` with all metrics and p-values. **Dependency**: T031, T032, T035a, T036.
- [ ] T049 [US3] Secondary Benchmark (PhysisForcing Comparison). **Logic**: Compare Filtered Model Score vs. PhysisForcing Paper Report. **Output**: `data/eval/secondary_benchmark.json`. **Note**: This is a descriptive comparison, not a causal test of the filtering hypothesis. SC-003 comparability is determined solely by the TOST p-value in T039. **Dependency**: T024, T025, T033a, T039.

### Tests for User Story 3 (Run AFTER Implementation)

- [ ] T030b [US3] Integration test for orthogonality check. **Input**: Filter scores, MuJoCo scores. **Output**: Verify correlation < 0.95 is correctly detected and reported. **Dependency**: T038c.
- [ ] T030 [US3] Integration test for full evaluation pipeline. **Input**: Trained model, baseline model, n=30 eval set. **Output**: Verify `data/eval/results.json` contains valid scores, p-values, and gap calculation. **Dependency**: T030b.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (curated dataset) and T038b (Gate)
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
- Different user stories can be worked on in parallel by different team members

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
- **CRITICAL**: All tasks MUST run on CPU-only (limited cores, constrained RAM). No CUDA, no large model training, no GPU-specific libraries.
- **CRITICAL**: All data must be real. No fabricated datasets. Use verified URLs for RobotBench prompts and Wan2.1 weights.
- **CRITICAL**: MuJoCo validation (T038c) MUST NOT use CV-extracted trajectories from T016; it must use real-world data or a strictly independent engine on actual physical outcomes to ensure scientific validity.
- **CRITICAL (Revision)**: The "Physics-Informed Training Proxy" is REMOVED. The baseline comparison is now against the *actual* PhysisForcing paper results (T033a) or the *Unfiltered Baseline* model (T017) trained on raw data with the same algorithm.
- **CRITICAL (Revision)**: Wan2.1 generation must explicitly handle CPU fallback or distilled CPU-compatible weights; if GPU is required for generation, the task MUST specify offload to Kaggle GPU with a fallback to abort if offload fails.
- **CRITICAL (Revision)**: Data loading tasks MUST implement a "fail loud" strategy: if the real dataset fetch fails, raise an exception immediately. Do NOT implement `try/except` blocks that fall back to synthetic/mock data generation, as this violates the fabrication guard.
- **CRITICAL (Revision)**: The discard rate is set to a dynamic percentile threshold (default 40th) in `config.yaml` (T007b) as a fallback, and T016 enforces this dynamic threshold.
- **CRITICAL (Revision)**: T023 (Augmentation) is moved to Phase 2 as a module definition; T016c (Phase 3) handles execution.
- **CRITICAL (Revision)**: T038a/T038b (Orthogonality Check) are moved to Phase 3 and serve as the hard gate before Phase 4.
- **CRITICAL (Revision)**: T015c (Control Indices) now depends on T016d (for metadata existence) and T016c (if augmentation occurred).
- **CRITICAL (Revision)**: T040 (Augmentation in Eval) is REMOVED. Augmentation is strictly a training-set preparation step (T016c). Evaluation uses the already-augmented curated set.
- **CRITICAL (Revision)**: T037 generates MuJoCo ground truth from *actual* curated videos, not prompts, to avoid circularity.
- **CRITICAL (Revision)**: T024 model size updated to 50M parameters to ensure scientific validity.
- **CRITICAL (Revision)**: T029 added to log training time for SC-005.
- **CRITICAL (Revision)**: T038c added as final orthogonality gate.
- **CRITICAL (Revision)**: T013 removed GPU offload fallback; strictly CPU with fail-loud error or Kaggle offload if available.
- **CRITICAL (Revision)**: T025 reduced epoch limit to 3 to guarantee 4-hour runtime (replaced by wall-clock timeout).
- **CRITICAL (Revision)**: T037 removed; T038c is the sole orthogonality gate.
- **CRITICAL (Revision)**: T016c is now conditional.
- **CRITICAL (Revision)**: T016d added to re-score augmented samples.
- **CRITICAL (Revision)**: T015b (Video-to-Simulation Reconstruction) added to enable scoring actual video content.
- **CRITICAL (Revision)**: T018b (MuJoCo Reconstruction) added to enable independent validation.
- **CRITICAL (Revision)**: T033a-1 added to fetch baseline results; hardcoded fallback removed.
- **CRITICAL (Revision)**: T013a added to check Kaggle availability before offload.
- **CRITICAL (Revision)**: T001 split into T001a and T001b for parallel execution.
- **CRITICAL (Revision)**: T024b removed; T024c is the sole verification task.
- **CRITICAL (Revision)**: T022 (US3) renamed to T049 to resolve ID conflict.
- **CRITICAL (Revision)**: T015b (second instance) renamed to T015c to resolve duplicate ID conflict.
- **CRITICAL (Revision)**: T015b now uses lightweight CV methods (frame differencing, color segmentation).
- **CRITICAL (Revision)**: T018b now uses lightweight CV methods.
- **CRITICAL (Revision)**: T033a-2 added as fallback baseline.
- **CRITICAL (Revision)**: T034 logic updated to sample from augmented set if natural count < 30.
- **CRITICAL (Revision)**: T025 now enforces wall-clock timeout.
- **CRITICAL (Revision)**: T017 renamed to "Train Unfiltered Baseline Model".
- **CRITICAL (Revision)**: T002 split into T002a and T002b.
- **CRITICAL (Revision)**: T005 split into T005a and T005b.
- **CRITICAL (Revision)**: T024 split into T024a, T024b, T024c.