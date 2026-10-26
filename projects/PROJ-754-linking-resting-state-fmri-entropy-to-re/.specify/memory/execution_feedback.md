# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit <maximum_subjects>  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 (rc=1); python -m pytest -v tests/ (rc=2); 5 declared deliverable(s) absent: data/derived/clean_subjects.parquet; data/derived/entropy_matrix.parquet; data/derived/invalid_parcels.csv

## Failing / missing run-book commands

- python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit <maximum_subjects>  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 -> rc=1
ting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pandas/compat/__init__.py", line 29, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pandas/compat/pyarrow.py", line 12, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pyarrow/__init__.py", line 65, in <module>
    import pyarrow.lib as _lib
AttributeError: _ARRAY_API not found
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/src/run_pipeline.py", line 16, in <module>
    from code.src.pipeline import run_pipeline as _orchestrator
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/pipeline.py", line 15, in <module>
    from src.config.env_manager import get_hcp_token
ModuleNotFoundError: No module named 'src.config'

- python -m pytest -v tests/ -> rc=2

tests/unit/test_power_pre.py:14: in <module>
    from src.stats.power_pre import compute_power, write_results, POWER_THRESHOLD
E   ModuleNotFoundError: No module named 'src.stats.power_pre'
____________________ ERROR collecting tests/unit/test_qc.py ____________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/tests/unit/test_qc.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_qc.py:19: in <module>
    from src.data.qc import validate_and_filter, main
E   ModuleNotFoundError: No module named 'src.data'
=========================== short test summary info ============================
ERROR tests/unit/test_entropy.py
ERROR tests/unit/test_pipeline_execution.py
ERROR tests/unit/test_power_pre.py
ERROR tests/unit/test_qc.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.50s ===============================



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
    - `code/src/stats/model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/entropy_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/invalid_parcels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/tests/unit/test_entropy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/invalid_parcels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/subject_qc.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/subject_qc.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dsrt_scores.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download_hcp.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dsrt_scores.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
