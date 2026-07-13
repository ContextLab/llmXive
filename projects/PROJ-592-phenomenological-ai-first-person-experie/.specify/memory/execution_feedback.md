# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --task generate --config code/config.py (rc=1); python code/main.py --task generate_control --config code/config.py (rc=1); python code/main.py --task select_validation_sample --config code/config.py (rc=1); 1 declared deliverable(s) absent: data/processed/validity_scores.csv

## Failing / missing run-book commands

- python code/main.py --task generate --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)
- python code/main.py --task generate_control --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)
- python code/main.py --task select_validation_sample --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)
- python code/main.py --task analyze -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)
- python code/main.py --task validate_human -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)
- python code/main.py --task stats -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)
- python code/main.py --task sensitivity-kappa -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 27, in <module>
    from generation.runner import main as generation_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 36, in <module>
    from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
ImportError: cannot import name 'WarningContext' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/utils/logging.py)

## Declared deliverables still missing

- data/processed/validity_scores.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_operation` — defined in `code/utils/logging.py`; called 20 way(s):

- code/main.py: log_operation("setup_environment", config_path=config_path)
- code/main.py: log_operation("run_generation_phase")
- code/main.py: log_operation("run_control_phase")
- code/main.py: log_operation("run_analysis_phase")
- code/main.py: log_operation("run_stats_phase")
- code/main.py: log_operation("run_validation_phase")
- code/main.py: log_operation("run_full_pipeline")
- code/main.py: log_operation("full_pipeline_complete")
- code/main.py: log_operation("main_start", task=args.task, config=args.config)
- code/main.py: log_operation("task_complete", task=args.task)
- code/main.py: log_operation("task_failed", task=args.task, error=str(e))
- code/utils/logging.py: """Dual-purpose: a decorator (@log_operation) OR a direct logging call.
- code/analysis/stats.py: log_operation("load_aggregated_scores_start")
- code/analysis/stats.py: log_operation("load_aggregated_scores_complete", count=len(merged_records))
- code/analysis/stats.py: log_operation("orchestrate_analysis_start")
- code/analysis/stats.py: log_operation("orchestrate_analysis_complete", output=str(output_path))
- code/analysis/stats.py: log_operation("stats_main_start")
- code/generation/timeout_monitor.py: log_operation("timeout_monitor_main_start")
- code/generation/timeout_monitor.py: log_operation("timeout_monitor_main_complete", output=str(output_path))
- code/generation/runner.py: log_operation("generate_sample_attempt", strategy=strategy, seed=seed)

Make `log_operation` in `code/utils/logging.py` accept ALL of the above.

### `retry_on_failure` — defined in `code/utils/logging.py`; called 7 way(s):

- code/utils/logging.py: - @retry_on_failure(max_attempts=3, delay_seconds=1.0)
- code/utils/logging.py: - @retry_on_failure(max_attempts=3, delay=5)
- code/utils/logging.py: - @retry_on_failure(max_attempts=3, delay=2.0, logger=None)
- code/validation/turing_simulation.py: @retry_on_failure(max_attempts=3, delay_seconds=1.0)
- code/generation/runner_local.py: @retry_on_failure(max_attempts=3, delay=5)
- code/generation/runner.py: @retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0, logger=None)
- code/generation/control_corpus.py: @retry_on_failure(max_attempts=3, delay=2.0, logger=logger)

Make `retry_on_failure` in `code/utils/logging.py` accept ALL of the above.

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

- `data/processed/validity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/validity_justification.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/validation/stratified_sampler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
