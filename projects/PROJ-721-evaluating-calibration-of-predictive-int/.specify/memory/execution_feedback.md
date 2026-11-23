# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --subset-size 1000 --seed 42 (rc=1); python code/main.py --subset-size 10 --seed 42 (rc=1); python -m pytest tests/contract/ (rc=2)

## Failing / missing run-book commands

- python code/main.py --subset-size 1000 --seed 42 -> rc=1

2026-10-09 03:21:31,357 - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Non-scalable fonts are not supported
2026-10-09 03:21:31,371 - INFO - generated new fontManager
2026-10-09 03:21:31,474 - ERROR - Importing plotly failed. Interactive plots will not work.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-721-evaluating-calibration-of-predictive-int/code/main.py", line 30, in <module>
    logging.FileHandler('state/pipeline.log')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-721-evaluating-calibration-of-predictive-int/state/pipeline.log'

- python code/main.py --subset-size 10 --seed 42 -> rc=1

2026-10-09 03:21:32,552 - ERROR - Importing plotly failed. Interactive plots will not work.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-721-evaluating-calibration-of-predictive-int/code/main.py", line 30, in <module>
    logging.FileHandler('state/pipeline.log')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-721-evaluating-calibration-of-predictive-int/state/pipeline.log'

- python -m pytest tests/contract/ -> rc=2
test_schema_validation.py:9: in <module>
    from jsonschema import validate, ValidationError
E   ModuleNotFoundError: No module named 'jsonschema'
_______________ ERROR collecting tests/contract/test_schemas.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-721-evaluating-calibration-of-predictive-int/tests/contract/test_schemas.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/contract/test_schemas.py:8: in <module>
    from jsonschema import validate, ValidationError, Draft7Validator
E   ModuleNotFoundError: No module named 'jsonschema'
=========================== short test summary info ============================
ERROR tests/contract/test_schema_validation.py
ERROR tests/contract/test_schemas.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.26s ===============================


