# Quickstart: Claw-SWE-Bench CPU Adaptation

This guide runs the adapted benchmark on a CPU-only environment.

## Prerequisites
- Python 3.8+
- `datasets` library (optional, script falls back to embedded data if missing)

## Run Commands

```bash
python code/simulate_benchmark.py
```

## Expected Outputs
After running, check the `data/` and `figures/` directories:
- `data/adapter_results.csv`: Summary of Pass@1 scores for minimal vs. full adapter.
- `data/run_details.json`: Detailed per-instance results.
- `figures/performance_comparison.txt`: Text-based visualization of the results.

The script simulates the paper's finding that a "Full Adapter" significantly outperforms a "Minimal Adapter" (e.g., ~73% vs ~19% in the full benchmark, here simulated with a smaller gap on 10 instances).
