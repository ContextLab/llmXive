# Data Model: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Primary Dataset (`data/dataset.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `cod_id` | string | COD entry identifier (e.g., '1234567'). |
| `smiles` | string | Canonical SMILES string for the molecule. |
| `smiles_source` | string | `"extracted"` or `"generated"` flag. |
| `unit_cell_volume` | float | Unit‑cell volume (Å³) as reported in the CIF. |
| `packing_coefficient` | float | Raw packing coefficient (unit‑cell volume divided by sum of atomic vdW volumes). |
| `cape` | float | Composition‑adjusted packing efficiency (CAPE). |
| `radius_of_gyration` | float | 3‑D descriptor (Å) computed from a RDKit‑generated conformer of the isolated molecule. |
| `asphericity` | float | 3‑D descriptor (dimensionless) from the same conformer. |
| `principal_moments` | string | JSON‑encoded list of three moments (Å²) from the same conformer. |
| `lattice_system` | string | Crystal lattice system (e.g., `monoclinic`). |
| `temperature_K` | float | Measurement temperature (K). |
| `has_solvent` | boolean | Presence of solvent molecules (`true/false`). |
| `atom_type_counts` | string | JSON‑encoded dict of element → count (e.g., `{"C":12,"O":2}`); **not used as predictor** in the MLP. |
| `mlp_features` | string | JSON‑encoded combined feature vector **excluding** `atom_type_counts` (fingerprint PCs + 3‑D descriptors + confounders). |

*All rows must have non‑null values for the columns above; rows failing any check are excluded and logged.*

## Model Checkpoint (`models/mlp_regressor.pt`)
- **Framework**: PyTorch (CPU).  
- **Architecture**: Input size = `fingerprint_dim_PCs + 3 + N_confounders`; hidden layer = 128 units; ReLU activation; output layer = 1 (CAPE).  
- **Parameter Count**: ≤ 100 k (FR‑005).  
- **State Dict**: Serialized `torch.save(model.state_dict())`.  

## Validation Report (`results/validation_report.json`)
Conforms to `contracts/validation_report.schema.yaml`. Contains:
- `metrics`: `{ "MAE": float, "Pearson_r": float, "Spearman_rho": float, "Shapiro_W": float, "Shapiro_p": float }`
- `permutation_test`: `{ "p_value": float, "num_shuffles": 10000 }`
- `partial_correlation`: `{ "adjusted_r": float, "controlled_features": ["atom_type_counts"] }`
- `vif`: `{ "<feature_name>": float, ... }` (computed on PCA‑reduced fingerprint PCs + 3‑D descriptors + confounders)
- `sensitivity`: list of objects `{ "threshold": float, "Pearson_r": float, "Spearman_rho": float, "MAE": float, "p_value": float, "bonferroni_corrected_p": float }`
- `ablation`: `{ "MAE": float, "Pearson_r": float, "Spearman_rho": float, "Shapiro_W": float, "Shapiro_p": float }`
- `runtime_seconds`: float
- `git_commit": string
- `artifact_hashes`: `{ "dataset_csv": string, "model_pt": string, "report_html": string }`

---

