# Quickstart: NEO-ov Core Metric Reproduction

This guide runs the scaled-down reproduction of the NEO-ov paper's core claim on a CPU.

## Prerequisites
- Python 3.8+
- `pandas`, `numpy`, `matplotlib`

## Installation
```bash
pip install pandas numpy matplotlib
```

## Run the Experiment
Execute the following command to generate the results and plots:

```bash
python code/reproduce_neo_core.py
```

## Outputs
After completion, check the following artifacts:
- `data/results.csv`: Accuracy metrics for Native vs. Modular proxies.
- `figures/accuracy_comparison.png`: Visual comparison of the models.
