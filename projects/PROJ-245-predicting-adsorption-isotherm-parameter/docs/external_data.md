# External Data Source: Krypton on Carbon Nanotubes

## Overview

This document describes the external validation dataset used in the "External Flow" of the pipeline. The dataset consists of Krypton (Kr) adsorption isotherm parameters on various Carbon Nanotube (CNT) materials, manually curated from literature sources.

## Source

- **Material**: Carbon Nanotubes (CNTs)
- **Adsorbate**: Krypton (Kr)
- **Reference**: "Krypton adsorption on carbon nanotubes" (Literature source).
- **File Location**: `data/external/kr_cnt.csv`

## Data Structure

The CSV file follows the schema defined in `contracts/dataset.schema.yaml`.

### Columns

- `material_id`: Unique identifier for the CNT material.
- `smiles`: SMILES string representing the adsorbate (Kr).
- `surface_area`: BET surface area of the material (m²/g).
- `pore_volume`: Pore volume of the material (cm³/g).
- `langmuir_capacity`: Langmuir capacity parameter (mmol/g).
- `henry_constant`: Henry constant parameter (mmol/g/bar).
- `temperature`: Temperature at which adsorption was measured (K).

## Curation Process

1. **Extraction**: Data points were manually extracted from the reference literature.
2. **Validation**: The data was validated against `contracts/dataset.schema.yaml` to ensure correct data types and units.
3. **Cleaning**: Missing values were handled according to the project's preprocessing rules (imputation or exclusion).
4. **Storage**: The final dataset was saved to `data/external/kr_cnt.csv`.

## Usage

To use this dataset, run the pipeline in external mode:

```bash
python code/main.py --mode external
```

The `code/data/load_external.py` module will automatically load and validate this file.

## Notes

- This dataset is small and intended for validation of the scientific consensus checks (SC-002, SC-003) rather than robust model training.
- Future work includes expanding this dataset with more adsorbates and materials.
- If the external dataset is missing, the pipeline will fail with a clear error message.