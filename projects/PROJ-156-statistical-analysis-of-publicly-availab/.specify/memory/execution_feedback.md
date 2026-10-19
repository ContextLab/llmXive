# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest code/tests/ (rc=2); 3 declared deliverable(s) absent: data/checkpoints/fetch_checkpoint.json; data/processed/distribution_fits.csv; data/processed/run_records.csv

## Failing / missing run-book commands

- python -m pytest code/tests/ -> rc=2
ostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_pressure.py:11: in <module>
    from scripts.utils.pressure import calculate_lagged_pressure
code/scripts/utils/__init__.py:4: in <module>
    from .checkpoint import save_checkpoint, load_checkpoint, delete_checkpoint, ensure_checkpoint_dir, get_checkpoint_path
E   ImportError: cannot import name 'delete_checkpoint' from 'scripts.utils.checkpoint' (/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/utils/checkpoint.py)
=========================== short test summary info ============================
ERROR code/tests/test_checkpoint.py
ERROR code/tests/test_distribution_fitting.py
ERROR code/tests/test_fetch.py
ERROR code/tests/test_fetch_checkpoint.py
ERROR code/tests/test_models.py
ERROR code/tests/test_pagination.py
ERROR code/tests/test_preprocess_checkpoint.py
ERROR code/tests/test_pressure.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 0.77s ===============================



## Declared deliverables still missing

- data/checkpoints/fetch_checkpoint.json
- data/processed/distribution_fits.csv
- data/processed/run_records.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checkpoints/fetch_checkpoint.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fetch_data.py` — NOT invoked by the run-book
    - `code/tests/test_fetch_checkpoint.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checkpoints/fetch_checkpoint.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/distribution_fits.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_distributions.py` — NOT invoked by the run-book
    - `code/scripts/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/utils/bonferroni.py` — NOT invoked by the run-book
    - `code/scripts/validate_distribution_fits.py` — NOT invoked by the run-book
    - `code/tests/test_distribution_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_fits.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/run_records.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_distributions.py` — NOT invoked by the run-book
    - `code/scripts/fit_mixed_effects.py` — NOT invoked by the run-book
    - `code/scripts/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/preprocess.py` — NOT invoked by the run-book
    - `code/scripts/utils/pressure.py` — NOT invoked by the run-book
    - `code/tests/test_distribution_fitting.py` — NOT invoked by the run-book
    - `code/tests/test_models.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/run_records.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
