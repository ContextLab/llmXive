# Quickstart: Domino CPU Adaptation

This guide runs the CPU-scaled simulation of the Domino paper's core mechanism.

## Prerequisites
Ensure the following packages are installed (CPU-only):
```bash
pip install torch numpy matplotlib datasets tqdm loguru
```

## Run Command
Execute the simulation script. It will download a small real dataset, run the simulation, and generate outputs.
```bash
python code/run_domino_simulation.py
```

## Expected Outputs
After completion, check the `data/` and `figures/` directories:
- `data/acceptance_rates.json`: Contains the quantitative results (acceptance rates).
- `figures/acceptance_comparison.png`: A bar chart comparing the Baseline, Domino, and Causal methods.
