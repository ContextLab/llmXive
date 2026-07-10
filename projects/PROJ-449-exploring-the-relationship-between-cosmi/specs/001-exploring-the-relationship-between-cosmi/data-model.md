# Data Model: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

## Entity Definitions

### CosmicRayFlux
Represents the daily/weekly/monthly averaged, rigidity-binned differential flux for a specific particle species.

- **date**: `datetime` (YYYY-MM-DD)
- **species**: `string` (enum: "proton", "helium", "heavy")
- **rigidity_bin**: `string` (e.g., "1-2 GV", "2-4 GV")
- **flux_value**: `float` (differential flux in particles/(m²·s·sr·GV))
- **uncertainty**: `float` (statistical uncertainty)
- **source**: `string` (e.g., "AMS-02")
- **time_resolution**: `string` (e.g., "daily", "weekly", "monthly")

### SolarActivityIndex
Represents the daily sunspot number and solar wind parameters.

- **date**: `datetime` (YYYY-MM-DD)
- **sunspot_number**: `float` (daily sunspot number)
- **solar_wind_speed**: `float` (km/s, optional)
- **source**: `string` (e.g., "NOAA/SWPC")

### CompositionRatio
Represents the derived ratio between two species.

- **date**: `datetime` (YYYY-MM-DD)
- **numerator_species**: `string` (e.g., "helium", "heavy")
- **denominator_species**: `string` (e.g., "proton")
- **ratio_value**: `float`
- **lag_analysis_results**: `object` (correlation coefficients, p-values for each lag)

## Data Flow

1. **Raw Data Ingestion**:
   - `raw/ams02_flux.csv`: Raw AMS-02 flux data (daily/weekly/monthly, rigidity-binned).
   - `raw/noaa_sunspots.csv`: Raw NOAA sunspot number data.

2. **Preprocessing**:
   - `processed/aligned_data.csv`: Merged dataset with `date`, `species`, `rigidity_bin`, `flux_value`, `sunspot_number`.
   - `processed/ratios.csv`: Derived composition ratios (He/p, Fe/p).

3. **Analysis Output**:
   - `results/correlation_matrix.csv`: Correlation coefficients and p-values for all lags and rigidity bins (with $N_{eff}$ correction).
   - `results/bootstrap_ci.json`: 95% confidence intervals from Moving Block Bootstrap.
   - `results/model_fit.json`: Fitted parameters and R² value for the diffusion model.

## Data Hygiene

- **Checksums**: All raw and processed files will be checksummed (SHA-256) and recorded in `data/checksums.txt`.
- **Immutability**: Raw data files are never modified. Derivations create new files.
- **Versioning**: Each analysis run produces a new versioned output directory (e.g., `results/v1.0/`, `results/v1.1/`).