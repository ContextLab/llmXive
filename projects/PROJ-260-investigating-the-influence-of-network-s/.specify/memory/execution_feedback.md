# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.cli.main run --config config/default.yaml (rc=1); python -m pytest tests/ -v --cov=src (rc=2); 3 declared deliverable(s) absent: data/derived/reference/kappa_values.csv; data/metadata/manual_reference.json; data/metadata/valid_sources.json

## Failing / missing run-book commands

- python -m src.cli.main run --config config/default.yaml -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-260-investigating-the-influence-of-network-s/code/.venv/bin/python: No module named src.cli.main

- python -m pytest tests/ -v --cov=src -> rc=2
b.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    exec(co, module.__dict__)
tests/unit/test_utils.py:13: in <module>
    from src.lib.utils import (
E   ModuleNotFoundError: No module named 'src.lib'
=========================== short test summary info ============================
ERROR tests/contract/test_topology_schema.py
ERROR tests/unit/test_registry_generator.py
ERROR tests/unit/test_registry_validator.py
ERROR tests/unit/test_simulation_box.py
ERROR tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 1.69s ===============================



## Declared deliverables still missing

- data/derived/reference/kappa_values.csv
- data/metadata/manual_reference.json
- data/metadata/valid_sources.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/reference/kappa_values.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/services/data_aggregator.py` — NOT invoked by the run-book
    - `code/src/services/independence_validator.py` — NOT invoked by the run-book
    - `code/src/services/kappa_ingester.py` — NOT invoked by the run-book
    - `code/src/services/reference_generator.py` — NOT invoked by the run-book
    - `code/tests/integration/test_data_aggregator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_kappa_ingester.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/reference/kappa_values.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metadata/manual_reference.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_manual_reference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/manual_reference.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metadata/valid_sources.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/services/kappa_ingester.py` — NOT invoked by the run-book
    - `code/tests/unit/test_kappa_ingester.py` — NOT invoked by the run-book
    - `src/services/registry_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/valid_sources.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
