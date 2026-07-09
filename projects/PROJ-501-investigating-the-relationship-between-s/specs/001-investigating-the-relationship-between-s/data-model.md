# Data Model: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

## 1. Entity Definitions

### FlareEvent
Represents a single stellar flare detection.
- `star_id` (str): Unique identifier for the host star (e.g., TIC ID).
- `timestamp` (datetime): Time of flare detection.
- `energy` (float): Bolometric energy of the flare in ergs.
- `duration` (float): Duration of the flare in seconds.

### ExoplanetSystem
Represents a planet orbiting a host star.
- `planet_id` (str): Unique planet identifier.
- `star_id` (str): Foreign key to FlareEvent.
- `radius` (float): Planetary radius in cm.
- `mass` (float): Planetary mass in grams.
- `semi_major_axis` (float): Semi-major axis in cm.
- `host_type` (str): Spectral type (e.g., "M", "K", "G").
- `density` (float): Calculated bulk density in g/cm³.
- `system_age` (float): Estimated age in Gyr (may be default).
- `age_uncertain` (bool): True if age was imputed/defaulted.
- `flux_uncertain` (bool): True if quiescent flux was estimated via proxy.

### AnalysisResult
Computed metrics for a single system.
- `star_id` (str): Star identifier.
- `cumulative_flux` (float): Total XUV flux in erg/s/cm².
- `mass_loss_rate` (float): $\dot{M}$ in kg/s.
- `aei` (float): Atmospheric Erosion Index (dimensionless, normalized by binding energy).
- `is_valid` (bool): True if mass loss is physically plausible (<10% mass/Gyr).
- `aei_uncertain` (bool): True if AEI was calculated with uncertain age.

## 2. Data Flow

1. **Raw Ingestion**:
   - `data/raw/ma_st_flare_catalog.csv` (from MAST API)
   - `data/raw/nasa_exoplanet_archive.csv` (from NASA API)
2. **Derived Processing**:
   - `data/processed/filtered_m_dwarfs.csv` (M-dwarfs with $\ge$10 flares, no nulls, uncertainty flags)
   - `data/processed/analysis_results.csv` (Flux, Mass Loss, AEI)
3. **Final Output**:
   - `data/results/correlation_stats.json` (Correlation coefficient, p-value, sensitivity results, residual stats)
   - `data/results/plot_flux_aei.png` (Scatter plot of Flux vs. AEI Residuals)

## 3. Validation Rules

- **Completeness**: All rows in `analysis_results.csv` must have non-null `cumulative_flux`, `mass_loss_rate`, `aei`.
- **Range**: `aei` must be positive.
- **Physical Plausibility**: Rows with `is_valid == False` are excluded from the final correlation analysis.
- **Consistency**: `star_id` in `analysis_results` must exist in `filtered_m_dwarfs`.
- **Uncertainty Handling**: Records with `aei_uncertain=True` or `flux_uncertain=True` are flagged and may be excluded from the primary analysis.