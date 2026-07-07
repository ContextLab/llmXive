# Data Model: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Entity Definitions

### PlanetRecord
Represents a single exoplanet observation after filtering.
- `planet_id` (string): Unique identifier (e.g., "Kepler-1234.01").
- `radius` (float): Planet radius in Earth radii ($R_{\oplus}$).
- `radius_uncertainty` (float): Uncertainty in radius.
- `period` (float): Orbital period in days.
- `period_uncertainty` (float): Uncertainty in period.
- `stellar_radius` (float): Stellar radius in solar radii ($R_{\odot}$).
- `stellar_mass` (float): Stellar mass in solar masses ($M_{\odot}$).
- `stellar_temp` (float): Stellar effective temperature in Kelvin.
- `flux` (float): Incident flux (calculated).
- `completeness_weight` (float, optional): Inverse probability weight from completeness map. Defaults to 1.0 if data unavailable.
- `log_period` (float): Log10 of orbital period.
- `confirmed` (boolean): Whether the planet is confirmed.

### PeriodBin
Represents a binned aggregation of planets.
- `bin_id` (integer): Bin index (0-9).
- `bin_center_log_period` (float): Center of the log-period bin.
- `weighted_mean_log_period` (float): Weighted mean of log-periods in the bin.
- `planet_count` (integer): Number of planets in the bin.
- `gap_location` (float): Estimated gap radius ($R_{\oplus}$).
- `gap_uncertainty` (float): 95% CI half-width of the gap location.
- `is_unresolved` (boolean): True if BIC difference < 10 or peak separation < 0.1 R_earth.
- `synthetic_validation_status` (string): "PASS" if GMM/KDE on synthetic data matches ground truth, else "FAIL".

### GapAnalysisResult
Final aggregated results.
- `measured_slope` (float): Slope of `log(gap_radius)` vs `log(period)`.
- `slope_uncertainty` (float): Standard error of the slope.
- `mc_p_value_photoevaporation` (float): Monte Carlo percentile p-value vs Owen & Wu model.
- `mc_p_value_core_powered` (float): Monte Carlo percentile p-value vs Ginzburg et al. model.
- `synthetic_validation_status` (string): "PASS" if method recovers ground truth in synthetic data, else "FAIL".
- `stability_status` (string): "PASS" if |GMM - KDE| ≤ 0.05 $R_{\oplus}$ on synthetic data, else "FAIL".
- `vif_max` (float): Maximum Variance Inflation Factor among predictors.

## Data Flow

1.  **Raw Ingestion**: `kepler_dr25.csv` + `kepler_dr25_validation.csv` + `kic.csv` → Merged DataFrame.
2.  **Filtering**: Apply uncertainty thresholds (<20% radius, <1% period) and missing data exclusion → `filtered_planets.csv`.
3.  **Weighting**: Apply Inverse Probability Weights (IPW) from completeness map (or default to 1.0) → `weighted_planets.csv`.
4.  **Binning**: Log-spaced binning + merge logic → `binned_planets.csv`.
5.  **Gap Estimation**: GMM + Bootstrap + Synthetic Validation → `gap_estimates.csv`.
6.  **Regression & Testing**: Weighted regression + Monte Carlo Percentile Test → `final_results.json`.

## Storage Format

- **Raw Data**: CSV (UTF-8), checksummed.
- **Processed Data**: CSV (UTF-8) for tabular data; JSON for final results.
- **Artifacts**: All files stored in `data/` with content hashes recorded in `state/`.