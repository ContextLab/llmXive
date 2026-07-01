# Quickstart: Arbor CPU Simulation

This run-book reproduces the core quantitative claim of the Arbor paper (Arbor > Baseline) using a scaled-down, CPU-tractable simulation.

## Prerequisites
- Python 3.8+
- Dependencies: `numpy`, `pandas`, `scikit-learn`, `matplotlib`

## Run Commands

```bash
pip install numpy pandas scikit-learn matplotlib -q
python code/run_arbor_simulation.py
```

## Expected Artifacts
- `data/results.csv`: Table of scores.
- `figures/gain_plot.png`: Bar chart comparing agents.
- `data/summary.json`: JSON summary with the calculated gain.

The script will print the "Relative Gain" to stdout. A positive value confirms the paper's claim in this scaled context.
