# Data Model: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| `AR_Event` | A detected atmospheric river occurrence. | `event_id` (UUID), `start_time` (ISO‑8601), `end_time` (ISO‑8601), `band` (e.g., `30-40N`), `ivt_max` (float, kg m⁻¹ s⁻¹), `geometry` (GeoJSON polygon) |
| `Z500_Anomaly` | Monthly deviation of 500 hPa geopotential height from the 1979‑2023 climatology. | `time` (YYYY‑MM), `band`, `lat` (float), `lon` (float), `anomaly` (float, m) |
| `Correlation_Result` | Correlation statistics for a single grid cell, band, and season. | `band`, `season` (`DJF`/`MAM`/`JJA`/`SON`), `lat`, `lon`, `r` (float, Pearson coefficient), `p_raw` (float), `p_adj` (float), `significant` (bool) |
| `Sensitivity_Summary` | Aggregated impact of AR‑threshold variations. | `band`, `season`, `threshold_offset` (float), `significant_count` (int), `pct_change` (float), `flag_threshold_sensitive` (bool) |
| `Teleconnection_Validation` | Overlap metrics between significant AR‑Z500 fields and teleconnection patterns. | `band`, `season`, `index_name` (`PNA`/`NAO`), `pattern_corr` (float), `p_value` (float) |

## Storage Layout
```
data/
├── raw/
│   ├── era5_ivt_*.nc          # Original IVT from ERA5
│   └── era5_z500_*.nc         # Original Z500 from ERA5 (fetched via CDS)
├── processed/
│   ├── ar_freq_{band}.nc      # Monthly AR counts per band
│   ├── z500_anom_{band}.nc    # Monthly Z500 anomalies per band
│   ├── corr_raw_{band}_{season}.nc
│   ├── corr_fdr_{band}_{season}.nc
│   ├── sensitivity_summary.csv
│   └── validation_{band}_{season}.json
└── metadata.yaml               # Checksums, retrieval dates, provenance
```

All NetCDF files follow CF‑Convention with dimensions `(time, lat, lon)` and include global attributes `source`, `processing_step`, `checksum`, `creation_timestamp`.

## Contract Schema
The `contracts/correlation_result.schema.yaml` (see below) defines the required fields for any `Correlation_Result` record exported as a CSV/JSON artifact. Implementer tests will validate that every row conforms to this schema.

---
