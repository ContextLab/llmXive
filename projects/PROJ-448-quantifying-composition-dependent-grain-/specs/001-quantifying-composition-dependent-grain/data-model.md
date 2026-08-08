# Data Model: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

## Overview

This document defines the data structures used to represent the segregation profiles, alloy systems, and regression models. These structures ensure strict adherence to the project's data hygiene and reproducibility principles.

## Core Entities

### 1. SegregationProfile

Represents a single computed equilibrium state.

**Attributes**:
*   `solute_element` (str): The segregating element (e.g., "Cr", "Mo").
*   `temperature_K` (float): Temperature in Kelvin.
*   `bulk_concentration` (float): Bulk atomic fraction (0.0 to 1.0).
*   `segregation_energy_eV` (float): Surrogate-derived segregation energy (eV).
*   `equilibrium_concentration` (float): Calculated GB concentration (atomic fraction).
*   `system_id` (str): Identifier for the alloy system (e.g., "Fe-Cr-Mo").
*   `source` (str): "surrogate_calculated", "thermodynamic_proxy", or "literature".
*   `interaction_coefficient_truth` (float, optional): The ground-truth interaction coefficient injected during data generation (used for validation).

### 2. AlloySystem

Represents a specific chemical system configuration.

**Attributes**:
*   `base_element` (str): "Fe".
*   `solute_elements` (list[str]): List of solutes (e.g., ["Cr", "Mo"]).
*   `calphad_database_id` (str): Identifier for the thermodynamic database used (e.g., "tcfe9_open", "pycalphad_open").
*   `temperature_range` (list[float]): [min_K, max_K].
*   `supercell_model` (str): Identifier for the GB supercell model (e.g., "Sigma5_310").

### 3. RegressionModel

Represents the fitted empirical function.

**Attributes**:
*   `system_id` (str): The alloy system.
*   `coefficients` (dict[str, float]): Map of feature names to coefficients.
*   `interaction_terms` (list[str]): List of interaction term names (e.g., "Cr*Mo").
*   `r_squared` (float): R-squared metric.
*   `p_values` (dict[str, float]): P-values for each coefficient.
*   `cross_validation_scores` (list[float]): R-squared scores for each fold.
*   `held_out_mse_reduction` (float): Percentage reduction in MSE vs. additive model.
*   `validation_type` (str): "binary_validation" or "sensitivity_analysis".
*   `recovered_interaction_coefficient` (float): The coefficient recovered by the model for the injected term.
*   `injected_interaction_coefficient` (float): The ground-truth value injected during data generation.

## Data Flow

1.  **Input**: `AlloySystem` config + `Open Proxy` parameters.
2.  **Process**: `Surrogate` calculation (geometry + energy) + **Interaction Injection** -> `McLean` calculation -> `SegregationProfile` generation.
3.  **Process**: `Regression` fitting -> `RegressionModel` generation.
4.  **Output**: `SegregationProfile` list, `RegressionModel` object, Heatmaps.

## File Formats

*   **Raw Data**: JSON (for flexibility) or CSV (for tabular data).
*   **Manifest**: JSON (`data_manifest.json`).
*   **Models**: JSON (for coefficients and metadata).