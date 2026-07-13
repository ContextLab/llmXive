# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/download_hcp.py (rc=1); python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/predictions.npy; data/raw/behavioral/hcp1200_behavioral_data.csv

## Failing / missing run-book commands

- python code/data/download_hcp.py -> rc=1
    Error: log_stage_start() missing 1 required positional argument: 'stage_name'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/main.py", line 20, in <module>
    from data.preprocess import main as preprocess_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/data/preprocess.py", line 13, in <module>
    from nilearn.input_data import NiftiLabelsMasker
ModuleNotFoundError: No module named 'nilearn.input_data'

## Declared deliverables still missing

- data/processed/predictions.npy
- data/raw/behavioral/hcp1200_behavioral_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/predictions.npy` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/modeling/pipeline_factory.py` — NOT invoked by the run-book
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
    - `code/modeling/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/predictions.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/behavioral/hcp1200_behavioral_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_hcp.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/behavioral/hcp1200_behavioral_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
