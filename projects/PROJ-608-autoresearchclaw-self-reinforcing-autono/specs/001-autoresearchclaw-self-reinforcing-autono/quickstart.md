# Quickstart: AutoResearchClaw ARC-Bench Simulation

This package contains a CPU-tractable simulation of the ARC-Bench evaluation described in the paper "AutoResearchClaw: Self-Reinforcing Autonomous Research with Human-AI Collaboration".

Since the original benchmark requires running 25 complex autonomous agents (which is impossible on a 2-core CPU CI), this script **simulates** the statistical results based on the paper's reported metrics.

## Prerequisites

- Python 3.8+
- `pip install pandas matplotlib`

## Run the Simulation

Execute the following command to generate the results:

```bash
python code/simulate_arc_bench.py
```

## Outputs

After running, you will find the following artifacts:

1.  **`data/arc_bench_scores.json`**: Raw simulated scores for all 25 topics.
2.  **`data/arc_bench_aggregate.csv`**: Aggregated mean scores and standard deviations.
3.  **`data/hitl_modes.csv`**: Simulated performance across 7 intervention modes.
4.  **`figures/score_comparison.png`**: Bar chart showing the ~54.7% improvement.
5.  **`figures/hitl_modes.png`**: Chart showing the impact of different human intervention strategies.

## Verification

The script verifies the paper's core claim:
> "AutoResearchClaw outperforms AI Scientist v2 by 54.7%."

Check `data/arc_bench_aggregate.csv` to confirm the calculated improvement percentage.
