# Data Model: Cosmic Ray Anisotropy Solar‑Cycle Modulation

## Entities

### EventDataset
Represents raw event data from a detector.
- `source`: str (e.g., "IceCube", "Auger")
- `filepath`: str (local path)
- `checksum`: str (SHA-256)
- `timestamp_min`: datetime (earliest event)
- `timestamp_max`: datetime (latest event)
- `event_count`: int
- `coverage_status`: str (e.g., "full", "partial", "missing")

### SolarProxySeries
Time-ordered solar activity indices.
- `proxy_name`: str (e.g., "sunspot_number")
- `date`: datetime
- `value`: float
- `source`: str (e.g., "NOAA NGDC")

### AnisotropyInterval
Binned anisotropy metrics for one interval.
- `interval_start`: datetime
- `interval_end`: datetime
- `detector`: str (e.g., "IceCube")
- `dipole_amp`: float (relative anisotropy amplitude)
- `dipole_phase`: float (radians, 0–2π)
- `quad_amp`: float
- `partial_interval`: bool
- `event_count`: int
- `coverage_status`: str (inherited from dataset)

### CorrelationResult
Statistical test output for one detector-proxy pair.
- `detector`: str
- `proxy`: str
- `method`: str (e.g., "pearson", "spearman", "shuffle")
- `r`: float (correlation coefficient)
- `p_value`: float
- `fap`: float (False Alarm Probability)
- `bonferroni_adjusted`: bool
- `positive_result`: bool (True if |r|≥0.4 and p≤0.0017)

## Schemas

### CSV Output Schema (`anisotropy_timeseries.csv`)
| Column | Type | Description |
|--------|------|-------------|
| interval_start | datetime | Start of the binning interval in UTC ISO8601 format. |
| interval_end | datetime | End of the binning interval in UTC ISO8601 format. |
| detector | str | Detector name. |
| dipole_amp | float | Relative dipole amplitude (dimensionless). |
| dipole_phase | float | Dipole phase (radians). |
| quad_amp | float | Quadrupole amplitude. |
| partial_interval | bool | True if the interval is shorter than the configured bin size. |
| event_count | int | Number of events included in this interval. |
| coverage_status | str | "full" or "partial" (if dataset coverage <90%). |

### JSON Schema (`correlation_results.json`)
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "detector": {"type": "string"},
      "proxy": {"type": "string"},
      "method": {"type": "string"},
      "r": {"type": "number"},
      "p_value": {"type": "number"},
      "fap": {"type": "number"},
      "bonferroni_adjusted": {"type": "boolean"},
      "positive_result": {"type": "boolean"}
    },
    "required": ["detector", "proxy", "method", "r", "p_value", "fap", "positive_result"]
  }
}
```

## Data Flow

1. **Download**: Raw parquet/CSV → `data/raw/` (checksummed).
2. **Validation**: Check temporal coverage → set `coverage_status`.
3. **Binning**: Events → Exposure Map → Relative Anisotropy → HEALPix maps → Anisotropy intervals → `data/processed/anisotropy_timeseries.csv`.
4. **Analysis**: Anisotropy CSV + Solar proxies → Correlation results → `data/results/correlation_results.json`.
5. **Report**: Results → LaTeX → `reports/report.pdf`.
