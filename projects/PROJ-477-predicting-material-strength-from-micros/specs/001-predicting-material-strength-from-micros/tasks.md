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

- [X] T001 Write script `scripts/scaffold.py` to create the exact directory tree: `data/raw`, `data/processed`, `data/features`, `code/data`, `code/models`, `code/train`, `code/eval`, `code/utils`, `tests/unit`, `tests/integration`, `results`, `models`, `state`. Ensure `code/requirements.txt` is created. **Additionally**, create `code/config.yaml` with a `dataset_sha256` field. **Crucially**, implement logic to fetch the verified SHA256 hash for `Rxzh/ebsd-synthetic` from the HuggingFace dataset card (or `state/hashes.json` if pre-populated) and write it to `code/config.yaml` before T040 runs. This closes the dependency gap for checksum verification.

- [X] T002 Create `code/requirements.txt` containing the following pinned versions: PyTorch (CPU), torchvision, scikit-learn, pandas, numpy, matplotlib, opencv-python-headless, huggingface-hub, albumentations, pyyaml.

- [X] T003 [P] Create `code/.ruff.toml` and `code/pyproject.toml` with linting (ruff) and formatting (black) rules enabled.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup seed configuration and path management in `code/utils/config.py`
- [X] T005 [P] Implement batch loading strategy to prevent OOM on constrained memory in `code/data/loader.py`. **Dependency**: T006 must be complete first to provide data structures.
- [X] T006 Create base data structures `MicrostructureImage` and `YieldStrengthValue` Pydantic models in `code/data/models.py` with fields from data-model.md. **Note**: Removed `[P]` tag as T005 depends on this.
- [X] T007 [P] Create `code/utils/logging_config.py` that initializes a logger writing to `results/metrics.log` and `results/metrics.json` with the specified JSON schema.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download the public `Rxzh/ebsd-synthetic` dataset from HuggingFace (verified source for synthetic microstructure morphology), preprocess EBSD images (224x224, normalize), validate integrity, and split into train/val/test sets with manifests.

**Independent Test**: The pipeline can be fully tested by running the data loading script and verifying that the resulting train/validation/test directories contain the correct number of image files and that a corresponding CSV/JSON manifest correctly maps image filenames to yield strength values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for image resizing and normalization in `tests/unit/test_preprocess.py`: Implement `test_resize_normalizes_correctly(input_shape, expected_shape)` asserting output shape matches the expected target dimensions and pixel values are in [0, 1]. Implement `test_corrupted_image_raises` asserting that a corrupted image (e.g., an image with invalid bit depth or aspect ratio) raises a `ValueError` with a specific message.
- [X] T010 [P] [US1] Integration test for full generation and split workflow in `tests/integration/test_data_pipeline.py`: Implement `test_full_pipeline` that mocks the HuggingFace download, runs `preprocess.py`, `split.py`, and `validate.py`, asserting that `data/processed/train`, `val`, `test` directories exist with >0 files and `manifest.csv` contains valid mappings.

### Implementation for User Story 1

- [X] T040 [US1] **CRITICAL**: Implement data downloader in `code/data/download.py` to fetch the verified public dataset `Rxzh/ebsd-synthetic` from HuggingFace. **NO synthetic generation**. Read the expected SHA256 hash from `code/config.yaml` (populated in T001). Raise a hard `FileNotFoundError` if the dataset is missing, checksum fails, or hash is undefined in config. Output: `data/raw/` with original zip/images. This satisfies FR-001 by downloading a public dataset (synthetic morphology) rather than generating data internally.
- [ ] T042 [US1] **CRITICAL**: Create `code/data/validate.py` that outputs `results/validation_report.json` containing the invalid pair count and exits with code 1 if invalid ratio > 1%. Schema: `{invalid_count: int, total_count: int, invalid_ratio: float}`. Exit logic: if `invalid_ratio > 0.01`, exit(1); else exit(0). Validates the downloaded source integrity. **Execution Order**: Must run immediately after T040 and BEFORE T041. **Implementation**: Script must iterate through `data/raw/`, verify image integrity (non-corrupt, correct format), check for missing strength metadata, and count invalid pairs. **Output**: Write the report to `results/validation_report.json`.
- [X] T041 [US1] Implement image preprocessor in `code/data/preprocess.py` (Resize to 224x224, normalize, handle aspect ratios/depths per Edge Cases). Input: `data/raw/`. Output: `data/processed/`.
- [X] T013 [US1] Implement data splitter in `code/data/split.py` (Stratified split into train/val/test by specimen ID, generate manifest). Input: `data/processed/`. Output: `data/processed/train/`, `val/`, `test/` and `manifest.csv`.
- [X] T022 [US1] **CRITICAL**: Implement `code/data/validate_split.py` to assert NO cross-contamination of specimen IDs between train/val/test splits before feature extraction. Input: `manifest.csv`. Output: `results/split_validation.json` with `{status: "clean" | "leak_detected"}`. Exit code 1 if leak detected. **Dependency**: Must run after T013 and BEFORE T022a.
- [ ] T022a [US1] **CRITICAL**: Extract grain size features for **test set only** in `code/data/extract_features.py` (FR-009). Input: `manifest.csv` and `data/processed/test/`. Output: `data/features/test_grain_features.csv` with schema: `image_id`, `grain_size_um`. **Constraint**: Strictly limited to test set images to prevent data leakage. **Optional**: If `--full-dataset` flag is provided, also output `data/features/all_grain_features.csv` to support broader comparative analysis. **Implementation**: Script must iterate through test images, calculate grain size (e.g., via thresholding and connected components or using provided metadata), and save results.
- [X] T015 [US1] Create orchestration script `code/data/process_all.py` to chain: `download -> validate -> preprocess -> split -> validate_split -> extract_features`. **CLI**: `--steps` (comma-separated), `--seed`. **Error Handling**: `set -e` or try/except block that halts on first failure and logs error to `results/pipeline_error.log`. **Outputs**: Logs for each step and final `results/pipeline_status.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Evaluation (Priority: P2)

**Goal**: Train lightweight CNN (MobileNetV2/ResNet-18 frozen) on CPU with augmentation, compare against naive baseline, and perform statistical significance testing.

**Independent Test**: The model training and evaluation can be tested independently by executing the training script with a fixed random seed and verifying that it completes within the time limit, produces a model artifact, and outputs a report containing MSE and R² metrics for both the CNN and the naive mean predictor.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for metric calculation (MSE, R²) in `tests/unit/test_metrics.py`: Implement `test_mse_calculation` asserting MSE matches numpy implementation. {{claim:c_fd82e076}}
- [X] T017 [P] [US2] Integration test for training loop with early stopping in `tests/integration/test_training.py`: Implement `test_training_early_stop` using a mock dataset that forces early stopping, asserting `model_best.pt` is saved and `training_log.json` contains `early_stopped: true`.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement CNN model definition (MobileNetV2/ResNet-18 frozen backbone) in `code/models/cnn.py` (FR-002)
- [X] T019 [P] [US2] Implement naive mean baseline predictor in `code/models/baseline.py` (FR-004)
- [X] T020 [US2] Implement data augmentation transforms (random rotation, flip, brightness) in `code/train/augment.py` (FR-003)
- [X] T021 [US2] Implement training loop with early stopping (patience=5) and checkpoint saving in `code/train/trainer.py`
- [ ] T024 [US2] **CRITICAL**: Implement evaluation logic: MSE, R², and **single-sample t-test** (α=0.05) on squared errors comparing CNN error to naive baseline error in `code/eval/metrics.py` (FR-005, SC-002). **Implementation**: Calculate squared errors for both models. Perform `scipy.stats.ttest_1samp(cnn_sq_errors, baseline_sq_error_scalar)` where `baseline_sq_error_scalar` is the squared error of the training set mean. **Output**: `results/statistical_test.json` with `{test_type: "single-sample", t_statistic: float, p_value: float, outcome: "significant" | "not_significant"}`. **Note**: This strictly follows FR-005's mandate for a single-sample test, even if it is statistically conservative.
- [X] T025 [US2] Implement Null Hypothesis Protocol: **If R² < 0.2**, write `results/null_hypothesis_report.json` with schema: `{status: "accepted" | "rejected", r2_value: float, t_statistic: float, p_value: float, outcome: "significant" | "not_significant"}`. **Always exit with code 0** (success) unless the script crashes. Treats R² < 0.2 as a valid scientific outcome, not a system error. The `outcome` field MUST be "significant" if p < 0.05, otherwise "not_significant".
- [X] T026 [US2] Create separate script `code/models/train_ablation.py` (Plan Phase 2 Task 2.2) to train the model **without** data augmentation. This script runs independently from `code/train/trainer.py` to ensure a distinct artifact for ablation.
- [X] T028 [US2] Create main training orchestration script `code/main.py` supporting `--mode` (train, evaluate, ablation) flags to call the appropriate sub-scripts. (Renumbered from T027 to avoid duplicate ID).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps, perform sensitivity analysis on prediction thresholds, and calculate confidence intervals.

**Independent Test**: The interpretability and sensitivity features can be tested by running the analysis script on the test set, verifying that heatmaps are generated for sample images, and confirming that the sensitivity report shows performance variation across the defined threshold sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for Grad-CAM generation in `tests/unit/test_interpret.py`: Implement `test_gradcam_heatmap_shape` asserting output shape matches input image. Implement `test_iou_calculation` asserting IoU is within the valid theoretical range.
- [X] T030 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`: Implement `test_sensitivity_sweep` asserting `sensitivity_analysis.csv` contains rows for all threshold values and FPR/FNR columns are populated.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement Grad-CAM visualization generator in `code/eval/interpret.py` (FR-006) <!-- FAILED: unspecified -->
- [X] T030 [US3] Implement interpretability validation: Calculate **Intersection-over-Union (IoU)** between Grad-CAM heatmaps and manually annotated grain boundaries (if available). **If IoU data is missing**, generate `results/expert_review_report.md` containing a structured checklist for human experts. **Mechanism**: Accept a `--expert-input` CLI flag pointing to a JSON file containing `{"status": "passed" | "failed", "comments": "..."}`. If provided, set `expert_review_status` in the output JSON accordingly. If not provided, default to "pending" and log a warning. Output: `results/interpretability_report.json` with `{iou_score: float (or null), expert_review_status: "pending" | "passed" | "failed", checklist_details: {...}}`. Pass condition: IoU >= 0.4 OR (expert_review_status == "passed" via human input). (SC-005).
- [ ] T031 [US3] **CRITICAL**: Implement sensitivity analysis: Binarize using **median predicted strength of the test set** (Spec US-3 Scenario 2). Sweep thresholds across a **representative set of low absolute difference values** calculated as `median ± k * std` where `k` is a configurable `--sweep-factor` (default values spanning a range from fractional to integer multiples). Compute FPR/FNR in `code/eval/sensitivity.py` (FR-007). **Implementation**: Calculate median and std of test predictions. Define thresholds dynamically. For each threshold, calculate FPR and FNR. Output: `results/sensitivity_analysis.csv` with columns `threshold`, `fpr`, `fnr`, `sweep_factor`.
- [ ] T032 [US3] **CRITICAL**: Implement confidence interval calculation: Use **Monte Carlo Dropout** with **N=100 samples** and **dropout rate=0.2** during inference. Calculate **confidence intervals** using the **percentile method** (lower and upper percentiles). Append `ci_lower` and `ci_upper` columns to `results/predictions.csv` for **every sample** in the test set in `code/eval/predictor.py` (FR-008). **Implementation**: Enable dropout during inference. Run 100 forward passes per sample. [UNRESOLVED-CLAIM: c_919e1167 — status=not_enough_info] Calculate 2.5th and 97.5th percentiles of the 100 predictions. [UNRESOLVED-CLAIM: c_fcc722cf — status=not_enough_info] Calculate empirical coverage of the 95% CI (what % of true values fall within predicted CI) and log to `results/uncertainty_calibration.json`. Output: `results/predictions.csv` with `ci_lower`, `ci_upper`.
- [X] T033 [US3] Create analysis orchestration script `code/analyze.py` to run interpretability and sensitivity on the test set

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Update `research.md` under section "## Data Labeling Strategy" with the downloaded dataset citation (`Rxzh/ebsd-synthetic`) and preprocessing summary from `results/validation_report.json`.
- [X] T035 Run ruff check --fix on `code/` and verify exit code 0
- [X] T036 Run `code/data/loader.py` with `--stress-test` flag and record peak memory usage **and total runtime** in `results/memory_profile.json`; fail if RAM > 7GB or runtime > 6h.
- [X] T037 [P] Additional unit tests for edge cases (corrupted data, extreme aspect ratios) in `tests/unit/test_edge_cases.py`. Functions: `test_corrupted_image_handling` (16-bit depth, NaN values), `test_extreme_aspect_ratio` (extreme ratios).
- [X] T038 Execute `./quickstart.sh` (or equivalent) and verify exit code 0, recording the output log in `results/quickstart_validation.log`.
- [X] T039 Final integration test: Run full pipeline from download to final report generation using command `python code/main.py --mode full-pipeline`. Expected exit code 0. Record output log in `results/pipeline_run.log`.
- [X] T043 [US2] **Statistical Baseline Clarification**: Update `code/models/baseline.py` to explicitly document that the "naive baseline" is the mean of the *training set* yield strengths, and ensure this value is saved to `results/baseline_stats.json` for auditability.
- [ ] T046 Reconcile run-book vs implementation for `code/models/train.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/models/train.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T051 [US2] **Runtime Measurement**: Implement a wrapper script or decorator in `code/main.py` that logs the total execution time of the pipeline to `results/runtime_report.json`. Ensure this report is generated for every run to satisfy SC-004's requirement for measuring computational feasibility against the 6-hour limit.

---

## Phase 7: Revision & Correction (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in recent analysis regarding data sourcing, statistical rigor, and execution reliability.

- [ ] T047 [US1] **CRITICAL**: Update `code/data/download.py` to implement **streaming** for the `Rxzh/ebsd-synthetic` dataset using `datasets.load_dataset(..., streaming=True)` if the full download exceeds 7GB RAM, or `huggingface_hub.hf_hub_download` for specific shards if the full zip is too large. **Constraint**: Do NOT fallback to synthetic data. If streaming fails or the dataset is unreachable, the script MUST raise a `ConnectionError` or `FileNotFoundError` and halt. Add explicit logging of the download source URL and the number of shards/files processed.
- [ ] T048 [US2] **CRITICAL**: Refactor `code/eval/metrics.py` to ensure the **single-sample t-test** (FR-005) is implemented exactly as specified: Compare the distribution of CNN squared errors against the **single scalar value** of the baseline mean squared error (the mean of the training set). Ensure the null hypothesis is correctly formulated as "Mean(CNN_Error) == Baseline_Error". **Formula**: `scipy.stats.ttest_1samp(cnn_sq_errors, baseline_sq_error_scalar)`. Add a unit test in `tests/unit/test_metrics.py` specifically for this single-sample comparison logic to prevent regression to a paired test. **Note**: Moved to Phase 2 in this revision to ensure it is defined before T024.
- [X] T049 [US1] **CRITICAL**: Add a `--force-download` flag to `code/data/process_all.py` that bypasses local cache checks and re-downloads the dataset from the verified HuggingFace source. This ensures reproducibility if the local cache is corrupted. Document this flag in `quickstart.md`.
- [ ] T050 [US3] **CRITICAL**: In `code/eval/sensitivity.py`, add a validation step that ensures the **median predicted strength** used for thresholding is calculated **only** on the held-out test set predictions, NOT on the training or validation set. Log the median value used to `results/sensitivity_analysis.csv` header for auditability.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Must be completed before final integration (T039) to ensure all critical logic is corrected.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding T006->T005 dependency)
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
Task: "Implement data downloader in code/data/download.py"
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
- **Revision Note**: Phase 7 has been dissolved. All critical fixes (T045-T050) have been integrated into Phases 3, 4, and 5 as immediate prerequisites or sub-steps to ensure correct logic is implemented from the start. T006 is no longer parallel-safe due to dependencies. T040 now requires a config file for hash verification. T022 is split into validation and extraction to prevent data leakage. T030 now generates a human review report if IoU is unavailable. T031 and T032 now include explicit parameters for sweep range and Monte Carlo samples. T027 (Phase 4) was renumbered to T028 to avoid duplicate ID with Phase 5 test. T042, T022a, T024, T031, T032 have been fully implemented with detailed logic. T048 moved to Phase 2 to fix ordering. T051 added for runtime measurement.
- **New Revision Note**: Phase 7 has been re-introduced to explicitly address the critical gaps identified in the latest analysis (T047-T050). These tasks are mandatory and must be completed before the final integration test (T039). T047 ensures data streaming and prevents synthetic fallback. T048 corrects the statistical test implementation to match the spec. T049 adds reproducibility safeguards. T050 ensures thresholding logic is sound. T051 added for runtime measurement.
