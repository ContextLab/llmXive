# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python code/src/data/clean.py (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1
wnload.py", line 116, in main
    dest = download_vaers_dataset()
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 81, in download_vaers_dataset
    from datasets import load_dataset  # imported lazily so --help works fast
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/data/validate.py -> rc=2
2026-10-19 02:53:59,184 - validate - INFO - Loading schema from contracts/dataset.schema.yaml
2026-10-19 02:53:59,187 - validate - INFO - Loading data from data/processed/cleaned_vaers.parquet
2026-10-19 02:53:59,187 - validate - ERROR - Data file not found: data/processed/cleaned_vaers.parquet


- python code/src/data/clean.py -> rc=1

2026-10-19 02:53:59,561 - clean - INFO - Starting data cleaning process
2026-10-19 02:53:59,561 - clean - ERROR - No VAERS CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/code/data/raw

- python src/main.py -> rc=1
2026-10-19 02:54:00,289 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


