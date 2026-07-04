# Data Model: Predicting Coral Bleaching Susceptibility

## 1. Entity Definitions

### Reef-Species Unit
The primary observation row. Represents a unique combination of a reef location (5-km grid cell) and a coral species.
- **Key Attributes**: `reef_id`, `species_id`, `latitude`, `longitude`, `region` (West/East Pacific).
- **Data Availability Status**: Indicates if any required field (e.g., `thermal_tolerance`, `bleached`) was missing and caused the row to be dropped or flagged.

### Environmental Profile
Time-aggregated oceanographic variables associated with the Reef-Species Unit.
- **Attributes**: `sst_mean_30d`, `dhw_max`, `dhw_mean_30d`, `chlorophyll_a`, `wind_speed`.

### Trait Profile
Biological characteristics associated with the species.
- **Attributes**: `thermal_tolerance`, `growth_rate`, `colony_size`.
- **Note**: These fields are **required** for real data analysis. If missing, the row is excluded or the pipeline halts. No synthetic generation in default mode.

### Bleaching Label
Binary outcome.
- **Attributes**: `bleached` (0/1).
- **Note**: This field is **required** for model training. If missing, the pipeline halts.

## 2. Data Flow

1.  **Raw Ingestion**: Download verified NOAA/UNEP parquet files.
2.  **Data Gap Check**: Verify presence of Coral Trait and ReefBase data. If missing, generate `data_gap_report.md` and **HALT**.
3.  **Merging**: Join on spatial grid (5km).
4.  **Feature Construction**: Calculate lagged SST, interaction terms.
5.  **Definitional Circularity Check**: Flag if DHW is derived from SST.
6.  **Collinearity Filter**: Drop features with VIF > 5.
7.  **Split**: Separate into Train (West) and Test (East).
8.  **Model Input**: Final DataFrame passed to XGBoost.
9.  **Output**: Predictions, GeoTIFF map, Feature Importance table.

## 3. Schema Contracts

The following schemas define the strict contract for data inputs and outputs.

### Input Schema: Unified Reef Dataset
- **Format**: Parquet
- **Constraints**: No nulls in `sst_mean_30d`, `dhw_max`, `thermal_tolerance`, `bleached` for real data mode.
- **New Field**: `data_availability_status` (string): "complete", "missing_traits", "missing_labels".

### Output Schema: Model Predictions
- **Format**: Parquet
- **Columns**: `reef_id`, `species_id`, `predicted_prob`, `threshold_0.3_pred`, `threshold_0.5_pred`, `threshold_0.7_pred`.
- **New Field**: `variation_in_fp_fn` (number): The calculated delta/range of FP/FN rates across thresholds.

### Output Schema: Risk Map
- **Format**: GeoTIFF
- **Resolution**: 5km
- **Value Range**: 0.0 (Low Risk) to 1.0 (High Risk).

## 4. Data Integrity Rules

- **Checksums**: All raw files must have a corresponding SHA256 hash in `data/checksums.json`.
- **Imputation Flag**: Rows with imputed values must have a flag `is_imputed = true`.
- **Data Gap Flag**: If the pipeline halts due to missing data, `data_gap_report.md` is generated with details.
- **No Synthetic Data**: In default mode, no `is_synthetic` flag is used. If simulation mode is enabled, a separate `is_synthetic = true` flag is added, and all scientific claims are disabled.
