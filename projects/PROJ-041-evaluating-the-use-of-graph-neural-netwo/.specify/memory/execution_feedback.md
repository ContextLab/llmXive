# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py  --scenarios all      # processes every scenario present in the dataset; 2 command(s) failed: python -m pytest code/tests/test_graph_construction.py -q (rc=4); python -m pytest code/tests/test_memory_limits.py -q (rc=4); 1 declared deliverable(s) absent: data/raw/ctu13_scenario1.csv

## Failing / missing run-book commands

- python code/main.py  --scenarios all      # processes every scenario present in the dataset -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-041-evaluating-the-use-of-graph-neural-netwo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/code/main.py': [Errno 2] No such file or directory

- python -m pytest code/tests/test_graph_construction.py -q -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.2, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_graph_construction.py


- python -m pytest code/tests/test_memory_limits.py -q -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.2, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_memory_limits.py



## Declared deliverables still missing

- data/raw/ctu13_scenario1.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/ctu13_scenario1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/download_ctu13.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ctu13_scenario1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
