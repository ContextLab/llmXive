# Data Model: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

## Raw Data Assets
| Asset | Description | Location | Checksum (sha256) |
|-------|-------------|----------|-------------------|
| GSM8K train parquet | Full training set of GSM8K reasoning problems | `data/raw/gsm8k_train.parquet` | `{{sha256_of_train_parquet}}` |
| GSM8K test parquet | Full test set (used for held‑out generalization subset) | `data/raw/gsm8k_test.parquet` | `{{sha256_of_test_parquet}}` |
| Seed list | JSON file enumerating the seeds used across all experiments | `data/metadata/seeds.json` | `{{sha256_of_seeds_json}}` |

## Derived Data Assets
| Asset | Generation Step | Format | Key Fields |
|-------|-----------------|--------|------------|
| `subspace_mask_{seed}.json` | Layer‑wise SVD on first 3 epochs of OPD baseline **per seed** | JSON | `layer_name`, `mask_vector` (binary 0/1), `k`, `variance_explained` |
| `mask_random.json` | Random binary mask of same dimensionality as OPD mask, generated once with fixed seed (`mask_seed = 9999`) | JSON | Same schema as `subspace_mask_{seed}.json` |
| `model_checkpoints/` | Saved after each epoch for every seed & condition (FR‑002, FR‑004, FR‑005) | GGML 4‑bit binary files (`*.ggml`) | `run_id`, `seed`, `epoch`, `condition` |
| `results/accuracy.csv` | Accuracy on held‑out generalization subset per run | CSV | `run_id`, `seed`, `condition`, `accuracy` |
| `results/loss_trajectory.csv` | Epoch‑wise loss per run | CSV | `run_id`, `seed`, `condition`, `epoch`, `loss` |
| `results/resource_usage.csv` | Peak RAM (MB) and wall‑clock time (sec) per run | CSV | `run_id`, `seed`, `condition`, `peak_ram_mb`, `wall_time_sec` |
| `results/experiment_summary.csv` | **Unified artifact** containing **all** fields required by `contracts/experiment.schema.yaml` for each run (including variance explained, TOST p‑values, power, t‑test p‑value, accuracy drop, plateau epoch) | CSV | `run_id`, `seed`, `condition`, `epoch`, `accuracy`, `loss`, `peak_ram_mb`, `wall_time_sec`, `variance_explained`, `tost_p_lower`, `tost_p_upper`, `power`, `t_test_p`, `accuracy_drop_pp`, `plateau_epoch` |
| `results/statistics.json` | Summary of TOST, power, t‑tests, plateau epochs (overall) | JSON | `tost_p_lower`, `tost_p_upper`, `power`, `t_test_p`, `accuracy_drop_pp`, `plateau_epoch` |

All derived files are version‑hashed (e.g., `accuracy_{{hash}}.csv`) and referenced in the final report.

## Schema References
- `contracts/experiment.schema.yaml` defines the required columns and data types for each CSV/JSON asset (see contract file).  
- Checksums are stored in `data/checksums.txt` and verified at pipeline start.

## Data Flow Diagram (textual)
```
download_gsm8k.py  --> raw parquet files
opd_baseline.py    --> per‑layer deltas (saved as .npy)
svd_compute.py     --> subspace_mask_{seed}.json (+ sensitivity sweep, per‑seed)
mask.py            --> apply binary mask during training
train/*.py         --> model checkpoints + loss logs
evaluate.py        --> accuracy.csv, loss_trajectory.csv
stats.py           --> statistics.json, experiment_summary.csv
resource_monitor.py--> resource_usage.csv
```

---


