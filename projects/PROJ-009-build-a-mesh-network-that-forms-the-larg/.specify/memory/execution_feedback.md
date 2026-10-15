# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/integration/ -v --mock-testbed`
  - argparse error: `__main__.py: error: unrecognized arguments: --mock-testbed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/theoretical_bound.py --config config.yaml --input data/processed/regression_model.json; 5 command(s) failed: python code/orchestrator/scheduler.py --config config.yaml --granularity fine --nodes 15 --latency 100 (rc=1); python code/orchestrator/scheduler.py --config config.yaml --sweep (rc=1); python -m pytest tests/unit/ -v (rc=2); 2 declared deliverable(s) absent: data/raw/dropout_events.json; data/raw/validation_status.json

## Failing / missing run-book commands

- python code/orchestrator/scheduler.py --config config.yaml --granularity fine --nodes 15 --latency 100 -> rc=1
r/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py", line 66, in <module>
    class ExecutionRun(BaseModel):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py", line 79, in ExecutionRun
    @root_validator
     ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/lib/python3.11/site-packages/pydantic/deprecated/class_validators.py", line 235, in root_validator
    return root_validator()(*__args)  # type: ignore
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/lib/python3.11/site-packages/pydantic/deprecated/class_validators.py", line 241, in root_validator
    raise PydanticUserError(
pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip

- python code/orchestrator/scheduler.py --config config.yaml --sweep -> rc=1
r/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py", line 66, in <module>
    class ExecutionRun(BaseModel):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/orchestrator/models.py", line 79, in ExecutionRun
    @root_validator
     ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/lib/python3.11/site-packages/pydantic/deprecated/class_validators.py", line 235, in root_validator
    return root_validator()(*__args)  # type: ignore
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/lib/python3.11/site-packages/pydantic/deprecated/class_validators.py", line 241, in root_validator
    raise PydanticUserError(
pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip

- python code/analysis/theoretical_bound.py --config config.yaml --input data/processed/regression_model.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-009-build-a-mesh-network-that-forms-the-larg/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/code/analysis/theoretical_bound.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -v -> rc=2
on.py - pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip
ERROR tests/unit/test_scheduler_straggler.py - pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip
ERROR tests/unit/test_sweep_runner.py - pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip
!!!!!!!!!!!!!!!!!!! Interrupted: 14 errors during collection !!!!!!!!!!!!!!!!!!!
======================= 40 warnings, 14 errors in 0.89s ========================


- python -m pytest tests/contract/ -v -> rc=2
.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    return root_validator()(*__args)  # type: ignore

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/contract/test_execution_run.py - pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip
ERROR tests/contract/test_execution_run_schema.py - pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`. Note that `@root_validator` is deprecated and should be replaced with `@model_validator`.

For further information visit https://errors.pydantic.dev/2.14/u/root-validator-pre-skip
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 10 warnings, 2 errors in 0.22s ========================


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
