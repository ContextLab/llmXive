# Data Model: Predicting Molecular Interactions in Ionic Liquids

## 1. Entity Definitions

### 1.1 IonicLiquidPair
Represents a unique combination of a cation and anion.
- **id**: `string` (Unique hash of cation_smiles + anion_smiles)
- **cation_smiles**: `string`
- **anion_smiles**: `string`
- **cation_family**: `string` (e.g., "imidazolium")
- **anion_family**: `string` (e.g., "BF4")
- **status**: `string` ("valid", "invalid", "missing_data")

### 1.2 MolecularDescriptor
Computed features for a single ion.
- **ion_smiles**: `string`
- **partial_charge**: `float`
- **polarizability**: `float`
- **h_bond_donor_count**: `int`
- **h_bond_acceptor_count**: `int`
- **molecular_weight**: `float`
- **morgan_fingerprint**: `list[int]` (Binary vector, length 2048)

### 1.3 InteractionEnergyComponent
Decomposed energy values.
- **pair_id**: `string`
- **electrostatic_energy**: `float` (kcal/mol)
- **dispersion_energy**: `float` (kcal/mol)
- **h_bond_energy**: `float` (kcal/mol)
- **total_energy**: `float` (kcal/mol)
- **source**: `string` ("SAPT2023", "dft23-full")

### 1.4 GeometricFeature
Spatial relationship features (generated via ETKDG).
- **pair_id**: `string`
- **center_of_mass_distance**: `float` (Å)
- **orientation_angle**: `float` (degrees)

## 2. Unified Training Table Schema

The primary artifact for modeling is `data/processed/unified_training_table.csv`.

| Column Name | Type | Description | Nullable |
| :--- | :--- | :--- | :--- |
| `pair_id` | string | Unique identifier | No |
| `cation_smiles` | string | Cation structure | No |
| `anion_smiles` | string | Anion structure | No |
| `cation_family` | string | Cation structural family | No |
| `anion_family` | string | Anion structural family | No |
| `partial_charge_cation` | float | Gasteiger charge | Yes |
| `partial_charge_anion` | float | Gasteiger charge | Yes |
| `polarizability_cation` | float | Approximate polarizability | Yes |
| `polarizability_anion` | float | Approximate polarizability | Yes |
| `h_bond_count_cation` | int | H-bond donor/acceptor sum | No |
| `h_bond_count_anion` | int | H-bond donor/acceptor sum | No |
| `embedding_cation` | string | Base64 encoded Morgan fingerprint | No |
| `embedding_anion` | string | Base64 encoded Morgan fingerprint | No |
| `inter_ionic_distance` | float | Center-of-mass distance (ETKDG) | Yes |
| `orientation_angle` | float | Relative orientation (ETKDG) | Yes |
| `target_electrostatic` | float | Electrostatic energy (kcal/mol) | No |
| `target_dispersion` | float | Dispersion energy (kcal/mol) | No |
| `target_h_bond` | float | H-Bond energy (kcal/mol) | No |

**Note**: Rows with missing `inter_ionic_distance` or `orientation_angle` (due to ETKDG failure) are **excluded** from the training set and logged to `data/processed/invalid_rows.log`. No approximation is used.

## 3. Data Flow

1. **Ingestion**: Raw JSONL/Parquet (SAPT2023, dft23-full) + Local CSV (ILThermo) → `data/raw/` (Checksummed).
2. **Feature Engineering**: Raw → `data/processed/unified_training_table.csv`.
   - ETKDG generation performed.
   - Invalid rows (missing SMILES, energy, or ETKDG failure) are logged to `data/processed/invalid_rows.log` and excluded.
3. **Splitting**: CSV → `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv`.
4. **Model Output**: Models saved as `artifacts/models/{component}_model.json`.
5. **Analysis Output**: `artifacts/reports/manova_results.json`, `artifacts/reports/validation_report.json`.