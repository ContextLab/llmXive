# Data Model: Predicting Molecular Refractive Indices

## Entity Definitions

### 1. MoleculeGraph
Represents a molecular graph for the MPNN.

| Field | Type | Description |
| :--- | :--- | :--- |
| `smiles` | string | Canonical SMILES string. |
| `molecular_weight` | float | Calculated MW in g/mol. |
| `refractive_index` | float | Experimental RI (normalized to 20°C). |
| `nodes` | list[dict] | List of node features: `atomic_num`, `degree`, `hybridization`, `is_aromatic`. |
| `edges` | list[dict] | List of edge features: `bond_type`, `is_conjugated`, `stereo`. |
| `scaffold_id` | string | Murcko scaffold fingerprint (for splitting). |

### 2. PredictionResult
Output of the inference pipeline.

| Field | Type | Description |
| :--- | :--- | :--- |
| `smiles` | string | Input molecule SMILES. |
| `true_ri` | float | Experimental value. |
| `pred_ri_gnn` | float | MPNN prediction. |
| `pred_ri_baseline` | float | Atomic contribution prediction. |
| `error_gnn` | float | `abs(pred_ri_gnn - true_ri)`. |
| `error_baseline` | float | `abs(pred_ri_baseline - true_ri)`. |

### 3. FeatureAttribution
Output of the Integrated Gradients analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `smiles` | string | Input molecule. |
| `node_attributions` | list[float] | Attribution score per atom. |
| `edge_attributions` | list[float] | Attribution score per bond. |
| `top_features` | list[dict] | Top 5 attributed substructures (atom index, bond type). |

## Data Flow

1. **Raw Data** (`data/raw/*.parquet`) -> **Preprocessor** (`code/data/preprocess.py`) -> **Processed Splits** (`data/processed/train.csv`, `val.csv`, `test.csv`).
2. **Processed Splits** -> **MPNN Trainer** (`code/training/train.py`) -> **Model Weights** (`models/mpnn.pt`).
3. **Model Weights** + **Test Set** -> **Evaluator** (`code/training/evaluate.py`) -> **Results CSV** + **Plots**.
4. **Model Weights** + **Test Set** -> **Attribution Engine** (`code/models/attribution.py`) -> **Attribution CSV**.

## Schema Constraints

- **SMILES**: Must be valid RDKit parseable string.
- **Molecular Weight**: Must be > 0 and < 500.
- **Refractive Index**: Must be > 1.0 (physical lower bound).
- **Scaffold ID**: Must be unique per molecule group.
