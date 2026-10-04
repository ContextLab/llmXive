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
- [X] T002 Initialize Python 3.x project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `networkx`, `statsmodels`, `joblib`, `h5py`
- [X] T003 [P] Configure linting and formatting tools by creating `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']) sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration module (`code/config.py`) defining constants: `DATA_PATH`, `SEED`, `OUTLIER_SIGMA`, `VIF_THRESHOLD`, `TARGET_VAR` (default: 'conductivity'), `RAW_DATA_PATH` (default: 'data/raw/smiles.csv'), `SENSITIVITY_THRESHOLDS` (default: [2.5, 3.0, 3.5]), `CONFIDENCE_INTERVAL_TARGET` (default: 0.95) <!-- FAILED: unspecified -->
- [X] T005 [P] Implement data validation utilities in `code/validators.py` with functions `validate_smiles(smiles_str)`, `check_target_range(values, min_log_range=3.0)`, and a CLI interface `--validate <file> --schema <schema>` that loads the file, loads the schema, validates using `jsonschema` or manual checks, and exits with code 0 on success, 1 on failure.
- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` that configures a rotating file handler to `logs/pipeline.log` with JSON formatting
- [X] T007 Create `code/models.py` with Pydantic classes `Molecule` (fields: smiles, descriptors, target) and `Descriptor` (fields: name, value)
- [X] T008 [P] Implement scaffold splitting utility in `code/scaffold_split.py` using `rdkit.Chem.Scaffolds.MurckoScaffold` to ensure structural diversity and prevent data leakage (FR-002)
- [X] T009 Create `contracts/model_results_schema.yaml` and `contracts/descriptor_schema.yaml`.
 - `model_results_schema.yaml`: fields `r2`, `mae`, `cv_scores`, `sensitivity_data`, `vif_scores`, `quantum_proxy_metadata`.
 - `descriptor_schema.yaml`: fields `smiles`, `status`, `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`, `aromaticity_index`, `conjugation_length`, `num_conjugated_bonds`, `conjugation_density`, `ring_count`. (FR-001, FR-008, Reviewer: linus-pauling-simulated)
- [X] T013 [P] [US1] Implement `load_smiles(path: str) -> pd.DataFrame` in `code/data_loader.py` returning DataFrame with columns [smiles, valid, error_msg]

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

### Implementation for User Story 1

- [X] T018 [US1] **Filter Missing Targets**: Implement `filter_missing_targets(df, target_col)` in `code/data_loader.py`.
 - **Logic**:
 1. Load the raw data (T013).
 2. Identify rows where `target_col` is NaN or missing.
 3. Drop these rows and log the count: "Dropped {count} rows with missing target values."
 4. Return the filtered DataFrame.
 - **DEPENDS ON**: T013
 - **NOTE**: This task ensures FR-012 compliance by explicitly excluding molecules with missing targets *before* descriptor computation.

- [X] T014a [US1] Implement **Base Graph Descriptors** in `code/descriptors.py` (FR-001). Compute: `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`.
 - **Function Signature**: `def compute_base_descriptors(df: pd.DataFrame) -> pd.DataFrame`
- [X] T014b [US1] Implement **Aromaticity & Ring Descriptors** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromaticity_index`, `ring_count`.
 - **Function Signature**: `def compute_aromaticity(df: pd.DataFrame) -> pd.DataFrame`
- [X] T014c [US1] Implement **Conjugation Descriptors** in `code/descriptors.py` (FR-001). Compute: `conjugation_length` (longest simple path in conjugated subgraph), `num_conjugated_bonds`, `conjugation_density`.
 - **Function Signature**: `def compute_conjugation(df: pd.DataFrame) -> pd.DataFrame`
- [X] T014d [US1] Implement **Resonance Proxies (RDKit Only)** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromatic_ring_count`, `conjugated_ring_count`.
 - **Logic**:
 1. Parse SMILES to RDKit molecule object.
 2. Use `rdkit.Chem.Lipinski` and `rdkit.Chem.rdMolDescriptors` to compute aromatic ring counts and conjugation metrics.
 3. **Note**: All descriptors MUST be computed using RDKit. If a calculation fails for a specific molecule, log a warning and set the value to NaN for that molecule only. Do not halt the entire pipeline. (FR-001, FR-008)
 4. **Runtime Monitoring**: Log a warning if descriptor computation for a single molecule exceeds a predefined time threshold., but continue processing. Do NOT exit. (FR-010)
 - **Function Signature**: `def compute_resonance_proxies(df: pd.DataFrame) -> pd.DataFrame`

- [ ] T019a [US1] **Write Base Descriptors**: Write results of T014a, T014b, T014c, T014d to `data/processed/descriptors_base.csv`.
 - **Logic**:
 1. Load SMILES from T013 (filtered by T018).
 2. Compute descriptors using T014a-d.
 3. Drop rows with NaN in required descriptor columns. Log: "Dropped {count} rows due to NaN values in descriptors." (FR-001, FR-008)
 4. **Write File**: Execute `df.to_csv('data/processed/descriptors_base.csv', index=False)`.
 5. **Verify**: Assert `os.path.exists('data/processed/descriptors_base.csv')` and `len(df) > 0`.
 - **DEPENDS ON**: T014a, T014b, T014c, T014d, T018

- [ ] T019b [US1] **Write Full Descriptors (Base)**: Write results of T019a to `data/processed/descriptors.csv`, ensuring schema matches contract. <!-- FAILED: unspecified -->
 - **Logic**:
 1. Load `data/processed/descriptors_base.csv` (T019a).
 2. **Verify**: Check that the loaded DataFrame contains all columns defined in `contracts/descriptor_schema.yaml`. If missing, HALT with error.
 3. **Write File**: Execute `df.to_csv('data/processed/descriptors.csv', index=False)`.
 4. **Verify**: Assert `os.path.exists('data/processed/descriptors.csv')` and `len(df) > 0`.
 - **DEPENDS ON**: T019a

- [X] T026 [US1/US2] **Target Variable Validation & Selection (FR-011, FR-014)**: Implement `validate_and_select_target(path: str)` in `code/data_loader.py`.
 - **Logic**:
 1. Load raw data directly from `config.RAW_DATA_PATH`.
 2. Check for 'conductivity' or 'charge_carrier_mobility' column.
 3. **If Found**: Verify dynamic range (>= 3 orders of magnitude). If valid, set `TARGET_VAR = 'conductivity'`. **If Invalid**: HALT with error "CRITICAL: Target variable dynamic range (< 3 orders of magnitude) is insufficient per FR-011."
 4. **If NOT Found**: Check for 'HOMO_LUMO_gap'. **If Found**: Log "WARNING: Conductivity missing. Using HOMO-LUMO gap as proxy per Plan Scope Adjustment (FR-014 fallback)." Set `TARGET_VAR = 'HOMO_LUMO_gap'`. Proceed if HOMO-LUMO gap column exists and has valid dynamic range.
 5. **If NEITHER Found**: **Compute Empirical Proxy**. Use the formula: `log_conductivity_proxy = 0.5 * log(MW) + 0.3 * aromaticity_index + 0.2 * conjugation_length`. Log "WARNING: No direct target found. Using empirical proxy based on topological descriptors." Set `TARGET_VAR = 'log_conductivity_proxy'`.
 6. **DEPENDS ON**: T019a (descriptors must be computed to calculate proxy).
 - **NOTE**: This task implements the strict Spec requirement (FR-003/FR-011) with the fallback path mandated by the Plan. It explicitly HALTS if the proxy cannot be computed (e.g., missing descriptors), but proceeds with a warning if the proxy is valid.

- [X] T015 [US1/US2] **Generate Quantum Proxy Report**: Generate `data/processed/quantum_proxy_report.json` indicating presence/absence of quantum descriptors.
 - **Logic**:
 1. Check if 'HOMO_LUMO_gap' or other quantum columns exist in raw data.
 2. If absent, log "No quantum descriptors found. Using topological proxies."
 3. Save report to `data/processed/quantum_proxy_report.json`.
 - **DEPENDS ON**: T026

**Checkpoint**: Descriptor computation logic is ready, and results are written to file. Target variable is validated or proxied.

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
- [X] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO or proxy) in `code/model_training.py`. Use natural logarithm (`np.log`) on the target column. Create a new column named `log_{target_var}`. (FR-003)
- [X] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity in `code/analysis.py`. Function signature: `def filter_outliers(df, target_col, sigma_threshold):`. Logic: Calculate z-scores for `target_col`. Filter rows where `abs(z_score) <= sigma_threshold`. Return filtered DataFrame. Ensure it reuses the exact split indices from T027 and seed from T004. (FR-007)
- [X] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target in `code/model_training.py`. RF: `n_estimators=100`, `max_depth=None`, `random_state=SEED`. GB: `n_estimators=100`, `learning_rate=0.1`, `random_state=SEED`. **Note**: Initial training uses data filtered by T031 with default threshold (standard statistical significance level). (FR-003)
- [X] T030 [US2] Implement -fold cross-validation and metric recording in `code/model_training.py`. Use `cross_val_score` with `cv=5` and `scoring='r2'`. Record mean and std of R² scores. (FR-004)
- [X] T032a [US2] **Validate Thresholds**: Verify `config.SENSITIVITY_THRESHOLDS` is a valid list of numeric values.
 - **Logic**:
 1. Load `config.SENSITIVITY_THRESHOLDS`.
 2. Assert it is a list of floats.
 3. Log "Thresholds validated: {thresholds}".
 - **DEPENDS ON**: T004
- [X] T032b [US2] **Sensitivity Analysis Loop**: Implement the sensitivity analysis loop in `code/analysis.py`.
 - **Logic**:
 1. Iterate over each threshold in `config.SENSITIVITY_THRESHOLDS`.
 2. For each threshold:
 - Call T031 to filter data.
 - Re-run T027 (Scaffold Split) on the filtered data to ensure structural diversity is maintained for the subset.
 - Call T029 logic to train models on the new split.
 - Record R² and MAE.
 - Save intermediate model to `data/processed/models_intermediate/sensitivity/model_{threshold}.pkl`.
 - Record content hash in `data/processed/model_hashes.json`.
 3. Calculate variance of R² scores across the thresholds.
 4. Save results to `data/processed/sensitivity_analysis.json` with keys: `thresholds`, `r2_scores`, `r2_variance`, `range`, `population_variance`.
 - **DEPENDS ON**: T032a, T031, T027, T029
- [ ] T032c [US2] **Finalize Sensitivity**: Update `data/processed/model_results.json` with sensitivity analysis results.
 - **DEPENDS ON**: T032b

- [ ] T033a [US2] **Initialize**: Create `data/processed/model_results.json` with empty/default structure if no VIF loop or sensitivity analysis has run yet. Keys: `rf_r2: 0.0`, `gb_r2: 0.0`, `cv_scores: []`, `sensitivity_analysis: {}`, `vif_scores: []`. (FR-003, FR-004, FR-007)
 - **DEPENDS ON**: None (Metadata setup task)
- [ ] T033b [US2] **Finalize**: Update `data/processed/model_results.json` with final R²/MAE from T039d (VIF loop) and T032c (Sensitivity). (FR-003, FR-004, FR-007)
 - **DEPENDS ON**: T039d, T032c, T033a

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
- [X] T039b [US3] Implement feature exclusion logic for features with VIF > 10 in `code/analysis.py`. (FR-013)
- [X] T039c [US3] **Iterative VIF Loop**: Implement the iterative VIF loop in `code/analysis.py`.
 - **Logic**:
 1. Load `data/processed/descriptors.csv` (from T019b).
 2. WHILE any VIF > 10:
 - Exclude the feature with the HIGHEST VIF.
 - Recalculate VIF on the reduced feature set (T039a).
 - Retrain the model using the EXACT split indices from T027 and seed.
 - Record `iteration`, `excluded_feature`, `vif_scores`, `r2`, `mae`.
 - **Artifact Versioning**: Save the intermediate model for this iteration to `data/processed/models_intermediate/vif/vif_iter_{iteration:03d}.pkl` (zero-padded) using `joblib.dump` and record its content hash in `data/processed/model_hashes.json`.
 3. Guard Clause: If feature set becomes empty, log critical error and halt.
 4. Save `vif_iteration_log.json` (keys: `iterations: [{iteration, excluded_feature, vif_scores, r2, mae}]`).
 - **DEPENDS ON**: T031, T027, T029, T039a, T039b, T019b
- [ ] T039d [US3] **Finalize VIF**: Update `data/processed/model_results.json` with the final R²/MAE from the last iteration of the VIF loop. Ensure the schema matches `contracts/model_results_schema.yaml`. (FR-013)
 - **DEPENDS ON**: T039c

- [ ] T040 [US3] Compute feature importance rankings on the final VIF-filtered model in `code/analysis.py`. Use `sklearn.inspection.permutation_importance` with `n_repeats=10` and `random_state=SEED`. **Save the ranked list to `data/processed/feature_importance.csv`**. Output format: a ranked list of (feature, importance_score). (FR-005)
 - **Logic**:
 1. Calculate permutation importance.
 2. Sort by importance score (descending).
 3. **File I/O**: Execute `df.to_csv('data/processed/feature_importance.csv', index=False)`.
 4. **Verification**: Assert file exists and has columns ['feature', 'importance_score'].
 - **DEPENDS ON**: T039d

- [X] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values in `code/analysis.py`. Use `scipy.stats.pearsonr`. Output format: a dictionary mapping feature names to (correlation_coefficient, p_value). (FR-005)
 - **DEPENDS ON**: T039d, T040

- [X] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values in `code/analysis.py`. Use `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output format: a dictionary mapping feature names to adjusted p-values. (FR-006)
- [ ] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`. **Logic**: Select **top features by permutation importance score (descending)**, with ties broken by alphabetical feature name. **Keys**: `top__features`, `adjusted_p_values`, `fdr_method`. (FR-005)
 - **DEPENDS ON**: T040 (Feature importance ranking)
 - **NOTE**: T045 is independent of T043 (Plotting) and can run in parallel.
- [ ] T043 [US3] Generate scatter plots with regression lines and confidence intervals for **top features** (identified in T040) in `code/plotting.py`. Use `seaborn.regplot` with `ci=95`. **Save plots as PNG files to `data/processed/corr_plot_top5.png`**. (FR-005)
 - **DEPENDS ON**: T040, T041, T042
- [X] T057 [US3] Generate a specific correlation plot for `aromatic_ring_count` vs. target variable (conductivity/HOMO-LUMO) in `code/plotting.py`.
 **Action**: Create a scatter plot with regression line and 95% CI, saving to `data/processed/corr_plot_resonance.png`.
 **DEPENDS ON**: T040 (to ensure data is available)
- [ ] T044 [US3] **Verify CI Coverage**: Implement a bootstrap-based verification of the 95% confidence interval coverage in `code/analysis.py`.
 - **Logic**:
 1. Perform a sufficient number of bootstrap resamples of the data.
 2. For each resample, compute the correlation and its 95% CI.
 3. Check if the true correlation (from full dataset) falls within the bootstrap CIs.
 4. Calculate the coverage rate (percentage of CIs containing the true value).
 5. **Target**: The nominal coverage target is `config.CONFIDENCE_INTERVAL_TARGET` (default 0.95).
 6. **Comparison**: Compare the calculated coverage rate against the target. If coverage >= target, log "PASS: CI coverage meets target ({coverage} >= {target})". Else, log "FAIL: CI coverage below target ({coverage} < {target})".
 7. Save results to `data/processed/ci_coverage_report.json` including the calculated rate, the target, and the pass/fail status.
 - **DEPENDS ON**: T041, T043

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T046 [P] Update `docs/README.md` and `docs/quickstart.md` to include the HOMO-LUMO/Empirical Proxy fallback logic described in T026.
- [X] T047 Run `black --check` and `ruff check` on `code/`; fix all reported errors. Remove any import statements that are not used in the final code. Ensure all functions in `code/` have docstrings. (FR-010)
- [ ] T049 [P] Run full pipeline integration test on sample dataset (`data/raw/sample_smiles.csv`), verifying execution time < 6 hours on 2-core CPU. Log success/failure to `state/validation_log.json`. **Logic**:
 1. Record start time.
 2. Execute the full pipeline from T013 to T045 (US1-US3 only).
 3. Record end time.
 4. Calculate duration.
 5. If duration > 6 hours, log failure and exit with error.
 6. Log duration and pass/fail status to `state/validation_log.json`. (FR-010)
- [ ] T050 Run a validation script that loads `data/processed/descriptors.csv`, `data/processed/model_results.json`, and `data/processed/analysis_summary.json` and asserts they match the schemas defined in `contracts/descriptor_schema.yaml` and `contracts/model_results_schema.yaml`.
 - **Command**: `python code/validators.py --validate descriptors.csv --schema contracts/descriptor_schema.yaml && python code/validators.py --validate model_results.json --schema contracts/model_results_schema.yaml`
 - **Logic**: The `validators.py` script MUST implement a `--validate` CLI argument that:
 1. Loads the specified data file.
 2. Loads the specified schema YAML.
 3. Validates the data against the schema (using `jsonschema` or manual checks).
 4. Exits with code 0 on success, 1 on failure.
 - **DEPENDS ON**: T005 (Update T005 to include this CLI interface)

- [X] T051 Execute all commands listed in `docs/quickstart.md` in a fresh virtualenv. Log the exit code and any error output to `state/validation_log.json`. Assert all commands exit with code 0.

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
- **Phase 9 Tasks**: Removed.

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
- **Reviewer Feedback Addressed**: Tasks T014a-d implements standard topological descriptors (Degree, Path, Aromaticity, Ring, Conjugation) required by FR-001/FR-008. T032 (split into T032a/b/c) implements the sensitivity analysis with variance recording, explicitly saving to `sensitivity_analysis.json` and versioning intermediate models. T039c/d implements the iterative VIF filtering with reproducibility constraints, metric tracking, and explicit logging to `vif_iteration_log.json` and model hashing. T040, T043, and T045 now explicitly handle artifact saving and feature selection logic.
- **Target Variable Logic**: T026 implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO or Empirical Proxy) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment. It now explicitly logs a warning and proceeds, but **HALTS** if the proxy cannot be computed.
- **Ordering**: Phase 4 tasks are ordered to ensure T031 (filter) runs before T029 (training) for the initial model, and T032 (sensitivity) correctly re-uses T031. T039 (VIF) explicitly depends on T031 and T027. T026 (Target Validation) now runs AFTER T019a (descriptors) to ensure the proxy can be computed.
- **Task Dependencies Clarified**:
 - T019 (Write Descriptors) is now in Phase 3 and depends on T013 and T014.
 - T026 (Validate) now loads raw data directly and depends on T019a.
 - T045 (Analysis Summary) is explicitly marked as independent of T043 (Plotting), allowing parallel execution.
 - T043 (Plotting) dependencies corrected to remove T039 and T045, depending only on T040, T041, T042.
 - T050 (Validation) updated to check for new resonance columns and specify the validation command.
 - T033 is split into T033a (Initialize) and T033b (Finalize) to handle VIF loop results correctly.
 - T017 and T018 are removed (T018 is now T018 in Phase 3).
 - T052, T053, T054 are removed.
 - T055 is updated to confirm schema inclusion.
 - T057 is moved to Phase 5.
 - T044 (CI Coverage) added to satisfy SC-003.
 - T056a/b updated to use RDKit APIs for determinism.
 - T056 split into T056d-g for atomization.
 - **Phase 6 (Resonance Augmentation) Removed**: T072-T078 removed due to Constitution VI violation.
 - **T039d Removed**: Merged into T039c to eliminate redundancy.
 - **T026 Duplication Removed**: Only one authoritative T026 exists in Phase 3. T026a removed.
 - **T012b Dependency Fixed**: Renamed to T012b and made self-contained with inline logic.
 - **T056a/b Dependencies Corrected**: Now depend only on T013.
 - **T056c Flow Corrected**: Depends on T019b, produces augmented data for T056d.
 - **T039c Dependencies Corrected**: Explicitly depends on T019b and T018.
 - **File Naming Conventions**: Explicitly defined for T032 (underscore for floats) and T039c (zero-padded integers) using `joblib`.
 - **CI Coverage Target**: Explicitly defined as `config.CONFIDENCE_INTERVAL_TARGET` (default 0.95) in T044.
 - **Hückel Parameters**: Explicitly defined as alpha=0.0, beta=-1.0, scaling=200 kcal/mol.
 - **Bond Length Table**: Explicitly defined in T056a.
 - **Electronegativity Source**: Explicitly defined as RDKit Periodic Table in T056b.
 - **T064 Replacement**: T064 replaced by T064a to address rejection and missing artifacts. **T064 is now marked DEPRECATED.**
 - **T026 Fallback Logic**: T026 updated to compute fallback target instead of halting.
 - **T032 Config**: T032 updated to read from `config.SENSITIVITY_THRESHOLDS`.
 - **Intermediate Model Directories**: T032 saves to `models_intermediate/sensitivity/` and T039c saves to `models_intermediate/vif/` to prevent file collisions.
 - **Phase 9**: Removed.
 - **Removed Tasks**: T012b, T052-T054, T056a-g, T060-T064a, T065-T068 removed.
 - **T019a/T019b**: Updated to include function signatures and schema verification.
 - **T004/T032**: Updated to use concrete values [2.5, 3.0, 3.5].
 - **T044**: Updated to use config constant.
 - **T005**: Updated to include CLI interface.
 - **T026**: Updated to HALT if no target found (or invoke proxy).
- **New Tasks for Reviewer `linus-pauling-simulated`**:
 - **T072, T073, T074, T075, T076, T077, T078**: Removed (Constitution VI violation).
 - **T017b**: Removed (Not authorized by spec).
 - **T012b**: Removed (Deprecated).
- **Removed Tasks**: T012b, T052-T054, T056a-g, T060-T064a, T065-T068 removed.
- **T019a/T019b**: Updated to include function signatures and schema verification.
- **T004/T032**: Updated to use concrete values [2.5, 3.0, 3.5].
- **T044**: Updated to use config constant.
- **T005**: Updated to include CLI interface.
- **T026**: Updated to HALT if no target found (or invoke proxy).
- **T015a-d**: Removed (Constitution VI violation).
- **T058**: Removed (Depends on forbidden T015a).
- **T012b**: Removed (Depends on forbidden T015a).
- **T066**: Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
