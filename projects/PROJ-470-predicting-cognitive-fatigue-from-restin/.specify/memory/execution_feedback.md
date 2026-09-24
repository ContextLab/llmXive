# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py --validate (rc=1); python code/preprocess.py (rc=1); python code/features.py (rc=1); 6 declared deliverable(s) absent: data/analysis/ancova_results.csv; data/analysis/complexity_metrics.csv; data/analysis/resource_usage.json

## Failing / missing run-book commands

- python code/download.py --validate -> rc=1
    
- python code/preprocess.py -> rc=1
    ERROR: Sample EEG file not found at data/raw/sample_eeg.fif.
Please run code/download.py first.
- python code/features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/features.py", line 19, in <module>
    from utils.monitor import ResourceMonitor
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/utils/monitor.py", line 14, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'
- python code/analysis.py -> rc=1
    2026-09-24 19:24:22,503 - root - INFO - Starting analysis pipeline.
2026-09-24 19:24:22,504 - root - ERROR - Complexity metrics file not found: data/analysis/complexity_metrics.csv
- python code/report.py -> rc=1
    m-restin/code/report.py", line 207, in main
    generate_report(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/report.py", line 93, in generate_report
    report_lines.append(render_markdown_table(correlation_df))
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/report.py", line 66, in render_markdown_table
    return df.to_markdown(index=False)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/.venv/lib/python3.11/site-packages/pandas/core/frame.py", line 2983, in to_markdown
    tabulate = import_optional_dependency("tabulate")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/.venv/lib/python3.11/site-packages/pandas/compat/_optional.py", line 161, in import_optional_dependency
    raise ImportError(msg) from err
ImportError: `Import tabulate` failed.  Use pip or conda to install the tabulate package.

## Declared deliverables still missing

- data/analysis/ancova_results.csv
- data/analysis/complexity_metrics.csv
- data/analysis/resource_usage.json
- data/analysis/vif_valid_predictors.json
- data/processed/exclusion_log.csv
- data/raw/download_manifest.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/sensitivity_analysis.py`; called 16 way(s):

- code/verify_runtime.py: logger = get_logger("verify_runtime")
- code/preprocess.py: logger = get_logger(name, log_file)
- code/features.py: logger = get_logger(name)
- code/sensitivity_analysis.py: logger = get_logger("sensitivity_analysis")
- code/sensitivity_analysis.py: logger = get_logger("sensitivity_analysis", log_file="data/analysis/sensitivity_analysis.log")
- code/verify_memory.py: logger = get_logger("verify_memory")
- code/check_sample_size.py: logger = get_logger("check_sample_size")
- code/download.py: logger = get_logger(name=name, log_file=log_file)
- code/profile_memory.py: logger = get_logger("memory_profile")
- code/report.py: logger = get_logger("report")
- code/analysis.py: logger = get_logger(name)
- code/benjamini_hochberg.py: logger = get_logger(name, log_file)
- code/utils/logging.py: return get_logger().log(op, **kwargs)
- code/utils/logging.py: entry = get_logger().log("artifact_rejection", artifact_type=artifact_type, artifact_id=artifact_id, reason=reason)
- code/utils/logging.py: entry = get_logger().log("participant_exclusion", participant_id=participant_id, reason=reason)
- code/utils/logging.py: logger = get_logger()

Make `get_logger` in `code/sensitivity_analysis.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/sensitivity_analysis.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/sensitivity_analysis.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/analysis/ancova_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/ancova_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/complexity_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features.py` — IS a run-book command
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/complexity_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/resource_usage.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_runtime.py` — NOT invoked by the run-book
    - `code/verify_memory.py` — NOT invoked by the run-book
    - `code/utils/monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/resource_usage.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/vif_valid_predictors.json` is declared but was NOT written. Scripts referencing it:
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/vif_valid_predictors.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/check_sample_size.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/benjamini_hochberg.py` — NOT invoked by the run-book
    - `code/utils/logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/download_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_sample_size.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/download_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/analysis/complexity_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/features.py`, `code/collinearity.py`, `code/report.py`, `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/analysis/complexity_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/features.py`, `code/collinearity.py`, `code/report.py`, `code/analysis.py`.

### `data/processed/complexity_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/features.py`, `code/collinearity.py`, `code/report.py`, `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/complexity_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/features.py`, `code/collinearity.py`, `code/report.py`, `code/analysis.py`.
