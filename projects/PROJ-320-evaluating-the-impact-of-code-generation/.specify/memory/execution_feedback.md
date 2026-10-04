# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/data/fetch_github.py --output data/raw/prs_raw.json (rc=1); python code/data/classify_prs.py --input data/raw/prs_raw.json --output data/processed/prs_labeled.csv (rc=1); python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv (rc=1); 9 declared deliverable(s) absent: data/audit/error_rate.json; data/processed/complexity_scores.csv; data/processed/gate_status.json

## Failing / missing run-book commands

- python code/data/fetch_github.py --output data/raw/prs_raw.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/data/fetch_github.py", line 7, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/data/classify_prs.py --input data/raw/prs_raw.json --output data/processed/prs_labeled.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/data/classify_prs.py", line 15, in <module>
    from utils.seeds import set_global_seed, get_seed_manager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/utils/seeds.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv -> rc=1
    2026-10-04 17:43:04,125 - __main__ - INFO - Starting PR metrics extraction pipeline (T022)
2026-10-04 17:43:04,125 - __main__ - INFO - Loading labeled PRs from /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_prs_labeled
2026-10-04 17:43:04,125 - __main__ - ERROR - Input file error: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_prs_labeled. Ensure T017 (save_labeled_dataset) has completed successfully.
2026-10-04 17:43:04,125 - __main__ - ERROR - Pipeline failed
- python code/analysis/statistical_tests.py --input data/processed/prs_metrics.csv --output reports/results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 10, in <module>
    from scipy import stats as scipy_stats
ModuleNotFoundError: No module named 'scipy'
- python code/analysis/visualizations.py --input data/processed/prs_metrics.csv --output reports/figures/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/visualizations.py", line 13, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/analysis/sensitivity_analysis.py --input data/processed/prs_metrics.csv --output reports/sensitivity_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/sensitivity_analysis.py", line 20, in <module>
    from analysis.statistical_tests import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 10, in <module>
    from scipy import stats as scipy_stats
ModuleNotFoundError: No module named 'scipy'
- python code/audit/manual_validation.py --input data/processed/prs_metrics.csv --output data/processed/audit_log.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/audit/manual_validation.py", line 24, in <module>
    from utils.seeds import set_global_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/utils/seeds.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/audit/error_rate.json
- data/processed/complexity_scores.csv
- data/processed/gate_status.json
- data/processed/prs_labeled.csv
- data/processed/prs_metrics.csv
- data/processed/results.json
- figures/boxplots.pdf
- figures/final_report.pdf
- figures/histograms.pdf

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/audit/error_rate.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/audit/error_rate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/complexity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/complexity.py` — NOT invoked by the run-book
    - `code/analysis/save_complexity_scores.py` — NOT invoked by the run-book
    - `code/analysis/optimize_complexity_processing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/complexity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gate_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gate_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prs_labeled.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/save_labeled_dataset.py` — NOT invoked by the run-book
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/complexity.py` — NOT invoked by the run-book
    - `code/analysis/save_complexity_scores.py` — NOT invoked by the run-book
    - `code/analysis/optimize_complexity_processing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prs_labeled.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prs_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/data/save_metrics.py` — NOT invoked by the run-book
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/prs_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/batch_processor.py` — NOT invoked by the run-book
    - `code/data/save_labeled_dataset.py` — NOT invoked by the run-book
    - `code/data/classify_prs.py` — IS a run-book command
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/complexity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `figures/boxplots.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/visualizations.py` — IS a run-book command
  Make ONE of these WRITE `figures/boxplots.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `figures/final_report.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/final_report.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `figures/histograms.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/visualizations.py` — IS a run-book command
  Make ONE of these WRITE `figures/histograms.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
