# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/imputed_data.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
ated-exposure-to-neutr/code/data_fetcher.py", line 92, in fetch_project_implicit_political_data
    response.raise_for_status()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-469-the-impact-of-repeated-exposure-to-neutr/code/.venv/lib/python3.11/site-packages/requests/models.py", line 1167, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 500 Server Error: Internal Server Error for url: https://osf.io/download/4z9qg/

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-469-the-impact-of-repeated-exposure-to-neutr/code/main.py", line 91, in main
    data_path = fetch_project_implicit_political_data()
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-469-the-impact-of-repeated-exposure-to-neutr/code/data_fetcher.py", line 123, in fetch_project_implicit_political_data
    raise ValueError(error_msg) from e
ValueError: Real data source not found or inaccessible. URL: https://osf.io/download/4z9qg/, Status: 500. Aborting to prevent synthetic data fallback.



## Declared deliverables still missing

- data/processed/imputed_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/imputed_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/binary_model.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/imputed_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
