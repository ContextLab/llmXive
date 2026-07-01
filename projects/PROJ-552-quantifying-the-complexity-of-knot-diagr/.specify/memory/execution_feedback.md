# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/reproducibility/checksum_generator.py

## Failing / missing run-book commands

- python code/reproducibility/checksum_generator.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/checksum_generator.py': [Errno 2] No such file or directory

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/reproducibility/logs.py`; called 25 way(s):

- code/analysis/plotting.py: logger = get_logger(__name__)
- code/analysis/coverage.py: logger = get_logger(__name__)
- code/analysis/dataset_counts.py: logger = get_logger()
- code/analysis/coverage_reporting.py: logger = get_logger(__name__)
- code/analysis/validation_reporting.py: logger = get_logger(__name__)
- code/analysis/oeis_validation.py: self.logger_instance = get_logger() if logger is None else logger
- code/analysis/data_quality.py: logger = get_logger("data_quality")
- code/analysis/model_fitting.py: logger = get_logger(__name__)
- code/analysis/group_comparison.py: logger = get_logger(__name__)
- code/analysis/correlation.py: logger = get_logger(__name__)
- code/analysis/exploratory.py: logger = get_logger()
- code/analysis/validation.py: logger = get_logger(__name__)
- code/analysis/validation.py: self.logger = get_logger(__name__)
- code/analysis/regression.py: logger = get_logger(__name__)
- code/analysis/save_crossing_braid_plot.py: logger = get_logger()
- code/analysis/_utils.py: logger = get_logger()
- code/analysis/invariant_coverage.py: logger = get_logger(__name__)
- code/analysis/complexity_visualization_examples.py: logger = get_logger(__name__)
- code/analysis/validate_completeness.py: logger = get_logger()
- code/analysis/data_quality_report.py: logger = get_logger(__name__)
- code/filter/hyperbolic_filter.py: get_logger().log("hyperbolic_filter_completed", parameters={"kept": len(hyperbolic), "excluded": len(excluded)})
- code/data/validator.py: logger = get_logger(__name__)
- code/reproducibility/logs.py: return get_logger().log(op, **kwargs)
- code/reproducibility/quickstart_validator.py: ``get_logger('quickstart_validator')`` which failed because ``get_logger`` did not
- code/reproducibility/quickstart_validator.py: self.logger = get_logger("quickstart_validator")

Make `get_logger` in `code/reproducibility/logs.py` accept ALL of the above.

### `log_operation` — defined in `code/reproducibility/logs.py`; called 25 way(s):

- code/analysis/plotting.py: @log_operation
- code/analysis/dataset_counts.py: @log_operation
- code/analysis/coverage_reporting.py: log_operation(
- code/analysis/validation_reporting.py: log_operation("report_generation", "Hyperbolic Volume Report", {
- code/analysis/validation_reporting.py: log_operation("report_generation_complete", "Hyperbolic Volume Report", {"status": "success"})
- code/analysis/oeis_validation.py: log_operation(
- code/analysis/data_quality.py: log_operation(
- code/analysis/model_fitting.py: @log_operation
- code/analysis/group_comparison.py: @log_operation
- code/analysis/correlation.py: @log_operation
- code/analysis/validation.py: log_operation("validation_start", "Hyperbolic Volume Validation", {"input": str(input_path)})
- code/analysis/validation.py: log_operation("validation_end", "Hyperbolic Volume Validation", {
- code/analysis/regression.py: @log_operation
- code/analysis/invariant_coverage.py: log_operation(
- code/analysis/complexity_visualization_examples.py: log_operation("complexity_visualization_examples_start", parameters={})
- code/analysis/complexity_visualization_examples.py: log_operation(
- code/analysis/data_quality_report.py: @log_operation
- code/filter/hyperbolic_filter.py: @log_operation
- code/data/validator.py: log_operation("apply_missing_and_quality_flags_start", csv_path=str(csv_path))
- code/data/validator.py: log_operation("apply_missing_and_quality_flags_end", success=True, count=len(results))
- code/data/validator.py: log_operation("duplicate_id_check", duplicate_count=duplicate_count)
- code/data/validator.py: log_operation("validator_main_start", input=str(args.input), output=str(args.output))
- code/data/validator.py: log_operation("validator_main_end", success=True, output=str(args.output))
- code/reproducibility/logs.py: """Dual-purpose: a decorator (@log_operation) OR a direct logging call.
- code/reproducibility/logs.py: # Decorator usage: @log_operation

Make `log_operation` in `code/reproducibility/logs.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/reproducibility/logs.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/reproducibility/logs.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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
