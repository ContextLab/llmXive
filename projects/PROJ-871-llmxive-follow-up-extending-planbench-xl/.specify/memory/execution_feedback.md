# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/dataset/loader.py --download (rc=1); python code/dataset/indexer.py (rc=1); python code/analysis/stats.py --baseline data/logs/baseline_execution_log.json --augmented data/logs/augmented_execution_log.json --report data/report.md (rc=1); 2 declared deliverable(s) absent: data/derived/failure_signatures.json; data/results/final_report.json

## Failing / missing run-book commands

- python code/dataset/loader.py --download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py", line 9, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-871-llmxive-follow-up-extending-planbench-xl/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/dataset/indexer.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/indexer.py", line 65, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/indexer.py", line 59, in main
    injected_data = load_injected_data()
                    ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/indexer.py", line 14, in load_injected_data
    raise FileNotFoundError(f"Injected data not found at {input_path}")
FileNotFoundError: Injected data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/data/derived/implicit_failure_subset.jsonl

- python code/analysis/stats.py --baseline data/logs/baseline_execution_log.json --augmented data/logs/augmented_execution_log.json --report data/report.md -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/stats.py", line 6, in <module>
    def calculate_statistical_significance(baseline_path: Path, augmented_path: Path) -> Dict[str, Any]:
                                                          ^^^^
NameError: name 'Path' is not defined

- python -m pytest tests/unit/ -> rc=2
l:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
../../.llmxive-venvs/PROJ-871-llmxive-follow-up-extending-planbench-xl/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_stats.py:2: in <module>
    from analysis.stats import calculate_statistical_significance
code/analysis/stats.py:6: in <module>
    def calculate_statistical_significance(baseline_path: Path, augmented_path: Path) -> Dict[str, Any]:
E   NameError: name 'Path' is not defined
=========================== short test summary info ============================
ERROR tests/unit/test_config_t030a.py
ERROR tests/unit/test_edge_cases.py
ERROR tests/unit/test_extractor.py
ERROR tests/unit/test_loader.py
ERROR tests/unit/test_stats.py - NameError: name 'Path' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 2.39s ===============================



## Declared deliverables still missing

- data/derived/failure_signatures.json
- data/results/final_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/failure_signatures.json` is declared but was NOT written. Scripts referencing it:
    - `code/dataset/indexer.py` — IS a run-book command
    - `code/run_augmented.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/tests/unit/test_baseline_isolation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/failure_signatures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
