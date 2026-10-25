# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 (rc=1); python -m pytest -v tests/ (rc=2); 5 declared deliverable(s) absent: data/derived/clean_subjects.parquet; data/derived/entropy_matrix.parquet; data/derived/invalid_parcels.csv

## Failing / missing run-book commands

- python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 -> rc=1
lmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/download_data.py", line 12, in <module>
    from code.src.data.download_hcp import main as _download_hcp_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/data/download_hcp.py", line 18, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest -v tests/ -> rc=2
e.src.download_data import main as download_main
code/src/download_data.py:12: in <module>
    from code.src.data.download_hcp import main as _download_hcp_main
code/src/data/download_hcp.py:18: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/datasets/__init__.py:18: in <module>
    from .arrow_dataset import Dataset
../../.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/datasets/arrow_dataset.py:60: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/unit/test_qc.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.61s ===============================



## Declared deliverables still missing

- data/derived/clean_subjects.parquet
- data/derived/entropy_matrix.parquet
- data/derived/invalid_parcels.csv
- data/derived/subject_qc.csv
- data/raw/dsrt_scores.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/clean_subjects.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/clean_subjects.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/entropy_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/entropy_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/invalid_parcels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/tests/unit/test_entropy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/invalid_parcels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/subject_qc.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/subject_qc.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dsrt_scores.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download_hcp.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dsrt_scores.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
