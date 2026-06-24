# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/data/generate_processed_data.py (rc=1); python code/training/train_gnn.py (rc=1); python code/training/train_rf.py (rc=1); 1 declared deliverable(s) absent: data/processed/molecules_10k.parquet

## Failing / missing run-book commands

- python code/data/generate_processed_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/generate_processed_data.py", line 27, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/training/train_gnn.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_gnn.py", line 33, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/training/train_rf.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py", line 25, in <module>
    import joblib
ModuleNotFoundError: No module named 'joblib'
- python code/training/evaluate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py", line 11, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/generate_performance_plots.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 28, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'
- python code/analysis/generate_significance.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_significance.py", line 27, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/generate_summary.py -> rc=1
    ary
    significance = load_csv_as_dicts(significance_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 25, in load_csv_as_dicts
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
FileNotFoundError: CSV file not found: results/significance.csv

## Declared deliverables still missing

- data/processed/molecules_10k.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/molecules_10k.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/generate_processed_data.py` — IS a run-book command
    - `code/training/train_gnn.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/molecules_10k.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
