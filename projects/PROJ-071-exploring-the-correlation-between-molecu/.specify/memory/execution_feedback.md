# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/analysis_results.json: metric is null/NaN (R2, p_values, coefficients) — not a real measurement
- every produced artifact is gitignored (data/processed/analysis_results.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/report.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/analysis_results.json: metric is null/NaN (R2, p_values, coefficients) — not a real measurement; every produced artifact is gitignored (data/processed/analysis_results.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python code/ingest.py (rc=1); python code/report.py (rc=1); 1 declared deliverable(s) absent: data/stat_gate_status.json

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/ingest.py", line 421, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/ingest.py", line 350, in main
    log_pipeline_start("T012_Ingest_And_Gate", {"task": "T012"})
TypeError: log_pipeline_start() takes from 0 to 1 positional arguments but 2 were given
- python code/report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-071-exploring-the-correlation-between-molecu/code/report.py", line 33, in <module>
    def collect_reproducibility_metadata() -> Dict[str, Any]:
                                              ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

## Declared deliverables still missing

- data/stat_gate_status.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_pipeline_failure` — defined in `code/logging_config.py`; called 16 way(s):

- code/logging_config.py: - log_pipeline_failure("operation_name", "reason")
- code/logging_config.py: - log_pipeline_failure(reason="reason")
- code/logging_config.py: - log_pipeline_failure(str(e))
- code/logging_config.py: - log_pipeline_failure(logger, "op", "reason")
- code/logging_config.py: # Handle call shape: log_pipeline_failure(logger, "op", "reason")
- code/logging_config.py: # Handle call shape: log_pipeline_failure("op", "reason") or log_pipeline_failure(reason)
- code/validate_performance.py: log_pipeline_failure("performance_validation", str(e))
- code/ingest.py: log_pipeline_failure("T012_Ingest_And_Gate", str(e))
- code/run_pipeline.py: log_pipeline_failure("Ingest", str(e))
- code/run_pipeline.py: log_pipeline_failure("Descriptors", str(e))
- code/run_pipeline.py: log_pipeline_failure("Standardize", str(e))
- code/run_pipeline.py: log_pipeline_failure("Analysis", str(e))
- code/run_pipeline.py: log_pipeline_failure("Visualization", str(e))
- code/run_pipeline.py: log_pipeline_failure("Report", str(e))
- code/run_pipeline.py: log_pipeline_failure("Verification", str(e))
- code/run_pipeline.py: log_pipeline_failure("Pipeline", str(e))

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

- `data/stat_gate_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/statistical_insufficiency_report.py` — NOT invoked by the run-book
    - `code/standardize.py` — NOT invoked by the run-book
    - `code/insufficiency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/stat_gate_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `merged_drugs.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[train]`
- PRODUCER(s) to edit: `code/fresh_env_smoke_test.py`, `code/descriptors.py`, `code/report.py`, `code/ingest.py`, `code/standardize.py`, `code/insufficiency.py`
- CONSUMER(s) that read it: `code/fresh_env_smoke_test.py`, `code/descriptors.py`, `code/report.py`, `code/viz.py`, `code/ingest.py`, `code/standardize.py`, `code/insufficiency.py`
  → Edit the producer so every required name [train] is in `merged_drugs.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
