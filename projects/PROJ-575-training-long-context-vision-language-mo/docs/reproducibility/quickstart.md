# Reproducibility Quickstart

This guide provides the exact commands to reproduce the metrics found in `data/metrics_summary.json`.

## 1. Install Dependencies

```bash
pip install -r code/requirements.txt
```

## 2. Download Dataset

The evaluation script expects the dataset to be present in the `data/` directory. Ensure the dataset files are downloaded and placed there.

## 3. Run Evaluation

Execute the evaluation script with a sample size of 10 to regenerate the metrics:

```bash
python code/long_context_proxy.py --sample-size 10
```

This will overwrite `data/metrics_summary.json` with the new results.
