# Data Model: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Entity Definitions

| Entity | Attributes | Description |
|---|---|---|
| **SolarCycle** | `cycle_id` (int), `start_date` (date), `end_date` (date), `peak_date` (date), `avg_gsn` (float) | Derived from SILSO records (external definitions); stored in `data/processed/solar_cycles.parquet`. |
| **SunspotRecord** | `date` (date), `gsn` (float), `quality_flag` (enum: `raw`/`interpolated`/`proxy`), `cycle_id` (int), `gsn_lag1` (float) | Preprocessed GSN series; stored in `data/processed/preprocessed_data.parquet`. |
| **TSIProxyRecord** | `date` (date), `solar_forcing` (float) | CMIP series, comparison only; merged into `preprocessed_data.parquet`. |
| **ModelArtifact** | `model_type` (str), `validation_rmse` (float, nullable), `validation_r2` (float, nullable), `artifact_path` (str) | Serialized model + metrics; present only when TSI training ran. |
| **ReconstructionRecord** | `date` (date), `tsi_reconstructed` (float), `tsi_lower` (float), `tsi_upper` (float), `cycle_id` (int), `model_used` (enum: `cycle_specific`/`cycle_agnostic`) | Final 1610–2002 output with uncertainty bands; `data/processed/tsi_reconstruction_1610_2002.parquet`. |
| **BootstrapStat** | `solar_minimum` (str), `variance_mean` (float), `variance_ci_lower` (float), `variance_ci_upper` (float), `p_value_corrected` (float) | Variance comparison across Maunder, Dalton, Modern minima. |
| **SensitivityResult** | `threshold` (float ∈ {0.01, 0.05, 0.1}), `rmse_variation` (float, nullable), `coefficient_stability` (float) | Tolerance‑threshold sweep output (only when model trained). |

## 2. Data Flow

1. `code/data/ingestion.py` → raw parquet in `data/raw/` + `checksums.json` (SHA‑256).
2. `code/data/preprocessing.py` → `data/processed/solar_cycles.parquet`, then `data/processed/preprocessed_data.parquet` (merged SunspotRecord + TSIProxyRecord + one‑hot cycle features). **The preprocessing script must complete by writing `preprocessed_data.parquet` to disk** — this file is the contract‑tested artifact.
3. `code/models/train.py` (conditional on TSI) → `data/artifacts/model_*.pkl` + `cv_report.json`.
4. `code/analysis/sensitivity.py` (conditional) → `sensitivity_report.json`.
5. `code/models/predict.py` (conditional) → `data/processed/tsi_reconstruction_1610_2002.parquet` + `data/artifacts/figures/reconstruction.png`.
6. `code/analysis/comparison.py` → `comparison_report.json` (CMIP6 RMSE/bias, bootstrap stats, associational statement, multiplicity note, TSI/baseline omission note).

Every step writes new files; raw data is never modified in place (Principle III).

## 3. Storage Layout

```text
data/
├── raw/
│   ├── .gitkeep
│   ├── gsn.parquet
│   ├── silso.parquet
│   ├── cmip6_solar_forcing.parquet
│   └── checksums.json
├── processed/
│   ├── .gitkeep
│   ├── solar_cycles.parquet
│   ├── preprocessed_data.parquet
│   └── tsi_reconstruction_1610_2002.parquet
└── artifacts/
    ├── cv_report.json
    ├── sensitivity_report.json
    ├── comparison_report.json
    └── figures/
        └── reconstruction.png
```

All files checksum‑tracked in the project state YAML (Principle V).

## 4. Facular Baseline Note

The facular baseline offset used in the models is an internal constant (≈ 0.5 W/m²) that ensures non‑zero TSI when GSN ≈ 0. It is **not persisted** in any output file; the value is documented in `code/config.py` and applied during model prediction.
