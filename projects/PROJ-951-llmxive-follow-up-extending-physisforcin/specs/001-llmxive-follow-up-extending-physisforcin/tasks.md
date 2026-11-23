---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending PhysisForcing (Physics Filter)

**Input**: Design documents from `/specs/001-llmxive-physs-filter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

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
- [X] T002b Install dependencies from `requirements.txt` in a virtualenv and verify `pip install` on CPU-only runner. **Output**: `logs/requirements_install.log`. **Dependency**: T002a.
- [ ] T002c Generate `requirements_lock.txt` via `pip freeze` after installation for reproducibility. **Output**: `requirements_lock.txt`. **Dependency**: T002b.
- [ ] T003 Configure linting (ruff) and formatting (black) tools. **Output**: `pyproject.toml` or config files. **Dependency**: T002b.
- [ ] T004 Verify `requirements.txt` installation on CPU-only runner. **Output**: `logs/requirements_verification.log`. **Dependency**: T002b.
- [ ] T004a Run a small import sanity‑check script and write results to `logs/requirements_verification.log`. **Dependency**: T002b.
- [X] T007 Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU‑only flags. **Output**: `src/training/config.py`. **Dependency**: T002b.
- [ ] T007b Create `config.yaml` with schema definition and a **configurable parameter** `discard_percentile` representing the percentage of videos to discard from the bottom of the distribution (no fixed default; must be set by the researcher). **Output**: `config.yaml`. **Dependency**: None. **Note**: The value will be used to compute the score threshold dynamically.
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected. **Output**: `src/utils/verify_env.py`. **Dependency**: T002b.
- [ ] T008a Add explicit CPU‑only assertion to `verify_env.py` that raises if `torch.cuda.is_available()` is true. **Output**: Updated `src/utils/verify_env.py`. **Dependency**: T008.
- [ ] T080 Validate CPU‑only environment: run `src/utils/verify_env.py` and assert `torch.cuda.is_available() == False`. Write result to `logs/cpu_only_check.log`. **Dependency**: T002b.
- [ ] T009 Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches. **Output**: `src/utils/seeding.py`. **Dependency**: T002b.
- [ ] T006b Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks. **Output**: `src/utils/profile_memory.py`. **Dependency**: T002b.
- [ ] T023 Define Data Augmentation Module in `src/augmentation/geometric_augmenter.py` (temporal jittering, geometric flipping) for FR-009. **Logic**: Define the augmentation functions (code only, no execution). **Specifics**: Apply temporal jittering (±10% speed) and geometric flipping (horizontal). **Dependency**: None (Phase 2). **Note**: This task produces the *code* for the module; execution happens in T016c.
- **New Setup Tasks (addressing revision concerns)**
- [ ] T050 Create script `src/generation/download_wan_weights.py` to download Wan2.1 model weights from HuggingFace via `huggingface_hub`, verify SHA256 checksum, and store under `models/wan2.1/`.
- [X] T051 Add unit test `tests/unit/test_download_wan_weights.py` that asserts the download script creates the expected files and checksum matches. **Dependency**: T050.
- [X] T052 Add `huggingface_hub` to `requirements.txt` (ensure it is installed).
- [ ] T053 Create script `src/prompts/fetch_robotbench_prompts.py` to download a real set of robotic manipulation prompts from the RobotBench repository and write to `data/prompts.jsonl`.
- [ ] T065 Enforce CPU‑only compliance across all generation, training, and inference scripts. **Logic**: Run `src/utils/verify_env.py` at the start of every pipeline stage, assert no CUDA devices are available, and fail loudly if violated. **Dependency**: T008a, T080.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a Create data directory structure: `data/raw`, `data/curated`, `data/eval`, `data/validation`. **Output**: Directories. **Dependency**: T001b.
- [ ] T005b Implement checksumming utilities in `src/utils/io_utils.py`. **Output**: `src/utils/io_utils.py`. **Dependency**: T005a.
- [ ] T006 Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics. **Output**: `src/utils/logging.py`. **Dependency**: T002b.
- [ ] T012 Load Verified Prompts. **Logic**: Execute the fetch script `src/prompts/fetch_robotbench_prompts.py` to obtain `data/prompts.jsonl`. **Dependency**: T053. **Output**: `data/prompts.jsonl`. **Note**: This satisfies FR-001 by using externally verified prompts.
- [ ] T033a-1 Construct PhysisForcing Baseline Results. **Logic**: Manually construct `data/eval/physisforcing_baseline.json` by extracting reported R‑Bench and PAI‑Bench scores from the PhysisForcing paper. **Constraint**: If paper values are unavailable, log a critical error and halt. **Output**: `data/eval/physisforcing_baseline.json`. **Dependency**: None.
- [ ] T055 Implement baseline JSON schema validator in `src/evaluation/baseline_validator.py` and expose `validate_baseline(json_path)` that checks required keys (`r_bench_score`, `pai_bench_score`, `tost_pvalue`).
- [ ] T056 Add unit test `tests/unit/test_baseline_validator.py` to verify that a well‑formed baseline JSON passes and a malformed one raises an error.
- [ ] T057 Extend `src/utils/verify_env.py` to assert that MuJoCo version ≥ 2.3 is installed; log the version and raise if not satisfied.
- [ ] T099a Verify that all data‑download scripts raise loudly on failure and never fall back to synthetic placeholders. Run `tests/unit/test_download_scripts.py` and write `logs/download_scripts_verification.log`. **Dependency**: T050, T053.
- [ ] T101 Add contract test `tests/contract/test_config_schema.py` that validates `config.yaml` against its JSON‑Schema definition. **Dependency**: T007b.

## Phase 3: Shared Data Generation & Curation (Support for US‑1 & US‑3)

- [ ] T013 Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use `'Wan-AI/Wan2.1-Turbo'` from HuggingFace. **Logic**: Attempt inference on CPU; if CPU fails, abort with clear error (no automatic GPU offload) to satisfy FR‑007. **Dependency**: T012. **Pre‑condition**: Run `src/utils/verify_env.py` (T008) beforehand.
- [ ] T102 Ensure generation script logs a clear message when it aborts due to CPU limits, writing to `logs/generation_abort.log`. **Dependency**: T013.
- [ ] T015a Create Physics Simulation Schema. **Logic**: Create `src/filtering/schema.py` defining the mapping from prompt semantic tags to PyBullet object types (e.g., `'object_A' -> 'cube'`, `'action' -> 'push'`). **Output**: `src/filtering/schema.py`. **Dependency**: None.
- [ ] T015b Create 3D State Reconstruction Pipeline. **Logic**: Create `src/filtering/reconstruction.py` to convert video frames (MP4) into 3D state vectors using DepthAnything for monocular depth estimation and OpenPose for 2D pose estimation, then triangulate 3D trajectories. Handles corrupted frames by logging and assigning a default state. **Output**: `data/raw/reconstructed_states.parquet`. **Dependency**: T013.
- [ ] T015 Implement physics scoring in `src/filtering/pybullet_filter.py`. **Logic**: Load generated video from `data/raw/`. Load reconstructed states from `data/raw/reconstructed_states.parquet`. Simulate expected physics based on the prompt's semantic tags (using schema from T015a) to score trajectory continuity and contact conservation. If PyBullet simulation fails, assign a score of 0.0, log the error, and continue. **Output**: `data/curated/scores.parquet` with columns `video_id`, `continuity_score`, `contact_score`. **Dependency**: T015a, T015b.
- [ ] T016 Implement dynamic percentile‑based filtering logic in `src/filtering/score_utils.py`. **Logic**: Read `data/curated/scores.parquet`. Read `discard_percentile` from `config.yaml`. Calculate the score threshold corresponding to this percentile of the current batch distribution. Discard videos where `combined_score < calculated_threshold`. Write `data/curated/curated_metadata.jsonl` containing `N_curated`, `calculated_threshold`, and `needs_augmentation` flag. Save retained videos to `data/curated/`. **Dependency**: T015, T007b. **Output**: Curated videos and metadata.
- [ ] T016b Verify and log discard rate and runtime constraints. **Logic**: Calculate actual discard proportion, assert it is within ±5 % of the target (derived from `discard_percentile`). Also assert processing time ≤ 2 h and peak RAM ≤ 6 GB, writing results to `logs/discard_rate.log` and `logs/runtime_constraints.log`. **Dependency**: T016, T080.
- [ ] T016c Execute Augmentation (Conditional). **Logic**: Read `needs_augmentation` from `data/curated/curated_metadata.jsonl`. If `true`, call `src/augmentation/geometric_augmenter.py` to augment the dataset; otherwise log `"No augmentation needed"` to `logs/augmentation.log`. **Output**: Updated curated set and metadata. **Dependency**: T016.
- [ ] T016d Re‑score Augmented Samples. **Logic**: If augmentation occurred, re‑run the physics filter (T015) on the augmented samples and retain only those meeting the original `calculated_threshold`. **Output**: Updated `data/curated/scores.parquet` and metadata. **Dependency**: T016c, T015.
- [ ] T018b Implement MuJoCo Reconstruction. **Logic**: Create `src/filters/mujoco_validator.py` to convert video frames into MuJoCo state vectors using DepthAnything and OpenPose (same as T015b), handling corrupted frames gracefully. **Output**: `data/validation/mujoco_reconstructed_states.parquet`. **Dependency**: T013.
- [ ] T018 Run MuJoCo Validation & Orthogonality Check (Sanity Gate). **Logic**: Load reconstructed states from T018b, compute MuJoCo scores per video, output `data/validation/mujoco_scores.parquet` and `data/validation/sanity_check.json`. **Dependency**: T018b.
- [ ] T038a Compute Correlation (Full Orthogonality Check). **Logic**: Compute Pearson correlation between PyBullet scores (`data/curated/scores.parquet`) and MuJoCo scores (`data/validation/mujoco_scores.parquet`). **Output**: `data/validation/correlation.json`. **Dependency**: T015, T018.
- [ ] T038b Verify Orthogonality Gate. **Logic**: If correlation ≥ 0.95, raise `RuntimeError`; otherwise log success to `logs/orthogonality_gate.log`. **Dependency**: T038a.
- [ ] T058 Add unit tests for physics scoring functions in `tests/unit/test_physics_scoring.py` (verify that a clearly invalid video receives a low score and a valid video receives a high score). **Dependency**: T015.

## Phase 4: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Orchestrate generation and filtering using shared tasks.

- [ ] T011a Integration test: Verify generation of a representative set of samples and that the **discard rate** (proportion removed) is within ±5 % of the target derived from `discard_percentile`. **Test file**: `tests/integration/test_discard_rate.py`. **Output**: `logs/test_discard_rate.log`. **Dependency**: T013, T016b.
- [ ] T011b Integration test: Verify physics filter assigns low score to corrupted frames. **Test file**: `tests/integration/test_corrupted_frame_scoring.py`. **Output**: `logs/test_corrupted_frame.log`. **Dependency**: T015.
- [ ] T011c Integration test: Verify curated dataset contains only videos with score ≥ threshold. **Test file**: `tests/integration/test_curated_threshold.py`. **Output**: `logs/test_curated_threshold.log`. **Dependency**: T016.

## Phase 5: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of moderate capacity on the curated dataset using CPU‑only optimization, ensuring feasibility within 4 hours.

- [ ] T024a Define UNet Architecture Config. **Logic**: Create `src/training/model_config.py` with parameters for a medium‑scale model (e.g., 64 base channels, 3 down blocks, 3 up blocks, 8 attention heads). **Output**: `src/training/model_config.py`. **Dependency**: None.
- [ ] T024b Implement UNet‑based diffusion model class in `src/training/unet_diffusion.py` (CPU‑optimized). **Dependency**: T024a.
- [ ] T024 Implement diffusion trainer in `src/training/diffusion_trainer.py` (CPU‑optimized). **Logic**: Configure UNet architecture with a parameter count on the order of tens of millions. **Dependency**: T024a, T024b.
- [ ] T024c Verify Model Size. **Logic**: Run `src/training/verify_model_size.py` and log result to `logs/model_size_verification.log`. **Dependency**: T024.
- [ ] T024d Implement Memory Optimization Strategy. **Logic**: Integrate 8‑bit quantization (bitsandbytes) and gradient checkpointing into the training loop to ensure the 50M model fits within 7 GB RAM. Verify with `src/utils/profile_memory.py` and write peak usage to `logs/training_memory.log`. **Dependency**: T024, T024c.
- [ ] T025 Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning‑rate adjustment (retry up to 3 times, halve LR each retry), and wall‑clock timeout (max several hours). **Dependency**: T024, T024c, T024d.
- [ ] T059 Implement learning‑rate‑adjustment and retry logic inside the training loop (max 3 attempts, halve LR on each retry) in `src/training/diffusion_trainer.py`. **Dependency**: T025.
- [ ] T060 Add early‑stopping based on validation loss plateau (patience = 2 epochs) to the training loop. **Dependency**: T025.
- [ ] T026 Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for RAM. Must raise loudly if data fetch fails. **Dependency**: T024, T024c.
- [ ] T048 Implement "Fail Loud" data loader in `src/training/diffusion_trainer.py`. **Logic**: Ensure the loader raises an exception if `data/curated/` is empty or missing, preventing any synthetic fallback. **Dependency**: T026.
- [ ] T027 Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`. **Dependency**: T025.
- [ ] T028 Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`. **Output**: `logs/training_resource_monitor.log`. **Dependency**: T025.
- [ ] T029 Instrument Training Metrics. **Logic**: Log wall‑clock training time to `data/eval/training_metrics.json` for SC‑005 verification. **Dependency**: T025.
- [ ] T017 Train Unfiltered Baseline Model. **Logic**: Use the same training script to train a control model on the raw dataset using indices from `data/control/indices.json`. **Output**: `models/control_model/`. **Dependency**: T013, T025.
- [ ] T022 Integration test for training on curated samples. **Input**: 60 videos from `data/curated/`. **Output**: Verify model converges (loss decreases) and saves a checkpoint within 4 hours. **Dependency**: T024, T025.
- [ ] T022b Integration test for control model training. **Input**: 60 videos from `data/raw/` (random subset). **Output**: Verify control model converges. **Dependency**: T017.

## Phase 6: Shared Model Artifact Provision (Support for US‑3)

- [ ] T200 Prepare evaluation dataset from curated data. **Logic**: Read `data/curated/curated_metadata.jsonl`, sample `n ≥ 30` videos (apply augmentation flag if needed) and write `data/eval/eval_set.parquet`. **Output**: `data/eval/eval_set.parquet`. **Dependency**: T016.
- [ ] T201 Verify trained model checkpoint availability. **Logic**: Check that `models/filtered_model/` exists and contains `checkpoint.pt`; write status to `logs/model_checkpoint_check.log`. **Dependency**: T024.

## Phase 7: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R‑Bench and PAI‑Bench with statistical significance testing.

- [ ] T061 Implement Two‑One‑Sided Tests (TOST) equivalence testing in `src/evaluation/tost.py` with a 15 % equivalence margin; expose `run_tost(metric_a, metric_b, margin=0.15)` and integrate result into `src/evaluation/stats.py`. **Dependency**: None.
- [ ] T062 Add power‑analysis utility `src/evaluation/power_analysis.py` that computes required sample size for effect size d = 0.5, power ≥ 0.80 and warns if the evaluation set is smaller than the computed size. **Dependency**: None.
- [ ] T031 Implement R‑Bench scorer in `src/evaluation/r_bench.py`. **Dependency**: T024, T025.
- [ ] T032 Implement PAI‑Bench scorer in `src/evaluation/pai_bench.py`. **Dependency**: T024, T025.
- [ ] T034 Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`. **Logic**: Sample from the *augmented* curated dataset if `needs_augmentation` flag (from T016) is true; otherwise from the natural curated set. Ensure n ≥ 30. **Dependency**: T200, T062. **Output**: `data/eval/eval_set.parquet` (already created by T200).
- [ ] T035a Implement t‑test and Mann‑Whitney U statistical testing in `src/evaluation/stats.py` (FR‑006 compliance). **Dependency**: T034, T031, T032, T061.
- [ ] T036 Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`. **Dependency**: T034, T031, T032.
- [ ] T038c Final Orthogonality Gate. **Logic**: Compute correlation between PyBullet and MuJoCo scores on the final evaluation set. Verify correlation < 0.95. **Output**: `data/validation/final_orthogonality.json`. **Gate**: Proceed only if correlation < 0.95. **Dependency**: T015, T018.
- [ ] T039 Generate final JSON report in `data/eval/results.json` with all metrics, p‑values, and gap calculation. **Dependency**: T031, T032, T035a, T036, T061.
- [ ] T049 Secondary Benchmark (PhysisForcing Comparison). **Logic**: Compare filtered model score vs. PhysisForcing paper report. **Output**: `data/eval/secondary_benchmark.json`. **Dependency**: T201, T039, T033a-1.
- [ ] T030b Integration test for orthogonality check. **Test file**: `tests/integration/test_orthogonality_check.py`. **Output**: `logs/test_orthogonality.log`. **Dependency**: T038c.
- [ ] T030 Integration test for full evaluation pipeline. **Test file**: `tests/integration/test_full_evaluation_pipeline.py`. **Output**: `logs/test_full_evaluation.log`. **Dependency**: T030b.

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 Documentation updates in `docs/` including `quickstart.md` and `data-model.md`.
- [ ] T041a Create `quickstart.md` with step‑by‑step instructions to run the full pipeline on a small sample, referencing tasks T013, T016, T024, and T061. **Output**: `docs/quickstart.md`. **Dependency**: T001b, T013, T016, T024, T061.
- [ ] T042 Code cleanup and refactoring for memory efficiency across modules `src/filtering/`, `src/training/`, `src/evaluation/` to reduce peak RAM to < 5.5 GB. Record peak usage in `logs/memory_optimization.log`.
- [ ] T043 Performance optimization for CV pipeline (`src/filtering/reconstruction.py`) to reduce processing time per video to < 2 minutes. Record timings in `logs/cv_performance.log`.
- [ ] T044 Additional unit tests for edge cases (corrupted frames, NaN loss, small dataset) in `tests/unit/`.
- [ ] T045 Run `quickstart.md` validation via CI workflow `.github/workflows/ci.yml` and capture status in `logs/quickstart_ci_status.log`. **Dependency**: T041a, T066.
- [ ] T046 Verify all artifacts have content hashes recorded in `state/projects/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml`.
- [ ] T064 Add CI workflow `.github/workflows/ci.yml` that runs linting, unit/integration tests, and a lightweight end‑to‑end pipeline on the GitHub Actions free‑tier CPU runner.
- [ ] T100 Integration test: Run the entire pipeline on a tiny sample (e.g., 5 videos) to verify end‑to‑end correctness. **Test file**: `tests/integration/test_full_pipeline_small_sample.py`. **Output**: `logs/full_pipeline_small_sample.log`. **Dependency**: T200, T201, T061.
- [ ] T066 Verify quickstart guide execution. **Logic**: Execute the steps outlined in `docs/quickstart.md` on a minimal dataset and assert successful generation, filtering, training, and evaluation, logging results to `logs/quickstart_execution.log`. **Dependency**: T041a, T065.
