# Data Model: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Branch**: `001-born-model-solvation-comparison` | **Date**: 2026-06-26

## Entity Definitions

### IonSolventPair

Represents a single experimental measurement of solvation free energy for an ion in a solvent.

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| ion_id | string | Yes | Unique ion identifier (e.g., "Na+", "Cl-") | Shannon radii database |
| solvent_id | string | Yes | Unique solvent identifier (e.g., "water", "ethanol") | NIST/CRC Handbook |
| experimental_delta_g | float | Yes | Experimental solvation free energy (kcal/mol) | NIST/CRC Handbook |
| experimental_uncertainty | float | Yes | Uncertainty estimate for experimental value (kcal/mol) | NIST/CRC Handbook |
| temperature_celsius | float | Yes | Measurement temperature (°C) | NIST/CRC Handbook |
| temperature_uncertainty | float | Yes | Temperature uncertainty (°C) | NIST/CRC Handbook |
| source_reference | string | Yes | Citation for this measurement | NIST/CRC Handbook |
| data_quality_flag | string | Yes | "complete" or "uncertainty_missing" | Computed |

### BornPrediction

Represents a theoretical Born model calculation for an ion-solvent pair.

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| ion_id | string | Yes | Unique ion identifier (matches IonSolventPair) | Input |
| solvent_id | string | Yes | Unique solvent identifier (matches IonSolventPair) | Input |
| ionic_radius_angstrom | float | Yes | Ionic radius (Å) | Shannon radii database |
| radius_uncertainty_angstrom | float | Yes | Radius uncertainty (Å) | Shannon radii database |
| dielectric_constant | float | Yes | Solvent dielectric constant (dimensionless) | NIST/CRC Handbook |
| dielectric_uncertainty | float | Yes | Dielectric constant uncertainty | NIST/CRC Handbook |
| ion_charge | integer | Yes | Ion charge (e.g., +1, -1) | Input |
| predicted_delta_g | float | Yes | Born model prediction (kcal/mol) | Computed |
| predicted_delta_g_uncertainty | float | Yes | Propagated uncertainty in predicted ΔG (kcal/mol) | Computed via error propagation |
| prediction_method | string | Yes | "born_continuum" | Hardcoded |

### ResidualAnalysis

Represents regression output comparing Born predictions to experimental values.

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| ion_id | string | Yes | Unique ion identifier | Input |
| solvent_id | string | Yes | Unique solvent identifier | Input |
| residual | float | Yes | Experimental - theoretical (kcal/mol) | Computed |
| residual_relative | float | Yes | Residual / |experimental_delta_g| (dimensionless) | Computed |
| combined_uncertainty | float | Yes | Combined experimental + predicted uncertainty (kcal/mol) | Computed |
| within_measurement_error | boolean | Yes | True if |residual| < combined_uncertainty | Computed |
| ion_size_class | string | Yes | Categorical size class (e.g., "small", "medium", "large") | Computed |
| solvent_class | string | Yes | Categorical solvent class (e.g., "water", "alcohol", "aprotic") | Computed |
| p_value | float | Yes | Statistical significance from regression | Computed |
| multiple_comparison_corrected | boolean | Yes | Whether MFC was applied | Computed |
| breakdown_flag | boolean | Yes | True if residual exceeds RMSE threshold | Computed |

## File Schema

### data/experimental_solvation.csv

| Column | Type | Description |
|--------|------|-------------|
| ion_id | string | Ion identifier |
| solvent_id | string | Solvent identifier |
| experimental_delta_g | float | Experimental ΔG (kcal/mol) |
| experimental_uncertainty | float | Uncertainty (kcal/mol) |
| temperature_celsius | float | Temperature (°C) |
| source_reference | string | Citation |

### data/born_predictions.csv

| Column | Type | Description |
|--------|------|-------------|
| ion_id | string | Ion identifier |
| solvent_id | string | Solvent identifier |
| ionic_radius_angstrom | float | Ionic radius (Å) |
| radius_uncertainty_angstrom | float | Radius uncertainty (Å) |
| dielectric_constant | float | Dielectric constant |
| dielectric_uncertainty | float | Dielectric uncertainty |
| ion_charge | integer | Ion charge |
| predicted_delta_g | float | Born prediction (kcal/mol) |
| predicted_delta_g_uncertainty | float | Propagated uncertainty (kcal/mol) |
| prediction_method | string | Method identifier |

### data/parameters.csv

| Column | Type | Description |
|--------|------|-------------|
| parameter_name | string | Name (e.g., "elementary_charge", "vacuum_permittivity") |
| value | float | Numerical value |
| unit | string | Unit of measurement |
| source | string | Source citation |
| temperature_celsius | float | Temperature condition |

### code/requirements.txt

| Package | Version | Description |
|---------|---------|-------------|
| pandas | pinned | Data manipulation |
| numpy | pinned | Numerical operations |
| scipy | pinned | Statistical functions |
| matplotlib | pinned | Plot generation |
| scikit-learn | pinned | Regression analysis |
| pyyaml | pinned | Schema validation |

## Data Flow

1. **Raw Data Download** → data/raw/ (checksummed) - stores IonSolventPair raw records from NIST/CRC/Shannon
2. **Compilation** → data/experimental_solvation.csv (derived) - IonSolventPair entity
3. **Parameter Extraction** → data/parameters.csv (derived) - physical constants with citations
4. **Born Calculation** → code/born_calculator.py → data/born_predictions.csv - BornPrediction entity with uncertainty propagation
5. **Residual Analysis** → code/regression_analysis.py → data/residual_analysis.csv - ResidualAnalysis entity
6. **Diagnostic Plots** → code/diagnostics.py → figures/ - visualization artifacts

## Assumptions

- All experimental values measured at controlled temperature (±0.5°C) or temperature specifications available for dielectric constant correction
- Ionic radii from Shannon database are consistent across all ions; crystal radii may differ from effective solvated radii (documented)
- All required variables (experimental ΔG, solvent ε, ionic radius r, ion charge z) exist in compiled dataset; missing pairs excluded per Assumptions
- Single-ion absolute solvation energies NOT experimentally measurable; all measurements normalized using extra-thermodynamic assumption (documented)
- Extra-thermodynamic assumption (TPA⁺/TPB⁻ convention) carries systematic uncertainty of ±3-5 kcal/mol affecting all single-ion values