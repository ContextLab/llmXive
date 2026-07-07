# Tasks: Assessing the Stability of Statistical Model Performance Across Data Subsets

**Input**: Design documents from `/specs/001-assess-model-stability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` by creating files: `code/__init__.py`, `code/main.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `tests/__init__.py`, `tests/contract/.gitkeep`, `tests/unit/.gitkeep`, `tests/integration/.gitkeep`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions: `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `scipy>=1.11.0`, `openml>=0.13.0`
- [ ] T003a [P] Configure linting tool by creating `.ruff.toml` with default rules
- [ ] T003b [P] Configure formatting tool by creating `pyproject.toml` with Black settings (e.g., `line-length = 88`, `target-version = ['py311']`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` for seed pinning, logging setup, and error handling wrappers
- [ ] T005 [P] Implement `code/data_loader.py` with OpenML fetch logic, binary-class validation, and SHA-256 checksum caching to `data/raw/`. **MUST** support direct URL fetch for UCI datasets if not available on OpenML. **MUST** explicitly select 15 binary classification datasets (OpenML IDs) defined in `code/config.py` (Constitution Principle VII). **Logic**:
 1. Validate each dataset: if `n_samples < 100` or `n_samples > 100000`, log a warning and **skip only that specific dataset** (do not fail the whole run).
 2. Perform **programmatic spectrum validation**: verify the remaining valid datasets collectively span the 100-100k sample size range.
 3. If the count of valid datasets is insufficient (e.g., < 15), raise a critical error [UNRESOLVED-CLAIM: c_6c91f9b3 — status=not_enough_info].
 4. Implement **robust network error handling**: if a download fails, log the error, skip that dataset, and continue with the rest.
- [X] T006 Implement `code/preprocessor.py` with leakage-safe imputation (median/mode) and scaling wrappers
- [~] T007 [P] Create contract tests in `tests/contract/test_dataset_schema.py` and `tests/contract/test_evaluation_run_schema.py` to validate schemas defined in `specs/001-assess-model-stability/contracts/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repeated Cross-Validation Execution (Priority: P1) 🎯 MVP

**Goal**: Execute repeated k-fold evaluations for LR, RF, Linear SVM on multiple datasets, recording raw metrics.

**Independent Test**: Run on a single small dataset (e.g., Iris) and verify that a sufficient number of records are generated with non-zero variance across all models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests ensure the evaluation engine produces the correct volume and structure of data.

- [~] T009 [P] [US1] Contract test for `EvaluationRun` schema in `tests/contract/test_evaluation_run.py` (Depends on Phase 2 schema definitions)
- [~] T010 [US1] **Write Integration Test** `test_repeated_cv_iris` in `tests/integration/test_cv_engine.py`.
 - **Dataset**: Use a standard benchmark dataset from OpenML., filtering to classes 0 and 1 only to create a binary classification subset.
 - **Assertion**: Verify that the expected number of rows are generated (multiple repeats × 3 models).
 - **Assertion**: Verify non-zero variance in accuracy scores across multiple repeats for at least one model.
 - **Dependency**: Must be written before T011/T012 (TDD).

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/evaluator.py` with `RepeatedStratifiedKFold` logic.
 - **Logic**: Check `n_samples < 100`. If true, log warning and return early (skip dataset). If valid, run `RepeatedStratifiedKFold(n_splits=10, n_repeats=10)`.
 - **Constraint**: It MUST NOT reduce the fold count or alter the dataset for valid cases.
- [~] T012 [US1] Implement training loop for Logistic Regression, Random Forest (n_estimators=100), and Linear SVM [UNRESOLVED-CLAIM: c_3063dfde — status=not_enough_info] in `code/evaluator.py` (Depends on T011 structure)
- [~] T013 [US1] Implement metric calculation (Accuracy, F1) inside the CV loop to prevent leakage
- [~] T014 [US1] Write raw evaluation results to `results/raw_evaluations.csv` with exact columns: `dataset_id` (OpenML ID), `model_name`, `fold_id`, `repeat_id`, `accuracy`, `f1_score`. (Output path must match Plan.md `results/` schema).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Variance Quantification and Correlation Analysis (Priority: P2)

**Goal**: Calculate CV (std/mean) for each (dataset, model) pair and compute Pearson correlations with dataset properties.

**Independent Test**: Feed synthetic data with zero variance and verify CV is 0; verify correlation matrix matches expected synthetic relationships.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Unit test for `calculate_cv` function handling zero-variance cases in `tests/unit/test_analyser.py` <!-- SKIPPED: YAML+regex parse failed (expected '<document start>', but found '<block sequence start>'
 in "<unicode string>", line 6, column 1:
 - **File Created**: `tests/unit/...
 ^) -->
- [~] T017 [P] [US2] Unit test for Pearson correlation calculation in `tests/unit/test_analyser.py`

### Implementation for User Story 2

- [~] T018 [US2] Implement aggregation logic in `code/analyser.py` to compute `mean_accuracy`, `cv_accuracy`, `mean_f1`, `cv_f1` per (dataset, model).
 - **Input**: Must consume `results/raw_evaluations.csv` (validated against schema from T007).
- [~] T019 [US2] Implement **Pearson correlation** calculation in `code/analyser.py` to compute correlation coefficients between CV metrics and dataset properties (sample size, feature count) as required by FR-004.
 - **Primary Output**: Pearson r.
 - **Secondary**: Compute Spearman rho for robustness check.
 - **Verification**: Ensure `correlation_results.csv` contains non-null Pearson r values for all rows.
- [~] T020 [US2] Compute residuals from log-log linear regression of log(CV) against log(n_samples) and log(n_features) as a secondary metric; ensure Pearson r remains the primary output per FR-004
- [~] T021 [US2] Write summary tables to `results/stability_metrics.csv` and `results/correlation_results.csv` including Pearson r, p-values, and regression residuals <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance of Variance Differences (Priority: P3)

**Goal**: Apply Permutation Test on the absolute differences of squared deviations to compare variance distributions and correct for multiple comparisons.

**Independent Test**: Generate synthetic groups with known different variances and verify the test correctly rejects the null hypothesis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for permutation test logic in `tests/unit/test_analyser.py`
- [ ] T024 [P] [US3] Unit test for Bonferroni correction implementation in `tests/unit/test_analyser.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement Permutation Test in `code/analyser.py` to compare variance distributions across LR, RF, and SVM.
 - **Test Statistic**: Calculate the absolute difference of the variances (|Var_A - Var_B|) derived from the squared deviations of accuracy scores for each model pair.
 - **Input**: Must consume variance values from T018 output.
- [ ] T026 [US3] Implement **Bonferroni correction** globally across the set of ALL hypothesis tests (correlations and Permutation Tests) performed across the full collection of datasets to control the **family-wise error rate (FWER)** per FR-007.
 - **Input**: Must consume p-values from `results/correlation_results.csv` (from T019) and `results/permutation_results.csv` (from T025). **Must wait for T025 completion**.
 - **Output**: Adjusted p-values.
- [ ] T027 [US3] Write permutation test results (statistic, raw p-value, adjusted p-value, significance flag) to `results/permutation_results.csv`
- [ ] T028 [US3] Generate a final summary report in `results/final_report.md` using a Markdown template containing sections:
 1. 'Significant Variance Differences' (list datasets where adj_p < 0.05).
 2. 'Model Comparison' (rank by mean CV).
 3. 'Correction Methodology' (confirm Bonferroni application for FWER).
 4. 'Achieved FWER' (calculate and report the effective alpha level).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `specs/001-assess-model-stability/quickstart.md`
- [ ] T031 Performance optimization: Ensure memory usage stays <7GB by processing datasets sequentially and clearing caches [UNRESOLVED-CLAIM: c_bd2e780f — status=not_enough_info]
- [ ] T032 [P] Run end-to-end validation on a small subset of datasets to verify total runtime < 6h [UNRESOLVED-CLAIM: c_a6df4d9a — status=not_enough_info]
- [ ] T033 Run `quickstart.md` validation to ensure reproducibility

---

## Phase X: Review Resolution & Hardening

**Purpose**: Address specific reviewer concerns regarding dataset diversity, statistical rigor, and CI reliability.

- [ ] T035 [P] **Statistical Method Alignment**: Update `code/analyser.py` to explicitly prioritize **Pearson correlation** as the primary test for CV vs. Dataset Properties (n_samples, n_features) to satisfy Spec FR-004. Retain Spearman Rank Correlation as a secondary/robustness check. Update `results/correlation_results.csv` schema to reflect Pearson r and p-value as primary columns. (Addresses Plan T021 & FR-004 interpretation; Note: Plan T021 suggests Spearman, but Spec FR-004 mandates Pearson).
- [ ] T036 [P] **CI Timeout Configuration**: Refactor `ci.yml` to include a specific `timeout-minutes` directive (e.g., 360) for the evaluation job and implement a `signal_handler` in `code/main.py` to gracefully shut down and save partial results if the runner is terminated early, ensuring no silent data loss. (Addresses Plan T008 & Edge Case: Network/Timeout failure).
- [ ] T037 [P] **Zero-Variance Edge Case Handling**: Add explicit logic in `code/analyser.py` to detect datasets/models where `std=0` (perfect stability). Ensure these are handled gracefully in correlation calculations (e.g., excluded from Pearson but logged) and do not cause division-by-zero errors in CV calculation. (Addresses Spec Edge Case: Zero Variance).
- [ ] T038 [P] **Multiple Comparison Correction Verification**: Add a unit test in `tests/unit/test_analyser.py` specifically for the Bonferroni implementation to verify that the adjusted p-values are correctly ordered and monotonic relative to raw p-values, ensuring the FWER control logic is mathematically sound before full pipeline execution. (Addresses FR-007 & SC-005).

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
- **User Story 2 (P2)**: Depends on T014 (raw data generation) - Must wait for US1 completion
- **User Story 3 (P3)**: Depends on T018/T021 (aggregated metrics) - Must wait for US2 completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core logic (evaluator/analyser) before file I/O
- Aggregation before correlation/significance testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- Unit tests for US2 and US3 can be written in parallel while US1 is running

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify a representative sample of generated rows)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Stability metrics)
4. Add User Story 3 → Test independently → Deploy/Demo (Significance testing)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Engine)
 - Developer B: Unit tests for US2/US3
3. Once US1 data is generated:
 - Developer A: User Story 2 (Correlation)
 - Developer B: User Story 3 (Permutation)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All models must run on CPU-only GitHub Actions runners [UNRESOLVED-CLAIM: c_eed811a6 — status=not_enough_info]; no GPU or deep learning models allowed.
- **Constraint**: Datasets <100 samples must be skipped, not downsampled or altered.
- **Constraint**: No fabricated data; all results must come from real OpenML/UCI datasets.
- **Dataset IDs**: The specific 15 OpenML/UCI IDs must be defined in `code/config.py` before execution.