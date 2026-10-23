# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/dropout_events.json, data/raw/run_001.csv, data/raw/validation_status.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.orchestrator.cli mock --config config.yaml`
  - script usage: `orchestrator [-h] {verify,run,calibrate,sweep} ...`
  - argparse error: `orchestrator: error: argument command: invalid choice: 'mock' (choose from 'verify', 'run', 'calibrate', 'sweep')`
- run-book command: `python -m pytest tests/integration/ -v --mock-testbed`
  - argparse error: `__main__.py: error: unrecognized arguments: --mock-testbed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/dropout_events.json, data/raw/run_001.csv, data/raw/validation_status.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 command(s) failed: python -m code.orchestrator.node_manager --verify (rc=1); python -m code.orchestrator.cli mock --config config.yaml (rc=2); python -m code.analysis.regression  --input data/raw/  --output data/processed/ (rc=1); 3 declared deliverable(s) absent: data/raw/cpu_calibration.json; data/raw/network_calibration.json; data/runtime/pipeline_runtime.json

## Failing / missing run-book commands

- python -m code.orchestrator.node_manager --verify -> rc=1
2026-10-23 21:30:30 - llmXive.node_manager - INFO - Starting node discovery for 2 candidates.
2026-10-23 21:30:30 - llmXive.node_manager - ERROR - Node 127.0.0.1: SSH error: No authentication methods available
2026-10-23 21:30:30 - llmXive.node_manager - ERROR - Node 127.0.0.2: SSH error: No authentication methods available
2026-10-23 21:30:30 - llmXive.__main__ - ERROR - Discovery failed for all 2 nodes.

2026-10-23 21:30:30,209 INFO llmXive.node_manager: Starting node discovery for 2 candidates.
2026-10-23 21:30:30,336 INFO paramiko.transport: Connected (version 2.0, client OpenSSH_9.6p1)
2026-10-23 21:30:30,342 ERROR llmXive.node_manager: Node 127.0.0.1: SSH error: No authentication methods available
2026-10-23 21:30:30,348 INFO paramiko.transport: Connected (version 2.0, client OpenSSH_9.6p1)
2026-10-23 21:30:30,353 ERROR llmXive.node_manager: Node 127.0.0.2: SSH error: No authentication methods available
2026-10-23 21:30:30,354 ERROR llmXive.__main__: Discovery failed for all 2 nodes.

- python -m code.orchestrator.cli mock --config config.yaml -> rc=2

usage: orchestrator [-h] {verify,run,calibrate,sweep} ...
orchestrator: error: argument command: invalid choice: 'mock' (choose from 'verify', 'run', 'calibrate', 'sweep')

- python -m code.analysis.regression  --input data/raw/  --output data/processed/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/bin/python: No module named code.analysis.regression

- python -m code.analysis.theoretical_bound  --input data/processed/execution_runs.csv  --output data/processed/ -> rc=1

2026-10-23 21:30:32,430 ERROR __main__: Missing required '--config' argument

- python -m pytest tests/unit/ -v -> rc=2
ortlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
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
ERROR tests/unit/test_remote_wall_clock_timer.py - NameError: name 'pytest' is not defined
ERROR tests/unit/test_scheduler_execution.py
ERROR tests/unit/test_scheduler_straggler.py
ERROR tests/unit/test_sweep_runner.py
ERROR tests/unit/test_timeout_guard.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 0.83s ==============================


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
=============================== 1 error in 0.13s ===============================


- python -m pytest tests/integration/ -v --mock-testbed -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --mock-testbed
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg



## Declared deliverables still missing

- data/raw/cpu_calibration.json
- data/raw/network_calibration.json
- data/runtime/pipeline_runtime.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/cpu_calibration.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/calibration.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/cpu_calibration.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/network_calibration.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/calibration.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/network_calibration.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/runtime/pipeline_runtime.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/runtime_tracker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/runtime/pipeline_runtime.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
