# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/download.py: self-declared fabricated metric — “…h in config.yaml is still the placeholder value. Please update with the real…”
- code/data/extract_features.py: synthetic/fake INPUT data not authorized by the spec — “…estimation based on the synthetic dataset properties.     In a rea…”
- code/data/extract_features.py: synthetic/fake INPUT data not authorized by the spec — “…pixel = 0.1 um for this synthetic dataset         median_pixels =…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/eval/metrics.py`
  - script usage: `metrics.py [-h] --predictions PREDICTIONS [--output OUTPUT]`
  - argparse error: `metrics.py: error: the following arguments are required: --predictions`
- run-book command: `python code/eval/sensitivity.py`
  - script usage: `sensitivity.py [-h] --predictions PREDICTIONS [--output OUTPUT]`
  - argparse error: `sensitivity.py: error: the following arguments are required: --predictions`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/download.py: self-declared fabricated metric — “…h in config.yaml is still the placeholder value. Please update with the real…”; code/data/extract_features.py: synthetic/fake INPUT data not authorized by the spec — “…estimation based on the synthetic dataset properties.     In a rea…”; code/data/extract_features.py: synthetic/fake INPUT data not authorized by the spec — “…pixel = 0.1 um for this synthetic dataset         median_pixels =…”; 10 command(s) failed: python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); python code/data/validate.py (rc=1); 1 declared deliverable(s) absent: data/features/test_grain_features.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/download.py", line 53, in setup_download_logging
    results_dir = get_results_dir()
                  ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 97, in get_results_dir
    root = get_project_root()
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 77, in get_project_root
    return _find_project_root()
           ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 65, in _find_project_root
    raise FileNotFoundError(
FileNotFoundError: Could not determine project root. Expected 'code' and 'data' directories. Searched: /home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py, /home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros and their parents.
- python code/data/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/preprocess.py", line 225, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/preprocess.py", line 211, in main
    logger = setup_logging()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/preprocess.py", line 32, in setup_logging
    return get_logger("preprocess", log_file="results/preprocess.log")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() got an unexpected keyword argument 'log_file'
- python code/data/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/validate.py", line 183, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/validate.py", line 133, in main
    logger = setup_logging()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/validate.py", line 25, in setup_logging
    logger = get_logger('validate', log_file='results/validation.log')
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() got an unexpected keyword argument 'log_file'
- python code/data/extract_features.py -> rc=1
    2026-08-03 18:56:01,323 - extract_features - INFO - Starting test set feature extraction (T022a)
2026-08-03 18:56:01,323 - extract_features - ERROR - Feature extraction failed: Could not determine project root. Expected 'code' and 'data' directories. Searched: /home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py, /home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros and their parents.
- python code/models/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/models/train.py", line 24, in <module>
    from train.trainer import main as trainer_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/models/train.py", line 24, in <module>
    from train.trainer import main as trainer_main
ModuleNotFoundError: No module named 'train.trainer'; 'train' is not a package
- python code/models/train_ablation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/models/train_ablation.py", line 18, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/eval/metrics.py -> rc=2
    usage: metrics.py [-h] --predictions PREDICTIONS [--output OUTPUT]
                  [--alpha ALPHA] [--seed SEED]
metrics.py: error: the following arguments are required: --predictions
- python code/eval/interpret.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/eval/interpret.py", line 21, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/eval/predictor.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/eval/predictor.py", line 17, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/eval/sensitivity.py -> rc=2
    usage: sensitivity.py [-h] --predictions PREDICTIONS [--output OUTPUT]
                      [--seed SEED]
sensitivity.py: error: the following arguments are required: --predictions

## Declared deliverables still missing

- data/features/test_grain_features.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/utils/logging_config.py`; called 7 way(s):

- code/utils/logging_config.py: logger = get_logger()
- code/train/trainer.py: logger = get_logger("trainer")
- code/eval/iou_calculator.py: logger = get_logger("iou_calculator")
- code/data/split.py: return get_logger("splitter", "split")
- code/data/process_all.py: logger = get_logger("process_all")
- code/data/validate.py: logger = get_logger('validate', log_file='results/validation.log')
- code/data/preprocess.py: return get_logger("preprocess", log_file="results/preprocess.log")

Make `get_logger` in `code/utils/logging_config.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/utils/logging_config.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/utils/logging_config.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/features/test_grain_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_features.py` — IS a run-book command
  Make ONE of these WRITE `data/features/test_grain_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
