# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python code/data_ingestion.py --download-only (rc=1); 1 declared deliverable(s) absent: data/processed/merged_clean.parquet

## Failing / missing run-book commands

- python code/data_ingestion.py --download-only -> rc=1

2026-10-12 12:21:15,134 - config - WARNING - Config file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-275-statistical-analysis-of-publicly-availab/specs/001-sentiment-revenue-lag-analysis/config.yaml, using defaults
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-275-statistical-analysis-of-publicly-availab/code/data_ingestion.py", line 244, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-275-statistical-analysis-of-publicly-availab/code/data_ingestion.py", line 190, in main
    ensure_directories([log_file.parent])
TypeError: ensure_directories() takes 0 positional arguments but 1 was given

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-275-statistical-analysis-of-publicly-availab/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-275-statistical-analysis-of-publicly-availab/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/merged_clean.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_clean.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/lag_decay_analysis.py` — NOT invoked by the run-book
    - `code/sentiment_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_dataset_schema.py` — NOT invoked by the run-book
    - `code/tests/test_t013_save_intermediate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_clean.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
