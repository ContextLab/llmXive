# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 4 declared deliverable(s) absent: data/derived/analysis_results.json; data/derived/master_dataset.csv; data/derived/sensitivity_analysis.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/derived/analysis_results.json
- data/derived/master_dataset.csv
- data/derived/sensitivity_analysis.json
- data/derived/stratified_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/derive_analysis_results.py` — NOT invoked by the run-book
    - `code/optimize_performance.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/report_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/master_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/derive_analysis_results.py` — NOT invoked by the run-book
    - `code/derive_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/generate_master_dataset.py` — NOT invoked by the run-book
    - `code/ingest.py` — IS a run-book command
    - `code/optimize_performance.py` — NOT invoked by the run-book
    - `code/report_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/master_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/derive_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/stratified_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/stratified_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
