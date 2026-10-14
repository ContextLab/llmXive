# Data Model: llmxive-density-analysis

## Entities

### TrainingConfig
| Field               | Type    | Description |
|---------------------|---------|-------------|
| `run_id`            | `string`| Unique identifier for the training run. |
| `rho_teacher`       | `float` | Retaining ratio; either a fixed value or `null` for adaptive mode. |
| `adaptive`          | `bool`  | `true` if the scheduler is active. |
| `max_epochs`        | `int`   | Upper bound on training epochs (default 10). |
| `batch_size`        | `int`   | Number of examples per training step. |
| `seed`              | `int`   | Random seed for reproducibility. |
| `timeout_seconds`   | `int`   | Hard wall‑clock limit (6 h = 21600 s). |
| `dataset_name`      | `string`| Name of the dataset (e.g., `"gsm8k"`). |

### TrainingRun
| Field               | Type                | Description |
|---------------------|---------------------|-------------|
| `config`            | `TrainingConfig`    | Configuration used for the run. |
| `loss_trajectory`   | `list<float>`       | Per‑step training loss values. |
| `final_accuracy`    | `float`             | Logical accuracy on the held‑out test set. |
| `runtime_seconds`   | `float`             | Total wall‑clock time. |
| `density_time_series`| `list<float>` (optional) | ρ values per step (present only for adaptive runs). |
| `timeout`           | `bool`              | `true` if the run stopped due to the 6‑hour limit. |
| `metadata`          | `dict`              | Arbitrary key‑value info (e.g., checkpoint paths). |

### StatisticalResult
| Field                     | Type                | Description |
|---------------------------|---------------------|-------------|
| `t_test_result`           | `dict`              | Keys: `t_statistic`, `p_value`, `df` (or `u_statistic`, `p_value` for non‑parametric fallback). |
| `quadratic_coefficients`  | `list<float>` (len 3) | Coefficients `[a, b, c]` for `a·ρ² + b·ρ + c`. |
| `peak_density`            | `float`             | ρ value that maximizes the quadratic fit. |
| `sensitivity_slopes`     | `dict`              | Keys: `"plus_0.05"`, `"minus_0.05"`, `"plus_0.1"`, `"minus_0.1"`; values are accuracy change per 0.01 density. |
| `analysis_timestamp`      | `string` (ISO‑8601) | When the analysis was executed. |

All entities are serializable to JSON and validated against the schemas in `contracts/`.

---

