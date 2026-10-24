# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/main.py; python code/main.py --n-simulations 500 --thresholds "-1 -0.5 0 0.5 1"; python code/main.py --dry-run; 2 declared deliverable(s) absent: data/processed/coverage_report.json; data/processed/map_stats.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-352-statistical-analysis-of-early-universe-c/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-352-statistical-analysis-of-early-universe-c/code/main.py': [Errno 2] No such file or directory

- python code/main.py --n-simulations 500 --thresholds "-1 -0.5 0 0.5 1" -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-352-statistical-analysis-of-early-universe-c/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-352-statistical-analysis-of-early-universe-c/code/main.py': [Errno 2] No such file or directory

- python code/main.py --dry-run -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-352-statistical-analysis-of-early-universe-c/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-352-statistical-analysis-of-early-universe-c/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/coverage_report.json
- data/processed/map_stats.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/coverage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/coverage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/coverage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/map_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/map_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
