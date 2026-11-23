# Data Model: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Entity Definitions

| Entity | Attributes | Description |
|---|---|---|
| **SolarCycle** | `cycle_id` (int), `start_date` (date), `end_date` (date), `peak_date` (date), `avg_gsn` (float) | Derived from SILSO records; stored in `data/processed/solar_cycles.parquet`. |
| **SunspotRecord** | `date` (date), `gsn` (float, nullable), `quality_flag` (enum: `raw`/`interpolated`/`proxy`), `cycle_id` (int, nullable), `gsn_lag1` (float, nullable) | Preprocessed GSN series; if GSN is unavailable the fields are left null and the record still exists for alignment with SILSO cycle information. Stored in `data/processed/preprocessed_data.parquet`. |
| **TSIProxyRecord** | `time` (date), `solar_forcing` (float) | CMIP6 solar forcing; merged for comparison only. |
| **ModelArtifact** | `model_type` (str), `validation_rmse` (float, nullable), `validation_r2` (float, nullable), `artifact_path` (str) | Serialized model + metrics; present only when TSI training succeeded. |
| **ReconstructionRecord** | `date` (date), `tsi_reconstructed` (float), `tsi_lower` (float), `tsi_upper` (float), `cycle_id` (int), `model_used` (enum: `cycle_specific`/`cycle_agnostic`) | Final 1610‑2002 reconstruction with uncertainty; written only if a model was trained. |
| **BootstrapStat** | `solar_minimum` (str), `variance_mean` (float), `variance_ci_lower` (float), `variance_ci_upper` (float), `p_value_corrected` (float) | Variance comparison across Maunder, Dalton, Modern minima. |
| **SensitivityResult** | `threshold` (float ∈ {0.01, 0.05, 0.1}), `rmse_variation` (float, nullable), `coefficient_stability` (float) | Result of the tolerance‑threshold sweep (only when a model exists). |

## 2. Data Flow

1. `code/data/ingestion.py` → raw parquet files in `data/raw/` + `checksums.json`.  
2. `code/data/preprocessing.py` → `solar_cycles.parquet` and `preprocessed_data.parquet`.  
3. `code/models/train.py` (conditional) → `data/artifacts/model_*.pkl` + `cv_report.json`.  
4. `code/analysis/sensitivity.py` (conditional) → `sensitivity_report.json`.  
5. `code/models/predict.py` (conditional) → `tsi_reconstruction_1610_2002.parquet` + `figures/reconstruction.png`.  
6. `code/analysis/comparison.py` → `comparison_report.json` (RMSE, bias, bootstrap stats, framing statements).  

Every step writes a **new** file; raw data is never overwritten (Principle III).

## 3. Storage Layout

```text
data/
├── raw/
│   ├── .gitkeep
│   ├── silso.parquet
│   ├── cmip6_solar_forcing.parquet
│   └── checksums.json
├── processed/
│   ├── .gitkeep
│   ├── solar_cycles.parquet
│   ├── preprocessed_data.parquet
│   └── tsi_reconstruction_1610_2002.parquet   # only if a model was trained
└── artifacts/
    ├── cv_report.json
    ├── sensitivity_report.json
    ├── comparison_report.json
    └── figures/
        └── reconstruction.png               # only if a model was trained
```

All files are SHA‑256‑checked and recorded in the project state YAML (Principle V).

## 4. Facular Baseline Note
The facular offset (≈ 0.5 W/m²) is a **constant** defined in `code/config.py`. It is applied during model prediction to avoid zero TSI when GSN ≈ 0. It is **not persisted** in any output file; its value is documented in the configuration file.

---



