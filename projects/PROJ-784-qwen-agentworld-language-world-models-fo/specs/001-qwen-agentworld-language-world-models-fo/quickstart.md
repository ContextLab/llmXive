# Quickstart: Qwen-AgentWorld Adaptation

This script reproduces the core "World Model" evaluation from the paper using a small-scale, CPU-tractable setup.

## Prerequisites

Ensure the following dependencies are installed:
```bash
pip install gymnasium torch numpy matplotlib
```

## Run Commands

Execute the following command to run the adaptation. It will collect real data from the `FrozenLake-v1` environment, train a small LSTM world model, and generate artifacts.

```bash
python code/world_model_adapter.py
```

## Expected Outputs

After completion, verify the following files exist in the `data/` and `figures/` directories:
- `data/model_results.json`: Contains accuracy metrics comparing the World Model to a baseline.
- `figures/prediction_accuracy.png`: A visualization of the training loss and accuracy comparison.

The script is designed to complete in under 15 minutes on a standard CPU.
