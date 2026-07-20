# Tasks: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

**Input**: Design documents from `/specs/001-predict-carbon-diffusion-bcc/`
**Prerequisites**: plan.md, spec.md

**Tests**: Included per spec requirements (US1 validation, US2 model metrics, US3 SHAP analysis).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root per `plan.md`
- Paths shown below assume single project structure defined in `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, contract definition, and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/`)
- [X] T002 Initialize Python 3.11 project with pinned `code/requirements.txt` (pandas, numpy, scikit-learn, xgboost, shap, pymatgen, requests, pyarrow, pytest, psutil)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Create `specs/001-predict-carbon-diffusion-bcc/contracts/dataset.schema.yaml` defining schema for `dataset_cleaned.csv`
- [ ] T005 [P] Create `specs/001-predict-carbon-diffusion-bcc/contracts/model_output.schema.yaml` defining schema for `model_results.json`, `feature_importance.json`, and `variance_partition.csv`
- [X] T006 [P] Implement `code/utils.py` helper functions for periodic table property retrieval (atomic radius, VEC, electronegativity)
- [ ] T007 [P] Setup deterministic logging and error handling infrastructure (including `DataInsufficientError`, `PowerWarning`, `SHAPError`)
- [ ] T008 [P] Configure environment configuration management for random seeds and file paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 [US1] Implement `code/01_download.py` to fetch the verified HuggingFace dataset URL (as defined in `research.md`), generate SHA256 checksum, and store in `data/raw/`. Raise `DataInsufficientError` if fetch fails or checksum mismatch.
- [X] T010 [US1] Implement `code/02_preprocess.py` to:
 - Filter for `structure == "BCC"` and `solute == "C"`
 - Enforce provenance check (exclude entries missing `microstructure_controlled`/`single_crystal` flags) and log excluded entries
 - Normalize atomic fractions to sum to 1.0
 - Compute descriptors: `atomic_radius_variance`, `VEC`, `electronegativity_spread` (per FR-002)
 - Apply `log10` transformation to `diffusion_coefficient` (FR-003)
 - Count total samples: if N < 30, log a `PowerWarning` to the console (do not halt, do not make split decision)
 - Output `data/processed/dataset_cleaned.csv`
- [ ] T011 [P] [US1] Implement `tests/test_preprocess.py` to verify:
 - Output `dataset_cleaned.csv` contains only BCC entries with valid composition
 - Atomic fractions sum to 1.0
 - `log10` transformation is applied correctly
 - Provenance flags are respected (no entries with missing flags in output)
 - **Do not** test LOOCV or PowerWarning logic here; that belongs to training (T015/T025)
- [ ] T012 [P] [US1] Contract test for `specs/001-predict-carbon-diffusion-bcc/contracts/dataset.schema.yaml` validation in `tests/test_preprocess.py`
- [ ] T013 [P] [US1] Validation test ensuring no non-BCC or missing-composition entries remain in `tests/test_preprocess.py`
- [ ] T013b [P] [US1] Implement `tests/test_provenance.py` to explicitly validate the provenance exclusion logic (FR-008, SC-006): verify that entries missing `microstructure_controlled` or `single_crystal` flags are correctly excluded and logged in `code/02_preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Train and Evaluate Composition-Only Regression Models (Priority: P2)

**Goal**: Train RF, XGBoost, Elastic Net models, perform grid search, and run permutation tests.

**Independent Test**: `model_results.json` contains $R^2$, RMSE, MAE, and p-value; runtime < 6 hours on CPU-only CI; memory < 6 GB.

### Tests for User Story 2

- [ ] T014 [P] [US2] Contract test for `specs/001-predict-carbon-diffusion-bcc/contracts/model_output.schema.yaml` validation in `tests/test_contracts.py`
- [X] T015 [US2] Implement `code/03_train.py` to:
 - Read sample count from preprocessing log or re-count `dataset_cleaned.csv`
 - Split data: 80/20 if $N \ge 30$, else LOOCV (emit `PowerWarning` if N < 30)
 - Train Random Forest, XGBoost, and Elastic Net with constrained grid search (a limited set of combinations)
 - Train an **Elastic Net** model explicitly as the "linear baseline" **on the exact same train/test split** as the best ML model (per FR-005)
 - Select best ML model based on cross-validated $R^2$
 - Calculate $R^2$, RMSE, MAE on test set
 - Perform a permutation test with **10,000 iterations** comparing best ML model vs. the Elastic Net baseline (same split)
 - Save trained best model object to `data/outputs/best_model.pkl`
 - Save baseline model object to `data/outputs/baseline_model.pkl`
 - Output `data/outputs/model_results.json`
- [X] T016 [P] [US2] Implement `code/memory_monitor.py` using `psutil` to track and log peak memory usage during model training
- [X] T017 [P] [US2] Add pytest fixture in `tests/test_memory.py` that wraps training execution and asserts peak memory < 6 GB
- [ ] T025 [P] [US2] Implement `tests/test_train.py` to verify:
 - If N < 30, `PowerWarning` is emitted and LOOCV is used
 - If N >= 30, 80/20 split is used
 - The Elastic Net baseline is trained on the **same split** as the best model
 - Permutation test logic (10,000 iterations) and p-value calculation are correct
- [ ] T026 [P] [US2] Implement `tests/test_permutation.py` to specifically verify the statistical validity of the permutation test: correct null distribution generation, [deferred] iteration count, and p-value calculation logic against FR-005

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Quantify Variance Partitioning and Feature Importance (Priority: P3)

**Goal**: Generate SHAP values, partial dependence plots, and variance partitioning metrics.

**Independent Test**: `feature_importance.json` ranks descriptors; `variance_partition.csv` reports adjusted $R^2$ as the composition-explainable upper bound.

### Tests for User Story 3

- [X] T018 [P] [US3] Contract test for `feature_importance.json` schema in `tests/test_contracts.py`
- [ ] T027 [P] [US3] Implement `tests/test_evaluate.py` to verify:
 - Partial dependence plots are saved to `data/outputs/`
 - Plot files exist and contain valid data
 - `feature_importance.json` and `variance_partition.csv` are generated correctly

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/04_evaluate.py` to:
 - Load `best_model.pkl` (produced by T015)
 - Load baseline results (Elastic Net metrics) produced in T015
 - Compute SHAP values for the best model on the test set
 - Rank descriptors by SHAP magnitude and identify top two
 - Generate partial dependence plots for top descriptors and **save them to `data/outputs/`**
 - Calculate **total variance** of the target variable
 - Calculate **adjusted R^2** from the **best model** (not baseline) as the upper bound of variance explainable by composition
 - Calculate **microstructural gap** as `1 - adjusted R^2` (using best model's R^2) and output it explicitly
 - **Explicitly label** the residual variance components as "noise, measurement error, and missing compositional descriptors" in the output (per FR-007)
 - Use the baseline results (from T015) only for the permutation test comparison, not for the variance gap calculation
 - If SHAP computation fails, raise `SHAPError` (do not fallback to other methods)
 - Output `data/outputs/feature_importance.json` and `data/outputs/variance_partition.csv`
- [X] T020 [P] [US3] Add logic to `code/04_evaluate.py` to handle `SHAPError` by logging the error and halting execution gracefully

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T021 [P] Documentation updates in `projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/docs/` (README, data provenance notes, paper drafts) and `specs/001-predict-carbon-diffusion-bcc/quickstart.md`
- [ ] T022 Code cleanup and refactoring for readability
- [ ] T023 [P] Final validation of all contracts and checksums
- [ ] T024 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Depends on US1 (requires `dataset_cleaned.csv` from T010)
- **User Story 3 (P3)**: Depends on US2 (requires `best_model.pkl` and `model_results.json` from T015)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
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
# Launch all tests for User Story 1 together:
Task: "Contract test for dataset.schema.yaml validation in tests/test_preprocess.py"
Task: "Validation test ensuring no non-BCC or missing-composition entries remain in tests/test_preprocess.py"
Task: "Implement tests/test_provenance.py to validate provenance exclusion logic"

# Launch implementation for User Story 1:
Task: "Implement code/01_download.py to fetch verified HuggingFace URL..."
Task: "Implement code/02_preprocess.py to filter, compute descriptors, and log-transform..."
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
 - Developer B: User Story 2 (can start once US1 data is available)
 - Developer C: User Story 3 (can start once US2 model is available)
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
- **Constraint Reminder**: All models MUST run on CPU-only CI (no CUDA, no 8-bit quantization). Dataset size is assumed < 10k rows to fit in available RAM.
- **Memory Constraint**: Peak memory usage must stay within acceptable system limits. as verified by `code/memory_monitor.py` and `tests/test_memory.py`.
- **Baseline Clarity**: The "linear baseline" for permutation tests is explicitly an **Elastic Net** model trained on the **same split** as the best model, as defined in FR-005 and the Plan.
- **Data Integrity**: The `code/01_download.py` script MUST raise `DataInsufficientError` if the verified HuggingFace source returns zero entries or fails checksum validation; it MUST NOT fallback to synthetic data or mock generators.
- **Streaming Rule**: If the initial download exceeds available disk space, `code/01_download.py` must be updated to stream the parquet file in chunks rather than loading it entirely into memory, ensuring the process fits within the disk constraint of the CI runner.
- **Variance Gap**: The "microstructural gap" is calculated as `1 - adjusted R^2` using the **best model's** adjusted R^2, not the baseline's.
- **Plot Output**: Partial dependence plots MUST be saved to `data/outputs/` and validated by T027.