# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/analysis/stats.py --output results/analysis_results.csv; python src/analysis/visualize.py --input results/analysis_results.csv; 4 command(s) failed: python code/src/data/download.py --check-only (rc=1); python code/src/data/preprocess.py --subjects 50 --mode cpu (rc=1); python src/analysis/connectivity.py --subjects 50 (rc=1); 1 declared deliverable(s) absent: data/preprocessing/run_log.json

## Failing / missing run-book commands

- python code/src/data/download.py --check-only -> rc=1

2026-10-17 04:37:22,218 INFO __main__: Fetching file list for dataset ds000233...
2026-10-17 04:37:22,529 ERROR __main__: Pipeline failed: Cannot access OpenNeuro dataset ds000233 API: 404 Client Error: Not Found for url: https://openneuro.org/api/datasets/ds000233/files

- python code/src/data/preprocess.py --subjects 50 --mode cpu -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/code/src/data/preprocess.py", line 295, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/code/src/data/preprocess.py", line 272, in main
    subjects = [d.name.replace("sub-", "") for d in (base_path / "preprocessing").iterdir() 
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/code/src/data/preprocess.py", line 272, in <listcomp>
    subjects = [d.name.replace("sub-", "") for d in (base_path / "preprocessing").iterdir() 
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 931, in iterdir
    for name in os.listdir(self):
                ^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/preprocessing'

- python src/analysis/connectivity.py --subjects 50 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/src/analysis/connectivity.py", line 9, in <module>
    from nilearn import input_data
ImportError: cannot import name 'input_data' from 'nilearn' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-232-investigating-the-relationship-between-b/lib/python3.11/site-packages/nilearn/__init__.py)

- python src/analysis/stats.py --output results/analysis_results.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-232-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/src/analysis/stats.py': [Errno 2] No such file or directory

- python src/analysis/visualize.py --input results/analysis_results.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-232-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/src/analysis/visualize.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=4

ERROR: /home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/pyproject.toml: Cannot overwrite a value (at line 96, column 25)



## Declared deliverables still missing

- data/preprocessing/run_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/preprocessing/run_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/connectivity.py` — NOT invoked by the run-book
    - `code/src/data/preprocess.py` — IS a run-book command
    - `code/tests/unit/test_preprocess_motion_exclusion.py` — NOT invoked by the run-book
    - `src/analysis/connectivity.py` — IS a run-book command
  Make ONE of these WRITE `data/preprocessing/run_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
