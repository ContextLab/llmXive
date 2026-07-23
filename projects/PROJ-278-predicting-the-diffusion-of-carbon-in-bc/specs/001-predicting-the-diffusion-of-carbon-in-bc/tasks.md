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

- [ ] T001 [P] Create project structure per implementation plan: Execute `mkdir -p projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/{code,data/raw,data/processed,tests,docs,specs/001-predict-carbon-diffusion-bcc/contracts}` and create empty `__init__.py` in `code/` and `tests/`.
- [X] T002 [P] Initialize Python 3.11 project with pinned `code/requirements.txt` (pandas, numpy, scikit-learn, xgboost, shap, pymatgen, requests, pyarrow, pytest, psutil)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `code/.ruff.toml` with `[lint]` rules for E4, E7, E9, F, I, N, UP, W and `code/.black.toml` with `line-length = 88` and `target-version = py311`.
- [ ] T004a [P] [US1] Define schema content for `specs/001-predict-carbon-diffusion-bcc/contracts/dataset.schema.yaml`: Specify fields `composition` (str), `structure` (str, const "BCC"), `log_D` (float), `atomic_radius_variance` (float), `VEC` (float), `electronegativity_spread` (float), `mixing_entropy` (float, derived per Plan Phase 1 Step 4), `inv_temperature` (float, derived per Plan Phase 1 Step 4), `microstructure_controlled` (bool), and `single_crystal` (bool). Note: FR-002 mandates the core descriptors; `mixing_entropy` and `inv_temperature` are valid extensions per the plan's feature engineering step.
- [ ] T004b [P] [US1] Write `specs/001-predict-carbon-diffusion-bcc/contracts/dataset.schema.yaml`: Create the YAML file defined in T004a, including all provenance flags.
- [ ] T004c [P] [US1] Define schema content for `specs/001-predict-carbon-diffusion-bcc/contracts/split_config.schema.yaml`: Specify fields `strategy` (str, enum ["80/20", "LOOCV"]), `n_samples` (int), and `warning_emitted` (bool).
- [ ] T005a [P] [US2] Define schema content for `specs/001-predict-carbon-diffusion-bcc/contracts/model_output.schema.yaml`: Specify keys for `model_results.json` (`best_model`, `baseline_model`, `r2`, `rmse`, `mae`, `p_value`), `feature_importance.json` (`ranked_features`, `top_two`), and `variance_partition.csv` (`adjusted_r2`, `microstructural_gap`, `residual_variance_label` constrained to enum ["noise, measurement error, and missing compositional descriptors"]).
- [ ] T005b [P] [US2] Write `specs/001-predict-carbon-diffusion-bcc/contracts/model_output.schema.yaml`: Create the YAML file defined in T005a.
- [X] T006 [P] [US1] Implement `code/utils.py` helper functions for periodic table property retrieval (atomic radius, VEC, electronegativity) using `pymatgen` or `matminer`.
- [X] T007 [P] [US1] Setup deterministic logging and error handling infrastructure: Create `code/logging_config.py` with log format `%(asctime)s - %(levelname)s - %(message)s` and implement custom exceptions `DataInsufficientError`, `PowerWarning`, `SHAPError` inheriting from `Exception`.
- [X] T008 [P] [US1] Configure environment configuration management: Create `code/config.yaml` with keys `random_seed` (int), `data_path` (str), `output_path` (str) and implement a loader in `code/utils.py` to read these values.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T004b/T005b/T004c (Schemas) MUST be completed before T010/T012/T014.

- [X] T009 [US1] Implement `code/01_download.py` to fetch the verified HuggingFace dataset URL (as defined in `research.md`), generate SHA256 checksum, and store in `data/raw/`. Raise `DataInsufficientError` if fetch fails, checksum mismatch, OR if required columns (`structure`, `composition`, `diffusion_coefficient`, `temperature`, `microstructure_controlled`) are missing from the raw file.
- [X] T010 [US1] [Depends on T004b, T004c] Implement `code/02_preprocess.py` to:
 - Filter for `structure == "BCC"` and `solute == "C"`
 - Enforce provenance check (exclude entries missing `microstructure_controlled`/`single_crystal` flags) and log excluded entries
 - Normalize atomic fractions to sum to 1.0
 - Compute descriptors: `atomic_radius_variance`, `VEC`, `electronegativity_spread` (per FR-002), `mixing_entropy`, `inv_temperature`
 - Apply `log10` transformation to `diffusion_coefficient` (FR-003)
 - Count total samples: if N < 30, emit `PowerWarning` AND set `split_strategy=LOOCV`; if N >= 30, set `split_strategy=80/20`.
 - **Explicitly write the chosen strategy to `data/processed/split_config.json`** and validate it against `split_config.schema.yaml` (T004c).
 - Output `data/processed/dataset_cleaned.csv`.
- [X] T011 [US1] Implement `tests/test_preprocess.py` to verify:
 - Output `dataset_cleaned.csv` contains only BCC entries with valid composition
 - Atomic fractions sum to 1.0
 - `log10` transformation is applied correctly
 - Provenance flags are respected (no entries with missing flags in output)
 - **Depends on T010**: Verify `split_config.json` exists, is valid JSON, and matches the schema defined in T004c.
- [ ] T012 [US1] Implement `tests/test_preprocess.py` function `test_dataset_schema_validation` using `jsonschema.validate(data, schema)` to ensure `dataset_cleaned.csv` matches the schema defined in T004b. **Depends on T004b and T010**.
- [X] T013 [US1] [P] Validation test ensuring no non-BCC or missing-composition entries remain: Implement `tests/test_preprocess.py` function `test_bcc_filter_and_completeness` asserting `len(df[df['structure'] != 'BCC']) == 0` and `df['composition'].isnull().sum() == 0`.
- [X] T013b [US1] [P] Implement `tests/test_provenance.py` to explicitly validate the provenance exclusion logic (FR-008, SC-006): verify that entries missing `microstructure_controlled` or `single_crystal` flags are correctly excluded and logged in `code/02_preprocess.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently **provided T004b, T004c and T010 are complete**.

---

## Phase 3: User Story 2 - Train and Evaluate Composition-Only Regression Models (Priority: P2)

**Goal**: Train RF, XGBoost, Elastic Net models, perform grid search, and run permutation tests.

**Independent Test**: `model_results.json` contains $R^2$, RMSE, MAE, and p-value; runtime < 6 hours on CPU-only CI; memory < 6 GB.

### Tests for User Story 2

- [ ] T014 [US2] Implement `tests/test_contracts.py` function `test_model_output_schema_validation` using `jsonschema.validate(data, schema)` to ensure `model_results.json` matches the schema defined in T005b. **Depends on T005b and T015**.
- [X] T015 [US2] Implement `code/03_train.py` to:
 - Read `split_config.json` from T010 to determine split strategy (80/20 or LOOCV).
 - Split data: 80/20 if N >= 30, else LOOCV (emit `PowerWarning` if N < 30).
 - Train Random Forest, XGBoost, and Elastic Net with constrained grid search (a limited set of combinations).
 - Train an **Elastic Net** model explicitly as the "linear baseline" **on the exact same train/test split** as the best ML model (per FR-005).
 - Select best ML model based on cross-validated $R^2$.
 - Calculate $R^2$, RMSE, MAE on test set.
 - Perform a permutation test with **10,000 iterations** comparing best ML model vs. the Elastic Net baseline (same split).
 - Save trained best model object to `data/outputs/best_model.pkl`.
 - Save baseline model object to `data/outputs/baseline_model.pkl`.
 - Output `data/outputs/model_results.json`.
- [X] T016 [US2] [P] Implement `code/memory_monitor.py` using `psutil` to track and log peak memory usage during model training.
- [X] T017 [US2] [P] Add pytest fixture in `tests/test_memory.py` that wraps training execution and asserts peak memory < 6 GB.
- [X] T025 [US2] [P] Implement `tests/test_train.py` to verify:
 - If N < 30, `PowerWarning` is emitted and LOOCV is used; if N >= 30, 80/20 split is used.
 - The Elastic Net baseline is trained on the **same split** as the best model.
 - Permutation test logic (10,000 iterations) and p-value calculation are correct.
 - **Depends on T015**: Verify `best_model.pkl` and `baseline_model.pkl` exist.
- [ ] T026 [US2] [P] Implement `tests/test_permutation.py` to specifically verify the statistical validity of the permutation test: correct null distribution generation, **[deferred] iterations** (hardcoded constant), and p-value calculation logic against FR-005. **Depends on T015**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Quantify Variance Partitioning and Feature Importance (Priority: P3)

**Goal**: Generate SHAP values, partial dependence plots, and variance partitioning metrics.

**Independent Test**: `feature_importance.json` ranks descriptors; `variance_partition.csv` reports adjusted $R^2$ as the composition-explainable upper bound.

### Tests for User Story 3

- [X] T018 [US3] [P] Contract test for `feature_importance.json` schema in `tests/test_contracts.py`.
- [X] T027 [US3] Implement `tests/test_evaluate.py` to verify:
 - Partial dependence plots are saved to `data/outputs/`.
 - Plot files exist and contain valid data.
 - `feature_importance.json` and `variance_partition.csv` are generated correctly.
 - **Depends on T019**: Verify artifacts exist.

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/04_evaluate.py` to:
 - Load `best_model.pkl` (produced by T015) and `baseline_model.pkl` (produced by T015).
 - Compute SHAP values for the best model on the test set.
 - Rank descriptors by SHAP magnitude and identify top two.
 - Generate partial dependence plots for top descriptors and **save them to `data/outputs/`**.
 - Calculate **total variance** of the target variable.
 - Calculate **adjusted R^2** from the **best model** (not baseline) as the upper bound of variance explainable by composition.
 - Calculate **microstructural gap** as `1 - adjusted R^2` (using best model's R^2) and output it explicitly.
 - **Explicitly label** the residual variance components as "noise, measurement error, and missing compositional descriptors" in the output (per FR-007). **Ensure this label appears as a specific row value or column header in `data/outputs/variance_partition.csv` and matches the schema constraint in T005a**.
 - **Verify** that the baseline model's R^2 is NOT used in the gap calculation.
 - Use the baseline results (from T015) only for the permutation test comparison, not for the variance gap calculation.
 - If SHAP computation fails, raise `SHAPError` (do not fallback to other methods).
 - Output `data/outputs/feature_importance.json` and `data/outputs/variance_partition.csv`.
- [X] T020 [US3] [P] Add logic to `code/04_evaluate.py` to handle `SHAPError` by logging the error and halting execution gracefully.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T021a [P] Documentation updates: Create `projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/README.md` (Prerequisites, Installation, Usage, Reproducibility).
- [X] T021b [P] Documentation updates: Create `specs/001-predict-carbon-diffusion-bcc/quickstart.md` (Step-by-step end-to-end run instructions).
- [X] T021c [P] Validation: Run the pipeline end-to-end using `quickstart.md` and generate `docs/validation_report.json` containing exit codes, runtime metrics, and artifact checksums to verify success.
- [X] T022 [P] Code cleanup and refactoring for readability: Ensure `ruff` passes with zero warnings and generate `docs/refactoring_summary.md` listing changed functions and updated docstrings.
- [X] T023 [P] Final validation of all contracts and checksums: Generate `state/validation_log.json` listing all passed schema checks and checksum matches.
- [X] T024a [P] Execute end-to-end validation defined in T021c.
- [X] T024b [P] Verify `docs/validation_report.json` exists and contains valid success metrics.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **T004b/T005b/T004c (Schemas) MUST complete before T010/T012/T014.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 (requires `dataset_cleaned.csv` and `split_config.json` from T010).
- **User Story 3 (P3)**: Depends on US2 (requires `best_model.pkl` and `model_results.json` from T015). **T015 must complete before T019**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T010/T011 which depend on T004b/T004c**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel **WITH OTHER TESTS**, but NOT with their implementation task.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after T010, T004b, and T004c complete):
Task: "Validation test ensuring no non-BCC or missing-composition entries remain in tests/test_preprocess.py (T013)"
Task: "Implement tests/test_provenance.py to validate provenance exclusion logic (T013b)"
# Note: T012 (Contract test) depends on T004b and T010, so it runs after these, but can run in parallel with T013/T013b once dependencies are met.

# Launch implementation for User Story 1:
Task: "Implement code/01_download.py to fetch verified HuggingFace URL... (T009)"
Task: "Implement code/02_preprocess.py to filter, compute descriptors, and log-transform... (T010)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories). **Ensure T004b/T004c/T005b are done before T010.**
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!).
3. Add User Story 2 → Test independently → Deploy/Demo.
4. Add User Story 3 → Test independently → Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1.
 - Developer B: User Story 2 (can start once US1 data is available).
 - Developer C: User Story 3 (can start once US2 model is available).
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies (unless noted).
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Constraint Reminder**: All models MUST run on CPU-only CI (no CUDA, no 8-bit quantization). Dataset size is assumed < 10k rows to fit in available RAM.
- **Memory Constraint**: Peak memory usage must stay within acceptable system limits. as verified by `code/memory_monitor.py` and `tests/test_memory.py`.
- **Baseline Clarity**: The "linear baseline" for permutation tests is explicitly an **Elastic Net** model trained on the **same split** as the best model, as defined in FR-005 and the Plan.
- **Data Integrity**: The `code/01_download.py` script MUST raise `DataInsufficientError` if the verified HuggingFace source returns zero entries or fails checksum validation; it MUST NOT fallback to synthetic data or mock generators.
- **Streaming Rule**: If the initial download exceeds available disk space, `code/01_download.py` must be updated to stream the parquet file in chunks rather than loading it entirely into memory, ensuring the process fits within the disk constraint of the CI runner.
- **Variance Gap**: The "microstructural gap" is calculated as `1 - adjusted R^2` using the **best model's** adjusted R^2, not the baseline's.
- **Plot Output**: Partial dependence plots MUST be saved to `data/outputs/` and validated by T027.
- **Split Logic**: The split strategy (LOOCV vs 80/20) is determined in T010 and logged in `split_config.json` to ensure T015 consumes the correct strategy. **T010 validates this file against T004c**.
- **Permutation Iterations**: The permutation test MUST execute **[deferred] iterations** as specified in FR-005; this constant must be explicitly defined in the code and tested in T026.