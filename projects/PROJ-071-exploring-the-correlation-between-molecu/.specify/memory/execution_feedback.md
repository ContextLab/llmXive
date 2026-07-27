# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/ingest.py (rc=1); 4 declared deliverable(s) absent: data/gate_status.json; data/processed/analysis_results.json; data/processed/merged_drugs.csv

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
    Drugs
2026-07-27 18:15:02 - llmXive_pipeline.__main__ - ERROR - Failed to fetch dataset: 'train'

Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/ingest.py", line 145, in main
    df = fetch_fda_drugs()
         ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/ingest.py", line 35, in fetch_fda_drugs
    data = list(dataset['train'])
                ~~~~~~~^^^^^^^^^
KeyError: 'train'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/ingest.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/ingest.py", line 175, in main
    log_pipeline_failure(str(e))
TypeError: log_pipeline_failure() missing 1 required positional argument: 'reason'

## Declared deliverables still missing

- data/gate_status.json
- data/processed/analysis_results.json
- data/processed/merged_drugs.csv
- data/processed/structural_subset.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_pipeline_failure` — defined in `code/logging_config.py`; called 5 way(s):

- code/validate_performance.py: log_pipeline_failure("performance_validation", str(e))
- code/ingest.py: log_pipeline_failure("Missing degradation columns")
- code/ingest.py: log_pipeline_failure(reason)
- code/ingest.py: log_pipeline_failure(str(e))
- code/run_pipeline.py: log_pipeline_failure(logger, "T055_Full_Pipeline_Smoke_Test", str(e))

Make `log_pipeline_failure` in `code/logging_config.py` accept ALL of the above.

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

- `data/gate_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/fresh_env_smoke_test.py` — NOT invoked by the run-book
    - `code/generate_performance_failure_report.py` — NOT invoked by the run-book
    - `code/final_gate_check.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/gate_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/fresh_env_smoke_test.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/viz.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_drugs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fresh_env_smoke_test.py` — NOT invoked by the run-book
    - `code/descriptors.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/viz.py` — NOT invoked by the run-book
    - `code/ingest.py` — IS a run-book command
    - `code/standardize.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_drugs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/structural_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/memory_profiler.py` — NOT invoked by the run-book
    - `code/edge_case_stress_test.py` — NOT invoked by the run-book
    - `code/robustness_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/structural_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `merged_drugs.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[train]`
- PRODUCER(s) to edit: `code/fresh_env_smoke_test.py`, `code/descriptors.py`, `code/report.py`, `code/ingest.py`, `code/standardize.py`, `code/run_pipeline.py`
- CONSUMER(s) that read it: `code/fresh_env_smoke_test.py`, `code/descriptors.py`, `code/report.py`, `code/viz.py`, `code/ingest.py`, `code/standardize.py`, `code/run_pipeline.py`
  → Edit the producer so every required name [train] is in `merged_drugs.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
