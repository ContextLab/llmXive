# Data Model: llmXive follow‑up – extending "Mellum2 Technical Report"

## Overview
All intermediate and final artifacts are stored as columnar Parquet (Snappy) or JSON files. Schemas are defined in `contracts/` and validated with `jsonschema`. Deterministic file naming and checksums guarantee reproducibility.

## Entities

### 1. CodeChunk
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (`repo:file:chunk_index`). |
| `repo_name` | string | Source repository name. |
| `language` | string (`"python"` | `"java"` | `"other"` ) | Programming language. |
| `content` | string | Raw source code. |
| `cyclomatic_complexity` | integer ≥ 0 | From CodeQL. |
| `nesting_depth` | integer ≥ 0 | From tree‑sitter. |
| `repetition_ratio` | number ∈ [0, 1] | Token‑level repetition. |
| `token_count` | integer ≥ 1 | Number of tokens (confounder). |
| `ngram_probability` | number > 0 | KenLM estimate (FR‑010). |
| `per_token_loss` | number | Average cross‑entropy loss. |
| `entropy` | number | Average prediction entropy. |
| `inference_time_ms` | integer ≥ 0 | Latency per chunk (ms). |
| `status` | string (`"success"` | `"timeout"` | `"parse_error"` | `"oom"` ) | Processing outcome. |
| **Optional** `comment_density` | number ≥ 0 | Ratio of comment tokens to total tokens (additional confound). |
| **Optional** `file_length` | integer ≥ 0 | Number of lines in the source file (additional confound). |
| **Optional** `repo_popularity` | number ≥ 0 | Normalized star count or fork count of the repository (additional confound). |

### 2. RepositoryAggregate
| Field | Type | Description |
|-------|------|-------------|
| `repo_name` | string | Repository identifier. |
| `language` | string | Language of repo. |
| `mean_cyclomatic_complexity` | float | Repo‑level mean. |
| `mean_nesting_depth` | float | Repo‑level mean. |
| `mean_per_token_loss` | float | Raw loss mean. |
| `mean_normalized_loss` | float | Loss after regression‑residual normalization. |
| `mean_token_count` | float | Mean token count. |
| `chunk_count` | integer ≥ 1 | Number of processed chunks. |

### 3. CorrelationResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string |
| `language` | string |
| `method` | string (`"pearson"` | `"spearman"` ) |
| `correlation_coefficient` | float ∈ [‑1, 1] |
| `p_value` | float ∈ [0, 1] |
| `p_value_adjusted` | float ∈ [0, 1] |
| `sample_size` | integer ≥ 1 |

### 4. ThresholdResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string |
| `language` | string |
| `threshold_value` | float |
| `slope_before` | float |
| `slope_after` | float |
| `model_fit` | string (`"piecewise"` | `"linear"` ) |
| `aic_difference` | float |
| `significance` | boolean |
| `bootstrap_stability` | float |
| `confidence_interval_width` | float |
| `sensitivity_range` | array of float |

### 5. FinalReport (output.schema.yaml)
See `contracts/output.schema.yaml` for the full JSON schema.

## Data Flow Diagram
1. **Download** → `raw_samples.parquet` (`Dataset` schema).  
2. **Static analysis** → `code_chunks.parquet` (`CodeChunk` schema).  
3. **KenLM** → adds `ngram_probability`.  
4. **Inference** → adds `per_token_loss`, `entropy`, `inference_time_ms`, `status`.  
5. **Normalization** → regression residuals produce `normalized_loss`.  
6. **Aggregation** → `repository_aggregates.parquet`.  
7. **Statistical analysis** → `correlation_results.parquet`, `threshold_results.parquet`.  
8. **Report** → `final_report.json` + figures.

All files are listed in `data/checksums.txt` with SHA‑family hashes.

---

