# Data Model: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## Entity Definitions

### 1. ExperimentRecord (Raw Input)
Represents a single experimental observation.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier (UUID or auto‑increment) | PK |
| `alloy_series` | string | e.g., "5xxx", "6xxx" | Optional |
| `cold_work_pct` | float | Percentage of cold work deformation | > 0, < 100 |
| `mg_wt` | float | Magnesium weight percentage | ≥ 0 |
| `si_wt` | float | Silicon weight percentage | ≥ 0 |
| `cu_wt` | float | Copper weight percentage | ≥ 0 |
| `mn_wt` | float | Manganese weight percentage | ≥ 0 |
| `annealing_temp_k` | float | Annealing temperature in Kelvin | > 273 |
| `time_to_peak` | float | Time to peak softening (minutes) – **raw target** |
| `source` | string | Origin of the data point (e.g., "User", "Synthetic") |

### 2. EngineeredFeatureSet (Processed Input)
Derived from `ExperimentRecord` for model training.

| Field | Type | Derivation | Description |
| :--- | :--- | :--- | :--- |
| `cold_work_mg` | float | `cold_work_pct * mg_wt` | Interaction term |
| `cold_work_si` | float | `cold_work_pct * si_wt` | Interaction term |
| `cold_work_cu` | float | `cold_work_pct * cu_wt` | Interaction term |
| `cold_work_mn` | float | `cold_work_pct * mn_wt` | Interaction term |
| `time_to_peak_norm` | float | `arrhenius_normalize(time_to_peak, annealing_temp_k, Q=140000)` (optional) | For exploratory plots **only**; **never used for training or success‑criteria**. |
| `features_vector` | array | List of all predictor columns (including interactions) | Input to RF |
| `raw_target` | float | Alias of `time_to_peak` (used for training) | |

### 3. ModelPerformanceMetrics (Output)
Results from the analysis pipeline.

| Field | Type | Description |
| :--- | :--- | :--- |
| `r2_score` | float | Coefficient of determination on the held‑out test set (raw target). |
| `mae` | float | Mean Absolute Error on the held‑out test set (minutes). |
| `cv_r2_mean` | float | Mean R² from 5‑fold cross‑validation (raw target). |
| `cv_r2_std` | float | Standard deviation of R² from 5‑fold CV. |
| `interaction_p_value` | float | Empirical p‑value from the permutation test comparing additive vs. interaction models. |
| `feature_importance` | dict | Map of feature name to permutation‑importance score. |
| `success_criteria_met` | object | Booleans indicating whether each success criterion was satisfied. |
| `outlier_log_path` | string | Path to `results/outlier_log.txt` (if any clipping occurred). |

## Data Flow

1. **Ingestion**: Load `ExperimentRecord` from `data/raw/alloy_data.csv` (or generated synthetic file).  
2. **Cleaning**: Impute missing composition values with column means; drop rows missing `cold_work_pct` or `time_to_peak`.  
3. **Outlier Clipping**: Cap `time_to_peak` > 1000 h to the 99th percentile; log clipped rows.  
4. **Engineering**: Create `EngineeredFeatureSet`. `time_to_peak_norm` is **optional** and **excluded** from any training or metric calculation.  
5. **Split**: 80/20 train / test (seed = 42).  
6. **Training & Validation**: Random Forest on `features_vector` → `raw_target`.  
7. **Statistical Testing**: Permutation test comparing additive vs. interaction model (see research.md).  
8. **Output**: Write `ModelPerformanceMetrics` to `results/metrics.json`.

## Assumptions & Constraints

* **Units**: Time in minutes, temperature in Kelvin.  
* **Missing Data**: Composition missing → mean imputation; `cold_work_pct` or `time_to_peak` missing → row removal.  
* **Collinearity**: Interaction terms are derived from main effects; importance interpreted descriptively.  
* **Normalization**: `time_to_peak_norm` is for visualization only; all success criteria are computed on the raw target to avoid leakage.  
