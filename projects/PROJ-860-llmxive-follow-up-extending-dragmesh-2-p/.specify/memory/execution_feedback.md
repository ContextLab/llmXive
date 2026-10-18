# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/main.py --mode full  --num_objects 10  --seed 42; python code/analysis/statistical_test.py --input data/logs/; python code/main.py --mode full --seed $RANDOM; 1 command(s) failed: python code/data_loader.py (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py -> rc=1
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py", line 20, in <module>
    raise ImportError(
ImportError: The 'datasets' library is required to fetch DragMesh-2. Please install it via: pip install datasets

- python code/main.py --mode full  --num_objects 10  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/main.py': [Errno 2] No such file or directory

- python code/analysis/statistical_test.py --input data/logs/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/analysis/statistical_test.py': [Errno 2] No such file or directory

- python code/main.py --mode full --seed $RANDOM -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/main.py': [Errno 2] No such file or directory

## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
