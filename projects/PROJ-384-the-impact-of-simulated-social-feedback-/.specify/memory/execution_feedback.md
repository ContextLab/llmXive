# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python 03_analysis.py; python 04_report.py; 3 command(s) failed: python code/01_ingest.py (rc=1); python code/01_ingest.py (rc=1); python code/02_metrics.py (rc=1); 2 declared deliverable(s) absent: data/processed/user_metrics.csv; data/processed/valence_sequence.csv

## Failing / missing run-book commands

- python code/01_ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/01_ingest.py", line 20, in <module>
    logger = setup_logger()
             ^^^^^^^^^^^^^^
TypeError: setup_logger() missing 1 required positional argument: 'name'
- python code/01_ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/01_ingest.py", line 20, in <module>
    logger = setup_logger()
             ^^^^^^^^^^^^^^
TypeError: setup_logger() missing 1 required positional argument: 'name'
- python code/02_metrics.py -> rc=1
    ter downloads.

Loading weights:   0%|          | 0/201 [00:00<?, ?it/s]
Loading weights: 100%|██████████| 201/201 [00:00<00:00, 14921.59it/s]
2026-08-16 01:55:47,887 - metrics_calculation - ERROR - Failed to load models/lexicon: Lexicon file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/data/raw/lexicons/rosenberg_words.txt
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/02_metrics.py", line 310, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/02_metrics.py", line 248, in main
    lexicon = get_rosenberg_lexicon()
              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/model_loader.py", line 70, in get_rosenberg_lexicon
    raise FileNotFoundError(f"Lexicon file not found: {lexicon_path}")
FileNotFoundError: Lexicon file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/data/raw/lexicons/rosenberg_words.txt
- python 03_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/03_analysis.py': [Errno 2] No such file or directory
- python 04_report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/04_report.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/user_metrics.csv
- data/processed/valence_sequence.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logger` — defined in `code/utils/logger.py`; called 2 way(s):

- code/01_ingest.py: logger = setup_logger()
- code/02_metrics.py: logger = setup_logger("metrics_calculation")

Make `setup_logger` in `code/utils/logger.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/utils/logger.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/utils/logger.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/processed/user_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/user_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valence_sequence.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest.py` — IS a run-book command
    - `code/02_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/valence_sequence.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
