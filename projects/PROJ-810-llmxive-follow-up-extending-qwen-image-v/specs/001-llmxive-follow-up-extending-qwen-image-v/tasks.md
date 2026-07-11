# Tasks: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-qwen-image-v/`
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

## Phase 0: Feasibility & Power Analysis (Pre-Execution)

**Purpose**: Critical pre-execution steps to determine sample size, model availability, and memory constraints.

- [ ] T000 [P] [Feasibility] Implement `src/analysis/separability.py` -> Power Analysis (Task 0.1). **Logic**: Calculate minimum N required for [deferred] power (d > 0.8). **Deliverable**: `data/results/power_analysis.json` containing `N_required`, `effect_size`, `power`, and `N_audit` (sample size for manual audit).
- [ ] T001 [P] [Feasibility] Implement `src/models/vae_loader.py` -> Model Availability & Fallback Validation (Task 0.2). Verify `Qwen-Image-VAE-2.0` exists and is CPU-feasible. If not, trigger Model Substitution Protocol. **Deliverable**: `data/results/model_availability.json` with status and fallback model ID.
- [ ] T002 [P] [Feasibility] Implement `src/utils/memory.py` -> Memory Budget Check (Task 0.3). Estimate peak RAM for VAE + OCR + Classifier. Configure chunk size or fallback to smaller N if > 7GB. **Deliverable**: `data/results/memory_budget.json` with `chunk_size`, `max_samples`, `fallback_strategy`.
- [ ] T002b [P] [Feasibility] Implement `src/utils/memory.py` -> Runtime Fallback Logic (Task 0.4). **Logic**: If `N_required` (from T000) exceeds estimated 6h runtime, reduce N to `N_fallback` and flag `runtime_inconclusive` status. **Deliverable**: `data/results/runtime_fallback.json` with `N_final`, `estimated_runtime`, `status` (PASS/INCONCLUSIVE).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T003a [P] Create project directory structure (`src/`, `tests/`, `specs/`, `data/`, `data/results/`, `data/manual/`)
- [ ] T003b [P] Initialize git repository (if not already initialized)
- [ ] T003c [P] Create `.gitignore` for Python/ML artifacts (`.pyc`, `__pycache__`, `data/raw/`, `data/interim/`)
- [ ] T004 [P] Initialize Python 3.11 project with `requirements.txt` (pinning `torch`, `transformers`, `scikit-learn`, `pandas`, `opencv-python`, `paddleocr`, `pillow`, `numpy`, `pytest`)
- [ ] T005 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Implement `src/data/download.py` to fetch `OmniDoc-TokenBench` dataset. **Logic**: Resolve specific subset ID from Qwen-Image-VAE-2.0 report reference (do NOT hardcode `Omni-Doc-1`). Compute checksum. **Deliverable**: `data/raw/omnidoc_tokenbench.parquet` and `data/results/checksum.json`.
- [ ] T007 [P] Implement `src/models/vae_loader.py` to load `Qwen-Image-VAE-2.0` in CPU-only mode with fallback protocol (already partially done in T001, finalize implementation)
- [ ] T008 [P] Implement `src/data/preprocess.py` -> Region extraction based on bounding boxes. **Deliverable**: `data/interim/regions_crops.parquet` (unlabeled images).
- [ ] T009 [P] Implement `src/data/preprocess.py` -> Heuristic label derivation (OCR density). **Logic**: Derive "text"/"image" labels using OCR density. **Deliverable**: `data/interim/heuristic_labels_ocr.csv`.
- [ ] T010 [P] Implement `src/data/preprocess.py` -> Heuristic label derivation (Aspect Ratio). **Logic**: Derive "text"/"image" labels using aspect ratio. **Deliverable**: `data/interim/heuristic_labels_ar.csv`.
- [ ] T011 [P] Implement `src/data/preprocess.py` -> Manual Audit Logic (Task 1.4). **Logic**: Randomly sample N_audit regions (seed=42, size=N_audit from T000) from `data/interim/heuristic_labels_ocr.csv`. Compare against manual labels in `data/manual/audit_labels.csv` (schema: region_id, human_label). Halt if agreement < 80%. **Deliverable**: `data/results/label_audit.json` with `agreement_rate`, `status` (PASS/FAIL).
- [ ] T012 [P] Implement `src/data/preprocess.py` -> Cross-Modal Validation (Task 1.5). Derive a second set of labels using edge density heuristic. Compare against OCR-derived labels. **Deliverable**: `data/interim/cross_modal_labels.csv` and `data/results/cross_modal_agreement.json`.
- [ ] T013 [P] Implement `src/utils/logging.py` for structured logging and error tracking
- [ ] T014 [P] Implement `src/utils/metrics.py` with wrappers for Masked SSIM and LPIPS (CPU-safe)
- [ ] T015 [P] Implement `src/data/cache/` directory structure for intermediate latent vector storage
- [ ] T016 [P] [US1] Unit test for `src/data/download.py` checksum validation in `tests/unit/test_download.py`
- [ ] T017 [P] [US1] Unit test for `src/models/vae_loader.py` CPU fallback logic in `tests/unit/test_vae_loader.py`
- [ ] T018 [P] [US1] Unit test for `src/data/preprocess.py` region extraction in `tests/unit/test_preprocess.py`
- [ ] T019 [P] [US1] Integration test for end-to-end encoding pipeline on sample data in `tests/integration/test_encoding_pipeline.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Latent Space Disentanglement Analysis (Priority: P1) 🎯 MVP

**Goal**: Encode document image regions into latent vectors and verify linear separability between text and image modalities using a lightweight classifier.

**Independent Test**: Run encoding and classification on a sampled subset; report accuracy ≥ 90% and F1 ≥ 0.90 against ground-truth labels.

### Implementation for User Story 1

- [ ] T020 [US1] Implement `src/analysis/separability.py` -> Triviality Check (Task 2.1) on raw pixel stats. **Deliverable**: `data/results/triviality_check.json`.
- [ ] T021 [US1] Implement `src/analysis/separability.py` -> Latent Encoding with chunked processing (Task 2.2). **Deliverable**: `data/interim/latent_vectors.parquet` (unlabeled features).
- [ ] T022 [US1] Implement `src/analysis/separability.py` -> Data Splitting. **Logic**: Split `latent_vectors.parquet` into `training_features` (unlabeled) and `evaluation_labels` (ground truth from audit/cross-modal). Ensure classifier training (T023) uses ONLY `training_features`. **Deliverable**: `data/interim/split_data.json` (paths to train/eval).
- [ ] T023 [US1] Implement `src/models/classifier.py` -> Train Linear SVM on full latent dimensionality (Task 2.3). **Logic**: **Fit model using ONLY training_features (unlabeled). Inject evaluation_labels ONLY for post-fit metric calculation.** **Deliverable**: `data/results/us1_metrics.json` with `accuracy`, `f1_score`, `model_path`, `optimal_boundary`.
- [ ] T024 [US1] Implement `src/analysis/separability.py` -> Permutation Test (1000 iterations) for p-value < 0.05 (Task 2.4). **Deliverable**: `data/results/permutation_pvalue.json` with `p_value`, `observed_accuracy`, `null_distribution_mean`.
- [ ] T025 [US1] Implement `src/analysis/separability.py` -> Threshold Sweep for Optimal Boundary (Task 2.5). **Logic**: Sweep thresholds to find the boundary that maximizes F1. **Deliverable**: `data/results/us1_threshold_sweep.json` with `optimal_boundary` and `metrics_at_boundary`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Zero-Shot Semantic Editing via Vector Arithmetic (Priority: P2)

**Goal**: Perform linear vector arithmetic on latent representations to swap text content while preserving layout.

**Independent Test**: Compute $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$, decode, and verify text change with Masked SSIM ≥ 0.85 and OCR accuracy ≥ 95%.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US2] Unit test for `src/utils/metrics.py` Masked SSIM calculation in `tests/unit/test_metrics.py`
- [ ] T027 [P] [US2] Integration test for vector arithmetic and decoding in `tests/integration/test_editing.py`

### Implementation for User Story 2

- [ ] T028 [US2] Implement `src/analysis/editing.py` -> Linearity Verification (Task 3.1) with small $\alpha$ steps. **Logic**: If linearity check fails, write failure report to `data/results/linearity_check.json` and HALT pipeline. **Deliverable**: `data/results/linearity_check.json` with `is_linear`, `message`.
- [ ] T029 [US2] Implement `src/analysis/editing.py` -> Centroid computation for text/image clusters (Task 3.2). **Dependency**: Requires T021 (Latent Vectors) and T023 (Labels). **Deliverable**: `data/results/centroids.json`.
- [ ] T030 [US2] Implement `src/analysis/editing.py` -> Vector Arithmetic ($z_{new}$ calculation) logic. **Dependency**: Requires T029 (Centroids) and T028 (Linearity Check passed).
- [ ] T031 [US2] Implement `src/analysis/editing.py` -> Decoding and Masked SSIM evaluation (Task 3.3). **Deliverable**: `data/results/us2_metrics.json` with `ssim`, `ocr_accuracy`, `execution_time`.
- [ ] T032 [US2] Implement `src/analysis/editing.py` -> OCR validation using PaddleOCR v (Task 3.3).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds and report statistical robustness without cross-metric corrections.

**Independent Test**: Verify stability of error rates across threshold sweeps and confirm p-values for distinct metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `src/analysis/sensitivity.py` -> Robustness Verification (Task 3.1). **Logic**: Re-run threshold sweep around `optimal_boundary` (from T023) to measure **variation in false-positive rates** specifically for SC-005. **Deliverable**: `data/results/us3_sensitivity.json` with `threshold`, `false_positive_rate`, `false_negative_rate`, `variation_metric`.
- [ ] T035 [US3] Implement `src/analysis/sensitivity.py` -> Individual significance tests for accuracy, F1, SSIM (Task 3.2). **Constraint**: **NO cross-metric corrections (e.g., Bonferroni, Holm)**. **DO NOT call statsmodels.stats.multitest or similar. Compute raw p-values only.** **Deliverable**: `data/results/us3_significance.json` with `metric`, `p_value`, `significant`.
- [ ] T036 [US3] Implement `src/analysis/sensitivity.py` -> Power analysis reporting (inconclusive if power < 0.8) (Task 3.3). **Deliverable**: `data/results/power_report.json` with `achieved_power`, `conclusion`, `limitation_text`, `N_actual`.
- [ ] T037 [US3] Generate final statistical report to `data/results/us3_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T038 [P] Generate final research report compiling metrics, plots, and limitations in `research.md`
- [ ] T039 [P] Update `quickstart.md` with execution instructions for the full pipeline
- [ ] T040 Run `pytest` with coverage to ensure all paths are tested
- [ ] T041 Validate `data/results/*.json` schemas against `contracts/output.schema.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Feasibility)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on centroids from US1 (T029)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Aggregates metrics from US1/US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download/preprocessing before encoding
- Encoding before classification/editing
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
Task: "Unit test for src/data/download.py checksum validation in tests/unit/test_download.py"
Task: "Unit test for src/models/vae_loader.py CPU fallback logic in tests/unit/test_vae_loader.py"

# Launch preprocessing and encoding tasks together:
Task: "Implement src/data/preprocess.py -> Region extraction"
Task: "Implement src/analysis/separability.py -> Triviality Check on raw pixel stats"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Feasibility
2. Complete Phase 1: Setup
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

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All VAE operations must use chunked processing to stay within available RAM constraints.
- **Constraint**: No GPU/CUDA dependencies; fallback protocol must be triggered if model unavailable.
- **Critical Methodology**: Classifier training (T023) MUST use ONLY unlabeled features; labels are used ONLY for evaluation.
- **Critical Methodology**: Significance tests (T035) MUST NOT apply cross-metric corrections.