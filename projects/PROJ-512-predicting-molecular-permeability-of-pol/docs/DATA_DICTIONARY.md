# Data Dictionary: Polymer Permeability Dataset

## Overview
This document describes the schema and features used in the `polymers.h5` dataset
and the internal `PolymerGraph` representation.

## Entity: `PolymerGraph`
A graph representation of a polymer repeat unit.

### Node Features (Per Atom)
| Feature Name | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `atom_type` | Integer | Encoded atom type (e.g., 0=C, 1=N, 2=O) | RDKit `GetAtomicNum` |
| `hybridization` | Integer | Hybridization state (SP, SP2, SP3) | RDKit `GetHybridization` |
| `formal_charge` | Float | Formal charge of the atom | RDKit `GetFormalCharge` |
| `num_neighbors` | Integer | Number of bonded neighbors | Graph topology |
| `is_aromatic` | Boolean | Whether the atom is part of an aromatic system | RDKit `GetIsAromatic` |

### Edge Features (Per Bond)
| Feature Name | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `bond_type` | Integer | Bond order (1=Single, 2=Double, 3=Triple) | RDKit `GetBondType` |
| `is_conjugated` | Boolean | Whether the bond is part of a conjugated system | RDKit `GetIsConjugated` |
| `is_in_ring` | Boolean | Whether the bond is part of a ring | RDKit `IsInRing` |

### Graph-Level Properties
| Property Name | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `smiles` | String | Canonical SMILES string of the repeat unit | Input data |
| `molecular_weight` | Float | Calculated MW of the repeat unit (Da) | RDKit `CalcExactMolWt` |
| `log_permeability` | Float | Target variable (log10 of permeability coefficient) | NIST/PubChem |
| `scaffold_id` | Integer | Murcko scaffold cluster ID | RDKit `GetScaffoldForMol` |

## Dataset Schema (`polymers.h5`)
The HDF5 file is structured as follows:

```
/
├── /nodes (Dataset: N x 5)
│ └── [atom_type, hybridization, formal_charge, num_neighbors, is_aromatic]
├── /edges (Dataset: M x 3)
│ └── [source_idx, target_idx, bond_type]
├── /edge_attr (Dataset: M x 2)
│ └── [is_conjugated, is_in_ring]
├── /graph_props (Dataset: G x 3)
│ └── [molecular_weight, log_permeability, scaffold_id]
└── /metadata (Attributes)
 ├── source: "NIST_PubChem"
 ├── version: "1.0"
 └── record_count: <int>
```

## Derived Features (Baselines)
For baseline models (Random Forest, Linear Regression), the following derived
features are computed in `code/models/baselines.py`:

- **ECFP4 Fingerprints**: 2048-bit circular fingerprints generated via RDKit.
- **RDKit Descriptors**:
 - `LogP`: Octanol-water partition coefficient.
 - `TPSA`: Topological Polar Surface Area.
 - `NumRotBonds`: Number of rotatable bonds.
 - `NumHDonors` / `NumHAcceptors`: Hydrogen bond counts.

## Data Cleaning Rules
1. **Missing Values**: Records with missing `log_permeability` are excluded.
2. **Duplicates**: Entries with identical SMILES are averaged (arithmetic mean of log-permeability).
3. **Small Molecules**: Records with MW < 1000 Da are flagged in `logs/small_molecule_review.csv`.
 If `EXCLUDE_SMALL_MOLS=true`, they are removed from the dataset.
