# MCompassRAG Adaptation: Quickstart

This guide runs the scaled-down reproduction of the MCompassRAG paper.
It uses a small sample of the `20newsgroups` dataset, `all-MiniLM-L6-v2` for embeddings, and `sklearn` for topic modeling.

## Prerequisites
```bash
pip install torch sentence-transformers scikit-learn pandas matplotlib datasets
```

## Run the Experiment
Execute the single script below. It will:
1. Load and chunk real data.
2. Build a topic model (LDA).
3. Generate queries.
4. Run Baseline and Compass retrieval.
5. Save results to `data/` and `figures/`.

```bash
python code/compass_lite.py
```

## Expected Output
- `data/results.csv`: Detailed per-query performance.
- `data/metrics.json`: Aggregated HR@5 and MRR.
- `figures/comparison.png`: Visualization of the improvement.

The script is designed to run in under 2 minutes on a standard CPU.
