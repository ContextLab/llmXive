# Data Model: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Data Flow

1.  **Raw Input**: CIF files from COD Organic Subset (downloaded).
2.  **Intermediate**: Parsed molecular structures (RDKit `Mol` objects), 3D coordinates.
3.  **Processed**: `dataset.csv` (features + target).
4.  **Model Input**: NumPy arrays (features), PyTorch tensors (targets).
5.  **Output**: `validation_report.json`, `model.pt`, `report.html`.

## Entity Definitions

### 1. Crystal Record
Represents a single organic crystal structure entry.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `cod_id` | str | Unique COD identifier | CIF Header |
| `smiles` | str | Canonical SMILES string | Extracted or RDKit Gen |
| `smiles_source` | str | "extracted" or "generated" | Pipeline Flag |
| `unit_cell_volume` | float | Volume in Å³ | CIF Cell Parameters |
| `n_atoms` | int | Count of non-H atoms | RDKit |
| `sum_vdw_volume` | float | Sum of atomic VdW volumes (Bondi) | RDKit + Bondi Radii |
| `packing_coefficient` | float | $V_{cell} / \sum V_{vdW}$ | Calculated (Diagnostic Only) |
| `cape` | float | Composition-Adjusted Packing Efficiency | Calculated (Target for ALL Models) |
| `radius_gyration` | float | $R_g$ in Å | 3D Geometry |
| `asphericity` | float | Shape parameter (0-1) | 3D Geometry |
| `moments_inertia` | list(float) | [I1, I2, I3] in amu·Å² | 3D Geometry |
| `lattice_system` | str | e.g., "monoclinic", "orthorhombic" | CIF Metadata |
| `temperature_K` | float | Measurement temperature | CIF Metadata |
| `has_solvent` | bool | Presence of solvent molecules | CIF Metadata |
| `atom_type_counts` | dict | {C: 5, N: 2, ...} | RDKit |

### 2. Model Features
The feature vector $X$ for the MLPs:
-   **Baseline Model**: $X_{smiles}$ (Fixed-length embedding from frozen transformer). **Target**: `cape`.
-   **Control Model**: $X_{geo}$ (Radius of Gyration, Asphericity, Moments) + $X_{conf}$ (Lattice, Temp, Solvent). **Target**: `cape`.
-   **Upper Bound Model**: $X_{smiles}$ + $X_{geo}$ + $X_{conf}$. **Target**: `cape`.
    -   **Exclusion**: `sum_vdw_volume` and `n_atoms` are **NOT** included in the feature set for any CAPE model to prevent circularity.

### 3. Prediction Output
-   `predicted_cape`: float.
-   `residual`: `observed_cape` - `predicted_cape`.

## Data Constraints

-   **SMILES**: Must be valid RDKit SMILES.
-   **CAPE**: Must be > 0.
-   **Missing Data**: Records with missing CIF metadata (e.g., no temperature) are excluded or imputed with "unknown" category if applicable.
-   **Atom Count**: Filtered to ≤ 50 non-H atoms.

## Schema Validation
All processed data must conform to `contracts/dataset.schema.yaml`.
