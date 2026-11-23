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
| `target_type` | string | "experimental" if the target column is a true experimental permeability measurement; "surrogate" if it is an approved surrogate (e.g., simulated permeability) that has passed the independence verification (max |r| < 0.5). |

**Required fields**: `smiles`, `mol_valid`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds`, `target`, `polymer_type_onehot`, `target_type`. No additional properties are allowed.

### 2.3 Model Artifacts
- `code/models/gnn.pt` – checkpoint of the trained MPNN.  
- `code/models/rf.pkl` – serialized `RandomForestRegressor`.  

### 2.4 Evaluation Results *(conforms to `contracts/results.schema.yaml`)*  
Includes `gnn_metrics`, `rf_metrics`, `statistical_test`, `normality_test`, `power_analysis`, `bias_check`, and `interpretability_overlap`.

### 2.5 Training Log *(conforms to `contracts/training_log.schema.yaml`)*  
Records model identifier, start/end timestamps, total wall‑clock time (must be < 6 h for CI compliance), planned sample size for power, achieved power, and a `sufficient` flag.

## 3. Transformation Workflow
1. **Download** raw files → `data/raw/` (checksum‑verified).  
2. **Preprocess** (`code/data/preprocess.py`):  
   - Parse SMILES with `rdkit.Chem.MolFromSmiles`; set `mol_valid`; drop rows where `mol_valid=False`.  
 - Apply **retention Guard**: require **≥ 95 %** valid molecules; abort if < 95 % (FR‑012).  
   - If a surrogate target is approved, record `target_type` as `"surrogate"` and store the surrogate column as `target`.  
   - Compute MW, logP, TPSA, HBA, HBD, rotatable bonds, and one‑hot `polymer_type` (if present).  
   - Write `data/processed/processed_data.parquet` **and** `processed_data.csv` (validated against `contracts/dataset.schema.yaml`).  
3. **Split** (`code/data/split.py`): generate 5‑fold stratified CV splits and a hold‑out test set **only when a non‑null `target` column exists**. Store both Parquet and CSV versions under `data/processed/`.  
4. **Model Training** (`code/models/gnn.py`, `code/models/rf.py`): serialize models; each training run appends an entry to `results/training_log.json` (including `total_hours`, `planned_sample_size`, `achieved_power`, `sufficient`) for each model, and the power‑analysis gate prevents aborts due to insufficient power.  
5. **Evaluation** (`code/analysis/evaluate.py`): compute RMSE, MAE, R² for both models, normality test, paired test on per‑sample errors, bias assessment (max |r| reported, `is_confounded` flag set when >0.6). Write `results/metrics.json` (validated against `contracts/results.schema.yaml`).  
6. **Interpretability** (`code/analysis/explain.py`): generate SHAP bar charts, GNNExplainer heatmaps, and **empirical overlap metric** (correlation‑based mapping + count of overlapping top‑5 features) producing `overlap_top5` and `overlap_meets_threshold` as required by the schema.  

## 4. Constraints
- No NaNs in any numeric column of the processed dataset.  
- Graph construction must be a faithful RDKit conversion (Constitution VI).  
- **Target column must be experimental permeability**; if absent, a surrogate may be used **only when it passes the independence verification (max |r| < 0.5)** and is sourced from a validated simulation study. Otherwise, the pipeline halts, preserving scientific rigor (Constitution VII).

---



