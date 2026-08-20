# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 command(s) failed: python code/download.py --output data/raw (rc=1); python code/retrieval.py --input data/raw --output data/processed (rc=1); python code/analysis.py --input data/processed/analysis_dataset.csv --output results (rc=1); 6 declared deliverable(s) absent: data/processed/analysis_results.json; data/processed/bootstrap_ci.json; data/processed/correlation_stats.json

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/main.py': [Errno 2] No such file or directory
- python code/download.py --output data/raw -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 5, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/retrieval.py --input data/raw --output data/processed -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 6, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis.py --input data/processed/analysis_dataset.csv --output results -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/analysis.py", line 3, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/analysis_results.json
- data/processed/bootstrap_ci.json
- data/processed/correlation_stats.json
- data/processed/metadata.csv
- data/processed/regression_results.json
- data/processed/retrieval_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bootstrap_ci.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bootstrap_ci.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/correlation_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/retrieval.py` — IS a run-book command
    - `code/plots_noise_signal.py` — NOT invoked by the run-book
    - `code/api_config.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/plots.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/aggregate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/regression_stats.py` — NOT invoked by the run-book
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/analysis_tobit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/retrieval_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/plots_noise_signal.py` — NOT invoked by the run-book
    - `code/mdc_stats.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/retrieval_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/retrieval_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
