# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/report.py; 4 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1
2026-10-12 11:11:50,487 - __main__ - INFO - Starting T002: Data Acquisition Pipeline.
2026-10-12 11:11:50,487 - __main__ - INFO - Downloading NOAA pressure file: https://psl.noaa.gov/thredds/fileServer/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc
2026-10-12 11:11:50,614 - __main__ - ERROR - NOAA download failed: 404 Client Error:  for url: https://psl.noaa.gov/thredds/fileServer/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc
2026-10-12 11:11:50,614 - __main__ - CRITICAL - T002 failed: Critical failure downloading NOAA data: 404 Client Error:  for url: https://psl.noaa.gov/thredds/fileServer/Datasets/ncep.reanalysis.dailyavgs/pressure/2020/pressure.20200101.nc


- python code/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 12, in <module>
    import geopandas as gpd
ModuleNotFoundError: No module named 'geopandas'

- python code/analysis.py -> rc=1
 11:11:51 - __main__ - INFO - Starting analysis pipeline.

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
/tests/unit/test_t017_master_dataset.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_t017_master_dataset.py:11: in <module>
    from preprocess import load_config, validate_master_dataset, load_schema, get_expected_count
code/preprocess.py:12: in <module>
    import geopandas as gpd
E   ModuleNotFoundError: No module named 'geopandas'
=========================== short test summary info ============================
ERROR tests/integration/test_permutation.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_deduplication.py
ERROR tests/unit/test_generate_master_dataset.py
ERROR tests/unit/test_null_hypothesis.py
ERROR tests/unit/test_ocean_mask.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_preprocess_anomalies.py
ERROR tests/unit/test_statistics.py
ERROR tests/unit/test_t017_master_dataset.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 0.81s ==============================


