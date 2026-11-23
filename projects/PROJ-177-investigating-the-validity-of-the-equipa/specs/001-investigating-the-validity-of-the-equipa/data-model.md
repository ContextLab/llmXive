# Data Model: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Entity Relationship Overview

The data model is designed to support the flow from raw kinematic data to statistical conclusions.

1.  **Raw Data**: Particle tracking CSVs (positions, orientations) and driving signal logs.
2.  **Derived Data**: `EnergySample` records (calculated energy components per particle per frame).
3.  **Aggregated Data**: `EnergyDistribution` statistics (mean, variance) per bin.
4.  **Results**: `StatisticalResult` and `RegressionResult` objects.

## Core Entities

### ParticleState
Represents a single particle at a single time step.
- `particle_id`: Integer (unique ID)
- `timestamp`: Float (seconds)
- `position_x`, `position_y`, `position_z`: Float (meters)
- `orientation_theta`: Float (radians)
- `material_type`: String ("steel", "glass", "polymer")
- `mass`: Float (kg)
- `moment_of_inertia`: Float (kg·m²)

### EnergySample
Derived entity storing computed energy values.
- `sample_id`: Integer
- `particle_id`: Integer
- `timestamp`: Float
- `E_trans`: Float (Joules)
- `E_rot`: Float (Joules)
- `E_pot`: Float (Joules)
- `E_vib`: Float (Joules)
- `frequency_bin`: Integer (e.g., 10 for 10Hz)
- `is_excluded`: Boolean (true if non-stationary or missing data)

### StatisticalResult
Outcome of hypothesis tests.
- `bin_id`: String (e.g., "steel_10Hz")
- `test_type`: String ("KS", "ChiSq", "Ratio")
- `statistic_value`: Float
- `p_value_raw`: Float
- `p_value_corrected`: Float (Permutation-based FDR)
- `is_significant`: Boolean
- `null_hypothesis`: String ("Equipartition holds")

### RegressionResult
Outcome of linear regression.
- `model_id`: String
- `slope`: Float
- `intercept`: Float
- `r_squared`: Float
- `slope_p_value`: Float
- `model_fit_quality`: String ("Good", "Poor")

## Data Flow

1.  **Ingestion**: `raw_data.csv` -> `ParticleState` (in memory).
2.  **Calculation**: `ParticleState` -> `EnergySample` (stored in `data/derived/energy_samples.csv`).
3.  **Binning**: `EnergySample` -> Grouped by `frequency_bin` and `material_type`.
4.  **Testing**: Grouped data -> `StatisticalResult` (stored in `data/derived/statistical_results.json`).
5.  **Regression**: `StatisticalResult` (aggregated deviations) -> `RegressionResult` (stored in `data/derived/regression_results.json`).

## Constraints & Validation

- **Time Continuity**: Gaps in `timestamp` > 2 frames trigger interpolation or exclusion flags.
- **Energy Units**: All energy values must be in Joules.
- **Frequency Bins**: Must be discrete (5Hz intervals).
- **Missing Data**: Any `NaN` in `E_trans`, `E_rot`, etc., must be flagged and excluded from statistical tests.
