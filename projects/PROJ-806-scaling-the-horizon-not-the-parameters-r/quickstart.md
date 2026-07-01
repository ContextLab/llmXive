# Quickstart: Agents-A1 Horizon Scaling Adaptation

This run-book reproduces the core finding of "Scaling the Horizon, Not the Parameters" using a CPU-safe proxy. It validates that longer agent horizons lead to higher success rates on complex tasks.

## Prerequisites
- Python 3.8+
- `matplotlib` (for plotting)

## Steps

1. **Install Dependencies**
   ```bash
   pip install matplotlib
   ```

2. **Run the Adaptation Script**
   This script loads real questions from the `evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/` directory (or uses a fallback if the path is different) and runs a simulated agent with varying horizon limits.
   ```bash
   python code/horizon_scaling_demo.py
   ```

3. **Verify Outputs**
   Check the generated artifacts in the `data/` and `figures/` directories:
   - `data/horizon_scaling_results.json`: Detailed metrics for each run.
   - `figures/horizon_scaling_plot.png`: A chart showing success rate increasing with horizon length.

## Expected Output
The script will print a summary of success rates for short (5 steps), medium (15 steps), and long (45 steps) horizons. You should see that the success rate increases as the horizon limit increases, confirming the paper's hypothesis in a scaled-down, reproducible manner.
