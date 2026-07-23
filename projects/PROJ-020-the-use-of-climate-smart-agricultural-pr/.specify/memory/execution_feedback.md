# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analysis/robustness.py --data data/processed/merged_sample.parquet --formula "hdds ~ csa_index + digital_access + finance_access + (digital_access * finance_access)"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/ingestion.py (rc=1); python code/preprocessing.py (rc=1); python code/modeling.py (rc=1); 2 declared deliverable(s) absent: data/processed/ipw_weights.parquet; data/processed/merged_sample.parquet

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/ingestion.py", line 24, in <module>
    from data.download import download_lsms_batch, download_nasa_power_batch, download_faostat_batch
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/data/__init__.py", line 4, in <module>
    from .download import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/data/download.py", line 23, in <module>
    initialize_logging()
TypeError: initialize_logging() missing 1 required positional argument: 'name'
- python code/preprocessing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/preprocessing.py", line 29, in <module>
    from data.clean import run_sampling_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/data/__init__.py", line 4, in <module>
    from .download import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/data/download.py", line 23, in <module>
    initialize_logging()
TypeError: initialize_logging() missing 1 required positional argument: 'name'
- python code/modeling.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/modeling.py", line 24, in <module>
    from data.features import main as features_main
ModuleNotFoundError: No module named 'data.features'
- python code/analysis/robustness.py --data data/processed/merged_sample.parquet --formula "hdds ~ csa_index + digital_access + finance_access + (digital_access * finance_access)" -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/analysis/robustness.py", line 243, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/analysis/robustness.py", line 208, in main
    raise FileNotFoundError(f"Data file not found: {args.data}")
FileNotFoundError: Data file not found: data/processed/merged_sample.parquet
- python code/viz.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz.py", line 48, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz.py", line 30, in main
    initialize_logging(log_path=log_path, level=logging.INFO)
TypeError: initialize_logging() got an unexpected keyword argument 'log_path'
- python code/verify_reproducibility.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/verify_reproducibility.py", line 256, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/verify_reproducibility.py", line 173, in main
    initialize_logging(log_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/utils/logging.py", line 12, in initialize_logging
    logger = logging.getLogger(name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 2082, in getLogger
    return Logger.manager.getLogger(name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1340, in getLogger
    raise TypeError('A logger name must be a string')
TypeError: A logger name must be a string

## Declared deliverables still missing

- data/processed/ipw_weights.parquet
- data/processed/merged_sample.parquet

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `initialize_logging` — defined in `code/utils/logging.py`; called 7 way(s):

- code/main.py: logger = initialize_logging()
- code/viz.py: initialize_logging(log_path=log_path, level=logging.INFO)
- code/verify_reproducibility.py: initialize_logging(log_file)
- code/ingestion.py: initialize_logging()
- code/modeling.py: initialize_logging(log_file, level=logging.INFO)
- code/preprocessing.py: logger = initialize_logging("preprocessing")
- code/data/download.py: initialize_logging()

Make `initialize_logging` in `code/utils/logging.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/utils/logging.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/utils/logging.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/processed/ipw_weights.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/verify_reproducibility.py` — IS a run-book command
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ipw_weights.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/verify_reproducibility.py` — IS a run-book command
    - `code/ingestion.py` — IS a run-book command
    - `code/preprocessing.py` — IS a run-book command
    - `code/validation/quickstart_validator.py` — NOT invoked by the run-book
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/data/features.py` — NOT invoked by the run-book
    - `code/analysis/performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/merged_sample.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/verify_reproducibility.py`, `code/data/clean.py`, `code/data/features.py`, `code/analysis/performance.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/merged_sample.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/verify_reproducibility.py`, `code/ingestion.py`, `code/preprocessing.py`, `code/validation/quickstart_validator.py`, `code/data/clean.py`, `code/data/features.py`, `code/analysis/performance.py`.
