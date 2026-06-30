# WBench CPU Adaptation - Quick Start

This script reproduces a **scaled-down, CPU-tractable** version of the WBench evaluation.
It replaces heavy GPU models (SAM2, Depth Anything, LMMs) with **synthetic proxies** and **randomized metrics** to demonstrate the evaluation pipeline logic without requiring GPUs or large datasets.

## Prerequisites
- Python 3.8+
- `pip install numpy pandas matplotlib` (Optional: script runs with stdlib fallbacks if these are missing, but plots require matplotlib).

## Execution

Run the adaptation script. It will:
1. Check for real cases in `data/cases`.
2. If missing or insufficient, generate 10 synthetic cases.
3. Compute proxy metrics (Video Quality, Consistency, Navigation, Physics).
4. Save results to `work_dirs/cpu_adaptation/results/` and plots to `work_dirs/cpu_adaptation/figures/`.

```bash
python code/wbench_cpu_adaptation.py
```

To regenerate synthetic cases (clearing existing ones):
```bash
python code/wbench_cpu_adaptation.py --regenerate
```

To process more cases (e.g., 50):
```bash
python code/wbench_cpu_adaptation.py --cases 50
```

## Output Artifacts
The following files are generated in `work_dirs/cpu_adaptation/`:
- `results/results.csv`: Summary table of scores.
- `results/results_full.json`: Detailed per-case metrics.
- `results/summary.json`: Aggregate statistics.
- `figures/score_distribution.png`: Histogram of total scores.
- `figures/nav_vs_nonnav.png`: Boxplot comparing navigation vs non-navigation cases.
