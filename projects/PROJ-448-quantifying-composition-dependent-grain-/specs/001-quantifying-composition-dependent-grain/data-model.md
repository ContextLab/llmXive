# Data Model: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

## Overview

This document defines the data structures, schemas, and relationships used in the project. All data flows from `data/raw/` (immutable) to `data/derived/` (computed) and is validated against the contracts defined in `contracts/`.

## Core Entities

### 1. SegregationProfile
Represents a single computed equilibrium segregation state.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `solute_element` | str | The segregating element (e.g., "Cr", "Mo") | Must be in [Cr, Mo, V, W] |
| `base_element` | str | The matrix element (e.g., "Fe") | Must be "Fe" |
| `temperature_K` | float | Temperature in Kelvin | Range: 500.0 - 900.0 |
| `bulk_concentration` | float | Bulk atomic fraction of solute | Range: 0.0 - 1.0 |
| `segregation_energy_eV` | float | DFT-derived segregation energy | Source: Literature |
| `equilibrium_concentration` | float | Calculated GB concentration | Range: 0.0 - 1.0 |
| `system_id` | str | Alloy system identifier (e.g., "Fe-Cr-Mo") | Binary or Ternary |
| `gb_structure` | str | Grain boundary structure ID | e.g., "Sigma5(310)" |
| `source_doi` | str | DOI of the DFT source | Required |

### 2. AlloySystem
Represents the chemical system configuration.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `system_id` | str | Unique identifier (e.g., "Fe-Cr-Mo") |
| `base_element` | str | Base element (Fe) |
| `solute_elements` | list[str] | List of solutes (e.g., ["Cr", "Mo"]) |
| `calphad_db_id` | str | Identifier for the CALPHAD database used |
| `temperature_range` | tuple[float, float] | Min and Max temperature |

### 3. RegressionModel
Represents the fitted empirical model.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `model_id` | str | Unique identifier |
| `coefficients` | dict[str, float] | Mapping of term name to coefficient |
| `interaction_terms` | list[str] | List of interaction terms included |
| `r_squared` | float | R-squared value on training set |
| `cv_scores` | list[float] | R-squared scores for each CV fold |
| `p_values` | dict[str, float] | P-values for each coefficient |
| `held_out_mse` | float | MSE on held-out test set |
| `mse_reduction` | float | % reduction vs additive model |

## Data Flow

1.  **Ingestion**: `data_loader.py` fetches raw data (CALPHAD params, DFT energies) into `data/raw/`.
2.  **Validation**: `validator.py` checks checksums and schema compliance.
3.  **Computation**: `calculator.py` generates `SegregationProfile` objects and writes to `data/derived/segregation_profiles.csv`.
4.  **Analysis**: `regression.py` fits models and writes `data/derived/regression_results.json`.
5.  **Manifest**: `data_manifest.json` is updated with all source DOIs and checksums.

## Contracts

The following contracts define the strict schema for data validation. See `contracts/` for the YAML definitions.

*   `contracts/segregation_profile.schema.yaml`: Validates individual profile records.
*   `contracts/regression_model.schema.yaml`: Validates model output.
*   `contracts/data_manifest.schema.yaml`: Validates the data source manifest.