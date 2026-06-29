# Data Model: Qwen‑VLA Cross‑Embodiment Transfer Study  

## Overview
All artifacts are defined as explicit JSON‑compatible records and validated against YAML schemas located in `contracts/`. The schemas are used by the test suite (`pytest‑contracts`) to guarantee structural integrity before any CI job proceeds.

## Entities & Schemas

### 1. `DatasetSubset`
| Field | Type | Description |
|-------|------|-------------|
| `num_examples` | integer | Number of demonstrations after filtering. |
| `platform_ids` | list[string] | Unique robot platform identifiers present in the subset. |
| `checksum` | string | SHA‑256 checksum of the parquet file. |
| `dataset_version` | string | Exact version identifier (e.g., commit hash or revision ID) of the source dataset. |
| `path` | string | Relative path to the parquet file (e.g., `data/subset.parquet`). |
| `ratio` | number | Cross‑embodiment proportion (0.0 – 1.0). |

### 2. `ModelCheckpoint`
| Field | Type | Description |
|-------|------|-------------|
| `size_mb` | number | File size in megabytes (≤ 2000). |
| `training_config` | object | Nested object containing hyper‑parameters (learning_rate, batch_size, seeds, ratio, wall_time_sec). |
| `path` | string | Relative path to the checkpoint file (`models/checkpoint_{ratio}_{seed}.pt`). |
| `timestamp` | string (ISO‑8601) | Creation time. |

### 3. `EvaluationResult`
| Field | Type | Description |
|-------|------|-------------|
| `seed` | integer | Random seed used for this run. |
| `benchmark` | string | Either `LIBERO-Spatial` or `LIBERO-Object`. |
| `platform` | string | Held‑out robot platform (`Franka` or `UR5`). |
| `success_rate` | number | Percentage of successful task completions (0‑100). |
| `trajectory_length` | number | Mean trajectory length (timesteps). |
| `variance` | number | Variance of success_rate across episodes. |
| `checkpoint_path` | string | Path to the checkpoint evaluated. |

### 4. `StatisticalReport`
| Field | Type | Description |
|-------|------|-------------|
| `test_name` | string | `"wilcoxon_signed_rank"` or `"linear_regression_slope"`. |
| `p_value` | number | Raw p‑value. |
| `p_value_corrected` | number | Holm‑Bonferroni corrected p‑value (if applicable). |
| `significant` | boolean | Decision at α = 0.05. |
| `effect_size` | number | For Wilcoxon: `r`; for regression: slope. |
| `confidence_interval` | list[number] | 95 % CI for the effect size. |
| `seed_vectors` | list[number] | Success‑rate vectors used in the test. |

### 5. `ReproducibilityManifest`
| Field | Type | Description |
|-------|------|-------------|
| `python_version` | string | e.g., `"3.11.9"` |
| `torch_version` | string | e.g., `"2.3.0+cpu"` |
| `dependencies` | list[string] | Full `pip freeze` output. |
| `git_commit` | string | Full commit hash. |
| `dataset_checksum` | string | SHA‑256 of the filtered subset. |
| `dataset_version` | string | Exact version identifier of the source dataset. |
| `hyperparameters` | object | All FR‑related hyper‑parameters (learning_rate, batch_size, seeds, ratio). |
| `wall_time_sec` | number | Total wall‑time of the CI job. |
| `peak_ram_gb` | number | Peak RSS observed. |

## Contract Files
- `contracts/dataset_subset.schema.yaml`
- `contracts/model_checkpoint.schema.yaml`
- `contracts/evaluation_result.schema.yaml`
- `contracts/statistical_report.schema.yaml`
- `contracts/reproducibility_manifest.schema.yaml`

Each schema is a single valid YAML document (see individual files below).

---
