# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.0 0.5 0.9 (rc=1); 1 declared deliverable(s) absent: data/processed/human_python.csv

## Failing / missing run-book commands

- python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.0 0.5 0.9 -> rc=1
me/runner/work/llmXive/llmXive/projects/PROJ-347-evaluating-the-impact-of-code-generation/src/run_pipeline.py", line 19, in <module>
    from code.download_devign import main as download_devign_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-347-evaluating-the-impact-of-code-generation/code/download_devign.py", line 13, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4


## Declared deliverables still missing

- data/processed/human_python.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/human_python.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_human_python.py` — NOT invoked by the run-book
    - `src/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/human_python.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
