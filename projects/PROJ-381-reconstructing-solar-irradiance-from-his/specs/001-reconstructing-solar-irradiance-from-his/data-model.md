# Data Model: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Entity Definitions

| Entity | Attributes | Description |
|---|---|---|
| **SolarCycle** | `cycle_id` (int), `start_year` (int), `end_year` (int), `peak_year` (int), `avg_gsn` (float) | Logical grouping of years; derived from SILSO cycle maxima. Used as a categorical feature in modeling. |
| **SunspotRecord** | `date` (date), `gsn` (float), `quality_flag` (enum: `raw`, `interpolated`, `proxy`), `cycle_id` (int), `gsn_lag1` (float) | Preprocessed GSN time‑series with engineered features and explicit categorical Cycle ID. |
| **TSIProxyRecord** | `date` (date), `solar_forcing` (float) | CMIP6 solar‑forcing variable used **only for comparative analysis**, not as a training target. |
| **ModelArtifact** | `model_type` (str), `validation_rmse` (float), `validation_r2` (float), `artifact_path` (str) | Serialized model (pickle) plus validation metrics. |
| **ReconstructionRecord** | `date` (date), `tsi_reconstructed` (float), `tsi_lower` (float), `tsi_upper` (float) | Final TSI reconstruction for 1610‑2002 with uncertainty bands. |
| **BootstrapStat** | `solar_minimum` (str), `variance_mean` (float), `variance_ci_lower` (float), `variance_ci_upper` (float), `p_value_corrected` (float) | Results of variance comparison across minima (Maunder, Dalton, Modern). |
| **SensitivityResult** | `threshold` (float), `rmse_variation` (float) | Output of the inconsistency‑tolerance sweep. |

## 2. Data Flow Diagram

1. **Ingestion** (`code/data/ingestion.py`) → raw parquet files in `data/raw/`.  
2. **SolarCycle Generation** (`code/data/preprocessing.py`) → `data/processed/solar_cycles.parquet`.  
3. **Preprocessing** (`code/data/preprocessing.py`) → `data/processed/preprocessed_data.parquet` containing merged `SunspotRecord` + `TSIProxyRecord` + categorical `cycle_id`.  
4. **Model Training** (`code/models/train.py`) → `data/artifacts/model_*.pkl` + `cv_report.json`.  
5. **Sensitivity Analysis** (`code/analysis/sensitivity.py`) → `sensitivity_report.json`.  
6. **Reconstruction** (`code/models/predict.py`) → `data/processed/tsi_reconstruction_1610_2002.parquet`.  
7. **Comparison & Bootstrap** (`code/analysis/comparison.py`) → `comparison_report.json` (metrics, bootstrap stats).  

All intermediate files are immutable; each step writes a new artifact, satisfying Principle III.

## 3. Storage Layout

```
data/
├── raw/
│   ├── .gitkeep
│   ├── gsn.parquet
│   ├── silso.parquet
│   └── cmip6_solar_forcing.parquet
├── processed/
│   ├── .gitkeep
│   ├── preprocessed_data.parquet
│   └── solar_cycles.parquet
└── artifacts/
    ├── model_rf.pkl
    ├── model_gp.pkl
    ├── cv_report.json
    ├── sensitivity_report.json
    └── comparison_report.json
```

Each file is checksum‑tracked in the project state YAML.

---

