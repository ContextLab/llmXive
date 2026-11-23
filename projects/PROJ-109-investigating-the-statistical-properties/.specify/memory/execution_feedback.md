# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --mode generate; python code/main.py --mode compute; python code/main.py --mode analyze

## Failing / missing run-book commands

- python code/main.py --mode generate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-109-investigating-the-statistical-properties/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-109-investigating-the-statistical-properties/code/main.py': [Errno 2] No such file or directory

- python code/main.py --mode compute -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-109-investigating-the-statistical-properties/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-109-investigating-the-statistical-properties/code/main.py': [Errno 2] No such file or directory

- python code/main.py --mode analyze -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-109-investigating-the-statistical-properties/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-109-investigating-the-statistical-properties/code/main.py': [Errno 2] No such file or directory

- python code/main.py --mode plot -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-109-investigating-the-statistical-properties/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-109-investigating-the-statistical-properties/code/main.py': [Errno 2] No such file or directory

