# Data Model: Brain Network Efficiency and Fluid Intelligence

## Entities and Relationships

### Subject
- **ID**: Unique subject identifier (string/int).
- **Fluid_Intelligence**: NIH Toolbox composite score (float).
- **Age**: Age in years (int/float).
- **Sex**: Sex (categorical: 'M', 'F').
- **Mean_FD**: Mean framewise displacement in mm (float).
- **Status**: 'valid', 'excluded_missing_score', 'excluded_motion'.

### Connectivity Matrix
- **Subject_ID**: Foreign key to Subject.
- **Atlas**: 'Schaefer_200', 'Schaefer_400'.
- **Density**: Threshold density (float: 0.15, 0.20, 0.25).
- **Matrix**: 2D array of Pearson correlations (positive edges only).
- **Graph**: Binary graph object (NetworkX) derived from thresholded matrix.

### Efficiency Metric
- **Subject_ID**: Foreign key to Subject.
- **Atlas**: 'Schaefer_200', 'Schaefer_400'.
- **Density**: Threshold density (float).
- **Global_Efficiency**: Global efficiency value (float).
- **Frontoparietal_Efficiency**: Frontoparietal subgraph efficiency value (float).
- **Computation_Time**: Time to compute (float, optional).

### Statistical Result
- **Test_Type**: 'correlation', 'regression', 'permutation'.
- **Metric**: 'Global_Efficiency', 'Frontoparietal_Efficiency'.
- **Density**: Threshold density (float).
- **Coefficient**: Correlation/regression coefficient (float).
- **P_Value**: Raw p-value (float).
- **P_Corrected**: FWER-corrected p-value (float).
- **CI_Lower**: Lower bound of 95% CI (float).
- **CI_Upper**: Upper bound of 95% CI (float).
- **Effect_Size**: Cohen's f² or r (float).
- **VIF**: Variance Inflation Factor for predictors (float).

## Data Flow

1. **Raw Data**: HCP rs-fMRI + behavioral scores → `data/raw/`.
2. **Preprocessed Data**: Nuisance regression + band-pass → `data/processed/time_series/`.
3. **Connectivity Matrices**: Correlation matrices → `data/processed/matrices/`.
4. **Graph Metrics**: Efficiency values → `data/results/efficiency_metrics.csv`.
5. **Statistical Outputs**: Regression/correlation tables → `data/results/statistical_results.csv`.
6. **Reports**: Figures + tables → `paper/figures/`, `paper/tables/`.

## Storage Format

- **Time Series**: `.nii.gz` (NIfTI) or `.npz` (NumPy compressed).
- **Matrices**: `.npy` (NumPy) or `.csv` (for small matrices).
- **Metrics/Stats**: `.csv` (pandas DataFrame) with columns as defined above.
- **Graphs**: `.pickle` (NetworkX object) or `.gexf` (optional).

## Data Validation Rules

- **Subject**: `Fluid_Intelligence` must be non-null; `Mean_FD` ≤ 0.5 mm.
- **Matrix**: Diagonal must be 0 (or 1 if self-loop); off-diagonal ∈ [0, 1] (positive edges only).
- **Graph**: Edge density must be within ±1% of target density.
- **Metrics**: Efficiency values must be ∈ (0, 1] (typically 0.1–0.6 for brain networks).
- **Stats**: P-values ∈ [0, 1]; VIF ≥ 1.
