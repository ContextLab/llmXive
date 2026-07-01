# Role-Agent Adaptation Run-Book

This script simulates the core WIA/AIW mechanisms of the Role-Agent paper using a text-based grid world. It requires no GPU and no external datasets.

## Prerequisites
- Python 3.8+
- `matplotlib`, `numpy` (standard pip install)

## Run Commands
Execute the following in order:

```bash
python code/simulate_role_agent.py
```

## Expected Outputs
After execution, the following files will be generated:
- `data/baseline_results.csv`: Performance logs for the baseline agent.
- `data/role_agent_results.csv`: Performance logs for the Role-Agent (WIA+AIW).
- `data/log.json`: Summary metrics including the calculated improvement percentage.
- `figures/comparison.png`: A bar chart visualizing the success rate improvement.

## Verification
Check `data/log.json` to confirm the "improvement_percent" value. The paper claims >4% improvement; this simulation should demonstrate a positive gain (often higher due to the controlled environment) by utilizing the `text_similarity_ratio` for state prediction alignment.
