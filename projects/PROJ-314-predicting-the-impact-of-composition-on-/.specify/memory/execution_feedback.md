# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/run_pipeline_timing.py (rc=1); 6 declared deliverable(s) absent: data/reports/data_availability_report.json; data/results/baseline_metrics.json; data/results/feature_ranking_table.csv

## Failing / missing run-book commands

- python code/run_pipeline_timing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/run_pipeline_timing.py", line 12, in <module>
    from ingestion import main as run_ingestion
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/ingestion.py", line 11, in <module>
    from chemparse import Composition
ImportError: cannot import name 'Composition' from 'chemparse' (/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/.venv/lib/python3.11/site-packages/chemparse/__init__.py)

## Declared deliverables still missing

- data/reports/data_availability_report.json
- data/results/baseline_metrics.json
- data/results/feature_ranking_table.csv
- data/results/leakage_report.json
- data/results/shap_summary.png
- data/results/stability_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/reports/data_availability_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/scripts/run_gap_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/data_availability_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/feature_ranking_table.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/feature_ranking_table.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/leakage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_metrics_report.py` — NOT invoked by the run-book
    - `code/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/leakage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_summary.png` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/shap_summary.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
