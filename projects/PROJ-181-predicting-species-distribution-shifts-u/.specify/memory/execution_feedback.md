# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/bias_correction.py --occurrence data/raw/occurrence_1970_2000.csv  --output data/processed/bias_layer.tif; python code/project.py --models data/artifacts/ --climate data/raw/cmip6_2050.tif; python code/evaluate.py --models data/artifacts/  --test-data data/raw/occurrence_2005_2020.csv  --bias-layer data/processed/bias_layer.tif; 6 command(s) failed: python code/download.py --species-list list_of_species.txt --year-range 1970,2000 (rc=1); python code/download.py --species-list list_of_species.txt --year-range 2005,2020 --target recent (rc=1); python code/download.py --climate cmip6 --scenario SSP2-4.5 --year 2050 (rc=1); 1 declared deliverable(s) absent: data/processed/occurrence_clean.csv

## Failing / missing run-book commands

- python code/download.py --species-list list_of_species.txt --year-range 1970,2000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/download.py", line 12, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/download.py --species-list list_of_species.txt --year-range 2005,2020 --target recent -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/download.py", line 12, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/download.py --climate cmip6 --scenario SSP2-4.5 --year 2050 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/download.py", line 12, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/bias_correction.py --occurrence data/raw/occurrence_1970_2000.csv  --output data/processed/bias_layer.tif -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/bias_correction.py': [Errno 2] No such file or directory
- python code/preprocess.py --input data/raw/occurrence_1970_2000.csv  --bias-layer data/processed/bias_layer.tif  --thinning-distance 10 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/preprocess.py", line 13, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/baseline.py --data data/processed/filtered_thinned.csv  --output metrics/baseline_performance.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/baseline.py", line 25, in <module>
    logger = get_train_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_train_logger() takes 0 positional arguments but 1 was given
- python code/train.py --data data/processed/filtered_thinned.csv --cv-blocks 5 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/train.py", line 10, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/project.py --models data/artifacts/ --climate data/raw/cmip6_2050.tif -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/project.py': [Errno 2] No such file or directory
- python code/evaluate.py --models data/artifacts/  --test-data data/raw/occurrence_2005_2020.csv  --bias-layer data/processed/bias_layer.tif -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/evaluate.py': [Errno 2] No such file or directory
- python code/sensitivity.py --metrics metrics/final_results.csv  --output metrics/sensitivity_report.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-181-predicting-species-distribution-shifts-u/code/sensitivity.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/occurrence_clean.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_train_logger` — defined in `code/logging_config.py`; called 4 way(s):

- code/bias_null.py: return get_train_logger("bias_null")
- code/baseline.py: logger = get_train_logger(__name__)
- code/verify_gpu_free.py: logger = get_train_logger("verify_gpu_free")
- code/train.py: logger = get_train_logger()

Make `get_train_logger` in `code/logging_config.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/logging_config.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/logging_config.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/processed/occurrence_clean.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_clean_data.py` — NOT invoked by the run-book
    - `code/bias_null.py` — NOT invoked by the run-book
    - `code/baseline.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
    - `code/validate_clean_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/occurrence_clean.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
