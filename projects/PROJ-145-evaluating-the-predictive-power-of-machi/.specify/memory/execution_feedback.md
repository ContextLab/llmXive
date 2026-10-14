# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; 1 command(s) failed: python -m pytest -q (rc=2); 3 declared deliverable(s) absent: data/processed/heas_train.csv; data/processed/true_novel.csv; data/raw/hea_placeholder.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-145-evaluating-the-predictive-power-of-machi/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-145-evaluating-the-predictive-power-of-machi/code/run_pipeline.py': [Errno 2] No such file or directory

- python -m pytest -q -> rc=2
arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-145-evaluating-the-predictive-power-of-machi/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-145-evaluating-the-predictive-power-of-machi/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/integration/test_data_ingestion.py
ERROR tests/integration/test_dedup_index_integration.py
ERROR tests/unit/test_data_ingestion.py
ERROR tests/unit/test_data_ingestion_t014.py
ERROR tests/unit/test_dedup_index.py
ERROR tests/unit/test_descriptors.py
ERROR tests/unit/test_download_hmao.py
ERROR tests/unit/test_export_holdout.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_true_novel.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 1.99s ==============================



## Declared deliverables still missing

- data/processed/heas_train.csv
- data/processed/true_novel.csv
- data/raw/hea_placeholder.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/heas_train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/feature_engineering.py` — NOT invoked by the run-book
    - `code/generate_true_novel.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/validate_splits.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/heas_train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/true_novel.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/feature_engineering.py` — NOT invoked by the run-book
    - `code/generate_true_novel.py` — NOT invoked by the run-book
    - `code/validate_splits.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/true_novel.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/hea_placeholder.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/hea_placeholder.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
