# Tasks: llmXive follow-up: extending "DanceOPD: On-Policy Generative Field Distillation"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-danceopd-on/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per implementation plan in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/` including directories: `code/`, `code/utils/`, `code/data/`, `code/models/`, `code/metrics/`, `data/raw/`, `data/processed/`, `data/results/`, `models/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`.
- [ ] T001b [P] Create empty Python script files in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`: `main.py`, `00_data_generation.py`, `01_train_trees.py`, `02_evaluate_fidelity.py`, `03_versioning.py`.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/` including pinned dependencies: `torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `transformers`, `accelerate`, `pillow`, `scipy`, `torch-fidelity`, `pyyaml`, `pytest`.
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/config.py` to manage seeds, paths, and hyperparameters (including `TEACHER_WEIGHTS_PATH`).
- [ ] T005 [P] Create `code/utils/metrics.py` with stub functions `calculate_clip_score(image_path_1: str, image_path_2: str) -> float` and `calculate_fid(image_path_1: str, image_path_2: str) -> float` that raise `NotImplementedError`. These stubs allow the pipeline to run without crashing.
- [ ] T006 Create `code/03_versioning.py` to calculate SHA256 hashes for artifacts and update `state/`.
- [ ] T007 Setup data directories: `data/raw/`, `data/processed/`, `data/results/` in the project root.
- [ ] T008 Implement pre‑flight check script `code/utils/check_weights.py` that verifies existence and SHA256 checksum of user‑provided weights against `data/raw/weights_manifest.json`. If the manifest is missing, a file is missing, or checksum/size mismatches, exit with code 1. **If** a verified pre‑computed `data/raw/teacher_ground_truth.parquet` exists (checksum validated), the script may pass, allowing downstream tasks to use it; otherwise it aborts with a clear error.
- [ ] T009 Create JSON schemas for `TeacherRoutingDataset`, `InferenceResult`, and `DecisionTreeMetadata` in `specs/contracts/`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Teacher Routing Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of `(prompt_embedding, noise_level, routing_label, velocity_vector)` tuples by running the pre‑trained DanceOPD teacher model on sampled ImageNet‑1K and LAION‑400M prompts.

**Independent Test**: The system produces a CSV/Parquet file with ≥1,000 rows, valid expert identifiers, and consistent velocity vector dimensions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for data schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_data_schema.py`
- [ ] T011 [P] [US1] Integration test for data generation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_data_generation.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement data streaming logic in `code/_data_streaming.py` to perform a stratified random sample of images from ImageNet‑1K and LAION‑400M, writing raw batches to `data/raw/`. The script must monitor cumulative CPU time; if the 6‑hour limit is reached it must **save partial results** (e.g., current batches) and exit cleanly with status `partial`.
- [ ] T012b [P] [US1] Load the streamed samples from `data/raw/imageNet_samples.parquet` (and `data/raw/laion_samples.parquet`), assert `len(imageNet_samples) > 0` and `len(laion_samples) > 0`, and combine them into a unified list for downstream processing.
- [ ] T013a [US1] Implement teacher model loading and inference in `code/00_teacher_inference.py`. **Primary Path**: Attempt GPU inference to generate `teacher_ground_truth.parquet` from the streamed samples. **Fallback Path**: If GPU is unavailable, check for a verified `data/raw/teacher_ground_truth.parquet` (checksum validated against manifest). If found, load it; if not found, abort with a clear error indicating that GPU inference is required or a verified fallback must be provided. This task is the sole producer of the dataset or the gatekeeper for the verified fallback.
- [ ] T013b [US1] Detect undefined routing paths during inference, log the count, and **exclude** those samples from the final dataset (no fallback label assigned).
- [ ] T014 [US1] Implement logic in `code/00_data_extraction.py` to extract `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector` from inference outputs and stream them to `data/processed/teacher_routing_dataset.parquet`.
- [ ] T015 [US1] Add validation in `code/00_data_extraction.py` to ensure each `routing_label` matches a known expert field ID from the DanceOPD configuration.
- [ ] T016 [US1] Implement checksumming and versioning of the generated dataset using `code/03_versioning.py`.
- [ ] T016b [US1] Validate that `teacher_routing_dataset.parquet` contains samples from **both** ImageNet‑1K and LAION‑400M sources.
- [ ] T016c [US1] Record the number of excluded undefined‑route samples in `data/results/exclusion_log.json` and include this metadata in the dataset version record.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Static Decision Trees (Priority: P2)

**Goal**: Train Decision Tree classifiers with `max_depth` ranging from shallow to deep on the generated dataset to approximate routing labels and compute "Routing Consistency".

**Independent Test**: A tree with `max_depth=5` is saved and reports a reproducible validation accuracy on a held‑out test split.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Decision Tree training parameters in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_tree_training.py`
- [ ] T019 [P] [US2] Integration test for training loop and metadata schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_tree_training.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement data splitting logic (train/test) in `code/01_train_trees.py` consuming `data/processed/teacher_routing_dataset.parquet`. **Note**: This task depends on T014 completion and is NOT parallelizable; the [P] flag has been removed.
- [ ] T021 [US2] Implement a loop to train `DecisionTreeClassifier` (scikit‑learn, CPU) for `max_depth` values **ranging from 2 to 20** (inclusive) in `code/01_train_trees.py`.
- [ ] T022 [US2] Compute and log "Routing Consistency" (accuracy) for each depth against the test set.
- [ ] T023 [US2] Save each trained model to `models/trained_trees/` and generate a results table (`depth vs. accuracy`) saved to `data/results/tree_accuracy.csv`.
- [ ] T024 [US2] Validate model metadata against the schema from `specs/contracts/DecisionTreeMetadata.json` and update `state/` with model hashes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantify Fidelity Degradation and Statistical Significance (Priority: P3)

**Goal**: Execute CPU‑only inference using tree‑predicted routing, measure FID/CLIP for **all** samples, and perform statistical tests (bootstrap, paired t‑test) to determine significance of fidelity degradation.

**Independent Test**: The system calculates FID/CLIP for teacher vs. tree (depth=5) on the full dataset and outputs valid p‑values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for statistical test functions (bootstrap, t‑test) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_statistics.py`
- [ ] T027 [P] [US3] Integration test for full fidelity evaluation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_fidelity_evaluation.py`

### Implementation for User Story 3

- [ ] T005b [US3] Implement the actual CPU‑only CLIP Score (using `transformers`) and FID (using `torch-fidelity`) functions in `code/utils/metrics.py`, replacing the stubs from T005. These functions will be used by T028. **Note**: This task must complete before T028; it is NOT parallel to T028.
- [ ] T029 [US3] Implement CPU‑only Euler integrator in `code/models/inference.py`. The function accepts `velocity_vector`, `noise_level`, and `expert_type`, uses a fixed step size and step count, and invokes the appropriate expert field logic to generate an image. This module is the single source of truth for the integrator. **Note**: This task must complete before T028.
- [ ] T028 [US3] Implement logic in `code/02_evaluate_fidelity.py` to generate **all** images using two modes:
    1. **Tree‑Generated**: For each sample, predict the expert with the trained Decision Tree, re‑run that expert to obtain a fresh `velocity_vector`, and integrate (via `code/models/inference.py`) to produce an image.
    2. **Teacher‑Baseline**: For each sample, use the stored `routing_label` from the teacher dataset, re‑run the corresponding expert to obtain a fresh `velocity_vector`, and integrate to produce an image.
    Images are saved under `data/results/` with prefixes `tree_depth{D}_sample_{idx}.png` and `teacher_baseline_sample_{idx}.png`. **Note**: This task depends on T005b (metrics) and T029 (integrator) being complete.
- [ ] T030 [US3] Compute FID and CLIP Score **on the entire dataset** comparing Tree‑Generated images vs. Teacher‑Baseline images. Store results in `data/results/fidelity_metrics.csv`. Derive total degradation metrics (ΔFID, ΔCLIP) and write them to the same CSV.
- [ ] T030a [US3] Perform a bootstrap hypothesis test on the FID distribution. Increase the sample size by 10 samples per iteration until statistical power ≥ 0.8 **or** remaining runtime < 30 min; if the time budget would be exceeded, save current results to `data/results/partial_results.json` with `status: partial` and exit with code 2.
- [ ] T030c [US3] Perform a paired t‑test on per‑sample CLIP scores using the same power‑checking loop as Ta. Handle runtime limits identically.
- [ ] T031 [US3] After successful power checks, write final statistical test outputs (p‑values, confidence intervals) to `data/results/statistical_tests.json`.
- [ ] T032 [US3] Generate a summary report `data/results/fidelity_summary.md` that includes degradation metrics, statistical significance statements, and any partial‑result notes.
- [ ] T033 [US3] Implement a hard 6‑hour timeout using the `signal` module. On timeout **or** on early exit due to **statistical power insufficiency**, ensure all completed depth results and any partial metrics are persisted to `data/results/partial_results.json` with a `status: partial` flag.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` and `README.md`.
- [ ] T035 Code cleanup and refactoring in `code/`.
- [ ] T036 Performance optimization for data streaming and batch processing.
- [ ] T037 [P] Additional unit tests for edge cases (memory exhaustion, undefined routes) in `tests/unit/`.
- [ ] T038 Run `quickstart.md` validation to ensure end‑to‑end reproducibility.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: In Phase 5, T005b and T029 are independent prerequisites but must both complete before T028. T028 is NOT parallel to T005b or T029.
- **Note**: T020 in Phase 4 is NOT parallel; it depends on T014.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU‑only CI with minimal computational resources (limited CPU cores and RAM, ≤7 GB RAM, ≤6 hours total runtime). No CUDA, no 8‑bit/4‑bit quantization, no large model training.
- **Data Integrity**: No synthetic/fake input data allowed. All data must come from real sources (ImageNet/LAION via HF) or real teacher model inference.
- **File Separation**: Phase 3 tasks are split into `00_data_streaming.py`, `00_teacher_inference.py`, `00_data_extraction.py` to prevent merge conflicts. Phase 5 tasks are split into `02_evaluate_fidelity.py`, `models/inference.py`, `utils/metrics.py`, `statistics.py` for the same reason.
- **Statistical Validity**: T030a/T030c enforce hard stop if power < 0.8, with partial‑save logic.
- **Real Data Streaming**: T012 mandates streaming real data (ImageNet/LAION) rather than using synthetic fallbacks; if real fetch fails, the script MUST raise an error and NOT fall back to mock data.
- **Undefined Route Handling**: T013b explicitly excludes undefined routes rather than assigning fallback labels.
- **Timeout Logic**: T033/T033b implement a hard 6‑hour timeout using `signal.SIGALRM` to prevent CI hangs and ensure partial results are saved.
- **Teacher Inference**: T013a supports GPU execution or pre‑computed fallback to avoid impossible CPU‑only constraints.
- **Re‑generation Logic**: T029 explicitly re‑generates velocity vectors based on routing source (Tree vs Teacher) to measure full error propagation.
- **Dependency Correction**: T005b (metrics) must run before T028 (evaluation). T029 (integrator) must run before T028 (evaluation). T020 (splitting) must run after T014 (generation).