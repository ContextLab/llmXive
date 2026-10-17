# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.run_pipeline --full (rc=1); python -m pytest tests/quickstart_test.py (rc=4)

## Failing / missing run-book commands

- python -m code.run_pipeline --full -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 74, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 63, in main
    raise NotImplementedError(
NotImplementedError: the full pipeline is implemented by tasks T002-T010; use --sample for the Phase-0 smoke test

- python -m pytest tests/quickstart_test.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/quickstart_test.py


