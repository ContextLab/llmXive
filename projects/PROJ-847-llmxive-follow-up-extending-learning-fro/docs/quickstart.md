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

### Options

| Flag | Description |
|------|-------------|
| `--config <path>` | Path to a YAML config file (default `configs/quickstart.yaml`) |
| `--stage <name>` | Run only one stage: `data`, `model`, `fixed_baselines`, `adaptive_runs`, or `analysis` |
| `--seed <int>` | Override the seed from the config file for this run |
| `--dry-run` | Initialize outputs and exit without running any stage |

## Required environment variables

None. All datasets used by the pipeline (GSM8K, bigbench_lite) are
publicly downloadable from HuggingFace without authentication. If a
later stage introduces an authenticated resource, this section will be
updated and the loader will fail loudly rather than silently falling
back to synthetic data.

## Seed control

- The global seed is set in the config file (`seed: 42` in
 `configs/quickstart.yaml`) and can be overridden per invocation with
 `--seed`.
- The seed is applied to Python's `random`, NumPy, and (when installed)
 PyTorch RNGs before any stage runs, and the effective value is
 recorded in `outputs/run_config.json` for exact reproducibility.
- Replication seeds for training runs (default `[42, 43, 44]`) are
 configured under `training.seeds` in the config file.

## Configuration file

`configs/quickstart.yaml` controls:

- `seed` — global random seed,
- `output_dirs` — subdirectories created under `outputs/`,
- `stages` — ordered list of pipeline stages to execute,
- `training` — hyper-parameters (ρ values, seeds, epochs, batch size,
 wall-clock timeout),
- `data` / `model` — dataset and model settings consumed by later tasks.

## Outputs

- `outputs/run_config.json` — effective run configuration (written at
 initialization).
- Later tasks add: `data/raw/`, `data/results/`,
 `outputs/statistics/`, `outputs/figures/`, `outputs/summary/`,
 `outputs/checkpoints/`.
