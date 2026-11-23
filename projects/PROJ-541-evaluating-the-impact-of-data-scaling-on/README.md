# Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

Simulation-based study of how three data scaling methods
(standardization, min-max, robust median/IQR) affect the Type I error
rates and statistical power of parametric tests (t-test, ANOVA,
chi-squared) under varying distributional assumptions, with real-world
validation on public UCI/OpenML datasets.

## Project layout

```text
code/ # source code (simulation, preprocessing, analysis, visualization)
code/tests/ # unit and integration tests
data/ # raw / synthetic / scaled data
results/ # aggregated results, figures, reports
logs/ # structured run logs
specs/ # feature specification, plan, contracts
```

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

All dependencies are pinned for reproducibility. The heavy ML backends
(jax, tensorflow, torch) that were previously listed but never imported
have been removed; `numpy` is pinned to the 2.x series so that
`pyarrow`/`datasets` import cleanly.

## Usage

```bash
# Smoke run of the simulation loop
python code/main.py --mode simulation --iterations 100

# Real-world dataset pipeline
python code/main.py --mode real_world

# Analysis / visualization
python code/main.py --mode analyze
python code/main.py --mode visualize
```

## Linting and formatting

The project uses `ruff` for linting and `black` for formatting
(configuration in `ruff.toml` and `pyproject.toml` at the repository
root). Pre-commit hooks are declared in `.pre-commit-config.yaml`.

```bash
pip install ruff black pre-commit
ruff check.
black --check.
pre-commit install
```

A one-shot verification script checks that all scaffolding files exist
and that both linters pass:

```bash
python code/verify_scaffolding.py
```

## Testing

```bash
pytest code/tests
```

## Reproducibility

* All random seeds are pinned in the simulation configuration.
* External datasets are checksummed on ingestion.
* Figures and statistics are generated programmatically from
 `results/` artifacts.
