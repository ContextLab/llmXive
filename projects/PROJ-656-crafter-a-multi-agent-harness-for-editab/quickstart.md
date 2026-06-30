# Crafter CPU Adaptation - Quick Start

This adaptation reproduces the **evaluation metrics** of the Crafter paper on a small, real subset of the CraftBench dataset. It runs entirely on CPU, avoids GPU-heavy generation, and produces real artifacts.

## Prerequisites

Ensure you have the required dependencies installed:

```bash
pip install datasets pandas numpy scipy scikit-image matplotlib pillow requests
```

## Run Commands

Execute the adaptation script in order. It will download real data, compute metrics, and save outputs.

```bash
python code/crafter_adaptation.py
```

## Expected Outputs

After running, the following files will be created:

- `data/evaluation_results.json`: Detailed scores for each sample.
- `data/evaluation_results.csv`: Tabular version of the results.
- `figures/score_distribution.png`: A bar chart visualizing the scores.
- `data/<id>_gt.png`: The real ground truth images downloaded from the dataset.

## Verification

The script automatically verifies that the output files are non-empty and exist. If any step fails (e.g., network issue downloading data), it will exit with an error code rather than fabricating results.
