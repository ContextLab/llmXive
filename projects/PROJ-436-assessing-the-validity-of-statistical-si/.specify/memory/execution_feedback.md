# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW (rc=1); python code/main.py --action visualize --output figures/ (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 23, in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'

- python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 23, in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'

- python code/main.py --action visualize --output figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 23, in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'

- python -m pytest tests/ -v -> rc=2
n/test_us2_sensitivity.py __________
tests/integration/test_us2_sensitivity.py:29: in <module>
    from main import run_sensitivity_sweep, validate_condition_matrix, generate_tipping_point_report
code/main.py:23: in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1181: in __init__
    StreamHandler.__init__(self, self._open())
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1213: in _open
    return open_func(self.baseFilename, self.mode,
E   FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'
=========================== short test summary info ============================
ERROR tests/integration/test_us2_sensitivity.py - FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.24s ===============================


