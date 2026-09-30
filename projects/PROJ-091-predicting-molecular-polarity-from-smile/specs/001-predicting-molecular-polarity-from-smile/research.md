# Research: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Research Question
Can a machine learning model trained **exclusively** on 2D topological descriptors (derived from SMILES) predict the **scalar magnitude** of quantum-mechanically calculated dipole moments with sufficient accuracy to serve as a lightweight screening tool, and which specific 2D features carry the strongest predictive signal?

> **Note on Target Variable**: The QM9 dataset provides `mu`, which is the scalar magnitude of the dipole moment vector (in Debye). This study tests whether 2D topology can predict this scalar magnitude, acknowledging that the vector direction (a 3D property) cannot be captured by 2D descriptors.

## Dataset Strategy

### Primary Dataset: QM9
The project utilizes the **QM9** dataset, a standard benchmark containing [deferred] stable small organic molecules. It provides SMILES strings and quantum-mechanically calculated dipole moment magnitudes (`mu`) at the B3LYP/6-31G(2df,p) level.

**Source Verification**:
- **Loader**: `qm9pack` (Python package).
- **Verified Access**: `from qm9pack import get_data; df = get_data('qm9')`.
- **Fields**: `SMILES`, `mu` (Target, scalar magnitude), and atomic composition.
- **URL Reference**: The data is sourced via the `qm9pack` library, which internally fetches from the Maxwell Institute/Zenodo repository. No direct URL fabrication is used.
- **Variable Fit**:
  - **Predictors**: SMILES strings (converted to 2D descriptors).
  - **Outcome**: `mu` (Target, scalar magnitude in Debye).
  - **Covariates**: None required; the model relies on the derived descriptors.
- **Feasibility**: The dataset size (~130k rows) fits within the 6GB RAM limit when processed in chunks or with efficient Pandas/Arrow backends. No authentication is required.

### Excluded Datasets
- **ChemData700K**: Contains SMILES but lacks the specific QM9 dipole moment ground truth required for this specific regression task.
- **TPSA/SMARTS Datasets**: Explicitly excluded by FR-001 to prevent tautological leakage.

## Methodological Rigor

### 1. Feature Engineering (2D-Only)
- **Tool**: `rdkit.Chem.Descriptors` and `rdkit.Chem.rdMolDescriptors`.
- **Constraints**:
  - **No 3D**: Functions like `Get3DConformer` or `EmbedMolecule` are strictly forbidden.
  - **No TPSA**: `TPSA`, `TPSA_E` excluded.
  - **No Functional Groups**: No SMARTS counting for specific polar groups (e.g., -OH, -C=O).
  - **No High-Correlation Exclusion**: Features with |r| > 0.85 with the target are **retained**. High correlation is a sign of predictive power, not leakage. Collinearity is handled downstream.
- **Output**: A matrix of ≥200 2D topological descriptors (connectivity indices, atom counts, etc.).

### 2. Collinearity Mitigation (VIF + L1 Fallback)
- **Method**: Variance Inflation Factor (VIF) calculated for all descriptors.
- **Iterative Removal**: Remove the feature with the highest VIF if VIF > 5.0.
- **Fallback Trigger**: If the feature count drops below **50** during iterative removal, switch to **L1 regularization (Lasso)** instead of further pruning. This prevents the removal of chemically significant descriptors that happen to be collinear.
- **Rationale**: SHAP values can be unstable in the presence of high collinearity. This step ensures the "strongest signal" claim is robust while preserving predictive power.

### 3. Model Training
- **Algorithm**: LightGBM (Gradient Boosting Regressor).
- **Split**: Standard random split (no stratification by target value) to avoid data leakage and simulate real-world deployment.
- **Validation**: k-fold cross-validation (k=[deferred], likely 5 or 10) for hyperparameter tuning.
- **Baseline**: Null model (predicting mean dipole).
- **Metrics**: R², RMSE.

### 4. Interpretability & Stability
- **SHAP Analysis**: Quantify contribution of each descriptor using **SHAP interaction values** to handle correlated features.
- **Cluster Aggregation**: For features identified as collinear (VIF > 5.0), report their joint contribution as a cluster sum rather than independent effects.
- **Bootstrap Stability**: 
  - **Strategy**: 100 bootstrap resamples are drawn from the **full 130k dataset** (with replacement).
  - **Training Constraint**: For each resample, the model is trained on a **10k subsample** to meet runtime constraints.
  - **Metric**: Jaccard similarity of the top 10 features across resamples (target ≥ 0.7).
- **Collinearity Handling**: If descriptors are definitionally related (e.g., total atom count vs. specific atom counts), their joint contribution is reported descriptively, not as independent causal effects.

## Statistical Considerations
- **Multiple Comparisons**: While SHAP provides feature importance, the bootstrap stability check (FR-005) serves as the primary correction for feature selection stability.
- **Power Analysis**: The full QM9 dataset (130k samples) provides ample power for regression. The subsampling for bootstrapping is a computational necessity, not a statistical limitation, as resamples are drawn from the full population.
- **Causal Framing**: The study is observational. Claims will be framed as "predictive associations" rather than causal mechanisms.

## Compute Feasibility
- **CPU-First**: LightGBM and RDKit are highly optimized for CPU.
- **Memory**: Streaming/Chunked processing of the QM9 dataset ensures peak RAM < 6GB.
- **Time**: Processing 130k molecules with ~200 descriptors is estimated at < 2 hours on 2 vCPU. Bootstrap stability (100 iterations on 10k subsamples) is estimated at < 4 hours.
- **GPU**: Not required. No deep learning models (transformers) are planned.

## Decision/Rationale
- **Why LightGBM?**: Fast, handles tabular data well, robust to outliers, and provides native feature importance (complementary to SHAP).
- **Why QM9?**: It is the only open dataset with high-quality QM dipole moment magnitudes paired with SMILES, matching the exact requirements of the research question.
- **Why VIF + L1?**: VIF handles collinearity, but the L1 fallback ensures we do not discard the most informative features due to arbitrary pruning thresholds.
- **Why 2D-Only?**: To isolate the information content of topological representations and test the feasibility of lightweight screening pipelines without 3D geometry generation.