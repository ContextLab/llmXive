# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --stage discovery (rc=1); python code/main.py --stage preprocess (rc=1); python code/main.py --stage analysis (rc=1); 1 declared deliverable(s) absent: data/processed/variance_matrix.csv

## Failing / missing run-book commands

- python code/main.py --stage discovery -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/main.py", line 31, in <module>
    from analysis.correlation import run_correlation_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/analysis/__init__.py", line 5, in <module>
    from correlation import (
ModuleNotFoundError: No module named 'correlation'

- python code/main.py --stage preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/main.py", line 31, in <module>
    from analysis.correlation import run_correlation_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/analysis/__init__.py", line 5, in <module>
    from correlation import (
ModuleNotFoundError: No module named 'correlation'

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/main.py", line 31, in <module>
    from analysis.correlation import run_correlation_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/analysis/__init__.py", line 5, in <module>
    from correlation import (
ModuleNotFoundError: No module named 'correlation'

- python code/main.py --stage viz -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/main.py", line 31, in <module>
    from analysis.correlation import run_correlation_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-058-the-role-of-epigenetic-drift-in-adaptive/code/analysis/__init__.py", line 5, in <module>
    from correlation import (
ModuleNotFoundError: No module named 'correlation'


## Declared deliverables still missing

- data/processed/variance_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/variance_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/stressor_stratification.py` — NOT invoked by the run-book
    - `code/analysis/timescale_align.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/preprocess/filter_genes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/variance_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
