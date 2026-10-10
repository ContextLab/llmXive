# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/cohort_merged.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
2026-10-10 06:17:48,104 - __main__ - INFO - Starting full analysis pipeline...
2026-10-10 06:17:48,104 - __main__ - INFO - Step 1: Running data ingestion...
2026-10-10 06:17:48,104 - ingestion - INFO - Starting data ingestion pipeline...
2026-10-10 06:17:48,104 - __main__ - ERROR - Pipeline failed: AGP raw data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/data/raw/agp_metadata.csv. Ensure T011 has completed.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/main.py", line 40, in main
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/ingestion.py", line 272, in main
    raise FileNotFoundError(f"AGP raw data not found at {agp_raw_path}. Ensure T011 has completed.")
FileNotFoundError: AGP raw data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/data/raw/agp_metadata.csv. Ensure T011 has completed.


- python code/main.py -> rc=1
2026-10-10 06:17:48,419 - __main__ - INFO - Starting full analysis pipeline...
2026-10-10 06:17:48,419 - __main__ - INFO - Step 1: Running data ingestion...
2026-10-10 06:17:48,419 - ingestion - INFO - Starting data ingestion pipeline...
2026-10-10 06:17:48,419 - __main__ - ERROR - Pipeline failed: AGP raw data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/data/raw/agp_metadata.csv. Ensure T011 has completed.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/main.py", line 40, in main
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/ingestion.py", line 272, in main
    raise FileNotFoundError(f"AGP raw data not found at {agp_raw_path}. Ensure T011 has completed.")
FileNotFoundError: AGP raw data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/data/raw/agp_metadata.csv. Ensure T011 has completed.



## Declared deliverables still missing

- data/processed/cohort_merged.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cohort_merged.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/diversity.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/validation.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cohort_merged.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
