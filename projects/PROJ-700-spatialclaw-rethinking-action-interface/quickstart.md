# Quickstart: SpatialClaw CPU Adaptation

This guide runs the simplified, CPU-tractable version of the SpatialClaw evaluation.
It processes a small sample of the `erqa` benchmark to verify the pipeline and generate artifacts.

## Prerequisites
- Python 3.8+
- `pandas`, `matplotlib`

## Installation
```bash
pip install pandas matplotlib
```

## Run
Execute the adaptation script:
```bash
python code/spatial_claw_cpu_adapter.py --limit 5 --benchmark erqa
```

## Output
The script will generate:
- `data/results.csv`: Detailed results table.
- `data/results.json`: JSON formatted results.
- `figures/accuracy_bar.png`: Visualization of the accuracy metric.
