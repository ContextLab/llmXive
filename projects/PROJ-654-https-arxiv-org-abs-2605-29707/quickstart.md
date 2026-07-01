# Domino CPU Adaptation Quickstart

This guide runs the CPU-scaled adaptation of the **Domino** paper. It reproduces the core finding: **decoupling causal modeling from a parallel draft backbone improves draft quality** (measured here as next-token prediction accuracy on a small text sample).

## Prerequisites
- Python 3.9+
- `pip install datasets scikit-learn pandas matplotlib numpy tqdm`

## Run Command
Execute the following single command to run the full experiment:

```bash
python code/domino_cpu_demo.py
```

## Expected Output
1. **Console**: Logs showing the training of the "Parallel Backbone" and "Domino Head", followed by their accuracy scores.
2. **`data/results.csv`**: A CSV file containing the accuracy metrics for both methods.
3. **`figures/accuracy_comparison.png`**: A bar chart comparing the performance.

## Interpretation
- **Parallel Backbone**: Represents a drafter that ignores token order (fast but low quality).
- **Domino Head**: Represents the paper's innovation—a lightweight module that adds causal context to the parallel draft.
- **Result**: The Domino Head should show higher accuracy, validating the paper's claim that causal refinement is necessary even with parallel drafting.
