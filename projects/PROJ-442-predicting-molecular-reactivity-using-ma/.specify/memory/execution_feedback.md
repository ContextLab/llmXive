# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/src/modeling/evaluate.py --input data/results/cv_results.csv --output reports/final_report.md`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python src/data/ingestion.py --output data/processed/filtered_reactions.parquet (rc=1); python src/data/preprocessing.py --input data/processed/filtered_reactions.parquet --output data/processed/features.parquet (rc=1); python src/modeling/train.py --config src/modeling/config.yaml (rc=1); 5 declared deliverable(s) absent: data/models/xgboost_model.json; data/processed/analysis_report.json; data/processed/class_exclusion_metadata.json

## Failing / missing run-book commands

- python src/data/ingestion.py --output data/processed/filtered_reactions.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/data/ingestion.py", line 371, in <module>
    setup_logger()
TypeError: setup_logger() missing 1 required positional argument: 'name'
- python src/data/preprocessing.py --input data/processed/filtered_reactions.parquet --output data/processed/features.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/data/preprocessing.py", line 314, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/data/preprocessing.py", line 307, in main
    setup_logger(__name__)
    ^^^^^^^^^^^^
NameError: name 'setup_logger' is not defined. Did you mean: 'get_logger'?
- python src/modeling/train.py --config src/modeling/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/modeling/train.py", line 13, in <module>
    from sklearn.metrics import spearmanr
ImportError: cannot import name 'spearmanr' from 'sklearn.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/code/.venv/lib/python3.11/site-packages/sklearn/metrics/__init__.py)
- python code/src/modeling/evaluate.py --input data/results/cv_results.csv --output reports/final_report.md -> rc=1
    2026-09-20 08:10:01,652 - __main__ - INFO - Loading CV results from data/results/cv_results.csv
2026-09-20 08:10:01,653 - __main__ - ERROR - File not found: CV results file not found: data/results/cv_results.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/code/src/modeling/evaluate.py", line 313, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/code/src/modeling/evaluate.py", line 288, in main
    df = load_cv_results(args.input)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/code/src/modeling/evaluate.py", line 39, in load_cv_results
    raise FileNotFoundError(f"CV results file not found: {input_path}")
FileNotFoundError: CV results file not found: data/results/cv_results.csv

## Declared deliverables still missing

- data/models/xgboost_model.json
- data/processed/analysis_report.json
- data/processed/class_exclusion_metadata.json
- data/processed/feature_matrix.parquet
- data/processed/training_log.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logger` — defined in `code/src/utils/logging.py`; called 5 way(s):

- code/src/main.py: logger = setup_logger("main_orchestrator")
- code/src/modeling/train.py: setup_logger()
- code/src/modeling/evaluate.py: setup_logger(__name__)
- code/src/data/ingestion.py: logger = setup_logger("ingestion")
- code/src/utils/logging.py: return setup_logger(name)

Make `setup_logger` in `code/src/utils/logging.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/src/utils/logging.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/src/utils/logging.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/models/xgboost_model.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_train_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/xgboost_model.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/evaluate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/class_exclusion_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_t017_save.py` — NOT invoked by the run-book
    - `code/src/modeling/evaluate.py` — IS a run-book command
    - `code/src/data/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/class_exclusion_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_train_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/train.py` — NOT invoked by the run-book
    - `code/src/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/training_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_train_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/training_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/results/cv_results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/src/modeling/evaluate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/results/cv_results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/src/modeling/evaluate.py`.
