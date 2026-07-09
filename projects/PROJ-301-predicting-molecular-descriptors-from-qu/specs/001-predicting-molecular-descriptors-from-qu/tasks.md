# Tasks: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

**Input**: Design documents from `/specs/001-predict-molecular-descriptors-from-qu/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw`, `data/processed`, `data/results`, `tests/`, `utils/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pins `rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `tqdm`)
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Implement `utils/memory_monitor.py` to track RAM usage and trigger downsampling if ≥ 6.5 GB
- [ ] T005 [P] Implement `utils/parsers.py` for SMILES conversion and XYZ parsing (with error handling for malformed molecules)
- [ ] T006 Create base data model classes for `Molecule`, `FeatureSet`, and `ModelResult` in `code/utils/models.py`
- [ ] T007 Setup reproducible environment: Pin `np.random.seed` and `random.seed` in `code/config.py`
- [ ] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T009.1 [US1] **Spec Amendment**: Update `spec.md` FR-001 to reflect the HuggingFace source (`lisn/QM9`) as the approved requirement, documenting the waiver from the Harvard Dataverse URL as per `plan.md` Spec Conflict Resolution. **Verification**: Ensure FR-001 text contains "HuggingFace" and "lisn/QM9" via string check. **Prerequisite**: Must be completed before T009.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download QM9 dataset, generate 2D/3D features, and ensure memory safety.

**Independent Test**: Verify existence of `.npy` feature matrices and `.csv` labels with matching dimensions for the selected subset, and confirm peak memory ≤ 7 GB.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/01_data_download.py`: **Download, Filter, Split, and Downsample**. 
  1. **Source**: Download QM9 dataset **strictly from the verified HuggingFace source (`lisn/QM9`)** as mandated by `plan.md` (Spec Conflict Resolution Waiver) and T009.1. Validate data integrity by verifying the presence of required DFT columns (dipole, HOMO, LUMO) and valid 3D coordinates.
  2. **Strict Intersection Filter**: **IMMEDIATELY AFTER** loading, drop molecules where DFT labels are missing or 3D coordinates are invalid. Save the filtered indices to `data/processed/split_manifest.json`. **Note**: This logic is implemented in `code/01_data_download.py` as confirmed by T009.2.
  3. **Train/Test Split Construction**: Construct the final Train/Test split (e.g., a majority/minority ratio). **AFTER** the intersection filter is applied to ensure the test set is aligned and valid for baseline calculations (FR-007). Save split indices to `data/processed/split_manifest.json`.
  4. **Dynamic Downsampling**: If memory usage > 6.5 GB, apply **stratified downsampling by atom count** to preserve chemical diversity distribution. Log the downsampling ratio and final count.
  5. **Dependency**: This task MUST complete before T011, T015, T016. **Prerequisite**: T009.1 must be completed first.

- [ ] T011 [P] [US1] Implement `code/02_feature_extraction.py`: Generate 2D Morgan fingerprints (radius=2, nBits=2048) from SMILES, 3D graph features (atomic number, hybridization, distance bins, bond angles, dihedral angles) from XYZ coordinates, and extract DFT reference labels (dipole, HOMO, LUMO) for the **pre-filtered** dataset (loaded from `data/processed/split_manifest.json`). Save outputs to `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, and `data/processed/labels.csv`. **Dependency**: Must wait for T009.

- [ ] T014 [US1] Add unit tests in `tests/test_feature_extraction.py`. Required functions: `test_feature_matrix_shape` (asserts shape matches subset size), `test_label_alignment` (asserts labels match feature indices), `test_3d_parsing_error_handling` (asserts malformed molecules are dropped).

**Checkpoint**: Data pipeline complete. 2D and 3D features are aligned and ready for training.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest Regressors on 2D and 3D features using 5-fold CV within 6 hours.

**Independent Test**: Verify that 5-fold CV completes for both models, `.pkl` files are saved, and total runtime ≤ 6 hours.

### Implementation for User Story 2

- [ ] T015 [P] [US2] Implement `code/03_model_training.py` (2D):
  1. **Grid Search Logic**: Implement K-fold Cross-Validation with `GridSearchCV` using a hyperparameter grid for `n_estimators` spanning a range of low to high values and `max_depth` ∈ {10, 20, None}..
  2. **Model Training & Saving**: Train the final Random Forest Regressor on the full training set using the best parameters found, and save the model to `data/results/model_2d.pkl`.
- [ ] T016 [US2] Implement `code/03_model_training.py` (3D):
  1. **Grid Search Logic**: Implement 5-fold Cross-Validation with `GridSearchCV` using the *identical* hyperparameter grid as T015.
  2. **Model Training & Saving**: Train the final Random Forest Regressor on the full training set using the best parameters found, and save the model to `data/results/model_3d.pkl`.
- [ ] T017 [US2] Implement `code/03_model_training.py` (Aggregator): **Post-Processing & Reporting**. Run *after* T015 and T016 complete. 
  1. Aggregate CV metrics (MAE, RMSE, std_mae per fold) from both models and save to `data/results/cv_metrics.json`. 
  2. **Stability Verification**: Explicitly calculate the stability ratio (std_mae / mean_mae) for each descriptor and verify it is ≤ 5% as mandated by SC-005. 
  3. **Output Format**: Save the raw per-fold MAE list to `cv_metrics.json` under a `fold_maes` key. Save `stability_report.json` with schema: `{\"fold_maes\": [float], \"stability_ratio\": float, \"passed\": bool}`.
- [ ] T020 [US2] Add unit tests in `tests/test_model_training.py` to verify model saving and metric calculation.

**Checkpoint**: Models trained and validated. Performance baselines established.

---

## Phase 5: User Story 3 - Comparative Analysis and Failure Boundary Identification (Priority: P3)

**Goal**: Compute relative error increase, generate parity plots, and identify failure boundaries.

**Independent Test**: Generate error comparison table and parity plots; verify relative error increase calculation and visual distinction between models.

### Implementation for User Story 3

- [ ] T023.1 [US3] **Spec Amendment**: Update `spec.md` US-3 Acceptance Scenario 3 to explicitly mandate the "Wilcoxon signed-rank test" instead of the "paired t-test", resolving the contradiction with the plan. **Dependency**: Must complete before T023.
- [ ] T021 [P] [US3] Implement `code/04_analysis.py` (Metrics): **Load** model artifacts from `data/results/model_2d.pkl` and `model_3d.pkl` (T015/T016). Calculate MAE, RMSE, and Relative Error Increase (REI) for dipole, HOMO, and LUMO on the **identical test set** (constructed in T009). Save results to `data/results/metrics_comparison.json`. **Dependency**: Must wait for T015 and T016.
- [ ] T022 [US3] Implement `code/04_analysis.py` (Plots): **Load** model artifacts from T015/T016. Generate parity plots (Predicted vs. DFT) for both 2D and 3D models. Save to `data/results/parity_2d.png` and `data/results/parity_3d.png`. Ensure plots include regression lines, titles, and axis labels.
- [ ] T023 [US3] Implement `code/04_analysis.py` (Statistics): Perform **non-parametric Wilcoxon signed-rank test** on absolute errors of 2D vs 3D models for each descriptor. Apply Benjamini-Hochberg correction for multiple comparisons. Report p-values to `data/results/statistics.json`. **Dependency**: Must wait for T023.1.
- [ ] T024 [US3] Implement `code/04_analysis.py` (Boundary): Define and report "Failure Boundary" where **REI ≥ 10% OR p < 0.05** (per spec.md US-3 Acceptance Scenario 3 as amended by T023.1). **Save** the list of molecules meeting these criteria to `data/results/failure_boundary.json`. The JSON schema MUST be: `[{"molecule_id": "string", "descriptor": "string", "reason": "string"}, ...]`. **Input**: Load p-values from `data/results/statistics.json` (output of T023).
- [ ] T025 [US3] Implement `code/04_analysis.py` (Baseline): Calculate **Identity Mapping Error** (Mean Predictor) on the **identical test set** (constructed in T009) used for the 3D model to establish the theoretical lower bound (FR-007). This is the error of predicting the mean of the training labels. **Dependency**: Must load test set indices from T009 output. Save result to `data/results/baseline_error.json`.
- [ ] T026 [US3] Implement `code/04_analysis.py` (Stability): Calculate CV stability (std_mae / mean_mae) for both models. **Verify** that stability ≤ 5% (SC-005). 
  1. **Data Source**: Load `fold_maes` from `cv_metrics.json` (T017) or recalculate if T017 failed. **Dependency**: Must wait for T017.
  2. **Reporting**: If stability > 5%, **save `stability_failure_report.json` with details** and log a warning. **Do NOT halt the pipeline**. This allows downstream analysis (T022, T023, T024) to proceed and report the instability. Save the report to `data/results/stability_report.json`.
- [ ] T027 [US3] Save final analysis report and metrics to `data/results/final_report.json`.
- [ ] T028 [US3] Add integration tests in `tests/test_analysis.py` to verify plot generation and metric consistency.

**Checkpoint**: Analysis complete. Failure boundaries identified and visualized.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` (README, quickstart, data-model)
- [ ] T030 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T031 Performance optimization: Ensure data loading is chunked where possible to minimize memory spikes. (Note: Memory Watchdog in T009 handles primary downsampling).
- [ ] T032 [P] Run `pytest` to verify all unit and integration tests pass.
- [ ] T033 Run `quickstart.md` validation to ensure end-to-end pipeline execution.
- [ ] T034 [US2] Implement `code/03_model_training.py` (Monitor): **Runtime Measurement**. Wrap the training pipeline (T015/T016) to measure total runtime. If runtime > 6 hours, trigger a graceful failure with a clear error log and save the partial results to `data/results/runtime_failure.json`.

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
Task: "Implement feature extraction in code/02_feature_extraction.py (T011)"
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