# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/main.py scaffold; python code/main.py download; python code/main.py preprocess

## Failing / missing run-book commands

- python code/main.py scaffold -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py download -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py preprocess -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py train -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py evaluate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

- python code/main.py report -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-181-predicting-species-distribution-shifts-u/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/main.py': [Errno 2] No such file or directory

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
