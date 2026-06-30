# Quickstart: MM-OCEAN CPU Adaptation

This guide runs the adapted evaluation on a CPU-only environment using a small subset of real data from the repository.

## Prerequisites
- Python 3.8+
- No external dependencies required (uses only standard library).

## Run Commands

Execute the following commands in order. Each command produces real artifacts in `data/`.

```bash
python code/simulate_mmocean.py
```

## Expected Outputs
After the script finishes, verify the following files exist in the `data/` directory:
- `data/results.json`: Contains the aggregated metrics (Accuracy, MAE, Prejudice Rate, etc.).
- `data/task3_mcq_accuracy.csv`: Detailed breakdown of MCQ performance by category.
- `data/summary.txt`: Human-readable summary of the findings.

The script simulates the "Prejudice Gap" described in the paper, demonstrating how a model can achieve correct ratings without proper grounding, even on real data samples.
