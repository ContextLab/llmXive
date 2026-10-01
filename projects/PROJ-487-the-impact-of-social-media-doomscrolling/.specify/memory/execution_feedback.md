# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 5 declared deliverable(s) absent: data/processed/aligned_timeseries.csv; data/processed/granger_results.csv; data/processed/stationarity_check.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/aligned_timeseries.csv
- data/processed/granger_results.csv
- data/processed/stationarity_check.csv
- data/raw/google_trends.csv
- data/reports/analysis_report.pdf

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_timeseries.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/save_aligned_data.py` — NOT invoked by the run-book
    - `code/data/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/post_interpolation_check.py` — NOT invoked by the run-book
    - `code/data/analyze.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_timeseries.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/granger_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/analyze.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/granger_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stationarity_check.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/save_aligned_data.py` — NOT invoked by the run-book
    - `code/data/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stationarity_check.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/google_trends.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/utils/update_state.py` — NOT invoked by the run-book
    - `code/data/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/verify_output.py` — NOT invoked by the run-book
    - `code/data/validate_date_range.py` — NOT invoked by the run-book
    - `code/data/verify_cpu_compliance.py` — NOT invoked by the run-book
    - `code/data/verify_data_completeness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/google_trends.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/reports/analysis_report.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/data/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/analyze.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/analysis_report.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
