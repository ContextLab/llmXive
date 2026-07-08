# Data Model: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Entity Definitions

### 1. Supernova Record
Represents a single Type Ia supernova entry after ingestion and cleaning.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique identifier from Pantheon+ (e.g., "SN2012fr") |
| `ra` | float | Right Ascension in degrees (J2000) |
| `dec` | float | Declination in degrees (J2000) |
| `redshift` | float | Redshift ($z$) |
| `distance_modulus` | float | Observed distance modulus ($\mu_{obs}$) |
| `uncertainty` | float | Uncertainty in distance modulus ($\sigma_\mu$) |
| `residual` | float | Calculated residual ($\mu_{obs} - \mu_{th}$) |
| `healpix_index` | int | Pixel index on Nside=16 grid (for mask/visualization only) |

### 2. Healpix Pixel
Represents a spatial bin on the celestial sphere (Nside=16).

| Field | Type | Description |
| :--- | :--- | :--- |
| `pixel_index` | int | HEALPix index (Nside=16) |
| `nside` | int | Grid resolution (always 16) |
| `mean_residual` | float | Mean residual of supernovae in this pixel (for visualization) |
| `count` | int | Number of supernovae in this pixel |

### 3. Likelihood Result
Represents the output of the Maximum Likelihood Estimation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `dipole_amplitude` | float | $A_1$ from MLE in magnitudes |
| `dipole_direction_ra` | float | RA of the dipole vector in degrees |
| `dipole_direction_dec` | float | Dec of the dipole vector in degrees |
| `quadrupole_amplitude` | float | $A_2$ from MLE in magnitudes |
| `intrinsic_scatter` | float | Estimated $\sigma_{int}$ |

### 4. Simulation Result
Represents one iteration of the isotropic mock catalog.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | int | Simulation iteration number (0 to N-1) |
| `dipole_amplitude` | float | $A_1$ for this simulation |
| `quadrupole_amplitude` | float | $A_2$ for this simulation |

## Data Flow

1. **Raw Input**: `data/raw/pantheon_plus.csv` (External, immutable).
2. **Processed Input**: `data/processed/supernova_records.csv` (Derived, checksummed).
3. **Intermediate**: `data/processed/mask.fits` (HEALPix FITS file, Nside=16).
4. **Results**: `data/processed/likelihood_results.json` (MLE amplitudes).
5. **Simulation Output**: `data/processed/simulation_results.csv` (Streaming scalar results).
6. **Final Output**: `data/processed/analysis_summary.json` (P-values, amplitudes).