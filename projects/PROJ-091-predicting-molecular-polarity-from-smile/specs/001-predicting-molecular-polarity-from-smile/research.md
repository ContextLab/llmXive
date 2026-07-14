# Research: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Research Question
To what extent can 2D topological descriptors alone (excluding 3D geometry, TPSA, and functional group proxies) predict quantum-mechanically calculated dipole moments, and which specific **clusters** of 2D features carry the strongest *stable* predictive signal?

## Dataset Strategy

The project relies on the **QM9** dataset, which contains 134k small organic molecules with computed quantum mechanical properties, including dipole moments.

| Dataset Name | Source URL | Format | Variables Used | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **QM9** | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | Parquet | `smiles` (SMILES string), `mu` (Dipole moment in Debye) | Primary source. Contains both features (SMILES) and target (`mu`). |

**Data Loading Strategy**:
1.  The raw Parquet file is downloaded to `data/raw/qm9_full.parquet`.
2.  A checksum is computed and stored in `state/` to satisfy Constitution Principle III.
3.  The dataset is loaded into a Pandas DataFrame.
4.  **Sampling**: To meet the ≤6GB RAM constraint on the free-tier runner, a representative subset of the QM9 dataset will be sampled (e.g., 10k-20k molecules) if the full set exceeds memory limits during feature engineering. The sampling method (stratified by dipole magnitude or random) will be documented in `code/data/download_qm9.py`.
5.  **Variable Fit Check**: The QM9 dataset explicitly contains `mu` (dipole moment) and `smiles`. No external variables are required. The plan confirms that `mu` is the target and `smiles` is the source for 2D descriptors.

**Excluded Data Sources**:
-   **TPSA/SMARTS datasets**: Explicitly excluded by FR-001 to prevent tautological validation.
-   **3D Geometry datasets**: Explicitly excluded by Constitution Principle VI.
-   **Unverified URLs**: No other dataset URLs are used. The "Verified datasets" block provided in the prompt lists QM9 sources; no other sources are needed.

## Methodological Approach

### 1. Feature Engineering (2D Topology Only)
-   **Library**: `rdkit.Chem.Descriptors` and `rdkit.Chem.rdMolDescriptors`.
-   **Exclusions**:
    -   NO `rdkit.Chem.AllChem.EmbedMolecule` or `Get3DConformer`.
    -   NO `CalcTPSA`, `CalcTPSA_E`, or any surface-area proxies.
    -   NO SMARTS pattern matching for specific functional groups (e.g., -OH, -C=O).
    -   **CRITICAL**: **NO exclusion of features based on correlation with the target (|r| > 0.85)**. All 2D descriptors are retained to measure the true predictive capacity of 2D topology. High-correlation features are valid signals, not leakage.
-   **Output**: A matrix of ≥200 2D descriptors per molecule.
-   **Handling**: NaN values imputed with median; malformed SMILES skipped with logging.

### 2. Model Training
-   **Algorithm**: LightGBM Regressor (`lightgbm.LGBMRegressor`).
-   **Validation**: 5-fold Cross-Validation (CV) with standard random split.
-   **Baseline**: Null model predicting the mean `mu` of the training set (R² = 0.0).
-   **Hyperparameters**: Tuned via CV (grid search or Optuna) for `num_leaves`, `learning_rate`, `max_depth`.
-   **Constraint**: CPU-only execution; no GPU acceleration.
-   **Power Analysis**: The study is designed to detect a **Minimum Detectable Effect Size (MDES)** for **Cluster Stability** of 0.2 (Jaccard similarity difference from random baseline 0.5 to stable 0.7) with 80% power at alpha=0.05. The sample size (N) will be verified against this MDES before full training.

### 3. Interpretability & Stability (Cluster-Aware)
-   **SHAP Analysis**: `shap.TreeExplainer` on the trained LightGBM model.
-   **Collinearity Handling (Cluster-Aware)**:
    -   Calculate correlation matrix for all descriptors.
    -   **Group** descriptors into clusters where |r| > 0.8 (e.g., using hierarchical clustering).
    -   **VIF Diagnostic**: Calculate VIF for diagnostic reporting, but **DO NOT remove features** based on VIF > 5.0.
    -   **Signal Attribution**: Use **SHAP Interaction Values** to attribute importance within clusters. The "strongest signal" is defined as the **cluster** with the highest aggregate SHAP value. Features within a cluster are reported as a group.
-   **Stability Check (Two-Stage Bootstrap)**:
    -   **Stage 1**: Train a single robust model on the full dataset.
    -   **Stage 2**: Perform 100 bootstrap iterations by **resampling data points and recalculating SHAP values only** (no re-training). This ensures runtime feasibility (<6h).
    -   **Metric**: Calculate Jaccard similarity of the **top 10 feature clusters** across resamples.
    -   **Threshold**: Jaccard ≥ 0.7 required to claim cluster stability (FR-005).
    -   **Fallback**: If Stage 2 exceeds time limits, reduce to 20 iterations and log the rationale.

## Statistical Rigor & Limitations

-   **Multiple Comparisons**: SHAP feature importance is exploratory; no strict family-wise error correction is applied to the ranking itself, but the stability bootstrap (100 resamples) serves as a robustness check against overfitting to a single split.
-   **Sample Size/Power**: The effective sample size is the number of molecules in the QM9 subset used. A pre-study power analysis will confirm N is sufficient to detect an MDES of 0.2 for cluster stability.
-   **Causal Inference**: This is an **observational study**. The model predicts association, not causation. Claims will be framed as "predictive power of 2D topology" rather than "causal mechanism."
-   **Measurement Validity**: Dipole moments (`mu`) are derived from high-level quantum mechanical calculations (QM9 standard), providing a valid ground truth. 2D descriptors are standard topological indices with established chemical meaning.
-   **Collinearity**: Addressed via **Cluster-Aware SHAP**. Features in a correlated cluster are reported as a group, with the total cluster importance and the distribution of credit described descriptively.

## Decision Rationale (Compute Feasibility)

-   **LightGBM vs. Deep Learning**: LightGBM is chosen for its speed, CPU efficiency, and ability to handle tabular data (descriptors) effectively. Deep learning (GNNs) would require GPU or excessive CPU time and is not necessary for this specific 2D descriptor task.
-   **Sampling**: If the full QM dataset causes memory pressure during the 200+ descriptor calculation, a random sample of molecules will be used. This ensures the pipeline runs within the available memory constraints.
-   **Bootstrap Cost**: 100 full re-trains are computationally prohibitive. The **Two-Stage Bootstrap** (SHAP-only resampling) is selected to meet the 6h runtime constraint while preserving statistical validity for feature stability. This approach is standard for tree-based models where SHAP calculation is significantly faster than training.

## References

-   **QM9 Dataset**: https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet
-   **LightGBM**: https://lightgbm.readthedocs.io/
-   **SHAP**: https://shap.readthedocs.io/
-   **RDKit**: https://www.rdkit.org/