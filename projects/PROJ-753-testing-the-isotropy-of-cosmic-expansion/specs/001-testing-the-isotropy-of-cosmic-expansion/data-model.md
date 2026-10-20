# Data Model: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Overview
All artifacts reside under `data/`. Raw, immutable inputs are stored in `data/raw/`; derived products are stored in `data/processed/`; human‑readable reports live in `data/reports/`.

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

Conforms to `contracts/residuals.schema.yaml`.

### 2. `healpix_map.fits`
A FITS binary table with one row per pixel.

| Column | Type | Description |
|--------|------|-------------|
| `pixel_index` | integer | HEALPix pixel index (Nside = 32). |
| `nside` | integer | HEALPix resolution (constant 32). |
| `mean_residual` | float | Mean residual of all SNe in the pixel (mag). |
| `count` | integer | Number of supernovae contributing to the pixel. |
| `mask_value` | integer | 1 = pixel used in analysis, 0 = masked. |

Conforms to `contracts/healpix_map.schema.yaml`.

### 3. `simulation_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| `run_id` | integer | Simulation iteration number (starting at 1). |
| `dipole_amp` | float | Dipole amplitude (mag) for this mock catalog. |
| `quadrupole_amp` | float | Quadrupole amplitude (mag) for this mock catalog. |

Conforms to `contracts/simulation_results.schema.yaml`.

### 4. `analysis_result.json`
A JSON object summarising the final scientific outcome (see `contracts/analysis_result.schema.yaml`).

### 5. `final_report.txt`
Plain‑text human‑readable report containing the same numeric results plus a concise interpretation.

## Data Flow Diagram
1. **Download** → `data/raw/pantheon_plus.dat`  
2. **Ingestion & Residuals** → `data/processed/residuals.csv`  
3. **HEALPix Projection** → `data/processed/healpix_map.fits`  
4. **Harmonic Analysis** → in‑memory coefficients (used for amplitudes)  
5. **Simulations** → `data/processed/simulation_results.csv`  
6. **Significance & Reporting** → `data/reports/final_report.txt`, `analysis_result.json`  

All steps are deterministic given the fixed random seed and checksum‑verified inputs.

---
