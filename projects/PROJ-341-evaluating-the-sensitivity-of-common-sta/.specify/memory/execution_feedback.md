# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/simulation_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py --mode validation`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/simulation_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/main.py (rc=1); python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 (rc=1); python code/main.py --mode validation (rc=1); 6 declared deliverable(s) absent: data/simulation/error_rates_summary.csv; data/simulation/p_values_raw.csv; data/simulation/real_data_power.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    ', 'hypotheses': 'null,alternative', 'alpha': 0.05, 'chunk_size': 50}
2026-07-15 08:41:48 - code.simulation.logging_config - CRITICAL - Unexpected error: register_run() takes 1 positional argument but 2 were given

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 371, in main
    run_simulation_grid_chunked(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 203, in run_simulation_grid_chunked
    register_run("simulation", vars(args))
TypeError: register_run() takes 1 positional argument but 2 were given

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 390, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 385, in main
    log_error_details(e)
TypeError: log_error_details() missing 2 required positional arguments: 'error' and 'context'
- python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 -> rc=1
    ', 'hypotheses': 'null,alternative', 'alpha': 0.05, 'chunk_size': 50}
2026-07-15 08:41:50 - code.simulation.logging_config - CRITICAL - Unexpected error: register_run() takes 1 positional argument but 2 were given

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 371, in main
    run_simulation_grid_chunked(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 203, in run_simulation_grid_chunked
    register_run("simulation", vars(args))
TypeError: register_run() takes 1 positional argument but 2 were given

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 390, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 385, in main
    log_error_details(e)
TypeError: log_error_details() missing 2 required positional arguments: 'error' and 'context'
- python code/main.py --mode validation -> rc=1
    lmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/.venv/lib/python3.11/site-packages/ucimlrepo/fetch.py", line 91, in fetch_ucirepo
    raise DatasetNotFoundError('"{}" dataset (id={}) exists in the repository, but is not available for import. Please select a dataset from this list: https://archive.ics.uci.edu/datasets?skip=0&take=10&sort=desc&orderBy=NumHits&search=&Python=true'.format(name, id))
ucimlrepo.fetch.DatasetNotFoundError: "AutoUniv" dataset (id=197) exists in the repository, but is not available for import. Please select a dataset from this list: https://archive.ics.uci.edu/datasets?skip=0&take=10&sort=desc&orderBy=NumHits&search=&Python=true

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 390, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 385, in main
    log_error_details(e)
TypeError: log_error_details() missing 2 required positional arguments: 'error' and 'context'

## Declared deliverables still missing

- data/simulation/error_rates_summary.csv
- data/simulation/p_values_raw.csv
- data/simulation/real_data_power.json
- data/simulation/real_data_pvalues.csv
- data/simulation/thresholds.json
- data/simulation/validation_metrics.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_error_details` — defined in `code/simulation/logging_config.py`; called 1 way(s):

- code/main.py: log_error_details(e)

Make `log_error_details` in `code/simulation/logging_config.py` accept ALL of the above.

### `register_run` — defined in `code/utils/checksum_utils.py`; called 1 way(s):

- code/main.py: register_run("simulation", vars(args))

Make `register_run` in `code/utils/checksum_utils.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/simulation/logging_config.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/simulation/logging_config.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/simulation/error_rates_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/visualization/comparative_plots.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/error_rates_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/p_values_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/simulation/output_writer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/p_values_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_power.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_power.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/real_data_runner.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/thresholds.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/thresholds.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
