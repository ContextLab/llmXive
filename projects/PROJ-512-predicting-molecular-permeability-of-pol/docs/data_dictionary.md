# Data Dictionary: Polymer Permeability Dataset

This document describes the schema, feature definitions, and data integrity constraints
for the `polymers.h5` dataset used in the `PROJ-512` pipeline. All data originates
from verified real sources (NIST/PubChem) as per FR-001. Synthetic data is strictly
prohibited.

## File Location
`code/data/processed/polymers.h5`

## Schema Overview

The HDF5 file contains a root group `/polymers` with the following datasets:

| Dataset Name | Type | Description |
|:--- |:--- |:--- |
| `smiles` | String (Variable) | Canonical SMILES string of the polymer repeat unit. |
| `log_permeability` | Float64 | Target variable: Log10 of permeability coefficient (Barrer). |
| `molecular_weight` | Float64 | Calculated molecular weight of the repeat unit (Daltons). |
| `node_features` | Float32 (N, F) | Concatenated node features for the molecular graph. |
| `edge_index` | Int64 (2, E) | Sparse edge list (source, target) for graph connectivity. |
| `edge_features` | Float32 (E, F) | Concatenated edge features (bond type, conjugation). |
| `scaffold_id` | String (Variable) | Murcko scaffold hash for splitting logic. |
| `source_id` | String (Variable) | Original record ID from NIST/PubChem. |

## Feature Definitions

### Node Features (Per Atom)
Features are extracted using RDKit based on the `PolymerGraph` schema (T006).
Order: `[Atom Type One-Hot, Hybridization One-Hot, Formal Charge, Aromaticity]`

1. **Atom Type (One-Hot)**: Encodes element identity.
 * `C` (Carbon)
 * `N` (Nitrogen)
 * `O` (Oxygen)
 * `S` (Sulfur)
 * `Cl` (Chlorine)
 * `F` (Fluorine)
 * `Other` (Fallback for rare elements)
2. **Hybridization (One-Hot)**:
 * `SP`
 * `SP2`
 * `SP3`
 * `SP3D`
 * `SP3D2`
 * `UNSPECIFIED`
3. **Formal Charge**: Integer value (0, +1, -1, etc.), normalized to float.
4. **Aromaticity**: Boolean (0.0 or 1.0).

### Edge Features (Per Bond)
Features describe the connection between atoms.
Order: `[Bond Type One-Hot, Conjugation, Is In Ring]`

1. **Bond Type (One-Hot)**:
 * `SINGLE`
 * `DOUBLE`
 * `TRIPLE`
 * `AROMATIC`
2. **Conjugation**: Boolean (0.0 or 1.0).
3. **Is In Ring**: Boolean (0.0 or 1.0).

## Data Integrity Constraints

* **Missing Values**: No entries with missing `log_permeability` are included (T012).
* **Duplicates**: Duplicates identified by SMILES are averaged; only unique SMILES remain in the final dataset.
* **Small Molecules**: Entries with `molecular_weight` < 1000 Da are flagged in `logs/small_molecule_review.csv`. If `EXCLUDE_SMALL_MOLS=true`, they are removed from `polymers.h5`.
* **Scaffolds**: `scaffold_id` is generated using RDKit's `GetScaffoldForMol` (T020) to ensure valid Murcko splitting.

## Usage Example

```python
import h5py
import numpy as np

with h5py.File('code/data/processed/polymers.h5', 'r') as f:
 smiles = [s.decode('utf-8') for s in f['polymers/smiles'][:]]
 targets = f['polymers/log_permeability'][:]
 node_feats = f['polymers/node_features'][:]
 edge_idx = f['polymers/edge_index'][:]
```
