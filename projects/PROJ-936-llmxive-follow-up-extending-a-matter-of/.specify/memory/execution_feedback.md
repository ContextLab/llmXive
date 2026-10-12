# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipelines.run_all  --max_tasks 200  --penalty_threshold 2.0  --seed 42 (rc=1); 1 declared deliverable(s) absent: data/raw/τc_bench/tasks.json

## Failing / missing run-book commands

- python -m src.pipelines.run_all  --max_tasks 200  --penalty_threshold 2.0  --seed 42 -> rc=1

  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/src/pipelines/run_all.py", line 18, in <module>
    from download_tau_c_bench import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/code/download_tau_c_bench.py", line 18, in <module>
    import datasets
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-936-llmxive-follow-up-extending-a-matter-of/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-936-llmxive-follow-up-extending-a-matter-of/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-936-llmxive-follow-up-extending-a-matter-of/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4


## Declared deliverables still missing

- data/raw/τc_bench/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/τc_bench/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_tau_c_bench.py` — NOT invoked by the run-book
    - `src/pipelines/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/τc_bench/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
