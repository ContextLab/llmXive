# Data Model: Cosmic Ray Anisotropy Solar‑Cycle Modulation

## Entities

### EventDataset
Represents raw event data from IceCube or Pierre Auger.

| Attribute | Type | Description |
|-----------|------|-------------|
| `source` | str | "icecube" or "auger" |
| `filepath` | str | Local path to downloaded file |
| `checksum` | str | SHA-256 hash of file |
| `start_date` | datetime | Earliest event timestamp |
| `end_date` | datetime | Latest event timestamp |
| `event_count` | int | Total number of events |
| `sampled` | bool | True if data was sampled to fit memory |

### SolarProxySeries
Time-ordered series of solar activity indicators.

| Attribute | Type | Description |
|-----------|------|-------------|
| `proxy_name` | str | "sunspot", "solar_wind", "imf_magnitude" |
| `date` | datetime | Observation date (UTC) |
| `value` | float | Measured value |
| `source` | str | "NOAA" |

### AnisotropyInterval
Aggregated anisotropy metrics for a temporal bin.

| Attribute | Type | Description |
|-----------|------|-------------|
| `interval_start` | datetime | Start of bin (UTC) |
| `interval_end` | datetime | End of bin (UTC) |
| `dipole_amplitude` | float | Fitted dipole amplitude |
| `dipole_phase` | float | Fitted dipole phase (degrees) |
| `quadrupole_amplitude` | float | Fitted quadrupole amplitude |
| `detector` | str | "icecube" or "auger" |
| `event_count` | int | Events in this interval |

### CorrelationResult
Statistical correlation metrics between anisotropy and solar proxy.

| Attribute | Type | Description |
|-----------|------|-------------|
| `detector` | str | "icecube" or "auger" |
| `proxy_name` | str | "sunspot", "solar_wind", "imf_magnitude" |
| `correlation_type` | str | "pearson" or "spearman" |
| `r_value` | float | Correlation coefficient |
| `p_value` | float | Two-sided p-value |
| `bonferroni_p` | float | Bonferroni-corrected p-value |
| `fap` | float | Monte-Carlo false alarm probability |
| `positive_result` | bool | True if abs(r)≥0.4 AND p≤0.0017 (spec artifact) |
| `phase_corr_r` | float | Circular-linear correlation coefficient |
| `phase_corr_p` | float | P-value for phase correlation |

## Data Flow

1. **Download**: `EventDataset` and `SolarProxySeries` fetched from sources; checksums verified.
2. **Preprocess**: Events binned into `AnisotropyInterval`; HEALPix maps generated; dipole/quadrupole fitted. Sampling applied if needed.
3. **Analyze**: `CorrelationResult` computed via Lomb-Scargle, data-driven block bootstrap, phase-sensitive correlation, Monte-Carlo shuffle (both series).
4. **Report**: Results aggregated into CSV, plots, and LaTeX report.

## Schema Validation

- All numeric columns must be non-null.
- Dates must be valid UTC timestamps.
- `detector` must be "icecube" or "auger".
- `proxy_name` must be one of the three solar proxies.
- `positive_result` is a boolean derived from spec thresholds.
