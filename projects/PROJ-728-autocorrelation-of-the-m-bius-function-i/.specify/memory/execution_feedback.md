# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py (rc=-1); python code/viz.py --run (rc=1); python -m pytest tests/integration/ (rc=-1); 2 declared deliverable(s) absent: data/processed/autocorr_stats.csv; data/processed/uniformity_test.json

## Failing / missing run-book commands

- python code/main.py -> rc=-1
usage: main.py [-h] [--max MAX] [--output OUTPUT] [--generate]

Generate the Möbius function array up to N and save as a NumPy .npy file.

options:
  -h, --help       show this help message and exit
  --max MAX        Maximum integer N (inclusive) for which to compute μ(n).
                   Default: 10,000,000.
  --output OUTPUT  Path to write the NumPy .npy file. Default:
                   data/raw/mobius_array.npy
  --generate       If set, compute the array and write it to the output path.
Saved Möbius array of length 10000000 to data/raw/mobius_array.npy
Möbius array written to: data/raw/mobius_array.npy
Window start indices written to: data/raw/window_starts.json
Demo autocorrelation written to data/results/demo_autocorr.csv: start=44622, L=1000, h=1, autocorrelation=-0.047047047047
Full autocorrelation matrix written to data/processed/autocorr_raw.csv


[TIMEOUT after 120s]
- python code/viz.py --run -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/viz.py", line 109, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/viz.py", line 100, in main
    raise FileNotFoundError(f"Required CSV not found: {INPUT_CSV}")
FileNotFoundError: Required CSV not found: data/processed/autocorr_stats.csv

- python -m pytest tests/integration/ -> rc=-1
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 2 items

tests/integration/test_demo_pipeline.py .                                [ 50%]
tests/integration/test_full_pipeline.py 

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/processed/autocorr_stats.csv
- data/processed/uniformity_test.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/autocorr_stats.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fdr_correction.py` — NOT invoked by the run-book
    - `code/null_distribution.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/uniformity_test.py` — NOT invoked by the run-book
    - `code/viz.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/autocorr_stats.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/uniformity_test.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/uniformity_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/uniformity_test.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
