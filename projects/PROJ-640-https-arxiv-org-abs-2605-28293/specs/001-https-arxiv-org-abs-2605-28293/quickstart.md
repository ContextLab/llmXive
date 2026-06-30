# ProRL Adaptation Quickstart

This guide runs the CPU-tractable adaptation of the ProRL paper. It generates synthetic data, runs a simplified policy gradient simulation with the paper's core mechanisms (Stepwise Reward Centering and Position-Specific Advantage), and outputs results.

## Prerequisites
- Python 3.8+
- `pip install numpy pandas matplotlib` (PyTorch is optional; if missing, the script runs in pure NumPy fallback mode).

## Run Commands
Execute the following in order:

```bash
python code/adapter_proRL.py
```

## Output Artifacts
After execution, verify the following files exist:
- `data/prorl_results.csv`: Training metrics per epoch.
- `data/prorl_summary.json`: Final summary of the experiment.
- `figures/prorl_training_curve.png`: Visualization of reward and variance over epochs.
