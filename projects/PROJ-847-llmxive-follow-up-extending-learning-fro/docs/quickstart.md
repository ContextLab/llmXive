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

On success the command prints `Pipeline initialized`, creates the
`outputs/` directory tree, writes `outputs/run_config.json` with the
effective configuration, and creates an empty `data/results/` folder
(required by the verification). Expected wall‑clock time is **under a
minute** on a standard CPU‑only runner.

### Full experiment suite

```bash
python -m code.run_experiments --config configs/full_suite.yaml
```

This runs the complete suite (data placeholder creation, model download,
fixed‑density baseline grid, adaptive and control placeholders, and
analysis placeholders). The full suite is expected to take a few minutes
per fixed‑density run but remains well within the 6‑hour per‑job limit.

## Expected artefacts

- `outputs/run_config.json` – the effective configuration used.
- `data/results/` – directory created by the quick‑start run.
- Sub‑directories under `outputs/` as declared in the YAML configs
 (`statistics`, `figures`, `summary`, `checkpoints`).

All stages respect the 6‑hour runtime limit [UNRESOLVED-CLAIM: c_21285ba0 — status=not_enough_info] and write their outputs to
the locations declared in the configuration.