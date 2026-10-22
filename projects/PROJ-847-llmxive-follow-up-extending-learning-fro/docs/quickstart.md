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

## Running the pipeline

### Thin (quick‑start) run

```bash
python -m code.run_experiments --config configs/quickstart.yaml
```

On success the command prints `Pipeline initialized`, creates the
`outputs/` directory tree, writes `outputs/run_config.json` with the
effective configuration, and creates the `data/results/` folder.
Expected wall‑clock time is **under 10 minutes** depending on the
model download speed. This run generates a single baseline result for
$\rho=0.5$, seed 42.

### Full experiment suite

```bash
python -m code.run_experiments --config configs/full_suite.yaml
```

This runs the complete suite: data loading, model initialization, and
the full grid of fixed-density baseline runs (5 ratios $\times$ 5 seeds).
The full suite is expected to take several hours but remains well within
the 6‑hour per‑job limit. This is the primary path for regenerating
all baseline artifacts.

## Expected artefacts

- `outputs/run_config.json` – the effective configuration used.
- `data/results/` – directory containing baseline CSVs/JSONs.
- Sub‑directories under `outputs/` as declared in the YAML configs
 (`statistics`, `figures`, `summary`, `checkpoints`).