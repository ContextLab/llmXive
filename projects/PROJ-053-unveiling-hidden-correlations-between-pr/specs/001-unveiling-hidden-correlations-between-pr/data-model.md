# Data Model: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## 1. Conceptual Overview
The pipeline transforms **raw experimental records** into a **processed table** that feeds a **Gaussian Process Regression** model. The raw dataset must contain the exact columns required by the specification:

- `laser_power` (numeric)  
- `scan_speed` (numeric)  
- `layer_thickness` (numeric)  
- `alloy_composition` (categorical)  
- `yield_strength` (numeric)  
- `ductility` (numeric)

The preprocessing step performs median imputation, min‑max scaling, and one‑hot encoding of `alloy_composition`. After splitting, the processed files (`train.csv`, `test.csv`) are validated against the **dataset schema** (`contracts/dataset.schema.yaml`).

## 2. Entities & Schemas

### 2.1 Raw Dataset Record (`data/raw/<dataset>.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `laser_power` | number | Laser power setting (W). |
| `scan_speed` | number | Scan speed (mm/s). |
| `layer_thickness` | number | Layer thickness (µm). |
| `alloy_composition` | string | Identifier of alloy type (e.g., `Ti-6Al-4V`). |
| `yield_strength` | number | Measured yield strength (MPa). |
| `ductility` | number | Measured ductility (% elongation). |
| *(optional additional columns)* | – | May include microstructural descriptors or other covariates. |

### 2.2 Processed Record (`data/processed/train.csv` & `data/processed/test.csv`)
| Field | Type | Constraints |
|-------|------|-------------|
| `laser_power_norm` | number | Min‑max normalized to `[0, 1]`. |
| `scan_speed_norm` | number | Min‑max normalized to `[0, 1]`. |
| `layer_thickness_norm` | number | Min‑max normalized to `[0, 1]`. |
| `alloy_<type>` | integer (0/1) | One‑hot encoded alloy flags (one column per unique composition). |
| `yield_strength_norm` | number | Min‑max normalized to `[0, 1]`. |
| `ductility_norm` | number | Min‑max normalized to `[0, 1]`. |
| *(optional additional normalized columns)* | – | Normalized versions of any extra numeric covariates. |

### 2.3 Model Artifacts
- `results/model/gpr_model.joblib` – Serialized `GaussianProcessRegressor` with fitted hyper‑parameters and attached scalers.  
- `results/model/baseline_model.joblib` – Serialized `LinearRegression` model.

### 2.4 Metrics Output (`results/metrics.json`) – conforms to `contracts/model_output.schema.yaml`
- `r2_score` (float) – GPR test R².  
- `rmse` (float) – Root Mean Square Error.  
- `mae` (float) – Mean Absolute Error.  
- `rmse_percentage_range` (float) – RMSE expressed as a percent of the observed target range.  
- `hyperparameters` (object) – `length_scale`, `sigma`.  
- `high_uncertainty_ratio` (float, 0‑1) – Fraction of test samples with predictive std dev > 2 × median.  
- `feature_importance` (array of `{feature_name, importance_score}`) – Permutation importance scores.  
- `baseline_r2` (float) – Linear regression baseline R².  
- `residual_analysis` (object) – `heteroscedasticity_detected` (bool) and `method_used` (string).  
- `runtime_seconds` (float) – Total pipeline runtime in seconds.  
- `power_analysis` (object) – `minimum_detectable_r2` (float) and `note` (string) describing the bootstrap‑based estimate.

### 2.5 Visualization Metadata (`results/visualization/<plot>.json`)
Fields: `file_name`, `x_axis`, `y_axis`, `z_axis`, `uncertainty_flag`, `max_uncertainty`, `median_uncertainty`.

### 2.6 High‑Uncertainty Regions (`results/high_uncertainty_regions.csv`)
Columns: `sample_id`, `laser_power_norm`, `scan_speed_norm`, `layer_thickness_norm`, `predicted_yield_strength`, `sigma`.

### 2.7 Confounder Report (`results/confounders.json`)
A JSON object listing any predictor‑response Pearson correlations with absolute value > 0.8 (potential confounders) and any VIF > 5 warnings. If `alloy_composition` is present, per‑alloy R² scores will be added here.

### 2.8 Manifest (`state/manifest.yaml`)
A YAML manifest enumerating all primary artifacts (raw checksum, processed splits, model files, metrics, visualizations) to satisfy the Single Source of Truth principle.

## 3. Logical Data Flow
```mermaid
graph TD
    A[Raw CSV] -->|T002| B[data/raw/<dataset>.csv]
    B -->|T003| C[Preprocessed train.csv / test.csv]
    C -->|T004| D[GPR + Baseline models]
    D -->|T004| E[Metrics JSON (includes feature_importance, residual_analysis, power_analysis)]
    D -->|T005| F[Importance merged into Metrics]
    D -->|T006| G[Prediction grid]
    G -->|T006| H[Contour PNG + Heatmap PNG]
    D -->|T007| I[High‑Uncertainty CSV]
    D -->|T010| J[Confounder JSON (incl. per‑alloy R² if possible)]
    D -->|T011| K[Power‑Analysis embedded in Metrics]
    D -->|T012| L[Manifest YAML]
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#bbf,stroke:#333,stroke-width:2px
```

## 4. Data Constraints
- **Non‑negative values** for all numeric fields after preprocessing.  
- **Normalization**: All numeric features must lie in `[0, 1]`.  
- **Completeness**: No missing values in `data/processed/*.csv`.  
- **Zero‑variance** columns are dropped with a logged warning.  
- **Sample Count**: Minimum 50 rows enforced in T002 (post‑download).  

---


