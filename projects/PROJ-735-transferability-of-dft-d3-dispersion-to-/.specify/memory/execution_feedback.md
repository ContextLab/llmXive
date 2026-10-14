# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 declared deliverable(s) absent: data/derived/raw_energies.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-735-transferability-of-dft-d3-dispersion-to-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/derived/raw_energies.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/raw_energies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_energies.py` — IS a run-book command
    - `code/correlate_bulk.py` — IS a run-book command
    - `code/derive_scaling.py` — IS a run-book command
    - `code/generate_reports.py` — IS a run-book command
    - `code/write_scaling_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/raw_energies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
