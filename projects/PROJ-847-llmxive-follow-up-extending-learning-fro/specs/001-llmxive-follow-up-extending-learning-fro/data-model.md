# Data Model: llmxive-density-analysis

## Entities

### TrainingConfig
| Field               | Type                     | Description |
|---------------------|--------------------------|-------------|
| `run_id`            | `string`                 | Unique identifier for the training run. |
| `rho_teacher`       | `number` or `null`       | Fixed retaining ratio; `null` when adaptive. |
| `adaptive`          | `boolean`                | `true` if the entropy‑based scheduler is active. |
| `max_epochs`        | `integer`                | Upper bound on training epochs (default 5). |
| `batch_size`        | `integer`                | Number of examples per training step. |
| `seed`              | `integer`                | Random seed for reproducibility. |
| `timeout_seconds`   | `integer`                | Hard wall‑clock limit (21600 s). |
| `dataset_name`      | `string`                 | Identifier of the dataset (e.g., `"gsm8k"`). |

### TrainingRun
| Field                | Type                     | Description |
|----------------------|--------------------------|-------------|
| `config`             | `TrainingConfig`         | Configuration used for the run. |
| `loss_trajectory`    | `array<number>`          | Per‑step training loss values. |
| `final_accuracy`     | `number`                 | Exact‑match logical accuracy on the held‑out test set. |
| `final_f1`           | `number`                 | Token‑level F1 (graded accuracy). |
| `runtime_seconds`    | `number`                 | Total wall‑clock time. |
| `density_time_series`| `array<number>` (optional) | ρ values per step (present only for adaptive runs). |
| `timeout`            | `boolean`                | `true` if stopped due to the 6‑hour limit. |
| `metadata`           | `object` (free‑form)     | Arbitrary key‑value info (e.g., checkpoint paths). |

### StatisticalResult
| Field                     | Type                     | Description |
|---------------------------|--------------------------|-------------|
| `t_test_result`           | `object`                 | Contains `t_statistic`, `p_value`, `df` (or `u_statistic` for non‑parametric). |
| `quadratic_coefficients`  | `array<number>` (len 3)  | Coefficients `[a, b, c]` for `a·ρ² + b·ρ + c`. |
| `peak_density`            | `number`                 | ρ value that maximizes the quadratic fit (with CI). |
| `sensitivity_slopes`     | `object`                 | Keys: `"plus_0.05"`, `"minus_0.05"`, `"plus_0.1"`, `"minus_0.1"`; values are accuracy change per 0.01 density. |
| `entropy_error_correlation`| `object`                | Keys: `pearson_r`, `p_value`; correlation between prediction entropy and per‑example error. |
| `causal_control_test`    | `object` (optional)      | Result of adaptive vs. shuffled‑entropy control comparison (t‑statistic, p‑value, df). |
| `analysis_timestamp`      | `string` (ISO‑8601)      | When the statistical analysis was executed. |

All entities are JSON‑serializable and validated against the schemas in `contracts/`.

---
