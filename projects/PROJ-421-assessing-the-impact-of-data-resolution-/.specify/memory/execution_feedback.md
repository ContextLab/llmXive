# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python main.py --action ingest --state CO --output data/derived/; python main.py --action analyze --class-id 41 --permutations 1000 --simulations 1000; python main.py --action plot --output figures/power_curve.png; 1 declared deliverable(s) absent: data/results/morans_i_results.csv

## Failing / missing run-book commands

- python main.py --action ingest --state CO --output data/derived/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-421-assessing-the-impact-of-data-resolution-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/main.py': [Errno 2] No such file or directory

- python main.py --action analyze --class-id 41 --permutations 1000 --simulations 1000 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-421-assessing-the-impact-of-data-resolution-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/main.py': [Errno 2] No such file or directory

- python main.py --action plot --output figures/power_curve.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-421-assessing-the-impact-of-data-resolution-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/results/morans_i_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/morans_i_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/full_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/morans_i_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
