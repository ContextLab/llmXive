# SpatialBench CPU Adaptation - Quick Start

This guide runs the simplified SpatialBench adaptation on CPU.

## Prerequisites
```bash
pip install torch numpy matplotlib scipy
```

## Run Commands
Execute the following commands in order:

```bash
python code/adapter.py
```

## Expected Outputs
After running, you should see:
- `data/results.csv` - Performance metrics per domain
- `data/synthetic_dataset.json` - Dataset metadata
- `figures/comparison.png` - Visualization of results

The script will print progress updates and final metrics to the console.

<!-- FILE: code/adapter.py -->
