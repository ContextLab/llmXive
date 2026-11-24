# Data Model: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Core Entities

### UserSession (Raw & Processed)
| Attribute | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Unique learner identifier. |
| `session_id` | string | Unique session identifier (row key). |
| `recommended_items` | array[string] | List of category tokens representing algorithmic recommendations (raw column). |
| `enrolled_items` | array[string] | List of category tokens representing actual enrollments (raw column). |
| `recommended_categories` | array[string] | List of category tokens after **semantic merging** (used for entropy calculation). |
| `enrolled_categories` | array[string] | List of category tokens after **semantic merging** (used for entropy calculation). |
| `recommendation_diversity_score` | number | null | Shannon entropy (log₂) of `recommended_categories`. |
| `learner_diversity_score` | number | null | Shannon entropy (log₂) of `enrolled_categories`. |
| `baseline_vector` | object | Mapping `category → probability` derived from pre‑session history. |
| `weight` | number | Stabilized GPSW weight (null if GLS fallback). |
| `session_length` | number | null | Duration of the session in minutes (optional covariate). |
| `time_of_day` | string | null | Categorical time bucket (e.g., `morning`, `afternoon`, `evening`). |
| `platform_version` | string | null | Version identifier of the learning platform at session time. |

### ModelResult
| Attribute | Type | Description |
|-----------|------|-------------|
| `coefficient` | number | β₁ estimate for Recommendation_Diversity. |
| `std_error` | number | Standard error of the coefficient. |
| `p_value` | number | Two‑sided p‑value for the coefficient. |
| `vif` | number | Maximum Variance Inflation Factor among baseline covariates. |
| `convergence_status` | boolean | `true` if weighted regression converged; `false` if GLS used. |
| `weights_distribution` | object | `{median, max, mean}` of GPSW weights. |
| `sensitivity_analysis` | array[object] | Each entry: `{threshold, coefficient, p_value}`. |
| `permutation_test` | object | `{observed_effect, null_distribution_mean, null_distribution_std, p_value_permuted, iterations}`. |

## Data Flow Diagram
1. **Ingestion** (`code/data_fetcher.py`) → `data/raw/validated_dataset.parquet`.  
2. **Preprocessing** (`code/preprocessing.py`) → `data/processed/cleaned_data.parquet`, `diversity_scores.json`, `baseline_vectors.parquet`.  
3. **Modeling** (`code/modeling.py`) → `data/processed/model_results.csv`.  
4. **Robustness** (`code/robustness.py`) → `permutation_test_results.json`, `sensitivity_analysis.csv`.  
5. **Reporting** (`code/main.py`) → `docs/reports/analysis_report.md`.  

## Schemas

### Input Schema (Raw Data)
| Field | Type | Required? |
|-------|------|-----------|
| `user_id` | string | yes |
| `session_id` | string | yes |
| `recommended_items` | array[string] | yes (maps to `recommended_categories`). |
| `enrolled_items` | array[string] | yes (maps to `enrolled_categories`). |
| `timestamp` | string (ISO‑8601) | optional (used for pre‑study split) |
| `session_length` | number | optional |
| `time_of_day` | string | optional |
| `platform_version` | string | optional |

### Processed Output Schema
| Field | Type |
|-------|------|
| `user_id` | string |
| `session_id` | string |
| `recommendation_diversity_score` | number | null |
| `learner_diversity_score` | number | null |
| `baseline_vector` | object (category → float) |
| `weight` | number | null |
| `session_length` | number | null |
| `time_of_day` | string | null |
| `platform_version` | string | null |
| `coefficient` | number |
| `std_error` | number |
| `p_value` | number |
| `vif` | number |
| `convergence_status` | boolean |
| `weights_distribution` | object |
| `sensitivity_analysis` | array[object] |
| `permutation_test` | object |

## Assumptions & Constraints
- **Empty Enrollments** → `learner_diversity_score` set to `null`; row excluded from regression.  
- **Semantic Merging** threshold is configurable; default = 0.05.  
- **Baseline Imputation**: Uniform distribution when no pre‑study history exists.  
- **Small Sample**: GLS used when unique users < 30 (FR‑008).  

---

