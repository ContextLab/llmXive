# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --mode full --seed 42 (rc=1); python code/main.py --mode dry-run --seed 42 (rc=1); python code/main.py --validate-contracts (rc=1); 2 declared deliverable(s) absent: data/raw/cochrane_base.csv; data/results/reml_failures.json

## Failing / missing run-book commands

- python code/main.py --mode full --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/main.py", line 35, in <module>
    from analysis.metrics import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/analysis/__init__.py", line 26, in <module>
    from .estimators import (
ModuleNotFoundError: No module named 'analysis.estimators'

- python code/main.py --mode dry-run --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/main.py", line 35, in <module>
    from analysis.metrics import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/analysis/__init__.py", line 26, in <module>
    from .estimators import (
ModuleNotFoundError: No module named 'analysis.estimators'

- python code/main.py --validate-contracts -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/main.py", line 35, in <module>
    from analysis.metrics import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/analysis/__init__.py", line 26, in <module>
    from .estimators import (
ModuleNotFoundError: No module named 'analysis.estimators'

- python -m pytest tests/unit/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/raw/cochrane_base.csv
- data/results/reml_failures.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/cochrane_base.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config_loader.py` — NOT invoked by the run-book
    - `code/fetch_cochrane_data.py` — NOT invoked by the run-book
    - `code/generate_synthetic_base.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/adapt_parameters.py` — NOT invoked by the run-book
    - `code/scripts/fetch_cochrane.py` — NOT invoked by the run-book
    - `code/scripts/generate_synthetic_base.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/cochrane_base.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/reml_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/simulation/estimators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/reml_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
