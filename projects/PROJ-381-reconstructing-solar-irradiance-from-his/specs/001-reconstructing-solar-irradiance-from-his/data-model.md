# Data Model: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Entity Definitions

### 1.1 SolarCycle
Logical entity representing a specific solar activity cycle.
*   **cycle_id**: Integer (e.g., 1, 2, ..., 25).
*   **start_year**: Integer (approximate start).
*   **end_year**: Integer (approximate end).
*   **peak_year**: Integer (year of maximum activity).
*   **avg_gsn**: Float (average sunspot number over the cycle).

### 1.2 SunspotRecord
Time-series entity for Group Sunspot Number.
*   **date**: Date (YYYY-MM-DD).
*   **gsn**: Float (Group Sunspot Number).
*   **quality_flag**: String (e.g., "raw", "interpolated", "proxy").
*   **cycle_phase**: Float (sin/cos of day-of-year).

### 1.3 TSIRecord
Time-series entity for Total Solar Irradiance.
*   **date**: Date (YYYY-MM-DD).
*   **tsi_value**: Float (W/m²).
*   **tsi_lower**: Float (Lower bound of uncertainty).
*   **tsi_upper**: Float (Upper bound of uncertainty).
*   **source**: String ("satellite", "reconstruction", "synthetic").

### 1.4 ModelArtifact
Trained model metadata.
*   **model_type**: String ("RandomForest", "GaussianProcess").
*   **validation_rmse**: Float (Time-Block CV).
*   **r_squared**: Float.
*   **pkl_path**: String (path to pickled model).

## 2. Data Flow

1.  **Ingestion**: Raw GSN (SILSO) and TSI (Satellite) loaded.
2.  **Preprocessing**:
    *   Gap filling (Linear/Proxy GSN=0).
    *   Cycle detection (SILSO boundaries).
    *   Feature engineering (Cycle_Phase).
    *   Output: `preprocessed_data.parquet` (SunspotRecord + TSIRecord).
3.  **Training**:
    *   Split by Time-Block (Train: 2003-2015, Test: 2016-Present).
    *   Train RF/GP.
    *   Output: `model_artifact.pkl` + `cv_report.json`.
4.  **Sensitivity Analysis**:
    *   Sweep inconsistency tolerance threshold.
    *   Output: `sensitivity_report.json`.
5.  **Reconstruction**:
    *   Apply model to pre-satellite GSN.
    *   Generate uncertainty bands.
    *   Output: `tsi_reconstruction_1610_2002.parquet`.
6.  **Comparison**:
    *   Compare with baseline/CMIP6.
    *   Output: `comparison_report.json`.

## 3. Storage Layout

```text
data/
├── raw/
│   ├── silso_sunspot.parquet          # Source GSN
│   ├── tsi_satellite.parquet          # Source TSI
│   └── cmip6_baseline.parquet         # Source CMIP6
├── processed/
│   ├── preprocessed_data.parquet      # Joined, gap-filled, phase-labeled
│   └── tsi_reconstruction_1610_2002.parquet # Final output
└── artifacts/
    ├── model_rf.pkl
    ├── model_gp.pkl
    ├── cv_report.json
    ├── sensitivity_report.json
    └── comparison_report.json
```