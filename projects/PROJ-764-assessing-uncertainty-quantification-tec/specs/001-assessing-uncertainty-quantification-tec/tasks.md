# Tasks: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

**Input**: Design documents from `/specs/001-assessing-uncertainty-quantification/`
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

 Tasks MUST be organized by user story so each story can be independently completable and testable.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `code/`, `data/`, `results/`, `tests/`, `docs/`.
- [X] T001b [P] Create initial empty files: `code/requirements.txt`, `code/config.yaml`, `README.md`.
- [X] T001 [P] Document the deviation from Spec FR-001 (Materials Project) to Plan's OQMD source in `docs/data_source_rationale.md` to satisfy reproducibility principles while using an executable dataset.
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T004 [P] Implement `code/config.yaml` with the following exact keys and values: `seed` (int, default a predefined baseline value), `split_ratio` (list [0.8, 0.1, 0.1]), `split_type` (string, MUST be "stratified"), and `timeout_hours` (float, 5.0). Define exact keys: `seed`, `split_ratio`, `split_type`, `timeout_hours`. File path: `code/config.yaml`.
- [ ] T005a [P] [US1] Implement `code/data/download.py` to fetch the **OQMD** Formation Energy dataset via HuggingFace (`datasets.load_dataset("oqmd/formation-energy", streaming=False)`). **Requirement**: Implement retry logic with exponential backoff (up to 3 attempts) for network failures. **Materialization Requirement**: Explicitly call `dataset.to_parquet('data/raw/oqmd.parquet')` to materialize the stream into the specific file path. **Checksum Requirement**: Calculate SHA-256 hash of `data/raw/oqmd.parquet` and record it in `data/checksums.json` with the exact schema: `{"filename": "oqmd.parquet", "sha256": "<hash_string>"}`. Output artifact: `data/raw/oqmd.parquet`.
- [X] T005b [P] [US1] Implement `code/data/download.py` (Structural Descriptor Validation): Parse the dataset columns to identify structural features (radius, packing fraction). **Strict Fallback**: If structural descriptors are missing, the task MUST raise a `FileNotFoundError` with a clear message indicating the OQMD schema does not support FR-001 requirements, and the pipeline must fail. Do NOT compute approximations. **Dependency**: T005a.
- [X] T005c [P] [US1] Implement `code/data/download.py` (Structural Feature Extraction): Extract **radius** and **packing fraction** from the dataset. **Conditional**: This task runs ONLY if T005b confirms the columns exist. **Validation**: Assert that at least one structural descriptor is present for every row. **Output**: Append `radius` and `packing_fraction` columns to the dataset. **Dependency**: T005b.
- [X] T005d [P] [US1] Implement `code/data/download.py` (Validation Update): Update `validation_report.json` to include counts of rows where structural descriptors were extracted. **Dependency**: T005c.
- [ ] T006a [P] [US1] Implement `code/data/preprocess.py` (Split & Binning): Read `code/config.yaml` for `split_type` and `seed`. Apply a **stratified random split** (train/validation/test) based on the target variable (formation energy) using **quantile binning** to handle the continuous target. **Output**: Explicitly generate `data/processed/raw_train.csv`, `data/processed/raw_val.csv`, `data/processed/raw_test.csv`. **Requirement**: The output CSVs MUST include a new column `target_bin` representing the quantile bin of the formation energy. **Dependency**: T005d.
- [ ] T006b1 [P] [US1] Implement `code/data/preprocess.py` (PCA Fit/Transform): Read `data/processed/raw_train.csv` from T006a. Fit PCA on **training set only** to reduce features to **20 principal components**. Transform train/val/test sets using the fitted PCA. **Output**: `data/processed/features_train_20pca.csv`, `data/processed/features_val_20pca.csv`, `data/processed/features_test_20pca.csv`. **Dependency**: T006a.
- [ ] T006b2 [P] [US1] Implement `code/data/preprocess.py` (Exclusion Logic): Read `data/processed/features_train_20pca.csv`, etc., from T006b1. Exclude rows with missing critical features (including structural descriptors). **Output**: `data/processed/exclusion_log.json` with schema `{"excluded_count": int, "missing_columns": [str]}`. **Dependency**: T006b1.
- [ ] T006b3 [P] [US1] Implement `code/data/preprocess.py` (Artifact Serialization): Read `data/processed/exclusion_log.json` from T006b2. Save the PCA transformer object as `data/processed/pca_transformer.pkl`. **Output**: `data/processed/pca_transformer.pkl`, `data/processed/exclusion_log.json`. **Dependency**: T006b2.
- [ ] T007 [P] [US1] Implement `code/data/validation_report.json` generator script that consumes `data/processed/exclusion_log.json` (from T006b3) and writes `data/validation_report.json` with the count of excluded rows and list of missing variables, adhering to the schema `{"excluded_count": int, "missing_columns": [str]}` defined in FR-010. **Dependency**: T006b3.
- [X] T008 [X] Implement global timeout wrapper in `code/main.py` to enforce 5-hour pipeline limit, exiting with code 1 on timeout. (Logic merged into T016b).
- [ ] T009 Setup `code/contracts/` directory with `material_sample.schema.yaml` and `uq_prediction.schema.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Model Training and UQ Application (Priority: P1) 🎯 MVP

**Goal**: Train a baseline FFNN and apply three UQ techniques (Deep Ensembles, MC Dropout, Sparse GP) to generate predictions and variance estimates on CPU.

**Independent Test**: The system ingests the dataset, trains the baseline, runs UQ inference, and outputs a CSV with (prediction, lower_bound, upper_bound, variance) without GPU errors within 5 hours. Note: The implementation tasks (T012-T018) MUST produce these outputs directly; T010/T011 are supplementary unit tests.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These are supplementary; the primary verification is the output of T012-T018.

- [X] T010 [P] [US1] Unit test for `code/data/preprocess.py` PCA and missing data exclusion in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Contract test for output schema in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/models/baseline_nn.py`: 2 hidden layers, ≤10k params, heteroscedastic output head. **Verification**: Before saving the model, calculate the total parameter count. Assert `total_params <= 10000`. If assertion fails, raise an error and do NOT save the file. Output artifact: `results/models/baseline_seed42.pt`.
- [X] T013 [P] [US1] Implement `code/models/deep_ensemble.py`: **Train exactly 5** independently initialized copies of the baseline model and aggregate predictions to estimate mean and variance. **Output**: Save models to `results/models/ensemble/` with unique filenames `ensemble_seed_<seed>.pt`. **Dependency**: T006b3.
- [X] T014 [P] [US1] Implement `code/models/mc_dropout.py`: Enable dropout (p=0.2), run **30 stochastic forward passes** per sample. **Output**: Save model to `results/models/mc_dropout/mc_dropout_seed_<seed>.pt`. **Dependency**: T006b3.
- [ ] T015a [P] [US1] Implement `code/models/sparse_gp.py` (Verification): Check existence of `data/processed/features_test_20pca.csv` and `data/processed/pca_transformer.pkl` before execution. Fail loudly if missing. **Do not re-fit PCA**. **Dependency**: T006b3.
- [X] T015b [P] [US1] Implement `code/models/sparse_gp.py` (Fitting): Use a sufficient number of inducing points, fit with GPyTorch (CPU mode) on the PCA-reduced features. **Dependency**: T015a, T006b3.
- [~] T015c [P] [US1] Implement `code/models/sparse_gp.py` (Saving): Save the fitted GP model to `results/models/sparse_gp_model.pt`. **Dependency**: T015b.
- [~] T016a [P] [US1] Implement `code/models/run_single_seed.py`: A reusable runner script that performs **model training and UQ inference** for **one specific seed**. **Constraint**: This script MUST **NOT** perform data download or preprocessing. It must load pre-processed artifacts from `data/processed/` (generated by T006) and train/infer only. **Execution**: **Load** model weights from `results/models/ensemble/`, `results/models/mc_dropout/`, and `results/models/sparse_gp_model.pt` (as produced by T013, T014, T015c). **Inference**: Run inference, **calculate bounds from variance** (lower_50, upper_50, etc.), and write CSV. Output artifact: `results/uq_predictions_seed_<seed>.csv` with the **exact** following columns in order: `sample_id` (int), `method` (str), `prediction` (float64), `variance` (float64), `lower_50` (float64), `upper_50` (float64), `lower_90` (float64), `upper_90` (float64). **Dependency**: T006b3, T012, T013, T014, T015c.
- [~] T016b [US1] Implement `code/main.py` orchestrator to chain data load -> train -> UQ inference. **Global Timeout**: Enforce a hard timeout for the **entire pipeline** (T016a runs + T026 tasks). **Wait Logic**: Explicitly wait for the completion of T013 and T014 (models) before T016a starts. **Merge**: Explicitly depend on and merge outputs from T016a runs into `results/uq_predictions_base.csv`. **Dependency**: T006b3, T012, T013, T014, T015c, T016a.
- [X] T017a [P] [US1] Configure logging format in `code/utils/logging_config.py` to output to `logs/pipeline.log` with timestamps and metric keys.
- [X] T017b [P] [US1] Implement metric recording logic in `code/utils/logging_config.py` to write `epoch_time` and `total_training_time` to `logs/pipeline.log`.
- [ ] T018 [US1] Verify `results/uq_predictions_base.csv` generation and schema compliance. **Dependency**: T016b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calibration and Reliability Evaluation (Priority: P2)

**Goal**: Evaluate calibration (ECE, Interval Score) and rank methods based on uncertainty accuracy.

**Independent Test**: Calculate ECE and Interval Score for specified confidence intervals, generate reliability diagrams, and rank methods by ECE.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for ECE calculation logic in `tests/unit/test_uq_metrics.py`
- [X] T020 [P] [US2] Unit test for Interval Score and Sharpness calculation in `tests/unit/test_uq_metrics.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/uq/metrics.py`: ECE (quantile binning), Interval Score, Sharpness.
- [X] T022a [US2] **REQUIRED**: Implement the calculation logic in `code/uq/metrics.py` to separate aleatoric and epistemic uncertainty: **Epistemic variance = variance of means across samples**, **Aleatoric variance = mean of predicted variances**. **Condition**: If method is Sparse GP, set `aleatoric` and `epistemic` to `null` and `total` to `variance`. **Dependency**: T016a.
- [ ] T022b [US2] **REQUIRED**: Implement the execution script in `code/uq/apply_decomposition.py` to be used in T022d. This script imports the decomposition logic from T022a and prepares to populate `results/uq_predictions.csv`. **Dependency**: T022a, T016a.
- [ ] T022d [US2] **REQUIRED**: Execute the script from T022b to populate `results/uq_predictions.csv`. **Execution**: **Import and invoke** the decomposition logic from T022a via T022b. **Serialization**: Use `pandas.DataFrame.to_csv` with `na_rep=''` to handle `null` values for Sparse GP (aleatoric/epistemic columns). The output CSV must include columns: `sample_id`, `method`, `prediction`, `variance`, `lower_50`, `upper_50`, `lower_90`, `upper_90`, `aleatoric`, `epistemic`, `total`, `uncertainty_type`. **Dependency**: T022a, T022b, T016a.
- [X] T022c [US2] **REQUIRED**: Implement a verification script in `code/uq/validate_uq.py` that explicitly asserts the aleatoric/epistemic decomposition logic is correctly applied to the *Deep Ensemble* and *MC-Dropout* outputs specifically, validating that **epistemic variance is non-negative** and **consistent with model variance (correlation > 0.9)**. Output artifact: `logs/uq_validation.log`. **Dependency**: T022a, T022d.
- [ ] T023 [US2] Generate reliability diagrams (PDF/PNG) for each method in `results/`.
- [ ] T024 [US2] Compute final metrics and save to `results/calibration_report.csv`. **Schema**: `method` (str), `ece` (float), `interval_score` (float), `sharpness` (float), `coverage_50` (float), `coverage_90` (float). **Dependency**: T022d.
- [ ] T025a [P] [US2] **REQUIRED**: Implement `code/run_seeds.py` as a **Seed Orchestrator**. **Logic**: Iterate over a fixed list of seeds (e.g., [, 43, 44]). For each seed, **invoke `code/models/run_single_seed.py`** (T016a) with the specific seed argument. **Constraint**: This script MUST **NOT** call T005 (Download) or T006 (Preprocess). It must rely entirely on the **single frozen dataset** artifacts in `data/processed/` generated by T006. **DO NOT** re-download or re-preprocess data. **Output**: Generate `results/uq_predictions_seed_<seed>.csv` for each seed and aggregate them into `results/ece_scores_by_seed.json`. **Dependency**: T016a, T006b3.
- [ ] T025b [US2] **REQUIRED**: Implement the **Coefficient of Variation (CV)** calculation logic for ECE scores across seeds. **Input**: `results/ece_scores_by_seed.json`. **Output**: `results/robustness_report.json` containing: `cv` (float, or null if calculation fails), `pass` (boolean, **true if CV ≤ 0.05 AND cv is not null, else false**), `seeds_used` (array of integers [42, 43, 44]). **Gate**: If `pass` is false, the pipeline MUST exit with a clear error code indicating robustness failure. **Error Handling**: If CV calculation fails (e.g., division by zero), set `cv=null` and `pass=false`. **Dependency**: T025a.
- [ ] T025 [US2] Implement ranking logic to identify best-performing method based on ECE and Interval Score. **Dependency**: T024.
- [ ] T026 [US2] **REQUIRED**: Implement the **Robustness Gate** in `code/main.py`. **Logic**: After T025b completes, `main.py` must load `results/robustness_report.json`. If the `pass` field is `false`, `main.py` MUST **immediately exit with code 1** and print a clear error message: "Robustness Gate Failed: CV > 0.05". **Dependency**: T025b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Downstream Screening Case Study (Priority: P3)

**Goal**: Demonstrate practical utility by comparing UQ-based screening vs point-prediction screening for perovskite stability.

**Independent Test**: Filter candidates using Expected Loss ranking; verify precision improvement over point-prediction baseline at fixed recall.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Integration test for screening logic in `tests/integration/test_screening.py`

### Implementation for User Story 3

- [ ] T028a [US3] **REQUIRED**: Implement `code/uq/screening.py` (Threshold Calculation): Calculate the specific formation energy threshold required to achieve the target recall from the test set distribution. **Output**: `results/screening_threshold.json` with schema `{"recall_target": float, "threshold_value": float}`. **Dependency**: T022d.
- [ ] T028 [US3] **REQUIRED**: Implement `code/uq/screening.py`: **Expected Loss ranking** (prediction + variance penalty) as required by FR-007 and Plan Phase 3. **Input**: `results/calibration_report.csv` (T024) and `results/uq_predictions.csv` (T022d). **Dependency**: T025, T024, T022d, T028a. Output artifact: `results/screening_candidates.csv`.
- [ ] T028b [US3] **REQUIRED**: Implement `code/uq/screening.py`: Point-prediction baseline screening logic for comparison. **Baseline Logic**: Rank candidates by mean prediction value and filter by the **threshold calculated in T028a** to ensure fixed recall. **Dependency**: T022d, T028a. Output artifact: `results/screening_baseline.csv`.
- [ ] T028c [US3] **REQUIRED**: Implement fallback logic in `code/uq/screening.py`: If the Sparse GP model fails to load or produce predictions, **exclude** GP results from the screening process and proceed with Deep Ensemble/MC-Dropout results only, logging a warning. **Dependency**: T028.
- [ ] T029 [US3] Calculate precision/recall curves for both UQ (consumes output of T028) and baseline methods (T028b). **MUST** explicitly compare the filtered set from T028 against the baseline. **Output**: `results/selection_decisions.csv` containing binary flags (`selected_uq`, `selected_baseline`) for each candidate to enable McNemar's test. **Dependency**: T028 and T028b must complete before T029 starts.
- [ ] T029b [US3] **REQUIRED**: Perform **McNemar's test** to validate statistical significance of precision gain, using the binary classification matrix from T029. **Input**: `results/selection_decisions.csv`. **Output**: `results/screening_significance.json` containing p-value, test statistic, and test method ("McNemar"). **Dependency**: T029.
- [ ] T030 [US3] Generate `results/screening_results.csv` with selection metrics and comparison p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033a [P] Update `README.md` with project overview and usage instructions.
- [ ] T033b [P] Update `docs/api.md` with usage examples for `screening.py`.
- [ ] T034a [P] Run `ruff check code/` to identify unused imports and linting errors.
- [ ] T034b [P] Run `black code/` to enforce formatting standards.
- [ ] T035 Verify `results/` artifacts against `code/contracts/` schemas
- [ ] T036 [P] Run `tests/unit/` and `tests/contract/` suites to ensure all pass
- [ ] T037 [P] Implement `code/utils/runtime_logger.py` to measure and record the total wall-clock time of the pipeline in `results/runtime_report.json` to satisfy SC-002. **Dependency**: T016b.
- [ ] T039 [US2] **Data Flow Correction**: Ensure `code/uq/metrics.py` (T021) is invoked *before* T022b to guarantee the decomposition logic is available before updating `results/uq_predictions.csv`. **Dependency**: T022a, T022d.
- [ ] T040 [US3] **Data Flow Correction**: Ensure `code/uq/screening.py` (T028) explicitly checks for the existence of `results/calibration_report.csv` (T024) and `results/uq_predictions.csv` (T022d) before attempting to load UQ results.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2).
 - **User Story 2 (P2)**: **Depends on User Story 1 completion** (specifically T016a output). US2 cannot start until US1 is complete.
 - **User Story 3 (P3)**: Depends on Foundational (Phase 2) - Requires US2 output (ranking) and US1 output.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **MUST wait for User Story 1 to complete** (specifically T016a generating `results/uq_predictions_seed_<seed>.csv`).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 output (ranking) and US1 output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services/orchestrators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **User stories CANNOT start in parallel**. US2 and US3 are semantically dependent on US1 output.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel **only after** the preceding dependencies are met (e.g., US3 can start after US2 is done, but US2 must wait for US1).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for preprocess.py in tests/unit/test_preprocess.py"
Task: "Contract test for output schema in tests/contract/test_schemas.py"

# Launch all models for User Story 1 together:
Task: "Implement baseline_nn.py"
Task: "Implement deep_ensemble.py"
Task: "Implement mc_dropout.py"
Task: "Implement sparse_gp.py"
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
 - Developer A: User Story 1 (Models)
 - **Wait for US1 completion**
 - Developer B: User Story 2 (Metrics)
 - **Wait for US2 completion**
 - Developer C: User Story 3 (Screening)
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

---

## Revision Concerns & Fixes

**Purpose**: Address specific failures identified in the previous analysis pass and ensure data flow integrity.

- [ ] T039 [US2] **Data Flow Correction**: Ensure `code/uq/metrics.py` (T021) is invoked *before* T022b to guarantee the decomposition logic is available before updating `results/uq_predictions.csv`. **Dependency**: T022a, T022d.
- [ ] T040 [US3] **Data Flow Correction**: Ensure `code/uq/screening.py` (T028) explicitly checks for the existence of `results/calibration_report.csv` (T024) and `results/uq_predictions.csv` (T022d) before attempting to load UQ results.