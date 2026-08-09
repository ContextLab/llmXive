# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python code/src/main.py --step check_data; python code/src/main.py --step ingest; python code/src/main.py --step analyze; 3 declared deliverable(s) absent: data/processed/cleaned_microbiome_sleep.csv; data/processed/correlation_results.csv; data/processed/ingestion_report.json

## Failing / missing run-book commands

- python code/src/main.py --step check_data -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py': [Errno 2] No such file or directory
- python code/src/main.py --step ingest -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py': [Errno 2] No such file or directory
- python code/src/main.py --step analyze -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py': [Errno 2] No such file or directory
- python code/src/main.py --step viz -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py': [Errno 2] No such file or directory
- python code/src/main.py --step all -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/cleaned_microbiome_sleep.csv
- data/processed/correlation_results.csv
- data/processed/ingestion_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_microbiome_sleep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_t030_save_plots.py` — NOT invoked by the run-book
    - `code/scripts/run_t024_save_results.py` — NOT invoked by the run-book
    - `code/scripts/run_t036_validate_quickstart.py` — NOT invoked by the run-book
    - `code/src/ingestion_optimized.py` — NOT invoked by the run-book
    - `code/src/ingestion.py` — NOT invoked by the run-book
    - `code/src/viz.py` — NOT invoked by the run-book
    - `code/src/diversity.py` — NOT invoked by the run-book
    - `code/src/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_microbiome_sleep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_correlation_io.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t031_report.py` — NOT invoked by the run-book
    - `code/tests/unit/test_viz_t030.py` — NOT invoked by the run-book
    - `code/tests/unit/test_viz_t027.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t030_plots.py` — NOT invoked by the run-book
    - `code/scripts/run_t030_save_plots.py` — NOT invoked by the run-book
    - `code/scripts/run_t024_save_results.py` — NOT invoked by the run-book
    - `code/scripts/run_t025b_blocked_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingestion_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_t031_report.py` — NOT invoked by the run-book
    - `code/scripts/run_t025b_blocked_report.py` — NOT invoked by the run-book
    - `code/scripts/run_t036_validate_quickstart.py` — NOT invoked by the run-book
    - `code/scripts/run_t031_generate_report.py` — NOT invoked by the run-book
    - `code/src/ingestion_optimized.py` — NOT invoked by the run-book
    - `code/src/report_final.py` — NOT invoked by the run-book
    - `code/src/report.py` — NOT invoked by the run-book
    - `code/src/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ingestion_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
