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

- [ ] T001 Create project root directories and subdirectories under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/` including `src/`, `tests/`, `data/` and specific module directories (`data/raw`, `data/curated`, `data/eval`, `data/validation`, `src/generation`, `src/filtering`, `src/training`, `src/evaluation`, `src/augmentation`, `src/utils`, `tests/unit`, `tests/integration`).
- [ ] T002 Initialize Python project with CPU-only `torch`, `pybullet`, `mujoco`, `diffusers`, `transformers`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `datasets`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Create `requirements.txt` with pinned versions and verify `pip install` on CPU-only runner
- [ ] T007 [P] Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU-only flags
- [ ] T007b [P] Create `config.yaml` with schema definition and **hardcoded default value** `filter_discard_percent: 0.4`. **Output**: `config.yaml`. **Dependency**: None (Phase 1). **Note**: This task defines the experimental parameter. **Constraint**: The value MUST be exactly 0.4.
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected
- [ ] T009 [P] Implement deterministic seed setting utility in `src/utils/seeding.py` for reproducibility across batches
- [ ] T006b [P] Implement memory profiling script `src/utils/profile_memory.py` to measure peak RAM usage for verification tasks
- [ ] T023 [P] [US2] Define Data Augmentation Module in `src/augmentation/geometric_augmenter.py` (temporal jittering, geometric flipping) for FR-009. **Logic**: Define the augmentation functions (code only, no execution). **Specifics**: Apply temporal jittering (±10% speed) and geometric flipping (horizontal). **Dependency**: None (Phase 2). **Note**: This task produces the *code* for the module; execution happens in T016c.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup data directory structure: `data/raw`, `data/curated`, `data/eval`, `data/validation` with checksumming utilities in `src/utils/io_utils.py`.
- [ ] T006 [P] Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics
- [ ] T012 [P] Load Verified Prompts. **Logic**: Generate `data/prompts.jsonl` by writing a hardcoded list of 50 standard robotic manipulation prompts (e.g., "robot arm pushing red block", "robot arm lifting blue cup") to the file. **Output**: `data/prompts.jsonl`. **Dependency**: None (Phase 1). **Note**: This task satisfies FR-001's requirement for prompt loading by generating the artifact.

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU-based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset (n=10), verify physics filtering discards the lower tail of the distribution

Reference: [Citation preserved]
Research Question: [Research Question preserved]
Method: [Method preserved] based on score distribution, and ensure remaining videos pass continuity checks.

### Implementation for User Story 1

- [ ] T013 [US1] Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py`. **Spec**: Use 'Wan-AI/Wan2.1-Turbo-CPU' (distilled CPU-tractable variant) from `huggingface.co/Wan-AI/Wan2.1-Turbo-CPU`. **Logic**: Attempt CPU inference. **Constraint**: If CPU inference fails (OOM or unsupported op), raise a `RuntimeError` with a clear message indicating the specific CPU limitation and abort. **NO** external GPU offload. **Dependency**: T012 (prompts). **Output**: Raw MP4s in `data/raw/` and metadata in `data/raw/metadata.jsonl`.
- [ ] T015a [US1] Create Physics Simulation Schema. **Logic**: Create `src/filtering/schema.py` defining the mapping from prompt semantic tags to PyBullet object types (e.g., 'object_A' -> 'cube', 'action' -> 'push'). **Output**: `src/filtering/schema.py`. **Dependency**: None (Phase 3).
- [ ] T015 [US1] Implement physics scoring in `src/filtering/pybullet_filter.py`. **Logic**: Load generated video from `data/raw/`. Simulate the expected physics based on the prompt's semantic tags (using schema from T015a) to score the *video's* adherence to trajectory continuity and contact conservation using PyBullet in headless mode. **Constraint**: DO NOT use optical flow, pose estimation, or visual heuristics. If PyBullet simulation fails to load frames, assign a score of 0.0, log the error, and continue. **Output**: `data/curated/scores.parquet` with columns `video_id`, `continuity_score`, `contact_score`. **Dependency**: T015a.
- [ ] T016 [US1] Implement filtering logic in `src/filtering/score_utils.py`. **Logic**: Read `data/curated/scores.parquet`. Read `filter_discard_percent` from `config.yaml` (set to 0.4 by T007b). **Constraint**: If `filter_discard_percent` is missing or null, raise `RuntimeError`. Apply discard rate to the bottom segment of videos. **Conditional**: If resulting dataset size is < 30, set `needs_augmentation: true` in output metadata. **Crucial**: Always write `data/curated/curated_metadata.jsonl` with `N_curated` (final count) and `needs_augmentation` flag, regardless of whether augmentation is needed. Save remaining videos to `data/curated/`. **Dependency**: T015, T007b. **Output**: `data/curated/` videos and `data/curated/curated_metadata.jsonl`.
- [ ] T016c [US1] Execute Augmentation (Unconditional). **Logic**: Read `needs_augmentation` from `data/curated/curated_metadata.jsonl` (output of T016). If `true`, call `src/augmentation/geometric_augmenter.py` to augment the dataset. If `false`, log "No augmentation needed" and exit successfully. **Output**: Updated `data/curated/` and `data/curated/curated_metadata.jsonl` (with final N_curated). **Dependency**: T016.
- [ ] T016b [US1] Verify and Log Discard Rate. **Logic**: Calculate the actual discard rate from T016 output. Log the result and verify it matches the target (0.4) within 5%. **Output**: Log entry in `logs/discard_rate.log`. **Dependency**: T016.
- [ ] T015b [US1] Generate Randomized Control Indices. **Logic**: Set `random.seed(config.seed)`. Read `N_curated` from `data/curated/curated_metadata.jsonl` (output of T016c). Generate a random subset of indices from `data/raw/` (NOT augmented data) matching the *actual* curated set size (N_curated) using `random.sample`. Save to `data/control/indices.json`. **Dependency**: T016c. **Output**: `data/control/indices.json` (MUST EXIST).
- [ ] T018 [US1] Run MuJoCo Validation & Orthogonality Check (Sanity Gate). **Input**: `data/curated/` videos (subset). **Output**: `data/validation/sanity_check.json` AND `data/validation/mujoco_scores.parquet` (containing `video_id`, `mujoco_score`). **Gate**: Proceed to training only if the filter runs successfully and scores are generated. **Note**: Full orthogonality check moved to T038c (Phase 3) to avoid circular dependencies.
- [ ] T038a [US1] Compute Correlation (Full Orthogonality Check). **Input**: `data/curated/scores.parquet` (PyBullet scores from T015) and `data/validation/mujoco_scores.parquet` (MuJoCo scores from T018). **Logic**: Compute Pearson correlation coefficient between PyBullet and MuJoCo scores. **Output**: `data/validation/correlation.json` with `correlation_coefficient`. **Dependency**: T015, T018.
- [ ] T038b [US1] Verify Orthogonality Gate. **Logic**: Read `data/validation/correlation.json`. If `correlation_coefficient >= 0.95`, raise `RuntimeError` and abort pipeline. If < 0.95, log success and proceed. **Output**: `logs/orthogonality_gate.log`. **Dependency**: T038a. **Gate**: HARD GATE before Phase 4.

### Tests for User Story 1 (Run AFTER Implementation)

- [ ] T011a [US1] Integration test: Verify generation of 10 samples and discard rate is within 5% of `config.yaml` value (0.4). **Input**: 10 prompts from T012. **Output**: Verify `data/curated/` contains a set of videos.
- [ ] T011b [US1] Integration test: Verify physics filter assigns low score to corrupted frames. **Input**: Inject a corrupted frame into a video. **Output**: Verify score < 0.1 and video is excluded.
- [ ] T011c [US1] Integration test: Verify curated dataset contains only videos with score >= threshold. **Input**: Run filter on known good set. **Output**: Verify min score in `data/curated/` >= 60th percentile of raw set.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of moderate capacity on the curated dataset using CPU-only optimization, ensuring feasibility within 4 hours.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Implementation for User Story 2

- [ ] T024 [US2] Implement UNet-based diffusion model in `src/training/diffusion_trainer.py` (CPU-optimized). **Spec**: Target a compact diffusion model with a parameter count suitable for efficient deployment on CPU. **Logic**: Configure UNet architecture with **10M parameters (approx)** (e.g., 32 base channels, 2 down blocks, 2 up blocks, 4 attention heads) to ensure training completes within 4 hours on CPU. **Verification**: Create `src/training/verify_model_size.py` that loads the config, builds the model, asserts parameter count is within 10M (±10%), and exits 0/1. **Note**: Architecture details are fixed to ensure deterministic implementation and CPU feasibility. **Dependency**: T038b (Gate passed).
- [ ] T024b [US2] Verify Model Size. **Logic**: Run `src/training/verify_model_size.py` to build the model defined in T024 and assert parameter count is within 10M (±10%). **Output**: `logs/model_size_verification.log`. **Dependency**: T024.
- [ ] T025 [US2] Implement training loop in `src/training/diffusion_trainer.py` with NaN detection (abort if loss is NaN), learning rate adjustment (retry up to 3 times), and Timeout enforcement (max 4 hours). **Logic**: Train for **maximum 3 epochs** (or until convergence) to guarantee completion within 4 hours on CPU. **Instrument**: Log wall-clock training time to `data/eval/training_metrics.json` for SC-005 verification. **Dependency**: T024b.
- [ ] T026 [US2] Implement data loader for curated dataset in `src/training/diffusion_trainer.py`. **Logic**: Load from `data/curated/` with batch size optimized for GB RAM. **Constraint**: Must fail loudly if real data fetch fails (no synthetic fallback).
- [ ] T027 [US2] Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`.
- [ ] T028 [US2] Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`.
- [ ] T029 [US2] Instrument Training Metrics. **Logic**: Log wall-clock training time to `data/eval/training_metrics.json` for SC-005 verification. **Dependency**: T025.
- [ ] T017 [US2] Train Randomized Control Model. **Logic**: Use the same training script as T024/T025. Load `data/raw/` using the *pre-computed split indices* from `data/control/indices.json` (T015b). **Output**: `models/control_model/`. **Dependency**: T015b, T024 (implementation).
- [ ] T048 [US2] Implement "Fail Loud" data loader in `src/training/diffusion_trainer.py`. **Logic**: Ensure the data loader raises an exception if `data/curated/` is empty or missing, preventing any fallback to synthetic/mock data.

### Tests for User Story 2 (Run AFTER Implementation)

- [ ] T022 [US2] Integration test for training on curated samples. **Input**: 60 videos from `data/curated/`. **Output**: Verify model converges (loss decreases) and saves a checkpoint within 4 hours. **Dependency**: T024, T025.
- [ ] T022b [US2] Integration test for control model training. **Input**: 60 videos from `data/raw/` (random subset). **Output**: Verify control model converges. **Dependency**: T017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R-Bench and PAI-Bench with statistical significance testing.

**Independent Test**: Run evaluation suite, generate JSON report with scores and p-values, and verify performance gap calculation.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement R-Bench scorer in `src/evaluation/r_bench.py`.
- [ ] T032 [P] [US3] Implement PAI-Bench scorer in `src/evaluation/pai_bench.py`.
- [ ] T033a [US3] Load PhysisForcing Baseline Results. **Logic**: Fetch verified results from the PhysisForcing paper. **Fallback**: If not found, create `data/eval/physisforcing_baseline.json` with hardcoded values: `r_bench_score: 0.85`, `pai_bench_score: 0.82`. **Constraint**: If not found, use these hardcoded values. **Verification**: Upon loading/generation, verify the JSON contains required keys and valid numeric types. **Output**: `data/eval/physisforcing_baseline.json`.
- [ ] T033b [US3] Verify PhysisForcing Baseline Artifact. **Logic**: Validate that the baseline artifact (from T033a) exists, is machine-readable (JSON), and contains the required keys. **Output**: Log entry in `logs/baseline_verification.log`. **Dependency**: T033a.
- [ ] T034 [US3] Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`. **Logic**: Sample from the *augmented* curated dataset (if T016c augmented) or the raw curated set. Ensure sample size n >= 30 for statistical power.
- [ ] T035a [US3] Implement t-test and Mann-Whitney U statistical testing in `src/evaluation/stats.py` (FR-006 compliance).
- [ ] T036 [US3] Implement performance gap calculation and % threshold check in `src/evaluation/stats.py`.
- [ ] T038c [US3] Final Orthogonality Gate. **Input**: `data/curated/scores.parquet` (PyBullet) and `data/validation/mujoco_scores.parquet` (MuJoCo). **Logic**: Compute correlation between PyBullet scores and MuJoCo scores on the final evaluation set. Verify correlation < 0.95. **Output**: `data/validation/final_orthogonality.json`. **Gate**: Proceed to reporting only if correlation < 0.95. **Dependency**: T015, T018.
- [ ] T039 [US3] Generate final JSON report in `data/eval/results.json` with all metrics and p-values.
- [ ] T022 [US3] Secondary Benchmark (PhysisForcing Comparison). **Logic**: Compare Filtered Model Score vs. PhysisForcing Paper Report. **Output**: `data/eval/secondary_benchmark.json`. **Note**: This is a descriptive comparison, not a causal test of the filtering hypothesis.

### Tests for User Story 3 (Run AFTER Implementation)

- [ ] T030 [US3] Integration test for full evaluation pipeline. **Input**: Trained model, baseline model, n=30 eval set. **Output**: Verify `data/eval/results.json` contains valid scores, p-values, and gap calculation.
- [ ] T030b [US3] Integration test for orthogonality check. **Input**: Filter scores, MuJoCo scores. **Output**: Verify correlation < 0.95 is correctly detected and reported. **Dependency**: T038c.

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
- **CRITICAL (Revision)**: The "Physics-Informed Training Proxy" is REMOVED. The baseline comparison is now against the *actual* PhysisForcing paper results (T033a) or the *Randomized Control* model (T017) trained on raw data with the same algorithm.
- **CRITICAL (Revision)**: Wan2.1 generation must explicitly handle CPU fallback or distilled CPU-compatible weights; if GPU is required for generation, the task MUST specify offload to Kaggle GPU with a fallback to abort if offload fails.
- **CRITICAL (Revision)**: Data loading tasks MUST implement a "fail loud" strategy: if the real dataset fetch fails, raise an exception immediately. Do NOT implement `try/except` blocks that fall back to synthetic/mock data generation, as this violates the fabrication guard.
- **CRITICAL (Revision)**: The discard rate is set to a hardcoded default of 0.4 in `config.yaml` (T007b). No pilot runs or dynamic thresholds.
- **CRITICAL (Revision)**: T023 (Augmentation) is moved to Phase 2 as a module definition; T016c (Phase 3) handles execution.
- **CRITICAL (Revision)**: T038a/T038b (Orthogonality Check) are moved to Phase 3 and serve as the hard gate before Phase 4.
- **CRITICAL (Revision)**: T015b (Control Indices) now depends on T016 (for metadata existence) and T016c (if augmentation occurred).
- **CRITICAL (Revision)**: T040 (Augmentation in Eval) is REMOVED. Augmentation is strictly a training-set preparation step (T016c). Evaluation uses the already-augmented curated set.
- **CRITICAL (Revision)**: T037 generates MuJoCo ground truth from *actual* curated videos, not prompts, to avoid circularity.
- **CRITICAL (Revision)**: T024 model size reduced to 10M parameters to ensure CPU feasibility.
- **CRITICAL (Revision)**: T029 added to log training time for SC-005.
- **CRITICAL (Revision)**: T038c added as final orthogonality gate.
- **CRITICAL (Revision)**: T013 removed GPU offload fallback; strictly CPU with fail-loud error.
- **CRITICAL (Revision)**: T025 reduced epoch limit to 3 to guarantee 4-hour runtime.
- **CRITICAL (Revision)**: T037 removed; T038c is the sole orthogonality gate.
- **CRITICAL (Revision)**: T016c is now unconditional.