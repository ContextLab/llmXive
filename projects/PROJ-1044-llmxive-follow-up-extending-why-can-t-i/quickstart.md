# Quickstart: Counterfactual Consistency Research Pipeline

> **One-command end-to-end** — runs the pipeline driver, which
> pre-computes optical-flow features for the original videos, writes the
> SHA-256 checksum manifest, and prints a summary of the generated
> artifacts before exiting with status 0.

## Prerequisites

- Python 3.11 with the project environment (numpy, pandas, scipy,
 matplotlib, scikit-learn, opencv, PyYAML are already available).
- CPU-only machine; no GPU required.

## Run

```bash
python -m src.pipeline.run_all --config configs/run.yaml
```

The command reads default paths and hyper-parameters from
`configs/run.yaml` (subset size, λ sweep values, seeds, thresholds,
output directory), executes the pipeline stages in order, prints a
`=== Pipeline Summary ===` block listing the generated artifacts, and
exits with status 0 on success.

## Artifacts produced

| Artifact | Description |
|----------|-------------|
| `data/flow/orig/*.npy` | Pre-computed Farneback optical-flow tensors for original videos |
| `data/checksums/manifest.csv` | SHA-256 manifest of every generated `.npy` file |
| `output/` | Root output directory for downstream stages |

## Re-running or extending

- Change the number of sampled videos via `subset_size` in the config.
- Extend `lambda_values` or `seeds` in the config for the sweep.
- All hyper-parameters live in `configs/run.yaml`; the run is
 deterministic for a fixed config.
