# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 (rc=1); python -m pytest -q tests/contract (rc=4); python -m src.pipeline.run_all  --window_size 30  --step_size 5  --seed 123  --output_dir data/output/window30_step5  --permutations 5000 (rc=1); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; ds = load_dataset('openneuro', 'ds000246'); print(ds)" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/bin/python: Error while finding module specification for 'src.pipeline.run_all' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


- python -m src.pipeline.run_all  --window_size 30  --step_size 5  --seed 123  --output_dir data/output/window30_step5  --permutations 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/bin/python: Error while finding module specification for 'src.pipeline.run_all' (ModuleNotFoundError: No module named 'src')


## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_openneuro.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
