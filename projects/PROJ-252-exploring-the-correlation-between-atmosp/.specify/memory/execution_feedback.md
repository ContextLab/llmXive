# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.download_pressure   # streams data, no large disk footprint`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 command(s) failed: python -m pytest tests/   # should exit with a successful status (rc=4); python -m code.download_usgs (rc=1); python -m code.download_pressure   # streams data, no large disk footprint (rc=1); 1 declared deliverable(s) absent: data/raw/usgs_2013_2023.csv

## Failing / missing run-book commands

- python -m pytest tests/   # should exit with a successful status -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.2, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python -m code.download_usgs -> rc=1
2026-10-23 07:49:16,983 - download - INFO - Fetching USGS earthquake catalog from 2013-01-01T00:00:00 to 2023-12-31T00:00:00
2026-10-23 07:49:17,013 - download - ERROR - Failed to fetch USGS data via ObsPy: Bad request. If you think your request was valid please contact the developers.
HTTP Status code: 400
Detailed response of server:


2026-10-23 07:49:17,014 - __main__ - ERROR - download_usgs failed: Critical failure fetching USGS data: Bad request. If you think your request was valid please contact the developers.
HTTP Status code: 400
Detailed response of server:




- python -m code.download_pressure   # streams data, no large disk footprint -> rc=1
2026-10-23 07:49:17,526 - download - INFO - Downloading NOAA pressure dataset from https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/mslp.daily.nc
2026-10-23 07:49:17,712 - download - ERROR - Failed to download NOAA pressure dataset: [Errno -90] NetCDF: file not found: 'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/mslp.daily.nc'
2026-10-23 07:49:17,712 - __main__ - ERROR - download_pressure failed: Critical failure downloading NOAA dataset: [Errno -90] NetCDF: file not found: 'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/mslp.daily.nc'


- python -m code.preprocess -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 12, in <module>
    import geopandas as gpd
ModuleNotFoundError: No module named 'geopandas'

- python -m code.analysis -> rc=1
ozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
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

- python -m code.report -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: No module named code.report

- python -m code.download_climate   # streams ENSO/PDO and ERA5 covariates -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: No module named code.download_climate

- python -m code.preprocess_extended -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: No module named code.preprocess_extended

- python -m code.analysis_extended -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: No module named code.analysis_extended

- python -m code.report_extended -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: No module named code.report_extended

- python -m pytest tests/contract/ -> rc=1
data_schema.py:63: in load_schema
    raise FileNotFoundError(f"Schema file not found: {schema_file}")
E   FileNotFoundError: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/contracts/earthquake.yaml
=========================== short test summary info ============================
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_load_earthquake_schema
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_load_pressure_anomaly_schema
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_earthquake_schema_validates_valid_data
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_earthquake_schema_rejects_missing_fields
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_pressure_anomaly_schema_validates_valid_data
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_pressure_anomaly_schema_rejects_missing_fields
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_required_fields_match_spec
============================== 7 failed in 0.07s ===============================



## Declared deliverables still missing

- data/raw/usgs_2013_2023.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/usgs_2013_2023.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/usgs_2013_2023.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
