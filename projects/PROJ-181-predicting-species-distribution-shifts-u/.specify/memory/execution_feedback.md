# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python code/main.py download; python code/main.py preprocess; python code/main.py train

## Failing / missing run-book commands

- python code/main.py download -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py preprocess -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py train -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py evaluate -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py report -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

