# Tasks: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Input**: Design documents from `/specs/001-llmxive-vae-geometric-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T003a-code [P] Create `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/` directory
- [ ] T003a-tests [P] Create `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/` directory
- [ ] T003a-data [P] Create `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/` directory
- [ ] T003a-results [P] Create `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/` directory
- [ ] T003a-manual [P] Create `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/manual/` directory
- [ ] T003a-cache [P] Create `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/cache/` directory
- [ ] T003b [P] Initialize git repository (if not already initialized)
- [ ] T003c [P] Create `.gitignore` for Python/ML artifacts (`.pyc`, `__cache__`, `data/raw/`, `data/interim/`)
- [ ] T004 [P] Create file `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/requirements.txt` with the following content:
```text
torch==2.2.0+cpu
transformers==4.40.0
datasets==2.18.0
scikit-learn==1.4.0
opencv-python-headless==4.9.0.80
paddleocr==2.7.3
pyyaml==6.0.1
pandas==2.2.1
numpy==1.26.4
matplotlib==3.8.3
seaborn==0.13.2
pillow==10.2.0
pytest==8.1.1
pytest-cov==5.0.0
statsmodels==0.14.1
```
- [ ] T005 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 0: Feasibility & Power Analysis (Pre-Execution)

**Purpose**: Critical pre-execution steps to determine sample size, model availability, and memory constraints.
**Status**: **Re-decomposed** from previous failure cycle. T000/T002 are implementation tasks; T000b/T002b are the execution tasks that generate the missing artifacts.

### Sub-phase 0.1: Implementation (Parallel)
- [ ] T000-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Power Analysis. **Logic**: Calculate minimum N required for power (d > 0.8) using `statsmodels.stats.power`. **Input**: Use effect_size `d=0.8` as defined in spec.md Assumptions. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/power_analysis.json` containing `N_required`, `effect_size`, `power`, and `N_audit`. **Constraint**: MUST include logic to check `power < 0.8` and set `status="INCONCLUSIVE"` in the output JSON to satisfy SC-001/US-01.
- [ ] T002-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/memory.py` -> Memory Budget Check (Task 0.3). **Logic**: Estimate peak RAM for VAE + OCR + Classifier. Configure chunk size or fallback to smaller N if > 7GB. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/memory_budget.json` with `chunk_size`, `max_samples`, `fallback_strategy`, `estimated_N`.

### Sub-phase 0.2: Execution (Sequential - Must run after Implementation)
- [ ] T000-run [Feasibility] Execute Power Analysis. **Logic**: **Requires T000-impl completion**. Run `code/analysis/separability.py` with arguments `--mode=power` to generate `power_analysis.json`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/power_analysis.json`.
- [ ] T002b-run [Feasibility] Execute Runtime Fallback Logic. **Logic**: **Requires T000-run and T002-impl completion**. If `N_required` (from T000-run) exceeds estimated runtime of approximately six hours or `max_samples` (from T002-impl), reduce N to `N_fallback` and flag `runtime_inconclusive` status. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_fallback.json` with `N_final`, `estimated_runtime`, `status` (PASS/INCONCLUSIVE).

### Sub-phase 0.3: Cleanup
- [ ] T001-removed [Removed] **Removed**: T001 logic merged into T002b-run. **Reason**: T001's original logic (Memory Budget Check) was merged into T002b-run to avoid duplication. This task entry is retained for historical tracking only.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Sub-phase 2.1: Parallel Infrastructure
- [ ] T006-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` to fetch `OmniDoc-TokenBench` dataset. **Logic**: Resolve specific subset ID from Qwen-Image-VAE-2.0 report reference. **Constraint**: If subset ID not found, load local sample from `data/local_sample.parquet` if exists, else raise `DatasetNotFoundError` with schema `{error_code, message}`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py`.
- [ ] T006a-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/verified_datasets.py` -> Verified Datasets Block. **Logic**: Create `verified_datasets.md` block with canonical URLs and checksums for all datasets used. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/specs/001-llmxive-vae-geometric-analysis/verified_datasets.md`.
- [ ] T006b-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/reference_validator.py` -> Reference-Validator Agent. **Logic**: Parse `research.md` and `spec.md`, extract URLs, cross-reference against `verified_datasets.md`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/reference_validator.py`.
- [ ] T006b-run [P] Execute Reference-Validator. **Logic**: **Requires T006a-impl completion**. Run the validator against current artifacts and update state file with verification status. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/verification_status.json`.
- [ ] T007-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_loader.py` -> **CPU-Only VAE Loading** (Task 1.0). **Logic**: Implement CPU-only loading logic for `Qwen/Qwen-Image-VAE-2.0` ensuring no CUDA/GPU dependencies are invoked. **Constraint**: Verify exact model ID `Qwen/Qwen-Image-VAE-2.0` exists on HuggingFace before loading. **Sub-task**: Implement `torch.cuda.is_available()` assertion and fallback mechanism to reduce N if CPU memory limits are exceeded. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_loader.py` with `load_vae_cpu()` function.
- [ ] T008-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` -> **Ground-Truth Label Extraction** (Task 1.1). **Logic**: Extract "text"/"image" labels directly from OmniDoc-TokenBench ground-truth bounding box annotations using columns `bbox_x_min, bbox_y_min, bbox_width, bbox_height, modality_label`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/ground_truth_labels.parquet` (region_id, modality_label, bbox). **CRITICAL**: This is the primary source for evaluation in FR-003.
- [ ] T008b-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` -> **Heuristic Label Derivation** (Task 1.2). **Logic**: Derive "text"/"image" labels using OCR density (`char_count / (bbox_width * bbox_height) > 0.05`) and aspect ratio (`width / height > 2.0`) from **ground-truth bounding box fields** (bbox_width, bbox_height). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/heuristic_labels.csv`. **Note**: **Do not use for primary evaluation**; strictly for sanity checks. **Constraint**: MUST NOT be used for training or evaluation. **Explicit Exclusion**: `heuristic_labels.csv` must be excluded from `eval_labels.parquet` generation in T021.
- [ ] T012 [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/logging.py` for structured logging and error tracking
- [ ] T013 [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/metrics.py` with wrappers for Masked SSIM and LPIPS (CPU-safe)
- [ ] T014 [P] Create directory `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/cache/` for intermediate latent vector storage

### Sub-phase 2.2: Sequential Validation (Must run after 2.1)
- [ ] T006-run [Feasibility] **Re-executed**: Run Dataset Download. **Logic**: **Requires T006-impl and T002b-run completion**. Fetch dataset using `N_final` from `runtime_fallback.json`. **Constraint**: If download fails, create `data/results/dataset_error.json` with error code and message. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/raw/omnidoc_tokenbench.parquet` and `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/checksum.json`.
- [ ] T008-run [Feasibility] **Re-executed**: Run Ground-Truth Label Extraction. **Logic**: **Requires T008-impl and T006-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/ground_truth_labels.parquet`.
- [ ] T008b-run [Feasibility] **Re-executed**: Run Heuristic Label Derivation. **Logic**: **Requires T008b-impl and T006-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/heuristic_labels.csv`.
- [ ] T009-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Crop Extraction & Latent Encoding** (Task 1.3). **Logic**: **Requires T007-impl, T008-impl, T002b-run completion**. Load raw images from T006-run and bounding boxes from T008-run. Crop regions strictly defined by bounding boxes. Encode crops using VAE from T007-impl. Process in chunks defined by `chunk_size` in `data/results/memory_budget.json`. **Constraint**: Output MUST be `latent_vectors_unlabeled.parquet` containing only features (no labels). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/latent_vectors_unlabeled.parquet`.
- [ ] T009-run [Feasibility] Execute Crop Extraction & Latent Encoding. **Logic**: **Requires T009-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/latent_vectors_unlabeled.parquet`.
- [ ] T010-impl [Feasibility] **Re-executed**: Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` -> Manual Audit Logic (Task 1.4). **Logic**: **Requires T008b-run completion**. Randomly sample N_audit regions (seed=42, size=N_audit from T000-run) from `heuristic_labels.csv`. Compare against manual labels in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/manual/audit_labels.csv` (schema: region_id, human_label). **Constraint**: Heuristics MUST NOT be used for training; strictly for sanity checks. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/label_audit.json` with `agreement_rate`, `status` (PASS/FAIL).
- [ ] T043-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/checksums.py` -> **Artifact Checksumming**. **Logic**: Generate SHA-256 checksums for all files in `data/` (raw, interim, processed). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/checksums_all.json`.
- [ ] T043-run [Feasibility] Execute Artifact Checksumming. **Logic**: **Requires T006-run, T008-run, T009-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/checksums_all.json`.
- [ ] T042b-impl [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/runtime.py` -> **Runtime Monitoring & Early Termination**. **Logic**: **Must run DURING execution of Phases 3 & 4**. Monitor cumulative runtime. **Constraint**: If cumulative runtime exceeds `threshold_seconds=21600`, **raise `RuntimeExceededError`** to halt the pipeline immediately. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_monitor.log`.
- [ ] T042b-run [Feasibility] Execute Runtime Monitoring. **Logic**: **Requires T042b-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_monitor.log`.

### Sub-phase 2.3: Testing (Parallel)
- [ ] T015 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` checksum validation in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_download.py`
- [ ] T016 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_loader.py` CPU fallback logic in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_vae_loader.py`
- [ ] T017 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` region extraction in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_preprocess.py`
- [ ] T018 [P] [US1] Integration test for end-to-end encoding pipeline on sample data in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/integration/test_encoding_pipeline.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Latent Space Disentanglement Analysis (Priority: P1) 🎯 MVP

**Goal**: Encode document image regions into latent vectors and verify linear separability between text and image modalities using a lightweight classifier.

**Independent Test**: Run encoding and classification on a sampled subset; report accuracy ≥ 90% and F1 ≥ 0.90 against ground-truth labels.

### Sub-phase 3.1: Parallel Implementation
- [ ] T019 [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Triviality Check (Task 2.1) on raw pixel stats. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/triviality_check.json`.

### Sub-phase 3.2: Sequential Execution (Must run after 3.1)
- [ ] T021-impl [US1] **Re-executed**: Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Data Splitting Logic. **Logic**: **Requires T009-run and T008-run completion**. Split `latent_vectors_unlabeled.parquet` into `train_features.parquet` (strictly unlabeled features) and `eval_labels.parquet` (ground truth from T008-run). **Constraint**: `eval_labels.parquet` MUST be derived **STRICTLY** from T008-run (ground-truth bounding boxes); **explicitly EXCLUDE** heuristic labels (T008b-run). **Split Logic**: 80/20 split, seed=42. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/train_features.parquet` and `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/eval_labels.parquet`.
- [ ] T022 [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/classifier.py` -> Train Linear SVM on full latent dimensionality (Task 2.3). **Logic**: **Load ONLY `train_features.parquet` for `model.fit()`; inject `eval_labels.parquet` ONLY for post-fit metric calculation.** **Constraint**: MUST NOT consume heuristic labels (T008b) for training or evaluation. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us1_metrics.json` with `accuracy`, `f1_score`, `model_path`, `optimal_boundary`.
- [ ] T023-impl [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Permutation Test (1000 iterations) for p-value < 0.05 (Task 2.4). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/permutation_pvalue.json` with `p_value`, `observed_accuracy`, `null_distribution_mean`.
- [ ] T023b-run [P] [US1] Execute Permutation Test Visualization. **Logic**: **Requires T023-impl completion**. Generate null distribution plot and statistical report. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/permutation_report.pdf` and `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/permutation_pvalue.json`.
- [ ] T024-impl [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Threshold Sweep for Optimal Boundary and Sensitivity Metrics (Task 2.5). **Logic**: Sweep thresholds to find the boundary that maximizes F1. **Constraint**: Output MUST include full list of `{threshold, fpr, fnr}` in `us1_sweep_metrics.json` to satisfy FR-008 and SC-005. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us1_threshold_sweep.json` with `optimal_boundary` and `metrics_at_boundary`. **AND** `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us1_sweep_metrics.json` containing the full sweep data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Zero-Shot Semantic Editing via Vector Arithmetic (Priority: P2)

**Goal**: Perform linear vector arithmetic on latent representations to swap text content while preserving layout.

**Independent Test**: Compute $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$, decode, and verify text change with Masked SSIM ≥ 0.85 and OCR accuracy ≥ 95%.

### Sub-phase 4.1: Parallel Implementation
- [ ] T025 [P] [US2] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/metrics.py` Masked SSIM calculation in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_metrics.py`
- [ ] T026 [P] [US2] Integration test for vector arithmetic and decoding in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/integration/test_editing.py`
- [ ] T027 [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> Linearity Verification (Task 3.1) with small $\alpha$ steps. **Logic**: Compute linearity metric as **R-squared of linear fit** for $\alpha$ range **from the lower bound to the upper bound** with steps of **0.01**. **Constraint**: If linearity metric is low, MUST HALT pipeline or FLAG as `INVALID_GEOMETRY` in output. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/linearity_check.json` with `is_linear`, `message`, `metric_value`.
- [ ] T028 [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> Centroid computation for text/image clusters (Task 3.2). **Dependency**: Requires T009-run (Latent Vectors) and T008-run (Ground Truth). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/centroids.json`.
- [ ] T031a-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> **Mask Creation Logic** (Task 3.4a). **Logic**: Implement `create_non_text_mask` function that creates a binary mask from image dimensions (H, W) by setting bbox regions (from T008-run) to 0 and non-bbox to 1. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` with `create_non_text_mask` function.

### Sub-phase 4.2: Sequential Execution (Must run after 4.1)
- [ ] T029-impl [US2] **Re-executed**: Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> Vector Arithmetic ($z_{new}$ calculation) logic. **Logic**: **Requires T027 and T028 completion**. **Constraint**: If T027 `is_linear` is false, **HALT** pipeline and flag as `INVALID_EDIT`. **Specific Logic**: Retrieve $z_{doc}$ for the source document. Retrieve $\mu_{text\_old}$ from the text regions of the source document (from T028). Retrieve $\mu_{text\_new}$ from a reference set of text regions or generate via encoding a synthetic text image if reference unavailable. **Input**: Accept a target text string as input, generate its latent representation (or use a pre-computed mean from a reference set), and perform the arithmetic. Compute $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_arithmetic.json`.
- [ ] T029-run [US2] Execute Vector Arithmetic. **Logic**: **Requires T029-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_arithmetic.json`.
- [ ] T030-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> Decoding and Masked SSIM evaluation (Task 3.3). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_ssim.json` with `ssim`, `baseline_path`, `edited_path`.
- [ ] T030-run [P] [US2] Execute SSIM Evaluation. **Logic**: **Requires T030-impl and T029-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_ssim.json`.
- [ ] T030a-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/sensitivity.py` -> **SSIM Significance Test** (Task 3.3b). **Logic**: Perform t-test or permutation test on SSIM scores to generate p-value. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_ssim_pvalue.json`.
- [ ] T030a-run [P] [US2] Execute SSIM Significance Test. **Logic**: **Requires T030a-impl and T030-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_ssim_pvalue.json`.
- [ ] T031b-impl [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> **Keypoint Matching Score** (Task 3.4, FR-010). **Logic**: **Requires T031a-impl completion**. Detect keypoints (SIFT/ORB) in **non-text regions** (masked using `create_non_text_mask` from T031a-impl) of baseline and edited images. Match and compute score. **Constraint**: Must explicitly mask text regions before detection. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_keypoint_score.json` with `keypoint_score` (must be ≥ 0.80).
- [ ] T031c-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/sensitivity.py` -> **Keypoint Significance Test** (Task 3.4b). **Logic**: Perform t-test or permutation test on Keypoint scores to generate p-value. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_keypoint_pvalue.json`.
- [ ] T031c-run [P] [US2] Execute Keypoint Significance Test. **Logic**: **Requires T031c-impl and T031b-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_keypoint_pvalue.json`.
- [ ] T032 [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing.py` -> OCR validation and Manual Verification Fallback (Task 3.5). **Logic**: Run PaddleOCR. If accuracy < 95%, generate `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/manual/verification_queue.csv` with a set of random samples for manual review. **Sampling**: Randomly sample [deferred] of failed samples. **Schema**: `image_id, original_text, predicted_text, confidence`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us2_ocr.json` with `ocr_accuracy`, `verification_queue_path` (if applicable).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds and report statistical robustness with Bonferroni correction.

**Independent Test**: Verify stability of error rates across threshold sweeps and confirm p-values for distinct metrics with correction.

### Sub-phase 5.1: Sequential Execution (Must run after Phase 3/4)
- [ ] T034-impl [US3] **Re-executed**: Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/sensitivity.py` -> Robustness Verification (Task 3.1). **Logic**: **Requires T024-impl completion**. Consume full sweep metrics from T024-impl to calculate **variation in false-positive rates** specifically for SC-005. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us3_sensitivity.json` with `threshold`, `false_positive_rate`, `false_negative_rate`, `variation_metric`.
- [ ] T034-run [US3] Execute Robustness Verification. **Logic**: **Requires T034-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us3_sensitivity.json`.
- [ ] T035-impl [US3] **Re-executed**: Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/sensitivity.py` -> **Aggregate p-values and Bonferroni Correction** (Task 3.2 + 3.3). **Logic**: **Requires T034-run, T023-run, T030a-run, T031c-run completion**. **Aggregate**: Collect p-values from T023-run (`p_value`), T030a-run (`p_value`), and T031c-run (`p_value`). **Correction**: Apply Bonferroni or Holm-Bonferroni correction using `statsmodels.stats.multitest` to control family-wise error rate at α ≤ 0.05. **Constraint**: Include the permutation test p-value (T023) as the primary separability significance. **Note**: Accuracy/F1 are metrics, not p-values, and are excluded from this specific correction step as per spec interpretation. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us3_corrected_pvalues.json` with `raw_p_values`, `adjusted_p_values`, `significant_after_correction`.
- [ ] T035-run [US3] Execute Bonferroni Correction. **Logic**: **Requires T035-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us3_corrected_pvalues.json`.
- [ ] T036 [P] [US3] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/sensitivity.py` -> Power analysis reporting (inconclusive if power < 0.8) (Task 3.4). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/power_report.json` with `achieved_power`, `conclusion`, `limitation_text`, `N_actual`.
- [ ] T037 [P] [US3] Generate final statistical report to `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/us3_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T038 [P] Generate final research report compiling metrics, plots, and limitations in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/research.md`
- [ ] T039 [P] Update `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/quickstart.md` with execution instructions for the full pipeline
- [ ] T040 Run `pytest` with coverage to ensure all paths are tested
- [ ] T041 Validate `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/*.json` schemas against `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/contracts/output.schema.yaml`
- [ ] T042-impl [P] [Polish] **Re-executed**: Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/runtime.py` -> **Measure End-to-End Runtime** (Task 4.1). **Logic**: **Must run AFTER all pipeline tasks complete**. Measure total execution time of the full pipeline and compare against a predefined time threshold. **Constraint**: The threshold MUST be set to `threshold_seconds=21600` (6 hours) to capture extended temporal patterns without introducing excessive noise, as per SC-004. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_verification.json` with `total_runtime_seconds`, `threshold_seconds` (21600), `status` (PASS/FAIL).
- [ ] T042-run [P] [Polish] Execute Runtime Measurement. **Logic**: **Requires T042-impl and T042b-run completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_verification.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 0 (Feasibility)**: Depends on Phase 1 completion (T003a, T003b, T003c, T004, T005 must pass)
- **Foundational (Phase 2)**: Depends on Phase 0 completion (T000-run, T002b-run must pass) - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on centroids from US1 (T028)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Aggregates metrics from US1/US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download/preprocessing before encoding
- Encoding before classification/editing
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] in Sub-phase 2.1 can run in parallel
- All Testing tasks marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/data/download.py checksum validation in tests/unit/test_download.py"
Task: "Unit test for code/models/vae_loader.py CPU fallback logic in tests/unit/test_vae_loader.py"

# Launch preprocessing and encoding tasks together:
Task: "Implement code/data/preprocess.py -> Ground-Truth Label Extraction"
Task: "Implement code/analysis/separability.py -> Triviality Check on raw pixel stats"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 0: Feasibility (Ensure T000-run, T002b-run pass)
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
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
 - Developer A: User Story 1 (Disentanglement)
 - Developer B: User Story 2 (Editing)
 - Developer C: User Story 3 (Sensitivity)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (within their sub-phase)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All VAE operations must use chunked processing to stay within available RAM constraints.
- **Constraint**: No GPU/CUDA dependencies; fallback protocol must be triggered if model unavailable.
- **Critical Methodology**: Classifier training (T022) MUST use ONLY unlabeled features (from T009-run); labels are used ONLY for evaluation (from T008-run ground truth).
- **Critical Methodology**: Significance tests (T035-run) MUST apply Bonferroni/Holm-Bonferroni correction to the family of p-values from Permutation, SSIM, and Keypoint tests. Accuracy/F1 are metrics, not p-values, and are excluded from this specific correction.
- **Critical Methodology**: Keypoint Matching Score (T031c-run) is required for US-02 validation (FR-010) and must mask text regions (T031a-impl).
- **Critical Methodology**: Sensitivity sweep (T024-impl) must output full FPR/FNR metrics, not just optimal boundary.
- **Critical Methodology**: T034-run must consume T024-impl output to avoid duplication.
- **Critical Methodology**: T027 must report linearity metrics and flag invalid geometry; T029-run must halt if geometry is invalid.
- **Critical Methodology**: T000-run must halt if power < 0.8.
- **Critical Methodology**: T042b-impl must halt the pipeline if runtime exceeds 21600 seconds.
- **Critical Methodology**: T042-impl must report final status based on T042b-impl.
- **Note**: T001 has been removed as its logic was merged into T002b-run.
- **Note**: T020-impl has been removed and its logic merged into T009-impl to resolve artifact duplication.
- **Note**: T008b-impl is now sequential after T008-impl.
- **Note**: T029-impl is now sequential after T027 and T028.
- **Note**: T031b-impl is now sequential after T031a-impl.
- **Note**: T042b-impl and T042b-run are added for runtime monitoring.
- **Note**: T043-impl and T043-run are added for comprehensive checksumming.
- **Note**: T009-impl is added for explicit crop extraction and latent encoding.
- **Note**: T006-impl is updated with specific subset resolution and fallback logic.
- **Note**: T000-impl is updated with explicit effect_size value.
- **Note**: T008-impl is updated with explicit column names.
- **Note**: T009-impl is updated with explicit chunking strategy.
- **Note**: T029-impl is updated with explicit target text handling.
- **Note**: T032 is updated with explicit sampling strategy and schema.
- **Note**: T042-impl is updated with explicit threshold value.
- **Note**: T000-run is updated with explicit command arguments.
- **Note**: T006a-impl is updated with correct deliverable path.
- **Note**: T035-impl is updated with explicit p-value scope clarification.