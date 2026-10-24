# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW (rc=1); python code/main.py --action visualize --output figures/ (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 11, in <module>
    from config import SimulationConfig, load_config, validate_config, config_to_dict
ImportError: cannot import name 'config_to_dict' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/config.py)

- python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 11, in <module>
    from config import SimulationConfig, load_config, validate_config, config_to_dict
ImportError: cannot import name 'config_to_dict' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/config.py)

- python code/main.py --action visualize --output figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 11, in <module>
    from config import SimulationConfig, load_config, validate_config, config_to_dict
ImportError: cannot import name 'config_to_dict' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/config.py)

- python -m pytest tests/ -v -> rc=2
me[level:], package, level)
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
code/main.py:11: in <module>
    from config import SimulationConfig, load_config, validate_config, config_to_dict
E   ImportError: cannot import name 'config_to_dict' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/config.py)
=========================== short test summary info ============================
ERROR tests/integration/test_main_us1.py
ERROR tests/integration/test_us2_sensitivity.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.05s ===============================


