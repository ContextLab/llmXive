# Data Model: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Data Flow

1. **Raw Ingestion**: `code/data/fetch.py` downloads QM9 via `qm9pack` → `data/raw/qm9_raw.parquet`.
2. **Feature Generation**: `code/data/preprocess.py` converts SMILES to 2D descriptors → `data/processed/descriptors.parquet`.
3. **Feature Selection**: `code/data/feature_selection.py` computes VIF, iteratively removes high-VIF features (with L1 fallback if < 50 features remain), and performs Hierarchical Clustering (Ward linkage) → `data/processed/vif_scores.csv` and `data/processed/cluster_map.csv`.
4. **Model Training**: `code/model/train.py` trains LightGBM → `data/processed/model.pkl`.
5. **Analysis**: `code/model/evaluate.py` runs SHAP (with interaction values) and Bootstrap Stability (resamples from full dataset, A subsample per iteration) → `data/results/shap_summary.png`, `data/results/stability_report.json`.

## Schema Definitions

### 1. Raw QM9 Data (`data/raw/qm9_raw.parquet`)
- **Source**: `qm9pack.get_data('qm9')`
- **Key Fields**:
  - `SMILES`: String
  - `mu`: Float (Target, scalar magnitude of dipole moment in Debye)
  - `Index`: Integer
  - `Stoichiometry`: String

### 2. Descriptor Matrix (`data/processed/descriptors.parquet`)
- **Rows**: Molecules (filtered for valid SMILES and no NaNs).
- **Columns**:
  - `SMILES`: String (Identifier)
  - `mu`: Float (Target, scalar magnitude)
  - `Desc_0` ... `Desc_N`: Float (2D topological descriptors, N ≥ 200)
- **Constraints**:
  - No 3D coordinates.
  - No TPSA.
  - No NaNs (imputed or dropped).
  - **No High-Correlation Exclusion**: All features retained.

### 3. VIF Scores (`data/processed/vif_scores.csv`)
- **Columns**:
  - `feature_name`: String
  - `vif_score`: Float
  - `removed`: Boolean (True if VIF > 5.0 and feature count > 50)
  - `fallback_triggered`: Boolean (True if L1 regularization was used)

### 4. Cluster Map (`data/processed/cluster_map.csv`)
- **Columns**:
  - `feature_name`: String
  - `cluster_id`: String (ID of the correlation cluster)
- **Algorithm**: Hierarchical Clustering with Ward linkage on the correlation matrix.

### 5. Model Output (`data/processed/model.pkl`)
- **Type**: Pickled LightGBM Booster object.
- **Attributes**: Hyperparameters, feature names, tree structure.

### 6. Stability Report (`data/results/stability_report.json`)
- **Structure**:
  - `bootstrap_count`: Integer (100)
  - `resample_strategy`: String ("Full dataset resampling, 10k subsample per iteration")
  - `jaccard_similarity`: Float (≥ 0.7 target)
  - `top_features`: List of strings (consistent across bootstraps)
  - `stability_status`: String ("stable" or "unstable")
- **Calculation**: Jaccard similarity of the top features across bootstrap resamples.

## Data Hygiene & Validation
- **Checksums**: All files in `data/processed/` are checksummed (SHA-256) and stored in `state/manifest.json`.
- **Validation**: `code/data/validate.py` checks column counts and types against the schema before training.
- **Imputation**: Missing descriptor values are imputed with the median of that column. If >5% missing, the record is dropped.