# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json; python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/; 2 command(s) failed: python code/data_loader.py --download (rc=1); python code/descriptors.py --input data/raw/combined_smiles.csv --output data/processed/descriptors.csv (rc=1); 6 declared deliverable(s) absent: data/processed/analysis_summary.json; data/processed/corr_plot_top5.png; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/data_loader.py", line 2, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/descriptors.py --input data/raw/combined_smiles.csv --output data/processed/descriptors.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/descriptors.py", line 3, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/model_training.py': [Errno 2] No such file or directory
- python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/analysis.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/analysis_summary.json
- data/processed/corr_plot_top5.png
- data/processed/descriptors.csv
- data/processed/feature_importance.csv
- data/processed/model_results.json
- data/processed/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/corr_plot_top5.png` is declared but was NOT written. Scripts referencing it:
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corr_plot_top5.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_cross_validation.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/descriptors.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
    - `code/correlation_analysis.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
