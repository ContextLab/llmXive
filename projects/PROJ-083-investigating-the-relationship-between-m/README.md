# PROJ-083: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

## Overview
This project investigates the correlation between topological molecular descriptors (Wiener, Balaban, Zagreb indices) and regioselectivity in Electrophilic Aromatic Substitution (EAS) reactions.

## Project Structure
```
.
├── code/ # Source code modules
│ ├── ingestion.py # Data download and filtering
│ ├── descriptors.py # Topological index calculations
│ ├── modeling.py # Statistical modeling
│ ├── config.py # Configuration management
│ └── utils/ # Utilities (smiles_parser, logger, symmetry)
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Cleaned and filtered data
│ └── models/ # Trained models and results
├── tests/ # Unit and integration tests
├── specs/ # Project specifications
│ └── 001-molecular-topology-selectivity/
├── docs/ # Documentation and reports
└── requirements.txt # Python dependencies
```

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Refer to `docs/quickstart.md` for execution instructions.

## Key Constraints
- **Symmetry Invariance**: All topological indices must be proven invariant under the defined symmetry group of the aromatic ring (see `docs/reports/symmetry_group_definition.md`).
- **Data Integrity**: Pipeline halts if EAS reaction count < 100.
- **Model Validation**: Models must meet R² > 0.05 threshold or report project failure.
