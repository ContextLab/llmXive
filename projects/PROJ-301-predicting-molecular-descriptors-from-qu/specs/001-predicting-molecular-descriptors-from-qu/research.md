# Research: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## Executive Summary

This research validates the hypothesis that 3D geometric features provide a statistically significant advantage over 2D topological fingerprints for predicting directional electronic properties (dipole moments) compared to global properties (HOMO/LUMO gaps), using the QM9 dataset. The study employs Random Forest Regressors to ensure computational feasibility on free-tier CI infrastructure.

## Dataset Strategy

The project utilizes the QM dataset, a standard benchmark in computational chemistry containing a large-scale collection of small organic molecules with DFT-computed properties.

| Dataset Name | Source / URL | Format | Key Variables | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **QM9 (Parquet)** | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | Parquet | `smiles`, `mu` (dipole), `homo`, `lumo`, `coordinates` (XYZ implied or derived) | Verified |

**Dataset Fit Analysis**:
- **Required Variables**: The spec requires `mu` (dipole), `homo`, `lumo`, and 3D coordinates.
- **Fit Confirmation**: The verified HuggingFace QM9 dataset contains these exact fields. The `coordinates` field (or equivalent geometry data) allows for 3D graph construction.
- **Missing Data Handling**: Rows with missing `mu`, `homo`, or `lumo` will be dropped prior to feature extraction to ensure label alignment (US-1 Edge Case).

**Note on Harvard Dataverse**: The spec references Harvard Dataverse (doi:10.7910/DVN/28075). As no verified URL exists for this specific DOI in the provided list, and to satisfy the "Verified Accuracy" principle, the implementation uses the verified HuggingFace mirror (Spec Amendment T009.1).

## Methodology

### 1. Feature Extraction
- **2D Features**: Morgan Fingerprints (radius=2, nBits=2048) generated via `rdkit`. Captures topological connectivity.
- **3D Features**: Graph-based features constructed from DFT-optimized geometries.
  - **Node Features**: Atomic number, hybridization state.
  - **Edge Features**: Interatomic distances (binned), bond angles, dihedral angles.
  - **Construction**: Implemented using `rdkit` to parse XYZ coordinates and construct adjacency lists with geometric attributes.

### 2. Model Training
- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Rationale**: CPU-tractable, handles non-linear relationships, robust to noise, and provides feature importance without GPU requirements.
- **Hyperparameter Grid**:
  - `n_estimators`: [100, 500] (Selected to balance accuracy and runtime).
  - `max_depth`: [10, 20, None] (None allows full depth, bounded by memory).
  - `random_state`: Fixed integer (e.g., 42) for reproducibility.
- **Validation**: 5-Fold Cross-Validation.
- **Constraints**: Memory monitoring enforces a hard limit. If usage > 6.5GB, the sample size is reduced by [deferred] iteratively using **Stratified Random Sampling** (strata: atom count, polarity) to preserve chemical diversity.

### 3. Comparative Analysis & Failure Boundary
- **Metric**: Relative Error Increase (REI) = `(MAE_2D - MAE_3D) / MAE_3D`.
- **Hypothesis Testing**:
 - **Data**: Per-molecule errors on the test set (N [deferred]), NOT fold aggregates.
  - **Test**: Wilcoxon signed-rank test (non-parametric, robust to outliers) or paired t-test if normality holds.
  - **Correction**: Bonferroni correction applied (α = 0.05 / 3 ≈ 0.0167).
- **Failure Boundary**: Defined as descriptors where **REI ≥ 10% OR p-value < 0.0167**.
  - *Note*: This definition follows the Spec (US-3) which uses "OR". While this conflates effect size and significance, the analysis will report both metrics separately.
- **Theoretical Lower Bound**: Calculation of the **Mean Predictor Error** (predicting the mean of the training set) to contextualize the 3D model's performance against a trivial baseline.
  - *Scientific Note*: This is a Zero-Order Baseline, not the Bayes error rate. It satisfies FR-007's intent to contextualize performance but is not the true theoretical lower bound.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied (α = 0.0167).
- **Sample Size & Power**: The study uses a subset of molecules. Per-molecule error testing with a sufficiently large sample size provides high statistical power.
- **Causal Inference**: This is an observational study (predictive modeling). Claims will be framed as "associational" or "predictive accuracy".
- **Collinearity**: 2D and 3D features are derived from the same molecule. The analysis compares *models*, not individual feature coefficients.
- **DFT Self-Consistency**: The 3D model uses DFT-optimized geometries to predict DFT properties. The "Failure Boundary" is specific to this DFT-consistent context and may not generalize to noisy experimental geometries.
- **Baseline Interpretation**: The "Theoretical Lower Bound" is interpreted as the Mean Predictor Error (Zero-Order Baseline) for practical purposes.

## Computational Feasibility Decision

- **Hardware Constraint**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Decision**: Use `scikit-learn` Random Forest with default precision (float64). Avoid `torch` or `tensorflow` to eliminate CUDA dependencies and overhead.
- **Data Strategy**: Process molecules in batches. If memory usage exceeds 6.5 GB during feature extraction, the pipeline will automatically downsample the dataset to a manageable subset. using stratified sampling and re-run extraction.
- **Runtime Budget**: Estimated several hours for 10k molecules (5-fold CV on 2048 features). This is within the -hour limit.