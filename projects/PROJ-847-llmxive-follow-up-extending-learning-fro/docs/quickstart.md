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
`PyYAML `, `requests`, `jsonschema`, and `psutil`.

## Command line

Run the whole pipeline with the quickstart configuration:

```bash
python -m code.run_experiments --config configs/quickstart.yaml
```

On success the command prints `Pipeline initialized` [UNRESOLVED-CLAIM: c_28bd2609 — status=not_enough_info], creates the
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
| `--dry-run` | Initialize outputs and exit without running any stage |

## Required environment variables

None. All datasets used by the pipeline (GSM8K, bigbench_lite) are
publicly downloadable from HuggingFace without authentication.

## Seed control

- The global seed is set in the config file (`seed: 42` in
 `configs/quickstart.yaml`) and can be overridden per invocation with
 `--seed`.
- The seed is recorded in `outputs/run_config.json` for reproducibility. [UNRESOLVED-CLAIM: c_edec4965 — status=not_enough_info]

## Configuration file

`configs/quickstart.yaml` controls:

- `seed` — global random seed,
- `output_dirs` — subdirectories created under `outputs/`,
- `stages` — ordered list of pipeline stages to execute,
- `training` — hyper‑parameters (ρ values, seeds, epochs, batch size,
 wall‑clock timeout),
- `data` / `model` — dataset and model settings consumed by later tasks.

## Outputs

- `outputs/run_config.json` — effective run configuration (written at
 initialization).
- Later tasks add: `data/raw/`, `data/results/`,
 `outputs/statistics/`, `outputs/figures/`, `outputs/summary/`,
 `outputs/checkpoints/`.