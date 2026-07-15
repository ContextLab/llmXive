# Tasks: Predicting Material Strength from Microstructure Images

**Input**: Design documents from `/specs/001-predict-material-strength-cnn/`
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

- [X] T001 Write script `scripts/scaffold.py` to create the exact directory tree per implementation plan (`projects/PROJ-477-predicting-material-strength-from-micros/`) including `data/raw`, `data/processed`, `code`, `tests`, `results`.
- [X] T002 Create `code/requirements.txt` containing the following pinned versions: PyTorch (CPU), torchvision, scikit-learn, pandas, numpy, matplotlib, opencv-python-headless, huggingface-hub.
- [X] T003 [P] Create `code/.ruff.toml` and `code/pyproject.toml` with linting (ruff) and formatting (black) rules enabled.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup seed configuration and path management in `code/utils/config.py`
- [X] T005 [P] Implement batch loading strategy to prevent OOM on constrained memory in `code/data/loader.py`
- [X] T022 Implement grain size feature extraction for every image in `code/data/extract_features.py` (FR-009, Mandatory per Plan). Output: `data/processed/grain_features.csv` with schema: `image_id`, `grain_size_um`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T008 Implement Hall-Petch label generation logic in `code/data/label_generator.py` (Mandatory per Plan: Physics-Based Label Generation). Depends on T022 output.
- [X] T006 Create base data structures `MicrostructureImage` and `YieldStrengthValue` Pydantic models in `code/data/models.py` with fields from data-model.md.
- [X] T007 [P] Create `code/utils/logging_config.py` that initializes a logger writing to `results/metrics.log` and `results/metrics.json` with the specified JSON schema.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download public dataset, preprocess EBSD images (224x224, normalize), and split into train/val/test sets with manifests.

**Independent Test**: The pipeline can be fully tested by running the data loading script and verifying that the resulting train/validation/test directories contain the correct number of image files and that a corresponding CSV/JSON manifest correctly maps image filenames to yield strength values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for image resizing and normalization in `tests/unit/test_preprocess.py`
- [ ] T010 [P] [US1] Integration test for full download and split workflow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement dataset downloader in `code/data/download.py` (Fetch from verified HuggingFace/Zenodo source, verify checksum)
- [ ] T012 [US1] Implement image preprocessor in `code/data/preprocess.py` (Resize to 224x224, normalize, handle aspect ratios/depths per Edge Cases)
- [X] T013 [US1] Implement data splitter in `code/data/split.py` (Stratified split into train/val/test, generate manifest)
- [~] T014 [US1] Create `code/data/validate.py` that outputs `results/validation_report.json` containing the invalid pair count and exits with code 1 if invalid ratio > 1%.
- [X] T015 [US1] Create orchestration script `code/data/process_all.py` to chain download -> preprocess -> split -> validate

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
- [ ] T019 [P] [US2] Implement naive mean baseline predictor in `code/models/baseline.py` (FR-004)
- [X] T020 [US2] Implement data augmentation transforms (random rotation, flip, brightness) in `code/train/augment.py` (FR-003)
- [X] T021 [US2] Implement training loop with early stopping (patience=5) and checkpoint saving in `code/train/trainer.py`
- [X] T023 [US2] Implement physics-based baseline (Hall-Petch predictor) in `code/models/physics_baseline.py` (Plan Phase 2 Task 2.4). Depends on T022.
- [X] T024 [US2] Implement evaluation logic: MSE, R², and **single-sample t-test** (α=0.05) on squared errors comparing CNN error to baseline error in `code/eval/metrics.py` (FR-005, SC-002).
- [~] T025 [US2] Implement Null Hypothesis Protocol: **If R² < 0.2**, write `results/null_hypothesis_report.json` with schema: `{status: str, r2_value: float, threshold: float}` and raise `SystemExit(1)` in `code/eval/evaluator.py` (Plan Phase 3 Task 3.6)
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
- [ ] T030 [US3] Implement IoU calculation: Calculate **IoU ≥ 0.4** between Grad-CAM heatmaps and manually annotated grain boundaries (if available) OR generate an expert review report. Input: `data/processed/grain_features.csv` or manual annotation file. Output: `results/interpretability_iou.json` (SC-005). Depends on T029 and T022.
- [X] T031 [US3] Implement sensitivity analysis: Binarize using **median predicted strength** of test set (per FR-007, overriding plan.md), sweep thresholds {0.01, 0.05, 0.1}, compute FPR/FNR in `code/eval/sensitivity.py` (FR-007)
- [~] T032 [US3] Implement confidence interval calculation: Use **Monte Carlo Dropout (30 samples)** with a **verification step** to ensure [deferred] coverage. Append `ci_lower` and `ci_upper` columns to `results/predictions.csv` in `code/eval/predictor.py` (FR-008)
- [X] T033 [US3] Create analysis orchestration script `code/analyze.py` to run interpretability and sensitivity on the test set

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034 [P] Documentation updates: Append the label generation protocol and power analysis status to `research.md` under section "Data Labeling Strategy".
- [ ] T035 Run ruff check --fix on `code/` and verify exit code 0
- [ ] T036 Run `code/data/loader.py` with `--stress-test` flag and record peak memory usage in `results/memory_profile.json`; fail if > 7GB.
- [ ] T037 [P] Additional unit tests for edge cases (corrupted data, extreme aspect ratios) in `tests/unit/`
- [ ] T038 Execute `./quickstart.sh` (or equivalent) and verify exit code 0, recording the output log in `results/quickstart_validation.log`.
- [ ] T039 Final integration test: Run full pipeline from download to final report generation

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
Task: "Integration test for full download and split workflow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset downloader in code/data/download.py"
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