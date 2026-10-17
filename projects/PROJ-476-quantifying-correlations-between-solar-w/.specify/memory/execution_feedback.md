# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m code.main --stage all (rc=1); python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 (rc=1); python -m code.main --stage align (rc=1); 1 declared deliverable(s) absent: data/processed/synced.csv

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 278, in fetch_ace
    _fetch_and_merge_ace(start_date, end_date, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 158, in _fetch_and_merge_ace
    swepam_files = _list_ftp_files(host, swepam_dir)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 97, in _list_ftp_files
    ftp.login()
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 412, in login
    resp = self.sendcmd('USER ' + user)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 281, in sendcmd
    return self.getresp()
           ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 254, in getresp
    raise error_perm(resp)
ftplib.error_perm: 550 SSL/TLS required on the control channel

- python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 -> rc=1
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 278, in fetch_ace
    _fetch_and_merge_ace(start_date, end_date, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 158, in _fetch_and_merge_ace
    swepam_files = _list_ftp_files(host, swepam_dir)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 97, in _list_ftp_files
    ftp.login()
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 412, in login
    resp = self.sendcmd('USER ' + user)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 281, in sendcmd
    return self.getresp()
           ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 254, in getresp
    raise error_perm(resp)
ftplib.error_perm: 550 SSL/TLS required on the control channel

- python -m code.main --stage align -> rc=1
rrelations-between-solar-w/code/data/align.py", line 11, in load_raw_ace
    df = pd.read_csv(filepath)
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/ace_raw.csv'

- python -m code.main --stage analyze --lags 0,1,2,3,6 -> rc=1

2026-10-17 02:19:31,556 - solar_wind - INFO - --- Stage analyze: lagged correlations ---
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 161, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 149, in main
    run_analyze(lags=lags)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 74, in run_analyze
    df = load_synced_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/analysis/correlation.py", line 38, in load_synced_data
    raise FileNotFoundError(f"Synced data file not found at {data_path}")
FileNotFoundError: Synced data file not found at data/processed/synced.csv

- python -m code.main --stage validate -> rc=1
un_validate
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/synced.csv'


## Declared deliverables still missing

- data/processed/synced.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/synced.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/significance.py` — NOT invoked by the run-book
    - `code/analysis/thresholds.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synced.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
