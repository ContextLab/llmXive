# Data Model: Testing Cosmic Ray Arrival Direction Isotropy

## 1. Entity Definitions

### 1.1 EventCatalog
Represents the raw or pre-processed list of cosmic ray events.
*   **Attributes**:
    *   `event_id`: Unique identifier (string).
    *   `energy`: Energy in EeV (float).
    *   `ra`: Right Ascension in degrees (float, [0, 360)).
    *   `dec`: Declination in degrees (float, [-90, 90]).
    *   `detector`: Source detector ("auger" or "ta") (string).
*   **Constraints**:
    *   `energy` > 50.0.
    *   `ra`, `dec` must not be NaN.
    *   `detector` must be one of the allowed values.

### 1.2 ExposureMap
A HEALPix map representing the relative probability of detecting an event from a given direction, assuming an isotropic sky.
*   **Attributes**:
    *   `nside`: Resolution parameter (integer, fixed at 64).
    *   `pixels`: Array of float values (length $12 \times nside^2$).
    *   `norm`: Normalization factor (total events / sum of pixels).
*   **Constraints**:
    *   Values $\ge 0$.
    *   Sum of pixels > 0.

### 1.3 PowerSpectrum
The result of the spherical harmonic decomposition.
*   **Attributes**:
    *   `l_values`: List of multipoles (integers, [1, 2, 3, 4, 5]).
    *   `c_l_values`: List of power values (floats) **after shot-noise subtraction**.
    *   `max_c_l`: The maximum value in `c_l_values`.
    *   `p_value`: Global empirical p-value (float).
    *   `is_rejected`: Boolean indicating if $p \le 0.05$.

## 2. File Formats

### 2.1 Input Data (Raw)
*   **Format**: CSV or ASCII tables downloaded from observatories.
*   **Columns**: `Energy`, `RA`, `Dec`, `Source`.
*   **Validation**: Must pass schema validation before ingestion.

### 2.2 Processed Data (HEALPix)
*   **Format**: FITS or HDF5 (via `healpy`).
*   **Content**:
    *   `obs_map.fits`: Observed counts per pixel ($N_{obs}$).
    *   `exp_map.fits`: Expected counts per pixel ($N_{exp}$).
    *   `intensity_map.fits`: Exposure-corrected intensity ($N_{obs} / N_{exp}$).
    *   `residual_map.fits`: **Deprecated** (No longer used for C_l calculation).

### 2.3 Output Results
*   **Format**: JSON.
*   **Content**: `PowerSpectrum` object serialized.

## 3. Data Flow Diagram

```mermaid
graph TD
    A[Raw CSVs] -->|Download & Filter| B(EventCatalog)
    B -->|Convert to HEALPix| C[Observed Map N_obs]
    D[Exposure Model] -->|Normalize| E[Expected Map N_exp]
    C -->|Divide| F[Intensity Map N_obs/N_exp]
    F -->|Spherical Harmonic Transform| G[Raw C_l]
    G -->|Subtract Shot Noise (1/N)| H[Corrected C_l]
    I[Monte Carlo Simulations] -->|Generate Null Distribution (via Exposure + Shot Noise Subtraction)| J[Max C_l Distribution]
    H -->|Compare| K[Global P-Value]
    J -->|Compare| K
    K --> L[Final Result JSON]
```

## 4. Constraints & Validation Rules

*   **Coordinate Wrapping**: RA must be normalized to [0, 360). Dec must be clamped to [-90, 90].
*   **Pixel Overflow**: HEALPix indices must be $< 12 \times nside^2$.
*   **Zero Exposure**: If a pixel in the exposure map is 0, the intensity for that pixel must be masked (set to NaN) to avoid division by zero.
* **Statistical Validity**: $N_{MC}$ must be **[deferred]** (reduced from [deferred] to meet runtime constraints). The shot-noise term ($1/N_{tot}$) must be subtracted from the raw $C_\ell$ to isolate the anisotropy signal.