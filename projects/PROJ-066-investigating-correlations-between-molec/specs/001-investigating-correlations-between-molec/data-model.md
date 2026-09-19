# Data Model: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

## 1. Entity Definitions

### 1.1 Molecule
Represents a single chemical compound in the analysis.

*   **smiles**: `string` - Canonical SMILES representation.
*   **target_value**: `float` - The measured value (e.g., Bioavailability %, Papp, Clearance).
*   **target_type**: `string` - One of: "bioavailability", "permeability", "clearance".
*   **descriptors**: `object` - Dictionary of calculated 2D descriptors.
    *   `logP`: `float`
    *   `TPSA`: `float`
    *   `MW`: `float`
    *   `rotatable_bonds`: `int`
    *   `h_bond_donors`: `int`
    *   `h_bond_acceptors`: `int`
    *   `ring_count`: `int`
*   **metadata**: `object`
    *   `assay_date`: `string` (ISO 8601)
    *   `source_id`: `string` (Original ChEMBL ID)

### 1.2 ModelArtifact
Represents a trained statistical model.

*   **model_id**: `string` - Unique identifier (e.g., "RF-bioavailability-20260920").
*   **model_type**: `string` - "LinearRegression" or "RandomForest".
*   **target_variable**: `string` - The target it predicts.
*   **metrics**: `object`
    *   `rmse`: `float`
    *   `pearson_r`: `float`
    *   `r_squared`: `float`
*   **feature_importance**: `array` - List of `{feature: string, importance: float}`.

## 2. Data Flow

1.  **Raw Input**: SQLite file from ChEMBL 33.
2.  **Sanitized**: Rows with invalid SMILES or missing targets removed.
3.  **Deduplicated**: Duplicate SMILES resolved per FR-009.
4.  **Pre-Sampled**: Validation checks row counts per target.
5.  **Sampled**: Stratified random sample of a large number of rows.
6.  **Processed**: `preprocess.py` calculates descriptors and outputs `molecules_processed.csv` (flat structure).
7.  **Split**: Train (majority) / Test (minority) CSVs.
8.  **Output**: Model artifacts (`.pkl`) and Plot images (`.png`).

## 3. Storage Layout

```text
data/
├── raw/
│   └── ChEMBL_33.sqlite.gz           # Unmodified download
├── processed/
│   ├── molecules_processed.csv       # Sanitized, deduplicated, sampled, with descriptors
│   ├── train.csv                     # Training split
│   ├── test.csv                      # Test split
│   ├── model_rf_bio.pkl              # Random Forest model
│   ├── model_lr_bio.pkl              # Linear Regression model
│   └── metrics_summary.json          # Aggregated metrics
└── plots/
    ├── pred_vs_exp_bio.png           # Scatter plot
    └── feature_importance_bio.png    # Bar chart
```

## 4. Constraints & Validation

*   **SMILES Validity**: Must pass `rdkit.Chem.MolFromSmiles`.
*   **Numeric Types**: All descriptors must be finite floats (no `NaN`, `Inf`).
*   **Target Range**: Experimental values must be within physical bounds (e.g., Bioavailability 0-100%).
*   **Memory**: Processed CSV must be < 500MB to allow safe loading into RAM for training.
*   **Schema Compliance**: `molecules_processed.csv` must strictly adhere to `contracts/molecule.schema.yaml`.