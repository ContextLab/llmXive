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

- [X] T001 Write script `scripts/scaffold.py` to create the exact directory tree: `data/raw`, `data/processed`, `data/features`, `code/data`, `code/models`, `code/train`, `code/eval`, `code/utils`, `tests/unit`, `tests/integration`, `results`, `models`, `state`. Ensure `code/requirements.txt` is created. **Additionally**, create `code/config.yaml` with a `dataset_sha256` field containing the **pinned, hardcoded** SHA256 hash for `Rxzh/ebsd-synthetic`. **Crucially**, implement logic to fetch this hash from `code/config.yaml`. If the hash is missing or invalid, raise a `ValueError` with the exact message "SHA256 hash not found or invalid in code/config.yaml" and exit with code 1. **Implementation**: Use `hashlib.sha256` to compute the file hash and compare it against the hardcoded value in `config.yaml`. If mismatch, raise `ValueError`. This closes the dependency gap for checksum verification and ensures reproducibility on fresh runners by eliminating reliance on mutable local state files like `state/hashes.json`.

- [X] T002 Create `code/requirements.txt` containing the following pinned versions: PyTorch (CPU), torchvision, scikit-learn, pandas, numpy, matplotlib, opencv-python-headless, huggingface-hub, albumentations, pyyaml.

- [X] T003 [P] Create `code/.ruff.toml` and `code/pyproject.toml` with linting (ruff) and formatting (black) rules enabled.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup seed configuration and path management in `code/utils/config.py`
- [X] T006 [P] Create base data structures `MicrostructureImage` and `YieldStrengthValue` Pydantic models in `code/data/models.py` with fields from data-model.md.
- [X] T005 [P] Implement `BatchLoader` class in `code/data/loader.py` to prevent OOM on constrained memory. **Implementation**: Define a class `BatchLoader` wrapping `torch.utils.data.DataLoader` with `num_workers=4`, `pin_memory=True`. Implement a method `calculate_dynamic_batch_size(max_ram_gb=7.0)` that estimates image size in RAM and sets `batch_size` accordingly to ensure peak RAM < 7GB. **Dependency**: T006 must be complete first to provide data structures.
- [X] T007 [P] Create `code/utils/logging_config.py` that initializes a logger writing to `results/metrics.log` and `results/metrics.json` with the specified JSON schema. **Implementation**: The logger must write structured JSON to `results/metrics.json` with keys `timestamp`, `level`, `message`, and `context`. It must also write human-readable logs to `results/metrics.log`. **Output**: `results/metrics.log` and `results/metrics.json`.

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
- [X] T047 [US1] **CRITICAL**: Update `code/data/download.py` to implement **streaming** for the `Rxzh/ebsd-synthetic` dataset using `datasets.load_dataset(..., streaming=True)` if the full download exceeds substantial RAM, or `huggingface_hub.hf_hub_download` for specific shards if the full zip is too large. **Constraint**: Do NOT fallback to synthetic data. If streaming fails or the dataset is unreachable, the script MUST raise a `ConnectionError` or `FileNotFoundError` and halt. **Crucial**: The script MUST buffer the entire streamed dataset to `data/raw/` before T042 (validation) proceeds, ensuring atomic download and consistent input as required by FR-001. Add explicit logging of the download source URL and the number of shards/files processed. **Dependency**: T040 must be complete first. **Note**: T047 must be completed before T015 as it modifies the download logic used by the orchestrator.
- [X] T042 [US1] **CRITICAL**: Create `code/data/validate.py` that outputs `results/validation_report.json` containing the invalid pair count and exits with code 1 if invalid ratio > 1%. Schema: `{invalid_count: int, total_count: int, invalid_ratio: float}`. Exit logic: if `invalid_ratio > 0.01`, exit(non-zero); else exit(0). Validates the downloaded source integrity. **Execution Order**: Must run immediately after T047 and BEFORE T041. **Implementation**: Script must iterate through `data/raw/`, verify image integrity (non-corrupt, correct format), check for missing metadata field `yield_strength_mpa` (as defined in data-model.md), and count invalid pairs. **Output**: Write the report to `results/validation_report.json`.
- [X] T041 [US1] Implement image preprocessor in `code/data/preprocess.py` (Resize to 224x224, normalize, handle aspect ratios/depths per Edge Cases). Input: `data/raw/`. Output: `data/processed/`.
- [X] T013 [US1] Implement data splitter in `code/data/split.py` (Stratified split into train/val/test by specimen ID, generate manifest). Input: `data/processed/`. Output: `data/processed/train/`, `val/`, `test/` and `manifest.csv`.
- [X] T022 [US1] **CRITICAL**: Implement `code/data/validate_split.py` to assert NO cross-contamination of specimen IDs between train/val/test splits before feature extraction. Input: `manifest.csv`. Output: `results/split_validation.json` with `{status: "clean" | "leak_detected"}`. Exit code 1 if leak detected. **Dependency**: Must run after T013 and BEFORE T022a.
- [X] T022a [US1] **CRITICAL**: Extract grain size features for **test set only** in `code/data/extract_features.py` (FR-009). Input: `manifest.csv` and `data/processed/test/`. Output: `data/features/test_grain_features.csv` with schema: `image_id`, `grain_size_um`. **Constraint**: Strictly limited to test set images to prevent data leakage. **Dependency**: Must run AFTER T022 (Validate Split) to ensure the split is clean before feature extraction. **Implementation**: Script must iterate through test images. **Primary Method**: Extract `grain_size_um` from the `manifest.csv` generated in T013. **Fallback**: If `grain_size_um` is missing in the manifest, raise a `FileNotFoundError` with message "Metadata 'grain_size_um' missing in manifest. Feature extraction requires existing metadata per FR-009. NO image processing fallback allowed." **Note**: Prioritize metadata to ensure deterministic primary path. NO image processing fallback.
- [X] T015 [US1] Create orchestration script `code/data/process_all.py` to chain: `download -> validate -> preprocess -> split -> validate_split -> extract_features`. **CLI**: `--steps` (comma-separated), `--seed`. **Error Handling**: `set -e` or try/except block that halts on first failure and logs error to `results/pipeline_error.log`. **Outputs**: Logs for each step and final `results/pipeline_status.json`. **Dependency**: Requires T022a to be complete first.
- [X] T049 [US1] **CRITICAL**: Add a `--force-download` flag to `code/data/process_all.py` that bypasses local cache checks and re-downloads the dataset from the verified HuggingFace source. This ensures reproducibility if the local cache is corrupted. Document this flag in `quickstart.md`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Evaluation (Priority: P2)

**Goal**: Train lightweight CNN (MobileNetV2/ResNet-18 frozen) on CPU with augmentation, compare against naive baseline, and perform statistical significance testing.

**Independent Test**: The model training and evaluation can be tested independently by executing the training script with a fixed random seed and verifying that it completes within the time limit, produces a model artifact, and outputs a report containing MSE and R² metrics for both the CNN and the naive mean predictor.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for metric calculation (MSE, R²) in `tests/unit/test_metrics.py`: Implement `test_mse_calculation` asserting MSE matches numpy implementation.
- [X] T017 [P] [US2] Integration test for training loop with early stopping in `tests/integration/test_training.py`: Implement `test_training_early_stop` using a mock dataset that forces early stopping, asserting `model_best.pt` is saved and `training_log.json` contains `early_stopped: true`.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement CNN model definition (MobileNetV2/ResNet-18 frozen backbone) in `code/models/cnn.py` (FR-002)
- [X] T019 [P] [US2] Implement naive mean baseline predictor in `code/models/baseline.py` (FR-004)
- [X] T020 [US2] Implement data augmentation transforms (random rotation, flip, brightness) in `code/train/augment.py` (FR-003). **Implementation**: Implement `get_train_transforms()` with `RandomRotation(15)`, `RandomHorizontalFlip(0.5)`, and `ColorJitter(brightness=0.2, contrast=0.2)`.
- [X] T021 [US2] Implement training loop with early stopping (patience=5) and checkpoint saving in `code/train/trainer.py`
- [X] T048 [US2] **CRITICAL**: Define single-sample t-test logic for `code/eval/metrics.py` (FR-005). **Logic**: Calculate squared errors for CNN predictions. Calculate the scalar baseline squared error (MSE of the training set mean). Perform `scipy.stats.ttest_1samp(cnn_sq_errors, baseline_sq_error_scalar)`. Ensure the null hypothesis is correctly formulated as "Mean(CNN_Error) == Baseline_Error". **Note**: The plan.md Summary and Constitution Check table incorrectly state a 'paired t-test'. This task implements the spec.md FR-005 requirement for a 'single-sample t-test'. The plan.md must be updated in a subsequent pass to align with the spec. **Output**: `results/statistical_test.json` with `{test_type: "single-sample", t_statistic: float, p_value: float, outcome: "significant" | "not_significant"}`. Add a unit test in `tests/unit/test_metrics.py` specifically for this single-sample comparison logic to prevent regression.
- [X] T024 [US2] **CRITICAL**: Implement evaluation logic: MSE, R², and **single-sample t-test** (α=0.05) on squared errors comparing CNN error to naive baseline error in `code/eval/metrics.py` (FR-005, SC-002). **Implementation**: Calculate squared errors for both models. Perform a one-sample statistical test to compare the distribution of CNN squared errors against a baseline scalar derived from the training set mean squared error. **Dependency**: Must depend on T048 (Logic Definition). **Output**: `results/statistical_test.json` with `{test_type: "single-sample", t_statistic: float, p_value: float, outcome: "significant" | "not_significant"}`. **Note**: This strictly follows FR-005's mandate for a single-sample test, even if it is statistically conservative.
- [X] T025 [US2] Implement Null Hypothesis Protocol: **If R² < 0.2**, write `results/null_hypothesis_report.json` with schema: `{status: "accepted" | "rejected", r2_value: float, t_statistic: float, p_value: float, outcome: "significant" | "not_significant"}`. **Always exit with code 0** (success) unless the script crashes. Treats R² < 0.2 as a valid scientific outcome, not a system error. The `outcome` field MUST be "significant" if p < 0.05, otherwise "not_significant".
- [X] T026 [US2] Create separate script `code/models/train_ablation.py` (Plan Phase 2 Task 2.2) to train the model **without** data augmentation. **Implementation**: This script must accept a `--no-augmentation` flag or be configured via `code/config.yaml` to disable augmentation. It must save its best model to `models/ablation_best.pt` and log results to `results/ablation_report.json`. **Dependency**: T021 must be complete first.
- [X] T028 [US2] Create main training orchestration script `code/main.py` supporting `--mode` (train, evaluate, ablation) flags to call the appropriate sub-scripts. **Note**: Ensure `--mode ablation` explicitly replicates the logging and artifact naming of the standalone `train_ablation.py` script to maintain consistency with the plan's unified flow intent. (Renumbered from T027 to avoid duplicate ID).
- [X] T046 [US2] Reconcile run-book vs implementation for `code/models/train.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/models/train.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. **Resolution**: Update `quickstart.md` to explicitly call `code/main.py --mode train` or the specific existing script `code/train/trainer.py` instead of the non-existent `code/models/train.py`.
- [X] T043 [US2] **Statistical Baseline Clarification**: Update `code/models/baseline.py` to explicitly document that the "naive baseline" is the mean of the *training set* yield strengths, and ensure this value is saved to `results/baseline_stats.json` for auditability.
- [X] T051 [US2] **Runtime Measurement**: Implement a wrapper script or decorator in `code/main.py` that logs the total execution time of the pipeline to `results/runtime_report.json`. Ensure this report is generated for every run to satisfy SC-004's requirement for measuring computational feasibility against the 6-hour limit.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps, perform sensitivity analysis on prediction thresholds, and calculate confidence intervals.

**Independent Test**: The interpretability and sensitivity features can be tested by running the analysis script on the test set, verifying that heatmaps are generated for sample images, and confirming that the sensitivity report shows performance variation across the defined threshold sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Grad-CAM generation in `tests/unit/test_interpret.py`: Implement `test_gradcam_heatmap_shape` asserting output shape matches input image. Implement `test_iou_calculation` asserting IoU is within the valid theoretical range.
- [ ] T030 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`: Implement `test_sensitivity_sweep` asserting `sensitivity_analysis.csv` contains rows for all threshold values and FPR/FNR columns are populated.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement Grad-CAM visualization generator in `code/eval/interpret.py` (FR-006). **Implementation**: Use the `torchcam` library to generate Grad-CAM heatmaps. Output format: PNG images overlaid on original images, saved to `results/heatmaps/`. Required arguments: `image_path`, `model`, `target_layer`.
- [X] T030 [US3] Implement interpretability validation: Calculate **Intersection-over-Union (IoU)** between Grad-CAM heatmaps and manually annotated grain boundaries (if available). **If IoU data is missing**, generate an `expert_review_report.json` containing a qualitative assessment of the heatmap quality (e.g., "Heatmaps focus on grain boundaries") and mark status as "passed via expert review". **Implementation**: Script must load annotations if available. If not, generate the expert report. **Output**: `results/interpretability_report.json` with `{iou_score: float (or null), status: "passed" | "failed" | "passed_via_expert_review"}`. (SC-005). **Constraint**: NO fallback to expert review checklist; must generate a report.
- [X] T050 [US3] **CRITICAL**: In `code/eval/sensitivity.py`, add a validation step that ensures the **median predicted strength** used for thresholding is calculated **only** on the held-out test set predictions, NOT on the training or validation set. Log the median value used to `results/sensitivity_analysis.csv` header for auditability.
- [X] T032 [US3] **CRITICAL**: Implement confidence interval calculation: Use **Test-Time Residuals** method. **Algorithm**: 1. Run inference on the full **test set** to get residuals `r = y_true - y_pred`. 2. Calculate the standard deviation of these **test** residuals `sigma`. 3. For each prediction `y_pred_i` in the **test set**, calculate the prediction interval as `[y_pred_i - z * sigma, y_pred_i + z * sigma]`, where `z` represents the critical value for **95% confidence level (z=1.96)**. **Dependency**: Must depend on T018 (Model Definition) and T024 (Evaluation). **Output**: Append `ci_lower` and `ci_upper` columns to `results/predictions.csv` for **every sample** in the test set in `code/eval/predictor.py` (FR-008).
- [X] T031 [US3] **CRITICAL**: Implement sensitivity analysis: Binarize using **median predicted strength of the test set** (Spec US-3 Scenario 2). Sweep thresholds by calculating `median + offset` for each offset in the list defined in `code/config.yaml` (default range including negative and positive values in MPa). **Implementation**: Calculate median of test predictions. For each offset in the list, calculate threshold = `median + offset`. Compute FPR/FNR for each threshold. Output: `results/sensitivity_analysis.csv` with columns `threshold`, `fpr`, `fnr`, `offset_from_median`. **Dependency**: T050 (Validation of median calculation).
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
- [X] T052 [US2] **Documentation Alignment**: Update `plan.md` to explicitly reflect the **single-sample t-test** methodology implemented in T048 and T024. Remove all references to "paired t-test" from the Summary and Constitution Check sections to ensure the plan matches the spec and implementation. This task is critical to resolve the semantic drift between the plan and the spec.
- [X] T053 [US1] **Dataset Verification**: Update `quickstart.md` to include a step for verifying the `code/config.yaml` file exists and contains the correct SHA256 for `Rxzh/ebsd-synthetic` before running the pipeline. Add a troubleshooting section explaining the "SHA256 hash not found" error.
- [X] T054 [US3] **Sensitivity Analysis Validation**: Add a unit test in `tests/unit/test_sensitivity.py` to verify that the median calculation in `code/eval/sensitivity.py` strictly uses only the test set predictions, ensuring no data leakage from train/val sets into the threshold definition.
- [X] T055 [US2] **Ablation Study Integration**: Ensure `code/main.py --mode ablation` correctly generates a distinct artifact (e.g., `models/ablation_best.pt`) and logs it to `results/ablation_report.json` to satisfy Constitution VII's architectural ablation requirement.
- [X] T056 [US2] **Plan Correction**: Update `plan.md` (Summary and Constitution Check sections) to replace all instances of "paired t-test" with "single-sample t-test" to align with spec.md FR-005 and the implementation in T048/T024. **Action**: Edit `plan.md` text directly.

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
- **Revision Note**: Phase 7 has been removed. All critical fixes (T047-T050, T056) have been integrated into Phases 2, 3, 4, 5, and 6. T006 is no longer parallel-safe due to dependencies. T040 now requires a config file for hash verification. T022 is split into validation and extraction to prevent data leakage. T030 now generates a human review report if IoU is unavailable. T031 and T032 now include explicit parameters for sweep range and residual-based CI. T027 (Phase 5 Test) was moved to Phase 5. T028 (Phase 4 Orchestration) is the main entry point. T042, T022a, T024, T031, T032 have been fully implemented with detailed logic. T048 moved to Phase 2 to fix ordering. T051 added for runtime measurement. T052 moved to Phase 6. T046 moved to Phase 6. T056 added to correct plan.md.
- **Critical Execution Order**: T047 (Streaming) and T048 (Stat Test) must be completed before T039 (Full Pipeline) to ensure data integrity and statistical validity. T050 must be completed before T031 (Sensitivity Analysis). T022a must be completed before T015 (Orchestration). T047 must be completed before T015. T048 must be completed before T024. T050 must be completed before T032.
- **Statistical Method**: The project uses a **single-sample t-test** (FR-005) comparing CNN errors to the scalar baseline mean, as defined in the spec. The plan.md's mention of a "paired t-test" is a documentation error that contradicts the spec and will be corrected in T056.
- **Data Hygiene**: T022a and T030 now strictly enforce extraction and measurable criteria, removing all fallbacks that would violate Constitution III or SC-005.
- **Reproducibility**: T001 now uses hardcoded hashes in `config.yaml` instead of mutable local state files.
- **Executability**: T031, T032, T005, T020, T029, T026, T007, T042 now include specific parameters, artifact names, and logic to ensure deterministic execution.
- **Executability Fix**: T032 now explicitly mandates using the **test set** for residual calculation to ensure distributional similarity with the test set, and explicitly defines the **95% confidence level (z=1.96)** adjacent to the formula.