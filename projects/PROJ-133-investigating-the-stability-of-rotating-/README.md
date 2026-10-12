# Investigating the Stability of Rotating Bose‑Einstein Condensates with Dipolar Interactions

**Project ID:** PROJ‑133
**Repository root:** `projects/PROJ-133-investigating-the-stability-of-rotating-`

## Overview

This repository implements a reproducible computational study of rotating dipolar Bose‑Einstein condensates (BECs).
The core scientific question is **how rotation frequency (Ω), dipolar interaction strength (ε₍dd₎), and atom number (N) jointly determine the dynamical stability and vortex‑lattice structures** of a trapped BEC.

The workflow consists of:
1. Solving the time‑dependent Gross‑Pitaevskii equation (GPE) on a 2‑D grid.
2. Detecting vortices via phase‑winding analysis.
3. Computing stability metrics (vortex density, radial variance, structure‑factor sharpness).
4. Performing a Two‑Way ANOVA with Dunnett post‑hoc on the metrics.
5. Generating phase‑map visualisations.

All steps are fully automated and stored under the `data/` and `figures/` directories.

## Dependencies

The project uses only standard scientific Python packages that are pre‑installed on the platform **plus** a pinned `requirements.txt` for reproducibility.
```text
numpy
scipy
matplotlib
pandas
numba
pytest
```
The full list with exact versions is in `code/requirements.txt`.

## Quick‑Start

The following single command reproduces the **full 64 × 64 grid scan** (≈300 runs, 5 repeats each) and writes all raw outputs to `data/raw/`:

```bash
python -m simulation.runner --grid-config../../specs/001-investigating-the-stability-of-rotating/grid_config.json --repeats 5 --output-dir../../data/raw
```

After the simulations finish, run the analysis and visualisation pipeline:

```bash
# Compute metrics from the raw snapshots
python -m analysis.metrics --input-dir../../data/raw --output-file../../data/processed/metrics.csv

# Aggregate statistics and perform Two‑Way ANOVA
python -m statistics.aggregators --input-file../../data/processed/metrics.csv --output-file../../data/aggregated/statistical_results.json

# Generate the final phase‑map figures
python -m viz.plotter --input-file../../data/aggregated/statistical_results.json --output-dir../../figures
```

For a **single validation run** (e.g., Ω = 0.5, ε₍dd₎ = 0.5, N = 10⁴) you can execute:

```bash
python -m simulation.runner --N 10000 --Omega 0.5 --epsilon_dd 0.5 --seed 42 --output-dir../../data/raw
```

## Generated Figures

The pipeline produces the following visual artefacts in the `figures/` directory:

- `phase_map.png` – Contour map of the vortex‑density phase diagram (Ω × ε₍dd₎).
- `stable_example.png` – Representative density/phase snapshot of a stable configuration.
- `metastable_example.png` – Representative snapshot of a metastable configuration.
- `unstable_example.png` – Representative snapshot of an unstable configuration.

These figures are referenced throughout the manuscript and the `docs/methods.md` documentation.

## Repository Structure

```
code/
├── analysis/
├── simulation/
├── statistics/
├── viz/
└── utils/
data/
├── raw/
├── processed/
└── aggregated/
tests/
├── unit/
├── contract/
└── integration/
specs/
└── 001-gene-regulation/
 ├── quickstart.md
 └── spec.md
```

## Running Tests

```bash
pytest tests/
```

All contract tests (`tests/contract/`) must pass, ensuring that the directory layout, linting configuration, and README contents meet the project standards.

## License

This project is released under the MIT License. See `LICENSE` for details.