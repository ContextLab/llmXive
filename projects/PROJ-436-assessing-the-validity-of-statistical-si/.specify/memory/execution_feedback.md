# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW (rc=1); python code/main.py --action visualize --output figures/ (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1

2026-10-24 18:08:35,615 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW -> rc=1

2026-10-24 18:08:36,687 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python code/main.py --action visualize --output figures/ -> rc=1

2026-10-24 18:08:37,801 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python -m pytest tests/ -v -> rc=2
mod = import_path(
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
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
tests/integration/test_main_us1.py:19: in <module>
    from main_us1 import run_single_condition_simulation
code/main_us1.py:21: in <module>
    import openml
E   ModuleNotFoundError: No module named 'openml'
=========================== short test summary info ============================
ERROR tests/integration/test_main_us1.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.32s ===============================


