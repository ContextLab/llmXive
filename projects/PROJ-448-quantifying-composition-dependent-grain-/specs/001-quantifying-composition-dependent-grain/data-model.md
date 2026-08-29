# Data Model: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

## Overview

This document defines the data structures used to represent segregation profiles, alloy systems, and regression models. All data is stored in JSON/Parquet formats under `data/`.

## Key Entities

### 1. SegregationProfile

Represents the computed equilibrium concentration at the grain boundary for a specific solute, temperature, and bulk composition.

**Attributes**:
- `solute_element` (str): e.g., "Cr", "Mo".
- `temperature_K` (float): Temperature in Kelvin (500-900).
- `bulk_concentration` (float): Atomic fraction of solute in bulk (0.0-1.0).
- `segregation_energy_eV` (float): DFT-derived segregation energy (negative for segregation).
- `equilibrium_concentration` (float): Calculated GB concentration (0.0-1.0).
- `system_id` (str): e.g., "Fe-Cr-Mo".
- `source` (str): "dft_surrogate" or "experimental".
- `interaction_coefficient_truth` (float, optional): Ground-truth interaction coefficient for synthetic data.

### 2. AlloySystem

Represents a specific chemical system.

**Attributes**:
- `base_element` (str): "Fe".
- `solute_elements` (list[str]): e.g., ["Cr", "Mo"].
- `calphad_database_id` (str): "OpenCalphad-Reduced".
- `temperature_range` (dict): `{"min": 500, "max": 900}`.

### 3. RegressionModel

Represents the fitted empirical function.

**Attributes**:
- `coefficients` (dict): Mapping of feature names to coefficients.
- `interaction_terms` (list[str]): e.g., ["Cr-Mo", "Cr-V"].
- `r_squared` (float): Model fit on training set.
- `p_values` (dict): p-values for each coefficient.
- `cross_validation_scores` (list[float]): R² for each of 5 folds.
- `held_out_mse_reduction` (float): % reduction vs. additive model.

## Data Flow

1.  **Input**: `data/raw/calphad_params.json` (Bulk compositions), `data/raw/dft_energies.json` (Energies).
2.  **Process**: `code/services/segregation_engine.py` combines inputs to generate `SegregationProfile` objects.
3.  **Output**: `data/processed/segregation_profiles.parquet`.
4.  **Analysis**: `code/services/analysis_engine.py` fits models and outputs `data/processed/regression_results.json`.

## Validation Rules

- `bulk_concentration` must be $\in [0.0, 1.0]$.
- `equilibrium_concentration` must be $\in [0.0, 1.0]$ (capped if >1.0).
- `temperature_K` must be $\in [500, 900]$.
- `segregation_energy_eV` must be a float (typically negative).