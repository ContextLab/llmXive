# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_simulation.py --generate --seed [RANDOM_SEED] --count 500; python src/cli/run_simulation.py --execute --mode full; python src/cli/run_simulation.py --execute --mode compressed --depths 1,2,3,4,5,6,7,8,9,10; 1 command(s) failed: python -m pytest tests/ -v (rc=2); 2 declared deliverable(s) absent: data/raw/workflows.json; data/results/tradeoff_curve.csv

## Failing / missing run-book commands

- python src/cli/run_simulation.py --generate --seed [RANDOM_SEED] --count 500 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode full -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode compressed --depths 1,2,3,4,5,6,7,8,9,10 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --analyze --bootstraps [sufficient_resampling_iterations] -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
ckages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_tradeoff_model.py:9: in <module>
    from analysis.tradeoff_model import logistic_function, fit_tradeoff_curve, load_processed_logs
E   ImportError: cannot import name 'logistic_function' from 'analysis.tradeoff_model' (/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/analysis/tradeoff_model.py)
=========================== short test summary info ============================
ERROR tests/security/test_network_isolation.py - NameError: name 'List' is no...
ERROR tests/unit/test_finalize_state.py
ERROR tests/unit/test_pm4py_integration.py
ERROR tests/unit/test_reproducibility.py
ERROR tests/unit/test_state_manager.py
ERROR tests/unit/test_state_registry.py
ERROR tests/unit/test_tradeoff_model.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 1.77s ===============================



## Declared deliverables still missing

- data/raw/workflows.json
- data/results/tradeoff_curve.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/workflows.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/tradeoff_model.py` — NOT invoked by the run-book
    - `code/analysis/vif_analyzer.py` — NOT invoked by the run-book
    - `code/engines/compressed_context.py` — NOT invoked by the run-book
    - `code/engines/full_context.py` — NOT invoked by the run-book
    - `code/engines/invalid_workflow_filter.py` — NOT invoked by the run-book
    - `code/generators/synthetic_workflow.py` — NOT invoked by the run-book
    - `code/services/executor.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/workflows.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/tradeoff_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_regression_data.py` — NOT invoked by the run-book
    - `code/generate_paper_handoff.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
    - `code/utils/verify_data_consistency.py` — NOT invoked by the run-book
    - `code/utils/verify_invalid_workflow_exclusion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/tradeoff_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
