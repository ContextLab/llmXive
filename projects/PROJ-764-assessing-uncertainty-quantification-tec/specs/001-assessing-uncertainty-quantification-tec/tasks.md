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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T004 [P] Implement `code/config.yaml` with the following exact keys and values: `seed` (int, default a predefined baseline value), `split_ratio` (list [0.8, 0.1, 0.1]), `split_type` (string, MUST be "stratified"), and `timeout_hours` (float, 5.0). Define exact keys: `seed`, `split_ratio`, `split_type`, `timeout_hours`. File path: `code/config.yaml`.
- [ ] T005 [P] Implement `code/data/download.py` to fetch the **OQMD** Formation Energy dataset via HuggingFace (`datasets.load_dataset("oqmd/formation-energy")`). **Requirement**: Implement retry logic with exponential backoff (up to 3 attempts) for network failures. Output artifact: `data/raw/oqmd.parquet`.
- [ ] T006a [P] [US1] Implement `code/data/preprocess.py` (Split Logic): Read `code/config.yaml` for `split_type` and `seed`. Apply a **stratified random split** (train/validation/test) based on the target variable (formation energy) using **quantile binning** to handle the continuous target. Output artifacts: `data/processed/raw_train.csv`, `data/processed/raw_val.csv`, `data/processed/raw_test.csv`. **Dependency**: T005.
- [ ] T006b [P] [US1] Implement `code/data/preprocess.py` (PCA & Validation Logic): 1) Read the split files from T006a. 2) Exclude rows with missing critical features (including structural descriptors). 3) Generate `data/processed/exclusion_log.json` with schema `{"excluded_count": int, "missing_columns": [str]}`. 4) Fit PCA on **training set only** to reduce features to **exactly 20 components**. 5) Transform train/val/test sets using the fitted PCA. 6) Save `data/processed/features_train_20pca.csv`, `data/processed/features_val_20pca.csv`, `data/processed/features_test_20pca.csv`. 7) Save the PCA transformer object as `data/processed/pca_transformer.pkl`. **Dependency**: T006a.
- [ ] T007 [P] [US1] Implement `code/data/validation_report.json` generator script that consumes `data/processed/exclusion_log.json` (from T006b) and writes `data/validation_report.json` with the count of excluded rows and list of missing variables, adhering to the schema `{"excluded_count": int, "missing_columns": [str]}` defined in FR-010. **Dependency**: T006b.
- [X] T008 [X] Implement global timeout wrapper in `code/main.py` to enforce 5-hour pipeline limit, exiting with code 1 on timeout. (Logic merged into T016).
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

- [ ] T012 [P] [US1] Implement `code/models/baseline_nn.py`: 2 hidden layers, ≤10k params, heteroscedastic output head. Output artifact: `results/models/baseline_seed42.pt`.
- [X] T013 [P] [US1] Implement `code/models/deep_ensemble.py`: Train multiple independent models, aggregate mean/variance. Output artifact: `results/models/ensemble_models/`.
- [ ] T014 [P] [US1] Implement `code/models/mc_dropout.py`: Enable dropout (p=0.2), run multiple stochastic forward passes. Output artifact: `results/models/mc_dropout_model.pt`.
- [ ] T015 [US1] Implement `code/models/sparse_gp.py`: **Consume** `data/processed/raw_test.csv` (T006a) and `data/processed/pca_transformer.pkl` (T006b). Apply the PCA transformer to the test data (do not re-fit). Use a set of inducing points, fit with GPyTorch (CPU mode). Output artifact: `results/models/sparse_gp_model.pt`. **Dependency**: T006b, T012, T013, T014. <!-- FAILED: unspecified -->
- [ ] T016 [US1] Implement `code/main.py` orchestrator to chain data load -> train -> UQ inference. Must generate `results/uq_predictions.csv` with the **exact** following columns in order: `sample_id` (int), `method` (str), `prediction` (float64), `variance` (float64), `lower_50` (float64), `upper_50` (float64), `lower_90` (float64), `upper_90` (float64), `aleatoric` (float64, **NULL for all rows**), `epistemic` (float64, **NULL for all rows**), `total` (float64, **NULL for all rows**), `uncertainty_type` (str: **NULL**). **Enforcement**: Implement a hard 5-hour timeout logic directly in this script. Exit with code 1 on timeout and generate `logs/pipeline.log`. **Dependency**: T006b, T012, T013, T014, T015.
- [X] T017a [P] [US1] Configure logging format in `code/utils/logging_config.py` to output to `logs/pipeline.log` with timestamps and metric keys.
- [X] T017b [P] [US1] Implement metric recording logic in `code/utils/logging_config.py` to write `epoch_time` and `total_training_time` to `logs/pipeline.log`.
- [ ] T018 [US1] Verify `results/uq_predictions.csv` generation and schema compliance.

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
- [X] T022a [US2] **REQUIRED**: Implement the calculation logic in `code/uq/metrics.py` to separate aleatoric and epistemic uncertainty: **Epistemic variance = variance of means across samples**, **Aleatoric variance = mean of predicted variances**. **Condition**: If method is Sparse GP, set `aleatoric` and `epistemic` to `null` and `total` to `variance`. **Dependency**: T016.
- [ ] T022b [US2] **REQUIRED**: Update `results/uq_predictions.csv` (from T016) to populate the `aleatoric`, `epistemic`, `total`, and `uncertainty_type` columns calculated in T022a. **Do not overwrite the file structure**; append/populate values to the existing rows. **Dependency**: T022a, T016.
- [X] T022c [US2] **REQUIRED**: Implement a verification script in `code/uq/validate_uq.py` that explicitly asserts the aleatoric/epistemic decomposition logic is correctly applied to the *Deep Ensemble* and *MC-Dropout* outputs specifically, validating against expected theoretical bounds. Output artifact: `logs/uq_validation.log`. **Dependency**: T022a.
- [~] T023 [US2] Generate reliability diagrams (PDF/PNG) for each method in `results/`.
- [ ] T024 [US2] Compute final metrics and save to `results/calibration_report.csv`.
- [~] T025 [US2] Implement ranking logic to identify best-performing method based on ECE and Interval Score.
- [ ] T025a [US2] **REQUIRED**: Run the full **training and evaluation** pipeline (T012-T016) exactly **3 times** with seeds **42, 43, 44**. **Optimization**: Re-use the preprocessing artifacts (T006) to avoid redundant data loading. Aggregate the resulting ECE scores for each method into a temporary file `results/ece_scores_by_seed.json`. **Note**: This is a sequential operation, not parallel. **Dependency**: T016. <!-- FAILED: unspecified -->
- [~] T025b [US2] **REQUIRED**: Implement the statistical significance test logic (Bootstrap Paired T-Test) to compare ECE scores across seeds. **Dependency**: T025a.
- [ ] T025c [US2] **REQUIRED**: Implement **Holm-Bonferroni correction** logic for multiple comparisons as required by Plan Phase 2 and SC-004. Output artifact: `results/significance_test_results.json`. **Dependency**: T025b.
- [ ] T026 [US2] Compute Coefficient of Variation (CV) of ECE scores across the 3 runs from `results/ece_scores_by_seed.json`. **MUST** output `results/robustness_report.json` containing: `cv` (float, or null if calculation fails), `pass` (boolean, **true if CV ≤ 0.05 AND cv is not null, else false**), `seeds_used` (array of integers [42, 43, 44]). **Gate**: If `pass` is false, the pipeline MUST exit with a clear error code indicating robustness failure. **Error Handling**: If CV calculation fails (e.g., division by zero), set `cv=null` and `pass=false`. **Dependency**: T025a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Downstream Screening Case Study (Priority: P3)

**Goal**: Demonstrate practical utility by comparing UQ-based screening vs point-prediction screening for perovskite stability.

**Independent Test**: Filter candidates using Expected Loss ranking; verify precision improvement over point-prediction baseline at fixed recall.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Integration test for screening logic in `tests/integration/test_screening.py`

### Implementation for User Story 3

- [~] T028 [US3] **REQUIRED**: Implement `code/uq/screening.py`: **Expected Loss ranking** (prediction + variance penalty) as required by FR-007 and Plan Phase 3. Output artifact: `results/screening_candidates.csv`. **Dependency**: T022b.
- [ ] T028b [US3] **REQUIRED**: Implement `code/uq/screening.py`: Point-prediction baseline screening logic for comparison. Output artifact: `results/screening_baseline.csv`.
- [ ] T028c [US3] **REQUIRED**: Implement fallback logic in `code/uq/screening.py`: If the Sparse GP model fails to load or produce predictions, **exclude** GP results from the screening process and proceed with Deep Ensemble/MC-Dropout results only, logging a warning. **Dependency**: T028.
- [ ] T029 [US3] Calculate precision/recall curves for both UQ (consumes output of T028) and baseline methods (T028b). **MUST** explicitly compare the filtered set from T028 against the baseline. **Dependency**: T028 and T028b must complete before T029 starts.
- [ ] T029b [US3] **REQUIRED**: Perform **Bootstrap Paired T-Test** (1000 resamples) to validate statistical significance of precision gain, applying **Holm-Bonferroni correction** as required by Plan Phase 2. **Input**: Precision scores per bootstrap resample derived from T029. **Note**: Explicitly note in the output that McNemar's test was not used as it is inappropriate for regression metrics, but the Bootstrap T-Test provides the required statistical validation. Output artifact: `results/screening_significance.json` containing p-value, test statistic, and correction method. **Dependency**: T029.
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

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2).
 - **User Story 2 (P2)**: **Depends on User Story 1 completion** (specifically T016 output). US2 cannot start until US1 is complete.
 - **User Story 3 (P3)**: Depends on Foundational (Phase 2) - Requires US2 output (ranking) and US1 output.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **MUST wait for User Story 1 to complete** (specifically T016 generating `results/uq_predictions.csv`).
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