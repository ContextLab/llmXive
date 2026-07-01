# Quickstart: OpenThoughts-Agent Data Probe

This script reproduces the **data curation** aspect of the OpenThoughts-Agent paper at a small, CPU-tractable scale. It loads a real, tiny sample from the paper's dataset source, analyzes its quality (token distribution, diversity), and writes real artifacts.

## Prerequisites
- Python 3.9+
- `pip`

## Installation
```bash
pip install datasets pandas numpy matplotlib tqdm pyarrow tiktoken
```
*(Note: `tiktoken` is optional; if missing, a word-count fallback is used.)*

## Execution
Run the probe script. It will download a tiny sample of real data from HuggingFace, analyze it, and save results to `data/`.

```bash
python code/run_data_probe.py --limit 5 --output-dir data
```

## Expected Output
- `data/data_quality_stats.json`: JSON with metrics (mean tokens, diversity ratio).
- `data/sample_tasks.parquet`: A small parquet file with the real task samples.
- `data/data_distribution.png`: A plot of token distribution and diversity.

The script is designed to run entirely on CPU and finish in under 30 seconds.
