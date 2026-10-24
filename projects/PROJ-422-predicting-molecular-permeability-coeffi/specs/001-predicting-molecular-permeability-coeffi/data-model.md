# Data Model: Molecular Permeability Prediction

## 1. Overview
Defines JSON‑Schema contracts for raw ingestion, processed intermediate representations, and model output. All files are validated against the schemas located in `contracts/`.

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

### 2.3 Model Prediction Record *(conforms to `contracts/results.schema.yaml`)*  
| Field | Type | Description |
|-------|------|-------------|
| `molecule_id` | string | Unique identifier (e.g., row index) |
| `true_value` | number | Ground‑truth target (permeability) |
| `predicted_gnn` | number | GNN regression output |
| `predicted_rf` | number | RF baseline output |
| `predicted_rf_ablation` | number | RF trained on graph stats only |
| `error_gnn` | number | `predicted_gnn – true_value` |
| `error_rf` | number | `predicted_rf – true_value` |

## 3. Transformation Workflow
1. **Download** raw files → `data/raw/` (checksum verified).  
2. **Preprocess** (`code/data/preprocess.py`):  
   - Parse SMILES → graph; compute descriptors.  
   - Set `mol_valid`; drop rows where `mol_valid=False`.  
 - Write `data/processed/processed_data.parquet` **before** applying the [deferred] retention guard.
   - If the guard fails, the script exits with a non‑zero code **after** the file exists, satisfying the unit test.  
   - Rows with `target` = null are excluded from modeling later.  
3. **Split** (`code/data/split.py`): produce `train.parquet` and `test.parquet` under `data/processed/` (only rows with non‑null `target`).  
4. **Model Training** → serialize models under `code/models/`.  
5. **Evaluation** → write `results/metrics.json` (validated against `contracts/results.schema.yaml`).  
6. **Interpretability** → write PNG/HTML under `results/interpretability/`.

## 4. Constraints
- No NaNs in any numeric column of the processed dataset.  
- Graph construction must be a faithful RDKit conversion (Constitution VI).  
- **Target column must be experimental permeability**; if absent, the pipeline stops before modeling (Constitution VII).

---
