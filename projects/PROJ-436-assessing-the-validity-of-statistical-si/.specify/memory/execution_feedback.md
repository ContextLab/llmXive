# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW (rc=1); python code/main.py --action visualize --output figures/ (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1

2026-10-24 12:08:55,583 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW -> rc=1

2026-10-24 12:08:56,453 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python code/main.py --action visualize --output figures/ -> rc=1

2026-10-24 12:08:57,320 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python -m pytest tests/ -v -> rc=2
thon/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
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
tests/integration/test_us2_sensitivity.py:29: in <module>
    from main import run_sensitivity_sweep, validate_condition_matrix, generate_tipping_point_report
E   ImportError: cannot import name 'run_sensitivity_sweep' from 'main' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py)
=========================== short test summary info ============================
ERROR tests/integration/test_main_us1.py
ERROR tests/integration/test_us2_sensitivity.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.29s ===============================


