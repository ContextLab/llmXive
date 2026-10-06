# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/01_data_ingestion.py; 4 command(s) failed: python code/02_preprocessing.py (rc=1); python code/02_preprocessing.py --power-analysis (rc=1); python code/03_model_training.py (rc=1); 2 declared deliverable(s) absent: data/logs/missing_value_report.json; data/raw/seabass.csv

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/01_data_ingestion.py': [Errno 2] No such file or directory
- python code/02_preprocessing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/02_preprocessing.py", line 12, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'
- python code/02_preprocessing.py --power-analysis -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/02_preprocessing.py", line 12, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'
- python code/03_model_training.py -> rc=1
    WARNING:root:PyTorch or Transformers not installed. VLM training will fallback to RF as per spec.
ERROR:__main__:Model training failed: Aligned data not found at data/processed/aligned_dataset.nc
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/03_model_training.py", line 263, in main
    data = load_aligned_data(data_path)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/03_model_training.py", line 68, in load_aligned_data
    raise FileNotFoundError(f"Aligned data not found at {path}")
FileNotFoundError: Aligned data not found at data/processed/aligned_dataset.nc
- python code/04_evaluation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/04_evaluation.py", line 10, in <module>
    from statsmodels.stats.outliers_influence import variance_inflation_factor
ModuleNotFoundError: No module named 'statsmodels'

## Declared deliverables still missing

- data/logs/missing_value_report.json
- data/raw/seabass.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/missing_value_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/logs/missing_value_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/seabass.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing.py` — IS a run-book command
    - `code/01_fetch_seabass.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/seabass.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
