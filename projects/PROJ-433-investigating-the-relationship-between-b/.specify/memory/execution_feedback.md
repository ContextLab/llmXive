# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/preprocess.py --n-subjects 10 --mode cpu`
  - script usage: `preprocess.py [-h] --subject SUBJECT [--mode {ci,cluster}]`
  - argparse error: `preprocess.py: error: argument --mode: invalid choice: 'cpu' (choose from 'ci', 'cluster')`
- run-book command: `python code/metrics.py --window-size 30 --step-size 5 --atlas schaefer-200`
  - script usage: `metrics.py [-h] --subject SUBJECT --input-dir INPUT_DIR`
  - argparse error: `metrics.py: error: the following arguments are required: --subject, --input-dir`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/preprocess.py --n-subjects 10 --mode cpu (rc=2); python code/metrics.py --window-size 30 --step-size 5 --atlas schaefer-200 (rc=2); python code/analysis.py --permutations 1000 --seed 42 (rc=1); 3 declared deliverable(s) absent: data/processed/metrics_aggregated.tsv; data/results/permutation_report.png; data/results/permutation_results.tsv

## Failing / missing run-book commands

- python code/preprocess.py --n-subjects 10 --mode cpu -> rc=2

usage: preprocess.py [-h] --subject SUBJECT [--mode {ci,cluster}]
preprocess.py: error: argument --mode: invalid choice: 'cpu' (choose from 'ci', 'cluster')

- python code/metrics.py --window-size 30 --step-size 5 --atlas schaefer-200 -> rc=2

usage: metrics.py [-h] --subject SUBJECT --input-dir INPUT_DIR
                  [--output-dir OUTPUT_DIR] [--window-size WINDOW_SIZE]
                  [--step-size STEP_SIZE]
metrics.py: error: the following arguments are required: --subject, --input-dir

- python code/analysis.py --permutations 1000 --seed 42 -> rc=1

ERROR:__main__:Failed to load data for analysis: attempted relative import with no known parent package
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-433-investigating-the-relationship-between-b/code/analysis.py", line 258, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-433-investigating-the-relationship-between-b/code/analysis.py", line 212, in main
    metrics_dict, behavior_dict = load_metrics_and_behavioral_data()
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-433-investigating-the-relationship-between-b/code/analysis.py", line 43, in load_metrics_and_behavioral_data
    from .analysis import load_metrics_and_behavioral_data as _original_load
ImportError: attempted relative import with no known parent package

- python -m pytest tests/ -v -> rc=2
:92
code/.venv/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92
code/.venv/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92
code/.venv/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92
  /home/runner/work/llmXive/llmXive/projects/PROJ-433-investigating-the-relationship-between-b/code/.venv/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

code/.venv/lib/python3.11/site-packages/matplotlib/_mathtext.py:45
  /home/runner/work/llmXive/llmXive/projects/PROJ-433-investigating-the-relationship-between-b/code/.venv/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_download.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 1 error in 0.76s =========================



## Declared deliverables still missing

- data/processed/metrics_aggregated.tsv
- data/results/permutation_report.png
- data/results/permutation_results.tsv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics_aggregated.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_aggregated.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_report.png` is declared but was NOT written. Scripts referencing it:
    - `code/log_permutation_report_creation.py` — NOT invoked by the run-book
    - `code/permutation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_report.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_results.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/permutation_report.py` — NOT invoked by the run-book
    - `code/save_permutation_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_results.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
