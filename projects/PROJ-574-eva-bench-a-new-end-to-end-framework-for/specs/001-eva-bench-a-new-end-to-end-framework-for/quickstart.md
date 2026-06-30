# EVA-Bench Adapter Quickstart

This guide runs the CPU-tractable adaptation of the EVA-Bench framework.
It generates synthetic conversations, evaluates them against proxy metrics, and produces artifacts.

**Prerequisites**: Python 3.8+, `numpy`, `matplotlib`.
```bash
pip install numpy matplotlib
```

**Run the adaptation**:
```bash
python code/eva_bench_adapter.py
```

**Expected Outputs**:
- `data/simulated_conversations.json`: Raw synthetic dialogue data.
- `data/evaluation_results.csv`: Per-scenario scores for 3 proxy systems.
- `data/aggregated_metrics.json`: Mean scores and robustness gaps.
- `figures/eva_performance.png`: Scatter plot of EVA-A vs EVA-X.
- `figures/robustness_gap.png`: Bar chart of noise impact.
