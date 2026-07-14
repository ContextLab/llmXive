# Data Model: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Overview
This document defines the data structures, schemas, and transformations used in the project. It ensures that all data artifacts adhere to the project's Constitution (Data Hygiene, Reproducibility).

## Data Flow Diagram

```mermaid
graph TD
    A[Raw QM9 Parquet] -->|Download & Checksum| B(data/raw/qm9_full.parquet)
    B -->|Parse SMILES, Calc 2D Descriptors| C[Feature Matrix (CSV/Parquet)]
    C -->|Correlation Clustering, NaN Imputation| D[Clustered Feature Matrix]
    D -->|Train/Test Split| E[Train Set]
    D -->|Train/Test Split| F[Test Set]
    E -->|LightGBM Training| G[Model Artifact (.pkl)]
    G -->|Cluster-Aware SHAP Analysis| H[SHAP Values (JSON/Parquet)]
    H -->|Bootstrap Stability (SHAP-only)| I[Stability Report (JSON)]
```

## Entity Definitions

### 1. Molecule (Raw)
-   **Source**: QM9 Parquet
-   **Fields**:
    -   `smiles` (string): Canonical SMILES representation.
    -   `mu` (float): Dipole moment in Debye.
    -   `mol_id` (string): Unique identifier (if available).

### 2. Descriptor Row (Processed)
-   **Source**: `code/data/preprocess_2d.py`
-   **Fields**:
    -   `mol_id` (string): Foreign key to raw molecule.
    -   `smiles` (string): Input SMILES.
    -   `mu` (float): Target variable.
    -   `desc_001` ... `desc_N` (float): 2D topological descriptors (e.g., `MolWt`, `NumRotBonds`, `NumHDonors` - excluding TPSA/3D).
    -   `cluster_id` (string): ID of the correlation cluster this descriptor belongs to (assigned post-calculation).
    -   `status` (string): "valid", "nan_imputed", "skipped_malformed".

### 3. Model Output
-   **Source**: `code/models/evaluate.py`
-   **Fields**:
    -   `mol_id` (string): Molecule ID.
    -   `mu_true` (float): Actual dipole moment.
    -   `mu_pred` (float): Predicted dipole moment.
    -   `residual` (float): `mu_true - mu_pred`.
    -   `shap_values` (array): Array of SHAP values for each feature.
    -   `cluster_shap_values` (array): Array of aggregated SHAP values for each cluster.

## Data Constraints

-   **No 3D Data**: No fields representing coordinates (x, y, z) or 3D conformers.
-   **No TPSA**: No fields named `TPSA`, `TPSA_E`, or similar.
-   **No Functional Groups**: No fields representing SMARTS counts for specific groups.
-   **No VIF Pruning**: All features are retained; VIF is used only for clustering diagnostics.
-   **NaN Handling**: All missing values in the feature matrix must be imputed with the median of the training set.

## File Naming Convention

-   Raw: `data/raw/qm9_full.parquet`
-   Processed: `data/processed/features_{timestamp}.parquet`
-   Models: `models/lightgbm_{timestamp}.pkl`
-   Reports: `reports/shap_stability_{timestamp}.json`