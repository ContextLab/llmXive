# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/simulation_runner.py (rc=1); python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 (rc=1); 3 declared deliverable(s) absent: data/derived/baseline_results.csv; data/derived/final_report.csv; data/derived/robustResults.csv

## Failing / missing run-book commands

- python code/simulation_runner.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/simulation_runner.py", line 10, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/simulation_runner.py", line 10, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/derived/baseline_results.csv
- data/derived/final_report.csv
- data/derived/robustResults.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/run_simulation_baseline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/final_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/final_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/robustResults.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/run_simulation_robust.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/robustResults.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
