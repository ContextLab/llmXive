# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.run_pipeline  --seed 42  --max-pairs 200  --confidence-thresholds 0.0 0.5 0.9 (rc=1); 2 declared deliverable(s) absent: data/checksums.json; data/raw/devign/devign.csv

## Failing / missing run-book commands

- python -m src.run_pipeline  --seed 42  --max-pairs 200  --confidence-thresholds 0.0 0.5 0.9 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/bin/python: Error while finding module specification for 'src.run_pipeline' (ModuleNotFoundError: No module named 'src')


## Declared deliverables still missing

- data/checksums.json
- data/raw/devign/devign.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_devign.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/devign/devign.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_devign.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/devign/devign.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
