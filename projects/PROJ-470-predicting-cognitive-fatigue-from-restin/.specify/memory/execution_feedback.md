# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/download_manifest.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/download_manifest.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/download.py --validate (rc=1); python code/preprocess.py (rc=1); python code/features.py (rc=1); 4 declared deliverable(s) absent: data/analysis/bh_corrected_pvalues.csv; data/analysis/complexity_metrics.csv; data/analysis/delta_scores.csv

## Failing / missing run-book commands

- python code/download.py --validate -> rc=1
    2026-09-03 02:44:04,064 - download - INFO - Starting download pipeline.
2026-09-03 02:44:04,307 - download - ERROR - HTTP Error: 404 - Not Found
2026-09-03 02:44:04,309 - download - ERROR - Failed to fetch or parse metadata. Exiting.
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 161, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 139, in main
    logger = setup_logger("preprocess")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 19, in setup_logger
    logger = get_logger(name, log_file)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 1 positional argument but 2 were given
- python code/features.py -> rc=1
    unner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/.venv/lib/python3.11/site-packages/nolds/__init__.py", line 5, in <module>
    from .datasets import brown72, tent_map, logistic_map, fbm, fgn, qrandom, \
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/.venv/lib/python3.11/site-packages/nolds/datasets.py", line 467, in <module>
    brown72 = load_brown72()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/.venv/lib/python3.11/site-packages/nolds/datasets.py", line 162, in load_brown72
    with resources.files(__name__).joinpath(fname).open('rb') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/importlib/resources/_common.py", line 22, in files
    return from_package(get_package(package))
                        ^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/importlib/resources/_common.py", line 55, in get_package
    raise TypeError(f'{package!r} is not a package')
TypeError: 'nolds.datasets' is not a package
- python code/analysis.py -> rc=1
    2026-09-03 02:44:06,758 - analysis - INFO - Starting analysis pipeline.
2026-09-03 02:44:06,759 - analysis - INFO - Loaded config: {'filter_low': 1, 'filter_high': 40, 'artifact_threshold': 100, 'random_seed': 42, 'min_participants': 30, 'notch_freq': 50}
2026-09-03 02:44:06,759 - analysis - ERROR - Complexity metrics file not found: data/analysis/complexity_metrics.csv
2026-09-03 02:44:06,760 - analysis - ERROR - Run code/features.py first to generate complexity metrics.
- python code/report.py -> rc=1
    ck (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/report.py", line 138, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/report.py", line 133, in main
    generate_report(results_df, sensitivity_df, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/report.py", line 83, in generate_report
    report.append(render_markdown_table(results))
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/report.py", line 62, in render_markdown_table
    pd.options.mode.future_infer_string = False
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/.venv/lib/python3.11/site-packages/pandas/_config/config.py", line 425, in __setattr__
    raise OptionError("You can only set the value of existing options")
pandas.errors.OptionError: You can only set the value of existing options

## Declared deliverables still missing

- data/analysis/bh_corrected_pvalues.csv
- data/analysis/complexity_metrics.csv
- data/analysis/delta_scores.csv
- data/processed/exclusion_log.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/utils/logging.py`; called 5 way(s):

- code/verify_memory.py: logger = get_logger("verify_memory")
- code/check_sample_size.py: logger = get_logger("check_sample_size")
- code/profile_memory.py: logger = get_logger("memory_profile")
- code/collinearity.py: logger = get_logger(name, log_file)
- code/preprocess.py: logger = get_logger(name, log_file)

Make `get_logger` in `code/utils/logging.py` accept ALL of the above.

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

- `data/analysis/bh_corrected_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/benjamini_hochberg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/bh_corrected_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/complexity_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/complexity_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/delta_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/delta_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_sample_size.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/utils/logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/analysis/complexity_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/features.py`, `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/analysis/complexity_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/features.py`, `code/analysis.py`.

### `data/processed/complexity_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/features.py`, `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/complexity_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/features.py`, `code/analysis.py`.

### `data/processed/lzc_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/features.py`, `code/collinearity.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/lzc_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/features.py`, `code/collinearity.py`.
