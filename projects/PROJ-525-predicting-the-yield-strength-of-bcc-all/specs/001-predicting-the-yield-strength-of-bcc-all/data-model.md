# Data Model: Predicting Yield Strength of BCC Alloys

## Entity-Relationship Overview

The data model consists of three primary entities: `AlloyRecord`, `CompositionalDescriptor`, and `ModelPerformance`. Data flows from raw ingestion to derived features, then to model evaluation.

### 1. AlloyRecord (Raw & Filtered)

Represents a single alloy entry from the source database.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `system_id` | string | Unique identifier for the alloy. | Primary Key, Non-null |
| `elemental_composition` | dict | Map of element symbol to atomic fraction. | Keys: 1-3 char symbols; Values: float, sum to 1.0 |
| `yield_strength` | float | Yield strength in MPa. | Non-null, > 0 |
| `crystal_structure` | string | Crystal phase (e.g., "BCC", "FCC"). | Must be "BCC" for valid records |
| `source_reference` | string | DOI or URL of the source. | Non-null |
| `processing_status` | string | "raw", "filtered", "rejected". | Enum |
| `rejection_reason` | string | Reason if rejected (e.g., "Missing Yield", "Non-BCC"). | Nullable |

### 2. CompositionalDescriptor (Engineered)

Derived features for each valid `AlloyRecord`.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `system_id` | string | FK to `AlloyRecord`. | Primary Key |
| `delta_radius` | float | Atomic radius mismatch (%). | Calculated |
| `vec` | float | Valence Electron Concentration. | Calculated |
| `mixing_entropy` | float | Mixing entropy (J/mol·K). | Calculated |
| `mixing_enthalpy` | float | Mixing enthalpy (kJ/mol). | Calculated |
| `electronegativity_diff` | float | Electronegativity difference. | Calculated |
| `ilr_features` | list[float] | Isometric Log-Ratio transformed features. | Length = N_elements - 1 |
| `selected_features` | list[str] | Names of features selected by RFE/L1. | Nullable |

### 3. ModelPerformance (Evaluation)

Results from model training and validation.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `model_id` | string | Unique ID for the run (e.g., "RF_seed42"). | Primary Key |
| `model_type` | string | "RandomForest", "GradientBoosting", "Ridge". | Enum |
| `r_squared_mean` | float | Mean R² across 5-fold CV. | Float |
| `r_squared_ci_lower` | float | Lower bound of 95% CI. | Float |
| `r_squared_ci_upper` | float | Upper bound of 95% CI. | Float |
| `mae_mean` | float | Mean Absolute Error. | Float |
| `rmse_mean` | float | Root Mean Square Error. | Float |
| `feature_importance` | dict | Map of feature name to importance score. | Nullable |
| `seed` | int | Random seed used. | Non-null |

## Data Flow Diagram

1.  **Ingestion**: `raw_data.csv` -> `data_ingestion.py` -> `filtered_bcc.csv` (AlloyRecord).
2.  **Engineering**: `filtered_bcc.csv` + `periodic_table.json` -> `feature_engineering.py` -> `descriptors.csv` (CompositionalDescriptor).
3.  **Modeling**: `descriptors.csv` -> `modeling.py` -> `results.json` (ModelPerformance).
4.  **Reporting**: `results.json` -> `paper/` (aggregated stats).

## Storage Constraints

- **Raw Data**: Stored in `data/raw/` with SHA-256 checksums.
- **Processed Data**: Stored in `data/processed/` with timestamps.
- **Logs**: `data/logs/rejected_entries.log` for traceability (Principle III).
