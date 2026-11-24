# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m ingestion --download (rc=1); python -m main (rc=1); python -m pytest tests/unit/test_metrics.py::test_birthday_ratio_reference (rc=4); 1 declared deliverable(s) absent: data/processed/metrics.json

## Failing / missing run-book commands

- python -m ingestion --download -> rc=1
aws.csv: 5e6fe0a6133ec1a9447e239ee28507bb1c91f010b82956a48d75a4645a88bd82
2026-10-19 12:58:35,142 - INFO - Checksum persisted to /home/runner/work/llmXive/llmXive/projects/PROJ-095-statistical-analysis-of-lottery-number-f/data/checksums.json
2026-10-19 12:58:35,142 - INFO - Processing raw data from /home/runner/work/llmXive/llmXive/projects/PROJ-095-statistical-analysis-of-lottery-number-f/data/raw/lottery_draws.csv
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-095-statistical-analysis-of-lottery-number-f/code/ingestion.py", line 260, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-095-statistical-analysis-of-lottery-number-f/code/ingestion.py", line 252, in main
    df = process_draws(RAW_PATH, PROCESSED_PATH)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-095-statistical-analysis-of-lottery-number-f/code/ingestion.py", line 179, in process_draws
    raise LotteryDataError("Loaded data is empty")
exceptions.LotteryDataError: Loaded data is empty

- python -m main -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-095-statistical-analysis-of-lottery-number-f/bin/python: No module named main

- python -m pytest tests/unit/test_metrics.py::test_birthday_ratio_reference -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-095-statistical-analysis-of-lottery-number-f
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_metrics.py::test_birthday_ratio_reference



## Declared deliverables still missing

- data/processed/metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/constants.py` — NOT invoked by the run-book
    - `code/generate_legacy_metrics.py` — NOT invoked by the run-book
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/save_metrics.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
