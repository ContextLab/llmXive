# Data Model: llmXive follow‑up – extending "Mellum2 Technical Report"

## Overview
All intermediate and final artifacts are stored as columnar Parquet (Snappy) or JSON files. Schemas are defined in `contracts/` and validated with `jsonschema`.

## Entities

### 1. CodeChunk
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique chunk identifier (`repo:file:chunk_index`). |
| `repo_name` | string | Source repository name. |
| `language` | string (`"python"` | `"java"` | `"other"` ) | Programming language. |
| `content` | string | Raw source code. |
| `cyclomatic_complexity` | integer ≥ 0 | From CodeQL. |
| `nesting_depth` | integer ≥ 0 | From tree‑sitter. |
| `repetition_ratio` | number ∈ [0, 1] | Token‑level repetition. |
| `token_count` | integer ≥ 1 | Number of tokens (mandatory confounder). |
| `ngram_probability` | number > 0 | KenLM estimate (FR‑010). |
| `per_token_loss` | number | Average cross‑entropy loss. |
| `entropy` | number | Average prediction entropy. |
| `inference_time_ms` | integer ≥ 0 | Timing metric. |
| `status` | string (`"success"` | `"timeout"` | `"parse_error"` | `"oom"` ) | Processing outcome. |

### 2. RepositoryAggregate
| Field | Type | Description |
|-------|------|-------------|
| `repo_name` | string | Repository identifier. |
| `language` | string | Language of repo. |
| `mean_cyclomatic_complexity` | float | Repo‑level mean. |
| `mean_nesting_depth` | float | Repo‑level mean. |
| `mean_per_token_loss` | float | Repo‑level mean (raw). |
| `mean_normalized_loss` | float | Loss after n‑gram division. |
| `mean_token_count` | float | Mean token count. |
| `chunk_count` | integer ≥ 1 | Number of processed chunks. |

### 3. CorrelationResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string | `"cyclomatic_complexity"` | `"nesting_depth"` | `"repetition_ratio"` |
| `language` | string | `"python"` | `"java"` |
| `method` | string (`"pearson"` | `"spearman"` ) | Correlation method. |
| `correlation_coefficient` | float | Value in [‑1, 1]. |
| `p_value` | float ∈ [0, 1] | Raw permutation p‑value. |
| `p_value_adjusted` | float ∈ [0, 1] | FDR‑corrected p‑value. |
| `sample_size` | integer ≥ 1 | Number of repositories used. |

### 4. ThresholdResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string | Same as above. |
| `language` | string | `"python"` | `"java"` |
| `threshold_value` | float | Identified breakpoint. |
| `slope_before` | float | Slope for values < threshold. |
| `slope_after` | float | Slope for values > threshold. |
| `model_fit` | string (`"piecewise"` | `"linear"` ) | Preferred model after AIC/BIC. |
| `aic_difference` | float | AIC(piecewise) ‑ AIC(linear). |
| `significance` | boolean | True if non‑linear model preferred (ΔAIC > 2). |
| `bootstrap_stability` | float | Max shift of threshold across 1 000 bootstrap samples (SC‑002). |
| `confidence_interval_width` | float | Width of 95 % CI for threshold. |
| `sensitivity_range` | array of float | Thresholds examined in sweep (FR‑006). |

### 5. FinalReport (output.schema.yaml)
See `contracts/output.schema.yaml` for full JSON schema.

## Data Flow
1. **Download** → raw streaming → `raw_samples.parquet` (contains `repo_name`, `language`, `content`).  
2. **Static analysis** → enrich to `code_chunks.parquet` (matches `CodeChunk` schema).  
3. **KenLM** → adds `ngram_probability`.  
4. **Inference** → adds `per_token_loss`, `entropy`, `inference_time_ms`, `status`.  
5. **Aggregation** → `repository_aggregates.parquet`.  
6. **Statistical analysis** → `correlation_results.parquet`, `threshold_results.parquet`.  
7. **Report** → `final_report.json` + figures.

All files are version‑hashed and listed in `data/checksums.txt`.

---
