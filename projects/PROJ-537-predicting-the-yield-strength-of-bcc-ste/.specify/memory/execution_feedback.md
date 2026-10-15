# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 declared deliverable(s) absent: data/results/output.json; data/results/shap_summary.png; data/results/stability_distribution.png

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/results/output.json
- data/results/shap_summary.png
- data/results/stability_distribution.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/output.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion/fetch_dft.py` — NOT invoked by the run-book
    - `code/ingestion/fetch_experimental.py` — NOT invoked by the run-book
    - `code/ingestion/finalize_dataset.py` — NOT invoked by the run-book
    - `code/ingestion/generate_checksums.py` — NOT invoked by the run-book
    - `code/ingestion/merge_and_filter.py` — NOT invoked by the run-book
    - `code/ingestion/update_state.py` — NOT invoked by the run-book
    - `code/interpretability/bootstrap_stability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/output.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_summary.png` is declared but was NOT written. Scripts referencing it:
    - `code/interpretability/plot_results.py` — NOT invoked by the run-book
    - `code/interpretability/shap_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/shap_summary.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_distribution.png` is declared but was NOT written. Scripts referencing it:
    - `code/interpretability/plot_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_distribution.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
