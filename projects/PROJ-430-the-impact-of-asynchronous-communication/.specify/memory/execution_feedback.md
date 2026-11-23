# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --metrics data/derived/pair_metrics.parquet --sentiment data/derived/pair_sentiment.parquet --output data/derived/statistical_results.json; 3 command(s) failed: python code/metrics.py --input data/raw/sample_events.json --output data/derived/pair_metrics.parquet (rc=1); python code/sentiment.py --input data/raw/sample_events.json --output data/derived/pair_sentiment.parquet (rc=1); python code/validation.py --vader data/derived/pair_sentiment.parquet --manual data/validation/manual_ground_truth.csv --output data/validation/validity_report.json (rc=1); 6 declared deliverable(s) absent: data/derived/pair_metrics.parquet; data/derived/pair_sentiment.parquet; data/derived/project_cohesion_scores.csv

## Failing / missing run-book commands

- python code/metrics.py --input data/raw/sample_events.json --output data/derived/pair_metrics.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/metrics.py", line 12, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-430-the-impact-of-asynchronous-communication/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/sentiment.py --input data/raw/sample_events.json --output data/derived/pair_sentiment.parquet -> rc=1

Input file not found: data/raw/sample_events.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/sentiment.py", line 304, in main
    with open(args.input, 'r', encoding='utf-8') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/sample_events.json'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/sentiment.py", line 411, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/sentiment.py", line 308, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined

- python code/analysis.py --metrics data/derived/pair_metrics.parquet --sentiment data/derived/pair_sentiment.parquet --output data/derived/statistical_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-430-the-impact-of-asynchronous-communication/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/analysis.py': [Errno 2] No such file or directory

- python code/validation.py --vader data/derived/pair_sentiment.parquet --manual data/validation/manual_ground_truth.csv --output data/validation/validity_report.json -> rc=1
{"timestamp": "2026-10-22T03:33:16.307809", "level": "INFO", "logger": "ingest_ground_truth", "message": "Starting multi-modal validation preparation (T023)...", "module": "validation", "function": "run_validation_pipeline", "line": 217}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/validation.py", line 278, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/validation.py", line 267, in main
    result = run_validation_pipeline(config)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/validation.py", line 220, in run_validation_pipeline
    sentiment_df = load_sentiment_derived_data(config)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-430-the-impact-of-asynchronous-communication/code/validation.py", line 54, in load_sentiment_derived_data
    data_dir = Path(config['paths']['data_dir'])
                    ~~~~~~^^^^^^^^^
KeyError: 'paths'


## Declared deliverables still missing

- data/derived/pair_metrics.parquet
- data/derived/pair_sentiment.parquet
- data/derived/project_cohesion_scores.csv
- data/derived/project_metrics.csv
- data/raw/events.json
- data/validation/manual_ground_truth.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/pair_metrics.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_project_metrics.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/metrics.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
    - `code/persist_project_metrics.py` — NOT invoked by the run-book
    - `code/persist_timestamp_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pair_metrics.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/pair_sentiment.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_pair_sentiment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pair_sentiment.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/project_cohesion_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/project_cohesion_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/project_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_project_metrics.py` — NOT invoked by the run-book
    - `code/metrics.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
    - `code/persist_project_metrics.py` — NOT invoked by the run-book
    - `code/persist_timestamp_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/project_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/events.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_pair_sentiment.py` — NOT invoked by the run-book
    - `code/aggregate_project_metrics.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/metrics.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
    - `code/persist_project_metrics.py` — NOT invoked by the run-book
    - `code/persist_timestamp_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/events.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/validation/manual_ground_truth.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest_ground_truth.py` — NOT invoked by the run-book
    - `code/validate_cohesion.py` — NOT invoked by the run-book
    - `code/validation.py` — IS a run-book command
  Make ONE of these WRITE `data/validation/manual_ground_truth.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
