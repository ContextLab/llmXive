# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m analysis.metrics --input-dir ../../data/raw --output-file ../../data/processed/metrics.csv`
  - script usage: `metrics.py [-h] snapshot`
  - argparse error: `metrics.py: error: unrecognized arguments: --input-dir --output-file ../../data/processed/metrics.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m simulation.runner --N 10000 --Omega 0.5 --epsilon_dd 0.5 --seed 42 --output-dir ../../data/raw (rc=1); python -m simulation.runner --grid-config ../../specs/001-gene-regulation/grid_config.json --repeats 5 --output-dir ../../data/raw (rc=1); python -m analysis.metrics --input-dir ../../data/raw --output-file ../../data/processed/metrics.csv (rc=2); 2 declared deliverable(s) absent: data/aggregated/statistical_results.json; figures/phase_map.png

## Failing / missing run-book commands

- python -m simulation.runner --N 10000 --Omega 0.5 --epsilon_dd 0.5 --seed 42 --output-dir ../../data/raw -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-133-investigating-the-stability-of-rotating-/code/simulation/runner.py", line 14, in <module>
    from utils.logger import get_logger, info, warning, error, debug
ImportError: cannot import name 'info' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-133-investigating-the-stability-of-rotating-/code/utils/logger.py)

- python -m simulation.runner --grid-config ../../specs/001-gene-regulation/grid_config.json --repeats 5 --output-dir ../../data/raw -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-133-investigating-the-stability-of-rotating-/code/simulation/runner.py", line 14, in <module>
    from utils.logger import get_logger, info, warning, error, debug
ImportError: cannot import name 'info' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-133-investigating-the-stability-of-rotating-/code/utils/logger.py)

- python -m analysis.metrics --input-dir ../../data/raw --output-file ../../data/processed/metrics.csv -> rc=2

usage: metrics.py [-h] snapshot
metrics.py: error: unrecognized arguments: --input-dir --output-file ../../data/processed/metrics.csv

- python -m pytest tests/ -> rc=2
vortex_stats.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_zero_vortex_stats.py:21: in <module>
    from statistics.aggregators import calculate_point_statistics, determine_stability_status
E   ImportError: cannot import name 'calculate_point_statistics' from 'statistics.aggregators' (/home/runner/work/llmXive/llmXive/projects/PROJ-133-investigating-the-stability-of-rotating-/code/statistics/aggregators.py)
=========================== short test summary info ============================
ERROR tests/contract/test_metrics_schema.py
ERROR tests/contract/test_repro.sh.py
ERROR tests/integration/test_aggregation.py
ERROR tests/integration/test_single_run.py
ERROR tests/unit/test_gpe_solver.py
ERROR tests/unit/test_initial_conditions.py
ERROR tests/unit/test_statistics.py
ERROR tests/unit/test_zero_vortex_stats.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 1.07s ===============================



## Declared deliverables still missing

- data/aggregated/statistical_results.json
- figures/phase_map.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/aggregated/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/statistics/aggregators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/phase_map.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz/plotter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/phase_map.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
