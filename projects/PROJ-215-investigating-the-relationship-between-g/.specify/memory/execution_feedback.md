# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data_ingestion.py --check-only (rc=1); python code/data_ingestion.py --output data/processed/merged_clean.parquet (rc=1); python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet (rc=1); 7 declared deliverable(s) absent: data/interim/unadjusted_alpha_pvals.csv; data/interim/unadjusted_taxa_pvals.csv; data/processed/association_results.csv

## Failing / missing run-book commands

- python code/data_ingestion.py --check-only -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/data_ingestion.py", line 5, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/data_ingestion.py --output data/processed/merged_clean.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/data_ingestion.py", line 5, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/preprocessing.py", line 3, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis.py --input data/processed/diversity_metrics.parquet --output data/results/associations.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/analysis.py", line 3, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/visualization.py --input data/results/associations.csv --output docs/figures/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/visualization.py", line 3, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/report.py --input data/results/associations.csv --output docs/report.md -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/report.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/interim/unadjusted_alpha_pvals.csv
- data/interim/unadjusted_taxa_pvals.csv
- data/processed/association_results.csv
- data/processed/bray_curtis.npz
- data/processed/cleaned_dataset.csv
- data/processed/ks_test_results.json
- data/processed/validation_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/unadjusted_alpha_pvals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_covariate_adjustment.py` — NOT invoked by the run-book
    - `code/output_association_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/unadjusted_alpha_pvals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/unadjusted_taxa_pvals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_covariate_adjustment.py` — NOT invoked by the run-book
    - `code/output_association_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/unadjusted_taxa_pvals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/association_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_covariate_adjustment.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/check_ks_pvalue.py` — NOT invoked by the run-book
    - `code/output_association_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/association_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bray_curtis.npz` is declared but was NOT written. Scripts referencing it:
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bray_curtis.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ks_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ks_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/reference_validator.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/run_reference_validator.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_validation_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
