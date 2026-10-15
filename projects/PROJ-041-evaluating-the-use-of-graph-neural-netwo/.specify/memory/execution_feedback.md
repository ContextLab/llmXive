# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py --scenarios 1 2 3 --seeds 42 123 456; 2 command(s) failed: python code/data/ingest_netflow.py --source fallback (rc=1); python -m pytest code/tests/test_graph_construction.py -v (rc=4)

## Failing / missing run-book commands

- python code/data/ingest_netflow.py --source fallback -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/code/data/ingest_netflow.py", line 8, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-041-evaluating-the-use-of-graph-neural-netwo/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.2

- python code/main.py --scenarios 1 2 3 --seeds 42 123 456 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-041-evaluating-the-use-of-graph-neural-netwo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/code/main.py': [Errno 2] No such file or directory

- python -m pytest code/tests/test_graph_construction.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.3, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-041-evaluating-the-use-of-graph-neural-netwo/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo
configfile: pyproject.toml
plugins: memprof-0.1.0, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_graph_construction.py


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
