# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/loaders.py --output data/processed/ (rc=1); python code/main.py --permutations [variable] --threshold 0.3 --sweep (rc=1)

## Failing / missing run-book commands

- python code/loaders.py --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 18, in <module>
    logging.FileHandler('output/logs/loader.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/output/logs/loader.log'
- python code/main.py --permutations [variable] --threshold 0.3 --sweep -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/main.py", line 16, in <module>
    from loaders import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 18, in <module>
    logging.FileHandler('output/logs/loader.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/output/logs/loader.log'
