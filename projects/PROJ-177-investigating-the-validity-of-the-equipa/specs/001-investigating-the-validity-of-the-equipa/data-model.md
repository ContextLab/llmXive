# Data Model: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Entity Definitions

### 1. ParticleFrame
Represents a single particle at a specific timestamp.
- `particle_id`: int (unique identifier for the particle)
- `timestamp`: float (seconds)
- `position_x`: float (float32)
- `position_y`: float (float32)
- `position_z`: float (float32)
- `orientation_theta`: float (float32)
- `material_type`: str (e.g., "steel", "glass")
- `driving_frequency`: float (Hz) (global parameter)
- `velocity_x`: float (float32, derived)
- `velocity_y`: float (float32, derived)
- `velocity_z`: float (float32, derived)
- `angular_velocity`: float (float32, derived)
- `mass`: float (float64, derived or provided)
- `moment_of_inertia`: float (float64, derived)
- `friction_coefficient`: float (float32, from synthetic generator)
- `E_trans`: float (float64, Joules)
- `E_rot`: float (float64, Joules)
- `E_pot`: float (float64, Joules)
- `diff_E`: float (float64, derived: `E_trans - E_rot`)
- `ratio_E`: float (float64, derived: `E_trans / E_rot`)

### 2. EnergyBin
Aggregated statistics for a specific frequency and material combination.
- `frequency_bin`: str (e.g., "5Hz", "10Hz")
- `material_type`: str
- `n_frames`: int
- `mean_E_trans`: float
- `mean_E_rot`: float
- `std_E_trans`: float
- `std_E_rot`: float
- `mean_diff_E`: float (mean of `diff_E`)
- `std_diff_E`: float (std of `diff_E`)
- `ratio_mean`: float ($mean\_E\_trans / mean\_E\_rot$)
- `t_statistic`: float (from paired t-test)
- `p_value_raw`: float
- `p_value_corrected`: float (Holm-Bonferroni)
- `ks_statistic`: float (from KS test)
- `ks_p_value`: float
- `is_significant`: bool

### 3. StatisticalResult
Output of a specific hypothesis test or regression.
- `test_type`: str (e.g., "paired-t-test", "ANOVA", "regression", "KS-test")
- `bin_id`: str (frequency + material)
- `statistic_value`: float
- `raw_p_value`: float
- `corrected_p_value`: float
- `degrees_of_freedom`: int
- `confidence_interval_low`: float
- `confidence_interval_high`: float
- `effect_size`: float (Cohen's d for paired differences)

## Data Flow

1. **Ingestion**: Raw CSV/Parquet $\rightarrow$ `ParticleFrame` (with missing values handled).
2. **Derivation**: `ParticleFrame` $\rightarrow$ Calculate velocities, mass, $I$, $E_{trans}$, $E_{rot}$, $E_{pot}$, `diff_E`, `ratio_E`.
3. **Binning**: `ParticleFrame` $\rightarrow$ Group by `frequency_bin` + `material_type` $\rightarrow$ `EnergyBin` aggregates.
4. **Testing**: `EnergyBin` $\rightarrow$ Run **Paired t-test**, **KS test**, ANOVA $\rightarrow$ `StatisticalResult`.
5. **Sensitivity**: `StatisticalResult` $\rightarrow$ Sweep $\alpha$ $\rightarrow$ Summary Table.

## Constraints & Validations

- **Mass Derivation**: If `mass` is missing, derive from `material_type` and `r=2.5mm`. If `material_type` is unknown, raise error.
- **Frequency Binning**: 5Hz intervals (e.g., 0-5, 5-10). 0Hz bins excluded from ratio test.
- **Missing Data**: If velocity cannot be calculated (gaps > threshold), mark frame as invalid or interpolate.
- **Precision**: Coordinates stored as float32 to save memory; energies and derived statistics stored as float64 for accuracy.
- **Chunking**: Data processed in chunks of 100k frames to fit within 7GB RAM. This is the primary execution path.