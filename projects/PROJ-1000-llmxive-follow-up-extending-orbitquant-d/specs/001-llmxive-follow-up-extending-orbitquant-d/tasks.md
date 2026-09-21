# Tasks: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [ ] T002 Initialize Python project with dependencies (`torch`, `transformers`, `diffusers`, `datasets`, `scikit-learn`, `accelerate`, `sentence-transformers`, `peft`, `fid-score`, `clip-score`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and pre-computed artifacts that MUST be complete before ANY user story can be implemented. This includes the generation of rotation matrices (FR-003) required for the validation gate.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with hyperparameters, paths, seeds, and device detection logic (CPU default, GPU escape hatch flag)
- [X] T005 [P] Implement `code/data/download_coco.py` to fetch MS-COCO validation set (captions + images) using `datasets.load_dataset` with streaming disabled for local caching; ensure no synthetic fallbacks
- [ ] T006 [P] Implement `code/data/preprocess.py` to extract captions into `data/processed/prompts.csv` and split into train/test sets
- [X] T006a [P] Implement `code/data/download_diverse_prompts.py` to fetch a diverse set of text prompts from verified public repositories (e.g., HuggingFace Hub datasets containing diverse captions) and merge with MS-COCO captions; **CRITICAL**: These prompts MUST be used as the conditioning inputs for the DiT generation pass in T017 to measure activation variance (per plan.md Critical Methodological Correction); ensure no synthetic fallbacks; if a real source cannot be verified, the task must fail loudly
- [X] T007 Implement `code/models/flux_wan_loader.py` to load FLUX.1-dev/Wan 2.1 (GPU) or Stable Diffusion 2.1 (CPU) with hooks for activation capture during the **text-to-image generation loop**
- [X] T008 Implement `code/models/dit_wrapper.py` to inject hooks into DiT intermediate layers for capturing float32 activation tensors **during the generative trajectory** (text-to-image generation conditioned on prompt)
- [X] T009 Implement `code/analysis/entropy_proxy.py` using a lightweight LLM (e.g., `transformers` with `do_sample=True`) to compute semantic entropy via **generative paraphrase sampling** (generate multiple paraphrases, cluster them, compute entropy)
- [X] T010 Implement `code/quantization/w2a4_engine.py` for W2A4 quantization with rotation matrix application capability
- [X] T011 Implement `code/quantization/static_baseline.py` implementing the original OrbitQuant static rotation logic for comparison
- [ ] T022 [P] [Shared] Implement `code/analysis/clustering.py` and generate `data/processed/clustering_report.json` containing layers, subsets, boundaries, and the K=16 pre-optimized rotation matrices derived from clustering activation histograms of the MS-COCO train split **generated trajectories**; this task is a prerequisite for the Validation Gate (Phase 2.5) and must run regardless of Phase 3 outcome.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Validation Gate (Blocking Pre-Implementation)

**Purpose**: Validate `clustering_report.json` before Router Implementation (Constitution Principle VI)

**⚠️ CRITICAL**: Phase 3 cannot begin until this phase is complete

- [ ] T023a [P] Implement `code/validation/validate_clustering.py` to verify `data/processed/clustering_report.json` exists, contains required keys (layers, subsets, boundaries, matrices), and validates structure before Phase 3
- [X] T023b [P] Implement `code/main.py` orchestration script for Phase 2.5: Run T023a; if validation fails, halt execution and log error; if valid, proceed to Phase 3

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
- [X] T017 [US1] Implement `code/run_correlation.py` orchestration script: Load prompts (from T006a) -> Compute Entropy -> Run DiT Generation (GPU/CPU) **using prompts as conditioning inputs** -> Capture Variances -> Compute Correlation -> Save Results
- [ ] T018 [US1] Generate `data/processed/correlation_results.json` containing the correlation coefficient, p-value, and raw data points
- [ ] T019a [US1] Implement `code/run_quantization_validation.py` to run the W2A4 engine (T010) on the MS-COCO validation set using the rotation matrices from T022 to generate `data/processed/quantized_activations.json`; **this task explicitly generates the artifact required for T019**
- [X] T019 [US1] Implement `code/analysis/mse_validator.py` to compute MSE quantization error on the **quantized activations generated by T019a** vs. float32 targets to validate the variance-sensitivity hypothesis; **must depend on T019a and T017**

**Checkpoint**: Correlation analysis complete; if p < 0.05, proceed to US2.

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
- [X] T026 [US2] Implement `code/run_router_train.py` orchestration script for Phase 2 Training: Load Train Split -> Cluster -> Generate Matrices -> Save Lookup Table (Note: T022 already performs the heavy lifting; this script orchestrates the specific train/test split usage if needed)
- [ ] T027 [US2] Implement `code/run_router_inference.py` orchestration script for Phase 2 Inference: Load Test Split -> Compute Entropy -> Select Matrix -> Generate Images -> Log Metrics

**Checkpoint**: Dynamic router implemented and integrated with W2A4 engine.

---

## Phase 5: User Story 3 - Evaluate Fidelity Gains and Runtime Overhead (Priority: P3)

**Goal**: Compare dynamic router method against static baseline using perceptual metrics and measure runtime overhead.

**Independent Test**: Run both methods on the same prompts, compute FID/CLIP/MSE, and calculate percentage increase in inference time.

### Tests for User Story 3

- [ ] T028 [P] [US3] Contract test for metric calculation in `tests/unit/test_metrics.py`
- [ ] T029 [P] [US3] Integration test for end-to-end pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/evaluation/metrics.py` to compute FID, CLIP scores, and MSE using CPU-compatible implementations
- [ ] T031 [US3] Implement `code/evaluation/timing.py` to measure wall-clock inference time for both static and dynamic methods
- [ ] T032 [US3] Implement `code/analysis/statistical_test.py` to perform paired t-tests on metric distributions; **conditionally apply Bonferroni correction** if the number of comparisons exceeds a defined threshold (e.g., >3); define threshold in config
- [ ] T033 [US3] Implement `code/analysis/sensitivity.py` to sweep entropy cut-off points by **±5% of the total observed entropy range calculated from the Phase 3 results (T018)** and report variance in FID scores
- [ ] T034 [US3] Implement `code/run_evaluation.py` orchestration script for Phase 3: Run Baseline -> Run Dynamic -> Compute Metrics -> Run Statistical Tests -> Generate Report
- [ ] T035 [US3] Generate `data/processed/final_evaluation_report.json` containing all metrics, p-values, and overhead calculations

**Checkpoint**: All user stories complete; final report generated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `docs/`
- [ ] T037 Code cleanup and refactoring of `code/` into modular runners
- [ ] T038 Performance optimization for data loading and streaming
- [ ] T039 [P] Additional unit tests for edge cases (entropy out-of-range, proxy failure) in `tests/unit/`
- [ ] T040 Security hardening of data paths and model loading

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T022 (Clustering)** is now in Phase 2 to ensure `clustering_report.json` exists for Phase 2.5.
- **Validation Gate (Phase 2.5)**: Depends on T022 (clustering report generation) - BLOCKS Phase 3
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must succeed** (p < 0.05) to justify US2.
 - **T019 (MSE Validator)** now depends on **T019a (Quantized Outputs)** and **T017 (Variances)**.
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
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, **includes T022 Clustering**)
3. Complete Phase 2.5: Validation Gate (Validates T022 output)
4. Complete Phase 3: User Story 1 (Includes T019a to generate quantized data for T019)
5. **STOP and VALIDATE**: Test User Story 1 independently. If correlation is not significant, the project may pivot or stop.
6. Deploy/demo results if ready.

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
- **GPU Escape Hatch**: Tasks involving DiT generation (US1, US2, US3) must handle CPU failure gracefully and trigger the Kaggle GPU offload mechanism if the CPU runner lacks resources.
- **Data Hygiene**: No synthetic data. All prompts and images must come from the real MS-COCO dataset and diverse prompt repositories.
- **Edge Cases**: Ensure router handles entropy out-of-range and proxy failures as per spec (clamp to boundary, fallback to median).
- **Validation Gate**: Phase 2.5 (T023a, T023b) is a blocking gate before Phase 3 (Router) implementation, as required by Constitution Principle VI. **T022 (Clustering) is now in Phase 2 to ensure the artifact exists for this gate.**
- **Critical Methodological Correction**: T006a and T017 explicitly use prompts as conditioning inputs for the DiT generation pass to measure activation variance.
- **FR-009 Validation**: T019 now depends on T019a, which generates the necessary quantized activations for MSE calculation.