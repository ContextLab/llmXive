# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m code.run_pipeline --full (rc=1); 2 declared deliverable(s) absent: data/gold_standard/annotations.json; data/raw/commit_pairs.csv

## Failing / missing run-book commands

- python -m code.run_pipeline --full -> rc=1
ready cloned at /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/repos/scikit-learn, pulling latest.
2026-10-17 14:35:20,608 INFO code.data_extraction: Processing repository scikit-learn (https://github.com/scikit-learn/scikit-learn.git)
2026-10-17 14:35:20,623 INFO code.data_extraction: Finished repo scikit-learn: collected 0 rows so far, 0 commits skipped (no doc change).
2026-10-17 14:35:20,623 INFO code.data_extraction: Repo already cloned at /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/repos/pandas, pulling latest.
2026-10-17 14:35:20,975 INFO code.data_extraction: Processing repository pandas (https://github.com/pandas-dev/pandas.git)
2026-10-17 14:35:20,990 INFO code.data_extraction: Finished repo pandas: collected 0 rows so far, 0 commits skipped (no doc change).
2026-10-17 14:35:20,990 INFO code.data_extraction: Extraction finished: 0 rows collected, 0 commits skipped (no doc change).
2026-10-17 14:35:20,990 ERROR code.data_extraction: Insufficient commit‑pair rows collected: 0 (required 500).
2026-10-17 14:35:20,990 ERROR __main__: Data extraction failed with exit code 1


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
