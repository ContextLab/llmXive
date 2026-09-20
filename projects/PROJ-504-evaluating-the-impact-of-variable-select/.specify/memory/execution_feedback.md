# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --mode simulate; python code/main.py --mode analyze; python code/main.py --mode paper; 1 command(s) failed: python code/data/downloader.py (rc=1); 1 declared deliverable(s) absent: data/processed/simulation_results.csv

## Failing / missing run-book commands

- python code/data/downloader.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/data/downloader.py", line 18, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/main.py --mode simulate -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/main.py': [Errno 2] No such file or directory
- python code/main.py --mode analyze -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/main.py': [Errno 2] No such file or directory
- python code/main.py --mode paper -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/main.py': [Errno 2] No such file or directory
- python code/verify.py --check-memory --check-runtime -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/verify.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/simulation_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/simulation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
