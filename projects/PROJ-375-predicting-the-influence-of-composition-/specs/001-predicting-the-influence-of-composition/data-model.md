# Data Model: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Entities

### 1. MetallicGlassEntry
Represents a single alloy sample.

| Field | Type | Description | Source | Required |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | Unique identifier (e.g., MP-XXXXX) | API / Zenodo | Yes |
| `composition` | `string` | Chemical formula (e.g., "Zr50Cu40Al10") | API / Zenodo | Yes |
| `cte` | `float` | Coefficient of Thermal Expansion (1/K) | API / Zenodo | Yes |
| `alloy_family` | `string` | Base metal (e.g., "Zr", "Pd", "Fe") | Derived | Yes |
| `mean_atomic_radius` | `float` | Weighted mean atomic radius (Å) | Derived | Yes |
| `electronegativity_var` | `float` | Variance of electronegativity | Derived | Yes |
| `vec` | `float` | Valence Electron Concentration | Derived | Yes |
| `size_mismatch` | `float` | Atomic size mismatch parameter | Derived | **No** (Optional due to VIF check) |
| `source` | `string` | "Materials Project", "AFLOWlib", or "Zenodo" | API / Zenodo | Yes |

### 2. ModelPerformance
Stores evaluation metrics for a specific model run.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | `string` | "LinearRegression", "RandomForest", or "NullModel" |
| `fold` | `int` | CV fold number (1-5) or -1 for full dataset |
| `r2` | `float` | Coefficient of determination |
| `mae` | `float` | Mean Absolute Error |
| `rmse` | `float` | Root Mean Squared Error |
| `p_value` | `float` | From permutation test (null if N < 50) |
| `is_significant` | `boolean` | True if p < 0.05 and R2 > 0.3 (null if N < 50) |
| `analysis_type` | `string` | "Quantitative" (N >= 50), "Qualitative" (N < 50), or "NoData" |

### 3. FeatureImportance
Ranking of features by contribution.

| Field | Type | Description |
| :--- | :--- | :--- |
| `feature_name` | `string` | Name of the descriptor |
| `importance_score` | `float` | Permutation importance or coefficient magnitude |
| `rank` | `int` | 1, 2, 3... |
| `correlation_with_cte` | `float` | Absolute correlation coefficient |
| `divergence_flag` | `boolean` | True if rank differs significantly from correlation rank |

## Data Flow

1.  **Ingestion**: Raw JSON/CSV from API or Zenodo → `raw/` (unchanged).
2.  **Processing**: `fetch_data.py` + `descriptors.py` → `processed/clean_mg_data.parquet`.
    *   Filters: `cte` not null, `state` is amorphous.
    *   Derivation: Calculates 4 descriptors.
    *   **VIF Check**: If VIF(`mean_atomic_radius`, `size_mismatch`) > 5.0, drop `size_mismatch` from model input (field remains in data but is marked as excluded).
3.  **Splitting**: `clean_mg_data.parquet` → `train.csv`, `test.csv` (stratified, with fallback).
4.  **Modeling**: `train.py` → `models/linear.pkl`, `models/rf.pkl`, `models/null.pkl`, `results/metrics.json`.
5.  **Evaluation**: `evaluate.py` → `results/permutation_pvalues.json`, `results/divergence_analysis.json`.

## Assumptions & Constraints

*   **Missing Data**: Entries with missing CTE or undefined composition are dropped.
*   **Chemical Formula Parsing**: Assumes standard stoichiometric format (e.g., "Zr50Cu40Al10"). Ambiguous formulas are excluded.
*   **Unit Consistency**: All CTE values must be normalized to `1/K` before training.
*   **Multicollinearity**: `size_mismatch` is mathematically coupled with `mean_atomic_radius`. The pipeline excludes it if VIF > 5.0 to ensure valid feature importance.