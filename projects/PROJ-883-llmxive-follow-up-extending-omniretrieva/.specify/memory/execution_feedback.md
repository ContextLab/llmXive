# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest -v (rc=2); 1 declared deliverable(s) absent: data/processed/generation_log.json

## Failing / missing run-book commands

- python -m pytest -v -> rc=2
dule_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_synthetic_query.py:20: in <module>
    from generators.synthetic_query import SyntheticQueryGenerator
E   ModuleNotFoundError: No module named 'generators.synthetic_query'
=========================== short test summary info ============================
ERROR tests/integration/test_latency_pipeline.py
ERROR tests/integration/test_throttling_abort.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_query_gen.py
ERROR tests/unit/test_synthetic_query.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 0.57s ===============================



## Declared deliverables still missing

- data/processed/generation_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/generation_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark_runner.py` — NOT invoked by the run-book
    - `code/query_generator.py` — NOT invoked by the run-book
    - `code/router/sut_router.py` — NOT invoked by the run-book
    - `code/transform_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/generation_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
