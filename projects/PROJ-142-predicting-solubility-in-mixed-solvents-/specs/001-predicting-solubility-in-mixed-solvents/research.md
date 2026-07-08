# Research: Predicting Solubility in Mixed Solvents with Machine Learning

## 1. Problem Statement & Literature Context

Predicting solubility in mixed solvents is a critical challenge in process chemistry and drug formulation. While solubility in pure solvents is well-studied, mixed solvent systems exhibit non-linear behavior due to complex solute-solvent and solvent-solvent interactions. Traditional linear models (e.g., Abraham solvation parameters) often fail to capture these non-linear mixing effects.

**Research Question**:
*Primary*: Can machine learning models with explicitly engineered interaction terms (solute-solvent, solvent-solvent) outperform traditional linear Abraham models in predicting solubility (logS) for **actual** binary and ternary mixed solvent systems?
*Pivot (if no mixed data)*: Can machine learning models with complex solute-solvent interaction terms outperform linear models in predicting solubility for **pure** solvent systems? (Note: The "non-linear mixing" hypothesis is dropped in this scenario).

**Hypothesis**:
*Primary*: Non-linear mixing effects are significant. ML models incorporating composition-weighted solvent descriptors and explicit interaction terms will achieve a ≥5% reduction in RMSE and R² > 0.70 compared to the Abraham baseline, with statistical significance (p < 0.05).
*Pivot*: ML models will capture non-linear solute-solvent interactions in pure systems, but claims about "mixing" effects are untestable without mixed data. The hypothesis is re-scoped to pure solvent prediction.

## 2. Dataset Strategy

The project relies on verified datasets for solubility measurements and molecular structures.

| Dataset Name | Role in Project | Verified URL / Source | Notes on Coverage |
|:--- |:--- |:--- |:--- |
| **MoleculeNet (ESOL)** | Primary source of solubility (logS) and SMILES for small molecules. | ` | Contains solubility in **pure** water. Used to derive solute descriptors and validate RDKit pipeline. **Limitation**: Does not contain mixed solvent data. |
| **MoleculeNet (FreeSolv)** | Secondary solubility source. | ` | Pure water solubility. Used for cross-validation of descriptor calculation. |
| **EPA Micro All** | Source of experimental data potentially containing mixed solvent entries. | ` | **Critical**: Will be scanned for entries with "solvent" columns indicating mixtures. **If no mixed solvent data exists (N < 100), the project pivots to pure solvent analysis.** No synthetic data is generated. |
| **DSSTox** | Target source for mixed solvent data. | **NO verified source found** | The spec requires DSSTox, but no URL is verified. The plan proceeds with EPA/MoleculeNet data and explicitly notes the missing DSSTox source in the "Assumptions & Gaps" section. **Spec FR-001 requires amendment.** |
| **CRC Handbook** | Source of solvent properties (dielectric constant, dipole moment). | **NO verified source found** | No verified URL for a machine-readable CRC Handbook. The plan will use a curated dictionary of solvent properties (hardcoded for common solvents) or derive them from RDKit if possible, with KNN imputation for missing values. |

### Data Coverage Analysis & Gap Mitigation

**Critical Gap**: The spec requires "binary and ternary mixtures with known composition ratios" (FR-001). The verified MoleculeNet datasets (ESOL, FreeSolv) contain **pure solvent** data. The EPA dataset is the only candidate for mixed solvents.

**Mitigation Strategy**:
1. **Ingestion**: The `01_data_ingestion.py` script will first parse the EPA dataset to identify rows with multiple solvents or explicit mixture composition.
2. **Pivot Condition**: If the EPA dataset lacks sufficient mixed solvent entries (N < 100), the project **pivots** to "Pure Solvent Prediction".
 * **NO synthetic data generation**: The plan explicitly rejects generating synthetic targets via linear blending rules (logS_mix = x1*logS1 + x2*logS2) as this creates a tautology that invalidates the non-linear hypothesis test.
 * **Scope Reduction**: The research question is reframed to pure solvent prediction. The "non-linear mixing" hypothesis is **dropped**.
 * **Reporting**: The final report will explicitly state that the "mixed solvent" hypothesis was untestable due to data gaps.

**Variable Fit Check**:
* **Solute SMILES**: Available in MoleculeNet/EPA.
* **Solvent Properties**: Not in MoleculeNet. Will be mapped via a hardcoded dictionary (common solvents) or RDKit-derived properties (if solvent SMILES are available).
* **Composition**: Must be extracted from EPA text fields. If missing, the row is treated as a pure solvent entry (pivot condition).

## 3. Methodology

### 3.1 Data Preprocessing (FR-001)
1. **Ingestion**: Load CSVs from verified URLs.
2. **Filtering**:
 * Retain molecules with MW < 500 Da (calculated via RDKit).
 * Filter for rows with valid solvent composition (sum of mole fractions ≈ 1.0 ± 0.01) **OR** identify pure solvent rows for the pivot track.
 * Drop rows with missing logS.
3. **Imputation**:
 * Missing solvent properties (dielectric, dipole) → KNN imputation (k=5) using available solvent descriptors.
 * If KNN fails (insufficient neighbors) → Drop row, log warning.
 * **Success Metric**: Imputation rate < 15% (SC-005) **on the actual data ingested**.

### 3.2 Feature Engineering (FR-002, FR-003, Principle VI)
1. **Solute Descriptors**:
 * Morgan Fingerprints (radius=2, nBits=2048).
 * Topological indices (MW, LogP, TPSA, HBA, HBD).
2. **Solvent Descriptors**:
 * **Mixed Solvent Track**: Composition-weighted average of individual solvent properties: $P_{mix} = \sum (x_i \cdot P_i)$.
 * **Pure Solvent Track**: Single solvent properties.
 * Properties: Dielectric constant, Dipole moment, Polarity index.
3. **Interaction Terms** (Non-linear mixing):
 * **Mixed Solvent Track**:
 * **Solute-Solvent**: Product of solute LogP and mixture Polarity.
 * **Solvent-Solvent**: Product of dielectric constant and dipole moment of the mixture.
 * **Polynomials**: Squared terms of key descriptors.
 * **Ratio**: Solute MW / Mixture Polarity.
 * **Pure Solvent Track**: Solute-solvent interaction terms (e.g., LogP * Polarity) are generated, but interpreted as **solute-solvent correlations**, not "mixing" effects. The "mixing" hypothesis is dropped.
 * *Reporting*: The specific forms used will be logged in `artifacts/feature_definitions.yaml`. Collinearity between interaction terms and parent terms will be acknowledged.

### 3.3 Model Training (FR-004)
1. **Algorithms**:
 * **XGBoost Regressor**: `xgboost.XGBRegressor` (CPU only, `tree_method='hist'` or `'exact'`).
 * **Random Forest**: `sklearn.ensemble.RandomForestRegressor`.
 * **Baseline**: Abraham Solvation Parameter Model (implemented via `solv` package or linear regression on Abraham parameters if available).
2. **Validation**:
 * K-Fold Cross-Validation (stratified by solvent system if possible, otherwise random).
 * Hyperparameter Grid: Limited to a reasonable time budget per trial. (e.g., `max_depth=[3, 5, 7]`, `n_estimators=[50, 100]`).
3. **Constraints**:
 * Random seed pinned (e.g., `42`).
 * Memory monitoring: Abort if > 7 GB (FR-008).

### 3.4 Evaluation & Statistics (FR-005, SC-001)
1. **Metrics**: RMSE, MAE, R² on hold-out test set.
2. **Statistical Test**: **Paired t-test** on absolute errors (ML vs. Baseline).
 * *Note*: Spec FR-005 requests Wilcoxon, but Constitution Principle VII mandates a paired t-test. The plan implements the t-test. **Spec FR-005 requires amendment.**
 * Null Hypothesis: No difference in absolute errors.
 * Success: p < 0.05, RMSE reduction ≥ 5%, **and R² > 0.70**. **Spec SC-001 requires amendment to include R² > 0.70.**
3. **Causal/Associational**: Observational data; claims are associational. No randomization.

### 3.5 Interpretability (FR-006, FR-007, SC-002, SC-004)
1. **SHAP Analysis**:
 * Compute SHAP values for the best model.
 * Generate summary plot and feature importance table.
2. **Interaction Term Ranking**:
 * Filter features for "interaction" type.
 * Identify the most significant interaction terms by |mean SHAP|.
3. **Sensitivity Analysis**:
 * Thresholds: A range of significance levels.
 * For each threshold, identify top 5 interaction terms.
 * Calculate Jaccard similarity between sets.
 * **Success**: Minimum Jaccard similarity ≥ 0.6 (SC-004).
4. **Stability**: Spearman rank correlation of SHAP values across CV folds (SC-002).

## 4. Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB disk).
* **Data Volume**: Estimated < 100k rows (after filtering MW < 500). Fits easily in memory.
* **Model Training**: XGBoost and RF on CPU are feasible for this data size within 6 hours.
* **Libraries**: `xgboost`, `scikit-learn`, `rdkit` have CPU wheels available. No CUDA required.
* **Risk**: Memory spike during SHAP calculation for large datasets. Mitigation: Use `shap.TreeExplainer` (fast for tree models) and subsample if necessary.

## 5. Assumptions & Gaps

1. **Data Gap**: No verified URL for DSSTox or CRC Handbook. The plan relies on EPA data and hardcoded/simulated solvent properties. This is a known limitation. **Spec FR-001 requires amendment.**
2. **Mixed Solvent Data**: If EPA data lacks mixed solvent entries, the study **pivots** to "Pure Solvent Prediction". **No synthetic data is generated.** The "non-linear mixing" hypothesis is **dropped**.
3. **Abraham Baseline**: Implementation of the Abraham model may require parameter estimation. If the `solv` package fails, a linear regression on available descriptors will serve as a "Linear Baseline" proxy.
4. **Collinearity**: Interaction terms (products of descriptors) are inherently collinear with their parent terms. The plan will acknowledge this and report descriptive relationships rather than claiming independent causal effects for collinear pairs.
5. **Spec/Constitution Conflict**: The plan implements the Constitution's requirements (t-test, R² > 0.70) over the Spec's conflicting requirements (Wilcoxon, relative RMSE only). **Spec FR-005 and SC-001 require amendment.**