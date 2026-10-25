# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ (rc=1); python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true (rc=1); python -m pytest -q tests/contract/ (rc=1); 6 declared deliverable(s) absent: data/processed/dense_subset.parquet; data/processed/exclusion_log.json; data/processed/non_dense.parquet

## Failing / missing run-book commands

- python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ -> rc=1
runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/src/cli/run_experiment.py", line 33, in <module>
    from code.data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/code/data/download.py", line 23, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true -> rc=1
runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/src/cli/run_experiment.py", line 33, in <module>
    from code.data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/code/data/download.py", line 23, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest -q tests/contract/ -> rc=1
ontract/test_contracts.py:26: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/contracts/inference_results.schema.yaml')
mode = 'r', buffering = -1, encoding = 'utf-8', errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
E       FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/contracts/inference_results.schema.yaml'

/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py:1044: FileNotFoundError
=========================== short test summary info ============================
ERROR tests/contract/test_contracts.py::test_parquet_files_conform_to_schema
1 error in 0.49s



## Declared deliverables still missing

- data/processed/dense_subset.parquet
- data/processed/exclusion_log.json
- data/processed/non_dense.parquet
- data/raw/coco_val.parquet
- data/raw/refcoco_plus.parquet
- data/raw/vrsbench.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dense_subset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `src/cli/run_experiment.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/dense_subset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_dense.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_dense.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/coco_val.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/coco_val.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/refcoco_plus.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/refcoco_plus.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/vrsbench.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/vrsbench.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
