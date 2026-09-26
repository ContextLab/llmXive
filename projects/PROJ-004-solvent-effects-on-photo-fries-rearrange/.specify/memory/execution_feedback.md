# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/power.py: self-declared fabricated metric — “…pproximation formula     # or hard-coded values for the specific n=3 case wh…”
- code/data/generate_synthetic.py: self-declared fabricated metric — “…ulate variety     # These are NOT real measurements, just deterministic patterns…”
- code/analysis/ground_state.py: synthetic/fake INPUT data not authorized by the spec — “…t     silent fallback to synthetic data.      Returns:         D…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generation Module. Imple…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…Constraint: This module generates DETERMINISTIC synthetic data for CI logic testin…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…) -> tuple:     """     Generate a deterministic synthetic decay curve.     Uses a…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…th) -> None:     """     Generate synthetic transient-absorption tra…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…1          logger.info(f"Generated synthetic traces to {output_path}"…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/main.py --mode simulate`
- `python code/main.py --mode real --data-path data/raw/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 26 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/power.py: self-declared fabricated metric — “…pproximation formula     # or hard-coded values for the specific n=3 case wh…”; code/data/generate_synthetic.py: self-declared fabricated metric — “…ulate variety     # These are NOT real measurements, just deterministic patterns…”; code/analysis/ground_state.py: synthetic/fake INPUT data not authorized by the spec — “…t     silent fallback to synthetic data.      Returns:         D…”; 2 command(s) failed: python code/main.py --mode simulate (rc=1); python code/main.py --mode real --data-path data/raw/ (rc=1); 8 declared deliverable(s) absent: data/compute/solvent_solvation.csv; data/processed/calibrated_traces.csv; data/processed/environment_logs.json

## Failing / missing run-book commands

- python code/main.py --mode simulate -> rc=1
    2_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1790424151.990976    2400 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1790424151.991353    2400 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
E0000 00:00:1790424153.034756    2400 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
TensorFlow GPU devices disabled via config.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 206, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 193, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'
- python code/main.py --mode real --data-path data/raw/ -> rc=1
    2_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1790424156.525006    2410 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1790424156.525409    2410 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
E0000 00:00:1790424157.568788    2410 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
TensorFlow GPU devices disabled via config.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 206, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 193, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'

## Declared deliverables still missing

- data/compute/solvent_solvation.csv
- data/processed/calibrated_traces.csv
- data/processed/environment_logs.json
- data/processed/kinetic_metrics.csv
- data/processed/study_power_analysis.json
- data/processed/validation_flags.json
- data/raw/real_traces.csv
- data/raw/synthetic_traces.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logging` — defined in `code/utils/logging.py`; called 12 way(s):

- code/main.py: setup_logging(level=logging.INFO)
- code/data/generate_synthetic.py: setup_logging()
- code/data/compute/solvent_models.py: setup_logging(level=args.log_level)
- code/analysis/detection_threshold.py: setup_logging(level=args.log_level)
- code/analysis/kinetic_metrics.py: setup_logging(log_file=log_file)
- code/analysis/ground_state.py: setup_logging(level=args.log_level)
- code/analysis/kinetic_fit.py: setup_logging()
- code/analysis/calibration.py: setup_logging()
- code/analysis/validation.py: setup_logging()
- code/analysis/environment.py: setup_logging()
- code/analysis/sample_tracker.py: setup_logging(level=level)
- code/analysis/error_propagation.py: setup_logging()

Make `setup_logging` in `code/utils/logging.py` accept ALL of the above.

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

- `data/compute/solvent_solvation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/compute/solvent_models.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/compute/solvent_solvation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/calibrated_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/kinetic_metrics.py` — NOT invoked by the run-book
    - `code/analysis/calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/calibrated_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/environment_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/method_spec.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/analysis/environment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/environment_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/kinetic_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/detection_threshold.py` — NOT invoked by the run-book
    - `code/analysis/kinetic_metrics.py` — NOT invoked by the run-book
    - `code/analysis/method_spec.py` — NOT invoked by the run-book
    - `code/analysis/kinetic_fit.py` — NOT invoked by the run-book
    - `code/analysis/replicate_dashboard.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/error_propagation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/kinetic_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/study_power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/study_power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_flags.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/ground_state.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_flags.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/real_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/real_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/hardware/interface.py` — NOT invoked by the run-book
    - `code/data/generate_synthetic.py` — NOT invoked by the run-book
    - `code/analysis/kinetic_fit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
