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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python project with pinned dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Implement `code/config.yaml` with the following exact keys and values: `seed` (int, default 42), `split_ratio` (list [0.8, 0.1, 0.1]), `split_type` (string, MUST be "stratified"), and `timeout_hours` (float, 5.0). Define exact keys: `seed`, `split_ratio`, `split_type`, `timeout_hours`. File path: `code/config.yaml`.
- [ ] T005 [P] Implement `code/data/download.py` to fetch the OQMD Formation Energy dataset via HuggingFace (`datasets.load_dataset("oqmd/formation-energy")`) and save the raw data to `data/raw/oqmd.parquet`.
- [ ] T006 [P] Implement `code/data/preprocess.py` to: 1) Read `code/config.yaml` for `split_type` and `seed`, 2) Apply a **stratified random split** (train/validation/test) based on the target variable if `split_type` is "stratified", 3) Apply PCA to reduce features to **exactly 20 components**, 4) Exclude rows with missing critical features, 5) Output `data/processed/features_20pca.csv` and generate a JSON log `data/processed/exclusion_log.json` with schema `{"excluded_count": int, "missing_columns": [str]}`.
- [ ] T007 [P] Implement `code/data/validation_report.json` generator script that consumes `data/processed/exclusion_log.json` and writes `data/validation_report.json` with the count of excluded rows and list of missing variables, adhering to the schema `{"excluded_count": int, "missing_columns": [str]}`.
- [~] T008 Implement global timeout wrapper in `code/main.py` to enforce 5-hour pipeline limit, exiting with code 1 on timeout.
- [~] T009 Setup `code/contracts/` directory with `material_sample.schema.yaml` and `uq_prediction.schema.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Model Training and UQ Application (Priority: P1) 🎯 MVP

**Goal**: Train a baseline FFNN and apply three UQ techniques (Deep Ensembles, MC Dropout, Sparse GP) to generate predictions and variance estimates on CPU.

**Independent Test**: The system ingests the OQMD subset, trains the baseline, runs UQ inference, and outputs a CSV with (prediction, lower_bound, upper_bound, variance) without GPU errors within 5 hours. Note: The implementation tasks (T012-T018) MUST produce these outputs directly; T010/T011 are supplementary unit tests.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These are supplementary; the primary verification is the output of T012-T018.

- [~] T010 [P] [US1] Unit test for `code/data/preprocess.py` PCA and missing data exclusion in `tests/unit/test_preprocess.py`
- [~] T011 [P] [US1] Contract test for output schema in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/models/baseline_nn.py`: 2 hidden layers, ≤10k params, heteroscedastic output head. Output artifact: `results/models/baseline_seed42.pt`.
- [~] T013 [P] [US1] Implement `code/models/deep_ensemble.py`: Train multiple independent models, aggregate mean/variance. Output artifact: `results/models/ensemble_models/`.
- [~] T014 [P] [US1] Implement `code/models/mc_dropout.py`: Enable dropout (p=0.2), run 30 stochastic forward passes. Output artifact: `results/models/mc_dropout_model.pt`.
- [~] T015 [P] [US1] Implement `code/models/sparse_gp.py`: **Consume** `data/processed/features_20pca.csv` (do not re-apply PCA), use a set of inducing points, fit with GPyTorch (CPU mode). Output artifact: `results/models/sparse_gp_model.pt`.
- [~] T016 [US1] Implement `code/main.py` orchestrator to chain data load -> train -> UQ inference. Must generate `results/uq_predictions.csv` (base file) with columns: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90, **exit with code 1 on timeout**, and generate `logs/pipeline.log`.
- [~] T017 [US1] Add logging for model training times and UQ inference durations to monitor 5h budget.
- [~] T018 [US1] Verify `results/uq_predictions.csv` generation and schema compliance.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calibration and Reliability Evaluation (Priority: P2)

**Goal**: Evaluate calibration (ECE, Interval Score) and rank methods based on uncertainty accuracy.

**Independent Test**: Calculate ECE and Interval Score for specified confidence intervals, generate reliability diagrams, and rank methods by ECE.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for ECE calculation logic in `tests/unit/test_uq_metrics.py`
- [~] T020 [P] [US2] Unit test for Interval Score and Sharpness calculation in `tests/unit/test_uq_metrics.py`

### Implementation for User Story 2

- [~] T021 [P] [US2] Implement `code/uq/metrics.py`: ECE (quantile binning), Interval Score, Sharpness.
- [~] T022a [US2] **REQUIRED**: Implement the calculation logic in `code/uq/metrics.py` to separate aleatoric and epistemic uncertainty: **Epistemic variance = variance of means across samples**, **Aleatoric variance = mean of predicted variances**. This task focuses strictly on the mathematical implementation.
- [~] T022b [US2] **REQUIRED**: Write the resulting `uncertainty_type` column to `results/uq_predictions.csv` and `results/calibration_report.csv` as required by FR-008. Also generate `results/uncertainty_decomposition.csv` with detailed breakdown including columns `aleatoric`, `epistemic`, and `total`. This task consumes the output of T022a.
- [~] T023 [US2] Generate reliability diagrams (PDF/PNG) for each method in `results/`.
- [~] T024 [US2] Compute final metrics and save to `results/calibration_report.csv`.
- [~] T025 [US2] Implement ranking logic to identify best-performing method based on ECE and Interval Score.
- [~] T025a [US2] **REQUIRED**: Run the full pipeline (data load -> train -> eval) exactly **3 times** with seeds **42, 43, 44** and aggregate the resulting ECE scores for each method into a temporary file `results/ece_scores_by_seed.json`.
- [~] T026 [US2] Compute Coefficient of Variation (CV) of ECE scores across the 3 runs from `results/ece_scores_by_seed.json`. **MUST** output `results/robustness_report.json` containing the CV value and a boolean `pass` (true if CV ≤ 0.05). **DO NOT exit with code 1** if `pass` is false; report the finding and continue.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Downstream Screening Case Study (Priority: P3)

**Goal**: Demonstrate practical utility by comparing UQ-based screening vs point-prediction screening for perovskite stability.

**Independent Test**: Filter candidates using Expected Loss ranking; verify precision improvement over point-prediction baseline at fixed recall.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T027 [P] [US3] Integration test for screening logic in `tests/integration/test_screening.py`

### Implementation for User Story 3

- [ ] T028 [US3] **REQUIRED**: Implement `code/uq/screening.py`: **Expected Loss ranking** (prediction + variance penalty) as required by FR-007 and Plan Phase 3. Output artifact: `results/screening_candidates.csv`.
- [ ] T028b [US3] **REQUIRED**: Implement `code/uq/screening.py`: Point-prediction baseline screening logic for comparison. Output artifact: `results/screening_baseline.csv`.
- [ ] T029 [US3] Calculate precision/recall curves for both UQ (consumes output of T028) and baseline methods (T028b). **MUST** explicitly compare the filtered set from T028 against the baseline. **Dependency**: T028 and T028b must complete before T029 starts.
- [ ] T030 [US3] Perform McNemar's test or bootstrap t-test to validate statistical significance of precision gain. Output artifact: `results/screening_significance.json` containing p-value and test statistic.
- [ ] T031 [US3] Generate `results/screening_results.csv` with selection metrics and comparison p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033a [P] Update `README.md` with project overview and usage instructions.
- [ ] T033b [P] Update `docs/api.md` with usage examples for `screening.py`.
- [ ] T034 Code cleanup and refactoring of `code/models/` and `code/uq/`: **Remove unused imports** and **enforce black formatting**.
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