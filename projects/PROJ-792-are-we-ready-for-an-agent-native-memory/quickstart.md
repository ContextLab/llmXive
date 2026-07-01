# Quickstart: Agent Memory System Evaluation (Adapted)

This run-book executes the adapted evaluation of the paper "Are We Ready For An Agent-Native Memory System?". It reproduces the core analytical framework (4 modules) and compares memory strategies on a CPU-tractable scale using real data samples.

## Prerequisites
- Python 3.8+
- `matplotlib`, `numpy`
- (Optional) `datasets` (for loading real HotpotQA data; if missing, a structured generator is used)

## Installation
```bash
pip install matplotlib numpy datasets
```

## Execution
Run the simulation script. It will generate `data/metrics.csv` and `figures/ablation.png`.

```bash
python code/simulate_memory_evaluation.py
```

## Verification
After execution, verify the outputs:
1. Check `data/metrics.csv` for precision and cost metrics.
2. Open `figures/ablation.png` to see the trade-off visualization.
