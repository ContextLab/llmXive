# Data Model: Predicting Material Properties from Compositional Data with Graph Neural Networks

## Overview
The project defines a small set of structured artifacts that flow from raw ingestion to final results. All artifacts are version‑hashed and validated against JSON/YAML schemas stored in `contracts/`.

## Raw Data Schema (`raw_materials.parquet`)
| Field | Type | Description |
|-------|------|-------------|
| `material_id` | string | Unique identifier from source dataset. |
| `formula` | string | Chemical formula (e.g., `"Fe2O3"`). |
| `band_gap` | float | Band‑gap energy (eV). |
| `hardness` | float | Hardness (GPa). |
| `crystal_system` | string | One of `{triclinic, monoclinic, orthorhombic, tetragonal, trigonal, hexagonal, cubic}`. |
| `source_split` | string | `"train"` / `"val"` / `"test"` after stratified split. |

*All columns are required; rows missing any of the above are dropped with a warning.*

## Processed CSV (`materials_processed.csv`)
- Same columns as raw, plus:
  - `element_list` (list of element symbols, derived from `formula`).
  - `element_features` (list of dicts with atomic number, electronegativity, valence electrons, atomic radius).

## Graph Object (`CompositionGraph/<material_id>.pt`)
- Torch‑Geometric `Data` object serialized with `torch.save`.
- Node attributes: `x` (tensor of shape `[n_elements, 4]`).
- Edge index: fully connected including self‑loops.
- Edge attributes: `edge_weight` (periodic‑distance scalar).

## Model Checkpoint (`gnn_checkpoint_<hash>.pt`)
- State dict of `CompositionGNN`.
- Includes training hyperparameters and random seed metadata.

## Metrics JSON (`results_composition_only.json`)
Conforms to `contracts/model_metrics.schema.yaml` (see contract file). Contains, for each target (`band_gap`, `hardness`):
- `r2_mean`, `r2_std`
- `mae_mean`, `mae_std`
- `rmse_mean`, `rmse_std`

## Embeddings (`node_embeddings.npy`)
- Numpy array of shape `[n_elements, hidden_dim]` for the final trained model.

## Interpretability Report (`interpretability_report.md`)
- Markdown table with PCA component, Pearson *r*, two‑tailed *p*-value, and significance flag.

## Per‑Crystal‑System Metrics (`metrics_by_system.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `crystal_system` | string | Crystal system identifier (same categories as raw). |
| `target` | string | `"band_gap"` or `"hardness"`. |
| `r2_mean` | float | Mean R² across CV folds for this system and target. |
| `r2_std` | float | Standard deviation of R². |
| `mae_mean` | float | Mean MAE. |
| `mae_std` | float | Standard deviation of MAE. |
| `rmse_mean` | float | Mean RMSE. |
| `rmse_std` | float | Standard deviation of RMSE. |

*Generated in Phase 9 of the implementation plan; provenance recorded in `state/...`.*

---


