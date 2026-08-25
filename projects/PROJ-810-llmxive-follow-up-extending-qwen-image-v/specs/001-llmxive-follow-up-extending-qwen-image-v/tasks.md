# Tasks: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/`, `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/` at repository root
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

**Purpose**: Project initialization and basic structure. **CRITICAL**: Must complete before ANY code execution.

- [ ] T003a-init [P] Initialize Project Structure. **Logic**: Create all required directories in a single operation: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/`, `tests/`, `data/`, `data/results/`, `data/manual/`, `code/data/cache/`. **Deliverable**: All directory structures created. **Verification**: Run `ls -R projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/` to confirm all directories exist.
- [X] T003b [P] Create and execute `scripts/init_git.sh`. **Logic**: Script must run `git init` and verify `.git/HEAD` exists. **Deliverable**: `scripts/init_git.sh` and `.git/` directory.
- [ ] T004 [P] Create file `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/requirements.txt`. **Logic**: Content MUST match the plan's Technical Context exactly. **Deliverable**: Valid `requirements.txt` at `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/requirements.txt`. **Verification**: Run `grep -E "torch==2.2.0\+cpu|transformers==4.40.0" projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/requirements.txt` to ensure all patterns are present.
  **Required Content**:
  ```text
  torch==2.2.0+cpu
  transformers==4.40.0
  datasets==2.18.0
  scikit-learn==1.4.0
  opencv-python-headless==4.9.0.80
  paddleocr==2.7.3
  pyyaml==6.0.1
  scipy==1.12.0
  statsmodels==0.14.1
  pandas==2.2.1
  numpy==1.26.4
  matplotlib==3.8.3
  seaborn==0.13.2
  pillow==10.2.0
  pytest==8.1.1
  pytest-cov==5.0.0
  ```
- [X] T005 [P] Configure linting and formatting. **Logic**: Create `pyproject.toml` containing `[tool.black]` and `[tool.ruff]` sections with default project settings. **Constraint**: This task depends on T004 completion to ensure requirements.txt exists for dependency resolution in linting tools. **Deliverable**: `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections.

---

## Phase 0: Feasibility & Power Analysis (Pre-Execution)

**Purpose**: Critical pre-execution steps to determine sample size, model availability, and memory constraints.
**Status**: **Re-decomposed** from previous failure cycle. T000/T002 are implementation tasks; T000-run/T002b-run are the execution tasks that generate the missing artifacts.

### Sub-phase 0.1: Implementation (Parallel)
- [ ] T000a-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Power Calculation**. **Logic**: Write function that calculates minimum N required for power (d > 0.8) using `statsmodels.stats.power`. **Input**: Use effect_size `d=0.8` as defined in spec.md Assumptions. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` (Power Calculation function).
- [ ] T000b-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Status Logic**. **Logic**: Write function that checks `power < 0.8` and sets `status="INCONCLUSIVE"` instead of halting. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` (Status Logic function).
- [ ] T002a-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` -> **Memory Budget Function**. **Logic**: Write function that estimates peak RAM for VAE + OCR + Classifier. Configure chunk size or fallback to smaller N if > 7GB. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` (Memory Budget function).
- [ ] T002b-impl-6hr [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` -> **6-Hour Runtime Constraint Logic**. **Logic**: Write function that explicitly enforces the fixed runtime limit defined in SC-004. It must calculate estimated runtime based on N and hardware constraints. If estimated runtime > 6 hours, log a warning and set `status="runtime_warning"` but DO NOT reduce N, as the spec assumes the sample size is adequate. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` (6-Hour Constraint function).

### Sub-phase 0.2: Execution (Sequential - Must run after Implementation)
- [ ] T000-run [Feasibility] Execute Power Analysis. **Logic**: **Requires T000a-impl, T000b-impl completion**. Run `code/analysis/separability.py` with arguments `--mode=power` to generate `power_analysis.json`. **Constraint**: If power < 0.8, set `status="INCONCLUSIVE"` and allow pipeline to continue (do NOT halt). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/power_analysis.json` containing `N_required`, `effect_size`, `power`, and `status`.
- [ ] T002b-run [Feasibility] Execute 6-Hour Runtime Fallback Logic. **Logic**: **Requires T000-run, T002a-impl, T002b-impl-6hr completion**. If `N_required` (from T000-run) exceeds estimated runtime of approximately six hours, log a warning and set `status="runtime_warning"` (do NOT reduce N). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_fallback.json` with `N_final`, `estimated_runtime`, `status` (PASS/WARNING).
- [ ] T021b-check [Feasibility] Power Flag Check. **Logic**: **Requires T000-run completion**. Read `power_analysis.json`. If `status="INCONCLUSIVE"`, write a flag to `data/results/pipeline_status.json` setting `status="INCONCLUSIVE"` and `reason="Insufficient Power"` (do NOT set `halt=true`). **Constraint**: This task MUST run before any data processing tasks (Phase 2.5+). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/pipeline_status.json`.

---

## Phase 2.5: Data Ingestion & Sampling (Replaces Phase 7)

**Purpose**: Ensure reproducible data ingestion by downloading a static subset and creating a deterministic sample. **CRITICAL**: Must complete BEFORE Ground-Truth Extraction (Phase 2.2).
**Status**: **New**: Added to satisfy Constitution Principle I (Reproducibility) and Spec Assumptions.

### Sub-phase 2.5.1: Implementation (Parallel)
- [ ] T050-impl [P] [US1/US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` -> **Static Subset Download with Graceful Fallback**. **Logic**: Write script that attempts to download the specific subset ID referenced in the Qwen report from HuggingFace datasets to `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/raw/omnidoc_tokenbench.parquet`. **Constraint**: The `subset_id` MUST be read from `config.py`. If the specific subset is unavailable, the script MUST check for a local sample in `data/manual/local_sample.parquet`. If the local sample exists, use it as a fallback (authorized by spec Edge Cases). If neither exists, raise `DatasetNotFoundError` with a clear message: "Specific subset and local sample unavailable. Please provide a local sample or specify a valid subset." **NO** silent fallback to "train" split. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` (Static download function).
- [ ] T051-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` -> **Deterministic Sampling**. **Logic**: Write script that reads the static `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/raw/omnidoc_tokenbench.parquet` (or local sample) and creates a deterministic sample of N images (based on `N_final` from `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_fallback.json` - **Requires T002b-run completion to read N_final**) using a fixed random seed (fixed). **Constraint**: This task must wait for T002b-run to complete to ensure N_final is available. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` (Sampling function).

### Sub-phase 2.5.2: Execution (Sequential)
- [ ] T050-run [Feasibility] Execute Static Subset Download. **Logic**: **Requires T050-impl completion**. Download specific subset or local sample to `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/raw/omnidoc_tokenbench.parquet`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/raw/omnidoc_tokenbench.parquet`.
- [ ] T051-run [Feasibility] Execute Deterministic Sampling. **Logic**: **Requires T051-impl completion, T002b-run completion**. Generate sample file `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/sample_omnidoc.parquet`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/sample_omnidoc.parquet`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Sub-phase 2.1: Parallel Infrastructure (Reordered for Dependencies)
- [ ] T007-impl-load [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_wrapper.py` -> **CPU-Only VAE Loading** (Task 1.0). **Logic**: Implement CPU-only loading logic for `Qwen/Qwen-Image-VAE-2.0` ensuring no CUDA/GPU dependencies are invoked. **Constraint**: **MUST explicitly call `model.to('cpu')` and `torch.no_grad()`** before any inference. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_wrapper.py` with `load_vae_cpu()` function that enforces CPU device mapping and no_grad context.
- [ ] T007-impl-constraints [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_wrapper.py` -> **Resource Constraint Logic**. **Logic**: Implement explicit enforcement of the 2 vCPU, 7 GB RAM constraint defined in FR-002. **Constraint**: Must include `torch.set_num_threads(2)` and memory mapping logic to ensure resource limits are respected. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_wrapper.py` with `set_resource_constraints()` function.
- [ ] T008-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` -> **Ground-Truth Label Extraction** (Task 1.1). **Logic**: Extract "text"/"image" labels directly from OmniDoc-TokenBench ground-truth bounding box annotations using columns `bbox_x_min, bbox_y_min, bbox_width, bbox_height, modality_label`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` (Ground-Truth extraction function). **CRITICAL**: This is the primary source for evaluation in FR-003.

### Sub-phase 2.1.5: Sequential Execution (Must run after 2.1)
- [ ] T008-run [Feasibility] Execute Ground-Truth Label Extraction. **Logic**: **Requires T008-impl, T050-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/ground_truth_labels.parquet`.

### Sub-phase 2.2: Sequential Validation (Must run after 2.1.5 & 2.5)
- [ ] T009a-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Crop Extraction & Latent Encoding (Unlabeled)**. **Logic**: **Requires T007-impl-load, T007-impl-constraints, T051-run**. Crop regions strictly defined by bounding boxes. **Coordinate System**: Use [x_min, y_min, width, height] from parquet, convert to [x_min, y_min, x_max, y_max] for PIL cropping. **Image Format**: RGB. Encode crops using VAE from T007-impl. **Constraint**: Do NOT extract labels for training; only encode the image crops. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` (Crop & Encode function).
- [ ] T009b-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Prepare Evaluation Labels**. **Logic**: **Requires T008-run**. Prepare the ground-truth labels from `ground_truth_labels.parquet` for use ONLY in evaluation. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` (Label preparation function).
- [ ] T009a-run [Feasibility] Execute Crop Extraction & Latent Encoding. **Logic**: **Requires T009a-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/latent_vectors_unlabeled.parquet`.
- [ ] T043-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/checksums.py` -> **Artifact Checksumming**. **Logic**: Generate SHA-256 checksums for all files in data/. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/checksums.py`.
- [ ] T043-run [Feasibility] Execute Artifact Checksumming. **Logic**: **Requires T043-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/checksums_all.json`.

### Sub-phase 2.3: Sequential Validation & Global Checks (Must run after 2.2)
- [X] T016 [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_wrapper.py` CPU fallback logic in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_vae_loader.py`. **Logic**: **Requires T007-impl-load completion**. **Deliverable**: Unit tests.
- [X] T017 [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` region extraction in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_preprocess.py`. **Logic**: **Requires T008-impl completion**. **Deliverable**: Unit tests.
- [X] T015 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` checksum validation in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_download.py`
- [X] T018 [US1] Integration test for end-to-end encoding pipeline on sample data in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/integration/test_encoding_pipeline.py`. **Logic**: **Requires T008-run, T009a-run completion**. **Deliverable**: Integration tests.

---

## Phase 3: User Story 1 - Latent Space Disentanglement Analysis (Priority: P1) 🎯 MVP

- [ ] T022a-impl [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Permutation Test & Classification**. **Logic**: **Requires T000-run, T009a-run completion**. Check `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/power_analysis.json`; if `status="INCONCLUSIVE"`, skip execution and write "inconclusive" result. Train Linear SVM/LogReg on latent vectors from `latent_vectors_unlabeled.parquet` using labels **ONLY** from `ground_truth_labels.parquet` for evaluation. Compute accuracy/F1. Perform Permutation Test (N=1000): Shuffle labels N times, retrain classifier, record accuracy distribution. Compute empirical p-value using a permutation-based estimation of the tail probability, consistent with established non-parametric significance testing frameworks (e.g., Good; Phipson & Smyth, 2010). **Crucially**: Compute mean vectors for text and image clusters from `latent_vectors_unlabeled.parquet` and `ground_truth_labels.parquet` and save them to `data/interim/centroids.json` to serve as input for US2. **Constraint**: Must explicitly write results to disk. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/permutation_test_results.json` containing `empirical_p_value`, `distribution`, `observed_accuracy`, `f1_score`, `status` (PASS/INCONCLUSIVE) AND `data/interim/centroids.json`.
- [ ] T022a-run [US1] Execute Permutation Test & Classification. **Logic**: **Requires T022a-impl completion**. Execute the permutation loop defined in T022a-impl to generate `permutation_test_results.json` and `centroids.json`. **Deliverable**: `permutation_test_results.json` and `centroids.json`.
- [ ] T022a-report [US1] Generate Separability Report. **Logic**: **Requires T022a-run completion**. Read `permutation_test_results.json` and `power_analysis.json`. Write `separability_report.json` explicitly stating the 'PASS/INCONCLUSIVE' status and the specific power value for SC-001 verification. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/separability_report.json`.
- [ ] T024-impl [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **PCA Visualization**. **Logic**: Reduce latent vectors to 2D using PCA. Plot text vs image clusters. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/pca_plot.png`.
- [ ] T024-run Execute PCA Visualization. **Logic**: **Requires T024-impl completion**. **Deliverable**: `pca_plot.png`.
- [ ] T024-verify [US1] Validate PCA Cluster Distinctness. **Logic**: **Requires T024-run completion**. **Constraint**: Visual inspection only. If clusters appear overlapping, flag `status="INCONCLUSIVE"` in `pca_validation.json` and require manual review. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/pca_validation.json`.

---

## Phase 4: User Story 2 - Zero-Shot Semantic Editing via Vector Arithmetic (Priority: P2)

- [ ] T025-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/editing.py` -> **Vector Arithmetic**. **Logic**: **Requires T022a-run completion**. Compute centroids for text/image. Implement $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$. **Input**: Source centroids from `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/centroids.json`. **Deliverable**: `code/models/editing.py`.
- [ ] T026-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Baseline Reconstruction**. **Logic**: Encode and decode original image to create baseline. **Deliverable**: `data/interim/baseline_reconstructions/`.
- [ ] T027-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Masked SSIM**. **Logic**: Compute SSIM between edited and baseline, masking out text regions using bounding boxes. **Deliverable**: `data/results/ssim_scores.json`.
- [ ] T028-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Keypoint Matching**. **Logic**: Detect SIFT/ORB keypoints in non-text regions. Match between edited and baseline. Compute score as ratio of inlier matches to total matches. **Constraint**: Compare score against 0.80. If score < 0.80, set `hypothesis_rejected=true` and `failure_reason="VAE texture artifacts"` in output JSON. **Deliverable**: `data/results/keypoint_scores.json`.
- [ ] T028b-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Failure Attribution Logic**. **Logic**: **Requires T027-run, T028-run completion**. Check if SSIM < 0.85 AND Keypoint Score >= 0.80. If true, set `failure_reason="VAE texture artifacts"`. If both fail, set `failure_reason="Layout distortion"`. **Deliverable**: `data/results/editing_failure_analysis.json`.
- [ ] T029-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **OCR Verification**. **Logic**: Run PaddleOCR on edited text regions. Compare to target string. **Deliverable**: `data/results/ocr_accuracy.json`.
- [ ] T030-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Per-Image Latency Monitor**. **Logic**: Wrap editing pipeline to measure time per image. **Constraint**: If any image takes > 60 seconds, raise `LatencyExceededError` and log the specific image ID. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` (Latency monitoring function).
- [ ] T032-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Manual Verification Fallback**. **Logic**: **Requires T029-run completion**. If OCR accuracy < 95%, randomly sample a small subset of failed samples using a fixed seed (a deterministic value). **Constraint**: Read `SAMPLE_SIZE` from `config.py`. Logic: `itertools.islice(random.sample(..., k=min(SAMPLE_SIZE, count)))`. The specific value to remove/generalize: 'SAMPLE_SIZE' **Schema**: Generate `data/manual/verification_queue.csv` with columns: `sample_id`, `reason`, `ocr_score`, `target_text`. **State Update**: Update `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/pipeline_status.json` to set `manual_review_required=true` and append the CSV path to a `review_queue` array. **Deliverable**: `data/manual/verification_queue.csv` and updated `pipeline_status.json`.
- [ ] T033b-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Manual Verification Resolution**. **Logic**: **Requires T032-run completion**. Read `verification_queue.csv`. Allow manual update of `verification_status` column (e.g., 'verified', 'failed'). Update `pipeline_status.json` to set `manual_review_required=false` if all samples are resolved. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` (Resolution function).
- [ ] T025-run Execute Vector Arithmetic. **Logic**: **Requires T025-impl completion**. **Deliverable**: Edited images in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/edited_images/` with naming convention `edited_{sample_id}.png`.
- [ ] T026-run [US2] Execute Baseline Reconstruction. **Logic**: **Requires T026-impl completion**. Generate baseline images for comparison. **Deliverable**: Baseline images in `data/interim/baseline_reconstructions/`.
- [ ] T027-run Execute Masked SSIM. **Logic**: **Requires T027-impl completion**. **Deliverable**: `ssim_scores.json`.
- [ ] T028-run [US2] Execute Keypoint Matching. **Logic**: **Requires T028-impl completion, T026-run completion**. Execute Keypoint Matching using baseline images from T026-run to compute the score. **Constraint**: Baseline images from T026-run are required to compute the Keypoint Matching Score. **Deliverable**: `keypoint_scores.json`.
- [ ] T028b-run Execute Failure Attribution. **Logic**: **Requires T028b-impl completion**. **Deliverable**: `editing_failure_analysis.json`.
- [ ] T029-run Execute OCR Verification. **Logic**: **Requires T029-impl completion**. **Deliverable**: `ocr_accuracy.json`.
- [ ] T030-run Execute Per-Image Latency Monitor. **Logic**: **Requires T030-impl completion**. **Deliverable**: `latency_report.json`.
- [ ] T032-run Execute Manual Verification Fallback. **Logic**: **Requires T032-impl completion**. **Deliverable**: `verification_queue.csv` and updated `pipeline_status.json`.
- [ ] T033b-run Execute Manual Verification Resolution. **Logic**: **Requires T033b-impl completion**. **Deliverable**: Updated `pipeline_status.json` (manual_review_required=false if resolved).

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

- [ ] T033-impl [P] [US3] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/stats.py` -> **Sensitivity Analysis**. **Logic**: Sweep classification threshold. Report FPR/FNR variation. **Deliverable**: `data/results/sensitivity_analysis.json`.
- [ ] T034a-impl [P] [US3] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/stats.py` -> **P-Value Aggregation**. **Logic**: **Requires T022a-run completion**. Collect p-values from T022a-run (accuracy AND F1-score) into a single JSON file. **Constraint**: Explicitly include p-values for 'accuracy' and 'F1-score' as distinct entries. **Constraint**: The p-values are generated by the execution tasks (T022a-run) which produce `permutation_test_results.json`. **Deliverable**: `data/results/aggregated_p_values.json`.
- [ ] T034-impl [P] [US3] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/stats.py` -> **Bonferroni Correction**. **Logic**: Apply Bonferroni correction to p-values from `aggregated_p_values.json`. **Deliverable**: `data/results/corrected_p_values.json`.
- [ ] T033-run Execute Sensitivity Analysis. **Logic**: **Requires T033-impl completion**. **Deliverable**: `sensitivity_analysis.json`.
- [ ] T034a-run [US3] Execute P-Value Aggregation. **Logic**: **Requires T034a-impl completion, T022a-run completion**. Collect p-values from the artifacts generated by T022a-run. **Deliverable**: `aggregated_p_values.json`.
- [ ] T034-run Execute Bonferroni Correction. **Logic**: **Requires T034a-run completion**. **Deliverable**: `corrected_p_values.json`.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T040-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/versioning.py` -> Versioning Mechanism. **Logic**: Compute SHA-256 of artifacts, update state file. **Deliverable**: `code/utils/versioning.py`.
- [ ] T041-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/main.py` -> Orchestration. **Logic**: Chain all tasks in dependency order. **Deliverable**: `code/main.py`.
- [ ] T042b-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/runtime_monitor.py` -> **Final Runtime Monitor**. **Logic**: Monitor cumulative runtime of the full pipeline. **Constraint**: MUST compare cumulative runtime against the -hour threshold defined in SC-004. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/runtime_monitor.py` with `check_runtime_limit()` function.
- [ ] T042b-run Execute Final Runtime Monitor. **Logic**: **Requires T042b-impl completion**. **Deliverable**: `data/results/runtime_monitor.log` containing cumulative runtime and a PASS/FAIL status against the 6-hour limit.
- [X] T044 [P] Final Integration Test. **Logic**: Run full pipeline on a small sample. Verify all outputs exist. **Deliverable**: `data/results/final_report.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Ingestion (Phase 2.5)**: Must complete BEFORE Foundational Phase 2.2 (Ground-Truth Extraction)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Data Ingestion
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence