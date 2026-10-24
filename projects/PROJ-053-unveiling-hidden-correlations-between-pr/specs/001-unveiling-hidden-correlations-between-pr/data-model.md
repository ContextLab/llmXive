# Data Model: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## 1. Conceptual Overview
The pipeline transforms **raw experimental records** into a **processed table** that feeds a **Gaussian Process Regression** model. The model yields predictions, uncertainties, and feature‑importance scores, all persisted as JSON artifacts. The data flow is strictly linear and each artifact is validated against a JSON‑Schema contract (CSV rows are validated by converting each row to a dict and applying the schema).

## 2. Entities & Schemas

### 2.1 Raw Dataset Record (`data/raw/doe.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `x1` | float | Numeric experimental factor 1 (proxy for a processing parameter). |
| `x2` | float | Numeric experimental factor 2. |
| `x3` | float | Numeric experimental factor 3. |
| `response` | float | Measured outcome (proxy for a mechanical property). |

### 2.2 Processed Record (`data/processed/train.csv` & `data/processed/test.csv`)
| Field | Type | Constraints |
|-------|------|-------------|
| `x1_norm` | float | Min‑max normalized to `[0, 1]`. |
| `x2_norm` | float | Min‑max normalized to `[0, 1]`. |
| `x3_norm` | float | Min‑max normalized to `[0, 1]`. |
| `response_norm` | float | Min‑max normalized to `[0, 1]`. |
| *(optional categorical flags)* | integer (0/1) | One‑hot encoded if any categorical columns exist (none for this dataset). |

### 2.3 Model Artifacts
- `results/model/gpr_model.joblib` – Serialized `GaussianProcessRegressor` with fitted hyper‑parameters and attached scaler.  
- `results/model/baseline_model.joblib` – Serialized `LinearRegression` model.

### 2.4 Metrics Output (`results/metrics.json`) – conforms to `contracts/model_output.schema.yaml`
- `r2_score` (float) – GPR test R².  
- `rmse` (float) – Root Mean Square Error.  
- `mae` (float) – Mean Absolute Error.  
- `rmse_percentage_range` (float) – RMSE expressed as a percent of the observed target range.  
- `hyperparameters` (object) – `length_scale`, `sigma`.  
- `high_uncertainty_ratio` (float, 0‑1) – Fraction of test samples with σ > 2 × median.  
- `feature_importance` (array of `{feature_name, importance_score}`) – Permutation importance merged here (Task T005).  
- `baseline_r2` (float) – Linear regression baseline R².  
- `residual_analysis` (object) – `heteroscedasticity_detected` (bool) and `method_used` (string).  
- `runtime_seconds` (float) – Total pipeline runtime.  
- `power_analysis` (object) – Minimum detectable R² estimate (from Task T011).

### 2.5 Visualization Metadata (`results/visualization/<plot>.json`) – conforms to `contracts/visualization.schema.yaml`
Fields: `file_name`, `x_axis`, `y_axis`, `z_axis`, `uncertainty_flag`, `max_uncertainty`, `median_uncertainty`.

### 2.6 High‑Uncertainty Regions (`results/high_uncertainty_regions.csv`)
Columns: `sample_id`, `x1_norm`, `x2_norm`, `x3_norm`, `predicted_response`, `sigma`.

### 2.7 Confounder Report (`results/confounders.json`)
A JSON object listing any predictor‑response Pearson correlations with absolute value > 0.8, flagged as potential confounders.

### 2.8 Power‑Analysis Estimate (`results/power_analysis.json`)
Contains the estimated minimum detectable R² for N = 50, α = 0.05, 5‑fold CV, and a brief note on the exploratory nature of the study.

## 3. Logical Data Flow
```mermaid
graph TD
    A[Raw CSV] -->|T002| B[data/raw/doe.csv]
    B -->|T003| C[Preprocessed train.csv / test.csv]
    C -->|T004| D[GPR + Baseline models]
    D -->|T004| E[Metrics JSON (includes feature_importance)]
    D -->|T005| F[Importance merged into Metrics]
    D -->|T006| G[Prediction grid]
    G -->|T006| H[Contour PNG + Heatmap PNG]
    D -->|T007| I[High‑Uncertainty CSV]
    D -->|T010| J[Confounder JSON]
    D -->|T011| K[Power‑Analysis JSON]
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#bbf,stroke:#333,stroke-width:2px
```

## 4. Data Constraints
- **Non‑negative values** for all numeric fields after preprocessing.  
- **Normalization**: All numeric features must lie in `[0, 1]`.  
- **Completeness**: No missing values in `data/processed/*.csv`.  
- **Zero‑variance** columns are dropped with a logged warning.  
- **Sample Count**: Minimum 50 rows enforced in T002.  

---



