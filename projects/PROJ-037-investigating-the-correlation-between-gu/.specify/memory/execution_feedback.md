# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/main.py; python code/main.py; 4 declared deliverable(s) absent: data/outputs/correlation_results.csv; data/outputs/heatmap.png; data/outputs/pcoa_sleep_quality.png

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/main.py': [Errno 2] No such file or directory
- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-037-investigating-the-correlation-between-gu/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/outputs/correlation_results.csv
- data/outputs/heatmap.png
- data/outputs/pcoa_sleep_quality.png
- data/processed/cohort_merged.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/outputs/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/report_results.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/outputs/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/outputs/heatmap.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/outputs/heatmap.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/outputs/pcoa_sleep_quality.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/outputs/pcoa_sleep_quality.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cohort_merged.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/diversity.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cohort_merged.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
