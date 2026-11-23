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
| `source_url` | string | URL of the verified dataset source (e.g., `https://zenodo.org/records/1234567`). |
| `hand_crafted_features` | object | Exactly the four descriptors required for the linear‑regression baseline: |
|  | `surface_area` | number |
|  | `pore_volume` | number |
|  | `largest_cavity_diameter` | number |
|  | `accessible_surface_area` | number |
| `covariates` | object | Additional numeric descriptors (e.g., `framework_density`, `unit_cell_volume`) that are **concatenated to the graph embedding** before the regression head for confound control (methodology‑afec5e12). |

*Note*: The four hand‑crafted descriptors are **only** used by the linear‑regression baseline (FR‑015, SC‑010). The optional `covariates` field stores any extra numeric descriptors that may be concatenated to the pooled embedding for confound adjustment (see `analysis/confound_adjustment.py`).

## 2. Data Flow Overview
1. **Raw download** → `data/raw/` (MOF JSON, IZA ZIP, `gas_smiles.csv`).  
2. **Streaming & filtering** → retain only pairs with non‑null experimental permeability (FR‑001).  
3. **Stratified sampling across covariates** → two‑level stratification (gas type + surface‑area quartile) to obtain up to 500 representative pairs (addresses methodology‑8891fea9).  
4. **Graph construction** (`preprocess.py`) → `data/processed/graphs.pt`.  
5. **Target loading** (`download.py`/`loaders.py`) → `data/processed/targets.json` (contains `experimental_permeability`).  
6. **Split generation** (`train.py`) → `data/processed/cv_splits.pt`.  
7. **Model training / evaluation** → `data/results/metrics.json`, `ablation_report.json`, `sensitivity_report.json`, `feature_importance.json`, `confound_report.json`.  

All intermediate files are version‑hashed and recorded under `state/...yaml` (Principle III).

## 3. Schema Constraints (also expressed in `contracts/dataset.schema.yaml`)

- **Missing values**: Records missing any required field are dropped and logged.  
- **Stereochemistry**: If RDKit cannot assign stereochemistry, the molecule is canonicalized without stereochemical tags; the pair is retained.  
- **Periodic boundaries**: For frameworks exceeding memory limits, `preprocess.py` loads CIFs in chunks; atoms beyond the first 10 000 are omitted with a warning (FR‑019).  
- **Distance cutoffs**: Neighbor edges within the same component must have distance ≤ 0.35 nm (SC‑009). Cross‑contact edges are built using the current sweep threshold.  
- **Target integrity**: `experimental_permeability` must be a finite number; NaNs trigger exclusion.  
- **Covariate inclusion**: If `covariates` are present, they must be numeric and will be concatenated to the graph embedding for confound adjustment (methodology‑afec5e12).  

---



