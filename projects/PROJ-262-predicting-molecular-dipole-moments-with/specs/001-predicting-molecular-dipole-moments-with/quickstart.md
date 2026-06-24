# Quickstart for Predicting Molecular Dipole Moments

This document describes the minimal commands required to run the end‑to‑end
pipeline on the synthetic dataset generated for the CI environment.

## Steps

1. **Generate synthetic processed data**

 ```bash
 python code/data/generate_processed_data.py
 ```

2. **Train the Graph Neural Network**

 ```bash
 python code/training/train_gnn.py
 ```

3. **Train the Random Forest baseline**

 ```bash
 python code/training/train_rf.py
 ```

4. **Evaluate models and produce metrics**

 ```bash
 python code/training/evaluate.py
 python code/generate_metrics.py
 ```

5. **Generate analysis visualisations**

 ```bash
 python code/analysis/generate_performance_plots.py
 python code/analysis/generate_significance.py
 ```

6. **Create the final summary report**

 ```bash
 python code/generate_summary.py
 ```

The commands above assume a fresh checkout and that the `requirements.txt`
have been installed (e.g. `pip install -r requirements.txt`). All
intermediate artefacts are written under the `data/` or `results/`
directories as described in the task list.