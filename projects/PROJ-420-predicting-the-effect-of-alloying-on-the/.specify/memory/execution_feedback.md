# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/test_contracts.py (rc=4)

## Failing / missing run-book commands

- python code/main.py -> rc=1
t recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/main.py", line 163, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/main.py", line 124, in main
    aggregate_report_context()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/main.py", line 137, in aggregate_report_context
    model_metrics = load_json_safe(str(Path(CONFIG.results) / "model_metrics.json"))
                                       ^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not function

- python -m pytest tests/test_contracts.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the
configfile: pyproject.toml
plugins: platformdirs-4.13.5, cov-7.1.0, anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/test_contracts.py


