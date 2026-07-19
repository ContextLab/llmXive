# Data Dictionary: 2D Molecular Features for Polymer Permeability Prediction

This document describes the 2D molecular features used in the `PROJ-512` project for predicting molecular permeability of polymers. These features are strictly limited to graph topology and atomic composition as defined in FR-001, excluding 3D structural data, free-volume metrics, or chain dynamics.

## Feature Schema Overview

The `PolymerGraph` entity (see `code/models/polymer_graph.py`) utilizes the following node and edge feature sets. All features are derived from 2D SMILES representations using RDKit.

### Node Features (Per Atom)

Each atom in the molecular graph is represented by a feature vector composed of the following categorical and numerical properties:

| Feature Name | Type | Description | Encoding / Values | Source |
|:--- |:--- |:--- |:--- |:--- |
| `atom_type` | Categorical | The chemical element of the atom. | One-hot encoded or integer index mapped to: `{C, H, O, N, S, P, F, Cl, Br, I, Other}`. | RDKit `GetAtomicNum()` |
| `hybridization` | Categorical | The hybridization state of the atom. | One-hot encoded: `{SP, SP2, SP3, SP3D, SP3D2, OTHER}`. | RDKit `GetHybridization()` |
| `degree` | Integer | The number of bonded neighbors (valence). | Integer: `0` to `12`. | RDKit `GetDegree()` |
| `formal_charge` | Integer | The formal charge of the atom. | Integer: e.g., `-1, 0, 1`. | RDKit `GetFormalCharge()` |
| `num_h_explicit` | Integer | Number of explicitly defined hydrogens. | Integer. | RDKit `GetTotalNumHs()` |
| `is_aromatic` | Boolean | Whether the atom is part of an aromatic system. | `0` (False) or `1` (True). | RDKit `GetIsAromatic()` |

*Note: As per FR-001, features such as atomic radii, 3D coordinates, or partial charges derived from 3D geometry are **excluded**.*

### Edge Features (Per Bond)

Each bond connecting two atoms is represented by the following properties:

| Feature Name | Type | Description | Encoding / Values | Source |
|:--- |:--- |:--- |:--- |:--- |
| `bond_type` | Categorical | The order/type of the chemical bond. | One-hot encoded: `{SINGLE, DOUBLE, TRIPLE, AROMATIC}`. | RDKit `GetBondType()` |
| `is_conjugated` | Boolean | Whether the bond is part of a conjugated system. | `0` (False) or `1` (True). | RDKit `GetIsConjugated()` |
| `is_in_ring` | Boolean | Whether the bond is part of a ring structure. | `0` (False) or `1` (True). | RDKit `IsInRing()` |

### Global Graph Features (Molecule-Level)

These features are computed for the entire polymer repeat unit or molecule and are often used as global context in the GNN readout phase.

| Feature Name | Type | Description | Calculation |
|:--- |:--- |:--- |:--- |
| `molecular_weight` | Float | The total molecular weight of the repeat unit. | Sum of atomic masses (Daltons). Calculated in `code/data/ingestion.py` via `calculate_mw()`. |
| `num_atoms` | Integer | Total number of atoms in the graph. | Count of nodes. |
| `num_bonds` | Integer | Total number of bonds in the graph. | Count of edges. |
| `num_rings` | Integer | Number of independent rings (cyclomatic number). | Calculated via RDKit `GetRingInfo()`. |

## Data Processing Pipeline

1. **Ingestion**: Raw SMILES strings are loaded from `code/data/raw/nist_polymer_raw.csv` (or `simulation_data.csv` if fallback).
2. **Parsing**: `smiles_to_polymer_graph()` in `code/data/ingestion.py` converts SMILES to `PolymerGraph` objects.
3. **Feature Extraction**: `extract_graph_features()` in `code/data/preprocessing.py` computes the vectors defined above.
4. **Storage**: Processed features are serialized into `code/data/processed/polymers.h5`.

## Constraints & Compliance

- **No 3D Features**: Features requiring 3D conformation (e.g., bond lengths, angles, torsion, radius of gyration) are strictly forbidden per FR-001.
- **No Physics-Based Features**: Metrics like "free-volume" or "chain dynamics" are not included in this schema.
- **Reproducibility**: All feature extraction logic is deterministic given the same SMILES input and RDKit version.

## References

- **Project Spec**: `specs/001-predicting-molecular-permeability/`
- **FR-001**: "Graph-based representation using only 2D topological features."
- **Implementation**: `code/models/polymer_graph.py`, `code/data/preprocessing.py`
