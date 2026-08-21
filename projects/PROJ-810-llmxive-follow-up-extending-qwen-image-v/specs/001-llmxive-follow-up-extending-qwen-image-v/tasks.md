---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Input**: Design documents from `/specs/[###-feature-name]/`
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
- [X] T003b [P] Create and execute `scripts/init_git.sh`. **Logic**: Script must run `git init` and verify `.git/HEAD` exists. **Deliverable**: `scripts/init_git.sh` and `.git/` directory.
- [ ] T003c [P] Create `.gitignore`. **Logic**: Must include patterns `data/raw/`, `data/interim/`, `__pycache__/`, `*.pyc`, `.env`, and `data/results/*.log`. **Deliverable**: `.gitignore` file.
- [ ] T004 [P] Create file `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/requirements.txt`. **Logic**: Content MUST match the plan's Technical Context exactly: `torch==2.2.0+cpu`, `transformers==4.40.0`, `datasets==2.18.0`, `scikit-learn==1.4.0`, `opencv-python-headless==4.9.0.80`, `paddleocr==2.7.3`, `pyyaml==6.0.1`, `pandas==2.2.1`, `numpy==1.26.4`, `matplotlib==3.8.3`, `seaborn==0.13.2`, `pillow==10.2.0`, `pytest==8.1.1`, `pytest-cov==5.0.0`. **Deliverable**: Valid `requirements.txt`.
- [X] T005 [P] Configure linting and formatting. **Logic**: Create `pyproject.toml` containing `[tool.black]` and `[tool.ruff]` sections with default project settings. **Deliverable**: `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections.

---

## Phase 0: Feasibility & Power Analysis (Pre-Execution)

**Purpose**: Critical pre-execution steps to determine sample size, model availability, and memory constraints.
**Status**: **Re-decomposed** from previous failure cycle. T000/T002 are implementation tasks; T000b/T002b are the execution tasks that generate the missing artifacts.

### Sub-phase 0.1: Implementation (Parallel)
- [ ] T000-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Power Analysis. **Logic**: Write script that calculates minimum N required for power (d > 0.8) using `statsmodels.stats.power`. **Input**: Use effect_size `d=0.8` as defined in spec.md Assumptions. **Constraint**: MUST include logic to check `power < 0.8` and set `status="INCONCLUSIVE"` in the output JSON. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` (Power Analysis function).
- [ ] T002-impl [P] [Feasibility] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` -> Memory Budget Check (Task 0.3). **Logic**: Write script that estimates peak RAM for VAE + OCR + Classifier. Configure chunk size or fallback to smaller N if > 7GB. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` (Memory Budget function).

### Sub-phase 0.2: Execution (Sequential - Must run after Implementation)
- [ ] T000-run [Feasibility] Execute Power Analysis. **Logic**: **Requires T000-impl completion**. Run `code/analysis/separability.py` with arguments `--mode=power` to generate `power_analysis.json`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/power_analysis.json` containing `N_required`, `effect_size`, `power`, and `status`.
- [ ] T021b-check [Feasibility] Power Flag Check. **Logic**: **Requires T000-run completion**. Read `power_analysis.json`. If `status="INCONCLUSIVE"`, write a flag to `data/results/pipeline_status.json` setting `halt=true` and `reason="Insufficient Power"`. **Constraint**: This task MUST run before any data processing tasks (Phase 2.5+). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/pipeline_status.json`.
- [ ] T002b-run [Feasibility] Execute Runtime Fallback Logic. **Logic**: **Requires T002-impl completion**. If `N_required` (from T000-run) exceeds estimated runtime of approximately six hours or `max_samples` (from T002-impl), reduce N to `N_fallback` and flag `runtime_inconclusive` status. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_fallback.json` with `N_final`, `estimated_runtime`, `status` (PASS/INCONCLUSIVE).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Sub-phase 2.1: Parallel Infrastructure (Reordered for Dependencies)
- [ ] T006c-impl [Validation] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/citation_validator.py` -> **Spec Citation Validator** (Task 0.2). **Logic**: Write script that parses `spec.md` to extract all external URLs. For each URL, perform HTTP HEAD request to verify reachability, compute SHA-256 checksum, and verify title-token-overlap >= 0.7 with the cited source. **Constraint**: No dependencies. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/citation_validator.py`.
- [ ] T007-impl Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_loader.py` -> **CPU-Only VAE Loading** (Task 1.0). **Logic**: Implement CPU-only loading logic for `Qwen/Qwen-Image-VAE-2.0 ` ensuring no CUDA/GPU dependencies are invoked. **Constraint**: **MUST explicitly call `model.to('cpu')` and `torch.no_grad()`** before any inference. **Sub-task**: Implement `torch.cuda.is_available()` assertion and fallback mechanism to reduce N if CPU memory limits are exceeded. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_loader.py` with `load_vae_cpu()` function that enforces CPU device mapping and no_grad context.
- [ ] T008-impl Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` -> **Ground-Truth Label Extraction** (Task 1.1). **Logic**: Extract "text"/"image" labels directly from OmniDoc-TokenBench ground-truth bounding box annotations using columns `bbox_x_min, bbox_y_min, bbox_width, bbox_height, modality_label`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` (Ground-Truth extraction function). **CRITICAL**: This is the primary source for evaluation in FR-003.
- [ ] T008b-impl Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` -> **Heuristic Label Derivation** (Task 1.2). **Logic**: Derive "text"/"image" labels using OCR density (`char_count / (bbox_width * bbox_height) > 0.05`) and aspect ratio (`width / height > 2.0`) from **ground-truth bounding box fields** (bbox_width, bbox_height). **Unit Definition**: `char_count` is the number of characters detected by OCR within the bounding box; the A threshold of a small magnitude is characters per pixel.. **Constraint**: **MUST rely on `paddleocr==2.7.3 `** as defined in `requirements.txt` (T004) for reproducibility. **Data Isolation**: This artifact (`heuristic_labels.csv`) is strictly for logging and sanity checks. It MUST NOT be read by T022-impl or T028-impl. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` (Heuristic derivation function).
- [X] T015 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` checksum validation in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_download.py`
- [X] T016 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/vae_loader.py` CPU fallback logic in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_vae_loader.py`
- [X] T017 [P] [US1] Unit test for `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/preprocess.py` region extraction in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/unit/test_preprocess.py`
- [X] T018 [P] [US1] Integration test for end-to-end encoding pipeline on sample data in `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/tests/integration/test_encoding_pipeline.py`

### Sub-phase 2.2: Sequential Validation (Must run after 2.1)
- [ ] T008-run [Feasibility] **Re-executed**: Run Ground-Truth Label Extraction. **Logic**: **Requires T008-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/ground_truth_labels.parquet`.
- [ ] T008b-run [Feasibility] **Re-executed**: Run Heuristic Label Derivation. **Logic**: **Requires T008b-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/heuristic_labels.csv`.
- [ ] T009-impl Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Crop Extraction & Latent Encoding. **Logic**: **Requires T007-impl, T008-run**. Crop regions strictly defined by bounding boxes. **Coordinate System**: Use [x_min, y_min, width, height] from parquet, convert to [x_min, y_min, x_max, y_max] for PIL cropping. **Image Format**: RGB. Encode crops using VAE from T007-impl. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` (Crop & Encode function).
- [ ] T009-run Execute Crop Extraction & Latent Encoding. **Logic**: **Requires T009-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/latent_vectors_unlabeled.parquet`.
- [ ] T010-impl Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> Manual Audit Logic (Task 1.4). **Logic**: Randomly sample regions from `heuristic_labels.csv`. Compare against manual labels in `data/manual/audit_labels.csv`.
- [ ] T043-impl Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/checksums.py` -> Artifact Checksumming. **Logic**: Generate SHA-256 checksums for all files in data/.
- [ ] T043-run Execute Artifact Checksumming. **Logic**: **Requires T043-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/checksums_all.json`.

### Sub-phase 2.3: Sequential Validation & Global Checks (Must run after 2.2)
- [ ] T042b-impl Measure End-to-End Runtime (Task 4.1). **Logic**: Monitor cumulative runtime to ensure it remains within limits.
- [ ] T042b-run Execute Runtime Monitoring. **Logic**: **Requires T042b-impl completion**. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/runtime_monitor.log`.

---

## Phase 2.5: Data Ingestion & Sampling (Replaces Phase 7)

**Purpose**: Ensure reproducible data ingestion by downloading a static subset and creating a deterministic sample.
**Status**: **New**: Added to satisfy Constitution Principle I (Reproducibility) and Spec Assumptions.

- [ ] T050-impl [P] [US1/US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` -> **Static Subset Download**. **Logic**: Write script that downloads the "train" split of `omnidoc_tokenbench` from HuggingFace datasets to `data/raw/omnidoc_tokenbench.parquet`. **Constraint**: MUST NOT use `streaming=True`. MUST save the full subset to disk. **Fallback**: If specific subset ID not found in spec, default to "train" split. If "train" fails, check for `data/local_sample.parquet`. If both fail, raise `DatasetNotFoundError` with message "Could not resolve dataset subset". **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/download.py` (Static download function).
- [ ] T051-impl [P] [US1/US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` -> **Deterministic Sampling**. **Logic**: Write script that reads the static `data/raw/omnidoc_tokenbench.parquet` and creates a deterministic sample of N images (based on `N_final` from `runtime_fallback.json`) using a fixed random seed (). **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/data/loaders.py` (Sampling function).

### Sub-phase 2.5: Execution
- [ ] T050-run [Feasibility] Execute Static Subset Download. **Logic**: **Requires T050-impl completion**. Download "train" split to `data/raw/omnidoc_tokenbench.parquet`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/raw/omnidoc_tokenbench.parquet`.
- [ ] T051-run [Feasibility] Execute Deterministic Sampling. **Logic**: **Requires T051-impl completion**. Generate sample file `data/interim/sample_omnidoc.parquet`. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/interim/sample_omnidoc.parquet`.

---

## Phase 3: User Story 1 - Latent Space Disentanglement Analysis (Priority: P1) 🎯 MVP

- [ ] T022-impl [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **Permutation Test & Classification**. **Logic**: **Requires T000-run**. Check `power_analysis.json`; if `status="INCONCLUSIVE"`, skip execution and write "inconclusive" result. **CRITICAL**: If `heuristic_labels.csv` exists, raise `ValueError` to prevent contamination. Train Linear SVM/LogReg on latent vectors using labels **ONLY** from `ground_truth_labels.parquet`. Compute accuracy/F1. Perform Permutation Test (N=1000): Shuffle labels N times, retrain classifier, record accuracy distribution. Compute empirical p-value as `(count(perm_acc >= obs_acc) + adjustment) / (N + adjustment)`, where adjustment represents a standard continuity correction term to ensure valid probability estimation.. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/permutation_test_results.json` containing `empirical_p_value`, `distribution`, `observed_accuracy`, `f1_score`, `status` (PASS/INCONCLUSIVE).
- [ ] T024-impl [P] [US1] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/separability.py` -> **PCA Visualization**. **Logic**: Reduce latent vectors to 2D using PCA. Plot text vs image clusters. **Deliverable**: `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/data/results/pca_plot.png`.
- [ ] T022-run Execute Permutation Test & Classification. **Logic**: **Requires T022-impl completion**. **Deliverable**: `permutation_test_results.json`.
- [ ] T024-run Execute PCA Visualization. **Logic**: **Requires T024-impl completion**. **Deliverable**: `pca_plot.png`.

---

## Phase 4: User Story 2 - Zero-Shot Semantic Editing via Vector Arithmetic (Priority: P2)

- [ ] T025-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/models/editing.py` -> **Vector Arithmetic**. **Logic**: Compute centroids for text/image. Implement $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$. **Deliverable**: `code/models/editing.py`.
- [ ] T026-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Baseline Reconstruction**. **Logic**: Encode and decode original image to create baseline. **Deliverable**: `data/interim/baseline_reconstructions/`.
- [ ] T027-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Masked SSIM**. **Logic**: Compute SSIM between edited and baseline, masking out text regions using bounding boxes. **Deliverable**: `data/results/ssim_scores.json`.
- [ ] T028-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **Keypoint Matching**. **Logic**: Detect SIFT/ORB keypoints in non-text regions. Match between edited and baseline. Compute score. **Deliverable**: `data/results/keypoint_scores.json`.
- [ ] T029-impl [P] [US2] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/editing_eval.py` -> **OCR Verification**. **Logic**: Run PaddleOCR on edited text regions. Compare to target string. **Deliverable**: `data/results/ocr_accuracy.json`.
- [ ] T032 [P] [US2] Manual Verification Fallback. **Logic**: If OCR accuracy < 95%, randomly sample a small subset of failed samples using a fixed seed. If count < 5, sample all. Logic: `itertools.islice(random.sample(..., k=min(50, count)))`. Flag these in `data/manual/verification_queue.csv`. **Deliverable**: `data/manual/verification_queue.csv`.
- [ ] T025-run Execute Vector Arithmetic. **Logic**: **Requires T025-impl completion**. **Deliverable**: Edited images.
- [ ] T026-run Execute Baseline Reconstruction. **Logic**: **Requires T026-impl completion**. **Deliverable**: Baseline images.
- [ ] T027-run Execute Masked SSIM. **Logic**: **Requires T027-impl completion**. **Deliverable**: `ssim_scores.json`.
- [ ] T028-run Execute Keypoint Matching. **Logic**: **Requires T028-impl completion**. **Deliverable**: `keypoint_scores.json`.
- [ ] T029-run Execute OCR Verification. **Logic**: **Requires T029-impl completion**. **Deliverable**: `ocr_accuracy.json`.
- [ ] T032-run Execute Manual Verification Fallback. **Logic**: **Requires T032 completion**. **Deliverable**: `verification_queue.csv`.

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

- [ ] T033-impl [P] [US3] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/stats.py` -> **Sensitivity Analysis**. **Logic**: Sweep classification threshold. Report FPR/FNR variation. **Deliverable**: `data/results/sensitivity_analysis.json`.
- [ ] T034-impl [P] [US3] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/analysis/stats.py` -> **Bonferroni Correction**. **Logic**: Apply Bonferroni correction to p-values from T022. **Deliverable**: `data/results/corrected_p_values.json`.
- [ ] T033-run Execute Sensitivity Analysis. **Logic**: **Requires T033-impl completion**. **Deliverable**: `sensitivity_analysis.json`.
- [ ] T034-run Execute Bonferroni Correction. **Logic**: **Requires T034-impl completion**. **Deliverable**: `corrected_p_values.json`.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T040-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/utils/versioning.py` -> Versioning Mechanism. **Logic**: Compute SHA-256 of artifacts, update state file. **Deliverable**: `code/utils/versioning.py`.
- [ ] T041-impl [P] Implement `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/main.py` -> Orchestration. **Logic**: Chain all tasks in dependency order. **Deliverable**: `code/main.py`.
- [X] T044 [P] Final Integration Test. **Logic**: Run full pipeline on a small sample. Verify all outputs exist. **Deliverable**: `data/results/final_report.md`.

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
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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