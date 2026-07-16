# Tasks: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

**Input**: Design documents from `/specs/001-predict-molecular-descriptors-from-qu/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/raw`, `data/processed`, `data/results`, `tests/`, `utils/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pins `rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `tqdm`, `huggingface_hub`, `matplotlib`, `seaborn`, `scipy`)
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Implement `utils/memory_monitor.py` to track RAM usage and trigger downsampling if ≥ 6.5 GB
- [X] T005 [P] Implement `utils/parsers.py` for SMILES conversion and XYZ parsing (with error handling for malformed molecules)
- [X] T006 Create base data model classes for `Molecule`, `FeatureSet`, and `ModelResult` in `code/utils/models.py`
- [X] T007 Setup reproducible environment: Pin `np.random.seed` and `random.seed` in `code/config.py`
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download QM9 dataset, generate 2D/3D features, and ensure memory safety.

**Independent Test**: Verify existence of `.npy` feature matrices and `.csv` labels with matching dimensions for the selected subset, and confirm peak memory ≤ 7 GB.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/01_download.py`: **Download & Verify**.
 1. **Source**: Download QM9 dataset **strictly from the verified HuggingFace source (`lisn/QM9`)** as mandated by `plan.md` (T009.1 Amendment).
 2. **Integrity Check**: Validate data integrity by verifying the presence of required DFT columns (dipole, HOMO, LUMO) and valid 3D coordinates. **Verification**: Confirm the `plan.md` contains the amendment record for this source (no new task required).
 3. **Output**: Save raw data to `data/raw/qm9_full.parquet` and checksums to `data/checksums.json`.
 4. **Dependency**: This task MUST complete before T010.

- [X] T010 [US1] Implement `code/02_clean.py`: **Parse & Validate**.
 1. **Parsing**: Parse the downloaded `data/raw/qm9_full.parquet` and validate molecule structures.
 2. **Filtering**: Drop rows with missing DFT labels or invalid geometry.
 3. **Output**: Save the filtered dataset to `data/processed/molecules_cleaned.parquet`.
 4. **Dependency**: Must wait for T009.

- [X] T011 [US1] Implement `code/03_feature_extraction.py`: **Split & Feature Generation**.
 1. **Input**: Load `data/processed/molecules_cleaned.parquet` (output of T010).
 2. **Split Construction**: Construct the final Train/Test split from the pre-filtered dataset. **Output**: Save train indices to `data/processed/split_indices_train.json`, test indices to `data/processed/split_indices_test.json`.
 3. **Feature Generation**: Generate 2D Morgan fingerprints (radius=2, nBits=2048) and 3D graph features. **Explicitly include**: atomic number, hybridization, distance bins, bond angles, and dihedral angles as required by FR-002.
 4. **Downsampling Logic**: Monitor memory usage. If usage exceeds 6.5 GB, apply **Stratified Random Sampling** (strata: atom count, polarity) to reduce the sample size. **Target**: The target is explicitly the maximum sample size that fits within the 6.5 GB memory limit. **Stopping Condition**: Reduce sample size iteratively, but **limit to a maximum of 5 iterations**. If the limit is still not met after 5 iterations, fail with a clear error log. **Output Metric**: Log final `n_samples` and `peak_memory_mb` to `artifacts/metrics/downsampling_log.json`.
 5. **Output**: Save outputs to `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, `data/processed/labels_train.csv`, `data/processed/labels_test.csv`.
 6. **Dependency**: Must wait for T010.

- [X] T014 [US1] Add unit tests in `tests/test_feature_extraction.py`. Required functions: `test_feature_matrix_shape` (asserts shape matches subset size), `test_label_alignment` (asserts labels match feature indices), `test_3d_parsing_error_handling` (asserts malformed molecules are dropped).

**Checkpoint**: Data pipeline complete. 2D and 3D features are aligned and ready for training.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest Regressors on 2D and 3D features using 5-fold CV within 6 hours.

**Independent Test**: Verify that 5-fold CV completes for both models, `.pkl` files are saved, and total runtime ≤ 6 hours.

### Implementation for User Story 2

- [X] T015 [P] [US2] Implement `code/04_model_training.py` (2D):
 1. **Grid Search Logic**: Implement K-fold Cross-Validation with `GridSearchCV` using a hyperparameter grid: `n_estimators` ∈ {100, 500, 1000}, `max_depth` ∈ {10, 20, None}.
 2. **Model Training & Saving**: Train the final Random Forest Regressor on the full training set using the best parameters found, and save the model to `artifacts/models/model_2d.pkl`.
 3. **Runtime Monitoring**: Wrap the training process to measure total runtime. If runtime > 6 hours, trigger a graceful failure with a clear error log and save partial results to `artifacts/metrics/runtime_failure.json`.

- [X] T016 [US2] Implement `code/04_model_training.py` (3D):
 1. **Grid Search Logic**: Implement k-fold Cross-Validation with `GridSearchCV` using the *identical* hyperparameter grid as T015.
 2. **Model Training & Saving**: Train the final Random Forest Regressor on the full training set using the best parameters found, and save the model to `artifacts/models/model_3d.pkl`.
 3. **Runtime Monitoring**: Wrap the training process to measure total runtime. If runtime > 6 hours, trigger a graceful failure with a clear error log and save partial results to `artifacts/metrics/runtime_failure.json`.

- [X] T017 [US2] Implement `code/04_model_training.py` (Aggregator): **Post-Processing & Reporting**. Run *after* T015 and T016 complete.
 1. Aggregate CV metrics (MAE, RMSE, std_mae per fold) from both models and save to `artifacts/metrics/cv_metrics.json`.
 2. **Stability Verification (SC-005)**: Explicitly calculate the stability ratio (std_mae / mean_mae) for each descriptor. **Action**: If stability ratio > 5%, **set `passed: false` in `artifacts/metrics/stability_report.json` and log a warning**, but **DO NOT halt the pipeline**. Continue artifact generation to allow analysis of why stability failed.
 3. **Output Format**: Save the raw per-fold MAE list to `cv_metrics.json` under a `fold_maes` key. Save `artifacts/metrics/stability_report.json` with schema: `{\"fold_maes\": [float], \"stability_ratio\": float, \"passed\": bool}`.

- [X] T020 [US2] Add unit tests in `tests/test_model_training.py` to verify model saving and metric calculation.

**Checkpoint**: Models trained and validated. Performance baselines established.

---

## Phase 5: User Story 3 - Comparative Analysis and Failure Boundary Identification (Priority: P3)

**Goal**: Compute relative error increase, generate parity plots, and identify failure boundaries.

**Independent Test**: Generate error comparison table and parity plots; verify relative error increase calculation and visual distinction between models.

### Implementation for User Story 3

- [X] T021 [P] [US3] Implement `code/05_analysis.py` (Baselines): **Compute Mean Predictor Error**.
 1. **Logic**: Calculate the error of predicting the mean of the training labels (Zero-Order Baseline) for each descriptor (dipole, HOMO, LUMO) on the test set. **Note**: This implements the Plan's interpretation of FR-007 ("theoretical lower bound") as the Mean Predictor Error.
 2. **Input**: Load `data/processed/labels_test.csv` (produced by T011).
 3. **Output**: Save results to `artifacts/metrics/baseline_error.json`.
 4. **Dependency**: Must wait for T011.

- [X] T022 [US3] Implement `code/05_analysis.py` (Predictions): **Generate Predictions**.
 1. **Logic**: Load model artifacts from `artifacts/models/model_2d.pkl` and `model_3d.pkl` (T015/T016). Generate predictions for the test set (out-of-fold) for both models.
 2. **Input**: Load test labels from `data/processed/labels_test.csv` (T011).
 3. **Output**: Store per-molecule errors in `artifacts/metrics/test_predictions.json` (includes `error_2d`, `error_3d` arrays per molecule).
 4. **Dependency**: Must wait for T015, T016, and T011.

- [X] T023 [US3] Implement `code/05_analysis.py` (Statistics): **Statistical Analysis**.
 1. **Logic**: Perform **non-parametric Wilcoxon signed-rank test** on **per-molecule absolute errors (N~large-scale)** of 2D vs 3D models for each descriptor. **Input**: Load `error_2d` and `error_3d` arrays from `artifacts/metrics/test_predictions.json`.
 2. **Correction**: Apply **Bonferroni correction** for multiple comparisons (α = 0.05 / 3 ≈ 0.0167). **Note**: This threshold is applied as amended by `plan.md` T023 to ensure statistical power, overriding the default spec threshold.
 3. **Output**: Report p-values to `artifacts/metrics/statistics.json`.
 4. **Dependency**: Must wait for T022.

- [X] T024 [US3] Implement `code/05_analysis.py` (Boundary): **Define Failure Boundary**.
 1. **Logic**: Define "Failure Boundary" where **Relative Error Increase (REI) ≥ 10% OR p-value < 0.0167** (Bonferroni corrected).
 2. **Input**: Load p-values from `artifacts/metrics/statistics.json` (output of T023) and MAE values.
 3. **Synthesis**: **Generate a binary conclusion (Pass/Fail) for the research hypothesis** based on whether any descriptor meets the failure boundary criteria. **Output**: Save the list of molecules meeting these criteria AND the final hypothesis conclusion to `artifacts/metrics/failure_boundary.json`. Schema: `[{"molecule_id": "string", "descriptor": "string", "reason": "string"}, ...]` AND `{"hypothesis_passed": bool, "conclusion": "string"}`.
 4. **Dependency**: Must wait for T023.

- [X] T025 [US3] Implement `code/05_analysis.py` (Plots): **Generate Parity Plots**.
 1. **Logic**: Generate parity plots (Predicted vs. DFT) for both 2D and 3D models.
 2. **Output**: Save to `artifacts/plots/parity_2d.png` and `artifacts/plots/parity_3d.png`. Ensure plots include regression lines, titles, and axis labels.
 3. **Dependency**: Must wait for T022.

- [X] T026 [US3] Implement `code/05_analysis.py` (Stability): **Report Stability**.
 1. **Logic**: Load `stability_report.json` from T017. If stability > 5% (i.e., `passed: false`), **save `artifacts/metrics/stability_failure_report.json` with details** and log a warning. **Do NOT halt the pipeline**.
 2. **Dependency**: Must wait for T017.

- [X] T027 [US3] Implement `code/05_analysis.py` (Report): **Generate Final Report**.
 1. **Logic**: Compile all metrics, plots, and logs into a final summary.
 2. **Output**: Save to `artifacts/report.md`.
 3. **Dependency**: Must wait for T021, T023, T024, T025, **and T026**.

- [X] T028 [US3] Add integration tests in `tests/test_analysis.py` to verify plot generation and metric consistency.

**Checkpoint**: Analysis complete. Failure boundaries identified and visualized.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] **Documentation Updates (FR-006, SC-003, SC-004)**.
 1. **Create `docs/README.md`**: Project overview, installation steps, and usage guide.
 2. **Create `docs/quickstart.md`**: A 5-step pipeline guide demonstrating end-to-end execution (explicitly required by SC-003/SC-004 to verify runtime/memory constraints).
 3. **Create `docs/data-model.md`**: Documentation of `Molecule`, `FeatureSet`, and `ModelResult` entities with schema definitions (required by FR-006 for memory enforcement context).
 4. **Verification**: Ensure all files exist, contain required sections, and pass a manual review against the spec's documentation requirements.

- [ ] T030 **Code Cleanup and Refactoring (Constitution Principle I, IV)**.
 1. **Remove Debug Prints**: Scan all `code/` files for print statements used for debugging and remove them.
 2. **Add Type Hints**: Ensure all functions in `code/` have complete type hints.
 3. **Verification**: Run `mypy --strict code/` and `ruff check code/`. **Pass Criteria**: 0 warnings/errors. Save the output of these commands to `artifacts/metrics/static_analysis_report.txt`.

- [ ] T031 **Performance Optimization: Chunked Data Loading (FR-006)**.
 1. **Implementation**: Implement chunked data loading in `code/01_download.py` and `code/03_feature_extraction.py` using a `chunk_size` parameter (e.g., 1000 rows) to enforce the memory limits mandated by FR-006.
 2. **Verification**: Generate a profiling log (`artifacts/metrics/memory_profile.log`) showing peak memory reduction compared to non-chunked loading.
 3. **Testing**: Add a unit test in `tests/test_feature_extraction.py` (`test_chunked_loading`) that asserts the data loader iterates in chunks and does not load the entire dataset into memory at once.

- [ ] T032 [P] Run `pytest` to verify all unit and integration tests pass.
- [ ] T033 Run `quickstart.md` validation to ensure end-to-end pipeline execution.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (features/labels)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2 (model predictions/metrics)

### Within Each User Story

- Models before services
- Services before endpoints (if applicable)
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
# Launch all tasks for User Story 1 together (after Foundational):
Task: "Implement feature extraction in code/03_feature_extraction.py (T011)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (data pipeline works, memory safe)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - *Can start once T011 is done*
 - Developer C: User Story 3 (Analysis) - *Can start once T015/T016 are done*
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