# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m code.run_pipeline --full (rc=-1); 2 declared deliverable(s) absent: data/gold_standard/annotations.json; data/raw/commit_pairs.csv

## Failing / missing run-book commands

- python -m code.run_pipeline --full -> rc=-1
Power analysis: estimated power for n=500 is 1.0000; exploratory=False
Wrote /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/results/power_report.md

2026-10-17 15:19:29,772 INFO __main__: Running full pipeline
2026-10-17 15:19:29,772 INFO __main__: Running power analysis...
2026-10-17 15:20:12,714 INFO code.power_analysis: Power analysis complete: power=1.0000 (n=500), exploratory=False
2026-10-17 15:20:12,714 INFO __main__: Running data extraction...
2026-10-17 15:20:12,714 INFO code.data_extraction: Repo already cloned at /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/repos/requests, pulling latest.

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/gold_standard/annotations.json
- data/raw/commit_pairs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/gold_standard/annotations.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/generation.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
    - `code/power_analysis.py` — IS a run-book command
    - `code/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/gold_standard/annotations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/commit_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/commit_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
