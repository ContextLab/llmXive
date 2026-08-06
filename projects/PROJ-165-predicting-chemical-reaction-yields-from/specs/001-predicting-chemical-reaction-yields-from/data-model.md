# Data Model: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## Entity Definitions

### ReactionSample
Represents a single chemical reaction instance.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `reaction_smiles` | String | Canonical SMILES of the reaction. | USPTO / DFT |
| `yield_percent` | Float | Synthetic yield (0-100), generated from descriptors. | `src/data/synthetic_yield_generator.py` |
| `ir_spectrum` | Array[Float] | IR spectrum intensities (400-4000 cm⁻¹, resampled). | DFT |
| `nmr_spectrum` | Array[Float] | NMR spectrum intensities (0-10 ppm, resampled). | DFT |
| `rfp` | Array[Float] | ECFP4 fingerprint vector. | Computed from SMILES |
| `reaction_template_id` | String | Hash of the reaction center substructure. | Computed from SMILES |
| `solvent_id` | Integer | Encoded solvent ID. | DFT |
| `catalyst_id` | Integer | Encoded catalyst ID. | DFT |
| `temperature_k` | Float | Reaction temperature in Kelvin. | DFT |
| `split` | String | 'train', 'val', 'test'. | Generated |
| `descriptors` | Object | MW, LogP, TPSA used to generate yield. | Computed from SMILES |

### SpectralGrid
Defines the standardized domain for spectral data.

| Attribute | Type | Description |
|-----------|------|-------------|
| `type` | String | 'IR', 'Raman', 'NMR' |
| `min_value` | Float | Minimum wavenumber/shift (e.g., 400, 0) |
| `max_value` | Float | Maximum wavenumber/shift (e.g., 4000, 10) |
| `num_bins` | Integer | Number of resampled bins (e.g., 1000) |

### ModelCheckpoint
Represents a saved state of the trained model.

| Attribute | Type | Description |
|-----------|------|-------------|
| `epoch` | Integer | Training epoch number |
| `validation_rmse` | Float | Validation RMSE at checkpoint |
| `weights_path` | String | Path to saved weights |
| `config_hash` | String | Hash of model configuration |

### NISTFunctionalGroup
Represents a verified functional group frequency.

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | String | Functional group name (e.g., "Carbonyl") |
| `wavenumber` | Float | Center wavenumber (cm⁻¹) |
| `range` | Float | ±50 cm⁻¹ tolerance |

## Data Flow

[omitted - unchanged]

## Constraints

[omitted – unchanged]

## Verified Static Lists

- **NIST Functional Groups**: `data/verified/nist_functional_groups.yaml`
  - Pre-computed from NIST Chemistry WebBook via `src/data/generate_nist_list.py`.
  - Checksummed and versioned.
  - Used for attention peak validation (SC-003).
  - **Note**: Values are NOT hardcoded in code; they are loaded from this artifact.