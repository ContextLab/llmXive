# Data Model: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

## 1. Entity Definitions

### Gas‑Framework Pair
| Field | Type | Description |
|---|---|---|
| `pair_id` | string | SHA‑256 hash of `<SMILES>_<framework_id>` (unique). |
| `molecule_smiles` | string | SMILES representation of the permeant gas. |
| `molecule_graph` | object | `HeteroData` sub‑object for molecule atoms (node features, edge index, edge attributes). |
| `framework_id` | string | Identifier from source dataset (e.g., MOF‑1234). |
| `framework_graph` | object | `HeteroData` sub‑object for framework atoms. |
| `cross_edges` | object | Edge index & distance attributes linking molecule ↔ framework atoms. |
| `experimental_permeability` | number | **Log₁₀‑transformed experimental permeability** (peer‑reviewed, publicly available source). |
| `source_url` | string | URL of the verified dataset source. |
| `hand_crafted_features` | object | Descriptors required for the linear‑regression baseline (exactly four): |
|  | `surface_area` | number |
|  | `pore_volume` | number |
|  | `largest_cavity_diameter` | number |
|  | `accessible_surface_area` | number |

*Note*: The four hand‑crafted descriptors are **only** used by the linear regression baseline (FR‑015, SC‑010).

## 2. Data Flow Overview
1. **Raw download** → `data/raw/` (MOF JSON, IZA ZIP, `gas_smiles.csv`).  
2. **Streaming & filtering** → retain only pairs with non‑null experimental permeability (FR‑001).  
3. **Graph construction** (`preprocess.py`) → `data/processed/graphs.pt`.  
4. **Target loading** (`download.py`/`loaders.py`) → `data/processed/targets.json` (contains `experimental_permeability`).  
5. **Split generation** (`train.py`) → `data/processed/cv_splits.pt`.  
6. **Model training / evaluation** → `data/results/metrics.json`, `ablation_report.json`, `sensitivity_report.json`, `feature_importance.json`.  

All intermediate files are version‑hashed and recorded under `state/...yaml` (Principle III).

## 3. Schema Constraints (also expressed in `contracts/dataset.schema.yaml`)

- **Missing values**: Records missing any required field are dropped and logged.  
- **Stereochemistry**: If RDKit cannot assign stereochemistry, the molecule is canonicalized without stereochemical tags; the pair is retained.  
- **Periodic boundaries**: For frameworks exceeding memory limits, `preprocess.py` loads CIFs in chunks; atoms beyond the first 10 000 are omitted with a warning.  
- **Distance cutoffs**: Neighbor edges within the same component must have distance ≤ 0.35 nm (SC‑009). Cross‑contact edges are built using the current sweep threshold.  
- **Target integrity**: `experimental_permeability` must be a finite number; NaNs trigger exclusion.  

---


