# Re-plan: the analysis could not be made to run — adjust the approach

The execution fix-loop exhausted EVERY model tier (the registered default plus escalations, last tier=0) without producing a clean, real run. Rather than escalate to a human, the pipeline is RE-PLANNING this project: re-derive the implementation approach using the evidence below so the new plan AVOIDS the failures that blocked the last one.

**Last execution summary**: 3 command(s) failed: python code/analysis/generate_performance_plots.py (rc=1); python code/analysis/generate_significance.py (rc=1); python code/generate_summary.py (rc=1)

## What worked (artifacts that WERE produced)

- `data/checkpoints/model_seed_0.pt.npy`
- `data/checkpoints/model_seed_1.pt.npy`
- `data/checkpoints/model_seed_2.pt.npy`
- `data/checkpoints/model_seed_3.pt.npy`
- `data/checkpoints/model_seed_4.pt.npy`
- `data/processed/features_2d.parquet`
- `data/processed/features_3d.parquet`
- `data/processed/molecules_10k.parquet`

## What failed (commands + error tails)

- python code/analysis/generate_performance_plots.py -> rc=1
     line 138, in generate_plots
    df = load_metrics(metrics_csv)
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 51, in load_metrics
    raise ValueError(f"Metrics CSV missing columns: {missing}")
ValueError: Metrics CSV missing columns: {'rmse', 'model', 'mae'}
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

## Required change

The implementation approach needs adjustment given the errors above — re-plan with a design that avoids them. Keep what worked; replace the parts of the method that produced the failures above with a CPU-tractable, dependency-light alternative that the free CI can run.

