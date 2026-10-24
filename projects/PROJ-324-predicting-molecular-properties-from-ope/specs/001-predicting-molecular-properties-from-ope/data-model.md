# Data Model: Molecular Property Prediction Pipeline

## Input Schema (Raw PubChem)

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `cid` | integer | PubChem Compound ID | PubChem |
| `smiles` | string | Isomeric SMILES | PubChem |
| `logp` | number | Experimental logP | PubChem |
| `solubility` | number | Experimental aqueous solubility (logS) | PubChem |
| `boiling_point` | number | Experimental boiling point (K) | PubChem |
| `molecular_weight` | number | Molecular weight (g/mol) | PubChem |
| `property_type` | string | `"Experimental"` (only) | PubChem |
| `measurement_uncertainty` | number or null | Optional confidence score from PubChem | PubChem |
| `quantity_of_substance` | number or null | Optional amount, if present | PubChem |
| `source` | string | `"PubChem"` | Fixed |
| `confidence` | string | `"High"` / `"Medium"` / `"Low"` (derived from `property_type`) | Derived |
| `logp_source` | string | Must be `"Experimental"` | Derived / verification |
| `solubility_source` | string | Must be `"Experimental"` | Derived / verification |
| `boiling_point_source` | string | Must be `"Experimental"` | Derived / verification |

*Required*: `cid`, `smiles`, `logp`, `solubility`, `boiling_point`, `property_type`, `source`, `confidence`, `logp_source`, `solubility_source`, `boiling_point_source`.

## Derived Data (Preprocessing)

| Field | Type | Description |
|-------|------|-------------|
| `missing_covariates` | list[string] | Names of absent metadata (e.g., `"pH"`, `"temperature"`). Produced by `preprocess.py`. |
| `data_quality_report` | string (CSV) | Path to `data/derived/data_quality_report.csv` summarising missing covariates and experimental‑data ratio. |
| `verification_log` | string (TXT) | Path to `data/derived/verification_log.txt` documenting URL verification outcomes. |

## Intermediate Data (Fingerprints)

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Isomeric SMILES |
| `maccs` | list[int] (0/1) | Standard MACCS fingerprint (full‑length fingerprint) |
| `ecfp4` | list[int] (0/1) | Fixed‑length ECFP fingerprint (standard fixed length, hashed) |
| `fp2` | list[int] (0/1) | Fixed‑length hashed fingerprint (of appropriate length) |

## Output Data (Predictions & Analyses)

| Field | Type | Description |
|-------|------|-------------|
| `cid` | integer | PubChem Compound ID |
| `smiles` | string | Isomeric SMILES |
| `target` | number | Experimental value for the property under analysis |
| `baseline_pred` | number | Additive baseline prediction (property‑specific) |
| `rf_pred` | number | Random Forest prediction |
| `baseline_error` | number | `abs(target − baseline_pred)` |
| `rf_error` | number | `abs(target − rf_pred)` |
| `shap_values` | list[number] | SHAP value per fingerprint bit |
| `shap_interaction` | list[list[number]] | SHAP interaction matrix (saved as .npy file) |
| `local_non_additivity_index` | number | LNAI score for a molecule |
| `deviation_contexts` | list[object] | Rows from `deviation_contexts.csv` (see `interaction_context.schema.yaml`) |
| `validation_summary` | string (CSV) | Path to `data/derived/validation_summary.csv` collating key audit metrics. |

## Visual Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Baseline residual plot | `data/derived/baseline_residuals.png` | MAE/RMSE residuals for additive baseline |
| RF residual plot | `data/derived/rf_residuals.png` | MAE/RMSE residuals for Random Forest |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` | Heatmap of SHAP interaction values |
| LNAI table | `data/derived/lna_index.csv` | Significant bit‑pair interaction zones (derived from `interaction_context.schema.yaml`) |
| Deviation contexts table | `data/derived/deviation_contexts.csv` | MACCS‑SMARTS mapping for top‑K bits |
| Validation summary | `data/derived/validation_summary.csv` | Consolidated checksum, data‑quality, verification, residuals, LNAI, SHAP validation summary |
| Test‑set split | `data/derived/test_set.csv` | CID, outer‑fold assignment, test‑set flag |

All files are immutable after creation; subsequent steps read‑only them.

---


