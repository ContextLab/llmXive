# Quickstart: AdaPlanBench Adaptation

This guide runs the scaled-down adaptive planning simulation.

## Prerequisites
- Python 3.8+
- No external dependencies required (uses only standard library).

## Run the Adaptation
Execute the following command to run the simulation and generate results:

```bash
python code/ada_plan_bench_adaptation.py
```

## Outputs
After execution, check the `data/` directory for:
- `adaplan_results.json`: Detailed JSON results including plans and constraints.
- `adaplan_results.csv`: A summary table of success rates and iterations.
- `summary.txt`: A text summary of the metrics.

The script simulates the core logic of the AdaPlanBench paper (progressive constraint revelation and re-planning) using a deterministic agent and a small sample of real household tasks.
