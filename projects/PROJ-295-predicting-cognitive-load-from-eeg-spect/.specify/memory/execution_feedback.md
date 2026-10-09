# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/data/download.py (rc=1); python code/main.py (rc=1); python -m pytest tests/ -v (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
Starting dataset download for ds000246
Data directory: data/raw

ERROR: datalad is not installed. Please install it via: pip install datalad

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-295-predicting-cognitive-load-from-eeg-spect/code/main.py", line 23, in <module>
    from utils.runtime_profiler import check_and_halt
ModuleNotFoundError: No module named 'utils.runtime_profiler'

- python -m pytest tests/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-295-predicting-cognitive-load-from-eeg-spect/code/.venv/bin/python: No module named pytest

