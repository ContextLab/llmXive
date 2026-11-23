# Feature Engineering Documentation

This document details the feature engineering pipeline used to convert raw polymer data into graph representations suitable for the `PolymerGNN` model.

## 1. Overview

The feature engineering process transforms SMILES strings into `PolymerGraph` objects containing node and edge features. These features are then serialized into HDF5 format for efficient loading during training.

**Pipeline Stages:**
1. **SMILES Parsing**: Conversion of string to RDKit `Mol` object.
2. **Graph Construction**: Creation of `PolymerGraph` entity.
3. **Feature Extraction**: Calculation of atom/bond properties.
4. **Normalization**: Scaling of continuous features (if applicable).

## 2. Node Features (Atom Properties)

The following features are extracted for every atom in the molecular graph.

### 2.1 Atomic Number (`atom_type`)
- **Source**: RDKit `Atom.GetAtomicNum()`
- **Type**: Integer
- **Range**: 1 (Hydrogen) to 118 (Oganesson).
- **Usage**: Direct input to the embedding layer of the GNN.

### 2.2 Hybridization (`hybridization`)
- **Source**: RDKit `Atom.GetHybridization()`
- **Type**: One-hot vector (4 dimensions)
- **Mapping**:
 - Index 0: `SP`
 - Index 1: `SP2`
 - Index 2: `SP3`
 - Index 3: `OTHER` (including `S`, `UNSPECIFIED`)
- **Usage**: Captures geometric constraints and orbital information.

### 2.3 Formal Charge (`formal_charge`)
- **Source**: RDKit `Atom.GetFormalCharge()`
- **Type**: Integer
- **Range**: Typically -3 to +3.
- **Usage**: Indicates ionic character of the atom.

### 2.4 Aromaticity (`is_aromatic`)
- **Source**: RDKit `Atom.GetIsAromatic()`
- **Type**: Boolean (0 or 1)
- **Usage**: Identifies delocalized electron systems.

### 2.5 Implicit/Explicit Hydrogens (`num_hs`)
- **Source**: RDKit `Atom.GetTotalNumHs()`
- **Type**: Integer
- **Range**: 0 to 4 (typical).
- **Usage**: Completes valence information for the atom.

## 3. Edge Features (Bond Properties)

Features are extracted for every bond connecting two atoms.

### 3.1 Bond Type (`bond_type`)
- **Source**: RDKit `Bond.GetBondType()`
- **Type**: Integer (encoded)
- **Mapping**:
 - 1: Single
 - 2: Double
 - 3: Triple
 - 4: Aromatic
- **Usage**: Determines the strength and order of the interaction.

### 3.2 Conjugation (`is_conjugated`)
- **Source**: RDKit `Bond.GetIsConjugated()`
- **Type**: Boolean
- **Usage**: Indicates participation in a conjugated system.

### 3.3 Ring Membership (`is_in_ring`)
- **Source**: RDKit `Bond.IsInRing()`
- **Type**: Boolean
- **Usage**: Identifies cyclic structures.

## 4. Implementation Details

The feature extraction logic resides in `code/data/preprocessing.py`.

### 4.1 `extract_graph_features(mol)`
- **Input**: `rdkit.Chem.Mol` object.
- **Output**: Dictionary containing `node_features` (N x F) and `edge_features` (E x G).
- **Logic**:
 1. Iterate over atoms to build the node feature matrix.
 2. Iterate over bonds to build the edge feature matrix.
 3. Ensure all features are converted to `numpy.float32` for GPU/TPU compatibility (though currently CPU-only).

### 4.2 `convert_to_polymer_graph(smiles)`
- **Input**: SMILES string.
- **Output**: `PolymerGraph` instance.
- **Logic**:
 1. Parse SMILES to `Mol`.
 2. Call `extract_graph_features`.
 3. Populate `PolymerGraph` fields.

## 5. Feature Validation

During the `process_dataset` step, features are validated:
- **Node Count**: Must match the number of atoms in the molecule.
- **Edge Count**: Must match the number of bonds.
- **Feature Dimensions**: Must match the expected schema (e.g., hybridization is always 4-dim).

Any record failing these checks is logged and excluded.
