# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode simulation`
  - script usage: `main.py [-h] {simulation,real_world,analyze,visualize} ...`
  - argparse error: `main.py: error: unrecognized arguments: --mode`
- run-book command: `python code/main.py --mode real_world`
  - script usage: `main.py [-h] {simulation,real_world,analyze,visualize} ...`
  - argparse error: `main.py: error: unrecognized arguments: --mode`
- run-book command: `python code/main.py --mode simulation --config-id "test-config-1" --iterations 100`
  - script usage: `main.py [-h] {simulation,real_world,analyze,visualize} ...`
  - argparse error: `main.py: error: unrecognized arguments: --mode`
- run-book command: `python code/main.py --mode visualize`
  - script usage: `main.py [-h] {simulation,real_world,analyze,visualize} ...`
  - argparse error: `main.py: error: unrecognized arguments: --mode`
- run-book command: `python code/main.py --mode analyze`
  - script usage: `main.py [-h] {simulation,real_world,analyze,visualize} ...`
  - argparse error: `main.py: error: unrecognized arguments: --mode`
- run-book command: `python code/main.py --mode verify-checksums`
  - script usage: `main.py [-h] {simulation,real_world,analyze,visualize} ...`
  - argparse error: `main.py: error: argument mode: invalid choice: 'verify-checksums' (choose from 'simulation', 'real_world', 'analyze', 'visualize')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --mode simulation (rc=2); python code/main.py --mode real_world (rc=2); python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 (rc=2)

## Failing / missing run-book commands

- python code/main.py --mode simulation -> rc=2
    usage: main.py [-h] {simulation,real_world,analyze,visualize} ...
main.py: error: unrecognized arguments: --mode
- python code/main.py --mode real_world -> rc=2
    usage: main.py [-h] {simulation,real_world,analyze,visualize} ...
main.py: error: unrecognized arguments: --mode
- python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 -> rc=2
    usage: main.py [-h] {simulation,real_world,analyze,visualize} ...
main.py: error: unrecognized arguments: --mode
- python code/main.py --mode visualize -> rc=2
    usage: main.py [-h] {simulation,real_world,analyze,visualize} ...
main.py: error: unrecognized arguments: --mode
- python code/main.py --mode analyze -> rc=2
    usage: main.py [-h] {simulation,real_world,analyze,visualize} ...
main.py: error: unrecognized arguments: --mode
- python code/main.py --mode verify-checksums -> rc=2
    usage: main.py [-h] {simulation,real_world,analyze,visualize} ...
main.py: error: argument mode: invalid choice: 'verify-checksums' (choose from 'simulation', 'real_world', 'analyze', 'visualize')

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_full_analysis_pipeline` — defined in `code/analysis/metrics.py`; called 2 way(s):

- code/tests/unit/analysis/test_metrics.py: result = run_full_analysis_pipeline(df)
- code/tests/unit/analysis/test_metrics.py: result = run_full_analysis_pipeline()

Make `run_full_analysis_pipeline` in `code/analysis/metrics.py` accept ALL of the above.

### `setup_logger` — defined in `code/simulation/logger.py`; called 18 way(s):

- code/main.py: logger = setup_logger(batch_id="main_pipeline")
- code/benchmark_generator.py: logger = setup_logger(__name__)
- code/validate_quickstart.py: logger = setup_logger("quickstart_validation")
- code/utils/env.py: logger = setup_logger(logger_name)
- code/tests/unit/simulation/test_logger_fix.py: logger = setup_logger("test_name")
- code/tests/unit/simulation/test_logger_fix.py: logger = setup_logger(batch_id="main_pipeline")
- code/tests/unit/simulation/test_logger_fix.py: logger = setup_logger(__name__)
- code/tests/unit/simulation/test_logger_fix.py: logger = setup_logger()
- code/tests/unit/simulation/test_logger_fix.py: logger = setup_logger("test")
- code/tests/unit/simulation/test_main.py: logger = setup_logger("test")
- code/tests/unit/preprocessing/test_scaling.py: test_logger = setup_logger("test_scaling")
- code/simulation/persistence.py: logger = setup_logger(__name__)
- code/simulation/generator.py: logger = setup_logger(__name__)
- code/simulation/logger.py: 1. setup_logger("name_string") -> positional arg
- code/simulation/logger.py: 2. setup_logger(batch_id="id") -> keyword arg
- code/simulation/logger.py: 3. setup_logger(__name__) -> positional arg
- code/simulation/orchestrator.py: logger = setup_logger("orchestrator")
- code/preprocessing/ingestion.py: logger = setup_logger("preprocessing.ingestion")

Make `setup_logger` in `code/simulation/logger.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/simulation/logger.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/simulation/logger.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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
