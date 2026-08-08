# Data Model: Predicting Molecular Reactivity

## Overview
This document defines the data schemas, transformations, and storage formats for the molecular reactivity prediction pipeline. All data flows from `data/raw` (immutable) to `data/processed` (derived) to `artifacts` (results).

## Data Flow

1. **Raw Data**: Downloaded from verified sources (QM9 Parquet) or curated static assets (Reference/Kinetic CSVs).
2. **Processed Data**:
   - `graphs.pt`: Serialized list of PyTorch Geometric `Data` objects.
   - `splits/`: JSON files containing train/test indices based on Murcko scaffolds.
3. **Artifacts**:
   - `metrics.json`: Aggregated performance metrics.
   - `predictions.parquet`: Test set predictions with ground truth.
   - `attribution_maps.json`: Feature importance scores.

## Schema Definitions

### 1. Molecular Graph Node Features
| Field | Type | Description |
| :--- | :--- | :--- |
| `atomic_number` | int | Atomic number (e.g., 6 for Carbon). |
| `hybridization` | int | Hybridization state (e.g., SP, SP2, SP3). |
| `formal_charge` | int | Formal charge of the atom. |
| `num_neighbors` | int | Degree of the node. |

### 2. Molecular Graph Edge Features
| Field | Type | Description |
| :--- | :--- | :--- |
| `bond_type` | int | Bond type (1: Single, 2: Double, 3: Triple, 4: Aromatic). |
| `conjugation` | bool | Whether the bond is conjugated. |
| `in_ring` | bool | Whether the bond is part of a ring. |

### 3. Target Variable (DFT Property)
| Field | Type | Description |
| :--- | :--- | :--- |
| `homo_lumo_gap` | float | HOMO-LUMO gap in eV (target for regression). Derived as `lumo - homo` from QM9 columns `lumo` and `homo`. |
| `energy` | float | Total energy (optional, for multi-task). |

### 4. Split Metadata
| Field | Type | Description |
| :--- | :--- | :--- |
| `scaffold_id` | str | Murcko scaffold hash. |
| `split` | str | "train", "val", or "test". |
| `similarity_score` | float | Max Tanimoto similarity to any training molecule (used for filtering). |

### 5. Attribution Map
| Field | Type | Description |
| :--- | :--- | :--- |
| `molecule_id` | str | Unique identifier for the molecule. |
| `node_importance` | list[float] | Importance score per node. |
| `edge_importance` | list[float] | Importance score per edge. |
| `top_substructure` | str | SMILES of the most important subgraph. |
| `alignment_score` | float | Tanimoto similarity against the closest reference substructure (0.0 to 1.0). |
| `null_model_score` | float | Baseline score from random subgraph selection. |

### 6. Curated Reference Substructure
| Field | Type | Description |
| :--- | :--- | :--- |
| `smiles` | str | SMILES of the substructure. |
| `source_doi` | str | DOI of the literature source. |
| `description` | str | Description of the reactivity. |

### 7. Curated Kinetic Entry
| Field | Type | Description |
| :--- | :--- | :--- |
| `smiles` | str | SMILES of the molecule. |
| `reaction_rate` | float | Experimental reaction rate (units: 1/s). |
| `reaction_type` | str | Type of reaction (e.g., "thermodynamic", "kinetic"). |
| `source_doi` | str | DOI of the literature source. |

## Storage Formats
- **Raw Data**: Parquet (for QM9), CSV (for static assets).
- **Processed Graphs**: PyTorch `.pt` (binary).
- **Metrics/Predictions**: JSON and Parquet.
- **Checksums**: `data/raw/checksums.json` (SHA-256 hashes).

## Data Hygiene Rules
- **Immutability**: Files in `data/raw` are never modified. New versions are written to `data/raw/v2/`.
- **Checksums**: Every file in `data/raw` must have a corresponding entry in `checksums.json`.
- **Validation**: Preprocessing scripts must validate that node/edge feature counts match the expected schema before saving.
