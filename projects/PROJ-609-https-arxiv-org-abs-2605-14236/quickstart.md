# Quick Start Guide

Run the adaptation script to generate synthetic results and plots.
This script requires `numpy`, `pandas`, and `matplotlib` (standard CPU dependencies).

```bash
pip install numpy pandas matplotlib
python code/run_adaptation.py
```

The script will:
1. Generate a synthetic dataset of 5 queries.
2. Run Bubble Sort, Quick Sort, and an Active Learning proxy.
3. Save results to `data/synthetic_results.csv`.
4. Save plots to `figures/ndcg_vs_budget.png` and `figures/noise_analysis.png`.
