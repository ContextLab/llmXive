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
| `property_type` | string | Must be `"Experimental"` | PubChem |
| `measurement_uncertainty` | number or null | Optional confidence score | PubChem |
| `quantity_of_substance` | number or null | Optional amount of substance, if available | PubChem |
| `source` | string | `"PubChem"` (fixed) | Fixed |
| `confidence` | string | Derived confidence based on property_type | Derived |
| `logp_source` | string | `"Experimental"` | Derived |
| `solubility_source` | string | `"Experimental"` | Derived |
| `boiling_point_source` | string | `"Experimental"` | Derived |

*Required*: `cid`, `smiles`, `logp`, `solubility`, `boiling_point`, `property_type`, `source`, `confidence`, `logp_source`, `solubility_source`, `boiling_point_source`.

## Derived Data (Preprocessing)

| Field | Type | Description |
|-------|------|-------------|
| `missing_covariates` | list[string] | Names of absent metadata fields (e.g., `"pH"`). |
| `data_quality_report` | string (CSV) | Path to `data/derived/data_quality_report.csv` summarising missing covariate rate, low‑confidence rate, duplicate count. |
| `verification_log` | string (TXT) | Path to `data/derived/verification_log.txt`. |

## Intermediate Data (Fingerprints)

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Isomeric SMILES |
| `maccs` | list[int] (0/1) | MACCS fingerprint (standard set of bits) |
| `ecfp4` | list[int] (0/1) | ECFP fingerprint (standard configuration, using a fixed‑length bit vector) |

## Output Data (Predictions & Analyses)

| Field | Type | Description |
|-------|------|-------------|
| `cid` | integer | PubChem Compound ID |
| `smiles` | string | Isomeric SMILES |
| `target` | number | Experimental value for the property under analysis |
| `baseline_pred` | number | Additive‑fragment baseline prediction (property‑specific) |
| `rf_pred` | number | Random Forest prediction |
| `baseline_error` | number | `abs(target − baseline_pred)` |
| `rf_error` | number | `abs(target − rf_pred)` |
| `shap_values` | list[number] | SHAP value per fingerprint bit |
| `shap_interaction` | list[list[number]] | SHAP interaction matrix (saved as `.npy` file) |
| `local_non_additivity_index` | number | **Per‑molecule** LNAI score (average of significant pairwise LNAI values for that molecule). |
| `deviation_contexts` | list[object] | Rows from `deviation_contexts.csv` (see `interaction_context.schema.yaml`) |
| `validation_summary` | string (CSV) | Path to `data/derived/validation_summary.csv`. |

## Visual & Tabular Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Baseline residual plot | `data/derived/baseline_residuals.png` | MAE/RMSE residuals for additive baseline |
| RF residual plot | `data/derived/rf_residuals.png` | MAE/RMSE residuals for Random Forest |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` | Heatmap of SHAP interaction magnitudes |
| LNAI table | `data/derived/lna_index.csv` | Significant bit‑pair interaction zones (derived from `interaction_context.schema.yaml`) |
| Per‑molecule LNAI table | `data/derived/lna_index_per_molecule.csv` | Average LNAI score per molecule |
| Deviation contexts table | `data/derived/deviation_contexts.csv` | MACCS‑SMARTS mapping for all selected bits |
| Interaction‑Zone Report | `data/derived/interaction_zone_report.pdf` | Summarises statistically significant bit‑pair interactions |
| Validation Report | `data/derived/validation_report.pdf` | Expert review outcomes (≥ 2 chemists) |
| Validation Audit | `data/derived/validation_audit.pdf` | Consolidated checksum, QC, SHAP validation, mapping metrics, per‑molecule LNAI, expert review |
| Test‑set split | `data/derived/test_set.csv` | CID, outer‑fold index, test‑set flag |
| Mapping metrics (precision/recall) | `data/derived/mapping_metrics.txt` | Precision/recall of SMARTS mapping against the reference set |
| Predictions schema CSV | `data/derived/predictions_schema.csv` | Records conforming to `prediction.schema.yaml` |
| Molecules schema CSV | `data/derived/molecules_schema.csv` | Records conforming to `molecule.schema.yaml` |

All files are immutable after creation; downstream steps read‑only them.

---



