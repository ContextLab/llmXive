# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py (rc=1); python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 (rc=1); python code/main.py --mode validation (rc=1); 7 declared deliverable(s) absent: data/simulation/error_rates_summary.csv; data/simulation/p_values_raw.csv; data/simulation/real_data_power.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 24, in <module>
    from code.analysis.aggregator import main as aggregator_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/aggregator.py", line 13, in <module>
    from code.simulation.output_writer import load_p_values_raw
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/simulation/output_writer.py", line 12, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^
NameError: name 'get_logger' is not defined
- python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 24, in <module>
    from code.analysis.aggregator import main as aggregator_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/aggregator.py", line 13, in <module>
    from code.simulation.output_writer import load_p_values_raw
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/simulation/output_writer.py", line 12, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^
NameError: name 'get_logger' is not defined
- python code/main.py --mode validation -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 24, in <module>
    from code.analysis.aggregator import main as aggregator_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/aggregator.py", line 13, in <module>
    from code.simulation.output_writer import load_p_values_raw
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/simulation/output_writer.py", line 12, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^
NameError: name 'get_logger' is not defined

## Declared deliverables still missing

- data/simulation/error_rates_summary.csv
- data/simulation/p_values_raw.csv
- data/simulation/real_data_power.json
- data/simulation/real_data_pvalues.csv
- data/simulation/thresholds.json
- data/simulation/validation_metrics.json
- data/simulation_metadata.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_error_details` — defined in `code/simulation/logging_config.py`; called 0 way(s):


Make `log_error_details` in `code/simulation/logging_config.py` accept ALL of the above.

### `register_run` — defined in `code/utils/checksum_utils.py`; called 0 way(s):


Make `register_run` in `code/utils/checksum_utils.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/simulation/logging_config.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/simulation/logging_config.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

```python
"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
```

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/simulation/error_rates_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/visualization/comparative_plots.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/error_rates_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/p_values_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/simulation/output_writer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/p_values_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_power.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_power.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/analysis/validator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/real_data_runner.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/thresholds.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/thresholds.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/checksum_utils.py` — NOT invoked by the run-book
    - `code/utils/metadata_manager.py` — NOT invoked by the run-book
    - `code/analysis/validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
