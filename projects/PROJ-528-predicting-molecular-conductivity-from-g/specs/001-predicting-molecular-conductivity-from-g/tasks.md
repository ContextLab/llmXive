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
- [X] T002 Initialize Python 3.x project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `networkx`, `statsmodels`
- [X] T003 [P] Configure linting and formatting tools by creating `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']) sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration module (`code/config.py`) defining constants: `DATA_PATH`, `SEED`, `OUTLIER_SIGMA`, `VIF_THRESHOLD`, `TARGET_VAR` (default: 'conductivity'), `RAW_DATA_PATH` (default: 'data/raw/smiles.csv')
- [X] T005 [P] Implement data validation utilities in `code/validators.py` with functions `validate_smiles(smiles_str)` and `check_target_range(values, min_log_range=3.0)`
- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` that configures a rotating file handler to `logs/pipeline.log` with JSON formatting
- [X] T007 Create `code/models.py` with Pydantic classes `Molecule` (fields: smiles, descriptors, target) and `Descriptor` (fields: name, value)
- [X] T008 [P] Implement scaffold splitting utility in `code/scaffold_split.py` using `rdkit.Chem.Scaffolds.MurckoScaffold` to ensure structural diversity and prevent data leakage (FR-002)
- [X] T009 Create `contracts/model_results_schema.yaml` and `contracts/descriptor_schema.yaml`.
 - `model_results_schema.yaml`: fields `r2`, `mae`, `cv_scores`, `sensitivity_data`, `vif_scores`, `quantum_proxy_metadata`.
 - `descriptor_schema.yaml`: fields `smiles`, `status`, `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`, `aromaticity_index`, `ring_count`, `conjugation_length`, `num_conjugated_bonds`, `conjugation_density`, `aromatic_ring_count`, `conjugated_ring_count`, `huckel_resonance_energy`, `estimated_bond_order`, `estimated_bond_length`, `electronegativity_diff_weighted`. (FR-001, FR-008, Reviewer-001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load molecular structures and compute graph-based descriptors (Priority: P1) 🎯 MVP

**Goal**: Parse SMILES, compute standard topological descriptors, implement quantum-inspired proxies, and address resonance-related structural features as per reviewer feedback.

**Independent Test**: Can be fully tested by running the descriptor computation pipeline on a sample of SMILES strings and verifying that the output table contains all required descriptor columns with valid numeric values for each molecule.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write unit test code (expected to fail) before implementation

- [X] T010 [P] [US1] Write unit test code for aromaticity index calculation on benzene (SMILES: "c1ccccc1") in `tests/test_descriptors.py`. Function name: `test_aromaticity_benzene`. Assert that `aromaticity_index` equals a non-zero value defined by the implementation.
- [X] T011 [P] [US1] Write unit test code for conjugation path length on butadiene vs. butane in `tests/test_descriptors.py`. Function name: `test_conjugation_path_length`. Use SMILES "C=CC=C" (butadiene) and "CCCC" (butane). Assert that butadiene's `conjugation_length` is greater than butane's.
- [X] T012 [P] [US1] Write unit test code for descriptor computation on mixed hybridization molecules in `tests/test_descriptors.py`. Function name: `test_mixed_hybridization_descriptors`. Use a molecule with both sp2 and sp3 carbons (e.g., "CC=C"). Assert that all computed descriptors are finite numbers and no NaN values are present.
- [X] T012b [P] [US1] Write unit test code for Hückel resonance energy calculation on benzene vs. cyclohexane in `tests/test_descriptors.py`. Function name: `test_huckel_resonance_benzene`. Assert that benzene's `huckel_resonance_energy` is significantly positive while cyclohexane's is near zero.
 - **DEPENDS ON**: T014e

### Implementation for User Story 1

- [X] T013 [US1] Implement `load_smiles(path: str) -> pd.DataFrame` in `code/data_loader.py` returning DataFrame with columns [smiles, valid, error_msg]
- [X] T026 [US1] **Target Variable Validation**: Implement `validate_target_variable(path: str)` in `code/data_loader.py`.
 - **Logic**:
 1. Load raw data directly from `config.RAW_DATA_PATH`.
 2. Check for 'conductivity' or 'charge_carrier_mobility' column.
 3. If found: Verify dynamic range (>= 3 orders of magnitude). If valid, proceed.
 4. If NOT found: Check for 'HOMO_LUMO_gap'. If found: Log "CRITICAL WARNING: Conductivity missing. Using HOMO-LUMO gap as proxy for Electronic Delocalization Potential." Proceed with HOMO-LUMO as target.
 5. If NEITHER found: `sys.exit(1)` with error "CRITICAL: No valid target variable found (Conductivity or HOMO-LUMO gap missing)."
 - **DEPENDS ON**: T013 (ensures raw data is loaded and validated)
 - **NOTE**: This task validates the raw input file. It does not produce the data T019 needs; T019 will also load the raw file independently.

- [X] T014a [US1] Implement **Base Graph Descriptors** in `code/descriptors.py` (FR-001). Compute: `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`.
- [X] T014b [US1] Implement **Aromaticity & Ring Descriptors** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromaticity_index`, `ring_count`.
- [X] T014c [US1] Implement **Conjugation Descriptors** in `code/descriptors.py` (FR-001). Compute: `conjugation_length` (longest simple path in conjugated subgraph), `num_conjugated_bonds`, `conjugation_density`.
- [X] T014d [US1] Implement **Resonance Proxies (RDKit Only)** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromatic_ring_count`, `conjugated_ring_count`.
 - **Logic**:
 1. Parse SMILES to RDKit molecule object.
 2. Use `rdkit.Chem.Lipinski` and `rdkit.Chem.rdMolDescriptors` to compute aromatic ring counts and conjugation metrics.
 3. **Note**: All descriptors MUST be computed using RDKit. If a calculation fails for a specific molecule, log a warning and set the value to NaN for that molecule only. Do not halt the entire pipeline. (FR-001, FR-008)
 4. **Runtime Monitoring**: Log a warning if descriptor computation for a single molecule exceeds a predefined time threshold., but continue processing. Do NOT exit. (FR-010)

- [X] T014e [US1] Implement **Hückel Resonance Energy Estimation** in `code/descriptors.py` (Reviewer-001, FR-008).
 - **Logic**:
 1. Identify aromatic rings and conjugated systems using RDKit.
 2. **Algorithm**: Construct the adjacency matrix A for the subgraph induced by conjugated bonds (double, aromatic). Compute eigenvalues of A. The Hückel energy proxy is the sum of the eigenvalues (or the sum of occupied orbital energies approximated by the negative of the eigenvalues).
 3. Calculate a `huckel_resonance_energy` score (in arbitrary units or scaled kcal/mol equivalent) for the molecule.
 4. **Constraint**: Must be computable entirely on CPU without DFT libraries. If the molecule lacks a clear conjugated system, return 0.0.
 5. **Fallback**: If the matrix construction or eigenvalue calculation fails (e.g., singular matrix, no conjugated bonds), log a warning "Hückel calculation failed, defaulting to 0.0" and return 0.0. This ensures the pipeline does not block (FR-014).
 6. **Validation**: Ensure the score is non-negative and correlates with known aromatic systems (e.g., benzene > cyclohexane).

- [X] T014f [US1] Implement **Bond Order & Length Annotation** in `code/descriptors.py` (Reviewer-001, FR-008).
 - **Logic**:
 1. Iterate over all bonds in the molecular graph.
 2. **Mapping**:
    - Single bond: order = 1.0, length = 1.54 Å
    - Double bond: order = 2.0, length = 1.34 Å
    - Aromatic bond: order = 1.5, length = 1.39 Å
 3. **Aggregation**: Compute `estimated_bond_order` as the **weighted average** of bond orders across all bonds in the molecule (weighted by bond length). Compute `estimated_bond_length` as the **weighted average** of bond lengths across all bonds.
 4. **Output**: Add these as scalar descriptors to the molecule record.

- [X] T014g [US1] Implement **Electronegativity-Weighted Polarity** in `code/descriptors.py` (Reviewer-001, FR-008).
 - **Logic**:
 1. Map atoms to Pauling electronegativity values (e.g., C=2.55, N=3.04, O=3.44, H=2.20).
 2. For each bond, calculate `delta_en = abs(en_atom1 - en_atom2)`.
 3. Calculate a polarity term: `polarity_term = delta_en * bond_length` (using the estimated bond length from T014f).
 4. **Aggregation**: Compute the molecule-level descriptor `electronegativity_diff_weighted` as the **SUM** of polarity terms across all bonds.
 5. **Output**: Add this scalar descriptor to the molecule record.

- [X] T019 [US1] **Write Descriptors**: Compute all descriptors (T014a-g) and write results to `data/processed/descriptors.csv`.
 - **Logic**:
 1. Load raw SMILES data directly from `config.RAW_DATA_PATH`.
 2. Compute base descriptors (T014a), aromaticity descriptors (T014b), conjugation descriptors (T014c), resonance descriptors (T014d), Hückel energy (T014e), bond metrics (T014f), and polarity (T014g) for each valid molecule.
 3. Merge all descriptor columns into a single DataFrame by calling the specific functions from `code/descriptors.py` and concatenating the resulting columns.
 4. **Required Columns**: `smiles`, `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`, `aromaticity_index`, `ring_count`, `conjugation_length`, `num_conjugated_bonds`, `conjugation_density`, `aromatic_ring_count`, `conjugated_ring_count`, `huckel_resonance_energy`, `estimated_bond_order`, `estimated_bond_length`, `electronegativity_diff_weighted`, `target`.
 5. **NaN Handling**: Drop any row where ANY of the required columns is NaN. Log: "Dropped {count} rows due to NaN values in required descriptors." (FR-001, FR-008, FR-012)
 6. Write the final DataFrame to `data/processed/descriptors.csv`.
 7. Ensure the output schema matches `contracts/descriptor_schema.yaml`.
 8. **Execution**: Run `code/descriptors.py --output data/processed/descriptors.csv`.
 - **DEPENDS ON**: T013, T014a, T014b, T014c, T014d, T014e, T014f, T014g

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

- [X] T027 [US2] Implement scaffold-based train/test split (a majority/minority ratio) in `code/scaffold_split.py` AFTER T026 completes (FR-002)
- [X] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO) in `code/model_training.py`. Use natural logarithm (`np.log`) on the target column. Create a new column named `log_{target_var}`. (FR-003)
- [X] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity in `code/analysis.py`. Function signature: `def filter_outliers(df, target_col, sigma_threshold):`. Logic: Calculate z-scores for `target_col`. Filter rows where `abs(z_score) <= sigma_threshold`. Return filtered DataFrame. Ensure it reuses the exact split indices from T027 and seed from T004. (FR-007)
- [X] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target in `code/model_training.py`. RF: `n_estimators=100`, `max_depth=None`, `random_state=SEED`. GB: `n_estimators=100`, `learning_rate=0.1`, `random_state=SEED`. **Note**: Initial training uses data filtered by T031 with default threshold (3.0σ). (FR-003)
- [X] T030 [US2] Implement 5-fold cross-validation and metric recording in `code/model_training.py`. Use `cross_val_score` with `cv=5` and `scoring='r2'`. Record mean and std of R² scores. (FR-004)
- [X] T032 [US2] Implement sensitivity analysis loop in `code/analysis.py`. **Logic**:
 1. Define thresholds: `{, 3.0, 3.5}`.
 2. For each threshold, call T031 to filter data, then retrain models (using T029 logic) and record R².
 3. Calculate variance of R² scores across the 3 thresholds.
 4. Save results to `data/processed/sensitivity_analysis.json` with keys: `thresholds`, `r2_scores` (list of raw scores), `r2_variance`, `range`, `population_variance`.
 5. **Artifact Versioning**: Save the intermediate model objects for each threshold to `data/processed/models_intermediate/model_{threshold}.pkl` and record their content hashes in `data/processed/model_hashes.json` to satisfy Constitution Principle IV (Single Source of Truth). (FR-007)
 - **DEPENDS ON**: T029, T031

- [X] T033a [US2] **Initialize**: Create `data/processed/model_results.json` with empty/default structure if no VIF loop or sensitivity analysis has run yet. Keys: `rf_r2: 0.0`, `gb_r2: 0.0`, `cv_scores: []`, `sensitivity_analysis: {}`, `vif_scores: []`. (FR-003, FR-004, FR-007)
 - **DEPENDS ON**: None (Metadata setup task)

- [X] T033b [US2] **Finalize**: Update `data/processed/model_results.json` with final R²/MAE from T039c (VIF loop) and T032 (Sensitivity). (FR-003, FR-004, FR-007)
 - **DEPENDS ON**: T039c, T032, T033a

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

- [X] T039a [US3] Implement VIF calculation function in `code/analysis.py`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor`. Input: feature matrix (numpy array). Output: dictionary mapping feature names to VIF scores. **This function MUST be callable iteratively.** (FR-013)
- [X] T039b [US3] Implement feature exclusion logic for features with VIF > 10 in `code/analysis.py`. If any feature has VIF > 10, mark it for exclusion. (FR-013)
- [X] T039c [US3] **Unified VIF Loop & Finalize**: Implement the iterative VIF loop in `code/analysis.py` and perform final artifact updates. **Prerequisites**: Must run on data filtered by T031 (outliers) and use split indices from T027.
 1. Load `data/processed/descriptors.csv` (which includes ALL descriptors: base, aromaticity, conjugation, resonance, Hückel, bond metrics, polarity).
 2. WHILE any VIF > 10:
 - Exclude the feature with the HIGHEST VIF.
 - Recalculate VIF on the reduced feature set (T039a).
 - Retrain the model using the EXACT split indices and seed.
 - Record `iteration`, `excluded_feature`, `vif_scores`, `r2`, `mae`.
 - **Artifact Versioning**: Save the intermediate model for this iteration to `data/processed/models_intermediate/vif_iter_{iteration}.pkl` and record its content hash in `data/processed/model_hashes.json`.
 3. Guard Clause: If feature set becomes empty, log critical error and halt.
 4. Save `vif_iteration_log.json` (keys: `iterations: [{iteration, excluded_feature, vif_scores, r2, mae}]`).
 5. **Finalize**: Update `data/processed/model_results.json` with the final R²/MAE from the last iteration of the VIF loop. Ensure the schema matches `contracts/model_results_schema.yaml`. (FR-013)
 - **DEPENDS ON**: T031, T027, T029, T039a, T039b, T019

- [X] T040 [US3] Compute feature importance rankings on the final VIF-filtered model in `code/analysis.py`. Use `sklearn.inspection.permutation_importance` with `n_repeats=10` and `random_state=SEED`. **Save the ranked list to `data/processed/feature_importance.csv`**. Output format: a ranked list of (feature, importance_score).
 - **Logic**:
 1. Load the final VIF-filtered model (from T039c).
 2. Load the test set features and target.
 3. Compute permutation importance using `sklearn.inspection.permutation_importance`.
 4. **Sort**: Rank features by importance score in **DESCENDING** order. **Tie-breaking**: If scores are equal, sort by feature name **ALPHABETICALLY** (A-Z).
 5. Save the ranked list to `data/processed/feature_importance.csv`.
 6. **Execution**: Run `code/analysis.py --mode importance --output data/processed/feature_importance.csv`.
 - **DEPENDS ON**: T039c

- [X] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values in `code/analysis.py`. Use `scipy.stats.pearsonr`. Output format: a dictionary mapping feature names to (correlation_coefficient, p_value). (FR-005)
 - **DEPENDS ON**: T039c, T040

- [X] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values in `code/analysis.py`. Use `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output format: a dictionary mapping feature names to adjusted p-values. (FR-006)
 - **DEPENDS ON**: T039c, T041

- [X] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`. **Logic**: Select **top features by permutation importance score (descending)**, with ties broken by alphabetical feature name. **Keys**: `top_5_features`, `adjusted_p_values`, `fdr_method`, `resonance_feature_rankings`. (FR-005)
 - **Logic**:
 1. Load `feature_importance.csv` (from T040).
 2. Load adjusted p-values (from T042).
 3. Select top features by importance score.
 4. Specifically extract and rank the resonance-related features (Hückel energy, bond order, polarity) to verify Reviewer-001's hypothesis.
 5. **Fallback**: If resonance features are missing or have zero importance, `resonance_feature_rankings` is an empty list `[]`.
 6. Save the summary to `data/processed/analysis_summary.json`.
 7. **Execution**: Run `code/analysis.py --mode summary --output data/processed/analysis_summary.json`.
 - **DEPENDS ON**: T040, T042, T039c
 - **NOTE**: T045 is independent of T043 (Plotting) and can run in parallel.
- [X] T043 [US3] Generate scatter plots with regression lines and confidence intervals for **top 5 features** (identified in T040) in `code/plotting.py`. Use `seaborn.regplot` with `ci=95`. **Save plots as PNG files to `data/processed/corr_plot_top5.png`**. (FR-005)
 - **Logic**:
 1. Load `feature_importance.csv` (from T040) to get top 5 features.
 2. Load the data with target variable.
 3. Generate scatter plots with regression lines and confidence intervals for each top feature.
 4. Save plots as PNG files to `data/processed/corr_plot_top5.png`.
 5. **Execution**: Run `code/plotting.py --mode correlation --output data/processed/corr_plot_top5.png`.
 - **DEPENDS ON**: T040, T041, T042

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T046 [P] Update `docs/README.md` and `docs/quickstart.md` to include the HOMO-LUMO fallback logic described in T026.
- [X] T047 Run `black --check` and `ruff check` on `code/`; fix all reported errors. Remove any import statements that are not used in the final code. Ensure all functions in `code/` have docstrings. (FR-010)
- [X] T049 [P] Run full pipeline integration test on sample dataset (`data/raw/sample_smiles.csv`), verifying execution time < 6 hours on 2-core CPU. Log success/failure to `state/validation_log.json`. **Logic**:
 1. Record start time.
 2. Execute the full pipeline from T013 to T045 (US1-US3 only).
 3. Record end time.
 4. Calculate duration.
 5. If duration > 6 hours, log failure and exit with error.
 6. Log duration and pass/fail status to `state/validation_log.json`. (FR-010)
- [X] T050a [P] **Schema Validation**: Run a validation script that loads `contracts/descriptor_schema.yaml` and `contracts/model_results_schema.yaml` and asserts they are valid YAML and contain the required fields. Log success/failure to `state/validation_log.json`.
 - **Logic**:
 1. Extend `code/validators.py` to include a `validate_schema(schema_path)` function.
 2. Run `validate_schema('contracts/descriptor_schema.yaml')`.
 3. Run `validate_schema('contracts/model_results_schema.yaml')`.
 4. Log success/failure to `state/validation_log.json`.
 5. **Execution**: Run `code/validators.py --validate-schemas`.
 - **DEPENDS ON**: T009
- [X] T050b [P] **Artifact Validation**: Run a validation script that loads `data/processed/descriptors.csv`, `data/processed/model_results.json`, and `data/processed/analysis_summary.json` and asserts they match the schemas defined in `contracts/descriptor_schema.yaml` and `contracts/model_results_schema.yaml`.
 - **Logic**:
 1. Extend `code/validators.py` to include a `validate_file(file_path, schema_path)` function.
 2. Run `validate_file('data/processed/descriptors.csv', 'contracts/descriptor_schema.yaml')`.
 3. Run `validate_file('data/processed/model_results.json', 'contracts/model_results_schema.yaml')`.
 4. Run `validate_file('data/processed/analysis_summary.json', 'contracts/model_results_schema.yaml')`.
 5. Log success/failure to `state/validation_log.json`.
 6. **Execution**: Run `code/validators.py --validate-all`.
 - **DEPENDS ON**: T005, T019, T039c, T045
- [X] T051 Execute all commands listed in `docs/quickstart.md` in a fresh virtualenv. Log the exit code and any error output to `state/validation_log.json`. Assert all commands exit successfully.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

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
- **Unified VIF Loop**: T039c now runs a single VIF loop on the full descriptor set (including resonance features from T014d-e-g) to satisfy FR-013 and Reviewer-001. No separate Phase 6 re-training exists.
- **Target Variable Logic**: T026 implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment. It now explicitly logs a warning and proceeds, but HALTS if neither is found.
- **Ordering**: Phase 4 tasks are ordered to ensure T031 (filter) runs before T029 (training) for the initial model, and T032 (sensitivity) correctly re-uses T031. T039 (VIF) explicitly depends on T031 and T027. T026 (Target Validation) now loads raw data directly and depends on T013.
- **Task Dependencies Clarified**:
 - T019 (Write Descriptors) is now in Phase 3 and depends on T013 and T014.
 - T026 (Validate) now loads raw data directly and depends on T013.
 - T045 (Analysis Summary) is explicitly marked as independent of T043 (Plotting), allowing parallel execution.
 - T043 (Plotting) dependencies corrected to remove T039 and T045, depending only on T040, T041, T042.
 - Phase 6 (Resonance Augmentation) removed as a separate phase; resonance descriptors are computed in T014d-e-g and included in the unified VIF loop (T039c).
 - T057 removed. T043 handles all top-feature plotting.
 - T039d removed. T039c now handles finalization.
 - T033b now depends on T039c.
 - T050 updated to check for resonance columns and specify the validation command.
 - T009 schema updated to remove non-RDKit fields (`clar_aromaticity_proxy`, `huckel_aromaticity_count`) and add new resonance/bond descriptors.
- **Reviewer-001 Response**: Tasks T014e (Hückel Energy), T014f (Bond Order/Length), and T014g (Electronegativity Polarity) directly address the request to augment graph descriptors with quantum-chemical parameters and resonance-related features. These are computed via RDKit-based proxies to remain CPU-tractable.
- **Hückel Fallback**: T014e includes explicit fallback to 0.0 if the calculation fails, ensuring the pipeline does not block.
- **NaN Handling**: T019 explicitly defines required columns and drops rows with NaN in any of them.
- **Schema Validation**: T050 split into T050a (executable now) and T050b (depends on artifacts).
- **Algorithm Definitions**: T014e (Hückel: adjacency matrix eigenvalues), T014f (Bond: weighted average), T014g (Polarity: SUM) are now explicitly defined to ensure executability.
- **Circular Dependency Broken**: T050a validates schemas independently; T050b validates data after artifacts are produced.
- **Task Status**: All tasks T014e-g, T019, T033a, T039c, T043, T045, T050a, T050b are now marked as complete [X] with executable logic.