# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/usgs_test_subset.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/usgs_test_subset.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/report.py; 3 command(s) failed: python code/preprocess.py (rc=1); python code/analysis.py (rc=1); python -m pytest tests/ (rc=3); 4 declared deliverable(s) absent: data/interim/anomalies_raw.csv; data/interim/clean_events.csv; data/interim/masked_events.csv

## Failing / missing run-book commands

- python code/preprocess.py -> rc=1
e 125, in interpolate_pressure_grid
    raw_pressure_df.to_parquet(out_path, index=False)
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/util/_decorators.py", line 333, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 3113, in to_parquet
    return to_parquet(
           ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 476, in to_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 67, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.


- python code/analysis.py -> rc=1
2026-10-12 04:26:10 - __main__ - INFO - Starting analysis pipeline.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 320, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 313, in main
    results = run_analysis()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 267, in run_analysis
    df = load_master_dataset()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 19, in load_master_dataset
    raise FileNotFoundError(f"Master dataset not found at {path}")
FileNotFoundError: Master dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/data/processed/master_dataset.csv

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=3
LERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pluggy/_callers.py", line 167, in _multicall
INTERNALERROR>     raise exception
INTERNALERROR>   File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pluggy/_callers.py", line 121, in _multicall
INTERNALERROR>     res = hook_impl.function(*args)
INTERNALERROR>           ^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/debugging.py", line 72, in pytest_configure
INTERNALERROR>     import pdb
INTERNALERROR>   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pdb.py", line 77, in <module>
INTERNALERROR>     import code
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/__init__.py", line 17, in <module>
INTERNALERROR>     from .utils.logging import setup_logging, get_logger
INTERNALERROR> ImportError: cannot import name 'setup_logging' from 'code.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/utils/logging.py)


## Declared deliverables still missing

- data/interim/anomalies_raw.csv
- data/interim/clean_events.csv
- data/interim/masked_events.csv
- data/interim/pressure_grid_fine.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/anomalies_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/anomalies_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/clean_events.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/clean_events.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/masked_events.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/masked_events.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/pressure_grid_fine.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/pressure_grid_fine.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
