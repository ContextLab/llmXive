---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending PhysisForcing (Physics Filter)

**Input**: Design documents from `/specs/001-llmxive-physs-filter/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create project root directory `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`. **Output**: Empty directory. **Dependency**: None.
- [ ] T001b Create subdirectories under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/` including `src/`, `tests/`, `data/` and specific module directories (`data/raw`, `data/curated`, `data/eval`, `data/validation`, `src/generation`, `src/filtering`, `src/training`, `src/evaluation`, `src/augmentation`, `src/utils`, `tests/unit`, `tests/integration`). **Output**: Directory structure. **Dependency**: T001a.
- [X] T002a Create `requirements.txt` with pinned versions for CPU-only `torch`, `pybullet`, `mujoco`, `diffusers`, `transformers`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `datasets`, `kaggle`, `depth-anything`, `openpose`. **Output**: `requirements.txt`. **Dependency**: None.
- [X] T002b Install dependencies from `requirements.txt` in a virtualenv and verify `pip install` on CPU-only runner. **Output**: Installed environment. **Dependency**: T002a. <!-- ATOMIZE: requested -->
- [ ] T003 Configure linting (ruff) and formatting (black) tools. **Output**: `pyproject.toml` or config files. **Dependency**: T002b.
- [X] T004 Verify `requirements.txt` installation on CPU-only runner. **Dependency**: T002b.
- [X] T007 Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU-only flags. **Output**: `src/training/config.py`. **Dependency**: T002b.
- [ ] T007b Create `config.yaml` with schema definition and a **configurable parameter** `discard_percentile` representing the percentage of videos to discard from the bottom of the distribution. **Output**: `config.yaml`. **Dependency**: None. **Note**: This task defines the experimental parameter for the percentile‑based filter. **Constraint**: The value represents the bottom percentage to discard (e.g., 40 means discard the bottom [deferred]). **Fallback**: The implementation MUST dynamically calculate the score threshold corresponding to this percentile from the batch distribution (e.g., if `discard_percentile=40`, threshold = 40th percentile score).
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected. **Output**: `src/utils/verify_env.py`. **Dependency**: T002b.
- [ ] T009 Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches. **Output**: `src/utils/seeding.py`. **Dependency**: T002b.
- [ ] T006b Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks. **Output**: `src/utils/profile_memory.py`. **Dependency**: T002b.
- [ ] T023 Define Data Augmentation Module in `src/augmentation/geometric_augmenter.py` (temporal jittering, geometric flipping) for FR-009. **Logic**: Define the augmentation functions (code only, no execution). **Specifics**: Apply temporal jittering (±10% speed) and geometric flipping (horizontal). **Dependency**: None (Phase 2). **Note**: This task produces the *code* for the module; execution happens in T016c.

**New Setup Tasks (addressing revision concerns)**
- [ ] T050 Create script `src/generation/download_wan_weights.py` to download Wan2.1 model weights from HuggingFace via `huggingface_hub`, verify SHA256 checksum, and store under `models/wan2.1/`.
- [X] T051 Add unit test `tests/unit/test_download_wan_weights.py` that asserts the download script creates the expected files and checksum matches.
- [X] T052 Add `huggingface_hub` to `requirements.txt` (ensure it is installed).
- [ ] T053 Create script `src/prompts/fetch_robotbench_prompts.py` to download a real set of robotic manipulation prompts from the RobotBench repository and write to `data/prompts.jsonl`.
- [X] T054 {{claim:c_8996df32}}

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a Create data directory structure: `data/raw`, `data/curated`, `data/eval`, `data/validation`. **Output**: Directories. **Dependency**: T001b.
- [ ] T005b Implement checksumming utilities in `src/utils/io_utils.py`. **Output**: `src/utils/io_utils.py`. **Dependency**: T005a.
- [ ] T006 Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics. **Output**: `src/utils/logging.py`. **Dependency**: T002b.
- [ ] T012 Load Verified Prompts. **Logic**: Execute the fetch script `src/prompts/fetch_robotbench_prompts.py` to obtain `data/prompts.jsonl`. **Dependency**: T053. **Output**: `data/prompts.jsonl`. **Note**: This satisfies FR-001 by using externally verified prompts.
- [ ] T033a-1 Construct PhysisForcing Baseline Results. **Logic**: Manually construct `data/eval/physisforcing_baseline.json` by extracting reported R-Bench and PAI-Bench scores from the PhysisForcing paper. **Constraint**: If paper values are unavailable, log a critical error and halt. **Output**: `data/eval/physisforcing_baseline.json`. **Dependency**: None.
- [ ] T055 Implement baseline JSON schema validator in `src/evaluation/baseline_validator.py` and expose `validate_baseline(json_path)` that checks required keys (`r_bench_score`, `pai_bench_score`, `tost_pvalue`).
- [ ] T056 Add unit test `tests/unit/test_baseline_validator.py` to verify that a well‑formed baseline JSON passes and a malformed one raises an error.
- [ ] T057 Extend `src/utils/verify_env.py` to assert that MuJoCo version >= 2.3 is installed; log the version and raise if not satisfied.
- [ ] T070 Create `contracts/` directory under the project root. **Output**: Empty `contracts/` folder. **Dependency**: T001b.
- [ ] T071 Generate contract artifacts (e.g., `contracts/data_contract.yaml`, `contracts/model_contract.yaml`) that formalize inputs/outputs for each pipeline stage. **Dependency**: T070.
- [ ] T072 Define data‑model schema in `data-model.yaml` describing `VideoSample`, `CuratedDataset`, `TrainedModel`, and `BenchmarkResult`. **Dependency**: None.
- [ ] T073 Validate data‑model against schema using a script `src/utils/validate_data_model.py`. **Dependency**: T072.

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU‑based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset (n=10), verify physics filtering discards the lower tail of the distribution

Reference: [Citation preserved]
Research Question: [Research Question preserved]
Method: [Method preserved] based on score distribution, and ensure remaining videos pass continuity checks.

### Implementation for User Story 1

- [ ] T013a Check Kaggle Offload Availability. **Logic**: Verify if Kaggle credentials and environment are configured (e.g., `KAGGLE_KEY` env var exists). **Output**: Boolean flag `kaggle_available`. **Dependency**: None. **Note**: This task ensures T013 can abort gracefully if offload is not configured.
- [ ] T013 Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use 'Wan-AI/Wan2.1-Turbo' from `huggingface.co/Wan-AI/Wan2.1-Turbo`. **Logic**: Attempt inference on CPU. If CPU fails (OOM or unsupported op), trigger Kaggle offload script to run generation on Kaggle GPU and download results. **Dependency**: T012 (prompts), T013a. **Output**: Raw MP4s in `data/raw/` and metadata in `data/raw/metadata.jsonl`.
- [ ] T015a Create Physics Simulation Schema. **Logic**: Create `src/filtering/schema.py` defining the mapping from prompt semantic tags to PyBullet object types (e.g., 'object_A' -> 'cube', 'action' -> 'push'). **Output**: `src/filtering/schema.py`. **Dependency**: None.
- [ ] T015b Create 3D State Reconstruction Pipeline. **Logic**: Create `src/filtering/reconstruction.py` to convert video frames (MP4) into 3D state vectors using DepthAnything for monocular depth estimation and OpenPose for 2D pose estimation, then triangulate 3D trajectories. Handles corrupted frames by logging and assigning a default state. **Output**: `data/raw/reconstructed_states.parquet`. **Dependency**: T013.
- [ ] T015 Implement physics scoring in `src/filtering/pybullet_filter.py`. **Logic**: Load generated video from `data/raw/`. Load reconstructed states from `data/raw/reconstructed_states.parquet`. Simulate expected physics based on the prompt's semantic tags (using schema from T015a) to score trajectory continuity and contact conservation. If PyBullet simulation fails, assign a score of 0.0, log the error, and continue. **Output**: `data/curated/scores.parquet` with columns `video_id`, `continuity_score`, `contact_score`. **Dependency**: T015a, T015b.
- [ ] T016 Implement dynamic percentile‑based filtering logic in `src/filtering/score_utils.py`. **Logic**: Read `data/curated/scores.parquet`. Read `discard_percentile` from `config.yaml` (default 40). Calculate the score threshold corresponding to this percentile of the current batch distribution. Discard videos where `combined_score < calculated_threshold`. Write `data/curated/curated_metadata.jsonl` containing `N_curated`, `calculated_threshold`, and `needs_augmentation` flag. Save retained videos to `data/curated/`. **Dependency**: T015, T007b. **Output**: Curated videos and metadata.
- [ ] T016c Execute Augmentation (Conditional). **Logic**: Read `needs_augmentation` from `data/curated/curated_metadata.jsonl`. If `true`, call `src/augmentation/geometric_augmenter.py` to augment the dataset; otherwise log "No augmentation needed". **Output**: Updated curated set and metadata. **Dependency**: T016.
- [ ] T016d Re‑score Augmented Samples. **Logic**: If augmentation occurred, re‑run the physics filter (T015) on the augmented samples and retain only those meeting the original `calculated_threshold`. **Output**: Updated `data/curated/scores.parquet` and metadata. **Dependency**: T016c, T015.
- [ ] T016b Verify and Log Discard Rate. **Logic**: Calculate the actual discard rate (proportion of original videos removed) and assert it is within ±5 % of the target rate derived from `discard_percentile` (e.g., target discard rate = 0.40). Log the result. **Dependency**: T016, T007b. **Output**: Log entry in `logs/discard_rate.log`.
- [ ] T015c Generate Randomized Control Indices. **Logic**: Set `random.seed(config.seed)`. Read `N_curated` from `data/curated/curated_metadata.jsonl`. Generate a stratified random subset of indices from `data/raw/` (NOT augmented data) matching `N_curated` using `random.sample`, ensuring diversity of prompts and video length. Save to `data/control/indices.json`. **Dependency**: T013, T007b. **Output**: `data/control/indices.json`.
- [ ] T018b Implement MuJoCo Reconstruction. **Logic**: Create `src/filters/mujoco_validator.py` to convert video frames into MuJoCo state vectors using DepthAnything and OpenPose (same as T015b), handling corrupted frames gracefully. **Output**: `data/validation/mujoco_reconstructed_states.parquet`. **Dependency**: T013.
- [ ] T018 Run MuJoCo Validation & Orthogonality Check (Sanity Gate). **Logic**: Load reconstructed states from T018b, compute MuJoCo scores per video, output `data/validation/mujoco_scores.parquet` and `data/validation/sanity_check.json`. **Dependency**: T018b.
- [ ] T038a Compute Correlation (Full Orthogonality Check). **Logic**: Compute Pearson correlation between PyBullet scores (`data/curated/scores.parquet`) and MuJoCo scores (`data/validation/mujoco_scores.parquet`). **Output**: `data/validation/correlation.json`. **Dependency**: T015, T018.
- [ ] T038b Verify Orthogonality Gate. **Logic**: If correlation ≥ 0.95, raise `RuntimeError`; otherwise log success. **Output**: `logs/orthogonality_gate.log`. **Dependency**: T038a.
- [ ] T058 Add unit tests for physics scoring functions in `tests/unit/test_physics_scoring.py` (verify that a clearly invalid video receives a low score and a valid video receives a high score). **Dependency**: T015.

### Tests for User Story 1 (Run AFTER Implementation)

- [ ] T011a Integration test: Verify generation of a representative set of samples and that the **discard *rate*** (proportion removed) is within ±5 % of the target derived from `discard_percentile` ([deferred]). **Input**: 10 prompts from T012. **Output**: Verify `data/curated/` contains expected videos.
- [ ] T011b Integration test: Verify physics filter assigns low score to corrupted frames. **Input**: Inject a corrupted frame into a video. **Output**: Verify score < 0.1 and video is excluded.
- [ ] T011c Integration test: Verify curated dataset contains only videos with score ≥ threshold. **Input**: Run filter on known good set. **Output**: Verify min score in `data/curated/` ≥ threshold.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of moderate capacity on the curated dataset using CPU‑only optimization, ensuring feasibility within 4 hours.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Implementation for User Story 2

- [ ] T024a Define UNet Architecture Config. **Logic**: Create `src/training/model_config.py` with parameters for a medium-scale model (e.g., 64 base channels, 3 down blocks, 3 up blocks, 8 attention heads). **Output**: `src/training/model_config.py`. **Dependency**: None.
- [ ] T024b Implement UNet‑based diffusion model class in `src/training/unet_diffusion.py` (CPU‑optimized). **Dependency**: T024a.
- [ ] T024 Implement UNet‑based diffusion model in `src/training/diffusion_trainer.py` (CPU‑optimized). **Logic**: Configure UNet architecture with a parameter count on the order of tens of millions. **Dependency**: T038b, T024a, T024b.
- [ ] T024c Verify Model Size. **Logic**: Run `src/training/verify_model_size.py` and log result to `logs/model_size_verification.log`. **Dependency**: T024.
- [ ] T024d Implement Memory Optimization Strategy. **Logic**: Integrate 8-bit quantization (bitsandbytes) and gradient checkpointing into the training loop to ensure the 50M model fits within 7GB RAM. Verify with `src/utils/profile_memory.py`. **Dependency**: T024, T024c.
- [ ] T025 Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning‑rate adjustment (retry up to 3 times, halve LR each retry), and wall‑clock timeout (max several hours). **Dependency**: T024, T024c, T024d.
- [ ] T059 Implement learning‑rate‑adjustment and retry logic inside the training loop (max 3 attempts, halve LR on each retry) in `src/training/diffusion_trainer.py`. **Dependency**: T025.
- [ ] T060 Add early‑stopping based on validation loss plateau (patience = 2 epochs) to the training loop. **Dependency**: T025.
- [ ] T026 Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for RAM. Must raise loudly if data fetch fails. **Dependency**: T024, T024c.
- [ ] T048 Implement "Fail Loud" data loader in `src/training/diffusion_trainer.py`. **Logic**: Ensure the loader raises an exception if `data/curated/` is empty or missing, preventing any synthetic fallback. **Dependency**: T026.
- [ ] T027 Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`. **Dependency**: T025.
- [ ] T028 Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`. **Dependency**: T025.
- [ ] T029 Instrument Training Metrics. **Logic**: Log wall‑clock training time to `data/eval/training_metrics.json` for SC‑005 verification. **Dependency**: T025.
- [ ] T017 Train Unfiltered Baseline Model. **Logic**: Use the same training script to train a control model on the raw dataset using indices from `data/control/indices.json`. **Output**: `models/control_model/`. **Dependency**: T015c, T024, T025.
- [ ] T022 Integration test for training on curated samples. **Input**: 60 videos from `data/curated/`. **Output**: Verify model converges (loss decreases) and saves a checkpoint within 4 hours. **Dependency**: T024, T025.
- [ ] T022b Integration test for control model training. **Input**: 60 videos from `data/raw/` (random subset). **Output**: Verify control model converges. **Dependency**: T017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R‑Bench and PAI‑Bench with statistical significance testing.

**Independent Test**: Run evaluation suite, generate JSON report with scores and p‑values, and verify performance gap calculation.

### Implementation for User Story 3

- [ ] T061 Implement Two‑One‑Sided Tests (TOST) equivalence testing in `src/evaluation/tost.py` with a 15 % equivalence margin; expose `run_tost(metric_a, metric_b, margin=0.15)` and integrate result into `src/evaluation/stats.py`. **Dependency**: None.
- [ ] T062 Add power‑analysis utility `src/evaluation/power_analysis.py` that computes required sample size for effect size d = 0.5, power ≥ 0.80 and warns if the evaluation set is smaller than the computed size. **Dependency**: None.
- [ ] T031 Implement R‑Bench scorer in `src/evaluation/r_bench.py`. **Dependency**: T024, T025.
- [ ] T032 Implement PAI‑Bench scorer in `src/evaluation/pai_bench.py`. **Dependency**: T024, T025.
- [ ] T034 Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`. **Logic**: Sample from the *augmented* curated dataset if `needs_augmentation` flag (from T016) is true; otherwise from the natural curated set. Ensure n ≥ 30. **Dependency**: T016, T062. **Output**: `data/eval/eval_set.parquet` with metadata `eval_source: natural` or `eval_source: augmented`.
- [ ] T035a Implement t‑test and Mann‑Whitney U statistical testing in `src/evaluation/stats.py` (FR‑006 compliance). **Dependency**: T034, T031, T032, T061.
- [ ] T036 Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`. **Dependency**: T034, T031, T032.
- [ ] T038c Final Orthogonality Gate. **Logic**: Compute correlation between PyBullet and MuJoCo scores on the final evaluation set. Verify correlation < 0.95. **Output**: `data/validation/final_orthogonality.json`. **Gate**: Proceed only if correlation < 0.95. **Dependency**: T015, T018.
- [ ] T039 Generate final JSON report in `data/eval/results.json` with all metrics, p‑values, and gap calculation. **Dependency**: T031, T032, T035a, T036, T061.
- [ ] T049 Secondary Benchmark (PhysisForcing Comparison). **Logic**: Compare filtered model score vs. PhysisForcing paper report. **Output**: `data/eval/secondary_benchmark.json`. **Dependency**: T024, T025, T033a, T039.

**Tests for User Story 3 (Run AFTER Implementation)**

- [ ] T030b Integration test for orthogonality check. **Input**: Filter scores, MuJoCo scores. **Output**: Verify correlation < 0.95 is correctly detected and reported. **Dependency**: T038c.
- [ ] T030 Integration test for full evaluation pipeline. **Input**: Trained model, baseline model, n=30 eval set. **Output**: Verify `data/eval/results.json` contains valid scores, p‑values, and gap calculation. **Dependency**: T030b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T042 Code cleanup and refactoring for memory efficiency across all modules to reduce peak RAM to < 5.5 GB (verified by `src/utils/profile_memory.py`)
- [ ] T043 Performance optimization for CV pipeline (if used) to reduce processing time per video to < 2 minutes
- [ ] T044 Additional unit tests for edge cases (corrupted frames, NaN loss, small dataset) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure all phases execute correctly on CPU‑only runner
- [ ] T046 Verify all artifacts have content hashes recorded in `state/projects/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml`
- [ ] T064 Add CI workflow `.github/workflows/ci.yml` that runs linting, unit/integration tests, and a lightweight end‑to‑end pipeline on the GitHub Actions free‑tier CPU runner.