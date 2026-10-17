# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python data/preprocess.py --filter-mw 500 --split-ratio 0.8,0.1,0.1; python training/train.py --epochs 200 --batch-size 32 --seed 42; python training/evaluate.py --model models/mpnn.pt; 1 command(s) failed: python code/data/download.py (rc=1); 1 declared deliverable(s) absent: data/raw/ri_dataset.csv

## Failing / missing run-book commands

- python -c "import rdkit; print(rdkit.__version__)" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'rdkit'

- python code/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/code/data/download.py", line 36, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python data/preprocess.py --filter-mw 500 --split-ratio 0.8,0.1,0.1 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/data/preprocess.py': [Errno 2] No such file or directory

- python training/train.py --epochs 200 --batch-size 32 --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/training/train.py': [Errno 2] No such file or directory

- python training/evaluate.py --model models/mpnn.pt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/training/evaluate.py': [Errno 2] No such file or directory

- python models/attribution.py --model models/mpnn.pt --output results/attributions.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/models/attribution.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/ri_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/ri_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/ri_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
