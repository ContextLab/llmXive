# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/ (rc=1)

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-092-statistical-analysis-of-feature-importan/code/main.py", line 39, in <module>
    window_data: pd.DataFrame,
                 ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-092-statistical-analysis-of-feature-importan/code/.venv/bin/python: No module named pytest

