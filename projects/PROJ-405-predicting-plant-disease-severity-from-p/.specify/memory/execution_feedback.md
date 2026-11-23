# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --mode full (rc=1); python code/main.py --mode dry-run --limit 50 (rc=1); python code/main.py --stage extract_features (rc=1); 1 declared deliverable(s) absent: data/processed/unified_analysis.csv

## Failing / missing run-book commands

- python code/main.py --mode full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/main.py", line 11, in <module>
    from config import get_path, ensure_dirs, MAX_MEMORY_GB, MAX_RUNTIME_HOURS
ImportError: cannot import name 'MAX_MEMORY_GB' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/config.py)

- python code/main.py --mode dry-run --limit 50 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/main.py", line 11, in <module>
    from config import get_path, ensure_dirs, MAX_MEMORY_GB, MAX_RUNTIME_HOURS
ImportError: cannot import name 'MAX_MEMORY_GB' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/config.py)

- python code/main.py --stage extract_features -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/main.py", line 11, in <module>
    from config import get_path, ensure_dirs, MAX_MEMORY_GB, MAX_RUNTIME_HOURS
ImportError: cannot import name 'MAX_MEMORY_GB' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/config.py)


## Declared deliverables still missing

- data/processed/unified_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/unified_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/utils/validity_check.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
