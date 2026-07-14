# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/03_compute_graph_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…s connectivity matrix or generate a synthetic one.      The pipeline u…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/03_compute_graph_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…s connectivity matrix or generate a synthetic one.      The pipeline u…”; 5 command(s) failed: python code/01_download_and_filter.py (rc=2); python code/03_compute_graph_metrics.py (rc=1); python code/04_train_model.py (rc=1); 4 declared deliverable(s) absent: data/processed/eligible_subjects.csv; data/processed/graph_metrics.csv; data/processed/performance_report.json

## Failing / missing run-book commands

- python code/01_download_and_filter.py -> rc=2
    
- python code/03_compute_graph_metrics.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/03_compute_graph_metrics.py", line 183, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/03_compute_graph_metrics.py", line 130, in main
    raise FileNotFoundError(f"Missing {ELIGIBLE_SUBJECTS_CSV}")
FileNotFoundError: Missing data/processed/eligible_subjects.csv
- python code/04_train_model.py -> rc=1
    
- python code/05_evaluate_model.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/05_evaluate_model.py", line 20, in <module>
    from joblib import load, dump, clone
ImportError: cannot import name 'clone' from 'joblib' (/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/.venv/lib/python3.11/site-packages/joblib/__init__.py)
- python code/06_permutation_test.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/06_permutation_test.py", line 172, in <module>
    @log_operation("run_permutation_test")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable

## Declared deliverables still missing

- data/processed/graph_metrics.csv
- data/processed/performance_report.json
- data/processed/permutation_results.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/11_external_outcome_check.py`; called 14 way(s):

- code/12_memory_profiler.py: logger = get_logger("memory_profiler")
- code/06_permutation_test.py: return get_logger(name)
- code/06_permutation_test.py: logger = get_logger()
- code/08_collinearity_check.py: logger = get_logger("collinearity_check")
- code/15_ci_memory_profiler.py: logger = get_logger("ci_memory_profiler")
- code/00_data_gate.py: logger = get_logger("data_gate")
- code/01_download_and_filter.py: logger = get_logger(__name__)
- code/11_external_outcome_check.py: sites (e.g. ``get_logger("graph_metrics")`` or ``get_logger()``) continue
- code/11_external_outcome_check.py: return get_logger().log(op, **kwargs)
- code/03_compute_graph_metrics.py: logger = get_logger("graph_metrics")
- code/04_train_model.py: LOGGER = get_logger("nested_cv")
- code/05_evaluate_model.py: return get_logger(name)
- code/utils/logger.py: return get_logger().log(op, **kwargs)
- code/utils/memory_profiler.py: logger = get_logger(__name__)

Make `get_logger` in `code/11_external_outcome_check.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/11_external_outcome_check.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/11_external_outcome_check.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/12_memory_profiler.py` — NOT invoked by the run-book
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/08_collinearity_check.py` — IS a run-book command
    - `code/15_run_ci_memory_profile.py` — NOT invoked by the run-book
    - `code/15_ci_memory_profiler.py` — NOT invoked by the run-book
    - `code/11_external_outcome_check.py` — NOT invoked by the run-book
    - `code/14_ci_memory_profiler.py` — NOT invoked by the run-book
    - `code/03_compute_graph_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/09_generate_report.py` — IS a run-book command
    - `code/04_train_model.py` — IS a run-book command
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/09_generate_report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/graph_metrics.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[data]`
- PRODUCER(s) to edit: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
- CONSUMER(s) that read it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
  → Edit the producer so every required name [data] is in `data/processed/graph_metrics.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `graph_metrics.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[data]`
- PRODUCER(s) to edit: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
- CONSUMER(s) that read it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
  → Edit the producer so every required name [data] is in `graph_metrics.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `model.pkl`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[data]`
- PRODUCER(s) to edit: `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
- CONSUMER(s) that read it: `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
  → Edit the producer so every required name [data] is in `model.pkl`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/processed/eligible_subjects.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/06_permutation_test.py`, `code/01_download_and_filter.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/eligible_subjects.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/01_download_and_filter.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`.

### `data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/raw/ds000246/participants.tsv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/01_download_and_filter.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/raw/ds000246/participants.tsv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/01_download_and_filter.py`.

### `participants.tsv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/01_download_and_filter.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `participants.tsv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/01_download_and_filter.py`.
