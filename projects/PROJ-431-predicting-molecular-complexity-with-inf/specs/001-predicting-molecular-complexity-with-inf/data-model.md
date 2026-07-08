# Data Model: Predicting Molecular Complexity with Information Theory

## 1. Entity Definitions

### MoleculeRecord
Represents a single molecule with computed entropy scores, experimental labels, and size metrics.
- **smiles** (string): Canonical SMILES string.
- **atom_entropy** (float): Shannon entropy of atom degree distribution.
- **bond_entropy** (float): Shannon entropy of bond type/degree distribution.
- **molecular_weight** (float): Calculated molecular weight (MW).
- **atom_count** (integer): Total number of non-hydrogen atoms.
- **logS** (float, nullable): Experimental aqueous solubility (log mol/L).
- **logP** (float, nullable): Experimental octanol-water partition coefficient.

### ModelArtifact
Serialized Ridge Regression model and its metadata.
- **model_path** (string): Path to `.pkl` file.
- **target** (string): Either `logS` or `logP`.
- **alpha** (float): Regularization parameter.
- **metrics** (dict): Contains `rmse`, `pearson_r`, `p_value`, `baseline_rmse`, `baseline_r`.

## 2. Data Flow

1.  **Input**: CSV file with `smiles`, `logS`, `logP` columns.
2.  **Schema Verification (Hard Gate)**:
    - Check for presence of `smiles`, `logS`, `logP`.
    - If missing: **Abort** with error "Missing required columns: [list]".
3.  **Process (Entropy & Size)**:
    - Parse SMILES with RDKit.
    - Compute `atom_entropy`, `bond_entropy`.
    - Compute `molecular_weight`, `atom_count`.
    - Output: Enriched CSV (original columns + entropy + size columns).
4.  **Process (Modeling)**:
    - Filter rows where `logS` or `logP` is not null.
    - Split 80/20 (seed 42).
    - Train **Null Model** (mean predictor).
    - Train **Size Model** (MW + Atom Count).
    - Train **Entropy Model** (Atom/Bond Entropy).
    - Evaluate all on test set.
    - Output: `.pkl` models, `.json` report.
5.  **Process (Visualization)**:
    - Generate scatter plots (Entropy vs. Property).
    - Output: `.png` file.

## 3. Schema Constraints

- **SMILES**: Must be a valid string parsable by `rdkit.Chem.MolFromSmiles`.
- **Entropy**: Must be $\ge 0$.
- **logS/logP**: Numeric. Missing values result in exclusion from training but retention in entropy output (with nulls).
- **Size Metrics**: Must be $\ge 0$.

## 4. Column Mapping (Source to Target)

| Source Column | Target Column | Transformation |
| :--- | :--- | :--- |
| `smiles` | `smiles` | Pass-through (validated) |
| `logS` | `logS` | Pass-through (float) |
| `logP` | `logP` | Pass-through (float) |
| *Computed* | `atom_entropy` | Shannon Entropy (Atom Degree) |
| *Computed* | `bond_entropy` | Shannon Entropy (Bond Degree) |
| *Computed* | `molecular_weight` | RDKit Mol.GetMolWeight() |
| *Computed* | `atom_count` | RDKit Mol.GetNumAtoms() |