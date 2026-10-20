# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/orchestrator/cli.py: self-declared fabricated metric — “…ark once per node and collect dummy metrics     rows = []     for idx, n…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/integration/ -v --mock-testbed`
  - argparse error: `__main__.py: error: unrecognized arguments: --mock-testbed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/orchestrator/cli.py: self-declared fabricated metric — “…ark once per node and collect dummy metrics     rows = []     for idx, n…”; 7 command(s) failed: python code/orchestrator/cli.py calibrate --config config.yaml (rc=1); python code/orchestrator/cli.py run  --config config.yaml  --granularity fine  --node-count 15  --injected-latency 100 (rc=1); python code/orchestrator/cli.py sweep --config config.yaml (rc=1); 4 declared deliverable(s) absent: data/raw/dropout_events.json; data/raw/run_001.csv; data/raw/validation_status.json

## Failing / missing run-book commands

- python code/orchestrator/cli.py calibrate --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/cli.py", line 49, in <module>
    from runtime.runtime_tracker import start as rt_start, stop as rt_stop
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/runtime/runtime_tracker.py", line 29, in <module>
    def stop(limit_seconds: float) -> Tuple[float, bool]:
                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

- python code/orchestrator/cli.py run  --config config.yaml  --granularity fine  --node-count 15  --injected-latency 100 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/cli.py", line 49, in <module>
    from runtime.runtime_tracker import start as rt_start, stop as rt_stop
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/runtime/runtime_tracker.py", line 29, in <module>
    def stop(limit_seconds: float) -> Tuple[float, bool]:
                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

- python code/orchestrator/cli.py sweep --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/cli.py", line 49, in <module>
    from runtime.runtime_tracker import start as rt_start, stop as rt_stop
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/runtime/runtime_tracker.py", line 29, in <module>
    def stop(limit_seconds: float) -> Tuple[float, bool]:
                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

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
tlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_sweep_runner.py:13: in <module>
    from orchestrator.sweep_runner import SweepRunner, SweepConfig, generate_default_configs
E   ImportError: cannot import name 'SweepRunner' from 'orchestrator.sweep_runner' (/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/sweep_runner.py)
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
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 1.02s ===============================


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

- data/raw/dropout_events.json
- data/raw/run_001.csv
- data/raw/validation_status.json
- data/runtime/pipeline_runtime.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dropout_events.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/cli.py` — IS a run-book command
    - `code/orchestrator/heartbeat_monitoring.py` — NOT invoked by the run-book
    - `code/orchestrator/scheduler.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dropout_events.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/run_001.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/radio_metrics_extractor.py` — NOT invoked by the run-book
    - `code/orchestrator/cli.py` — IS a run-book command
    - `code/orchestrator/task_chunk_store.py` — NOT invoked by the run-book
    - `code/tests/contract/test_task_chunk_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/run_001.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/validation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/instrumentation_validator.py` — NOT invoked by the run-book
    - `code/analysis/radio_metrics_validator.py` — NOT invoked by the run-book
    - `code/orchestrator/cli.py` — IS a run-book command
    - `code/orchestrator/network_saturation_handler.py` — NOT invoked by the run-book
    - `code/orchestrator/scheduler_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/validation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/runtime/pipeline_runtime.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestrator/runtime_tracker.py` — NOT invoked by the run-book
    - `code/runtime/runtime_tracker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/runtime/pipeline_runtime.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
