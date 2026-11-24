# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m pytest -q (rc=1); python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 (rc=-1); python -m code.utils.validate --check-all (rc=1)

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

- python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 -> rc=-1

2026-10-26 01:40:16,765 WARNING __main__: Trial 0 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 77.05 exceeds allowed maximum 20.0
2026-10-26 01:40:30,318 WARNING __main__: Trial 1 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 88.85 exceeds allowed maximum 20.0
2026-10-26 01:40:43,885 WARNING __main__: Trial 2 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 89.73 exceeds allowed maximum 20.0
2026-10-26 01:40:57,437 WARNING __main__: Trial 3 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 89.04 exceeds allowed maximum 20.0
2026-10-26 01:41:10,900 WARNING __main__: Trial 4 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 90.13 exceeds allowed maximum 20.0
2026-10-26 01:41:24,359 WARNING __main__: Trial 5 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 88.91 exceeds allowed maximum 20.0
2026-10-26 01:41:37,859 WARNING __main__: Trial 6 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 89.62 exceeds allowed maximum 20.0
2026-10-26 01:41:51,321 WARNING __main__: Trial 7 for N=3, sigma=0.0001 aborted: Unphysical trajectory: norm 86.23 exceeds allowed maximum 20.0

[TIMEOUT after 120s]
- python -m code.utils.validate --check-all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-101-quantifying-the-influence-of-initial-con/bin/python: No module named code.utils.validate

