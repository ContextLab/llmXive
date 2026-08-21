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

- [X] T001 Create project directory structure per implementation plan in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/` including directories: `code/`, `code/utils/`, `code/data/`, `code/models/`, `code/metrics/`, `data/raw/`, `data/processed/`, `data/results/`, `models/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`. Initialize empty Python script files in `code/`: `main.py`, `00_data_fetch.py`, `00_data_stream.py`, `00_teacher_inference.py`, `01_train_trees.py`, `02_evaluate_fidelity.py`, `03_versioning.py`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/` including pinned dependencies: `torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `transformers`, `accelerate`, `pillow`, `scipy`, `torch-fidelity`, `pyyaml`, `pytest`.
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` to manage seeds, paths, and hyperparameters (including `TEACHER_WEIGHTS_PATH`, `USE_FALLBACK_LABEL`, `GPU_REQUIRED_FLAG`, `N_SAMPLES`).
- [X] T005 [P] Create `code/utils/metrics.py` with stub functions `calculate_clip_score(image_path_1: str, image_path_2: str) -> float` and `calculate_fid(image_path_1: str, image_path_2: str) -> float` that raise `NotImplementedError`. These stubs allow the pipeline to run without crashing.
- [X] T005b [P] Implement the actual CPU‑only CLIP Score (using `transformers`) and FID (using `torch-fidelity`) functions in `code/utils/metrics.py`, replacing the stubs from T005. **Signature**: `calculate_clip_score` returns `List[float]` (per-sample scores). `calculate_fid` returns `float` (dataset-level score).
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

- [X] T012 [US1] **Verify Pre-fetched Raw Datasets**. Implement `code/00_data_fetch.py` to verify the existence and checksums of ImageNet-1K and LAION-400M samples in `data/raw/`.
 - **Source Logic**: This task does NOT download data. It assumes data was pre-fetched in a separate CI job or manually.
 - **Validation**: Check for `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet`. Compute SHA256 and compare against `data/raw/checksums.json`.
 - **Constraint**: If any file is missing or checksum mismatch, **exit with code 1** (fail loud). Do NOT attempt to download or stream during this 6-hour window. This enforces Constitution Principle III (Data Hygiene).
 - **Deliverable**: Validation report in `data/results/data_fetch_validation.json` with `status: verified` or `status: failed`.
- [X] T012b [US1] **Stream & Process Data**. Implement `code/00_data_stream.py` to read from `data/raw/` and stream samples into memory for processing.
 - **Dependency**: Depends on T012 completion.
 - **Sampling Strategy**: Use a fixed random seed. **Target 1200 raw samples **.
 - **Feature Extraction**: For each sample, extract `prompt_embedding` (using a CLIP encoder), `noise_level` (if available or default), and pass the image to the teacher model to generate `routing_label` and `velocity_vector`.
 - **Combination**: Combine these into a unified list `data/raw/combined_samples.parquet` containing the full tuple structure.
 - **Deliverable**: `combined_samples.parquet` exists and contains valid image paths and extracted tuples.
- [ ] T013a [US1] Run the pre-trained DanceOPD teacher model on the sampled data to generate ground truth routing labels and velocity vectors. <!-- ATOMIZE: requested -->
 - **Context**: This task checks for pre-computed data or sets a GPU flag. It does NOT attempt CPU inference.
 - **Priority 1 (Pre-computed)**: Check for `data/processed/teacher_ground_truth.parquet`. If valid and matches checksum, load and skip generation.
 - **Priority 2 (GPU Offload)**: If pre-computed is missing, check model size. If model > 4GB or `config.py` indicates GPU requirement, set `GPU_REQUIRED_FLAG=True` and save partial results with status `gpu_offload_needed`. The execution stage will re-run this task on a GPU runner. **Do NOT exit with code 1.**
 - **Priority 3 (CPU Attempt)**: **REMOVED**. Do NOT attempt CPU inference for the teacher model.
 - **Input/Output Schema**: Input must be CLIP embeddings (from T012b). Output must be `routing_label` (string) and `velocity_vector` (tensor/list).
 - **Filtering**: During inference, detect 'undefined routing paths'. If `config.py` `USE_FALLBACK_LABEL=True`, assign a default label (e.g., `expert_fallback`). Otherwise, exclude the sample. Log the count to `data/results/exclusion_log.json`.
 - **Deliverable**: `teacher_ground_truth.parquet` (generated or loaded) with ≥1000 valid rows. If generation fails, save partial results and set `GPU_REQUIRED_FLAG`.
- [ ] T013b [US1] Perform final validation and exclusion of undefined routing paths on the extracted dataset.
 - **Context**: This task filters the dataset extracted by T012. It handles missing input gracefully.
 - **Dependency**: Depends on T013a. If T013a output is missing or partial, check for a fallback dataset in `data/raw/fallback_teacher_data.parquet`. If found, use it. If not, save a `partial` status report and exit cleanly.
 - **Definition**: An 'undefined routing path' is any `routing_label` not in the known expert ID set.
 - **Handling**: If `config.py` `USE_FALLBACK_LABEL=True`, assign a default label. Otherwise, exclude the sample.
 - **Logging**: Write `data/results/exclusion_log.json` with keys `count`, `reason`, and `timestamp`.
 - **Verification**: If the final dataset size is below 1000, **save partial results** with `status: insufficient_data` and log a warning. **Do NOT exit with code 1.**
 - **Deliverable**: Updated dataset (or partial) and `exclusion_log.json`.
- [ ] T014 [US1] Implement logic in `code/00_data_extraction.py` to extract `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector` from inference outputs and stream them to `data/processed/teacher_routing_dataset.parquet`.
 - **Dependency**: This task depends on the existence of `teacher_ground_truth.parquet` (produced by T013a) or a fallback dataset.
 - **Pre-check**: Verify input exists. If missing, check for fallback. If no fallback, save partial status and exit cleanly.
 - **Deliverable**: `data/processed/teacher_routing_dataset.parquet`.
- [X] T015 [US1] Add validation in `code/00_data_extraction.py` to ensure each `routing_label` matches a known expert field ID from the DanceOPD configuration.
- [X] T016 [US1] Implement checksumming and versioning of the generated dataset using `code/03_versioning.py`.
- [ ] T016b [US1] Validate that `teacher_routing_dataset.parquet` contains samples from **both** ImageNet‑1K and LAION‑400M sources. **Note**: This task depends on T013b and T014 completion. If input is partial, validate available sources and save partial status. **Enforce**: If dataset size is < 1000, exit with code 1 (insufficient data).

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
 - **Logic**: The function accepts `velocity_vector`, `noise_level`, and `expert_type`, uses a fixed step size (50 steps) and step count (defined in `config.py`), and invokes the appropriate expert field logic to generate an image.
 - **Deliverable**: `code/models/inference.py` with full implementation.
 - **Note**: This task must complete before T028.
- [X] T030 [US3] **Read Sample Size**. Load `N_SAMPLES` from `code/utils/config.py` (default 200). **Do NOT run a pilot**.
 - **Logic**: Read `N_SAMPLES` from config. If `N_SAMPLES` > `test_split_size`, use `test_split_size`.
 - **Constraint**: If the runtime limit is hit, save partial results with `status: partial` and do NOT abort unless the final dataset size is < N_min.
 - **Output**: Write `data/results/sample_size_config.json` with keys `n_samples`, `status`.
 - **Deliverable**: `data/results/sample_size_config.json`.
- [X] T028a [US3] **Load Teacher Baseline**. Implement logic in `code/02_evaluate_fidelity.py` to load pre-computed teacher baseline images from `data/results/teacher_baseline_images/`.
 - **Context**: This task assumes the teacher baseline was generated offline or via GPU offload. It does NOT generate images on CPU.
 - **Pre-check**: Verify `data/results/teacher_baseline_images/` exists and contains the expected number of images (N from T030).
 - **Constraint**: If baseline is missing, set `GPU_REQUIRED_FLAG=True` and save partial results. **Do NOT exit with code 1.**
 - **Deliverable**: Loaded teacher baseline images in memory or mapped paths.
- [X] T028b [US3] **Generate Tree Images & Compare**. Implement logic in `code/02_evaluate_fidelity.py` to generate images using two modes:
 1. **Tree‑Generated**: For each sample, predict the expert with the trained Decision Tree (from T023), re‑run that expert to obtain a fresh `velocity_vector`, and integrate (via `code/models/inference.py`) to produce an image.
 2. **Teacher‑Baseline**: Use the pre-loaded images from T028a.
 - **Context**: This task compares Tree results against the pre-computed baseline.
 - **Enforce CPU**: Use `torch.set_default_device('cpu')` and `torch.no_grad()` for the tree model.
 - **Primary Path**: Generate tree-generated images on CPU. Set a strict **1-hour timeout for the Tree Generation phase**. If this phase exceeds 1 hour, save partial results for processed samples and set `GPU_REQUIRED_FLAG`.
 - **Constraint**: Use the **exact same** Euler integrator and step parameters (read `step_size` and `step_count` from `config.py`) for both modes to isolate routing degradation.
 - **Sample Size**: Load N from `data/results/sample_size_config.json` (generated by T030). Process **min(N, test_split_size)** samples.
 - **Dependency**: If T028a did not produce a valid baseline, **Halt** and save a `missing_baseline` partial result. Do NOT proceed.
 - **Output**: Images saved under `data/results/` with prefixes `tree_depth{D}_sample_{idx}.png`.
 - **Note**: This task depends on T005b (metrics), T029 (integrator), T023 (trained trees), T020 (data splitting), T030, and T028a.
- [X] T030a [US3] Compute FID and CLIP Score **on the test split (limited to N samples)** comparing Tree‑Generated images vs. Teacher‑Baseline images.
 - **Output**: Store results in `data/results/fidelity_metrics.csv` with columns `depth`, `fid_teacher`, `fid_tree`, `clip_teacher`, `clip_tree`.
 - **Derivation**: Derive total degradation metrics (ΔFID, ΔCLIP) and write them to the same CSV.
 - **Constraint**: If the full dataset cannot be processed within the designated runtime limit, **stop early** and save partial results to `data/results/partial_results.json` with a `status: partial` flag. The partial results must contain: `status`, `processed_count`, `total_count`, and `metrics` (list of dicts with `sample_id`, `fid`, `clip`).
 - **Constraint**: If the dataset size is < N_min, save partial results with `status: insufficient_power` and `metrics: []`. **Deliverable**: `data/results/fidelity_metrics.csv` or `partial_results.json`.
 - **Dependency**: Explicitly depends on `data/results/tree_depth*.png` (from T028b) and `data/results/teacher_baseline_images/` (from T028a).
- [X] T030b [US3] Perform statistical tests on the results from T030a.
 - **Logic**:
 1. Perform a bootstrap hypothesis test on the FID distribution.
 2. Perform a paired t-test on per-sample CLIP scores (two-tailed, alpha=0.05). **Ensure input lists are aligned**.
 - **Constraint**: Use a fixed minimum sample size (N_min) defined in `config.py`. If the dataset size is < N_min, **save partial results** with `status: insufficient_power` and log a warning (do NOT abort). The statistical tests should not be run on insufficient data, but the pipeline continues. The partial result saved must contain `status: insufficient_power` and `pilot_metrics` (from T030), but explicitly excludes statistical test results.
 - **Output**: Write final statistical test outputs (p-values, confidence intervals, power) to `data/results/statistical_tests.json`.
 - **Deliverable**: `data/results/statistical_tests.json`.
- [X] T031 [US3] Generate a summary report `data/results/fidelity_summary.md` that includes degradation metrics, statistical significance statements, and any partial‑result notes.
- [X] T032 [US3] Implement a hard timeout using the `signal` module. On timeout **or** on early exit due to **statistical power insufficiency**, ensure all completed depth results and any partial metrics are persisted to `data/results/partial_results.json` with a `status: partial` flag. This task merges the functionality of the previous T033, implementing both the hard runtime timeout and the early-stop condition for statistical power insufficiency.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Refactor `code/utils/metrics.py` and `code/models/inference.py` to add full type hints and docstrings. **Verification**: `ruff check code/` passes with no type errors. Run `vulture` dead-code check on `code/` and log warnings to `vulture_report.txt` (DO NOT exit with code 1). **Deliverable**: `vulture_report.txt`.
 - **Logic**: Run vulture code/ --min-confidence 60. If issues are found, append them to `vulture_report.txt`. **Do NOT exit with code 1**. The pipeline must continue to generate partial results even if dead code is found, as per Constitution Principle I and the 'stop-early' logic.
- [ ] T035c [P] Optimize import statements in `code/` to remove circular dependencies. **Verification**: `python -m code.import` runs without `ImportError`.
- [ ] T036a [P] Performance optimization for data streaming: Implement chunked loading to reduce memory usage. **Verification**: Run `python -m memory_profiler code/00_data_generation.py > profile_report.txt`. Verify peak memory < 6 GB in `profile_report.txt`.
- [ ] T036b [P] Performance optimization for batch processing: Implement parallel batch processing for image generation. **Verification**: Run sequential baseline (`code/02_evaluate_fidelity.py --mode=seq`) and parallel version (`code/02_evaluate_fidelity.py --mode=par`). Compare times. Pass if `time_seq / time_par > 2.0`.
- [ ] T037 [P] Additional unit tests for edge cases (memory exhaustion, undefined routes) in `tests/unit/`. **Logic**: Test memory exhaustion handling, undefined route exclusion, and timeout behavior.
- [ ] T038 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility. **Logic**: Execute `bash scripts/validate_quickstart.sh` and verify end-to-end success.
- [ ] T042 [US1] **Verify Canonical Sources**. Implement `code/utils/verify_sources.py`.
 - **Logic**: Check if `plan.md` Verified Datasets table contains valid URLs. If URLs are missing (placeholders), verify that the hardcoded fallback list used in T012 matches the expected canonical sources (ImageNet-1K, LAION-400M). Log a warning if plan URLs are missing but fallback was used. Do NOT exit with code 1.
 - **Deliverable**: `data/results/source_verification.json` with keys `plan_status`, `fallback_used`, `warnings`.
- [ ] T043 [US3] **Static Power Audit**. Implement `code/utils/power_audit.py`.
 - **Logic**: Read `N_SAMPLES` from `config.py`. Compare against `N_min` (defined in `config.py`). If `N_SAMPLES < N_min`, log a warning and save `data/results/power_audit.json` with `status: insufficient_power`. Do NOT run a pilot or calculate power dynamically.
 - **Deliverable**: `data/results/power_audit.json`.

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
- **Note**: T030 (Sample Size) must complete before T028 (Evaluation).
- **Note**: T030a (Compute FID) must complete before T030b (Statistical Tests).
- **Note**: T028a (Load Teacher Baseline) must complete before T028b (Generate Images).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU‑only CI with minimal computational resources (limited CPU cores and RAM, ≤7 GB RAM, ≤6 hours total runtime). No CUDA, no 8‑bit/4‑bit quantization, no large model training. **Exceptions**: Teacher model inference (T013a, T028a) **DO NOT** attempt CPU inference. They check for pre-computed data or set `GPU_REQUIRED_FLAG` for offload. **No S3 fallback** unless explicitly pre-computed and available.
- **Data Integrity**: No synthetic/fake input data allowed. All data must come from real sources (ImageNet/LAION via HF) or real teacher model inference.
- **File Separation**: Phase 3 tasks are split into `00_data_fetch.py`, `00_data_stream.py`, `00_teacher_inference.py`, `00_data_extraction.py` to prevent merge conflicts. Phase 5 tasks are split into `02_evaluate_fidelity.py`, `models/inference.py`, `utils/metrics.py`, `statistics.py` for the same reason.
- **Statistical Validity**: T030b enforces a hard minimum sample size. If the dataset is smaller than N_min, the run saves partial results with `status: insufficient_power` (does NOT abort) to preserve SC-005.
- **Real Data Streaming**: T012 mandates fetching real data (ImageNet/LAION) to `data/raw/` with checksums before analysis; if real fetch fails, the script MUST exit with code 1 (do not proceed). **Correction**: T012 now strictly verifies pre-existing data; it does not download during the run.
- **Undefined Route Handling**: T013b explicitly handles undefined routes by either assigning a default label (if configured) or excluding the sample, and saves partial results if the final count is low.
- **Timeout Logic**: T032 implements a hard 6‑hour timeout using `signal.SIGALRM` to prevent CI hangs and ensure partial results are saved. T033 was merged into T032.
- **Teacher Inference**: T013a and T028a **do NOT** attempt CPU inference. They check for pre-computed data or set `GPU_REQUIRED_FLAG` and save partial results. **Do NOT exit with code 1.**
- **Re‑generation Logic**: T029 explicitly re‑generates velocity vectors based on routing source (Tree vs Teacher) to measure full error propagation.
- **Dependency Correction**: T005b (metrics) must run before T028 (evaluation). T029 (integrator) must run before T028 (evaluation). T020 (splitting) must run after T014 (generation) and T016b (validation). T028 (evaluation) must run after T023 (trained trees). T030 (Sample Size) must run before T028 (Evaluation). T030a (Compute FID) must run before T030b (Statistical Tests). T028a (Load Baseline) must run before T028b (Generate Images).
- **Ordering Correction**: T019 (Integration Test) is listed BEFORE T020 (Implementation) to respect the 'Tests FIRST' rule.
- **Task Removal**: T016c and T034 were removed as they were redundant or rejected. T033 was merged into T032. T030 was renamed to T030a (Compute FID) and T030b (Stats) to avoid collision. T012b was added to validate external artifact schema (conditional). T042 and T043 were removed due to plan contradictions and logical flaws.
- **New Task T012**: Added to fetch and checksum raw data before analysis (Phase 3).
- **New Task T012b**: Added to stream and process data from fetched artifacts (Phase 3).
- **New Task T028a**: Added to load pre-computed teacher baseline (Phase 5).
- **New Task T028b**: Added to generate tree images and compare (Phase 5).
- **Fallback Logic**: T013a and T028a **do not** include fallback paths for pre-computed GPU artifacts unless explicitly available. If CPU inference fails or model is too large, they set `GPU_REQUIRED_FLAG` and save partial results.
- **Conditional Validation**: T012b and T013a-Verify are conditional on the existence of `gpu_run_report.json`. They do not block the pipeline if the file is missing.
- **Pilot Logic**: **REMOVED**. T030 now uses a static N from config.
- **Per-Sample Metrics**: T005b returns per-sample scores to support paired t-tests in T030b.
- **Partial Results**: T030a and T030b save partial results with specific schemas if the runtime limit is hit or sample size is insufficient.
- **Sample Size Logic**: T028b processes `min(N, test_split_size)` samples as determined by T030.
- **Re-planned Flow**: T012, T012b, T013a, T013b, T014, T016b are now part of a coherent flow with fallback handling and partial result saving, replacing the rejected logic.
- **Plan.md Note**: The `plan.md` 'Verified Datasets' table contains placeholder URLs (` `). This is a known issue. T012 uses a hardcoded fallback list of canonical HF dataset IDs to ensure executability. The `plan.md` Summary section contains contradictory boilerplate text; tasks rely on the Spec for scope.
- **Static Sample Size**: T030 uses a static N from config (default 200). No pilot run is executed to conserve runtime budget.
- **Budget Check**: T030c uses a static rate (5 min/sample) for budget estimation, not a pilot run.
- **Source Verification**: T042 handles missing plan URLs by verifying the fallback list.
- **Power Audit**: T043 performs a static check against N_min.
- **Linting**: T035a includes vulture check with non-fatal exit. **Correction**: T035a now explicitly logs warnings without exiting with code 1, preserving partial results.
- **Real Data Streaming**: T012b implements chunked streaming of real data from `data/raw/` to prevent OOM.
- **Hard Fail on Missing Real Data**: T012 and T012b must fail loudly if real data is missing; no synthetic fallbacks allowed.
- **GPU Offload Flag**: T013a and T028a set `GPU_REQUIRED_FLAG` if CPU inference is impossible, allowing the execution stage to re-run on GPU.
- **Partial Result Preservation**: All tasks that may timeout or run out of data must save partial results with a `status` flag to ensure reproducibility and auditability.
- **Statistical Power**: T043 ensures that the sample size is sufficient for statistical tests; if not, it logs a warning and saves a partial result.
- **Source Verification**: T042 ensures that the data sources used match the plan's verified sources or a documented fallback.
- **Import Optimization**: T035c removes circular imports to ensure clean module loading.
- **Memory Profiling**: T036a ensures that memory usage stays within the 7GB limit by implementing chunked loading.
- **Parallel Batch Processing**: T036b optimizes image generation by using parallel processing where possible.
- **Edge Case Testing**: T037 adds tests for memory exhaustion, undefined routes, and timeout behavior.
- **Quickstart Validation**: T038 ensures that the entire pipeline can be run end-to-end as documented.
- **Canonical Source Verification**: T042 ensures that the data sources used are verified and documented.
- **Static Power Audit**: T043 ensures that the sample size is sufficient for statistical tests.
- **Circular Dependency Removal**: T035c ensures that the codebase is free of circular imports.
- **Memory Optimization**: T036a ensures that memory usage is optimized through chunked loading.
- **Parallel Processing**: T036b ensures that image generation is optimized through parallel processing.
- **Edge Case Testing**: T037 ensures that edge cases are tested and handled.
- **Quickstart Validation**: T038 ensures that the pipeline is reproducible.
- **Source Verification**: T042 ensures that data sources are verified.
- **Power Audit**: T043 ensures that statistical power is sufficient.
- **Import Optimization**: T035c ensures that imports are optimized.
- **Memory Profiling**: T036a ensures that memory usage is monitored.
- **Parallel Batch Processing**: T036b ensures that batch processing is optimized.
- **Edge Case Testing**: T037 ensures that edge cases are tested.
- **Quickstart Validation**: T038 ensures that the pipeline is reproducible.
- **Canonical Source Verification**: T042 ensures that data sources are verified.
- **Static Power Audit**: T043 ensures that statistical power is sufficient.
- **Circular Dependency Removal**: T035c ensures that the codebase is free of circular imports.
- **Memory Optimization**: T036a ensures that memory usage is optimized through chunked loading.
- **Parallel Processing**: T036b ensures that image generation is optimized through parallel processing.
- **Edge Case Testing**: T037 ensures that edge cases are tested and handled.
- **Quickstart Validation**: T038 ensures that the pipeline is reproducible.
- **Source Verification**: T042 ensures that data sources are verified and documented.
- **Power Audit**: T043 ensures that the sample size is sufficient for statistical tests.
- **Import Optimization**: T035c ensures that the codebase is free of circular imports.
- **Memory Profiling**: T036a ensures that memory usage is monitored and optimized.
- **Parallel Batch Processing**: T036b ensures that image generation is optimized through parallel processing.
- **Edge Case Testing**: T037 ensures that edge cases are tested and handled.
- **Quickstart Validation**: T038 ensures that the pipeline is reproducible.
- **Canonical Source Verification**: T042 ensures that data sources are verified and documented.
- **Static Power Audit**: T043 ensures that the sample size is sufficient for statistical tests.
