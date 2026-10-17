# Quickstart: Density-Supervision Study for d-OPSD Diffusion LLMs

This guide describes how to run the full experimental pipeline from a
clean checkout. The single entry point is `code/run_experiments.py`,
driven by a YAML configuration file.

## Prerequisites

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

The platform runner already provides `numpy`, `pandas`, `scipy`,
`matplotlib`, `scikit-learn`, `statsmodels`, `seaborn`, `pytest`,
`PyYAML`, `requests`, `jsonschema`, and `psutil`.

## Command line

Run the whole pipeline with the quickstart configuration:

```bash
python -m code.run_experiments --config configs/quickstart.yaml
```

On success the command prints `Pipeline initialized`, creates the
`outputs/` directory tree, writes `outputs/run_config.json` with the
effective configuration, and executes the stages listed in the config.
Stages whose implementing modules do not exist yet are skipped with a
warning — they are added by later tasks.

### Options (for later tasks)

| Flag | Description |
|------|-------------|
| `--config <path>` | Path to a YAML config file (default `configs/quickstart.yaml`) |
| `--mode <name>` | Run only one stage: `fixed` or `adaptive` |
| `--rhos <list>` | Retaining ratios for fixed‑density runs |
| `--seeds <list>` | Random seeds for replication |
| `--output <path>` | Destination for result files |
| `--dry-run` | Initialise outputs and exit without running any stage |

## Expected artefacts from the quick‑start run

- `outputs/run_config.json` – the effective configuration used.
- `data/results/fixed_baselines.csv` – CSV containing a thin
 fixed‑density baseline run (the default training hyper‑parameters
 from `quickstart.yaml`).
- `outputs/` sub‑directories as declared in `quickstart.yaml`
 (`statistics`, `figures`, `summary`, `checkpoints`).

The thin run uses a single seed (42) and a single retaining ratio
(0.5) as defined in `configs/quickstart.yaml`. It completes within the
6‑hour wall‑clock limit on a standard CPU‑only runner.

## Seed control

The global seed is recorded in `outputs/run_config.json`. The trainer
sets the Python, NumPy, and (if available) PyTorch RNGs for each run
to guarantee reproducibility.

## How the pipeline works

1. **Data stage** – streams GSM8K and the logical reasoning dataset,
 snapshots them under `data/raw/`, and writes `data/raw/manifest.txt`.
2. **Model stage** – downloads a ≤ 100 M‑parameter diffusion model and
 writes `outputs/model_checkpoint.json`.
3. **Fixed‑baseline stage** – runs a lightweight dummy training loop
 (CPU‑only) and records a deterministic accuracy metric in
 `data/results/fixed_baselines.csv`.
4. **Adaptive / analysis stages** – placeholders for later tasks.

All stages respect the 6‑hour runtime limit and write their outputs
to the locations declared in the configuration.