# Data Model: Molecular Permeability Prediction

## 1. Overview
Defines JSON‑Schema contracts for raw ingestion, processed intermediate representations, model predictions, evaluation results, and training logs. All files are validated against the schemas located in `contracts/`.

## 2. Entities

### 2.1 Raw Molecule Record
| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | SMILES notation of the molecule |
| `polymer_type` | string / null | Optional stratification label |
| `permeability` | number / null | Experimental permeability coefficient (may be missing in open datasets) |
| `logp` | number / null | Calculated LogP (present in some descriptor datasets) |

### 2.2 Processed Molecule Record *(conforms to `contracts/dataset.schema.yaml`)*  
| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Original SMILES |
| `mol_valid` | boolean | `True` if RDKit parsed successfully |
| `mw` | number | Molecular Weight |
| `logp` | number | Calculated LogP |
| `tpsa` | number | Topological Polar Surface Area |
| `hba` | integer | Number of Hydrogen Bond Acceptors |
| `hbd` | integer | Number of Hydrogen Bond Donors |
| `rotatable_bonds` | integer | Number of Rotatable Bonds |
| `target` | number / null | Experimental permeability coefficient if available; null otherwise |
| `polymer_type` | string / null | Polymer type for stratification (optional) |
| `polymer_type_onehot` | object | One‑hot encoding of polymer type (key = type, value = 0 or 1) |
| `target_type` | string | `"experimental"` if the target column is a true experimental permeability measurement; `"surrogate"` if it is an approved surrogate (e.g., simulated permeability). |
| `target_surrogate` | string / null | **[DEPRECATED]** Previously allowed surrogate target; **removed** from schema to enforce experimental target only. |

**NOTE**: The `target_surrogate` field is retained here only for documentation of the deprecation; it is **not required** and is omitted from the JSON‑Schema (see `contracts/dataset.schema.yaml`). All pipelines must produce a `target` column; surrogate targets are accepted **only** when `target_type` is `"surrogate"` and the source is a validated simulation study.

required:
  - smiles
  - mol_valid
  - mw
  - logp
  - tpsa
  - hba
  - hbd
  - rotatable_bonds
  - target
  - polymer_type_onehot
  - target_type

additionalProperties: false

## 3. Transformation Workflow
1. **Download** raw files → `data/raw/` (checksum verified).  
2. **Preprocess** (`code/data/preprocess.py`):  
   - Parse SMILES → graph; compute descriptors.  
   - Set `mol_valid`; drop rows where `mol_valid=False`.  
   - Apply retention guard (≥ 95 % valid); if guard fails, attempt canonicalization and abort if still below threshold.  
   - If a surrogate target is approved (historical note only), record its name in `target_surrogate` **but do not use it** for model training; instead, the pipeline will set `target_type` to `"surrogate"` and use the column as `target`.  
   - Write `data/processed/processed_data.parquet` **and** `processed_data.csv` (validated against `contracts/dataset.schema.yaml`).  
3. **Split** (`code/data/split.py`): generate 5‑fold stratified CV splits and a hold‑out test set (only when a non‑null target exists). Store both Parquet and CSV versions under `data/processed/`.  
4. **Model Training** (`code/models/gnn.py`, `code/models/rf.py`): serialize models; each training run appends an entry to `results/training_log.json`.  
5. **Evaluation** (`code/analysis/evaluate.py`): compute metrics, normality test, paired test on per‑sample errors, bias check; write `results/metrics.json` (validated against `contracts/results.schema.yaml`).  
6. **Interpretability** (`code/analysis/explain.py`): generate SHAP bar charts, GNNExplainer heatmaps, and overlap metric; store visualizations under `results/interpretability/`.  

## 4. Constraints
- No NaNs in any numeric column of the processed dataset.  
- Graph construction must be a faithful RDKit conversion (Constitution VI).  
- **Target column must be experimental permeability**; if absent, a surrogate may be used **only if** it is a validated simulation-derived measure and is flagged via `target_type`. Otherwise, the pipeline halts (Constitution VII).  

---



