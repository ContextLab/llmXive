# Domino Adaptation Quickstart

This guide runs the scaled-down CPU adaptation of the Domino paper.
It reproduces the core finding: **Decoupling causal modeling (Domino Head) improves draft acceptance rates** compared to a naive parallel baseline.

## Prerequisites
- Python 3.8+
- `pip install torch transformers datasets matplotlib pandas tqdm rich`

## Run Commands
Execute the following commands in order:

```bash
python code/run_domino_analysis.py
```

This script will:
1. Load a small subset of real text (WikiText-2 or snippets).
2. Initialize a tiny target model (DistilGPT2) and draft simulators.
3. Simulate Parallel vs. Domino drafting and verification.
4. Output `data/acceptance_rates.csv`, `data/summary.json`, and `figures/acceptance_comparison.png`.
