# Data Model: Investigating the Correlation Between Muon Flux and Atmospheric Temperature Profiles

## Entity Relationships

The data model follows a linear transformation pipeline:
`Raw IceCube` + `Raw ERA5` -> `Aligned Dataset` -> `Analysis Results`

### 1. MuonTimeSeries (Raw Input)
Represents the raw muon flux data from IceCube.
- **Attributes**:
  - `date` (datetime): The date of the observation.
  - `count` (float): Total muon counts for the day.
  - `uncertainty` (float): Statistical uncertainty (e.g., $\sqrt{count}$).
  - `quality_flag` (string): Status (e.g., "valid", "calibration", "maintenance").
  - `energy_threshold` (float, optional): Minimum energy threshold applied (e.g., 1000 GeV).

### 2. AtmosphericProfile (Raw Input)
Represents the raw atmospheric data from ERA5.
- **Attributes**:
  - `date` (datetime): The date of the observation.
  - `pressure_levels` (dict): Map of pressure (hPa) to temperature (K).
  - `mean_temp` (float): Mean temperature across all levels (derived).
  - `vertical_gradient` (float): Temperature change per km (derived).

### 3. EffectiveTemperature (Derived)
Represents the calculated $T_{eff}$ metric.
- **Attributes**:
  - `date` (datetime): Date of calculation.
  - `t_eff_value` (float): Calculated effective temperature (K or C).
  - `weight_function_version` (string): Identifier for the $W(z)$ used (e.g., "Grieder1985").
  - `interpolation_used` (bool): True if linear interpolation was required for missing levels.

### 4. AlignedDataset (Processed)
The merged dataset ready for analysis.
- **Attributes**:
  - `date` (datetime): Primary key.
  - `muon_count` (float): Aligned muon count.
  - `t_eff_value` (float): Aligned $T_{eff}$.
  - `season_flag` (string): "Summer" or "Winter".
  - `exclusion_reason` (string): If excluded, reason (e.g., "missing_era5", "low_energy").
  - `pre_whitened_residual_muon` (float): Residual from AR(1) model.
  - `pre_whitened_residual_teff` (float): Residual from AR(1) model.

### 5. CorrelationResult (Analysis Output)
- **Attributes**:
  - `metric_pair` (string): e.g., "flux_vs_t_eff".
  - `correlation_type` (string): "Pearson" or "Spearman".
  - `r_value` (float): Correlation coefficient.
  - `p_value` (float): Significance level.
  - `sample_size` (int): Number of data points.
  - `pre_whitened` (bool): True if AR(1) residuals were used.

### 6. RegressionModel (Analysis Output)
- **Attributes**:
  - `slope` (float): Temperature coefficient.
  - `intercept` (float): Baseline flux.
  - `r_squared` (float): Goodness of fit.
  - `slope_ci_lower` (float): 95% CI lower bound (Newey-West).
  - `slope_ci_upper` (float): 95% CI upper bound (Newey-West).
  - `season` (string): "All", "Summer", or "Winter".
  - `method` (string): "OLS with Newey-West SEs".

## Data Flow Diagram (Text)

```
[IceCube Parquet] --(Ingest)--> [MuonTimeSeries] --(Filter Energy)--> [Clean Muon]
                                                                  |
[ERA5 HDF5]     --(Ingest)--> [AtmosphericProfile] --(Calc T_eff)--> [EffectiveTemperature]
                                                                  |
                                                                  v
                                                  [AlignedDataset] (Join on Date)
                                                                  |
                                                  +---------------+---------------+
                                                  |               |               |
                                          [Pre-whiten]   [Pre-whiten]   [Season Split]
                                                  |               |               |
                                                  v               v               v
                                          [Residuals]     [Residuals]     [Subsets]
                                                  |               |               |
                                                  v               v               v
                                          [Correlation]   [Regression]   [Sensitivity]
                                                  |               |               |
                                                  v               v               v
                                          [CorrelationResult] [RegressionModel] [SensitivityResult]
```

## Constraints

- **Temporal Resolution**: All analysis is performed on **daily** bins.
- **Data Integrity**: Rows with `null` in either `muon_count` or `t_eff_value` are excluded.
- **Precision**: Float64 for all numerical calculations.
- **Date Format**: ISO 8601 (`YYYY-MM-DD`).
- **Energy Threshold**: Default filter E > 1 TeV (if data available).