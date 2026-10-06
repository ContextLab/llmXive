# Tasks: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
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

- [X] T001 Create project structure: Create directories `code/`, `code/analysis/`, `code/data/`, `code/models/`, `code/quantization/`, `code/evaluation/`, `code/validation/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/` at repository root; Create empty `__init__.py` in each directory.
- [X] T002 Initialize Python project: Create `requirements.txt` containing: `torch>=2.0`, `transformers>=4.35`, `diffusers>=0.24`, `datasets>=2.14`, `scikit-learn>=1.3`, `accelerate>=0.24`, `sentence-transformers>=2.2`, `peft>=0.6`, `fid-score`, `clip-score`, `numpy>=1.24`, `pandas>=2.0`.
- [X] T003 [P] Configure linting and formatting: Create `.ruff.toml` with ruff config; Create `pyproject.toml` with `[tool.black]` section.
- [X] T041 [P] Implement GPU Offload Logic: Create `code/utils/gpu_offload.py` to detect CPU failure on DiT generation tasks and trigger the Kaggle GPU offload mechanism; this is a critical infrastructure component required for T017 and T046.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and data preparation. **CRITICAL**: T017 (Correlation) must run BEFORE T022 (Matrices) to validate the hypothesis.

- [X] T004 Implement `code/config.py` with hyperparameters, paths, seeds, and device detection logic (CPU default, GPU escape hatch flag)
- [X] T005 [P] Implement `code/data/download_coco.py` to fetch MS-COCO validation set (captions + images) using `datasets.load_dataset` with streaming disabled for local caching; ensure no synthetic fallbacks
- [X] T006 [P] Implement and run `code/data/preprocess.py` to extract captions from MS-COCO into `data/processed/prompts.csv`; **Deliverable**: Verify `data/processed/prompts.csv` exists with columns `[id, caption]` and row count > 0.
- [X] T006c [P] Implement and run `code/data/download_diverse_prompts.py` to fetch a diverse set of text prompts from `nlpconnect/vit-gpt2-image-captioning` dataset on HuggingFace; **CRITICAL**: Extract `caption` column; ensure no synthetic fallbacks; if a real source cannot be verified, the task must fail loudly.
- [ ] T006d [P] Run `code/data/download_diverse_prompts.py` to generate `data/processed/diverse_prompts.csv`; **Deliverable**: Verify `data/processed/diverse_prompts.csv` exists with columns `[id, caption, source]` and non-empty captions.
- [X] T007 Implement `code/models/flux_wan_loader.py` to load FLUX.1-dev/Wan 2.1 (GPU) or Stable Diffusion 2.1 (CPU) with hooks for activation capture during the **text-to-image generation loop**
- [X] T008 Implement `code/models/dit_wrapper.py` to inject hooks into DiT intermediate layers for capturing float32 activation tensors **during the generative trajectory** (text-to-image generation conditioned on prompt)
- [X] T009 Implement `code/analysis/entropy_proxy.py` using a lightweight LLM (e.g., `transformers` with `do_sample=True`) to compute semantic entropy via **generative paraphrase sampling** (generate multiple paraphrases, cluster them, compute entropy)
- [X] T010 Implement `code/quantization/w2a4_engine.py` for W2A4 quantization with rotation matrix application capability
- [X] T011 Implement `code/quantization/static_baseline.py` implementing the original OrbitQuant static rotation logic for comparison
- [X] T017 [US1] Implement `code/run_correlation.py` orchestration script: Load prompts (from T006d) -> Compute Entropy -> Run DiT Generation (GPU/CPU) **using prompts as conditioning inputs** -> Capture Variances -> Compute Correlation -> Generate `data/processed/correlation_results.json`; **must depend on T006d, T007, T008, T009, and T041**.
- [X] T023b [P] Implement `code/validation/validate_correlation.py` to verify `data/processed/correlation_results.json` exists and p-value < 0.05; **must depend on T017**.

**Checkpoint**: Correlation hypothesis tested. If T023b passes (p < 0.05), proceed to Phase 4 (US2). If not, project may pivot.

---

## Phase 2.5: Post-US1 Validation Gate (Blocking Pre-Implementation of Router)

**Purpose**: Validate `correlation_results.json` before Router Implementation (Constitution Principle VI)

**⚠️ CRITICAL**: This phase runs AFTER Phase 2 (Foundational) and blocks Phase 4 (US2). It validates that the correlation is significant.

- [ ] T023a [P] Implement `code/validation/validate_clustering.py` to verify `data/processed/clustering_report.json` exists (if it exists) and contains required keys.
- [X] T023c [P] Implement `code/main_validation.py` orchestration script for Phase 2.5: Run T023b; if validation fails (p >= 0.05), halt execution and log error; if valid, proceed to Phase 4.

---

## Phase 3: User Story 1 - Establish Correlation (Priority: P1) 🎯 MVP

**Goal**: Empirically determine if a statistical correlation exists between prompt semantic entropy and DiT activation variance.

**Independent Test**: Run the correlation analysis pipeline on the MS-COCO validation set with a curated set of prompts, outputting a correlation coefficient and p-value.

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for `code/analysis/entropy_proxy.py` entropy calculation logic in `tests/unit/test_entropy.py`
- [X] T013 [P] [US1] Integration test for variance measurement hook in `tests/integration/test_activation_variance.py`

**Implementation Note**: Implementation logic for US1 is consolidated in T017 (Phase 2). Phase 3 is for validation and reporting.

---

## Phase 4: User Story 2 - Implement Dynamic Rotation Router based on Entropy (Priority: P2)

**Goal**: Implement a lightweight router that maps prompt semantic entropy to a pre-optimized rotation matrix. **Only executed if T023b passes.**

**Independent Test**: Feed a prompt with known entropy into the router and verify the correct rotation matrix index is selected and applied.

- [ ] T022 [P] [US2/Foundational] Implement and run `code/analysis/clustering.py` on the **train split** of activation variances (from T017) to derive $K=16$ pre-optimized rotation matrices and generate `data/processed/clustering_report.json` containing layers, subsets, boundaries, and matrices; **Deliverable**: Verify `data/processed/clustering_report.json` exists and contains keys: layers, subsets, boundaries, matrices (shape 16xD, where D is the activation dimension). **This task is CONDITIONAL on T023b success**. If T023b fails, use static baseline rotation. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [ ] T022c [P] [US2/Foundational] Implement and run `code/run_quantization_validation.py` to generate quantized activations using the rotation matrices from T022 (or static baseline if T022 fails) on the MS-COCO validation set; generate `data/processed/quantized_activations.json`; **must depend on T022**. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T019 [US2] Implement `code/analysis/mse_validator.py` to compute MSE quantization error on the **quantized activations generated by T022c** vs. float32 targets to validate the variance-sensitivity hypothesis; **must depend on T022c**.
- [X] T024 [US2] Implement `code/analysis/router.py` to map entropy scores to matrix indices with clamping logic for out-of-range values and outlier handling
- [X] T025 [US2] Update `code/quantization/w2a4_engine.py` to integrate the dynamic router logic for selecting the rotation matrix during inference
- [X] T028 [US2] Implement `code/analysis/load_matrices.py` to load and verify the pre-computed rotation matrices from `data/processed/clustering_report.json` (generated by T022); **Deliverable**: Create `code/analysis/load_matrices.py` that reads `data/processed/clustering_report.json` and returns a list of 16 numpy arrays, raising ValueError if keys are missing or shapes mismatch. **Must depend on T022**.
- [X] T029 [US2] Implement `code/run_router_inference.py` orchestration script for Phase 2 Inference: Load Test Split -> Compute Entropy -> Load Matrices (T028) -> Select Matrix -> Generate Images -> Log Metrics; **must depend on T028**.

### Tests for User Story 2

- [X] T020 [P] [US2] Contract test for router lookup logic in `tests/unit/test_router.py`
- [X] T021 [P] [US2] Integration test for rotation application in `tests/integration/test_rotation_application.py`

**Checkpoint**: Dynamic router implemented and integrated with W2A4 engine.

---

## Phase 5: User Story 3 - Evaluate Fidelity Gains and Runtime Overhead (Priority: P3)

**Goal**: Compare dynamic router method against static baseline using perceptual metrics and measure runtime overhead.

**Independent Test**: Run both methods on the same prompts, compute FID/CLIP/MSE, and calculate percentage increase in inference time.

### Tests for User Story 3

- [X] T030 [P] [US3] Contract test for metric calculation in `tests/unit/test_metrics.py`
- [X] T031 [P] [US3] Integration test for end-to-end pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/evaluation/metrics.py` to compute FID, CLIP scores, and MSE using CPU-compatible implementations
- [X] T033 [US3] Implement `code/evaluation/timing.py` to measure wall-clock inference time for both static and dynamic methods
- [X] T034 [US3] Implement `code/analysis/statistical_test.py` to perform paired t-tests on metric distributions; **conditionally apply Bonferroni correction** if the number of comparisons exceeds a defined threshold (e.g., >3); define threshold in config
- [X] T035 [US3] Implement `code/analysis/sensitivity.py` to sweep entropy cut-off points by **±5% of the total observed entropy range calculated from T017 (correlation_results.json)** and report variance in FID scores; **must depend on T017**.
- [ ] T036 [US3] Implement `code/run_evaluation.py` orchestration script for Phase 3: Run Baseline -> Run Dynamic -> Compute Metrics -> Run Statistical Tests -> Generate `data/processed/final_evaluation_report.json`

**Checkpoint**: All user stories complete; final report generated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Refactor runners into modular structure: Refactor `code/run_correlation.py` and `code/run_router_inference.py` into modular runners in `code/runners/`; **Deliverable**: Verify `code/runners/` contains modular scripts and `README.md` updated with usage examples.
- [X] T038 [P] Implement streaming for MS-COCO: Refactor `code/data/download_coco.py` to use streaming; **Deliverable**: Verify memory usage < 2GB via benchmark script `tests/unit/test_memory.py`.
- [ ] T039 [P] Additional unit tests for edge cases (entropy out-of-range, proxy failure) in `tests/unit/`
- [ ] T040 [P] Security hardening: Sanitize file paths in data loading; validate model checksums against `state/artifact_hashes.json` before loading; **Deliverable**: Verify checksum validation logic exists and raises error on mismatch for `state/artifact_hashes.json`.

---

## Phase 7: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data sourcing, error handling, and runtime efficiency to ensure the project passes the execution gate.

- [X] T042 [P] [Data Hygiene] Refactor `code/data/download_diverse_prompts.py` to implement a **fail-loud** strategy: remove any `try/except` blocks that fallback to synthetic data; instead, raise a `RuntimeError` with a clear message if the HuggingFace dataset fetch fails (specifically: HTTP 404, TimeoutError, or EmptyDatasetError), ensuring the pipeline halts rather than fabricating data. **Deliverable**: Verify that removing try/except blocks causes the script to exit with code 1 and a RuntimeError message when HuggingFace fetch fails.
- [X] T043 [P] [Edge Case] Implement robust error handling in `code/analysis/entropy_proxy.py` to detect timeout or API errors from the lightweight LLM proxy; implement the required **static fallback** (median rotation index) ONLY when the proxy fails, ensuring the pipeline continues without crashing, while logging the failure event for audit.
- [X] T044 [P] [Performance] Refactor `code/run_correlation.py` and `code/run_router_inference.py` to use **streaming** for the MS-COCO dataset where memory is a bottleneck, ensuring the full dataset is processed in chunks without loading it entirely into RAM, while maintaining the statistical integrity of the variance calculation.
- [X] T045 [P] [Validation] Add a sanity check task in `code/validation/validate_clustering.py` to verify that the derived rotation matrices in `clustering_report.json` are indeed orthogonal and have unit norm, preventing numerical instability in the W2A4 engine. **Deliverable**: Add a function in `code/validation/validate_clustering.py` that checks matrix orthogonality (dot product ~0) and unit norm (L2 ~1) for all 16 matrices in `clustering_report.json`.

---

## Phase 8: GPU Execution Validation & Scaling (Addressing Compute Constraints)

**Purpose**: Ensure the GPU escape hatch functions correctly for the specific DiT models (FLUX.1-dev, Wan 2.1) and that the "scaled-down" GPU task is correctly defined for the Kaggle environment to avoid CPU fabrication.

- [X] T046 [P] [GPU Validation] Create `code/run_gpu_validation.py` to explicitly test the GPU offload path: attempt to load FLUX.1-dev with `device="cuda"` and `load_in_8bit=True` on a dummy batch; if CUDA fails, trigger the Kaggle offload mechanism and verify the task re-runs successfully on the GPU runner; **Deliverable**: Verify `state/gpu_validation_log.json` contains a successful run record with `device=cuda` and `model=flux.1-dev` or `wan-2.1`. **This task does NOT depend on T022b**.
- [X] T047 [P] [Scaling] Refactor `code/analysis/entropy_proxy.py` to support a "scaled" mode for the Kaggle GPU runner: limit the number of paraphrase samples per prompt to 5 and the number of diverse prompts to 200 for the initial correlation run, ensuring the total VRAM usage stays under 12GB; **Deliverable**: Verify the script accepts a `--sample-size=5` and `--prompt-count=200` argument and logs the exact counts used. **Must depend on T046 and T017**.
- [X] T048 [P] [Streaming] Refactor `code/analysis/correlation.py` to process the MS-COCO validation set in chunks of 50 images, accumulating variance statistics online without holding the full batch in memory; **Deliverable**: Verify `code/analysis/correlation.py` uses a generator pattern and logs "Chunk processed: X" for each batch.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T017 (Correlation)** is in Phase 2, **independent of T022**.
 - **T023b (Validate Correlation)** is in Phase 2, depends on T017.
 - **T022 (Derive Matrices)** is in Phase 4, depends on T023b (Validation Success).
 - **T022c (Quantized Outputs)** is in Phase 4, depends on T022.
 - **T019 (MSE Validator)** is in Phase 4, depends on T022c.
- **Post-US1 Validation Gate (Phase 2.5)**: Depends on Phase 2 (Foundational) completion. BLOCKS Phase 4.
 - Validates `correlation_results.json` (T017).
 - **Execution Order**: T017 must be executed before T023b.
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion. **Must succeed** (p < 0.05) to justify US2.
- **User Story 2 (Phase 4)**: Depends on Phase 2.5 Validation Gate success.
- **User Story 3 (Phase 5)**: Depends on Phase 4 implementation and Foundational phase.
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on Phase 5 completion; addresses specific execution gate concerns.
- **GPU Validation (Phase 8)**: Depends on Phase 1 (Setup) and Phase 2 (Foundational) to ensure the GPU offload logic and model loaders are ready for testing. **T046 is independent of T022**.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). **Must succeed** (p < 0.05) to justify US2.
- **User Story 2 (P2)**: Depends on US1 results (correlation data) and Foundational phase.
- **User Story 3 (P3)**: Depends on US2 implementation and Foundational phase.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Helpers before Services
- Services before Orchestration scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding T017/T023b sequence)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 8 (GPU Validation) can run in parallel with Phase 6 (Polish) as it does not depend on US3 completion.

---

## Parallel Example: User Story 1

```bash
# Launch all tasks for User Story 1 together:
Task: "Unit test for entropy calculation in tests/unit/test_entropy.py"
Task: "Integration test for variance measurement in tests/integration/test_activation_variance.py"

# Launch all models/helpers for User Story 1 together:
Task: "Implement entropy_proxy.py"
Task: "Implement correlation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, **includes T017 Correlation**)
3. Complete Phase 2.5: Validation Gate (Validate T017)
4. **STOP and VALIDATE**: Test User Story 1 independently. If correlation is not significant, the project may pivot or stop.
5. Deploy/demo results if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Phase 2.5 Validation Gate → Validate US1 results
4. Add User Story 2 → Test independently → Deploy/Demo (Requires T023b success)
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Correlation)
 - Developer B: User Story 2 (Router) - *Can start once US1 data schema is defined*
 - Developer C: User Story 3 (Evaluation) - *Can start once US2 API is defined*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **GPU Escape Hatch**: Tasks involving DiT generation (US1, US2, US3) must handle CPU failure gracefully and trigger the Kaggle GPU offload mechanism if the CPU runner lacks resources. **T041 (Phase 1)** implements this logic.
- **Data Hygiene**: No synthetic data. All prompts and images must come from the real MS-COCO dataset and diverse prompt repositories (`nlpconnect/vit-gpt2-image-captioning`). **T042** enforces fail-loud behavior.
- **Edge Cases**: Ensure router handles entropy out-of-range and proxy failures as per spec (clamp to boundary, fallback to median). **T043** implements the proxy failure fallback.
- **Validation Gate**: Phase 2.5 (T023a, T023b, T023c) is a blocking gate **AFTER** Phase 2 (Foundational), as required by Constitution Principle VI. **T017 (Correlation)** is in Phase 2 and is **independent of T022**.
- **Critical Methodological Correction**: T006c and T017 explicitly use diverse prompts as conditioning inputs for the DiT generation pass to measure activation variance.
- **FR-009 Validation**: T019 now depends on T022c, which generates the necessary quantized activations for MSE calculation.
- **Task ID Corrections**: T006a/T006b merged into T006. T022a/T022b merged into T022. T018 removed. T035 remains in Phase 5. T041 added to Phase 1. T042-T045 added to Phase 7 for robustness.
- **Removed Ambiguity**: T037 and T038 are now specific implementation tasks for modular runners and streaming. T040 explicitly validates against `state/artifact_hashes.json`. T045 explicitly checks orthogonality and unit norm.
- **New GPU Tasks**: T046, T047, T048 added to Phase 8 to explicitly validate the GPU offload path, implement scaled-down GPU execution for the Kaggle environment, and ensure streaming is used for memory efficiency during correlation. These tasks address the "Compute Feasibility" rule by ensuring the real GPU computation is scaled correctly (8-bit, limited samples) to fit the free Kaggle GPU constraints without fabricating a CPU imitation.
- **T042/T043 Status**: These tasks are marked [ ] (incomplete) and require revision to implement the fail-loud and fallback logic.