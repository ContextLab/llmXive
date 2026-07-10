# Data Model: Predicting Battery Electrolyte Decomposition Products

## 1. Entities

### 1.1 ElectrolyteMolecule
Represents a chemical species and its intrinsic properties.
- `dft_id` (string): Unique identifier from the source dataset.
- `smiles` (string): Canonical SMILES representation.
- `formation_energy` (float): Formation energy in eV.
- `homo` (float): Highest Occupied Molecular Orbital energy (eV).
- `lumo` (float): Lowest Unoccupied Molecular Orbital energy (eV).
- `band_gap` (float): LUMO - HOMO (eV). *Note: This field is present in raw data and processed logs for reference but is EXCLUDED from the model input matrix (X) to prevent collinearity.*
- `bond_lengths` (list[float]): List of bond lengths in Angstroms.
- `bond_angles` (list[float]): List of bond angles in degrees.
- `molecular_weight` (float): Calculated MW in g/mol.

### 1.2 DecompositionEvent
Represents the calculated stability of a molecule at a specific potential.
- `molecule_id` (string): Reference to `ElectrolyteMolecule.dft_id`.
- `potential_v` (float): Applied electrochemical potential (0, 2, or 4 V).
- `decomposition_energy` (float): Calculated $E_{decomp}$ in eV.
- `n_electrons` (int): Number of electrons transferred (from hardcoded lookup table).
- `reaction_mechanism` (string): The specific reaction mechanism used (e.g., "EC_reduction_n2").
- `is_valid` (boolean): Flag indicating if the entry passed outlier checks and has a defined reaction mechanism.

### 1.3 ModelRun
Represents a specific training configuration and its results.
- `run_id` (string): UUID for the run.
- `model_type` (string): "RandomForest".
- `potential_bin` (string): "low" (0-2V), "high" (3-5V), or "global".
- `r2_score` (float): Coefficient of determination on test set.
- `mae` (float): Mean Absolute Error on test set.
- `feature_importance` (dict): Map of feature name to importance score (EXCLUDING `band_gap`).
- `sensitivity_threshold` (float): The threshold used for this run.
- `external_validation_status` (string): "N/A" (due to missing data).

## 2. Data Flow

1.  **Raw Input**: Parquet files from HuggingFace.
2.  **Filtered**: `ElectrolyteMolecule` records (cleaned, deduplicated).
3.  **Derived**: `DecompositionEvent` records (calculated $E_{decomp}$ using hardcoded reaction table).
4.  **Model Input**: Feature matrix (X) and Target vector (y) constructed from `DecompositionEvent`. **Note: `band_gap` is explicitly dropped from X to ensure feature independence.**
5.  **Output**: `ModelRun` artifacts (metrics, importance maps).

## 3. Constraints & Validations

- **Missing Data**: Any record with `None` in `homo`, `lumo`, or `formation_energy` is excluded.
- **Physical Bounds**: `band_gap` must be $> 0$ for inclusion in the dataset (used for filtering outliers).
- **Potential Range**: `potential_v` must be in $\{0, 2, 4\}$.
- **Reaction Mechanism**: `n_electrons` and `reaction_mechanism` must be defined in the hardcoded lookup table. Molecules without a defined mechanism are excluded.
- **Energy Formula**: $E_{decomp}$ must be calculated using the explicit thermodynamic relation defined in the spec.
- **Feature Selection**: `band_gap` is **excluded** from model training inputs to prevent collinearity issues. It remains in the dataset for descriptive statistics only.