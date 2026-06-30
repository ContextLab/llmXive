# Quick Start: $\pi$-Bench CPU Adaptation

This guide runs the simplified, CPU-tractable simulation of the $\pi$-Bench paper.
It generates synthetic data to reproduce the core finding: the distinction between **Task Completion** and **Proactivity**.

## Prerequisites
Ensure the following packages are installed:
```bash
pip install numpy pandas matplotlib scikit-learn
```

## Run the Simulation
Execute the adaptation script. It will generate CSV results and a comparison plot.

```bash
python code/simulate_pi_bench.py
```

## Verify Outputs
After execution, check the generated artifacts:
- `data/results.csv`: Raw simulation data for each task.
- `data/aggregate_metrics.csv`: Summary statistics (Task Completion vs. Proactivity).
- `data/detailed_results.json`: Sampled interaction logs.
- `figures/comparison_bar.png`: Visual comparison of the two metrics.
