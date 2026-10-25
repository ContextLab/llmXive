# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m pytest -q (rc=1); python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 (rc=1); python -m code.utils.validate --check-all (rc=1)

## Failing / missing run-book commands

- python -m pytest -q -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 148, in _get_module_details
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pytest/__init__.py", line 29, in <module>
    from _pytest.legacypath import TempdirFactory
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/legacypath.py", line 31, in <module>
    from _pytest.pytester import HookRecorder
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/pytester.py", line 650, in <module>
    class Pytester:
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/pytester.py", line 1331, in Pytester
    stdout: Union[int, TextIO] = subprocess.PIPE,
                                 ^^^^^^^^^^^^^^^
AttributeError: module 'subprocess' has no attribute 'PIPE'

- python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/main.py", line 10, in <module>
    from data.generator import (
ImportError: cannot import name 'generate_coupled_lorenz_trajectory' from 'data.generator' (/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/data/generator.py)

- python -m code.utils.validate --check-all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-101-quantifying-the-influence-of-initial-con/bin/python: No module named code.utils.validate

