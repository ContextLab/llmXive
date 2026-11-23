# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/ (rc=2); 3 declared deliverable(s) absent: data/processed/excluded_session_ids.csv; data/processed/session_validation_metrics.json; data/processed/ventral_striatum_activation.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
S ROI Contract ---
2026-10-12 14:20:48,390 - __main__ - INFO - --- Phase 2: Generate VS ROI Contract completed successfully ---
2026-10-12 14:20:48,390 - __main__ - INFO - --- Starting Phase 2: Generate Exclusion Contract ---
2026-10-12 14:20:48,391 - __main__ - ERROR - --- Phase 2: Generate Exclusion Contract failed: VS ROI must contain 'center' key with [x, y, z] coordinates ---
2026-10-12 14:20:48,393 - __main__ - ERROR - Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/main.py", line 37, in run_stage
    module.main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/create_power_excl_vs_json.py", line 144, in main
    overlapping_nodes = find_overlapping_nodes(
                        ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/create_power_excl_vs_json.py", line 59, in find_overlapping_nodes
    raise ValueError("VS ROI must contain 'center' key with [x, y, z] coordinates")
ValueError: VS ROI must contain 'center' key with [x, y, z] coordinates


- python -m pytest tests/ -> rc=2
cting tests/unit/test_write_excluded_session_ids.py ________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/tests/unit/test_write_excluded_session_ids.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_write_excluded_session_ids.py:17: in <module>
    from code.write_excluded_session_ids import write_excluded_subjects_csv, run_validation_if_needed, load_validation_state
E   ImportError: cannot import name 'run_validation_if_needed' from 'code.write_excluded_session_ids' (/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/write_excluded_session_ids.py)
=========================== short test summary info ============================
ERROR tests/unit/test_write_excluded_session_ids.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.62s ===============================



## Declared deliverables still missing

- data/processed/excluded_session_ids.csv
- data/processed/session_validation_metrics.json
- data/processed/ventral_striatum_activation.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/excluded_session_ids.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/session_validation_metrics.py` — NOT invoked by the run-book
    - `code/write_excluded_session_ids.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/excluded_session_ids.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/session_validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/session_validation_metrics.py` — NOT invoked by the run-book
    - `code/verify_session_validation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/session_validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ventral_striatum_activation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_vs_activation.py` — NOT invoked by the run-book
    - `code/verify_vs_activation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ventral_striatum_activation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
