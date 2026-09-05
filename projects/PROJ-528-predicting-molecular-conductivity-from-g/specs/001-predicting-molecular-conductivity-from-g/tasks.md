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
- [X] T002 Initialize Python 3.x project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`
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
- [X] T014 [US1] Implement **Graph-Based Descriptor Computation** in `code/descriptors.py` (FR-001, FR-008). Compute the following descriptors for each valid molecule:
  1. **Degree Distribution**: `degree_mean`, `degree_std`, `degree_max`, `degree_min`.
  2. **Path Length**: `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min` (using `rdkit.Chem.rdmolops.GetDistanceMatrix`).
  3. **Aromaticity & Rings**: `aromaticity_index`, `ring_count`, `huckel_aromaticity_count`, `clar_aromaticity_proxy`.
  4. **Conjugation**: `conjugation_length` (longest simple path in conjugated subgraph via DFS), `num_conjugated_bonds`, `conjugation_density`.
  5. **Reviewer Feedback Proxies**: `weighted_path_length`, `electronegativity_polarity`, `resonance_proxy`.
  
  **Logic**:
  - Compute base descriptors first. If any base descriptor fails (NaN), mark molecule as invalid.
  - If base descriptors are valid, compute reviewer feedback proxies.
  - **Runtime Guard**: If total runtime for this function exceeds 5 hours (check `time.time()` vs start), log a warning and skip the calculation of the three reviewer feedback proxies (`weighted_path_length`, `electronegativity_polarity`, `resonance_proxy`), setting them to NaN. Do NOT skip base descriptors.
  - **Quantum Fallback**: If a quantum-derived descriptor (e.g., HOMO-LUMO gap) is missing from the dataset for a molecule, log a warning: "Quantum descriptor missing for {smiles}; falling back to topological proxy." Use the topological conjugation length as the proxy. If both quantum and topological proxies fail for a molecule, exclude the molecule from the output. (FR-014)
  - **Output**: Return a dictionary or DataFrame row with all these columns. **MUST return NaN for any calculation that fails.** (FR-001, FR-008)
  - **Note**: This task is sequential within the pipeline to ensure all descriptors are aggregated before writing to the output file.
  
- [X] T017 [US1] Implement fallback logic for missing quantum descriptors in `code/descriptors.py`. If a quantum-derived descriptor (e.g., HOMO-LUMO gap) is missing from the dataset for a molecule, log a warning: "Quantum descriptor missing for {smiles}; falling back to topological proxy." Use the topological conjugation length as the proxy. If both quantum and topological proxies fail for a molecule, exclude the molecule from the output. (FR-014)
- [X] T018 [US1] Implement error handling for invalid SMILES and missing conductivity in `code/data_loader.py`. If a SMILES string is invalid, log an error: "Invalid SMILES: {smiles}" and exclude the molecule. If the target variable (conductivity) is missing for a molecule, log a warning: "Missing conductivity for {smiles}" and exclude the molecule. (FR-012)
- [X] T019 [US1] Write descriptor computation results to `data/processed/descriptors.csv` with EXACT columns: [smiles, status, degree_mean, degree_std, degree_max, degree_min, path_length_mean, path_length_std, path_length_max, path_length_min, aromaticity_index, huckel_aromaticity_count, clar_aromaticity_proxy, conjugation_length, num_conjugated_bonds, conjugation_density, ring_count, weighted_path_length, electronegativity_polarity, resonance_proxy]. **Logic**: Iterate through computed descriptors. If any row has NaN values in the required descriptor columns, drop the row and log: "Dropped {count} rows due to NaN values in descriptors." (FR-001, FR-008)
  - **DEPENDS ON**: T014, T017, T018

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train regression models and evaluate predictive performance (Priority: P2)

**Goal**: Split data, train RF/GB models, handle outliers via sensitivity analysis, and validate target variable dynamic range.

**Independent Test**: Can be fully tested by running the training pipeline on a fixed dataset and verifying that both models produce R² scores, MAE values, and cross-validation metrics in a structured results file.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Integration test for scaffold split ensuring no structural leakage
- [X] T024 [P] [US2] Unit test for log-transformation of target variable
- [X] T025 [P] [US2] Unit test for outlier exclusion threshold logic

### Implementation for User Story 2

- [X] T026 [US2] Implement target variable validation in `code/data_loader.py`: Check for 'conductivity'. If present and log-range >= 3.0, proceed. If missing, check for 'HOMO_LUMO_gap'. If missing, **HALT** with `sys.exit(1)` and error message: "CRITICAL: No valid target variable found (Conductivity or HOMO-LUMO gap missing)." If HOMO_LUMO exists, **log a CRITICAL warning**: "Conductivity missing; using HOMO-LUMO gap fallback (Scope Change: Electronic Delocalization Potential)." **Update `data/processed/metadata.json`** with keys: `scope_change: true`, `target_variable_used: 'HOMO_LUMO_gap'`, `reason: 'Conductivity missing'`. Reframe the research question in all subsequent outputs to "Electronic Delocalization Potential". (FR-003, Plan Scope Adjustment, FR-011)
  - **DEPENDS ON**: T019 (Data must be loaded and descriptors computed before target validation)
  - **NOTE**: This task MUST run before T028 (log-transformation) and T029 (training) to determine the target column name.
  
- [X] T027 [US2] Implement scaffold-based train/test split (a majority/minority ratio) in `code/scaffold_split.py` AFTER T026 completes (FR-002)
- [X] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO) in `code/model_training.py`. Use natural logarithm (`np.log`) on the target column. Create a new column named `log_{target_var}`. (FR-003)
- [X] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity in `code/analysis.py`. Function signature: `def filter_outliers(df, target_col, sigma_threshold):`. Logic: Calculate z-scores for `target_col`. Filter rows where `abs(z_score) <= sigma_threshold`. Return filtered DataFrame. Ensure it reuses the exact split indices from T027 and seed from T004. (FR-007)
- [X] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target in `code/model_training.py`. RF: `n_estimators=100`, `max_depth=None`, `random_state=SEED`. GB: `n_estimators=100`, `learning_rate=0.1`, `random_state=SEED`. **Note**: Initial training uses data filtered by T031 with default threshold (3.0σ). (FR-003)
- [X] T030 [US2] Implement 5-fold cross-validation and metric recording in `code/model_training.py`. Use `cross_val_score` with `cv=5` and `scoring='r2'`. Record mean and std of R² scores. (FR-004)
- [X] T032 [US2] Implement sensitivity analysis loop in `code/analysis.py`. **Logic**:
  1. Define thresholds: `{2.5, 3.0, 3.5}`.
  2. For each threshold, call T031 to filter data, then retrain models (using T029 logic) and record R².
  3. Perform a **Kruskal-Wallis test** on the R² scores across the 3 thresholds.
  4. Save results to `data/processed/sensitivity_analysis.json` with keys: `thresholds`, `r2_scores` (list of raw scores), `kruskal_statistic`, `p_value`, `range`, `population_variance`. (FR-007)
  - **DEPENDS ON**: T029, T031
- [X] T033 [US2] Save model results and sensitivity analysis data to `data/processed/model_results.json` with keys: `rf_r2`, `gb_r2`, `cv_scores`, `sensitivity_analysis: {thresholds, r2_scores, kruskal_statistic, p_value}`. (FR-003, FR-004, FR-007)
  - **DEPENDS ON**: T032, T030

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate feature importance analysis and correlation plots (Priority: P3)

**Goal**: Analyze feature importance, apply VIF filtering, correct for multiple comparisons, and generate visualizations.

**Independent Test**: Can be fully tested by running the analysis script on a trained model and verifying that feature importance rankings are exported and correlation plots are generated as image files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Unit test for VIF calculation and thresholding
- [X] T035 [P] [US3] Unit test for Benjamini-Hochberg correction implementation
- [X] T036 [P] [US3] Unit test for correlation plot generation with confidence intervals

### Implementation for User Story 3

- [X] T037 [US3] Implement VIF calculation function in `code/analysis.py`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor`. Input: feature matrix (numpy array). Output: dictionary mapping feature names to VIF scores. **This function MUST be callable iteratively.** (FR-013)
- [X] T038 [US3] Implement feature exclusion logic for features with VIF > 10 in `code/analysis.py`. If any feature has VIF > 10, mark it for exclusion. (FR-013)
- [X] T039 [US3] Implement iterative VIF loop in `code/analysis.py`. **Prerequisites**: Must run on data filtered by T031 (outliers) and use split indices from T027.
  1. WHILE any VIF > 10:
     - Exclude the feature with the HIGHEST VIF.
     - Recalculate VIF on the reduced feature set (T037).
     - Retrain the model using the EXACT split indices and seed.
     - Record `iteration`, `excluded_feature`, `vif_scores`, `r2`, `mae`.
  2. Guard Clause: If feature set becomes empty, log critical error and halt.
  3. Save `vif_iteration_log.json` (keys: `iterations: [{iteration, excluded_feature, vif_scores, r2, mae}]`).
  4. **Re-evaluate final model** on the test set and update `model_results.json` (T033) with the final R²/MAE. (FR-013)
  - **DEPENDS ON**: T031, T027, T029
- [X] T040 [US3] Compute feature importance rankings on the final VIF-filtered model in `code/analysis.py`. Use `sklearn.inspection.permutation_importance` with `n_repeats=10` and `random_state=SEED`. **Save the ranked list to `data/processed/feature_importance.csv`**. Output format: a ranked list of (feature, importance_score). (FR-005)
  - **DEPENDS ON**: T039
- [X] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values in `code/analysis.py`. Use `scipy.stats.pearsonr`. Output format: a dictionary mapping feature names to (correlation_coefficient, p_value). (FR-005)
- [X] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values in `code/analysis.py`. Use `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output format: a dictionary mapping feature names to adjusted p-values. (FR-006)
- [X] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`. **Logic**: Select **top features by permutation importance score (descending)**, with ties broken by alphabetical feature name. **Keys**: `top_5_features`, `adjusted_p_values`, `fdr_method`. (FR-005)
  - **DEPENDS ON**: T040 (Feature importance ranking)
  - **NOTE**: T045 is independent of T043 (Plotting) and can run in parallel.
- [X] T043 [US3] Generate scatter plots with regression lines and confidence intervals for **top 5 features** (identified in T040) in `code/plotting.py`. Use `seaborn.regplot` with `ci=95`. **Save plots as PNG files to `data/processed/corr_plot_top5.png`**. (FR-005)
  - **DEPENDS ON**: T040, T041, T042

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T046 [P] Documentation updates in `docs/` including reviewer feedback
- [X] T047 Code cleanup and refactoring. Criteria: remove unused imports, fix linting errors (black, ruff), and ensure all functions have docstrings. (FR-010)
- [X] T049 [P] Run full pipeline integration test on sample dataset (`data/raw/sample_smiles.csv`), verifying execution time < 6 hours on 2-core CPU. Log success/failure to `state/validation_log.json`. **Logic**:
  1. Record start time.
  2. Execute the full pipeline from T013 to T045.
  3. Record end time.
  4. Calculate duration.
  5. If duration > 6 hours, log failure and exit with error.
  6. Log duration and pass/fail status to `state/validation_log.json`. (FR-010)
- [X] T050 Verify all artifacts match `contracts/` schemas
- [X] T051 Run quickstart.md validation by executing all commands in `docs/quickstart.md` and logging success/failure to `state/validation_log.json`

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
- **User Story 2 (P2)**: Depends on US1 completion (needs descriptors)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained models)

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
 - Developer A: User Story 1 (Descriptors)
 - Developer B: User Story 2 (Model Training & Sensitivity)
 - Developer C: User Story 3 (Analysis & VIF)
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
- **Reviewer Feedback Addressed**: Tasks T014 implements standard topological descriptors (Degree, Path, Aromaticity, Ring, Conjugation) required by FR-001/FR-008. T014 includes runtime guards for reviewer feedback proxies to ensure FR-010 is met. T032 implements the sensitivity analysis with Kruskal-Wallis test and raw R² recording, explicitly saving to `sensitivity_analysis.json`. T039 implements the iterative VIF filtering with reproducibility constraints, metric tracking, and explicit logging to `vif_iteration_log.json`. T040, T043, and T045 now explicitly handle artifact saving and feature selection logic.
- **Target Variable Logic**: T026 implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment and reframing the research question.
- **Ordering**: Phase 4 tasks are ordered to ensure T031 (filter) runs before T029 (training) for the initial model, and T032 (sensitivity) correctly re-uses T031. T039 (VIF) explicitly depends on T031 and T027.
- **Task Dependencies Clarified**: 
  - T019 (Write Results) now explicitly depends on T014 to ensure data consistency.
  - T026 (Target Validation) explicitly depends on T019 to ensure data is loaded.
  - T045 (Analysis Summary) is explicitly marked as independent of T043 (Plotting), allowing parallel execution.
  - T043 (Plotting) dependencies corrected to remove T039 and T045, depending only on T040, T041, T042.