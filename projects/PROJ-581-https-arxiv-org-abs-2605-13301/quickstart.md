# Quick Start: SU-01 CPU Adaptation

This guide runs the CPU-tractable simulation of the SU-01 paper's core result (Test-Time Scaling) on a 2-core, 7GB RAM environment.

## Prerequisites
- Python 3.8+
- `matplotlib` (optional, for plotting)

## Run Commands

```bash
# 1. Install minimal dependencies (if not present)
pip install matplotlib --quiet

# 2. Run the simulation
python code/run_simulation.py
```

The script will generate:
- `data/pass_at_k_results.json` (JSON)
- `data/verification_log.csv` (CSV)
- `figures/pass_at_k_curve.png` (PNG)
