# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m code.main --stage all (rc=1); python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 (rc=1); python -m code.main --stage align (rc=1); 1 declared deliverable(s) absent: data/processed/synced.csv

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1

2026-10-17 04:08:32,624 ERROR code: Both --start and --end are required for the full pipeline.

- python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 -> rc=1
())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 141, in main
    _run_fetch(args.start, args.end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 35, in _run_fetch
    ace_path = fetch_ace(start_date, end_date)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 210, in fetch_ace
    _fetch_and_merge_ace(start_date, end_date, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 148, in _fetch_and_merge_ace
    swepam_txt = _download_text(swepam_url)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 52, in _download_text
    raise ConnectionError(f"Unable to download {url}") from exc
ConnectionError: Unable to download https://services.swpc.noaa.gov/products/ace/ace_swepam_1m.txt

- python -m code.main --stage align -> rc=1
xception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 174, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 145, in main
    _run_align()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 47, in _run_align
    output_path = run_sync()
                  ^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/sync.py", line 213, in run_sync
    merged_raw = _load_csv(fixture_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/sync.py", line 47, in _load_csv
    raise FileNotFoundError(f"Required file not found: {filepath}")
FileNotFoundError: Required file not found: data/fixtures/monthly_sample.csv

- python -m code.main --stage analyze --lags 0,1,2,3,6 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 174, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 150, in main
    _run_analyze(lags)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 58, in _run_analyze
    df = load_synced_data()
         ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/analysis/correlation.py", line 38, in load_synced_data
    raise FileNotFoundError(f"Synced data file not found at {data_path}")
FileNotFoundError: Synced data file not found at data/processed/synced.csv

- python -m code.main --stage validate -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 174, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 154, in main
    _run_validate()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 78, in _run_validate
    df = load_synced_data()
         ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/analysis/correlation.py", line 38, in load_synced_data
    raise FileNotFoundError(f"Synced data file not found at {data_path}")
FileNotFoundError: Synced data file not found at data/processed/synced.csv


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
    - `code/data/sync.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synced.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
