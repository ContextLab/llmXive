# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 5 declared deliverable(s) absent: data/analysis/centrality_metrics.csv; data/analysis/diagnostics.json; data/analysis/qc_log.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
rali/code/main.py", line 21, in <module>
    from code.main_us2 import run_us2_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-299-assessing-the-impact-of-network-centrali/code/main_us2.py", line 20, in <module>
    from code.analysis.regression import run_regression_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-299-assessing-the-impact-of-network-centrali/code/analysis/regression.py", line 18, in <module>
    import statsmodels.api as sm
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/api.py", line 76, in <module>
    from . import datasets, distributions, iolib, regression, robust, tools
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/distributions/__init__.py", line 7, in <module>
    from .discrete import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/distributions/discrete.py", line 5, in <module>
    from scipy._lib._util import _lazywhere
ImportError: cannot import name '_lazywhere' from 'scipy._lib._util' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-299-assessing-the-impact-of-network-centrali/lib/python3.11/site-packages/scipy/_lib/_util.py)


## Declared deliverables still missing

- data/analysis/centrality_metrics.csv
- data/analysis/diagnostics.json
- data/analysis/qc_log.json
- data/analysis/regression_results.csv
- data/raw/participant_list.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/centrality_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/data_merger.py` — NOT invoked by the run-book
    - `code/centrality/metrics.py` — NOT invoked by the run-book
    - `code/data_models.py` — NOT invoked by the run-book
    - `code/main_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/centrality_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/diagnostics.py` — NOT invoked by the run-book
    - `code/main_us2.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/qc_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/qc_validator.py` — NOT invoked by the run-book
    - `code/centrality/connectivity.py` — NOT invoked by the run-book
    - `code/centrality/metrics.py` — NOT invoked by the run-book
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/preprocess/fMRI_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/qc_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/regression_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/diagnostics.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/main_us2.py` — NOT invoked by the run-book
    - `code/viz/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/regression_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participant_list.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download/adni_downloader.py` — NOT invoked by the run-book
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/preprocess/fMRI_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/participant_list.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
