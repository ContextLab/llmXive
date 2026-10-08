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

- [X] T001 Create `data/raw/`, `data/processed/`, `data/results/`, `code/`, and `tests/` directories with `.gitkeep` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin, including spec alignment.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/requirements.txt` pinning exact versions: `torch==2.1.0+cpu `, `transformers==4.36.0 `, `datasets==2.14.0 `, `scikit-learn==1.3.0 `, `opencv-python-headless==4.8.0 `, `numpy==1.24.0 `, `pandas==2.0.0 `, `matplotlib==3.7.0 `, `scipy==1.10.0 `, `psutil==2.3.0 `.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [ ] T036 [Foundational] **SPEC VERIFICATION**: Verify that `spec.md` contains the required amendments: exclusion of ChestX-ray14 (FR-003/US-2), native 1024x1024 ground truth (FR-004), and paired t-test/Wilcoxon (SC-004). **Dependency**: None. **Action**: Script must read `spec.md` and assert presence of these specific text blocks. If missing, raise `RuntimeError`. **Deliverable**: Verification log or successful exit. **Verification**: Assert that `spec.md` contains the exact strings: "ChestX-ray14 is excluded", "native 1024x1024 ground truth", and "Paired t-test or Wilcoxon signed-rank test".
- [ ] T036b-1 [Foundational] **PLAN ALIGNMENT (SC-005 Removal)**: Edit `plan.md` to remove the reference to "SC-005" in the "Spec Amendments Required" section. **Dependency**: None. **Action**: Search and remove all instances of "SC-005". **Rationale**: SC-005 (one-sample t-test) is scientifically unsound per DR-002 and has been superseded by SC-004 (paired test). This task cleans the plan to reflect the final approved methodology. **Verification**: Assert "SC-005" does not appear in `plan.md`. **Deliverable**: Updated `plan.md`.
- [ ] T036b-2 [Foundational] **PLAN ALIGNMENT (Decision Record)**: Create `decisions/003-plan-spec-alignment.md` documenting the removal of the SC-005 reference and the confirmation of SC-004 as the correct test. **Dependency**: None. **Action**: Create file with content explaining the alignment and referencing DR-002. **Verification**: Assert file exists. **Deliverable**: `decisions/003-plan-spec-alignment.md`.
- [ ] T036c-1 [Foundational] **SPEC UPDATE (FR-003)**: Edit `spec.md` to formally document the exclusion of ChestX-ray14. **Action**: Insert text block into FR-003 stating: "ChestX-ray dataset is excluded from all data loading and analysis steps per Decision Record 001". **Verification**: Assert this exact string exists in `spec.md`. **Deliverable**: Updated `spec.md`.
- [ ] T036c-2 [Foundational] **SPEC UPDATE (FR-004)**: Edit `spec.md` to formally document the use of native 1024x1024 ground truth. **Action**: Insert text block into FR-004 stating: "Native 1024x1024 ground truth images are used for fidelity measurement per Decision Record 002". **Verification**: Assert this exact string exists in `spec.md`. **Deliverable**: Updated `spec.md`.
- [ ] T036c-3 [Foundational] **SPEC UPDATE (SC-004)**: Edit `spec.md` to formally document the statistical test change. **Action**: Insert text block into SC-004 stating: "Paired t-test or Wilcoxon signed-rank test is used to compare error distributions per the established decision protocol (DR-002)." **Verification**: Assert this exact string exists in `spec.md`. **Deliverable**: Updated `spec.md`.
- [X] T004 Implement `code/config.py` with explicit keys: `batch_size` (default 8), `learning_rate` (default 1e-4), `seed` (default 42), `dataset_limits` (e.g., `max_train_samples`), `paths` (data dirs), and `thresholds` (e.g., `semantic_threshold`).
- [X] T005 [P] Implement `code/data_loader.py` to load COCO (`datasets.load_dataset("coco", split="train", streaming=True)`) with standard spatial resize to a fixed resolution and ImageNet-1K (`datasets.load_dataset("imagenet", split="validation", streaming=False)`) with batch handling; explicitly exclude ChestX-ray14 per Decision Record 001 (T036a); fail loudly if fetch fails. **Dependency**: T036 (Spec Verification ensures the exclusion is documented).
- [X] T006 [P] [Foundational] Implement `code/model.py` defining VQ-VAE Codebook, Projection Head, and Frozen ViQ/CLIP wrappers. Use ViQ-Base placeholder ID "viq-base-v". **Note**: If checkpoint missing, the script MUST raise a `RuntimeError` with a clear message; NO fallback architecture is permitted. **Dependency**: T005.
- [X] T006a [Foundational] **CRITICAL HYPOTHESIS CHECK**: Implement `code/validate_viq_invariance.py` to load the frozen ViQ encoder weights and perform a forward pass on a 1024x1024 image sample. **Source**: Use a random sample from the ImageNet-1K validation set ONLY (ChestX-ray14 is explicitly excluded per FR-003). **Deliverable**: Script must raise a `RuntimeError` with a clear message if the ViQ encoder fails to process the 1024x1024 input (indicating lack of resolution invariance of the quantized representation). **Success Verification**: Verify script exits with code 0 on a known 1024x1024 sample. **Dependency**: T005.
- [X] T006b [Foundational] **HYPOTHESIS FAILURE CONTINGENCY**: Implement `code/handle_hypothesis_failure.py`. **Trigger**: Run T006a; if exit code != 0, then generate `data/results/pivot_plan.md` and `data/results/failure_analysis.md`. **Action**: Create these two files documenting the failure and fallback strategy. **CRITICAL**: This task MUST also update `plan.md` and `spec.md` to reflect the pivot (e.g., removing the hypothesis or changing scope) to maintain Single Source of Truth (Principle IV). **Verification**: Assert both files exist, contain non-empty content, and `plan.md`/`spec.md` are updated. **Deliverable**: `data/results/pivot_plan.md`, `data/results/failure_analysis.md`, and updated `plan.md`/`spec.md`. **Dependency**: T006a (Conditional: runs only if T006a fails).
- [X] T007 Implement `code/utils.py` for metric calculation (PSNR, SSIM, Cosine Similarity, Texture Complexity via Laplacian Variance).
- [X] T008a [P] [Foundational] Implement `tests/test_data.py` with `test_data_loader_streaming_returns_64x64_shape` (ensure it FAILS initially).
- [X] T008b [P] [Foundational] Implement `tests/test_metrics.py` with `test_psnr_calculation_on_known_pair` (ensure it FAILS initially).
- [X] T009 Implement `code/state.py` to manage artifact hashing and versioning per Constitution Principle V.
- [ ] T040 [P] [Foundational] Implement `code/verify_data_integrity.py` to calculate and store cryptographic checksums for all downloaded raw datasets (COCO, ImageNet) immediately after download in `data/raw/checksums.json`. **Rationale**: Addresses reviewer concern regarding "Data Hygiene" (Constitution Principle III) by ensuring raw data integrity is verified and logged before processing. **Verification**: Assert `data/raw/checksums.json` exists and contains valid SHA256 hashes for all raw files. **Dependency**: T005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Low-Resolution Training & Codebook Initialization (Priority: P1) 🎯 MVP

**Goal**: Initialize and train a visual quantization codebook using low-resolution COCO data on CPU-only hardware..

**Independent Test**: The system can be tested by running the training loop on a representative sample of COCO pairs, verifying that the codebook converges (loss decreases) and that the resulting quantized tokens can be reconstructed into 64x64 images with a standard VQ-VAE loss, all within the specified CPU time limit.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation
> *Note: T010 and T011 moved to Phase 2 as they test foundational code.*

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/train.py` with CPU-only training loop, frozen ViQ encoder, and VQ-VAE (codebook+commitment) + Contrastive (InfoNCE, temp=0.07, negative sampling via in-batch negatives) loss. **Deliverable**: Script must dynamically adjust batch size (start with `config.batch_size`, decrement if RAM > 6.5GB), log "Final batch_size: X" and "Peak RAM: Y GB", save checkpoint to `data/results/codebook_v0.pth`, and verify loss decreases. **Verification**: Assert `data/results/codebook_v0.pth` exists and `data/results/train_log.json` contains rows with keys `initial_total_loss` and `final_total_loss` where `final_total_loss < initial_total_loss * 0.5` or a CRITICAL warning if time limit exceeded. **Dependency**: T005, T004.
- [X] T014 [US1] Implement reconstruction verification script in `code/eval_low_res.py` to calculate PSNR on 64x64 samples. **Deliverable**: Script must calculate PSNR and SSIM, log the values, and exit successfully if metrics are computed. **Dependency**: T012.
- [X] T015 [US1] Implement `code/eval_semantic_baseline.py` to load `data/results/codebook_v0.pth` and a small batch of 64x64 COCO images/captions, compute projected visual embeddings, and calculate mean cosine similarity against frozen CLIP text embeddings. **Deliverable**: Save results to `data/results/semantic_baseline.json` with keys `mean_similarity`, `count`, and `resolution`. Produces artifact required by T028. **Dependency**: T012.
- [X] T016 [US1] Add logging for training loss, reconstruction loss, and codebook usage statistics. **Deliverable**: Write metrics in JSON format to `data/results/train_log.json` with fields `step`, `total_loss`, `vq_loss`, `contrastive_loss`, `elapsed_time`, `initial_total_loss`, `final_total_loss`. **Dependency**: T012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Resolution Inference & Fidelity Measurement (Priority: P2)

**Goal**: Evaluate the trained low-resolution codebook on high-resolution (1024x1024) images to measure fidelity degradation and correlation with texture complexity.

**Independent Test**: The system can be tested by processing a batch of high-resolution images (1024x1024) from ImageNet-1K and COCO, generating reconstructions, and calculating the mean PSNR and SSIM. The test passes if the metrics are computed and the correlation with texture complexity is plotted.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for `code/eval_high_res.py` verifying shape handling for 1024x1024 inputs in `tests/test_metrics.py`.
- [X] T018 [P] [US2] Integration test for end-to-end inference on a small batch in `tests/integration/test_eval.py`.

### Implementation for User Story 2

- [X] T019a [P] [US2] **DATA EXTRACTION**: Implement `code/extract_native_images.py` to extract native 1024x1024 images from raw archives (COCO, ImageNet) into `data/processed/`. **Dependency**: T005 (downloaded archives). **Action**: Extract images, validate resolution (must be 1024x1024), and save to `data/processed/native_1024/`. **Verification**: Assert `data/processed/native_1024/` contains valid 1024x1024 images. **Deliverable**: Extracted images in `data/processed/native_1024/`. **Dependency**: T005.
- [ ] T019 [P] [US2] Implement `code/eval_high_res.py` to load `data/results/codebook_v0.pth` (Depends on T012) and process 1024x1024 images from ImageNet-1K and COCO (ChestX-ray14 excluded per Decision Record 001; FR-003/US-2 amended) without resizing; save projected visual embeddings to `data/results/embeddings_high_res.h5` AND read native 1024x1024 ground truth images from `data/processed/native_1024/` (produced by T019a). **Dependency**: T005, T006a, T012, T036c-2, T019a. **Gate Condition**: T006a [GATE]. If T006a failed (RuntimeError raised), the project halts and T019 cannot be executed. **Verification**: Assert `data/results/embeddings_high_res.h5` exists, size > 0MB, and schema matches expected HDF5 structure. **Dependency**: T005, T006a (Must Pass), T012, T036c-2, T019a.
- [X] T020 [US2] Implement texture complexity calculation in `code/utils.py`: Variance of Laplacian (cv2.Laplacian) on grayscale, normalized by the number of pixels.
- [ ] T021 [US2] Implement metric aggregation script to calculate mean PSNR/SSIM comparing against **native 1024x1024 ground truth** (per Spec FR-004 (amended)) andsave to `data/results/fidelity_metrics.json`. **Deliverable**: Calculate PSNR using `skimage.metrics.peak_signal_noise_ratio` and SSIM using `skimage.metrics.structural_similarity` with `window_size=11 (Wikipedia: Structural similarity index measure, https://en.wikipedia.org/wiki/Structural_similarity_index_measure)` on native 1024x1024 images. **CRITICAL**: Must also calculate texture complexity per image and store it in the JSON schema. **JSON Schema**: `{"mean_psnr": float, "mean_ssim": float, "count": int, "note": "native ground truth used per Spec FR-004 (amended)", "per_image_data": [{"id": str, "psnr": float, "ssim": float, "texture_complexity": float}]}`. **Verification**: Assert JSON schema contains required fields, `mean_psnr` is a float between 0 and 100, and `per_image_data` contains `texture_complexity`. **Dependency**: T036c-2, T019, T020.
- [ ] T021b [US2] **PAIRED DATA GENERATION**: Implement `code/generate_paired_data.py` to join low-res and high-res reconstruction errors for the SAME image IDs into a single CSV. **Input**: `data/results/fidelity_metrics.json` (high-res) and `data/results/eval_low_res_metrics.json` (low-res, from T014). **Action**: Join on image ID, calculate difference (high_res_error - low_res_error), and save to `data/results/paired_errors.csv`. **Verification**: Assert CSV exists with columns `image_id`, `low_res_psnr`, `high_res_psnr`, `error_diff`. **Deliverable**: `data/results/paired_errors.csv`. **Dependency**: T021, T014.
- [X] T022 [US2] Implement correlation analysis script in `code/analysis.py` using `scipy.stats.spearmanr` (SC-002) AND **paired t-test/Wilcoxon** (SC-004) between texture complexity and reconstruction error. **Deliverable**: Perform Shapiro-Wilk test on error distribution (SC-003); if p > 0.05 use paired t-test, else use Wilcoxon signed-rank test. **Input**: `data/results/paired_errors.csv` (produced by T021b) for the paired test, and `data/results/fidelity_metrics.json` for texture correlation. **Output**: JSON {spearman_r, p_value_spearman, normality_p_value, method, test_statistic, test_p_value}. **Dependency**: T036c-3, T021, T021b, T020.
- [X] T023 [US2] Generate visualization of correlation plot in `code/analysis.py` using `matplotlib.pyplot` and save to `data/results/correlation_plot.png`. **Deliverable**: Script must explicitly define figure size, labels, and title. **Dependency**: T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Semantic Alignment Validation (Priority: P3)

**Goal**: Verify that semantic alignment between visual tokens and text embeddings remains stable despite resolution shift using a frozen CLIP text encoder.

**Independent Test**: The system can be tested by computing the cosine similarity between the projected visual embeddings of high-resolution images and their corresponding text embeddings. The test passes if the similarity scores are computed and compared against the low-res baseline scores.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for `code/eval_semantic.py` verifying CLIP text embedding extraction in `tests/test_model.py`. **Note**: Ensure it FAILS initially.
- [X] T025 [P] [US3] Unit test for cosine similarity calculation in `tests/test_metrics.py`. **Note**: Ensure it FAILS initially.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/eval_semantic.py` to load `data/results/embeddings_high_res.h5` (produced by T019) and frozen CLIP text encoder to compute text embeddings for captions, extract projected visual embeddings, and compute cosine similarity against text embeddings. **Deliverable**: Save high-res similarity scores to `data/results/semantic_high_res.json`. **Verification**: Assert script exits with code 0 and `data/results/semantic_high_res.json` exists with keys [mean_similarity, count, resolution]. **Dependency**: T019, T012, T024, T025 (if tests requested).
- [ ] T028 [US3] Implement statistical comparison script in `code/analysis.py` to calculate percentage difference between high-res (from `data/results/semantic_high_res.json` produced by T026) and low-res baseline (from `data/results/semantic_baseline.json` produced by T015) similarity scores. **Deliverable**: Depends on T015 and T026. Output file: `data/results/semantic_diff.json`. Logic: First, perform Paired t-test or Wilcoxon signed-rank test (SC-004) on the distribution of differences (requires paired data from T021b logic applied to semantic scores). Second, calculate percentage difference: `abs(high_res_mean - low_res_mean) / low_res_mean * 100`. Flag if p-value < 0.05. **Verification**: Assert output JSON contains `percentage_diff`, `p_value`, `method`, and `threshold_exceeded` boolean. **Dependency**: T015, T026, T021b (for paired logic).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030a [P] Update `README.md` overview section with project scope, data sources, and exclusion of ChestX-ray14 (referencing Decision Record 001).
- [X] T030b [P] Update `README.md` usage section with run commands, memory fallback strategy, and the mandatory resolution-invariance check (T006a).
- [X] T030c [P] Create `docs/quickstart.md` with step-by-step setup instructions.
- [X] T031 Code cleanup and refactoring of `code/` modules: Ensure `ruff` passes, remove duplicate imports, and verify type hints.
- [X] T032 [P] Performance optimization for streaming data loading in `code/data_loader.py`: Measure baseline batch load time for a representative set of batches; log before/after times to `data/results/baseline_metrics.json` with keys `baseline_time_ms` and `optimized_time_ms`.
- [X] T033 [P] Additional unit tests for edge cases (e.g., extreme noise, missing captions) in `tests/unit/`.
- [X] T034 Run `quickstart.md` validation to ensure full reproducibility.
- [X] T035 Finalize `data/results/` directory structure and ensure all artifacts are hashed.
- [X] T037 [P] Create `code/eval.py` as a wrapper script that invokes `code/train.py`, `code/eval_high_res.py`, and `code/analysis.py` in the correct order, ensuring the run-book matches the implementation.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **HARD DEPENDENCY**: T012 (codebook generation) must complete before T019 starts. **HARD DEPENDENCY**: T006a (ViQ invariance check) must pass before T019 starts. **HARD DEPENDENCY**: T036c-2 (Spec Update) must complete before T021. **HARD DEPENDENCY**: T019a (Extraction) must complete before T019. **HARD DEPENDENCY**: T021b (Paired Data) must complete before T022 and T028.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **HARD DEPENDENCY**: T012 (codebook) and T019 (high-res embeddings) must complete. **HARD DEPENDENCY**: T015 (low-res baseline) must complete before T028 runs. **HARD DEPENDENCY**: T021b (Paired Data) must complete before T028.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T003, T006, T007, T008a, T008b, T009, T040) can run in parallel (T005, T006a, T006b, T036, T036b-1, T036b-2, T036c-1, T036c-2, T036c-3 are blocking)
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
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure codebook converges and metrics are calculated)
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
- **Compute Constraint**: Training MUST complete within 6 hours on CPU; if not, reduce sample size in `code/config.py` and log the reduction. T012 explicitly monitors this.
- **Plan Amendments**: ChestX-ray14 is excluded from scope (Decision Record 001). FR-004 (upsampled baseline) and SC-005 (one-sample t-test) are amended per Decision Record 002 to use native ground truth and paired t-test/Wilcoxon respectively.
- **Explicit Exclusions**: T005, T019 explicitly document exclusion of ChestX-ray14 per Decision Record 001.
- **Explicit Deviations**: T021 and T022 explicitly note deviations from Spec FR-004 and SC-005 due to scientific unsoundness per Decision Record 002.
- **Hypothesis Integrity**: T006a MUST pass before T019 runs. If T006a fails, T006b generates a Pivot Plan and Failure Analysis before halts, AND updates plan/spec.
- **Artifact Flow**: T019 produces `data/results/embeddings_high_res.h5` for T026/T027/T021 to consume. T015 produces `data/results/semantic_baseline.json` for T028 to consume. T021b produces `data/results/paired_errors.csv` for T022/T028 to consume.
- **Explicit Dependencies**: T012 depends on T005, T004; T026 depends on T024, T025, T019, T012; T028 depends on T015 and T026; T019 depends on T006a and T012 and T019a.
- **Spec Alignment**: T036 ensures `spec.md` is verified to reflect the implemented deviations (native ground truth, paired tests, invariance check) to resolve the contradiction between spec and plan. T036c-1, T036c-2, T036c-3 update `spec.md` to formally document these deviations.
- **Run-book Reconciliation**: T037 ensures the `quickstart.md` run-book matches the actual script names (`code/eval_high_res.py`, `code/train.py`, etc.) by creating a wrapper `code/eval.py`.
- **Review Resolution**: T040 was added to explicitly address reviewer concerns regarding raw data integrity logging.
- **Scope Closure**: T019b and T038/T039 were removed as they were redundant or out of scope.
- **Constraint Preservation**: All tasks now strictly adhere to the Spec's requirements without introducing undefined claims or unverified fallbacks.