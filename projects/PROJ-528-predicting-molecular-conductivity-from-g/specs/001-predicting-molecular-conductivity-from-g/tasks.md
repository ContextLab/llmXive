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
- [X] T002 Initialize Python 3.x project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `networkx`, `statsmodels`, `joblib`
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
 - `descriptor_schema.yaml`: fields `smiles`, `status`, `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`, `aromaticity_index`, `huckel_aromaticity_count`, `clar_aromaticity_proxy`, `conjugation_length`, `num_conjugated_bonds`, `conjugation_density`, `ring_count`, `bond_order_weighted_path`, `electronegativity_polarity_score`. (FR-001, FR-008, Reviewer: linus-pauling-simulated)
- [X] T013 [P] [US1] Implement `load_smiles(path: str) -> pd.DataFrame` in `code/data_loader.py` returning DataFrame with columns [smiles, valid, error_msg]
- [X] T026 [P] [US1/US2] **Target Variable Validation (FR-011)**: Implement `validate_target_variable(path: str)` in `code/data_loader.py`.
 - **Logic**:
 1. Load raw data directly from `config.RAW_DATA_PATH` (output of T013).
 2. Check for 'conductivity' or 'charge_carrier_mobility' column.
 3. **If Found**: Verify dynamic range (>= 3 orders of magnitude). If valid, set `TARGET_VAR = 'conductivity'`. **If Invalid**: HALT with error "CRITICAL: Target variable dynamic range (< 3 orders of magnitude) is insufficient per FR-011."
 4. **If NOT Found**: Check for 'HOMO_LUMO_gap'. **If Found**: Log "WARNING: Conductivity missing. Using HOMO-LUMO gap as proxy per Plan Scope Adjustment (FR-014 fallback)." Set `TARGET_VAR = 'HOMO_LUMO_gap'`. Proceed if HOMO-LUMO gap column exists and has valid dynamic range.
 5. **If NEITHER Found**: **HALT** with error "CRITICAL: No valid target variable found (Conductivity or HOMO-LUMO gap missing)."
 - **DEPENDS ON**: T013 (ensures raw data is loaded)
 - **NOTE**: This task MUST run BEFORE T019 (Write Results) and T028 (Log Transform) to ensure data validity. It implements the strict Spec requirement (FR-003/FR-011) with a documented fallback path for the Plan's scope adjustment.

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
 - **DEPENDS ON**: T061

### Implementation for User Story 1

- [X] T018 [US1] **Filter Missing Targets (FR-012)**: Implement `filter_missing_targets(df, target_col)` in `code/data_loader.py`.
 - **Logic**:
 1. Load the raw data (T013).
 2. Identify rows where `target_col` is NaN or missing.
 3. Drop these rows and log the count: "Dropped {count} rows with missing target values."
 4. Return the filtered DataFrame.
 - **DEPENDS ON**: T013, T026 (ensures target column is identified)
 - **NOTE**: This task ensures FR-012 compliance by explicitly excluding molecules with missing targets *before* descriptor computation.

- [X] T014a [US1] Implement **Base Graph Descriptors** in `code/descriptors.py` (FR-001). Compute: `degree_mean`, `degree_std`, `degree_max`, `degree_min`, `path_length_mean`, `path_length_std`, `path_length_max`, `path_length_min`.
- [X] T014b [US1] Implement **Aromaticity & Ring Descriptors** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromaticity_index`, `ring_count`.
- [X] T014c [US1] Implement **Conjugation Descriptors** in `code/descriptors.py` (FR-001). Compute: `conjugation_length` (longest simple path in conjugated subgraph), `num_conjugated_bonds`, `conjugation_density`.
- [X] T014d [US1] Implement **Resonance Proxies (RDKit Only)** in `code/descriptors.py` (FR-001, FR-008). Compute: `aromatic_ring_count`, `conjugated_ring_count`.
 - **Logic**:
 1. Parse SMILES to RDKit molecule object.
 2. Use `rdkit.Chem.Lipinski` and `rdkit.Chem.rdMolDescriptors` to compute aromatic ring counts and conjugation metrics.
 3. **Note**: All descriptors MUST be computed using RDKit. If a calculation fails for a specific molecule, log a warning and set the value to NaN for that molecule only. Do not halt the entire pipeline. (FR-001, FR-008)
 4. **Runtime Monitoring**: Log a warning if descriptor computation for a single molecule exceeds a predefined time threshold., but continue processing. Do NOT exit. (FR-010)

- [X] T019a [US1] **Write Base Descriptors**: Write results of T014a, T014b, T014c, T014d to `data/processed/descriptors_base.csv`.
 - **Logic**:
 1. Load SMILES from T013 (filtered by T018).
 2. Compute descriptors using T014a-d.
 3. Drop rows with NaN in required descriptor columns. Log: "Dropped {count} rows due to NaN values in descriptors." (FR-001, FR-008)
 4. **Write File**: Execute `df.to_csv('data/processed/descriptors_base.csv', index=False)`.
 5. **Verify**: Assert `os.path.exists('data/processed/descriptors_base.csv')` and `len(df) > 0`.
 - **DEPENDS ON**: T014a, T014b, T014c, T014d, T018
 - **run**:
 ```bash
 python -c "
import pandas as pd
import sys
import os
from code.data_loader import load_smiles, filter_missing_targets
from code.descriptors import compute_base_descriptors, compute_aromaticity, compute_conjugation, compute_resonance_proxies

# Load and filter raw data
df_raw = load_smiles('data/raw/smiles.csv')
df_filtered = filter_missing_targets(df_raw, target_col='conductivity') # or 'HOMO_LUMO_gap' based on T026

# Compute descriptors
df_desc = compute_base_descriptors(df_filtered)
df_desc = compute_aromaticity(df_desc)
df_desc = compute_conjugation(df_desc)
df_desc = compute_resonance_proxies(df_desc)

# Filter NaNs
df_final = df_desc.dropna(subset=['degree_mean', 'ring_count', 'conjugation_length', 'aromatic_ring_count'])

# Ensure the directory exists
os.makedirs('data/processed', exist_ok=True)

# EXACT FILE WRITE COMMAND (per executability concern)
df_final.to_csv('data/processed/descriptors_base.csv', index=False)

# EXACT VERIFICATION COMMAND (per executability concern)
assert os.path.exists('data/processed/descriptors_base.csv'), 'File write failed: descriptors_base.csv does not exist.'
assert len(pd.read_csv('data/processed/descriptors_base.csv')) > 0, 'File write failed: descriptors_base.csv is empty.'

print('T019a: Base descriptors written and verified successfully.')
"
 - **DEPENDS ON**: T014a, T014b, T014c, T014d, T018

- [X] T019b [US1] **Write Full Descriptors (Base)**: Write results of T019a to `data/processed/descriptors.csv`, ensuring schema matches contract.
 - **Logic**:
 1. Load `data/processed/descriptors_base.csv` (T019a).
 2. Ensure final schema matches `contracts/descriptor_schema.yaml`.
 3. **Write File**: Execute `df.to_csv('data/processed/descriptors.csv', index=False)`.
 4. **Verify**: Assert `os.path.exists('data/processed/descriptors.csv')` and `len(df) > 0`.
 - **DEPENDS ON**: T019a
 - **run**:
 ```bash
 python -c "
import pandas as pd
import os

# Load base descriptors (from T019a)
df_base = pd.read_csv('data/processed/descriptors_base.csv')

# Ensure the directory exists
os.makedirs('data/processed', exist_ok=True)

# EXACT FILE WRITE COMMAND (per executability concern)
df_base.to_csv('data/processed/descriptors.csv', index=False)

# EXACT VERIFICATION COMMAND (per executability concern)
assert os.path.exists('data/processed/descriptors.csv'), 'File write failed: descriptors.csv does not exist.'
assert len(pd.read_csv('data/processed/descriptors.csv')) > 0, 'File write failed: descriptors.csv is empty.'

print('T019b: Full descriptors written and verified successfully.')
"
 - **DEPENDS ON**: T019a

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

- [X] T026a [US2] **Target Variable Selection (FR-003/FR-014)**: Implement `select_target_variable(df, target_candidates)` in `code/model_training.py`.
 - **Logic**:
 1. Check for 'conductivity' or 'charge_carrier_mobility' in `df`.
 2. **If Present**: Use as target. Log "INFO: Using conductivity as target (FR-003)."
 3. **If Missing**: Check for 'HOMO_LUMO_gap'. **If Present**: Use as target. Log "WARNING: Conductivity missing. Using HOMO-LUMO gap as proxy (FR-014 fallback)."
 4. **If Neither**: Raise `ValueError` "CRITICAL: No valid target variable found."
 5. Store `target_type` in `model_results.json`.
 - **DEPENDS ON**: T026 (validation), T018 (filtering)

- [X] T027 [US2] Implement scaffold-based train/test split (a majority/minority ratio) in `code/scaffold_split.py` AFTER T026a completes (FR-002)
- [X] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO) in `code/model_training.py`. Use natural logarithm (`np.log`) on the target column. Create a new column named `log_{target_var}`. (FR-003)
- [X] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity in `code/analysis.py`. Function signature: `def filter_outliers(df, target_col, sigma_threshold):`. Logic: Calculate z-scores for `target_col`. Filter rows where `abs(z_score) <= sigma_threshold`. Return filtered DataFrame. Ensure it reuses the exact split indices from T027 and seed from T004. (FR-007)
- [X] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target in `code/model_training.py`. RF: `n_estimators=100`, `max_depth=None`, `random_state=SEED`. GB: `n_estimators=100`, `learning_rate=0.1 (2304.07537, https://arxiv.org/abs/2304.07537)`, `random_state=SEED`. **Note**: Initial training uses data filtered by T031 with default threshold (standard statistical significance level). (FR-003)
- [X] T030 [US2] Implement -fold cross-validation and metric recording in `code/model_training.py`. Use `cross_val_score` with `cv=5` and `scoring='r2'`. Record mean and std of R² scores. (FR-004)
- [X] T032 [US2] Implement sensitivity analysis loop in `code/analysis.py`. **Logic**:
 1. Define thresholds: `{2.5, 3.0, 3.5}`.
 2. For each threshold, call T031 to filter data, then retrain models (using T029 logic) and record R².
 3. Calculate variance of R² scores across the 3 thresholds.
 4. Save results to `data/processed/sensitivity_analysis.json` with keys: `thresholds`, `r2_scores` (list of raw scores), `r2_variance`, `range`, `population_variance`.
 5. **Artifact Versioning**: Save the intermediate model objects for each threshold to `data/processed/models_intermediate/model_{threshold_formatted}.pkl` (e.g., `model_2_5.pkl` for 2.5) using `joblib.dump`. Record their content hashes in `data/processed/model_hashes.json` to satisfy Constitution Principle IV (Single Source of Truth). (FR-007)
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
- [X] T039b [US3] Implement feature exclusion logic for features with VIF > 10 in `code/analysis.py`. {{claim:c_f1155d99}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) (FR-013)
- [X] T039c [US3] **Unified VIF Loop & Finalize**: Implement the iterative VIF loop in `code/analysis.py` and perform final artifact updates. **Prerequisites**: Must run on data filtered byT031 (outliers) and use split indices from T027.
 1. Load `data/processed/descriptors.csv` (from T019b).
 2. WHILE any VIF > 10:
 - Exclude the feature with the HIGHEST VIF.
 - Recalculate VIF on the reduced feature set (T039a).
 - Retrain the model using the EXACT split indices and seed.
 - Record `iteration`, `excluded_feature`, `vif_scores`, `r2`, `mae`.
 - **Artifact Versioning**: Save the intermediate model for this iteration to `data/processed/models_intermediate/vif_iter_{iteration:03d}.pkl` (zero-padded) using `joblib.dump` and record its content hash in `data/processed/model_hashes.json`.
 3. Guard Clause: If feature set becomes empty, log critical error and halt.
 4. Save `vif_iteration_log.json` (keys: `iterations: [{iteration, excluded_feature, vif_scores, r2, mae}]`).
 5. **Finalize**: Update `data/processed/model_results.json` with the final R²/MAE from the last iteration of the VIF loop. Ensure the schema matches `contracts/model_results_schema.yaml`. (FR-013)
 - **DEPENDS ON**: T031, T027, T029, T039a, T039b, T019b
- [X] T040 [US3] Compute feature importance rankings on the final VIF-filtered model in `code/analysis.py`. Use `sklearn.inspection.permutation_importance` with `n_repeats=10` and `random_state=SEED`. **Save the ranked list to `data/processed/feature_importance.csv`**. Output format: a ranked list of (feature, importance_score). (FR-005)
 - **Logic**:
 1. Calculate permutation importance.
 2. Sort by importance score (descending).
 3. **File I/O**: Execute `df.to_csv('data/processed/feature_importance.csv', index=False)`.
 4. **Verification**: Assert file exists and has columns ['feature', 'importance_score'].
 - **DEPENDS ON**: T039c

- [X] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values in `code/analysis.py`. Use `scipy.stats.pearsonr`. Output format: a dictionary mapping feature names to (correlation_coefficient, p_value). (FR-005)
 - **DEPENDS ON**: T039c, T040

- [X] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values in `code/analysis.py`. Use `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output format: a dictionary mapping feature names to adjusted p-values. (FR-006)
- [X] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`. **Logic**: Select **top features by permutation importance score (descending)**, with ties broken by alphabetical feature name. **Keys**: `top_5_features`, `adjusted_p_values`, `fdr_method`. (FR-005)
 - **DEPENDS ON**: T040 (Feature importance ranking)
 - **NOTE**: T045 is independent of T043 (Plotting) and can run in parallel.
- [X] T043 [US3] Generate scatter plots with regression lines and confidence intervals for **top 5 features** (identified in T040) in `code/plotting.py`. Use `seaborn.regplot` with `ci=95`. **Save plots as PNG files to `data/processed/corr_plot_top5.png`**. (FR-005)
 - **DEPENDS ON**: T040, T041, T042
- [X] T057 [US3] Generate a specific correlation plot for `aromatic_ring_count` vs. target variable (conductivity/HOMO-LUMO) in `code/plotting.py`.
 **Action**: Create a scatter plot with regression line and 95% CI, saving to `data/processed/corr_plot_resonance.png`.
 **DEPENDS ON**: T056 (to ensure data is available)
- [X] T044 [US3] **Verify CI Coverage**: Implement a bootstrap-based verification of the 95% confidence interval coverage in `code/analysis.py`.
 - **Logic**:
 1. Perform a sufficient number of bootstrap resamples of the data.
 2. For each resample, compute the correlation and its 95% CI.
 3. Check if the true correlation (from full dataset) falls within the bootstrap CIs.
 4. Calculate the coverage rate (percentage of CIs containing the true value).
 5. **Target**: The nominal coverage target is **0.95** ([deferred]).
 6. Log the coverage rate and compare against 0.95 (tolerance +/- 0.05).
 7. Save results to `data/processed/ci_coverage_report.json`.
 - **DEPENDS ON**: T041, T043

---

## Phase 6: Resonance & Bond-Order Augmentation (Priority: P3 - Reviewer Revision)

**Goal**: Address reviewer `linus-pauling-simulated`'s concern regarding the fundamental role of resonance in electronic delocalization by augmenting descriptors with bond-order and electronegativity-based proxies using RDKit.

**Independent Test**: Verify that molecules with known conjugated systems (e.g., benzene, butadiene) exhibit higher `bond_order_weighted_path` and `electronegativity_polarity_score` compared to saturated analogs.

### Implementation for Resonance Augmentation

- [X] T055 [US3] **Update Schema**: Ensure `contracts/descriptor_schema.yaml` includes resonance columns: `aromatic_ring_count`, `conjugated_ring_count`, `bond_order_weighted_path`, `electronegativity_polarity_score`. (Already defined in T009, this task confirms inclusion).
 **DEPENDS ON**: T009

- [X] T056a [US1] **Compute Bond-Order Weighted Path**: Implement `compute_bond_order_weighted_path(mol)` in `code/descriptors.py`.
 **Logic**:
 1. Iterate over all edges in the RDKit molecule graph.
 2. Estimate bond order: Use `bond.GetBondType()` (SINGLE=1, DOUBLE=2, AROMATIC=1.5 (Wikipedia: Bond order, https://en.wikipedia.org/wiki/Bond_order)).
 3. {{claim:c_53ded197}}
 4. Compute a "weighted path" metric: Sum of (1 / estimated_bond_length) for the longest conjugated path.
 5. **Rationale**: Captures the "effective bond length contracts by a measurable degree" nuance mentioned in the review.
 6. Add result to descriptor dictionary.
 **DEPENDS ON**: T013

- [X] T056b [US1] **Compute Electronegativity-Polarity Score**: Implement `compute_electronegativity_polarity(mol)` in `code/descriptors.py`.
 **Logic**:
 1. Iterate over all edges (bonds) in the molecule.
 2. Retrieve atomic numbers for the two bonded atoms.
 3. Use `rdkit.Chem.GetPeriodicTable().GetElectronegativity(atom_num)` to get Pauling electronegativity values.
 4. Calculate `delta_EN = abs(EN_atom1 - EN_atom2)`.
 5. Estimate bond length as in T056a.
 6. Calculate `polarity_contribution = delta_EN * estimated_bond_length`.
 7. Sum `polarity_contribution` across all bonds (or average) to get a molecular score.
 8. **Rationale**: Captures "electronegativity difference multiplied by bond length" as recommended by the reviewer.
 **DEPENDS ON**: T013

- [X] T056c [US1] **Integrate New Descriptors**: Update `code/descriptors.py` to call T056a and T056b and merge results into the final descriptor DataFrame.
 - **Logic**:
 1. Reload `data/processed/descriptors.csv` (T019b).
 2. Compute T056a and T056b for each molecule.
 3. Merge new columns into the DataFrame.
 4. **File I/O**: Save to `data/processed/descriptors_augmented.csv`.
 - **DEPENDS ON**: T056a, T056b, T019b

- [X] T056d [US2] **Reload Descriptors**: Reload the augmented descriptors for retraining.
 - **Logic**:
 1. Load `data/processed/descriptors_augmented.csv` (from T056c).
 2. Validate schema includes new resonance columns.
 - **DEPENDS ON**: T056c

- [X] T056e [US2] **Re-run VIF Loop**: Re-run the VIF filtering loop (T039a-d) on the augmented dataset to ensure new features don't introduce collinearity.
 - **DEPENDS ON**: T056d, T039a, T039b

- [X] T056f [US2] **Retrain Models**: Retrain RF and GB models on the VIF-filtered augmented dataset.
 - **DEPENDS ON**: T056e, T029

- [X] T056g [US2] **Compare Metrics**: Compare R²/MAE against the baseline (T033b) and log the improvement (or degradation) in `data/processed/resonance_impact_report.json`.
 - **Logic**:
 1. Calculate delta R² and delta MAE.
 2. Log results.
 - **DEPENDS ON**: T056f, T033b

**Checkpoint**: Resonance and bond-order descriptors are integrated, and their impact on model performance is quantified.

---

## Phase 7: Polish & Cross-Cutting Concerns

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
- [X] T050 Run a validation script that loads `data/processed/descriptors.csv`, `data/processed/model_results.json`, and `data/processed/analysis_summary.json` and asserts they match the schemas defined in `contracts/descriptor_schema.yaml` and `contracts/model_results_schema.yaml`.
 - **Command**: `python code/validators.py --validate descriptors.csv --schema contracts/descriptor_schema.yaml && python code/validators.py --validate model_results.json --schema contracts/model_results_schema.yaml`
 - **Logic**: The `validators.py` script MUST implement a `--validate` CLI argument that:
 1. Loads the specified data file.
 2. Loads the specified schema YAML.
 3. Validates the data against the schema (using `jsonschema` or manual checks).
 4. Exits with code 0 on success, 1 on failure.
 - **DEPENDS ON**: T005 (Update T005 to include this CLI interface)

- [X] T051 Execute all commands listed in `docs/quickstart.md` in a fresh virtualenv. Log the exit code and any error output to `state/validation_log.json`. Assert all commands exit with code 0.

---

## Phase 8: Hückel Resonance Energy Calculation (Priority: P3 - Reviewer Revision)

**Goal**: Implement a simplified Hückel Molecular Orbital (HMO) calculation to estimate resonance energy per fragment, addressing the reviewer's specific request for quantum-chemical parameters to capture delocalization energy.

**Independent Test**: Verify that benzene yields a positive resonance energy consistent with literature values (approx. -40 kcal/mol relative to a localized reference), while cyclohexane yields near-zero resonance energy.

### Implementation for Hückel Resonance

- [X] T060 [US1] **Implement Hückel Matrix Builder**: Create `code/descriptors.py::build_huckel_matrix(mol)`.
 - **Logic**:
 1. Identify the conjugated π-system within the RDKit molecule (subset of atoms with p-orbitals).
 2. Construct the Hückel Hamiltonian matrix (H) where:
 - Diagonal elements (Coulomb integrals) are set to **alpha = 0.0**.
 - Off-diagonal elements (Resonance integrals) are set to **beta = -1.0** if atoms are bonded and part of the π-system, 0.0 otherwise.
 - Handle heteroatoms (N, O) by adjusting alpha and beta based on electronegativity (simplified Pauling scaling).
 - **Output**: A numpy array representing the H matrix for the π-system.
 - **DEPENDS ON**: T013 (to load molecules)

- [X] T061 [US1] **Compute Resonance Energy**: Create `code/descriptors.py::compute_huckel_resonance_energy(mol)`.
 - **Logic**:
 1. Call `build_huckel_matrix` to get H.
 2. Compute eigenvalues of H (energy levels).
 3. Fill orbitals with π-electrons (2 per orbital, following Aufbau principle).
 4. Calculate Total Energy of the delocalized system (sum of occupied eigenvalues).
 5. Calculate Total Energy of a hypothetical localized reference system (sum of isolated C=C double bond energies, e.g., proportional to β per double bond).
 6. `Resonance Energy = E_localized - E_delocalized`.
 7. Convert to kcal/mol using a scaling factor of **200 kcal/mol per beta unit**.
 8. Return the resonance energy value.
 - **Rationale**: Directly implements the reviewer's request to "calculate resonance energy per fragment using Hückel theory".
 - **DEPENDS ON**: T060

- [X] T062 [US1] **Integrate Hückel Descriptor**: Update `code/descriptors.py` to call `compute_huckel_resonance_energy` and add the result as a new column `huckel_resonance_energy` in the descriptor DataFrame.
 - **Logic**:
 1. Iterate over all molecules in the dataset.
 2. Compute Hückel energy for each.
 3. Handle cases where the π-system cannot be identified (log warning, set to NaN).
 4. Merge into `data/processed/descriptors.csv`.
 - **DEPENDS ON**: T061, T019b

- [X] T063 [US3] **Validate Hückel Results**: Create a unit test in `tests/test_huckel.py::test_benzene_resonance_energy` to verify that the computed resonance energy for benzene is positive and within an expected range (e.g., > 0.5 β units), and for cyclohexane is near zero.
 - **DEPENDS ON**: T062

- [ ] T064 [US2] **Re-evaluate Model with Hückel Feature**: Re-run the full VIF loop (T039a-d) and model training (T029) including the new `huckel_resonance_energy` feature.
 - **Logic**:
 1. Load updated descriptors (T062).
 2. Run VIF filtering to check for collinearity with other resonance proxies.
 3. Train models and record metrics.
 4. Save results to `data/processed/huckel_impact_report.json`.
 - **DEPENDS ON**: T062, T039a, T029, T056e (Phase 6 completion)

**Checkpoint**: Hückel resonance energy is integrated, validated, and its impact on predictive fidelity is quantified.

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
- **Resonance Tasks**: T014d, T055, T056a, T056b, T056c can be implemented in parallel as they modify different parts of `descriptors.py` and `analysis.py`.
- **Hückel Tasks**: T060, T061, T062 can be implemented in parallel as they are distinct computational steps.

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
- **Reviewer Feedback Addressed**: Tasks T014a-d implements standard topological descriptors (Degree, Path, Aromaticity, Ring, Conjugation) required by FR-001/FR-008. T032 implements the sensitivity analysis with variance recording, explicitly saving to `sensitivity_analysis.json` and versioning intermediate models. T039c implements the iterative VIF filtering with reproducibility constraints, metric tracking, and explicit logging to `vif_iteration_log.json` and model hashing. T040, T043, and T045 now explicitly handle artifact saving and feature selection logic.
- **Phase 6 (Resonance Augmentation) Added**: Addresses `linus-pauling-simulated`'s concern about resonance. T014d implements aromatic ring counts and conjugation metrics using RDKit. T056a, T056b, T056c implement the specific bond-order and electronegativity proxies requested using RDKit APIs. T056d-g re-evaluates model performance with these new features.
- **Phase 8 (Hückel Resonance) Added**: Addresses `linus-pauling-simulated`'s specific request for "calculate resonance energy per fragment using Hückel theory". T060 builds the Hückel matrix, T061 computes the energy, T062 integrates it, T063 validates it, and T064 re-evaluates the model.
- **Phase 6 Removal (Custom Quantum)**: The previous Phase 6 (T052-T057 custom quantum) was removed because it attempted to implement custom quantum-chemical proxies (Hückel matrix diagonalization, custom bond order estimation) that violate Constitution Principle VI (Graph Descriptor Transparency) and lack a spec anchor. The project now strictly adheres to RDKit-based descriptors and topological proxies, with Hückel theory implemented as a simplified, transparent proxy for resonance energy.
- **Target Variable Logic**: T026 implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment. It now explicitly logs a warning and proceeds, but **HALTS** if neither is found. **CRITICAL**: The Plan's "Critical Scope Adjustment" to use HOMO-LUMO is a manual research pivot requiring a plan amendment, not an automatic code path. The implementation enforces FR-003/FR-011 strictly, with the fallback path explicitly documented as a warning and requiring the presence of HOMO-LUMO data.
- **Ordering**: Phase 4 tasks are ordered to ensure T031 (filter) runs before T029 (training) for the initial model, and T032 (sensitivity) correctly re-uses T031. T039 (VIF) explicitly depends on T031 and T027. T026 (Target Validation) now runs BEFORE T019 (Write Results) to ensure the schema is validated before writing.
- **Task Dependencies Clarified**:
 - T019 (Write Descriptors) is now in Phase 3 and depends on T013 and T014.
 - T026 (Validate) now loads raw data directly and depends on T013.
 - T045 (Analysis Summary) is explicitly marked as independent of T043 (Plotting), allowing parallel execution.
 - T043 (Plotting) dependencies corrected to remove T039 and T045, depending only on T040, T041, T042.
 - Phase 6 (Resonance) added as a revision phase, dependent on US1 and US3.
 - T050 (Validation) updated to check for new resonance columns and specify the validation command.
 - T033 is split into T033a (Initialize) and T033b (Finalize) to handle VIF loop results correctly.
 - T017 and T018 are removed (T018 is now T018 in Phase 3).
 - T052, T053, T054 are removed.
 - T055 is updated to confirm schema inclusion.
 - T057 is moved to Phase 5.
 - T044 (CI Coverage) added to satisfy SC-003.
 - T056a/b updated to use RDKit APIs for determinism.
 - T056 split into T056d-g for atomization.
 - Phase 8 (Hückel) added as a new revision phase to address the specific resonance energy calculation request.
 - **T039d Removed**: Merged into T039c to eliminate redundancy.
 - **T026 Duplication Removed**: Only one authoritative T026 exists in Phase 2.
 - **T012b Dependency Fixed**: Now depends on T061.
 - **T056a/b Dependencies Corrected**: Now depend only on T013.
 - **T056c Flow Corrected**: Depends on T019b, produces augmented data for T056d.
 - **T039c Dependencies Corrected**: Explicitly depends on T019b and T018.
 - **File Naming Conventions**: Explicitly defined for T032 (underscore for floats) and T039c (zero-padded integers) using `joblib`.
 - **CI Coverage Target**: Explicitly defined as 0.95 in T044.
 - **Hückel Parameters**: Explicitly defined as alpha=0.0, beta=-1.0, scaling=200 kcal/mol.
 - **Bond Length Table**: Explicitly defined in T056a.
 - **Electronegativity Source**: Explicitly defined as RDKit Periodic Table in T056b.