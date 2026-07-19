# Data Model: Molecular Property Prediction Pipeline

## Input Schema

### Raw Data (PubChem)

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `cid` | int | PubChem Compound ID | PubChem |
| `smiles` | str | Isomeric SMILES string | PubChem |
| `logp` | float | XLogP3 or Experimental value | PubChem |
| `solubility` | float | Aqueous solubility (logS) | PubChem |
| `boiling_point` | float | Boiling point (K) | PubChem |
| `molecular_weight` | float | Molecular weight (g/mol) | PubChem |
| `property_type` | str | "Experimental" or "Computed" | PubChem |
| `measurement_uncertainty` | float | **Optional/Derived**: Confidence score or null | PubChem (if available) |
| `quantity_of_substance` | float | **Optional/Derived**: Amount (if available) or null | PubChem (if available) |
| `source` | str | "PubChem" | Metadata |
| `confidence` | str | "High", "Medium", "Low" | PubChem |

### Derived Data (Preprocessing)

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `missing_covariates` | list[str] | **Derived**: List of missing metadata (e.g., "pH", "temperature", "Experimental flag") | `preprocess.py` |

### Intermediate Data (Fingerprints)

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | str | Isomeric SMILES string |
| `maccs` | list[int] | MACCS fingerprint (166 bits) |
| `ecfp4` | list[int] | ECFP4 fingerprint (1024 bits) |
| `fp2` | list[int] | FP2 fingerprint (1024 bits) |

### Output Data (Predictions)

| Field | Type | Description |
|-------|------|-------------|
| `cid` | int | PubChem Compound ID |
| `smiles` | str | Isomeric SMILES string |
| `target` | float | Experimental value (LogP, Solubility, BP) |
| `baseline_pred` | float | Crippen prediction |
| `rf_pred` | float | Random Forest prediction |
| `baseline_error` | float | Absolute error (baseline) |
| `rf_error` | float | Absolute error (RF) |
| `shap_values` | list[float] | SHAP values for each fingerprint bit |
| `shap_interaction` | list[list[float]] | SHAP interaction values |
| `local_non_additivity_index` | float | **Derived**: Correlation of residual difference with substructure presence | `stats.py` |

## Data Flow

1.  **Download**: `code/data/download.py` fetches raw data from PubChem, **filtering for 'Experimental' values** where possible, and saves to `data/raw/`.
2.  **Preprocess**: `code/data/preprocess.py` cleans data, handles missing values, **derives `missing_covariates`** by checking for absence of metadata, and logs quality metrics to `data/derived/data_quality_report.csv`.
3.  **Fingerprint**: `code/data/fingerprint.py` generates fingerprints and saves to `data/processed/`.
4.  **Baseline**: `code/models/baseline.py` computes Crippen predictions and saves to `data/derived/baseline_predictions.csv`.
5.  **Model**: `code/models/rf.py` trains Random Forest and saves predictions to `data/derived/`.
6.  **Analysis**: `code/analysis/stats.py` computes metrics, performs Wilcoxon test, **computes Local Non-Additivity Index**, and generates plots.
7.  **Explainability**: `code/analysis/explainability.py` computes SHAP values, **maps bits to substructures via RDKit SMARTS**, and saves plots.

## Data Hygiene

- **Checksums**: All files in `data/raw/` are checksummed.
- **Immutability**: Raw data is never modified; derivations are written to new files.
- **Logging**: `data_quality_report.csv` logs all missing covariates (metadata absence) and excluded entries.

## Metadata

- `data/raw/dataset_metadata.json`: Contains source, download date, confidence, experimental conditions, and **property type distribution** (Experimental vs. Computed).