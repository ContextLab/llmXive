# Tasks: llmXive follow-up: extending "DanceOPD: On-Policy Generative Field Distillation"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-danceopd-on/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

- [X] T001a [P] Create project directory structure per implementation plan in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/` including directories: `code/`, `code/utils/`, `code/data/`, `code/models/`, `code/metrics/`, `data/raw/`, `data/processed/`, `data/results/`, `models/`, `tests/unit/`, `tests/integration/`, `tests/contract/`.
- [X] T001b [P] Initialize empty Python script files in `code/` and subdirectories: `code/main.py`, `code/00_data_fetch.py`, `code/00_data_stream.py`, `code/00_teacher_inference.py`, `code/01_train_trees.py`, `code/02_evaluate_fidelity.py`, `code/03_versioning.py`, `code/utils/timer.py`, `code/utils/stats.py`, `code/data/generate_teacher.py`, `code/models/train_tree.py`.
 - **Verification**: Verify all 11 files exist and contain `#!/usr/bin/env python` or `# Implementation` string (ensuring >0 bytes).
- [X] T002 Initialize Python project with `requirements.txt` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/` including pinned dependencies: `torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `transformers`, `accelerate`, `pillow`, `scipy`, `torch-fidelity`, `pyyaml`, `pytest`. **Constraint**: Ensure `torch` is installed with `cpuonly` flag or configured to default to CPU.
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` to manage seeds, paths, and hyperparameters (including `TEACHER_WEIGHTS_PATH`, `N_SAMPLES`, `N_MIN`, `N_PILOT`, `MIN_SAMPLE_SIZE=1000`, `TIMEOUT_HOURS=6`).
- [X] T005 [P] Create `code/utils/metrics.py` with stub functions `calculate_clip_score(image_path_1: str, image_path_2: str) -> float` and `calculate_fid(img_list_ref, img_list_gen) -> float` that raise `NotImplementedError`. These stubs allow the pipeline to run without crashing.
- [X] T005b [P] Implement the actual CPU‑only CLIP Score (using `transformers`) and FID (using `torch-fidelity`) functions in `code/utils/metrics.py`, replacing the stubs from T005. **Signature**: `calculate_clip_score` returns `List[float]` (per-sample scores). `calculate_fid` returns `float` (dataset-level score). **Constraint**: Enforce `device='cpu'` and `torch.set_default_device('cpu')` at the start of both functions. **Input Logic**: Convert PIL Images to tensors using `transforms.ToTensor()`, normalize using ImageNet mean/std (standard normalization parameters), and move to CPU. **Aggregation Logic**: The calling task (T030a) MUST compute the mean of the list for dataset-level reporting.
 - **Dependency**: T005 (stubs must exist to be replaced).
 - **Verification**: Verify functions return `List[float]` and `float` respectively, do not raise `NotImplementedError`, and pass a sanity check against a small set of dummy images (assert no NaN/Inf). Verify that the aggregation (mean) is NOT performed inside this function but is documented as the caller's responsibility.
- [X] T006 Create `code/03_versioning.py` to calculate SHA256 hashes for artifacts and update `state/`.
- [X] T007 Setup data directories: `data/raw/`, `data/processed/`, `data/results/` in the project root.
- [X] T008 [P] Implement weight manifest verification logic in `code/utils/check_weights.py`. **Logic**: 1. Initialize manifest if missing. 2. Verify checksums against manifest. 3. Handle missing files by raising an error.
 - **Dependency**: Consolidated from T008a, T008b, T008c.
- [X] T012c [P] Initialize CLIP model for metrics in `code/utils/models.py`. **Model**: `ViT-B/32 (2304.08480, https://arxiv.org/abs/2304.08480)`. **Device**: Explicitly set `device='cpu'`. **Note**: This task MUST complete before T012b starts.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Teacher Routing Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of `(prompt_embedding, noise_level, routing_label, velocity_vector)` tuples by running the pre‑trained DanceOPD teacher model on sampled ImageNet‑1K and LAION‑400M prompts.

**Independent Test**: The system produces a CSV/Parquet file with ≥1,000 rows, valid expert identifiers, and consistent velocity vector dimensions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for data schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_data_schema.py`
- [X] T011 [P] [US1] Integration test for data generation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_data_generation.py`. **Logic**: Verify `teacher_ground_truth.parquet` exists, has ≥1000 rows, and valid routing labels matching the teacher's known architecture.

### Implementation for User Story 1

- [ ] T042 [US1] **Implement Robust Real Data Streaming Fetch**. Implement `code/00_data_fetch.py` to check for data availability in two tiers: 1. **Pre-fetched**: Check for `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet` and verify checksums. 2. **Stream**: If pre-fetched missing, attempt to stream from `huggan/imagenet-1k` and `laion/laion400m` (filtered). **Constraint**: **Only exit with code 1 if both tiers fail.** Log the successful tier used. **Real Data Only**: If streaming, use `datasets.load_dataset(..., streaming=True)`. **Fail Loud**: If the stream fails (network error, 404, empty stream), **raise an explicit exception and exit with code 1**. **DO NOT** implement any `try/except` block that falls back to `generate_synthetic_data()` or random noise. **Reproducibility**: Before writing any data to disk, compute the SHA256 hash of the **raw stream buffer** (the exact bytes received from the source) for each chunk and aggregate to a total hash. Store this **stream hash** in `state/artifact_hashes.yaml` under a key `source_stream_hash_<dataset_name>`. After hashing, write the data to `data/raw/` as Parquet files. **Target N=2500**. **Dynamic Adjustment**: If stream yields < 2500 but >= 1000, proceed with warning. If < 1000, exit with code 1.
 - **Source Logic**: This task handles the "pre-computed dataset" fallback mandated by Spec Assumption A1 (for raw data only).
 - **Validation**: If Tier 1 (Pre-fetched) is used, verify SHA256. If Tier 2 (Stream) is used, verify stream integrity.
 - **Deliverable**: Validation report in `data/results/data_fetch_validation.json` with `status: verified` or `status: failed` and `source_tier: <tier_id>`. `state/artifact_hashes.yaml` updated with stream hashes.
- [X] T012 [US1] **Verify Data Availability & Fallback**. **DEPRECATED**: Replaced by T042. Do not implement.
- [ ] T043 [US1] **Add Data Source Verification & Hashing**. Extend T042 to verify the integrity of the streamed data.
 - **Rationale**: To ensure reproducibility and prevent silent corruption of the real data stream.
 - **Logic**: After T042 completes, compute SHA256 hashes for the *written* files `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet`. Compare these file hashes against the **stream hashes** stored in `state/artifact_hashes.yaml` by T042. If the file hash does not match the stream hash (which indicates a mismatch in the source bytes vs. the written file, or a drift in the source if re-fetched), **fail loud** (exit 1) unless a re-fetch is explicitly triggered. If the stream hash is not present (e., pre-fetched data), compute and store the file hash in `data/results/source_hashes.json` for future verification. This task acts as a verification step ensuring the file on disk matches the canonical stream hash recorded during fetch.
 - **Deliverable**: `data/results/source_hashes.json` with valid hashes for the real data sources, and a verification log in `data/results/verification_log.json` confirming the stream-hash-to-file-hash match.
- [X] T012b [US1] **Stream & Process Data**. Implement `code/00_data_stream.py` to read from `data/raw/`, stream samples, and extract `prompt_embedding` using the CLIP model (initialized in T012c).
 - **Dependency**: Depends on T042 completion (data verified) AND T012c completion (CLIP model initialized).
 - **Sampling Strategy**: Use `seed=42`. **Target N=2500** (configurable via `config.N_TARGET`). **Dynamic Adjustment**: Stream until `N_TARGET` is reached or stream ends. If total samples < 1000, **exit with code 1**. If 1000 <= samples < 2500, log warning and proceed.
 - **Streaming Logic**: Use `datasets.load_dataset(..., streaming=True)` to process data in chunks without loading the full dataset into RAM. Use `itertools.islice` to limit to the target sample size.
 - **Feature Extraction**: For each sample, extract `noise_level` and **`prompt_embedding`** using the CLIP model from T012c.
 - **Output Schema**: Write `data/processed/combined_samples.parquet` with columns: `image_path` (str, absolute path to raw image), `noise_level` (float), `prompt_embedding` (list[float32]).
 - **Deliverable**: `data/processed/combined_samples.parquet` exists and contains valid image paths, noise levels, and prompt embeddings.
- [X] T013a [US1] **Generate Teacher Ground Truth**. Implement `code/00_teacher_inference.py` to run the pre-trained DanceOPD teacher model on the sampled data (from T012b) to generate ground truth routing labels and velocity vectors.
 - **Context**: This task executes the teacher model on a scaled-down subset (N=2500).
 - **Input Logic**: Load `data/processed/combined_samples.parquet`. For each row, load the **raw image** from `image_path`. **Validation**: Verify `image_path` is absolute and file exists before loading. Pass raw image + embeddings to the teacher model.
 - **Output Schema**: Write `data/processed/teacher_ground_truth.parquet` with columns: `prompt_embedding` (list[float32]), `noise_level` (float), `routing_label` (str, expert ID), `velocity_vector` (list[float32]).
 - **Constraint**: If CPU inference fails to produce ≥1,000 valid samples, **exit with code 1** (fail loud). Do NOT generate an empty file. This enforces the FR-001 minimum sample requirement.
 - **Filtering**: During inference, detect 'undefined routing paths'. **Strict Exclusion**: If `routing_label` is not in the known expert ID set, **exclude** the sample. **Log** the `image_path` and `prompt_embedding` of these samples to `data/results/undefined_routing_log.json`. **DO NOT** assign a default label unless `USE_FALLBACK_LABEL` is explicitly set to `True` in `config.py` (and even then, log it heavily). If exclusion reduces the dataset below a sufficient threshold for analysis, **fail loud** (exit with a non-zero status).
 - **Deliverable**: `data/processed/teacher_ground_truth.parquet` (must contain ≥1000 rows or task fails) and `data/results/undefined_routing_log.json`.
- [X] T013c [US1] **Handle Teacher Inference Resource Constraints**. Implement logic in `code/00_teacher_inference.py` to handle the case where the teacher model inference exceeds CPU limits (Assumption A1).
 - **Rationale**: Spec Assumption A1 states that if the teacher model runs on a separate GPU or if CPU limits are hit, a pre-computed teacher dataset may be used. This task ensures that if the CPU inference fails due to time/memory, the pipeline can gracefully stop or switch to a pre-computed teacher dataset if available, without skipping the raw data fetch (T042).
 - **Logic**: If T013a fails due to timeout or memory, check for `PRE_COMPUTED_TEACHER_DATA_DIR`. If present, load the pre-computed `teacher_ground_truth.parquet`. If not, **exit with code 1**. **Do NOT** fall back to synthetic data.
 - **Deliverable**: `data/processed/teacher_ground_truth.parquet` (either generated or loaded from pre-computed source).
- [X] T014 [US1] **Extract and Stream Final Dataset**. Implement logic in `code/00_data_extraction.py` to extract `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector` from the filtered dataset and stream them to `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_ground_truth_filtered.parquet` (produced by T013a/T013c).
 - **Pre-check**: Verify input exists. **If the input file has < 1000 rows, exit with code 1** (fail loud) to prevent silent relaxation of constraints.
 - **Extraction Logic**: Load `teacher_ground_truth_filtered.parquet`. Select columns `prompt_embedding`, `noise_level`, `routing_label`, `velocity_vector`. Stream to `teacher_routing_dataset.parquet` to avoid memory spikes.
 - **Verification**: Verify `data/processed/teacher_routing_dataset.parquet` exists, is a valid Parquet file, and contains the expected columns (`prompt_embedding`, `noise_level`, `routing_label`, `velocity_vector`) with ≥1000 rows.
 - **Deliverable**: `data/processed/teacher_routing_dataset.parquet`.
- [X] T015 [US1] Add validation in `code/00_data_extraction.py` to ensure each `routing_label` matches a known expert field ID from the DanceOPD configuration.
- [X] T016 [US1] Implement checksumming and versioning of the generated dataset using `code/03_versioning.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Static Decision Trees (Priority: P2)

**Goal**: Train Decision Tree classifiers with `max_depth` ranging from shallow to deep on the generated dataset to approximate routing labels and compute "Routing Consistency".

**Independent Test**: A tree with `max_depth=5` is saved and reports a reproducible validation accuracy on a held‑out test split.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Decision Tree training parameters in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_tree_training.py`. **Logic**: Verify `DecisionTreeClassifier` instantiation with specific depths and correct accuracy calculation. **Note**: This task explicitly references the spec's 'Independent Test' for US2.
- [X] T019 [P] [US2] Integration test for training loop and metadata schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_tree_training.py`. **Logic**: Verify `teacher_routing_dataset.parquet` (the final input for US2) exists and is valid, and that `teacher_ground_truth_filtered.parquet` exists. **Note**: This test validates the output of T020-T023.

### Implementation for User Story 2

- [X] T020 [US2] Implement data splitting logic (train/test) in `code/01_train_trees.py` consuming `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_routing_dataset.parquet` (produced by T014) and its validation (T016b).
 - **Pre-check**: Verify `teacher_routing_dataset.parquet` exists and is valid before splitting.
 - **Enforce CPU**: Ensure no GPU usage in data loading (default behavior).
 - **Verification**: Verify `data/processed/train_split.parquet` and `data/processed/test_split.parquet` exist, are valid Parquet files, and contain the expected columns with non-zero row counts.
 - **Deliverable**: `data/processed/train_split.parquet` and `data/processed/test_split.parquet`.
- [X] T021a [US2] **Train Single Decision Tree**. Implement a function in `code/01_train_trees.py` to train a single `DecisionTreeClassifier` (scikit‑learn, CPU) for a given `max_depth`.
 - **Logic**: Train a tree for a specific depth `d`.
 - **Enforce CPU**: Explicitly set `device='cpu'` in scikit-learn (default) and ensure no PyTorch GPU tensors are used.
 - **Overfitting Check**: Calculate `train_accuracy` and `test_accuracy`. If difference > 0.1, log warning to `data/results/overfitting_log.json`. **Constraint**: The final analysis MUST use ONLY `test_accuracy`.
 - **Deliverable**: A single model saved to `models/trained_trees/` and accuracy metrics.
- [X] T021b [US2] **Run Training Loop for Decision Trees**. Implement a loop in `code/01_train_trees.py` to call T021a for `max_depth` values **range(2, 21)** (step 1).
 - **Logic**: Train a tree for each depth `d` in the range 2 to 20 to capture the saturation point and adhere to the "low-complexity" constraint (Constitution Principle VI).
 - **Deliverable**: A set of models saved to `models/trained_trees/` and a unified results table showing `max_depth` vs. `routing_accuracy` saved to `data/results/tree_accuracy.csv`.
- [X] T021c [US2] **Train Random Forests (Constitution VI Compliance)**. Implement a loop in `code/01_train_trees.py` to train `RandomForestClassifier` models with varying `n_estimators` (e., 10, 50, 100, 200) on the same dataset.
 - **Rationale**: Constitution Principle VI mandates varying `max_depth` AND using tree count for Random Forests to fully address the "theoretical compressibility" hypothesis.
 - **Logic**: Train a Random Forest for each `n_estimators` value. Calculate `train_accuracy` and `test_accuracy`. Log overfitting warnings if applicable.
 - **Deliverable**: A set of models saved to `models/trained_random_forests/` and a results table showing `n_estimators` vs. `routing_accuracy` saved to `data/results/forest_accuracy.csv`.
- [ ] T021d [US2] **Validate Model Metadata and Results**. Validate model metadata against the schema from `specs/contracts/DecisionTreeMetadata.json` and update `state/` with model hashes.
 - **Logic**: Ensure `tree_accuracy.csv` and `forest_accuracy.csv` are complete and sorted.
 - **Deliverable**: `data/results/tree_accuracy.csv` and `data/results/forest_accuracy.csv` with columns `max_depth`/`n_estimators`, `train_accuracy`, `test_accuracy`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantify Fidelity Degradation and Statistical Significance (Priority: P3)

**Goal**: Execute CPU‑only inference using tree-predicted routing, measure FID/CLIP for **ALL** samples (matched and mismatched), and perform statistical tests (bootstrap, t-test) to determine significance of fidelity degradation.

**Independent Test**: The system calculates FID/CLIP for teacher vs. tree (depth=5) on the full dataset and outputs valid p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for statistical test functions (bootstrap, t‑test) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_statistics.py`
- [X] T027 [P] [US3] Integration test for full fidelity evaluation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_fidelity_evaluation.py`. **Logic**: Verify FID/CLIP calculation and statistical test execution.

### Implementation for User Story 3

- [X] T029b [US3] **Load Expert Field Logic**. Implement `code/models/expert_loader.py` to load the individual expert field weights and logic from the teacher model package.
 - **Dependency**: None (Foundational).
 - **Logic**: Extract and cache the specific expert field modules required for re-inference.
 - **Deliverable**: Loaded expert field objects available to T029a.
- [X] T029c [US3] **Implement CPU-only Euler Integrator**. Implement `code/models/euler.py` to accept `velocity_vector`, `noise_level`, and `expert_type`, use a fixed step size and step count, and invoke the specific expert field logic to generate the image.
 - **Dependency**: Depends on T029b (Expert Fields Loaded).
 - **Logic**: Implement the Euler integration loop with noise injection: `x_{t+1} = x_t + step_size * v_t + sqrt(step_size) * noise`. **Parameters**: `step_size=0.1`, `steps=10`.
 - **Deliverable**: `code/models/euler.py` with function `integrate(velocity_vector, noise_level, expert_type) -> image`.
- [X] T029a [US3] **Generate Velocity Vectors from Tree Routing**. Implement `code/models/expert_reinference.py` to generate velocity vectors based on tree predictions.
 - **Dependency**: Depends on T029b (Expert Fields Loaded), T014 (Final Dataset), and T021b/T021c/T021d (Trained Trees/Forests).
 - **Input**: `routing_label` (predicted by tree), `prompt_embedding`, `noise_level`. **Note**: Do NOT use `image_path` for vector generation; the vector is a function of the routing decision and input state.
 - **Logic**: Load the specific expert field logic/weights (from T029b) corresponding to the `routing_label`. **Validation**: If `routing_label` is not in the loaded expert fields, raise an exception. **Re-run the expert field** using the tree-predicted routing label and input state (`prompt_embedding`, `noise_level`) to generate a **NEW velocity_vector**. The expert field function signature is explicitly: `expert_field(routing_label, prompt_embedding, noise_level) -> velocity_vector`.
 - **Verification**: Verify that the generated `velocity_vector` differs from the teacher's pre-computed vector for at least some samples (indicating routing change impact).
 - **Deliverable**: `velocity_vector` for each sample, saved to `data/processed/tree_predicted_vectors.parquet`.
- [X] T028a [US3] **Generate Teacher and Tree Images (Pilot)**. Implement `code/02_evaluate_fidelity.py` to generate images for BOTH the Teacher baseline and the Tree-predicted routing for a **Pilot** sample size (N=50). <!-- FAILED: unspecified -->
 - **Dependency**: Depends on T020 (Data Split), T021b/T021c/T021d (Trained Trees), T029b (Expert Fields Loaded), T029a (Velocity Generation), T029c (Euler Integrator).
 - **Logic**: Iterate through the first 50 samples of the test set. For each sample:
 1. **Teacher Baseline**: **Load** `routing_label` and `velocity_vector` from `data/processed/teacher_ground_truth_filtered.parquet` (pre-computed). Generate image using Euler integrator (T029c).
 2. **Tree Prediction**: Run Tree model to get `predicted_routing_label`. Use T029a to get `velocity_vector` based on prediction. Generate image using Euler integrator (T029c).
 3. **Crucial**: Use the **exact same random seed (config.SEED)** and sample indices for both generations to ensure 1:1 alignment.
 4. **No Filtering**: Process **EVERY** row in the input subset. Do NOT filter for matched routing labels.
 - **Deliverable**: `data/results/teacher_baseline_images_pilot/` and `data/results/tree_generated_images_pilot/` with matching filenames.
- [ ] T030a [US3] **Compute FID and CLIP Scores (Pilot)**. Compute metrics for pilot images.
 - **Input**: Results from T028a (Pilot image sets).
 - **Dependency**: Depends on T005b (Metrics implementation).
 - **Logic**: Process **ALL samples** (including mismatched). Aggregate per-sample CLIP scores (mean) and calculate dataset-level FID.
 - **Deliverable**: Metrics saved in `data/results/fidelity_metrics_pilot.csv`.
- [ ] T030b [US3] **Run Pilot Variance Calculation**. Execute T030a on the pilot images to estimate variance for power calculation.
 - **Dependency**: Depends on T028a (Pilot Images).
 - **Logic**: Calculate variance of the CLIP score differences using `data/results/teacher_baseline_images_pilot/` and `data/results/tree_generated_images_pilot/`.
 - **Deliverable**: Pilot variance estimate saved to `data/results/pilot_variance.json`.
- [ ] T030c [US3] **Calculate Power and Configure Sample Size**. Calculate required sample size based on pilot variance.
 - **Logic**: Calculate N based on pilot variance using `statsmodels.stats.power.TTestIndPower` with `target_power=0.8` and `effect_size=0.5` (medium). **Handle Missing Pilot**: If `data/results/pilot_variance.json` is missing, run a default pilot (N=50) or fail with error.
 - **Constraint**: **Check `timer.check_timeout()`** (see T033a). **Action**: If the calculated N exceeds the time limit, **reduce N linearly to the maximum feasible count** within the 6-hour limit and set `status: reduced` in `data/results/sample_size_config.json`. **Do NOT** proceed with an N that is known to be impossible to complete. If N is underpowered but feasible, set `status: underpowered` and proceed with a warning. **Ensure N does not exceed the available test set size.**
 - **Deliverable**: Final sample size configuration for full evaluation saved to `data/results/sample_size_config.json`.
- [X] T028b [US3] **Generate Teacher and Tree Images (Full)**. Implement `code/02_evaluate_fidelity.py` to generate images for BOTH the Teacher baseline and the Tree-predicted routing for the **Full** sample size (N calculated in T030c). <!-- ATOMIZE: requested -->
 - **Dependency**: Depends on T030c (Sample Size Config), T020 (Data Split), T021b/T021c/T021d (Trained Trees), T029b (Expert Fields Loaded), T029a (Velocity Generation), T029c (Euler Integrator).
 - **Logic**: Iterate through the test set (up to `sample_size` from T030c). For each sample:
 1. **Teacher Baseline**: **Load** `routing_label` and `velocity_vector` from `data/processed/teacher_ground_truth_filtered.parquet` (pre-computed). Generate image using Euler integrator (T029c).
 2. **Tree Prediction**: Run Tree model to get `predicted_routing_label`. Use T029a to get `velocity_vector` based on prediction. Generate image using Euler integrator (T029c).
 3. **Crucial**: Use the **exact same random seed (config.SEED)** and sample indices for both generations to ensure 1:1 alignment.
 4. **No Filtering**: Process **EVERY** row in the input subset. Do NOT filter for matched routing labels.
 - **Stop-Early**: If timer expires (checked via T033a), save partial results with `status: partial` flag.
 - **Verification**: Verify that generated images match filenames and that partial results are saved if timer expires.
 - **Deliverable**: `data/results/teacher_baseline_images_full/` and `data/results/tree_generated_images_full/` with matching filenames.
- [ ] T030d [US3] **Compute FID and CLIP Scores (Full)**. Compute metrics for full images.
 - **Input**: Results from T028b (Full image sets).
 - **Dependency**: Depends on T005b (Metrics implementation), T028b (Full Images).
 - **Logic**: Process **ALL samples** (including mismatched). Aggregate per-sample CLIP scores (mean) and calculate dataset-level FID.
 - **Deliverable**: Metrics saved in `data/results/fidelity_metrics_full.csv`.
- [X] T033a [US3] **Implement Early-Stop Timer**. Implement `code/utils/timer.py` to use a cross-platform timeout mechanism (e., `threading` with fallback) for a configurable timeout duration and save partial results as JSON with a `status: partial` flag if exceeded.
 - **Logic**: Set a timer at the start of the evaluation. If time expires, save partial results and exit gracefully.
 - **Verification**: Verify `check_timeout()` returns boolean and `save_partial_results()` writes valid JSON.
 - **Deliverable**: `code/utils/timer.py` with `check_timeout()` function.
- [X] T033b [US3] **Enforce Hard Stop-Eearly**. Implement logic in `code/02_evaluate_fidelity.py` to wrap the training/evaluation loops with the timer from T033a. **Logic**: Check `timer.check_timeout()` at the start of each sample iteration. If timeout, break loop, save partial results, and set `status: partial` in all output JSONs.
 - **Dependency**: Depends on T033a.
 - **Deliverable**: Hard stop-early enforcement in the evaluation pipeline.
- [ ] T030e [US3] **Perform Statistical Tests**. Perform statistical tests on the FID distributions and CLIP scores to determine the significance of performance degradation using bootstrap testing and paired t-tests.
 - **Input**: Results from T030d (Full Metrics), T030c (Sample Size Config), T030b (Pilot Variance). **Constraint**: Input data MUST include **ALL samples** (matched and mismatched). Verify count of mismatched samples before running tests.
 - **Logic**: Handle partial data gracefully (use available N).
 - **Deliverable**: Statistical test outputs saved in `data/results/statistical_tests.json` with schema: `{ "p_value_fid": float, "p_value_clip": float, "conclusion": str, "n_samples": int, "status": "complete|partial" }`.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/quickstart.md` reflecting the streaming data strategy and fail-loud behavior.
 - **Logic**: Update `docs/quickstart.md` to explain streaming logic and `exit(1)` on failure conditions.
 - **Deliverable**: Updated `docs/quickstart.md`.
- [X] T038 Code cleanup and refactoring to remove duplicate imports and unused variables.
 - **Logic**: Run `ruff check` and `black` to clean code.
 - **Deliverable**: Clean codebase with no linting errors.
- [X] T039 Performance optimization for the Euler integrator (vectorization where possible).
 - **Logic**: Vectorize image generation loops where applicable.
 - **Deliverable**: Optimized `code/models/euler.py`.
- [X] T040 [P] Additional unit tests for streaming logic in `tests/unit/test_streaming.py`.
 - **Logic**: Test `datasets.load_dataset(streaming=True)` and chunking logic. **Specific Cases**:
 1. Verify that `islice` correctly limits the number of rows.
 2. Verify that the stream handles end-of-file correctly without crashing.
 3. Verify that chunking does not load the entire dataset into memory (mock memory check).
 - **Deliverable**: `tests/unit/test_streaming.py` with passing tests for streaming, chunking, and end-of-stream behavior.
- [X] T041 Run `quickstart.md` validation to ensure the updated pipeline executes end-to-end.
 - **Logic**: Execute `quickstart.md` steps in a clean environment.
 - **Deliverable**: Validation report in `data/results/e2e_validation.json`.

**Checkpoint**: Project complete and validated

---

## Phase N+1: Revision & Review Resolution (Addressing Analysis Findings)

**Purpose**: Address specific concerns raised by `/speckit.analyze` regarding data integrity, reproducibility, and edge case handling.

- [X] T042 [US1] **Implement Robust Real Data Streaming Fetch**. **Replaced by T042 in Phase 3**. Do not implement.
- [X] T043 [US1] **Add Data Source Verification & Hashing**. **Replaced by T043 in Phase 3**. Do not implement.
- [X] T044 [US3] **Explicitly Handle Undefined Routing Paths**. **Replaced by logic in T013a**. Do not implement.
- [X] T045 [US3] **Validate Statistical Power Calculation**. **Replaced by logic in T030c**. Do not implement.
- [X] T046 [US2] **Prevent Overfitting in Decision Tree Training**. **Replaced by logic in T021a/T021b**. Do not implement.

**Checkpoint**: All analysis concerns resolved, pipeline robust against fabrication and statistical underpowering.