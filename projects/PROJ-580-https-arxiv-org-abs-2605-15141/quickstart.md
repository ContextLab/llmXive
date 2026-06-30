# Quickstart: Causal Forcing++ CPU Adaptation

This guide runs the simplified reproduction of the Causal Forcing++ paper.
It generates synthetic data, runs a 48-step teacher and a 2-step student,
and compares the results to demonstrate the "Causal Forcing" benefit.

## Prerequisites
- Python 3.8+
- `pip install torch numpy pandas matplotlib`

## Run Commands
Execute the following commands in order:

```bash
python code/simulate_causal_forcing.py
```

## Expected Outputs
After running, the following files will be generated:
- `data/results.csv`: Quantitative comparison of MSE errors.
- `data/teacher_trajectory.csv`: The 48-step reference path.
- `data/student_trajectory.csv`: The 2-step student paths.
- `figures/flow_comparison.png`: A plot visualizing the trajectory alignment.

The script will print the improvement percentage, demonstrating that the
"Causal" initialization (our proxy for the paper's method) significantly
reduces the trajectory error compared to a naive start.
