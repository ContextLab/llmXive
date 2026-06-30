# Quickstart: Long-Context Retrieval Proxy

This script simulates the core quantitative findings of the paper "Training Long-Context Vision-Language Models Effectively..." using a CPU-tractable "Needle In A Haystack" proxy.

**Prerequisites:**
- Python 3.8+
- `pip install matplotlib` (optional, for plots)

**Run Commands:**
```bash
python code/long_context_proxy.py
```

**Expected Outputs:**
- `data/retrieval_results.csv`: Detailed per-sample results.
- `data/metrics_summary.json`: Aggregated accuracy metrics.
- `figures/accuracy_vs_length_depth.png`: Visualization of accuracy degradation.
