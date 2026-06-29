# Data Model: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

## Entities

### PerovskiteEntry
Represents a single material record after ingestion and cleaning.

| Field | Type | Description |
|-------|------|-------------|
| `material_id` | string | Unique identifier from Materials Project (e.g., "mp-12345"). |
| `stoichiometry` | string | Chemical formula (e.g., "ABX3"). |
| `thermal_conductivity` | float | Thermal conductivity in W/m·K. |
| `unit_cell_volume` | float | Volume in Å³. |
| `tolerance_factor` | float | Goldschmidt tolerance factor (unitless). |
| `tilting_angle` | float | Octahedral tilting angle in degrees. |
| `bond_length_variance` | float | Variance of bond lengths (unitless). |
| `source_api_date` | string | ISO 8601 date of API query. |

### AnalysisResult
Represents the output of the correlation/regression phase.

| Field | Type | Description |
|-------|------|-------------|
| `descriptor_name` | string | Name of the structural descriptor. |
| `pearson_r` | float | Pearson correlation coefficient. |
| `spearman_r` | float | Spearman correlation coefficient. |
| `p_value` | float | Raw p-value. |
| `p_value_fdr` | float | Benjamini-Hochberg corrected p-value. |
| `significant` | boolean | True if `p_value_fdr` < 0.05. |
| `regression_coefficient` | float | Coefficient from OLS model. |
| `vif_score` | float | Variance Inflation Factor for this predictor. |

## Data Flow

1.  **Raw Fetch**: API response saved to `data/raw/mp_query_[timestamp].json`.
2.  **Ingestion**: Filtered/merged to `data/processed/cleaned_perovskites.csv`.
3.  **Descriptors**: Computed and appended to `data/processed/with_descriptors.csv`.
4.  **Analysis**: Results saved to `data/processed/analysis_results.csv`.
5.  **Report**: Figures and text generated from `analysis_results.csv`.

## Integrity Rules

- **Uniqueness**: `material_id` is primary key.
- **Completeness**: `thermal_conductivity` must not be null (enforced in Ingestion).
- **Determinism**: All CSVs generated with fixed seed for sorting/ordering.
- **Checksum**: Every file in `data/` has a SHA-256 hash recorded in `state/...yaml`.
