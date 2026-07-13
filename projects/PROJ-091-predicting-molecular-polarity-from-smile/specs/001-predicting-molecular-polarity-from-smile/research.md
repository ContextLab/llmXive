# Research: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Executive Summary

This research investigates whether 2D topological descriptors, derived solely from SMILES strings, can effectively predict quantum-mechanically calculated dipole moments (polarity) of small organic molecules. The study utilizes the QM dataset, a standard benchmark in computational chemistry containing [deferred] stable organic molecules with computed properties. The hypothesis is that topological features (e.g., atom types, connectivity indices) capture a significant portion of the variance in dipole moments, enabling a lightweight, CPU-tractable screening pipeline without the need for expensive 3D conformer generation.

**Critical Methodological Note**: To ensure scientific validity, this study explicitly excludes features definitionally correlated with the target (e.g., TPSA) and employs Variance Inflation Factor (VIF) analysis rather than simple pairwise correlation to mitigate multi-collinearity.

## Dataset Strategy

The project relies exclusively on the **QM9** dataset. The specific source is verified as a Parquet file hosted on HuggingFace.

| Dataset Name | Source URL | Format | Key Variables | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **QM9 (Full)** | `https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet` | Parquet | `smiles`, `dipole_moment` (Debye), `mu_x`, `mu_y`, `mu_z`, `alpha`, `homo`, `lumo`, `gap` | **Verified** (Reachable, Format Confirmed) |
| **QM9 (Subset)** | `https://huggingface.co/datasets/hadoan/enthalpy-QM9-1k/resolve/main/data/train-00000-of-00001-ffd5f7908688c934.parquet` | Parquet | `smiles`, `mu` (Debye) | **Verified** (Reachable, Format Confirmed) |

**Dataset Fit Analysis**:
- **Required Variables**: The study requires `smiles` (input) and `dipole_moment` (target).
- **Verification**: The primary QM9 source (`lisn519010/QM9`) contains a `smiles` column and a `dipole_moment` column (often stored as a vector or scalar magnitude). The vector components (`mu_x`, `mu_y`, `mu_z`) allow for calculation of the magnitude $\sqrt{\mu_x^2 + \mu_y^2 + \mu_z^2}$ if a scalar is not pre-provided.
- **Constraint Check**: The dataset contains the necessary predictors (SMILES) and outcome (Dipole). No external data sources are needed.
- **Missing Data Handling**: The plan explicitly addresses handling of molecules with missing dipole values or malformed SMILES by logging and skipping (FR-001).

**Dataset Loading Strategy**:
- The `code/data/download.py` script will use `pandas.read_parquet` with the verified URL.
- To ensure reproducibility, the file will be saved to `data/raw/qm9_full.parquet` and checksummed.
- A sample of [deferred] molecules will be used for initial development to verify the 2D descriptor pipeline, with the full dataset used for final training if memory permits (otherwise, a stratified random sample of ~50k will be used to stay within 6GB RAM).

## Feature Engineering Strategy

**Method**: RDKit 2D Descriptor Calculation.
**Constraint**: Strictly NO 3D conformer generation (`AllChem.EmbedMolecule` is forbidden).

**Descriptor Categories**:
1. **Count Descriptors**: Atom counts (C, N, O, F, etc.), bond counts (single, double, aromatic).
2. **Topological Indices**: Wiener index, Balaban index, Kier-Hall connectivity indices, Randic indices.
3. **Fragment Counts**: Presence of specific functional groups based on SMARTS patterns.
   - **Constraint**: **Direct polar group flags (e.g., "has -OH", "has -C=O") are strictly EXCLUDED** to prevent trivial lookup-table predictions. Instead, connectivity indices that capture the *topological environment* of these groups are used.
4. **Excluded Features**: 
   - **Topological Polar Surface Area (TPSA)**: Explicitly excluded as it is a 2D approximation of polar surface area strongly correlated with dipole moment, creating a near-tautological validation.
   - **3D-Dependent Descriptors**: Any descriptor requiring 3D coordinates (e.g., WHIM, GETAWAY) is excluded.

**Handling Collinearity & Target Leakage (FR-007)**:
- **Step 1: Target Correlation Check**: Before model training, calculate Pearson correlation between every descriptor and the target (`dipole_moment`). Any feature with $|r| > 0.90$ is **excluded** to prevent definitional redundancy or target leakage.
- **Step 2: Multi-Collinearity Mitigation**: Instead of simple pairwise filtering, apply an iterative **Variance Inflation Factor (VIF)** approach.
  - Calculate VIF for all remaining features.
  - Iteratively remove the feature with the highest VIF (threshold > 5.0) until all remaining features have VIF < 5.0.
  - This addresses linear combinations of >2 features, ensuring SHAP value stability.
- **Note**: If two descriptors are definitionally related (e.g., total atom count vs. sum of specific atom types), their relationship will be reported descriptively, not as independent causal effects (Constitution Principle VI).

## Model Strategy

**Algorithm**: LightGBM Regressor.
**Rationale**:
- **CPU Efficiency**: LightGBM is highly optimized for CPU execution and significantly faster than XGBoost or Random Forests on large datasets, fitting the 6-hour runtime constraint.
- **Non-Linearity**: Dipole moments arise from complex electronic distributions; tree-based models capture non-linear interactions between structural features better than linear regression.
- **Interpretability**: LightGBM supports native SHAP integration.

**Training Protocol**:
- **Split**: **Random Split** ([deferred] Training / [deferred] Test).
  - *Rationale*: Stratification by binning a continuous target is statistically invalid and introduces discretization bias. A simple random split with a fixed seed (42) ensures the test set is a representative sample of the population without artificial artifacts.
- **Validation**: 5-Fold Cross-Validation on the training set to tune hyperparameters (`num_leaves`, `learning_rate`, `max_depth`).
- **Baseline**: A Null Model predicting the mean dipole moment of the training set. The 2D model must exceed this baseline (SC-001).
- **Hyperparameter Tuning**: Grid search or Bayesian optimization over a small defined space to avoid excessive runtime.

**Statistical Rigor**:
- **Multiple Comparisons**: Not applicable in the traditional hypothesis testing sense (regression), but model selection is based on cross-validated mean R².
- **Power Analysis**: Given the large dataset size (>100k), statistical power is high. The limitation is computational, not sample size.
- **Causal Framing**: The study is observational. Claims will be framed as "predictive associations" rather than causal effects of structural features on polarity.

## Sensitivity & Robustness Analysis

**Bootstrap Stability Analysis (Primary)**:
- To address the stability of the "strongest signal" claim, a **Bootstrap Stability Analysis** will be performed.
- **Method**: Resample the training set with replacement multiple times (e.g., 50 iterations). Train a LightGBM model on each resample.
- **Metric**: Track the frequency with which the top 10 SHAP features appear across the models.
- **Output**: A stability report showing which features consistently carry the strongest signal vs. those that are artifacts of specific data splits.

**Threshold Sweeps (FR-005)**:
- A secondary sensitivity analysis will be performed on feature selection thresholds (e.g., VIF cutoff) and model hyperparameters.
- Specific sweeps: VIF cutoffs at $\{3.0, 5.0, 10.0\}$ and learning rates at $\{0.01, 0.05, 0.1\}$.
- **Metric**: Variation in MAE and RMSE on the held-out test set.
- **Output**: A report detailing how model stability changes with these parameters.

**Edge Case Handling**:
- **Undefined Stereochemistry**: SMILES strings with missing stereochemistry will be normalized (e.g., removing `@` symbols) or flagged. If the descriptor calculation fails, the molecule is skipped.
- **Flexible Molecules**: Molecules with high flexibility (many rotatable bonds) are expected to have higher prediction errors due to the 2D approximation. These will be identified as outliers in the error analysis.
- **NaN Handling**: If RDKit returns `NaN` for a descriptor, the value will be imputed with the median of the training set.

## Decision Rationale: CPU-Only Feasibility

The plan explicitly avoids GPU-dependent methods (e.g., Graph Neural Networks with PyTorch Geometric requiring CUDA) and 3D conformer generation (e.g., RDKit `AllChem.EmbedMolecule` which can be slow and memory-intensive for large batches).
- **Library Choice**: `lightgbm` has native CPU support and is significantly lighter than deep learning frameworks.
- **Memory Management**: Data is processed in chunks. The feature matrix is saved as a compressed Parquet file. The model is trained on a subset if the full matrix exceeds available memory resources (leaving sufficient capacity for OS and overhead).
- **Runtime**: LightGBM training on 50k samples with 200 features typically completes in <10 minutes on 2 vCPU. The bottleneck is feature generation, which is parallelized but bounded by a fixed time limit.