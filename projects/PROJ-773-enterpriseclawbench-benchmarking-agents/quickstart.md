# EnterpriseClawBench Adaptation - Quickstart

This script reproduces the core quantitative results of the EnterpriseClawBench paper (Skill Transfer, Role Performance, Cost Analysis) using a scaled-down, deterministic synthetic dataset and a mock agent.

## Prerequisites
- Python 3.8+
- `pip install pandas matplotlib`

## Run Command
Execute the adaptation script:

```bash
python code/enterprise_clawbench_adaptation.py
```

## Expected Outputs
After running, the following artifacts will be generated in `data/` and `figures/`:
- `data/synthetic_tasks.json`: The generated task set (50 tasks).
- `data/evaluation_results.csv`: Detailed per-task results (success, tokens, errors).
- `data/benchmark_summary.json`: Aggregated stats per role.
- `data/skill_transfer_matrix.csv`: Matrix for heatmap generation.
- `data/leaderboard.csv`: Role vs. Success Rate.
- `figures/skill_transfer_heatmap_all_roles.png`: Visualization of skill transfer.
- `figures/leaderboard_all_roles.png`: Visualization of role performance.

These artifacts demonstrate the evaluation protocol functioning correctly without requiring the proprietary data or live sandbox infrastructure.
