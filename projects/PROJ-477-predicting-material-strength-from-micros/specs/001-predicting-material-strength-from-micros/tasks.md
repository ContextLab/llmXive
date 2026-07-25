# Tasks: Predicting Material Strength from Microstructure Images

**Input**: Design documents from `/specs/001-predict-material-strength-cnn/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Write script `scripts/scaffold.py` to create the exact directory tree per implementation plan (`projects/PROJ-477-predicting-material-strength-from-micros/`) including `data/raw`, `data/processed`, `code`, `tests`, `results`.
- [X] T002 Create `code/requirements.txt` containing the following pinned versions: PyTorch (CPU), torchvision, scikit-learn, pandas, numpy, matplotlib, opencv-python-headless, huggingface-hub, voronoi.
- [X] T003 [P] Create `code/.ruff.toml` and `code/pyproject.toml` with linting (ruff) and formatting (black) rules enabled.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup seed configuration and path management in `code/utils/config.py`
- [X] T005 [P] Implement batch loading strategy to prevent OOM on constrained memory in `code/data/loader.py`
- [X] T006 [P] Create base data structures `MicrostructureImage` and `YieldStrengthValue` Pydantic models in `code/data/models.py` with fields from data-model.md.
- [X] T007 [P] Create `code/utils/logging_config.py` that initializes a logger writing to `results/metrics.log` and `results/metrics.json` with the specified JSON schema.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic microstructure-strength dataset (Voronoi + Hall-Petch), preprocess EBSD images (224x224, normalize), and split into train/val/test sets with manifests.

**Independent Test**: The pipeline can be fully tested by running the data generation script and verifying that the resulting train/validation/test directories contain the correct number of image files and that a corresponding CSV/JSON manifest correctly maps image filenames to yield strength values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for image resizing and normalization in `tests/unit/test_preprocess.py`
- [X] T010 [P] [US1] Integration test for full generation and split workflow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T040 [US1] **CRITICAL**: Implement synthetic data generator in `code/data/generate.py` using Voronoi tessellation and Hall-Petch relation to create images and labels. **NO external download**; this is the PRIMARY data source. Raise hard exception if generation fails. (Replaces T011 download).
- [X] T041 [US1] Implement image preprocessor in `code/data/preprocess.py` (Resize to 224x224, normalize, handle aspect ratios/depths per Edge Cases).
- [X] T013 [US1] Implement data splitter in `code/data/split.py` (Stratified split into train/val/test by specimen ID, generate manifest).
- [X] T042 [US1] **CRITICAL**: Create `code/data/validate.py` that outputs `results/validation_report.json` containing the invalid pair count and exits with code 1 if invalid ratio > 1%. Schema: `{invalid_count: int, total_count: int, invalid_ratio: float}`. Exit logic: if `invalid_ratio > 0.01`, exit(1); else exit(0). Validates the synthetic source integrity.
- [X] T022 [Shared] **Moved to Phase 3**: Extract grain size features for **split subsets** (train/val/test) ONLY in `code/data/extract_features.py` (FR-009). **Depends on T013**. Output: `data/processed/grain_features.csv` with schema: `image_id`, `grain_size_um`, `split`. **Post-split extraction prevents data leakage**.
- [X] T008 [US1] **Moved to Phase 3**: Generate Hall-Petch ground truth labels for the training set in `code/data/label_generator.py`. **Depends on T040**. This task generates the scalar `yield_strength` labels used for training the CNN, derived from the generated grain morphology (Voronoi), not the preprocessed images. (Prevents data leakage).
- [X] T015 [US1] Create orchestration script `code/data/process_all.py` to chain generate -> preprocess -> split -> validate -> extract_features -> label_generate.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Evaluation (Priority: P2)

**Goal**: Train lightweight CNN (MobileNetV2/ResNet-18 frozen) on CPU with augmentation, compare against naive baseline, and perform statistical significance testing.

**Independent Test**: The model training and evaluation can be tested independently by executing the training script with a fixed random seed and verifying that it completes within the time limit, produces a model artifact, and outputs a report containing MSE and R² metrics for both the CNN and the baseline mean predictor.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for metric calculation (MSE, R²) in `tests/unit/test_metrics.py`
- [X] T017 [P] [US2] Integration test for training loop with early stopping in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement CNN model definition (MobileNetV2/ResNet-18 frozen backbone) in `code/models/cnn.py` (FR-002)
- [X] T019 [P] [US2] Implement naive mean baseline predictor in `code/models/baseline.py` (FR-004)
- [X] T020 [US2] Implement data augmentation transforms (random rotation, flip, brightness) in `code/train/augment.py` (FR-003)
- [X] T021 [US2] Implement training loop with early stopping (patience=5) and checkpoint saving in `code/train/trainer.py`
- [X] T023 [US2] Implement physics-based baseline (Hall-Petch predictor) in `code/models/physics_baseline.py` (Plan Phase 2 Task 2.4). **Depends on T022**. This task implements the evaluation baseline using the extracted grain features to predict strength, separate from the CNN training labels.
- [X] T024 [US2] Implement evaluation logic: MSE, R², and **single-sample t-test** (α=0.05) on squared errors comparing CNN error to baseline error in `code/eval/metrics.py` (FR-005, SC-002). **Note**: Implements single-sample t-test as per Spec FR-005.
- [X] T025 [US2] Implement Null Hypothesis Protocol: **If R² < 0.2**, write `results/null_hypothesis_report.json` with schema: `{status: "accepted" | "rejected", r2_value: float, threshold: float}` and exit with code 0 (success) in `code/eval/evaluator.py` (Plan Phase 3 Task 3.6). Treats R² < 0.2 as a valid scientific outcome, not a system error. The `status` field MUST be "accepted" if R² < 0.2, otherwise "rejected".
- [X] T026 [US2] Create main training orchestration script `code/main.py` supporting `--no-augmentation` flag for ablation study (Plan Phase 2 Task 2.2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps, perform sensitivity analysis on prediction thresholds, and calculate confidence intervals.

**Independent Test**: The interpretability and sensitivity features can be tested by running the analysis script on the test set, verifying that heatmaps are generated for sample images, and confirming that the sensitivity report shows performance variation across the defined threshold sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for Grad-CAM generation in `tests/unit/test_interpret.py`
- [X] T028 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement Grad-CAM visualization generator in `code/eval/interpret.py` (FR-006)
- [X] T030 [US3] Implement interpretability validation: Calculate **Pearson correlation** between Grad-CAM intensity and extracted grain size (from T022) AND implement **Expert Review Protocol** (simulated checklist/heuristic) as per Plan Phase 5 T030 and SC-005. Input: `data/processed/grain_features.csv` and Grad-CAM outputs. Output: `results/interpretability_correlation.json` with `{correlation: float, p_value: float, expert_review_status: "passed" | "failed"}`. Pass condition: p < 0.05 AND expert_review_status == "passed". (SC-005).
- [X] T031 [US3] Implement sensitivity analysis: Binarize using **median predicted strength of the test set** (Spec US-3 Scenario 2), sweep thresholds {0.01, 0.05, 0.1}, compute FPR/FNR in `code/eval/sensitivity.py` (FR-007).
- [X] T032 [US3] Implement confidence interval calculation: Use **Monte Carlo Dropout (30 samples)** to generate **95% Confidence Intervals** for each prediction. Append `ci_lower` and `ci_upper` columns to `results/predictions.csv` for **every sample** in the test set in `code/eval/predictor.py` (FR-008). Verification: Ensure coverage of 95% CI is checked and logged.
- [X] T033 [US3] Create analysis orchestration script `code/analyze.py` to run interpretability and sensitivity on the test set

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Append the label generation protocol and power analysis status to `research.md` under section "## Data Labeling Strategy". Format: Include Hall-Petch equation derivation and sample size justification.
- [X] T035 Run ruff check --fix on `code/` and verify exit code 0
- [X] T036 Run `code/data/loader.py` with `--stress-test` flag and record peak memory usage in `results/memory_profile.json`; fail if > 7GB.
- [X] T037 [P] Additional unit tests for edge cases (corrupted data, extreme aspect ratios) in `tests/unit/test_edge_cases.py`. Functions: `test_corrupted_image_handling`, `test_extreme_aspect_ratio`.
- [X] T038 Execute `./quickstart.sh` (or equivalent) and verify exit code 0, recording the output log in `results/quickstart_validation.log`.
- [X] T039 Final integration test: Run full pipeline from generation to final report generation using command `python code/main.py --full-pipeline`. Expected exit code 0. Record output log in `results/pipeline_run.log`.
- [X] T043 [US2] **Statistical Baseline Clarification**: Update `code/models/baseline.py` to explicitly document that the "naive baseline" is the mean of the *training set* yield strengths, and ensure this value is saved to `results/baseline_stats.json` for auditability.
- [X] T044 [US3] **Uncertainty Validation**: Add a task in `code/eval/predictor.py` to calculate the empirical coverage of the 95% CI (i.e., what % of true values actually fall within the predicted CI) and log this metric to `results/uncertainty_calibration.json`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data; may integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for model; may integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding T022->T008 dependency)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for image resizing and normalization in tests/unit/test_preprocess.py"
Task: "Integration test for full generation and split workflow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic data generator in code/data/generate.py"
Task: "Implement image preprocessor in code/data/preprocess.py"
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
- **Revision Note**: Phase 7 has been eliminated. All critical data source fixes (T040-T042) have been integrated into Phase 3 (US1) to ensure the pipeline is executable and constitution-compliant from the start. T008 is now clearly defined as label generation for training, distinct from T023 (baseline evaluation). T022 is tagged [Shared] to reflect its cross-story utility. T008 now depends on T040 (Generate) directly, not T041 (Preprocess), to ensure labels are derived from raw morphology. T022 now depends on T013 (Split) to ensure post-split extraction and prevent leakage.