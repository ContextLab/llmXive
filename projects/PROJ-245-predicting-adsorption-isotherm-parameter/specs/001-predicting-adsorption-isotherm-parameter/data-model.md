# Data Model: Predicting Adsorption Isotherm Parameters from Molecular Features

## Dataset Schema (NIST)

This schema describes the structure of the NIST adsorption dataset **after** preprocessing and fitting.

**Important Note on Target Variables**: The fields `langmuir_capacity` and `henry_constant` are **not** direct observations. They are **fitted parameters** derived from non-linear regression of the raw isotherm data (Pressure vs. Amount Adsorbed) using the Langmuir model. The fitting process includes a quality check (R² > 0.9); entries failing this check are excluded.

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: NIST Adsorption Dataset (Processed)
description: Cleaned and preprocessed data from the NIST Adsorption Database. Target variables are fitted parameters.
type: object
properties:
  adsorbate_name:
    type: string
    description: Name of the adsorbate gas.
  adsorbent_material:
    type: string
    description: Identifier for the adsorbent material.
  temperature:
    type: number
    format: float
    unit: "K"
    description: Temperature at which adsorption was measured.
  pressure:
    type: number
    format: float
    unit: "kPa"
    description: Pressure at which adsorption was measured.
  amount_adsorbed:
    type: number
    format: float
    unit: "mmol/g"
    description: Amount of adsorbate adsorbed per gram of adsorbent.
  polarizability:
    type: number
    format: float
    unit: "Å³"
    description: Polarizability of the adsorbate molecule (calculated via RDKit).
  molecular_weight:
    type: number
    format: float
    unit: "g/mol"
    description: Molecular weight of the adsorbate (calculated via RDKit).
  surface_area:
    type: number
    format: float
    unit: "m²/g"
    description: Surface area of the adsorbent material (from metadata).
  pore_volume:
    type: number
    format: float
    unit: "cm³/g"
    description: Pore volume of the adsorbent material (from metadata).
  langmuir_capacity:
    type: number
    format: float
    unit: "mmol/g"
    description: Langmuir capacity parameter (Q_max) FITTED from raw isotherm data.
  henry_constant:
    type: number
    format: float
    unit: "kPa⁻¹"
    description: Henry constant (K_H) FITTED from raw isotherm data.

required:
  - adsorbate_name
  - adsorbent_material
  - temperature
  - pressure
  - amount_adsorbed
  - polarizability
  - molecular_weight
  - surface_area
  - langmuir_capacity
  - henry_constant
```

## Data Relationships

The dataset is structured as a collection of adsorption measurements, where each row represents an observation for a specific adsorbate/adsorbent pair at a given temperature and pressure. The primary key is a composite key consisting of `adsorbate_name`, `adsorbent_material`, `temperature`, and `pressure`.

## Assumptions

*   All descriptors are calculated using consistent units (as specified in the schema).
*   Missing values have been handled during data preprocessing (e.g., exclusion, not imputation).
*   Target variables (`langmuir_capacity`, `henry_constant`) are derived quantities with associated fitting uncertainty (not included in this schema but tracked in logs).