# Data Model: Molecular Permeability Prediction (Proxy)

## 1. Overview
Defines schemas for raw ingestion, processed intermediate representations, and model output. All files are validated against JSON‑Schema contracts located in `contracts/`.

## 2. Entities

### 2.1 Raw Molecule Record
| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | SMILES notation (source). |
| `polymer_type` | string / null | Optional stratification label. |
| `permeability` | number / null | Experimental coefficient (absent in open data). |
| `logp` | number / null | Calculated logP (used as proxy target if `permeability` missing). |

### 2.2 Processed Molecule Record *(conforms to `contracts/dataset.schema.yaml`)*  
| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Original SMILES. |
| `mol_valid` | boolean | `True` if RDKit parsed successfully. |
| `mw` | number | Molecular Weight. |
| `logp` | number | Calculated LogP (descriptor). |
| `tpsa` | number | Topological Polar Surface Area. |
| `hba` | integer | H‑bond acceptors count. |
| `hbd` | integer | H‑bond donors count. |
| `rotatable_bonds` | integer | Number of rotatable bonds. |
| `target` | number | Proxy target (`logp` or experimental permeability). |
| `polymer_type` | string / null | Stratification key (if any). |

### 2.3 Model Prediction Record *(conforms to `contracts/results.schema.yaml`)*  
| Field | Type | Description |
|-------|------|-------------|
| `molecule_id` | string | Unique identifier (e.g., row index). |
| `true_value` | number | Ground‑truth target. |
| `predicted_gnn` | number | GNN regression output. |
| `predicted_rf` | number | RF baseline output. |
| `predicted_rf_ablation` | number | RF trained on graph stats only. |
| `error_gnn` | number | `predicted_gnn – true_value`. |
| `error_rf` | number | `predicted_rf – true_value`. |

## 3. Transformation Workflow
1. **Download** raw files → `data/raw/` (checksum verified).  
2. **Preprocess** (`code/data/preprocess.py`):  
   - Parse SMILES → graph; compute descriptors.  
   - Set `mol_valid`; drop rows where `mol_valid=False`.  
   - Apply retention guard (≥ 95 % valid).  
   - If `target` missing, compute `logp` and assign as proxy.  
   - Output `data/processed/processed_data.parquet` (validated against `dataset.schema.yaml`).  
3. **Split** (`code/data/split.py`): produce `train.parquet` and `test.parquet` under `data/processed/`.  
4. **Model Training** → produce serialized model files under `code/models/`.  
5. **Evaluation** → write `results/metrics.json` (validated against `results.schema.yaml`).  
6. **Interpretability** → write PNG/HTML under `results/interpretability/`.

## 4. Constraints
- No NaNs in any numeric column of the processed dataset.  
- Graph construction must be a faithful RDKit conversion (Constitution VI).  
- Target column must be either experimental permeability *or* calculated `logp` (proxy).  

---
