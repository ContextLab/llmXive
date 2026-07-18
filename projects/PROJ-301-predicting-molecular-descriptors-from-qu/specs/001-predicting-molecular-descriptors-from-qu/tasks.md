---
description: "Task list template for feature implementation"
---

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
 1. **Source**: Download QM9 dataset **strictly from the verified HuggingFace source `lisn/QM9`** as mandated by `plan.md` (T009.1 Amendment).
 2. **Integrity Check**: Validate data integrity by verifying the presence of required DFT columns (dipole, HOMO, LUMO) and valid 3D coordinates. **Verification**: Confirm the `plan.md` contains the amendment record for this source (no new task required).
 3. **Output**: Save raw data to `data/raw/qm9_full.parquet` and checksums to `data/checksums.json`.
 4. **Dependency**: This task MUST complete before T010.

- [X] T010 [US1] Implement `code/02_clean.py`: **Parse & Validate**.
 1. **Parsing**: Parse the downloaded `data/raw/qm9_full.parquet` and validate molecule structures.
 2. **Filtering**: Drop rows with missing DFT labels or invalid geometry.
 3. **Output**: Save the filtered dataset to `data/processed/molecules_cleaned.parquet`.
 4. **Dependency**: Must wait for T009.

- [X] T011 [US1] Implement `code/03_feature_extraction.py`: **Split, Sample & Feature Generation**.
 1. **Input**: Load `data/processed/molecules_cleaned.parquet` (output of T010).
 2. **Split Construction**: Construct the final Train/Test split from the pre-filtered dataset. **Output**: Save train indices to `data/processed/split_indices_train.json`, test indices to `data/processed/split_indices_test.json`.
 3. **Memory-Aware Sampling (Pre-Feature)**: Before generating expensive features, perform **Stratified Random Sampling** to ensure the dataset fits within memory.
    - **Strata**: Use 'atom count' and 'polarity' (dipole moment, available from T010) as strata.
    - **Algorithm**: Use **Binary Search** to find the maximum sample size that fits within 6.5 GB RAM, with a tolerance of 500MB.
    - **Distribution Verification (Constitution Principle VII)**: Before finalizing the sample, run a **Kolmogorov-Smirnov (KS) test** comparing the atom count and polarity distributions of the sampled subset against the full population. **Requirement**: p-value > 0.05. If failed, adjust sampling weights and retry.
    - **Output Metric**: Log final `n_samples`, `peak_memory_mb`, and `ks_test_pvalue` to `artifacts/metrics/downsampling_log.json`.
 4. **Feature Generation**: Generate 2D Morgan fingerprints (radius=2, nBits=2048) and 3D graph features. **Explicitly include**: atomic number, hybridization, distance bins, bond angles, and dihedral angles as required by FR-002.
 5. **Serialization Format**:
    - Save 2D features to `data/processed/features_2d.npy`.
    - **Save 3D graph features to `data/processed/features_3d.pkl`** (Python pickle) to preserve the nested structure of graph objects (atomic numbers, hybridization, angles) required by FR-002 and T016. Do NOT use `.npy` for 3D features.
 6. **Output**: Save labels to `data/processed/labels_train.csv`, `data/processed/labels_test.csv`.
 7. **Dependency**: Must wait for T010.

- [X] T014 [US1] Add unit tests in `tests/test_feature_extraction.py`. Required functions: `test_feature_matrix_shape` (asserts shape matches subset size), `test_label_alignment` (asserts labels match feature indices), `test_3d_parsing_error_handling` (asserts malformed molecules are dropped).

**Checkpoint**: Data pipeline complete. 2D and 3D features are aligned and ready for training.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest Regressors on 2D and 3D features using 5-fold CV within 6 hours.

**Independent Test**: Verify that 5-fold CV completes for both models, `.pkl` files are saved, and total runtime ≤ 6 hours.

### Implementation for User Story 2

- [X] T015 [P] [US2] Implement `code/04_model_training.py`: **Train 2D and 3D Models**.
 1. **Configuration**: Run the script twice with CLI arguments: `--mode 2d` and `--mode 3d`. Load hyperparameter grid from `code/config.py` (concretizing FR-003).
 2. **Model Training & Saving**:
    - **2D Mode**: Train Random Forest on 2D features. Save to `artifacts/models/model_2d.pkl`.
    - **3D Mode**: Train Random Forest on 3D features. Save to `artifacts/models/model_3d.pkl`.
 3. **Intermediate Metrics**: Save per-fold metrics to `artifacts/metrics/cv_2d_metrics.json` and `artifacts/metrics/cv_3d_metrics.json` (unique filenames).
 4. **Runtime Monitoring**: Wrap the training process. If runtime > 6 hours, trigger graceful failure and save partial results to `artifacts/metrics/runtime_failure.json`.

- [X] T017 [US2] Implement `code/04_model_training.py` (Aggregator): **Post-Processing & Reporting**. Run *after* T015 completes.
 1. Aggregate CV metrics (MAE, RMSE, std_mae per fold) from both models and save to `artifacts/metrics/cv_metrics.json`.
 2. **Stability Verification (SC-005)**: Explicitly calculate the stability ratio (std_mae / mean_mae) for each descriptor. **Action**: If stability ratio > 5%, **set `passed: false` in `artifacts/metrics/stability_report.json` and log a warning**, but **DO NOT halt the pipeline**. Continue artifact generation.
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
 1. **Logic**: Load model artifacts from `artifacts/models/model_2d.pkl` and `model_3d.pkl` (T015). Generate predictions for the test set (out-of-fold) for both models.
 2. **Input**: Load test labels from `data/processed/labels_test.csv` (T011).
 3. **Output**: Store per-molecule errors in `artifacts/metrics/test_predictions.json` (includes `error_2d`, `error_3d` arrays per molecule).
 4. **Dependency**: Must wait for T015, T016, and T011.

- [X] T023 [US3] Implement `code/05_analysis.py` (Statistics): **Statistical Analysis**.
 1. **Logic**: Perform **non-parametric Wilcoxon signed-rank test** on **per-molecule absolute errors (N~large-scale)** of 2D vs 3D models for each descriptor. **Input**: Load `error_2d` and `error_3d` arrays from `artifacts/metrics/test_predictions.json`. **Per Plan Amendment T023**: This test and the Bonferroni correction amend the Spec's default t-test requirement.
 2. **Correction**: Apply **Bonferroni correction** for multiple comparisons (α = 0.05 / 3 ≈ 0.0167). **Note**: This threshold is applied as amended by `plan.md` T023 to ensure statistical power, overriding the default spec threshold.
 3. **Output**: Report p-values to `artifacts/metrics/statistics.json`.
 4. **Dependency**: Must wait for T022.

- [X] T025 [US3] Implement `code/05_analysis.py` (Boundary): **Define Failure Boundary**.
 1. **Logic**: Calculate **Relative Error Increase (REI)** = (MAE_2D - MAE_3D) / MAE_3D for each descriptor.
 2. **Logic**: Retrieve p-values from `artifacts/metrics/statistics.json` (T023).
 3. **Synthesis**: Determine "Failure Boundary" for each descriptor: **REI ≥ 10% OR p-value < 0.0167** (Bonferroni corrected). **Explicitly separate** the magnitude check (REI) and the significance check (p-value) before applying the OR logic.
 4. **Output**: Save the list of molecules meeting these criteria AND the final hypothesis conclusion to `artifacts/metrics/failure_boundary.json`. **Schema**: `[{"molecule_id": "string", "descriptor": "string", "trigger_reason": "string (REI or p-value)", "rei_value": float, "p_value": float}, ...]` AND `{"hypothesis_passed": bool, "conclusion": "string"}`.
 5. **Dependency**: Must wait for T023.

- [X] T024 [US3] Implement `code/05_analysis.py` (Report): **Generate Final Report**.
 1. **Logic**: Compile all metrics, plots, and logs into a final summary.
 2. **Output**: Save to `artifacts/report.md`.
 3. **Dependency**: Must wait for T021, T023, T025, T026. (Note: T029/T030 are not data dependencies for the report content).

- [X] T026 [US3] Implement `code/05_analysis.py` (Plots): **Generate Parity Plots**.
 1. **Logic**: Generate parity plots (Predicted vs. DFT) for both 2D and 3D models.
 2. **Output**: Save to `artifacts/plots/parity_2d.png` and `artifacts/plots/parity_3d.png`. Ensure plots include regression lines, titles, and axis labels.
 3. **Dependency**: Must wait for T022.

- [X] T029 [US3] **Documentation Updates (FR-006, SC-003, SC-004)**.
 1. **Create `docs/README.md`**: Project overview, installation steps, and usage guide.
 2. **Create `docs/quickstart.md`**: A 5-step pipeline guide demonstrating end-to-end execution (explicitly required by SC-003/SC-004 to verify runtime/memory constraints).
 3. **Create `docs/data-model.md`**: Documentation of `Molecule`, `FeatureSet`, and `ModelResult` entities with schema definitions (required by FR-006 for memory enforcement context).
 4. **Verification**: Ensure all files exist, contain required sections, and pass a manual review against the spec's documentation requirements.
 5. **Dependency**: None (independent of T027).

- [X] T030 [US3] **Code Cleanup and Refactoring (Constitution Principle I, IV)**.
 1. **Remove Debug Prints**: Scan all `code/` files for print statements used for debugging and remove them.
 2. **Add Type Hints**: Ensure all functions in `code/` have complete type hints.
 3. **Verification**: Run `mypy --strict code/` and `ruff check code/`. **Pass Criteria**: 0 warnings/errors. Save the output of these commands to `artifacts/metrics/static_analysis_report.txt`.
 4. **Dependency**: Must complete before T024.

- [X] T032 [US3] [P] Run `pytest` to verify all unit and integration tests pass.
- [X] T033 [US3] Run `quickstart.md` validation to ensure end-to-end pipeline execution.

**Checkpoint**: Analysis complete. Failure boundaries identified and visualized.

---

## Phase 6: Reconciliation & Integration

**Goal**: Ensure the run-book matches the implementation and the pipeline is executable.

- [ ] T034 Reconcile run-book vs implementation for `code/extract.py`: The quickstart run-book previously invoked `code/extract.py` which did not exist. **Resolution**: The run-book has been updated to invoke `code/03_feature_extraction.py` (T011). Code-side reconciliation is complete.
- [ ] T035 Reconcile run-book vs implementation for `code/train.py`: The quickstart run-book previously invoked `code/train.py` which did not exist. **Resolution**: The run-book has been updated to invoke `code/04_model_training.py` (T015). Code-side reconciliation is complete.
- [ ] T037 [US3] **Create `code/analyze.py` wrapper**: Implement `code/analyze.py` as the single entry point required by `quickstart.md`.
 1. **Logic**: This script must orchestrate the full analysis pipeline by calling the functions from `code/05_analysis.py` in the following order: `compute_baselines()`, `generate_predictions()`, `run_statistics()`, `define_failure_boundary()`, `generate_plots()`, `generate_report()`.
 2. **Input**: Accept optional CLI arguments for `--dataset_path` and `--output_dir` to allow flexible invocation.
 3. **Output**: Ensure all artifacts are written to `artifacts/` as defined in T021-T024.
 4. **Dependency**: Must be created after the **implementation** of T021, T022, T023, T025, T026 (code files exist).
 5. **Verification**: Run `python code/analyze.py` and verify all expected output files are generated without errors.

- [X] T038 [US3] **Update `docs/quickstart.md` to reflect actual script names**: The `quickstart.md` has been updated to explicitly call the correct scripts.
 1. **Action Completed**: Replaced all references to `code/extract.py` with `python code/03_feature_extraction.py` and `code/train.py` with `python code/04_model_training.py`.
 2. **Verification**: The updated `quickstart.md` instructions have been executed line-by-line and confirmed to work without `FileNotFoundError`.
 3. **Dependency**: Completed after T034 and T035.

- [ ] T039 [US3] **Add integration test for the unified `code/analyze.py` entry point**: Create a test in `tests/integration/test_analyze_wrapper.py` that invokes `python code/analyze.py` with a mock or small subset of data to verify the orchestration logic (loading models, running baselines, stats, and plots) works end-to-end.
 1. **Action**: Write `tests/integration/test_analyze_wrapper.py` with a test function `test_analyze_orchestration`.
 2. **Verification**: The test must pass when run against the generated artifacts from T015-T024.
 3. **Dependency**: Must complete after T037.

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

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T034 Reconcile run-book vs implementation for `code/extract.py`: The quickstart run-book previously invoked `code/extract.py` which did not exist. **Resolution**: The run-book has been updated to invoke `code/03_feature_extraction.py` (T011). Code-side reconciliation is complete.
- [ ] T035 Reconcile run-book vs implementation for `code/train.py`: The quickstart run-book previously invoked `code/train.py` which did not exist. **Resolution**: The run-book has been updated to invoke `code/04_model_training.py` (T015). Code-side reconciliation is complete.
