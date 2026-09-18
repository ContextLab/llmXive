# Data Model: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

## 1. Entity Definitions

### Gas-MOF Pair
A unique record representing the interaction between a permeant molecule and a porous framework.
- **ID**: Unique hash of (Molecule_SMILES + Framework_ID).
- **Molecule**: SMILES string, molecular graph (atoms, bonds).
- **Framework**: Framework ID, crystal graph (atoms, bonds, unit cell).
- **Target**: **Geometric Proxy** (Surface Area or Pore Volume). *Computed from structure using pymatgen, not experimental.*

### Heterogeneous Graph
A PyTorch Geometric `HeteroData` object.
- **Node Types**: `molecule_atom`, `framework_atom`.
- **Edge Types**: `covalent`, `neighbor`, `cross_contact`.
- **Features**:
  - `molecule_atom`: Atomic number, hybridization, chirality.
  - `framework_atom`: Atomic number, element type.
  - `edges`: Distance (float), bond order (int).

### Hand-Crafted Descriptors (Baseline Input)
- **Molecular**: Molecular Weight, Atom Count, LogP (from RDKit).
- **Framework**: Density, Unit Cell Volume (from Pymatgen).
- *Note: Surface Area and Pore Volume are NOT used as baseline inputs to avoid circularity; they are the target.* The baseline uses **Simple Descriptors** (MW, Atom Count, Density, Unit Cell Volume) which are distinct from the target (SA, PV) to avoid circularity.

## 2. Data Flow

1.  **Raw Input**:
    - `data/raw/mof_structures.json` (from HuggingFace).
    - `data/raw/zeolite_structures.zip` (from HuggingFace).
    - `data/raw/gas_smiles.csv` (from HuggingFace or user input).
2.  **Preprocessing**:
    - `data/processed/graphs.pt`: List of `HeteroData` objects.
    - `data/processed/targets.json`: Map of IDs to computed geometric proxies (SA, PV).
    - `data/processed/metadata.json`: Map of IDs to original sources, checksums.
3.  **Training**:
    - `data/processed/train_val_test_splits.pt`: Indices for 5-fold CV.
4.  **Output**:
    - `data/results/metrics.json`: RMSE, R², MAE, Pearson r per fold.
    - `data/results/ablation_report.json`: Performance delta.
    - `data/results/sensitivity_report.json`: Variance across thresholds {0.01, 0.05, 0.1} nm.

## 3. Schema Constraints

- **Missing Values**: Any pair with missing structure data is filtered out (logged).
- **Stereochemistry**: Undefined stereochemistry in SMILES is handled by RDKit default (skip or canonicalize).
- **Periodic Boundaries**: Structures exceeding memory limits are chunked or skipped.
- **Target Computation**: The target (Geometric Proxy) MUST be computed from the structure using `pymatgen` before training. It is NOT a raw input field.
- **Baseline Inputs**: The linear baseline uses **Simple Descriptors** (Molecular Weight, Atom Count, Framework Density, Unit Cell Volume) which are distinct from the target (Surface Area, Pore Volume) to avoid circularity.