# Quickstart: EmbedFilter CPU Adaptation

This script reproduces the core mechanism of the EmbedFilter paper on a CPU-only environment using a scaled-down model and dataset.

## Prerequisites
Ensure the following packages are installed:
```bash
pip install torch transformers datasets matplotlib numpy
```

## Run Command
Execute the adaptation script:
```bash
python code/adapter.py
```

## Expected Outputs
- `data/similarity_results.json`: Contains the similarity scores before and after filtering.
- `figures/similarity_comparison.png`: A bar chart comparing the two metrics.
