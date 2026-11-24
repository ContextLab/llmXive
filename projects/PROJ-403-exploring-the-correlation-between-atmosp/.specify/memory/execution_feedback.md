# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.cli.run_analysis --full (rc=2); python -m src.cli.run_analysis --phase 6 # executes only phase 6 (sensitivity) (rc=2); python -m pytest -q (rc=2)

## Failing / missing run-book commands

- python -m src.cli.run_analysis --full -> rc=2

Usage: python -m src.cli.run_analysis [OPTIONS]
Try 'python -m src.cli.run_analysis --help' for help.

Error: No such option '--full'.

- python -m src.cli.run_analysis --phase 6 # executes only phase 6 (sensitivity) -> rc=2

Usage: python -m src.cli.run_analysis [OPTIONS]
Try 'python -m src.cli.run_analysis --help' for help.

Error: No such option '--phase'. Did you mean '--help'?

- python -m pytest -q -> rc=2
6971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_analysis.py
ERROR tests/unit/test_download.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 2 errors in 1.20s ========================


- python -m pytest tests/contract/test_correlation_schema.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-403-exploring-the-correlation-between-atmosp/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-403-exploring-the-correlation-between-atmosp
configfile: pyproject.toml
plugins: cov-7.1.0
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_correlation_schema.py


