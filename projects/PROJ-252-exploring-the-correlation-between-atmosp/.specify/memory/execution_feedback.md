# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/report.py; 4 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1

2026-10-12 07:46:11,369 - __main__ - INFO - Starting download pipeline (T002).
2026-10-12 07:46:11,369 - __main__ - WARNING - DEV-001 (Global Data Block) deviation record not found.
2026-10-12 07:46:11,371 - __main__ - INFO - Downloading NOAA pressure file: https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc
2026-10-12 07:46:11,522 - __main__ - ERROR - Failed to download https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc: 404 Client Error: Not Found for url: https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc
2026-10-12 07:46:11,522 - __main__ - CRITICAL - NOAA download failed: NOAA download failed for https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc

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
 07:46:12 - __main__ - INFO - Starting analysis pipeline.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 317, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 310, in main
    results = run_analysis()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 264, in run_analysis
    df = load_master_dataset()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 30, in load_master_dataset
    raise FileNotFoundError(f"Master dataset not found at {parquet_path} or {csv_path}")
FileNotFoundError: Master dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/data/processed/master_dataset.parquet or /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/data/processed/master_dataset.csv

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_t017_master_dataset.py:11: in <module>
    from preprocess import load_config, validate_master_dataset, load_schema, get_expected_count
E   ImportError: cannot import name 'validate_master_dataset' from 'preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py)
=========================== short test summary info ============================
ERROR tests/integration/test_permutation.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_generate_master_dataset.py
ERROR tests/unit/test_null_hypothesis.py
ERROR tests/unit/test_ocean_mask.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_preprocess_anomalies.py
ERROR tests/unit/test_statistics.py
ERROR tests/unit/test_t017_master_dataset.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.72s ===============================


