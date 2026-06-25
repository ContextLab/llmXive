# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/analysis/generate_performance_plots.py (rc=1); python code/analysis/generate_significance.py (rc=1); python code/generate_summary.py (rc=1)

## Failing / missing run-book commands

- python code/analysis/generate_performance_plots.py -> rc=1
     line 138, in generate_plots
    df = load_metrics(metrics_csv)
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 51, in load_metrics
    raise ValueError(f"Metrics CSV missing columns: {missing}")
ValueError: Metrics CSV missing columns: {'model', 'rmse', 'mae'}
- python code/analysis/generate_significance.py -> rc=1
    ric_data = _load_metrics(metrics_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_significance.py", line 54, in _load_metrics
    raise ValueError(f"Metrics CSV missing required columns: {missing}")
ValueError: Metrics CSV missing required columns: {'rmse', 'model', 'mae'}
- python code/generate_summary.py -> rc=1
    ary
    significance = load_csv_as_dicts(significance_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 25, in load_csv_as_dicts
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
FileNotFoundError: CSV file not found: results/significance.csv
