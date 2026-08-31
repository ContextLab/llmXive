# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/preprocessing.py --input data/processed/merged_dataset.parquet --output data/processed/cleaned_dataset.parquet; python code/robustness.py --input data/processed/cleaned_dataset.parquet --output results/stats/sensitivity_analysis.csv; 3 command(s) failed: python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json (rc=1); python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet (rc=1); python code/modeling.py --input data/processed/cleaned_dataset.parquet --output results/stats/model_results.json --figs results/figures/ (rc=1); 3 declared deliverable(s) absent: data/processed/merged_dataset.parquet; data/raw/era5_full.h5; data/raw/era5_sample.h5

## Failing / missing run-book commands

- python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/validate_sources.py", line 6, in <module>
    import cdsapi
ModuleNotFoundError: No module named 'cdsapi'
- python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/ingestion.py", line 6, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/preprocessing.py --input data/processed/merged_dataset.parquet --output data/processed/cleaned_dataset.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/preprocessing.py': [Errno 2] No such file or directory
- python code/modeling.py --input data/processed/cleaned_dataset.parquet --output results/stats/model_results.json --figs results/figures/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/modeling.py", line 19, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/robustness.py --input data/processed/cleaned_dataset.parquet --output results/stats/sensitivity_analysis.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/robustness.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/merged_dataset.parquet
- data/raw/era5_full.h5
- data/raw/era5_sample.h5

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/derive_demographics.py` — NOT invoked by the run-book
    - `code/run_merge_era5_moral.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
    - `code/run_output_generation.py` — NOT invoked by the run-book
    - `code/modeling.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merged_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/era5_full.h5` is declared but was NOT written. Scripts referencing it:
    - `code/fetch_era5_full.py` — NOT invoked by the run-book
    - `code/run_fetch_era5_full.py` — NOT invoked by the run-book
    - `code/update_state_checksum_era5_full.py` — NOT invoked by the run-book
    - `code/run_merge_era5_moral.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/pre_ingestion_validation_gate.py` — NOT invoked by the run-book
    - `code/fetch_era_full.py` — NOT invoked by the run-book
    - `code/run_compute_checksum_sample.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/era5_full.h5` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/era5_sample.h5` is declared but was NOT written. Scripts referencing it:
    - `code/fetch_era_sample.py` — NOT invoked by the run-book
    - `code/validate_era5.py` — NOT invoked by the run-book
    - `code/fetch_era5.py` — NOT invoked by the run-book
    - `code/compute_checksum.py` — NOT invoked by the run-book
    - `code/run_compute_checksum_sample.py` — NOT invoked by the run-book
    - `code/aggregate_validation_results.py` — NOT invoked by the run-book
    - `code/fetch_era5_sample.py` — NOT invoked by the run-book
    - `code/update_state_checksum_sample.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/era5_sample.h5` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
