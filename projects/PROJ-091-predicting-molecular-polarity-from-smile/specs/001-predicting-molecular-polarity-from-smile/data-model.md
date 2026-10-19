# Data Model: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Data Flow Overview
1. **Raw QM9 Ingestion** – `code/data/fetch.py` → `data/raw/qm9_raw.parquet`.  
2. **2‑D Descriptor Generation** – `code/data/preprocess.py` → `data/processed/descriptors.parquet`.  
3. **Feature Selection & Clustering** – `code/data/feature_selection.py` → `data/processed/vif_scores.csv`, `data/processed/cluster_map.csv`.  
4. **Model Artifact** – `code/model/train.py` → `data/processed/model.pkl`.  
5. **Analysis Outputs** – `code/model/evaluate.py` → `data/results/shap_summary.png`, `data/results/stability_report.json`.  

## Schema Definitions

### 1. Raw QM9 (`data/raw/qm9_raw.parquet`)
| Field | Type | Description |
|-------|------|-------------|
| `Index` | integer | Unique row identifier. |
| `SMILES` | string | Canonical SMILES. |
| `Dipole_debye` | float | Target dipole moment magnitude (Debye). |
| *(additional QM9 fields omitted for brevity)* | | |

*Constraints*: No 3‑D coordinates; TPSA not required.

### 2. Descriptor Matrix (`data/processed/descriptors.parquet`)
| Column | Type | Description |
|--------|------|-------------|
| `SMILES` | string | Identifier (matches raw). |
| `Dipole_debye` | float | Target variable. |
| `Desc_0 … Desc_N` | float | ≥ 200 2‑D topological descriptors (TPSA, SMARTS excluded). |
| `is_valid` | boolean | True if all descriptors computed (no NaNs after imputation). |
| `stereochemistry_flag` | boolean | True if original SMILES lacked stereochemistry and was normalized. |
| `flexible_flag` | boolean | True if rotatable‑bond count ≥ 5. |

*Constraints*: No 3‑D coordinates; no TPSA; no NaNs (imputed or dropped); ≥ 200 descriptor columns.

### 3. VIF Scores (`data/processed/vif_scores.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `feature_name` | string | Descriptor name. |
| `vif_score` | float | Calculated VIF. |
| `removed` | boolean | True if pruned due to VIF > 5.0. |
| `fallback_triggered` | boolean | True if L1 regularization was activated (global flag). |

### 4. Cluster Map (`data/processed/cluster_map.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `feature_name` | string | Descriptor name. |
| `cluster_id` | string | ID of hierarchical cluster (Ward linkage on correlation matrix). |

### 5. Model Artifact (`data/processed/model.pkl`)
- **Type**: Pickled LightGBM `Booster`.  
- **Contains**: Trained trees, feature names, hyper‑parameters, training metadata (seed, CV scores).

### 6. Stability Report (`data/results/stability_report.json`)
```json
{
  "bootstrap_count": 100,
  "resample_strategy": "Full dataset resampling, A large (thousand‑scale) subsample per iteration.",
  "jaccard_similarity": "[deferred]",
  "top_features": ["Desc_42", "Desc_87", "..."],
  "stability_status": "[deferred]"
}
```
*Fields*: Jaccard similarity of top‑10 SHAP features across bootstraps; list of stable features; status (“stable” if ≥ 0.7).

## Data Hygiene & Validation
- **Checksums**: SHA‑256 hashes for every file in `data/processed/` stored in `state/manifest.json`.  
- **Validation Script** (`code/data/validate.py`): Loads each artifact, checks column counts/types against the schemas above, and verifies checksum matches.  
- **Imputation Policy**: Median imputation for descriptor NaNs; records with > 5 % missing descriptors are dropped, with a log entry.  

## Contract Validation Mapping
| Contract File | Pipeline Step | Validation Action |
|---------------|---------------|-------------------|
| `contracts/dataset.schema.yaml` | `code/data/fetch.py` (post‑download) | `validate.py` checks raw QM9 metadata against the schema. |
| `contracts/descriptor_schema.schema.yaml` | `code/data/preprocess.py` | `validate.py` confirms descriptor matrix shape, exclusion rules, and column metadata. |
| `contracts/vif_schema.schema.yaml` | `code/data/feature_selection.py` | `validate.py` verifies VIF scores, fallback flag, and descriptor count. |
| `contracts/features.schema.yaml` | `code/data/preprocess.py` (post‑processing) | `validate.py` ensures each record conforms to the feature schema (flags, imputation status). |
| `contracts/model_output.schema.yaml` | `code/model/train.py` & `code/model/evaluate.py` | `validate.py` checks model artifact, predictions, and SHAP output against the schema. |
| `contracts/model_output_schema.schema.yaml` | `code/model/evaluate.py` | Additional sanity check on aggregated metrics and SHAP summary. |

---

