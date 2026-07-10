# Data Model: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Entities

### 1. Supernova Record
Represents a single Type Ia supernova entry from the Pantheon+ dataset after filtering.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | `str` | Unique identifier (e.g., `SN2015F`) | Pantheon+ `NAME` column |
| `ra` | `float` | Right Ascension in degrees | Pantheon+ `RA` column |
| `dec` | `float` | Declination in degrees | Pantheon+ `DEC` column |
| `z` | `float` | Redshift (dimensionless) | Pantheon+ `Z` column |
| `mu` | `float` | Observed Distance Modulus (mag) | Pantheon+ `MU` column |
| `mu_err` | `float` | Uncertainty in Distance Modulus (mag) | Pantheon+ `MUERR` column |
| `mu_th` | `float` | Theoretical Distance Modulus (mag) | Calculated via ΛCDM |
| `residual` | `float` | $\mu_{obs} - \mu_{th}$ (mag) | Calculated |

### 2. Healpix Pixel
Represents a spatial bin on the celestial sphere.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `pixel_index` | `int` | HEALPix pixel index (Nside=32) |
| `nside` | `int` | Resolution parameter (fixed at 32) |
| `mean_residual` | `float` | Inverse‑variance weighted mean of `residual` for SNe in this pixel |
| `weight_sum` | `float` | Σ (1/σ_i²) for the pixel (used for weighting) |
| `count` | `int` | Number of SNe in this pixel |
| `mask` | `bool` | `True` if `weight_sum` > 0 (pixel contributes to analysis) |

### 3. Harmonic Coefficient
Represents a term in the spherical harmonic expansion.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `l` | `int` | Angular degree (ℓ ∈ {1,2,3}) |
| `m` | `int` | Azimuthal order (‑ℓ ≤ m ≤ ℓ) |
| `real` | `float` | Real part of $a_{\ell m}$ |
| `imag` | `float` | Imaginary part of $a_{\ell m}$ |

### 4. Simulation Run
Represents one iteration of the null distribution simulation.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `run_id` | `int` | Iteration number (0‑based) |
| `dipole_amp` | `float` | Calculated dipole amplitude for this run (mag) |
| `quadrupole_amp` | `float` | Calculated quadrupole amplitude for this run (mag) |
| `seed` | `int` | Random seed used for this iteration (always 42 for reproducibility) |

## Data Flow

1. **Raw**: `data/raw/pantheon_plus.csv` (downloaded from the verified GitHub repository).  
2. **Processed**:  
   * `data/processed/supernovae_clean.csv` – filtered Supernova Records with residuals.  
   * `data/processed/healpix_map.fits` – HEALPix map of inverse‑variance‑weighted residuals (includes mask).  
   * `data/processed/harmonic_coeffs.json` – dictionary of $a_{\ell m}$ for ℓ ≤ 3.  
   * `data/processed/null_distribution.csv` – rows of `Simulation Run` records.  
3. **Output**:  
   * `data/processed/final_results.json` – p‑values, significance flag, summary statistics.  
   * `reports/` – plots and a concise summary PDF.

## Constraints

* **RA/Dec**: Degrees, RA ∈ [0, 360), Dec ∈ [‑90, 90].  
* **Redshift**: > 0, and a mandatory cut *z* > 0.02 (see plan justification).  
* **Residuals**: Numerical integration tolerance = 1e‑6.  
* **Seeds**: All stochastic operations use seed = 42.  
* **Mask**: Binary; a pixel contributes only if `weight_sum` > 0.  

## Additional Metadata (for reproducibility)

`data/metadata.json` records:

```json
{
  "pantheon_version": "v1.0",
  "checksum_sha256": "<computed‑hash>",
  "cosmology": {
    "H0": 67.4,
    "Omega_m": 0.315,
    "Omega_lambda": 0.685
  },
  "redshift_cut": 0.02,
  "seed": 42
}
```
