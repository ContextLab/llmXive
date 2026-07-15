# Tasks: llmXive follow-up: extending "ViQ: Text-Aligned Visual Quantized Representations at Any Resolution"

**Input**: Design documents from `/specs/001-viq-resolution-invariance/`
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

- [ ] T001 Create `data/raw/`, `data/processed/`, `data/results/`, `code/`, and `tests/` directories with `.gitkeep` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with `projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/requirements.txt` pinning exact versions: `torch==2.1.0+cpu`, `transformers==4.36.0`, `datasets==2.14.0`, `scikit-learn==1.3.0`, `pillow==10.1.0`, `opencv-python-headless==4.8.0`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [X] T004 Implement `code/config.py` with explicit keys: `batch_size` (default 8), `learning_rate` (default 1e-4), `seed` (default 42), `dataset_limits` (e.g., `max_train_samples`), `paths` (data dirs), and `thresholds` (e.g., `semantic_threshold`).
- [X] T005 [P] Implement `code/data_loader.py` to load COCO (`datasets.load_dataset("coco", split="train", streaming=True)`) with standard spatial resize to a fixed resolution and ImageNet-1K (`datasets.load_dataset("imagenet", split="validation", streaming=False)`) with batch handling; explicitly exclude ChestX-ray14 per Plan Spec Amendment #3 and #5; fail loudly if fetch fails.
- [X] T006 [P] [Foundational] Implement `code/model.py` defining VQ-VAE Codebook, Projection Head, and Frozen ViQ/CLIP wrappers. Use ViQ-Base placeholder ID "viq-base-v". If checkpoint missing, define fallback architecture: ResNet based VQ-VAE with 512 hidden dimensions, 1024 codebook size, and global average pooling for resolution invariance.
- [X] T007 Implement `code/utils.py` for metric calculation (PSNR, SSIM, Cosine Similarity, Texture Complexity via Laplacian Variance).
- [ ] T008 [P] [Foundational] Implement `tests/test_data.py` with `test_data_loader_streaming_returns_64x64_shape` and `tests/test_metrics.py` with `test_psnr_calculation_on_known_pair` (ensure they FAIL initially). <!-- SKIPPED: non-mapping output -->
- [X] T009 Implement `code/state.py` to manage artifact hashing and versioning per Constitution Principle V.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Low-Resolution Training & Codebook Initialization (Priority: P1) 🎯 MVP

**Goal**: Initialize and train a visual quantization codebook using low-resolution (64x64) COCO data on CPU-only hardware.

**Independent Test**: The system can be tested by running the training loop on a representative sample of COCO pairs, verifying that the codebook converges (loss decreases) and that the resulting quantized tokens can be reconstructed into 64x64 images with a PSNR > 15 dB, all within the specified CPU time limit.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> *Note: T010 and T011 moved to Phase 2 as they test foundational code.*

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/train.py` with CPU-only training loop, frozen ViQ encoder, and VQ-VAE (codebook+commitment) + Contrastive (InfoNCE, temp=0.07, negative sampling via in-batch negatives) loss (weights: 1.0 VQ, 0.1 Contrastive). Text encoder input format: raw strings tokenized by `transformers.CLIPTextModel` tokenizer.
- [X] T013 [US1] Implement dataset sampling strategy in `code/train.py` to fit 64x64 images within 7GB RAM (batch size tuning).
- [ ] T014 [US1] Implement checkpoint saving logic in `code/train.py` to output `data/results/codebook_v0.pth`.
- [ ] T015 [US1] Implement reconstruction verification script in `code/eval_low_res.py` to calculate PSNR on 64x64 samples.
- [ ] T016 [US1] Add logging for training loss, reconstruction loss, and codebook usage statistics.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Resolution Inference & Fidelity Measurement (Priority: P2)

**Goal**: Evaluate the trained low-resolution codebook on high-resolution (1024x1024) images to measure fidelity degradation and correlation with texture complexity.

**Independent Test**: The system can be tested by processing a batch of 50 high-resolution images (1024x1024) from ImageNet-1K and COCO, generating reconstructions, and calculating the mean PSNR and SSIM. The test passes if the metrics are computed and the correlation with texture complexity is plotted.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for `code/eval_high_res.py` verifying shape handling for 1024x1024 inputs in `tests/test_metrics.py`.
- [ ] T018 [P] [US2] Integration test for end-to-end inference on a small batch in `tests/integration/test_eval.py`.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/eval_high_res.py` to load `data/results/codebook_v0.pth` (Depends on T014) and process 1024x1024 images from ImageNet-1K and COCO (ChestX-ray14 excluded per Plan Spec Amendment #3 and #5) without resizing; save projected visual embeddings to `data/results/embeddings_high_res.h5`. Note: Relies on T005 which is configured to exclude ChestX-ray14.
- [ ] T019b [P] [US2] Explicitly document exclusion of ChestX-ray14 in evaluation: add comment/log in `code/eval_high_res.py` stating "ChestX-ray14 excluded per Plan Spec Amendments; FR-003/US-2 amended".
- [ ] T020 [US2] Implement texture complexity calculation in `code/utils.py`: Variance of Laplacian (cv2.Laplacian) on grayscale, normalized by the number of pixels.
- [ ] T021 [US2] Implement metric aggregation script to calculate mean PSNR/SSIM comparing against native 1024x1024 ground truth (deviating from Spec FR-004 which required upsampled ground truth per Plan Spec Amendment #1) and save to `data/results/fidelity_metrics.json`. JSON Schema: `{"mean_psnr": float, "mean_ssim": float, "count": int, "note": "native ground truth used per Plan Amendment"}`.
- [ ] T022 [US2] Implement correlation analysis script using Spearman rank correlation AND paired t-test/Wilcoxon (deviating from Spec SC-005 which required one-sample t-test per Plan Spec Amendment #4) between texture complexity and reconstruction error. Input: pandas DataFrame with columns [texture_complexity, psnr], Output: JSON {spearman_r, p_value, method}.
- [ ] T023 [US2] Generate visualization of correlation plot and save to `data/results/correlation_plot.png`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Semantic Alignment Validation (Priority: P3)

**Goal**: Verify that semantic alignment between visual tokens and text embeddings remains stable despite resolution shift using a frozen CLIP text encoder.

**Independent Test**: The system can be tested by computing the cosine similarity between the projected visual embeddings of high-resolution images and their corresponding text embeddings. The test passes if the similarity scores are computed and compared against the low-res baseline scores.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for `code/eval_semantic.py` verifying CLIP text embedding extraction in `tests/test_model.py`.
- [ ] T025 [P] [US3] Unit test for cosine similarity calculation in `tests/test_metrics.py`.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/eval_semantic.py` to load `data/results/embeddings_high_res.h5` (produced by T019) and frozen CLIP text encoder to compute text embeddings for captions.
- [ ] T027 [US3] Implement logic to extract projected visual embeddings from high-res images (requires T014 codebook) and compute cosine similarity against text embeddings.
- [ ] T028 [US3] Implement statistical comparison script to calculate percentage difference between high-res and low-res baseline similarity scores. Output file: `data/results/semantic_diff.json`. Logic: `abs(high_res_mean - low_res_mean) / low_res_mean * 100`. Flag if > `config.semantic_threshold`.
- [ ] T029 [US3] Generate semantic alignment report in `data/results/semantic_report.json` with flags for threshold exceedance.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] Update `README.md` overview section with project scope, data sources, and exclusion of ChestX-ray14.
- [ ] T030b [P] Update `README.md` usage section with run commands and memory fallback strategy.
- [ ] T030c [P] Create `docs/quickstart.md` with step-by-step setup instructions.
- [ ] T031 Code cleanup and refactoring of `code/` modules: Ensure `ruff` passes, remove duplicate imports, and verify type hints.
- [ ] T032 Performance optimization for streaming data loading in `code/data_loader.py`: Target a significant reduction in data loading time via batch prefetching or optimized transform pipelines.
- [ ] T033 [P] Additional unit tests for edge cases (e.g., extreme noise, missing captions) in `tests/unit/`.
- [ ] T034 Run `quickstart.md` validation to ensure full reproducibility.
- [ ] T035 Finalize `data/results/` directory structure and ensure all artifacts are hashed.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on Codebook output from US1 (T014)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on Codebook output from US1 (T014) and Inference from US2 (T019)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T003, T006, T008) can run in parallel (T005 is blocking)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/data_loader.py verifying 64x64 resize and streaming behavior in tests/test_data.py"
Task: "Unit test for code/model.py verifying VQ-VAE loss calculation on a dummy batch in tests/test_model.py"

# Launch all models for User Story 1 together:
Task: "Implement code/train.py with CPU-only training loop..."
Task: "Implement dataset sampling strategy in code/train.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure codebook converges and PSNR > 15 dB)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Evaluate fidelity drop)
4. Add User Story 3 → Test independently → Deploy/Demo (Validate semantic alignment)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Training)
 - Developer B: User Story 2 (Inference & Metrics)
 - Developer C: User Story 3 (Semantic Alignment)
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
- **Critical Data Constraint**: `code/data_loader.py` MUST fail loudly if real data fetch fails; NO synthetic fallbacks.
- **Compute Constraint**: Training MUST complete within 6 hours on CPU; if not, reduce sample size in `code/config.py` and log the reduction.
- **Plan Amendments**: ChestX-ray14 is excluded from scope. FR-004 (upsampled baseline) and SC-005 (one-sample t-test) are amended per Plan to use native ground truth and paired t-test/Wilcoxon respectively.
- **Explicit Exclusions**: T005, T019, T019b explicitly document exclusion of ChestX-ray14 per Plan.
- **Explicit Deviations**: T021 and T022 explicitly note deviations from Spec FR-004 and SC-005 due to scientific unsoundness per Plan.
- **Artifact Flow**: T019 produces `data/results/embeddings_high_res.h5` for T026/T027 to consume.