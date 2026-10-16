# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/pipeline/extract.py; python code/pipeline/train.py --pilot; python code/pipeline/train.py; 1 command(s) failed: python -m pytest tests/   # runs unit, integration, and contract tests (rc=4)

## Failing / missing run-book commands

- python code/pipeline/extract.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/pipeline/extract.py': [Errno 2] No such file or directory

- python code/pipeline/train.py --pilot -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/pipeline/train.py': [Errno 2] No such file or directory

- python code/pipeline/train.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/pipeline/train.py': [Errno 2] No such file or directory

- python code/pipeline/evaluate.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/pipeline/evaluate.py': [Errno 2] No such file or directory

- python code/pipeline/evaluate.py --mode sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/pipeline/evaluate.py': [Errno 2] No such file or directory

- python code/pipeline/evaluate.py --mode ablation -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/pipeline/evaluate.py': [Errno 2] No such file or directory

- python -m pytest tests/   # runs unit, integration, and contract tests -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.2, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-930-llmxive-follow-up-extending-mobileforge/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-930-llmxive-follow-up-extending-mobileforge
configfile: pyproject.toml
plugins: platformdirs-4.13.3
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
