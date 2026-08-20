# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 declared deliverable(s) absent: data/confounds.csv; data/descriptors_dft.csv; data/descriptors_semi.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/confounds.csv
- data/descriptors_dft.csv
- data/descriptors_semi.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/confounds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/confound_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/confounds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_dft.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/evaluate_models.py` — NOT invoked by the run-book
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/dft_calculator.py` — NOT invoked by the run-book
    - `code/validate_subset_alignment.py` — NOT invoked by the run-book
    - `code/track_compute_resources.py` — NOT invoked by the run-book
    - `code/evaluators/missing_dof_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_dft.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_semi.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/physical_validator.py` — NOT invoked by the run-book
    - `code/evaluate_models.py` — NOT invoked by the run-book
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/noise_injection.py` — NOT invoked by the run-book
    - `code/validate_subset_alignment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_semi.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
