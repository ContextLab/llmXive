# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/imputed_data.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    05:37:27 - root - [32mINFO[0m - Logging initialized. File: logs/pipeline.log

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-469-the-impact-of-repeated-exposure-to-neutr/code/main.py", line 19, in <module>
    from binary_model import run_binary_model_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-469-the-impact-of-repeated-exposure-to-neutr/code/binary_model.py", line 13, in <module>
    def fit_binary_model(data: pd.DataFrame) -> sm.OLSResults:
                                                ^^^^^^^^^^^^^
AttributeError: module 'statsmodels.api' has no attribute 'OLSResults'

## Declared deliverables still missing

- data/processed/imputed_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/imputed_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/binary_model.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/imputed_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
