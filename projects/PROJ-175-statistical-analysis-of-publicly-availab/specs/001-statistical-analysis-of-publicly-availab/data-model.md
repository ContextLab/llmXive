# Data Model: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

## Entities

### IngredientPair
Represents a unique pair of ingredients $(i, j)$ used for modeling.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `ingredient_a` | string | Canonical ID of ingredient A. | Normalized Recipe1M |
| `ingredient_b` | string | Canonical ID of ingredient B. | Normalized Recipe1M |
| `log_co_occurrence` | float | Log-transformed co-occurrence count ($\log(1 + C_{ij})$). | Recipe1M |
| `semantic_similarity` | float | Cosine similarity of embeddings (proxy for flavor). | Recipe1M Embeddings |
| `functional_role` | string | Categorical: "primary", "secondary", "garnish". | Derived (Position/Freq) |
| `compatibility_label` | int | Binary: 1 (compatible), 0 (incompatible). | Recipe1M Ratings (Proxy) |
| `validation_score` | float | Correlation score of semantic similarity proxy with known chemical pairs. | Proxy Validation |

### ModelResult
Output of the statistical fitting process.

| Attribute | Type | Description |
|-----------|------|-------------|
| `coefficients` | dict | Map of predictor names to coefficient values. |
| `p_values` | dict | Map of predictor names to p-values. |
| `vif_scores` | dict | Map of predictor names to VIF. |
| `auc` | float | Area Under the Curve. |
| `log_likelihood` | float | Log-likelihood of the model. |
| `leakage_metric` | float | Quantified data leakage (predicting frequency from similarity). |

### EvaluationMetrics
Performance summary on the test set.

| Attribute | Type | Description |
|-----------|------|-------------|
| `auc` | float | AUC on test set (cross-validation). |
| `precision` | float | Precision. |
| `recall` | float | Recall. |
| `calibration_error` | float | Mean absolute error from ideal diagonal. |
| `leakage_metric` | float | Quantified data leakage. |

## Data Flow

1.  **Raw**: `data/raw/recipe1m_*.parquet` (Checksummed).
2.  **Processed**: `data/processed/ingredient_pairs.csv` (Normalized pairs).
3.  **Split**: `data/processed/train.csv`, `data/processed/test.csv`.
4.  **Logs**: `data/logs/pipeline_execution_log.json`, `data/logs/model_fitting_log.json`.
