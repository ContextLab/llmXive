# Quickstart: EfficientRollout Scaled-Down Adaptation

This guide runs the analytical model to reproduce the paper's core "Toggle Boundary" result on a CPU.

## Prerequisites
- Python 3.9+
- `numpy`, `matplotlib` (standard scientific stack)

## Run Commands
Execute the following commands in order:

```bash
python code/run_efficientrollout_demo.py
```

## Expected Outputs
After running, the following artifacts will be generated:
- `data/toggle_decision_sweep.csv`: A table of theoretical speedups for various batch/sequence sizes.
- `figures/toggle_boundary.png`: A visualization of the decision boundary where Speculative Decoding becomes beneficial.

The script will print a summary indicating the percentage of configurations where SD is beneficial and the maximum theoretical speedup, reproducing the paper's claim of ~19.6% latency reduction in optimal regimes.
