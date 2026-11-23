# Data Model: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Overview
All artifacts live under the `data/` hierarchy:

- `data/raw/` – immutable source files (Pantheon+ release).  
- `data/processed/` – derived tables, maps, and simulation outputs.  
- `data/reports/` – human‑readable final report and JSON summary.

Each file is validated against a JSON/YAML schema located in `contracts/`.

## Entity Schemas

### 1. `residuals.csv`
| Field | Type | Description |
|------|------|-------------|
| `id` | string | Supernova identifier (e.g., SN name). |
| `ra` | float | Right Ascension (degrees, 0 ≤ ra < 360). |
| `dec` | float | Declination (degrees, –90 ≤ dec ≤ 90). |
| `z` | float | Redshift (≥ 0). |
| `mu_obs` | float | Observed distance modulus. |
| `mu_err` | float | Uncertainty on the distance modulus (≥ 0). |
| `mu_th` | float | Theoretical distance modulus from flat ΛCDM. |
| `residual` | float | μ_obs − μ_th. |
| `valid` | boolean | True if the row passed all filters. |
*Conforms to `contracts/residuals.schema.yaml`.*

### 2. `healpix_map.fits`
A FITS binary table, one row per pixel (Nside = 32).

| Column | Type | Description |
|--------|------|-------------|
| `pixel_index` | integer | HEALPix pixel index. |
| `nside` | integer | Fixed to 32. |
| `mean_residual` | float | Inverse‑variance‑weighted mean residual (mag). |
| `count` | integer | Number of SNe contributing to the pixel. |
| `mask_value` | integer | 1 = used in analysis, 0 = masked. |
*Conforms to `contracts/healpix_map.schema.yaml`.*

### 3. `simulation_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| `run_id` | integer | Simulation iteration (starting at 1). |
| `dipole_amp` | float | Dipole amplitude (mag) for this mock. |
| `quadrupole_amp` | float | Quadrupole amplitude (mag) for this mock. |
*Conforms to `contracts/simulation_results.schema.yaml`.*

### 4. `power_analysis_results.csv` **(new)**
| Column | Type | Description |
|--------|------|-------------|
| `scenario` | string | Description of the power‑analysis scenario (e.g., `analytic`, `pilot_mc`). |
| `detectable_dipole_amp` | float | Minimum dipole amplitude (mag) detectable at p < 0.05 with ≥ 80 % power. |
| `n_sne` | integer | Number of supernovae used in the scenario. |
| `sigma_residual` | float | Assumed residual dispersion (mag) used in the analytic estimate. |
| `method` | string | `analytic` or `monte_carlo`. |
*Conforms to `contracts/power_analysis_results.schema.yaml`.*

### 5. `analysis_result.json`
A JSON object summarising the final scientific outcome.  
*Conforms to `contracts/analysis_result.schema.yaml`.*

### 6. `final_report.txt`
Plain‑text report containing observed amplitudes, p‑values, and the significance flag.  
*Conforms to `contracts/final_report.schema.yaml`.*

## Data Flow Diagram
```
download → data/raw/pantheon_plus.dat
      ↓
ingestion & residuals → data/processed/residuals.csv
      ↓
HEALPix projection → data/processed/healpix_map.fits
      ↓
anisotropy estimators → (in‑memory amplitudes)
      ↓
null simulations → data/processed/simulation_results.csv
      ↓
significance & reporting → data/reports/final_report.txt
                               data/reports/analysis_result.json
```
The optional **Power‑Analysis** step runs **before** the main pipeline and produces
`power_analysis_results.csv`, informing interpretation of a null result.  The
analytic component uses the **heteroscedastic** per‑SN uncertainties (σ_i) and a
common systematic term (σ_sys = 0.02 mag); the Monte‑Carlo component samples each
σ_i explicitly, ensuring the power estimate reflects the true error budget.

All transformations are deterministic given the fixed random seed and dataset checksum.

---  
*End of Data Model*===