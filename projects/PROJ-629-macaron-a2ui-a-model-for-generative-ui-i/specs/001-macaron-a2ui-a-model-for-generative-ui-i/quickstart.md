# Macaron-A2UI CPU-Scale Evaluation Run Book

This run book executes a **scaled-down, CPU-tractable evaluation** of the Macaron-A2UI paper's core quantitative result (L1/L2/L3 scoring) using a rule-based proxy instead of the original 30B+ GPU models.

## Prerequisites
- Python 3.9+
- `matplotlib` (optional, for plotting)

## Install Dependencies
```bash
pip install matplotlib
```

## Execute
Run the evaluation script:
```bash
python code/run_eval_proxy.py
```

## Expected Artifacts
The script will generate the following files in `data/` and `figures/`:
- `data/l1_scores.json`: Detailed L1 pass/fail metrics per task.
- `data/l2_scores.json`: Detailed L2 component metrics per task.
- `data/l3_scores.json`: Detailed L3 utility metrics per task.
- `data/summary.csv`: Aggregated scores by dataset source.
- `figures/score_distribution.png`: Visualization of scores.

## Notes
- This script **does not** call external APIs or require a GPU.
- It uses **pre-cached sample outputs** to simulate model behavior, allowing the evaluation logic to be tested on a small CPU instance.
- The scores are **proxy scores** based on deterministic rules, not the exact LLM-judged scores from the paper, but they demonstrate the evaluation pipeline's correctness.
