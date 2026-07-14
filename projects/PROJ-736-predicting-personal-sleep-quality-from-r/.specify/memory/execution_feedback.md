# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/config.py: self-declared fabricated metric — “…rn env_val          # Default hardcoded values for the pipeline     default…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…regions = 400          # Generate synthetic but realistic-looking da…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…ounds is None:         # Generate synthetic confounds         confou…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/config.py: self-declared fabricated metric — “…rn env_val          # Default hardcoded values for the pipeline     default…”; code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…regions = 400          # Generate synthetic but realistic-looking da…”; code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…ounds is None:         # Generate synthetic confounds         confou…”; 2 command(s) failed: python code/data/download_hcp.py (rc=1); python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/predictions.npy; data/raw/behavioral/hcp1200_behavioral_data.csv

## Failing / missing run-book commands

- python code/data/download_hcp.py -> rc=1
    
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/main.py", line 12, in <module>
    from data.download_hcp import download_hcp_data
ImportError: cannot import name 'download_hcp_data' from 'data.download_hcp' (/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/data/download_hcp.py)

## Declared deliverables still missing

- data/processed/predictions.npy
- data/raw/behavioral/hcp1200_behavioral_data.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_stage_start` — defined in `code/utils/logging.py`; called 25 way(s):

- code/main.py: log_stage_start("full_pipeline", message="[Pipeline] START: Beginning end-to-end execution")
- code/main.py: log_stage_start("Data Download", message="[Data Download] START: Fetching HCP data")
- code/main.py: log_stage_start("Preprocessing", message="[Preprocessing] START: Running nuisance regression and filtering")
- code/main.py: log_stage_start("Feature Engineering", message="[Feature Engineering] START: Computing connectivity vectors")
- code/main.py: log_stage_start("Model Training", message="[Model Training] START: Running ElasticNetCV")
- code/utils/logging.py: log_stage_start(stage)
- code/utils/logging.py: log_stage_start(stage, message=...)
- code/utils/logging.py: log_stage_start(logger, stage)
- code/utils/logging.py: log_stage_start(logger, stage, message=...)
- code/data/download_hcp.py: log_stage_start("download_behavioral_csv", message=f"Downloading to {dest_path}")
- code/data/download_hcp.py: log_stage_start("create_filtered_subjects", message=f"Reading {csv_path}")
- code/data/preprocess.py: log_stage_start("Preprocessing", message="[Preprocessing] START: Beginning nuisance regression and filtering")
- code/data/feature_engineering.py: log_stage_start("Feature Engineering", message="[Feature Engineering] START: Computing connectivity vectors")
- code/modeling/interpret.py: log_stage_start("Interpretation", "Extracting non-zero coefficients")
- code/modeling/evaluate.py: log_stage_start(logger, "Loading Data")
- code/modeling/evaluate.py: log_stage_start(logger, "Bootstrap Resampling (1000 iterations)")
- code/modeling/evaluate.py: log_stage_start(logger, "Saving Bootstrap Results")
- code/modeling/evaluate.py: log_stage_start(logger, "Evaluation")
- code/modeling/train.py: log_stage_start("load_data", message="Reading feature matrix and labels")
- code/modeling/train.py: log_stage_start(
- code/modeling/report_generator.py: log_stage_start(logger, "Report Generation")
- code/modeling/visualize.py: log_stage_start(logger, "Interpretation", "Extracting non-zero coefficients")
- code/modeling/visualize.py: log_stage_start(logger, "Visualization", "Loading Schaefer coordinates")
- code/modeling/visualize.py: log_stage_start(logger, "Visualization", "Generating brain surface plot")
- code/modeling/validate_plot.py: log_stage_start("T033", f"Validating {plot_path}")

Make `log_stage_start` in `code/utils/logging.py` accept ALL of the above.

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

- `data/processed/predictions.npy` is declared but was NOT written. Scripts referencing it:
    - `code/utils/metrics.py` — NOT invoked by the run-book
    - `code/modeling/__init__.py` — NOT invoked by the run-book
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/predictions.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/behavioral/hcp1200_behavioral_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_hcp.py` — IS a run-book command
    - `code/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/behavioral/hcp1200_behavioral_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `hcp1200_behavioral_data.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[raw_dir]`
- PRODUCER(s) to edit: `code/data/download_hcp.py`, `code/modeling/train.py`
- CONSUMER(s) that read it: `code/config.py`, `code/data/download_hcp.py`, `code/modeling/train.py`
  → Edit the producer so every required name [raw_dir] is in `hcp1200_behavioral_data.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
