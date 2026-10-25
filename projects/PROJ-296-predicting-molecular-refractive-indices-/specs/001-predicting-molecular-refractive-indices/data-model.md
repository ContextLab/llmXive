# Data Model: Predicting Molecular Refractive Indices

## Entity Definitions

### 1. MoleculeGraph
Represents a molecular graph for the MPNN.

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Canonical SMILES string of the molecule. |
| `molecular_weight` | float | Molecular weight in g/mol (0 < value < 500). |
| `refractive_index` | float | Experimental RI normalized to 20 °C (≥ 1.0). |
| `node_features` | list[object] | List of atom feature objects (`atomic_num`, `degree`, `hybridization`, `is_aromatic`). |
| `edge_features` | list[object] | List of bond feature objects (`bond_type`, `is_conjugated`, `stereo`). |
| `scaffold_id` | string | Murcko scaffold fingerprint (used for split). |
| `global_features` | object | Optional scalars (e.g., normalized `molecular_weight`). |
| `temperature` | number | Measurement temperature in Kelvin (optional). |
| `temperature_uncertainty` | number | Propagated uncertainty from temperature normalization (optional). |

### 2. PredictionResult
Output of the inference pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Input molecule SMILES. |
| `true_ri` | float | Experimental refractive index. |
| `pred_ri_gnn` | float | MPNN predicted RI. |
| `pred_ri_baseline` | float | Atomic‑contribution baseline prediction. |
| `error_gnn` | float | `abs(pred_ri_gnn - true_ri)`. |
| `error_baseline` | float | `abs(pred_ri_baseline - true_ri)`. |
| `top_features` | list[object] | Normalized attribution scores for top‑10 features (each with `feature_type`, `feature_index`, `score`). |

### 3. FeatureAttribution
Output of Integrated Gradients analysis (conforms to `output.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Input molecule. |
| `top_features` | list[object] | Array of attribution entries, each with: |
|  - `feature_type` | string (enum: `"ATOM"`, `"BOND"`) | Type of feature. |
|  - `feature_index` | integer | Index of the atom or bond within the graph. |
|  - `score` | number | Normalized attribution score (higher = more important). |

### 4. PhysicalProperty
Independent physical measurement used for attribution validation (SC‑003).

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Molecule identifier (must match `MoleculeGraph.smiles`). |
| `polarizability` | float | Experimental isotropic polarizability (Å³) at 20 °C. |
| `source` | string | Citation or URL of the dataset (must be a verified open source). |

### 5. SSoTMetrics (new)
Aggregated metrics that serve as the **Single Source of Truth** for the paper.

| Field | Type | Description |
|-------|------|-------------|
| `fold` | integer | Scaffold partition index (1‑5). |
| `repeat` | integer | Repeat index within the partition (1‑5). |
| `mae_gnn` | float | Test‑set MAE for the GNN. |
| `rmse_gnn` | float | Test‑set RMSE for the GNN. |
| `mae_baseline` | float | Test‑set MAE for the baseline. |
| `rmse_baseline` | float | Test‑set RMSE for the baseline. |
| `p_value` | float | Paired test p‑value (t‑test or Wilcoxon). |
| `effect_size` | float | Cohen’s d (or rank‑biserial for Wilcoxon). |
| `power` | float | Achieved statistical power (estimated via statsmodels). |
| `attr_corr_polarizability` | float | Pearson correlation coefficient between summed top‑10 attribution scores and experimental polarizability. |
| `attr_corr_p_value` | float | Two‑tailed p‑value for the correlation. |

## Data Flow
1. **Raw CSV** → `download.py` → `data/raw/raw.csv`.  
2. **Preprocess** → `preprocess.py` → `data/processed/filtered.csv` (includes `node_features`, `edge_features`, `temperature`, `temperature_uncertainty`).  
3. **Scaffold Split** → `split.py` → `data/splits/train_{fold}_{repeat}.csv`, `val_{fold}_{repeat}.csv`, `test_{fold}_{repeat}.csv`.  
4. **Baseline** → `baseline.py` → `results/baseline_predictions_{fold}_{repeat}.csv`.  
5. **MPNN Training** → `train.py` → `models/mpnn_{fold}_{repeat}.pt`.  
6. **Evaluation** → `evaluate.py` → `results/metrics_summary.csv`, `parity_{fold}_{repeat}.png`, `importance_{fold}_{repeat}.png`.  
7. **Attribution** → `attribution.py` → `results/attributions_{fold}_{repeat}.csv`.  
8. **Physical Property Load** → `utils/polarizability_loader.py` → `data/aux/polarizability.csv`.  
9. **Combined Prediction Output** → `merge_predictions.py` → `results/prediction_results_{fold}_{repeat}.csv` (conforms to `output.schema.yaml`).  
10. **SSoT Generation** → `evaluate.py` → `results/ssot_metrics.csv`.  

## Schema Constraints (mirrored in contracts)
- **SMILES**: Must be RDKit‑parseable (regex enforced in schema).  
- **Molecular Weight**: 0 < value < 500.  
- **Refractive Index**: ≥ 1.0.  
- **Node/Edge Features**: Types and enumerations as defined in `contracts/dataset.schema.yaml`.  
- **Temperature Handling**: If `temperature` is present, `temperature_uncertainty` must be present; otherwise both may be omitted.  
- **PhysicalProperty**: Must have a verified source URL; the dataset is required for SC‑003 validation.  

---


