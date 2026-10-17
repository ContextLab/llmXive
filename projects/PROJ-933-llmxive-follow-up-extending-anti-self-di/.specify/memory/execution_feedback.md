# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python main.py --mode full --timeout 18000   # 5 h = 18 000 s`
  - script usage: `main.py [-h] [--mode {full,data,inference,train,analysis}]`
  - argparse error: `main.py: error: unrecognized arguments: # 5 h = 18 000 s`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/download.py (rc=1); python main.py --mode full --timeout 18000   # 5 h = 18 000 s (rc=2)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-933-llmxive-follow-up-extending-anti-self-di/code/data/download.py", line 7, in <module>
    import datasets
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-933-llmxive-follow-up-extending-anti-self-di/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-933-llmxive-follow-up-extending-anti-self-di/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-933-llmxive-follow-up-extending-anti-self-di/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python main.py --mode full --timeout 18000   # 5 h = 18 000 s -> rc=2

usage: main.py [-h] [--mode {full,data,inference,train,analysis}]
               [--timeout TIMEOUT]
main.py: error: unrecognized arguments: # 5 h = 18 000 s

