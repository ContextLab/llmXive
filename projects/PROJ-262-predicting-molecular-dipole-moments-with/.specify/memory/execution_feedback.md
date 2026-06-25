# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/training/train_rf.py (rc=1); python code/analysis/generate_performance_plots.py (rc=1); python code/analysis/generate_significance.py (rc=1)

## Failing / missing run-book commands

- python code/training/train_rf.py -> rc=1
    ts-with/code/training/train_rf.py", line 40, in <module>
    from training.save_checkpoints import save_rf_checkpoint
ImportError: cannot import name 'save_rf_checkpoint' from partially initialized module 'training.save_checkpoints' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/save_checkpoints.py)
- python code/analysis/generate_performance_plots.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 28, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'
- python code/analysis/generate_significance.py -> rc=1
    ric_data = _load_metrics(metrics_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_significance.py", line 54, in _load_metrics
    raise ValueError(f"Metrics CSV missing required columns: {missing}")
ValueError: Metrics CSV missing required columns: {'mae', 'model', 'rmse'}
- python code/generate_summary.py -> rc=1
    ary
    significance = load_csv_as_dicts(significance_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 25, in load_csv_as_dicts
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
FileNotFoundError: CSV file not found: results/significance.csv

## Files your producers ACTUALLY wrote — reconcile consumers against THESE

A `missing columns` / `KeyError` / `FileNotFoundError: <file>` failure above is a cross-file DATA-contract mismatch: a consumer expects column names or a path the UPSTREAM producer did not write. The traceback shows only what the consumer EXPECTS — here is what actually landed on disk. Make the PRODUCER write the exact column names / path the consumers need (or make the consumers read these actual names). Fix the ROOT producer first: a script failing on a missing INPUT file is a CASCADE that clears once its producer is fixed — do not edit the cascade victim in isolation.

- `data/checkpoints/model_seed_0.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_1.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_2.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_3.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_4.pt.npy` (144 bytes)
- `data/checkpoints/rf_metrics.csv` — actual CSV header: `model,seed,mae,rmse`
- `data/checkpoints/rf_seed_0.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_1.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_2.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_3.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_4.pkl` (337617 bytes)
- `data/processed/features_2d.parquet` (330751 bytes)
- `data/processed/features_3d.parquet` (3816421 bytes)
- `data/processed/molecules_10k.parquet` (629397 bytes)
- `results/metrics.csv` — actual CSV header: `seed,model_type,MAE,RMSE`
