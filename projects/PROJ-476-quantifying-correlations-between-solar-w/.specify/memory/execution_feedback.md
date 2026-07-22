# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py fetch --start 1998-01-01 --end 2020-12-31`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py fetch --start 1998-01-01 --end 2020-12-31 (rc=1); python code/main.py compute-thresholds (rc=1); python code/main.py analyze --data data/processed/synced.csv --lags 0,1,2,3,6 (rc=1); 3 declared deliverable(s) absent: data/processed/synced.csv; data/raw/ace_raw.csv; data/raw/noaa_raw.csv

## Failing / missing run-book commands

- python code/main.py fetch --start 1998-01-01 --end 2020-12-31 -> rc=1
    turn self.getresp()
           ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/ftplib.py", line 254, in getresp
    raise error_perm(resp)
ftplib.error_perm: 550 SSL/TLS required on the control channel

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 257, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 237, in main
    run_fetch(args.start, args.end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 88, in run_fetch
    ace_path = fetch_ace(start_date, end_date)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch.py", line 161, in fetch_ace
    raise ConnectionError(f"Failed to connect to NASA SPDF FTP: {e}")
ConnectionError: Failed to connect to NASA SPDF FTP: 550 SSL/TLS required on the control channel
- python code/main.py compute-thresholds -> rc=1
    2026-07-22 09:33:21,565 - solar_wind - INFO - --- Phase 3: Global Threshold Calculation ---
2026-07-22 09:33:21,566 - solar_wind - ERROR - Failed to calculate thresholds: load_synced_data() takes 0 positional arguments but 1 was given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 257, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 241, in main
    run_thresholds(args.data, args.output)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 120, in run_thresholds
    df = load_synced_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_synced_data() takes 0 positional arguments but 1 was given
- python code/main.py analyze --data data/processed/synced.csv --lags 0,1,2,3,6 -> rc=1
    2026-07-22 09:33:22,810 - solar_wind - INFO - --- Phase 4: Lagged Correlation Analysis ---
2026-07-22 09:33:22,810 - solar_wind - ERROR - Failed to run correlation analysis: load_synced_data() takes 0 positional arguments but 1 was given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 257, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 244, in main
    run_analyze(args.data, lags, args.output)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 141, in run_analyze
    df = load_synced_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_synced_data() takes 0 positional arguments but 1 was given
- python code/main.py validate --data data/processed/synced.csv --test-start 2018-01-01 --test-end 2020-12-31 -> rc=1
    2026-07-22 09:33:24,057 - solar_wind - INFO - --- Phase 5: Validation & Reporting ---
2026-07-22 09:33:24,057 - solar_wind - ERROR - Failed to run validation: run_validation_report() got an unexpected keyword argument 'data_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 257, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 246, in main
    run_validate(args.data, args.correlations, args.thresholds, args.test_start, args.test_end, args.report)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 161, in run_validate
    run_validation_report(
TypeError: run_validation_report() got an unexpected keyword argument 'data_path'

## Declared deliverables still missing

- data/processed/synced.csv
- data/raw/ace_raw.csv
- data/raw/noaa_raw.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `load_synced_data` — defined in `code/analysis/correlation.py`; called 3 way(s):

- code/main.py: df = load_synced_data(data_path)
- code/viz/plots.py: df = load_synced_data(data_path)
- code/analysis/correlation.py: df = load_synced_data()

Make `load_synced_data` in `code/analysis/correlation.py` accept ALL of the above.

### `run_validation_report` — defined in `code/viz/report.py`; called 1 way(s):

- code/main.py: run_validation_report(

Make `run_validation_report` in `code/viz/report.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/synced.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/viz/report.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/viz/report_generation.py` — NOT invoked by the run-book
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/analysis/thresholds.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synced.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ace_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/validate.py` — NOT invoked by the run-book
    - `code/data/fetch.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ace_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/noaa_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/validate.py` — NOT invoked by the run-book
    - `code/data/fetch.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/noaa_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
