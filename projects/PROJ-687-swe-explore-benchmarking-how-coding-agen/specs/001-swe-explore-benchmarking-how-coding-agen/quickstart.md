# SWE-Explore CPU Adaptation Runbook

This runbook executes a scaled-down version of the SWE-Explore evaluation on a CPU-only environment. It simulates a repository, defines ground-truth "oracle" trajectories, and compares them against TF-IDF and Random baselines.

## Prerequisites

Ensure the following packages are installed:
```bash
pip install pandas scikit-learn matplotlib numpy
```

## Execution

Run the evaluation script:

```bash
python code/evaluate_metrics.py
```

## Outputs

The script generates the following artifacts in the `data/` and `figures/` directories:

- `data/evaluation_results.csv`: Detailed metrics (Precision, Recall, nDCG) for each issue and explorer.
- `data/evaluation_results.json`: JSON version of the results.
- `figures/comparison_scaled.png`: Bar chart comparing the performance of Oracle, TF-IDF, and Random baselines.
