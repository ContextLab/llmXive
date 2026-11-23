# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/loaders.py --output data/processed/ (rc=1); python code/main.py --permutations [variable] --threshold 0.3 --sweep (rc=1); python -m pytest tests/unit/ -v (rc=1)

## Failing / missing run-book commands

- python code/loaders.py --output data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 10, in <module>
    import openml
ModuleNotFoundError: No module named 'openml'

- python code/main.py --permutations [variable] --threshold 0.3 --sweep -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/main.py", line 12, in <module>
    import joblib
ModuleNotFoundError: No module named 'joblib'

- python -m pytest tests/unit/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/.venv/bin/python: No module named pytest

- python -m pytest tests/integration/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/.venv/bin/python: No module named pytest

