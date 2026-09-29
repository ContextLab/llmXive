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
- [X] T041 [P] Implement GPU Offload Logic: Create `code/utils/gpu_offload.py` to detect CPU failure on DiT generation tasks and trigger the Kaggle GPU offload mechanism; this is a critical infrastructure component required for T017 and T027.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and pre-computed artifacts that MUST be complete before ANY user story can be implemented. This includes the generation of rotation matrices (FR-003) and quantized activations (FR-009) required for the Validation Gate.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with hyperparameters, paths, seeds, and device detection logic (CPU default, GPU escape hatch flag)
- [X] T005 [P] Implement `code/data/download_coco.py` to fetch MS-COCO validation set (captions + images) using `datasets.load_dataset` with streaming disabled for local caching; ensure no synthetic fallbacks
- [ ] T006a [P] Implement `code/data/preprocess.py` to extract captions from MS-COCO into `data/processed/prompts.csv`
- [ ] T006b [P] Run `code/data/preprocess.py` to generate `data/processed/prompts.csv` and split into `data/processed/prompts_train.csv` and `data/processed/prompts_test.csv`
- [X] T006c [P] Implement `code/data/download_diverse_prompts.py` to fetch a diverse set of text prompts from verified public repositories (e.,g., `nlpconnect/vit-gpt2-image-captioning` dataset on HuggingFace); **CRITICAL**: Extract captions from this dataset to use as prompts; ensure no synthetic fallbacks; if a real source cannot be verified, the task must fail loudly
- [ ] T006d [P] Run `code/data/download_diverse_prompts.py` to generate `data/processed/diverse_prompts.csv`
- [X] T007 Implement `code/models/flux_wan_loader.py` to load FLUX.1-dev/Wan 2.1 (GPU) or Stable Diffusion 2.1 (CPU) with hooks for activation capture during the **text-to-image generation loop**
- [X] T008 Implement `code/models/dit_wrapper.py` to inject hooks into DiT intermediate layers for capturing float32 activation tensors **during the generative trajectory** (text-to-image generation conditioned on prompt)
- [X] T009 Implement `code/analysis/entropy_proxy.py` using a lightweight LLM (e.g., `transformers` with `do_sample=True`) to compute semantic entropy via **generative paraphrase sampling** (generate multiple paraphrases, cluster them, compute entropy)
- [X] T010 Implement `code/quantization/w2a4_engine.py` for W2A4 quantization with rotation matrix application capability
- [X] T011 Implement `code/quantization/static_baseline.py` implementing the original OrbitQuant static rotation logic for comparison
- [X] T022a [P] [Shared] Implement `code/analysis/clustering.py` to perform K-Means clustering on activation histograms; this task creates the logic but does not generate the final matrices yet.
- [ ] T022b [P] [Foundational] Run `code/analysis/clustering.py` on the **train split** of activation variances to derive $K=16$ pre-optimized rotation matrices and generate `data/processed/clustering_report.json` containing layers, subsets, boundaries, and matrices; **this task is MANDATORY and unconditional** (does not depend on T017 success) to satisfy FR-003 and Constitution Principle VI. <!-- FAILED: unspecified -->
- [X] T022c [P] [Foundational] Implement and run `code/run_quantization_validation.py` to generate quantized activations using the rotation matrices from T022b (or static baseline if T022b fails validation) on the MS-COCO validation set; generate `data/processed/quantized_activations.json`; **must depend on T022b**.
- [X] T019 [US1] Implement `code/analysis/mse_validator.py` to compute MSE quantization error on the **quantized activations generated by T022c** vs. float32 targets to validate the variance-sensitivity hypothesis; **must depend on T022c**.
- [X] T017 [US1] Implement `code/run_correlation.py` orchestration script: Load prompts (from T006c) -> Compute Entropy -> Run DiT Generation (GPU/CPU) **using prompts as conditioning inputs** -> Capture Variances -> Compute Correlation -> Generate `data/processed/correlation_results.json`; **must depend on T006d and T007/T008**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Post-US1 Validation Gate (Blocking Pre-Implementation of Router)

**Purpose**: Validate `clustering_report.json` and correlation results before Router Implementation (Constitution Principle VI)

**⚠️ CRITICAL**: This phase runs AFTER Phase 2 (Foundational) completion and blocks Phase 4 (US2). It validates that the correlation is significant and the matrices are derived correctly.

- [X] T023a [P] Implement `code/validation/validate_clustering.py` to verify `data/processed/clustering_report.json` exists, contains required keys (layers, subsets, boundaries, matrices), and validates structure
- [X] T023b [P] Implement `code/validation/validate_correlation.py` to verify `data/processed/correlation_results.json` exists and p-value < 0.05
- [X] T023c [P] Implement `code/main_validation.py` orchestration script for Phase 2.5: Run T023a and T023b; if validation fails, halt execution and log error; if valid, proceed to Phase 4

---

## Phase 3: User Story 1 - Establish Correlation between Prompt Entropy and Activation Variance (Priority: P1) 🎯 MVP

**Goal**: Empirically determine if a statistical correlation exists between prompt semantic entropy and DiT activation variance.

**Independent Test**: Run the correlation analysis pipeline on the MS-COCO validation set with a curated set of prompts, outputting a correlation coefficient and p-value.

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for `code/analysis/entropy_proxy.py` entropy calculation logic in `tests/unit/test_entropy.py`
- [X] T013 [P] [US1] Integration test for variance measurement hook in `tests/integration/test_activation_variance.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/analysis/correlation.py` to compute Pearson correlation coefficient and p-value between entropy scores and activation variances
- [X] T015 [US1] Implement `code/analysis/diagnostic.py` to perform collinearity checks on multi-layer variances and log outliers
- [X] T016 [US1] Implement `code/analysis/visualization.py` to generate scatter plots of entropy vs. variance for visual inspection
- [X] T019 [US1] Implement `code/analysis/mse_validator.py` to compute MSE quantization error on the **quantized activations generated by T022c** vs. float32 targets to validate the variance-sensitivity hypothesis; **must depend on T022c**.

**Checkpoint**: Correlation analysis complete; if p < 0.05, proceed to Phase 2.5 (Validation Gate).

---

## Phase 4: User Story 2 - Implement Dynamic Rotation Router based on Entropy (Priority: P2)

**Goal**: Implement a lightweight router that maps prompt semantic entropy to a pre-optimized rotation matrix.

**Independent Test**: Feed a prompt with known entropy into the router and verify the correct rotation matrix index is selected and applied.

### Tests for User Story 2

- [X] T020 [P] [US2] Contract test for router lookup logic in `tests/unit/test_router.py`
- [X] T021 [P] [US2] Integration test for rotation application in `tests/integration/test_rotation_application.py`

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/analysis/router.py` to map entropy scores to matrix indices with clamping logic for out-of-range values and outlier handling
- [X] T025 [US2] Update `code/quantization/w2a4_engine.py` to integrate the dynamic router logic for selecting the rotation matrix during inference
- [ ] T028 [P] [US2] Implement `code/analysis/load_matrices.py` to load and verify the pre-computed rotation matrices from `data/processed/clustering_report.json` (generated by T022b); **must depend on T022b**.
- [X] T029 [US2] Implement `code/run_router_inference.py` orchestration script for Phase 2 Inference: Load Test Split -> Compute Entropy -> Load Matrices (T028) -> Select Matrix -> Generate Images -> Log Metrics; **must depend on T028**.

**Checkpoint**: Dynamic router implemented and integrated with W2A4 engine.

---

## Phase 5: User Story 3 - Evaluate Fidelity Gains and Runtime Overhead (Priority: P3)

**Goal**: Compare dynamic router method against static baseline using perceptual metrics and measure runtime overhead.

**Independent Test**: Run both methods on the same prompts, compute FID/CLIP/MSE, and calculate percentage increase in inference time.

### Tests for User Story 3

- [X] T028 [P] [US3] Contract test for metric calculation in `tests/unit/test_metrics.py`
- [X] T029 [P] [US3] Integration test for end-to-end pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/evaluation/metrics.py` to compute FID, CLIP scores, and MSE using CPU-compatible implementations
- [X] T031 [US3] Implement `code/evaluation/timing.py` to measure wall-clock inference time for both static and dynamic methods
- [X] T032 [US3] Implement `code/analysis/statistical_test.py` to perform paired t-tests on metric distributions; **conditionally apply Bonferroni correction** if the number of comparisons exceeds a defined threshold (e.g., >3); define threshold in config
- [X] T033 [US3] Implement `code/analysis/sensitivity.py` to sweep entropy cut-off points by **±5% of the total observed entropy range calculated from T017 (correlation_results.json)** and report variance in FID scores; **must depend on T017**.
- [X] T034 [US3] Implement `code/run_evaluation.py` orchestration script for Phase 3: Run Baseline -> Run Dynamic -> Compute Metrics -> Run Statistical Tests -> Generate `data/processed/final_evaluation_report.json`

**Checkpoint**: All user stories complete; final report generated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates: Update `README.md` with GPU escape hatch instructions and API docs for `code/analysis/router.py`; add usage examples for `code/run_correlation.py` and `code/run_router_inference.py`.
- [~] T037 Code cleanup and refactoring of `code/` into modular runners
- [~] T038 Performance optimization for data loading and streaming
- [~] T039 [P] Additional unit tests for edge cases (entropy out-of-range, proxy failure) in `tests/unit/`
- [ ] T040 [P] Security hardening: Sanitize file paths in data loading; validate model checksums against `state/artifact_hashes.json` before loading.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T022a (Clustering Logic)** is in Phase 2 to ensure code exists.
 - **T022b (Derive Matrices)** is in Phase 2, **unconditional**, and **before T017**.
 - **T022c (Quantized Outputs)** is in Phase 2, depends on T022b.
 - **T017 (Correlation)** is in Phase 2, depends on T006d, T007, T008.
- **Post-US1 Validation Gate (Phase 2.5)**: Depends on Phase 2 (Foundational) completion. BLOCKS Phase 4.
 - Validates `clustering_report.json` (T022b) and `correlation_results.json` (T017).
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion. **Must succeed** (p < 0.05) to justify US2.
- **User Story 2 (Phase 4)**: Depends on Phase 2.5 Validation Gate success.
- **User Story 3 (Phase 5)**: Depends on Phase 4 implementation and Foundational phase.
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). **Must succeed** (p < 0.05) to justify US2.
 - **T019 (MSE Validator)** now depends on **T022c (Quantized Outputs)**.
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

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
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, **includes T022a Logic, T022b Matrices, T022c Quantized Outputs, T017 Correlation**)
3. Complete Phase 2.5: Validation Gate (Validate T022b and T017)
4. **STOP and VALIDATE**: Test User Story 1 independently. If correlation is not significant, the project may pivot or stop.
5. Deploy/demo results if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Phase 2.5 Validation Gate → Validate US1 results
4. Add User Story 2 → Test independently → Deploy/Demo
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
- **Data Hygiene**: No synthetic data. All prompts and images must come from the real MS-COCO dataset and diverse prompt repositories (`nlpconnect/vit-gpt2-image-captioning`).
- **Edge Cases**: Ensure router handles entropy out-of-range and proxy failures as per spec (clamp to boundary, fallback to median).
- **Validation Gate**: Phase 2.5 (T023a, T023b, T023c) is a blocking gate **AFTER** Phase 2 (Foundational), as required by Constitution Principle VI. **T022b (Derive Matrices)** is in Phase 2 and is **unconditional**.
- **Critical Methodological Correction**: T006c and T017 explicitly use diverse prompts as conditioning inputs for the DiT generation pass to measure activation variance.
- **FR-009 Validation**: T019 now depends on T022c, which generates the necessary quantized activations for MSE calculation.
- **Task ID Corrections**: T006a (Preprocess), T006b (Run Preprocess), T006c (Download Diverse), T006d (Run Diverse). T022b (Derive Matrices), T022c (Run Quant Script). T018 and T035 removed (merged into T017 and T034). T026 renamed to T029. T041 added to Phase 1.