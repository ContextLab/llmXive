# Tasks: llmXive follow-up: extending "DanceOPD: On-Policy Generative Field Distillation"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-danceopd-on/`
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

- [X] T001a Create project directory structure per implementation plan in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/` including directories: `code/`, `code/utils/`, `code/data/`, `code/models/`, `code/metrics/`, `data/raw/`, `data/processed/`, `data/results/`, `models/`, `tests/unit/`, `tests/integration/`, `tests/contract/`.
- [ ] T001b Initialize empty Python script files in `code/`: `main.py`, `00_data_fetch.py`, `00_data_stream.py`, `00_teacher_inference.py`, `01_train_trees.py`, `02_evaluate_fidelity.py`, `03_versioning.py`, `utils/timer.py`, `utils/stats.py`, `data/generate_teacher.py`, `models/train_tree.py`.
 - **Verification**: Verify all 9 files exist and contain `#!/usr/bin/env python` or `# Implementation` string (ensuring >0 bytes).
- [X] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/` including pinned dependencies: `torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `transformers`, `accelerate`, `pillow`, `scipy`, `torch-fidelity`, `pyyaml`, `pytest`.
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` to manage seeds, paths, and hyperparameters (including `TEACHER_WEIGHTS_PATH`, `N_SAMPLES`, `N_MIN`, `N_PILOT`, `MIN_SAMPLE_SIZE=1000`).
- [X] T005 [P] Create `code/utils/metrics.py` with stub functions `calculate_clip_score(image_path_1: str, image_path_2: str) -> float` and `calculate_fid(img_list_ref, img_list_gen) -> float` that raise `NotImplementedError`. These stubs allow the pipeline to run without crashing.
- [X] T005b [P] Implement the actual CPU‑only CLIP Score (using `transformers`) and FID (using `torch-fidelity`) functions in `code/utils/metrics.py`, replacing the stubs from T005. **Signature**: `calculate_clip_score` returns `List[float]` (per-sample scores). `calculate_fid` returns `float` (dataset-level score).
 - **Dependency**: T005 (stubs must exist to be replaced).
 - **Verification**: Verify functions return `List[float]` and `float` respectively, do not raise `NotImplementedError`, and pass a sanity check against 5 dummy images (assert no NaN/Inf).
- [X] T006 Create `code/03_versioning.py` to calculate SHA256 hashes for artifacts and update `state/`.
- [X] T007 Setup data directories: `data/raw/`, `data/processed/`, `data/results/` in the project root.
- [X] T008a [P] Implement logic to create a weights manifest file (`code/utils/check_weights.py`).
- [X] T008b [P] Implement logic to verify checksums against the manifest (`code/utils/check_weights.py`).
- [X] T008c [P] Implement logic to initialize the manifest with existing weight files if present (`code/utils/check_weights.py`).
- [X] T012c [P] Initialize CLIP encoder in `code/utils/models.py`. **Note**: This task MUST complete before T012b starts.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Teacher Routing Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of `(prompt_embedding, noise_level, routing_label, velocity_vector)` tuples by running the pre‑trained DanceOPD teacher model on sampled ImageNet‑1K and LAION‑400M prompts.

**Independent Test**: The system produces a CSV/Parquet file with ≥1,000 rows, valid expert identifiers, and consistent velocity vector dimensions. [UNRESOLVED-CLAIM: c_5482bd26 — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for data schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_data_schema.py`
- [X] T011 [P] [US1] Integration test for data generation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_data_generation.py`. **Logic**: Verify `teacher_ground_truth.parquet` exists, has ≥1000 rows, and valid routing labels matching the teacher's known architecture.

### Implementation for User Story 1

- [X] T012 [US1] **Verify Pre-fetched Raw Datasets**. Implement `code/00_data_fetch.py` to verify the existence and checksums of ImageNet-1K and LAION-400M samples in `data/raw/`.
 - **Source Logic**: This task does NOT download data. It assumes data was pre-fetched in a separate CI job or manually.
 - **Validation**: Check for `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet`. Compute SHA256 and compare against `data/raw/checksums.json`.
 - **Constraint**: If any file is missing or checksum mismatch, **exit with code 1** (fail loud). Do NOT attempt to download or stream during this 6-hour window. This enforces Constitution Principle III (Data Hygiene).
 - **Deliverable**: Validation report in `data/results/data_fetch_validation.json` with `status: verified` or `status: failed`.
- [X] T012b [US1] **Stream & Process Data**. Implement `code/00_data_stream.py` to read from `data/raw/` and stream samples into memory for processing. <!-- FAILED: unspecified -->
 - **Dependency**: Depends on T012 completion (data verified) AND T012c completion (encoder initialized). **T012c (Phase 2) must complete before this task starts.**
 - **Sampling Strategy**: Use `seed=42`. **Target 1200 raw samples** from `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet`.
 - **Feature Extraction**: For each sample, extract `prompt_embedding` (using the CLIP encoder from T012c) and `noise_level`. **Do NOT run teacher model here**.
 - **Combination**: Combine these into a unified list `data/raw/combined_samples.parquet` containing the full tuple structure (excluding routing/velocity).
 - **Deliverable**: `combined_samples.parquet` exists and contains valid image paths and extracted tuples.
- [ ] T013a [US1] **Generate Teacher Ground Truth**. Implement `code/00_teacher_inference.py` to run the pre-trained DanceOPD teacher model on the sampled data (from T012b) to generate ground truth routing labels and velocity vectors.
 - **Context**: This task executes the teacher model on a scaled-down subset (N=1200).
 - **Logic**: Load `combined_samples.parquet`. For each sample, run the teacher model to get `routing_label` and `velocity_vector`.
 - **Constraint**: If CPU inference fails to produce ≥1,000 valid samples, **exit with code 1** (fail loud). Do NOT generate an empty file. This enforces the FR-001 minimum sample requirement.
 - **Filtering**: During inference, detect 'undefined routing paths'. If `config.py` `USE_FALLBACK_LABEL=True`, assign a default label (e.g., `expert_fallback`). Otherwise, exclude the sample. Log the count to `data/results/exclusion_log.json`.
 - **Deliverable**: `data/processed/teacher_ground_truth.parquet` (must contain ≥1000 rows or task fails).
- [ ] T013b [US1] **Filter and Validate Dataset**. Implement logic in `code/00_teacher_inference.py` to perform final validation and exclusion of undefined routing paths on the extracted dataset.
 - **Context**: This task filters the dataset generated by T013a.
 - **Dependency**: Depends on T013a.
 - **Logic**: Load `data/processed/teacher_ground_truth.parquet`. If the file is empty, log a warning and pass an empty file to the next step. Filter out any samples with `routing_label` not in the known expert ID set, unless `USE_FALLBACK_LABEL` is True, in which case assign the default label.
 - **Writing**: **Write the filtered dataset to `data/processed/teacher_ground_truth_filtered.parquet`**.
 - **Logging**: Write `data/results/exclusion_log.json` with keys `count`, `reason`, and `timestamp`.
 - **Deliverable**: `data/processed/teacher_ground_truth_filtered.parquet` (the filtered dataset) and `exclusion_log.json`.
- [ ] T014 [US1] **Extract and Stream Final Dataset**. Implement logic in `code/00_data_extraction.py` to extract `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector` from the filtered dataset and stream them to `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_ground_truth_filtered.parquet` (produced by T013b).
 - **Pre-check**: Verify input exists. If missing, check for partial artifact `teacher_ground_truth_partial.parquet`. If found, use it. **If the input file has < 1000 rows, exit with code 1** (fail loud) to prevent silent relaxation of constraints. If no fallback, save partial status and exit cleanly.
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

- [ ] T020 [US2] Implement data splitting logic (train/test) in `code/01_train_trees.py` consuming `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_routing_dataset.parquet` (produced by T014) and its validation (T016b).
 - **Pre-check**: Verify `teacher_routing_dataset.parquet` exists and is valid before splitting.
 - **Enforce CPU**: Ensure no GPU usage in data loading (default behavior).
 - **Verification**: Verify `data/processed/train_split.parquet` and `data/processed/test_split.parquet` exist, are valid Parquet files, and contain the expected columns with non-zero row counts.
 - **Deliverable**: `data/processed/train_split.parquet` and `data/processed/test_split.parquet`.
- [X] T021 [US2] Implement a loop to train `DecisionTreeClassifier` (scikit‑learn, CPU) for `max_depth` values **range(2, 21)** (step 1) in `code/01_train_trees.py`.
 - **Logic**: Train a tree for each depth `d` in `range(2, 21)`.
 - **Enforce CPU**: Explicitly set `device='cpu'` in scikit-learn (default) and ensure no PyTorch GPU tensors are used.
 - **Deliverable**: A set of models and a results table showing `max_depth` vs. `routing_accuracy` saved to `data/results/tree_accuracy.csv`.
- [X] T023 [US2] Save each trained model to `models/trained_trees/` and generate a results table (`depth vs. accuracy`) saved to `data/results/tree_accuracy.csv`.
 - **Logic**: Compute and log "Routing Consistency" (accuracy) for each depth against the test set.
 - **Deliverable**: `data/results/tree_accuracy.csv` with columns `max_depth`, `train_accuracy`, `test_accuracy`.
- [X] T024 [US2] Validate model metadata against the schema from `specs/contracts/DecisionTreeMetadata.json` and update `state/` with model hashes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantify Fidelity Degradation and Statistical Significance (Priority: P3)

**Goal**: Execute CPU‑only inference using tree‑predicted routing, measure FID/CLIP for **all** samples, and perform statistical tests (bootstrap, paired t-test) to determine significance of fidelity degradation.

**Independent Test**: The system calculates FID/CLIP for teacher vs. tree (depth=5) on the full dataset and outputs valid p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for statistical test functions (bootstrap, t‑test) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_statistics.py`
- [X] T027 [P] [US3] Integration test for full fidelity evaluation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_fidelity_evaluation.py`. **Logic**: Verify FID/CLIP calculation and statistical test execution.

### Implementation for User Story 3

- [X] T029b [US3] **Load Expert Field Logic**. Implement `code/models/expert_loader.py` to load the individual expert field weights and logic from the teacher model package.
 - **Dependency**: None (Foundational).
 - **Logic**: Extract and cache the specific expert field modules required for re-inference.
 - **Deliverable**: Loaded expert field objects available to T029a.
- [ ] T029c [US3] **Implement CPU-only Euler Integrator**. Implement `code/models/euler.py` to accept `velocity_vector`, `noise_level`, and `expert_type`, use a fixed step size and step count, and invoke the specific expert field logic to generate the image.
 - **Dependency**: Depends on T029b (Expert Fields Loaded).
 - **Logic**: Implement the Euler integration loop.
 - **Deliverable**: `code/models/euler.py` with function `integrate(velocity_vector, noise_level, expert_type) -> image`.
- [ ] T029a [US3] **Generate Velocity Vectors from Tree Routing**. Implement `code/models/expert_reinference.py` to generate velocity vectors based on tree predictions.
 - **Dependency**: Depends on T029b (Expert Fields Loaded).
 - **Input**: `routing_label` (predicted by tree), `noise_level`, `prompt_embedding`.
 - **Logic**: Load the specific expert field logic/weights (from T029b) corresponding to the `routing_label`. Invoke the expert field to generate the `velocity_vector`.
 - **Deliverable**: `velocity_vector` for each sample.
- [ ] T028a [US3] **Generate Teacher and Tree Images**. Implement `code/02_evaluate_fidelity.py` to generate images for BOTH the Teacher baseline and the Tree-predicted routing.
 - **Dependency**: Depends on T020 (Data Split), T021 (Trained Trees), T029b (Expert Fields Loaded), T029a (Velocity Generation), T029c (Euler Integrator).
 - **Logic**: Iterate through the test set. For each sample:
 1. Run Teacher model to get `routing_label` and `velocity_vector`. Generate image using Euler integrator (T029c).
 2. Run Tree model to get `predicted_routing_label`. Use T029a to generate `velocity_vector` based on prediction. Generate image using Euler integrator (T029c).
 3. **Crucial**: Use the **exact same random seed (config.SEED)** and sample indices for both generations to ensure 1:1 alignment.
 - **Deliverable**: `data/results/teacher_baseline_images/` and `data/results/tree_generated_images/` with matching filenames.
- [X] T030a [US3] **Compute FID and CLIP Scores**. Compute metrics for tree-generated images against teacher baseline images using metrics from `code/utils/metrics.py`.
 - **Input**: Results from T028a (both image sets).
 - **Deliverable**: Metrics saved in `data/results/fidelity_metrics.csv`.
- [X] T030b [US3] **Run Pilot**. Execute a pilot run (N=50) to estimate variance for power calculation. [UNRESOLVED-CLAIM: c_8bc3866a — status=not_enough_info]
 - **Dependency**: Depends on T030a.
 - **Deliverable**: Pilot variance estimate.
- [ ] T030c [US3] **Calculate Power and Configure Sample Size**. Calculate required sample size based on pilot variance.
 - **Logic**: Calculate N based on pilot variance using `statsmodels.stats.power.TTestIndPower` and `pilot_variance` variable. **Do not enforce a hard minimum of 1000**. Use the calculated N, but respect the timer from T033a.
 - **Constraint**: If the timer (T033a) indicates time is running out, stop early and use the current N.
 - **Deliverable**: Final sample size configuration for full evaluation.
- [X] T030d [US3] **Perform Statistical Tests**. Perform statistical tests on the FID distributions and CLIP scores to determine the significance of performance degradation using bootstrap testing and paired t-tests.
 - **Input**: Results from T030a (full dataset).
 - **Deliverable**: Statistical test outputs saved in `data/results/statistical_tests.json`.
- [ ] T033a [US3] **Implement Early-Stop Timer**. Implement `code/utils/timer.py` to use the `signal` module for a configurable timeout duration and save partial results as JSON with a `status: partial` flag if exceeded.
 - **Logic**: Set a timer at the start of the evaluation. If time expires, save partial results and exit gracefully.
 - **Deliverable**: `code/utils/timer.py` with `check_timeout()` function.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T032 Reconcile run-book vs implementation for `code/models/train_tree.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/models/train_tree.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T033 Reconcile run-book vs implementation for `code/utils/stats.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/utils/stats.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.