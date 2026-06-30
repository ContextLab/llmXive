# Quickstart: AntiSD Simulation

This guide runs the CPU-tractable simulation of the Anti-Self-Distillation paper.

## Prerequisites
Ensure you have the following pip packages installed:
```bash
pip install numpy pandas scikit-learn matplotlib
```

## Run the Simulation
Execute the following command to generate the synthetic dataset, run the simulated training loop, and produce the analysis artifacts:

```bash
python code/antisd_simulation.py
```

## Expected Outputs
After completion, you will find:
- `data/pmi_analysis.csv`: Token-level PMI and entropy metrics.
- `data/training_comparison.csv`: Step-by-step accuracy for SD vs. AntiSD.
- `data/training_comparison.json`: Summary statistics (final accuracy, gain).
- `figures/convergence_curve.png`: Visualization of the training dynamics.
