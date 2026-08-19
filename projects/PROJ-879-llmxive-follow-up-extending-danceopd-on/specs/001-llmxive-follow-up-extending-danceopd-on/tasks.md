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

- [X] T001 Create project directory structure per implementation plan in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/` including directories: `code/`, `code/utils/`, `code/data/`, `code/models/`, `code/metrics/`, `data/raw/`, `data/processed/`, `data/results/`, `models/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`.
- [X] T001b [P] Create empty Python script files in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`: `main.py`, `00_data_generation.py`, `01_train_trees.py`, `02_evaluate_fidelity.py`, `03_versioning.py`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/` including pinned dependencies: `torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `transformers`, `accelerate`, `pillow`, `scipy`, `torch-fidelity`, `pyyaml`, `pytest`.
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` to manage seeds, paths, and hyperparameters (including `TEACHER_WEIGHTS_PATH`).
- [X] T005 [P] Create `code/utils/metrics.py` with stub functions `calculate_clip_score(image_path_1: str, image_path_2: str) -> float` and `calculate_fid(image_path_1: str, image_path_2: str) -> float` that raise `NotImplementedError`. These stubs allow the pipeline to run without crashing.
- [X] T005b [P] Implement the actual CPU‑only CLIP Score (using `transformers`) and FID (using `torch-fidelity`) functions in `code/utils/metrics.py`, replacing the stubs from T005. **Signature**: `calculate_clip_score` returns `List[float]` (per-sample scores). `calculate_fid` returns `List[float]` (per-sample scores) to support paired t-tests.
- [X] T006 Create `code/03_versioning.py` to calculate SHA256 hashes for artifacts and update `state/`.
- [X] T007 Setup data directories: `data/raw/`, `data/processed/`, `data/results/` in the project root.
- [X] T008 [P] Implement `code/utils/check_weights.py` to manage `data/raw/weights_manifest.json`.
 - **T008a**: Create `data/raw/weights_manifest.json` if missing. Initialize with a placeholder entry for `teacher_weights.pth` (file_path and expected_sha256 keys).
 - **T008b**: Verify checksums. Load `data/raw/weights_manifest.json`, compute SHA256 of the target weight file, and compare. Exit with code 1 if mismatch or file missing.
 - **T008c**: If the manifest is created from scratch (T008a), compute the SHA256 of an existing `teacher_weights.pth` file if present. If the file is missing, **exit with code 1 and log an error** (do NOT prompt the user). This ensures deterministic execution in CI/CD. **Deliverable**: `data/raw/weights_manifest.json` exists with a valid hash or the script exits with code 1.
- [X] T012b [P] Verify schema of `data/raw/gpu_run_report.json` **IF IT EXISTS**.
 - **Context**: This task is conditional. If the pipeline is running in CPU-only generation mode, this file may not exist.
 - **Schema Check**: If `data/raw/gpu_run_report.json` exists, verify it contains required keys: `gpu_id`, `timestamp`, `model_hash`, `source_dataset`, and `checksum`.
 - **Validation**: If the file exists, verify that the `model_hash` matches the expected teacher model hash in `data/raw/weights_manifest.json`.
 - **Deliverable**: If file exists and is valid, pass. If file missing, log warning and pass. If file exists but invalid, exit with code 1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Teacher Routing Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of `(prompt_embedding, noise_level, routing_label, velocity_vector)` tuples by running the pre‑trained DanceOPD teacher model on sampled ImageNet‑1K and LAION‑400M prompts.

**Independent Test**: The system produces a CSV/Parquet file with ≥1,000 rows, valid expert identifiers, and consistent velocity vector dimensions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for data schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_data_schema.py`
- [X] T011 [P] [US1] Integration test for data generation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_data_generation.py`. **Logic**: Verify `teacher_ground_truth.parquet` exists, has ≥1000 rows, and valid routing labels matching the teacher's known architecture.

### Implementation for User Story 1

- [ ] T012 [US1] Implement data streaming logic in `code/_data_streaming.py` to perform a stratified random sample of images from ImageNet‑1K and LAION‑400M.
 - **Source**: Use `datasets.load_dataset('laion/laion2B-en', split='train', streaming=True)` and `datasets.load_dataset('imagenet-1k', split='train', streaming=True)`.
 - **Sampling Strategy**: Use a fixed random seed. **Target 1200 raw samples** (oversampled to account for exclusions). If pilot exclusion rate > 20%, increase target to 1500.
 - **Pilot Run**: Execute a pilot run of **500 samples** to estimate the 'undefined routing path' exclusion rate. Store this rate in `data/results/pilot_exclusion_rate.json`.
 - **Output**: Write raw batches to `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet`.
 - **Raw Preservation**: Save the raw downloaded image files (or a manifest of URLs and checksums) to `data/raw/` as immutable artifacts to satisfy Constitution Principle III (Data Hygiene).
 - **Feature Extraction**: For each sample, extract `prompt_embedding` (using a CLIP encoder), `noise_level` (if available or default), and pass the image to the teacher model to generate `routing_label` and `velocity_vector`.
 - **Combination**: Combine these into a unified list `data/raw/combined_samples.parquet` containing the full tuple structure.
 - **Retry Logic**: If the initial stream fails or yields insufficient samples, extend sampling until [deferred] raw samples are collected. If the source is unavailable, log the error, save partial results, and exit cleanly (do NOT crash on missing source).
 - **Deliverable**: `combined_samples.parquet` exists and contains valid image paths and extracted tuples.
- [ ] T013a-Generate [US1] Run the pre-trained DanceOPD teacher model on the sampled data to generate ground truth routing labels and velocity vectors.
 - **Context**: This task attempts to run the teacher model on CPU. If it fails (timeout or OOM), it exits with code 1. **No fallback to S3 artifacts.**
 - **Enforce CPU**: Use `torch.set_default_device('cpu')` and `torch.no_grad()` to ensure the model runs on CPU.
 - **Timeout Mechanism**: Use `signal.signal(signal.SIGALRM, handler)` to enforce a **1-hour timeout**. If the timeout is hit, log the error and exit with code 1.
 - **Primary Path**: Attempt to load the teacher model and run inference on the data from T012.
 - **Filtering**: During inference, detect 'undefined routing paths' (labels not in the known expert set). **Exclude** these samples immediately. Log the count to `data/results/exclusion_log.json`.
 - **Deliverable**: `teacher_ground_truth.parquet` (generated) with ≥1000 valid rows. If generation fails, exit with code 1.
- [ ] T013b [US1] Perform final validation and exclusion of undefined routing paths on the extracted dataset.
 - **Context**: This task filters the dataset extracted by T014. It does NOT perform inference.
 - **Definition**: An 'undefined routing path' is any `routing_label` not in the known expert ID set (e.g., `expert_text_to_image`, `expert_editing`).
 - **Note**: The spec's edge case handling for 'assign a default fallback label' is NOT implemented in this iteration. **Exclude** those samples.
 - **Logging**: Write `data/results/exclusion_log.json` with keys `count`, `reason` (e.g., "undefined_label"), and `timestamp`.
 - **Verification**: (2506.09162, https://arxiv.org/abs/2506.09162) If the final dataset size is below 1000 after exclusion, **exit with code 1 and log the specific error "Dataset size below 1000 after exclusion"**.
 - **Deliverable**: Updated dataset excluding null/undefined rows and `exclusion_log.json`.
- [ ] T014 [US1] Implement logic in `code/00_data_extraction.py` to extract `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector` from inference outputs and stream them to `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_ground_truth.parquet` (produced by T013a-Generate). It does NOT depend on conditional tasks like T013a-Verify or T013a-Load.
 - **Pre-check**: Verify `teacher_ground_truth.parquet` exists and is valid before processing.
 - **Deliverable**: `data/processed/teacher_routing_dataset.parquet`.
- [X] T015 [US1] Add validation in `code/00_data_extraction.py` to ensure each `routing_label` matches a known expert field ID from the DanceOPD configuration.
- [X] T016 [US1] Implement checksumming and versioning of the generated dataset using `code/03_versioning.py`.
- [ ] T016b [US1] Validate that `teacher_routing_dataset.parquet` contains samples from **both** ImageNet‑1K and LAION‑400M sources. **Note**: This task depends on T013b and T014 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Static Decision Trees (Priority: P2)

**Goal**: Train Decision Tree classifiers with `max_depth` ranging from shallow to deep on the generated dataset to approximate routing labels and compute "Routing Consistency".

**Independent Test**: A tree with `max_depth=5` is saved and reports a reproducible validation accuracy on a held‑out test split.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Decision Tree training parameters in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_tree_training.py`. **Logic**: Verify `DecisionTreeClassifier` instantiation with specific depths and correct accuracy calculation. **Note**: This task explicitly references the spec's 'Independent Test' for US2.
- [X] T019 [P] [US2] Integration test for training loop and metadata schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_tree_training.py`. **Note**: This test validates the output of T020-T023. **Ordering**: Written FIRST, before T020.

### Implementation for User Story 2

- [ ] T020 [US2] Implement data splitting logic (train/test) in `code/01_train_trees.py` consuming `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_routing_dataset.parquet` (produced by T014) and its validation (T016b).
 - **Pre-check**: Verify `teacher_routing_dataset.parquet` exists and is valid before splitting.
 - **Enforce CPU**: Ensure no GPU usage in data loading (default behavior).
 - **Deliverable**: `data/processed/train_split.parquet` and `data/processed/test_split.parquet`.
- [X] T021 [US2] Implement a loop to train `DecisionTreeClassifier` (scikit‑learn, CPU) for `max_depth` values **systematically varying from 2 to 20** (step 1) in `code/01_train_trees.py`.
 - **Logic**: Train a tree for each depth `d` in `2, 3,..., 20`.
 - **Enforce CPU**: Explicitly set `device='cpu'` in scikit-learn (default) and ensure no PyTorch GPU tensors are used.
 - **Deliverable**: A set of models and a results table showing `max_depth` vs. `routing_accuracy`.
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

- [X] T029 [US3] Implement CPU‑only Euler integrator in `code/models/inference.py`.
 - **Logic**: The function accepts `velocity_vector`, `noise_level`, and `expert_type`, uses a fixed step size and step count (defined in `config.py`), and invokes the appropriate expert field logic to generate an image.
 - **Deliverable**: `code/models/inference.py` with full implementation.
 - **Note**: This task must complete before T028.
- [ ] T028 [US3] Implement logic in `code/02_evaluate_fidelity.py` to generate images using two modes:
 1. **Tree‑Generated**: For each sample, predict the expert with the trained Decision Tree (from T023), re‑run that expert to obtain a fresh `velocity_vector`, and integrate (via `code/models/inference.py`) to produce an image.
 2. **Teacher‑Baseline**: For each sample, use the stored `routing_label` from the teacher dataset, re‑run the corresponding expert to obtain a fresh `velocity_vector`, and integrate to produce an image.
 - **Context**: This task attempts to generate teacher baseline on CPU. If it fails (timeout or OOM), it exits with code 1. **No fallback to S3 artifacts.**
 - **Enforce CPU**: Use `torch.set_default_device('cpu')` and `torch.no_grad()` for the teacher model.
 - **Primary Path**: Generate teacher baseline images on CPU. Set a strict **1-hour timeout** (using `signal.SIGALRM`).
 - **Constraint**: Use the **exact same** Euler integrator and step parameters for both modes to isolate routing degradation.
 - **Sample Size**: Load N from `data/results/sample_size_config.json` (generated by T030b-Exec). Process **min(N, test_split_size)** samples.
 - **Output**: Images saved under `data/results/` with prefixes `tree_depth{D}_sample_{idx}.png` and `teacher_baseline_sample_{idx}.png`.
 - **Note**: This task depends on T005b (metrics), T029 (integrator), T023 (trained trees), T020 (data splitting), and **T030b-Exec**.
- [ ] T030b-Impl [US3] Implement dynamic sample size logic in `code/02_evaluate_fidelity.py`.
 - **Logic**: Define a function to calculate required sample size using **effect_size=0.5 (medium), alpha=0.05, power=0.8**.
 - **Deliverable**: Implementation of the calculation function.
- [ ] T030b-Exec [US3] Run the pilot and determine final N.
 - **Logic**: Run a pilot with **N=50** (first 50 samples, seed 42). If dataset < 50, use all. Calculate power using the function from T030b-Impl. If power < 0.8, extend N up to a maximum of 200 or until runtime limit (30s for pilot).
 - **Constraint**: If the runtime limit is hit, save partial results with `status: partial` and do NOT abort unless the final dataset size is < N_min (see T030a).
 - **Output**: Write `data/results/sample_size_config.json` with keys `n_pilot`, `calculated_n`, `power`, `status`.
 - **Deliverable**: `data/results/sample_size_config.json`.
- [X] T030 [US3] Compute FID and CLIP Score **on the test split (limited to N samples)** comparing Tree‑Generated images vs. Teacher‑Baseline images.
 - **Output**: Store results in `data/results/fidelity_metrics.csv` with columns `depth`, `fid_teacher`, `fid_tree`, `clip_teacher`, `clip_tree`.
 - **Derivation**: Derive total degradation metrics (ΔFID, ΔCLIP) and write them to the same CSV.
 - **Constraint**: If the full dataset cannot be processed within the designated runtime limit, **stop early** and save partial results to `data/results/partial_results.json` with a `status: partial` flag. The partial results must contain: `status`, `processed_count`, `total_count`, and `metrics` (list of dicts with `sample_id`, `fid`, `clip`).
 - **Deliverable**: `data/results/fidelity_metrics.csv` or `partial_results.json`.
- [X] T030a [US3] Perform statistical tests on the results from T030.
 - **Logic**:
 1. Perform a bootstrap hypothesis test on the FID distribution.
 2. Perform a paired t-test on per-sample CLIP scores (two-tailed, alpha=0.05). **Ensure input lists are aligned**.
 - **Constraint**: Use a fixed minimum sample size (N_min) defined in `config.py`. If the dataset size is < N_min, **save partial results** with `status: insufficient_power` and log a warning (do NOT abort). The statistical tests should not be run on insufficient data, but the pipeline continues.
 - **Output**: Write final statistical test outputs (p-values, confidence intervals, power) to `data/results/statistical_tests.json`.
 - **Deliverable**: `data/results/statistical_tests.json`.
- [X] T031 [US3] Generate a summary report `data/results/fidelity_summary.md` that includes degradation metrics, statistical significance statements, and any partial‑result notes.
- [X] T032 [US3] Implement a hard timeout using the `signal` module. On timeout **or** on early exit due to **statistical power insufficiency**, ensure all completed depth results and any partial metrics are persisted to `data/results/partial_results.json` with a `status: partial` flag. This task merges the functionality of the previous T033.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Refactor `code/utils/metrics.py` and `code/models/inference.py` to add full type hints and docstrings. **Verification**: `ruff check code/` passes with no type errors.
- [ ] T035b [P] Remove dead code and unused imports from all `code/` modules. **Verification**: Run `vulture code/ --min-confidence [threshold] > vulture_report.txt`. The task must pass if `vulture_report.txt` exists and is empty (or contains only low-confidence warnings). If high-confidence issues are found, exit with code 1. **Deliverable**: `vulture_report.txt`.
- [ ] T035c [P] Optimize import statements in `code/` to remove circular dependencies. **Verification**: `python -m code.import` runs without `ImportError`.
- [ ] T036a [P] Performance optimization for data streaming: Implement chunked loading to reduce memory usage. **Verification**: Memory profile shows < 6 GB peak.
- [ ] T036b [P] Performance optimization for batch processing: Implement parallel batch processing for image generation. **Verification**: Verify wall-clock time reduction > 2x compared to sequential processing.
- [ ] T037 [P] Additional unit tests for edge cases (memory exhaustion, undefined routes) in `tests/unit/`. **Logic**: Test memory exhaustion handling, undefined route exclusion, and timeout behavior.
- [ ] T038 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility. **Logic**: Execute all commands in `quickstart.md` and verify end-to-end success.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T014 (dataset generation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T023 (trained trees) and T014 (dataset)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data streaming and schema validation before model training
- Training before inference and statistical testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: In Phase 5, T005b (metrics) and T029 (integrator) are independent prerequisites but must both complete before T028. T028 is NOT parallel to T005b or T029.
- **Note**: T020 in Phase 4 is NOT parallel; it depends on T014 and T016b.
- **Note**: T028 in Phase 5 depends on T023 (trained trees) being complete.
- **Note**: T030b (Dynamic Sample Size) must complete before T030 (Compute FID) and T030a (Statistical Tests).
- **Note**: T005b (Metrics Implementation) is in Phase 2 and is a prerequisite for T028.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU‑only CI with minimal computational resources (limited CPU cores and RAM, ≤7 GB RAM, ≤6 hours total runtime). No CUDA, no 8‑bit/4‑bit quantization, no large model training. **Exceptions**: Teacher model inference (T013a-Generate, T028) attempts CPU first, but exits with code 1 if CPU inference is infeasible. **No S3 fallback.**
- **Data Integrity**: No synthetic/fake input data allowed. All data must come from real sources (ImageNet/LAION via HF) or real teacher model inference.
- **File Separation**: Phase 3 tasks are split into `00_data_streaming.py`, `00_teacher_inference.py`, `00_data_extraction.py` to prevent merge conflicts. Phase 5 tasks are split into `02_evaluate_fidelity.py`, `models/inference.py`, `utils/metrics.py`, `statistics.py` for the same reason.
- **Statistical Validity**: T030a enforces a hard minimum sample size. If the dataset is smaller than N_min, the run saves partial results with `status: insufficient_power` (does NOT abort) to preserve SC-005.
- **Real Data Streaming**: T012 mandates streaming real data (ImageNet/LAION) rather than using synthetic fallbacks; if real fetch fails, the script MUST save partial results and exit cleanly.
- **Undefined Route Handling**: T013b explicitly excludes undefined routes and verifies the final dataset size meets the minimum requirement. The 'fallback' option is not implemented.
- **Timeout Logic**: T032 implements a hard 6‑hour timeout using `signal.SIGALRM` to prevent CI hangs and ensure partial results are saved. T033 was merged into T032.
- **Teacher Inference**: T013a-Generate and T028 attempt CPU inference first. If they fail (timeout/OOM), they **exit with code 1**. No fallback to pre-computed GPU artifacts.
- **Re‑generation Logic**: T029 explicitly re‑generates velocity vectors based on routing source (Tree vs Teacher) to measure full error propagation.
- **Dependency Correction**: T005b (metrics) must run before T028 (evaluation). T029 (integrator) must run before T028 (evaluation). T020 (splitting) must run after T014 (generation) and T016b (validation). T028 (evaluation) must run after T023 (trained trees). T030b (Dynamic Sample Size) must run before T030 (Compute FID).
- **Ordering Correction**: T019 (Integration Test) is listed BEFORE T020 (Implementation) to respect the 'Tests FIRST' rule.
- **Task Removal**: T016c and T034 were removed as they were redundant or rejected. T033 was merged into T032. T030 was renamed to T030b to avoid collision. T012b was added to validate external artifact schema (conditional).
- **New Task T039**: Addressed the "undefined routing path" edge case by enforcing strict exclusion and logging, ensuring no synthetic fallbacks are used.
- **New Task T040**: Addressed the "memory exhaustion" edge case by implementing chunked streaming and partial result saving, ensuring the pipeline never crashes on large datasets.
- **New Task T041**: Addressed the "overfitting" edge case by ensuring both training and test accuracy are reported, and the analysis focuses on test set performance.
- **Fallback Logic**: T013a-Generate and T028 **do not** include fallback paths for pre-computed GPU artifacts. If CPU inference fails, the pipeline stops.
- **Conditional Validation**: T012b and T013a-Verify are conditional on the existence of `gpu_run_report.json`. They do not block the pipeline if the file is missing.
- **Pilot Logic**: T030b-Exec uses a fixed pilot size (50) and seed (42) to determine sample size.
- **Per-Sample Metrics**: T005b returns per-sample scores to support paired t-tests in T030a.
- **Partial Results**: T030 and T030a save partial results with specific schemas if the runtime limit is hit or sample size is insufficient.
- **Sample Size Logic**: T028 processes `min(N, test_split_size)` samples as determined by T030b-Exec.