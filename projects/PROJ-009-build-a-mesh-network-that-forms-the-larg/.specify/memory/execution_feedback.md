# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/orchestrator/cli.py run  --config config.yaml  --granularity fine  --node-count 15  --injected-latency 100`
  - script usage: `orchestrator run [-h] --config CONFIG --granularity`
  - argparse error: `orchestrator run: error: the following arguments are required: --nodes, --latency`
- run-book command: `python -m pytest tests/integration/ -v --mock-testbed`
  - argparse error: `__main__.py: error: unrecognized arguments: --mock-testbed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/orchestrator/node_manager.py --verify (rc=1); python code/orchestrator/cli.py calibrate --config config.yaml (rc=1); python code/orchestrator/cli.py run  --config config.yaml  --granularity fine  --node-count 15  --injected-latency 100 (rc=2); 5 declared deliverable(s) absent: data/raw/cpu_calibration.json; data/raw/dropout_events.json; data/raw/network_calibration.json

## Failing / missing run-book commands

- python code/orchestrator/node_manager.py --verify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/node_manager.py", line 41, in <module>
    from paramiko import SSHClient, AutoAddPolicy, SSHException
ModuleNotFoundError: No module named 'paramiko'

- python code/orchestrator/cli.py calibrate --config config.yaml -> rc=1

2026-10-20 17:21:35,662 INFO orchestrator.calibration: Starting calibration procedures
2026-10-20 17:21:35,663 ERROR __main__: Calibration routine failed: [Errno 2] No such file or directory: 'iperf3'

- python code/orchestrator/cli.py run  --config config.yaml  --granularity fine  --node-count 15  --injected-latency 100 -> rc=2

usage: orchestrator run [-h] --config CONFIG --granularity
                        {fine,medium,coarse} --nodes NODES --latency LATENCY
orchestrator run: error: the following arguments are required: --nodes, --latency

- python code/analysis/theoretical_bound.py  --input data/processed/regression_model.json  --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/analysis/theoretical_bound.py", line 97, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/analysis/theoretical_bound.py", line 63, in main
    model = load_json(input_path)
            ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/analysis/theoretical_bound.py", line 29, in load_json
    raise FileNotFoundError(f"Input file not found: {path}")
FileNotFoundError: Input file not found: data/processed/regression_model.json

- python -m pytest tests/unit/ -v -> rc=2
ase-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_timeout_guard.py:8: in <module>
    from orchestrator.timeout_guard import (
E   ImportError: cannot import name 'run_with_timeout' from 'orchestrator.timeout_guard' (/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/timeout_guard.py)
=========================== short test summary info ============================
ERROR tests/unit/test_data_aggregator.py
ERROR tests/unit/test_heartbeat_monitoring.py
ERROR tests/unit/test_instrumentor_remote.py
ERROR tests/unit/test_models.py
ERROR tests/unit/test_monte_carlo.py
ERROR tests/unit/test_node_profiler.py
ERROR tests/unit/test_remote_tool_installer.py
ERROR tests/unit/test_remote_wall_clock_timer.py
ERROR tests/unit/test_scheduler.py
ERROR tests/unit/test_scheduler_execution.py
ERROR tests/unit/test_scheduler_straggler.py
ERROR tests/unit/test_sweep_runner.py
ERROR tests/unit/test_timeout_guard.py
!!!!!!!!!!!!!!!!!!! Interrupted: 13 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 13 errors in 1.21s ==============================


- python -m pytest tests/contract/ -v -> rc=2
_module(module_name)
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
E   ImportError: cannot import name 'ExecutionRun' from 'orchestrator.models' (/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py)
=========================== short test summary info ============================
ERROR tests/contract/test_execution_run_schema.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.15s ===============================


- python -m pytest tests/integration/ -v --mock-testbed -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --mock-testbed
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg



## Declared deliverables still missing

- data/raw/cpu_calibration.json
- data/raw/dropout_events.json
- data/raw/network_calibration.json
- data/raw/validation_status.json
- data/runtime/pipeline_runtime.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/cpu_calibration.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/cpu_calibration.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dropout_events.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/cli.py` — IS a run-book command
    - `code/orchestrator/heartbeat_monitoring.py` — NOT invoked by the run-book
    - `code/orchestrator/scheduler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dropout_events.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/network_calibration.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/network_calibration.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/validation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/instrumentation_validator.py` — NOT invoked by the run-book
    - `code/analysis/radio_metrics_validator.py` — NOT invoked by the run-book
    - `code/orchestrator/cli.py` — IS a run-book command
    - `code/orchestrator/network_saturation_handler.py` — NOT invoked by the run-book
    - `code/orchestrator/scheduler_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/validation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/runtime/pipeline_runtime.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/runtime_tracker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/runtime/pipeline_runtime.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
