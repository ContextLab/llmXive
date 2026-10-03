# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…y try/except fallback to synthetic data. It checks for local fil…”
- code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…tch this and fallback to synthetic data.         # The task requ…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…y try/except fallback to synthetic data. It checks for local fil…”; code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…tch this and fallback to synthetic data.         # The task requ…”; 1 command(s) failed: python code/main.py (rc=1); 7 declared deliverable(s) absent: data/processed/cleaned_data.csv; data/processed/correlation_results.csv; data/processed/lasso_diagnostics.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/main.py", line 45, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/main.py", line 18, in main
    log_pipeline_start("Gut Microbiome and Cognitive Performance Analysis")
TypeError: log_pipeline_start() takes 0 positional arguments but 1 was given
- python -c "import pandas as pd; df = pd.read_csv('data/processed/cleaned_data.csv'); print(df.shape); print(df.isnull().sum())" -> rc=1
    ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/cleaned_data.csv'

## Declared deliverables still missing

- data/processed/cleaned_data.csv
- data/processed/correlation_results.csv
- data/processed/lasso_diagnostics.json
- data/processed/lasso_results.csv
- data/processed/regression_diagnostics.json
- data/processed/regression_results.csv
- data/processed/vif_results.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_pipeline_start` — defined in `code/logging_config.py`; called 5 way(s):

- code/diversity.py: log_pipeline_start("diversity_pipeline")
- code/main.py: log_pipeline_start("Gut Microbiome and Cognitive Performance Analysis")
- code/verify_data_source.py: log_pipeline_start("verify_data_source")
- code/save_regression_results.py: log_pipeline_start("save_regression_results")
- code/analysis.py: log_pipeline_start("Analysis Pipeline")

Make `log_pipeline_start` in `code/logging_config.py` accept ALL of the above.

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

- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/diversity.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/save_cleaned_data.py` — NOT invoked by the run-book
    - `code/residual_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_correlation_results.py` — NOT invoked by the run-book
    - `code/validate_sc001.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lasso_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/residual_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lasso_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lasso_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_lasso_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lasso_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_sc002.py` — NOT invoked by the run-book
    - `code/save_regression_results.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/diversity.py`, `code/data_ingestion.py`, `code/analysis.py`, `code/save_cleaned_data.py`, `code/residual_validation.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/diversity.py`, `code/data_ingestion.py`, `code/analysis.py`, `code/residual_validation.py`.
