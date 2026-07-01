# PlanBench-XL CPU Adaptation Quickstart

This adaptation reproduces the core quantitative result of the PlanBench-XL paper:
the degradation of planning accuracy under tool blocking, using a CPU-tractable
rule-based proxy agent.

## Prerequisites

- Python 3.8+
- `matplotlib` (optional, for plotting)

## Run Commands

Execute the following commands in order to generate the results:

```bash
python code/planbench_xl_cpu_adaptation.py
```

## Outputs

- `data/planbench_xl_results.csv`: Summary of accuracy across blocking scenarios.
- `data/planbench_xl_details.json`: Detailed results per scenario.
- `figures/planbench_xl_accuracy.png`: Bar chart of accuracy vs. blocking ratio.

## Notes

- This script uses a deterministic, rule-based agent to simulate the "planning"
  process, avoiding the need for external LLM APIs.
- It scales down the dataset to 20 tasks and 50 tools to ensure fast execution.
- The "blocking" mechanism is simulated by randomly disabling a fraction of tools.
