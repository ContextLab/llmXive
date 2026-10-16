# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/ -v (rc=3)

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-223-statistical-analysis-of-publicly-availab/code/main.py", line 6, in <module>
    from .ingest import run_ingestion
ImportError: attempted relative import with no known parent package

- python -m pytest tests/ -v -> rc=3
TERNALERROR>     res = hook_impl.function(*args)
INTERNALERROR>           ^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-223-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/_pytest/debugging.py", line 69, in pytest_configure
INTERNALERROR>     import pdb
INTERNALERROR>   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pdb.py", line 77, in <module>
INTERNALERROR>     import code
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-223-statistical-analysis-of-publicly-availab/code/__init__.py", line 12, in <module>
INTERNALERROR>     from . import ingest, model, diagnostics, utils, config, main  # noqa: F401
INTERNALERROR>     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-223-statistical-analysis-of-publicly-availab/code/main.py", line 6, in <module>
INTERNALERROR>     from .ingest import run_ingestion
INTERNALERROR> ImportError: cannot import name 'run_ingestion' from 'code.ingest' (/home/runner/work/llmXive/llmXive/projects/PROJ-223-statistical-analysis-of-publicly-availab/code/ingest.py)

