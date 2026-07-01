# Quickstart: Scaled iLLaDA Adaptation

This script reproduces the core masked diffusion mechanism of the iLLaDA paper on a tiny scale using real data (WikiText-2) and a CPU-friendly model.

## Prerequisites
Ensure you have the necessary dependencies installed:
```bash
pip install torch transformers datasets matplotlib pandas tqdm numpy
```

## Run the Adaptation
Execute the following command to train the model and generate the real output artifacts:

```bash
python code/run_llada_scaled.py
```

## Expected Outputs
After completion, check the `data/` and `figures/` directories:
- `data/training_metrics.csv`: Loss history.
- `data/reconstruction_results.json`: **The core result** (Reconstruction Accuracy on real text).
- `figures/loss_curve.png`: Training visualization.

The `reconstruction_results.json` file will contain a real accuracy metric (e.g., `0.45` for 45%) derived from the model's ability to predict masked tokens in real English sentences, demonstrating the efficacy of the bidirectional diffusion approach at a small scale.
