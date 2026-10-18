# Quickstart: Density‑Supervision Study for d‑OPSD Diffusion LLMs

This guide describes how to run the experimental pipeline from a
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

## Running the pipeline

### Thin (quick‑start) run

```bash
python -m code.run_experiments --config configs/quickstart.yaml
```

On success the command prints `Pipeline initialized` [UNRESOLVED-CLAIM: c_52396f5a — status=not_enough_info], creates the
`outputs/` directory tree, writes `outputs/run_config.json` with the
effective configuration, and runs a single fixed‑density baseline
(ρ = 0.5, seed = 42) on a tiny placeholder dataset. Expected wall‑clock
time is **under a minute** on a standard CPU‑only runner.

### Full experiment suite

```bash
python -m code.run_experiments --config configs/full_suite.yaml
```

This runs the complete suite:
- Data placeholder creation
- Model download (`distilgpt2`)
- Fixed‑density baselines for five retaining ratios and five seeds [UNRESOLVED-CLAIM: c_6d2694e9 — status=not_enough_info]
- (Adaptive and analysis stages are placeholders for later tasks)

The full suite is expected to take **a few minutes** per fixed‑density
run but remains well within the 6‑hour per‑job limit.

## Expected artefacts

- `outputs/run_config.json` – the effective configuration used.
- `data/results/fixed_baselines.csv` – CSV containing results from the
 thin run (quick‑start) or the full grid (full suite).
- Sub‑directories under `outputs/` as declared in the YAML configs
 (`statistics`, `figures`, `summary`, `checkpoints`).

All stages respect the 6‑hour runtime limit [UNRESOLVED-CLAIM: c_35e79a28 — status=not_enough_info] and write their outputs
to the locations declared in the configuration.