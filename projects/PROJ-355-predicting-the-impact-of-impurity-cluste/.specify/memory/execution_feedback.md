# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/train_model.py --input data/processed/training_set.csv --output results/metrics.json; 1 command(s) failed: python code/data/validate_potential.py (rc=1); 1 declared deliverable(s) absent: data/processed/potential_validation.json

## Failing / missing run-book commands

- python code/data/validate_potential.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-355-predicting-the-impact-of-impurity-cluste/code/data/validate_potential.py", line 25, in <module>
    from ase import Atoms
ModuleNotFoundError: No module named 'ase'

- python code/train_model.py --input data/processed/training_set.csv --output results/metrics.json -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-355-predicting-the-impact-of-impurity-cluste/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-355-predicting-the-impact-of-impurity-cluste/code/train_model.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/potential_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/potential_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_potential.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/potential_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
