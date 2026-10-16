# Data Model: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Core Entities

### PolymerRecord
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | SHA‑256 hash of (`smiles` + `temperature` + `ph` + `uv_exposure`). | Required, unique |
| `smiles` | string | Canonical SMILES; **must be a valid RDKit SMILES** (no synthetic fallback). | Valid RDKit SMILES |
| `polymer_type` | string | Detected class (e.g., `"polyester"`). | Derived from SMARTS detection |
| `temperature` | number | °C; default 25 if imputed. | ≥ -273.15 |
| `ph` | number | pH; default 7 if imputed. | 0 – 14 |
| `uv_exposure` | number | Normalised UV (0‑1); default 0 if imputed. | 0 – 1 |
| `degradation_pathway` | string | `"hydrolysis"`, `"oxidation"` or `"photolysis"`. | Curated label required for training |
| `label_source` | string | `"curated"` (synthetic labels are **not** used for training). |
| `flagged_for_curation` | boolean | True if label was missing and therefore excluded from training. |
| `metadata` | object | Flags for imputation, validation status, etc. |
| `synthetic_smiles` | boolean | `true` if the SMILES was generated synthetically (records with this flag are excluded). |

### MolecularGraph
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | FK → `PolymerRecord.id` |
| `nodes` | list of objects | Atom features (`atom_type`, `degree`, `hybridization`, `formal_charge`). |
| `edges` | list of objects | Bond features (`bond_type`, `conjugation`, `aromaticity`). |
| `global_features` | object | `{temperature, ph, uv_exposure}` |
| `graph_hash` | string | SHA‑256 of the serialized graph. |

### MotifImportance
| Field | Type | Description |
|-------|------|-------------|
| `motif_id` | string | Unique identifier. |
| `motif_pattern` | string | SMILES of the subgraph motif. |
| `pathway` | string | `"hydrolysis"`, `"oxidation"` or `"photolysis"`. |
| `importance_score` | number | Integrated Gradients score (0 – 1). |
| `p_value` | number | χ² test p‑value (0 – 1). |
| `significant` | boolean | `p_value < 0.05`. |

### PredictionResult (output of inference)
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | FK to `PolymerRecord.id`. |
| `predicted_class` | string | One of the three pathways (hydrolysis, oxidation, photolysis). |
| `confidence` | number | Softmax probability (0 – 1). |
| `is_low_confidence` | boolean | `confidence < 0.6`. |
| `motif_importance` | object | Mapping `{motif_name: score}`. |
| `attribution_map` | array of numbers | Node‑level IG scores. |

## Data Flow Diagram (conceptual)

1. **Ingestion** → raw CSV (`data/raw/`).  
2. **Label Validation** → `label_flags.json` (adds `label_source`, `flagged_for_curation`).  
3. **Preprocess** → `PolymerRecord`s (`records.parquet`) + `MolecularGraph`s (`graphs/*.pkl`).  
4. **Augmentation** (bond rotation + atom masking) → augmented graphs (`augmented/graphs/*.pkl`).  
5. **Training** → model checkpoint (`code/models/model.pt`).  
6. **Inference** → `PredictionResult`s (`output/*.json`).  
7. **Attribution** → `MotifImportance`s (`motif_importance/*.json`).  
8. **Statistical Validation** → χ² results (`chi2_results.json`).  
9. **Report** → final markdown (`docs/reports/final_report.md`).

All files are version‑hashed and listed in `state/artifact_hashes.yaml` for reproducibility.

---

