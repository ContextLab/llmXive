# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/validate.py`
  - script usage: `validate.py [-h] --input INPUT [--schema SCHEMA]`
  - argparse error: `validate.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python src/data/clean.py (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1
12:23:29,314 INFO __main__: Starting download from https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/vaers_2020_2023.parquet
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 163, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 159, in main
    fetch_vaers_data()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 129, in fetch_vaers_data
    download_file(DATASET_URL, PARQUET_PATH)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 86, in download_file
    r.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/vaers_2020_2023.parquet

- python src/data/validate.py -> rc=2

usage: validate.py [-h] --input INPUT [--schema SCHEMA]
validate.py: error: the following arguments are required: --input

- python src/data/clean.py -> rc=1

2026-10-25 12:23:30,243 - clean - INFO - Starting data cleaning process
2026-10-25 12:23:30,244 - clean - ERROR - No VAERS data files found in /home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/data/raw

- python src/main.py -> rc=1
2026-10-25 12:23:31,007 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


