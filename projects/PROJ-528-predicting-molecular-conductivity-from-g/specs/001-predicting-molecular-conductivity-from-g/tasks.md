# Tasks: Predicting Molecular Conductivity from Graph-Based Features

**Input**: Design documents from `/specs/001-predicting-molecular-conductivity-from-g/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure by executing: `mkdir -p code tests data/raw data/processed contracts docs`
- [X] T002 Initialize Python 3.x project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `networkx`
- [X] T003 [P] Configure linting and formatting tools by creating `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']) sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration module (`code/config.py`) defining constants: `DATA_PATH`, `SEED`, `OUTLIER_SIGMA`, `VIF_THRESHOLD`, `TARGET_VAR` (default: 'conductivity')
- [X] T005 [P] Implement data validation utilities in `code/validators.py` with functions `validate_smiles(smiles_str)` and `check_target_range(values, min_log_range=3.0)`
- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` that configures a rotating file handler to `logs/pipeline.log` with JSON formatting
- [X] T007 Create `code/models.py` with Pydantic classes `Molecule` (fields: smiles, descriptors, target) and `Descriptor` (fields: name, value)
- [X] T008 [P] Implement scaffold splitting utility in `code/scaffold_split.py` using `rdkit.Chem.Scaffolds.MurckoScaffold` to ensure structural diversity and prevent data leakage (FR-002)
- [X] T009 Create `contracts/model_results_schema.yaml` defining fields: `r2`, `mae`, `cv_scores`, `sensitivity_data`, `vif_scores`, `quantum_proxy_metadata`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load molecular structures and compute graph-based descriptors (Priority: P1) 🎯 MVP

**Goal**: Parse SMILES, compute standard topological descriptors, implement quantum-inspired proxies, and address resonance-related structural features as per reviewer feedback.

**Independent Test**: Can be fully tested by running the descriptor computation pipeline on a sample of SMILES strings and verifying that the output table contains all required descriptor columns with valid numeric values for each molecule.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write unit test code (expected to fail) before implementation

- [X] T010 [P] [US1] Write unit test code for aromaticity index calculation on benzene (SMILES: "c1ccccc1") in `tests/test_descriptors.py`. Function name: `test_aromaticity_benzene`. Assert that `aromaticity_index` equals 1.0 (or a specific non-zero value defined by the implementation).
- [X] T011 [P] [US1] Write unit test code for conjugation path length on butadiene vs. butane in `tests/test_descriptors.py`. Function name: `test_conjugation_path_length`. Use SMILES "C=CC=C" (butadiene) and "CCCC" (butane). Assert that butadiene's `conjugation_length` is greater than butane's.
- [X] T012 [P] [US1] Write unit test code for descriptor computation on mixed hybridization molecules in `tests/test_descriptors.py`. Function name: `test_mixed_hybridization_descriptors`. Use a molecule with both sp2 and sp3 carbons (e.g., "CC=C"). Assert that all computed descriptors are finite numbers and no NaN values are present.

### Implementation for User Story 1

- [X] T013 [US1] Implement `load_smiles(path: str) -> pd.DataFrame` in `code/data_loader.py` returning DataFrame with columns [smiles, valid, error_msg]
- [X] T014a [US1] Implement **Base Graph Descriptors** in `code/descriptors.py` (FR-001). Compute: `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`.
- [X] T014b [US1] Implement **Aromaticity & Ring Descriptors** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromaticity_index`, `ring_count`, `huckel_aromaticity_count`, `clar_aromaticity_proxy`.
- [X] T014c [US1] Implement **Conjugation Descriptors** in `code/descriptors.py` (FR-001). Compute: `conjugation_length` (longest simple path in conjugated subgraph), `num_conjugated_bonds`, `conjugation_density`.
- [X] T014d [US1] Implement **Resonance & Bond-Order Proxies** in `code/descriptors.py` (Reviewer Feedback). Compute: `mean_bond_order`, `max_bond_order`, `bond_order_variance`, `total_polarity`, `mean_polarity`, `max_polarity`, `estimated_resonance_energy_kcal`, `resonance_energy_density`.
  - **Logic**:
    1. Parse SMILES to RDKit molecule object.
    2. Assign bond orders (1.5 for aromatic, 2.0 for double, 1.0 for single) with resonance correction for conjugated systems.
    3. Calculate bond polarity using Pauling electronegativity and bond lengths.
    4. Estimate resonance energy based on aromatic ring count and conjugated paths.
    5. **Note**: All descriptors MUST be computed. If a calculation fails for a specific molecule, log a warning and set the value to NaN for that molecule only. Do not halt the entire pipeline. (FR-001, FR-008)
    6. **Runtime Monitoring**: Log a warning if descriptor computation for a single molecule exceeds 30 minutes, but continue processing. Do NOT exit. (FR-010)

- [X] T017 [US1] **Merged into T014d**: Logic for quantum fallback is handled within the descriptor computation. If a quantum-derived descriptor is missing, use the topological proxy and log a warning.
- [X] T018 [US1] **Merged into T013**: Logic for invalid SMILES and missing conductivity is handled in `load_smiles`. Invalid SMILES are excluded with a log. Missing conductivity is excluded with a log. (FR-012)

- [ ] T019 [US1] Write descriptor computation results to `data/processed/descriptors.csv` with EXACT columns: [smiles, status, degree_mean, degree_std, degree_max, degree_min, path_length_mean, path_length_std, path_length_max, path_length_min, aromaticity_index, huckel_aromaticity_count, clar_aromaticity_proxy, conjugation_length, num_conjugated_bonds, conjugation_density, ring_count, mean_bond_order, max_bond_order, bond_order_variance, total_polarity, mean_polarity, max_polarity, estimated_resonance_energy_kcal, resonance_energy_density].
  - **Logic**: Iterate through computed descriptors. If any row has NaN values in the required descriptor columns, drop the row and log: "Dropped {count} rows due to NaN values in descriptors." (FR-001, FR-008)
  - **DEPENDS ON**: T014a, T014b, T014c, T014d

**Checkpoint**: Descriptor computation logic is ready, and results are written to file.

---

## Phase 4: User Story 2 - Train regression models and evaluate predictive performance (Priority: P2)

**Goal**: Split data, train RF/GB models, handle outliers via sensitivity analysis, and validate target variable dynamic range.

**Independent Test**: Can be fully tested by running the training pipeline on a fixed dataset and verifying that both models produce R² scores, MAE values, and cross-validation metrics in a structured results file.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Write unit test in `tests/test_scaffold_split.py::test_no_scaffold_leakage` that asserts intersection of MurckoScaffolds between train and test sets is empty.
- [X] T024 [P] [US2] Write unit test in `tests/test_model_training.py::test_log_transform_target` that asserts np.log(input_values) matches expected_output for a known array.
- [X] T025 [P] [US2] Write unit test in `tests/test_analysis.py::test_filter_outliers_threshold` that asserts filter_outliers(df, 'target', 3.0) returns a DataFrame with exactly N rows where N is the count of rows with |z| <= 3.0.

### Implementation for User Story 2

- [ ] T026a [US2] **Governance**: Create Change Request document at `docs/change_request_HOMO_LUMO.md` detailing the scope shift, justification, and impact on FR-003 if HOMO-LUMO gap is used as the target variable.
- [ ] T026b [US2] **Governance**: Update `spec.md` (or create a patch file) to reflect the new target variable and research question if HOMO-LUMO gap is used.
- [ ] T026c [US2] **Governance**: Validate that T026a and T026b have been completed if HOMO-LUMO gap is used. If not, halt with error.
  - **Logic**: Check for 'conductivity'. If present and log-range >= 3.0, proceed. If missing, check for 'HOMO_LUMO_gap'. If missing, **HALT** with `sys.exit(1)` and error message: "CRITICAL: No valid target variable found (Conductivity or HOMO-LUMO gap missing)." If HOMO_LUMO exists, **log a CRITICAL warning** and execute T026a/b/c. Reframe the research question in all subsequent outputs to "Electronic Delocalization Potential". (FR-003, Plan Scope Adjustment, FR-011, Constitution Principle V)
  - **DEPENDS ON**: T019 (Data must be loaded and descriptors computed before target validation)

- [X] T027 [US2] Implement scaffold-based train/test split (a majority/minority ratio) in `code/scaffold_split.py` AFTER T026 completes (FR-002)
- [X] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO) in `code/model_training.py`. Use natural logarithm (`np.log`) on the target column. Create a new column named `log_{target_var}`. (FR-003)
- [X] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity in `code/analysis.py`. Function signature: `def filter_outliers(df, target_col, sigma_threshold):`. Logic: Calculate z-scores for `target_col`. Filter rows where `abs(z_score) <= sigma_threshold`. Return filtered DataFrame. Ensure it reuses the exact split indices from T027 and seed from T004. (FR-007)
- [X] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target in `code/model_training.py`. RF: `n_estimators=100`, `max_depth=None`, `random_state=SEED`. GB: `n_estimators=100`, `learning_rate=0.1`, `random_state=SEED`. **Note**: Initial training uses data filtered by T031 with default threshold (3.0σ). (FR-003)
- [X] T030 [US2] Implement 5-fold cross-validation and metric recording in `code/model_training.py`. Use `cross_val_score` with `cv=5` and `scoring='r2'`. Record mean and std of R² scores. (FR-004)
- [X] T032 [US2] Implement sensitivity analysis loop in `code/analysis.py`. **Logic**:
 1. Define thresholds: `{2.5, 3.0, 3.5}`.
 2. For each threshold, call T031 to filter data, then retrain models (using T029 logic) and record R².
 3. Perform a **Kruskal-Wallis test** on the R² scores across the 3 thresholds.
 4. Save results to `data/processed/sensitivity_analysis.json` with keys: `thresholds`, `r2_scores` (list of raw scores), `kruskal_statistic`, `p_value`, `range`, `population_variance`.
 5. **Artifact Versioning**: Save the intermediate model objects for each threshold to `data/processed/models_intermediate/model_{threshold}.pkl` and record their content hashes in `data/processed/model_hashes.json` to satisfy Constitution Principle IV (Single Source of Truth). (FR-007)
 - **DEPENDS ON**: T029, T031

- [ ] T033a [US2] **Initialize**: Create `data/processed/model_results.json` with empty/default structure if no VIF loop or sensitivity analysis has run yet. Keys: `rf_r2`, `gb_r2`, `cv_scores`, `sensitivity_analysis`, `vif_scores`. (FR-003, FR-004, FR-007)
  - **DEPENDS ON**: T026c (Must run before any model training)

- [ ] T033b [US2] **Finalize**: Update `data/processed/model_results.json` with final R²/MAE from T039d (VIF loop) and T032 (Sensitivity). (FR-003, FR-004, FR-007)
  - **DEPENDS ON**: T039d, T032, T033a

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate feature importance analysis and correlation plots (Priority: P3)

**Goal**: Analyze feature importance, apply VIF filtering, correct for multiple comparisons, and generate visualizations.

**Independent Test**: Can be fully tested by running the analysis script on a trained model and verifying that feature importance rankings are exported and correlation plots are generated as image files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Write unit test in `tests/test_analysis.py::test_vif_calculation` that asserts calculate_vif(X) returns a dictionary with expected VIF scores for a known feature matrix X.
- [X] T035 [P] [US3] Write unit test in `tests/test_analysis.py::test_bh_correction` that asserts apply_bh_correction(p_values) returns adjusted p-values matching the expected output for a known input array.
- [X] T036 [P] [US3] Write unit test in `tests/test_plotting.py::test_correlation_plot_ci` that asserts generate_plot(...) creates a file at data/processed/corr_plot.png with width >= 800px and height >= 600px.

### Implementation for User Story 3

- [ ] T039a [US3] Implement VIF calculation function in `code/analysis.py`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor`. Input: feature matrix (numpy array). Output: dictionary mapping feature names to VIF scores. **This function MUST be callable iteratively.** (FR-013)
- [ ] T039b [US3] Implement feature exclusion logic for features with VIF > 10 in `code/analysis.py`. If any feature has VIF > 10, mark it for exclusion. (FR-013)
- [ ] T039c [US3] Implement iterative VIF loop in `code/analysis.py`. **Prerequisites**: Must run on data filtered by T031 (outliers) and use split indices from T027.
 1. WHILE any VIF > 10:
 - Exclude the feature with the HIGHEST VIF.
 - Recalculate VIF on the reduced feature set (T039a).
 - Retrain the model using the EXACT split indices and seed.
 - Record `iteration`, `excluded_feature`, `vif_scores`, `r2`, `mae`.
 - **Artifact Versioning**: Save the intermediate model for this iteration to `data/processed/models_intermediate/vif_iter_{iteration}.pkl` and record its content hash in `data/processed/model_hashes.json`.
 2. Guard Clause: If feature set becomes empty, log critical error and halt.
 3. Save `vif_iteration_log.json` (keys: `iterations: [{iteration, excluded_feature, vif_scores, r2, mae}]`).
 4. **Re-evaluate final model** on the test set and update `model_results.json` (T033b) with the final R²/MAE. (FR-013)
 - **DEPENDS ON**: T031, T027, T029, T039a, T039b

- [ ] T039d [US3] **Finalize VIF**: Write the final VIF results to `vif_iteration_log.json` and update `model_results.json` with the final model metrics. (FR-013)
  - **DEPENDS ON**: T039c

- [ ] T040 [US3] Compute feature importance rankings on the final VIF-filtered model in `code/analysis.py`. Use `sklearn.inspection.permutation_importance` with `n_repeats=10` and `random_state=SEED`. **Save the ranked list to `data/processed/feature_importance.csv`**. Output format: a ranked list of (feature, importance_score). (FR-005)
 - **DEPENDS ON**: T039d

- [ ] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values in `code/analysis.py`. Use `scipy.stats.pearsonr`. Output format: a dictionary mapping feature names to (correlation_coefficient, p_value). (FR-005)
- [ ] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values in `code/analysis.py`. Use `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output format: a dictionary mapping feature names to adjusted p-values. (FR-006)
- [ ] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`. **Logic**: Select **top features by permutation importance score (descending)**, with ties broken by alphabetical feature name. **Keys**: `top_5_features`, `adjusted_p_values`, `fdr_method`. (FR-005)
 - **DEPENDS ON**: T040 (Feature importance ranking)
 - **NOTE**: T045 is independent of T043 (Plotting) and can run in parallel.
- [ ] T043 [US3] Generate scatter plots with regression lines and confidence intervals for **top 5 features** (identified in T040) in `code/plotting.py`. Use `seaborn.regplot` with `ci=95`. **Save plots as PNG files to `data/processed/corr_plot_top5.png`**. (FR-005)
 - **DEPENDS ON**: T040, T041, T042

---

## Phase 6: Resonance & Bond-Order Augmentation (Priority: P3 - Reviewer Revision)

**Goal**: Address reviewer `linus-pauling-simulated`'s concern regarding the fundamental role of resonance in electronic delocalization by augmenting descriptors with bond-order and electronegativity-based proxies.

**Independent Test**: Verify that molecules with known conjugated systems (e.g., benzene, butadiene) exhibit higher `resonance_weighted_bond_order` and `polarity_index` scores compared to saturated analogs (e.g., cyclohexane, butane).

### Implementation for Resonance Augmentation

- [X] T052 [US1] **Merged into T014d**: Logic for Bond Order Estimation is handled in T014d.
- [X] T053 [US1] **Merged into T014d**: Logic for Electronegativity-Polarity Descriptor is handled in T014d.
- [X] T054 [US1] **Merged into T014d**: Logic for Resonance Energy Proxy is handled in T014d.

- [ ] T055 [US3] Update `data/processed/descriptors.csv` schema to include new resonance columns from T014d.
  **Action**: Modify the `write_descriptors` function (or T019 logic) to include: `mean_bond_order`, `max_bond_order`, `bond_order_variance`, `total_polarity`, `mean_polarity`, `max_polarity`, `estimated_resonance_energy_kcal`, `resonance_energy_density`.
  **DEPENDS ON**: T014d, T019

- [ ] T056 [US3] Retrain models (RF and GB) including the new resonance descriptors to evaluate their impact on predictive performance.
  **Logic**:
 1. Reload `descriptors.csv` with new columns.
 2. Re-run the VIF filtering loop (T039a-d) to ensure new features don't introduce collinearity.
 3. Retrain models and compare R²/MAE against the baseline (without resonance features).
 4. Log the improvement (or degradation) in `data/processed/resonance_impact_report.json`.
 5. **Hypothesis**: Models including resonance proxies should show higher R² for conjugated systems. (Reviewer Feedback: "should improve predictive fidelity")
  **DEPENDS ON**: T014d, T019, T039d

- [ ] T057 [US3] Generate a specific correlation plot for `estimated_resonance_energy_kcal` vs. target variable (conductivity/HOMO-LUMO) in `code/plotting.py`.
  **Action**: Create a scatter plot with regression line and 95% CI, saving to `data/processed/corr_plot_resonance.png`.
  **DEPENDS ON**: T056 (to ensure data is available)

**Checkpoint**: Resonance and bond-order descriptors are integrated, and their impact on model performance is quantified.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T046 [P] Update `docs/README.md` and `docs/quickstart.md` to include the HOMO-LUMO fallback logic described in T026 and the removal of Phase 6 (custom quantum proxies).
- [X] T047 Run `black --check` and `ruff check` on `code/`; fix all reported errors. Remove any import statements that are not used in the final code. Ensure all functions in `code/` have docstrings. (FR-010)
- [X] T049 [P] Run full pipeline integration test on sample dataset (`data/raw/sample_smiles.csv`), verifying execution time < 6 hours on 2-core CPU. Log success/failure to `state/validation_log.json`. **Logic**:
 1. Record start time.
 2. Execute the full pipeline from T013 to T045 (and T052-T057).
 3. Record end time.
 4. Calculate duration.
 5. If duration > 6 hours, log failure and exit with error.
 6. Log duration and pass/fail status to `state/validation_log.json`. (FR-010)
- [ ] T050 Run a validation script that loads `data/processed/descriptors.csv`, `data/processed/model_results.json`, and `data/processed/analysis_summary.json` and asserts they match the schemas defined in `contracts/model_results_schema.yaml` and `contracts/descriptor_schema.yaml`.
- [X] T051 Execute all commands listed in `docs/quickstart.md` in a fresh virtualenv. Log the exit code and any error output to `state/validation_log.json`. Assert all commands exit with code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Resonance Augmentation (Phase 6)**: Depends on US1 completion (needs descriptors logic) and US3 (needs analysis framework).
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs descriptors)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained models)
- **Resonance Augmentation (Phase 6)**: Depends on US1 (to add descriptors) and US3 (to retrain/analyze).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Resonance Tasks**: T052, T053, T054 can be implemented in parallel as they modify different parts of `descriptors.py`.

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
5. Add Resonance Augmentation (Phase 6) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Descriptors)
 - Developer B: User Story 2 (Model Training & Sensitivity)
 - Developer C: User Story 3 (Analysis & VIF)
 - Developer D (if available): Resonance Augmentation (T052-T054)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Reviewer Feedback Addressed**: Tasks T014a-d implements standard topological descriptors (Degree, Path, Aromaticity, Ring, Conjugation) required by FR-001/FR-008. T032 implements the sensitivity analysis with Kruskal-Wallis test and raw R² recording, explicitly saving to `sensitivity_analysis.json` and versioning intermediate models. T039a-d implements the iterative VIF filtering with reproducibility constraints, metric tracking, and explicit logging to `vif_iteration_log.json` and model hashing. T040, T043, and T045 now explicitly handle artifact saving and feature selection logic.
- **Phase 6 (Resonance Augmentation) Added**: Addresses `linus-pauling-simulated`'s concern about resonance. T014d implements bond order estimation, electronegativity-polarity descriptor, and resonance energy proxy. T056 re-evaluates model performance with these new features.
- **Phase 6 Removal (Custom Quantum)**: The previous Phase 6 (T052-T057 custom quantum) was removed because it attempted to implement custom quantum-chemical proxies (Hückel matrix diagonalization, custom bond order estimation) that violate Constitution Principle VI (Graph Descriptor Transparency) and lack a spec anchor. The project now strictly adheres to RDKit-based descriptors and topological proxies.
- **Target Variable Logic**: T026a-c implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment. It now explicitly requires a Change Request document and spec update.
- **Ordering**: Phase 4 tasks are ordered to ensure T031 (filter) runs before T029 (training) for the initial model, and T032 (sensitivity) correctly re-uses T031. T039 (VIF) explicitly depends on T031 and T027. T026 (Target Validation) now runs AFTER T019 (Write Results) to ensure the schema is validated before writing.
- **Task Dependencies Clarified**:
 - T019 (Write Results) now explicitly depends on T014 (Compute) to ensure data is computed before writing.
 - T026 (Validate) now explicitly depends on T019 (Write) to ensure the file exists before validation.
 - T045 (Analysis Summary) is explicitly marked as independent of T043 (Plotting), allowing parallel execution.
 - T043 (Plotting) dependencies corrected to remove T039 and T045, depending only on T040, T041, T042.
 - Phase 6 (Resonance) added as a revision phase, dependent on US1 and US3.
 - T050 (Validation) updated to check for new resonance columns.
 - T033 is split into T033a (Initialize) and T033b (Finalize) to handle VIF loop results correctly.
 - T017 and T018 are merged into T014d and T013 respectively to avoid redundancy.