# Data Model: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Key Entities

### PolymerRecord

Represents a single polymer degradation entry.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | str | Unique identifier (hash of SMILES + conditions) | Required, unique |
| `smiles` | str | SMILES string of polymer | Valid RDKit SMILES |
| `polymer_type` | str | Detected polymer class (e.g., "polyester") | Derived from SMILES |
| `temperature` | float | Temperature in °C | Imputed if missing (default: 25.0) |
| `ph` | float | pH value | Imputed if missing (default: 7.0) |
| `uv_exposure` | float | UV exposure level (0-1) | Imputed if missing (default: 0.0) |
| `degradation_pathway` | str | Pathway label (hydrolysis, oxidation, photolysis) | Synthetic or flagged for curation |
| `label_source` | str | "synthetic" or "curated" | Required |
| `flagged_for_curation` | bool | True if label missing/invalid | Required |
| `metadata` | dict | Additional info (e.g., imputation flags) | Optional |

### MolecularGraph

Graph representation of a polymer record.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `record_id` | str | Reference to PolymerRecord.id | Required |
| `nodes` | list[dict] | Atom nodes with features | At least 1 node |
| `edges` | list[dict] | Bond edges with features | At least 1 edge |
| `global_features` | dict | Environmental conditions | Must include temp, pH, UV |
| `graph_hash` | str | Content hash for versioning | Required |

### DegradationPathway

Categorical label for degradation mechanism.

| Value | Description |
|-------|-------------|
| `hydrolysis` | Breakdown via water (e.g., ester hydrolysis) |
| `oxidation` | Breakdown via oxidation (e.g., radical attack) |
| `photolysis` | Breakdown via UV light |

### MotifImportance

Derived metric linking subgraph patterns to degradation pathways.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `motif_id` | str | Unique motif identifier | Required |
| `motif_pattern` | str | SMILES subgraph pattern | Valid RDKit SMILES |
| `pathway` | str | Associated degradation pathway | Required |
| `importance_score` | float | Integrated Gradients score | 0.0-1.0 |
| `p_value` | float | χ² test p-value | 0.0-1.0 |
| `significant` | bool | True if p < 0.05 | Required |

## Data Flow

1. **Ingestion**: `ingest.py` fetches SMILES from verified sources → `PolymerRecord` (raw).
2. **Preprocessing**: `preprocess.py` converts SMILES to `MolecularGraph`, imputes missing values, flags for curation.
3. **Augmentation**: `augment.py` applies edge dropout/subgraph sampling → augmented `MolecularGraph` list.
4. **Training**: `train.py` fits GNN on augmented graphs → model weights.
5. **Attribution**: `attribution.py` computes `MotifImportance` via Integrated Gradients.
6. **Validation**: `validate.py` runs χ² test, generates final report.

## Storage Format

- **Raw Data**: `data/raw/` (CSV/Parquet from verified sources).
- **Processed Data**: `data/processed/` (JSONL: `PolymerRecord` objects).
- **Graph Data**: `data/processed/graphs/` (Pickled `MolecularGraph` objects).
- **Augmented Data**: `data/augmented/` (Pickled augmented graphs).
- **Model Checkpoints**: `code/models/` (PyTorch `.pt` files).
- **Reports**: `docs/reports/` (Markdown/JSON).
