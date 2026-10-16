# Data Model: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Key Entities

### PolymerRecord

| Field                | Type   | Description                                    | Constraints                                 |
|----------------------|--------|------------------------------------------------|--------------------------------------------|
| `id`                 | str    | Unique identifier (hash of SMILES + conditions) | Required, unique                           |
| `smiles`             | str    | Canonical SMILES string                        | Valid RDKit SMILES                         |
| `polymer_type`       | str    | Detected polymer class (e.g., "polyester")    | Derived from SMILES                        |
| `temperature`        | float  | Temperature in °C                              | Imputed default = 25.0 if missing          |
| `ph`                 | float  | pH value                                       | Imputed default = 7.0 if missing           |
| `uv_exposure`        | float  | UV exposure (0‑1)                              | Imputed default = 0.0 if missing           |
| `degradation_pathway`| str    | Pathway label (`hydrolysis`, `oxidation`, `photolysis`) | Synthetic or curated                      |
| `label_source`       | str    | `"synthetic"` or `"curated"`                  | Required                                   |
| `flagged_for_curation`| bool | True if label missing/invalid                  | Required                                   |
| `metadata`           | dict   | Additional flags (e.g., imputation)           | Optional                                   |

### MolecularGraph

| Field            | Type   | Description                                      | Constraints                                 |
|------------------|--------|--------------------------------------------------|--------------------------------------------|
| `record_id`      | str    | Reference to `PolymerRecord.id`                 | Required                                   |
| `nodes`          | list   | Atom nodes with features (`atom_type`, `degree`, `hybridization`, `formal_charge`) | ≥ 1 node                                   |
| `edges`          | list   | Bond edges with features (`bond_type`, `conjugation`, `aromaticity`) | ≥ 1 edge                                   |
| `global_features`| dict   | Environmental conditions (`temperature`, `ph`, `uv_exposure`) | All three keys present                     |
| `graph_hash`     | str    | Content hash for versioning                      | Required                                   |

### DegradationPathway

| Value        | Description                                   |
|--------------|-----------------------------------------------|
| `hydrolysis` | Breakdown via water (ester hydrolysis)       |
| `oxidation`  | Breakdown via oxidative mechanisms            |
| `photolysis` | Breakdown via UV exposure                     |

### MotifImportance

| Field               | Type   | Description                                      | Constraints                                 |
|---------------------|--------|--------------------------------------------------|--------------------------------------------|
| `motif_id`          | str    | Unique identifier for the subgraph pattern       | Required                                   |
| `motif_pattern`     | str    | SMILES representation of the motif               | Valid RDKit SMILES                         |
| `pathway`           | str    | Associated degradation pathway (`hydrolysis`, `oxidation`, `photolysis`) | Required |
| `importance_score`  | float  | Integrated Gradients score (0‑1)                | 0.0 ≤ score ≤ 1.0                          |
| `p_value`           | float  | χ² test p‑value                                  | 0.0 ≤ p ≤ 1.0                              |
| `significant`       | bool   | True if `p_value` < 0.05                         | Required                                   |

## Data Flow

1. **Ingestion** (`ingest.py`) → raw `PolymerRecord` (CSV).  
2. **Preprocessing** (`preprocess.py`) → validated `PolymerRecord` + `MolecularGraph`.  
3. **Augmentation** (`augment.py`) → doubled `MolecularGraph` set.  
4. **Training** (`train.py`) → model weights.  
5. **Attribution** (`attribution.py`) → `MotifImportance`.  
6. **Validation** (`validate.py`) → χ² test, final report.

## Storage Formats

- **Raw CSV**: `data/raw/records.csv` (original download).  
- **Processed Records**: `data/processed/records.parquet` (validated `PolymerRecord`).  
- **Graph Objects**: `data/processed/graphs/*.pkl` (pickled `MolecularGraph`).  
- **Augmented Graphs**: `data/augmented/graphs/*.pkl`.  
- **Model Checkpoint**: `code/models/model.pt`.  
- **Reports**: `docs/reports/final_report.md` (Markdown) and `final_report.json`.  

All files have SHA‑256 checksums stored in `state/artifact_hashes.yaml`.

---
