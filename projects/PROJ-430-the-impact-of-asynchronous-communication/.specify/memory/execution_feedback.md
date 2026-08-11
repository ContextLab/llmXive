# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --metrics data/derived/pair_metrics.parquet --sentiment data/derived/pair_sentiment.parquet --output data/derived/statistical_results.json; 3 command(s) failed: python code/data_ingestion.py --sample-size 5 --output data/raw/sample_events.json (rc=1); python code/sentiment.py --input data/raw/sample_events.json --output data/derived/pair_sentiment.parquet (rc=1); python code/validation.py --vader data/derived/pair_sentiment.parquet --manual data/validation/manual_ground_truth.csv --output data/validation/validity_report.json (rc=1); 5 declared deliverable(s) absent: data/derived/pair_sentiment.parquet; data/derived/project_metrics.csv; data/derived/timestamp_features.parquet

## Failing / missing run-book commands

- python code/data_ingestion.py --sample-size 5 --output data/raw/sample_events.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/data_ingestion.py", line 14, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/sentiment.py --input data/raw/sample_events.json --output data/derived/pair_sentiment.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/sentiment.py", line 273, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/sentiment.py", line 210, in main
    ensure_directories_exist(config)
TypeError: ensure_directories_exist() takes 0 positional arguments but 1 was given
- python code/analysis.py --metrics data/derived/pair_metrics.parquet --sentiment data/derived/pair_sentiment.parquet --output data/derived/statistical_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/analysis.py': [Errno 2] No such file or directory
- python code/validation.py --vader data/derived/pair_sentiment.parquet --manual data/validation/manual_ground_truth.csv --output data/validation/validity_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/validation.py", line 25, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/derived/pair_sentiment.parquet
- data/derived/project_metrics.csv
- data/derived/timestamp_features.parquet
- data/raw/events.json
- data/validation/manual_ground_truth.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_directories_exist` — defined in `code/config.py`; called 11 way(s):

- code/persist_project_metrics.py: ensure_directories_exist(config)
- code/setup_data_structure.py: ensure_directories_exist([dir_path], logger)
- code/validate_cohesion.py: ensure_directories_exist(config)
- code/aggregate_pair_sentiment.py: ensure_directories_exist(config)
- code/setup_venv.py: ensure_directories_exist([project_root])
- code/persist_timestamp_features.py: ensure_directories_exist(config)
- code/ingest_ground_truth.py: ensure_directories_exist([output_path.parent])
- code/data_ingestion.py: ensure_directories_exist([output_path])
- code/validation.py: ensure_directories_exist(config)
- code/aggregation.py: ensure_directories_exist()
- code/sentiment.py: ensure_directories_exist(config)

Make `ensure_directories_exist` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/pair_sentiment.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_pair_sentiment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pair_sentiment.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/project_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/persist_project_metrics.py` — NOT invoked by the run-book
    - `code/metrics.py` — IS a run-book command
    - `code/persist_timestamp_features.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/project_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/timestamp_features.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/persist_project_metrics.py` — NOT invoked by the run-book
    - `code/aggregate_pair_sentiment.py` — NOT invoked by the run-book
    - `code/persist_timestamp_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/timestamp_features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/events.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_pair_sentiment.py` — NOT invoked by the run-book
    - `code/metrics.py` — IS a run-book command
    - `code/persist_timestamp_features.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/sentiment.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
    - `code/utils/logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/events.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/manual_ground_truth.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_cohesion.py` — NOT invoked by the run-book
    - `code/ingest_ground_truth.py` — NOT invoked by the run-book
    - `code/validation.py` — IS a run-book command
  Make ONE of these WRITE `data/validation/manual_ground_truth.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
