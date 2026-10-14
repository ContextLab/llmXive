# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/integration/ -v --mock-testbed`
  - argparse error: `__main__.py: error: unrecognized arguments: --mock-testbed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/theoretical_bound.py --config config.yaml --input data/processed/regression_model.json; 5 command(s) failed: python code/orchestrator/scheduler.py --config config.yaml --granularity fine --nodes 15 --latency 100 (rc=1); python code/orchestrator/scheduler.py --config config.yaml --sweep (rc=1); python -m pytest tests/unit/ -v (rc=2); 2 declared deliverable(s) absent: data/raw/dropout_events.json; data/raw/validation_status.json

## Failing / missing run-book commands

- python code/orchestrator/scheduler.py --config config.yaml --granularity fine --nodes 15 --latency 100 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/scheduler.py", line 34, in <module>
    from orchestrator.models import PhysicalNode, TaskChunk, TaskStatus
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py", line 12, in <module>
    from pydantic import BaseModel, Field, validator, root_validator
ModuleNotFoundError: No module named 'pydantic'

- python code/orchestrator/scheduler.py --config config.yaml --sweep -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/scheduler.py", line 34, in <module>
    from orchestrator.models import PhysicalNode, TaskChunk, TaskStatus
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py", line 12, in <module>
    from pydantic import BaseModel, Field, validator, root_validator
ModuleNotFoundError: No module named 'pydantic'

- python code/analysis/theoretical_bound.py --config config.yaml --input data/processed/regression_model.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/analysis/theoretical_bound.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -v -> rc=2
tor.logger import get_logger, init_logger
E   ImportError: cannot import name 'init_logger' from 'orchestrator.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/logger.py)
=========================== short test summary info ============================
ERROR tests/unit/test_data_aggregator.py
ERROR tests/unit/test_heartbeat_monitoring.py
ERROR tests/unit/test_instrumentor_remote.py
ERROR tests/unit/test_logger.py
ERROR tests/unit/test_models.py
ERROR tests/unit/test_monte_carlo.py
ERROR tests/unit/test_network_impairments.py
ERROR tests/unit/test_overhead.py
ERROR tests/unit/test_remote_tool_checker.py
ERROR tests/unit/test_remote_tools_manager.py - AttributeError: module 'os' has no attribute 'dirname'
ERROR tests/unit/test_remote_wall_clock_timer.py - NameError: name 'pytest' is not defined
ERROR tests/unit/test_scheduler.py
ERROR tests/unit/test_scheduler_execution.py
ERROR tests/unit/test_scheduler_straggler.py
ERROR tests/unit/test_sweep_runner.py
!!!!!!!!!!!!!!!!!!! Interrupted: 15 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 15 errors in 1.23s ==============================


- python -m pytest tests/contract/ -v -> rc=2
(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/contract/test_execution_run_schema.py:19: in <module>
    from orchestrator.models import ExecutionRun, NodeStatus, TaskStatus
code/orchestrator/models.py:12: in <module>
    from pydantic import BaseModel, Field, validator, root_validator
E   ModuleNotFoundError: No module named 'pydantic'
=========================== short test summary info ============================
ERROR tests/contract/test_execution_run.py
ERROR tests/contract/test_execution_run_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.21s ===============================


- python -m pytest tests/integration/ -v --mock-testbed -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --mock-testbed
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg



## Declared deliverables still missing

- data/raw/dropout_events.json
- data/raw/validation_status.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dropout_events.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/heartbeat_monitoring.py` — NOT invoked by the run-book
    - `code/orchestrator/scheduler.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/dropout_events.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/validation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/instrumentation_validator.py` — NOT invoked by the run-book
    - `code/analysis/radio_metrics_validator.py` — NOT invoked by the run-book
    - `code/orchestrator/network_saturation_handler.py` — NOT invoked by the run-book
    - `code/orchestrator/scheduler_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/validation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
